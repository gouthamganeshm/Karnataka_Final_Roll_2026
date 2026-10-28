"""Unattended full English cross-check, one VM's share of the ACs (systemd).

    GH_TOKEN=... python scripts/home/eng_pilot.py --vm K [--target 4] [--once]

Order (the user's): Hassan, then every Bengaluru AC (the three BBMP districts,
Bangalore Urban and Bangalore Rural), then the rest in the import's queue order.
VM K of 4 takes every 4th AC of that order from the K-th, so all four work
down the same list together.

Each look, for this VM's ACs, in that order:

1. fetch   the AC's English roll (vm_fetch, lang=eng) and dispatch ocr.yml
           kind=epdf, only while fewer than `target` OCR runs are active and
           fewer than MAX_SETS English PDF sets wait in the work release;
           a failed run is re-dispatched while its PDFs remain, re-fetched
           after (MAX_RETRY each, then given up and listed);
2. check   once engfull-<ac>.tar is on <tag>-eng: xcheck.py against the live
           rows, and for every card needing a person a review sheet (both
           rolls' crops side by side); ledger and sheets go up as
           xcheck-<ac>.zip;
3. apply   once reference/manual/<ac>.json (git) decides every card the
           ledger left to a person (or none was left): reverify_live.py
           --epics sets the two-roll and manual EPICs, under its rule that no
           other published card may change; the ledger is re-uploaded with
           the outcome. A ledger made from older live rows is redone first;
           decisions are keyed by card, so they carry over. Nothing is
           applied while reference/manual/APPLY is absent (the gate).

Everything is re-read from GitHub and git each look: safe to kill and restart.
Local state (retries, given up): cache/eng-pilot.json. Log: stdout (journald).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import time
import traceback
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'home'))
sys.path.insert(0, str(ROOT / 'scripts' / 'ocr'))
import release  # noqa: E402
import run  # noqa: E402
import vm_fetch  # noqa: E402

MAIN = release.TAG
WORK = vm_fetch.WORK
ENG = f'{MAIN}-eng'
CROPS = f'{MAIN}-crops'
STATE = run.CACHE / 'eng-pilot.json'
TMP = run.CACHE / 'eng-pilot'
MANUAL = ROOT / 'reference' / 'manual'
MAX_RETRY = 3
MAX_SETS = 6           # English PDF sets waiting in the work release, all VMs together
PAUSE = 180
PER_SHEET = 12
TITLE = re.compile(r'^OCR AC (\d+) \((\w+)\)$')
FIRST = [{'HASSAN'}, run.BENGALURU | {'BANGALORE RURAL'}]
VMS = 4


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def load(path: Path, default):
    return json.loads(path.read_text('utf8')) if path.exists() else default


def save(path: Path, data) -> None:
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, indent=1), 'utf8')
    tmp.replace(path)


def on(tag: str, fn, *args):
    release.TAG = tag
    try:
        return fn(*args)
    finally:
        release.TAG = MAIN


def runs() -> list[dict]:
    return json.loads(release.gh('run', 'list', '-R', release.repo(), '--workflow', 'ocr.yml', '-L', '300',
                                 '--json', 'databaseId,displayTitle,status,conclusion,createdAt'))


def dispatch(ac: int) -> None:
    release.gh('workflow', 'run', 'ocr.yml', '-R', release.repo(), '-f', f'ac={ac}', '-f', f'tag={MAIN}',
               '-f', 'kind=epdf', '-f', f'shards={vm_fetch.SHARDS}')


def decisions(ac: int) -> dict:
    """card key 'part/page/cell' -> {'epic': str or None, 'deleted': bool (optional), 'note'}."""
    return load(MANUAL / f'{ac}.json', {}).get('decisions', {})


def key(item) -> str:
    return '/'.join(map(str, item['key']))


# ------------------------------------------------------------------- check
def bundles(tar_path: Path, parts: set[int]) -> dict:
    import tarfile
    import crops as C
    out = {}
    with tarfile.open(tar_path) as t:
        for m in t.getmembers():
            if m.name.endswith('.zip') and int(m.name.split('.')[0]) in parts:
                out[int(m.name.split('.')[0])] = C.read_bundle(t.extractfile(m).read())[1]
    return out


def sheets(led: dict, kan_tar: Path | None, eng_tar: Path) -> list[tuple[str, bytes]]:
    """Review sheets: per card, the Kannada and English EPIC and serial crops, enlarged, and the readings."""
    from PIL import Image, ImageDraw
    parts = {m['key'][0] for m in led['manual']}
    kb = bundles(kan_tar, parts) if kan_tar else {}
    eb = bundles(eng_tar, parts)

    def crop(b, k, i):
        try:
            im = b[k[0]][k[1]][i][k[2]]
        except (KeyError, IndexError):
            return None
        return None if im is None else im.resize((im.width * 2, im.height * 2))

    def text(c):
        if not c:
            return 'none'
        return (f"{c['epic']} {'agreed' if c['epicOk'] else 'unsure'}/{c['how']} rd={c['rd']} "
                f"serial {c['serial']}{'' if c['ok'] else '?'}{' DELETED' if c['deleted'] else ''}")

    out = []
    items = led['manual']
    for s in range(0, len(items), PER_SHEET):
        rows = []
        for m in items[s:s + PER_SHEET]:
            k = m['key']
            ims = [crop(kb, k, 0), crop(kb, k, 1), crop(eb, k, 0), crop(eb, k, 1)]
            h = max([i.height for i in ims if i] + [40])
            row = Image.new('L', (1900, h + 58), 255)
            x = 5
            for j, im in enumerate(ims):
                if j == 2:
                    x = 960
                if im:
                    row.paste(im, (x, 2))
                    x += im.width + 10
            d = ImageDraw.Draw(row)
            pub = m['published']
            d.text((5, h + 6), f"#{m['id']} {key(m)} {m['cat']} published={pub[0] + (' DEL' if pub[1] else '') if pub else 'no'}"
                   f"{' disputed=' + m['disputed'] if m['disputed'] else ''}", fill=0)
            d.text((5, h + 22), 'KAN ' + text(m['kan']), fill=0)
            d.text((5, h + 38), 'ENG ' + text(m['eng']), fill=0)
            d.line([(0, h + 56), (1900, h + 56)], fill=0)
            rows.append(row)
        sheet = Image.new('L', (1900, sum(r.height for r in rows)), 255)
        y = 0
        for r in rows:
            sheet.paste(r, (0, y))
            y += r.height
        buf = io.BytesIO()
        sheet.save(buf, 'PNG', optimize=True)
        out.append((f'sheet-{s // PER_SHEET + 1:03d}.png', buf.getvalue()))
    return out


def check(ac: int, main: dict, crops_rel: dict) -> None:
    d = TMP / str(ac)
    d.mkdir(parents=True, exist_ok=True)
    names = [f'live-rows-{ac}.jsonl.gz', f'live-verify-{ac}.json', f'live-rows-{ac}.summary.json']
    release.fetch(str(d), names)
    on(ENG, release.fetch, str(d), [f'engfull-{ac}.tar'])
    subprocess.run([sys.executable, str(ROOT / 'scripts' / 'home' / 'xcheck.py'), str(ac),
                    *(str(d / n) for n in names), str(d / f'engfull-{ac}.tar'), str(d)], check=True)
    led = json.loads((d / f'xcheck-{ac}.json').read_text('utf8'))
    pages = []
    if led['manual']:
        on(ENG, release.fetch, str(d), [f'crops-eng-{ac}.tar'])
        kan = None
        for tag, found in ((CROPS, crops_rel), (MAIN, main)):
            if f'crops-{ac}.tar' in found:
                on(tag, release.fetch, str(d), [f'crops-{ac}.tar'])
                kan = d / f'crops-{ac}.tar'
                break
        pages = sheets(led, kan, d / f'crops-eng-{ac}.tar')
        led['kanCrops'] = bool(kan)
    upload_ledger(ac, led, pages)
    c = led['counts']
    log(f'AC {ac}: checked {led["cards"]:,} cards: {c.get("confirmed", 0):,} confirmed, {c.get("kan-only", 0):,} '
        f'Kannada-only, {len(led["auto"])} decided from both rolls, {len(led["manual"])} for review '
        f'({len(pages)} sheets), {len(led["parts"])} parts flagged')
    for f in d.iterdir():
        f.unlink()


def upload_ledger(ac: int, led: dict, pages: list[tuple[str, bytes]]) -> None:
    path = TMP / f'xcheck-{ac}.zip'
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('ledger.json', json.dumps(led))
        for name, data in pages:
            z.writestr(name, data)
    on(ENG, release.replace, str(path))
    path.unlink()


def ledger(ac: int, asset: dict) -> tuple[dict, list[tuple[str, bytes]]]:
    """The AC's ledger zip, downloaded again only when the release copy changed."""
    d = TMP / 'ledgers'
    d.mkdir(parents=True, exist_ok=True)
    p, stamp = d / f'xcheck-{ac}.zip', d / f'xcheck-{ac}.stamp'
    when = asset.get('updated_at') or asset.get('created_at') or ''
    if not p.exists() or not stamp.exists() or stamp.read_text() != when:
        on(ENG, release.fetch, str(d), [f'xcheck-{ac}.zip'])
        stamp.write_text(when)
    with zipfile.ZipFile(p) as z:
        led = json.loads(z.read('ledger.json'))
        pages = [(n, z.read(n)) for n in z.namelist() if n.startswith('sheet-')]
    return led, pages


