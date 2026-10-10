"""Home stage: fetch each part PDF, cut the card crops, ship them to Actions.

Runs on the home machine because the ECI CDN serves residential connections and
refuses GitHub's runners (406, re-checked 2026-10-10 on every runner type). It
does only the cheap half of the work — download, and cutting each card's serial
box and EPIC to ink (`ocr/crops.py`). Tesseract runs on Actions.

Per constituency: every part becomes one crop bundle (crops, the cover and
summary pages for the printed totals, any PDF text layer), the bundles go into
`crops-<ac>.tar`, the tar is uploaded to the draft release, and the OCR
workflow is dispatched for that AC. PDFs are never written to disk.

English cross-check (verifier check V5): for one part per AC, chosen at random
but reproducibly, the *English* roll's PDF is fetched too and shipped as
`crops-eng-<ac>.tar`. If the English roll is not published yet (the Kannada one
may come first) this is skipped and can be run later with `eng-audit`.

    python scripts/home/run.py discover                   # part counts -> cache/manifest.json
    python scripts/home/run.py go                         # Bengaluru first, then largest first
    python scripts/home/run.py go --tranche blr           # only Bengaluru's 28 ACs
    python scripts/home/run.py go --tranche rest          # everything else
    python scripts/home/run.py go --ac 177,196 --limit 3  # a small test
    python scripts/home/run.py go --local pdf-dir         # PDFs already on disk, named <ac>-<part>.pdf
    python scripts/home/run.py eng-audit                  # English cross-check parts, if skipped earlier
    python scripts/home/run.py order                      # print the run order and stop
    python scripts/home/run.py status

Resumable: shipped ACs are recorded in cache/shipped.json and skipped.
"""
from __future__ import annotations

import argparse
import io
import json
import random
import sys
import tarfile
import threading
import time
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

# Bengaluru city: the three BBMP districts and Bangalore Urban — 28 ACs.
BENGALURU = {'B.B.M.P(CENTRAL)', 'B.B.M.P(NORTH)', 'B.B.M.P(SOUTH)', 'BANGALORE URBAN'}


def url(ac: int, part: int, lang: str = 'kan') -> str:
    if lang == 'eng':
        tpl = SOURCE.get('urlEng') or SOURCE['url'].replace('-KAN-', '-ENG-')
    else:
        tpl = SOURCE['url']
    return tpl.format(ac=ac, part=part)


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


def exists(ac: int, part: int, lang: str = 'kan') -> bool:
    for attempt in range(4):
        try:
            req = Request(url(ac, part, lang), method='HEAD', headers={'User-Agent': UA})
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


def run_order(parts_by_ac: dict[int, list[int]], tranche: str) -> list[int]:
    """Bengaluru's ACs first, then everything else; largest first within each."""
    district = {c['acNumber']: c['district'] for c in SEED['constituencies']}
    blr = sorted((a for a in parts_by_ac if district.get(a) in BENGALURU), key=lambda a: -len(parts_by_ac[a]))
    rest = sorted((a for a in parts_by_ac if district.get(a) not in BENGALURU), key=lambda a: -len(parts_by_ac[a]))
    return {'blr': blr, 'rest': rest}.get(tranche, blr + rest)


def audit_part(ac: int, n_parts: int) -> int:
    """The English cross-check part for an AC: random, but the same on every run."""
    return random.Random(f"{SOURCE['rollType']}-{ac}").randint(1, n_parts)


def cut(job: tuple) -> tuple[int, bytes | None, float]:
    """Worker process: fetch (or read) one part and cut it into a bundle."""
    import crops
    ac, part, local, lang = job
    t = time.time()
    data = Path(local).read_bytes() if local else fetch(url(ac, part, lang))
    if not data:
        return part, None, time.time() - t
    cp = crops.cut_part(data)
    return part, crops.write_bundle(cp['pages'], ac, part, cp, lang=lang), time.time() - t


