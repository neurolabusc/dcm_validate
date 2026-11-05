#!/usr/bin/env python3
"""Check dcm2niix's frame decoders on the synthetic fixtures from make_sample_fixtures.py.

For each entry in <fixtures_dir>/samples.json, runs decode_frames twice: --samples
(nii_decodeFrame) and RGBA (nii_decodeFrameRGBA, with the entry's bitsStored as the hint),
and compares SHA-256 with the expected values. Near-lossless entries are checked against
their source samples within `near`; `status` entries must fail with that status.
Exits 1 on any mismatch.

Usage: check_samples.py <bin_dir> <fixtures_dir>
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

STATUS = ['ok', 'decode-error', 'unsupported-precision', 'unsupported-components', 'unsupported-subsampling', 'unsupported-photometric', 'unsupported-signed', 'too-large']


def decode(binary, args, src, out):
    r = subprocess.run([str(binary), *args, str(src), str(out)], capture_output=True, text=True)
    fields = r.stdout.split()
    return STATUS[int(fields[1])], fields


def rgba_from_ppm(path):
    data = Path(path).read_bytes()
    rgb = np.frombuffer(data[data.index(b'255\n') + 4:], 'u1').reshape(-1, 3)
    return np.concatenate([rgb, np.full((len(rgb), 1), 255, 'u1')], 1)


def main():
    binary = Path(sys.argv[1]).resolve() / 'decode_frames'
    fixtures = Path(sys.argv[2]).resolve()
    entries = json.loads((fixtures / 'samples.json').read_text())
    bad = 0
    with tempfile.TemporaryDirectory() as t:
        out = Path(t) / 'out'
        for name, e in entries.items():
            src = fixtures / e['file']
            status, fields = decode(binary, ['--samples', e['photometric']], src, out)
            want = e.get('status', 'ok')
            if status != want:
                print(f'{name}: samples status {status}, expected {want}')
                bad += 1
                continue
            if want != 'ok':
                rs, _ = decode(binary, ['--bits', str(e['bitsStored']), e['photometric']], src, out)
                ok = rs == want
                print(f'{name}: {"ok" if ok else "FAIL"} (refused: {want})')
                bad += not ok
                continue
            got = out.read_bytes()
            if 'near' in e:
                a = np.frombuffer(got, '<u2' if e['bitsStored'] > 8 else 'u1').astype(int)
                ref = np.frombuffer((fixtures / e['source']).read_bytes(), '<u2' if e['bitsStored'] > 8 else 'u1').astype(int)
                err = int(np.abs(a - ref).max())
                ok = a.shape == ref.shape and err <= e['near']
                print(f'{name}: {"ok" if ok else "FAIL"} (samples max |error| {err} <= {e["near"]})')
                bad += not ok
                continue
            ok_s = hashlib.sha256(got).hexdigest() == e['samplesSha256']
            decode(binary, ['--bits', str(e['bitsStored']), e['photometric']], src, out)
            ok_r = hashlib.sha256(rgba_from_ppm(out).tobytes()).hexdigest() == e['rgbaSha256']
            print(f'{name}: samples {"ok" if ok_s else "FAIL"}, rgba {"ok" if ok_r else "FAIL"} (codestream bits {fields[5]})')
            bad += (not ok_s) + (not ok_r)
    print('OK' if not bad else f'FAILED {bad}')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
