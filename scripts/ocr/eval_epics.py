"""Where do the original read and the consensus read disagree, and who is right?

    python -I scripts/ocr/eval_epics.py OUT_DIR part.pdf [part.pdf ...]

For every card whose consensus EPIC differs from the original single read, or
was withheld, writes the crop with both readings into OUT_DIR/review.png so a
person can check them against the image. Prints counts and timings.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crops as C  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
review = []
tot = {'cards': 0, 'changed': 0, 'withheld': 0, 'legacy_valid': 0, 'agreed': 0}
t_legacy = t_cons = 0.0
for path in sys.argv[2:]:
    pages = C.cut_part_bytes(open(path, 'rb').read())
    kept = [e for ep, _ in pages for e in ep if e is not None]

    C.EPIC_MODE = 'legacy'
    t = time.perf_counter()
    legacy = C.ocr_pages(pages)
    t_legacy += time.perf_counter() - t

    C.EPIC_MODE = 'consensus'
    t = time.perf_counter()
    cons = C.ocr_pages(pages)
    t_cons += time.perf_counter() - t

    name = os.path.basename(path)
    for i, ((lr, lok), (cr, cok)) in enumerate(zip(legacy, cons)):
        tot['cards'] += 1
        tot['legacy_valid'] += bool(C.R.EPIC_RE.match(C.R.coerce_epic(lr.epic)))
        tot['agreed'] += cok
        legacy_epic = C.R.coerce_epic(lr.epic)
        if not cok:
            tot['withheld'] += 1
            review.append((kept[i], f'{name} #{i}  legacy={legacy_epic}  consensus=WITHHELD ({cr.epic})'))
        elif cr.epic != legacy_epic:
            tot['changed'] += 1
            review.append((kept[i], f'{name} #{i}  legacy={legacy_epic}  consensus={cr.epic}'))

print(tot)
print(f'time: legacy {t_legacy:.0f}s, consensus {t_cons:.0f}s for {tot["cards"]} cards')
if review:
    rows = []
    for crop, label in review:
        big = crop.resize((crop.width * 2, crop.height * 2))
        canvas = Image.new('L', (max(700, big.width + 20), big.height + 30), 255)
        canvas.paste(big, (10, 22))
        ImageDraw.Draw(canvas).text((10, 4), label, fill=0)
        rows.append(canvas)
    sheet = Image.new('L', (max(r.width for r in rows), sum(r.height for r in rows)), 255)
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    sheet.save(os.path.join(out_dir, 'review.png'))
    print('review image:', os.path.join(out_dir, 'review.png'), len(review), 'cards')
