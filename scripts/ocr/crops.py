"""Split roll_ocr into a cut stage and an OCR stage, joined by a crop bundle.

Why this exists: the ECI CDN only serves home/residential connections, so the
PDFs have to be fetched at home — but Tesseract is the expensive part and is
the reason a statewide pass took a week on one machine. So the home machine
does only the cheap half (fetch, cut each card's serial box and EPIC to ink) and
ships those crops; GitHub Actions does the expensive half in parallel.

The crops are the *exact* images `read_page_raw` would have fed to Tesseract
(`test_crops.py` checks that the legacy single read reproduces
`roll_ocr.read_part_bytes` row for row), and are stored as lossless grayscale
PNG: a bilevel or JPEG-recompressed crop would change what the readers see.

Bundle = one uncompressed zip per part (PNGs are already compressed):

    index.json      {"ac", "part", "lang", "pages": [[n_cells, [cells with a crop]], ...],
                     "text": per page, per cell [epic, serial] from a PDF text layer, or null}
    p000/c00e.png   epic crop for page 0, cell 0      p000/c00s.png  its serial crop
    cover.png       first page, bilevel — carries the part's elector totals (V3)
    summary.png     last page, bilevel — the elector summary, a fallback for V3
"""
from __future__ import annotations

import io
import json
import os
import re
import zipfile

import numpy as np
from PIL import Image

import roll_ocr as R

Page = tuple[list, list]          # (epic_crops, serial_crops), None = empty cell
RENDER_WIDTH = 1983               # px a page is rendered at when it is not one full-page image
EPIC_TOKEN = re.compile(r'^[A-Z]{3}[0-9]{7}$')


# ---------------------------------------------------------------- cut (home)

def page_images(doc):
    """(image, fitz page) for every page.

    The draft roll's pages are each one full-page JPEG; it is lifted straight
    out (roll_ocr's PNG round trip measured 16.6s of a part's 26s of non-OCR
    time). A page that is *not* a single full-page image — vector text, or an
    image that covers only part of the page — is rendered instead, at the
    draft's pixel width so card geometry and glyph sizes stay where the readers
    expect them.
    """
    import fitz
    for page in doc:
        img = None
        images = page.get_images(full=True)
        if len(images) == 1:
            xref = images[0][0]
            # get_image_bbox reads the placement from the page; get_image_rects
            # decodes the image to hash it (2.8s of a part's 9s of cutting).
            try:
                rect = page.get_image_bbox(images[0])
            except Exception:
                rect = None
            area = page.rect.width * page.rect.height
            if rect is not None and rect.is_valid and rect.width * rect.height >= 0.9 * area:
                img = Image.open(io.BytesIO(doc.extract_image(xref)['image']))
        if img is None:
            zoom = RENDER_WIDTH / page.rect.width
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
            img = Image.frombytes('L', (pix.width, pix.height), pix.samples)
        yield img, page


def cut_page(img: Image.Image, cells_out: list | None = None) -> Page:
    """The geometry half of `read_page_raw`: crops only, no Tesseract.

    `cells_out`, if given, receives each card's region (left, top, right,
    bottom) in image pixels, in the same order as the crops.
    """
    im = img.convert('L')
    dark = np.array(im) < 128
    grid = R.find_grid(dark)
    if grid is None:
        return [], []
    # Card pages have equal-width columns. The cover and summary tables do not,
    # and must not be mistaken for cards. A page holding one lone card has a
    # single column, accepted only at a card's width (31% of the page).
    widths = [r - l for l, r in grid.cols]
    if len(widths) == 1:
        if not 0.28 < widths[0] / im.width < 0.35:
            return [], []
    elif not widths or max(widths) > 1.15 * min(widths):
        return [], []
    epic_crops, serial_crops = [], []
    for band_top, band_bot in grid.bands:
        for left, right in grid.cols:
            s, e = R.card_header(im, dark, band_top, left, right)
            serial_crops.append(R._ink_box(s))
            epic_crops.append(R._ink_box(e))
            if cells_out is not None:
                cells_out.append((left, band_top, right, band_bot))
    return epic_crops, serial_crops


