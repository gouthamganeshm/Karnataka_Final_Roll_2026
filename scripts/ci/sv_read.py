"""25% sample verification, the Actions side: read the sampled cards of one AC.

    python scripts/ci/sv_read.py sv-<ac>.tar svread-<ac>.json.gz

sv-<ac>.tar (scripts/home/sv_pilot.py) holds, per booth and roll, the EPIC and
serial boxes of the sampled pages. Each page is read as the pipeline reads
one (crops.ocr_page: the four EPIC readers; the page's serials fitted to their
consecutive run; the mark beside the serial), on every core. Writes one JSON
object: booths.json as it came, and per booth, roll and page the cards as
[cell, epic, epic_ok, how, serial_raw, serial_fitted|null, mark].
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


def read_booth(item: tuple[str, bytes]) -> tuple[str, dict]:
    import crops as C
    import roll_ocr as R
    from PIL import Image
    name, data = item
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        have = set(z.namelist())
        index = json.loads(z.read('index.json'))

        def load(n):
            if n not in have:
                return None
            im = Image.open(io.BytesIO(z.read(n)))
            im.load()
            return im.convert('L')

        for p, (n, present) in index['pages'].items():
            p = int(p)
            epics, serials = [None] * n, [None] * n
            for c in present:
                epics[c] = load(f'p{p:03d}/c{c:02d}e.png')
                serials[c] = load(f'p{p:03d}/c{c:02d}s.png')
            e, ok, s, scrops, info = C.ocr_page(epics, serials, index['lang'])
            fitted, sure = R.repair_serials(s) if s else ([], [])
            out[str(p)] = [[d['cell'], e[j], bool(ok[j]), d.get('how'), s[j],
                            fitted[j] if sure[j] else None, R.serial_marker(scrops[j])]
                           for j, d in enumerate(info)]
    return name, out


def main(src: str, dest: str) -> int:
    t = time.time()
    items, booths = [], None
    with tarfile.open(src) as tar:
        for m in tar:
            data = tar.extractfile(m).read()
            if m.name == 'booths.json':
                booths = json.loads(data)
            else:
                items.append((m.name, data))
    res = {}
    with Pool(os.cpu_count()) as pool:
        for i, (name, pages) in enumerate(pool.imap_unordered(read_booth, items, chunksize=2)):
            res[name] = pages
            if (i + 1) % 100 == 0:
                print(f'{i + 1}/{len(items)} booth files read ({time.time() - t:.0f}s)', flush=True)
    with gzip.open(dest, 'wt', encoding='utf8') as f:
        json.dump({'booths': booths, 'reads': res, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}, f)
    cards = sum(len(c) for pages in res.values() for c in pages.values())
    print(f'{len(items)} booth files, {cards} cards read in {time.time() - t:.0f}s -> {dest}')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
