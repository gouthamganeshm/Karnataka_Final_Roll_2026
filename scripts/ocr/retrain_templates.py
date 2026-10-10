"""Re-learn the glyph templates from the fused readings (self-training).

    python -I scripts/ocr/retrain_templates.py IN.npz OUT.npz CACHE_DIR [--even|--odd]

`build_templates.py` labels its training glyphs with Tesseract, which is wrong
on ~2% of the letters it agrees on (AOH read as AQH teaches the Q template an
O). This pass reads the same cached crops with the current templates, fuses
the three readers (`crops.fuse`), and averages glyphs under the fused labels
instead.
"""
import io
import os
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

IN = None


def work(path):
    import crops as C
    import glyphs as G
    from PIL import Image
    tm = G.Templates.load(Path(IN))
    out = G.Templates()
    d = pickle.load(open(path, 'rb'))
    for blob, s, a in zip(d['crops'], d['sheet'], d['alone']):
        crop = Image.open(io.BytesIO(blob))
        det = tm.read_detail(crop)
        g = ''.join(x[0] for x in det) if det else None
        final = s if (g and g == s and C.R.EPIC_RE.match(s)) else C.fuse(det, s, a)
        if final:
            out.add(crop, final)
    return out.sum, out.n


def init(path):
    global IN
    IN = path


if __name__ == '__main__':
    src, dst, cache = sys.argv[1:4]
    files = sorted(Path(cache).glob('*.pkl'))
    if '--even' in sys.argv:
        files = [f for f in files if int(f.stem.split('-')[0]) % 2 == 0]
    if '--odd' in sys.argv:
        files = [f for f in files if int(f.stem.split('-')[0]) % 2 == 1]
    import glyphs as G
    total = G.Templates()
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 4) - 1), initializer=init, initargs=(src,)) as pool:
        for sums, ns in pool.map(work, files):
            t = G.Templates()
            t.sum, t.n = sums, ns
            total.merge(t)
    total.save(Path(dst))
    print('retrained on', len(files), 'parts:', {c: total.n[c] for c in sorted(total.n)})
