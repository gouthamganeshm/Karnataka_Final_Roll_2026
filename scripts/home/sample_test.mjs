// Random sample test of the live site: one card from every booth (part) of
// every published constituency, searched on the real page in a headless
// browser, and the answer it shows compared with the verified rows.
//
//   node scripts/home/sample_test.mjs                 # every live AC not yet tested
//   node scripts/home/sample_test.mjs --watch         # keep going as ACs go live
//   node scripts/home/sample_test.mjs --ac 150,196 --retest
//
// Expected answers come from the private release's live-* files (the exact
// input of the site build) with the build's own filters: readers agreed
// (epicOk) and not disputed by the verifier. An AC whose live files are newer
// than the site build (its counts differ from the manifest) waits for the
// next round. Samples hold real EPIC numbers, so everything is written under
// cache/ (git-ignored) and nothing leaves this machine except the searches
// themselves, which go to the site exactly as a voter's would.
import { execFileSync, execSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync, createReadStream } from 'node:fs';
import { createGunzip } from 'node:zlib';
import { createInterface } from 'node:readline';
import { join, resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { randomInt } from 'node:crypto';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const CACHE = join(ROOT, 'cache');
const DIR = join(CACHE, 'sample-test');
const SITE = 'https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/';
const EPIC_RE = /^[A-Z]{3}[0-9]{7}$/;
const PAGES = 8;            // browser tabs searching at once
const DELETED_PER_AC = 10;  // extra samples from deleted cards, the riskiest display

const args = process.argv.slice(2);
const opt = (k) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : null; };
const ONLY = opt('--ac')?.split(',').map(Number) ?? null;
const RETEST = args.includes('--retest');
const WATCH = args.includes('--watch');

// Playwright is installed globally (npm i -g playwright), not in this repo.
const require = createRequire(import.meta.url);
const npmRoot = execSync('npm root -g', { encoding: 'utf8' }).trim();
const { chromium } = require(join(npmRoot, 'playwright'));

mkdirSync(DIR, { recursive: true });
const LOG = join(CACHE, 'sample-test.log');
const log = (s) => { const line = `${new Date().toISOString().slice(0, 19)}Z ${s}`; console.log(line); appendFileSync(LOG, line + '\n'); };
const STATE = join(CACHE, 'sample-tested.json');
const state = existsSync(STATE) ? JSON.parse(readFileSync(STATE, 'utf8')) : {};

const py = (code) => execFileSync('python', ['-c', code], { cwd: ROOT, encoding: 'utf8', env: { ...process.env, PYTHONUTF8: '1' } });

function liveAssets() {
  return JSON.parse(py(`import sys,json; sys.path.insert(0,'scripts'); import release
print(json.dumps({n:a['id'] for n,a in release.assets().items() if n.startswith('live-')}))`));
}

// Downloads only files whose asset id changed (replace() gives a new id).
function fetchLive(ac, ids) {
  const names = [`live-rows-${ac}.jsonl.gz`, `live-verify-${ac}.json`];
  const stamp = join(DIR, `ids-${ac}.json`);
  const want = JSON.stringify(names.map((n) => ids[n]));
  if (!existsSync(stamp) || readFileSync(stamp, 'utf8') !== want || names.some((n) => !existsSync(join(DIR, n)))) {
    execFileSync('python', ['scripts/release.py', 'fetch', DIR, ...names], { cwd: ROOT, stdio: 'ignore' });
    writeFileSync(stamp, want);
  }
  return names.map((n) => join(DIR, n));
}

async function* rows(path) {
  const rl = createInterface({ input: createReadStream(path).pipe(createGunzip()), crlfDelay: Infinity });
  for await (const line of rl) if (line.trim()) yield JSON.parse(line);
}

// Exactly the records the build publishes for one AC.
async function published(ac, rowsPath, verPath) {
  const ver = JSON.parse(readFileSync(verPath, 'utf8'));
  const disputed = new Set((ver.disputed ?? []).map(([p, pg, c]) => `${p}/${pg}/${c}`));
  const out = [];
  for await (const r of rows(rowsPath)) {
    if (!EPIC_RE.test(r.epic) || r.epicOk === false || disputed.has(`${r.part}/${r.page}/${r.cell}`)) continue;
    out.push({ epic: r.epic, ac, part: r.part, serial: r.serial, approx: !r.ok, deleted: !!r.deleted });
  }
  return { ver, recs: out };
}

const key = (h) => `${h.ac}/${h.part}/${h.approx ? '~' : ''}${h.serial}`;

