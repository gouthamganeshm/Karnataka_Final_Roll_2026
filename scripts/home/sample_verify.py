"""Statewide sample verification: published records against ECI's own PDFs.

    python scripts/home/sample_verify.py --ac 1,2,3 [--booths 12 --pages 3] [--out cache/sample-verify]
    python scripts/home/sample_verify.py --shard 2/4            # every 4th AC from the 2nd

For each AC, a fixed random sample (seeded by the AC, so a rerun draws the same
cards) of booths, and of card pages in each booth; every card on a sampled page
is checked. A booth-level fault (pages shifted, a cell skipped) shows on a whole
page, which a card-level sample would see only once.

Each sampled booth's Kannada PDF (what the site was read from) and English PDF
(the same roll set in English: same pages, same cells, typeset separately) are
downloaded afresh and the sampled pages re-cut and re-read:

  epic     the published EPIC against the English card in the same cell, when
           the English readers agree outright ('direct'): an independent
           witness. Else against the fresh Kannada reading (same image: it
           catches a card published from the wrong cell, not a misread).
  serial   the published serial against the serial printed on either card
  deleted  the published deleted mark against the mark beside the serial
  cells    the cards on the page against the rows the page produced

Writes OUT/result-<ac>.json (counts, and each disagreement with the readings)
and OUT/review/ (the two crops of each disagreement, for eyes). Holds EPICs:
keep OUT out of git and off shared places.
"""
from __future__ import annotations

import argparse
import collections
import gzip
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'ocr'))
import release  # noqa: E402

EPIC = re.compile(r'^[A-Z]{3}[0-9]{7}$')
SOURCE = json.loads((ROOT / 'roll-source.json').read_text('utf8'))
URL_KAN = SOURCE['url']
URL_ENG = SOURCE.get('urlEng') or URL_KAN.replace('-KAN-', '-ENG-')


def log(msg: str) -> None:
    print(time.strftime('%H:%M:%S ') + msg, flush=True)


def get_pdf(url: str, dest: Path) -> bytes | None:
    for _ in range(4):
        subprocess.run(['curl', '-s', '-m', '180', '-A', 'Mozilla/5.0', '-o', str(dest), url], check=False)
        if dest.exists() and dest.read_bytes()[:5] == b'%PDF-':
            data = dest.read_bytes()
            dest.unlink()
            return data
        time.sleep(5)
    dest.unlink(missing_ok=True)
    return None


def page_reads(data: bytes, pages: list[int], style: str) -> dict:
    """page -> cell -> (epic, how, raw serial, mark, epic crop) for the sampled pages."""
    import fitz
    import crops as C
    import roll_ocr as R
    doc = fitz.open(stream=data, filetype='pdf')
    want, out = set(pages), {}
    for p, (img, _page) in enumerate(C.page_images(doc)):
        if p not in want:
            continue
        epics, serials = C.cut_page(img)
        e, ok, s, scrops, info = C.ocr_page(epics, serials, style)
        out[p] = {d['cell']: (e[j] if ok[j] else None, d.get('how'), s[j], R.serial_marker(scrops[j]),
                              epics[d['cell']])
                  for j, d in enumerate(info)}
    return out


def digits(s: str | None) -> int | None:
    found = re.findall(r'\d+', s or '')
    return int(found[-1]) if found else None


def review(path: Path, kan, eng, label: str) -> None:
    from PIL import Image, ImageDraw
    ims = [c.convert('L').resize((c.width * 3, c.height * 3)) for c in (kan, eng) if c is not None]
    w = max([i.width for i in ims] + [200]) + 20
    out = Image.new('L', (w + 700, sum(i.height + 10 for i in ims) + 40), 255)
    y = 5
    for i in ims:
        out.paste(i, (5, y))
        y += i.height + 10
    ImageDraw.Draw(out).text((w, 8), label, fill=0)
    out.save(path)


