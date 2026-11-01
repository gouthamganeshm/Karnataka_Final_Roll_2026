"""Make a card findable under the EPIC exactly as its PDF prints it, too.

    python scripts/home/set_aka.py AC PART/PAGE/CELL=SPELLING [...] [--apply]

A few cards print a letter where their EPIC has a digit (S for 5): the
readers settle the digit, so a visitor who types the print gets "not found".
`aka` on the card's live row is the printed spelling, read off both rolls by
a person; build.mjs publishes the card's record under it as well (same place,
counted once). Dry run unless --apply; then live-rows-<ac>.jsonl.gz is
replaced on the private release (the caller publishes). The spellings are
EPICs: pass them on the command line, never commit them.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402

DIR = ROOT / 'cache' / 'aka'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('ac', type=int)
    ap.add_argument('cards', nargs='+')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    want = {}
    for c in a.cards:
        k, v = c.split('=', 1)
        if not re.fullmatch(r'\d+/\d+/\d+', k) or not re.fullmatch(r'[A-Z0-9/]{6,16}', v):
            raise SystemExit(f'{c!r}: want PART/PAGE/CELL=SPELLING')
        want[tuple(map(int, k.split('/')))] = v
    name = f'live-rows-{a.ac}.jsonl.gz'
    DIR.mkdir(parents=True, exist_ok=True)
    release.fetch(str(DIR), [name])
    with gzip.open(DIR / name, 'rt', encoding='utf8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
    done = 0
    for r in rows:
        k = (r['part'], r['page'], r['cell'])
        if k in want:
            if want[k] == r['epic']:
                raise SystemExit(f'{k}: the spelling is the card\'s EPIC already')
            r['aka'] = sorted({*r.get('aka', []), want[k]})
            done += 1
            print(f'AC {a.ac} {k}: serial {r["serial"]}, also as printed')
    if done != len(want):
        raise SystemExit('a card is not in the live rows')
    if a.apply:
        out = DIR / 'live'
        out.mkdir(exist_ok=True)
        with gzip.open(out / name, 'wt', encoding='utf8') as f:
            for r in rows:
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
        release.replace(str(out / name))
        print(f'{name} replaced; publish to put it live')
    return 0


if __name__ == '__main__':
    sys.exit(main())