// What the page shows, read from its DOM (English).
async function search(page, epic) {
  await page.$eval('#result', (e) => { e.innerHTML = ''; });
  await page.fill('#epic', epic);
  await page.click('#go');
  await page.waitForFunction((e) => {
    const r = document.querySelector('#result .res');
    if (!r || r.querySelector('.spin')) return false;
    return r.querySelector('.epic-echo')?.textContent === e || !r.querySelector('.epic-echo');
  }, epic, { timeout: 30000 });
  return page.$eval('#result .res', (r) => {
    const blocks = [...r.querySelectorAll('.multi')].map((m) => {
      const v = [...m.querySelectorAll('.tk .v')].map((x) => x.textContent.trim());
      const serial = v[2] ?? '';
      return { ac: +v[0], part: +v[1], serial: +serial.replace('~', ''), approx: serial.startsWith('~') };
    });
    const note = [...r.querySelectorAll('.note')].map((n) => n.textContent).join(' ');
    const also = /Also listed as DELETED at (.*?) — /.exec(note);
    const alsoDeleted = also ? also[1].split(', ').map((s) => {
      const m = /(\d+) · part (\d+) · serial (\d+)/.exec(s);
      return m && { ac: +m[1], part: +m[2], serial: +m[3] };
    }).filter(Boolean) : [];
    return { kind: r.className.replace('res', '').trim(), head: r.querySelector('.res-head').textContent.trim(), blocks, alsoDeleted };
  });
}

// Compare the page with the expected records, only over ACs the site has in sync.
function judge(sample, shown, expected, synced) {
  const inSync = (h) => synced.has(h.ac);
  const problems = [];
  if (!expected.some((h) => key(h) === key(sample))) problems.push('sample not in expected set (bug in test)');
  if (!expected.every(inSync) || shown.blocks.some((h) => !inSync(h))) {
    // The EPIC is also in an AC the site has not rebuilt yet, or in one that
    // went live after this round loaded its files (a voter who moved there):
    // only the sampled place itself can be checked.
    const shownKeys = [...shown.blocks.map(key), ...shown.alsoDeleted.map((h) => `${h.ac}/${h.part}/${h.serial}`)];
    if (!shownKeys.includes(key(sample)) && !shownKeys.includes(`${sample.ac}/${sample.part}/${sample.serial}`)) problems.push(`missing ${key(sample)}`);
    return problems;
  }
  const live = expected.filter((h) => !h.deleted);
  const gone = expected.filter((h) => h.deleted);
  if (live.length) {
    if (shown.kind !== 'ok') problems.push(`expected on-roll, page says "${shown.head}"`);
    const want = new Set(live.map(key));
    const got = new Set(shown.blocks.filter(inSync).map(key));
    for (const k of want) if (!got.has(k)) problems.push(`missing ${k}`);
    for (const k of got) if (!want.has(k)) problems.push(`unexpected ${k}`);
    const wantGone = new Set(gone.map((h) => `${h.ac}/${h.part}/${h.serial}`));
    const gotGone = new Set(shown.alsoDeleted.filter(inSync).map((h) => `${h.ac}/${h.part}/${h.serial}`));
    for (const k of wantGone) if (!gotGone.has(k)) problems.push(`deleted note missing ${k}`);
    for (const k of gotGone) if (!wantGone.has(k)) problems.push(`unexpected deleted note ${k}`);
  } else {
    if (!/Marked DELETED/.test(shown.head)) problems.push(`expected DELETED, page says "${shown.head}"`);
    const want = new Set(gone.map(key));
    const got = new Set(shown.blocks.filter(inSync).map(key));
    for (const k of want) if (!got.has(k)) problems.push(`missing deleted ${k}`);
    for (const k of got) if (!want.has(k)) problems.push(`unexpected ${k}`);
  }
  return problems;
}

