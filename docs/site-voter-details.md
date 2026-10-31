# Planned: voter details on the search result

Comes **after** the open dataset ([dataset.md](dataset.md)), which comes after
the 25% sample verification. Order: verification → dataset → this.

## What a search will show

Today an EPIC search gives the constituency, part (booth) and serial. With the
dataset it will also show:

| New on the result | Source |
|---|---|
| Age, gender, relation (Father / Husband / Mother / Other) | dataset |
| Status in detail: live, modified (`#`), or deleted with the printed reason (dead, shifted, repeated, missing, disqualified) | dataset |
| **Polling station name and address** (where to go and vote) | each booth PDF's cover page, read once per booth |
| **"Open the PDF at page N"**: the link jumps straight to the page with the voter's card | the card's page |
| "Did you mean …?" when an EPIC is not found: the same number with commonly confused characters swapped (O/0, I/1, S/5, B/8, Z/2) that *is* on the roll | in the browser |

## What it will not show, and why

**No names** (the voter's or the relative's) and no house numbers. The site's
data files can be downloaded by anyone, and EPIC numbers can be guessed and
tested against them, so anything the site can show for an EPIC can be
collected in bulk for all 4.5 crore voters. Age, gender and booth are already
plainly printed in ECI's PDFs per booth and serial, so they add nothing new;
a machine-readable list of names with their EPICs would. The voter sees their
own card, with name, one click away through the "page N" link to ECI's own
PDF.

## How (no server, same privacy model)

* The 9-byte record grows to 12 bytes: + page, + age, + one byte for gender,
  relation and status. 4.56 crore × 12 bytes ≈ 550 MB, inside GitHub Pages'
  1 GB. `FORMAT` goes from 2 to 3 so cached pages reload (build.mjs, app.js).
* Polling station names: one small file per constituency
  (`data/stations/<ac>.json`), fetched only after a hit.
* The share picture gains age and polling station, never a name.
* Checked before going live: the browser check (`sv_browser.py`) is extended
  to compare every new field shown with the dataset row, on a random sample
  in every constituency.

## Ideas taken from sir-bangalore.shantanugoel.com

That site (Bengaluru only) shows a full elector record including names and
searches by name, through its own server and database. Useful for us:
polling station name on the result, a clear DELETED explanation (already
here), headline counts (already here), and tolerance for OCR slips (our
"did you mean"). Not taken: name search and names on results (a server
holding every voter's name, and bulk-collectable), which this site avoids by
design.
