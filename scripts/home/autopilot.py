"""Unattended driver for the rest of the import, on one cloud VM (systemd).

    GH_TOKEN=... python scripts/home/autopilot.py [--target 3] [--once]

Every few minutes it looks at the OCR runs and both draft releases and:

1. re-dispatches an AC whose last OCR run failed while its part PDFs are still
   in a release (at most MAX_RETRY times; then it is listed as given up);
2. dispatches a complete PDF set no run has picked up (a ship cut short
   between upload and dispatch) and deletes a partial one (an upload cut
   short) so the AC is fetched again;
3. re-fetches an AC whose run failed after its PDFs were already gone;
4. fetches the next AC (Bengaluru, then districts by electorate, largest
   first) only while fewer than `target` OCR runs are queued or running: a run
   takes all 20 Actions slots, so a short queue keeps them busy without piling
   gigabytes of PDFs into the work release.

State: cache/shipped-<release>.json (as vm_fetch) and cache/autopilot.json
(retries, given up). Log: stdout (journald under systemd). Safe to kill and
restart at any point: everything it decides from is re-read from GitHub.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'home'))
import release  # noqa: E402
import run  # noqa: E402
import vm_fetch  # noqa: E402

MAIN = release.TAG
WORK = vm_fetch.WORK
STATE = run.CACHE / 'autopilot.json'
MAX_RETRY = 4
COOL = 900              # after a failed run, no new dispatch for this long (a rate-limit window)
STALE_MIN = 20          # a partial PDF set this old is an upload that died
PAUSE = 120             # seconds between looks
# Final phase, once every AC is live: Bengaluru ACs cut before the lone-card fix
# (1a477c8) and read before the contact-sheet fix (965c299), whose crops were
# deleted when per-card verification still ran, so only a fresh download helps.
REDO = [150, 151, 152, 153, 154, 155, 158, 160, 162, 167, 171, 175, 176, 177, 196]
DRY = False            # --dry: say what would be done, change nothing
TITLE = re.compile(r'^OCR AC (\d+) \((\w+)\)$')


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def load(path: Path, default):
    return json.loads(path.read_text('utf8')) if path.exists() else default


def save(path: Path, data) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=1), 'utf8')
    tmp.replace(path)


def assets(tag: str) -> dict[str, dict]:
    release.TAG = tag
    try:
        return release.assets()
    finally:
        release.TAG = MAIN


def delete(tag: str, names: list[str]) -> None:
    if DRY:
        return
    release.TAG = tag
    try:
        release.delete(*names)
    finally:
        release.TAG = MAIN


def runs() -> list[dict]:
    out = release.gh('run', 'list', '-R', release.repo(), '--workflow', 'ocr.yml', '-L', '300', '--json',
                     'databaseId,displayTitle,status,conclusion,createdAt')
    return json.loads(out)


def dispatch(ac: int, kind: str, shards: int | None = None) -> None:
    if DRY:
        return
    args = ['workflow', 'run', 'ocr.yml', '-R', release.repo(), '-f', f'ac={ac}', '-f', f'tag={MAIN}',
            '-f', f'kind={kind}']
    if shards:
        args += ['-f', f'shards={shards}']
    release.gh(*args)


def pdf_sets(found: dict[str, dict]) -> dict[int, dict]:
    sets = collections.defaultdict(lambda: {'shards': set(), 'newest': ''})
    for name, a in found.items():
        m = re.match(r'pdfs-(\d+)\.s(\d+)\.tar$', name)
        if m:
            s = sets[int(m[1])]
            s['shards'].add(int(m[2]))
            s['newest'] = max(s['newest'], a.get('updated_at') or a.get('created_at') or '')
    return sets


def age_min(stamp: str) -> float:
    t = dt.datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    return (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 60


def tick(target: int, state: dict, parts_by_ac: dict[int, list[int]], order: list[int]) -> bool:
    """One look. Returns False once nothing is left to do."""
    all_runs = runs()
    latest: dict[int, dict] = {}
    active = 0
    for r in sorted(all_runs, key=lambda r: r['createdAt']):
        if r['status'] != 'completed':
            active += 1                       # untitled (just dispatched) runs count too
        m = TITLE.match(r['displayTitle'])
        if m and m[2] in ('pdf', 'kan'):
            latest[int(m[1])] = r
    main, work = assets(MAIN), assets(WORK)
    live = {int(m[1]) for n in main if (m := re.match(r'live-rows-(\d+)\.jsonl\.gz$', n))}
    shipped = load(run.SHIPPED, {})
    retries = state.setdefault('retries', {})
    gave_up = state.setdefault('gaveUp', [])
    sent = state.setdefault('dispatched', {})
    seen = set(state.setdefault('seenFailures', []))
    new_fail = [r for r in all_runs if r['conclusion'] == 'failure' and r['databaseId'] not in seen]
    if new_fail and seen:
        state['coolUntil'] = time.time() + COOL
        log(f'{len(new_fail)} new failed run(s); no new dispatch for {COOL // 60} min')
    state['seenFailures'] = sorted(seen | {r['databaseId'] for r in all_runs if r['conclusion'] == 'failure'})[-500:]
    cooling = time.time() < state.get('coolUntil', 0)

    def recent(ac: int) -> bool:
        return time.time() - sent.get(str(ac), 0) < 600

    def mark(ac: int) -> None:
        sent[str(ac)] = time.time()

    def retry(ac: int, why: str, conclusion: str) -> bool:
        if conclusion == 'cancelled':
            return True               # superseded or cancelled by hand: not a failure of the AC
        n = retries.get(str(ac), 0)
        if n >= MAX_RETRY:
            if ac not in gave_up:
                gave_up.append(ac)
                log(f'AC {ac}: gave up after {n} retries ({why})')
            return False
        retries[str(ac)] = n + 1
        log(f'AC {ac}: retry {n + 1}/{MAX_RETRY}: {why}')
        return True

    # PDF sets in either release: ready to dispatch, already read, or dropped.
    ready = {}
    for tag, found in ((WORK, work), (MAIN, main)):
        for ac, s in pdf_sets(found).items():
            n = max(s['shards']) + 1
            last = latest.get(ac)
            names = [f'pdfs-{ac}.s{i}.tar' for i in range(n)]
            if last and last['status'] != 'completed':
                continue
            if len(s['shards']) != n or n not in (16, 20):
                if age_min(s['newest']) > STALE_MIN:
                    log(f'AC {ac}: partial PDF set ({len(s["shards"])} of {n}) in {tag}; dropped, will re-fetch')
                    delete(tag, names)
                    shipped.pop(str(ac), None)
                continue
            if recent(ac):
                continue                      # dispatched a moment ago; its run may not be titled yet
            if last and last['createdAt'] > s['newest']:      # a run has read this upload
                if last['conclusion'] == 'success':
                    if ac in live:
                        delete(tag, names)    # merge normally drops them; a leftover
                    continue                  # (not live: held by the checks)
                if ac in gave_up:
                    continue
                ready[ac] = (n, tag, last['conclusion'])     # a retry, counted when dispatched
                continue
            ready[ac] = (n, tag, None)

    # Failed runs whose inputs are gone: fetch again (pdf) or re-read the home crops (kan).
    sets_now = set(pdf_sets(work)) | set(pdf_sets(main))
    for ac, last in latest.items():
        if last['status'] != 'completed' or last['conclusion'] == 'success' or ac in live or ac in sets_now:
            continue
        if ac in gave_up or recent(ac):
            continue
        kind = TITLE.match(last['displayTitle'])[2]
        if kind == 'kan' and f'crops-{ac}.tar' in main and not cooling:
            if retry(ac, f'kan run {last["conclusion"]}', last['conclusion']):
                dispatch(ac, 'kan')
                mark(ac)
                active += 1
        elif str(ac) in shipped and not cooling and retry(ac, f'run {last["conclusion"]}, PDFs gone: re-fetch', last['conclusion']):
            shipped.pop(str(ac), None)
    if DRY:
        log(f'(dry) {active} active runs; retries {retries}; shipped {len(shipped)}')
    else:
        save(run.SHIPPED, shipped)
        save(STATE, state)

    # Feed Actions while the queue is short (a deep one starves every merge job
    # of a runner): PDFs already uploaded first, in queue order, then a new fetch.
    if cooling:
        if not DRY:
            save(STATE, state)
        return True
    rank = {a: i for i, a in enumerate(order)}
    for ac in sorted(ready, key=lambda a: rank.get(a, 0)):
        if active >= target:
            return True
        n, tag, failed = ready[ac]
        if failed and not retry(ac, f'run {failed}', failed):
            continue
        log(f'AC {ac}: dispatching OCR for its {n} PDF shards in {tag} ({active} runs active)')
        dispatch(ac, 'pdf', n)
        mark(ac)
        active += 1
    if not DRY:
        save(STATE, state)
    todo = [a for a in order if str(a) not in shipped and a not in live and a not in gave_up and a not in sets_now]
    if not todo:
        held = {a for a, r in latest.items() if r['status'] == 'completed' and r['conclusion'] == 'success'}
        waiting = [a for a in order if a not in live and a not in gave_up and a not in held]
        redone = state.setdefault('redone', [])
        redo = [a for a in REDO if a not in redone]
        if waiting or not redo:
            return active > 0 or bool(waiting)
        if active >= target or ready or len(work) > 800:
            return True
        ac = redo[0]
        log(f'AC {ac}: final phase, downloading again (crops from before the lone-card and sheet fixes)')
        if DRY:
            return True
        paths, failed = vm_fetch.fetch_ac(ac, parts_by_ac[ac], 16)
        vm_fetch.ship(ac, paths)
        mark(ac)
        redone.append(ac)
        save(STATE, state)
        return True
    if active >= target or ready or len(work) > 800:
        return True
    ac = todo[0]
    log(f'AC {ac}: fetching ({active} OCR runs active, {len(todo)} ACs to go)')
    if DRY:
        return True
    paths, failed = vm_fetch.fetch_ac(ac, parts_by_ac[ac], 16)
    vm_fetch.ship(ac, paths)
    mark(ac)
    save(STATE, state)
    shipped = load(run.SHIPPED, {})
    shipped[str(ac)] = {'parts': len(parts_by_ac[ac]), 'failed': failed, 'via': 'autopilot'}
    save(run.SHIPPED, shipped)
    return 'again'                            # look again at once: the queue may still have room


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--target', type=int, default=3, help='OCR runs queued or running before fetching another AC')
    ap.add_argument('--once', action='store_true')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    global DRY
    DRY = args.dry
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies'] if c['parts']}
    order = run.run_order(parts_by_ac, 'all')
    state = load(STATE, {})
    log(f'autopilot: {len(order)} ACs, target {args.target} active runs')
    while True:
        try:
            busy = tick(args.target, state, parts_by_ac, order)
        except Exception:  # noqa: BLE001 - a GitHub hiccup must not stop the import
            log('tick failed:\n' + traceback.format_exc())
            busy = True
        if args.once:
            return 0
        if not busy:
            log('every AC is live, given up, or held by the checks; idle')
        if busy != 'again':
            time.sleep(PAUSE)


if __name__ == '__main__':
    sys.exit(main())
