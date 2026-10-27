"""Run the whole state through the home stage unattended: Kannada roll only,
Bengaluru first, resumable, restarted after any crash until every AC ships.

    python scripts/home/roll_queue.py                 # what the logon task runs
    python scripts/home/roll_queue.py --wait-for 153  # take over from a running `go`
                                                 # once it has shipped that AC

Only one queue runs at a time: a second copy (the logon task while one is
already going) exits at once. Log: cache/queue.log; run.py output:
cache/queue-run.log.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / 'cache'
SOURCE = json.loads((ROOT / 'roll-source.json').read_text('utf8'))
SHIPPED = CACHE / f"shipped-{SOURCE['release']}.json"
LOG = CACHE / 'queue.log'
QUIET = {'creationflags': 0x08000000} if os.name == 'nt' else {}   # no console windows under pythonw


def log(msg: str) -> None:
    with open(LOG, 'a', encoding='utf8') as f:
        f.write(time.strftime('%Y-%m-%d %H:%M:%S ') + msg + '\n')


def shipped() -> dict:
    return json.loads(SHIPPED.read_text('utf8')) if SHIPPED.exists() else {}


def pythons(pattern: str) -> list[int]:
    """PIDs of python processes whose command line matches `pattern`, not this one."""
    out = subprocess.run(['powershell', '-NoProfile', '-Command',
                          "Get-CimInstance Win32_Process -Filter \"Name='python.exe' OR Name='pythonw.exe'\" | "
                          f"Where-Object {{ $_.CommandLine -match '{pattern}' }} | ForEach-Object {{ $_.ProcessId }}"],
                         capture_output=True, text=True, **QUIET).stdout.split()
    return [int(p) for p in out if int(p) != os.getpid()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--wait-for', help='AC a running `go` must ship before this queue takes over')
    ap.add_argument('--workers', default='6')
    args = ap.parse_args()
    CACHE.mkdir(exist_ok=True)
    if pythons(r'roll_queue\.py'):
        log('another queue is already running; exiting')
        return 0
    all_acs = {str(c['acNumber']) for c in json.loads((CACHE / 'manifest.json').read_text('utf8'))['constituencies']
               if c['parts']}
    if args.wait_for:
        log(f'waiting for AC {args.wait_for} to ship')
        while args.wait_for not in shipped() and pythons(r'run\.py.*go'):
            time.sleep(20)
    # Only another queue's downloader; a targeted re-fetch (run.py go --ac ...)
    # beside the queue is left running.
    for pid in pythons(r'run\.py.*go.*--tranche'):
        subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], capture_output=True, **QUIET)
        log(f'stopped downloader {pid}')
    time.sleep(5)
    attempt = 0
    while not all_acs <= set(shipped()):
        for f in (CACHE / 'out').glob('crops-*.tar'):   # half-cut by an interrupted run
            try:
                f.unlink()
            except OSError:
                log(f'{f.name} is in use (a re-fetch beside the queue); left alone')
        attempt += 1
        log(f'run {attempt}: {len(set(shipped()) & all_acs)}/{len(all_acs)} ACs shipped')
        with open(CACHE / 'queue-run.log', 'a', encoding='utf8') as out:
            rc = subprocess.call([sys.executable, '-u', 'scripts/home/run.py', 'go', '--tranche', 'all',
                                  '--no-eng', '--workers', args.workers], cwd=ROOT, stdout=out, stderr=subprocess.STDOUT,
                                 **QUIET)
        log(f'run {attempt} exited {rc}')
        if not all_acs <= set(shipped()):
            time.sleep(120)
    failed = {a: v['failed'] for a, v in shipped().items() if v.get('failed')}
    log(f'ALL {len(all_acs)} ACs shipped; unreadable parts: {json.dumps(failed)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
