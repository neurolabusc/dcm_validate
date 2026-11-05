"""Helpers shared by the wsi_frames scripts: encapsulated Pixel Data items and PPM files."""
from pathlib import Path

import numpy as np

ITEM, SEQ_END = 0xE000FFFE, 0xE0DDFFFE  # little-endian tag words (group FFFE)


def pixel_items_start(ds, fp):
    """File offset of the first (FFFE,E000) item of encapsulated Pixel Data."""
    pos = ds['PixelData'].file_tell
    fp.seek(pos)
    return pos if fp.read(4) == b'\xfe\xff\x00\xe0' else pos + 12


def items(fp, start):
    """Yield (payload_offset, length) for each encapsulated item from start."""
    fp.seek(start)
    while True:
        hdr = fp.read(8)
        if len(hdr) < 8:
            return
        tag = int.from_bytes(hdr[:4], 'little')
        n = int.from_bytes(hdr[4:], 'little')
        if tag == SEQ_END:
            return
        if tag != ITEM:
            raise ValueError(f'unexpected tag {tag:08x} at {fp.tell() - 8}')
        yield fp.tell(), n
        fp.seek(n, 1)


def read_ppm(path):
    data = Path(path).read_bytes()
    fields, pos = [], 0
    while len(fields) < 4:  # P6, width, height, maxval; '#' comments may sit between them
        while data[pos:pos + 1].isspace():
            pos += 1
        if data[pos:pos + 1] == b'#':
            pos = data.index(b'\n', pos) + 1
            continue
        end = pos
        while not data[end:end + 1].isspace():
            end += 1
        fields.append(data[pos:end])
        pos = end
    w, h = int(fields[1]), int(fields[2])
    pos += 1  # the single whitespace byte before the raster
    return np.frombuffer(data[pos:pos + w * h * 3], np.uint8).reshape(h, w, 3)
