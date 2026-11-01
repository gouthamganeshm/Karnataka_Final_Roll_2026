"""Open dataset, the VM side (docs/dataset.md, steps 1-2).

    GH_TOKEN=... python scripts/home/ds_pilot.py --vm K        # systemd ds-pilot@K: every 4th AC
    GH_TOKEN=... python scripts/home/ds_pilot.py --ac 162        # given ACs, then stop (the pilot run)

Per AC, VM K taking every 4th AC from the K-th:

  cut    the English PDF of every booth, fresh from ECI (the owner's choice:
         English roll only); every card page cut into one sheet of the cards'
         text blocks (fields.page_sheet). A zip per booth, spread over SHARDS
         tars: ds-<ac>.s<i>.tar on <tag>-ds.
  read   dataset-read.yml on Actions, one job per shard ->
         dsread-<ac>.s<i>.json.gz on <tag>-ds
  merge  the shards' readings -> dsread-<ac>.json.gz on <tag>-ds; the sheet
         tars and shard readings are deleted.

At most MAX_OPEN ACs of a VM wait on Actions at a time, which bounds both the
release's size and the Actions queue. Progress is the set of files on the
release, so a restart carries on. Nothing here touches the live site or its
releases: the dataset is built apart from them and never feeds the site.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
import tarfile
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import release  # noqa: E402
import run  # noqa: E402

TAG = release.TAG
DS = f'{TAG}-ds'
OUT = ROOT / 'cache' / 'ds'
STATE = OUT / 'pilot.json'
SHARDS = 8
MAX_OPEN = 2
REDISPATCH_H = 6
EXT = 'png'
GREYS = [(v >> 4) * 17 for v in range(256)]


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def on_ds(fn, *args):
    release.TAG = DS
    try:
        return fn(*args)
    finally:
        release.TAG = TAG


def encode(sheet) -> bytes:
    # 16 greys read as well as the full 256 on 227 cards of both rolls (age,
    # gender, relation alike); 1-bit lost 5-15% of them. ~240 KB a page.
    buf = io.BytesIO()
    sheet.point(GREYS).save(buf, format='PNG', compress_level=6)
    return buf.getvalue()


def bundle(ac: int, part: int, lang: str, data: bytes) -> tuple[bytes, int]:
    """(zip of the booth's sheets, card count) for one roll's PDF."""
    import fitz
    import crops as C
    import fields as F
    doc = fitz.open(stream=data, filetype='pdf')
    buf = io.BytesIO()
    index = {'ac': ac, 'part': part, 'lang': lang, 'ext': EXT, 'pages': {}}
    cards = 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as z:
        for p, (img, _page) in enumerate(C.page_images(doc)):
            sheet, spans = F.page_sheet(img)
            if sheet is None:
                continue
            z.writestr(f'p{p:03d}.{EXT}', encode(sheet))
            index['pages'][str(p)] = spans
            cards += len(spans)
        z.writestr('index.json', json.dumps(index))
    return buf.getvalue(), cards


def cut_ac(ac: int, parts: list[int]) -> list[Path]:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = [OUT / f'ds-{ac}.s{i}.tar' for i in range(SHARDS)]
    tars = [tarfile.open(p, 'w') for p in paths]
    booths = {}

    def get(part):
        return part, run.fetch(run.url(ac, part, 'eng'))

    t = time.time()
    with ThreadPoolExecutor(6) as pool:
        window = 12
        futs = [pool.submit(get, p) for p in parts[:window]]
        nxt = window
        for i, _ in enumerate(parts):
            part, eng = futs[i].result()
            futs[i] = None
            if nxt < len(parts):
                futs.append(pool.submit(get, parts[nxt]))
                nxt += 1
            rec = {}
            for lang, data in (('eng', eng),):
                if data is None:
                    rec[lang] = None
                    continue
                z, n = bundle(ac, part, lang, data)
                info = tarfile.TarInfo(f'{part}.{lang}.zip')
                info.size = len(z)
                tars[i % SHARDS].addfile(info, io.BytesIO(z))
                rec[lang] = n
            booths[part] = rec
            if (i + 1) % 50 == 0:
                log(f'AC {ac}: {i + 1}/{len(parts)} booths cut ({time.time() - t:.0f}s)')
    meta = json.dumps({'ac': ac, 'shards': SHARDS, 'booths': booths,
                       'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}).encode()
    for tar in tars:
        info = tarfile.TarInfo('booths.json')
        info.size = len(meta)
        tar.addfile(info, io.BytesIO(meta))
        tar.close()
    miss = [p for p, r in booths.items() if not r['eng']]
    log(f'AC {ac}: {len(booths)} booths cut, {sum(p.stat().st_size for p in paths) / 1e6:.0f} MB '
        f'in {time.time() - t:.0f}s{f"; a PDF not served for {miss}" if miss else ""}')
    return paths


def dispatch(ac: int) -> None:
    release.gh('workflow', 'run', 'dataset-read.yml', '-R', release.repo(), '-f', f'ac={ac}',
               '-f', f'tag={TAG}', '-f', f'shards={SHARDS}')


def merge(ac: int) -> None:
    d = OUT / 'merge'
    d.mkdir(parents=True, exist_ok=True)
    names = [f'dsread-{ac}.s{i}.json.gz' for i in range(SHARDS)]
    on_ds(release.fetch, str(d), names)
    reads = {}
    for n in names:
        with gzip.open(d / n, 'rt', encoding='utf8') as f:
            reads.update(json.load(f)['reads'])
    dest = d / f'dsread-{ac}.json.gz'
    with gzip.open(dest, 'wt', encoding='utf8') as f:
        json.dump({'ac': ac, 'reads': reads}, f)
    on_ds(release.upload, str(dest))
    on_ds(release.delete, *names, *[f'ds-{ac}.s{i}.tar' for i in range(SHARDS)])
    for p in d.iterdir():
        p.unlink()
    log(f'AC {ac}: merged {len(reads)} booth rolls')


def load_state() -> dict:
    return json.loads(STATE.read_text('utf8')) if STATE.exists() else {}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1), 'utf8')


def step(acs: list[int], st: dict) -> tuple[int | None, int]:
    """Advance every AC one stage at most; (next AC to cut, ACs waiting on Actions)."""
    have = on_ds(release.assets)
    todo, waiting = None, 0
    for ac in acs:
        a = st.setdefault(str(ac), {})
        if f'dsread-{ac}.json.gz' in have:
            a['done'] = True
            continue
        if all(f'dsread-{ac}.s{i}.json.gz' in have for i in range(SHARDS)):
            merge(ac)
            continue
        if all(f'ds-{ac}.s{i}.tar' in have for i in range(SHARDS)):
            waiting += 1
            last = a.get('dispatched', 0)
            if time.time() - last > REDISPATCH_H * 3600:
                if last:
                    log(f'AC {ac}: not all shards read {REDISPATCH_H} h after dispatch; dispatching again')
                dispatch(ac)
                a['dispatched'] = time.time()
                save_state(st)
            continue
        if todo is None:
            todo = ac
    return todo, waiting


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vm', type=int)
    ap.add_argument('--ac', help='comma-separated ACs instead of a VM share')
    args = ap.parse_args()
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies'] if c['parts']}
    acs = [int(x) for x in args.ac.split(',')] if args.ac else \
        [a for a in range(1, 225) if (a - 1) % 4 == args.vm - 1]
    log(f'ACs {acs}')
    st = load_state()
    while True:
        try:
            todo, waiting = step(acs, st)
        except Exception as exc:  # noqa: BLE001 - GitHub hiccups: try again shortly
            log(f'step failed: {exc!r}')
            time.sleep(120)
            continue
        if all(st.get(str(a), {}).get('done') for a in acs):
            log('every AC read')
            return 0
        if todo is None or waiting >= MAX_OPEN:
            time.sleep(300)
            continue
        paths = cut_ac(todo, parts_by_ac[todo])
        on_ds(release.upload, *map(str, paths))
        for p in paths:
            p.unlink()
        dispatch(todo)
        st.setdefault(str(todo), {})['dispatched'] = time.time()
        save_state(st)


if __name__ == '__main__':
    sys.exit(main())