# ------------------------------------------------------------------- apply
def apply(ac: int, led: dict, pages: list) -> bool:
    """Returns True once the AC is applied (or nothing was left to apply)."""
    if not (MANUAL / 'APPLY').exists():
        return False                    # the gate: applies start once the comparison is calibrated
    dec = decisions(ac)
    todo = [m for m in led['manual'] if key(m) not in dec]
    if todo:
        return False
    d = TMP / str(ac)
    d.mkdir(parents=True, exist_ok=True)
    rows = release.fetch(str(d), [f'live-rows-{ac}.jsonl.gz'])[0]
    if hashlib.sha256(rows.read_bytes()).hexdigest()[:16] != led['liveRows']:
        log(f'AC {ac}: live rows changed since the check; checking again (decisions carry over)')
        on(ENG, release.delete, f'xcheck-{ac}.zip')
        return False
    edits = [list(a[:5]) for a in led['auto']]
    pub = {key(m): m['published'] for m in led['manual']}
    for k, v in dec.items():
        p = pub.get(k)
        if p and v.get('epic') == p[0] and v.get('deleted', p[1]) == p[1]:
            continue                                  # the published card stands
        if k in pub:
            edits.append([*map(int, k.split('/')), v.get('epic'), v.get('deleted')])
    out = {'applied': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'edits': len(edits)}
    if edits:
        f = d / 'epics.json'
        f.write_text(json.dumps({str(ac): edits}))
        res = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'home' / 'reverify_live.py'), '--epics', str(f),
                              '--apply', '--no-publish'], cwd=ROOT, capture_output=True, text=True)
        tail = (res.stdout + res.stderr).strip().splitlines()[-3:]
        log(f'AC {ac}: ' + ' | '.join(tail))
        out['result'] = tail
        if res.returncode or not any('replaced' in t for t in tail):
            out['applied'] = None
            out['failed'] = tail
    led['apply'] = out
    upload_ledger(ac, led, pages)
    if out['applied'] and edits:
        release.gh('workflow', 'run', 'publish.yml', '-R', release.repo(), '-f', f'tag={MAIN}')
    return bool(out['applied'])


