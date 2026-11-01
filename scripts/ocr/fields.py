"""Age, gender, relation type and house number of every card, from either roll.

    from fields import read_page
    read_page(img, lang='eng'|'kan', names=False) -> {cell: {'age', 'gender', 'relation', 'house'[, 'name']}}

For the open dataset (docs/dataset.md). Both rolls are read: each is a
witness for the other's age, gender and relation, and the site shows the
name in the visitor's language. Each card's text block (left of the
photo, below the serial and EPIC strip) is pasted into one sheet per page and
read by Tesseract once; its words go back to their card by position. Only the
fields the dataset needs are parsed. The relative's name is never parsed:
its line is dropped here, in memory. The elector's own name is returned only
when asked (`names=True`), for the site's search result, where it is stored
encrypted under the EPIC (docs/site-voter-details.md); it never goes into the
open dataset. The house number is returned only so the caller can turn it
into a keyed hash (household) and drop it.

The cloud run splits the work: a VM cuts each page into one sheet image
(`page_sheet`: every card with its photo blanked, stacked), Actions read the
sheets (`read_sheet`). Each card's first line is its serial box and its EPIC
as printed (`serial`, `epic_raw`, letters and digits as Tesseract sees them:
for checking the print against the published EPIC, never published).
"""
from __future__ import annotations

import csv
import io
import re
import subprocess

from PIL import Image

import crops as C

GAP = 12
REL = re.compile(r"\b(Father|Husband|Mother|Wife|Other|Others|Guru)\s*'?s?\s*Name", re.I)
AGE = re.compile(r'\bAge\s*[:;.,]?\s*(\d{1,3})\b', re.I)
GENDER = re.compile(r'\bGender\s*[:;.,]?\s*(Male|Female|Third\s*Gender|Transgender|Others?|TG)\b', re.I)
HOUSE = re.compile(r'House\s*Number\s*[:;.,]?\s*(.*?)\s*(?:\bAge\b|$)', re.I)
GENDERS = {'male': 'M', 'female': 'F'}
# The Kannada roll's labels: ಹೆಸರು name, ತಂದೆಯ / ಗಂಡನ / ತಾಯಿಯ ಹೆಸರು father's /
# husband's / mother's name, ಇತರೆ other, ಮನೆಯ ಸಂಖ್ಯೆ house number, ವಯಸ್ಸು age,
# ಲಿಂಗ gender: ಗಂಡು male, ಹೆಣ್ಣು female, ಇತರೆ third gender.
KAN_REL = re.compile(r'(ತಂದೆಯ|ಗಂಡನ|ತಾಯಿಯ|ಇತರೆ|ಇತರರ)\s*ಹೆಸರು')
KAN_REL_NAMES = {'ತಂದೆಯ': 'Father', 'ಗಂಡನ': 'Husband', 'ತಾಯಿಯ': 'Mother', 'ಇತರೆ': 'Other', 'ಇತರರ': 'Other'}
KAN_AGE = re.compile(r'ವಯಸ್ಸು\s*[:;.,]?\s*(\d{1,3})')
KAN_GENDER = re.compile(r'ಲಿಂಗ\s*[:;.,]?\s*(ಗಂಡು|ಹೆಣ್ಣು|ಇತರೆ)')
KAN_GENDERS = {'ಗಂಡು': 'M', 'ಹೆಣ್ಣು': 'F', 'ಇತರೆ': 'TG'}
KAN_HOUSE = re.compile(r'ಮನೆಯ\s*ಸಂಖ್ಯೆ\s*[:;.,]?\s*(.*?)\s*(?:ವಯಸ್ಸು|$)')
KAN_NAME = re.compile(r'^\s*ಹೆಸರು\s*[:;.,]?\s*(.+?)\s*$', re.M)


def card_image(g: Image.Image, box: tuple) -> Image.Image:
    """The whole card, its photo painted white: serial box and EPIC on the first line."""
    left, top, right, bottom = box
    w, h = right - left, bottom - top
    im = g.crop((left + 1, top + 1, right - 1, bottom - 2))
    im.paste(255, (int(0.70 * w), int(0.17 * h), im.width, im.height))
    return im


def page_sheet(img: Image.Image) -> tuple[Image.Image | None, list]:
    """(one sheet of the page's cards, stacked, [(top, bottom)] per cell): what Tesseract reads."""
    boxes = []
    C.cut_page(img, boxes)
    g = img.convert('L')
    crops = [card_image(g, b) for b in boxes]
    if not crops:
        return None, []
    sheet = Image.new('L', (max(c.width for c in crops), sum(c.height + GAP for c in crops)), 255)
    spans, y = [], 0
    for c in crops:
        sheet.paste(c, (0, y))
        spans.append((y, y + c.height))
        y += c.height + GAP
    return sheet.point(lambda v: 255 if v > 160 else 0).convert('1'), spans


