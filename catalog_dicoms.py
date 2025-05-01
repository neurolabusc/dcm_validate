#!/usr/bin/env python3
import os
import sys
import csv
import pydicom
from pydicom.tag import Tag
from pydicom.errors import InvalidDicomError

def is_dicom_file(path):
    # Checks first 132 bytes for 'DICM' header
    try:
        with open(path, 'rb') as f:
            return f.read(132)[128:132] == b'DICM'
    except Exception:
        return False

def catalog_dicoms(root_path, tag_str, verbose=False):
    tag = Tag(int(tag_str[:4], 16), int(tag_str[5:], 16))
    series_seen = set()
    rows = []

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
                rows.append([os.path.basename(filepath), value_str])
            except Exception as e:
                if verbose:
                    print(f"Skipping {filepath}: {e}", file=sys.stderr)
                continue

    with open('catalog_dicoms.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', f'Tag {tag_str}'])
        writer.writerows(rows)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python catalog_dicoms.py /path/to/DICOMs gggg,eeee [--verbose]", file=sys.stderr)
        sys.exit(1)

    verbose = '--verbose' in sys.argv
    catalog_dicoms(sys.argv[1], sys.argv[2], verbose=verbose)
