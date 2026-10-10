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


# ------------------------------------------------------------ EPIC reading
#
# The original pipeline read each page's EPICs once, from a contact sheet, with
# Tesseract. Measured 2026-10-10 against 224 sample parts (one per AC) that is
# not good enough: Tesseract misreads EPIC *letters* even when two independent
# Tesseract passes agree (IOP -> LIO, AOH -> AQH, WZU -> WZZ, IUO -> IWO,
# FZT -> FZI, YCX -> YYC), and occasionally a leading digit (XRR0514265 ->
# XRR5514265). Those are valid-looking EPICs; nothing downstream can catch them.
#
# So three readers now look at every EPIC, and `fuse` decides per character:
#
#   sheet   Tesseract, the page's contact sheet, psm 6 (the original read)
#   glyph   template matching on the fixed EPIC font (`glyphs.py`)
#   alone   Tesseract, the crop on its own as one line, psm 7 — run only when
#           sheet and glyph disagree, so it costs little
#
# Each reader fails on different characters. Letters follow the glyph reader
# (every letter disagreement checked by eye had it right). Digits need two of
# three readers, except that a very clear glyph digit wins on its own, and a
# middling glyph digit that contradicts both Tesseract passes withholds the
# EPIC (the glyph reader confuses 8 and 6 up to a margin of ~0.16).
#
# ROLL_EPIC_MODE=legacy restores the original single read (`test_crops.py`
# uses it to check the cut stage against `roll_ocr`); ROLL_EPIC_MODE=tesseract
# uses sheet + alone only, which is how the templates themselves are learned.
EPIC_MODE = os.environ.get('ROLL_EPIC_MODE', 'full')
LETTER_MARGIN = 0.04        # glyph letter accepted on its own from this lead
DIGIT_SOLO_MARGIN = 0.25    # glyph digit overrides Tesseract from this lead
DIGIT_DOUBT_MARGIN = 0.10   # ...and between these two, contradicting it withholds
TMP = '/dev/shm' if os.path.isdir('/dev/shm') else None
_templates = None


def templates():
    global _templates
    if _templates is None:
        import glyphs
        _templates = glyphs.Templates.load() if glyphs.DEFAULT_FILE.exists() else False
    return _templates


def fuse(detail, sheet: str, alone: str | None) -> str | None:
    """One EPIC from the glyph reader's per-character detail and the Tesseract
    readings (each used only if it is a well-formed EPIC). None = withhold."""
    valid = lambda e: bool(e and R.EPIC_RE.match(e))  # noqa: E731
    tess = [t for t in (sheet, alone) if valid(t)]
    if detail is None:
        # No glyph opinion: the two Tesseract passes must agree.
        return sheet if len(tess) == 2 and sheet == alone else None
    out = []
    for i, (g, _, margin) in enumerate(detail):
        votes = [t[i] for t in tess]
        if i < 3:
            if margin >= LETTER_MARGIN or g in votes:
                out.append(g)
            else:
                return None
            continue
        if margin >= DIGIT_SOLO_MARGIN:
            out.append(g)
            continue
        if votes and g not in votes and margin >= DIGIT_DOUBT_MARGIN:
            return None
        pool = votes + [g]
        agreed = [c for c in dict.fromkeys(pool) if pool.count(c) >= 2]
        if not agreed:
            return None
        out.append(agreed[0])
    epic = ''.join(out)
    return epic if valid(epic) else None


def _single_line(crop: Image.Image) -> Image.Image:
    """The same padding and upscale as `roll_ocr._reread`."""
    pad = 16
    canvas = Image.new('L', (crop.width + pad * 2, crop.height + pad * 2), 255)
    canvas.paste(crop, (pad, pad))
    scale = max(3, min(8, round(90 / max(1, crop.height))))
    return canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)


