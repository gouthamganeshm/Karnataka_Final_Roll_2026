"""Second look at an AC's EPIC letters, from what the whole AC says about its series.

    python scripts/ocr/series_pass.py crops-215.tar rows-215.jsonl.gz rows-215.fixed.jsonl.gz

An EPIC starts with a three-letter series (IQG, GGB, SLC...) that thousands of
cards in an AC share. The per-card readers decide letters one card at a time,
and on a letter like G/Q/O/C a thin margin or a Tesseract read shifted by an
extra leading mark (`LIQ…` for `IQG…`) leaves them unable to settle it:

  * a card is withheld, though the same series is read cleanly on 150,000 others;
  * worse, a shifted read once "supported" the glyph reader's Q, and a whole
    series was published as IQQ (AC 215: 627 cards; the crops read IQG).

Cards whose glyph and Tesseract readings agreed outright (`how == "direct"`) are
the evidence: a prefix with at least MIN_DIRECT of them is a series of the AC.
For each fused or withheld card:

  * its read prefix is a series -> pin it (a withheld card the readers could not
    settle on a thin margin);
  * exactly one series differs from its read prefix in one round letter
    (C/O/G/Q both ways) and the read prefix has under 1/RATIO of that series'
    direct cards -> pin that series (IQQ, IQO -> IQG; ZOI -> ZCI). This holds
    for direct cards too: in AC 4 both readers read twelve ZCI cards as ZOI
    (checked on the crops), and a lone ZOI beside 154,895 ZCI is no series.
    Any other letter is left alone, however small its series: small real
    series sit one letter from big ones (BZE beside BZC, MKW beside MQW,
    JIG beside JTG), and in 2026-10 every such pin checked against the
    English roll had changed a correct EPIC;
  * otherwise leave the card as it was.

Only the letters are pinned: the digits go through the same two-reader rule as
anywhere else (`crops.fuse(prefix=...)`), and a card they do not settle is
withheld, including a published one whose prefix was wrong. Rows come out as
`how == "series"`; the summary's published counts are redone.
"""
from __future__ import annotations

import collections
import gzip
import json
import os
import sys
import tarfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import crops  # noqa: E402
import roll_ocr as R  # noqa: E402

MIN_DIRECT = 100     # direct cards that make a prefix a series of this AC
RATIO = 200          # a prefix under 1/RATIO of a one-letter neighbour series is a misread of it
ROUND = set('COGQ')  # the letters the readers confuse with each other


def pin(prefix: str, direct: collections.Counter, big: set) -> str | None:
    if prefix in big:
        return prefix
    near = [b for b in big if round_neighbour(prefix, b)]
    if len(near) == 1 and direct[prefix] * RATIO < direct[near[0]]:
        return near[0]
    return None


def round_neighbour(a: str, b: str) -> bool:
    """a and b differ in exactly one letter, and both of those letters are round."""
    diff = [(x, y) for x, y in zip(a, b) if x != y]
    return len(diff) == 1 and set(diff[0]) <= ROUND


def reread(job: tuple) -> list[tuple[int, str | None]]:
    """One part: (row index, EPIC with its letters pinned, or None) per card asked about."""
    tar_path, part, items = job
    tm = crops.templates('kan')
    with tarfile.open(tar_path) as tar:
        _, pages = crops.read_bundle(tar.extractfile(f'{part}.zip').read())
    out = []
    for i, s, page, cell, sheet, alone in items:
        crop = pages[page][0][cell]
        detail = tm.read_detail(crop)
        out.append((i, crops.fuse(detail, sheet, alone, crops.proto_read(crop, 'kan'), prefix=s) if detail else None))
    return out


def main(tar_path: str, rows_path: str, out_path: str) -> int:
    with gzip.open(rows_path, 'rt', encoding='utf8') as f:
        rows = [json.loads(line) for line in f if line.strip()]
    direct = collections.Counter(r['epic'][:3] for r in rows if r['how'] == 'direct')
    big = {p for p, n in direct.items() if n >= MIN_DIRECT}
    todo = collections.defaultdict(list)
    for i, r in enumerate(rows):
        if R_VALID(r['epic']):
            s = pin(r['epic'][:3], direct, big)
            # Withheld cards are re-read on any series; published ones only to change their series.
            if s and (r['how'] == 'withheld' or s != r['epic'][:3]):
                todo[r['part']].append((i, s, r['page'], r['cell'], r['rd'][0], r['rd'][2]))
    stats = collections.Counter()
    jobs = [(tar_path, part, items) for part, items in sorted(todo.items())]
    # Touching glyphs make the cut search ~0.15 s a card: one process per core.
    with ProcessPoolExecutor(os.cpu_count() or 2) as pool:
        results = [x for res in pool.map(reread, jobs) for x in res]
    for i, fused in results:
        r = rows[i]
        was = r['epicOk']
        if fused:
            r.update(epic=fused, epicOk=True, how='series')
            stats['published' if not was else 'repinned'] += 1
            stats['prefix_changed'] += bool(r['rd'][1]) and fused[:3] != r['rd'][1][:3]
        elif was:
            r.update(epicOk=False, how='withheld')      # a prefix the AC does not support, digits unsettled
            stats['withdrawn'] += 1
        else:
            stats['still_withheld'] += 1
    with gzip.open(out_path, 'wt', encoding='utf8') as out:
        for r in rows:
            out.write(json.dumps(r, separators=(',', ':')) + '\n')
    sp = Path(rows_path).with_suffix('').with_suffix('.summary.json')
    if sp.exists():
        summary = json.loads(sp.read_text('utf8'))
        per = collections.Counter(r['part'] for r in rows if r['epicOk'])
        for k, v in summary['perPart'].items():
            v['published'] = per[int(k)]
        summary['published'] = sum(per.values())
        summary['seriesPass'] = dict(stats)
        Path(out_path).with_suffix('').with_suffix('.summary.json').write_text(json.dumps(summary))
    print(json.dumps({'series': sorted(big), **stats}))
    return 0


def R_VALID(e: str) -> bool:
    return bool(e and R.EPIC_RE.match(e))


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:4]))
