#!/usr/bin/env python3
"""Synthetic monochrome / >8-bit / JPEG-LS frames for dcm2niix's frame decoders.

Writes small codestreams (one DICOM-WSI frame each) plus samples.json to <out_dir>
(wsi_frames/fixtures, read by dcm2niix's js tests). Expected values come from the source gradients, never from
the decoder under test:
  samplesSha256  nii_decodeFrame output (lossless: the source samples, interleaved, uint8 or
                 little-endian uint16; 8-bit YBR_FULL: converted to RGB)
  rgbaSha256     nii_decodeFrameRGBA output: round(v * 255 / (2^bits - 1)) per component,
                 MONOCHROME1 inverted, alpha 255 (the D9 fixed mapping)
Near-lossless entries also carry `near` and the source samples (<name>.src); their hashes come from
the native ./decode_frames (checked within `near` here), so the JS tests compare WASM with native.

Encoders: opj_compress (JPEG 2000, lossless 5/3, RCT on for RGB), DCMTK dcmcjpls (JPEG-LS
line/sample interleave, near-lossless) and ./encode_jls (CharLS, planar RGB, which
dcmcjpls cannot write; 12-bit, as that encoder writes invalid 15-16-bit planar streams). Needs numpy and pydicom >= 3.

Usage: make_sample_fixtures.py <bin_dir> <out_dir>
"""
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.encaps import generate_frames
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

H, W = 45, 67  # odd sizes exercise edges


def gradient(bits, comps):
    """0 at the top left, the maximum at the bottom right; a scrambled third channel."""
    m = (1 << bits) - 1
    y, x = np.mgrid[0:H, 0:W]
    g = np.round((x / (W - 1) * 0.6 + y / (H - 1) * 0.4) * m).astype(np.int64)
    if comps == 1:
        return g[..., None]
    return np.stack([g, m - g, (x * 997 + y * 31) % (m + 1)], -1)


def store(a, bits):
    return a.astype('<u2' if bits > 8 else 'u1')


