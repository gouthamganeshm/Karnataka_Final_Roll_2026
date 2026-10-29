"""Manual review of the English cross-check, one AC at a time (the person's side).

    python scripts/home/xreview.py status              # every AC: fetched / read / checked / reviewed / applied
    python scripts/home/xreview.py next                # the next AC with cards left to review: fetch its sheets
    python scripts/home/xreview.py show AC             # its undecided cards, batch by batch, with their sheets
    python scripts/home/xreview.py decide AC ID=EPIC ID=keep ID=withhold ID=EPIC/del ID=EPIC/live ...
    python scripts/home/xreview.py sync                # upload decisions an outage kept local
    python scripts/home/xreview.py set AC PART/PAGE/CELL=EPIC ...   # by card, no ledger needed (same value forms)

Decisions hold EPICs, so they never go in git (the repo is public): each
`decide` writes cache/xreview/<ac>/decisions.json and uploads it at once as
decisions-<ac>.json to the private <tag>-eng draft, where the VMs read it.
They are keyed by card (part/page/cell), so a ledger redone from newer live
rows keeps them, and an interrupted review resumes at the first undecided card
(on any machine: the release copy is the record). The VM's eng_pilot applies
an AC as soon as every card it left for review is decided.

  ID=EPIC        the card carries this EPIC (read off the crops)
  ID=keep        the published card is right as it is
  ID=withhold    not settled from the crops: keep it off the site
  ID=EPIC/del    ... and it is marked deleted; ID=EPIC/live: it is not
  ID=...@474     ... and its serial is 474 (a serial card, or one the Kannada
                 rows lack, takes the ledger's serial from the card's place
                 in its part unless one is given)

The sheets and decisions hold EPICs: cache/ (git-ignored) and the private
draft release only, never git.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402
import epic_format  # noqa: E402

ENG = f'{release.TAG}-eng'
CACHE = ROOT / 'cache' / 'xreview'
EPIC = re.compile(r'^[A-Z]{3}[0-9]{7}$')
BATCH = 12


def eng_assets() -> dict:
    release.TAG, main = ENG, release.TAG
    try:
        return release.assets()
    finally:
        release.TAG = main


def ledger(ac: int, asset: dict | None = None) -> dict:
    """The AC's ledger and sheets, fetched again when the release copy changed (`asset` given)."""
    d = CACHE / str(ac)
    when = asset and (asset.get('updated_at') or asset.get('created_at'))
    stamp = d / 'stamp'
    if not (d / 'ledger.json').exists() or (when and (not stamp.exists() or stamp.read_text() != when)):
        for f in d.glob('sheet-*.png'):
            f.unlink()
        d.mkdir(parents=True, exist_ok=True)
        release.TAG, main = ENG, release.TAG
        try:
            p = release.fetch(str(d), [f'xcheck-{ac}.zip'])[0]
        finally:
            release.TAG = main
        with zipfile.ZipFile(p) as z:
            z.extractall(d)
        p.unlink()
        if when:
            stamp.write_text(when)
    return json.loads((d / 'ledger.json').read_text('utf8'))


def on_eng(fn, *args):
    release.TAG, main = ENG, release.TAG
    try:
        return fn(*args)
    finally:
        release.TAG = main


def decided(ac: int, found: dict | None = None) -> dict:
    """This AC's decisions: the local copy, else the release's (another machine's review).

    `found` is a listing of the release already in hand: status and next would
    otherwise list it again for every AC."""
    p = CACHE / str(ac) / 'decisions.json'
    if not p.exists() and f'decisions-{ac}.json' in (found if found is not None else on_eng(release.assets)):
        p.parent.mkdir(parents=True, exist_ok=True)
        on_eng(release.fetch, str(p.parent), [f'decisions-{ac}.json'])[0].replace(p)
    return json.loads(p.read_text('utf8')) if p.exists() else {'ac': ac, 'decisions': {}}


def upload(ac: int) -> bool:
    d = CACHE / str(ac)
    up = d / f'decisions-{ac}.json'
    up.write_bytes((d / 'decisions.json').read_bytes())
    for _ in range(4):
        try:
            on_eng(release.replace, str(up))
            (d / 'unsent').unlink(missing_ok=True)
            return True
        except Exception as err:  # noqa: BLE001 - the home line drops
            print('upload failed, retrying:', str(err)[:120])
    (d / 'unsent').write_text('1')
    return False


def sync() -> int:
    for f in CACHE.glob('*/unsent'):
        ac = int(f.parent.name)
        print(f'AC {ac}:', 'uploaded' if upload(ac) else 'STILL NOT UPLOADED')
    return 0


def card(m) -> str:
    return '/'.join(map(str, m['key']))


def status() -> int:
    found = eng_assets()
    rows = []
    for n in sorted(found):
        m = re.match(r'xcheck-(\d+)\.zip$', n)
        if not m:
            continue
        ac = int(m[1])
        led = ledger(ac, found[n])
        dec = decided(ac, found)['decisions']
        left = sum(card(x) not in dec for x in led['manual'])
        a = led.get('apply') or {}
        state = 'applied' if a.get('applied') else 'APPLY FAILED' if a.get('failed') else \
            'review' if left else 'ready to apply'
        rows.append((ac, state, len(led['manual']), left, len(led['auto']), led['counts'].get('confirmed', 0)))
    eng_read = {int(m[1]) for n in found if (m := re.match(r'engfull-(\d+)\.tar$', n))}
    print(f'{len(eng_read)} ACs read in English, {len(rows)} checked')
    for ac, state, n, left, auto, conf in rows:
        print(f'AC {ac:3}: {state:15} review {n - left}/{n} decided, {auto} from both rolls, {conf:,} confirmed')
    return 0


