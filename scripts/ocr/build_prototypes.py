"""Learn the verifier's prototype reader from cached sample parts.

    python -I scripts/ocr/build_prototypes.py CACHE_DIR OUT.npz [--style kan|eng]
        [--templates T.npz] [--split even|odd|all]

CACHE_DIR is what `build_templates.py --cache` wrote (crops plus both
Tesseract readings per card). Each card is labelled with the *production*
reading (`crops.fuse` over sheet, glyph and alone) — so the prototypes learn
from the main reader's output, but see the glyphs through different features
(`glyphs._norm_line`) and keep several prototypes per character.
"""
import argparse
import io
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ARGS = None
PER_FILE_CAP = 40      # vectors per character per part, so no one part dominates


def collect(path):
    import numpy as np
    import crops as C
    import glyphs as G
    from PIL import Image
    tm = G.Templates.load(Path(ARGS['templates']), ARGS['style'])
    d = pickle.load(open(path, 'rb'))
    out: dict[str, list] = {}
    for blob, s, a in zip(d['crops'], d['sheet'], d['alone']):
        crop = Image.open(io.BytesIO(blob))
        spans = []
        det = tm.read_detail(crop, spans_out=spans)
        g = ''.join(x[0] for x in det) if det else None
        final = s if (g and g == s and C.R.EPIC_RE.match(s)) else C.fuse(det, s, a)
        if not final or not spans:
            continue
        band, chosen = spans
        for ch, v in zip(final, G.Prototypes.vectors(band, chosen)):
            if v is not None and len(out.setdefault(ch, [])) < PER_FILE_CAP:
                out[ch].append(v.astype(np.float16))
    return out


def init(args):
    global ARGS
    ARGS = args


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cache')
    ap.add_argument('out')
    ap.add_argument('--style', default='kan')
    ap.add_argument('--templates')
    ap.add_argument('--split', default='all', choices=['all', 'even', 'odd'])
    args = ap.parse_args()
    import glyphs as G
    import numpy as np
    files = sorted(Path(args.cache).glob('*.pkl'))
    if args.split != 'all':
        files = [f for f in files if int(f.stem.split('-')[0]) % 2 == (args.split == 'odd')]
    cfg = {'templates': args.templates or str(G.template_file(args.style)), 'style': args.style}
    samples: dict[str, list] = {}
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 4) - 1), initializer=init, initargs=(cfg,)) as pool:
        for part in pool.map(collect, files):
            for ch, vs in part.items():
                samples.setdefault(ch, []).extend(v.astype(np.float32) for v in vs)
    pr = G.Prototypes.learn(samples)
    pr.style = args.style
    pr.save(Path(args.out))
    print(f'{len(files)} parts; prototypes per character:',
          {c: len(p) for c, p in sorted(pr.protos.items())},
          '\nsamples:', {c: len(v) for c, v in sorted(samples.items())})
