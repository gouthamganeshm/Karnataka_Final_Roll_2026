"""Learn the EPIC glyph templates from sample part PDFs.

    python -I scripts/ocr/build_templates.py --out scripts/ocr/templates.npz \
        --cache CACHE_DIR sample/            # read PDFs (Tesseract), cache, learn
    python -I scripts/ocr/build_templates.py --out T.npz --from-cache CACHE_DIR \
        [--style kan|eng] [--split even|odd|all]   # re-learn from the cache only

A card teaches the templates only when two Tesseract readings (the contact
sheet and the crop alone) agree on a valid EPIC and its ten glyphs separate
cleanly. O/Q and 6/8 labels are then corrected by the stroke tests in
`glyphs.refine` — Tesseract's agreement is wrong on those pairs often enough
(AOH read as AQH) to blur the averages otherwise. One part from every
constituency gives every series prefix in the state enough samples.

--cache keeps each part's crops and readings, so templates, prototypes and the
evaluation (`evaluate.py`) can be redone without running Tesseract again.
"""
from __future__ import annotations

import argparse
import io
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

STYLE = 'kan'


def _learn_cards(crops, sheet, alone, style):
    import glyphs as G
    import roll_ocr as R
    t = G.Templates(style)
    for k, s, a in zip(crops, sheet, alone):
        if s == a and R.EPIC_RE.match(s):
            t.add(k, s, relabel=True)
    return t


def learn(job):
    path, cache, style = job
    os.environ['ROLL_EPIC_MODE'] = 'tesseract'
    import crops as C
    import roll_ocr as R
    pages = C.cut_part_bytes(Path(path).read_bytes())
    kept, sheet, alone = [], [], []
    for epic_crops, _ in pages:
        if not any(c is not None for c in epic_crops):
            continue
        sh = C.R.contact_sheet(epic_crops)
        lines = R.ocr_lines(sh) if sh else []
        lines += [''] * (len(epic_crops) - len(lines))
        ks = [i for i, c in enumerate(epic_crops) if c is not None]
        kept += [epic_crops[i] for i in ks]
        sheet += [R.coerce_epic(lines[i]) for i in ks]
        alone += [R.coerce_epic(x) for x in C.read_each([C._single_line(epic_crops[i]) for i in ks])]
    t = _learn_cards(kept, sheet, alone, style)
    if cache:
        blobs = []
        for k in kept:
            b = io.BytesIO()
            k.save(b, format='PNG')
            blobs.append(b.getvalue())
        with open(Path(cache) / (Path(path).stem + '.pkl'), 'wb') as fh:
            pickle.dump({'crops': blobs, 'sheet': sheet, 'alone': alone}, fh)
    return Path(path).name, t.sum, t.n


def relearn(job):
    path, style = job
    from PIL import Image
    d = pickle.load(open(path, 'rb'))
    crops = [Image.open(io.BytesIO(b)) for b in d['crops']]
    t = _learn_cards(crops, d['sheet'], d['alone'], style)
    return Path(path).name, t.sum, t.n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdfs', nargs='*', help='PDF files, or directories of them')
    ap.add_argument('--out', required=True)
    ap.add_argument('--cache', help='write each part\'s crops and readings here')
    ap.add_argument('--from-cache', help='learn from a cache instead of PDFs')
    ap.add_argument('--style', default='kan')
    ap.add_argument('--split', default='all', choices=['all', 'even', 'odd'])
    ap.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 4) - 1))
    args = ap.parse_args()
    import glyphs as G

    if args.from_cache:
        files = sorted(Path(args.from_cache).glob('*.pkl'))
        if args.split != 'all':
            files = [f for f in files if int(f.stem.split('-')[0]) % 2 == (args.split == 'odd')]
        jobs, fn = [(str(f), args.style) for f in files], relearn
    else:
        if args.cache:
            Path(args.cache).mkdir(parents=True, exist_ok=True)
        pdfs = []
        for p in args.pdfs:    # a directory stands for every PDF in it
            pdfs += sorted(map(str, Path(p).glob('*.pdf'))) if Path(p).is_dir() else [p]
        jobs, fn = [(p, args.cache, args.style) for p in pdfs], learn

    total = G.Templates(args.style)
    with ProcessPoolExecutor(args.workers) as pool:
        for i, (name, sums, ns) in enumerate(pool.map(fn, jobs), 1):
            t = G.Templates(args.style)
            t.sum, t.n = sums, ns
            total.merge(t)
            if not args.from_cache:
                print(f'{i}/{len(jobs)} {name}', flush=True)
    total.save(Path(args.out))
    print(f'{len(jobs)} parts; samples per character:', {c: total.n[c] for c in sorted(total.n)})
    thin = [c for c in G.ALPHA + G.DIGIT if total.n.get(c, 0) < G.MIN_SAMPLES]
    print('characters without a usable template:', thin or 'none')


if __name__ == '__main__':
    main()
