/* Build the public site: verified OCR rows -> hashed binary buckets + manifest.
 *
 *   node scripts/ci/build.mjs <rows-dir> <out-dir>
 *
 * <rows-dir> holds, per AC, what the draft release carries: rows-<ac>.jsonl.gz
 * and its summary (OCR), verify-<ac>.json (verifier worker) and, for the
 * English cross-check, eng-<ac>.jsonl.gz; plus manifest.json from home.
 * <out-dir> gets a copy of site/ plus:
 *
 *   data/manifest.json       roll label, coverage, per-AC status, counts and names
 *   data/roll/ab/cd.bin      every record whose SHA-256(EPIC) starts with abcd
 *
 * Publish gate. An AC is published only when its verifier verdict is "pass";
 * until then it is "pending", and "held" if the verifier held it. Within a
 * published AC a record goes out only if its EPIC readers agreed (`epicOk`) and
 * the verifier did not dispute it. The English cross-check (V5) runs here,
 * because it needs both the Kannada and English OCR, which finish in either
 * order: in the cross-check part every record is compared serial by serial with
 * the English reading where two English readers agreed outright; a
 * record the English roll contradicts is withheld, and an AC agreeing on fewer
 * than 99.7% of compared records is held.
 *
 * Official count (reference/ceo-final-2026.json, from the CEO Karnataka's own
 * final-roll statement): an AC whose live cards read differ from its official
 * elector count by more than 0.5% is held, whatever the verifier said.
 *
 * A record is 9 bytes, sorted by suffix so the browser can binary-search a
 * bucket. The suffix is raw hash bytes (compare big-endian); the rest is
 * little-endian:
 *
 *   4 bytes      suffix: bytes 2..5 of SHA-256(EPIC)
 *   u8  ac
 *   u16 part     top bit set = the card is marked DELETED in the final roll
 *   u16 serial   top bit set = serial not OCR-confirmed (EPIC itself is fine)
 *
 * A deleted card is published like any other (same readers, same verifier),
 * so the site can say where the EPIC was struck off; it is not counted as an
 * elector.
 *
 * No EPIC is published, only a hash fragment — the browser already knows the
 * number the visitor typed. 4.4 crore electors at 9 bytes is ~400 MB, inside
 * GitHub Pages' 1 GB site limit.
 */
import { createHash } from 'node:crypto';
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { createGunzip } from 'node:zlib';
import { createReadStream } from 'node:fs';
import { createInterface } from 'node:readline';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
const [rowsDir, outDir] = process.argv.slice(2);
if (!rowsDir || !outDir) {
  console.error('usage: node scripts/ci/build.mjs <rows-dir> <out-dir>');
  process.exit(2);
}

const EPIC_RE = /^[A-Z]{3}[0-9]{7}$/;
const REC = 10; // bucket byte + 9-byte record, while grouping
// Bumped whenever the record layout changes meaning (2: part's top bit = deleted).
// site/app.js carries the same number and reloads itself if the data is newer.
const FORMAT = 2;
const BUILT = new Date().toISOString();
const V5_MIN_AGREE = 0.997;
const OFFICIAL_MAX_GAP = 0.005;

const source = JSON.parse(readFileSync(join(ROOT, 'roll-source.json'), 'utf8'));
const seed = JSON.parse(readFileSync(join(ROOT, 'seed', 'ac-metadata.json'), 'utf8'));
const readJson = (p) => (existsSync(p) ? JSON.parse(readFileSync(p, 'utf8')) : null);
const shipped = readJson(join(rowsDir, 'manifest.json'));
const meta = new Map(seed.constituencies.map((c) => [c.acNumber, c]));
const official = readJson(join(ROOT, 'reference', 'ceo-final-2026.json'))?.acs ?? {};
for (const c of shipped?.constituencies ?? []) meta.set(c.acNumber, { ...meta.get(c.acNumber), ...c });

async function* rowsOf(path) {
  const rl = createInterface({ input: createReadStream(path).pipe(createGunzip()), crlfDelay: Infinity });
  for await (const line of rl) if (line) yield JSON.parse(line);
}

// One growable buffer per first hash byte keeps memory to ~10 bytes a row.
const groups = Array.from({ length: 256 }, () => ({ buf: Buffer.alloc(1 << 16), n: 0 }));
function push(g, rec) {
  if ((g.n + 1) * REC > g.buf.length) {
    const bigger = Buffer.alloc(g.buf.length * 2);
    g.buf.copy(bigger, 0, 0, g.n * REC);
    g.buf = bigger;
  }
  rec.copy(g.buf, g.n * REC);
  g.n++;
}

