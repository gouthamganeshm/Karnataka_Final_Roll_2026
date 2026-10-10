"""Actions stage: OCR one constituency's crop tar into rows.

    python scripts/ci/ocr_ac.py crops-177.tar rows-177.jsonl.gz

Reads every part bundle in the tar, OCRs it with one process per core
(`crops.ocr_pages`: two different kinds of reader must agree on each EPIC),
and writes one JSON row per elector card:

    {"ac": 177, "part": 3, "serial": 1, "epic": "AAH4480430", "ok": true, "epicOk": true}

`epicOk`: independent readings agreed on the EPIC (see `crops.ocr_page`).
`ok`: as in the draft pipeline — valid EPIC and a serial the sequence confirms.

A part that home could not fetch is recorded with no rows and listed in the
summary line, so the build counts it as *not covered* rather than empty.
"""
from __future__ import annotations

import gzip
import io
import json
import os
import sys
import tarfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ocr'))


def ocr_bundle(item: tuple[str, bytes]) -> tuple[int, list[dict], float]:
    import crops
    import roll_ocr as R
    name, data = item
    t = time.time()
    index, pages = crops.read_bundle(data)
    rows = crops.ocr_pages(pages)
    ac, part = index['ac'], index['part']
    out = [{'ac': ac, 'part': part, 'serial': r.serial, 'epic': r.epic,
            'ok': bool(r.ok and R.EPIC_RE.match(r.epic)), 'epicOk': bool(agreed)}
           for r, agreed in rows]
    return part, out, time.time() - t


def main(tar_path: str, out_path: str) -> int:
    with tarfile.open(tar_path) as tar:
        meta = json.loads(tar.extractfile('meta.json').read())
        items = [(m.name, tar.extractfile(m).read()) for m in tar.getmembers() if m.name.endswith('.zip')]

    ac = meta['ac']
    workers = os.cpu_count() or 4
    t0, done, n_rows, n_ok = time.time(), 0, 0, 0
    read_parts = []
    with gzip.open(out_path, 'wt', encoding='utf8') as out, ProcessPoolExecutor(workers) as pool:
        for part, rows, secs in pool.map(ocr_bundle, items):
            for r in rows:
                out.write(json.dumps(r, separators=(',', ':')) + '\n')
            done += 1
            n_rows += len(rows)
            n_ok += sum(r['ok'] and r['epicOk'] for r in rows)
            if rows:
                read_parts.append(part)
            print(f'AC {ac} part {part}: {len(rows)} rows in {secs:.0f}s ({done}/{len(items)})', flush=True)

    unread = sorted(set(meta['parts']) - set(read_parts))
    summary = {'ac': ac, 'parts': len(meta['parts']), 'partsRead': len(read_parts),
               'unread': unread, 'rows': n_rows, 'ok': n_ok, 'secs': round(time.time() - t0)}
    Path(out_path).with_suffix('').with_suffix('.summary.json').write_text(json.dumps(summary))
    print(json.dumps(summary))
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
