"""Record-level checks the verifier worker runs on every published EPIC.

V1  independent re-read. The prototype reader (`glyphs.Prototypes`: different
    glyph features, several prototypes per character) re-reads each published
    EPIC. A character it disagrees on is looked at once more by Tesseract on
    the crop alone (psm 13, a different scale from the main pass). Every
    character must be supported by at least one of them, or the record is
    disputed and withheld.

V4  draft corroboration. An EPIC already present in the draft roll for the
    same constituency is independent evidence (the draft site was read from
    different PDFs, by a different pipeline). An EPIC that is *not* there — a
    new elector, a moved one, or a misread — is held to a stricter standard:
    the prototype reader must agree on every letter outright.

Kept free of I/O so the CI worker (`ci/verify_ac.py`) and the offline
evaluation run exactly the same rules.
"""
from __future__ import annotations

import hashlib

import numpy as np

import crops as C
import glyphs as G

prototypes = C.prototypes
proto_read = C.proto_read


def v1(records: list[tuple], style: str = 'kan', reads: list | None = None) -> list[str | None]:
    """records: [(crop, epic)] for one part. Returns, per record, None when
    every character is supported, else a short reason ("v1:3" = position 3).
    `reads` may carry `proto_read` results already computed for these crops."""
    if reads is None:
        reads = [proto_read(crop, style) for crop, _ in records]
    need = [i for i, ((_, epic), r) in enumerate(zip(records, reads))
            if r is None or ''.join(x[0] for x in r) != epic]
    t13 = {}
    if need:
        texts = C.read_each([C._single_line(records[i][0], target=70) for i in need], psm=13)
        t13 = {i: C.R.coerce_epic(t) for i, t in zip(need, texts)}
    out: list[str | None] = []
    for i, ((_, epic), r) in enumerate(zip(records, reads)):
        if i not in t13:
            out.append(None)
            continue
        t = t13[i] if C.R.EPIC_RE.match(t13[i] or '') else ''
        if r is None:
            # No glyph split to re-read: Tesseract alone must reproduce it all.
            out.append(None if t == epic else 'v1:noglyph')
            continue
        bad = [k for k, ch in enumerate(epic) if r[k][0] != ch and not (t and t[k] == ch)]
        out.append(f'v1:{bad[0]}' if bad else None)
    return out


def hash_key(epic: str) -> int:
    """The 12 hex digits of SHA-256(EPIC) the draft site stores (4 bucket + 8 suffix)."""
    return int(hashlib.sha256(epic.encode('utf8')).hexdigest()[:12], 16)


def corroborated(epics: list[str], keys: np.ndarray | None) -> list[bool | None]:
    """Per EPIC: is it in the draft roll's key set for this AC? None = no draft data."""
    if keys is None or not len(keys):
        return [None] * len(epics)
    q = np.array([hash_key(e) for e in epics], dtype=np.uint64)
    pos = np.searchsorted(keys, q)
    pos = np.minimum(pos, len(keys) - 1)
    return list(keys[pos] == q)


def v4(crop, epic: str, style: str = 'kan', read=False) -> str | None:
    """Stricter standard for an EPIC the draft roll does not corroborate: the
    prototype reader must agree on all three letters. `read` may carry the
    `proto_read` result already computed for this crop."""
    r = proto_read(crop, style) if read is False else read
    if r is None:
        return 'v4:noglyph'
    if ''.join(x[0] for x in r[:3]) != epic[:3]:
        return 'v4:letters'
    return None
