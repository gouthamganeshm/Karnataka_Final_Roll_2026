"""Open dataset v3: read again the cards whose age or gender is empty.

    GH_TOKEN=... python scripts/home/ds_reread.py --vm K         # systemd ds-reread@K: every 4th AC
    GH_TOKEN=... python scripts/home/ds_reread.py --ac 1 --dry   # one AC, written locally only

The first reading (ds_read.py) read each card's whole text block and needed
the label "Gender :" before the word. On a struck-off card the DELETED stamp
crosses that label, so nearly every struck-off entry came out without a
gender, though the word Male or Female beside it is plain. Here only the
card's last line (Age : NN Gender : Male, cut as ds_review.strip does: no
name, no house number on it) is read, and the word is taken wherever it
stands on that line.

Per AC, from ds-<ac>.csv.gz on <tag>-ds:
  targets   every entry with no age or no gender (live or struck off), and
            the age of every struck-off entry once more (the stamp made those
            less sure);
  controls  up to two entries per page with both read, read the same way:
            the English page is the one whose card count and control ages
            match (ds_join.offset's shift, found per booth), and the share of
            controls read alike measures this reading;
  pages     a page with nothing read on any card is read whole, as
            ds_read.py does (house number hashed at once, as ds_join.py).
Writes dsfix-<ac>.json to <tag>-ds:
  fills     a value where the dataset has none;
  differs   a value read here unlike the dataset's: not applied; a person
            reads the card (reference/dataset-corrections.json);
  pages     age, gender, relation, household_hash of the pages read whole.
No name, EPIC or house number is in it.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import gzip
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import ds_join  # noqa: E402
import ds_review  # noqa: E402
import release  # noqa: E402
import run  # noqa: E402

TAG = release.TAG
DS = f'{TAG}-ds'
OUT = ROOT / 'cache' / 'ds' / 'reread'
SHIFTS = (0, 1, -1, 2, -2)
CONTROLS = 2
RETRY_WAITS = (60, 300, 900, 1800, 3600)
AGE = re.compile(r'A\s*[gq9]\s*[e3c]\s*\W{0,3}\s*(\d{1,3})\b', re.I)
NUM = re.compile(r'\b(\d{2,3})\b')


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def parse_line(text: str) -> tuple[int | None, str | None]:
    """(age, gender) from the card's last line, the label optional."""
    m = AGE.search(text) or NUM.search(text)
    age = int(m.group(1)) if m and 18 <= int(m.group(1)) <= 120 else None
    low = [w.lower() for w in re.findall(r'[A-Za-z]{3,}', text)]
    if any(w in ('third', 'transgender', 'others', 'other') for w in low):
        return age, 'TG'
    if not low:
        return age, None
    # The value is the line's last word; the stamp garbles the label before it
    # and at times the word itself ("fale"): a word about as near to Male as
    # to Female is left unread.
    w = low[-1]
    f = difflib.SequenceMatcher(None, w, 'female').ratio()
    m = difflib.SequenceMatcher(None, w, 'male').ratio()
    if max(f, m) < 0.75 or abs(f - m) < 0.1:
        return age, None
    return age, 'F' if f > m else 'M'


def one_page(doc, pg: int):
    import crops as C
    import fitz
    if not 0 <= pg < doc.page_count:
        return None, []
    one = fitz.open()
    one.insert_pdf(doc, from_page=pg, to_page=pg)
    img = next(C.page_images(one))[0]
    boxes = []
    C.cut_page(img, boxes)
    return img, boxes


def read_strips(items: list) -> list[tuple]:
    """[(img, box)] -> [(age, gender)] by one Tesseract call over their strips."""
    from PIL import Image
    import fields as F
    strips = [ds_review.strip(img, box) for img, box in items]
    if not strips:
        return []
    w = max(s.width for s in strips) + 20
    sheet = Image.new('L', (w, sum(s.height + F.GAP + 8 for s in strips)), 255)
    spans, y = [], 4
    for s in strips:
        sheet.paste(s, (10, y))
        spans.append((y, y + s.height))
        y += s.height + F.GAP + 8
    text = F.sheet_text(sheet, spans, 'eng')
    return [parse_line(text.get(i, '')) for i in range(len(strips))]


def sheet_of(g, boxes: list) -> tuple:
    """fields.page_sheet, for boxes already cut."""
    from PIL import Image
    import fields as F
    crops = [g.crop(F.text_box(b)) for b in boxes]
    sheet = Image.new('L', (max(c.width for c in crops), sum(c.height + F.GAP for c in crops)), 255)
    spans, y = [], 0
    for c in crops:
        sheet.paste(c, (0, y))
        spans.append((y, y + c.height))
        y += c.height + F.GAP
    return sheet, spans


