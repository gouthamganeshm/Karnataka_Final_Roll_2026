# Final roll — extraction & publishing plan

Status: **ready, waiting for the final roll link (2026-10-10).** Build items
A–J are done (§5). The one thing not yet run is a full-size constituency
end to end, which happens as the release-day pilot (§7 step 5).

---

## 1. Targets

| Target | Definition | How it is measured |
|---|---|---|
| **Accuracy ≥ 99.9%** | Of the records the site *publishes*, ≥ 99.9% have the right EPIC → AC, part, serial | Verifier worker (§4) on every record; an independent reading of the English roll; a daily hand-checked audit |
| Coverage ≥ 98% | Share of elector cards that get published | Per-AC manifest. A card that can't be settled is withheld, never guessed |
| Bengaluru first | All 28 Bengaluru ACs live before the rest of the state | Run order (§3) |
| Speed | Bengaluru in ~8 h, whole state in ~55 h, on the current home line | Download-bound (§8) |

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
  which only the repo owner and its workflows can see → `ocr.yml` runs one
  Actions job per AC → `verify.yml` checks every record (§4) →
  `publish.yml` rebuilds the hashed buckets and deploys Pages. An AC goes
  public only once it is verified.
* **Why home fetches:** the ECI CDN answers every GitHub-hosted runner with
  `406`. This was re-tested 2026-10-10 on ubuntu, ubuntu-arm, windows and macos.
  Proxy, VPN and CDN-bypass workarounds were ruled out on purpose. Don't
  revisit them.
* **R2 is not used.** It is shared with the kgk-website.
* **EPIC reading** (`scripts/ocr/crops.py`, `glyphs.py`): four readers, combined
  character by character.
  1. Tesseract reads the page's contact sheet.
  2. A glyph-template reader matches the fixed EPIC font. O/Q and 6/8, which
     the templates can't separate at ~13 px, are settled by the one stroke
     that differs (Q's tail, 8's closed upper loop).
  3. Tesseract reads the crop on its own, when 1 and 2 disagree.
  4. A prototype reader with different features (k-means prototypes on a
     line-preserving glyph view). Where glyphs touch, it chooses its own cut,
     so it is an independent witness exactly where one is needed.

  A letter needs two readers to agree; digits need two of the votes. Two
  guards came out of the English-roll check below: a Tesseract reading whose
  letters are shifted (an extra glyph read at the start) gets no vote, and on
  touching glyphs the template and prototype readers only count as two
  witnesses when each chose its own cut. Anything unsettled is withheld.
* **If the PDF has a text layer** (the draft roll has none), its EPIC is used
  when an OCR reader confirms it.
* **Measured on held-out data:** 112 parts, 79,569 cards, read with templates
  and prototypes learned only from the *other* 112 sample parts.
  * **99.68% published**, 0.25% withheld by the readers, 0.07% disputed by the
    verifier's re-read (V1).
  * **Independent check — the English roll.** 56 of those parts were also
    downloaded in English, a separately rendered copy of the same cards, and
    read with their own English templates. Where two English readers agree
    outright, they match the published Kannada EPIC on **37,230 of 37,230**
    cards. The 161 cards where only a fused English reading differed were
    checked by eye: every one was an English misread (J→U, C→O, S→G, T→I).
  * The 1,267 hardest published cards in the other 56 parts (where readers
    overruled each other) were checked by eye per series: all correct.
  * Earlier rules had published **14 wrong EPICs** among these cards (13 in one
    part, `IQG…` as `IQQ…`; one `FLV…` as `FIW…`). Both causes are fixed and
    those cards are now withheld.
  * 0 errors in 37,230 independently confirmed records bounds the error rate
    below 0.01% at 95% confidence, well inside the 99.9% target.
  * The draft-site method differs from the new reading on 3.7% of the EPICs it
    published. In other words, the draft site likely has ~3% wrong EPICs.
* **Printed totals (V3):** each part's cover table and last-page summary are
  read; a reading is used only if Male + Female + Third gender = Total. Read
  on 28 of 28 sample parts, and equal to the cards read on all 28.
* **End to end on Actions (2026-10-10):** 11 sample parts from 9 ACs (7 in
  Bengaluru), cut and shipped from home in ~1 min; OCR, verify and publish
  green for every AC. 7,457 of 7,466 cards published, 0 disputed, printed
  totals matched on all 11 parts. V4: 1,338 of AC 177's 1,353 records are in
  the draft roll; the prototype reader confirmed the other 15. V5: AC 177's
  English part agreed 576 of 576. Search checked on the live site at phone
  width (390 and 360 px, light and dark).
