# Final roll — extraction & publishing plan

Status: **paused 2026-10-10, waiting for the final roll link.** Everything in
"Built and tested" works today against the draft roll. "Build before release"
is the work still to do so the run on release day is push-button.

---

## 1. Targets

| Target | Definition | How it is measured |
|---|---|---|
| **Accuracy ≥ 99.9%** | Of the records the site *publishes*, ≥ 99.9% have the right EPIC → AC, part, serial | Verifier worker (§4) on every record, plus a 3,000-record hand-checked audit: 0 errors in 3,000 bounds the error rate below 0.1% at 95% confidence |
| Coverage ≥ 98% | Share of elector cards that get published | Per-AC manifest. A card that can't be settled is withheld, never guessed |
| Bengaluru first | All 28 Bengaluru ACs live before the rest of the state | Run order (§3) |
| Speed | Bengaluru in ~9 h, whole state in ~55 h, on the current home line | Download-bound (§6) |

A withheld card makes the voter see "not found — check with 1950". A wrong
card can make them think they're registered somewhere they're not. So when
coverage and accuracy conflict, accuracy wins.

---

## 2. Built and tested (2026-10-10)

* **Repo** `gouthamganeshm/Karnataka_Final_Roll_2026` (public).
  **Local** `C:\Personal_Projects\karnataka-final-roll`.
  **Site** https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/
* **Flow:** home PC fetches each part PDF and cuts the card crops
  (`scripts/home/run.py`) → crop tar uploaded to a **draft** GitHub Release,
  which only the repo owner and its workflows can see → `ocr.yml` runs one Actions job per AC
  → `publish.yml` rebuilds hashed buckets and deploys Pages after every AC.
* **Why home fetches:** the ECI CDN answers every GitHub-hosted runner with
  `406`. This was re-tested 2026-10-10 on ubuntu, ubuntu-arm, windows and macos.
  Proxy, VPN and CDN-bypass workarounds were ruled out on purpose. Don't
  revisit them.
* **R2 is not used.** It is shared with the kgk-website.
* **EPIC reading** (`scripts/ocr/crops.py`): three readers are combined
  character by character.
  * Tesseract reads the page's contact sheet.
  * A glyph-template reader matches against the fixed EPIC font
    (`glyphs.py`, `templates.npz`, learned from 1 part × 224 ACs).
  * Tesseract reads the crop on its own, but only when the first two disagree.

  Letters follow the glyph reader. Digits need 2 of 3 readers to agree. An
  unsettled character withholds the EPIC.
* **Measured on 79,569 held-out cards:**
  * 98.1% published.
  * 1,364 cards where both Tesseract passes agreed on a *wrong* EPIC were
    corrected.
  * ~100 corrections were checked by eye and all were right.
  * The draft-site method differs from the new reading on 3.7% of the EPICs it
    published. In other words, the draft site likely has ~3% wrong EPICs.
* **End to end on Actions:** AC 177 and AC 196, 3 parts each. Fetched at home,
  OCR'd on Actions, published. `AAH4480430` → AC 177 / part 3 / serial 1 is
  live. Tesseract 5.3.4 on Actions vs 5.4 locally changed only *withheld vs
  published*, never a published EPIC.
* **Site:** Kannada and English, dark mode, binary hash buckets (~400 MB
  statewide). Each result links to the official ECI PDF. Until ≥ 99% of booths
  are loaded, a miss reads "can't say yet".

---

## 3. Run order

**Tranche 1 — Bengaluru, 28 ACs, ~9,000 parts, ~8 h download.**
Largest first:

176 Bangalore South (605) · 153 Yeshwanthapura (553) · 174 Mahadevapura (533) ·
151 K.R. Pura (509) · 152 Byatarayanapura (442) · 154 Rajarajeshwarinagar (437) ·
155 Dasarahalli (419) · 150 Yelahanka (418) · 175 Bommanahalli (390) ·
177 Anekal (384) · 160 Sarvagnanagar (337) · 158 Hebbal (285) ·
167 Vijayanagar (284) · 171 Padmanabanagar (279) · 156 Mahalakshmi Layout (276) ·
166 Govindarajanagar (269) · 161 C.V. Raman Nagar (244) · 172 B.T.M Layout (243) ·
159 Pulakeshinagar (228) · 169 Chickpet (222) · 164 Gandhinagar (220) ·
170 Basavanagudi (220) · 168 Chamrajapet (216) · 173 Jayanagar (210) ·
157 Malleshwaram (207) · 165 Rajajinagar (194) · 163 Shantinagar (193) ·
162 Shivajinagar (191)

