#!/usr/bin/env python3
"""
=================================
Catalog Orchestration Script
=================================

This script generates comprehensive catalogs for all dcm_qa datasets in the repository.
It creates both individual per-dataset catalogs and a combined catalog with all datasets.

Key Features:
- Auto-discovers all dcm_qa* directories
- Generates individual CSV catalog for each dataset
- Combines all catalogs into a single all_datasets.csv with Dataset column
- Supports custom field selection
- Outputs to organized catalogs/ directory

==========================
How to Use This Script:
==========================
Generate catalogs with default fields (from catalog_fields.txt):
    python generate_all_catalogs.py

Specify fields to catalog:
    python generate_all_catalogs.py --fields Manufacturer,Modality,EchoTime

Use absolute paths:
    python generate_all_catalogs.py --absolute-paths

Specify custom field file:
    python generate_all_catalogs.py --field-file my_fields.txt

Specify output directory:
    python generate_all_catalogs.py --out /path/to/output

=======================
Output:
=======================
- catalogs/dcm_qa_<name>.csv — individual dataset catalogs
- catalogs/all_datasets.csv — combined catalog with Dataset column

Author: Roger Newman-Norlund (2025)
License: BSD-2-Clause license (see included file "LICENSE")
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate catalogs for all dcm_qa datasets."
    )
    parser.add_argument(
        "--fields",
        type=str,
        help="Comma-separated list of fields to extract (bypass field file)"
    )
    parser.add_argument(
        "--field-file",
        type=str,
        default="catalog_fields.txt",
        help="Path to field list file (default: catalog_fields.txt)"
    )
    parser.add_argument(
        "--absolute-paths",
        action="store_true",
        help="Use absolute paths instead of relative paths in output"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="catalogs",
        help="Output directory for catalogs (default: catalogs)"
    )
    return parser.parse_args()


def discover_datasets(root_dir="."):
    """Find all dcm_qa* directories."""
    root = Path(root_dir)
    datasets = sorted([d for d in root.iterdir()
                      if d.is_dir() and d.name.startswith("dcm_qa")])
    return datasets


def check_submodules_initialized(datasets):
    """Check if dataset directories are empty (uninitialized submodules)."""
    empty_datasets = []

    for dataset in datasets:
        # Check if directory is empty or has no substantial content
        contents = list(dataset.iterdir())
        # Filter out hidden files like .git
        visible_contents = [f for f in contents if not f.name.startswith('.')]

        if len(visible_contents) == 0:
            empty_datasets.append(dataset.name)

    return empty_datasets


def generate_dataset_catalog(dataset_dir, output_dir, args):
    """Generate catalog for a single dataset."""
    dataset_name = dataset_dir.name
    output_file = output_dir / f"{dataset_name}.csv"

    # Build command for catalog_datasets.py
    cmd = [
        sys.executable,
        "catalog_datasets.py",
        str(dataset_dir),
        "--out", str(output_dir)
    ]

    # Add optional arguments
    if args.fields:
        cmd.extend(["--fields", args.fields])
    else:
        cmd.extend(["--field-file", args.field_file])

    if args.absolute_paths:
        cmd.append("--absolute-paths")

    print(f"Generating catalog for {dataset_name}...")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Rename output from dcm_qa_catalog.csv to dataset-specific name
        default_output = output_dir / "dcm_qa_catalog.csv"
        if default_output.exists():
            default_output.rename(output_file)

        return output_file
    except subprocess.CalledProcessError as e:
        print(f"Error generating catalog for {dataset_name}: {e}", file=sys.stderr)
        if e.stderr:
            print(e.stderr, file=sys.stderr)
        return None


def combine_catalogs(catalog_files, output_file):
    """Combine individual catalogs into single file with Dataset column."""
    print(f"\nCombining {len(catalog_files)} catalogs into {output_file}...")

    all_rows = []
    fieldnames = None

    for catalog_file in catalog_files:
        if not catalog_file.exists():
            continue

        dataset_name = catalog_file.stem  # e.g., dcm_qa_12bit

        with open(catalog_file, 'r', newline='') as f:
            reader = csv.DictReader(f)

            # Store fieldnames from first file
            if fieldnames is None:
                fieldnames = reader.fieldnames

            # Add Dataset column to each row
            for row in reader:
                row['Dataset'] = dataset_name
                all_rows.append(row)

    # Write combined catalog with Dataset as first column
    if fieldnames:
        output_fieldnames = ['Dataset'] + list(fieldnames)

        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=output_fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        print(f"Combined catalog written with {len(all_rows)} total records.")
    else:
        print("No data to combine.", file=sys.stderr)


def main():
    args = parse_args()

    # Create output directory
    output_dir = Path(args.out)
    output_dir.mkdir(exist_ok=True)

    # Discover all datasets
    datasets = discover_datasets()

    if not datasets:
        print("No dcm_qa* directories found in current directory.", file=sys.stderr)
        sys.exit(1)

    # Check for uninitialized submodules
    empty_datasets = check_submodules_initialized(datasets)
    if empty_datasets:
        print("Error: The following dataset directories are empty (uninitialized git submodules):",
              file=sys.stderr)
        for ds in empty_datasets:
            print(f"  - {ds}", file=sys.stderr)
        print("\nTo initialize submodules, run:", file=sys.stderr)
        print("  git submodule update --init --recursive", file=sys.stderr)
        print("\nOr clone with submodules initialized:", file=sys.stderr)
        print("  git clone --recursive <repository-url>", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(datasets)} datasets to catalog:")
    for ds in datasets:
        print(f"  - {ds.name}")
    print()

    # Generate individual catalogs
    catalog_files = []
    for dataset in datasets:
        catalog_file = generate_dataset_catalog(dataset, output_dir, args)
        if catalog_file:
            catalog_files.append(catalog_file)

    # Combine into single catalog
    if catalog_files:
        combined_output = output_dir / "all_datasets.csv"
        combine_catalogs(catalog_files, combined_output)
        print(f"\n✓ Catalog generation complete!")
        print(f"  Individual catalogs: {output_dir}/")
        print(f"  Combined catalog: {combined_output}")
    else:
        print("No catalogs were successfully generated.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