* **Site:** Kannada and English, dark mode, binary hash buckets (~400 MB
  statewide). Each result links to the official ECI PDF. A constituency shows
  as "processing" until verified and "under review" if held. Until ≥ 99% of
  booths are loaded, a miss reads "can't say yet".

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

Each AC goes public once its OCR **and verification** pass (§4), roughly
1–2 h after its download finishes. The site fills in AC by AC.

---

## 4. Accuracy: the verifier worker

`verify.yml` (`scripts/ci/verify_ac.py`) runs per AC after OCR and before the
AC may be published. Every record ends up **verified**, **disputed**
(withheld) or in a **held AC** (the whole AC stays off the site).

| Check | What it does | On failure |
|---|---|---|
| **V1 Independent re-read** | The prototype reader re-reads every published EPIC (on its own cut where glyphs touch). Where it differs, Tesseract `--psm 13` at a different scale must support each differing character. | Record → disputed |
| **V2 Structure** | Within each part: serials strictly increase and none repeats; no card is missing before a page's last card. Within each AC: no EPIC twice unless every copy was read outright by two readers. | Records → disputed; missing cards count toward the hold |
| **V3 Printed totals** | The part's cover table (start serial, end serial, male, female, third gender, total) and last-page summary, used only when the sum checks. Cards read must equal the total, and the last serial must equal the printed end. | Part flagged; missing cards count toward the hold |
| **V4 Draft corroboration** | Is the EPIC's hash in the draft roll for the same AC? Most electors carry over, so that is independent evidence. Records the draft doesn't have (new, moved, or misread) need the prototype reader to agree on all three letters. Keys come from `draft-keys.yml` (release `ref-draft-roll`, hash fragments only). | Record → disputed |
| **V5 English cross-check** | Home fetches the **ENG** PDF of one random part per AC. Its records where two English readers agree outright are compared with the Kannada ones, serial by serial (confirmed serials only). Runs in `publish.yml`, whichever finishes first. | Contradicted record → withheld; AC below 99.7% agreement (≥ 50 compared) → held |
| **V6 Hand-checked audit** | `audit-<ac>.png`: 15 random verified records per AC with EPIC and serial, plus `review-<ac>.png` with the disputed ones, uploaded to the draft release. Checked by eye daily. | Any error → root cause, fix, re-run affected ACs |

**Publish gate, per AC:** verifier verdict *pass* (disputed ≤ 3% of
published records, missing cards ≤ 0.5% of the printed total) and V5 ≥ 99.7%
when it has run. An AC that fails stays off the site and shows as "under
review". It never shows as "not found".

**Serials** are shown with "~" when the sequence fit couldn't confirm them.

---

## 5. Build items

| # | Item | Status |
|---|---|---|
| A | Run order: Bengaluru first, then largest first; `--tranche blr\|rest` | Done |
| B | Text layer: use the PDF's own text if the final roll has it, OCR-confirmed | Done (the draft has none, so untested on real text) |
| C | `verify.yml` + `verify_ac.py` (V1, V2, V3, V4) chained after `ocr.yml` | Done |
| D | Draft-roll hash keys for V4 (`draft-keys.yml` → release `ref-draft-roll`) | Done |
| E | English cross-check (V5); safe when the English roll comes later (§6) | Done |
| F | Ground truth for accuracy | Done — English-roll witness and eye checks (§2) instead of tuning on a hand-labelled set |
| G | Printed totals (V3) | Done |
| H | Publish gate in `build.mjs`; per-AC status in the manifest and on the site | Done |
| I | End-to-end on Actions | Done on 11 sample parts from 9 ACs (§2). A full-size AC runs as the release-day pilot |
| J | Phone-width check of the site. Keep `gouthamganeshm/eci-cdn-probe` | Done |

Also done: home now uploads each AC while the next one downloads, and the cut
takes ~1.5 s of CPU per part (was ~6 s), so home is never the bottleneck
below ~150 Mbps.

---

## 6. If the Kannada roll comes first

The Kannada roll is what gets published; the English roll is only V5's
witness. So the run is the same:

* `run.py go` tries one English part per AC; when it isn't published it logs
  "not available — V5 later via eng-audit" and moves on. `--no-eng` skips even
  the attempt.