def booth(ac: int, part: int, rows: list[dict], data: bytes, k: bytes, stats: dict) -> dict:
    """Fills, differs and whole pages of one booth."""
    import fitz
    import numpy as np
    import crops as C
    import fields as F
    per_page: dict[int, list] = {}
    for r in rows:
        per_page.setdefault(int(r['page']), []).append(r)
    whole = [p for p, rs in per_page.items() if all(not (r['age'] or r['gender'] or r['relation']) for r in rs)]
    want: dict[int, list] = {}
    for p, rs in per_page.items():
        if p in whole:
            continue
        tg = [r for r in rs if not r['age'] or not r['gender'] or r['status'] == 'deleted']
        if not tg:
            continue
        ctl = [r for r in rs if r['status'] == 'live' and r['age'] and r['gender']][:CONTROLS]
        want[p] = [(r, False) for r in tg] + [(r, True) for r in ctl]
    out = {'fills': [], 'differs': [], 'pages': []}
    if not want and not whole:
        return out
    doc = fitz.open(stream=data, filetype='pdf')
    pages: dict[int, tuple] = {}

    cols = []

    def page(pg):
        if pg not in pages:
            img, boxes = one_page(doc, pg)
            # A page whose column rules were not found (a few booths' English
            # PDFs: the gap between cards taken for columns) is cut by the
            # columns of a page of the same PDF that was, at its own rows.
            if img is not None and not boxes and template(pg):
                grid = C.R.find_grid(np.array(img.convert('L')) < 128)
                if grid is not None and len(grid.bands) <= 10:
                    boxes = [(l, t, r, b) for t, b in grid.bands for l, r in cols]
                    stats['pages_regridded'] += 1
            pages[pg] = (img, boxes)
        return pages[pg]

    def template(pg):
        if not cols:
            for q in range(2, doc.page_count):
                if q != pg:
                    bx = pages[q][1] if q in pages else one_page(doc, q)[1]
                    if len(bx) == 30:
                        cols.extend(sorted({(l, r) for l, _, r, _ in bx}))
                        break
        return len(cols) == 3

    # The shift: every page wanted holds as many cards in the English roll.
    need = sorted(set(want) | set(whole))
    best, shift = -1, None
    for d in SHIFTS:
        n = sum(len(page(p + d)[1]) == len(per_page[p]) for p in need)
        if n > best:
            best, shift = n, d
        if n == len(need):
            break
    ok = [p for p in need if len(page(p + shift)[1]) == len(per_page[p])]
    # A page where the English roll holds more cards than the verified rows (a
    # card with no EPIC is not a row) keeps its cells; it is taken only when
    # every control on it, at least two, reads alike.
    loose = [p for p in want if p not in ok
             and len(page(p + shift)[1]) > max(int(r['card']) for r in per_page[p])
             and sum(c for _, c in want[p]) >= 2]
    items, refs = [], []
    for p in ok + loose:
        if p in want:
            img, boxes = page(p + shift)
            g = img.convert('L')
            for r, ctl in want[p]:
                items.append((g, boxes[int(r['card'])]))
                refs.append((r, ctl))
    reads = read_strips(items)
    for p in loose:
        if any(ctl and int(r['page']) == p and (a != int(r['age']) or g != r['gender'])
               for (r, ctl), (a, g) in zip(refs, reads)):
            keep = [i for i, (r, _) in enumerate(refs) if int(r['page']) != p]
            refs, reads = [refs[i] for i in keep], [reads[i] for i in keep]
        else:
            ok.append(p)
    stats['pages_differ'] += len(need) - len(ok)
    stats['targets_skipped'] += sum(not c for p in need if p not in ok for _, c in want.get(p, []))
    stats['skipped_pages'] += [[part, p] for p in need if p not in ok]
    # The controls say whether this booth was read right (shift, crop); a
    # booth whose controls mostly disagree gives nothing.
    agree = [(a == int(r['age']), g == r['gender']) for (r, ctl), (a, g) in zip(refs, reads) if ctl and a is not None]
    stats['controls'] += len(agree)
    stats['control_age_agree'] += sum(x for x, _ in agree)
    stats['control_gender_agree'] += sum(y for _, y in agree)
    if agree and sum(x for x, _ in agree) < len(agree) / 2:
        stats['booths_controls_failed'] += 1
        return out
    for (r, ctl), (a, g) in zip(refs, reads):
        if ctl:
            continue
        stats['targets'] += 1
        at = [part, int(r['page']), int(r['card'])]
        for f, v in (('age', a), ('gender', g)):
            if v is None:
                stats[f'{f}_unread'] += 1
                continue
            old = r[f]
            if not old:
                out['fills'].append(at + [f, v])
                stats[f'fill_{f}'] += 1
            elif str(v) != old:
                out['differs'].append(at + [r['serial'], r['status'], f, int(old) if f == 'age' else old, v])
                stats[f'differ_{f}'] += 1
            else:
                stats[f'same_{f}'] += 1
    for p in whole:
        if p not in ok:
            continue
        img, boxes = page(p + shift)
        got = F.read_sheet(*sheet_of(img.convert('L'), boxes), 'eng')
        for cell in sorted(int(r['card']) for r in per_page[p]):
            c = got.get(cell) or {}
            house = ds_join.house_norm(c.get('house'))
            age = c.get('age') if isinstance(c.get('age'), int) and 18 <= c['age'] <= 120 else None
            out['pages'].append([part, p, cell, age, c.get('gender'), c.get('relation'),
                                 ds_join.mac(k, f'{ac}|{part}|{house}', 16) if house else None])
            stats['page_cards'] += 1
    return out


