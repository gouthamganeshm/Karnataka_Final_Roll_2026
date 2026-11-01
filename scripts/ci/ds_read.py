"""Open dataset, the Actions side: read the sheets of one shard of one AC.

    python scripts/ci/ds_read.py ds-<ac>.s<i>.tar dsread-<ac>.s<i>.json.gz

ds-<ac>.s<i>.tar (scripts/home/ds_pilot.py) holds, per booth and roll, one
sheet image per card page (the cards' text blocks stacked, fields.page_sheet)
and their spans. Each sheet is read once by Tesseract (fields.read_sheet), on
every core. Writes per booth, roll and page the cards as
{cell: {age, gender, relation, house}}. The house number is there only to be
hashed by the join (ds_join.py) and dropped; names are not read. Holds house
numbers: the private <tag>-ds draft only, never an Actions artifact.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import sys
import tarfile
import time
import zipfile
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'ocr')]


def read_page(item: tuple) -> tuple:
    import fields as F
    from PIL import Image
    name, page, lang, png, spans = item
    im = Image.open(io.BytesIO(png))
    im.load()
    return name, page, {str(c): v for c, v in F.read_sheet(im.convert('L'), spans, lang).items()}


def items(src: str):
    with tarfile.open(src) as tar:
        for m in tar:
            if not m.name.endswith('.zip'):
                continue
            with zipfile.ZipFile(io.BytesIO(tar.extractfile(m).read())) as z:
                index = json.loads(z.read('index.json'))
                for p, spans in index['pages'].items():
                    yield m.name, p, index['lang'], z.read(f'p{int(p):03d}.{index["ext"]}'), spans


def main(src: str, dest: str) -> int:
    t = time.time()
    out, n = {}, 0
    with Pool(os.cpu_count() or 2) as pool:
        for name, page, cards in pool.imap_unordered(read_page, items(src), chunksize=2):
            out.setdefault(name, {})[page] = cards
            n += 1
            if n % 200 == 0:
                print(f'{n} pages, {time.time() - t:.0f}s', flush=True)
    with gzip.open(dest, 'wt', encoding='utf8') as f:
        json.dump({'src': Path(src).name, 'reads': out}, f)
    print(f'{n} pages of {len(out)} booth rolls in {time.time() - t:.0f}s -> {dest}')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
