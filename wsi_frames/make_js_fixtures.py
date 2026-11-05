#!/usr/bin/env python3
"""Make the small, redistributable JPEG 2000 fixtures for @niivue/dcm2niix's frame-decoder tests.

  ict.j2k     one frame of CMU-1-JP2K-ICT-v2 (CC0): lossy 9/7, YBR_ICT, MCT
  rct.j2k     one frame of CMU-1-JP2K-RCT-v2 (CC0): lossless 5/3, YBR_RCT, MCT
  ybr422.j2k  synthetic: rct.j2k's RGB as full-range YCbCr (PS3.3 C.7.6.3.1.2), chroma
              averaged 2x1 (4:2:2), losslessly encoded with no MCT, as YBR_FULL_422 WSI
              frames are. Exercises upsampling and YCbCr conversion without the
              JP2K-33003-1 slide, whose licence is only "distributable".
Writes the files, plus expected.json (RGBA SHA-256 and sample pixels from the native
decode_frames harness, plus per-channel means), to <out>. Lossy (9/7) frames are marked:
their float decode may differ by 1 between WASM and native builds, so the browser test checks
them by sample pixels (within 1) and channel means (within 0.05; a double colour conversion
moves a mean by ~26), and lossless frames by SHA-256.

Usage: make_js_fixtures.py <frames_dir> <bin_dir> <out_dir>
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

from wsi_common import read_ppm


def tissue_frame(manifest_dir):
    """The first sampled level-0 frame whose opj reference is mostly not background."""
    m = json.loads((manifest_dir / 'manifest.json').read_text())
    inst = m['instances'][0]
    for fr in inst['frames']:
        ppm = (manifest_dir / fr['opjReference']).read_bytes()
        if np.frombuffer(ppm[-inst['tileWidth'] * inst['tileHeight'] * 3:], np.uint8).mean() < 215:
            return inst, fr
    raise SystemExit(f'no tissue frame in {manifest_dir}')


def decode(bin_dir, photometric, j2k):
    with tempfile.NamedTemporaryFile(suffix='.ppm') as t:
        subprocess.run([str(bin_dir / 'decode_frames'), photometric, str(j2k), t.name], check=True, capture_output=True)
        rgb = read_ppm(t.name)
    rgba = np.concatenate([rgb, np.full(rgb.shape[:2] + (1,), 255, np.uint8)], -1)
    return rgba


def main():
    frames_dir, bin_dir, out = (Path(a).resolve() for a in sys.argv[1:4])
    out.mkdir(parents=True, exist_ok=True)
    cases = {}
    for name, slide, photometric, lossy in [('ict', 'CMU-1-JP2K-ICT-v2', 'YBR_ICT', True), ('rct', 'CMU-1-JP2K-RCT-v2', 'YBR_RCT', False)]:
        inst, fr = tissue_frame(frames_dir / slide)
        (out / f'{name}.j2k').write_bytes((frames_dir / slide / fr['codestream']).read_bytes())
        cases[name] = {'photometric': photometric, 'source': f'{slide} {inst["file"]} frame {fr["frameNumber"]} (sha256 {inst["sha256"][:16]}...)'}
        if lossy:
            cases[name]['lossy'] = True
    rgb = decode(bin_dir, 'YBR_RCT', out / 'rct.j2k')[..., :3].astype(np.float64)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = -0.168736 * r - 0.331264 * g + 0.5 * b + 128
    cr = 0.5 * r - 0.418688 * g - 0.081312 * b + 128
    h, w = y.shape
    planes = [np.clip(np.rint(y), 0, 255).astype(np.uint8)]
    for c in (cb, cr):  # 4:2:2: average horizontal pairs
        planes.append(np.clip(np.rint((c[:, 0::2] + c[:, 1::2]) / 2), 0, 255).astype(np.uint8))
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / 'ybr422.raw'
        raw.write_bytes(b''.join(p.tobytes() for p in planes))
        subprocess.run(['opj_compress', '-i', str(raw), '-o', str(out / 'ybr422.j2k'), '-F', f'{w},{h},3,8,u@1x1:2x1:2x1', '-mct', '0'],
                       check=True, capture_output=True)
    cases['ybr422'] = {'photometric': 'YBR_FULL_422', 'source': 'synthetic from rct.j2k (see make_js_fixtures.py)'}
    for name, c in cases.items():
        rgba = decode(bin_dir, c['photometric'], out / f'{name}.j2k')
        c.update({'width': rgba.shape[1], 'height': rgba.shape[0], 'sha256': hashlib.sha256(rgba.tobytes()).hexdigest(),
                  'pixel0': rgba[0, 0].tolist(), 'pixelMid': rgba[rgba.shape[0] // 2, rgba.shape[1] // 2].tolist(),
                  'meanRGB': [round(float(m), 4) for m in rgba[..., :3].reshape(-1, 3).mean(0)]})
    (out / 'expected.json').write_text(json.dumps(cases, indent=1) + '\n')
    for name, c in cases.items():
        print(name, c['width'], c['height'], c['sha256'][:12], (out / f'{name}.j2k').stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