def _add(tar: tarfile.TarFile, name: str, data: bytes) -> None:
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def dispatch(ac: int, kind: str = 'kan') -> None:
    release.gh('workflow', 'run', 'ocr.yml', '-R', release.repo(),
               '-f', f'ac={ac}', '-f', f'tag={release.TAG}', '-f', f'kind={kind}', capture=True)


def cut_ac(ac: int, parts: list[int], args, pool) -> tuple[Path, dict]:
    """Fetch and cut every part of one AC into crops-<ac>.tar (download-bound)."""
    out = CACHE / 'out'
    out.mkdir(parents=True, exist_ok=True)
    tar_path = out / f'crops-{ac}.tar'
    failed, size, t0 = [], 0, time.time()
    local = Path(args.local) if args.local else None
    jobs = [(ac, p, str(local / f'{ac}-{p}.pdf') if local else '', 'kan') for p in parts]

    with tarfile.open(tar_path, 'w') as tar:
        for i, (part, bundle, secs) in enumerate(pool.map(cut, jobs), 1):
            if bundle is None:
                failed.append(part)
            else:
                _add(tar, f'{part}.zip', bundle)
                size += len(bundle)
            print(f'\r  AC {ac}: {i}/{len(parts)} parts cut, {size/1e6:.0f} MB, '
                  f'{len(failed)} unreadable', end='', flush=True)
        _add(tar, 'meta.json', json.dumps({'ac': ac, 'parts': parts, 'failed': failed, 'lang': 'kan'}).encode())
    took = time.time() - t0
    print(f'  ({took:.0f}s, {len(parts)/max(took,1)*60:.1f} parts/min)')
    return tar_path, {'parts': len(parts), 'failed': failed, 'cutSecs': round(took)}


def send_ac(ac: int, parts: list[int], tar_path: Path, rec: dict, args) -> dict:
    """Upload one AC's crops, start its OCR, then ship its English part. Runs
    on the shipping thread, so the next AC is already downloading meanwhile."""
    t1 = time.time()
    mb = tar_path.stat().st_size / 1e6
    release.upload(str(tar_path))
    up = time.time() - t1
    print(f'\n  AC {ac}: uploaded {mb:.0f} MB in {up:.0f}s ({mb * 8 / max(up, 1):.1f} Mbps up)', flush=True)
    tar_path.unlink()
    if not args.no_dispatch:
        dispatch(ac)
        print(f'  AC {ac}: OCR dispatched', flush=True)
    eng = None if args.local or args.no_eng else ship_eng(ac, parts, args)
    return {**rec, 'uploadSecs': round(up), 'eng': eng}


