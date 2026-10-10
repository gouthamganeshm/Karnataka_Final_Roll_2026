/* Build the public site: OCR rows -> hashed binary buckets + manifest.
 *
 *   node scripts/ci/build.mjs <rows-dir> <out-dir>
 *
 * <rows-dir> holds rows-<ac>.jsonl.gz, rows-<ac>.summary.json and (optionally)
 * manifest.json from the draft release. <out-dir> gets a copy of site/ plus:
 *
 *   data/manifest.json       roll label, coverage, per-AC counts and names
 *   data/roll/ab/cd.bin      every record whose SHA-256(EPIC) starts with abcd
 *
 * A record is 9 bytes, sorted by suffix so the browser can binary-search a
 * bucket. The suffix is raw hash bytes (compare big-endian); the rest is
 * little-endian:
 *
 *   4 bytes      suffix: bytes 2..5 of SHA-256(EPIC)
 *   u8  ac
 *   u16 part
 *   u16 serial   top bit set = serial not OCR-confirmed (EPIC itself is fine)
 *
 * No EPIC is published, only a hash fragment — the browser already knows the
 * number the visitor typed. 4.4 crore electors at 9 bytes is ~400 MB, inside
 * GitHub Pages' 1 GB site limit, where the draft site's JSON would not be.
 *
 * Acceptance is the draft project's rule: a row needs a well-formed EPIC;
 * `ok` only decides the approximate-serial flag.
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

const source = JSON.parse(readFileSync(join(ROOT, 'roll-source.json'), 'utf8'));
const seed = JSON.parse(readFileSync(join(ROOT, 'seed', 'ac-metadata.json'), 'utf8'));
const shipped = existsSync(join(rowsDir, 'manifest.json'))
  ? JSON.parse(readFileSync(join(rowsDir, 'manifest.json'), 'utf8'))
  : null;
const meta = new Map(seed.constituencies.map((c) => [c.acNumber, c]));
for (const c of shipped?.constituencies ?? []) meta.set(c.acNumber, { ...meta.get(c.acNumber), ...c });

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

const perAc = new Map();
const rowFiles = readdirSync(rowsDir).filter((f) => /^rows-\d+\.jsonl\.gz$/.test(f));
const rec = Buffer.alloc(REC);
for (const f of rowFiles) {
  const ac = Number(f.match(/\d+/)[0]);
  const stat = { electors: 0, approx: 0, unreadable: 0 };
  const rl = createInterface({ input: createReadStream(join(rowsDir, f)).pipe(createGunzip()), crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line) continue;
    const r = JSON.parse(line);
    if (!EPIC_RE.test(r.epic)) { stat.unreadable++; continue; }
    const h = createHash('sha256').update(r.epic, 'utf8').digest();
    rec[0] = h[1];
    h.copy(rec, 1, 2, 6);
    rec.writeUInt8(r.ac, 5);
    rec.writeUInt16LE(r.part, 6);
    rec.writeUInt16LE((r.serial & 0x7fff) | (r.ok ? 0 : 0x8000), 8);
    push(groups[h[0]], rec);
    stat.electors++;
    if (!r.ok) stat.approx++;
  }
  const sumPath = join(rowsDir, f.replace('.jsonl.gz', '.summary.json'));
  const sum = existsSync(sumPath) ? JSON.parse(readFileSync(sumPath, 'utf8')) : null;
  perAc.set(ac, { ...stat, partsRead: sum?.partsRead ?? 0, unread: sum?.unread ?? [] });
  console.log(`AC ${ac}: ${stat.electors} electors (${stat.approx} approximate serial, ${stat.unreadable} unreadable)`);
}

// ------------------------------------------------------------------ write
rmSync(outDir, { recursive: true, force: true });
cpSync(join(ROOT, 'site'), outDir, { recursive: true });
const dataDir = join(outDir, 'data');
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
    return {
      ac: c.acNumber, name: c.name, nameKn: c.nameKn, district: c.district,
      parts: c.parts, partsRead: s?.partsRead ?? 0,
      electors: s?.electors ?? 0, approx: s?.approx ?? 0, unreadable: s?.unreadable ?? 0
    };
  });
const parts = acs.reduce((n, a) => n + a.parts, 0);
const partsRead = acs.reduce((n, a) => n + a.partsRead, 0);
writeFileSync(join(dataDir, 'manifest.json'), JSON.stringify({
  rollType: shipped?.rollType ?? source.rollType,
  label: shipped?.label ?? source.label,
  labelKn: shipped?.labelKn ?? source.labelKn,
  url: shipped?.url ?? source.url,
  builtAt: new Date().toISOString(),
  record: 9,
  electors: records,
  parts, partsRead,
  coverage: parts ? partsRead / parts : 0,
  acs
}));
console.log(`\n${records} records in ${files} buckets (${dupes} exact duplicates dropped); ` +
  `coverage ${partsRead}/${parts} parts`);
