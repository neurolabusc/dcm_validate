# Frame-decoder fixtures

JPEG 2000 and JPEG-LS codestreams (one DICOM-WSI frame each, item payload only) for dcm2niix's `createFrameDecoder` tests (`js/test/browser.mjs`, `consumer.mjs`; the test server finds this folder beside dcm2niix or via `DCM2NIIX_FRAMES`).

| File | Source | Licence | Exercises |
|---|---|---|---|
| `ict.j2k` | OpenSlide test data, `CMU-1-JP2K-ICT-v2` (DICOM conversion of CMU-1.svs), level 0 | CC0-1.0 | lossy 9/7, YBR_ICT, MCT applied by the codec |
| `rct.j2k` | OpenSlide test data, `CMU-1-JP2K-RCT-v2`, level 0 | CC0-1.0 | lossless 5/3, YBR_RCT, MCT applied by the codec |
| `ybr422.j2k` | synthetic, from `rct.j2k` | CC0-1.0 | YCbCr 4:2:2 (chroma dx=2) with no MCT, as YBR_FULL_422 WSI frames are |

`expected.json` holds each frame's RGBA SHA-256, sample pixels (`pixel0`, `pixelMid`) and channel means (`meanRGB`) from the native `decode_frames` harness (built unfused, see dcm2niix `docs/PARSER_GOTCHAS.md`). Lossless frames must match the SHA-256 exactly. Lossy 9/7 decodes in floating point and WASM OpenJPEG 2.5.3 differs from native 2.5.4 by up to 1, so `ict` (`"lossy": true`) is checked by its two sample pixels (within 1) and per-channel means (within 0.05; a double colour conversion moves a mean by about 26). The test also asserts `mct`/`isYCbCr`: ICT inverted by the codec and not converted again, 4:2:2 converted from YCbCr.

Never hand-edit these files: `../make_js_fixtures.py` regenerates all of them (requirements and order in its README) from the OpenSlide corpus (https://openslide.cs.cmu.edu/download/openslide-testdata/DICOM/). `ict.j2k` and `rct.j2k` are copied byte for byte; `ybr422.j2k` is re-encoded by `opj_compress` (Homebrew OpenJPEG 2.5.4), so another OpenJPEG may give different bytes. Frame numbers and source checksums are in `expected.json`.

## Monochrome, >8-bit and JPEG-LS (`samples.json`)

Synthetic 67×45 gradients (CC0-1.0), written by `../make_sample_fixtures.py`, which also writes `samples.json`; never hand-edit them. Expected values are computed from the source gradients, not from a decoder: `samplesSha256` is the `output: 'samples'` result (interleaved; uint8, or little-endian uint16 above 8 bits) and `rgbaSha256` the RGBA result under the entry's `photometric` and `bitsStored` (`round(v * 255 / (2^bits - 1))`, MONOCHROME1 inverted). Entries may share a file under another photometric.

| Files | Encoder | Exercises |
|---|---|---|
| `j2k_mono{8,12,16}.j2k` | `opj_compress`, lossless 5/3 | monochrome precisions; `j2k_mono12_m1` reads the 12-bit file as MONOCHROME1 |
| `j2k_rgb16.j2k` | `opj_compress` (RCT) | 16-bit RGB with MCT |
| `jls_mono{8,12,16}.jls` | DCMTK `dcmcjpls`, lossless | JPEG-LS monochrome; DCMTK codes the 12-bit file at 16-bit precision, so its RGBA needs `bitsStored: 12` |
| `jls_rgb16_line.jls`, `jls_rgb8_sample.jls` | `dcmcjpls +il` / `+is` | line and sample interleave (decoded as RGB triplets); `jls_ybr8_sample` reads the 8-bit file as YBR_FULL |
| `jls_rgb12_planar.jls` | `../encode_jls` | interleave mode None (planar), which `dcmcjpls` cannot write; 12-bit because that encoder writes invalid 15–16-bit planar streams |
| `jls_mono12_near.jls` + `.src` | `dcmcjpls +en +md 2` | near-lossless: hashes from the native decoder (JS compares WASM with native); `check_samples.py` checks them within `near` (2) of `.src` |
| `j2k_signed16.j2k` | `opj_compress -F …,s` | refused as `unsupported-signed` |
