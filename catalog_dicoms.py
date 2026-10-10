#!/usr/bin/env python3
"""
============================
DICOM Tag Catalog Generator
============================

This script scans directories for DICOM files and catalogs specific tag values.
It processes one representative file per series (based on SeriesInstanceUID).

==========================
How to Use This Script:
==========================
Basic usage:
    python catalog_dicoms.py /path/to/DICOMs gggg,eeee

With verbose output:
    python catalog_dicoms.py /path/to/DICOMs gggg,eeee --verbose

Use absolute paths:
    python catalog_dicoms.py /path/to/DICOMs gggg,eeee --absolute-paths

Specify output file:
    python catalog_dicoms.py /path/to/DICOMs gggg,eeee --out mycatalog.csv

Author: Roger Newman-Norlund (2025)
License: BSD-2-Clause license (see included file "LICENSE")
"""

import os
import sys
import csv
import argparse
from pathlib import Path
import pydicom
from pydicom.tag import Tag
from pydicom.errors import InvalidDicomError

def parse_args():
    parser = argparse.ArgumentParser(
        description="Catalog specific DICOM tag values across a directory tree."
    )
    parser.add_argument("target", help="Directory to scan for DICOM files")
    parser.add_argument("tag", help="DICOM tag in format gggg,eeee (e.g., 0018,0015)")
    parser.add_argument("--verbose", action="store_true", help="Print verbose error messages")
    parser.add_argument("--out", type=str, default="catalog_dicoms.csv",
                        help="Output CSV file name (default: catalog_dicoms.csv)")
    parser.add_argument("--absolute-paths", action="store_true",
                        help="Use absolute paths instead of relative paths in output")
    return parser.parse_args()


def is_dicom_file(path):
    # Checks first 132 bytes for 'DICM' header
    try:
        with open(path, 'rb') as f:
            return f.read(132)[128:132] == b'DICM'
    except Exception:
        return False

def catalog_dicoms(root_path, tag_str, output_file='catalog_dicoms.csv',
                   verbose=False, use_absolute=False):
    tag = Tag(int(tag_str[:4], 16), int(tag_str[5:], 16))
    series_seen = set()
    rows = []
    cwd = Path.cwd()

    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            if not os.path.isfile(filepath):
                continue
            if not is_dicom_file(filepath):
                continue
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True, force=True)
                series_uid = str(ds.get((0x0020, 0x000E), None))
                if not series_uid or series_uid in series_seen:
                    continue
                series_seen.add(series_uid)
                if tag.group == 0x0002:
                    value = ds.file_meta.get(tag, '')
                else:
                    value = ds.get(tag, '')
                # Extract the raw value, not the DataElement object
                value_str = value.value if hasattr(value, 'value') else str(value)

                # Format path based on preference
                file_path = Path(filepath)
                if use_absolute:
                    path_str = str(file_path.resolve())
                else:
                    try:
                        path_str = str(file_path.relative_to(cwd))
                    except ValueError:
                        # Fallback to absolute if not relative to cwd
                        path_str = str(file_path.resolve())

                rows.append([path_str, value_str])
            except Exception as e:
                if verbose:
                    print(f"Skipping {filepath}: {e}", file=sys.stderr)
                continue

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Path', f'Tag {tag_str}'])
        writer.writerows(rows)


if __name__ == '__main__':
    args = parse_args()
    catalog_dicoms(
        args.target,
        args.tag,
        output_file=args.out,
        verbose=args.verbose,
        use_absolute=args.absolute_paths
    )
