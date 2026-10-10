"""Measure the full EPIC reading rule on cached sample parts.

    python -I scripts/ocr/eval_glyphs.py TEMPLATES.npz CACHE_DIR OUT_DIR [--only NAMES]

Uses the crops and Tesseract readings `build_templates.py --cache` saved, runs
the glyph reader with the given templates, applies the rule in
`crops.ocr_page`, and reports how many cards each step settled. Every card
where the outcome differs from "both Tesseract readings agreed" is drawn into
OUT_DIR/review-*.png with all three readings, for a person to check.
"""
import argparse
import io
import os
import pickle
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crops as C  # noqa: E402
import glyphs as G  # noqa: E402
import roll_ocr as R  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('templates')
ap.add_argument('cache')
ap.add_argument('out')
ap.add_argument('--only', help='comma-separated cache names (without .pkl)')
ap.add_argument('--score', type=float, default=C.GLYPH_MIN_SCORE)
ap.add_argument('--margin', type=float, default=C.GLYPH_MIN_MARGIN)
ap.add_argument('--holdout', action='store_true',
                help='learn templates from even-numbered ACs only, evaluate odd ones')
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)

all_names = sorted(p.stem for p in Path(args.cache).glob('*.pkl'))
names = all_names
if args.only:
    want = set(args.only.split(','))
    names = [n for n in names if n in want]
if args.holdout:
    tm = G.Templates()
    for name in all_names:
        if int(name.split('-')[0]) % 2:
            continue
        d = pickle.load(open(Path(args.cache) / f'{name}.pkl', 'rb'))
        for blob, s, a in zip(d['crops'], d['sheet'], d['alone']):
            if s == a and R.EPIC_RE.match(s):
                tm.add(Image.open(io.BytesIO(blob)), s)
    names = [n for n in names if int(n.split('-')[0]) % 2]
    print('held out: templates from', sum(tm.n.values()) // 10, 'cards; evaluating', len(names), 'parts')
else:
    tm = G.Templates.load(Path(args.templates))

valid = lambda e: bool(e and R.EPIC_RE.match(e))  # noqa: E731
stat = dict(cards=0, rule1=0, rule2=0, rule3=0, withheld=0, tess_agreed=0,
            overruled=0, rescued=0, glyph_confident=0)
review = []
for name in names:
    d = pickle.load(open(Path(args.cache) / f'{name}.pkl', 'rb'))
    for idx, (blob, s, a) in enumerate(zip(d['crops'], d['sheet'], d['alone'])):
        crop = Image.open(io.BytesIO(blob))
        g, sc, mg = tm.read(crop)
        conf = g if (g and sc >= args.score and mg >= args.margin) else None
        stat['cards'] += 1
        stat['glyph_confident'] += bool(conf)
        tess = s if (s == a and valid(s)) else None
        stat['tess_agreed'] += bool(tess)
        if conf and conf == s:
            final, rule = conf, 'rule1'
        elif conf and conf == a:
            final, rule = conf, 'rule2'
        elif not conf and valid(a) and a == s:
            final, rule = a, 'rule3'
        else:
            final, rule = None, 'withheld'
        stat[rule] += 1
        if tess and final != tess:
            stat['overruled'] += 1
            review.append((crop, f'{name}#{idx} tess={tess} glyph={g} ({sc:.2f}/{mg:.2f}) -> {final or "WITHHELD"}'))
        elif not tess and final:
            stat['rescued'] += 1
            review.append((crop, f'{name}#{idx} sheet={s} alone={a} glyph={g} ({sc:.2f}/{mg:.2f}) -> {final}'))

n = stat['cards']
print({k: v for k, v in stat.items()})
print(f"published {n - stat['withheld']}/{n} = {(n - stat['withheld']) / n:.2%}; "
      f"withheld {stat['withheld'] / n:.2%}; overruled tesseract {stat['overruled']}, rescued {stat['rescued']}")

# Overruled cards first: those are the ones that decide whether glyphs can be trusted.
review.sort(key=lambda r: ' tess=' not in r[1])
with open(Path(args.out) / 'review.txt', 'w', encoding='utf8') as fh:
    fh.write('\n'.join(label for _, label in review))
for k in range(0, len(review), 60):
    chunk = review[k:k + 60]
    rows = []
    for crop, label in chunk:
        big = crop.resize((crop.width * 2, crop.height * 2))
        c = Image.new('L', (760, big.height + 14), 255)
        c.paste(big, (4, 12))
        ImageDraw.Draw(c).text((4, 1), label, fill=0)
        rows.append(c)
    sheet = Image.new('L', (760, sum(r.height for r in rows)), 255)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(Path(args.out) / f'review-{k // 60:02d}.png')
print(f'{len(review)} cards drawn into {args.out}')
