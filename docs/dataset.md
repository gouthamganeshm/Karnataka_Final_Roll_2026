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
| `household_hash` | Keyed hash of the house number within the booth: equal = same printed house number |
| `verified` | Which checks the entry passed (both rolls, a person's review, the 25% sample) |

Plus summary tables per booth, constituency and district: electors by age
band and gender, deletions by reason, and a data-quality table.

## Privacy: what is never published

| Never in the dataset | How |
|---|---|
| Elector's name | Not in the dataset. It is read only for the site's search result, where it is stored encrypted under the EPIC ([site-voter-details.md](site-voter-details.md)) |
| Relative's name (father, husband, …) | Never parsed: the reader drops that line in memory; only the label "Father" / "Husband" / … is kept |
| EPIC series (first three letters) | Left out: it would make guessing EPICs easier |
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

1. **VMs** download every booth's **Kannada and English** PDFs afresh and
   upload them to the private work release.
2. **GitHub Actions** cut every card and read its text block once per page in
   each roll (Tesseract with its Kannada and English models, `fields.py`): age,
   gender, relation label, house number, and the elector's name (for the
   site only). The two rolls are typeset separately, so each is a witness for
   the other: a field goes out when both agree, or when one is unread and the
   other is plain; a disagreement is looked at by a person on the card images.
   Measured on the same 227 cards in both rolls: age agreed on 226 of 227,
   relation on 227 of 227, gender on every card both read (the Kannada reader
   missed 7, the English 1). Both rolls together are ~30 lakh page reads,
   about 2-3 days on Actions.
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
