# Planned: voter details on the search result

Comes **after** the open dataset ([dataset.md](dataset.md)), which comes after
the 25% sample verification. Order: verification → dataset → this.

## What a search will show

Today an EPIC search gives the constituency, part (booth) and serial. With the
dataset it will also show:

| New on the result | Source |
|---|---|
| **Voter's name, in the site's language**: Kannada as printed in the Kannada roll, English as printed in the English roll (the language button switches both the page and the name) | both rolls, read once per card |
| Age, gender, relation (Father / Husband / Mother / Other) | dataset |
| Status in detail: live, modified (`#`), or deleted with the printed reason (dead, shifted, repeated, missing, disqualified) | dataset |
| **Polling station name and address** (where to go and vote) | each booth PDF's cover page, read once per booth |
| **"Open the PDF at page N"**: the link jumps straight to the page with the voter's card | the card's page |
| "Did you mean …?" when an EPIC is not found: the same number with commonly confused characters swapped (O/0, I/1, S/5, B/8, Z/2) that *is* on the roll | in the browser |

Never shown or published: the EPIC itself (only the visitor's own typing is
echoed back), the relative's name, the house number.

## Protecting names from bulk collection

The site has no server: its data files can be downloaded by anyone. Today a
record holds only a 6-byte fragment of SHA-256(EPIC), which is fast to
compute, so someone could guess EPICs and find which exist. That only
reveals where an EPIC votes. With names it would reveal a name list for the
whole state, so names get stronger protection:

1. **Each name (Kannada and English) is encrypted with a key derived from its EPIC** (AES-GCM, key
   from a deliberately slow, memory-hard hash of the EPIC). Only a visitor who
   already knows the EPIC can read the name; the downloaded files hold
   unreadable bytes.
2. **The lookup itself moves to the slow hash** (bucket and fragment come
   from it, not from SHA-256), so a guessed EPIC can no longer be tested
   cheaply. One search costs the visitor's browser a fraction of a second;
   testing every possible EPIC of a single series costs years of computing.
3. **No EPIC series in the open dataset** (it would narrow the guessing).
4. **Names never enter the open dataset** ([dataset.md](dataset.md)); they
   exist only encrypted on the site and, while being built, on private
   releases (deleted afterwards).

What this cannot stop: someone who already has a list of real EPICs can read
those voters' names, exactly as ECI's own search lets them. It makes
*guessing* the whole roll impractical, not impossible for a very large
effort; that remaining risk is accepted for showing names.

## How (no server)

* Record grows from 9 bytes to about 40 (fragment, AC, part, serial, page,
  age, gender/relation/status, both names encrypted, packed one byte a
  letter). ~4.56 crore × ~55 bytes is ~2.5 GB, over GitHub Pages' 1 GB per site, so the records are split over
  three GitHub Pages repos (each gets its own 1 GB, free); Cloudflare R2
  stays out (it is shared with another site). `FORMAT` goes from 2 to 3.
* Build cost: the slow hash runs once per card, 4.56 crore times, on Actions.
* Polling station names: one small file per constituency
  (`data/stations/<ac>.json`), fetched only after a hit.
* The share picture gains age and polling station, never the EPIC.
* Checked before going live: the browser check (`sv_browser.py`) is extended
  to compare every new field shown with the dataset row, on a random sample
  in every constituency.

## Ideas taken from sir-bangalore.shantanugoel.com

That site (Bengaluru only) shows a full elector record including names and
searches by name, through its own server and database. Useful for us:
names and polling station on the result, a clear DELETED explanation
(already here), headline counts (already here), and tolerance for OCR slips
(our "did you mean"). Not taken: search *by name* (it needs every name
readable by the site, i.e. a bulk list) and showing the EPIC.
