"""Read serial numbers and EPICs out of a rasterised electoral-roll part PDF.

ECI publishes electoral rolls with NO text layer: every page is a single
full-page JPEG. PyMuPDF's get_text() returns zero characters on all of them.
So the rows have to be recovered by OCR, and this module does that.

The saving grace is that these are not scans of paper. They are crisp digital
rasterisations of a rigid template, so the structure can be recovered exactly
before any OCR happens:

    page -> 10 card bands x 3 card columns = 30 elector cards
    card -> a ruled serial box (top left) and an EPIC (top right)

Everything here is measured from the page's own ink, never hard-coded. That is
load-bearing: Karnataka renders at 1652x2338 and Meghalaya at 1983x2806, and
both parse with the same code.

Why OCR only the serial and the EPIC:
  - They answer the question the site exists to answer ("am I on the draft roll,
    and where"), and they are the two fields that are pure ASCII with a known
    grammar, so they can be validated rather than trusted.
  - They are ~5x cheaper than reading the whole card, which matters when the
    state is ~1.8 million page images.

Accuracy comes from three layers, in order of strength:
  1. Geometry. Crops are cut to detected rules and then trimmed to ink, so
     Tesseract never sees a box border (which it reads as '1' or 'I').
  2. Grammar. An EPIC is exactly [A-Z]{3}[0-9]{7}, so every confusable glyph has
     one legal reading once you know which side of the letter/digit boundary it
     falls on. `coerce_epic` applies that.
  3. Sequence. Serial numbers run consecutively down a part, so a page's serials
     are checked against that run and a disagreeing OCR result is corrected from
     its neighbours rather than published.

Anything still failing all three is returned with ok=False and must be counted
as unread, never as absent — see the coverage guard in the site.
"""

from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
from dataclasses import dataclass

import numpy as np
from PIL import Image

EPIC_RE = re.compile(r'^[A-Z]{3}[0-9]{7}$')

