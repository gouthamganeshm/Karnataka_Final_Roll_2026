"""25% sample verification, the VM side (docs/sample-verification.md, steps 3-5).

    GH_TOKEN=... python scripts/home/sv_pilot.py --vm K        # systemd sv-pilot@K: every 4th AC
    GH_TOKEN=... python scripts/home/sv_pilot.py --ac 1          # given ACs, then stop (the pilot run)

Per AC, in AC order, VM K taking every 4th AC from the K-th:

  sample   both PDFs of every booth, fresh from ECI; the Kannada pages cut into
           cards; card pages shuffled with a fixed seed and taken until >= 25%
           of the booth's cards; the same pages of the English PDF cut. Only
           the EPIC and serial boxes of the sampled pages are kept:
           sv-<ac>.tar (a zip per booth and roll + booths.json) on <tag>-sv.
  read     sample-verify.yml on Actions reads them -> svread-<ac>.json.gz on <tag>-svr
  compare  sv_compare.py against the site snapshot -> svres-<ac>.json.gz on <tag>-svr

Progress is the set of files on the two releases, so a restart carries on.
Downloads run ahead on threads; cutting is one booth at a time (1 core, 6 GB).
"""
from __future__ import annotations

import argparse
import io
import json
import math
import random
import sys
import tarfile
import threading
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home'), str(ROOT / 'scripts' / 'ocr')]
import release  # noqa: E402
import run  # noqa: E402

SHARE = 0.25
TAG = release.TAG
SV, SVR = f'{TAG}-sv', f'{TAG}-svr'
OUT = ROOT / 'cache' / 'sv'
STATE = OUT / 'pilot.json'
REDISPATCH_H = 3
_lock = threading.Lock()


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def listing(tag: str) -> dict:
    release.TAG = tag
    try:
        return release.assets()
    finally:
        release.TAG = TAG


def cut_pages(data: bytes, only: set | None = None) -> dict:
    """page -> (epic crops, serial crops) for card pages (all, or `only`)."""
    import fitz
    import crops as C
    doc = fitz.open(stream=data, filetype='pdf')
    out = {}
    for p, (img, _page) in enumerate(C.page_images(doc)):
        if only is not None and p not in only:
            continue
        e, s = C.cut_page(img)
        if any(x is not None for x in e):
            out[p] = (e, s)
    return out


def bundle(ac: int, part: int, lang: str, pages: dict) -> bytes:
    import crops as C
    buf = io.BytesIO()
    index = {'ac': ac, 'part': part, 'lang': lang, 'ext': 'png', 'pages': {}}
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_STORED) as z:
        for p, (epics, serials) in sorted(pages.items()):
            present = [c for c, (e, s) in enumerate(zip(epics, serials)) if e is not None or s is not None]
            for c in present:
                for tag, crop in (('e', epics[c]), ('s', serials[c])):
                    if crop is not None:
                        z.writestr(f'p{p:03d}/c{c:02d}{tag}.png', C._encode(crop))
            index['pages'][str(p)] = [len(epics), present]
        z.writestr('index.json', json.dumps(index))
    return buf.getvalue()


def pick(ac: int, part: int, cards: dict[int, int]) -> list[int]:
    """Card pages shuffled with a fixed seed, taken until >= 25% of the cards."""
    order = sorted(cards)
    random.Random(f'sv25-{ac}-{part}').shuffle(order)
    need, got, out = math.ceil(SHARE * sum(cards.values())), 0, []
    for p in order:
        if got >= need:
            break
        out.append(p)
        got += cards[p]
    return sorted(out)


