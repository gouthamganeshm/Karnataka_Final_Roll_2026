"""Open dataset: the entries a person looks at on the card image.

    GH_TOKEN=... python scripts/home/ds_review.py find --vm K        # every 4th AC -> cache/ds/review/find-K.json
    GH_TOKEN=... python scripts/home/ds_review.py sheets FILE.json   # card strips -> cache/ds/review/sheet-NNN.png

find: every entry whose age or gender disagrees with the second reading
(~/.ds_xcheck_url, as ds_release.py), by AC, part and confirmed serial.
sheets: for each, the age-and-gender line of the card, cut from the booth's
English PDF (the page lined up as ds_join.py does), stacked with what each
reading says, so a person reads the printed value. Only that line is cut:
no name is on it. The sheets stay on the VM and private drafts.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import ds_join  # noqa: E402
import ds_release  # noqa: E402
import release  # noqa: E402
import run  # noqa: E402

TAG = release.TAG
DS = f'{TAG}-ds'
OUT = ROOT / 'cache' / 'ds' / 'review'


def find(acs: list[int]) -> list[list]:
    out = []
    tmp = OUT / 'tmp'
    tmp.mkdir(parents=True, exist_ok=True)
    for ac in acs:
        dc = ds_release.dc_rows(ac, tmp)
        if dc is None:
            print(f'AC {ac}: second reading not available', flush=True)
            continue
        p, = ds_join.get(DS, [f'ds-{ac}.csv.gz'], str(tmp))
        n = 0
        with gzip.open(p, 'rt', encoding='utf8') as f:
            for r in csv.DictReader(f):
                if r['serial_sure'] != '1' or not r['serial']:
                    continue
                d = dc.get((int(r['part']), int(r['serial'])))
                if d is None:
                    continue
                age, gender = d
                if r['age'] and age is not None and int(r['age']) != age:
                    out.append([ac, int(r['part']), int(r['page']), int(r['card']), int(r['serial']), 'age', r['age'], age])
                    n += 1
                if r['gender'] and gender and r['gender'] != gender:
                    out.append([ac, int(r['part']), int(r['page']), int(r['card']), int(r['serial']), 'gender', r['gender'], gender])
                    n += 1
        p.unlink()
        print(f'AC {ac}: {n} disagreements', flush=True)
    return out


def eng_offset(ac: int, part: int, cache: dict) -> int:
    """English page = Kannada page + this, for one booth (ds_join.offset)."""
    if ac not in cache:
        tmp = OUT / 'tmp'
        rd, = ds_join.get(TAG, [f'live-rows-{ac}.jsonl.gz'], str(tmp))
        dr, = ds_join.get(DS, [f'dsread-{ac}.json.gz'], str(tmp))
        per = {}
        with gzip.open(rd, 'rt', encoding='utf8') as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r['page'] > 1:
                        per.setdefault(r['part'], {})
                        per[r['part']][r['page']] = per[r['part']].get(r['page'], 0) + 1
        with gzip.open(dr, 'rt', encoding='utf8') as f:
            reads = json.load(f)['reads']
        cache[ac] = {p: ds_join.offset(pages, {int(k): len(v) for k, v in reads.get(f'{p}.eng.zip', {}).items()})
                     for p, pages in per.items()}
        rd.unlink()
        dr.unlink()
    return cache[ac].get(part, 0)


def strip(img, box, above: int = 0):
    """The card's last text line (age, gender), left of the photo: the
    lowest band of ink rows in the card's text block."""
    import numpy as np
    import fields as F
    t = img.crop(F.text_box(box))
    ink = (np.array(t) < 140).sum(axis=1) > 2
    bands, start = [], None
    for y, on in enumerate(list(ink) + [False]):
        if on and start is None:
            start = y
        elif not on and start is not None:
            if y - start >= 4:
                bands.append((start, y))
            start = None
    if not bands:
        return t
    # Only the last line, measured up from the bottom of the ink: on a struck-off
    # card the DELETED stamp joins every line into one band, and the lines
    # above hold names.
    # `above`: lines of ink to step over (a stamp's tail below the last line).
    b = bands[-1 - above][1] if len(bands) > above else bands[-1][1]
    line = int(0.13 * t.height)
    return t.crop((0, max(0, b - line), t.width, min(t.height, b + 4)))


def sheets(items: list[list], per_sheet: int = 24, above: int = 0) -> list[Path]:
    import fitz
    from PIL import Image, ImageDraw
    import crops as C
    offs, strips = {}, []
    by_booth = {}
    for it in items:
        by_booth.setdefault((it[0], it[1]), []).append(it)
    for (ac, part), its in sorted(by_booth.items()):
        data = run.fetch(run.url(ac, part, 'eng'))
        if data is None:
            print(f'AC {ac} part {part}: PDF not served', flush=True)
            continue
        d = eng_offset(ac, part, offs)
        doc = fitz.open(stream=data, filetype='pdf')
        pages = {}
        for it in its:
            pg = it[2] + d
            if pg not in pages:
                img = None
                if pg < doc.page_count:   # render just this page
                    one = fitz.open()
                    one.insert_pdf(doc, from_page=pg, to_page=pg)
                    img = next(C.page_images(one))[0]
                boxes = []
                if img is not None:
                    C.cut_page(img, boxes)
                pages[pg] = (img, boxes)
            img, boxes = pages[pg]
            if img is None or it[3] >= len(boxes):
                print(f'{it[:5]}: card not found on page {pg}', flush=True)
                continue
            strips.append((it, strip(img.convert('L'), boxes[it[3]], above)))
    files = []
    for k in range(0, len(strips), per_sheet):
        chunk = strips[k:k + per_sheet]
        w = max(s.width for _, s in chunk) + 420
        hgt = sum(s.height + 14 for _, s in chunk) + 10
        sheet = Image.new('L', (w, hgt), 255)
        dr = ImageDraw.Draw(sheet)
        y = 5
        for n, (it, s) in enumerate(chunk):
            sheet.paste(s, (410, y))
            dr.text((6, y + 4), f'#{k + n:04d} AC{it[0]} p{it[1]} s{it[4]} {it[5]}', fill=0)
            dr.text((6, y + 20), f'ours {it[6]}  other {it[7]}', fill=0)
            y += s.height + 14
            dr.line((0, y - 7, w, y - 7), fill=200)
        p = OUT / f'sheet-{k // per_sheet:03d}.png'
        sheet.save(p)
        files.append(p)
    (OUT / 'sheets.json').write_text(json.dumps([it for it, _ in strips]), 'utf8')
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['find', 'sheets'])
    ap.add_argument('file', nargs='?')
    ap.add_argument('--vm', type=int)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.cmd == 'find':
        acs = [a for a in range(1, 225) if (a - 1) % 4 == args.vm - 1]
        res = find(acs)
        (OUT / f'find-{args.vm}.json').write_text(json.dumps(res), 'utf8')
        print(f'{len(res)} disagreements', flush=True)
    else:
        items = json.loads(Path(args.file).read_text('utf8'))
        print(f'{len(sheets(items))} sheets', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
