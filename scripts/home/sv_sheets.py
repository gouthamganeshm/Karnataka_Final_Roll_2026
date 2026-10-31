"""Review sheets for the 25% sample verification (docs/sample-verification.md, step 6).

    python scripts/home/sv_sheets.py AC [AC ...] [--out cache/sv/sheets]

From svres-<ac>.json.gz: tier A (every card not `ok` whose two rolls agree),
tier B (every other card not `ok`) and tier C (the random `ok` audit). Each
row is the whole card cut from the Kannada PDF (left) and the English PDF
(right), fetched afresh one booth at a time, with the readings and what the
site holds under it. Writes OUT/<ac>/<tier>-NNN.png (8 cards a sheet) and
OUT/<ac>/index.json (row number -> card). Holds EPICs and names: keep OUT off
git and shared places.
"""
from __future__ import annotations

import argparse
import gc
import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import release  # noqa: E402
import run  # noqa: E402

TAG = release.TAG
SVR = f'{TAG}-svr'
SV = ROOT / 'cache' / 'sv'
W = 620


def page_cards(data: bytes, pg: int, cells: set) -> dict:
    import fitz
    import crops as C
    doc = fitz.open(stream=data, filetype='pdf')
    if pg >= doc.page_count:
        return {}
    one = fitz.open()
    one.insert_pdf(doc, from_page=pg, to_page=pg)
    img, _ = next(iter(C.page_images(one)))
    boxes = []
    C.cut_page(img, boxes)
    g = img.convert('L')
    out = {}
    for c in cells:
        if c < len(boxes):
            im = g.crop(boxes[c])
            out[c] = im.resize((W, int(im.height * W / im.width)))
    return out


def label(i: int, ac: int, it: dict) -> str:
    site = '; '.join(f"{h['ac']}/{h['part']}/{'~' if h['approx'] else ''}{h['serial']}{' DEL' if h['deleted'] else ''}"
                     for h in it.get('site') or []) or 'not on site'
    k, e = it.get('kan'), it.get('eng')
    rd = lambda x: f"{x[0]}{'' if x[1] else '?'} s{x[4] if x[4] is not None else '?' + str(x[3])}{' X' if x[5] == 'X' else ''}" if x else '-'  # noqa: E731
    return (f"#{i} AC {ac} {it['part']}/{it['page']}/{it['cell']}  {it['result'].upper()} ({it['how']})  "
            f"kan {rd(k)} | eng {rd(e)} | site: {site}")


def sheets(ac: int, out: Path) -> int:
    from PIL import Image, ImageDraw
    src = SV / f'svres-{ac}.json.gz'
    if not src.exists():
        release.TAG = SVR
        try:
            release.fetch(str(SV), [src.name])
        finally:
            release.TAG = TAG
    with gzip.open(src, 'rt', encoding='utf8') as f:
        res = json.load(f)
    cards = [it for it in res['items'] if 'cell' in it]
    tiers = {'A': [it for it in cards if it['result'] != 'ok' and it['how'] == 'settled'],
             'B': [it for it in cards if it['result'] != 'ok' and it['how'] != 'settled'],
             'C': res['audit']}
    d = out / str(ac)
    d.mkdir(parents=True, exist_ok=True)
    index, n_sheets = {}, 0
    for tier, items in tiers.items():
        rows, n = [], 0
        by_booth = {}
        for it in items:
            by_booth.setdefault(it['part'], []).append(it)
        for part, its in sorted(by_booth.items()):
            got = {}
            for lang in ('kan', 'eng'):
                data = run.fetch(run.url(ac, part, lang))
                if not data:
                    continue
                for pg in sorted({it['page'] for it in its}):
                    for c, im in page_cards(data, pg, {it['cell'] for it in its if it['page'] == pg}).items():
                        got[(pg, c, lang)] = im
                del data
                gc.collect()
            for it in its:
                i = len(index)
                index[i] = {'tier': tier, **it}
                k, e = got.get((it['page'], it['cell'], 'kan')), got.get((it['page'], it['cell'], 'eng'))
                h = max([x.height for x in (k, e) if x] + [60])
                row = Image.new('L', (2 * W + 30, h + 24), 255)
                if k:
                    row.paste(k, (5, 0))
                if e:
                    row.paste(e, (W + 20, 0))
                dr = ImageDraw.Draw(row)
                dr.text((5, h + 6), label(i, ac, it), fill=0)
                dr.line((0, h + 23, 2 * W + 30, h + 23), fill=0)
                rows.append(row)
        for s in range(0, len(rows), 8):
            rs = rows[s:s + 8]
            sh = Image.new('L', (2 * W + 30, sum(r.height for r in rs)), 255)
            y = 0
            for r in rs:
                sh.paste(r, (0, y))
                y += r.height
            n += 1
            sh.resize((1000, sh.height * 1000 // sh.width)).save(d / f'{tier}-{n:03d}.png')
        n_sheets += n
        print(f'AC {ac} tier {tier}: {len(items)} cards, {n} sheets', flush=True)
    (d / 'index.json').write_text(json.dumps(index), 'utf8')
    return n_sheets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('acs', nargs='+', type=int)
    ap.add_argument('--out', default=str(SV / 'sheets'))
    a = ap.parse_args()
    for ac in a.acs:
        sheets(ac, Path(a.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
