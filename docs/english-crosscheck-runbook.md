# Full English cross-check: runbook and contingency

Goal: every EPIC of every booth (60,923 parts, ~4.5 crore cards) checked
against the English roll, which ECI typesets separately from the Kannada one
the site was read from. A card is final when both rolls agree, or a person
read it off the crops of both. Nothing that is uncertain is published.

## How it runs (no person needed)

| Stage | Where | Output (all on draft releases, never public) |
|---|---|---|
| Fetch the English PDFs of an AC | VM, `eng_pilot.py` (systemd `eng-pilot@K`) | `epdfs-<ac>.s<i>.tar` on `<tag>-work` |
| Read them (16 parallel jobs) | Actions, `ocr.yml kind=epdf` | `engfull-<ac>.tar`, `crops-eng-<ac>.tar` on `<tag>-eng` |
| Compare every card | VM, `xcheck.py` | `xcheck-<ac>.zip` on `<tag>-eng`: ledger + review sheets |
| Apply | VM, `reverify_live.py --epics` | live-* replaced, site republished |

Order: Hassan, then every Bengaluru AC (BBMP, Bangalore Urban, Bangalore Rural), then the
rest; VM K takes every 4th AC of that order, so all four work down one list.
The pilot applies an AC only when every card left for a person is decided, and
only if no other published card changes (else the ledger records the failure
and the AC stays as it was).

Buckets per card: `confirmed` (both rolls), `kan-only` (English unreadable,
both Kannada readers agreed: the original publish rule), `auto` (the English
EPIC is also a Kannada reading: corrected or recovered), `manual` (anything
else, including a card in one roll only, a different deleted mark or serial).

## Manual review (one AC at a time, in AC order)

    python scripts/home/xreview.py status     # where every AC stands
    python scripts/home/xreview.py next       # next AC with cards left; prints the batch + sheet paths
    python scripts/home/xreview.py decide AC 3=ABC1234567 4=keep 5=withhold 6=ABC7654321/del

A sheet shows 12 cards: Kannada EPIC and serial crops on the left, English on
the right, both readings and the published value under them. Each `decide` is
uploaded at once as `decisions-<ac>.json` to the private `<tag>-eng` draft
(they hold EPICs, so never git: the repo is public); a copy stays in
`cache/xreview/<ac>/`. `xreview.py sync` uploads any an outage kept local.

## Contingency: what survives what

Nothing that matters lives only in a session or on one machine.

| Failure | Effect | Resume |
|---|---|---|
| Claude's session ends / network outage at home | Fetch, OCR, compare and apply of ACs without review cards go on in the cloud | New session: read this file, `xreview.py status`, `xreview.py next`. Undecided cards are exactly those without a decision in `decisions-<ac>.json` |
| Outage in the middle of a review batch | Decisions already uploaded are safe; a batch kept local says `NOT UPLOADED` | `xreview.py sync`, then `xreview.py next` |
| A VM reboots or the pilot crashes | systemd restarts it within a minute; every decision is re-read from GitHub | none |
| A VM is lost | Its ACs stop | Re-create from `scripts/home/` docs; or run another VM's unit with `--vm <lost K>` |
| An OCR run fails | Re-dispatched while its PDFs remain, re-fetched after; 3 tries | Given-up ACs: `cache/eng-pilot.json` on the VM, `journalctl -u eng-pilot@K` |
| Live rows change after a check (another fix applied) | The apply notices (rows hash), deletes the ledger, the AC is checked again | Decisions are keyed by card, so they carry over |
| An apply is refused (another card would change) | Ledger records `apply.failed`; the AC stays as it was | `xreview.py status` lists it as APPLY FAILED; investigate, then delete its ledger to redo |

## Free tier

Only the four Always Free VMs (1 OCPU / 6 GB each) are used. PDFs are deleted
from the VM once uploaded; OCI egress (~0.7 TB in all) is under the 10 TB a
month; Actions on a public repo cost nothing. Pilots run at nice 5, under
the Kannada autopilot.

## Done when

`xreview.py status` shows every AC applied, then a fresh random sample
(`sample_verify.py`, new seed) agrees, and the final report lists per AC:
site count against the official count, cards confirmed by both rolls, cards
settled by a person, and cards withheld with the reason.