def verify_ac(ac: int, n_booths: int, n_pages: int, out: Path) -> dict:
    data = out / 'data'
    data.mkdir(parents=True, exist_ok=True)
    names = [f'live-rows-{ac}.jsonl.gz', f'live-verify-{ac}.json']
    for attempt in range(3):
        try:
            release.fetch(str(data), names)
            break
        except (RuntimeError, SystemExit):
            if attempt == 2:
                raise
            time.sleep(30)
    ver = json.loads((data / names[1]).read_text('utf8'))
    disputed = {tuple(d[:3]) for d in ver.get('disputed', [])}
    undeleted = {tuple(d) for d in ver.get('undeleted', [])}
    by_page = collections.defaultdict(list)
    with gzip.open(data / names[0], 'rt', encoding='utf8') as f:
        for line in f:
            if line.strip():
                r = json.loads(line)
                by_page[(r['part'], r['page'])].append(r)
    for n in names:
        (data / n).unlink(missing_ok=True)

    rng = random.Random(f'sample-verify-{ac}')
    parts = sorted({p for p, _ in by_page})
    booths = sorted(rng.sample(parts, min(n_booths, len(parts))))
    count = collections.Counter()
    issues = []
    (out / 'review').mkdir(exist_ok=True)
    for part in booths:
        pages = sorted(pg for p, pg in by_page if p == part)
        pick = sorted(rng.sample(pages, min(n_pages, len(pages))))
        kan_pdf = get_pdf(URL_KAN.format(ac=ac, part=part), out / f'k-{ac}-{part}.pdf')
        eng_pdf = get_pdf(URL_ENG.format(ac=ac, part=part), out / f'e-{ac}-{part}.pdf')
        if kan_pdf is None:
            count['booth_unfetched'] += 1
            continue
        kan = page_reads(kan_pdf, pick, 'kan')
        eng = page_reads(eng_pdf, pick, 'eng') if eng_pdf else {}
        count['booths'] += 1
        for pg in pick:
            rows = by_page[(part, pg)]
            k_page, e_page = kan.get(pg, {}), eng.get(pg, {})
            count['pages'] += 1
            if set(k_page) != {r['cell'] for r in rows}:
                count['page_cells_differ'] += 1
                issues.append({'kind': 'cells', 'part': part, 'page': pg,
                               'rows': sorted(r['cell'] for r in rows), 'pdf': sorted(k_page)})
            for r in rows:
                key = (r['part'], r['page'], r['cell'])
                pub = bool(r['epicOk'] and EPIC.match(r['epic'] or '') and key not in disputed)
                deleted = bool(r.get('deleted')) and key not in undeleted
                k = k_page.get(r['cell'])
                e = e_page.get(r['cell'])
                count['cards'] += 1
                if not pub:
                    count['unpublished'] += 1
                    if e and e[0] and e[1] == 'direct':
                        count['unpublished_eng_direct'] += 1
                    continue
                count['published'] += 1
                problems = []
                if e and e[0] and e[1] == 'direct':
                    count['epic_vs_eng'] += 1
                    if e[0] == r['epic']:
                        count['epic_eng_agree'] += 1
                    else:
                        problems.append('epic-eng')
                elif k and k[0]:
                    count['epic_vs_kan_only'] += 1
                    if k[0] == r['epic']:
                        count['epic_kan_agree'] += 1
                    else:
                        problems.append('epic-kan')
                else:
                    count['epic_unchecked'] += 1
                seen = {digits(x[2]) for x in (k, e) if x} - {None}
                if seen:
                    count['serial_checked'] += 1
                    if r['serial'] in seen:
                        count['serial_agree'] += 1
                    elif len(seen) == 1 and k and e:
                        problems.append('serial')
                    else:
                        count['serial_unsettled'] += 1
                if k:
                    count['deleted_checked'] += 1
                    if (k[3] == 'X') != deleted:
                        problems.append('deleted')
                    else:
                        count['deleted_agree'] += 1
                for p in problems:
                    count[f'bad_{p}'] += 1
                if problems:
                    issue = {'kind': problems, 'part': part, 'page': pg, 'cell': r['cell'],
                             'published': [r['epic'], r['serial'], deleted, r.get('how')],
                             'kan': list(k[:4]) if k else None, 'eng': list(e[:4]) if e else None}
                    issues.append(issue)
                    review(out / 'review' / f'{ac}-{part}-{pg}-{r["cell"]}.png',
                           k[4] if k else None, e[4] if e else None,
                           f'AC {ac} part {part} serial {r["serial"]}  published {r["epic"]}  '
                           f'kan {k[0] if k else "-"}  eng {e[0] if e else "-"}  {problems}')
    res = {'ac': ac, 'booths': booths, 'count': dict(count), 'issues': issues,
           'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    (out / f'result-{ac}.json').write_text(json.dumps(res), 'utf8')
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--ac')
    ap.add_argument('--shard', help='i/N: every N-th AC, starting from the i-th (1-based)')
    ap.add_argument('--booths', type=int, default=12)
    ap.add_argument('--pages', type=int, default=3)
    ap.add_argument('--out', default=str(ROOT / 'cache' / 'sample-verify'))
    args = ap.parse_args()
    acs = [int(a) for a in args.ac.split(',')] if args.ac else list(range(1, 225))
    if args.shard:
        i, n = map(int, args.shard.split('/'))
        acs = acs[i - 1::n]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for ac in acs:
        if (out / f'result-{ac}.json').exists():
            continue
        t = time.time()
        try:
            c = verify_ac(ac, args.booths, args.pages, out)['count']
        except Exception as exc:  # noqa: BLE001 - one AC's failure must not stop the shard
            log(f'AC {ac}: FAILED {exc!r}')
            continue
        bad = {k: v for k, v in c.items() if k.startswith('bad_') or k == 'page_cells_differ'}
        log(f"AC {ac}: {c.get('published', 0)} published cards checked, EPIC vs English "
            f"{c.get('epic_eng_agree', 0)}/{c.get('epic_vs_eng', 0)}, serial {c.get('serial_agree', 0)}/"
            f"{c.get('serial_checked', 0)}, deleted {c.get('deleted_agree', 0)}/{c.get('deleted_checked', 0)}"
            f"{', problems ' + str(bad) if bad else ''} ({time.time() - t:.0f}s)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