def sample_ac(ac: int, parts: list[int]) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    tar_path = OUT / f'sv-{ac}.tar'
    booths = {}

    def get(part):
        return part, run.fetch(run.url(ac, part, 'kan')), run.fetch(run.url(ac, part, 'eng'))

    t = time.time()
    with tarfile.open(tar_path, 'w') as tar, ThreadPoolExecutor(6) as pool:
        # Downloads run at most 12 booths ahead (~300 MB of PDFs in memory).
        window = 12
        futs = [pool.submit(get, p) for p in parts[:window]]
        nxt = window
        for i in range(len(parts)):
            part, kan, eng = futs[i].result()
            futs[i] = None
            if nxt < len(parts):
                futs.append(pool.submit(get, parts[nxt]))
                nxt += 1
            rec = {'kan': kan is not None, 'eng': eng is not None}
            if kan is None:
                booths[part] = rec
                continue
            kp = cut_pages(kan)
            cards = {p: sum(x is not None for x in e) for p, (e, _s) in kp.items()}
            chosen = pick(ac, part, cards)
            rec.update(cardPages=len(cards), cards=sum(cards.values()), pages=chosen,
                       sampled=sum(cards[p] for p in chosen))
            files = [(f'{part}.kan.zip', bundle(ac, part, 'kan', {p: kp[p] for p in chosen}))]
            if eng is not None:
                ep = cut_pages(eng, set(chosen))
                rec['engCards'] = {str(p): sum(x is not None for x in ep[p][0]) for p in ep}
                files.append((f'{part}.eng.zip', bundle(ac, part, 'eng', ep)))
            for name, data in files:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
            booths[part] = rec
            if (i + 1) % 50 == 0:
                log(f'AC {ac}: {i + 1}/{len(parts)} booths sampled ({time.time() - t:.0f}s)')
        data = json.dumps({'ac': ac, 'share': SHARE, 'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                           'booths': booths}).encode()
        info = tarfile.TarInfo('booths.json')
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    miss = [p for p, r in booths.items() if not r['kan']]
    log(f'AC {ac}: sampled {sum(r.get("sampled", 0) for r in booths.values())} of '
        f'{sum(r.get("cards", 0) for r in booths.values())} cards in {len(booths) - len(miss)} booths'
        f'{f", Kannada PDF not served: {miss}" if miss else ""} '
        f'({tar_path.stat().st_size / 1e6:.0f} MB, {time.time() - t:.0f}s)')
    return tar_path


def dispatch(ac: int) -> None:
    release.gh('workflow', 'run', 'sample-verify.yml', '-R', release.repo(), '-f', f'ac={ac}', '-f', f'tag={TAG}')


def load_state() -> dict:
    return json.loads(STATE.read_text('utf8')) if STATE.exists() else {}


def save_state(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=1), 'utf8')


def step(acs: list[int], parts_by_ac: dict, st: dict, site) -> int | None:
    """Advance every AC one stage at most; returns the next AC to sample, if any."""
    import sv_compare
    sv, svr = listing(SV), listing(SVR)
    todo = None
    for ac in acs:
        a = st.setdefault(str(ac), {})
        if f'svres-{ac}.json.gz' in svr:
            a['done'] = True
            continue
        if f'svread-{ac}.json.gz' in svr:
            if site is None:
                return None
            log(f'AC {ac}: comparing with the site snapshot')
            sv_compare.run(ac, site, upload=True)
            continue
        if f'sv-{ac}.tar' in sv and sv[f'sv-{ac}.tar'].get('state') == 'uploaded':
            last = a.get('dispatched', 0)
            if time.time() - last > REDISPATCH_H * 3600:
                if last:
                    log(f'AC {ac}: no readings {REDISPATCH_H} h after dispatch; dispatching again')
                dispatch(ac)
                a['dispatched'] = time.time()
                save_state(st)
            continue
        if todo is None:
            todo = ac
    return todo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--vm', type=int)
    ap.add_argument('--ac', help='comma-separated ACs instead of a VM share')
    args = ap.parse_args()
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts_by_ac = {c['acNumber']: list(range(1, c['parts'] + 1)) for c in manifest['constituencies'] if c['parts']}
    if args.ac:
        acs = [int(x) for x in args.ac.split(',')]
    else:
        acs = [a for a in range(1, 225) if (a - 1) % 4 == args.vm - 1]
    import sv_site
    if not sv_site.SNAP.exists():
        release.TAG = SVR
        release.fetch(str(sv_site.DIR), [sv_site.SNAP.name])
        release.TAG = TAG
    site = sv_site.Site()
    log(f'snapshot of build {site.manifest["builtAt"]}; ACs {acs}')
    st = load_state()
    while True:
        try:
            todo = step(acs, parts_by_ac, st, site)
        except Exception as exc:  # noqa: BLE001 - GitHub hiccups: try again shortly
            log(f'step failed: {exc!r}')
            time.sleep(120)
            continue
        if all(st.get(str(a), {}).get('done') for a in acs):
            log('every AC compared')
            return 0
        if todo is None:
            time.sleep(300)
            continue
        tar_path = sample_ac(todo, parts_by_ac[todo])
        release.TAG = SV
        try:
            release.upload(str(tar_path))
        finally:
            release.TAG = TAG
        tar_path.unlink()
        dispatch(todo)
        st.setdefault(str(todo), {})['dispatched'] = time.time()
        save_state(st)


if __name__ == '__main__':
    sys.exit(main())
