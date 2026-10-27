# Karnataka Final Roll 2026 — EPIC search

A voter types their EPIC number and gets their constituency, part and serial
number on the Karnataka electoral roll, with a link to the official ECI PDF of
their polling part. Unofficial; it reformats public data.

**Site:** https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/

**Status:** ready, waiting for the final roll to be published. The pipeline
has run end to end on Actions with sample parts from the draft roll: 11 parts
from 9 ACs, 7,457 of 7,466 cards published, none disputed, and the printed
totals matched on every part. The first full-size constituency runs as the
release-day pilot. Details are in [PLAN.md](PLAN.md).

Successor to [Karnataka_Draft_Roll_2026](https://github.com/gouthamganeshm/Karnataka_Draft_Roll_2026),
rebuilt so a statewide import takes hours, not a week.

## How it works

```
home PC                          GitHub (draft release, private)    GitHub Actions                       GitHub Pages
fetch part PDF ─► cut crops ─►   crops-<ac>.tar  ─────────────────► ocr.yml    (1 job per AC)
(scripts/home/run.py)                                                verify.yml (checks every record)
                                                                     publish.yml ─► hashed buckets ─────► site
```

* **Home fetches.** The ECI CDN refuses GitHub's runners (`406` on every runner
  type, re-checked 2026-10-10), so PDFs are downloaded at home. Home only does
  the cheap half: cutting each card's serial box and EPIC (~1.5 s of CPU per
  part). PDFs are never written to disk. Each AC uploads while the next one
  downloads.
* **Actions OCRs.** Tesseract (the expensive part, ~38 s per part per core)
  runs one job per constituency, in parallel, as soon as that AC's crops
  arrive.
* **Four readers per EPIC.** Tesseract on a contact sheet, a glyph-template
  reader for the fixed EPIC font, Tesseract on the crop alone, and a
  prototype reader with different features. A character is published only
  when independent readers agree; anything unsettled is withheld, never
  guessed. Details and measurements in [PLAN.md](PLAN.md).
* **A verifier before publishing.** `verify.yml` re-reads every record and
  checks serial order, duplicates and the part's printed elector total. It
  also looks each EPIC up in the draft roll (keys exported once by
  `draft-keys.yml`, hash fragments only) and compares one English-roll part
  per AC. A constituency goes public only when it passes; otherwise it shows
  as "under review".
* **Cut stage matches the draft pipeline.** `scripts/ocr/test_crops.py`
  checks the split reproduces `roll_ocr.read_part_bytes` row for row. Crops
  are lossless grayscale; bilevel crops were tried and changed ~60% of
  readings.
* **Private transfer.** Crops and rows travel through a *draft* release, which
  only repo collaborators and the repo's workflows can see. Only hashed buckets
  are published.
* **Site fills in as it goes.** Each finished AC republishes the site. Until
  ≥99% of booths are loaded a miss reads "can't say yet", never "not found".

## Release day

The full runbook is in [PLAN.md](PLAN.md) §7. In short:

1. Open three final-roll part PDFs in a browser (one Bengaluru, one large
   rural, one small) and check the URL scheme and card layout. Run
   `scripts/ocr/test_crops.py` and `scripts/ocr/evaluate.py` on them.
2. Put the URL in `roll-source.json` as `url` (with `{ac}` and `{part}`), and
   update `rollType`, `label`, `labelKn` and `release`. Commit and push.
3. `python scripts/home/run.py discover` — part counts per AC.
4. `python scripts/home/run.py go --ac 162` — the pilot. Check it, then
   `python scripts/home/run.py go --tranche blr` (the 28 Bengaluru ACs) and
   `go --tranche rest`. Resumable; re-run after any interruption. `status`
   shows progress.
5. Watch Actions. The site updates after every verified constituency.

On the current home line (~22 Mbps down) Bengaluru takes ~8 h and the whole
state ~55 h; the download is the bottleneck.

If the Kannada roll is out before the English one, nothing changes: the
Kannada roll is what gets published, and the English part per AC (only a
cross-check) is skipped and fetched later with `run.py eng-audit`.

**If something breaks:** `run.py go` skips ACs already in
`cache/shipped-<release>.json`. Re-run one AC's OCR with
`gh workflow run ocr.yml -f ac=N -f tag=<release>`, or re-ship it with
`run.py go --ac N --force`. If ECI throttles, lower `--workers` (default 4,
never above 8).

## Lookup

`SHA-256(EPIC)`: bytes 0–1 choose `data/roll/<ab>/<cd>.bin`, bytes 2–5 are
binary-searched in it. 9-byte records (`scripts/ci/build.mjs`): the whole state
is ~400 MB, inside Pages' 1 GB limit. The EPIC never leaves the visitor's device.

## Layout

| Path | What it is |
|---|---|
| `roll-source.json` | The one place the roll's URL, label and release tag are set |
| `scripts/home/run.py` | Home: discover, fetch, cut, upload, dispatch OCR |
| `scripts/ocr/` | Crop cutting and the EPIC readers, plus their tests |
| `scripts/ci/` | Actions: OCR per AC, verifier, draft-roll keys, site build |
| `scripts/release.py` | Draft-release helper (refuses to use a published release) |
| `.github/workflows/` | `ocr.yml`, `verify.yml`, `publish.yml`, `draft-keys.yml` |
| `site/` | The search page (Kannada and English, light and dark) |

## Requirements (home)

Python 3.10+ with `pip install -r scripts/ocr/requirements.txt` and the `gh`
CLI logged in. Tesseract is only needed for local tests, and Node 20+ only to
build the site locally.
