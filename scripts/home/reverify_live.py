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
  totals   `--totals FILE` (lines of {"ac", "part", "new"}: totals.py re-run on
           the part's PDF) replaces a part's printed totals in the summary when
           the new reading is the cover's, confirmed by the summary page; the
           summary is then replaced along with the rows and verify files.

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
    """What the site shows for each published card: EPIC, serial, deleted (as build.mjs sees it)."""
    disputed = {tuple(d[:3]) for d in verify['disputed']}
    undeleted = {tuple(d) for d in verify.get('undeleted', [])}
    return {(r['part'], r['page'], r['cell']):
            (r['epic'], r['serial'], bool(r.get('deleted')) and (r['part'], r['page'], r['cell']) not in undeleted)
            for r in rows
            if r['epicOk'] and EPIC.match(r['epic']) and (r['part'], r['page'], r['cell']) not in disputed}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--ac')
    ap.add_argument('--skip', default='')
    ap.add_argument('--totals', help='re-read totals (JSON lines) to patch into the summaries')
    args = ap.parse_args()
    skip = {int(a) for a in args.skip.split(',') if a}
    only = {int(a) for a in args.ac.split(',')} if args.ac else None
    reread = collections.defaultdict(dict)
    if args.totals:
        for line in Path(args.totals).read_text('utf8').splitlines():
            t = json.loads(line)
            if (t['new'] and not t['new'].get('conflict') and t['new'].get('from') == 'cover'
                    and t['new'].get('confirmed') and 'deleted' in t['new']):
                reread[t['ac']][str(t['part'])] = t['new']
        if only is None:
            only = set(reread)
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
        patched = 0
        if reread.get(ac):
            summary = json.loads(sum_p.read_text('utf8'))
            for part, t in reread[ac].items():
                if summary['perPart'].get(part, {}).get('totals') != t:
                    summary['perPart'].setdefault(part, {})['totals'] = t
                    patched += 1
            sum_p = DIR / f'new-sum-{ac}.json'
            sum_p.write_text(json.dumps(summary), 'utf8')
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
        # A card off its part's serial run (2010 read for serial 1) was published
        # with that wrong serial before V2 compared serials with the run.
        misread = {tuple(d[:3]) for d in ver['disputed'] if d[3] == 'v2:serial-order'}
        lost = [k for k, e in before.items() if after.get(k) != e and k not in misread]
        ok = ver['verdict'] == 'pass' and not lost
        print(f'AC {ac:3}: published {len(before):,} -> {len(after):,} (+{len(after) - len(before):,}; '
              f'{gained_realign} realigned, {patched} totals re-read) disputed {len(old_ver["disputed"]):,} -> {len(ver["disputed"]):,}; '
              f'verdict {ver["verdict"]}; lost {len(lost)}' + ('' if ok else '  -> NOT APPLIED'), flush=True)
        if args.apply and ok and len(after) > len(before):
            live = DIR / 'live'
            live.mkdir(exist_ok=True)
            (live / names[0]).write_bytes(new_rows.read_bytes())
            (live / names[2]).write_text(json.dumps(ver), 'utf8')
            files = [str(live / names[0]), str(live / names[2])]
            if patched:
                (live / names[1]).write_text(sum_p.read_text('utf8'), 'utf8')
                files.append(str(live / names[1]))
            release.replace(*files)
            changed += 1
    if args.apply and changed:
        release.gh('workflow', 'run', 'publish.yml', '-R', release.repo(), '-f', f'tag={release.TAG}')
        print(f'{changed} ACs replaced; publish dispatched')
    return 0


if __name__ == '__main__':
    sys.exit(main())