def text_cells(page, img: Image.Image, cells: list) -> list | None:
    """[epic, serial] per card from the PDF's own text layer, or None if the
    page has none. The draft roll has no text layer at all; if the final roll
    does, its digital text is used by `ocr_page` as a fourth, exact reader."""
    words = page.get_text('words')
    if not any(EPIC_TOKEN.match(w[4]) for w in words):
        return None
    sx = img.width / page.rect.width
    sy = img.height / page.rect.height
    placed = [((w[0] + w[2]) / 2 * sx, (w[1] + w[3]) / 2 * sy, w[4]) for w in words]
    out = []
    for left, top, right, bot in cells:
        inside = [(x, y, t) for x, y, t in placed if left <= x < right and top <= y < bot]
        epics = [t for x, y, t in inside if EPIC_TOKEN.match(t)]
        # The serial is the number in the box at the card's top-left corner.
        corner = [(y, x, t) for x, y, t in inside
                  if t.isdigit() and y < top + 0.25 * (bot - top) and x < left + 0.45 * (right - left)]
        serial = min(corner)[2] if corner else None
        out.append([epics[0] if len(epics) == 1 else None, serial])
    return out


def cut_part(data: bytes) -> dict:
    """Every page cut, plus the text layer (if any) and the cover/summary pages."""
    import fitz
    doc = fitz.open(stream=data, filetype='pdf')
    pages, texts, cover, summary = [], [], None, None
    n = doc.page_count
    for i, (img, page) in enumerate(page_images(doc)):
        cells = []
        crops = cut_page(img, cells)
        pages.append(crops)
        texts.append(text_cells(page, img, cells) if cells else None)
        if i == 0:
            cover = img
        if i == n - 1:
            summary = img
    return {'pages': pages, 'text': texts, 'cover': cover, 'summary': summary}


def cut_part_bytes(data: bytes, fast_decode: bool = True) -> list[Page]:
    if not fast_decode:
        import fitz
        doc = fitz.open(stream=data, filetype='pdf')
        return [cut_page(img) for img in R._pages(doc) if img is not None]
    return cut_part(data)['pages']


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


def _bilevel(img: Image.Image) -> bytes:
    """A whole page for reading printed numbers: thresholded, ~60 KB."""
    b = io.BytesIO()
    img.convert('L').point(lambda v: 255 if v > 160 else 0).convert('1').save(b, format='PNG', optimize=True)
    return b.getvalue()


def write_bundle(pages: list[Page], ac: int, part: int, extras: dict | None = None,
                 lang: str = 'kan') -> bytes:
    """`extras` is what `cut_part` returns beside the pages (text, cover, summary)."""
    extras = extras or {}
    buf = io.BytesIO()
    index = {'ac': ac, 'part': part, 'ext': EXT, 'lang': lang, 'pages': [],
             'text': extras.get('text')}
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
        for name in ('cover', 'summary'):
            if extras.get(name) is not None:
                z.writestr(f'{name}.png', _bilevel(extras[name]))
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