def sheet_text(sheet: Image.Image, spans: list, lang: str = 'eng') -> dict[int, str]:
    """cell -> the card's text as Tesseract read it (one call per sheet)."""
    buf = io.BytesIO()
    sheet.save(buf, format='PNG')
    out = subprocess.run([C.R._tesseract_cmd(), 'stdin', 'stdout', '--psm', '6', '-l', 'kan+eng' if lang == 'kan' else 'eng', 'tsv'],
                         input=buf.getvalue(), capture_output=True, check=False).stdout.decode('utf8', 'replace')
    lines: dict[tuple, list] = {}
    for row in csv.DictReader(io.StringIO(out), delimiter='\t', quoting=csv.QUOTE_NONE):
        word = (row.get('text') or '').strip()
        if not word:
            continue
        mid = int(row['top']) + int(row['height']) // 2
        cell = next((i for i, (a, b) in enumerate(spans) if a <= mid < b + GAP), None)
        if cell is None:
            continue
        lines.setdefault((cell, row['block_num'], row['par_num'], row['line_num']), []).append(
            (int(row['left']), word))
    text: dict[int, list] = {}
    for (cell, *_), words in sorted(lines.items(), key=lambda kv: (kv[0][0], int(kv[0][1]), int(kv[0][2]), int(kv[0][3]))):
        text.setdefault(cell, []).append(' '.join(w for _, w in sorted(words)))
    return {c: '\n'.join(t) for c, t in text.items()}


NAME = re.compile(r'^\s*Name\s*[:;.,]?\s*(.+?)\s*$', re.I | re.M)


FIRST = re.compile(r'^\D*?(\d{1,4})\b.*?([A-Za-z0-9/]{6,16})\s*$')


def head(text: str) -> dict:
    """The first line: serial box and the EPIC as printed."""
    line = text.splitlines()[0] if text else ''
    m = FIRST.match(line)
    return {'serial': int(m.group(1)) if m else None, 'epic_raw': m.group(2).upper() if m else None}


def parse_kan(text: str, names: bool = False) -> dict:
    rel = KAN_REL.search(text)
    age = KAN_AGE.search(text)
    gen = KAN_GENDER.search(text)
    flat = ' '.join(l for l in text.splitlines() if not re.search(r'ಹೆಸರು', l))
    house = KAN_HOUSE.search(flat)
    out = {
        'relation': KAN_REL_NAMES[rel.group(1)] if rel else None,
        'age': int(age.group(1)) if age and 18 <= int(age.group(1)) <= 125 else None,
        'gender': KAN_GENDERS[gen.group(1)] if gen else None,
        'house': house.group(1).strip(' ,.') if house and house.group(1).strip(' ,.') else None,
    }
    if names:
        name = KAN_NAME.search(text)
        out['name'] = name.group(1) if name else None
    return out


def parse(text: str, names: bool = False) -> dict:
    rel = REL.search(text)
    age = AGE.search(text)
    gen = GENDER.search(text)
    flat = ' '.join(l for l in text.splitlines() if not re.match(r'\s*(Name|Father|Husband|Mother|Wife|Other|Guru)', l, re.I))
    house = HOUSE.search(flat)
    g = gen.group(1).lower().replace(' ', '') if gen else None
    out = {
        'relation': rel.group(1).title().rstrip('s') if rel else None,
        'age': int(age.group(1)) if age and 18 <= int(age.group(1)) <= 125 else None,
        'gender': GENDERS.get(g, 'TG') if g else None,
        'house': house.group(1).strip(' ,.') if house and house.group(1).strip(' ,.') else None,
    }
    if names:
        name = NAME.search(text)
        out['name'] = name.group(1) if name else None
    return out


def read_sheet(sheet: Image.Image, spans: list, lang: str = 'eng', names: bool = False) -> dict[int, dict]:
    p = parse_kan if lang == 'kan' else parse
    return {cell: {**head(t), **p(t, names)} for cell, t in sheet_text(sheet, spans, lang).items()}


def read_page(img: Image.Image, lang: str = 'eng', names: bool = False) -> dict[int, dict]:
    sheet, spans = page_sheet(img)
    return read_sheet(sheet, spans, lang, names) if sheet is not None else {}
