#!/usr/bin/env python3
"""Extract a reproducible sample of encapsulated WSI frames plus opj_decompress references.

For each slide directory, take the largest VOLUME instance and the smallest
multi-frame one, and sample frames at the four corners, the edges, the centre
and 16 seeded random positions. Writes, under <out>/<slide>/:
  <instance>_f<frame>.j2k   the frame's codestream (item payload, no item header)
  <instance>_f<frame>.ppm   opj_decompress output (OpenJPEG decode + its sYCC->RGB)
  manifest.json             source checksums, frame numbers, tile positions, byte ranges

TILED_FULL only, one item per frame (what the JPEG 2000 corpus uses); anything
else is reported and skipped, never guessed.

Usage: python3 sample_frames.py <out_dir> <slide_dir> [<slide_dir> ...]
"""
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

import pydicom

from wsi_common import items, pixel_items_start

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fp:
        for chunk in iter(lambda: fp.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def sample_positions(cols, rows, seed):
    pts = {(0, 0), (cols - 1, 0), (0, rows - 1), (cols - 1, rows - 1),
           (cols // 2, 0), (cols // 2, rows - 1), (0, rows // 2), (cols - 1, rows // 2),
           (cols // 2, rows // 2)}
    rng = random.Random(seed)
    while len(pts) < min(cols * rows, 25):
        pts.add((rng.randrange(cols), rng.randrange(rows)))
    return sorted(pts, key=lambda p: (p[1], p[0]))


def main():
    out_root = Path(sys.argv[1])
    for slide in map(Path, sys.argv[2:]):
        vols = []
        for f in sorted(slide.glob('*.dcm')):
            ds = pydicom.dcmread(f, defer_size='1 KB')
            if 'VOLUME' in ds.ImageType and int(ds.get('NumberOfFrames', 1)) > 1:
                vols.append((int(ds.NumberOfFrames), f, ds))
        if not vols:
            print(f'{slide.name}: no multi-frame VOLUME instance')
            continue
        vols.sort(key=lambda v: v[0])
        picks = [vols[-1]] + ([vols[0]] if len(vols) > 1 else [])
        out = out_root / slide.name
        out.mkdir(parents=True, exist_ok=True)
        manifest = {'slide': slide.name, 'instances': []}
        for nframes, f, ds in picks:
            org = ds.get('DimensionOrganizationType', '')
            if org != 'TILED_FULL':
                print(f'{slide.name}/{f.name}: {org or "no"} DimensionOrganizationType, skipped')
                continue
            cols = -(-int(ds.TotalPixelMatrixColumns) // int(ds.Columns))
            rows = -(-int(ds.TotalPixelMatrixRows) // int(ds.Rows))
            with open(f, 'rb') as fp:
                its = list(items(fp, pixel_items_start(ds, fp)))[1:]  # drop the Basic Offset Table item
                if len(its) != nframes or cols * rows != nframes:
                    print(f'{slide.name}/{f.name}: {len(its)} items, {nframes} frames, {cols}x{rows} grid: not one item per frame, skipped')
                    continue
                inst = {'file': f.name, 'sha256': sha256(f), 'sopInstanceUID': str(ds.SOPInstanceUID),
                        'transferSyntax': str(ds.file_meta.TransferSyntaxUID), 'photometric': ds.PhotometricInterpretation,
                        'bitsStored': int(ds.BitsStored), 'samplesPerPixel': int(ds.SamplesPerPixel),
                        'tileWidth': int(ds.Columns), 'tileHeight': int(ds.Rows),
                        'totalWidth': int(ds.TotalPixelMatrixColumns), 'totalHeight': int(ds.TotalPixelMatrixRows),
                        'frames': []}
                for col, row in sample_positions(cols, rows, seed=nframes):
                    idx = row * cols + col  # TILED_FULL, one path, one plane: row-major
                    off, n = its[idx]
                    fp.seek(off)
                    data = fp.read(n)
                    stem = f'{f.stem}_f{idx + 1}'
                    (out / f'{stem}.j2k').write_bytes(data)
                    ref = out / f'{stem}.ppm'
                    r = subprocess.run(['opj_decompress', '-quiet', '-i', str(out / f'{stem}.j2k'), '-o', str(ref)],
                                       capture_output=True, text=True)
                    inst['frames'].append({'frameNumber': idx + 1, 'col': col, 'row': row, 'offset': off, 'length': n,
                                           'sha256': hashlib.sha256(data).hexdigest(), 'codestream': f'{stem}.j2k',
                                           'opjReference': ref.name if r.returncode == 0 else None})
                manifest['instances'].append(inst)
                print(f'{slide.name}/{f.name}: {len(inst["frames"])} frames sampled ({cols}x{rows} grid)')
        manifest['opj_decompress'] = subprocess.run(['opj_decompress', '-h'], capture_output=True, text=True).stdout.splitlines()[0:3]
        (out / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')


if __name__ == '__main__':
    main()
