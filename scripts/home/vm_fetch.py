"""Cloud-VM downloader: fetch part PDFs fast, let Actions cut and read them.

    GH_TOKEN=... python scripts/home/vm_fetch.py [--ac 1,2] [--threads 16]

An OCI Ampere VM downloads from the ECI CDN at ~35 MB/s (home: ~4 MB/s) but
has one core, too few to cut crops at that pace. So it only fetches: each
AC's PDFs are split into SHARDS tars exactly as `ocr_ac.py --shard i/N` splits
parts (sorted part list, every N-th from the i-th), uploaded to the private
draft release, and `ocr.yml` runs with kind=pdf: each shard cuts and reads its
own PDFs and the merge job rebuilds crops-<ac>.tar for the verifier.

Same order as the home queue (`run.run_order`: Bengaluru, then districts by
electorate), skipping ACs in the shipped list (copy home's over first). PDFs
are kept on disk only until uploaded.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'home'))
import release  # noqa: E402
import run  # noqa: E402

SHARDS = 20
WORK = f'{release.TAG}-work'    # ocr.yml reads the PDFs from here
OUT = run.CACHE / 'vm-out'


def _add(tar, name, data):
    info = tarfile.TarInfo(name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))


def fetch_ac(ac: int, parts: list[int], threads: int) -> tuple[list[Path], list[int]]:
    OUT.mkdir(parents=True, exist_ok=True)
    order = sorted(parts)
    shard_of = {p: k % SHARDS for k, p in enumerate(order)}
    paths = [OUT / f'pdfs-{ac}.s{i}.tar' for i in range(SHARDS)]
    tars = [tarfile.open(p, 'w') for p in paths]
    lock = threading.Lock()
    t0, done, size = time.time(), 0, 0

    def one(p):
        return p, run.fetch(run.url(ac, p))

    todo, failed = order, []
    for wait in (0, 30, 120, 300):
        if not todo:
            break
        if wait:
            print(f'  AC {ac}: retrying {len(todo)} parts in {wait}s', flush=True)
            time.sleep(wait)
        failed = []
        with ThreadPoolExecutor(threads) as pool:
            for p, data in pool.map(one, todo):
                if not data:
                    failed.append(p)
                    continue
                with lock:
                    _add(tars[shard_of[p]], f'{p}.pdf', data)
                    done += 1
                    size += len(data)
                if done % 50 == 0:
                    print(f'  AC {ac}: {done}/{len(order)} parts, {size / 1e6:.0f} MB, '
                          f'{size / 1e6 / (time.time() - t0):.1f} MB/s', flush=True)
        todo = failed
    meta = json.dumps({'ac': ac, 'parts': order, 'failed': failed, 'lang': 'kan', 'source': 'vm-pdf'}).encode()
    for t in tars:
        _add(t, 'meta.json', meta)
        t.close()
    took = time.time() - t0
    print(f'  AC {ac}: {done}/{len(order)} parts, {size / 1e6:.0f} MB in {took:.0f}s '
          f'({60 * done / max(took, 1):.0f} parts/min), unreadable {failed}', flush=True)
    return paths, failed


def ship(ac: int, paths: list[Path]) -> None:
    for wait in (30, 120, 300, 0):
        try:
            t = time.time()
            # Into the work release: in-flight PDFs must not count against the
            # 1,000-asset limit of the release holding every AC's results.
            release.gh('release', 'upload', WORK, *map(str, paths), '--clobber', '-R', release.repo())
            release.gh('workflow', 'run', 'ocr.yml', '-R', release.repo(), '-f', f'ac={ac}',
                       '-f', f'tag={release.TAG}', '-f', 'kind=pdf', '-f', f'shards={SHARDS}')
            print(f'  AC {ac}: uploaded {sum(p.stat().st_size for p in paths) / 1e6:.0f} MB in '
                  f'{time.time() - t:.0f}s, OCR dispatched', flush=True)
            break
        except Exception as err:  # noqa: BLE001
            if not wait:
                raise
            print(f'  AC {ac}: shipping failed ({err}); retrying in {wait}s', flush=True)
            time.sleep(wait)
    for p in paths:
        p.unlink()


def in_flight(ac: int) -> bool:
    """An OCR run for this AC is already queued or running (an earlier ship, or another machine's):
    uploading again would replace the tars it is about to read."""
    try:
        out = release.gh('run', 'list', '-R', release.repo(), '--workflow', 'ocr.yml', '--json',
                         'displayTitle,status', '-L', '100')
        return any(r['status'] in ('queued', 'in_progress') and r['displayTitle'].startswith(f'OCR AC {ac} (')
                   for r in json.loads(out))
    except Exception:  # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--ac', help='comma-separated ACs (default: every AC not shipped, in queue order)')
    ap.add_argument('--threads', type=int, default=16)
    ap.add_argument('--vm', type=int, help='VM number K in reference/vm-plan.json (python scripts/home/vm_plan.py)')
    ap.add_argument('--share', metavar='K/N', help='this VM is number K of N and takes every N-th district in queue '
                    'order (largest first)')
    ap.add_argument('--small', metavar='K/N', help='take the smallest districts first (home takes the largest); '
                    'with K/N this VM is number K of N and takes every N-th district of that order')
    args = ap.parse_args()
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies'] if c['parts']}
    order = run.run_order(parts_by_ac, 'all')
    if args.ac:
        want = {int(a) for a in args.ac.split(',')}
        order = [a for a in order if a in want]
    if args.vm:
        plan = json.loads((ROOT / 'reference' / 'vm-plan.json').read_text('utf8'))
        mine = set(plan[str(args.vm)])
        order = [a for a in order if a in mine]
        print(f'VM {args.vm}: {len(order)} ACs by plan', flush=True)
    elif args.small or args.share:
        k, n = map(int, (args.small or args.share).split('/'))
        district = {c['acNumber']: c['district'] for c in run.SEED['constituencies']}
        groups = []                              # districts in run_order, each a list of ACs
        for a in order:
            if groups and district.get(groups[-1][0]) == district.get(a):
                groups[-1].append(a)
            else:
                groups.append([a])
        mine = [g for i, g in enumerate(reversed(groups) if args.small else groups) if i % n == k - 1]
        order = [a for g in mine for a in g]
        print(f'VM {k}/{n}: districts {[district.get(g[0]) for g in mine]}', flush=True)
    release.ensure()      # the work release is made once from home: ROLL_RELEASE=<tag>-work release.py ensure
    lock = threading.Lock()
    pending = []
    with ThreadPoolExecutor(1) as shipper:
        for ac in order:
            shipped = json.loads(run.SHIPPED.read_text('utf8')) if run.SHIPPED.exists() else {}
            if str(ac) in shipped and not args.ac:
                continue
            if in_flight(ac):
                print(f'  AC {ac}: an OCR run is already queued or running; skipped', flush=True)
                continue
            paths, failed = fetch_ac(ac, parts_by_ac[ac], args.threads)
            for f in pending:
                f.result()                       # at most one AC waits for upload

            def done(ac=ac, paths=paths, failed=failed):
                ship(ac, paths)
                with lock:
                    cur = json.loads(run.SHIPPED.read_text('utf8')) if run.SHIPPED.exists() else {}
                    cur[str(ac)] = {'parts': len(parts_by_ac[ac]), 'failed': failed, 'via': 'vm-pdf'}
                    run.SHIPPED.write_text(json.dumps(cur, indent=1), 'utf8')
            pending = [shipper.submit(done)]
        for f in pending:
            f.result()
    print('done: every AC in the order is shipped', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
