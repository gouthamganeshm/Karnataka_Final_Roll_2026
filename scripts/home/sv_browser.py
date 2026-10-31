"""Tier D of the sample verification: cards searched on the real site, in a browser.

    python scripts/home/sv_browser.py AC [AC ...] [--shots N]

For each AC, the `browser` cards of svres-<ac>.json.gz (random cards the
snapshot lookup called ok) are typed into the live site in headless Chromium
(Playwright), exactly as a visitor would, and the answer the page shows is
compared with the card: the constituency, part and serial on one of the
result tickets, or in the "also listed as DELETED" note for a deleted card.
Writes cache/sv/browser-<ac>.json, and the first N result screenshots per AC
to cache/sv/shots/ (they show EPICs: keep them private).
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'scripts' / 'home')]
import release  # noqa: E402

SITE = 'https://gouthamganeshm.github.io/Karnataka_Final_Roll_2026/'
SV = ROOT / 'cache' / 'sv'
SVR = f'{release.TAG}-svr'


def shown(page) -> tuple[str, list[tuple[int, int, str]], str]:
    """(result heading, [(ac, part, serial text)] from the tickets, whole text)."""
    head = page.locator('#result .res-head, #result h2, #result h3').first.inner_text(timeout=5000)
    tickets = []
    for m in page.locator('#result .ticket').all():
        v = [x.inner_text() for x in m.locator('.v').all()]
        if len(v) == 3:
            tickets.append((int(v[0]), int(v[1]), v[2].strip()))
    return head, tickets, page.locator('#result').inner_text()


def check(page, card: dict, ac: int) -> dict:
    page.fill('#epic', card['epic'])
    page.click('#go')
    page.wait_for_function("() => !document.querySelector('#result .spin') && document.querySelector('#result').innerText.length > 0",
                           timeout=30000)
    head, tickets, text = shown(page)
    serials = {str(card['serial']), f"~{card['serial']}"}
    on_ticket = any(a == ac and p == card['part'] and s in serials for a, p, s in tickets)
    in_note = bool(re.search(rf"\b{ac} · \S+ {card['part']} · \S+(?: \S+)? {card['serial']}\b", text))
    ok = on_ticket or (card['deleted'] and in_note)
    return {'part': card['part'], 'serial': card['serial'], 'deleted': card['deleted'], 'ok': ok,
            'head': head, 'tickets': tickets}


def main() -> int:
    from playwright.sync_api import sync_playwright
    ap = argparse.ArgumentParser()
    ap.add_argument('acs', nargs='+', type=int)
    ap.add_argument('--shots', type=int, default=1)
    a = ap.parse_args()
    (SV / 'shots').mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1100, 'height': 1400})
        page.goto(SITE, wait_until='networkidle')
        built = page.evaluate("fetch('data/manifest.json').then(r => r.json()).then(m => m.builtAt)")
        for ac in a.acs:
            src = SV / f'svres-{ac}.json.gz'
            if not src.exists():
                release.TAG = SVR
                release.fetch(str(SV), [src.name])
            with gzip.open(src, 'rt', encoding='utf8') as f:
                res = json.load(f)
            out = []
            for i, card in enumerate(res['browser']):
                r = check(page, card, ac)
                out.append(r)
                if i < a.shots:
                    page.locator('#result').screenshot(path=str(SV / 'shots' / f'{ac}-{i}.png'))
            (SV / f'browser-{ac}.json').write_text(json.dumps({'ac': ac, 'builtAt': built, 'cards': out,
                                                               'at': time.strftime('%Y-%m-%dT%H:%M:%SZ')}), 'utf8')
            print(f'AC {ac}: {sum(r["ok"] for r in out)}/{len(out)} shown as expected on the live site '
                  f'(build {built})', flush=True)
        browser.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
