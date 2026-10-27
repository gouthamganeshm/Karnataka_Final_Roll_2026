# Karnataka Final Roll 2026 — EPIC search

A voter types their EPIC number and gets their constituency, part and serial
number on the Karnataka electoral roll, with a link to the official ECI PDF of
their polling part. If the final roll strikes the EPIC off, the site says so
and where. Unofficial; it reformats public data.

**Site:** https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/

**Status:** the SIR final roll was published on 2026-10-27 (ECI roll
`S10-2026-SIR-FIR-1`: 224 ACs, 60,923 parts) and the statewide run is under way,
Bengaluru first. The site's coverage table shows which constituencies are
live; each goes up about an hour after its download finishes. Details are in
[PLAN.md](PLAN.md).

Successor to [Karnataka_Draft_Roll_2026](https://github.com/gouthamganeshm/Karnataka_Draft_Roll_2026),
rebuilt so a statewide import takes hours, not a week.

## How it works

```
home PC                            GitHub (draft release, private)   GitHub Actions                          GitHub Pages
fetch part PDF ─► cut crops ─►     crops-<ac>.tar ─────────────────► ocr.yml    12 shard jobs + merge
(scripts/home/roll_queue.py                                          verify.yml 12 shard jobs + verdict
 → run.py)                                                           publish.yml ─► hashed buckets ────────► site
```

* **Home fetches.** The ECI CDN refuses GitHub's runners (`406`), so PDFs are
  downloaded at home, Kannada roll only. Home does the cheap half: cutting
  each card's serial box and EPIC. PDFs are never written to disk, and each
  crop tar is deleted once uploaded. Each AC uploads while the next one
  downloads. The download (~20 parts/min, an 8 MB PDF each) is the bottleneck:
  it fills a ~30 Mbps home line, so more workers do not help. About two
  days for the state.
* **Actions OCRs, split twelve ways.** `ocr.yml` splits an AC's parts over 12
  parallel jobs (`ocr_ac.py --shard i/N`); a merge job joins them into exactly
  what one job writes (`ocr_ac.py merge`). A 600-part AC takes under 10 min
  instead of ~1.5 h.
* **Four readers per EPIC.** Tesseract on a contact sheet, a glyph-template
  reader for the fixed EPIC font, Tesseract on the crop alone, and a
  prototype reader with different features. A character is published only
  when independent readers agree; anything unsettled is withheld, never
  guessed. Details and measurements in [PLAN.md](PLAN.md).
* **A verifier before publishing, also split twelve ways.** The per-card checks
  run on every core in 12 parallel jobs: V1 re-reads every record, V4 confirms
  the letters of EPICs the draft roll does not have (keys from
  `draft-keys.yml`, hash fragments only). A verdict job then checks the whole
  AC (V2: serial order, duplicates, missing cards; V3: the part's printed
  totals and deletions), refuses unless the shards covered every part, and
  holds the AC if more than 3% of records are disputed or 0.5% of cards are
  missing. A held AC shows as "under review", never as "not found".
* **Private transfer.** Crops, rows and shard results travel through a
  *draft* release, which only repo collaborators and the repo's workflows can
  see; never through Actions artifacts, which anyone signed in can download
  on a public repo. Only hashed buckets are published.
* **Site fills in as it goes.** Each verified AC republishes the site. Until
  ≥99% of booths are loaded a miss reads "can't say yet", never "not found".

## What the final roll looks like (and how it is read)

The final roll is the draft's layout (image-only pages, 10×3 cards) plus
supplement sections, found on release day and handled in `scripts/ocr/`:

* **Deleted electors stay in the PDF.** The card keeps its serial, gets a
  diagonal DELETED stamp and a reason code left of the serial (E dead, S
  shifted, R repeated, M missing, Q disqualified). `#` in the same place means
  *modified*, still on the roll. `roll_ocr.serial_marker` tells `#` (by a
  template, `hash-mark.npy`) from any other mark, which counts as a deletion.
* **Deleted cards are published, flagged** (top bit of the record's part). The
  site says "Marked DELETED in the final roll" with AC, part, serial and the
  PDF; a voter who moved shows the live entry plus a note naming the deleted
  one. Deleted cards are never counted as electors.
* **Additions list.** Added electors come after the main list, continuing the
  serial run, with a second box after the serial ("868 | 7"); the serial is
  read from the first box only. Their serial box is narrower, so a deletion
  code there sits ~10 px from the number instead of 130+.
* **Printed totals are net of deletions.** `totals.py` reads the deletion
  count from the cover (Ending − Starting + 1 − Total) and the summary page
  (rows I + II − III = net). V3 requires live cards = net total and detected =
  printed deletions; if not, every record of the part is disputed, so an
  unmarked deletion can never go out as a live elector.
* **A page with one lone card** (the end of a section) is cut too.

## Running it

The home stage runs unattended:

```
python scripts/home/run.py discover        # part counts per AC (cache/manifest.json)
python scripts/home/roll_queue.py          # every AC, Bengaluru first, Kannada only
```

`roll_queue.py` runs `run.py go --tranche all --no-eng --workers 6` and
restarts it after any crash until every AC is shipped; only one copy runs at a
time. A Windows Task Scheduler task, **Karnataka Final Roll queue**, starts it
at logon, so a reboot resumes where it stopped. Logs: `cache/queue.log` and
`cache/queue-run.log`. `python scripts/home/run.py status` shows what is on
the release.

Everything after the upload is on Actions: `run.py` dispatches `ocr.yml` per
AC, which dispatches `verify.yml`, which dispatches `publish.yml`.

**If something breaks:** finished ACs are in
`cache/shipped-<release>.json` and are skipped on re-run. Re-run one AC's OCR
with `gh workflow run ocr.yml -f ac=N -f tag=<release>` (needs its crop tar on
the release), or re-ship it with `run.py go --ac N --force`. `shards` is an
input of both `ocr.yml` and `verify.yml` (default 12, at most 20: GitHub's
free plan runs 20 jobs at once). If ECI throttles, lower
`--workers` (never above 8).

## Privacy

There is no server. Search happens in the browser: `SHA-256(EPIC)` bytes 0–1
choose `data/roll/<ab>/<cd>.bin` (one of 65,536 files, each shared by ~27 lakh
possible EPICs), bytes 2–5 are binary-searched in it. The EPIC is never sent
anywhere or put in the URL. No cookies, analytics or logs; the browser keeps
only the language, theme and scenes seen. Fonts are self-hosted, so the page
requests nothing from any third party; GitHub, as the host, sees visitors' IPs.
The page carries the same explanation in Kannada and English.

Records are 9 bytes (`scripts/ci/build.mjs`): hash suffix, AC, part (top bit:
deleted), serial (top bit: serial not OCR-confirmed). The whole state is
~400 MB, inside Pages' 1 GB limit. Script URLs carry the build time and the
manifest a record format, so a cached page never misreads newer data.

## Layout

| Path | What it is |
|---|---|
| `roll-source.json` | The one place the roll's URL, label and release tag are set |
| `scripts/home/run.py` | Home: discover, fetch, cut, upload, dispatch OCR |
| `scripts/home/roll_queue.py` | Unattended, single-instance queue over `run.py go` |
| `scripts/ocr/` | Crop cutting, the EPIC readers, deletion marks, printed totals, tests |
| `scripts/ci/` | Actions: OCR per AC (sharded), verifier (sharded), draft-roll keys, site build |
| `scripts/release.py` | Draft-release helper (refuses to use a published release) |
| `.github/workflows/` | `ocr.yml`, `verify.yml`, `publish.yml`, `draft-keys.yml` |
| `site/` | The search page (Kannada and English, light and dark, self-hosted fonts) |

## Requirements (home)

Python 3.10+ with `pip install -r scripts/ocr/requirements.txt` and the `gh`
CLI logged in. Tesseract is only needed for local tests, and Node 20+ only to
build the site locally.