def todo(ac: int, found: dict | None = None) -> list[dict]:
    dec = decided(ac, found)['decisions']
    return [m for m in ledger(ac)['manual'] if card(m) not in dec]


def show(ac: int) -> int:
    led = ledger(ac, eng_assets()[f'xcheck-{ac}.zip'])
    left = todo(ac)
    print(f'AC {ac}: {len(left)} of {len(led["manual"])} cards left; sheets in {CACHE / str(ac)}')
    sheets = sorted({m['id'] // BATCH + 1 for m in left[:BATCH * 3]})
    for m in left[:BATCH * 3]:
        k, e = m['kan'] or {}, m['eng'] or {}
        print(f"#{m['id']} sheet {m['id'] // BATCH + 1:03d} {card(m)} {m['cat']}{' ' + m['note'] if m.get('note') else ''}: published {m['published']} "
              f"| KAN {k.get('epic')} {k.get('how')} rd={k.get('rd')} | ENG {e.get('epic')} {e.get('how')} "
              f"del {k.get('deleted')}/{e.get('deleted')}")
    print('sheets:', ' '.join(str(CACHE / str(ac) / f'sheet-{s:03d}.png') for s in sheets))
    return 0


def nxt() -> int:
    found = eng_assets()
    for n in sorted(found, key=lambda n: int(re.sub(r'\D', '', n) or 0)):
        m = re.match(r'xcheck-(\d+)\.zip$', n)
        if m:
            ledger(int(m[1]), found[n])
            if todo(int(m[1]), found):
                return show(int(m[1]))
    print('nothing left to review')
    return 0


def parse(v: str) -> dict:
    """EPIC (any format), withhold; then /del or /live; then @serial."""
    v, _, serial = v.partition('@')
    val, mark = (v.rsplit('/', 1) if v.endswith(('/del', '/live')) else (v, ''))
    if val == 'withhold':
        d = {'epic': None}
    elif epic_format.valid(val):
        d = {'epic': val}
    else:
        raise SystemExit(f'{v!r} is not an EPIC or withhold')
    if mark:
        d['deleted'] = mark == 'del'
    if serial:
        d['serial'] = int(serial)
    return d


def set_by_card(ac: int, items: list[str]) -> int:
    """Decisions keyed by card, without a ledger: they outrank the check's own for that card."""
    rec = decided(ac)
    for it in items:
        k, v = it.split('=', 1)
        if not re.fullmatch(r'\d+/\d+/\d+', k):
            raise SystemExit(f'{k!r} is not PART/PAGE/CELL')
        rec['decisions'][k] = {**parse(v), 'cat': 'set', 'set': True}
    p = CACHE / str(ac) / 'decisions.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=1, sort_keys=True), 'utf8')
    if not upload(ac):
        print('NOT UPLOADED yet (network): kept in cache; run `xreview.py sync` when the line is back')
    print(f'AC {ac}: {len(items)} set by card')
    return 0


def decide(ac: int, items: list[str]) -> int:
    led = ledger(ac)
    by_id = {m['id']: m for m in led['manual']}
    rec = decided(ac)
    for it in items:
        i, v = it.split('=', 1)
        m = by_id[int(i)]
        v, _, serial = v.partition('@')
        # A trailing /del or /live is the deleted mark: old-format EPICs have slashes of their own.
        val, mark = (v.rsplit('/', 1) if v.endswith(('/del', '/live')) else (v, ''))
        if val == 'keep':
            if not m['published']:
                raise SystemExit(f'#{i} is not published: give its EPIC or withhold')
            d = {'epic': m['published'][0], 'deleted': m['published'][1]}
        elif val == 'withhold':
            d = {'epic': None}
        elif epic_format.valid(val):     # 8 digits or the old state format too: as printed
            d = {'epic': val}
        else:
            raise SystemExit(f'#{i}: {v!r} is not an EPIC, keep or withhold')
        if mark:
            d['deleted'] = mark == 'del'
        if serial:
            d['serial'] = int(serial)
        d['cat'] = m['cat']
        rec['decisions'][card(m)] = d
    p = CACHE / str(ac) / 'decisions.json'
    p.write_text(json.dumps(rec, indent=1, sort_keys=True), 'utf8')
    left = len(todo(ac))
    if not upload(ac):
        print('NOT UPLOADED yet (network): kept in cache; run `xreview.py sync` when the line is back')
    print(f'AC {ac}: {len(items)} decided, {left} left')
    return 0


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if cmd == 'status':
        sys.exit(status())
    if cmd == 'next':
        sys.exit(nxt())
    if cmd == 'show':
        sys.exit(show(int(sys.argv[2])))
    if cmd == 'set':
        sys.exit(set_by_card(int(sys.argv[2]), sys.argv[3:]))
    if cmd == 'sync':
        sys.exit(sync())
    if cmd == 'decide':
        sys.exit(decide(int(sys.argv[2]), sys.argv[3:]))
    sys.exit(__doc__)
