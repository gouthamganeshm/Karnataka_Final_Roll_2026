"""The live site as a visitor's browser sees it: snapshot, lookup, re-check.

    python scripts/home/sv_site.py snapshot     # all 65,536 buckets from the live site -> cache/sv/
    python scripts/home/sv_site.py upload       # the snapshot to the private results release
    python scripts/home/sv_site.py get          # the snapshot from the release (other VMs)
    python scripts/home/sv_site.py recheck      # live site again: is every file still the snapshot?

A lookup here is site/app.js's, byte for byte: SHA-256 of the EPIC's letters
and digits, bucket data/roll/<h0>/<h1>.bin, 9-byte records sorted by hash
bytes 2..5 (big-endian), then u8 ac, u16 part (top bit deleted), u16 serial
(top bit: serial not confirmed), little-endian. The snapshot is the data the
sample verification (docs/sample-verification.md) checks against; the site is
frozen meanwhile and `recheck` proves it at the end.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import sys
import tarfile
import time
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import release  # noqa: E402

SITE = 'https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/'
DIR = ROOT / 'cache' / 'sv'
SNAP = DIR / 'site-snapshot.tar'
RESULTS = f'{release.TAG}-svr'
REC = 9


def _get(url: str) -> bytes | None:
    for wait in (0, 2, 10, 30, 60):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}),
                                        timeout=60) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:  # noqa: BLE001 - retried
            pass
    raise RuntimeError(f'cannot fetch {url}')


def names() -> list[str]:
    return [f'{a:02x}/{b:02x}' for a in range(256) for b in range(256)]


def fetch_live() -> tuple[dict, dict[str, bytes | None]]:
    manifest = json.loads(_get(SITE + 'data/manifest.json?x=' + str(time.time())))
    v = urllib.request.quote(manifest['builtAt'])

    def one(n):
        return n, _get(f'{SITE}data/roll/{n}.bin?v={v}')
    with ThreadPoolExecutor(32) as pool:
        files = dict(pool.map(one, names()))
    return manifest, files


def snapshot() -> None:
    t = time.time()
    manifest, files = fetch_live()
    again = json.loads(_get(SITE + 'data/manifest.json?x=' + str(time.time())))
    if again['builtAt'] != manifest['builtAt']:
        raise SystemExit('the site was rebuilt during the snapshot; take it again')
    sha = {n: hashlib.sha256(b).hexdigest() if b is not None else None for n, b in files.items()}
    DIR.mkdir(parents=True, exist_ok=True)
    with tarfile.open(SNAP, 'w') as tar:
        for name, data in [('manifest.json', json.dumps(manifest).encode()),
                           ('sha256.json', json.dumps(sha).encode())] + \
                          [(f'roll/{n}.bin', b) for n, b in files.items() if b is not None]:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    size = sum(len(b) for b in files.values() if b)
    print(f'snapshot of build {manifest["builtAt"]}: {sum(b is not None for b in files.values())} files, '
          f'{size // REC} records, {size / 1e6:.0f} MB in {time.time() - t:.0f}s -> {SNAP}')


class Site:
    """The snapshot in memory (~400 MB): lookups by EPIC and by place."""

    def __init__(self, path: Path = SNAP):
        self.buckets: dict[str, bytes] = {}
        with tarfile.open(path) as tar:
            for m in tar:
                data = tar.extractfile(m).read()
                if m.name == 'manifest.json':
                    self.manifest = json.loads(data)
                elif m.name == 'sha256.json':
                    self.sha = json.loads(data)
                else:
                    self.buckets[m.name[5:10]] = data
        self._places: dict[int, dict] = {}

    @staticmethod
    def key(epic: str) -> bytes:
        return hashlib.sha256(re.sub(r'[^A-Z0-9]', '', epic.upper()).encode()).digest()

    @staticmethod
    def _rec(data: bytes, i: int) -> dict:
        _, ac, p, s = struct.unpack_from('>I', data, i * REC) + struct.unpack_from('<BHH', data, i * REC + 4)
        return {'ac': ac, 'part': p & 0x7fff, 'deleted': bool(p & 0x8000),
                'serial': s & 0x7fff, 'approx': bool(s & 0x8000)}

    def lookup(self, epic: str) -> list[dict]:
        h = self.key(epic)
        data = self.buckets.get(f'{h[0]:02x}/{h[1]:02x}', b'')
        want = int.from_bytes(h[2:6], 'big')
        lo, hi = 0, len(data) // REC
        while lo < hi:
            mid = (lo + hi) // 2
            if struct.unpack_from('>I', data, mid * REC)[0] < want:
                lo = mid + 1
            else:
                hi = mid
        hits = []
        while lo < len(data) // REC and struct.unpack_from('>I', data, lo * REC)[0] == want:
            hits.append(self._rec(data, lo))
            lo += 1
        return hits

    def places(self, ac: int) -> dict[tuple[int, int], list[tuple[bytes, bool, bool]]]:
        """(part, serial) -> [(hash bytes 0..5, deleted, approx)] for one AC: what the
        site holds at each place, to see a card published under another EPIC."""
        if ac not in self._places:
            import numpy as np
            dt = np.dtype([('h', '>u4'), ('ac', 'u1'), ('p', '<u2'), ('s', '<u2')])
            out = defaultdict(list)
            for name, data in self.buckets.items():
                prefix = bytes.fromhex(name.replace('/', ''))
                recs = np.frombuffer(data, dtype=dt)
                for h, p, s in recs[recs['ac'] == ac][['h', 'p', 's']].tolist():
                    out[(p & 0x7fff, s & 0x7fff)].append((prefix + h.to_bytes(4, 'big'),
                                                          bool(p & 0x8000), bool(s & 0x8000)))
            self._places = {ac: dict(out)}   # one AC at a time: memory
        return self._places[ac]


def recheck() -> int:
    site = Site()
    manifest, files = fetch_live()
    bad = [n for n, b in files.items()
           if (hashlib.sha256(b).hexdigest() if b is not None else None) != site.sha.get(n)]
    same_build = manifest['builtAt'] == site.manifest['builtAt']
    print(f'live build {manifest["builtAt"]} (snapshot {site.manifest["builtAt"]}); '
          f'{len(files) - len(bad)}/{len(files)} files identical to the snapshot'
          + (f'; DIFFERENT: {bad[:20]}' if bad else ''))
    return 0 if not bad and same_build else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['snapshot', 'upload', 'get', 'recheck'])
    a = ap.parse_args()
    if a.cmd == 'snapshot':
        snapshot()
    elif a.cmd == 'upload':
        release.TAG = RESULTS
        release.upload(str(SNAP))
    elif a.cmd == 'get':
        release.TAG = RESULTS
        release.fetch(str(DIR), [SNAP.name])
    else:
        return recheck()
    return 0


if __name__ == '__main__':
    sys.exit(main())
