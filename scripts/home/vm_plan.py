"""Split the ACs still to fetch across the VMs, balanced by part count, no AC on two VMs.

    python scripts/home/vm_plan.py [N=4]      # writes reference/vm-plan.json

Whole districts stay together and go to whichever VM has the fewest parts so
far, in queue order (largest district first), so every VM finishes at about
the same time. `vm_fetch.py --vm K` reads the plan; the plan is fixed, so VMs
never need to agree on anything at run time.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'scripts' / 'home'))
import run  # noqa: E402

PLAN = ROOT / 'reference' / 'vm-plan.json'


def main(n: int) -> None:
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    parts = {c['acNumber']: c['parts'] for c in manifest['constituencies'] if c['parts']}
    shipped = json.loads(run.SHIPPED.read_text('utf8')) if run.SHIPPED.exists() else {}
    district = {c['acNumber']: c['district'] for c in run.SEED['constituencies']}
    todo = [a for a in run.run_order({a: list(range(p)) for a, p in parts.items()}, 'all') if str(a) not in shipped]
    groups = []
    for a in todo:
        if groups and district.get(groups[-1][0]) == district.get(a):
            groups[-1].append(a)
        else:
            groups.append([a])
    load = [0] * n
    vms = [[] for _ in range(n)]
    for g in groups:
        k = load.index(min(load))
        vms[k] += g
        load[k] += sum(parts[a] for a in g)
    PLAN.write_text(json.dumps({str(k + 1): v for k, v in enumerate(vms)}, indent=1), 'utf8')
    for k in range(n):
        print(f'VM {k + 1}: {len(vms[k])} ACs, {load[k]} parts')


if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