// -------------------------------------------------------- English cross-check
async function crossCheck(ac) {
  const engPath = join(rowsDir, `eng-${ac}.jsonl.gz`);
  if (!existsSync(engPath)) return null;
  const eng = new Map();
  let part = null;
  for await (const r of rowsOf(engPath)) {
    part = r.part;
    // Only the English roll's strongest readings witness: two different readers
    // agreeing outright (or its text layer), on a confirmed serial. Its fused
    // readings misread C as O often enough to hold a correct AC.
    if (r.epicOk && r.ok && (r.how === 'direct' || r.how === 'text')) eng.set(r.serial, r.epic);
  }
  return { part, eng };
}

const perAc = new Map();
const rowFiles = readdirSync(rowsDir).filter((f) => /^rows-\d+\.jsonl\.gz$/.test(f));
const rec = Buffer.alloc(REC);
for (const f of rowFiles) {
  const ac = Number(f.match(/\d+/)[0]);
  const sum = readJson(join(rowsDir, f.replace('.jsonl.gz', '.summary.json')));
  const ver = readJson(join(rowsDir, `verify-${ac}.json`));
  const xc = await crossCheck(ac);
  const stat = {
    status: !ver ? 'pending' : ver.verdict === 'pass' ? 'verified' : 'held',
    reasons: ver?.reasons ?? [], electors: 0, deleted: 0, approx: 0, withheld: 0, disputed: 0,
    cards: 0, liveCards: 0, printed: 0, partsRead: sum?.partsRead ?? 0,
    v5: xc ? { part: xc.part, compared: 0, agree: 0 } : null
  };
  for (const p of Object.values(sum?.perPart ?? {})) stat.printed += p.totals?.total ?? 0;
  const disputed = new Set((ver?.disputed ?? []).map(([p, pg, c]) => `${p}/${pg}/${c}`));
  // Deletion marks V3 found false (the part prints no deletions and holds exactly its total).
  const undeleted = new Set((ver?.undeleted ?? []).map(([p, pg, c]) => `${p}/${pg}/${c}`));
  const pending = [];
  for await (const r of rowsOf(join(rowsDir, f))) {
    if (r.deleted && undeleted.has(`${r.part}/${r.page}/${r.cell}`)) r.deleted = false;
    stat.cards++;
    if (!r.deleted) stat.liveCards++;
    if (!EPIC_RE.test(r.epic) || r.epicOk === false) { stat.withheld++; continue; }
    if (disputed.has(`${r.part}/${r.page}/${r.cell}`)) { stat.disputed++; continue; }
    if (xc && r.ok && r.part === xc.part && xc.eng.has(r.serial)) {
      stat.v5.compared++;
      if (xc.eng.get(r.serial) === r.epic) stat.v5.agree++;
      else { stat.disputed++; continue; }        // the English roll contradicts it
    }
    pending.push(r);
  }
  if (stat.v5 && stat.v5.compared >= 50 && stat.v5.agree / stat.v5.compared < V5_MIN_AGREE && stat.status === 'verified') {
    stat.status = 'held';
    stat.reasons.push(`English cross-check ${stat.v5.agree}/${stat.v5.compared} < ${V5_MIN_AGREE * 100}%`);
  }
  const want = official[ac]?.electors;
  if (want && stat.status === 'verified' && Math.abs(stat.liveCards - want) > OFFICIAL_MAX_GAP * want) {
    stat.status = 'held';
    stat.reasons.push(`${stat.liveCards} cards read, official count ${want}`);
  }
  if (stat.status === 'verified') {
    for (const r of pending) {
      const h = createHash('sha256').update(r.epic, 'utf8').digest();
      rec[0] = h[1];
      h.copy(rec, 1, 2, 6);
      rec.writeUInt8(r.ac, 5);
      rec.writeUInt16LE((r.part & 0x7fff) | (r.deleted ? 0x8000 : 0), 6);
      rec.writeUInt16LE((r.serial & 0x7fff) | (r.ok ? 0 : 0x8000), 8);
      push(groups[h[0]], rec);
      if (r.deleted) { stat.deleted++; continue; }
      stat.electors++;
      if (!r.ok) stat.approx++;
    }
  }
  perAc.set(ac, stat);
  console.log(`AC ${ac}: ${stat.status}${stat.reasons.length ? ' (' + stat.reasons.join('; ') + ')' : ''} — ` +
    `${stat.electors} published, ${stat.deleted} deleted, ${stat.withheld} unreadable, ${stat.disputed} disputed, ` +
    `${stat.cards}/${stat.printed || '?'} cards, ${stat.liveCards} live vs official ${want ?? '?'}` + (stat.v5 ? `, English ${stat.v5.agree}/${stat.v5.compared}` : ''));
}

