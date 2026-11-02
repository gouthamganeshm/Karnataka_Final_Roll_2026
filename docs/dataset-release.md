# Karnataka final electoral roll 2026: open dataset

One row for every entry printed in the final electoral roll of Karnataka
(all {acs} assembly constituencies, published October 2026), with the age,
gender and relation label as printed in the English roll. **No names, no EPIC
numbers, no house numbers.** Release `{release}`, built {built} (code
`{commit}`), hash key id `{key_id}`.

Made by [Karnataka Final Roll 2026](https://github.com/gouthamganeshm/Karnataka_Final_Roll_2026).
It is separate from that project's search site and does not feed it.

## What is in it

| | |
|---|---|
| Entries | {entries} |
| Electors (not struck off) | {electors} (the CEO booklet: {ceo_electors}) |
| Struck off (DELETED stamp) | {deleted} |
| Male / female / third gender read | {male} / {female} / {tg} |
| Gender not read | {gender_unread} |
| Age not read | {age_unread} |

## Files

| File | What it is |
|---|---|
| `{name}.parquet` | Every entry, the whole state, one file (typed columns) |
| `{name}-acNNN.csv.gz` | The same rows, one CSV per constituency (NNN = 001 to 224) |
| `{name}-summary-booth.csv` | Counts per booth (polling station): electors, gender, age bands, unread fields |
| `{name}-summary-ac.csv` | The same per constituency, next to the CEO booklet's counts |
| `checks.json` | Every check run before release and its result |
| `LICENSE.txt` | The licence (ODbL 1.0) |
| `SHA256SUMS` | Checksums of all files |

## Columns

| Column | What it is |
|---|---|
| `ac` | Assembly constituency number (1 to 224) |
| `part` | Part (booth) number within the constituency |
| `page`, `card` | Page of the booth's PDF, counted from 0, and the card's place on that page (0 to 29) |
| `serial` | The entry's serial number in the part (empty when not read) |
| `serial_sure` | 1 = the serial was read and confirmed; 0 = approximate (shown with "~" on the project's site) |
| `status` | `live` or `deleted` (struck off with a DELETED stamp) |
| `age` | Age as printed |
| `gender` | `M`, `F` or `TG` as printed |
| `relation` | `Father`, `Husband`, `Mother`, `Wife`, `Other` or `Guru`: the label only, never the relative's name |
| `epic_hash` | A keyed hash of the EPIC number: the same EPIC always gives the same hash; it cannot be turned back into the EPIC. Empty for the few entries whose EPIC the project could not settle (they are not on its search site either) |
| `household_hash` | A keyed hash of the house number within the booth: equal hashes = the same printed house number |

An empty field is one the reader could not read with certainty; nothing is guessed.

**Struck-off entries:** the DELETED stamp is printed over the gender and the
house number of a struck-off card, so for those entries `gender` and
`household_hash` are almost always empty; age and relation are read on about
98% of them.

Anyone can check a row by opening the booth's PDF on the ECI site and going to
the page and card.

## Privacy

* Names of electors and relatives are **never read**.
* EPIC numbers and house numbers are read only to be hashed with a secret
  32-byte key (HMAC-SHA256) and are then thrown away. Without the key nobody
  can test a guessed EPIC against `epic_hash`. The key is never published;
  `{key_id}` (the first 8 hex of the key's SHA-256) only tells which releases
  can be compared with each other.
* Every value of every column was checked against what that column may hold
  before release, so no column can carry a name, an EPIC or a house number.
* Please do not use this dataset to try to identify electors.

## How it was made

1. The English PDF of every booth was downloaded from ECI, and each card page
   was cut into one image of the cards' text (cloud VMs).
2. Each image was read once by Tesseract OCR (GitHub Actions): age, gender,
   relation label, house number.
3. The readings were joined, page by page and card by card, to the project's
   verified rows (serial, EPIC, struck off). Where a booth's English roll has
   an extra front page the pages were lined up first ({shifted} booths); a page
   whose card count still did not agree was left empty.
4. An age no elector can have (under 18 or over 120, e.g. 123 read for 23)
   was left empty: {age_dropped} entries.
5. Marks on a booth's cover and map pages that the card cutter took for cards
   ({not_entries}, none with an EPIC, none counted by the CEO) are left out.

## Checks before release (all passed)

* Every value of every column matches the pattern its column allows.
* Rows per constituency = the project's verified rows.
* Every entry with an EPIC hash is exactly where the project's
  [search site](https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/)
  (build {site_build}) finds that EPIC: same constituency, part and serial,
  struck off or not alike; and each constituency has as many electors and
  deletions as the site shows.
* Electors per constituency = the CEO's final booklet.
* Gender read per constituency: no more than {gender_slack} of electors above
  the CEO's male, female or third-gender count.
* At least {min_read} of each constituency's cards read.
* One hash key for every constituency.

The results per constituency are in `checks.json` and `{name}-summary-ac.csv`.

**Still to come:** a person looks at the card images of the entries flagged by
the checks, the few pages left empty are read again, and the gender of
struck-off entries is read under the stamp. Any correction will come as a new
release; this one will stay as it is.

## Licence

[Open Database License (ODbL) 1.0](https://opendatacommons.org/licenses/odbl/1-0/).
Credit "Karnataka Final Roll 2026" with a link to the project.
Source: the final electoral rolls of the Election Commission of India and the
Chief Electoral Officer, Karnataka.
