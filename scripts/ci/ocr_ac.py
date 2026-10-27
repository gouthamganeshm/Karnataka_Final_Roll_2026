"""Actions stage: OCR one constituency's crop tar into rows.

    python scripts/ci/ocr_ac.py crops-177.tar rows-177.jsonl.gz
    python scripts/ci/ocr_ac.py crops-eng-177.tar eng-177.jsonl.gz     # the English cross-check part

Reads every part bundle in the tar, OCRs it with one process per core
(`crops.ocr_pages`: the readers must settle every character of each EPIC), and
writes one JSON row per elector card:

    {"ac": 177, "part": 3, "page": 2, "cell": 0, "serial": 1, "epic": "AAH4480430",
     "ok": true, "epicOk": true, "how": "direct", "rd": [sheet, glyph, alone]}

`epicOk`: the EPIC readers agreed (see `crops.ocr_page`); only such rows can
be published. A card the final roll marks deleted (`"deleted": true`, its
serial box carries a reason code) is never `epicOk`: the elector is off the roll. `ok`: as in the draft pipeline — a serial the sequence confirms.
`page`/`cell` locate the card's crop for the verifier.

Next to the rows, `<name>.summary.json` holds per-part counts and the part's
printed elector totals (`ocr/totals.py`), which the verifier checks (V3).
A part that home could not fetch is listed as unread, so the build counts it
as *not covered* rather than empty.
"""
from __future__ import annotations

import gzip
import json
import os
import sys
import tarfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ocr'))


def ocr_bundle(item: tuple[str, bytes]):
    import crops
    import roll_ocr as R
    import totals
    name, data = item
    t = time.time()
    index, pages = crops.read_bundle(data)
    style = index.get('lang', 'kan')
    rows = crops.ocr_pages(pages, style, index.get('text'))
    ac, part = index['ac'], index['part']
    out = [{'ac': ac, 'part': part, 'page': info['page'], 'cell': info['cell'],
            'serial': r.serial, 'epic': r.epic,
            'ok': bool(r.ok and R.EPIC_RE.match(r.epic)),
            'epicOk': bool(agreed) and info.get('mark') != 'X', 'deleted': info.get('mark') == 'X',
            'how': info.get('how'), 'rd': [info.get('sheet'), info.get('glyph'), info.get('alone')]}
           for r, agreed, info in rows]
    tot = totals.read_totals(crops.bundle_image(data, 'cover'), crops.bundle_image(data, 'summary'))
    grid = [[n, present] for n, present in index['pages'] if n]   # cells per page, and which held a card
    return part, style, out, tot, grid, time.time() - t


def main(tar_path: str, out_path: str) -> int:
    with tarfile.open(tar_path) as tar:
        meta = json.loads(tar.extractfile('meta.json').read())
        items = [(m.name, tar.extractfile(m).read()) for m in tar.getmembers() if m.name.endswith('.zip')]

    ac = meta['ac']
    workers = os.cpu_count() or 4
    t0 = time.time()
    parts = {}
    n_rows = n_pub = 0
    with gzip.open(out_path, 'wt', encoding='utf8') as out, ProcessPoolExecutor(workers) as pool:
        for part, style, rows, tot, grid, secs in pool.map(ocr_bundle, items):
            for r in rows:
                out.write(json.dumps(r, separators=(',', ':')) + '\n')
            n_rows += len(rows)
            pub = sum(r['epicOk'] for r in rows)
            n_pub += pub
            parts[part] = {'cards': len(rows), 'published': pub, 'deleted': sum(r['deleted'] for r in rows),
                           'totals': tot, 'grid': grid, 'style': style}
            print(f'AC {ac} part {part} [{style}]: {len(rows)} cards, {pub} readable'
                  f'{"" if tot is None else ", printed total " + str(tot.get("total"))} '
                  f'in {secs:.0f}s ({len(parts)}/{len(items)})', flush=True)

    unread = sorted(set(meta['parts']) - {p for p, v in parts.items() if v['cards']})
    summary = {'ac': ac, 'lang': meta.get('lang', 'kan'), 'parts': len(meta['parts']),
               'partsRead': sum(1 for v in parts.values() if v['cards']), 'unread': unread,
               'rows': n_rows, 'published': n_pub, 'secs': round(time.time() - t0),
               'perPart': {str(k): v for k, v in sorted(parts.items())}}
    Path(out_path).with_suffix('').with_suffix('.summary.json').write_text(json.dumps(summary))
    print(json.dumps({k: v for k, v in summary.items() if k != 'perPart'}))
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
