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
    python scripts/release.py delete NAME
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
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


def find() -> dict | None:
    """Drafts have no tag yet, so /releases/tags/<tag> cannot see them; list instead."""
    for page in range(1, 20):
        batch = json.loads(gh('api', f'repos/{repo()}/releases?per_page=100&page={page}'))
        for rel in batch:
            if rel['tag_name'] == TAG:
                return rel
        if len(batch) < 100:
            return None
    return None


def ensure() -> dict:
    rel = find()
    if rel:
        if not rel['draft']:
            raise SystemExit(f'release {TAG} is published, not a draft — refusing to put EPIC data in it')
        return rel
    # The listing can lag a just-created release by a few seconds, so use the
    # creation response itself.
    return json.loads(gh('api', '-X', 'POST', f'repos/{repo()}/releases',
                         '-f', f'tag_name={TAG}', '-f', f'name={TAG} (private transfer, do not publish)',
                         '-F', 'draft=true', '-f', 'body=Crops and OCR rows in transit between home and Actions. '
                         'Draft on purpose: never publish this release.'))


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


def download(name: str, dest: str = '.', asset: dict | None = None) -> Path:
    a = asset or assets().get(name)
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
    return [download(n, dest, a) for n, a in sorted(assets().items()) if n.startswith(prefixes)]


def delete(name: str) -> None:
    a = assets().get(name)
    if a:
        gh('api', '-X', 'DELETE', f'repos/{repo()}/releases/assets/{a["id"]}')


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:] or ['list']
    if cmd == 'ensure':
        print(ensure()['id'])
    elif cmd == 'list':
        for n, a in sorted(assets().items()):
            print(f'{a["size"]:>12,}  {n}')
    elif cmd == 'upload':
        upload(*rest)
    elif cmd == 'download':
        print(download(rest[0], rest[1] if len(rest) > 1 else '.'))
    elif cmd == 'download-all':
        for p in download_all(rest[0], tuple(rest[1:]) or ('rows-', 'manifest')):
            print(p)
    elif cmd == 'delete':
        delete(rest[0])
    else:
        raise SystemExit(__doc__)
