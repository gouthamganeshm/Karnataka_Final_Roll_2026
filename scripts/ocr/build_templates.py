"""Learn the EPIC glyph templates from sample part PDFs.

    python -I scripts/ocr/build_templates.py --out scripts/ocr/templates.npz \
        --cache CACHE_DIR sample/*.pdf

A card teaches the templates only when two Tesseract readings (the contact
sheet and the crop alone) agree on a valid EPIC and its ten glyphs separate
cleanly. One part from every constituency gives every series prefix in the
state enough samples (letters need MIN_SAMPLES to be used at all).

--cache keeps each part's crops and readings, so `eval_glyphs.py` can measure
the full reading rule without re-running Tesseract.
"""
from __future__ import annotations

import argparse
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def learn(job):
    path, cache = job
    os.environ['ROLL_EPIC_MODE'] = 'tesseract'
    import crops as C
    import glyphs as G
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
    t = G.Templates()
    for k, s, a in zip(kept, sheet, alone):
        if s == a and R.EPIC_RE.match(s):
            t.add(k, s)
    if cache:
        import io
        blobs = []
        for k in kept:
            b = io.BytesIO()
            k.save(b, format='PNG')
            blobs.append(b.getvalue())
        with open(Path(cache) / (Path(path).stem + '.pkl'), 'wb') as fh:
            pickle.dump({'crops': blobs, 'sheet': sheet, 'alone': alone}, fh)
    return Path(path).name, t.sum, t.n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pdfs', nargs='+', help='PDF files, or directories of them')
    ap.add_argument('--out', required=True)
    ap.add_argument('--cache')
    ap.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 4) - 1))
    args = ap.parse_args()
    if args.cache:
        Path(args.cache).mkdir(parents=True, exist_ok=True)
    pdfs = []
    for p in args.pdfs:    # a directory stands for every PDF in it
        pdfs += sorted(map(str, Path(p).glob('*.pdf'))) if Path(p).is_dir() else [p]
    args.pdfs = pdfs
    import glyphs as G
    total = G.Templates()
    with ProcessPoolExecutor(args.workers) as pool:
        for i, (name, sums, ns) in enumerate(pool.map(learn, [(p, args.cache) for p in args.pdfs]), 1):
            t = G.Templates()
            t.sum, t.n = sums, ns
            total.merge(t)
            print(f'{i}/{len(args.pdfs)} {name}', flush=True)
    total.save(Path(args.out))
    print('samples per character:', {c: total.n[c] for c in sorted(total.n)})
    thin = [c for c in G.ALPHA + G.DIGIT if total.n.get(c, 0) < G.MIN_SAMPLES]
    print('characters without a usable template:', thin or 'none')


if __name__ == '__main__':
    main()
