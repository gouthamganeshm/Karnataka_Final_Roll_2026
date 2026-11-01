# Sample verification results (31 Oct – 1 Nov 2026)

The plan is in [../sample-verification.md](../sample-verification.md). This
page is what came out of it. It holds counts only; the cards themselves (with
EPICs) stay on the private release.

## Coverage

| | |
|---|---|
| Constituencies | **224 of 224** |
| Booths | **60,923 of 60,923**, every one with at least 25% of its cards checked |
| Cards checked | **1,22,97,124** of 4,56,43,886 printed (26.9%) |
| Read afresh from | ECI's PDFs, downloaded again, both the Kannada and the English roll |
| Compared with | a snapshot of the live site (build of 30 Oct 2026, 21:00 UTC), looked up exactly as a visitor's browser does |

## First pass: what matched by machine

| Result | Cards | Meaning |
|---|---|---|
| Same as the site | 1,22,93,575 | 99.97% |
| Same booth, the site's serial marked "~" | 1,135 | looked at below |
| Same booth, a serial digit 5/9/3/0/8/6 differs | 461 | looked at below |
| Flagged for a person | 2,001 | everything else, below |

## Manual review of the flagged cards

Every flagged card was put on a review sheet (the Kannada card beside the
English one, with what the site holds) and looked at by eye. Where the
reading was in doubt, the EPIC read by eye was looked up in the site
snapshot.

| Flag | Cards | Outcome |
|---|---|---|
| EPIC not on the site | 1,864 | The fresh reader misread a character (O/C/Q/G, I/T, L/I, S/G, a dropped digit of an 8-digit EPIC, a heading printed over the card). 1,844 were matched automatically to the look-alike the site holds at that card's place and sampled by eye; the other 20 were read by eye and looked up: **19 on the site at the right place; 1 printed irregularly** (see below) |
| Serial differs | 50 | 48: the site is right, the fresh reader misread the serial. **2: the site's serial was wrong** (5 published as 3) |
| Page count differs | 48 | 41: fresh serial misreads (a whole page of 5xx read as 9xx). **7 pointed at wrong serials on the site** |
| Not on the site / unread | 24 | Not voter cards: photos of the polling station, maps and QR codes on the cover page |
| Deleted mark differs | 11 | A section heading printed over the serial box was read as a mark. No DELETED stamp on any of them; the site is right |
| In another constituency | 4 | The fresh reader misread the series; the right EPIC is on the site at the right place |
| "~" and 5/9/3 serials (above) | 1,596 | Spot check of 96 by eye: the site's serial is the printed one in 95; the other one is among the wrong serials below |

## Whole-state serial audit

The wrong serials the sample found all had the same cause: a 5 published as
3 or 9 when the card was set from the English roll. So every booth on the
site was checked for it, not just the sample: in a booth the serials must run
1, 2, 3 … with one card each, and a wrong serial leaves a gap where it should
be and a double (or an outlier) where it went.

| | |
|---|---|
| Booths with a gap or a double | **33** of 60,923 |
| Cards with a wrong serial | **67**, each read by eye off the PDF |
| Of these: 5 published as 3 or 9 | 47 cards in 32 booths |
| Of these: one booth (AC 176, part 480) whose PDF prints six deleted cards twice, which shifted the serials around them | 20 cards |

All 67 were corrected (see below). The same audit run on the site after
the correction finds **no booth** with a gap or a double.

## The one irregular print

One card (AC 175, part 145, serial 20) prints its EPIC with the letter S
where a 5 would be (`SVF` + `S` + 6 digits). The site holds it under the
standard form with a 5. A visitor who types it exactly as printed gets
"not found". Since the build of 1 Nov 2026 the card is found under both
spellings (`aka` on its row, `scripts/home/set_aka.py`; counted once).

## Fixes

| | |
|---|---|
| Cards corrected | 67 serials in 30 constituencies (EPIC, booth and deleted status unchanged) |
| How | `reverify_live.py --epics` with the serial read off the PDF; each constituency's checks rerun (all pass, no card lost) before its live files were replaced |
| Published | build of 1 Nov 2026, 07:42 UTC |
| Before publishing | the live site was re-read in full: 65,536 of 65,536 data files identical to the snapshot the sample was checked against |
| Elector counts | unchanged: 4,54,55,689; 224 of 224 match the CEO booklet ([proof](official-match.md)) |
| Serial audit after | 0 booths with a gap or a double |
| Browser check after | 5 cards per constituency typed into the live site in a real browser (1,120 cards): 1,109 shown with the expected constituency, booth and serial; the other 11 showed the right constituency and booth, but the fresh reading of their serial was unreadable, so the serial could not be compared |
