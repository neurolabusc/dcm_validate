#!/usr/bin/env python3
"""Summarize DICOM-WSI instances: geometry, codec, encapsulation and the first frame's J2K header.

Usage: python3 inspect_wsi.py <dir> [<dir> ...]
"""
import sys
from pathlib import Path

import pydicom

from wsi_common import items, pixel_items_start

def j2k_header(b):
    """MCT flag and component subsampling from a J2K codestream's image-size (FF51) and coding-style (FF52) markers."""
    out = {}
    i = 0
    while i + 4 < len(b) and i < 4096:
        if b[i] == 0xFF and b[i + 1] == 0x51:  # image size (FF51)
            n = int.from_bytes(b[i + 38:i + 40], 'big')
            comps = [(b[i + 40 + 3 * c], b[i + 41 + 3 * c], b[i + 42 + 3 * c]) for c in range(n)]
            out['comps'] = [f"{(s & 0x7F) + 1}{'s' if s & 0x80 else 'u'}/{dx}x{dy}" for s, dx, dy in comps]
        if b[i] == 0xFF and b[i + 1] == 0x52:  # coding style (FF52)
            out['mct'] = b[i + 8]
            out['wavelet'] = '5-3' if b[i + 13] else '9-7'
            break
        i += 1
    return out


for d in sys.argv[1:]:
    print(f'== {Path(d).name}')
    for f in sorted(Path(d).glob('*.dcm')):
        ds = pydicom.dcmread(f, defer_size='1 KB')
        ts = ds.file_meta.TransferSyntaxUID
        frames = int(ds.get('NumberOfFrames', 1))
        line = (f'  {f.name}: {"/".join(ds.ImageType[2:3])} {ds.get("TotalPixelMatrixColumns", ds.Columns)}x'
                f'{ds.get("TotalPixelMatrixRows", ds.Rows)} tile {ds.Columns}x{ds.Rows} frames {frames} '
                f'{ds.PhotometricInterpretation} spp {ds.SamplesPerPixel} bits {ds.BitsStored} ts {ts} '
                f'org {ds.get("DimensionOrganizationType", "-")} paths {ds.get("NumberOfOpticalPaths", "-")} '
                f'planes {ds.get("TotalPixelMatrixFocalPlanes", "-")}')
        if not ts.is_encapsulated:
            print(line + ' (native)')
            continue
        with open(f, 'rb') as fp:
            its = list(items(fp, pixel_items_start(ds, fp)))
            bot = its[0][1]
            fp.seek(its[1][0])
            head = fp.read(min(4096, its[1][1]))
        eot = 'EOT' if 'ExtendedOffsetTable' in ds else ''
        print(line + f' items {len(its) - 1} BOT {bot // 4} {eot} {j2k_header(head) if "4.9" in ts else ""}')
