"""The draft GitHub Release that carries crops and rows between home and Actions.

A *draft* release, deliberately: its assets are visible only to people with push
access to the repo (and to the repo's own workflows), never to the public. The
crops and the rows both contain plaintext EPIC numbers; only the hashed buckets
built by `ci/build.mjs` are ever published.

Everything goes through the `gh` CLI, which is logged in at home and is given
GITHUB_TOKEN on Actions.

    python scripts/release.py ensure
    python scripts/release.py list
    python scripts/release.py upload FILE [FILE...]
    python scripts/release.py download NAME [DEST_DIR]
    python scripts/release.py download-all DEST_DIR [PREFIX...]
    python scripts/release.py fetch DEST_DIR NAME [NAME...]
    python scripts/release.py delete NAME [NAME...]
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = json.loads((ROOT / 'roll-source.json').read_text('utf8'))
TAG = os.environ.get('ROLL_RELEASE', SOURCE['release'])


def gh(*args: str, capture: bool = True, binary: bool = False):
    proc = subprocess.run(['gh', *args], capture_output=capture, check=False)
    if proc.returncode != 0:
        err = proc.stderr.decode('utf8', 'replace') if capture else ''
        raise RuntimeError(f'gh {" ".join(args[:3])} failed: {err.strip()}')
    if not capture:
        return None
    return proc.stdout if binary else proc.stdout.decode('utf8', 'replace')


_REPO = None


def repo() -> str:
    global _REPO
    if _REPO is None:
        _REPO = os.environ.get('GITHUB_REPOSITORY') or gh(
            'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').strip()
    return _REPO


_CREATED = None


def find() -> dict | None:
    """Drafts have no tag yet, so /releases/tags/<tag> cannot see them; list instead.

    If two drafts ever carry the tag, the oldest is the one `gh release upload`
    writes to, so that is the one returned."""
    found = []
    for page in range(1, 20):
        batch = json.loads(gh('api', f'repos/{repo()}/releases?per_page=100&page={page}'))
        found += [rel for rel in batch if rel['tag_name'] == TAG]
        if len(batch) < 100:
            break
    return min(found, key=lambda r: r['id']) if found else None


def ensure() -> dict:
    global _CREATED
    rel = find() or _CREATED
    if rel:
        if not rel['draft']:
            raise SystemExit(f'release {TAG} is published, not a draft — refusing to put EPIC data in it')
        return rel
    # The listing can lag a just-created release by a few seconds, so use the
    # creation response itself, and remember it: the next ensure() in this
    # process (the manifest upload, straight after) would otherwise miss it in
    # the listing and create a second draft with the same tag — which happened
    # on the final roll's first run, and the OCR job then read the empty one.
    _CREATED = json.loads(gh('api', '-X', 'POST', f'repos/{repo()}/releases',
                             '-f', f'tag_name={TAG}', '-f', f'name={TAG} (private transfer, do not publish)',
                             '-F', 'draft=true', '-f', 'body=Crops and OCR rows in transit between home and Actions. '
                             'Draft on purpose: never publish this release.'))
    return _CREATED


def assets() -> dict[str, dict]:
    rel = find()
    if not rel:
        return {}
    out = {}
    for page in range(1, 50):
        batch = json.loads(gh('api', f'repos/{repo()}/releases/{rel["id"]}/assets?per_page=100&page={page}'))
        out.update({a['name']: a for a in batch})
        if len(batch) < 100:
            break
    return out


def upload(*paths: str) -> None:
    ensure()
    gh('release', 'upload', TAG, *paths, '--clobber', '-R', repo())


def replace(*paths: str) -> None:
    """Upload each file, swapping out any asset of the same name with no gap:
    upload as <name>.next, delete the old asset, rename. `upload --clobber`
    deletes first, so a reader in between (a publish build) saw no file."""
    import shutil
    import tempfile
    ensure()
    for path in paths:
        name = Path(path).name
        with tempfile.TemporaryDirectory() as tmp:
            nxt = Path(tmp) / f'{name}.next'
            shutil.copyfile(path, nxt)
            gh('release', 'upload', TAG, str(nxt), '--clobber', '-R', repo())
        a = assets()
        if name in a:
            gh('api', '-X', 'DELETE', f'repos/{repo()}/releases/assets/{a[name]["id"]}')
        gh('api', '-X', 'PATCH', f'repos/{repo()}/releases/assets/{a[f"{name}.next"]["id"]}', '-f', f'name={name}')


def download(name: str, dest: str = '.', asset: dict | None = None) -> Path:
    # The listing is paged, and an asset deleted by another job mid-listing
    # shifts the rest down a page, so one can be missed: look again before
    # concluding it is not there (AC 196's verify failed on exactly that).
    a = asset or assets().get(name)
    for wait in (3, 10):
        if a:
            break
        time.sleep(wait)
        a = assets().get(name)
    if not a:
        raise SystemExit(f'no asset {name} in {TAG}')
    out = Path(dest) / name
    out.parent.mkdir(parents=True, exist_ok=True)
    # Streamed straight to disk: a large constituency's crop tar is ~1 GB.
    with open(out, 'wb') as fh:
        proc = subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream',
                               f'repos/{repo()}/releases/assets/{a["id"]}'],
                              stdout=fh, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0 or out.stat().st_size != a['size']:
        raise RuntimeError(f'download of {name} failed: {proc.stderr.decode("utf8", "replace").strip()}')
    return out


def download_all(dest: str, prefixes: tuple[str, ...]) -> list[Path]:
    # An asset still being uploaded (state "starter", e.g. rows being replaced)
    # is skipped: the publish build read one half-written and failed on it.
    # Two listings are joined, so an asset one of them missed (see download)
    # is still fetched. One replaced since (new id) is looked up again.
    found = {**assets(), **assets()}
    out = []
    for n, a in sorted(found.items()):
        if n.startswith(prefixes) and a.get('state', 'uploaded') == 'uploaded':
            try:
                out.append(download(n, dest, a))
            except RuntimeError:
                out.append(download(n, dest))
    return out


def fetch(dest: str, names: list[str]) -> list[Path]:
    """Download several assets on one listing: Actions' token allows 1,000 API
    calls an hour per repo, and every listing costs a few."""
    found = assets()
    return [download(n, dest, found.get(n)) for n in names]


def delete(*names: str) -> None:
    found = assets()
    for name in names:
        if name in found:
            gh('api', '-X', 'DELETE', f'repos/{repo()}/releases/assets/{found[name]["id"]}')


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:] or ['list']
    if cmd == 'ensure':
        print(ensure()['id'])
    elif cmd == 'list':
        for n, a in sorted(assets().items()):
            print(f'{a["size"]:>12,}  {n}')
    elif cmd == 'upload':
        upload(*rest)
    elif cmd == 'replace':
        replace(*rest)
    elif cmd == 'download':
        print(download(rest[0], rest[1] if len(rest) > 1 else '.'))
    elif cmd == 'download-all':
        for p in download_all(rest[0], tuple(rest[1:]) or ('rows-', 'manifest')):
            print(p)
    elif cmd == 'fetch':
        for p in fetch(rest[0], rest[1:]):
            print(p)
    elif cmd == 'delete':
        delete(*rest)
    else:
        raise SystemExit(__doc__)
