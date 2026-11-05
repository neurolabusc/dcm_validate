#!/usr/bin/env python3
"""Check dcm2niix's tile decoder (nii_decodeFrameRGBA) on sampled WSI frames.

For each frame in <frames_dir>/<slide>/manifest.json (from sample_frames.py):
  1. decode_frames (dcm2niix)  -> RGB under test
  2. dump_components (OpenJPEG raw planes) + numpy here -> independent reference:
     chroma repeated to full size; if the codestream has no MCT and the photometric is
     YBR_FULL/YBR_FULL_422/YBR_ICT (or chroma is subsampled), YCbCr -> RGB with the
     DICOM PS3.3 C.7.6.3.1.2 coefficients, rounded half up as dcm2niix's nii_ybr2rgb does
     (the contract under test); with MCT, OpenJPEG's output is already RGB.
     Expect an exact match.
  3. opj_decompress's own PPM (its sYCC conversion truncates and uses 0.344/0.714):
     reported as max difference only, a cross-check rather than the contract.

Usage: check_frames.py <bin_dir> <frames_dir> [<slide> ...]
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from wsi_common import read_ppm


def reference(bin_dir, j2k, photometric):
    with tempfile.NamedTemporaryFile(suffix='.bin') as t:
        subprocess.run([str(bin_dir / 'dump_components'), str(j2k), t.name], check=True)
        raw = Path(t.name).read_bytes()
    lines = raw.split(b'\n')
    n, mct, cs = map(int, lines[0].split())
    comps = [tuple(map(int, lines[1 + k].split())) for k in range(n)]
    off = sum(len(lines[i]) + 1 for i in range(n + 1))
    planes = []
    for w, h, dx, dy, prec, sgnd in comps:
        planes.append(np.frombuffer(raw[off:off + w * h * 4], '<i4').reshape(h, w))
        off += w * h * 4
    h0, w0 = planes[0].shape
    full = [np.repeat(np.repeat(p, c[3], 0), c[2], 1)[:h0, :w0] for p, c in zip(planes, comps)]
    sub = any(c[2] > 1 or c[3] > 1 for c in comps[1:])
    if n == 1:
        g = full[0].astype(np.float64) * (255 / ((1 << comps[0][4]) - 1)) if comps[0][4] != 8 else full[0]
        g = np.clip(g, 0, 255).astype(np.int64)
        if photometric.startswith('MONOCHROME1'):
            g = 255 - g
        return np.stack([g, g, g], -1).astype(np.uint8), mct
    y, cb, cr = (p.astype(np.float32) for p in full)
    ycc = mct == 0 and (sub or cs == 3 or photometric.startswith('YBR_FULL') or photometric.startswith('YBR_ICT'))
    if not ycc:
        return np.clip(np.stack(full, -1), 0, 255).astype(np.uint8), mct
    r = y + np.float32(1.402) * (cr - 128)
    g = y - np.float32(0.344136) * (cb - 128) - np.float32(0.714136) * (cr - 128)
    b = y + np.float32(1.772) * (cb - 128)
    rgb = [np.clip(np.trunc(v + np.float32(0.5)), 0, 255) for v in (r, g, b)]
    return np.stack(rgb, -1).astype(np.uint8), mct


def main():
    bin_dir, frames_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
    slides = sys.argv[3:] or sorted(p.name for p in frames_dir.iterdir() if (p / 'manifest.json').exists())
    failures = 0
    for slide in slides:
        m = json.loads((frames_dir / slide / 'manifest.json').read_text())
        for inst in m['instances']:
            pi = inst['photometric']
            exact = opj_max = 0
            for fr in inst['frames']:
                j2k = frames_dir / slide / fr['codestream']
                with tempfile.NamedTemporaryFile(suffix='.ppm') as t:
                    r = subprocess.run([str(bin_dir / 'decode_frames'), pi, str(j2k), t.name], capture_output=True, text=True)
                    status = r.stdout.split()
                    if r.returncode or status[1] != '0':
                        print(f'  FAIL {slide}/{fr["codestream"]}: {r.stdout.strip()} {r.stderr.strip()}')
                        failures += 1
                        continue
                    got = read_ppm(t.name)
                ref, mct = reference(bin_dir, j2k, pi)
                if got.shape != ref.shape or not np.array_equal(got, ref):
                    d = np.abs(got.astype(int) - ref.astype(int)).max() if got.shape == ref.shape else 'shape'
                    print(f'  MISMATCH {slide}/{fr["codestream"]}: max diff {d}')
                    failures += 1
                else:
                    exact += 1
                if fr.get('opjReference'):
                    opj = read_ppm(frames_dir / slide / fr['opjReference'])
                    if opj.shape == got.shape:
                        opj_max = max(opj_max, int(np.abs(opj.astype(int) - got.astype(int)).max()))
            print(f'{slide}/{inst["file"]} {pi} mct={mct}: {exact}/{len(inst["frames"])} exact vs independent reference; '
                  f'max |diff| vs opj_decompress {opj_max}')
    print('FAILED' if failures else 'OK', failures)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
