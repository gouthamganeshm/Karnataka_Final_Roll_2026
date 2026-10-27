"""Parse the CEO Karnataka's final-roll statement into reference/ceo-final-2026.json.

    python scripts/home/ceo_reference.py acwise.pdf

The statement ("SIR 2026 Final Roll Publication", 27 Oct 2026,
https://ceo.karnataka.gov.in/uploads/PDF%20FINAL%20AC%20WISE%2027_1793094730.pdf)
is independent of the roll PDFs we read: Annexure-1 gives each AC's general
electors (male, female, third gender, total), Annexure-10 its polling
stations. Every AC's total must equal the live cards we read and its polling
stations the parts we fetched; the district and state rows check the parse.
"""
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'reference' / 'ceo-final-2026.json'
URL = 'https://ceo.karnataka.gov.in/uploads/PDF%20FINAL%20AC%20WISE%2027_1793094730.pdf'
NUM = r'([\d,]+)\s*\n'


def annexure(doc, title: str, cols: int) -> dict[int, list[int]]:
    text = ''.join(p.get_text() for p in doc if title in p.get_text())
    rows = {}
    for m in re.finditer(r'(?m)^(\d{1,3})\s*\n?\s*([A-Za-z][^\n\d]*?(?:-\s*\n[A-Za-z][^\n\d]*?)?)\s*\n' + NUM * cols, text):
        ac = int(m.group(1))
        if 1 <= ac <= 224:
            rows[ac] = [int(g.replace(',', '')) for g in m.groups()[2:]]
    return rows, text


def main(pdf: str) -> int:
    doc = fitz.open(pdf)
    electors, t1 = annexure(doc, 'AC Wise General Electors', 4)
    stations, t10 = annexure(doc, 'AC wise Polling Stations', 3)
    assert len(electors) == 224 and len(stations) == 224, (len(electors), len(stations))
    for ac, (m, f, tg, tot) in electors.items():
        assert m + f + tg == tot, ac
    for ac, (u, r, tot) in stations.items():
        assert u + r == tot, ac
    state = re.search(r'Karnataka State\s*\n([\d,]+)\s+([\d,]+)\s*\n([\d,]+)\s*\n([\d,]+)', t1)
    want = int(state.group(4).replace(',', ''))
    got = sum(v[3] for v in electors.values())
    assert got == want, (got, want)
    data = {'source': URL, 'published': '2026-10-27', 'stateElectors': want,
            'acs': {str(ac): {'male': electors[ac][0], 'female': electors[ac][1], 'tg': electors[ac][2],
                              'electors': electors[ac][3], 'stations': stations[ac][2]} for ac in sorted(electors)}}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + '\n', 'utf8')
    print(f'224 ACs, {want:,} electors, {sum(v[2] for v in stations.values()):,} polling stations -> {OUT}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
