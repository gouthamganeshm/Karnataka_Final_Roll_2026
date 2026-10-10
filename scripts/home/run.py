"""Home stage: fetch each part PDF, cut the card crops, ship them to Actions.

Runs on the home machine because the ECI CDN serves residential connections and
refuses GitHub's runners (406, re-checked 2026-10-10 on every runner type). It
does only the cheap half of the work — download, and cutting each card's serial
box and EPIC to ink (`ocr/crops.py`). Tesseract runs on Actions.

Per constituency: every part becomes one crop bundle, the bundles go into
`crops-<ac>.tar`, the tar is uploaded to the draft release, and the OCR workflow
is dispatched for that AC. PDFs are never written to disk.

    python scripts/home/run.py discover                   # part counts -> cache/manifest.json
    python scripts/home/run.py go                         # everything not yet shipped
    python scripts/home/run.py go --ac 177,196 --limit 3  # a small test
    python scripts/home/run.py go --local pdf-dir         # PDFs already on disk, named <ac>-<part>.pdf
    python scripts/home/run.py status

Resumable: shipped ACs are recorded in cache/shipped.json and skipped.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tarfile
import time
import io
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'ocr'))
import release  # noqa: E402

SOURCE = json.loads((ROOT / 'roll-source.json').read_text('utf8'))
SEED = json.loads((ROOT / 'seed' / 'ac-metadata.json').read_text('utf8'))
CACHE = ROOT / 'cache'
MANIFEST = CACHE / 'manifest.json'
SHIPPED = CACHE / 'shipped.json'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')


def url(ac: int, part: int) -> str:
    return SOURCE['url'].format(ac=ac, part=part)


def fetch(u: str, tries: int = 4) -> bytes | None:
    for attempt in range(tries):
        try:
            with urlopen(Request(u, headers={'User-Agent': UA}), timeout=180) as r:
                data = r.read()
            return data if data[:5] == b'%PDF-' else None
        except HTTPError as e:
            if e.code == 404:
                return None
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def exists(ac: int, part: int) -> bool:
    for attempt in range(4):
        try:
            req = Request(url(ac, part), method='HEAD', headers={'User-Agent': UA})
            with urlopen(req, timeout=60) as r:
                return r.status == 200
        except HTTPError as e:
            if e.code == 404:
                return False
        except Exception:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'AC {ac} part {part}: no clear answer from the CDN')


def count_parts(ac: int, hint: int) -> int:
    """Parts run 1..N with no gaps. Check the draft roll's count first (two
    requests when unchanged), otherwise binary-search the boundary."""
    if hint and exists(ac, hint) and not exists(ac, hint + 1):
        return hint
    if not exists(ac, 1):
        return 0
    lo, hi = 1, max(hint, 2)
    while exists(ac, hi):
        lo, hi = hi, hi * 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if exists(ac, mid) else (lo, mid)
    return lo


def discover(acs: list[int] | None) -> dict:
    prev = json.loads(MANIFEST.read_text('utf8')) if MANIFEST.exists() else {}
    known = {c['acNumber']: c for c in prev.get('constituencies', [])}
    seed = {c['acNumber']: c for c in SEED['constituencies']}
    todo = [a for a in sorted(seed) if not acs or a in acs]

    def one(ac):
        n = count_parts(ac, seed[ac]['parts'])
        print(f'  AC {ac:3}: {n} parts', flush=True)
        return ac, n

    with ThreadPoolExecutor(4) as pool:
        for ac, n in pool.map(one, todo):
            known[ac] = {**{k: v for k, v in seed[ac].items() if k != 'parts'}, 'parts': n}
    manifest = {'rollType': SOURCE['rollType'], 'label': SOURCE['label'],
                'labelKn': SOURCE.get('labelKn', ''), 'url': SOURCE['url'],
                'discoveredAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                'constituencies': [known[a] for a in sorted(known)]}
    CACHE.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), 'utf8')
    total = sum(c['parts'] for c in manifest['constituencies'])
    print(f'{len(manifest["constituencies"])} ACs, {total} parts -> {MANIFEST}')
    return manifest


def cut(job: tuple[int, int, str]) -> tuple[int, bytes | None, float]:
    """Worker process: fetch (or read) one part and cut it into a bundle."""
    import crops
    ac, part, local = job
    t = time.time()
    data = Path(local).read_bytes() if local else fetch(url(ac, part))
    if not data:
        return part, None, time.time() - t
    return part, crops.write_bundle(crops.cut_part_bytes(data), ac, part), time.time() - t


def ship_ac(ac: int, parts: list[int], args) -> dict:
    out = CACHE / 'out'
    out.mkdir(parents=True, exist_ok=True)
    tar_path = out / f'crops-{ac}.tar'
    failed, size, t0 = [], 0, time.time()
    local = Path(args.local) if args.local else None
    jobs = [(ac, p, str(local / f'{ac}-{p}.pdf') if local else '') for p in parts]

    with tarfile.open(tar_path, 'w') as tar, ProcessPoolExecutor(args.workers) as pool:
        for i, (part, bundle, secs) in enumerate(pool.map(cut, jobs), 1):
            if bundle is None:
                failed.append(part)
            else:
                info = tarfile.TarInfo(f'{part}.zip')
                info.size = len(bundle)
                tar.addfile(info, io.BytesIO(bundle))
                size += len(bundle)
            print(f'\r  AC {ac}: {i}/{len(parts)} parts cut, {size/1e6:.0f} MB, '
                  f'{len(failed)} unreadable', end='', flush=True)
        meta = json.dumps({'ac': ac, 'parts': parts, 'failed': failed}).encode()
        info = tarfile.TarInfo('meta.json')
        info.size = len(meta)
        tar.addfile(info, io.BytesIO(meta))
    took = time.time() - t0
    print(f'  ({took:.0f}s, {len(parts)/max(took,1)*60:.1f} parts/min)')

    t1 = time.time()
    release.upload(str(tar_path))
    up = time.time() - t1
    print(f'  AC {ac}: uploaded {tar_path.stat().st_size/1e6:.0f} MB in {up:.0f}s '
          f'({tar_path.stat().st_size*8/1e6/max(up,1):.1f} Mbps up)')
    tar_path.unlink()
    if not args.no_dispatch:
        release.gh('workflow', 'run', 'ocr.yml', '-R', release.repo(),
                   '-f', f'ac={ac}', '-f', f'tag={release.TAG}', capture=True)
        print(f'  AC {ac}: OCR dispatched')
    return {'parts': len(parts), 'failed': failed, 'cutSecs': round(took), 'uploadSecs': round(up)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['discover', 'go', 'status'])
    ap.add_argument('--ac', help='comma-separated AC numbers')
    ap.add_argument('--limit', type=int, help='parts per AC, for tests')
    ap.add_argument('--local', help='directory of <ac>-<part>.pdf files instead of fetching')
    ap.add_argument('--workers', type=int, default=4,
                    help='parts fetched and cut at once (default 4, as the draft pipeline used)')
    ap.add_argument('--no-dispatch', action='store_true')
    ap.add_argument('--force', action='store_true', help='re-ship ACs already shipped')
    args = ap.parse_args()
    acs = [int(a) for a in args.ac.split(',')] if args.ac else None

    if args.cmd == 'discover':
        discover(acs)
        return 0

    shipped = json.loads(SHIPPED.read_text('utf8')) if SHIPPED.exists() else {}
    if args.cmd == 'status':
        names = release.assets()
        print(f'shipped from home: {len(shipped)} ACs')
        print(f'release {release.TAG}: {sum(n.startswith("crops-") for n in names)} crop tars waiting, '
              f'{sum(n.startswith("rows-") for n in names)} AC row files done')
        return 0

    if args.local:
        parts_by_ac: dict[int, list[int]] = {}
        for p in Path(args.local).glob('*-*.pdf'):
            a, n = p.stem.split('-')
            parts_by_ac.setdefault(int(a), []).append(int(n))
        manifest = json.loads(MANIFEST.read_text('utf8')) if MANIFEST.exists() else {
            'rollType': SOURCE['rollType'], 'label': SOURCE['label'], 'labelKn': SOURCE.get('labelKn', ''),
            'url': SOURCE['url'], 'constituencies': []}
    else:
        if not MANIFEST.exists():
            raise SystemExit('run `discover` first')
        manifest = json.loads(MANIFEST.read_text('utf8'))
        parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies']}

    release.ensure()
    release.upload(str(MANIFEST)) if MANIFEST.exists() else None
    # Largest first: the biggest constituencies take longest to OCR, so they
    # should start on Actions while the small ones are still downloading.
    order = sorted(parts_by_ac, key=lambda a: -len(parts_by_ac[a]))
    for ac in order:
        if acs and ac not in acs:
            continue
        if str(ac) in shipped and not args.force:
            continue
        parts = sorted(parts_by_ac[ac])[: args.limit] if args.limit else sorted(parts_by_ac[ac])
        shipped[str(ac)] = ship_ac(ac, parts, args)
        SHIPPED.write_text(json.dumps(shipped, indent=1), 'utf8')
    print('done — every requested AC is shipped; OCR and publishing continue on Actions')
    return 0


if __name__ == '__main__':
    sys.exit(main())