async function round(browser) {
  const manifest = await (await fetch(`${SITE}data/manifest.json?t=${Date.now()}`)).json();
  const ids = liveAssets();
  const live = manifest.acs.filter((a) => a.status === 'verified' && (!ONLY || ONLY.includes(a.ac)));
  const all = manifest.acs.filter((a) => a.status === 'verified');

  // One AC's records at a time: the whole state's ~4.5 crore records do not
  // fit in memory (the tester died of it at ~95 ACs). First which ACs' live
  // files match what the site was built from, then the samples, then, for the
  // sampled EPICs only, every record of theirs across all live ACs.
  const synced = new Set();
  const paths = new Map();
  for (const a of all) {
    if (!ids[`live-rows-${a.ac}.jsonl.gz`]) continue;
    const [rp, vp] = fetchLive(a.ac, ids);
    paths.set(a.ac, [rp, vp]);
    const { recs } = await published(a.ac, rp, vp);
    const electors = recs.filter((r) => !r.deleted).length;
    if (electors === a.electors && recs.length - electors === a.deleted) synced.add(a.ac);
  }
  const sig = (a) => `${manifest.builtAt}|${a.electors}|${a.deleted}`;
  const todo = live.filter((a) => synced.has(a.ac) && (RETEST || state[a.ac]?.sig?.split('|').slice(1).join('|') !== sig(a).split('|').slice(1).join('|')));
  const waiting = live.filter((a) => !synced.has(a.ac)).map((a) => a.ac);
  if (waiting.length) log(`waiting for the site to catch up with: ${waiting.join(', ')}`);
  if (!todo.length) return 0;

  const samples = [];
  for (const a of todo) {
    const { recs } = await published(a.ac, ...paths.get(a.ac));
    const byPart = new Map();
    for (const r of recs) { if (!byPart.has(r.part)) byPart.set(r.part, []); byPart.get(r.part).push(r); }
    const empty = [];
    for (let p = 1; p <= a.parts; p++) {
      const pool = byPart.get(p);
      if (!pool?.length) { empty.push(p); continue; }
      samples.push({ ...pool[randomInt(pool.length)], why: 'booth' });
    }
    const gone = recs.filter((r) => r.deleted);
    for (let i = 0; i < Math.min(DELETED_PER_AC, gone.length); i++) samples.push({ ...gone[randomInt(gone.length)], why: 'deleted' });
    if (empty.length) log(`AC ${a.ac}: ${empty.length} booths have no published card to sample (${empty.slice(0, 15).join(', ')}${empty.length > 15 ? '…' : ''})`);
  }
  // Every record of a sampled EPIC, in any live AC (a voter moved between booths or ACs).
  const byEpic = new Map(samples.map((x) => [x.epic, []]));
  for (const [ac, [rp, vp]] of paths) {
    const { recs } = await published(ac, rp, vp);
    for (const r of recs) byEpic.get(r.epic)?.push(r);
  }
  log(`testing ${samples.length} samples from ${todo.length} ACs (${todo.map((a) => a.ac).join(', ')}) on ${PAGES} tabs`);

  const results = [];
  let next = 0;
  const t0 = Date.now();
  await Promise.all(Array.from({ length: PAGES }, async () => {
    const ctx = await browser.newContext();
    await ctx.addInitScript(() => { try { localStorage.setItem('lang', 'en'); } catch { /* */ } });
    const page = await ctx.newPage();
    await page.goto(SITE, { waitUntil: 'networkidle' });
    while (next < samples.length) {
      const s = samples[next++];
      let shown, problems;
      for (let attempt = 0; ; attempt++) {
        try {
          shown = await search(page, s.epic);
          problems = judge(s, shown, byEpic.get(s.epic), synced);
          break;
        } catch (err) {
          if (attempt === 2) { shown = null; problems = [`page error: ${err.message.split('\n')[0]}`]; break; }
          await page.goto(SITE, { waitUntil: 'networkidle' });
        }
      }
      results.push({ ...s, ok: !problems.length, problems, shown: shown && { kind: shown.kind, head: shown.head } });
      if (results.length % 500 === 0) log(`  ${results.length}/${samples.length} searched, ${results.filter((r) => !r.ok).length} failed`);
    }
    await ctx.close();
  }));

  const secs = Math.round((Date.now() - t0) / 1000);
  const stamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  writeFileSync(join(DIR, `report-${stamp}.json`), JSON.stringify({ site: SITE, builtAt: manifest.builtAt, secs, results }, null, 1));
  for (const a of todo) {
    const mine = results.filter((r) => r.ac === a.ac);
    const bad = mine.filter((r) => !r.ok);
    state[a.ac] = { sig: sig(a), tested: mine.length, failed: bad.length, at: new Date().toISOString() };
    log(`AC ${a.ac}: ${mine.length - bad.length}/${mine.length} pass` +
      ` (${mine.filter((r) => r.why === 'booth').length} booths of ${a.parts}, ${mine.filter((r) => r.deleted).length} deleted cards)` +
      (bad.length ? ` — FAILED: ${bad.slice(0, 5).map((r) => `${r.epic} [${r.problems.join('; ')}]`).join(' | ')}` : ''));
  }
  writeFileSync(STATE, JSON.stringify(state, null, 1));
  const failed = results.filter((r) => !r.ok).length;
  log(`round done: ${results.length - failed}/${results.length} pass in ${secs}s; report cache/sample-test/report-${stamp}.json`);
  return failed;
}

const browser = await chromium.launch();
try {
  do {
    try { await round(browser); } catch (err) { log(`round failed: ${err.stack || err}`); }
    if (WATCH) await new Promise((r) => setTimeout(r, 10 * 60 * 1000));
  } while (WATCH);
} finally {
  await browser.close();
}
