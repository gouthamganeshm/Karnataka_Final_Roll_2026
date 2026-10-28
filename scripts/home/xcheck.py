"""Full English cross-check: every card of an AC against the English roll.

    python scripts/home/xcheck.py AC live-rows.jsonl.gz live-verify.json live-summary.json engfull.tar OUT_DIR

The English roll is the same roll set separately in English: same parts, pages
and cells. Every Kannada card (the site's source) is joined with the English
card in its cell, and every card lands in one bucket:

  confirmed   published, and the English roll reads the same EPIC (any English
              reading: it is a second roll) with the same deleted mark
  kan-only    published, the English card unreadable, the Kannada readers
              agreed outright ('direct'): the publish rule both rolls started
              from; counted, not reviewed
  auto        decided from two rolls without a person: a published card the
              English roll corrects, or a withheld one it recovers, to an EPIC
              that is also a reading of the Kannada card
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
VERSION = 1


def valid(e) -> bool:
    return bool(e and EPIC.match(e))


def load_rows(data: bytes) -> list[dict]:
    return [json.loads(line) for line in gzip.decompress(data).decode('utf8').splitlines() if line.strip()]


def published(rows: list[dict], verify: dict) -> tuple[dict, dict]:
    """key -> (epic, deleted) for each card the site shows; key -> dispute reason."""
    disputed = {tuple(d[:3]): d[3] for d in verify['disputed']}
    undeleted = {tuple(d) for d in verify.get('undeleted', [])}
    pub = {}
    for r in rows:
        k = (r['part'], r['page'], r['cell'])
        if r['epicOk'] and valid(r['epic']) and k not in disputed:
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


def compare(ac: int, kan: list[dict], verify: dict, ksum: dict, eng: list[dict], esum: dict) -> dict:
    pub, disputed = published(kan, verify)
    ejoin, joined = join(kan, eng)
    kkeys = {(r['part'], r['page'], r['cell']) for r in kan}
    counts, auto, manual = collections.Counter(), [], []
    epic_seen = collections.Counter(e for e, _ in pub.values())

    def card(r):
        return None if r is None else {
            'epic': r['epic'], 'epicOk': r['epicOk'], 'how': r.get('how'), 'rd': r.get('rd'),
            'serial': r['serial'], 'ok': r['ok'], 'deleted': bool(r.get('deleted'))}

    def flag(cat, key, k, e, note=''):
        manual.append({'id': len(manual), 'key': list(key), 'cat': cat, 'note': note,
                       'published': list(pub[key]) if key in pub else None,
                       'disputed': disputed.get(key), 'kan': card(k), 'eng': card(e)})
        counts[f'manual:{cat}'] += 1

    eng_parts = {r['part'] for r in eng}
    for k in kan:
        key = (k['part'], k['page'], k['cell'])
        if k['part'] not in eng_parts:
            counts['part-not-in-english'] += 1
            continue
        e = ejoin.get(key)
        kreads = {x for x in [k['epic'], *(k.get('rd') or [])[:2]] if valid(x)}
        eread = e['epic'] if e is not None and valid(e['epic']) else None
        edel = bool(e and e.get('deleted'))
        if key in pub:
            epic, kdel = pub[key]
            if e is None:
                flag('no-english-card', key, k, e)
            elif eread == epic:
                if edel != kdel:
                    flag('deleted-mark', key, k, e)
                elif e['ok'] and k['ok'] and e['serial'] != k['serial']:
                    flag('serial', key, k, e)
                else:
                    counts['confirmed'] += 1
            elif eread is None or not e['epicOk']:
                # English unsure. Its best guess still disagrees, or it has none.
                if k.get('how') == 'direct' and edel == kdel:
                    counts['kan-only'] += 1
                else:
                    flag('english-unread', key, k, e)
            elif eread in kreads and k.get('how') != 'direct' and edel == kdel and epic_seen[eread] == 0:
                auto.append([*key, eread, kdel, 'corrected'])
                counts['auto:corrected'] += 1
            else:
                flag('conflict', key, k, e)
        else:
            # Withheld: unread, the readers disagreed, or the verifier disputed it.
            if e is not None and e['epicOk'] and eread in kreads and edel == bool(k.get('deleted')) \
                    and epic_seen[eread] == 0:
                auto.append([*key, eread, edel, 'recovered'])
                epic_seen[eread] += 1
                counts['auto:recovered'] += 1
            else:
                flag('withheld', key, k, e)
    # Cards the English roll has and the Kannada rows do not: a voter possibly missed.
    for key, e in ejoin.items():
        if key not in kkeys and joined.get(key[0]) == 'cell':
            flag('kannada-missing', key, None, e)
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