def reread(ac: int, k: bytes, dry: bool) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    p, = ds_join.get(DS, [f'ds-{ac}.csv.gz'], str(OUT))
    by_part: dict[int, list] = {}
    with gzip.open(p, 'rt', encoding='utf8') as f:
        for r in csv.DictReader(f):
            by_part.setdefault(int(r['part']), []).append(r)
    p.unlink()
    parts = sorted(pt for pt, rs in by_part.items()
                   if any(not r['age'] or not r['gender'] or r['status'] == 'deleted' for r in rs))
    stats = dict.fromkeys(['booths', 'targets', 'controls', 'control_age_agree', 'control_gender_agree',
                           'booths_controls_failed', 'pages_differ', 'pages_regridded', 'targets_skipped', 'page_cards', 'age_unread', 'gender_unread',
                           'fill_age', 'fill_gender', 'differ_age', 'differ_gender', 'same_age', 'same_gender'], 0)
    stats['skipped_pages'] = []
    res = {'ac': ac, 'key_id': ds_join.key_id(k), 'fills': [], 'differs': [], 'pages': []}
    t = time.time()

    def get(part):
        return part, run.fetch(run.url(ac, part, 'eng'))

    def take(part, data):
        o = booth(ac, part, by_part[part], data, k, stats)
        for x in res.keys() & o.keys():
            res[x] += o[x]
        stats['booths'] += 1

    missing = []
    with ThreadPoolExecutor(4) as pool:
        for i, (part, data) in enumerate(pool.map(get, parts)):
            if data is None:
                missing.append(part)
            else:
                take(part, data)
            if (i + 1) % 50 == 0:
                log(f'AC {ac}: {i + 1}/{len(parts)} booths ({time.time() - t:.0f}s)')
    for wait in RETRY_WAITS:
        if not missing:
            break
        log(f'AC {ac}: {len(missing)} PDFs did not come; trying again in {wait}s')
        time.sleep(wait)
        still = []
        for part in missing:
            data = run.fetch(run.url(ac, part, 'eng'))
            if data is None:
                still.append(part)
            else:
                take(part, data)
        missing = still
    if missing:
        raise RuntimeError(f'AC {ac}: PDFs of parts {missing} not served')
    stats['seconds'] = round(time.time() - t)
    res['stats'] = stats
    dest = OUT / f'dsfix-{ac}.json'
    dest.write_text(json.dumps(res), 'utf8')
    if not dry:
        release.TAG = DS
        try:
            release.upload(str(dest))
        finally:
            release.TAG = TAG
        dest.unlink()
    return stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vm', type=int)
    ap.add_argument('--ac', type=int, nargs='*')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    k = ds_join.key()
    acs = args.ac or [a for a in range(1, 225) if (a - 1) % 4 == args.vm - 1]
    while True:
        have = ds_join.listing(DS, fresh=True)
        left = [a for a in acs if args.dry or f'dsfix-{a}.json' not in have]
        if not left:
            log('every AC read again')
            return 0
        for ac in left:
            try:
                log(f'AC {ac}: {reread(ac, k, args.dry)}')
            except Exception as e:  # noqa: BLE001 - an outage: the next round tries again
                log(f'AC {ac}: {e!r}; later')
                time.sleep(300)
        if args.dry:
            return 0


if __name__ == '__main__':
    sys.exit(main())
