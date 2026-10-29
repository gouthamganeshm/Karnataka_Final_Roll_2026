"""Full English cross-check: every card of an AC against the English roll.

    python scripts/home/xcheck.py AC live-rows.jsonl.gz live-verify.json live-summary.json engfull.tar OUT_DIR

The English roll is the same roll set separately in English: same parts, pages
and cells. Every Kannada card (the site's source) is joined with the English
card in its cell, and every card lands in one bucket:

  confirmed   published, and an English reader reads the same EPIC (it is a
              second roll) with the same deleted mark
  confirmed-digits  published; the English roll reads the same 7 digits but
              slips on a series letter (a round one, or any when it is
              unsure), and two Kannada readers give the published series
  confirmed-kan-deletion  both rolls read the EPIC; only the Kannada roll's
              mark reader sees the deletion code printed after it
  not-a-card  a page-1 cell neither roll can read (the part's photo, heading)
  kan-only    published, the English card absent or unsure, two Kannada
              readers on the published EPIC: the publish rule both rolls
              started from; counted, not reviewed
  auto        decided from two rolls without a person: a published card the
              English roll corrects, or a withheld one it recovers, to an EPIC
              that is also a reading of the Kannada card; or a serial set to
              the card's place in its part (English roll complete) that the
              English reading confirms (a cell the Kannada cut skipped shifts
              every serial after it)
  manual      anything else: the rolls disagree, neither reads it, a deleted
              mark differs, or a card is in one roll only

A part whose serials do not line up cell by cell (pages shifted in one roll)
is joined by serial instead, and says so. Parts whose card count differs from
the printed total are listed.

Writes OUT_DIR/xcheck-<ac>.json: the ledger the review and the apply read. It
holds EPICs: it lives on the private draft release, never in git.
"""
from __future__ import annotations

import collections
import gzip
import hashlib
import json
import re
import sys
import tarfile
import time
from pathlib import Path

EPIC = re.compile(r'^[A-Z]{3}[0-9]{7}$')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import epic_format  # noqa: E402
VERSION = 5


def valid(e) -> bool:
    return bool(e and EPIC.match(e))


ROUND = set('COGQ')


def prefix_slip(read: str, epic: str, sure: bool) -> bool:
    """`read` is `epic` but for its series letters: an English slip when the
    letters are round (C read as O: its readers do it even when they agree),
    or any letter when the English readers were unsure (a deletion stamp on
    the card throws them)."""
    diff = [(a, b) for a, b in zip(read[:3], epic[:3]) if a != b]
    return read[3:] == epic[3:] and bool(diff) and (not sure or all(a in ROUND and b in ROUND for a, b in diff))


def load_rows(data: bytes) -> list[dict]:
    return [json.loads(line) for line in gzip.decompress(data).decode('utf8').splitlines() if line.strip()]


def published(rows: list[dict], verify: dict) -> tuple[dict, dict]:
    """key -> (epic, deleted) for each card the site shows; key -> dispute reason."""
    disputed = {tuple(d[:3]): d[3] for d in verify['disputed']}
    undeleted = {tuple(d) for d in verify.get('undeleted', [])}
    pub = {}
    for r in rows:
        k = (r['part'], r['page'], r['cell'])
        if r['epicOk'] and epic_format.valid(r['epic']) and k not in disputed:
            pub[k] = (r['epic'], bool(r.get('deleted')) and k not in undeleted)
    return pub, disputed


def join(kan: list[dict], eng: list[dict]) -> tuple[dict, dict]:
    """(part, page, cell) -> English row; per part, how it was joined."""
    by_part = collections.defaultdict(list)
    for r in eng:
        by_part[r['part']].append(r)
    kparts = collections.defaultdict(list)
    for r in kan:
        kparts[r['part']].append(r)
    out, how = {}, {}
    for part, erows in by_part.items():
        cell = {(r['page'], r['cell']): r for r in erows}
        both = [(k, cell.get((k['page'], k['cell']))) for k in kparts.get(part, [])]
        pairs = [(k, e) for k, e in both if e and k['ok'] and e['ok']]
        same = sum(k['serial'] == e['serial'] for k, e in pairs)
        if len(pairs) >= 10 and same < 0.9 * len(pairs):
            # One roll's pages are shifted: pair cards by serial (unique in a part).
            ser = collections.Counter(r['serial'] for r in erows if r['ok'])
            by_ser = {r['serial']: r for r in erows if r['ok'] and ser[r['serial']] == 1}
            for k in kparts.get(part, []):
                if k['ok'] and k['serial'] in by_ser:
                    out[(part, k['page'], k['cell'])] = by_ser[k['serial']]
            how[part] = f'serial ({same}/{len(pairs)} cells lined up)'
        else:
            for (pg, c), e in cell.items():
                out[(part, pg, c)] = e
            how[part] = 'cell'
    return out, how


