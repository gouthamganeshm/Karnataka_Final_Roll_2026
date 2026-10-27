"""Audit that no card was skipped between the PDF and the site, per booth.

    python scripts/home/coverage_audit.py              # every live AC
    python scripts/home/coverage_audit.py --ac 150,196

For each live AC (the private release's live-* files, the site build's input):

  fetch   every part 1..N has rows (none unread)
  cut     every card cell the cutter found on a page became a row
  serial  at least as many cards as the last confirmed serial (a deleted card
          keeps its serial), so a card or page the cutter missed shows
  printed cards = the part's printed net total + printed deletions (ECI's own
          counts from the cover / summary page), where both were read
  read    cards whose EPIC was unreadable (withheld) or disputed: read, not
          skipped, but not searchable

Writes cache/coverage/audit-<time>.json with every booth that fails a check;
prints one line per AC and the list of booths to re-process. No EPICs are
printed or written.
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402

DIR = ROOT / 'cache' / 'sample-test'      # shared with sample_test.mjs: same files
OUT = ROOT / 'cache' / 'coverage'
EPIC_OK = __import__('re').compile(r'^[A-Z]{3}[0-9]{7}$')


def fetch(ac: int, assets: dict) -> list[Path]:
    names = [f'live-rows-{ac}.jsonl.gz', f'live-rows-{ac}.summary.json', f'live-verify-{ac}.json']
    stamp = DIR / f'ids-{ac}.audit.json'
    want = json.dumps([assets[n]['id'] for n in names])
    if not stamp.exists() or stamp.read_text() != want or not all((DIR / n).exists() for n in names):
        release.fetch(str(DIR), names)
        stamp.write_text(want)
    return [DIR / n for n in names]


def audit(ac: int, rows_path: Path, sum_path: Path, ver_path: Path) -> dict:
    summary = json.loads(sum_path.read_text('utf8'))
    ver = json.loads(ver_path.read_text('utf8'))
    disputed = {(p, pg, c) for p, pg, c, *_ in ver.get('disputed', [])}
    parts = defaultdict(lambda: {'cards': 0, 'serials': set(), 'deleted': 0, 'withheld': 0, 'disputed': 0})
    with gzip.open(rows_path, 'rt', encoding='utf8') as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            p = parts[r['part']]
            p['cards'] += 1
            p['deleted'] += bool(r.get('deleted'))
            if r.get('ok'):
                p['serials'].add(r['serial'])
            if not EPIC_OK.match(r['epic'] or '') or r.get('epicOk') is False:
                p['withheld'] += 1
            elif (r['part'], r['page'], r['cell']) in disputed:
                p['disputed'] += 1

    booths = {}
    n_parts = summary['parts']
    totals = defaultdict(int)
    for part in range(1, n_parts + 1):
        info = summary['perPart'].get(str(part), {})
        p = parts.get(part)
        issues = []
        if not p:
            issues.append('not read (no rows)')
            booths[part] = issues
            totals['unread'] += 1
            continue
        cells = sum(len(present) for _, present in info.get('grid', []))
        if cells and cells != p['cards']:
            issues.append(f'cut {cells} cards, {p["cards"]} rows')
        # Fewer cards than the last confirmed serial: some were never cut.
        top = max(p['serials'], default=0)
        gaps = top - p['cards']
        if gaps > 0:
            issues.append(f'{p["cards"]} cards but serials run to {top}')
        t = info.get('totals') or {}
        if t.get('total') is not None and 'deleted' in t:
            want = t['total'] + t['deleted']
            if want != p['cards']:
                issues.append(f'{p["cards"]} cards, printed {t["total"]} + {t["deleted"]} deleted = {want}')
            totals['printed_checked'] += 1
        elif t.get('total') is not None:
            live = p['cards'] - p['deleted']
            if live != t['total']:
                issues.append(f'{live} live cards, printed net {t["total"]} (deletions not printed/read)')
            totals['printed_net_only'] += 1
        else:
            totals['printed_unread'] += 1
        totals['cards'] += p['cards']
        totals['deleted'] += p['deleted']
        totals['withheld'] += p['withheld']
        totals['disputed'] += p['disputed']
        totals['gaps'] += max(gaps, 0)
        if issues:
            booths[part] = issues
    return {'ac': ac, 'parts': n_parts, 'booths_flagged': len(booths), **totals, 'booths': booths}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--ac')
    args = ap.parse_args()
    only = {int(a) for a in args.ac.split(',')} if args.ac else None
    DIR.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    assets = release.assets()
    acs = sorted(int(n[len('live-rows-'):-len('.jsonl.gz')]) for n in assets
                 if n.startswith('live-rows-') and n.endswith('.jsonl.gz'))
    report = []
    for ac in acs:
        if only and ac not in only:
            continue
        r = audit(ac, *fetch(ac, assets))
        report.append(r)
        print(f'AC {ac:3}: {r["parts"]} booths, {r["cards"]:,} cards ({r["deleted"]:,} deleted) | '
              f'unread {r.get("unread", 0)}, serial gaps {r["gaps"]}, '
              f'printed check {r.get("printed_checked", 0)} full + {r.get("printed_net_only", 0)} net-only, '
              f'{r.get("printed_unread", 0)} unprinted | withheld {r["withheld"]}, disputed {r["disputed"]} | '
              f'{r["booths_flagged"]} booths flagged', flush=True)
    path = OUT / f'audit-{time.strftime("%Y%m%dT%H%M%S")}.json'
    path.write_text(json.dumps(report, indent=1))
    print(f'-> {path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
