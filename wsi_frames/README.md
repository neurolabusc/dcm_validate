# wsi_frames

Regression harness for dcm2niix's DICOM-WSI tile decoders, `nii_decodeFrameRGBA` and `nii_decodeFrame` (`console/nii_dicom.cpp`), which back `createFrameDecoder` in `@niivue/dcm2niix`. It samples JPEG 2000 frames from real slides and checks dcm2niix's RGB against an independent reference built from OpenJPEG's raw component planes plus the DICOM PS3.3 C.7.6.3.1.2 YCbCr equations (exact match required). `opj_decompress` output is reported as a cross-check only (its sYCC conversion truncates and uses other coefficients).

## Requirements

- Python 3 with `pydicom` and `numpy`.
- OpenJPEG: `opj_decompress` (references) and `opj_compress` (synthetic fixtures), plus the library and headers, e.g. `brew install openjpeg`. DCMTK `dcmcjpls` and CharLS 2.4 for the JPEG-LS fixtures (`brew install dcmtk charls`).
- Native helpers, built here (in bash) from a dcm2niix checkout (`D`) and OpenJPEG prefix (`O`), with JPEG-LS (CharLS) as in the WASM build:

```bash
D=../../dcm2niix/console O=$(brew --prefix openjpeg)
CHARLS="$D/charls/jpegls.cpp $D/charls/jpegmarkersegment.cpp $D/charls/interface.cpp $D/charls/jpegstreamwriter.cpp $D/charls/jpegstreamreader.cpp"
c++ -O2 -ffp-contract=off -std=c++14 -DUSE_OPENJPEG -DmyEnableJPEGLS -I$D -I$O/include/openjpeg-2.5 decode_frames.cpp $D/nii_dicom.cpp $D/jpg_0XC3.cpp $D/ujpeg.cpp $D/nifti1_io_core.cpp $D/dicom_fragments.cpp $CHARLS -L$O/lib -lopenjp2 -lz -o decode_frames
cc -O2 -I$O/include/openjpeg-2.5 dump_components.c -L$O/lib -lopenjp2 -o dump_components
c++ -O2 -std=c++14 -DCHARLS_NO_DEPRECATED_WARNING encode_jls.cpp $(pkg-config --cflags --libs charls) -o encode_jls  # use the installed CharLS encoder
```

`bench_frames.cpp` (same build line as `decode_frames`) times either decoder: `bench_frames <rgba|samples> <reps> <photometric> <in> ...`. Compile it with `-DBENCH_RGBA_ONLY` against a dcm2niix older than the samples decoder to get the before numbers.

`decode_frames [--samples] [--bits <bitsStored>] <photometric> <in> <out> ...` runs `nii_decodeFrameRGBA` (writing PPM) or, with `--samples`, `nii_decodeFrame` (writing the raw samples), and prints `file status width height components bits mct isYCbCr`. `encode_jls` writes JPEG-LS with any interleave mode through CharLS, for the planar fixture `dcmcjpls` cannot make. `dump_components <in.j2k> <out.bin>` writes the decoded planes with no colour handling. `-ffp-contract=off` is required: the decoder's contract is the unfused WASM arithmetic (`docs/PARSER_GOTCHAS.md` in dcm2niix).

## Corpus

OpenSlide DICOM test data (https://openslide.cs.cmu.edu/download/openslide-testdata/DICOM/, licences in its `index.yaml`), unzipped at `/Volumes/TB5/DICOM-wsi` (not in any repo). The JPEG 2000 slides are `CMU-1-JP2K-33005-v2` and `CMU-1-JP2K-ICT-v2` (YBR_ICT), `CMU-1-JP2K-RCT-v2` (YBR_RCT), and `JP2K-33003-1-v2` (YBR_FULL_422, chroma dx=2, no MCT; licence "distributable", so not used for checked-in fixtures). Sampled frames live in `/Volumes/TB5/DICOM-wsi/_frames`.

## Workflow

```bash
W=/Volumes/TB5/DICOM-wsi
python3 inspect_wsi.py $W/*-v2                           # geometry, transfer syntax, photometric, MCT/wavelet/subsampling per instance
python3 sample_frames.py $W/_frames $W/*JP2K*-v2         # 25 frames per instance (corners, edges, centre, seeded random) + opj references + manifest.json
python3 check_frames.py . $W/_frames                     # dcm2niix vs independent reference; exits 1 on any mismatch
python3 make_js_fixtures.py $W/_frames . fixtures        # ict/rct/ybr422 .j2k and expected.json for the JS browser tests
python3 make_sample_fixtures.py . fixtures               # synthetic monochrome/>8-bit/JPEG-LS frames and samples.json (no corpus needed)
python3 check_samples.py . fixtures                      # samples and RGBA vs values computed from the sources; exits 1 on any mismatch
```

`sample_frames.py` handles TILED_FULL with one item per frame only and skips anything else. `check_frames.py` takes the directory holding the two helpers first.

After any change to the frame decoders or the J2K/JPEG-LS paths: rebuild `decode_frames` (above), run `check_frames.py` and `check_samples.py`, rerun `make_js_fixtures.py` if the output may change (then review the `expected.json` diff), rebuild the WASM (`pixi run wasm` in dcm2niix), and run `cd js && npm test`.

## OpenSlide is not a colour reference

OpenSlide 4.0.0 refuses YBR_FULL_422 JPEG 2000 and YBR_RCT, and converts YBR_ICT slides to RGB a second time after OpenJPEG has already inverted the MCT, rendering them magenta. Compare against the raw-plane reference here, not OpenSlide.