def bundle_image(data: bytes, name: str) -> Image.Image | None:
    """cover.png / summary.png from a bundle, if it carries one."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if f'{name}.png' not in z.namelist():
            return None
        im = Image.open(io.BytesIO(z.read(f'{name}.png')))
        im.load()
        return im.convert('L')


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
# If the PDF carries a real text layer (the draft roll does not), its EPIC is a
# fourth reader and is used when at least one OCR reader agrees with it.
#
# ROLL_EPIC_MODE=legacy restores the original single read (`test_crops.py`
# uses it to check the cut stage against `roll_ocr`); ROLL_EPIC_MODE=tesseract
# uses sheet + alone only, which is how the templates themselves are learned.
EPIC_MODE = os.environ.get('ROLL_EPIC_MODE', 'full')
LETTER_MARGIN = 0.04        # glyph letter accepted on its own from this lead
DIGIT_SOLO_MARGIN = 0.25    # glyph digit overrides Tesseract from this lead
DIGIT_DOUBT_MARGIN = 0.10   # ...and between these two, contradicting it withholds
TMP = '/dev/shm' if os.path.isdir('/dev/shm') else None
_templates: dict = {}


def templates(style: str = 'kan'):
    """The glyph template set for a rendering style, or False if none ships."""
    if style not in _templates:
        import glyphs
        f = glyphs.template_file(style)
        _templates[style] = glyphs.Templates.load(f, style) if f.exists() else False
    return _templates[style]


_protos: dict = {}


def prototypes(style: str = 'kan'):
    """The prototype reader for a rendering style, or False if none ships."""
    if style not in _protos:
        import glyphs
        f = glyphs.template_file(style, 'prototypes')
        _protos[style] = glyphs.Prototypes.load(f, style) if f.exists() else False
    return _protos[style]


def proto_read(crop, style: str = 'kan'):
    """The prototype reader's per-character reading of a crop, or None. On a
    cleanly separated crop it reads the same ten glyphs as the template
    reader; where glyphs touch it chooses its own cut (`own_cut`)."""
    tm, pr = templates(style), prototypes(style)
    if not tm or not pr:
        return None
    spans = []
    detail = tm.read_detail(crop, spans_out=spans)
    if detail is None or not spans:
        return None
    band, chosen = spans
    return pr.read_touching(band) if detail.touching else pr.read(band, chosen)


def _lined_up(t: str, glyph: str, lo: int, hi: int, need: int) -> bool:
    return sum(a == b for a, b in zip(t[lo:hi], glyph[lo:hi])) >= need


def fuse(detail, sheet: str, alone: str | None, proto=None) -> str | None:
    """One EPIC from the glyph reader's per-character detail, the Tesseract
    readings (each used only if it is a well-formed EPIC) and, when given, the
    prototype reader's per-character reading. None = withhold.

    Letters: a glyph letter Tesseract agrees with is accepted. When they
    disagree the prototype reader breaks the tie — glyph + prototype, or
    Tesseract + prototype when the prototype's own lead is clear — and with no
    tie-break the EPIC is withheld. (The glyph reader alone used to win any
    clear disagreement; checked against the images it was wrong on D/O, so it
    no longer decides a letter by itself.)
    Digits: two readers must agree (the prototype reader counts as one), and a
    second answer with as many votes withholds; a very clear glyph digit wins
    on its own, and a middling one that contradicts Tesseract withholds.

    Two guards, from the errors an independent reading of the English roll
    turned up (2026-10-10):

    * A Tesseract reading votes on letters only if two of its three letters
      match the glyph reader's, and on digits only if four of seven do. An
      extra glyph read at the start ('IQG…' as 'LIQG…', which `coerce_epic`
      cuts to 'LIQ…') shifts every letter; its Q then "supported" a prototype
      Q in the G's place, and a whole series was published as IQQ.
    * When the glyphs touched and the reader chose its own cuts
      (`detail.touching`), no digit wins on the glyph's margin alone, and a
      letter Tesseract does not support needs the prototype reader to agree on
      a cut it found for itself (`own_cut`). On the template reader's cut the
      two were one witness, not two: 'FLV…' was cut as 'FIW…' and both read
      it so, against two Tesseract passes reading FLV.
    """
    valid = lambda e: bool(e and R.EPIC_RE.match(e))  # noqa: E731
    tess = [t for t in (sheet, alone) if valid(t)]
    if detail is None:
        # No glyph opinion: the two Tesseract passes must agree.
        return sheet if len(tess) == 2 and sheet == alone else None
    glyph = ''.join(d[0] for d in detail)
    touching = getattr(detail, 'touching', False)
    if touching and proto is not None and not getattr(proto, 'own_cut', False):
        proto = None                 # read on the same cut: not a second witness
    letter_tess = [t for t in tess if _lined_up(t, glyph, 0, 3, 2)]
    digit_tess = [t for t in tess if _lined_up(t, glyph, 3, 10, 4)]
    out = []
    for i, (g, _, margin) in enumerate(detail):
        p, p_margin = (proto[i][0], proto[i][2]) if proto else (None, 0.0)
        if i < 3:
            votes = [t[i] for t in letter_tess]
            if g in votes:
                out.append(g)
            elif touching:
                if p != g or min(margin, p_margin) < LETTER_MARGIN:
                    return None
                out.append(g)
            elif p is None:
                if margin < LETTER_MARGIN:
                    return None
                out.append(g)
            elif p == g and margin >= LETTER_MARGIN:
                out.append(g)
            elif p in votes and p_margin >= LETTER_MARGIN:
                out.append(p)
            else:
                return None
            continue
        votes = [t[i] for t in digit_tess]
        if margin >= DIGIT_SOLO_MARGIN and not touching:
            out.append(g)
            continue
        if votes and g not in votes and margin >= DIGIT_DOUBT_MARGIN:
            return None
        pool = votes + [g] + ([p] if p else [])
        agreed = [c for c in dict.fromkeys(pool) if pool.count(c) >= 2]
        if len(agreed) != 1:
            return None
        out.append(agreed[0])
    epic = ''.join(out)
    return epic if valid(epic) else None


def _single_line(crop: Image.Image, target: int = 90) -> Image.Image:
    """The same padding and upscale as `roll_ocr._reread` (target 90 px)."""
    pad = 16
    canvas = Image.new('L', (crop.width + pad * 2, crop.height + pad * 2), 255)
    canvas.paste(crop, (pad, pad))
    scale = max(3, min(8, round(target / max(1, crop.height))))
    return canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)


def read_each(images: list, psm: int = 7, extra: tuple = ()) -> list[str]:
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
        proc = subprocess.run([R.TESSERACT, lst, 'stdout', '--psm', str(psm), *extra],
                              stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              check=True, env=R.TESS_ENV)
    chunks = proc.stdout.decode('utf8', 'replace').split('\f')
    out = [''.join(c.split()) for c in chunks[:len(images)]]
    if len(out) != len(images):   # never seen; be safe rather than misalign
        out = [''.join(R.ocr_lines(im, psm=psm)) for im in images]
    return out


def ocr_page(epic_crops: list, serial_crops: list, style: str = 'kan', text: list | None = None):
    """The OCR half of `read_page_raw`, from crops.

    Returns (epics, epic_ok, serials, kept_serial_crops, info) for the non-empty
    cards; `info` records, per card, its cell and what every reader said.
    """
    if not any(c is not None for c in epic_crops):
        return [], [], [], [], []

    epic_lines = R.sheet_lines(epic_crops)
    serial_lines = R.sheet_lines(serial_crops)

    n = len(epic_crops)
    epic_lines += [''] * (n - len(epic_lines))
    serial_lines += [''] * (n - len(serial_lines))

    keep = [i for i in range(n) if epic_crops[i] is not None]
    sheet = [R.coerce_epic(epic_lines[i]) for i in keep]
    serials = [serial_lines[i] for i in keep]
    kept_serial_crops = [serial_crops[i] for i in keep]
    valid = lambda e: bool(e and R.EPIC_RE.match(e))  # noqa: E731
    tx = [text[i] if text and i < len(text) and text[i] else [None, None] for i in keep]
    for j, (_, ts) in enumerate(tx):
        if ts:
            serials[j] = ts                  # a digital serial beats any reading

    if EPIC_MODE == 'legacy':
        return ([epic_lines[i] for i in keep], [valid(e) for e in sheet], serials, kept_serial_crops,
                [{'cell': i, 'sheet': sheet[j]} for j, i in enumerate(keep)])

    tm = templates(style) if EPIC_MODE == 'full' else False
    detail = [tm.read_detail(epic_crops[i]) if tm else None for i in keep]
    glyph = [''.join(d[0] for d in det) if det else None for det in detail]
    info = [{'cell': i, 'sheet': sheet[j], 'glyph': glyph[j], 'alone': None,
             'gmin': round(min(d[2] for d in detail[j]), 3) if detail[j] else None}
            for j, i in enumerate(keep)]

    epics, ok = list(sheet), [False] * len(keep)
    pending = []
    for j in range(len(keep)):
        if tx[j][0] and tx[j][0] in (sheet[j], glyph[j]):
            epics[j], ok[j] = tx[j][0], True
            info[j]['how'] = 'text'
        elif glyph[j] and glyph[j] == sheet[j] and valid(sheet[j]) and not tx[j][0]:
            ok[j] = True                     # two different readers agree outright
            info[j]['how'] = 'direct'
        else:
            pending.append(j)
    if pending:
        alone = [R.coerce_epic(x) for x in
                 read_each([_single_line(epic_crops[keep[j]]) for j in pending])]
        for j, a in zip(pending, alone):
            info[j]['alone'] = a
            if tx[j][0]:
                # A text-layer EPIC no OCR reader confirms is not trusted either.
                if tx[j][0] == a:
                    epics[j], ok[j], info[j]['how'] = a, True, 'text'
                else:
                    epics[j], info[j]['how'] = tx[j][0], 'text-conflict'
                continue
            fused = fuse(detail[j], sheet[j], a, proto_read(epic_crops[keep[j]], style) if tm else None)
            if fused:
                epics[j], ok[j], info[j]['how'] = fused, True, 'fused'
            else:
                epics[j] = glyph[j] or (a if valid(a) else sheet[j])   # recorded, not published
                info[j]['how'] = 'withheld'
    return epics, ok, serials, kept_serial_crops, info


def ocr_pages(pages: list[Page], style: str = 'kan', texts: list | None = None) -> list[tuple]:
    """OCR every page, then fit serials across the part.

    Returns (Row, epic_ok, info) per card. `Row.ok` keeps roll_ocr's meaning
    (valid EPIC and confirmed serial); `epic_ok` says the readers settled every
    character of the EPIC; `info` has the page, cell, each reader's output and
    the serial box's mark (`R.serial_marker`: 'X' is a deleted elector).
    """
    epics, epic_ok, serials, crops, infos = [], [], [], [], []
    for p, (epic_crops, serial_crops) in enumerate(pages):
        text = texts[p] if texts and p < len(texts) else None
        e, k, s, c, inf = ocr_page(epic_crops, serial_crops, style, text)
        for d, crop in zip(inf, c):
            d['page'] = p
            d['mark'] = R.serial_marker(crop)
        epics.extend(e)
        epic_ok.extend(k)
        serials.extend(s)
        crops.extend(c)
        infos.extend(inf)
    return list(zip(R._assemble(epics, serials, crops), epic_ok, infos))
