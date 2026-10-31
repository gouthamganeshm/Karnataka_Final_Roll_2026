# Open dataset (planned): one row per entry on the roll, without identities

Runs **after** the 25% sample verification ([sample-verification.md](sample-verification.md))
finishes; verification has priority on the VMs and on GitHub Actions.

## What each row will hold

| Column | What it is |
|---|---|
| `ac`, `part`, `page`, `card`, `serial` | Where the entry is printed (anyone can open that ECI PDF) |
| `status` | live, deleted (with the printed reason code E/S/R/M/Q when read), modified (`#`) |
| `list` | main roll or additions list |
| `age`, `gender` | As printed |
| `relation` | Father, Husband, Mother, or Other (the label only) |
| `epic_hash` | Keyed hash of the EPIC: equal hashes = same EPIC; cannot be turned back into it |
| `epic_series` | The first three letters of the EPIC (the issuing series) |
| `household_hash` | Keyed hash of the house number within the booth: equal = same printed house number |
| `verified` | Which checks the entry passed (both rolls, a person's review, the 25% sample) |

Plus summary tables per booth, constituency and district: electors by age
band and gender, deletions by reason, and a data-quality table.

## Privacy: what is never published

| Never in the dataset | How |
|---|---|
| Elector's name | Never parsed: the reader drops those text lines in memory (`scripts/ocr/fields.py`) |
| Relative's name (father, husband, …) | Same: only the label "Father" / "Husband" / … is kept |
| House number / address | Only as a keyed hash, then discarded |
| EPIC number | Only as a keyed hash (HMAC-SHA256, first 24 hex characters) |

The hash key is a random 32-byte secret kept only in a GitHub Actions secret
and on the VMs (`~/.dataset_key`, readable only by its owner); it is never in
git, never printed, never in a release. Without it nobody can test a guessed
EPIC against `epic_hash` (a plain SHA-256 could be reversed by trying all
possible EPICs). The published `key_id` (first 8 hex of the key's own
SHA-256) only says which releases can be compared with each other.

Card-level intermediate files (readings with house numbers, joins with EPICs)
stay on private draft releases and are deleted once the dataset is built.

## How it will run (all in the cloud)

1. **VMs** download every booth's English PDF afresh (as for the cross-check)
   and upload them to the private work release.
2. **GitHub Actions** cut every card and read its text block once per page
   (Tesseract, `fields.py`): age, gender, relation label, house number.
   Measured on 227 cards: every age read, 99.6% gender, 98.7% relation label on
   the first pass; misses get a second, card-by-card read.
3. **A VM** joins the readings to the verified rows (EPIC, serial, deleted) by
   AC, part, page and card, hashes EPIC and house number, and drops them.
4. **Checks before release**
   * gender totals per constituency against the CEO booklet (male, female,
     third gender are printed there for every AC);
   * age and gender per entry against an independent reading
     ([Diagram Chasing's dataset](https://github.com/diagram-chasing/karnataka-sir-voter-rolls-data),
     ODbL), by AC, part and serial; disagreements looked at by a person on the
     card images;
   * no column can hold a name: a scan of every text value for letters before
     publishing.
5. **Publish** as a public GitHub release (CSV and Parquet, one file per
   constituency plus the summaries), with a column guide and the licence, only
   after the owner's go-ahead.