def read_each(images: list, psm: int = 7) -> list[str]:
    """Read many images, each as its own line, in ONE Tesseract process.

    Tesseract treats a `.txt` input as a list of image files and separates their
    outputs with form feeds. This gets the accuracy of reading crops one by one
    without paying process start-up per crop (~0.23s each when spawned singly).
    """
    import subprocess
    import tempfile
    if not images:
        return []
    if R.TESSERACT is None:
        R.TESSERACT = R._tesseract_cmd()
    with tempfile.TemporaryDirectory(dir=TMP) as d:
        files = []
        for i, im in enumerate(images):
            f = os.path.join(d, f'{i:03d}.png')
            im.save(f, compress_level=1)
            files.append(f)
        lst = os.path.join(d, 'list.txt')
        with open(lst, 'w', encoding='utf8') as fh:
            fh.write('\n'.join(files) + '\n')
        proc = subprocess.run([R.TESSERACT, lst, 'stdout', '--psm', str(psm)],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              check=True, env=R.TESS_ENV)
    chunks = proc.stdout.decode('utf8', 'replace').split('\f')
    out = [''.join(c.split()) for c in chunks[:len(images)]]
    if len(out) != len(images):   # never seen; be safe rather than misalign
        out = [''.join(R.ocr_lines(im, psm=psm)) for im in images]
    return out


def ocr_page(epic_crops: list, serial_crops: list):
    """The OCR half of `read_page_raw`, from crops.

    Returns (epics, epic_ok, serials, kept_serial_crops) for the non-empty cards.
    """
    if not any(c is not None for c in epic_crops):
        return [], [], [], []

    epic_sheet = R.contact_sheet(epic_crops)
    serial_sheet = R.contact_sheet(serial_crops)
    epic_lines = R.ocr_lines(epic_sheet) if epic_sheet else []
    serial_lines = R.ocr_lines(serial_sheet) if serial_sheet else []

    n = len(epic_crops)
    epic_lines += [''] * (n - len(epic_lines))
    serial_lines += [''] * (n - len(serial_lines))

    keep = [i for i in range(n) if epic_crops[i] is not None]
    sheet = [R.coerce_epic(epic_lines[i]) for i in keep]
    serials = [serial_lines[i] for i in keep]
    kept_serial_crops = [serial_crops[i] for i in keep]
    valid = lambda e: bool(e and R.EPIC_RE.match(e))  # noqa: E731

    if EPIC_MODE == 'legacy':
        return [epic_lines[i] for i in keep], [valid(e) for e in sheet], serials, kept_serial_crops

    tm = templates() if EPIC_MODE == 'full' else False
    detail = [tm.read_detail(epic_crops[i]) if tm else None for i in keep]
    glyph = [''.join(d[0] for d in det) if det else None for det in detail]

    epics, ok = list(sheet), [False] * len(keep)
    pending = []
    for j in range(len(keep)):
        if glyph[j] and glyph[j] == sheet[j] and valid(sheet[j]):
            ok[j] = True                     # two different readers agree outright
        else:
            pending.append(j)
    if pending:
        alone = [R.coerce_epic(x) for x in
                 read_each([_single_line(epic_crops[keep[j]]) for j in pending])]
        for j, a in zip(pending, alone):
            fused = fuse(detail[j], sheet[j], a)
            if fused:
                epics[j], ok[j] = fused, True
            else:
                epics[j] = glyph[j] or (a if valid(a) else sheet[j])   # recorded, not published
    return epics, ok, serials, kept_serial_crops


def ocr_pages(pages: list[Page]) -> list[tuple]:
    """OCR every page, then fit serials across the part.

    Returns (Row, epic_ok) per card. `Row.ok` keeps roll_ocr's meaning (valid
    EPIC and confirmed serial); `epic_ok` says the readers settled every
    character of the EPIC.
    """
    epics, epic_ok, serials, crops = [], [], [], []
    for epic_crops, serial_crops in pages:
        e, k, s, c = ocr_page(epic_crops, serial_crops)
        epics.extend(e)
        epic_ok.extend(k)
        serials.extend(s)
        crops.extend(c)
    return list(zip(R._assemble(epics, serials, crops), epic_ok))
