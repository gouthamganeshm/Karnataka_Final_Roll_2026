"""Age, gender, relation type and house number of every card, from the English roll.

    from fields import read_page
    read_page(img) -> {cell: {'age', 'gender', 'relation', 'house'}}

For the open dataset (docs/dataset.md). Each card's text block (left of the
photo, below the serial and EPIC strip) is pasted into one sheet per page and
read by Tesseract once; its words go back to their card by position. Only the
fields the dataset needs are parsed. The elector's and the relative's NAMES
are deliberately never parsed or kept: the text lines that carry them are
dropped here, in memory. The house number is returned only so the caller can
turn it into a keyed hash (household) and drop it.
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


def text_box(box: tuple) -> tuple:
    """The card's text block: below the serial/EPIC strip, left of the photo."""
    left, top, right, bottom = box
    w, h = right - left, bottom - top
    return (left + int(0.01 * w), top + int(0.17 * h), left + int(0.70 * w), bottom - 2)


def card_text(img: Image.Image, boxes: list) -> dict[int, str]:
    """cell -> the card's text as Tesseract read it (one call per page)."""
    g = img.convert('L')
    crops = [g.crop(text_box(b)) for b in boxes]
    if not crops:
        return {}
    sheet = Image.new('L', (max(c.width for c in crops), sum(c.height + GAP for c in crops)), 255)
    spans, y = [], 0
    for c in crops:
        sheet.paste(c, (0, y))
        spans.append((y, y + c.height))
        y += c.height + GAP
    buf = io.BytesIO()
    sheet.save(buf, format='PNG')
    out = subprocess.run([C.R._tesseract_cmd(), 'stdin', 'stdout', '--psm', '6', 'tsv'],
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


def parse(text: str) -> dict:
    rel = REL.search(text)
    age = AGE.search(text)
    gen = GENDER.search(text)
    flat = ' '.join(l for l in text.splitlines() if not re.match(r'\s*(Name|Father|Husband|Mother|Wife|Other|Guru)', l, re.I))
    house = HOUSE.search(flat)
    g = gen.group(1).lower().replace(' ', '') if gen else None
    return {
        'relation': rel.group(1).title().rstrip('s') if rel else None,
        'age': int(age.group(1)) if age and 18 <= int(age.group(1)) <= 125 else None,
        'gender': GENDERS.get(g, 'TG') if g else None,
        'house': house.group(1).strip(' ,.') if house and house.group(1).strip(' ,.') else None,
    }


def read_page(img: Image.Image) -> dict[int, dict]:
    boxes = []
    C.cut_page(img, boxes)
    return {cell: parse(t) for cell, t in card_text(img, boxes).items()}