# -------------------------------------------------------------------- tick
def tick(mine: list[int], target: int, state: dict, parts_by_ac: dict) -> None:
    all_runs = runs()
    active = sum(r['status'] != 'completed' for r in all_runs)
    latest = {}
    for r in sorted(all_runs, key=lambda r: r['createdAt']):
        m = TITLE.match(r['displayTitle'])
        if m and m[2] == 'epdf':
            latest[int(m[1])] = r
    main, work, eng = release.assets(), on(WORK, release.assets), on(ENG, release.assets)
    crops_rel = on(CROPS, release.assets)
    sets = {}
    for n in work:
        m = re.match(r'epdfs-(\d+)\.s(\d+)\.tar$', n)
        if m:
            sets.setdefault(int(m[1]), set()).add(int(m[2]))
    retries, gave_up = state.setdefault('retries', {}), state.setdefault('gaveUp', [])
    subprocess.run(['git', 'pull', '-q'], cwd=ROOT, check=False)      # manual decisions
    fetched = False
    for ac in mine:
        if ac in gave_up:
            continue
        if f'xcheck-{ac}.zip' in eng:
            asset = eng[f'xcheck-{ac}.zip']
            when = asset.get('updated_at') or asset.get('created_at')
            if state.setdefault('done', {}).get(str(ac)) == when:
                continue
            led, pages = ledger(ac, asset)
            outcome = led.get('apply') or {}
            if outcome.get('applied') or outcome.get('failed'):
                state['done'][str(ac)] = when         # applied, or failed and listed for a person
            elif apply(ac, led, pages):
                log(f'AC {ac}: applied')
            continue
        if f'engfull-{ac}.tar' in eng:
            check(ac, main, crops_rel)
            continue
        last = latest.get(ac)
        if last and last['status'] != 'completed':
            continue
        if ac in sets:
            if len(sets[ac]) == vm_fetch.SHARDS and (not last or last['conclusion'] != 'success'):
                n = retries.get(str(ac), 0)
                if last and n >= MAX_RETRY:
                    gave_up.append(ac)
                    log(f'AC {ac}: OCR failed {n} times; given up (PDFs left in the work release)')
                    continue
                if last:
                    retries[str(ac)] = n + 1
                log(f'AC {ac}: dispatching English OCR' + (f' (retry {n + 1})' if last else ''))
                dispatch(ac)
                active += 1
            continue
        if fetched or active >= target or len(sets) >= MAX_SETS:
            continue
        log(f'AC {ac}: fetching the English roll ({active} OCR runs active)')
        paths, failed = vm_fetch.fetch_ac(ac, parts_by_ac[ac], 16, 'eng')
        if failed:
            log(f'AC {ac}: {len(failed)} English parts not served: {failed[:20]}')
        vm_fetch.ship(ac, paths, 'epdf')
        fetched, active = True, active + 1
        sets[ac] = set(range(vm_fetch.SHARDS))
    save(STATE, state)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vm', type=int, required=True)
    ap.add_argument('--target', type=int, default=4)
    ap.add_argument('--once', action='store_true')
    args = ap.parse_args()
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies'] if c['parts']}
    district = {c['acNumber']: c['district'] for c in run.SEED['constituencies']}
    order = run.run_order(parts_by_ac, 'all')
    order = sorted(order, key=lambda a: next((i for i, ds in enumerate(FIRST) if district.get(a) in ds), len(FIRST)))
    mine = order[args.vm - 1::VMS]
    TMP.mkdir(parents=True, exist_ok=True)
    state = load(STATE, {})
    log(f'eng pilot VM {args.vm}: {len(mine)} ACs, target {args.target} active OCR runs')
    while True:
        try:
            tick(mine, args.target, state, parts_by_ac)
        except Exception:  # noqa: BLE001 - a GitHub hiccup must not stop the run
            log('tick failed:\n' + traceback.format_exc())
        if args.once:
            return 0
        time.sleep(PAUSE)


if __name__ == '__main__':
    sys.exit(main())
