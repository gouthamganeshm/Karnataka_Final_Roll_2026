"""A second, independent EPIC reader: glyph template matching.

The EPIC on every card is printed digitally in one fixed font, so each
character can be compared with a template of every letter and digit. This
fails in completely different ways from Tesseract — no language model, and it
must place exactly ten glyphs — which is what makes it useful as a referee.

Measured 2026-10-10: on four parts, two Tesseract readings *agreed* on wrong
EPICs (`WZU1594811` read as `WZZ…`, `TDB5006309` as `TDB0…`, `TDB4370342` as
`ITD…`); the template reader had all of them right.

The crops are only ~13 px tall, so neighbouring glyphs often touch and a
blank-column split finds 9 pieces, not 10. When that happens `read()` chooses
the cut points itself: it tries every cut at a low-ink column and keeps the
split into exactly ten glyphs whose template matches are best overall.

Templates are averaged from cards whose glyphs separate cleanly and whose
reading two Tesseract passes agreed on (`scripts/ocr/build_templates.py`), and
shipped as `templates.npz`.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

GH, GW = 24, 18           # every glyph is normalised into this box
ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGIT = '0123456789'
INK = 0.35
MIN_SAMPLES = 20          # a letter seen fewer times than this has no template
DEFAULT_FILE = Path(__file__).with_name('templates.npz')


def text_band(crop: Image.Image) -> np.ndarray:
    """Ink array cut to the one horizontal band that holds the text.

    Some crops carry a fragment of a ruled line above the EPIC; that ink would
    otherwise be read as a glyph or block the cut search.
    """
    a = 1.0 - np.asarray(crop.convert('L'), dtype=np.float32) / 255.0
    rows = a.max(axis=1) > INK
    runs, start = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and start is None:
            start = y
        elif not v and start is not None:
            runs.append((start, y))
            start = None
    if not runs:
        return a[:0]
    s, e = max(runs, key=lambda r: a[r[0]:r[1]].sum())
    return a[s:e]


def _norm(g: np.ndarray) -> np.ndarray | None:
    """Trim to ink, fit into GH x GW keeping aspect, zero-mean unit-norm."""
    rows = np.where(g.max(axis=1) > INK)[0]
    cols = np.where(g.max(axis=0) > INK)[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    g = g[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    h, w = g.shape
    s = min(GH / h, GW / w)
    nh, nw = max(1, round(h * s)), max(1, round(w * s))
    im = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize((nw, nh), Image.BILINEAR)
    box = np.zeros((GH, GW), np.float32)
    y, x = (GH - nh) // 2, (GW - nw) // 2
    box[y:y + nh, x:x + nw] = np.asarray(im, np.float32) / 255.0
    v = (box - box.mean()).ravel()
    n = np.linalg.norm(v)
    return v / n if n else None


def clean_segments(a: np.ndarray) -> list[tuple[int, int]]:
    """Glyph spans separated by fully blank columns."""
    if a.size == 0:
        return []
    on = a.max(axis=0) > INK
    spans, start = [], None
    for x, v in enumerate(list(on) + [False]):
        if v and start is None:
            start = x
        elif not v and start is not None:
            spans.append((start, x))
            start = None
    return spans


class Templates:
    def __init__(self):
        self.sum: dict[str, np.ndarray] = {}
        self.n: dict[str, int] = {}
        self._mats = None

    # ------------------------------------------------------------ learning
    def add(self, crop: Image.Image, epic: str) -> bool:
        a = text_band(crop)
        spans = clean_segments(a)
        if len(spans) != 10:
            return False
        vs = [_norm(a[:, s:e]) for s, e in spans]
        if any(v is None for v in vs):
            return False
        for ch, v in zip(epic, vs):
            self.sum[ch] = self.sum.get(ch, 0) + v
            self.n[ch] = self.n.get(ch, 0) + 1
        self._mats = None
        return True

    def merge(self, other: 'Templates') -> None:
        for ch in other.sum:
            self.sum[ch] = self.sum.get(ch, 0) + other.sum[ch]
            self.n[ch] = self.n.get(ch, 0) + other.n[ch]
        self._mats = None

    def save(self, path: Path = DEFAULT_FILE) -> None:
        chars = sorted(self.sum)
        np.savez_compressed(path, chars=np.array(chars),
                            sums=np.stack([self.sum[c] for c in chars]),
                            counts=np.array([self.n[c] for c in chars]))

    @classmethod
    def load(cls, path: Path = DEFAULT_FILE) -> 'Templates':
        t = cls()
        z = np.load(path)
        for c, s, n in zip(z['chars'], z['sums'], z['counts']):
            t.sum[str(c)] = s.astype(np.float32)
            t.n[str(c)] = int(n)
        return t

    # ------------------------------------------------------------- reading
    def _matrices(self):
        if self._mats is None:
            out = []
            for alphabet in (ALPHA, DIGIT):
                chars = [c for c in alphabet if self.n.get(c, 0) >= MIN_SAMPLES]
                if chars:
                    m = np.stack([self.sum[c] / self.n[c] for c in chars])
                    m /= np.linalg.norm(m, axis=1, keepdims=True)
                else:
                    m = np.zeros((0, GH * GW), np.float32)
                out.append((chars, m))
            self._mats = out
        return self._mats

    def _classify(self, v: np.ndarray, pos: int):
        (achars, am), (dchars, dm) = self._matrices()
        chars, m = (achars, am) if pos < 3 else (dchars, dm)
        if not chars:
            return None
        sc = m @ v
        o = np.argsort(sc)[::-1]
        second = sc[o[1]] if len(o) > 1 else -1.0
        return chars[o[0]], float(sc[o[0]]), float(sc[o[0]] - second)

    def read(self, crop: Image.Image) -> tuple[str | None, float, float]:
        """(EPIC, weakest match score, weakest best-vs-runner-up margin)."""
        d = self.read_detail(crop)
        if d is None:
            return None, 0.0, 0.0
        return ''.join(r[0] for r in d), min(r[1] for r in d), min(r[2] for r in d)

    def read_detail(self, crop: Image.Image) -> list[tuple[str, float, float]] | None:
        """Per character: (best character, its match score, lead over runner-up)."""
        a = text_band(crop)
        spans = clean_segments(a)
        if not spans or len(spans) > 10:
            return None
        if len(spans) == 10:                       # the common, fast case
            res = []
            for pos, (s, e) in enumerate(spans):
                v = _norm(a[:, s:e])
                r = self._classify(v, pos) if v is not None else None
                if r is None:
                    return None
                res.append(r)
            return res
        return self._read_touching(a, spans)

    def _read_touching(self, a: np.ndarray, spans):
        h, w = a.shape
        colink = a.sum(axis=0)
        cuts = {spans[0][0], spans[-1][1]}
        for s, e in spans:
            cuts.update((s, e))
            if e - s > 0.75 * h:                  # wide run: glyphs touch inside it
                for x in range(s + 2, e - 1):
                    if colink[x] <= colink[x - 1] and colink[x] <= colink[x + 1]:
                        cuts.add(x)
        cuts = sorted(cuts)
        on = a.max(axis=0) > INK
        maxw = int(1.4 * h) + 2
        n = len(cuts)
        cache = {}

        def score(i, j, pos):
            key = (i, j, pos < 3)
            if key not in cache:
                s, e = cuts[i], cuts[j]
                if e - s > maxw or not on[s:e].any():
                    cache[key] = None
                else:
                    v = _norm(a[:, s:e])
                    cache[key] = self._classify(v, pos) if v is not None else None
            return cache[key]

        NEG = -1e9
        best = [[NEG] * n for _ in range(11)]
        back = [[None] * n for _ in range(11)]
        best[0][0] = 0.0
        for k in range(1, 11):
            for j in range(1, n):
                for i in range(j):
                    if best[k - 1][i] == NEG:
                        continue
                    # Glyphs may be separated by blank gaps, but no ink may be skipped.
                    r = score(i, j, k - 1)
                    if r is None:
                        continue
                    t = best[k - 1][i] + r[1]
                    if t > best[k][j]:
                        best[k][j] = t
                        back[k][j] = (i, r)
        j = n - 1
        if best[10][j] == NEG:
            return None
        out = []
        for k in range(10, 0, -1):
            i, r = back[k][j]
            out.append(r)
            j = i
        out.reverse()
        return out
