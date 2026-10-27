"""Recover wrongly withheld cards in live ACs, from their stored rows alone.

    python scripts/home/reverify_live.py                 # dry run: report only
    python scripts/home/reverify_live.py --apply --skip 154,162

Two recoveries, neither needing the crops (deleted after verification):

  realign  A card withheld because the readers disagreed, whose glyph reading
           is exactly the contact-sheet reading of another card on the same
           page (the sheet's lines had shifted, fixed in 965c299), and which
           no other card on the page publishes. Glyph and sheet then read the
           same 10 characters from this card: the 'direct' rule's standard.
  V3 rule  The whole-AC checks rerun with verify_ac.py's current V3, which no
           longer withholds a booth whose printed deletions match the marks
           found. Per-card disputes from an earlier full verification (V1/V4)
           are kept.

An AC is replaced only if it still passes and every card published now stays
published with the same EPIC; then live-* is swapped and the site republished.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402

DIR = ROOT / 'cache' / 'reverify'
EPIC = re.compile(r'^[A-Z]{3}[0-9]{7}$')


def load(path: Path) -> list[dict]:
    with gzip.open(path, 'rt', encoding='utf8') as f:
        return [json.loads(line) for line in f if line.strip()]


def realign(rows: list[dict]) -> int:
    pages = collections.defaultdict(list)
    for r in rows:
        pages[(r['part'], r['page'])].append(r)
    n = 0
    for rs in pages.values():
        sheets = collections.Counter((r.get('rd') or [None])[0] for r in rs)
        taken = collections.Counter(r['epic'] for r in rs if r['epicOk'])
        for r in rs:
            rd = (r.get('rd') or []) + [None, None]
            glyph = rd[1]
            if (not r['epicOk'] and glyph and EPIC.match(glyph) and rd[0] != glyph
                    and sheets[glyph] >= 1 and taken[glyph] == 0):
                r['epic'], r['epicOk'], r['how'] = glyph, True, 'realigned'
                taken[glyph] += 1
                n += 1
    return n


def published(rows: list[dict], verify: dict) -> dict:
    disputed = {tuple(d[:3]) for d in verify['disputed']}
    return {(r['part'], r['page'], r['cell']): r['epic'] for r in rows
            if r['epicOk'] and EPIC.match(r['epic']) and (r['part'], r['page'], r['cell']) not in disputed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--ac')
    ap.add_argument('--skip', default='')
    args = ap.parse_args()
    skip = {int(a) for a in args.skip.split(',') if a}
    only = {int(a) for a in args.ac.split(',')} if args.ac else None
    DIR.mkdir(parents=True, exist_ok=True)
    assets = release.assets()
    acs = sorted(int(n[10:-9]) for n in assets if re.fullmatch(r'live-rows-\d+\.jsonl\.gz', n))
    changed = 0
    for ac in acs:
        if ac in skip or (only and ac not in only):
            continue
        names = [f'live-rows-{ac}.jsonl.gz', f'live-rows-{ac}.summary.json', f'live-verify-{ac}.json']
        for attempt in range(3):          # the home line is saturated: timeouts happen
            try:
                release.fetch(str(DIR), names)
                break
            except RuntimeError:
                if attempt == 2:
                    raise
        rows_p, sum_p, ver_p = (DIR / n for n in names)
        old_ver = json.loads(ver_p.read_text('utf8'))
        rows = load(rows_p)
        before = published(rows, old_ver)
        gained_realign = realign(rows)
        new_rows = DIR / f'new-rows-{ac}.jsonl.gz'
        with gzip.open(new_rows, 'wt', encoding='utf8') as f:
            for r in rows:
                f.write(json.dumps(r, separators=(',', ':')) + '\n')
        out = DIR / f'out-{ac}'
        subprocess.run([sys.executable, 'scripts/ci/verify_ac.py', str(ac), '-', str(new_rows), str(sum_p),
                        str(out), '--quick'], cwd=ROOT, check=True, capture_output=True)
        ver = json.loads((out / f'verify-{ac}.json').read_text('utf8'))
        keep = [d for d in old_ver['disputed'] if d[3].startswith(('v1', 'v4'))]
        have = {tuple(d[:3]) for d in ver['disputed']}
        ver['disputed'] += [d for d in keep if tuple(d[:3]) not in have]
        ver['checks'] = old_ver.get('checks', 'full') + '+reverified'
        after = published(rows, ver)
        lost = [k for k, e in before.items() if after.get(k) != e]
        ok = ver['verdict'] == 'pass' and not lost
        print(f'AC {ac:3}: published {len(before):,} -> {len(after):,} (+{len(after) - len(before):,}; '
              f'{gained_realign} realigned) disputed {len(old_ver["disputed"]):,} -> {len(ver["disputed"]):,}; '
              f'verdict {ver["verdict"]}; lost {len(lost)}' + ('' if ok else '  -> NOT APPLIED'), flush=True)
        if args.apply and ok and len(after) > len(before):
            live = DIR / 'live'
            live.mkdir(exist_ok=True)
            (live / names[0]).write_bytes(new_rows.read_bytes())
            (live / names[2]).write_text(json.dumps(ver), 'utf8')
            release.replace(str(live / names[0]), str(live / names[2]))
            changed += 1
    if args.apply and changed:
        release.gh('workflow', 'run', 'publish.yml', '-R', release.repo(), '-f', f'tag={release.TAG}')
        print(f'{changed} ACs replaced; publish dispatched')
    return 0


if __name__ == '__main__':
    sys.exit(main())
