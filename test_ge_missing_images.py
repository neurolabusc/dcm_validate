"""Check GE missing-image diagnostics using temporary copies of R2MB2 DICOMs."""
from copy import deepcopy
import subprocess
import sys
import tempfile
from pathlib import Path

import pydicom

binary = Path(sys.argv[1]).resolve()
source = Path(__file__).parent / 'dcm_qa_ge/In/04_Ax_DWI_TENSOR_R2MB2'
images = [pydicom.dcmread(p) for p in source.iterdir() if p.is_file() and not p.name.startswith('.')]
images.sort(key=lambda d: int(d.InstanceNumber))
assert len(images) == 63

cases = [
    ('both', 23, 'expected 63 slices with 9 spatial positions but found 23.'),
    ('total', 23, 'expected 63 slices but found 23.'),
    ('total_volumes', 54, 'expected 63 slices but found 54.'),
    ('spatial', 23, 'expected 9 spatial positions per volume but found 23 slices.'),
    ('zip', 17, 'expected 18 spatial positions per volume but found 17 slices.'),
    ('complete', 63, None),
]
for name, count, expected in cases:
    with tempfile.TemporaryDirectory(prefix='ge-missing-') as tmp:
        indir, outdir = Path(tmp) / 'in', Path(tmp) / 'out'
        indir.mkdir()
        outdir.mkdir()
        for i, original in enumerate(images[:count]):
            d = deepcopy(original)
            if name.startswith('total'):
                del d[0x0021104F]
                d.SoftwareVersions = ['30', 'LX', 'MR30']
            elif name == 'spatial':
                d.ImagesInAcquisition = 9
            elif name == 'zip':
                d.ImagesInAcquisition = 18
                d.SliceThickness = 2 * float(d.SpacingBetweenSlices)
            d.save_as(indir / f'{i}.dcm')
        run = subprocess.run([str(binary), '-b', 'n', '-z', 'n', '-o', str(outdir), str(indir)], capture_output=True, text=True)
        output = run.stdout + run.stderr
        if expected:
            assert 'There appear to be missing DICOM images, ' + expected in output, (name, output)
            assert 'spatial locations' not in output and output.count('missing DICOM images') == 1, (name, output)
        else:
            assert run.returncode == 0, output
            assert 'missing DICOM images' not in output and 'DICOM images may be missing' not in output, output
        print(f'PASS: {name}')