# Position-aware coercion. Applied only after the string is known to be 10 chars.
_TO_ALPHA = str.maketrans({'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '6': 'G', '8': 'B'})
_TO_DIGIT = str.maketrans({'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1',
                           'Z': '2', 'S': '5', 'G': '6', 'B': '8', 'A': '4', 'T': '7'})


def _tesseract_cmd() -> str:
    found = shutil.which('tesseract')
    if found:
        return found
    win = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(win):
        return win
    raise RuntimeError(
        'tesseract not found. Install it (apt-get install tesseract-ocr, or '
        'winget install UB-Mannheim.TesseractOCR) and put it on PATH.'
    )


TESSERACT = None

# The pipeline gets its parallelism from running many Tesseract *processes* at
# once (one per part, via ProcessPoolExecutor) — but Tesseract's LSTM engine
# also spawns its own OpenMP thread pool inside each call unless told not to.
# Left alone, 11 worker processes each opening a handful of threads means 30+
# threads contending for 12 cores: busy-looking CPU (measured 60-86%) that is
# actually thrashing on context switches rather than doing 11x the work. This
# pins every Tesseract call to one thread so the process-level parallelism —
# which is real, since each part is independent — is what the cores spend
# their time on.
TESS_ENV = {**os.environ, 'OMP_THREAD_LIMIT': '1'}


def ocr_lines(img: Image.Image, psm: int = 6) -> list[str]:
    """Run Tesseract once over an image and return its non-empty lines.

    Called once per field per page rather than once per card: process startup
    dominates the cost at this crop size, so batching 30 cards into one tall
    sheet takes ~0.9s where 30 separate calls take ~9.6s.
    """
    global TESSERACT
    if TESSERACT is None:
        TESSERACT = _tesseract_cmd()
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    # A whitelist is deliberately NOT set: it is unreliable under --psm 6 with
    # the LSTM engine (it silently lets digits through in a letters-only pass),
    # and `coerce_epic` enforces the grammar afterwards anyway.
    proc = subprocess.run(
        [TESSERACT, 'stdin', 'stdout', '--psm', str(psm)],
        input=buf.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        check=True, env=TESS_ENV,
    )
    return [ln.strip() for ln in proc.stdout.decode('utf8', 'replace').split('\n') if ln.strip()]


# ------------------------------------------------------------------ geometry

def _runs(idx: np.ndarray, gap: int = 6) -> list[tuple[int, int]]:
    """Collapse near-consecutive indices into (start, end) spans."""
    out: list[list[int]] = []
    for i in idx:
        if out and i - out[-1][-1] <= gap:
            out[-1].append(int(i))
        else:
            out.append([int(i)])
    return [(r[0], r[-1]) for r in out]


def _mids(idx: np.ndarray, gap: int = 6) -> list[int]:
    return [(s + e) // 2 for s, e in _runs(idx, gap)]


def _ink_box(img: Image.Image | None) -> Image.Image | None:
    """Trim to the ink. Keeps rules and padding away from Tesseract."""
    if img is None or img.width < 3 or img.height < 3:
        return None
    arr = np.array(img) < 128
    ys, xs = np.where(arr)
    if not len(ys):
        return None
    return img.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


@dataclass
class Grid:
    bands: list[tuple[int, int]]
    cols: list[tuple[int, int]]


def find_grid(dark: np.ndarray) -> Grid | None:
    """Recover the card grid from the page's own ruled lines.

    A card band is any pair of full-width rules more than an eighth of the page
    apart; that threshold is relative to page height so it holds at any DPI.
    """
    h, w = dark.shape
    gap = max(2, int(round(6 * w / REFERENCE_WIDTH)))
    rows = _mids(np.where(dark.sum(axis=1) > 0.6 * w)[0], gap)
    min_band = h // 18
    bands = [(rows[i], rows[i + 1]) for i in range(len(rows) - 1)
             if rows[i + 1] - rows[i] > min_band]
    if not bands:
        return None
    top, bot = bands[0]
    inset = max(2, int(round(5 * w / REFERENCE_WIDTH)))
    seg = dark[top + inset:bot - inset, :]
    if seg.shape[0] < 10:
        return None
    verts = _mids(np.where(seg.sum(axis=0) > 0.85 * seg.shape[0])[0], gap)
    cols = [(verts[i], verts[i + 1]) for i in range(0, len(verts) - 1, 2)]
    if not cols:
        return None
    return Grid(bands, cols)


"""Page width the pixel offsets below were measured against.

Every margin in `card_header` is expressed as a fraction of this and rescaled to
whatever the file actually is. That is not tidiness: Bihar publishes at 949x1343,
Karnataka at 1652x2338 and Meghalaya at 1983x2806, and a hard-coded 52-pixel
header strip that fits the last two runs straight through the elector's name on
the first — which read 3 rows out of a 44-page part instead of ~1,300.
"""
REFERENCE_WIDTH = 1652.0


def card_header(im: Image.Image, dark: np.ndarray, band_top: int,
                left: int, right: int) -> tuple[Image.Image | None, Image.Image | None]:
    """Split one card's header strip into its serial and EPIC crops.

    The serial sits in a drawn box; the EPIC is free text to its right. The box
    is located rather than assumed, because a two-digit and a four-digit serial
    put the ink in very different places and a proportional split clips one of
    them — which is exactly how the first version lost the leading digit of
    every serial above 72.
    """
    h, w = dark.shape
    s = w / REFERENCE_WIDTH
    px = lambda n: max(1, int(round(n * s)))  # noqa: E731

    strip_h = min(px(52), h - band_top - px(4))
    if strip_h < px(20):
        return None, None
    m = px(3)
    strip = dark[band_top + m:band_top + strip_h, left + m:right - m]
    if strip.size == 0:
        return None, None

    box_zone = strip[:, :int(strip.shape[1] * 0.35)]
    rules = _mids(np.where(box_zone.sum(axis=1) > 0.7 * box_zone.shape[1])[0], gap=px(6))
    if len(rules) < 2:
        return None, None
    top, bot = rules[0], rules[-1]
    inner = strip[top + px(2):bot - px(1), :]
    if inner.shape[0] < px(6):
        return None, None
    sides = _mids(np.where(inner.sum(axis=0) > 0.75 * inner.shape[0])[0], gap=px(6))
    if len(sides) < 2:
        return None, None

    bl, br = sides[0], sides[-1]
    y0, y1 = band_top + m + top + px(2), band_top + m + bot - px(1)
    serial_box = (left + m + bl + px(2), y0, left + m + br - px(1), y1)
    epic_box = (left + m + br + px(8), y0 - px(4), right - px(4), y1 + px(4))
    # A card whose detected box is degenerate (near-zero or negative width —
    # seen on a handful of parts where the rule-detection picks up noise)
    # must not crash the whole part over one card. PIL's crop() raises rather
    # than clamping, so this is checked explicitly; the card is dropped like
    # any other unreadable one (see the "Drop empty cells" step upstream).
    if serial_box[2] <= serial_box[0] or serial_box[3] <= serial_box[1]:
        return None, None
    if epic_box[2] <= epic_box[0] or epic_box[3] <= epic_box[1]:
        return None, None
    serial = im.crop(serial_box)
    epic = im.crop(epic_box)
    return serial, epic


"""Cap height Tesseract is happiest with, in pixels after upscaling."""
TARGET_GLYPH_PX = 60


def contact_sheet(crops: list[Image.Image | None], pad: int = 20) -> Image.Image | None:
    """Stack crops into one tall image, one per line, for a single OCR pass.

    The upscale factor is chosen to bring the text to a constant size rather
    than being a fixed multiple, so a 949-wide Bihar page and a 1983-wide
    Meghalaya one both reach Tesseract at the resolution it reads best.
    """
    real = [c for c in crops if c is not None]
    if not real:
        return None
    w = max(c.width for c in real)
    h = max(c.height for c in real)
    sheet = Image.new('L', (w + pad * 2, (h + pad) * len(crops) + pad), 255)
    for i, c in enumerate(crops):
        if c is not None:
            sheet.paste(c, (pad, pad + i * (h + pad)))
    scale = max(2, min(6, round(TARGET_GLYPH_PX / max(1, h))))
    return sheet.resize((sheet.width * scale, sheet.height * scale), Image.LANCZOS)


# ------------------------------------------------------------------ grammar

def coerce_epic(raw: str) -> str:
    """Force an OCR reading onto the EPIC grammar, or return it unchanged.

    An 11-character reading is almost always a spurious glyph inserted at the
    letter/digit boundary ('TDB0917013' read as 'TDBO0917013'), so the first
    three and last seven characters are the reliable parts.
    """
    s = re.sub(r'[^A-Za-z0-9]', '', raw).upper()
    if len(s) == 11:
        s = s[:3] + s[-7:]
    if len(s) != 10:
        return s
    return s[:3].translate(_TO_ALPHA) + s[3:].translate(_TO_DIGIT)


def repair_serials(raw: list[str]) -> tuple[list[int], list[bool]]:
    """Fit serials to the consecutive run they must form.

    Serials increase by one through a part, so the correct sequence can be
    inferred from whichever readings agree with each other and used to repair
    the rest. A '#2' supplement marker printed inside the serial box, for
    instance, reads as a leading digit and is corrected here rather than
    published as a wrong serial.

    Run this over a WHOLE PART, not a page. Fitting each page independently lets
    a page whose readings are mostly poor elect its own bad anchor, and since
    the anchor is unconstrained that produced serials running from -6 on a real
    file — visibly wrong here, but silently wrong on a page starting at 331.
    """
    nums: list[int | None] = []
    for r in raw:
        found = re.findall(r'\d+', r)
        nums.append(int(found[-1]) if found else None)

    # Model the sequence as offset[i] = serial[i] - i. A clean run makes that a
    # constant, but a real roll has gaps — a name struck off leaves a hole, and
    # every serial after it shifts. So the offset is piecewise constant, and a
    # single global anchor is the wrong model: on a real Meghalaya part it put
    # the whole file one out and flagged 40% of rows as unreliable.
    # A rolling mode tracks the steps instead of averaging across them.
    offsets = [n - i if n is not None else None for i, n in enumerate(nums)]
    window = 15
    fitted: list[int] = []
    for i in range(len(raw)):
        lo, hi = max(0, i - window), min(len(raw), i + window + 1)
        votes: dict[int, int] = {}
        for o in offsets[lo:hi]:
            # Serials are 1-based, so an offset implying serial < 1 is impossible.
            if o is not None and o + i >= 1:
                votes[o] = votes.get(o, 0) + 1
        if votes:
            fitted.append(max(votes, key=lambda k: (votes[k], -abs(k - (offsets[i] or k)))))
        elif fitted:
            fitted.append(fitted[-1])
        else:
            fitted.append(1)

    serials = [fitted[i] + i for i in range(len(raw))]
    confident = [nums[i] == serials[i] for i in range(len(raw))]
    return serials, confident


# ------------------------------------------------------------------ per page

@dataclass
class Row:
    serial: int
    epic: str
    ok: bool


def read_page_raw(img: Image.Image) -> tuple[list[str], list[str], list]:
    """Read one page: raw EPIC strings, raw serial strings, and the serial crops.

    Serials are left unrepaired: the sequence they belong to spans the whole
    part, so fitting it here would be fitting it to too little evidence. The
    serial crops are returned with them because the second pass in `_assemble`
    can only tell which serials to re-read once the whole part has been fitted,
    and re-cutting them from the page then would mean decoding every page twice.
    """
    im = img.convert('L')
    dark = np.array(im) < 128
    grid = find_grid(dark)
    if grid is None:
        return [], [], []

    serial_crops: list[Image.Image | None] = []
    epic_crops: list[Image.Image | None] = []
    for band_top, _ in grid.bands:
        for left, right in grid.cols:
            s, e = card_header(im, dark, band_top, left, right)
            serial_crops.append(_ink_box(s))
            epic_crops.append(_ink_box(e))

    if not any(c is not None for c in epic_crops):
        return [], [], []

    epic_sheet = contact_sheet(epic_crops)
    serial_sheet = contact_sheet(serial_crops)
    epic_lines = ocr_lines(epic_sheet) if epic_sheet else []
    serial_lines = ocr_lines(serial_sheet) if serial_sheet else []

    n = len(epic_crops)
    epic_lines += [''] * (n - len(epic_lines))
    serial_lines += [''] * (n - len(serial_lines))

    # Drop empty cells: the last page of a part is usually short, and a blank
    # card must not consume a serial the next real card needs.
    keep = [i for i in range(n) if epic_crops[i] is not None]
    epics = [epic_lines[i] for i in keep]
    serials = [serial_lines[i] for i in keep]
    kept_serial_crops = [serial_crops[i] for i in keep]

    # Optional second pass over the EPICs that fail the grammar, re-read
    # individually and upscaled harder.
    #
    # Off by default because it is a bad trade as measured: on a low-resolution
    # Bihar part it doubled the runtime (44s -> 113s) to move well-formed rows
    # from 88% to 90%. Rows it does not recover are flagged rather than
    # published, so the cost of skipping it is coverage, not correctness — and
    # Karnataka's own rolls render at ~200 DPI, where the first pass already
    # reads 100%. Set ROLL_OCR_RETRY=1 for a source that needs it.
    if os.environ.get('ROLL_OCR_RETRY') == '1':
        for j, i in enumerate(keep):
            if EPIC_RE.match(coerce_epic(epics[j])):
                continue
            better = _reread(epic_crops[i])
            if better and EPIC_RE.match(coerce_epic(better)):
                epics[j] = better

    return epics, serials, kept_serial_crops


def reread_serial(crop: Image.Image | None) -> str:
    """Re-OCR one serial box on its own, as a single word of digits.

    The contact sheet is read at --psm 6 with no whitelist, which is right for
    EPICs (mixed letters and digits, one per line) but is where every serial
    failure measured on Karnataka comes from: a crisp `51` read as `31`, `500`
    as `200`, `52` as `32`. The crops themselves are clean — rendered digits,
    trimmed to ink — so this is Tesseract's layout guess going wrong, not the
    geometry. Reading the box alone as a single word, with the alphabet
    restricted to digits, fixes about half of them.

    Unlike the EPIC pass the whitelist is safe here, because the field really is
    digits-only and --psm 8 does honour it.

    The upscale is deliberately modest. Padding to 24px and a 140px target
    measured *worse* than this (6 of 82 recovered against 34): these glyphs are
    already near the size Tesseract wants, and pushing them larger blurs them.
    """
    if crop is None:
        return ''
    pad = 16
    canvas = Image.new('L', (crop.width + pad * 2, crop.height + pad * 2), 255)
    canvas.paste(crop, (pad, pad))
    scale = max(3, min(10, round(90 / max(1, crop.height))))
    big = canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)
    buf = io.BytesIO()
    big.save(buf, format='PNG')
    global TESSERACT
    if TESSERACT is None:
        TESSERACT = _tesseract_cmd()
    proc = subprocess.run(
        [TESSERACT, 'stdin', 'stdout', '--psm', '8',
         '-c', 'tessedit_char_whitelist=0123456789'],
        input=buf.getvalue(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        check=True, env=TESS_ENV,
    )
    return ''.join(proc.stdout.decode('utf8', 'replace').split())


def _reread(crop: Image.Image | None) -> str:
    """Re-OCR one crop on its own, larger, as a single text line."""
    if crop is None:
        return ''
    pad = 16
    canvas = Image.new('L', (crop.width + pad * 2, crop.height + pad * 2), 255)
    canvas.paste(crop, (pad, pad))
    scale = max(3, min(8, round(90 / max(1, crop.height))))
    big = canvas.resize((canvas.width * scale, canvas.height * scale), Image.LANCZOS)
    lines = ocr_lines(big, psm=7)
    return lines[0] if lines else ''


def read_page(img: Image.Image) -> list[Row]:
    """Read one page standalone. Convenience for tests; prefer `read_part`."""
    epics, serials, crops = read_page_raw(img)
    return _assemble(epics, serials, crops)


def _assemble(epic_lines: list[str], serial_lines: list[str],
              serial_crops: list | None = None) -> list[Row]:
    """Fit serials across the part, re-reading the ones that do not agree.

    Two passes, because the first pass is what tells you which boxes to look at
    again. A serial whose sheet reading disagrees with the fitted sequence is
    re-cut and read alone as digits (`reread_serial`); the corrected string is
    put back and the whole sequence re-fitted, so a recovered reading also
    strengthens the vote for its neighbours.

    Measured on Karnataka AC 196 part 227 (792 cards): 10.4% of rows flagged
    after one pass, 5.9% after two, for +14s on a 69s part. The fitted serial
    itself moved on exactly 1 of 792 cards — the second pass is overwhelmingly
    confirming values the sequence already had right, which is the point. Those
    rows were being withheld while carrying a correct serial and a perfectly
    read EPIC.
    """
    serials, confident = repair_serials(serial_lines)

    if serial_crops and len(serial_crops) == len(serial_lines):
        retry = [i for i, ok in enumerate(confident) if not ok]
        if retry:
            corrected = list(serial_lines)
            for i in retry:
                better = reread_serial(serial_crops[i])
                if better:
                    corrected[i] = better
            serials, confident = repair_serials(corrected)

    rows = []
    for i, raw in enumerate(epic_lines):
        epic = coerce_epic(raw)
        rows.append(Row(serials[i], epic, bool(EPIC_RE.match(epic)) and confident[i]))
    return rows


def _pages(doc):
    """Yield each page's image. These PDFs hold exactly one full-page image per
    page, so the JPEG is lifted straight out — no rendering step, no rasteriser."""
    import fitz
    for page in doc:
        images = page.get_images()
        if len(images) != 1:
            yield None
            continue
        pix = fitz.Pixmap(doc, images[0][0])
        yield Image.open(io.BytesIO(pix.tobytes('png')))


def page_images(pdf_path: str):
    import fitz
    yield from _pages(fitz.open(pdf_path))


def _read(doc) -> list[Row]:
    epics: list[str] = []
    serials: list[str] = []
    crops: list = []
    for img in _pages(doc):
        if img is None:
            continue
        e, s, c = read_page_raw(img)
        epics.extend(e)
        serials.extend(s)
        crops.extend(c)
    return _assemble(epics, serials, crops)


def read_part(pdf_path: str) -> list[Row]:
    """Read every elector row in a part PDF, fitting serials across the part."""
    import fitz
    return _read(fitz.open(pdf_path))


def read_part_bytes(data: bytes) -> list[Row]:
    """As `read_part`, from bytes — the crawler never puts a PDF on disk."""
    import fitz
    return _read(fitz.open(stream=data, filetype='pdf'))
