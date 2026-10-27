"""Verifier worker: check one constituency's OCR before it may be published.

    python scripts/ci/verify_ac.py AC CROPS_TAR ROWS SUMMARY OUT_DIR [--draft-keys draft-AC.npy]
        [--shard i/N | --checks check-AC.s*.json]

The per-card checks (V1, V4) run part by part on every core. With `--shard i/N`
they run for every N-th part only and write OUT_DIR/check-<ac>.s<i>.json (no
EPICs: part, page, cell and reason); a run given those files with `--checks`
skips V1/V4, refuses unless the shards covered every part, and does the rest
as a single run would, with the same result.

Runs after `ocr_ac.py`, on the same crops, and writes OUT_DIR/verify-<ac>.json:

    {"ac", "verdict": "pass" | "hold", "reasons": [...], "stats": {...},
     "disputed": [[part, page, cell, reason], ...], "parts": {part: [flags]}}

Every published record gets, on top of the readers that produced it:

  V1  independent re-read (prototype reader; Tesseract psm 13 where it
      disagrees) — every character must be supported           -> else disputed
  V2  structure — serials strictly increasing within a part, no serial twice,
      no EPIC twice in the AC unless every copy was read
      unanimously, every full page has every card            -> disputed / part flag
  V3  the part's printed elector total equals the cards read   -> part flag
      less the cards marked deleted; and those deletions equal the printed
      count — if they do not, or there are more live cards than the
      total, a deleted elector may be unmarked, so every record of the
      part is disputed (unless the total is implausibly small: a misread)
  V4  EPICs the draft roll does not corroborate must have their letters
      confirmed by the prototype reader                         -> else disputed

A constituency is held back (not published at all) if disputed records exceed
3% of what it would publish, or if V2/V3 find more than 0.5% of its printed
cards missing. A held AC shows as "not loaded yet" on the site, never as
"not found". Disputed records are withheld individually.

Also writes OUT_DIR/audit-<ac>.png (15 random verified records, for the daily
hand-checked audit, V6) and OUT_DIR/review-<ac>.png (disputed records).
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import os
import random
import sys
import tarfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'ocr'))

import numpy as np  # noqa: E402

import crops as C  # noqa: E402
import verify as V  # noqa: E402

HOLD_DISPUTED = 0.03
HOLD_MISSING = 0.005


def load_rows(path: str) -> list[dict]:
    with gzip.open(path, 'rt', encoding='utf8') as fh:
        return [json.loads(line) for line in fh if line.strip()]


def card_crops(tar_path: str) -> dict[int, list]:
    """part -> pages as `crops.read_bundle` returns them (Kannada bundles only)."""
    out = {}
    with tarfile.open(tar_path) as tar:
        for m in tar.getmembers():
            if m.name.endswith('.zip') and not m.name.startswith('eng-'):
                index, pages = C.read_bundle(tar.extractfile(m).read())
                out[index['part']] = pages
    return out


_W: dict = {}


def _init(tar_path: str, keys_path: str | None) -> None:
    _W['tar'] = tar_path
    _W['keys'] = (np.sort(np.load(keys_path).astype(np.uint64))
                  if keys_path and Path(keys_path).exists() else None)


def check_part(item: tuple[int, list[dict]]) -> tuple[dict, collections.Counter]:
    """V1 and V4 for one part's published records: ({(part, page, cell): reason}, stats).
    V1 is tried first, so it names a record both would dispute, as before."""
    part, rows = item
    with tarfile.open(_W['tar']) as tar:
        try:
            _, pages = C.read_bundle(tar.extractfile(f'{part}.zip').read())
        except KeyError:
            pages = None

    def crop_of(r):
        return pages[r['page']][0][r['cell']] if pages else None

    disputed, stats = {}, collections.Counter()
    pub = [r for r in rows if r['epicOk']]
    seen = [(r, crop_of(r)) for r in pub]
    seen = [(r, c) for r, c in seen if c is not None]
    reads = [V.proto_read(c) for _, c in seen]
    for (r, _), reason in zip(seen, V.v1([(c, r['epic']) for r, c in seen], reads=reads)):
        if reason:
            disputed.setdefault((part, r['page'], r['cell']), reason)
    for _ in seen:
        stats['v1_checked'] += 1
    for r, k in zip(pub, V.corroborated([r['epic'] for r in pub], _W['keys'])):
        if k is None:
            stats['v4_no_draft'] += 1
            continue
        if k:
            stats['v4_corroborated'] += 1
            continue
        stats['v4_new'] += 1
        c = crop_of(r)
        reason = V.v4(c, r['epic']) if c is not None else 'v4:nocrop'
        if reason:
            disputed.setdefault((r['part'], r['page'], r['cell']), reason)
    return disputed, stats


def run_checks(rows_by_part: dict, parts: list[int], tar_path: str, keys_path: str | None):
    """V1/V4 over `parts`, one process per core."""
    disputed, stats = {}, collections.Counter()
    with ProcessPoolExecutor(os.cpu_count() or 4, initializer=_init, initargs=(tar_path, keys_path)) as pool:
        for d, st in pool.map(check_part, [(p, rows_by_part[p]) for p in parts]):
            disputed.update(d)
            stats.update(st)
    return disputed, stats


def v2_structure(rows_by_part: dict[int, list[dict]], summary: dict) -> tuple[dict, dict]:
    disputed, part_flags = {}, collections.defaultdict(list)
    for part, rows in rows_by_part.items():
        seen = collections.Counter(r['serial'] for r in rows)
        prev = 0
        for r in rows:
            key = (part, r['page'], r['cell'])
            if seen[r['serial']] > 1:
                disputed[key] = 'v2:serial-twice'
            elif r['serial'] <= prev:
                disputed[key] = 'v2:serial-order'
            prev = max(prev, r['serial'])
        # A hole — an empty cell before the page's last card — means a card's
        # header could not be cut. Trailing empty cells are normal: the last
        # page of a part, or of a section that ends mid-page.
        grid = summary['perPart'].get(str(part), {}).get('grid', [])
        missing = sum(len(set(range(max(present))) - set(present)) for _, present in grid if present)
        if missing:
            part_flags[part].append(f'v2:missing-cards:{missing}')
    by_epic = collections.defaultdict(list)
    for part, rows in rows_by_part.items():
        for r in rows:
            # A deleted card beside a live one is a voter who moved within the
            # AC (134 such pairs in AC 162), not a misread; only live copies count.
            if r['epicOk'] and not r.get('deleted'):
                by_epic[r['epic']].append(r)
    for epic, copies in by_epic.items():
        if len(copies) > 1 and not all(r['how'] == 'direct' for r in copies):
            for r in copies:
                if r['how'] != 'direct':
                    disputed[(r['part'], r['page'], r['cell'])] = 'v2:epic-twice'
    return disputed, part_flags


def v3_totals(rows_by_part: dict[int, list[dict]], summary: dict, part_flags: dict,
              disputed: dict) -> dict:
    checked = matched = 0
    missing = 0
    printed = 0
    for part_s, info in summary['perPart'].items():
        part = int(part_s)
        t = info.get('totals')
        if not t or t.get('conflict'):
            part_flags[part].append('v3:unreadable' if not t else 'v3:cover-summary-conflict')
            continue
        rows = rows_by_part.get(part, [])
        deleted = sum(bool(r.get('deleted')) for r in rows)
        cards = len(rows) - deleted
        if cards - t['total'] > 0.2 * t['total']:
            # Far more live cards than the total: the summary's net row did not
            # read and another row (additions, ~30) was taken for it — seen on
            # 8 of AC 162's 191 parts. Unmarked deletions leave a surplus of a
            # few cards, never this; the total is treated as unreadable.
            part_flags[part].append(f"v3:implausible-total:{cards}/{t['total']}")
            continue
        checked += 1
        printed += t['total']
        deletions_ok = cards <= t['total'] and t.get('deleted', deleted) == deleted
        if (cards == t['total'] and deletions_ok
                and ('end' not in t or max((r['serial'] for r in rows), default=0) == t['end'])):
            matched += 1
            continue
        part_flags[part].append(f"v3:count:{cards}/{t['total']}")
        missing += max(0, t['total'] - cards)
        if not deletions_ok:
            part_flags[part].append(f"v3:deleted:{deleted}/{t.get('deleted', '?')}")
            for r in rows:
                disputed.setdefault((part, r['page'], r['cell']), 'v3:deleted:unsettled')
    return {'checked': checked, 'matched': matched, 'printed': printed, 'missing': missing}


def sheet(items, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    try:
        font = ImageFont.load_default(size=22)
    except TypeError:          # Pillow < 10.1
        font = ImageFont.load_default()
    rows = []
    for crop, label in items:
        big = crop.resize((crop.width * 3, crop.height * 3))
        im = Image.new('L', (big.width + 520, max(big.height, 30) + 8), 255)
        im.paste(big, (4, 4))
        ImageDraw.Draw(im).text((big.width + 20, 6), label, fill=0, font=font)
        rows.append(im)
    if not rows:
        return
    w = max(r.width for r in rows)
    out = Image.new('L', (w, sum(r.height for r in rows)), 255)
    y = 0
    for r in rows:
        out.paste(r, (0, y))
        y += r.height
    out.save(path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('ac', type=int)
    ap.add_argument('crops')
    ap.add_argument('rows')
    ap.add_argument('summary')
    ap.add_argument('out')
    ap.add_argument('--draft-keys')
    ap.add_argument('--shard', help='i/N: V1/V4 for every N-th part only, written to a check file')
    ap.add_argument('--checks', nargs='+', help='shard check files: use them instead of running V1/V4')
    args = ap.parse_args()
    t0 = time.time()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.rows)
    rows_by_part = collections.defaultdict(list)
    for r in rows:
        rows_by_part[r['part']].append(r)
    for rs in rows_by_part.values():
        rs.sort(key=lambda r: (r['page'], r['cell']))
    keys_path = args.draft_keys if args.draft_keys and Path(args.draft_keys).exists() else None

    if args.shard:
        i, n = map(int, args.shard.split('/'))
        mine = sorted(rows_by_part)[i::n]
        found, st = run_checks(rows_by_part, mine, args.crops, keys_path)
        (out / f'check-{args.ac}.s{i}.json').write_text(json.dumps({
            'parts': mine, 'stats': dict(st),
            'disputed': [[p, pg, c, why] for (p, pg, c), why in sorted(found.items())]}))
        print(f'AC {args.ac} shard {i}/{n}: {len(mine)} parts, {len(found)} disputed, {dict(st)}')
        return 0

    if args.checks:
        found, st, covered = {}, collections.Counter(), set()
        for f in args.checks:
            c = json.loads(Path(f).read_text('utf8'))
            covered.update(c['parts'])
            st.update(c['stats'])
            found.update({(p, pg, cl): why for p, pg, cl, why in c['disputed']})
        if covered != set(rows_by_part):
            raise SystemExit(f'shard checks cover {len(covered)} parts, rows have {len(rows_by_part)}: '
                             f'missing {sorted(set(rows_by_part) - covered)[:10]}')
    else:
        found, st = run_checks(rows_by_part, sorted(rows_by_part), args.crops, keys_path)

    summary = json.loads(Path(args.summary).read_text('utf8'))
    pages_by_part = card_crops(args.crops)

    def crop_of(r):
        pages = pages_by_part.get(r['part'])
        return pages[r['page']][0][r['cell']] if pages else None

    disputed, part_flags = v2_structure(rows_by_part, summary)
    v3 = v3_totals(rows_by_part, summary, part_flags, disputed)

    published = [r for r in rows if r['epicOk']]
    for k, why in found.items():
        disputed.setdefault(k, why)
    stats = st
    n_pub = len(published)
    n_disputed = sum(1 for r in published if (r['part'], r['page'], r['cell']) in disputed)
    reasons_count = collections.Counter(v.split(':')[0] + ':' + v.split(':')[1] for v in disputed.values())
    missing_v2 = sum(int(f.split(':')[-1]) for fl in part_flags.values() for f in fl if f.startswith('v2:missing'))
    printed = v3['printed'] or sum(len(v) for v in rows_by_part.values())
    reasons = []
    if n_pub and n_disputed / n_pub > HOLD_DISPUTED:
        reasons.append(f'disputed {n_disputed}/{n_pub} > {HOLD_DISPUTED:.0%}')
    if (missing_v2 + v3['missing']) / max(printed, 1) > HOLD_MISSING:
        reasons.append(f'missing cards {missing_v2 + v3["missing"]}/{printed} > {HOLD_MISSING:.1%}')
    verdict = 'hold' if reasons else 'pass'

    result = {
        'ac': args.ac, 'verdict': verdict, 'reasons': reasons,
        'stats': {'cards': len(rows), 'published': n_pub, 'disputed': n_disputed,
                  'disputedBy': dict(reasons_count), 'v3': v3, 'v2MissingCards': missing_v2,
                  **dict(stats), 'secs': round(time.time() - t0)},
        'disputed': [[p, pg, c, why] for (p, pg, c), why in sorted(disputed.items())],
        'parts': {str(p): f for p, f in sorted(part_flags.items()) if f},
    }
    (out / f'verify-{args.ac}.json').write_text(json.dumps(result))
    print(json.dumps({k: v for k, v in result.items() if k not in ('disputed', 'parts')}))

    rnd = random.Random(f'audit-{args.ac}')
    ok = [r for r in published if (r['part'], r['page'], r['cell']) not in disputed]
    sheet([(crop_of(r), f"{r['part']}/{r['serial']}  {r['epic']}") for r in rnd.sample(ok, min(15, len(ok)))],
          out / f'audit-{args.ac}.png')
    bad = [r for r in published if (r['part'], r['page'], r['cell']) in disputed]
    sheet([(crop_of(r), f"{r['part']}/{r['serial']} {r['epic']} {disputed[(r['part'], r['page'], r['cell'])]}")
           for r in rnd.sample(bad, min(40, len(bad)))], out / f'review-{args.ac}.png')
    return 0


if __name__ == '__main__':
    sys.exit(main())
