"""JPEG lossless, JPEG 2000 and JPEG-LS frames whose DICOM Rows/Columns/BitsAllocated disagree with the codestream must fail cleanly, with no image output. Needs pydicom >= 3 (generate_frames number_of_frames)."""
import subprocess
import sys
import tempfile
from pathlib import Path

import pydicom
from pydicom.encaps import encapsulate, generate_frames

binary = Path(sys.argv[1]).resolve()


def first_frame_only(d):
    # one codestream left, header still claims every frame: the decoder output cannot fill the image
    d.PixelData = encapsulate([next(generate_frames(d.PixelData, number_of_frames=int(d.NumberOfFrames)))], has_bot=False)


def mosaic_frames(d):
    # Siemens mosaic stored as 3 frames: each frame is demosaiced, so it no longer fits the per-frame slot
    frame = next(generate_frames(d.PixelData, number_of_frames=1))
    d.NumberOfFrames = 3
    d.PixelData = encapsulate([frame] * 3, has_bot=False)


root = Path(__file__).parent
cases = [
    # (name, source, edits, path exercised)
    ('c3_single_taller', 'dcm_qa_jpg/In/cid0/image.dcm', {'Rows': 33}, 'JPEG lossless single frame'),
    ('c3_single_same_bytes', 'dcm_qa_jpg/In/cid0/image.dcm', {'Rows': 16, 'Columns': 64}, 'JPEG lossless shape mismatch, equal byte count'),
    ('c3_single_8bit', 'dcm_qa_jpg/In/cid0/image.dcm', {'BitsAllocated': 8, 'BitsStored': 8, 'HighBit': 7}, 'JPEG lossless sample size'),
    ('c3_stack', 'dcm_qa_jpg/In/dcmtk_lossless_rgb/0001_1.3.12.2.1107.5.2.43.67093.2022071112123439621008676.dcm', {'Rows': 73}, 'JPEG lossless multi-frame, one item per frame'),
    ('c3_fragments', 'dcm_qa_jpg/In/dcmtk_fragments_fmap/0001_1.3.12.2.1107.5.2.43.67093.2022071112105821698004979.dcm', {'Rows': 65}, 'JPEG lossless multi-frame, several items per frame'),
    ('j2k_single', 'dcm_qa_ts/In/9.dcm', {'Rows': 385}, 'JPEG 2000 single frame'),
    ('j2k_frames', 'dcm_qa_enh_compressed/In/j2k/philips_asl.dcm', {'Rows': 81}, 'JPEG 2000 multi-frame loop'),
    ('jls_single', 'dcm_qa_ts/In/8.dcm', {'Rows': 385}, 'JPEG-LS single frame'),
    ('jls_frames', 'dcm_qa_enh_compressed/In/jpegls/philips_asl.dcm', {'Rows': 81}, 'JPEG-LS multi-frame loop'),
    ('j2k_one_codestream', 'dcm_qa_enh_compressed/In/j2k/philips_asl.dcm', first_frame_only, 'JPEG 2000 multi-frame header, one codestream'),
    ('jls_one_codestream', 'dcm_qa_enh_compressed/In/jpegls/philips_asl.dcm', first_frame_only, 'JPEG-LS multi-frame header, one codestream'),
    ('jls_mosaic_frames', 'dcm_qa_ts/In/8.dcm', mosaic_frames, 'JPEG-LS mosaic split into frames'),
    ('b50_one_codestream', 'dcm_qa_jpg/In/dcmtk_baseline_fmap/0001_1.3.12.2.1107.5.2.43.67093.2022071112105821698004979.dcm', first_frame_only, 'baseline JPEG multi-frame header, one codestream'),
]
failed = 0
for name, source, edits, path in cases:
    for control in (True, False):
        with tempfile.TemporaryDirectory(prefix='jpeg-mismatch-') as tmp:
            indir, outdir = Path(tmp) / 'in', Path(tmp) / 'out'
            indir.mkdir()
            outdir.mkdir()
            d = pydicom.dcmread(root / source)
            if not control:
                if callable(edits):
                    edits(d)
                else:
                    for key, value in edits.items():
                        setattr(d, key, value)
            d.save_as(indir / 'image.dcm')
            run = subprocess.run([str(binary), '-z', 'n', '-o', str(outdir), str(indir)], capture_output=True, text=True)
            output = run.stdout + run.stderr
            images = list(outdir.glob('*.nii'))
            sidecars = list(outdir.glob('*.json'))
            if control:
                ok = run.returncode == 0 and len(images) > 0
            else:
                ok = run.returncode not in (0, -6, -11) and 'Sanitizer' not in output and not images and not sidecars and any(m in output for m in ('does not match DICOM', 'holds one frame', 'decodes to'))
            label = f"{name}{' (control)' if control else ''}"
            print(f"{'PASS' if ok else 'FAIL'}: {label}: {path}")
            if not ok:
                failed += 1
                print(f'  exit {run.returncode}; images {[p.name for p in images]}; sidecars {[p.name for p in sidecars]}\n  ' + output.strip().replace('\n', '\n  '))
sys.exit(1 if failed else 0)
