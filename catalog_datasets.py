#!/usr/bin/env python3
"""
===============================
Dynamic Dataset Catalog Builder
===============================

This script scans subdirectories of a specified folder (or the current folder by default)
for `.json` files containing DICOM metadata, and creates a CSV catalog of selected fields.

====================
Key Features:
====================
- Recursively detects `.json` metadata files.
- Accepts:
  1. Optional directory to scan
  2. Optional comma-separated field list (overrides catalog_fields.txt)
  3. Optional output directory for saving the CSV

==========================
How to Use This Script:
==========================
Basic:
    python catalog_datasets.py

Specify target folder:
    python catalog_datasets.py /path/to/data

Specify fields directly (bypasses catalog_fields.txt):
    python catalog_datasets.py /path --fields Vendor,Modality

Specify output directory:
    python catalog_datasets.py /path --fields Vendor --out /my/output

=====================
Output:
=====================
- dcm_qa_catalog.csv — generated in the current or specified output directory
- catalog_fields.txt — created on first run unless --fields is used

Author: Roger Newman-Norlund (2025)
License: BSD-2-Clause license (see included file "LICENSE")
"""

import json
import csv
import sys
from pathlib import Path

def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Catalog JSON metadata across directories.")
    parser.add_argument("target", nargs="?", default=".", help="Directory to scan (defaults to current)")
    parser.add_argument("--fields", type=str, help="Comma-separated list of fields to extract (bypass field file)")
    parser.add_argument("--out", type=str, help="Directory to save CSV output")
    return parser.parse_args()

def find_json_files(root):
    return list(Path(root).rglob("*.json"))

def collect_all_keys(json_files):
    keys = set()
    for path in json_files:
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            keys.update(data.keys())
        except Exception:
            continue
    return sorted(keys)

def load_selected_fields(field_file):
    with open(field_file, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def write_field_template(keys, field_file):
    with open(field_file, 'w') as f:
        f.write("# Edit this list to select which fields to include in the final CSV.\n")
        f.write("# Lines starting with # are comments and ignored.\n")
        for key in keys:
            f.write(f"{key}\n")

def extract_record(json_path, fields):
    record = {"Path": str(json_path)}
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        for field in fields:
            record[field] = data.get(field, "")
    except Exception as e:
        record["Error"] = str(e)
    return record

def write_csv(records, fields, output_path):
    all_fields = ["Path"] + fields + ["Error"]
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_fields)
        writer.writeheader()
        for r in records:
            writer.writerow(r)

def main():
    args = parse_args()
    root_dir = Path(args.target).resolve()
    out_dir = Path(args.out).resolve() if args.out else Path.cwd()
    field_file = Path("catalog_fields.txt")
    output_csv = out_dir / "dcm_qa_catalog.csv"

    print(f"Scanning: {root_dir}")
    json_files = find_json_files(root_dir)
    print(f"Found {len(json_files)} JSON files.")

    if args.fields:
        selected_fields = [f.strip() for f in args.fields.split(",") if f.strip()]
        print(f"Using fields from command line: {selected_fields}")
    else:
        all_keys = collect_all_keys(json_files)
        if not field_file.exists():
            print(f"Generating field list file: {field_file}")
            write_field_template(all_keys, field_file)
            print("Edit the field list and re-run this script, or use --fields option.")
            return
        selected_fields = load_selected_fields(field_file)
        print(f"Using selected fields from {field_file}: {selected_fields}")

    print("Generating catalog...")
    records = [extract_record(j, selected_fields) for j in json_files]
    write_csv(records, selected_fields, output_csv)

    print(f"Catalog written to: {output_csv}")

if __name__ == "__main__":
    main()