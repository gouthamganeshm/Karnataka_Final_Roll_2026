"""Review sheets for what sv_resolve.py left: doubts, a sample of slips, page counts.

    python scripts/home/sv_review.py AC [AC ...] [--slips 3] [--out cache/sv/review]

Tier D: every `doubt` card of resolve-<ac>.json. Tier S: every slip whose
two rolls agreed on the EPIC, and up to --slips per AC and look-alike pattern
of the rest (seeded), so each pattern is seen on the cards. Tier P: every
page whose site count differs from its cards, as the whole page, labelled
with what the readings and the site say for each cell. Kannada card left,
English right (P: the Kannada page). Writes OUT/<ac>/<tier>-NNN.png and
OUT/<ac>/index.json. Holds EPICs and names: keep OUT off git and shared places.
"""
from __future__ import annotations

import argparse
import gc
import gzip
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import release  # noqa: E402
import run  # noqa: E402
import sv_sheets  # noqa: E402

SV = ROOT / 'cache' / 'sv'
W = sv_sheets.W


def pattern(r: dict) -> str:
    a, b = r['from_reading'], r['site_variant']
    return ' '.join(f'{i}:{x}>{y}' for i, (x, y) in enumerate(zip(a, b)) if x != y)


def pick(ac: int, items: list, per: int) -> tuple[list, list]:
    doubts = [r for r in items if r['verdict'] == 'doubt']
    slips = [r for r in items if r['verdict'] == 'slip']
    keep = [r for r in slips if r['how'] == 'settled']
    by = {}
    for r in slips:
        if r['how'] != 'settled':
            by.setdefault(pattern(r), []).append(r)
    rng = random.Random(f'sv-review-{ac}')
    for pat, rs in sorted(by.items()):
        keep += rng.sample(rs, min(per, len(rs)))
    return doubts, keep


def page_items(ac: int) -> list:
    with gzip.open(SV / 'res' / f'svres-{ac}.json.gz', 'rt', encoding='utf8') as f:
        return [it for it in json.load(f)['items'] if it.get('result') == 'page']


def page_label(ac: int, it: dict, site, reads: dict) -> list[str]:
    """One line per cell: readings' EPIC and serials, and where the site has it."""
    lines = [f"AC {ac} part {it['part']} page {it['page']}: serials {it['range'][0]}-{it['range'][1]}, "
             f"PDF {it['pdf']} cards, site holds {it['site']} there"]
    kc = {c[0]: c for c in reads.get(f"{it['part']}.kan.zip", {}).get(str(it['page']), [])}
    ec = {c[0]: c for c in reads.get(f"{it['part']}.eng.zip", {}).get(str(it['page']), [])}
    for cell in sorted(set(kc) | set(ec)):
        k, e = kc.get(cell), ec.get(cell)
        hits = []
        for c in {x[1] for x in (k, e) if x and x[1]}:
            hits += [f"{h['part']}/{'~' if h['approx'] else ''}{h['serial']}{' DEL' if h['deleted'] else ''}"
                     for h in site.lookup(c) if h['ac'] == ac]
        lines.append(f"  cell {cell}: kan s{k[5] if k else '-'} ({k[4] if k else ''}) eng s{e[5] if e else '-'} "
                     f"({e[4] if e else ''}) site {', '.join(sorted(set(hits))) or 'none'}")
    return lines


