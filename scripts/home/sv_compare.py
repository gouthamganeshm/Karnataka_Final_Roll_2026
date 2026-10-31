"""25% sample verification, step 5: every sampled card looked up on the site snapshot.

    python scripts/home/sv_compare.py AC [--local svread-AC.json.gz] [--no-upload]

For each card the fresh readings (sv_read.py) decide what the PDF says:
settled (Kannada and English agree on the EPIC), one (only one roll read it),
conflict (they disagree: both are looked up) or unread. The EPIC is then
looked up the way site/app.js does (sv_site.Site), and the place is looked up
the other way (what the site holds at this AC, booth and serial):

  ok           found here, at this serial, deleted status right
  ok-approx    found in this booth; the site marks the serial "~" and it is off
  serial-glyph found in this booth at a serial differing from the reading only
               in digits the readers confuse (5/9/3/0/8/6): most likely a misread
  serial       found in this booth at another serial not marked "~"
  deleted      found here; deleted on one side only
  wrong-place  found only in another booth or AC
  wrong-epic   not found; the site holds a different EPIC at this place
  missing      not found; nothing at this place on the site
  unread       neither roll gave an EPIC to look up

plus two notes per card: extra (also found elsewhere) and serial-unread. A page
whose serial range holds a different number of records on the site than cards
in the PDF is a `page` observation.

Writes svres-<ac>.json.gz (holds EPICs: private release only) and returns the
counts that go public in docs/proof/sample-verification.md.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home')]
import release  # noqa: E402

TAG = release.TAG
SVR = f'{TAG}-svr'
OUT = ROOT / 'cache' / 'sv'
AUDIT = 5   # random ok cards per AC for eyes (tier C), and as many for the browser (tier D)


GLYPH = str.maketrans('593086', '555555')   # digits the serial readers confuse


def judge(site, ac: int, part: int, cands: list[str], serials: set, deleted: bool | None,
          places: dict, serial: int | None) -> tuple[str, str | None, list]:
    """(result, the candidate it is about, hits) for the best-matching candidate.
    `serials` are every serial the readings allow; `serial` the surest one."""
    rank = ['ok', 'ok-approx', 'deleted', 'serial-glyph', 'serial', 'wrong-place', 'wrong-epic', 'missing']
    best = None
    for c in cands:
        hits = site.lookup(c)
        here = [h for h in hits if h['ac'] == ac and h['part'] == part]
        at = [h for h in here if not serials or h['serial'] in serials]
        if at:
            r = 'ok' if deleted is None or any(h['deleted'] == deleted for h in at) else 'deleted'
        elif here:
            if all(h['approx'] for h in here):
                r = 'ok-approx'
            elif any(str(h['serial']).translate(GLYPH) == str(s).translate(GLYPH) for h in here for s in serials):
                r = 'serial-glyph'
            else:
                r = 'serial'
        elif hits:
            r = 'wrong-place'
        else:
            key = site.key(c)[:6]
            held = [x for s in serials for x in places.get((part, s), [])]
            r = 'wrong-epic' if any(k != key for k, _d, _a in held) else 'missing'
        if best is None or rank.index(r) < rank.index(best[0]):
            best = (r, c, hits)
    return best


def run_offset(cards: dict) -> int | None:
    """Serials on a page run on by cell, so most cards' serial - cell is one
    number; None unless at least half the read serials (and 4) agree on it."""
    diffs = collections.Counter(x[5] - cell for cell, x in cards.items() if x[5] is not None)
    if diffs:
        off, n = diffs.most_common(1)[0]
        if n >= 0.5 * sum(diffs.values()) and n >= 4:
            return off
    return None


def compare(ac: int, reads: dict, site) -> dict:
    places = site.places(ac)
    count = collections.Counter()
    items, oks = [], []
    booths = reads['booths']['booths']
    for part_s, b in booths.items():
        count['booths'] += 1
        count['cards_total'] += b.get('cards', 0)
        count['cards_sampled'] += b.get('sampled', 0)
        if not b['kan']:
            count['booth_not_covered'] += 1
            items.append({'result': 'not-covered', 'part': int(part_s)})
            continue
        count['booths_covered'] += 1
        if b.get('cards') and b['sampled'] < 0.25 * b['cards']:
            count['booth_under_25'] += 1
    for name, pages in reads['reads'].items():
        if not name.endswith('.kan.zip'):
            continue
        part = int(name.split('.')[0])
        eng = reads['reads'].get(f'{part}.eng.zip', {})
        for p, kcards in pages.items():
            kc = {c[0]: c for c in kcards}
            ec = {c[0]: c for c in eng.get(p, [])}
            if eng and set(kc) != set(ec):
                count['page_cells_differ'] += 1
                items.append({'result': 'cells', 'part': part, 'page': int(p),
                              'kan': sorted(kc), 'eng': sorted(ec)})
            # Each roll's serials fitted to the page's run by cell. The serial
            # readers misread 5 as 9 or 3 now and then, a whole page alike on one
            # roll (AC 162's pilot), so every serial the readings allow is kept and
            # the site's must be one of them; the surest (both runs agree, else
            # the rolls' readings agree) is reported and used for the page check.
            k_off, e_off = run_offset(kc), run_offset(ec)
            serials = []
            for cell in sorted(set(kc) | set(ec)):
                k, e = kc.get(cell), ec.get(cell)
                ke = k[1] if k and k[2] else None
                ee = e[1] if e and e[2] else None
                if ke and ee:
                    how = 'settled' if ke == ee else 'conflict'
                    cands = [ke] if ke == ee else [ke, ee]
                elif ke or ee:
                    how, cands = 'one', [ke or ee]
                else:
                    how = 'unread'
                    cands = sorted({x[1] for x in (k, e) if x and x[1]})
                ks, es = (k[5] if k else None), (e[5] if e else None)
                allowed = {ks, es} | {int(x[3]) for x in (k, e) if x and str(x[3]).isdigit()}
                allowed |= {cell + o for o in (k_off, e_off) if o is not None}
                allowed.discard(None)
                if k_off is not None and k_off == e_off:
                    serial = cell + k_off
                elif ks is not None and (es is None or es == ks):
                    serial = ks
                else:
                    serial = es if ks is None else None
                kd = (k[6] == 'X') if k else None
                ed = (e[6] == 'X') if e else None
                deleted = kd if kd is not None else ed
                count['cards'] += 1
                count[f'how_{how}'] += 1
                if serial is None:
                    count['serial_unread'] += 1
                else:
                    serials.append(serial)
                if cands:
                    result, epic, hits = judge(site, ac, part, cands, allowed, deleted, places, serial)
                else:
                    result, epic, hits = 'unread', None, []
                if result != 'unread' and how == 'unread':
                    count['unread_but_matched'] += 1
                count[result] += 1
                count[f'{result}_{how}'] += 1
                if len({(h['ac'], h['part']) for h in hits}) > 1:
                    count['extra'] += 1
                card = {'result': result, 'how': how, 'part': part, 'page': int(p), 'cell': cell,
                        'epic': epic, 'serial': serial, 'deleted': deleted,
                        'kan': k[1:] if k else None, 'eng': e[1:] if e else None, 'site': hits}
                if result != 'ok' or len(hits) > 1 or (kd is not None and ed is not None and kd != ed):
                    items.append(card)
                else:
                    oks.append(card)
            # A page's serials run on without a gap, so its range holds one card
            # per cell; a range that does not fit the cells (a serial misread at
            # an end) says nothing about the site.
            if serials:
                lo, hi = min(serials), max(serials)
                if hi - lo + 1 == len(kc):
                    held = sum(len(places.get((part, s), [])) for s in range(lo, hi + 1))
                    if held != len(kc):
                        count['page'] += 1
                        items.append({'result': 'page', 'part': part, 'page': int(p), 'range': [lo, hi],
                                      'site': held, 'pdf': len(kc)})
                else:
                    count['page_unsure'] += 1
    rng = random.Random(f'sv-audit-{ac}')
    audit = rng.sample(oks, min(2 * AUDIT, len(oks)))
    return {'ac': ac, 'builtAt': site.manifest['builtAt'], 'count': dict(count), 'items': items,
            'audit': audit[:AUDIT], 'browser': audit[AUDIT:],
            'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}


def run(ac: int, site, upload: bool = True, local: str | None = None) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    src = Path(local) if local else OUT / f'svread-{ac}.json.gz'
    if not local:
        release.TAG = SVR
        try:
            release.fetch(str(OUT), [src.name])
        finally:
            release.TAG = TAG
    with gzip.open(src, 'rt', encoding='utf8') as f:
        reads = json.load(f)
    res = compare(ac, reads, site)
    dest = OUT / f'svres-{ac}.json.gz'
    with gzip.open(dest, 'wt', encoding='utf8') as f:
        json.dump(res, f)
    c = res['count']
    print(f'AC {ac}: {c.get("cards", 0)} cards checked ({c.get("cards_sampled", 0)} of {c.get("cards_total", 0)}'
          f' sampled in {c.get("booths_covered", 0)}/{c.get("booths", 0)} booths): ok {c.get("ok", 0)}, '
          + ', '.join(f'{k} {c[k]}' for k in ('ok-approx', 'serial-glyph', 'serial', 'deleted', 'wrong-place', 'wrong-epic',
                                              'missing', 'unread', 'page', 'extra', 'page_cells_differ')
                      if c.get(k)), flush=True)
    if upload:
        release.TAG = SVR
        try:
            release.upload(str(dest))
        finally:
            release.TAG = TAG
        if not local:
            src.unlink(missing_ok=True)
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('ac', type=int)
    ap.add_argument('--local')
    ap.add_argument('--no-upload', action='store_true')
    a = ap.parse_args()
    import sv_site
    run(a.ac, sv_site.Site(), upload=not a.no_upload, local=a.local)
    return 0


if __name__ == '__main__':
    sys.exit(main())
