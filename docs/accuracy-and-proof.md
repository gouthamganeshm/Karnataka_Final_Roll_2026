# Accuracy and proof

This page lists, in plain words, every check the data went through before and
after it went on the site, with the numbers. Anything that holds a real EPIC
(card images, readings, decisions) is kept on a private release, so the proof
here is counts, tables and screenshots.

## The rule behind every step

A wrong answer is worse than no answer. If the site sends a voter to the wrong
booth, they may give up; if it says "not found", they call 1950 and check. So
at every step, a card that could not be settled was **held back**, never
guessed, until a person looked at it.

## 1. Reading each card

Every booth PDF is a set of page images. Each card page has 30 voter cards
(10 rows × 3). For every card the EPIC box and the serial box are cut out and
read:

| Reader | How it reads |
|---|---|
| Tesseract on a sheet | The page's EPIC crops pasted into one sheet and read by Tesseract OCR |
| Glyph templates | Each letter compared with the fixed font ECI prints EPICs in |
| Tesseract alone | The single crop read on its own, when the first two disagree |
| Prototypes | A second shape-based reader with different features |

A character is accepted only when independent readers agree. Measured before
the roll came out, on 79,569 cards the readers had never seen: 99.68% settled,
and no wrong EPIC among those published (fewer than 1 in 10,000 at 95%
confidence). Details in [PLAN.md](../PLAN.md).

## 2. Checking every booth against its own printed totals

Each booth PDF prints how many electors it has and how many were deleted (on
the cover and on the last page). A booth went live only when:

* the serial numbers run in order with no gap and no repeat (check **V2**), and
* the live cards read = the printed total, and the cards with a deletion mark
  = the printed deletions (check **V3**).

If a booth's numbers did not tie, every card of that booth was held back
until it was fixed.

## 3. Checking every constituency against the CEO's official count

The CEO Karnataka published the official elector count of every
constituency (the [booklet](https://ceo.karnataka.gov.in/uploads/PDF%20FINAL%20AC%20WISE%2027_1793094730.pdf),
27 Oct 2026). Those numbers are in `reference/ceo-final-2026.json`; the site
build refuses to publish a constituency more than 0.5% off.

**Result today: 224 of 224 constituencies match the booklet exactly, total
4,54,55,689.** The full table, generated straight from the live site, is in
[proof/official-match.md](proof/official-match.md).

## 4. Every card cross-checked against the English roll

ECI prints every booth twice: in Kannada (what the site was read from) and in
English. The two are typeset separately, so a reading error in one is
unlikely to repeat in the other. All 60,923 English PDFs were downloaded and
read as well, and every card compared, cell by cell:

| Outcome | What happened to the card |
|---|---|
| Both rolls agree | Final |
| English unreadable, two Kannada readers agree | Final (the original rule) |
| English EPIC is also one of the Kannada readings | Corrected automatically |
| Anything else (card in one roll only, different deletion or serial) | Looked at by a person |

**3,919 cards in 224 constituencies were decided by a person** looking at
both crops side by side. Decisions are stored privately (`decisions-<ac>.json`
on the private release). Runbook: [english-crosscheck-runbook.md](english-crosscheck-runbook.md).

Things this found and fixed, with examples checked by eye:

* **Round letters.** C / O / G / Q look alike at 13 pixels. 9,839 cards
  where readers had disagreed on a letter were re-checked against the English
  roll; a rule that had wrongly overruled two agreeing readers was found and
  reversed.
* **English overprint.** In some booths the English roll prints address text
  over the EPIC box; its DELETED flag there is spurious. Kept the Kannada
  reading.
* **Missing pages.** Two Kannada PDFs lacked whole pages; those cards were
  taken from the English roll.

## 5. Closing the last gap to 100%

After the cross-check, 116 voters in 55 constituencies were still missing
against the official count. Each was traced by reading the card images:

| Cause | Fix |
|---|---|
| The reader skipped one card in a row (a "hole"), so the later serials ran one low | Card added, serials set by position |
| Serial misread 5 → 9 (e.g. 957 for 557) | Serial corrected |
| A section heading printed over the first card of a page (e.g. "2. Sarathi-2") mistaken for a deletion mark | Card restored; real deletions carry the DELETED stamp |
| A card at the end of a page or booth missed | Card added |

Every fix passed the same booth checks (V2, V3) before it was applied. After
it, every constituency matched the booklet.

## 6. Irregular EPICs

About 600 cards whose EPIC is not the usual 3 letters + 7 digits were looked
at. Most are 3 letters + 8 digits or the old state format with slashes. Seven
are printed irregularly (for example 6 digits only, or a digit inside the
letters); both rolls print them the same way, so they are kept exactly as
printed and the site accepts them.

## Known limits (honest list)

| | Count | What the visitor sees |
|---|---:|---|
| Cards whose EPIC could not be read reliably, held back | 81 | "not found — check with 1950" (they are counted as electors, so the totals still match) |
| Serials marked "~" (the reader was not fully sure of the serial; the EPIC and booth are confirmed) | 16,89,335 | the serial with a "~" and a note to check the PDF |

The 25% sample check ([sample-verification.md](sample-verification.md)) will
measure, booth by booth, how often what the site says matches the PDF,
including these.

## How to check it yourself

1. Search your EPIC on the site and open the PDF link it gives.
2. Find your serial number in that PDF; your card is there.
3. For counts: compare [proof/official-match.md](proof/official-match.md)
   with the CEO booklet, or re-run `python scripts/home/official_match.py`.