// ------------------------------------------------------------------ write
rmSync(outDir, { recursive: true, force: true });
cpSync(join(ROOT, 'site'), outDir, { recursive: true });
// Pages lets browsers cache scripts for 10 minutes; a stale app.js reading new
// data showed a deleted card as a live one. Every build gets its own URLs.
const index = join(outDir, 'index.html');
writeFileSync(index, readFileSync(index, 'utf8').replace(/(src|href)="(app\.js|scenes\.js|styles\.css|fonts\.css)"/g,
  (_, attr, file) => `${attr}="${file}?v=${encodeURIComponent(BUILT)}"`));
const dataDir = join(outDir, 'data');
mkdirSync(join(dataDir, 'roll'), { recursive: true });
let records = 0, files = 0, dupes = 0;
for (let a = 0; a < 256; a++) {
  const g = groups[a];
  const idx = Array.from({ length: g.n }, (_, i) => i);
  // buf.compare(target, tStart, tEnd, sStart, sEnd) compares source x against target y.
  idx.sort((x, y) => g.buf.compare(g.buf, y * REC, y * REC + REC, x * REC, x * REC + REC));
  let i = 0;
  while (i < idx.length) {
    const b = g.buf[idx[i] * REC];
    const out = [];
    let prev = null;
    while (i < idx.length && g.buf[idx[i] * REC] === b) {
      const s = g.buf.subarray(idx[i] * REC + 1, idx[i] * REC + REC);
      if (prev && prev.equals(s)) dupes++; else { out.push(s); prev = s; }
      i++;
    }
    const ab = a.toString(16).padStart(2, '0');
    const cd = b.toString(16).padStart(2, '0');
    mkdirSync(join(dataDir, 'roll', ab), { recursive: true });
    writeFileSync(join(dataDir, 'roll', ab, `${cd}.bin`), Buffer.concat(out));
    records += out.length;
    files++;
  }
  groups[a] = null; // free as we go
}

const acs = [...meta.values()]
  .sort((x, y) => x.acNumber - y.acNumber)
  .map((c) => {
    const s = perAc.get(c.acNumber);
    const live = s?.status === 'verified';
    return {
      ac: c.acNumber, name: c.name, nameKn: c.nameKn, district: c.district, districtKn: c.districtKn,
      parts: c.parts, status: s?.status ?? 'pending',
      partsRead: live ? s.partsRead : 0,
      electors: live ? s.electors : 0, deleted: live ? s.deleted : 0, approx: live ? s.approx : 0,
      withheld: live ? s.withheld + s.disputed : 0,
      printed: s?.printed ?? 0,
      official: official[c.acNumber]?.electors ?? null
    };
  });
const parts = acs.reduce((n, a) => n + a.parts, 0);
const partsRead = acs.reduce((n, a) => n + a.partsRead, 0);
writeFileSync(join(dataDir, 'manifest.json'), JSON.stringify({
  rollType: shipped?.rollType ?? source.rollType,
  label: shipped?.label ?? source.label,
  labelKn: shipped?.labelKn ?? source.labelKn,
  url: shipped?.url ?? source.url,
  builtAt: BUILT,
  record: 9,
  format: FORMAT,
  electors: acs.reduce((n, a) => n + a.electors, 0),
  deleted: acs.reduce((n, a) => n + a.deleted, 0),
  parts, partsRead,
  coverage: parts ? partsRead / parts : 0,
  acs
}));
const n = (s) => acs.filter((a) => a.status === s).length;
console.log(`\n${records} records in ${files} buckets (${dupes} exact duplicates dropped); ` +
  `ACs verified ${n('verified')}, held ${n('held')}, pending ${n('pending')}; coverage ${partsRead}/${parts} parts`);