def true_serials(eng: list[dict], ksum: dict, esum: dict) -> dict:
    """(part, page, cell) -> serial from the card's place in its part, for parts the
    English roll has completely: as many cards as the printed Start..Ending, or
    (no printed range) every English serial its readers are sure of sitting at
    its place in one unbroken run."""
    by_part = collections.defaultdict(list)
    for r in eng:
        by_part[r['part']].append(r)
    out = {}
    for part, rows in by_part.items():
        t = (ksum.get('perPart', {}).get(str(part), {}).get('totals') or
             esum.get('perPart', {}).get(str(part), {}).get('totals') or {})
        rows.sort(key=lambda r: (r['page'], r['cell']))
        if t.get('start') is not None and t.get('end') is not None and len(rows) == t['end'] - t['start'] + 1:
            first = t['start']
        else:
            # No printed range: every serial the English readers are sure of
            # sits at its place in an unbroken run (and most are sure).
            sure = [(i, r['serial']) for i, r in enumerate(rows) if r['ok']]
            starts = {serial - i for i, serial in sure}
            if len(starts) != 1 or len(sure) < 0.9 * len(rows):
                continue
            first = starts.pop()
        for i, r in enumerate(rows):
            out[(part, r['page'], r['cell'])] = first + i
    return out


def compare(ac: int, kan: list[dict], verify: dict, ksum: dict, eng: list[dict], esum: dict) -> dict:
    pub, disputed = published(kan, verify)
    ejoin, joined = join(kan, eng)
    kkeys = {(r['part'], r['page'], r['cell']) for r in kan}
    counts, auto, manual = collections.Counter(), [], []
    epic_seen = collections.Counter(e for e, _ in pub.values())

    def card(r):
        return None if r is None else {
            'epic': r['epic'], 'epicOk': r['epicOk'], 'how': r.get('how'), 'rd': r.get('rd'),
            'serial': r['serial'], 'ok': r['ok'], 'deleted': bool(r.get('deleted')),
            'at': [r['page'], r['cell']]}       # its own place: a part joined by serial pairs other cells

    def flag(cat, key, k, e, note='', serial=None):
        manual.append({'id': len(manual), 'key': list(key), 'cat': cat, 'note': note, 'serial': serial,
                       'published': list(pub[key]) if key in pub else None,
                       'disputed': disputed.get(key), 'kan': card(k), 'eng': card(e)})
        counts[f'manual:{cat}'] += 1

    eng_parts = {r['part'] for r in eng}
    # Only where the rolls line up cell for cell: a part joined by serial has
    # its English places on other pages and cells than the Kannada ones.
    truth = {k: v for k, v in true_serials(eng, ksum, esum).items() if joined.get(k[0]) == 'cell'}

    def kagree(k, epic):
        return sum(x == epic for x in (k.get('rd') or [])[:3])

    def done(key, epic, deleted, serial, why):
        auto.append([*key, epic, deleted, serial, why])
        counts[f'auto:{why}'] += 1

    for k in kan:
        key = (k['part'], k['page'], k['cell'])
        if k['part'] not in eng_parts:
            counts['part-not-in-english'] += 1
            continue
        e = ejoin.get(key)
        kreads = {x for x in [k['epic'], *(k.get('rd') or [])[:3]] if valid(x)}
        ereads = collections.Counter(x for x in ([e['epic'], *(e.get('rd') or [])[:3]] if e else []) if valid(x))
        eread = e['epic'] if e is not None and e['epicOk'] and valid(e['epic']) else None
        edel = bool(e and e.get('deleted'))
        # The serial: the card's place in its part, when the English roll has
        # every card of the part (a skipped cell shifts the readings after it).
        t = truth.get(key)
        fix = None
        if t is not None and k['serial'] != t:
            if e is not None and e['ok'] and e['serial'] == t:
                fix = t                  # the English reader is sure of it, and it is the card's place
            elif k['ok'] and not (e is not None and e['ok']):
                pass                     # the Kannada reader is sure, the English one is not: it stands
            else:
                flag('serial', key, k, e, f'place in part says {t}', serial=t)
                continue
        if key in pub:
            epic, kdel = pub[key]
            strong = k.get('how') == 'direct' or kagree(k, epic) >= 2   # two Kannada readers on it
            if e is None:
                # No English card in this cell (its pages sit elsewhere): the Kannada roll alone.
                if strong and fix is None:
                    counts['kan-only'] += 1
                else:
                    flag('no-english-card', key, k, e)
            elif epic in ereads:                        # an English reader read this very EPIC
                if edel and not kdel:
                    flag('deleted-mark', key, k, e)
                elif kdel and not edel and fix is None:
                    # The reason code (Q, R, S) printed right after the EPIC: the
                    # English mark reader misses it there (Hassan: 13 of 13 by eye).
                    counts['confirmed-kan-deletion'] += 1
                elif fix is not None:
                    done(key, epic, kdel, fix, 'serial')
                else:
                    counts['confirmed'] += 1
            elif (edel == kdel and fix is None and (k.get('how') == 'direct' or kagree(k, epic) >= 2)
                  and ereads and all(prefix_slip(x, epic, bool(e['epicOk'])) for x in ereads)):
                # The 7 digits agree in both rolls; two Kannada readers give the series.
                counts['confirmed-digits'] += 1
            elif eread is None:
                if strong and (edel == kdel or kdel) and fix is None:
                    counts['kan-only'] += 1             # English unsure; two Kannada readers agreed
                else:
                    flag('english-unread', key, k, e)
            elif eread in kreads and k.get('how') != 'direct' and edel == kdel and epic_seen[eread] == 0:
                done(key, eread, kdel, fix, 'corrected')
            else:
                flag('conflict', key, k, e)
        else:
            # Withheld: unread, the readers disagreed, or the verifier disputed it.
            common = [x for x in ereads if x in kreads]
            kdirect = k.get('how') == 'direct' or kagree(k, k['epic']) >= 2
            pick = eread if eread in kreads else (
                common[0] if len(common) == 1 and (ereads[common[0]] >= 2 or
                                                   (kdirect and common[0] == k['epic'])) else None)
            if pick and e is not None and edel == bool(k.get('deleted')) and epic_seen[pick] == 0:
                done(key, pick, edel, fix, 'recovered')
                epic_seen[pick] += 1
            elif k['page'] <= 1 and not kreads and not ereads:
                counts['not-a-card'] += 1               # the part's photo or heading, read as cells
            else:
                flag('withheld', key, k, e)
    # Cards the English roll has and the Kannada rows do not: a voter possibly missed.
    for key, e in ejoin.items():
        if key not in kkeys and joined.get(key[0]) == 'cell':
            flag('kannada-missing', key, None, e, serial=truth.get(key, e['serial']))
    parts = {}
    for p, v in ksum.get('perPart', {}).items():
        t = (v.get('totals') or {}).get('total')
        ev = esum.get('perPart', {}).get(p, {})
        live = sum(1 for k, (_, d) in pub.items() if k[0] == int(p) and not d)
        if t is not None and live != t:
            parts[p] = {'printed': t, 'published': live, 'engCards': ev.get('cards'), 'join': joined.get(int(p))}
    for p, h in joined.items():
        if h != 'cell':
            parts.setdefault(str(p), {})['join'] = h
    return {'ac': ac, 'version': VERSION, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'cards': len(kan), 'published': len(pub), 'counts': dict(counts),
            'engUnread': esum.get('unread', []), 'parts': parts, 'auto': auto, 'manual': manual}


def main(ac: str, rows_p: str, ver_p: str, sum_p: str, eng_tar: str, out: str) -> int:
    rows_b = Path(rows_p).read_bytes()
    with tarfile.open(eng_tar) as t:
        eng = load_rows(t.extractfile(f'engfull-{ac}.jsonl.gz').read())
        esum = json.loads(t.extractfile(f'engfull-{ac}.summary.json').read())
    led = compare(int(ac), load_rows(rows_b), json.loads(Path(ver_p).read_text('utf8')),
                  json.loads(Path(sum_p).read_text('utf8')), eng, esum)
    led['liveRows'] = hashlib.sha256(rows_b).hexdigest()[:16]
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / f'xcheck-{ac}.json').write_text(json.dumps(led), 'utf8')
    print(json.dumps({'ac': led['ac'], 'cards': led['cards'], **led['counts'], 'parts flagged': len(led['parts'])}))
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:7]))