def render_rows(ac: int, cards: list, tier: str, d: Path, index: dict, extra=lambda r: '') -> int:
    from PIL import Image, ImageDraw
    rows = []
    by_booth = {}
    for it in cards:
        by_booth.setdefault(it['part'], []).append(it)
    for part, its in sorted(by_booth.items()):
        got = {}
        for lang in ('kan', 'eng'):
            data = run.fetch(run.url(ac, part, lang))
            if not data:
                continue
            for pg in sorted({it['page'] for it in its}):
                for c, im in sv_sheets.page_cards(data, pg, {it['cell'] for it in its if it['page'] == pg}).items():
                    got[(pg, c, lang)] = im
            del data
            gc.collect()
        for it in its:
            i = len(index)
            index[i] = {'tier': tier, **it}
            k, e = got.get((it['page'], it['cell'], 'kan')), got.get((it['page'], it['cell'], 'eng'))
            h = max([x.height for x in (k, e) if x] + [60])
            row = Image.new('L', (2 * W + 30, h + 40), 255)
            if k:
                row.paste(k, (5, 0))
            if e:
                row.paste(e, (W + 20, 0))
            dr = ImageDraw.Draw(row)
            dr.text((5, h + 6), sv_sheets.label(i, ac, it), fill=0)
            dr.text((5, h + 22), extra(it), fill=0)
            dr.line((0, h + 39, 2 * W + 30, h + 39), fill=0)
            rows.append(row)
    n = 0
    for s in range(0, len(rows), 8):
        rs = rows[s:s + 8]
        sh = Image.new('L', (2 * W + 30, sum(r.height for r in rs)), 255)
        y = 0
        for r in rs:
            sh.paste(r, (0, y))
            y += r.height
        n += 1
        sh.resize((1000, sh.height * 1000 // sh.width)).save(d / f'{tier}-{n:03d}.png')
    return n


def render_pages(ac: int, pages: list, site, d: Path, index: dict) -> int:
    import fitz
    from PIL import Image, ImageDraw
    import crops as C
    if not pages:
        return 0
    release.TAG = sv_sheets.SVR
    try:
        src = SV / f'svread-{ac}.json.gz'
        if not src.exists():
            release.fetch(str(SV), [src.name])
    finally:
        release.TAG = sv_sheets.TAG
    with gzip.open(src, 'rt', encoding='utf8') as f:
        reads = json.load(f)['reads']
    n = 0
    for it in pages:
        data = run.fetch(run.url(ac, it['part'], 'kan'))
        if not data:
            continue
        doc = fitz.open(stream=data, filetype='pdf')
        one = fitz.open()
        one.insert_pdf(doc, from_page=it['page'], to_page=it['page'])
        img, _ = next(iter(C.page_images(one)))
        img = img.convert('L')
        img = img.resize((1400, img.height * 1400 // img.width))
        lines = page_label(ac, it, site, reads)
        sh = Image.new('L', (1400, img.height + 16 * len(lines) + 10), 255)
        sh.paste(img, (0, 0))
        dr = ImageDraw.Draw(sh)
        for j, t in enumerate(lines):
            dr.text((5, img.height + 5 + 16 * j), t, fill=0)
        n += 1
        index[len(index)] = {'tier': 'P', **it}
        sh.save(d / f'P-{n:03d}.png')
        del data, doc
        gc.collect()
    return n


def main() -> int:
    import sv_site
    ap = argparse.ArgumentParser()
    ap.add_argument('acs', nargs='+', type=int)
    ap.add_argument('--slips', type=int, default=3)
    ap.add_argument('--out', default=str(SV / 'review'))
    a = ap.parse_args()
    site = sv_site.Site()
    for ac in a.acs:
        items = json.loads((SV / f'resolve-{ac}.json').read_text('utf8'))['items']
        doubts, slips = pick(ac, items, a.slips)
        pages = page_items(ac)
        if not (doubts or slips or pages):
            continue
        d = Path(a.out) / str(ac)
        d.mkdir(parents=True, exist_ok=True)
        index = {}
        nd = render_rows(ac, doubts, 'D', d, index)
        ns = render_rows(ac, slips, 'S', d, index,
                         lambda r: f"site holds the look-alike: {r['site_variant']} ({pattern(r)})")
        np_ = render_pages(ac, pages, site, d, index)
        (d / 'index.json').write_text(json.dumps(index), 'utf8')
        print(f'AC {ac}: D {len(doubts)} cards/{nd} sheets, S {len(slips)}/{ns}, P {len(pages)} pages', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
