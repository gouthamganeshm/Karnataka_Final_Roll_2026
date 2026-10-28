"""Settle the EPICs the series pass pinned, from what the English roll prints.

    python scripts/home/series_decide.py cache/series-check cache/series-check2 \
        --rows cache/verify-all --out cache/series-epics.json

Inputs are `sample_verify.py --targets` results (one result-<ac>.json per AC)
and the live rows, for both Kannada readings of each card. A card keeps its
published EPIC when the English roll prints it; it takes the English EPIC when
that is also a Kannada reading of the card (two rolls, two readers); otherwise
it is withheld. Any English reading counts, fused as well
as direct: it is a second roll, and it is only ever taken when it matches a
reading of the Kannada card. Writes reverify_live.py's `--epics` file,
listing only cards that change.
"""
from __future__ import annotations

import argparse
import collections
import glob
import gzip
import json
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('results', nargs='+', help='directories of result-<ac>.json')
    ap.add_argument('--rows', required=True, help='directory of live-rows-<ac>.jsonl.gz')
    ap.add_argument('--targets', nargs='+', default=['cache/series-targets.json', 'cache/series-targets2.json'])
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    asked = collections.defaultdict(set)
    for t in args.targets:
        for ac, cards in json.loads(Path(t).read_text()).items():
            asked[int(ac)] |= {tuple(c) for c in cards}
    seen = collections.defaultdict(dict)
    for d in args.results:
        for f in glob.glob(f'{d}/result-*.json'):
            res = json.loads(Path(f).read_text())
            for part, page, cell, pub, rd0, kan, eng in res['targets']:
                seen[res['ac']][(part, page, cell)] = (pub, kan, eng)
    edits, stats = collections.defaultdict(list), collections.Counter()
    for ac in sorted(asked):
        rows = {}
        with gzip.open(Path(args.rows) / f'live-rows-{ac}.jsonl.gz', 'rt', encoding='utf8') as f:
            for line in f:
                r = json.loads(line)
                key = (r['part'], r['page'], r['cell'])
                if key in asked[ac]:
                    rows[key] = r
        for key in sorted(asked[ac]):
            if key not in seen[ac]:
                stats['unchecked'] += 1
                continue
            pub, kan, eng = seen[ac][key]
            e = eng[0] if eng else None
            kannada = {x for x in (rows[key].get('rd') or [])[:2] if x}
            if kan and kan[1] == 'direct':
                kannada.add(kan[0])
            if e == pub:
                stats['kept: English prints it'] += 1
            elif e and e in kannada:
                edits[ac].append([*key, e])
                stats['corrected to the English EPIC'] += 1
            else:
                edits[ac].append([*key, None])
                stats['withheld: unsettled'] += 1
    Path(args.out).write_text(json.dumps({str(a): v for a, v in edits.items()}))
    print(dict(stats), f'{len(edits)} ACs change')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
