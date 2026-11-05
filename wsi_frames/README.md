# wsi_frames

Regression harness for dcm2niix's DICOM-WSI tile decoder, `nii_decodeFrameRGBA` (`console/nii_dicom.cpp`), which backs `createFrameDecoder` in `@niivue/dcm2niix`. It samples JPEG 2000 frames from real slides and checks dcm2niix's RGB against an independent reference built from OpenJPEG's raw component planes plus the DICOM PS3.3 C.7.6.3.1.2 YCbCr equations (exact match required). `opj_decompress` output is reported as a cross-check only (its sYCC conversion truncates and uses other coefficients).

## Requirements

- Python 3 with `pydicom` and `numpy`.
- OpenJPEG: `opj_decompress` (references) and `opj_compress` (synthetic 4:2:2 fixture), plus the library and headers, e.g. `brew install openjpeg`.
- Two native helpers, built here from a dcm2niix checkout (`D`) and OpenJPEG prefix (`O`):

```bash
D=../../dcm2niix/console O=$(brew --prefix openjpeg)
c++ -O2 -ffp-contract=off -std=c++14 -DUSE_OPENJPEG -I$D -I$O/include/openjpeg-2.5 decode_frames.cpp $D/nii_dicom.cpp $D/jpg_0XC3.cpp $D/ujpeg.cpp $D/nifti1_io_core.cpp $D/dicom_fragments.cpp -L$O/lib -lopenjp2 -lz -o decode_frames
cc -O2 -I$O/include/openjpeg-2.5 dump_components.c -L$O/lib -lopenjp2 -o dump_components
```

`decode_frames <photometric> <in.j2k> <out.ppm> ...` runs `nii_decodeFrameRGBA` and prints `file status width height components bits mct isYCbCr`. `dump_components <in.j2k> <out.bin>` writes the decoded planes with no colour handling. `-ffp-contract=off` is required: the decoder's contract is the unfused WASM arithmetic (`docs/PARSER_GOTCHAS.md` in dcm2niix).

## Corpus

OpenSlide DICOM test data (https://openslide.cs.cmu.edu/download/openslide-testdata/DICOM/, licences in its `index.yaml`), unzipped at `/Volumes/TB5/DICOM-wsi` (not in any repo). The JPEG 2000 slides are `CMU-1-JP2K-33005-v2` and `CMU-1-JP2K-ICT-v2` (YBR_ICT), `CMU-1-JP2K-RCT-v2` (YBR_RCT), and `JP2K-33003-1-v2` (YBR_FULL_422, chroma dx=2, no MCT; licence "distributable", so not used for checked-in fixtures). Sampled frames live in `/Volumes/TB5/DICOM-wsi/_frames`.

## Workflow

```bash
W=/Volumes/TB5/DICOM-wsi
python3 inspect_wsi.py $W/*-v2                           # geometry, transfer syntax, photometric, MCT/wavelet/subsampling per instance
python3 sample_frames.py $W/_frames $W/*JP2K*-v2         # 25 frames per instance (corners, edges, centre, seeded random) + opj references + manifest.json
python3 check_frames.py . $W/_frames                     # dcm2niix vs independent reference; exits 1 on any mismatch
python3 make_js_fixtures.py $W/_frames . ../../dcm2niix/js/test/frames   # ict/rct/ybr422 .j2k and expected.json for the JS browser tests
```

`sample_frames.py` handles TILED_FULL with one item per frame only and skips anything else. `check_frames.py` takes the directory holding the two helpers first.

After any change to `nii_decodeFrameRGBA` or the J2K path: rebuild `decode_frames` (above), run `check_frames.py`, rerun `make_js_fixtures.py` if the output may change (then review the `expected.json` diff), rebuild the WASM (`pixi run wasm` in dcm2niix), and run `cd js && npm test`.

## OpenSlide is not a colour reference

OpenSlide 4.0.0 refuses YBR_FULL_422 JPEG 2000 and YBR_RCT, and converts YBR_ICT slides to RGB a second time after OpenJPEG has already inverted the MCT, rendering them magenta. Compare against the raw-plane reference here, not OpenSlide.
