"""The split must be invisible: cut at home + OCR on Actions has to produce the
same rows, in the same order, as `roll_ocr.read_part_bytes` on the same PDF.

    python -I scripts/ocr/test_crops.py part1.pdf part2.pdf ...

Also reports what the split buys: home-side time, Actions-side time, and the
bundle size the home connection has to upload instead of the PDF.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crops as C
import roll_ocr as R

failed = 0
tot_pdf = tot_bundle = tot_cut = tot_ocr = tot_ref = 0.0
for path in sys.argv[1:]:
    data = open(path, 'rb').read()

    t = time.perf_counter()
    ref = R.read_part_bytes(data)
    t_ref = time.perf_counter() - t

    t = time.perf_counter()
    bundle = C.write_bundle(C.cut_part_bytes(data), ac=0, part=0)
    t_cut = time.perf_counter() - t

    t = time.perf_counter()
    _, pages = C.read_bundle(bundle)
    got = C.ocr_pages(pages)
    t_ocr = time.perf_counter() - t

    same = [(r.serial, r.epic, r.ok) for r in ref] == [(r.serial, r.epic, r.ok) for r in got]
    diffs = sum(1 for a, b in zip(ref, got) if (a.serial, a.epic, a.ok) != (b.serial, b.epic, b.ok))
    diffs += abs(len(ref) - len(got))
    failed += not same
    tot_pdf += len(data); tot_bundle += len(bundle)
    tot_cut += t_cut; tot_ocr += t_ocr; tot_ref += t_ref
    print(f'{os.path.basename(path):14} rows={len(ref):4} ok={sum(r.ok for r in ref):4} '
          f'{"IDENTICAL" if same else f"DIFFERS ({diffs} rows)"}  '
          f'pdf={len(data)/1e6:5.1f}MB bundle={len(bundle)/1e3:5.0f}KB  '
          f'original={t_ref:5.1f}s  home-cut={t_cut:5.1f}s  actions-ocr={t_ocr:5.1f}s')

print(f'\nbundle is {tot_bundle/tot_pdf:.1%} of the PDF bytes; '
      f'home does {tot_cut/tot_ref:.0%} of the original CPU time, Actions {tot_ocr/tot_ref:.0%}')
sys.exit(1 if failed else 0)
