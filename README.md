# Karnataka Final Roll 2026 — EPIC search

A voter types their EPIC number and gets their constituency, part and serial
number on the Karnataka electoral roll, with a link to the official ECI PDF of
their polling part. Unofficial; it reformats public data.

Successor to [Karnataka_Draft_Roll_2026](https://github.com/gouthamganeshm/Karnataka_Draft_Roll_2026),
rebuilt so a statewide import takes hours, not a week.

## How it works

```
home PC                         GitHub (draft release, private)        GitHub Actions                 GitHub Pages
fetch part PDF ─► cut crops ─►  crops-<ac>.tar  ─────────────────────► ocr.yml (1 job per AC) ─┐
(scripts/home/run.py)                                                    rows-<ac>.jsonl.gz ◄───┘
                                                                         publish.yml ─► hashed buckets ─► site
```

* **Home fetches.** The ECI CDN refuses GitHub's runners (`406` on every runner
  type, re-checked 2026-10-10), so PDFs are downloaded at home. Home only does
  the cheap half: cutting each card's serial box and EPIC (~11% of the CPU).
  PDFs are never written to disk.
* **Actions OCRs.** Tesseract (the expensive ~90%) runs one job per
  constituency, in parallel, as soon as that AC's crops arrive.
* **Same answers as the draft pipeline.** `scripts/ocr/test_crops.py` checks the
  split reproduces `roll_ocr.read_part_bytes` row for row. Crops are lossless
  grayscale; bilevel crops were tried and changed ~60% of readings.
* **Private transfer.** Crops and rows travel through a *draft* release, which
  only repo collaborators and the repo's workflows can see. Only hashed buckets
  are published.
* **Site fills in as it goes.** Each finished AC republishes the site. Until
  ≥99% of booths are loaded a miss reads "can't say yet", never "not found".

## Release day

1. Open one final-roll part PDF in a browser and note its URL. Put it in
   `roll-source.json` as `url` (with `{ac}` and `{part}`), and update
   `rollType`, `label`, `labelKn`, `release`. Commit and push.
2. `python scripts/home/run.py discover` — part counts per AC (~2 requests per
   AC when counts are unchanged from the draft).
3. `python scripts/home/run.py go` — fetch, cut, ship, dispatch. Resumable;
   re-run after any interruption. `status` shows progress.
4. Watch Actions. The site updates after every constituency.

Test run on a few parts: `python scripts/home/run.py go --ac 177,196 --limit 3`.

## Lookup

`SHA-256(EPIC)`: bytes 0–1 choose `data/roll/<ab>/<cd>.bin`, bytes 2–5 are
binary-searched in it. 9-byte records (`scripts/ci/build.mjs`): the whole state
is ~400 MB, inside Pages' 1 GB limit. The EPIC never leaves the visitor's device.

## Requirements (home)

Python 3.10+ with `pip install -r scripts/ocr/requirements.txt`, Node 20+,
the `gh` CLI logged in. Tesseract is only needed for local tests.
