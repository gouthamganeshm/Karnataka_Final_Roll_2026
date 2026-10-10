"""Export the draft roll site's records as per-AC hash-key sets (verifier check V4).

    python scripts/ci/draft_keys.py DRAFT_ROLL_DIR OUT_DIR

DRAFT_ROLL_DIR is the draft site's `docs/data/roll` (65,536 buckets,
`ab/cd.json`, each a JSON list of [suffix8, ac, part, serial(, 1)]). A record's
key is the 12 hex digits of SHA-256(EPIC) the draft site stores: the 4-digit
bucket prefix plus the 8-digit suffix. OUT_DIR gets `draft-<ac>.npy` per AC,
a sorted uint64 array of those keys — no EPIC appears anywhere.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np


def main(src: str, dst: str) -> int:
    keys = defaultdict(list)
    n = 0
    for f in sorted(Path(src).glob('*/*.json')):
        prefix = f.parent.name + f.stem
        if len(prefix) != 4:
            raise SystemExit(f'unexpected bucket path {f}')
        for rec in json.loads(f.read_text('utf8')):
            keys[int(rec[1])].append(int(prefix + rec[0], 16))
            n += 1
    out = Path(dst)
    out.mkdir(parents=True, exist_ok=True)
    for ac, ks in sorted(keys.items()):
        np.save(out / f'draft-{ac}.npy', np.unique(np.array(ks, dtype=np.uint64)))
    print(f'{n} draft records -> {len(keys)} ACs in {out}')
    return 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:3]))
