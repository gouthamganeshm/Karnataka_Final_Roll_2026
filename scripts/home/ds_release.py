"""Open dataset, the last step: check it and publish it, unattended.

    GH_TOKEN=... python scripts/home/ds_release.py                 # systemd ds-release on eci-1
    GH_TOKEN=... python scripts/home/ds_release.py --dry-run --acs 1,2   # a trial, nothing published

Waits until every AC is joined (ds-<ac>.csv.gz and dsstats-<ac>.json on the
private <tag>-ds draft, ds_pilot.py), then:

  check    every row against the live site (sv_site.py: where a visitor's
           lookup of its EPIC lands) and against a second reading of the roll
           (private: its results stay on the -ds draft);
           every value of every column against what it may hold (no column
           can carry a name, an EPIC or a house number); rows per AC = the
           verified rows; one hash key for all; electors and gender per AC
           against the CEO booklet (reference/ceo-final-2026.json); the share
           of cards read.
  build    one CSV per AC, one Parquet file for the state, summaries per booth
           and per AC, checks.json, README.md (docs/dataset-release.md filled
           in), LICENSE.txt, SHA256SUMS.
  publish  a draft release PUBLIC, every file uploaded and its size checked,
           then made public. A restart carries on; a published release ends it.

A check that fails holds the release (the failures go to the -ds draft as
dsrelease-checks.json) and is tried again every HOLD_H hours, so a fix made on
the -ds draft is picked up. Never touches the live site or its releases, and
never puts the readings (house numbers) or EPICs anywhere public.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home')]
import release  # noqa: E402
import run  # noqa: E402
import ds_join  # noqa: E402
from ds_join import EPIC_RE  # noqa: E402

TAG = release.TAG
DS = f'{TAG}-ds'
PUBLIC = 'dataset-final-roll-2026-v2'
NAME = 'karnataka-final-roll-2026'
OUT = ROOT / 'cache' / 'ds' / 'release'
CEO = ROOT / 'reference' / 'ceo-final-2026.json'
TEMPLATE = ROOT / 'docs' / 'dataset-release.md'
WAIT_S = 900
HOLD_H = 6
MIN_READ = 0.995          # share of an AC's cards whose fields were read
# A second reading of the same roll, kept off the repo (its URL template, with
# {ac:03d}, in ~/.ds_xcheck_url on the VM): only a check; nothing of it and
# nothing about it is published. A booth whose ages agree on fewer than
# DC_MIN_AGREE of the entries both read (at least DC_MIN_N) has its cards on the
# wrong rows.
DC_URL_FILE = Path.home() / '.ds_xcheck_url'
PRIVATE_COLS = ('dc_age_compared', 'dc_age_agree', 'dc_gender_compared', 'dc_gender_agree')
DC_MIN_AGREE = 0.9
DC_MIN_N = 30
GENDER_SLACK = 0.001      # misread genders allowed per AC, share of its electors (at least 5)
REJOIN_IF_NO = {'booths_shifted', 'age_dropped', 'epic_unsettled', 'not_entries'}   # stats a join by the current ds_join.py writes

PATTERNS = {
    'ac': r'^\d{1,3}$', 'part': r'^\d{1,4}$', 'page': r'^\d{1,3}$', 'card': r'^\d{1,2}$',
    'serial': r'^(\d{1,5})?$', 'serial_sure': r'^[01]$', 'status': r'^(live|deleted)$',
    'age': r'^(1[89]|[2-9]\d|1[01]\d|120)?$', 'gender': r'^(M|F|TG)?$',
    'relation': r'^(Father|Husband|Mother|Wife|Other|Guru)?$',
    'epic_hash': r'^([0-9a-f]{24})?$', 'household_hash': r'^([0-9a-f]{16})?$',
}
BANDS = [('18_19', 18, 19), ('20_29', 20, 29), ('30_39', 30, 39), ('40_49', 40, 49), ('50_59', 50, 59),
         ('60_69', 60, 69), ('70_79', 70, 79), ('80_plus', 80, 200)]
SUMMARY = ['entries', 'deleted', 'epic_unsettled', 'electors', 'male', 'female', 'tg', 'gender_unread',
           *[f'age_{b}' for b, _, _ in BANDS], 'age_unread', 'relation_unread']


def log(msg: str) -> None:
    print(time.strftime('%Y-%m-%d %H:%M:%S ') + msg, flush=True)


def on_ds(fn, *args):
    release.TAG = DS
    try:
        return fn(*args)
    finally:
        release.TAG = TAG


def public() -> dict | None:
    """The public release (or its unfinished draft), or None."""
    for r in json.loads(release.gh('api', f'repos/{release.repo()}/releases?per_page=100')):
        if r['tag_name'] == PUBLIC or r['name'] == PUBLIC:
            return r
    return None


def schema():
    import pyarrow as pa
    return pa.schema([
        ('ac', pa.uint8()), ('part', pa.uint16()), ('page', pa.uint16()), ('card', pa.uint8()),
        ('serial', pa.uint16()), ('serial_sure', pa.bool_()), ('status', pa.string()),
        ('age', pa.uint8()), ('gender', pa.string()), ('relation', pa.string()),
        ('epic_hash', pa.string()), ('household_hash', pa.string()),
    ])


def dc_rows(ac: int, tmp: Path) -> dict | None:
    """(part, serial) -> (age, gender) of the second reading; None when it
    cannot be had (the check is then reported as not run, not failed)."""
    import pyarrow.parquet as pq
    from urllib.request import Request, urlopen
    dest = tmp / f'dc-{ac}.parquet'
    if not DC_URL_FILE.exists():
        return None
    url = DC_URL_FILE.read_text('utf8').strip()
    for wait in (0, 30, 120, 300):
        time.sleep(wait)
        try:
            req = Request(url.format(ac=ac), headers={'User-Agent': 'Mozilla/5.0 (dataset cross-check)'})
            with urlopen(req, timeout=300) as r:
                dest.write_bytes(r.read())
            break
        except Exception as exc:  # noqa: BLE001
            log(f'AC {ac}: second reading not fetched: {exc!r}')
    else:
        return None
    g = {'male': 'M', 'female': 'F', 'third_gender': 'TG', 'transgender': 'TG'}
    out, seen = {}, set()
    for r in pq.read_table(dest, columns=['part', 'serial', 'age', 'gender']).to_pylist():
        k = (r['part'], r['serial'])
        if r['serial'] is None or k in seen:
            out.pop(k, None)  # a serial it read twice settles nothing
            seen.add(k)
            continue
        seen.add(k)
        out[k] = (r['age'], g.get(r['gender']))
    dest.unlink()
    return out


def check_ac(ac: int, csv_p: Path, stats: dict, kid: str, ceo: dict, writer, dc: dict | None) -> dict:
    """Checks of one AC (a list of failures, empty when all hold), its summary
    rows, and its rows appended to the Parquet writer."""
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.csv as pcsv
    fails = []
    with gzip.open(csv_p, 'rt', encoding='utf8') as f:
        header = f.readline().strip().split(',')
    if header != ds_join.COLUMNS:
        return {'fails': [f'header {header}'], 'booths': {}, 'ac': {}}
    t = pcsv.read_csv(csv_p, convert_options=pcsv.ConvertOptions(
        column_types={c: pa.string() for c in ds_join.COLUMNS}, strings_can_be_null=False))
    for c, pat in PATTERNS.items():
        bad = len(t) - pc.sum(pc.match_substring_regex(t[c], pat)).as_py() if len(t) else 0
        if bad:
            fails.append(f'{c}: {bad} values outside {pat}')
    if fails:  # nothing below is safe to compute on values that do not parse
        return {'fails': fails, 'booths': {}, 'ac': {}}
    if pc.sum(pc.not_equal(t['ac'], str(ac))).as_py():
        fails.append('rows of another AC')
    if len(t) != stats['stats']['cards']:
        fails.append(f'{len(t)} rows, the join counted {stats["stats"]["cards"]}')
    if stats.get('key_id') != kid:
        fails.append(f'key_id {stats.get("key_id")}, want {kid}')

    def num(c):
        return pc.cast(pc.if_else(pc.equal(t[c], ''), pa.scalar(None, pa.string()), t[c]), pa.int64())

    def text(c):
        return pc.if_else(pc.equal(t[c], ''), pa.scalar(None, pa.string()), t[c])

    cols = {c: num(c) for c in ('ac', 'part', 'page', 'card', 'serial', 'age')}
    typed = pa.table({
        'ac': pc.cast(cols['ac'], pa.uint8()), 'part': pc.cast(cols['part'], pa.uint16()),
        'page': pc.cast(cols['page'], pa.uint16()), 'card': pc.cast(cols['card'], pa.uint8()),
        'serial': pc.cast(cols['serial'], pa.uint16()), 'serial_sure': pc.equal(t['serial_sure'], '1'),
        'status': t['status'], 'age': pc.cast(cols['age'], pa.uint8()), 'gender': text('gender'),
        'relation': text('relation'), 'epic_hash': text('epic_hash'),
        'household_hash': text('household_hash'),
    }, schema=schema())
    if writer is not None:
        writer.write_table(typed)

    # Summaries: electors are the rows not struck off; epic_unsettled counts the
    # electors whose EPIC is not settled (no epic_hash).
    booths = {}
    parts, status = cols['part'].to_pylist(), t['status'].to_pylist()
    ages, gender, relation = cols['age'].to_pylist(), t['gender'].to_pylist(), t['relation'].to_pylist()
    hashes = t['epic_hash'].to_pylist()
    for part, s, a, g, r, h in zip(parts, status, ages, gender, relation, hashes):
        b = booths.get(part)
        if b is None:
            b = booths[part] = dict.fromkeys(SUMMARY, 0)
        b['entries'] += 1
        if s == 'deleted':
            b['deleted'] += 1
            continue
        b['epic_unsettled'] += h == ''
        b['electors'] += 1
        b[{'M': 'male', 'F': 'female', 'TG': 'tg', '': 'gender_unread'}[g]] += 1
        b['relation_unread'] += r == ''
        if a is None:
            b['age_unread'] += 1
        else:
            b[next(f'age_{n}' for n, lo, hi in BANDS if lo <= a <= hi)] += 1
    tot = {k: sum(b[k] for b in booths.values()) for k in SUMMARY}
    read = stats['stats']['read'] / max(1, stats['stats']['cards'])
    if read < MIN_READ:
        fails.append(f'{read:.4f} of cards read, want {MIN_READ}')
    if ceo['electors'] != tot['electors']:
        fails.append(f'{tot["electors"]} electors, CEO {ceo["electors"]}')
    over = sum(max(0, tot[k] - ceo[c]) for k, c in (('male', 'male'), ('female', 'female'), ('tg', 'tg')))
    allowed = max(5, int(GENDER_SLACK * ceo['electors']))
    if over > allowed:
        fails.append(f'{over} more read in a gender than the CEO counts (allowed {allowed})')
    # Against the second reading, entry by entry (part and confirmed serial).
    cmp = {'dc_age_compared': None, 'dc_age_agree': None, 'dc_gender_compared': None, 'dc_gender_agree': None}
    if dc is not None:
        sure = t['serial_sure'].to_pylist()
        serials = cols['serial'].to_pylist()
        per = {}
        na = aa = ng = gg = 0
        for part, sr, ok, a, g in zip(parts, serials, sure, ages, gender):
            d = dc.get((part, sr)) if ok == '1' and sr is not None else None
            if d is None:
                continue
            if a is not None and d[0] is not None:
                na += 1
                aa += a == d[0]
                c = per.setdefault(part, [0, 0])
                c[0] += 1
                c[1] += a == d[0]
            if g and d[1]:
                ng += 1
                gg += g == d[1]
        off = [p for p, (n, k) in per.items() if n >= DC_MIN_N and k / n < DC_MIN_AGREE]
        if off:
            fails.append(f'booths {sorted(off)}: ages agree with the second reading on under {DC_MIN_AGREE:.0%}')
        cmp = {'dc_age_compared': na, 'dc_age_agree': round(aa / na, 5) if na else None,
               'dc_gender_compared': ng, 'dc_gender_agree': round(gg / ng, 5) if ng else None}
    tot.update(cmp)
    tot.update({'ceo_electors': ceo['electors'], 'ceo_male': ceo['male'], 'ceo_female': ceo['female'],
                'ceo_tg': ceo['tg'], 'gender_over_ceo': over, 'cards_read_share': round(read, 5),
                'booths_shifted': stats['stats'].get('booths_shifted', 0)})
    return {'fails': fails, 'booths': booths, 'ac': tot}


def site_check(ac: int, csv_p: Path, tmp: Path, site, k: bytes) -> tuple[list[str], list[list], dict]:
    """Every row against the live site, as a visitor's lookup finds it
    (sv_site.Site): a row with an EPIC hash is on the site under that EPIC at
    its AC, part and serial, struck off or not as here, and its hash is that
    EPIC's; per AC, as many electors and deletions as the site counts.
    Conflicts are given by place only (no EPIC)."""
    lr, = ds_join.get(TAG, [f'live-rows-{ac}.jsonl.gz'], str(tmp))
    with gzip.open(lr, 'rt', encoding='utf8') as f:
        rows = sorted((json.loads(x) for x in f if x.strip()), key=lambda r: (r['part'], r['page'], r['cell']))
    lr.unlink()
    with gzip.open(csv_p, 'rt', encoding='utf8') as f:
        ds = {(int(d['part']), int(d['page']), int(d['card'])): d for d in csv.DictReader(f)}
    fails, conflicts = [], []
    live = dead = 0
    for r in rows:
        at = [ac, r['part'], r['page'], r['cell']]
        d = ds.pop(tuple(at[1:]), None)
        if d is None:   # a row left out as no entry: the site must not have it either
            if r['page'] > 1 or (r.get('epicOk') is not False and EPIC_RE.match(r.get('epic') or '')
                                 and site.lookup(r['epic'])):
                conflicts.append(at + ['left out'])
            continue
        if not d['epic_hash']:
            continue
        if d['epic_hash'] != ds_join.mac(k, r['epic'], 24):
            conflicts.append(at + ['hash'])
            continue
        gone = d['status'] == 'deleted'
        hits = [h for h in site.lookup(r['epic']) if h['ac'] == ac and h['part'] == r['part']]
        if not any(h['serial'] == (r['serial'] & 0x7fff) and h['deleted'] == gone for h in hits):
            conflicts.append(at + ['not on the site' if not hits else 'differs from the site'])
            continue
        dead += gone
        live += not gone
    if ds:
        fails.append(f'{len(ds)} rows not among the live rows')
    s = next((a for a in site.manifest['acs'] if a['ac'] == ac), {})
    if (live, dead) != (s.get('electors'), s.get('deleted')):
        fails.append(f'{live} electors and {dead} deletions with an EPIC hash; the site {s.get("electors")} and {s.get("deleted")}')
    if conflicts:
        fails.append(f'{len(conflicts)} rows disagree with the live site')
    return fails, conflicts, {'site_electors': s.get('electors'), 'site_deleted': s.get('deleted')}


def build(acs: list[int], dry: bool) -> tuple[bool, Path]:
    import pyarrow.parquet as pq
    if OUT.exists():
        shutil.rmtree(OUT)
    pub, tmp = OUT / 'pub', OUT / 'tmp'
    pub.mkdir(parents=True)
    tmp.mkdir()
    k = ds_join.key()
    kid = ds_join.key_id(k)
    ceo = json.loads(CEO.read_text('utf8'))['acs']
    writer = pq.ParquetWriter(pub / f'{NAME}.parquet', schema(), compression='zstd')
    checks, booth_rows, ac_rows, dropped, dc_missing, conflicts, skipped, corrected = {}, [], [], 0, [], [], 0, 0
    ds_join.listing(TAG, fresh=True)
    ds_join.listing(DS, fresh=True)
    import sv_site
    sv_site.snapshot()          # the live site as visitors see it, now
    site = sv_site.Site()
    built_at = site.manifest['builtAt']
    for ac in acs:
        csv_name, st_name = f'ds-{ac}.csv.gz', f'dsstats-{ac}.json'
        csv_p, st_p = ds_join.get(DS, [csv_name, st_name], str(tmp))
        stats = json.loads(st_p.read_text('utf8'))
        if not REJOIN_IF_NO.issubset(stats['stats']):  # joined by older code: join again
            log(f'AC {ac}: joined before {sorted(REJOIN_IF_NO - set(stats["stats"]))}; joining again')
            csv_p.unlink()
            st_p.unlink()
            ds_join.join(ac, k)
            ds_join.listing(DS, fresh=True)
            csv_p, st_p = ds_join.get(DS, [csv_name, st_name], str(tmp))
            stats = json.loads(st_p.read_text('utf8'))
        dc = dc_rows(ac, tmp)
        if dc is None:
            dc_missing.append(ac)
        res = check_ac(ac, csv_p, stats, kid, ceo[str(ac)], writer, dc)
        sfails, sconf, sres = site_check(ac, csv_p, tmp, site, k)
        res['fails'] += sfails
        conflicts += sconf
        if res['ac']:
            res['ac'].update(sres)
        checks[ac] = res['fails']
        for part, b in sorted(res['booths'].items()):
            booth_rows.append({'ac': ac, 'part': part, **b})
        if res['ac']:
            ac_rows.append({'ac': ac, **res['ac']})
        csv_p.rename(pub / f'{NAME}-ac{ac:03d}.csv.gz')
        st_p.unlink()
        dropped += stats['stats']['age_dropped']
        skipped += stats['stats']['not_entries']
        corrected += stats['stats'].get('corrected', 0)
        log(f'AC {ac}: {"ok" if not res["fails"] else res["fails"]}')
    writer.close()
    public_ac = [{k: v for k, v in r.items() if k not in PRIVATE_COLS} for r in ac_rows]
    for name, rows in (('summary-booth', booth_rows), ('summary-ac', public_ac)):
        with open(pub / f'{NAME}-{name}.csv', 'w', newline='', encoding='utf8') as f:
            if rows:
                w = csv.DictWriter(f, list(rows[0]))
                w.writeheader()
                w.writerows(rows)
    failed = {ac: f for ac, f in checks.items() if f}
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    tot = {c: sum(r[c] for r in ac_rows) for c in ('entries', 'electors', 'deleted', 'male', 'female', 'tg',
                                                    'gender_unread', 'age_unread', 'ceo_electors')}
    tot['age_dropped'] = dropped
    tot['not_entries'] = skipped
    tot['corrected_by_person'] = corrected
    for c in ('dc_age', 'dc_gender'):
        n = sum(r[f'{c}_compared'] or 0 for r in ac_rows)
        k = sum(round((r[f'{c}_agree'] or 0) * (r[f'{c}_compared'] or 0)) for r in ac_rows)
        tot[f'{c}_compared'], tot[f'{c}_agree'] = n, round(k / n, 5) if n else None
    tot['dc_not_run_acs'] = dc_missing
    tot['site_build'] = built_at
    tot['site_conflicts'] = len(conflicts)
    (OUT / 'dsrelease-conflicts.json').write_text(json.dumps(conflicts), 'utf8')
    report = {'release': PUBLIC, 'key_id': kid, 'built': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'commit': commit, 'acs': len(acs), 'passed': not failed, 'failed': failed, 'totals': tot,
              'thresholds': {'min_read': MIN_READ, 'gender_slack': GENDER_SLACK}}
    public = {**report, 'totals': {k: v for k, v in tot.items() if not k.startswith('dc_')},
              'failed': {a: [f for f in fs if 'second reading' not in f] for a, fs in failed.items()}}
    (pub / 'checks.json').write_text(json.dumps(public, indent=1), 'utf8')
    (OUT / 'dsrelease-checks.json').write_text(json.dumps(report, indent=1), 'utf8')
    shifted = sum(r['booths_shifted'] for r in ac_rows)
    readme = TEMPLATE.read_text('utf8').format(
        release=PUBLIC, key_id=kid, built=report['built'], commit=commit[:7], acs=len(acs),
        entries=f'{tot["entries"]:,}', electors=f'{tot["electors"]:,}', deleted=f'{tot["deleted"]:,}',
        ceo_electors=f'{tot["ceo_electors"]:,}', male=f'{tot["male"]:,}', female=f'{tot["female"]:,}',
        tg=f'{tot["tg"]:,}', gender_unread=f'{tot["gender_unread"]:,}', age_unread=f'{tot["age_unread"]:,}',
        shifted=shifted, age_dropped=f'{dropped:,}', not_entries=skipped, corrected=corrected, name=NAME, site_build=built_at,
        min_read=f'{MIN_READ:.1%}', gender_slack=f'{GENDER_SLACK:.1%}')
    (pub / 'README.md').write_text(readme, 'utf8')
    (pub / 'LICENSE.txt').write_text(LICENCE, 'utf8')
    sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in sorted(pub.iterdir()))
    (pub / 'SHA256SUMS').write_text(sums, 'utf8')
    shutil.rmtree(tmp)
    if not dry:
        on_ds(release.upload, str(OUT / 'dsrelease-checks.json'), str(OUT / 'dsrelease-conflicts.json'))
    log(f'built {len(acs)} ACs: {"all checks hold" if not failed else f"{len(failed)} ACs fail"}')
    return not failed, pub


def publish(pub: Path) -> None:
    rel = public()
    if rel is None:
        release.gh('release', 'create', PUBLIC, '-R', release.repo(), '--draft', '--target', 'main',
                   '--title', 'Karnataka final roll 2026: open dataset (no names, no EPICs)',
                   '--notes-file', str(pub / 'README.md'))
        rel = public()
    files = sorted(pub.iterdir())
    for attempt in range(6):
        have = {a['name']: a['size'] for a in json.loads(release.gh(
            'api', f'repos/{release.repo()}/releases/{rel["id"]}/assets?per_page=100&page=1'))}
        for page in range(2, 6):
            more = json.loads(release.gh('api', f'repos/{release.repo()}/releases/{rel["id"]}/assets?per_page=100&page={page}'))
            have.update({a['name']: a['size'] for a in more})
            if not more:
                break
        todo = [p for p in files if have.get(p.name) != p.stat().st_size]
        if not todo:
            break
        log(f'uploading {len(todo)} files (attempt {attempt + 1})')
        for i in range(0, len(todo), 10):
            try:
                release.gh('release', 'upload', PUBLIC, *map(str, todo[i:i + 10]), '--clobber', '-R', release.repo())
            except Exception as exc:  # noqa: BLE001 - checked on the next pass
                log(f'upload failed: {exc!r}')
                time.sleep(60)
    else:
        raise RuntimeError('files would not all upload')
    release.gh('release', 'edit', PUBLIC, '-R', release.repo(), '--draft=false', '--latest=false',
               '--notes-file', str(pub / 'README.md'))
    log(f'published {PUBLIC}: {len(files)} files')


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='build and check only')
    ap.add_argument('--acs', help='comma-separated ACs (a trial; implies --dry-run)')
    args = ap.parse_args()
    manifest = json.loads(run.MANIFEST.read_text('utf8'))
    acs = [int(x) for x in args.acs.split(',')] if args.acs else \
        sorted(c['acNumber'] for c in manifest['constituencies'] if c['parts'])
    dry = args.dry_run or bool(args.acs)
    while True:
        try:
            rel = None if dry else public()
            if rel and not rel['draft']:
                log(f'{PUBLIC} is published')
                return 0
            have = on_ds(release.assets)
            left = [a for a in acs if f'ds-{a}.csv.gz' not in have or f'dsstats-{a}.json' not in have]
            if left:
                log(f'{len(acs) - len(left)}/{len(acs)} ACs joined; waiting')
                time.sleep(WAIT_S)
                continue
            ok, pub = build(acs, dry)
            if dry:
                return 0 if ok else 1
            if not ok:
                log(f'checks fail; release held, built again in {HOLD_H} h')
                time.sleep(HOLD_H * 3600)
                continue
            publish(pub)
        except Exception as exc:  # noqa: BLE001 - an outage: try again shortly
            log(f'failed: {exc!r}')
            time.sleep(300)


LICENCE = """Karnataka final electoral roll 2026: open dataset (no names, no EPICs)

This database is made available under the Open Database License (ODbL) v1.0:
https://opendatacommons.org/licenses/odbl/1-0/
Any rights in individual contents of the database are licensed under the
Database Contents License: https://opendatacommons.org/licenses/dbcl/1-0/

In short: you may share, adapt and build on it, also commercially, if you
credit "Karnataka Final Roll 2026 (github.com/gouthamganeshm/Karnataka_Final_Roll_2026)",
keep any database you make from it under the ODbL, and do not use it to
re-identify electors.

Source: the final electoral rolls published by the Election Commission of India
(voters.eci.gov.in) and the Chief Electoral Officer, Karnataka (ceo.karnataka.gov.in).
"""


if __name__ == '__main__':
    sys.exit(main())
