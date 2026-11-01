"""Sort the sample verification's EPIC mismatches into reader slips and real doubts.

    python scripts/home/sv_resolve.py [AC ...]       # default: every svres on disk

A `wrong-epic` card is one whose fresh reading is not on the site while the
site does hold another EPIC at that card's place (AC, part, serial). Most are
the fresh reader confusing look-alike characters (O/Q/G/0, I/1, S/5, ...).
For each one, every reading with one or two look-alike characters swapped is
hashed and compared with what the site holds at the place: a match means the
site has the card under a near-identical EPIC, and the card goes to the
person's review as a `slip` (both images beside the site's variant); no match
means `doubt`. Every other non-minor result (serial, page, deleted,
wrong-place, missing, unread) is a `doubt` as it stands. Writes
cache/sv/resolve-<ac>.json (holds EPICs: private) and prints counts.
"""
from __future__ import annotations

import gzip
import itertools
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home')]
import sv_site  # noqa: E402

SV = ROOT / 'cache' / 'sv'
MINOR = {'ok', 'ok-approx', 'serial-glyph', 'extra', 'cells'}
GROUPS = ['OQGDCU0', 'I1LTJ7', 'S5', 'B83', 'Z27', 'EF', 'MNHW', 'VYU', 'KX', 'A4', 'PR', 'G6', '9g']
ALIKE = {c: set(''.join(g for g in GROUPS if c in g)) - {c} for c in ''.join(GROUPS)}


def variants(epic: str, most: int = 2):
    for n in range(1, most + 1):
        for pos in itertools.combinations(range(len(epic)), n):
            for subs in itertools.product(*(sorted(ALIKE.get(epic[i], ())) for i in pos)):
                v = list(epic)
                for i, c in zip(pos, subs):
                    v[i] = c
                yield ''.join(v)


def series(epic: str):
    """Every three-letter series in front of the reading's digits (and of each
    one-look-alike variant of them): the fresh readers misread series letters
    beyond the look-alike groups (L/I, Y/W, S/G, ...) and print case varies."""
    if len(epic) != 10 or not epic[3:].isdigit():
        return
    # Series with eight digits: the fresh readers dropped one.
    for i in range(3, 11):
        for d in '0123456789':
            yield epic[:i] + d + epic[i:]
    tails = [epic[3:]] + [v for v in variants(epic[3:], 1) if v.isdigit()]
    for tail in tails:
        for p in itertools.product('ABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=3):
            yield ''.join(p) + tail


def serials_of(item: dict) -> set:
    return {s for s in (item.get('serial'), item['kan'][4] if item.get('kan') else None,
                        item['eng'][4] if item.get('eng') else None) if s is not None}


def resolve(site, ac: int) -> dict:
    with gzip.open(SV / 'res' / f'svres-{ac}.json.gz', 'rt', encoding='utf8') as f:
        res = json.load(f)
    places = site.places(ac)
    out = []
    for it in res['items']:
        if it.get('result') in MINOR or 'kan' not in it:
            continue
        rec = {k: it.get(k) for k in ('result', 'how', 'part', 'page', 'cell', 'serial', 'deleted', 'kan', 'eng', 'site')}
        rec['verdict'] = 'doubt'
        if it['result'] == 'wrong-epic':
            held = {k for s in serials_of(it) for k, _d, _a in places.get((it['part'], s), [])}
            cands = {x[0] for x in (it['kan'], it['eng']) if x and x[0]}
            # A section heading printed over the card runs into the reading:
            # keep the EPIC-shaped tail of it.
            cands |= {m.group(0) for c in list(cands) for m in [re.search(r'[A-Z]{3}\d{7}$', c.upper())] if m}
            for c in sorted(cands):
                here = [h for h in site.lookup(c) if h['ac'] == ac and h['part'] == it['part']]
                if here:
                    rec.update(verdict='slip', site_variant=c, from_reading=c, site_at=here)
                    break
            for c in sorted(cands) if rec['verdict'] == 'doubt' else []:
                hit = next((v for v in variants(c) if site.key(v)[:6] in held), None)
                if not hit:
                    hit = next((v for v in series(c) if site.key(v)[:6] in held), None)
                if hit:
                    rec.update(verdict='slip', site_variant=hit, from_reading=c)
                    break
        out.append(rec)
    doc = {'ac': ac, 'items': out}
    (SV / f'resolve-{ac}.json').write_text(json.dumps(doc), 'utf8')
    return doc


def main() -> int:
    acs = [int(a) for a in sys.argv[1:]] or sorted(int(p.name[6:-8]) for p in (SV / 'res').glob('svres-*.json.gz'))
    site = sv_site.Site()
    tot = {}
    for ac in acs:
        doc = resolve(site, ac)
        n = {}
        for r in doc['items']:
            k = f"{r['result']}/{r['verdict']}"
            n[k] = n.get(k, 0) + 1
            tot[k] = tot.get(k, 0) + 1
        print(f'AC {ac}: {n}', flush=True)
    print('total', dict(sorted(tot.items())))
    return 0


if __name__ == '__main__':
    sys.exit(main())