(Part counts are the draft roll's. `discover` re-counts them for the final roll.)

**Tranche 2 — the other 196 ACs, largest first.** Starts with
215 Chamundeshwari (351), 197 Holenarasipur (330), 36 Shorapur (325),
24 Bagalkot (319), 14 Khanapur (319) …

| Milestone | Cumulative download (at ~2.75 MB/s) |
|---|---|
| Bengaluru complete | ~8 h |
| + 25 largest ACs elsewhere | ~15 h |
| + 50 | ~21 h |
| + 100 | ~34 h |
| Whole state (60,923 parts, ~540 GB) | ~55 h |

Each AC goes public once its OCR **and verification** pass (§4). That's
roughly 1–2 h after its download finishes. The site fills in AC by AC.

---

## 4. Accuracy: the verifier worker

A separate Actions job, `verify.yml`, runs per AC after OCR and before that AC
is allowed onto the site. Every record gets a status: **verified**,
**disputed** (withheld and queued for review) or **failed AC** (the whole AC is
held).

| Check | What it does | On failure |
|---|---|---|
| **V1 Independent re-read** | Re-reads every published EPIC crop with settings the main pass didn't use. The glyph reader is forced through its touching-glyph segmentation. Tesseract runs `--psm 13` at a different upscale. At least one must reproduce the published EPIC exactly. | Record → disputed |
| **V2 Structure** | Within each part: serials form the fitted run with no duplicates, and the card count matches the page grid (30 per page, last page partial). Within each AC: no EPIC appears twice. | Records involved → disputed |
| **V3 Part totals** | Reads the elector total printed in each part's summary and requires published + withheld = printed total. *Whether the final-roll PDF carries a readable total is to be checked on the draft before release (build item G).* | Part → failed until explained |
| **V4 Draft corroboration** | Checks whether the EPIC's hash already exists in the draft roll for the same AC. Most electors carry over, so "corroborated" is independent evidence. Records *not* corroborated (new or moved electors, or a misread) must have all three readers agree on every character. | Uncorroborated record that isn't unanimous → disputed |
| **V5 English-roll cross-check** | Home also fetches the **ENG** PDF of one random part per AC (~224 PDFs, ~2 GB, ~12 min). That's a separately rendered copy of the same cards, read independently. Every KAN record in that part is compared, EPIC and serial. | AC disagreement > 0.1% → AC held, investigated |
| **V6 Hand-checked audit** | Each day, 3,000 random published records are drawn as crop sheets with the published EPIC and serial and checked by eye. | Any error → root cause, fix, re-run affected ACs |

**Publish gate, per AC:** V2 and V3 clean (after demotions), V5 ≥ 99.9%
agreement, and disputed ≤ 2% of cards. An AC that fails stays off the site and
appears as "not loaded yet". It never appears as "not found".

**Serials** are shown with "~" when the sequence fit couldn't confirm them.
V2, V5 and V6 check serials as well as EPICs.

---

## 5. Build before release (in order)

| # | Item | Effort |
|---|---|---|
| A | Run order in `run.py`: Bengaluru tranche first, then largest first; `--tranche blr\|rest` flag | 15 min |
| B | Text-layer check: if the final-roll PDFs carry real text, read it directly (exact, no OCR) and keep OCR as fallback | 1–2 h, only if needed |
| C | `verify.yml` + `scripts/ci/verify_ac.py` (V1, V2, V4), chained after `ocr.yml` | ½ day |
| D | Draft-roll hash set for V4: export the draft site's buckets once into a release asset | 1 h |
| E | ENG cross-check (V5): home fetches 1 ENG part per AC; CI compares | 2–3 h |
| F | **Ground truth:** hand-verify 3,000 cards from the 224-part draft sample. Tune `LETTER_MARGIN` / `DIGIT_*` so that set shows 0 errors before day one | 3–4 h |
| G | Part totals (V3): find the printed total in the roll layout; implement if readable | 1–3 h |
| H | Publish gate in `build.mjs`: only verified ACs; manifest carries per-AC verified status; site shows it | 1 h |
| I | Load test: 2 full Bengaluru ACs end to end (~900 parts) to measure real throughput, upload speed and Actions concurrency | 2 h wall |
| J | Phone-width check of the site; delete `gouthamganeshm/eci-cdn-probe` | 15 min |

---

## 6. Release-day runbook

**Before:** PC on mains power, sleep and hibernate off, ≥ 5 GB free disk (one
AC's crop tar is up to ~1 GB), no other heavy downloads. `gh auth status` OK.

| Step | Action | Check / go-no-go | Time |
|---|---|---|---|
| 0 | You share the final-roll link | — | — |
| 1 | Open 3 part PDFs (one Bengaluru, one large rural, one small) | Same URL scheme? Text layer (→ item B)? Same 10×3 card grid, EPIC position, resolution? | 15 min |
| 2 | Calibrate: run `test_crops.py` and the reading evaluation on those 3 parts; eye-check every withheld or changed card | 0 wrong published EPICs on the 3 parts; otherwise retune first | 30 min |
| 3 | Edit `roll-source.json`: `url`, `rollType` (e.g. `S10-2026-FR`), `label` "Final Roll 2026" / Kannada, `release` `crops-S10-2026-FR`. Commit and push | The new release tag means draft test data never mixes in | 5 min |
| 4 | `python scripts/home/run.py discover` | Part counts for 224 ACs; compare with the draft (changes expected in Bengaluru) | ~10 min |
| 5 | **Pilot:** `run.py go --ac 162` (Shivajinagar, ~190 parts) | OCR + verify green; 300-record hand audit 0 errors; search works on the site | ~45 min |
| 6 | `run.py go --tranche blr` | `run.py status` every hour; Actions all green | ~8 h |
| 7 | Bengaluru audit: 3,000 records (V6) | 0 errors → announce Bengaluru | 1 h |
| 8 | `run.py go --tranche rest` | Same monitoring. Daily V6 audit | ~47 h |
| 9 | Final: coverage ≥ 98%, all ACs verified, the "not found" wording becomes final | Announce the state | — |

**If something breaks:** `run.py go` resumes on re-run, because finished ACs
are in `cache/shipped.json`. Re-running one AC's OCR:
`gh workflow run ocr.yml -f ac=N -f tag=<release>`. A bad publish rolls back
by re-running the previous `publish.yml` run. ECI throttling or errors: lower
`--workers` (default 4), never raise it past 8.

---

## 7. Speed levers (measured 2026-10-10)

* Home download: **21–24 Mbps**, measured against both ECI and neutral test
  servers, so this is the line itself, not ECI. Average part 8.9 MB.
* Actions OCR: ~38 s per part per core. 20 parallel jobs × 4 cores keep pace
  with any home line up to ~300 Mbps.
* Upload of crops: ~15% of PDF bytes (~80 GB statewide). It runs alongside the
  download, and the upload is smaller than the download, so it isn't the limit.
* **The only big lever is a faster line.** At ~300 Mbps the whole state takes
  ~4–5 h, and Bengaluru takes under an hour.

---

## 8. Unknowns until the link is live

* Same URL scheme and filename pattern? (`roll-source.json` is the only place
  to change.)
* Same image-only PDF and card layout? If the PDF has a text layer, accuracy
  becomes trivial (item B).
* Final part counts. Bengaluru may grow.
* Whether summary totals are printed and readable (item G).

## 9. Decisions on record

* Home fetch + Actions OCR + draft-release transfer + GitHub Pages.
* No proxy, VPN or CDN-bypass to reach ECI from the cloud.
* No R2 for this project.
* Accuracy over coverage: withhold rather than guess.
* Only hashed EPIC fragments are public. Plaintext rows live only in the draft
  release.