def rgba(a, bits, mono1=False):
    m = (1 << bits) - 1
    v = (a * 255 + m // 2) // m
    if mono1:
        v = 255 - v
    if v.shape[-1] == 1:
        v = np.repeat(v, 3, -1)
    return np.concatenate([v, np.full(v.shape[:-1] + (1,), 255)], -1).astype('u1')


def ybr2rgb(a):  # nii_ybr2rgb: float32 BT.601 full range, rounded half up
    y, cb, cr = (a[..., k].astype(np.float32) for k in range(3))
    r = y + np.float32(1.402) * (cr - 128)
    g = y - np.float32(0.344136) * (cb - 128) - np.float32(0.714136) * (cr - 128)
    b = y + np.float32(1.772) * (cb - 128)
    return np.stack([np.clip(np.trunc(v + np.float32(0.5)), 0, 255) for v in (r, g, b)], -1).astype(np.int64)


def sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()


def opj(a, bits, out, tmp):
    comps = a.shape[-1]
    pnm = tmp / ('in.pgm' if comps == 1 else 'in.ppm')
    hdr = f"{'P5' if comps == 1 else 'P6'}\n{W} {H}\n{(1 << bits) - 1}\n".encode()
    pnm.write_bytes(hdr + a.astype('>u2' if bits > 8 else 'u1').tobytes())
    subprocess.run(['opj_compress', '-i', str(pnm), '-o', str(out)], check=True, capture_output=True)


def opj_signed(out, tmp):
    raw = tmp / 'in.rawl'
    y, x = np.mgrid[0:H, 0:W]
    raw.write_bytes(((x - y) * 100).astype('<i2').tobytes())
    subprocess.run(['opj_compress', '-i', str(raw), '-o', str(out), '-F', f'{W},{H},1,16,s'], check=True, capture_output=True)


def dcmcjpls(a, bits, out, tmp, photometric, flags):
    ds = Dataset()
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.7'
    ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()
    ds.SOPClassUID, ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPClassUID, ds.file_meta.MediaStorageSOPInstanceUID
    ds.Rows, ds.Columns, ds.SamplesPerPixel = H, W, a.shape[-1]
    ds.PhotometricInterpretation = photometric
    if a.shape[-1] == 3:
        ds.PlanarConfiguration = 0
    ds.BitsAllocated = 16 if bits > 8 else 8
    ds.BitsStored, ds.HighBit, ds.PixelRepresentation = bits, bits - 1, 0
    ds.PixelData = store(a, bits).tobytes()
    src, dst = tmp / 'in.dcm', tmp / 'out.dcm'
    ds.save_as(src, enforce_file_format=True)
    subprocess.run(['dcmcjpls', *flags, str(src), str(dst)], check=True, capture_output=True)
    out.write_bytes(next(generate_frames(pydicom.dcmread(dst).PixelData, number_of_frames=1)))


def charls_planar(a, bits, out, tmp, bin_dir):
    raw = tmp / 'in.raw'
    raw.write_bytes(store(np.moveaxis(a, -1, 0), bits).tobytes())  # planar: RRR GGG BBB
    subprocess.run([str(bin_dir / 'encode_jls'), str(W), str(H), '3', str(bits), '0', '0', str(raw), str(out)], check=True)


def main():
    bin_dir, out_dir = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    entries = {}
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)

        def add(name, file, a, bits, photometric, **extra):
            e = {'file': file, 'photometric': photometric, 'width': W, 'height': H, 'components': a.shape[-1], 'bitsStored': bits}
            e.update(extra)
            if 'near' not in e and 'status' not in e:
                ybr = photometric.startswith('YBR_FULL')
                rgb = ybr2rgb(a) if ybr else a
                e['samplesSha256'] = sha(store(rgb, bits))
                e['rgbaSha256'] = sha(rgba(rgb, bits, photometric == 'MONOCHROME1'))
            entries[name] = e

        for bits in (8, 12, 16):
            a = gradient(bits, 1)
            opj(a, bits, out_dir / f'j2k_mono{bits}.j2k', tmp)
            add(f'j2k_mono{bits}', f'j2k_mono{bits}.j2k', a, bits, 'MONOCHROME2')
            dcmcjpls(a, bits, out_dir / f'jls_mono{bits}.jls', tmp, 'MONOCHROME2', [])
            add(f'jls_mono{bits}', f'jls_mono{bits}.jls', a, bits, 'MONOCHROME2')
        add('j2k_mono12_m1', 'j2k_mono12.j2k', gradient(12, 1), 12, 'MONOCHROME1')
        add('jls_mono16_m1', 'jls_mono16.jls', gradient(16, 1), 16, 'MONOCHROME1')
        a = gradient(16, 3)
        opj(a, 16, out_dir / 'j2k_rgb16.j2k', tmp)
        add('j2k_rgb16', 'j2k_rgb16.j2k', a, 16, 'RGB')
        dcmcjpls(a, 16, out_dir / 'jls_rgb16_line.jls', tmp, 'RGB', ['+il'])
        add('jls_rgb16_line', 'jls_rgb16_line.jls', a, 16, 'RGB')
        a = gradient(12, 3)  # the vendored CharLS encoder writes invalid 15-16-bit planar streams
        charls_planar(a, 12, out_dir / 'jls_rgb12_planar.jls', tmp, bin_dir)
        add('jls_rgb12_planar', 'jls_rgb12_planar.jls', a, 12, 'RGB')
        a = gradient(8, 3)
        dcmcjpls(a, 8, out_dir / 'jls_rgb8_sample.jls', tmp, 'RGB', ['+is'])
        add('jls_rgb8_sample', 'jls_rgb8_sample.jls', a, 8, 'RGB')
        add('jls_ybr8_sample', 'jls_rgb8_sample.jls', a, 8, 'YBR_FULL')  # same bytes, read as YCbCr
        a = gradient(12, 1)
        dcmcjpls(a, 12, out_dir / 'jls_mono12_near.jls', tmp, 'MONOCHROME2', ['+en', '+md', '2'])
        (out_dir / 'jls_mono12_near.src').write_bytes(store(a, 12).tobytes())
        add('jls_mono12_near', 'jls_mono12_near.jls', a, 12, 'MONOCHROME2', near=2, source='jls_mono12_near.src')
        dec = tmp / 'near.raw'
        subprocess.run([str(bin_dir / 'decode_frames'), '--samples', 'MONOCHROME2', str(out_dir / 'jls_mono12_near.jls'), str(dec)], check=True, capture_output=True)
        d = np.frombuffer(dec.read_bytes(), '<u2').astype(np.int64).reshape(a.shape)
        assert np.abs(d - a).max() <= 2, 'near-lossless decode outside NEAR'
        entries['jls_mono12_near'].update(samplesSha256=sha(store(d, 12)), rgbaSha256=sha(rgba(d, 12)))
        opj_signed(out_dir / 'j2k_signed16.j2k', tmp)
        add('j2k_signed16', 'j2k_signed16.j2k', gradient(16, 1), 16, 'MONOCHROME2', status='unsupported-signed')
    (out_dir / 'samples.json').write_text(json.dumps(entries, indent=1) + '\n')
    print(f'{len(entries)} entries -> {out_dir / "samples.json"}')


if __name__ == '__main__':
    main()
