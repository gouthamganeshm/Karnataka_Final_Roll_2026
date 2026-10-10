"""Measure the whole reading + verification chain on cached sample parts.

    python -I scripts/ocr/evaluate.py CACHE_DIR OUT_DIR [--split odd] [--style kan]
        [--templates T.npz] [--prototypes P.npz] [--sample N]

For every card: the production reading (`crops.fuse` over sheet, glyph and
alone), then verifier check V1 on everything that would be published. Prints
how many cards are published, withheld and disputed, and writes

    OUT_DIR/cards.pkl          every card's outcome (for audits)
    OUT_DIR/disputed-NN.png    disputed cards with every reading, to eyeball
    OUT_DIR/audit-NN.png       N random *published* cards (--sample), for the
                               hand-checked accuracy audit (verifier check V6)
"""
import argparse
import io
import os
import pickle
import random
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CFG = None


def init(cfg):
    global CFG
    CFG = cfg
    import crops as C
    import glyphs as G
    import verify as V
    if cfg.get('templates'):
        C._templates[cfg['style']] = G.Templates.load(Path(cfg['templates']), cfg['style'])
    if cfg.get('prototypes'):
        C._protos[cfg['style']] = G.Prototypes.load(Path(cfg['prototypes']), cfg['style'])


def run(path):
    import crops as C
    import verify as V
    from PIL import Image
    style = CFG['style']
    tm = C.templates(style)
    d = pickle.load(open(path, 'rb'))
    cards = []
    for idx, (blob, s, a) in enumerate(zip(d['crops'], d['sheet'], d['alone'])):
        crop = Image.open(io.BytesIO(blob))
        det = tm.read_detail(crop) if tm else None
        g = ''.join(x[0] for x in det) if det else None
        if g and g == s and C.R.EPIC_RE.match(s):
            final, how = s, 'direct'
        else:
            final = C.fuse(det, s, a, C.proto_read(crop, style) if tm else None)
            how = 'fused' if final else 'withheld'
        cards.append({'part': path.stem, 'idx': idx, 'sheet': s, 'alone': a, 'glyph': g,
                      'final': final, 'how': how})
    pub = [c for c in cards if c['final']]
    crops = [Image.open(io.BytesIO(d['crops'][c['idx']])) for c in pub]
    verdicts = V.v1([(cr, c['final']) for cr, c in zip(crops, pub)], style)
    for c, v in zip(pub, verdicts):
        c['v1'] = v
    return cards


def sheet(items, path, width=760):
    from PIL import Image, ImageDraw
    rows = []
    for crop, label in items:
        big = crop.resize((crop.width * 3, crop.height * 3))
        im = Image.new('L', (width, big.height + 16), 255)
        im.paste(big, (4, 14))
        ImageDraw.Draw(im).text((4, 1), label, fill=0)
        rows.append(im)
    out = Image.new('L', (width, sum(r.height for r in rows)), 255)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cache')
    ap.add_argument('out')
    ap.add_argument('--split', default='all', choices=['all', 'even', 'odd'])
    ap.add_argument('--style', default='kan')
    ap.add_argument('--templates')
    ap.add_argument('--prototypes')
    ap.add_argument('--sample', type=int, default=0)
    ap.add_argument('--seed', type=int, default=2026)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    files = sorted(Path(args.cache).glob('*.pkl'))
    if args.split != 'all':
        files = [f for f in files if int(f.stem.split('-')[0]) % 2 == (args.split == 'odd')]
    cfg = {'style': args.style, 'templates': args.templates, 'prototypes': args.prototypes}
    cards = []
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 4) - 1), initializer=init, initargs=(cfg,)) as pool:
        for part in pool.map(run, files):
            cards += part
    pickle.dump(cards, open(Path(args.out) / 'cards.pkl', 'wb'))

    n = len(cards)
    pub = [c for c in cards if c['final']]
    disputed = [c for c in pub if c.get('v1')]
    print(f'{len(files)} parts, {n} cards')
    print(f'reading: published {len(pub)} ({len(pub)/n:.2%}), withheld {n-len(pub)} ({(n-len(pub))/n:.2%}); '
          f'direct {sum(c["how"]=="direct" for c in cards)}, fused {sum(c["how"]=="fused" for c in cards)}')
    print(f'V1 disputes {len(disputed)} ({len(disputed)/max(len(pub),1):.3%} of published) -> '
          f'final published {len(pub)-len(disputed)} ({(len(pub)-len(disputed))/n:.2%} of cards)')
    reasons = {}
    for c in disputed:
        reasons[c['v1']] = reasons.get(c['v1'], 0) + 1
    print('dispute reasons:', dict(sorted(reasons.items())))

    def crop_of(c):
        from PIL import Image
        d = pickle.load(open(Path(args.cache) / f"{c['part']}.pkl", 'rb'))
        return Image.open(io.BytesIO(d['crops'][c['idx']]))

    rnd = random.Random(args.seed)
    show = rnd.sample(disputed, min(120, len(disputed)))
    for k in range(0, len(show), 40):
        sheet([(crop_of(c), f"{c['part']}#{c['idx']} published={c['final']} sheet={c['sheet']} "
                f"alone={c['alone']} glyph={c['glyph']} {c['v1']}") for c in show[k:k + 40]],
              Path(args.out) / f'disputed-{k // 40:02d}.png')
    if args.sample:
        ok = [c for c in pub if not c.get('v1')]
        audit = rnd.sample(ok, min(args.sample, len(ok)))
        pickle.dump(audit, open(Path(args.out) / 'audit.pkl', 'wb'))
        for k in range(0, len(audit), 50):
            sheet([(crop_of(c), f"{k + j + 1:04d}  {c['final']}") for j, c in enumerate(audit[k:k + 50])],
                  Path(args.out) / f'audit-{k // 50:03d}.png', width=420)
        print(f'audit: {len(audit)} published cards drawn into audit-*.png')
