"""Open dataset, step 3: join one AC's readings to its verified rows, hash, drop.

    python scripts/home/ds_join.py AC [AC ...]

From dsread-<ac>.json.gz (the English roll's age, gender, relation label,
house number per card; ds_pilot.py) and live-rows-<ac>.jsonl.gz (the
verified rows: EPIC, serial, deleted), one row per published card:

  ac, part, page, card, serial, serial_sure, status, age, gender, relation,
  epic_hash, household_hash

The verified rows are placed by the Kannada roll's pages; the English card is
taken from the same page and cell, and only when that page holds as many
cards in both rolls (else the card's fields stay empty and it is counted).
epic_hash = HMAC-SHA256(key, EPIC), first 24 hex; household_hash =
HMAC-SHA256(key, ac|part|house number with spaces and punctuation dropped),
first 16 hex. The key (~/.dataset_key, 32 bytes) never leaves the VMs and the
Actions secret; EPICs and house numbers are dropped here.

Writes ds-<ac>.csv.gz and dsstats-<ac>.json to the
private <tag>-ds draft. Never touches the live site or its releases.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import hmac
import io
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402

TAG = release.TAG
DS = f'{TAG}-ds'
DIR = ROOT / 'cache' / 'ds' / 'join'
KEY = Path.home() / '.dataset_key'
COLUMNS = ['ac', 'part', 'page', 'card', 'serial', 'serial_sure', 'status', 'age', 'gender', 'relation',
           'epic_hash', 'household_hash']
FIELDS = ('age', 'gender', 'relation')


def key() -> bytes:
    k = KEY.read_bytes()
    if len(k) != 32:
        raise SystemExit(f'{KEY}: want 32 bytes')
    return k


def key_id(k: bytes) -> str:
    return hashlib.sha256(k).hexdigest()[:8]


def mac(k: bytes, s: str, n: int) -> str:
    return hmac.new(k, s.encode('utf8'), hashlib.sha256).hexdigest()[:n]


def house_norm(h: str | None) -> str | None:
    if not h:
        return None
    s = re.sub(r'[\s.,:;\-_/\\()]+', '', h.upper())
    return s or None


def offset(live: dict[int, int], eng: dict[int, int]) -> int:
    """English page = Kannada page + offset, for one booth.

    Some booths' English roll has one more front page than the Kannada one, so
    every card page sits one later; a run of 30-card pages then matches by count
    at the wrong offset. The offset taken is the one under which the most pages
    hold as many cards in both rolls (0 on a tie); pages that still differ stay
    empty."""
    def hits(d):
        return sum(eng.get(p + d) == n for p, n in live.items())
    return max((0, 1, -1, 2, -2), key=lambda d: (hits(d), d == 0))


def join(ac: int, k: bytes) -> dict:
    DIR.mkdir(parents=True, exist_ok=True)
    rd, = release.fetch(str(DIR), [f'live-rows-{ac}.jsonl.gz'])
    release.TAG = DS
    try:
        dr, = release.fetch(str(DIR), [f'dsread-{ac}.json.gz'])
    finally:
        release.TAG = TAG
    with gzip.open(dr, 'rt', encoding='utf8') as f:
        reads = json.load(f)['reads']
    rows = []
    with gzip.open(rd, 'rt', encoding='utf8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    rows.sort(key=lambda r: (r['part'], r['page'], r['cell']))
    per_page = {}
    for r in rows:
        per_page[(r['part'], r['page'])] = per_page.get((r['part'], r['page']), 0) + 1
    shift = {}
    for part in {p for p, _ in per_page}:
        shift[part] = offset({pg: n for (pa, pg), n in per_page.items() if pa == part},
                             {int(pg): len(v) for pg, v in reads.get(f'{part}.eng.zip', {}).items()})
    out, stats = [], {'cards': 0, 'read': 0, 'page_differs': 0, 'no_page': 0,
                      'booths_shifted': sum(1 for d in shift.values() if d)}
    for r in rows:
        part, page, cell = r['part'], r['page'], r['cell']
        ep = reads.get(f'{part}.eng.zip', {}).get(str(page + shift[part]))
        stats['cards'] += 1
        if ep is None:
            stats['no_page'] += 1
            ec = None
        elif len(ep) != per_page[(part, page)]:
            stats['page_differs'] += 1
            ec = None
        else:
            ec = ep.get(str(cell))
        stats['read'] += ec is not None
        house = house_norm((ec or {}).get('house'))
        epic = r.get('epic') if r.get('epicOk', True) else None
        out.append({
            'ac': ac, 'part': part, 'page': page, 'card': cell, 'serial': r.get('serial'),
            'serial_sure': int(bool(r.get('ok'))),
            'status': 'withheld' if epic is None else 'deleted' if r.get('deleted') else 'live',
            **{f: (ec or {}).get(f) for f in FIELDS},
            'epic_hash': mac(k, epic, 24) if epic else None,
            'household_hash': mac(k, f'{ac}|{part}|{house}', 16) if house else None,
        })
    # Nothing that could hold a name or a number off the card leaves here.
    for o in out:
        for c in ('gender', 'relation'):
            if o[c] is not None and o[c] not in ('M', 'F', 'TG', 'Father', 'Husband', 'Mother', 'Wife', 'Other', 'Guru'):
                raise SystemExit(f'AC {ac}: unexpected {c} value')
        if o['age'] is not None and not isinstance(o['age'], int):
            raise SystemExit(f'AC {ac}: unexpected age value')
    buf = io.StringIO()
    w = csv.DictWriter(buf, COLUMNS)
    w.writeheader()
    w.writerows(out)
    csv_p = DIR / f'ds-{ac}.csv.gz'
    with gzip.open(csv_p, 'wt', encoding='utf8') as f:
        f.write(buf.getvalue())
    rev_p = DIR / f'dsstats-{ac}.json'
    rev_p.write_text(json.dumps({'ac': ac, 'key_id': key_id(k), 'stats': stats}), 'utf8')
    release.TAG = DS
    try:
        release.upload(str(csv_p), str(rev_p))
    finally:
        release.TAG = TAG
    for p in (rd, dr, csv_p, rev_p):
        p.unlink()
    return stats


def main() -> int:
    k = key()
    for ac in map(int, sys.argv[1:]):
        print(f'AC {ac}: {join(ac, k)}', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
