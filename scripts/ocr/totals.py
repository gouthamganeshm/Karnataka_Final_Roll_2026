"""Read the part's own printed elector count (verifier check V3).

Every part's first page ends with a ruled table, "4. NUMBER OF ELECTORS":

    Starting Serial No. | Ending Serial No. | Male | Female | Third Gender | Total
            1           |        650        | 324  |  326   |      0       |  650

and its last page repeats Male / Female / Third Gender / Total as a summary.
Both use plain digits in the Kannada and English rolls alike. The numbers row
is the band between the page's last two full-width rules; each cell is read on
its own, digits only.

A reading is only returned when it checks itself: Total = Male + Female +
Third Gender (and, on the cover, Ending >= Starting). Anything else is None —
"unreadable" is never turned into a number.

The final roll prints its deleted electors' cards too (stamped DELETED, kept
in the serial run), and Total is net of them. So `deleted`, the number of
printed cards that are not on the roll, is read twice: the cover's
Ending - Starting + 1 - Total, and the summary's rows I main list, II
additions, III deletions, IV gender corrections, net. Only the Total column
of rows I-III is used (their zero cells misread too often for the
Male + Female + TG check), and only when I + II - III = net: row IV moves
electors between columns, so its total is always 0.

    python -I scripts/ocr/totals.py part.pdf [...]     # try it on PDFs
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import roll_ocr as R  # noqa: E402


def _rules(dark: np.ndarray, frac: float) -> list[int]:
    h, w = dark.shape
    gap = max(2, int(round(6 * w / R.REFERENCE_WIDTH)))
    return R._mids(np.where(dark.sum(axis=1) > frac * w)[0], gap)


def _row_cells(img: Image.Image, y0: int, y1: int) -> list[Image.Image]:
    """Cell images of one table row, split at its vertical rules."""
    img = img.convert('L')
    a = np.asarray(img) < 128
    w = a.shape[1]
    band = a[y0 + 3:y1 - 2]
    if band.shape[0] < 8:
        return []
    gap = max(2, int(round(6 * w / R.REFERENCE_WIDTH)))
    verts = R._mids(np.where(band.sum(axis=0) > 0.8 * band.shape[0])[0], gap)
    cells = []
    for l, r in zip(verts, verts[1:]):
        if r - l < 15:
            continue
        crop = R._ink_box(img.crop((l + 4, y0 + 4, r - 3, y1 - 3)))
        cells.append(crop)
    return cells


DIGITS = ('-c', 'tessedit_char_whitelist=0123456789')
# Read without a whitelist first: with one, Tesseract's LSTM silently drops the
# 1s and 7s of this font (712 -> 72, 617 -> 6). Letters it mistakes for digits
# are mapped back; anything else makes the cell unreadable.
_AS_DIGIT = str.maketrans({'O': '0', 'o': '0', 'D': '0', 'Q': '0', 'I': '1', 'l': '1', 'i': '1',
                           '|': '1', '!': '1', ']': '1', 'L': '1', 'Z': '2', 'z': '2', 'S': '5',
                           's': '5', 'B': '8', 'g': '9', 'q': '9', 'T': '7'})


def _as_int(text: str) -> int | None:
    t = text.translate(_AS_DIGIT).strip(".,:;-_'`\"")
    return int(t) if t.isdigit() else None


def _candidates(cells: list) -> list[set]:
    """Every reading of each cell that parses as a number: one line without a
    whitelist (letters mapped back), and one word restricted to digits; a
    cell neither reads is retried as a single character (a lone "0" often
    needs it). The checksum then chooses among them."""
    import crops as C
    present = [i for i, c in enumerate(cells) if c is not None]
    imgs = [C._single_line(cells[i], target=60) for i in present]
    out: list[set] = [set() for _ in cells]
    if not imgs:
        return out
    for psm, extra in ((7, ()), (8, DIGITS)):
        for i, t in zip(present, C.read_each(imgs, psm=psm, extra=extra)):
            n = _as_int(t)
            if n is not None:
                out[i].add(n)
    retry = [i for i in present if not out[i]]
    if retry:
        again = C.read_each([C._single_line(cells[i], target=60) for i in retry], psm=10, extra=DIGITS)
        for i, t in zip(retry, again):
            n = _as_int(t)
            if n is not None:
                out[i].add(n)
    return out


def _consistent(cands: list[set], check) -> tuple | None:
    """The one reading of the row that passes `check`, or None if there is no
    such reading or more than one disagreeing on the total."""
    import itertools
    if any(not c for c in cands) or 1 < len(cands) and sum(len(c) > 1 for c in cands) > 4:
        return None
    hits = {combo for combo in itertools.product(*cands) if check(*combo)}
    totals = {combo[-1] for combo in hits}
    return sorted(hits)[0] if len(totals) == 1 else None


def read_cover(img: Image.Image | None) -> dict | None:
    if img is None:
        return None
    dark = np.asarray(img.convert('L')) < 128
    rules = _rules(dark, 0.6)
    if len(rules) < 2:
        return None
    cands = _candidates(_row_cells(img, rules[-2], rules[-1]))
    if len(cands) != 6:
        return None
    row = _consistent(cands, lambda s, e, m, f, g, t: t and t == m + f + g and e >= s)
    if row is None:
        return None
    start, end, male, female, tg, total = row
    out = {'start': start, 'end': end, 'male': male, 'female': female, 'tg': tg, 'total': total}
    if end - start + 1 >= total:     # less is a misread Ending, not a count
        out['deleted'] = end - start + 1 - total
    return out


def read_summary(img: Image.Image | None) -> dict | None:
    """The last page's summary: its last table row ends Male, Female, TG, Total."""
    if img is None:
        return None
    dark = np.asarray(img.convert('L')) < 128
    rules = _rules(dark, 0.5)
    for k, (y0, y1) in reversed(list(enumerate(zip(rules, rules[1:])))):
        cands = _candidates(_row_cells(img, y0, y1))[-4:]
        if len(cands) == 4:
            row = _consistent(cands, lambda m, f, g, t: t and t == m + f + g)
            if row:
                male, female, tg, total = row
                out = {'male': male, 'female': female, 'tg': tg, 'total': total}
                # Rows I, II, III are the ruled rows 4, 3 and 2 above the net row.
                if k >= 4:
                    last = [(_candidates(_row_cells(img, rules[k - j], rules[k - j + 1])) or [set()])[-1]
                            for j in (4, 3, 2)]
                    fits = {d for a in last[0] for b in last[1] for d in last[2] if a + b - d == total}
                    if len(fits) == 1:
                        out['deleted'] = fits.pop()
                return out
    return None


def read_totals(cover: Image.Image | None, summary: Image.Image | None) -> dict | None:
    """The cover's reading, cross-checked against the summary page when both read."""
    c, s = read_cover(cover), read_summary(summary)
    # The cover leaves `deleted` out when its Ending misreads; then the summary's stands.
    if c and s and (c['total'] != s['total'] or
                    ('deleted' in s and c.get('deleted', s['deleted']) != s['deleted'])):
        return {'conflict': True, 'cover': c, 'summary': s}
    if c:
        return {**c, 'from': 'cover', 'confirmed': bool(s)}
    if s:
        return {**s, 'from': 'summary'}
    return None


if __name__ == '__main__':
    import crops as C
    for path in sys.argv[1:]:
        parts = C.cut_part(open(path, 'rb').read())
        print(os.path.basename(path), read_totals(parts['cover'], parts['summary']))