* ACs publish on V1–V4. The gate does not wait for V5.
* When the English roll appears: `run.py eng-audit` ships one English part per
  AC. Each republish runs V5; an AC below 99.7% agreement drops to "under
  review" automatically.
* If the English URL isn't the Kannada one with `-KAN-` → `-ENG-`, set
  `urlEng` in `roll-source.json`.

If the English roll came first instead, the pipeline would need the English
templates promoted to the main reading (`run.py` and `ocr.yml` with
`kind=eng`), and the English reader's letter confusions fixed first. Not
expected; not prepared.

---

## 7. Release-day runbook

**Before:** PC on mains power, sleep and hibernate off, ≥ 5 GB free disk (two
crop tars of up to ~1 GB can wait for upload), no other heavy downloads.
`gh auth status` OK.

| Step | Action | Check / go-no-go | Time |
|---|---|---|---|
| 0 | You share the final-roll link | — | — |
| 1 | Open 3 part PDFs (one Bengaluru, one large rural, one small) | Same URL scheme? Text layer (→ item B)? Same 10×3 card grid, EPIC position, resolution? | 15 min |
| 2 | Calibrate: `test_crops.py` and `evaluate.py` on those 3 parts; eye-check every withheld or changed card | 0 wrong published EPICs; otherwise retune first | 30 min |
| 3 | Edit `roll-source.json`: `url`, `rollType` (e.g. `S10-2026-FR`), `label` "Final Roll 2026" / Kannada, `release` `crops-S10-2026-FR`. Commit and push | The new release tag means draft test data never mixes in | 5 min |
| 4 | `python scripts/home/run.py discover` | Part counts for 224 ACs; compare with the draft (changes expected in Bengaluru) | ~10 min |
| 5 | **Pilot:** `run.py go --ac 162` (Shivajinagar, ~190 parts) | OCR + verify green; audit sheet 0 errors; search works on the site | ~45 min |
| 6 | `run.py go --tranche blr` | `run.py status` every hour; Actions all green | ~8 h |
| 7 | Bengaluru audit: the `audit-*.png` sheets (V6) | 0 errors → announce Bengaluru | 1 h |
| 8 | `run.py go --tranche rest` | Same monitoring. Daily V6 audit | ~47 h |
| 9 | Final: coverage ≥ 98%, all ACs verified, the "not found" wording becomes final | Announce the state | — |

**If something breaks:** `run.py go` resumes on re-run, because finished ACs
are in `cache/shipped.json`. Re-running one AC's OCR:
`gh workflow run ocr.yml -f ac=N -f tag=<release>` (needs its crop tar on the
release; otherwise `run.py go --ac N --force`). A bad publish rolls back by
re-running the previous `publish.yml` run. ECI throttling or errors: lower
`--workers` (default 4), never raise it past 8.

---

## 8. Speed levers (measured 2026-10-10)

* Home download: **21–24 Mbps**, measured against both ECI and neutral test
  servers, so this is the line itself, not ECI. Average part 8.9 MB.
* Home cut: ~1.5 s of CPU per part; 4 workers cut ~2.5 parts/s, 8× what the
  line delivers.
* Upload of crops: 15% of PDF bytes (~80 GB statewide), now overlapped with
  the next AC's download. Measured 15 Mbps up to GitHub, ~4.5× what the
  current line needs.
* Actions OCR: ~38 s per part per core. 20 parallel jobs × 4 cores ≈ 2.1
  parts/s, which keeps pace with a home line up to ~150 Mbps.
* **The only big lever is a faster line.** At ~150 Mbps the whole state takes
  ~8 h and Bengaluru ~1.2 h (`--workers 8`); beyond that, Actions is the limit.

---

## 9. Unknowns until the link is live

* Same URL scheme and filename pattern? (`roll-source.json` is the only place
  to change.)
* Same image-only PDF and card layout? If the PDF has a text layer, accuracy
  becomes trivial (item B).
* Final part counts. Bengaluru may grow.
* Whether the English roll is published at the same time (§6).

## 10. Decisions on record

* Home fetch + Actions OCR + draft-release transfer + GitHub Pages.
* No proxy, VPN or CDN-bypass to reach ECI from the cloud.
* No R2 for this project.
* Accuracy over coverage: withhold rather than guess.
* Only hashed EPIC fragments are public. Plaintext rows live only in the draft
  release.
* Keep the `gouthamganeshm/eci-cdn-probe` repo.
