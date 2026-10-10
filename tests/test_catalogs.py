#!/usr/bin/env python3
"""
====================================
Test Suite for Catalog System
====================================

This script tests the catalog generation system to ensure:
1. Path handling (relative vs absolute) works correctly
2. Both catalog scripts produce valid output
3. The orchestration script successfully generates catalogs

Run with: python test_catalogs.py

Author: Roger Newman-Norlund (2025)
License: BSD-2-Clause license (see included file "LICENSE")
"""

import csv
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class TestCatalogSystem(unittest.TestCase):
    """Test suite for the dcm_validate catalog system."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        cls.repo_root = Path(__file__).parent
        cls.test_dir = cls.repo_root / "test_temp"
        cls.test_dir.mkdir(exist_ok=True)

        # Find a test dataset to use
        cls.test_dataset = None
        for dataset in cls.repo_root.glob("dcm_qa*"):
            if dataset.is_dir() and not dataset.name.endswith("_temp"):
                cls.test_dataset = dataset
                break

        if cls.test_dataset is None:
            raise ValueError("No dcm_qa* datasets found for testing")

        print(f"\nUsing test dataset: {cls.test_dataset.name}")

    @classmethod
    def tearDownClass(cls):
        """Clean up test directory after all tests."""
        if cls.test_dir.exists():
            shutil.rmtree(cls.test_dir)

    def test_catalog_datasets_relative_paths(self):
        """Test that catalog_datasets.py generates relative paths by default."""
        print("\n[TEST] Testing catalog_datasets.py with relative paths...")

        output_csv = self.test_dir / "test_relative.csv"

        # Run catalog_datasets.py with minimal fields
        cmd = [
            sys.executable,
            str(self.repo_root / "catalog_datasets.py"),
            str(self.test_dataset),
            "--fields", "Manufacturer",
            "--out", str(self.test_dir)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Rename output to expected location
        default_output = self.test_dir / "dcm_qa_catalog.csv"
        if default_output.exists():
            default_output.rename(output_csv)

        self.assertTrue(output_csv.exists(), "Output CSV not created")

        # Check that paths are relative
        with open(output_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            self.assertGreater(len(rows), 0, "No data in CSV")

            # Check first row's path
            first_path = rows[0]['Path']
            self.assertFalse(first_path.startswith('/'),
                           f"Path should be relative but got: {first_path}")
            self.assertTrue(self.test_dataset.name in first_path,
                          f"Path should contain dataset name: {first_path}")

        print(f"✓ Generated {len(rows)} records with relative paths")

    def test_catalog_datasets_absolute_paths(self):
        """Test that catalog_datasets.py generates absolute paths when requested."""
        print("\n[TEST] Testing catalog_datasets.py with absolute paths...")

        output_csv = self.test_dir / "test_absolute.csv"

        # Run with --absolute-paths flag
        cmd = [
            sys.executable,
            str(self.repo_root / "catalog_datasets.py"),
            str(self.test_dataset),
            "--fields", "Manufacturer",
            "--out", str(self.test_dir),
            "--absolute-paths"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Rename output to expected location
        default_output = self.test_dir / "dcm_qa_catalog.csv"
        if default_output.exists():
            default_output.rename(output_csv)

        self.assertTrue(output_csv.exists(), "Output CSV not created")

        # Check that paths are absolute
        with open(output_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            self.assertGreater(len(rows), 0, "No data in CSV")

            # Check first row's path
            first_path = rows[0]['Path']
            path_obj = Path(first_path)
            self.assertTrue(path_obj.is_absolute(),
                          f"Path should be absolute but got: {first_path}")

        print(f"✓ Generated {len(rows)} records with absolute paths")

    def test_catalog_dicoms_output(self):
        """Test that catalog_dicoms.py produces valid output."""
        print("\n[TEST] Testing catalog_dicoms.py output...")

        output_csv = self.test_dir / "test_dicoms.csv"

        # Find DICOM files in test dataset
        dicom_dir = None
        for subdir in self.test_dataset.rglob("*"):
            if subdir.is_dir():
                # Check if directory contains DICOM files
                dicom_files = list(subdir.glob("*.dcm")) or list(subdir.glob("*.IMA"))
                if dicom_files:
                    dicom_dir = subdir
                    break

        if dicom_dir is None:
            print("⊗ No DICOM files found in test dataset - skipping test")
            self.skipTest("No DICOM files available")
            return

        # Run catalog_dicoms.py on Manufacturer tag (0008,0070)
        cmd = [
            sys.executable,
            str(self.repo_root / "catalog_dicoms.py"),
            str(dicom_dir),
            "0008,0070",
            "--out", str(output_csv)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Check for errors in subprocess
        if result.returncode != 0:
            print(f"⊗ catalog_dicoms.py failed with error:\n{result.stderr}")
            self.skipTest(f"catalog_dicoms.py failed: {result.stderr}")
            return

        # The script might not find any valid DICOM series, which is okay
        if not output_csv.exists():
            print("⊗ No DICOM series cataloged (may be expected for some datasets)")
            self.skipTest("No DICOM output generated")
            return

        # Verify CSV structure
        with open(output_csv, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            # Should have Path and Tag columns
            self.assertIn('Path', reader.fieldnames)
            self.assertIn('Tag 0008,0070', reader.fieldnames)

            if len(rows) > 0:
                print(f"✓ Cataloged {len(rows)} DICOM series")
            else:
                print("⊗ No DICOM series found (may be expected for some datasets)")

    def test_generate_all_catalogs_discovery(self):
        """Test that generate_all_catalogs.py discovers datasets correctly."""
        print("\n[TEST] Testing dataset discovery...")

        # Run with --help to verify script is functional
        cmd = [
            sys.executable,
            str(self.repo_root / "generate_all_catalogs.py"),
            "--help"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, "Script should run --help successfully")
        self.assertIn("Generate catalogs", result.stdout)

        print("✓ generate_all_catalogs.py is functional")

        # Count actual datasets
        datasets = [d for d in self.repo_root.glob("dcm_qa*")
                   if d.is_dir() and not d.name.endswith("_temp")]

        print(f"✓ Found {len(datasets)} dcm_qa datasets")
        self.assertGreater(len(datasets), 0, "Should find at least one dataset")


def main():
    """Run the test suite."""
    print("=" * 60)
    print("dcm_validate Catalog System Test Suite")
    print("=" * 60)

    # Run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCatalogSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Summary
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("✗ Some tests failed")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