def ship_eng(ac: int, parts: list[int], args) -> dict:
    """Fetch, cut and ship the English cross-check part for one AC (V5)."""
    part = audit_part(ac, max(parts))
    _, bundle, _ = cut((ac, part, '', 'eng'))
    if bundle is None:
        print(f'  AC {ac}: English roll part {part} not available — V5 later via eng-audit')
        return {'part': part, 'ok': False}
    tar_path = CACHE / 'out' / f'crops-eng-{ac}.tar'
    with tarfile.open(tar_path, 'w') as tar:
        _add(tar, f'eng-{part}.zip', bundle)
        _add(tar, 'meta.json', json.dumps({'ac': ac, 'parts': [part], 'failed': [], 'lang': 'eng'}).encode())
    release.upload(str(tar_path))
    tar_path.unlink()
    if not args.no_dispatch:
        dispatch(ac, 'eng')
    print(f'  AC {ac}: English part {part} shipped for the cross-check')
    return {'part': part, 'ok': True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['discover', 'go', 'eng-audit', 'order', 'status'])
    ap.add_argument('--ac', help='comma-separated AC numbers')
    ap.add_argument('--tranche', choices=['blr', 'rest', 'all'], default='all',
                    help='blr = the 28 Bengaluru ACs; rest = all others; all = Bengaluru first, then rest')
    ap.add_argument('--limit', type=int, help='parts per AC, for tests')
    ap.add_argument('--local', help='directory of <ac>-<part>.pdf files instead of fetching')
    ap.add_argument('--workers', type=int, default=4,
                    help='parts fetched and cut at once (default 4, as the draft pipeline used)')
    ap.add_argument('--no-dispatch', action='store_true')
    ap.add_argument('--no-eng', action='store_true', help='skip the English cross-check part')
    ap.add_argument('--force', action='store_true', help='re-ship ACs already shipped')
    args = ap.parse_args()
    acs = [int(a) for a in args.ac.split(',')] if args.ac else None

    if args.cmd == 'discover':
        discover(acs)
        return 0

    shipped = json.loads(SHIPPED.read_text('utf8')) if SHIPPED.exists() else {}
    if args.cmd == 'status':
        names = release.assets()
        count = lambda pre: sum(n.startswith(pre) for n in names)  # noqa: E731
        print(f'shipped from home: {len(shipped)} ACs')
        print(f'release {release.TAG}: crop tars waiting {count("crops-") - count("crops-eng-")} '
              f'(+{count("crops-eng-")} English), OCR done {count("rows-") // 2}, '
              f'verified {count("verify-")}, English cross-checks {count("eng-")}')
        return 0

    if args.local:
        parts_by_ac: dict[int, list[int]] = {}
        for p in Path(args.local).glob('*-*.pdf'):
            a, n = p.stem.split('-')[:2]
            parts_by_ac.setdefault(int(a), []).append(int(n))
    else:
        if not MANIFEST.exists():
            raise SystemExit('run `discover` first')
        manifest = json.loads(MANIFEST.read_text('utf8'))
        parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1))
                       for c in manifest['constituencies'] if c['parts']}

    order = [a for a in run_order(parts_by_ac, args.tranche) if not acs or a in acs]
    if args.cmd == 'order':
        for i, a in enumerate(order, 1):
            print(f'{i:3}. AC {a:3}  {len(parts_by_ac[a]):4} parts')
        return 0

    release.ensure()
    if MANIFEST.exists():
        release.upload(str(MANIFEST))

    if args.cmd == 'eng-audit':
        for ac in order:
            if shipped.get(str(ac), {}).get('eng', {}).get('ok') and not args.force:
                continue
            res = ship_eng(ac, sorted(parts_by_ac[ac]), args)
            shipped.setdefault(str(ac), {})['eng'] = res
            SHIPPED.write_text(json.dumps(shipped, indent=1), 'utf8')
        return 0

    # Downloading and uploading overlap: one thread ships AC k (upload,
    # dispatch, English part) while the process pool fetches and cuts AC k+1.
    # At most two finished tars wait for upload, so a slow uplink cannot fill
    # the disk; it only makes the download pause.
    def ship(ac, parts, tar_path, rec):
        res = send_ac(ac, parts, tar_path, rec, args)
        with lock:
            shipped[str(ac)] = res
            SHIPPED.write_text(json.dumps(shipped, indent=1), 'utf8')

    lock = threading.Lock()
    waiting = []
    with ProcessPoolExecutor(args.workers) as pool, ThreadPoolExecutor(1) as shipper:
        for ac in order:
            if str(ac) in shipped and not args.force:
                continue
            parts = sorted(parts_by_ac[ac])[: args.limit] if args.limit else sorted(parts_by_ac[ac])
            tar_path, rec = cut_ac(ac, parts, args, pool)
            waiting = [f for f in waiting if not f.done()]
            while len(waiting) >= 2:
                waiting.pop(0).result()
            waiting.append(shipper.submit(ship, ac, parts, tar_path, rec))
        for f in waiting:
            f.result()
    print('done — every requested AC is shipped; OCR, verification and publishing continue on Actions')
    return 0


if __name__ == '__main__':
    sys.exit(main())
