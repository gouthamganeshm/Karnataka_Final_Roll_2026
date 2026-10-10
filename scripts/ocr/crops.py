"""Split roll_ocr into a cut stage and an OCR stage, joined by a crop bundle.

Why this exists: the ECI CDN only serves home/residential connections, so the
PDFs have to be fetched at home — but Tesseract is ~65% of the per-part cost and
is the reason a statewide pass took a week on one machine. So the home machine
does only the cheap half (fetch, cut each card's serial box and EPIC to ink) and
ships those crops; GitHub Actions does the expensive half (contact sheets,
Tesseract, serial fitting) in parallel.

The crops are the *exact* images `read_page_raw` would have fed to Tesseract, so
the OCR stage reproduces `roll_ocr.read_part_bytes` row for row. That is the
property `test_crops.py` checks, and the reason crops are stored as lossless
grayscale PNG: a bilevel or JPEG-recompressed crop would change what Tesseract
sees and silently change readings.

Bundle = one uncompressed zip per part (PNGs are already compressed):

    index.json                  {"ac":..,"part":..,"pages":[[n_cells, [cells with a crop]], ...]}
    p000/c00e.png  p000/c00s.png   epic / serial crop for page 0, cell 0
"""
from __future__ import annotations

import io
import json
import os
import zipfile

import numpy as np
from PIL import Image

import roll_ocr as R

Page = tuple[list, list]          # (epic_crops, serial_crops), None = empty cell


# ---------------------------------------------------------------- cut (home)

def page_images(doc):
    """Each page's single full-page JPEG, decoded directly.

    roll_ocr's `_pages` re-encodes every page to PNG and decodes it again, which
    measured 16.6s of a part's 26s of non-OCR time. Lifting the JPEG bytes out
    is 1.5s. `test_crops.py` checks the rows come out identical either way.
    """
    for page in doc:
        images = page.get_images()
        if len(images) != 1:
            yield None
            continue
        yield Image.open(io.BytesIO(doc.extract_image(images[0][0])['image']))


def cut_page(img: Image.Image) -> Page:
    """The geometry half of `read_page_raw`: crops only, no Tesseract."""
    im = img.convert('L')
    dark = np.array(im) < 128
    grid = R.find_grid(dark)
    if grid is None:
        return [], []
    epic_crops, serial_crops = [], []
    for band_top, _ in grid.bands:
        for left, right in grid.cols:
            s, e = R.card_header(im, dark, band_top, left, right)
            serial_crops.append(R._ink_box(s))
            epic_crops.append(R._ink_box(e))
    return epic_crops, serial_crops


def cut_part_bytes(data: bytes, fast_decode: bool = True) -> list[Page]:
    import fitz
    doc = fitz.open(stream=data, filetype='pdf')
    imgs = page_images(doc) if fast_decode else R._pages(doc)
    return [cut_page(img) for img in imgs if img is not None]


# Lossless only. Bilevel crops were tried (4.7% of PDF size instead of 15%) and
# changed ~60% of readings on every test part: contact_sheet's LANCZOS upscale
# needs the grey anti-aliasing. WebP lossless is identical too but only ~10%
# smaller than PNG and ~10x slower to encode, so PNG is the default.
FMT = os.environ.get('CROP_FMT', 'png')
EXT = 'webp' if FMT == 'webp' else 'png'


def _encode(crop: Image.Image) -> bytes:
    b = io.BytesIO()
    if FMT == 'webp':
        crop.convert('L').save(b, format='WEBP', lossless=True, quality=100, method=6)
    else:
        crop.convert('L').save(b, format='PNG', optimize=True)
    return b.getvalue()


def write_bundle(pages: list[Page], ac: int, part: int) -> bytes:
    buf = io.BytesIO()
    index = {'ac': ac, 'part': part, 'ext': EXT, 'pages': []}
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as z:
        for p, (epics, serials) in enumerate(pages):
            present = []
            for c, (e, s) in enumerate(zip(epics, serials)):
                if e is None and s is None:
                    continue
                present.append(c)
                for tag, crop in (('e', e), ('s', s)):
                    if crop is not None:
                        z.writestr(f'p{p:03d}/c{c:02d}{tag}.{EXT}', _encode(crop))
            index['pages'].append([len(epics), present])
        z.writestr('index.json', json.dumps(index))
    return buf.getvalue()


# ---------------------------------------------------------- OCR (Actions)

def read_bundle(data: bytes) -> tuple[dict, list[Page]]:
    pages = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = set(z.namelist())
        index = json.loads(z.read('index.json'))
        ext = index.get('ext', 'png')

        def load(name):
            if name not in names:
                return None
            im = Image.open(io.BytesIO(z.read(name)))
            im.load()
            return im.convert('L')

        for p, (n, present) in enumerate(index['pages']):
            epics, serials = [None] * n, [None] * n
            for c in present:
                epics[c] = load(f'p{p:03d}/c{c:02d}e.{ext}')
                serials[c] = load(f'p{p:03d}/c{c:02d}s.{ext}')
            pages.append((epics, serials))
    return index, pages


def ocr_page(epic_crops: list, serial_crops: list):
    """The OCR half of `read_page_raw`, from crops. Kept line-for-line in step
    with it — if `read_page_raw` changes, this must change with it."""
    import os
    if not any(c is not None for c in epic_crops):
        return [], [], []

    epic_sheet = R.contact_sheet(epic_crops)
    serial_sheet = R.contact_sheet(serial_crops)
    epic_lines = R.ocr_lines(epic_sheet) if epic_sheet else []
    serial_lines = R.ocr_lines(serial_sheet) if serial_sheet else []

    n = len(epic_crops)
    epic_lines += [''] * (n - len(epic_lines))
    serial_lines += [''] * (n - len(serial_lines))

    keep = [i for i in range(n) if epic_crops[i] is not None]
    epics = [epic_lines[i] for i in keep]
    serials = [serial_lines[i] for i in keep]
    kept_serial_crops = [serial_crops[i] for i in keep]

    if os.environ.get('ROLL_OCR_RETRY') == '1':
        for j, i in enumerate(keep):
            if R.EPIC_RE.match(R.coerce_epic(epics[j])):
                continue
            better = R._reread(epic_crops[i])
            if better and R.EPIC_RE.match(R.coerce_epic(better)):
                epics[j] = better

    return epics, serials, kept_serial_crops


def ocr_pages(pages: list[Page]) -> list:
    """As `roll_ocr._read`: OCR every page, then fit serials across the part."""
    epics, serials, crops = [], [], []
    for epic_crops, serial_crops in pages:
        e, s, c = ocr_page(epic_crops, serial_crops)
        epics.extend(e)
        serials.extend(s)
        crops.extend(c)
    return R._assemble(epics, serials, crops)
