"""Glyph-template readers for the EPIC: the font-matching half of the reading.

The EPIC on every card is printed digitally in one fixed font, so each
character can be compared with a template of every letter and digit. This
fails in completely different ways from Tesseract — no language model, and it
must place exactly ten glyphs — which is what makes it useful next to it.

Measured 2026-10-10: on four parts, two Tesseract readings *agreed* on wrong
EPICs (`WZU1594811` read as `WZZ…`, `TDB5006309` as `TDB0…`, `TDB4370342` as
`ITD…`); the template reader had all of them right.

Two readers live here:

* `Templates` — the main reader. Each glyph is trimmed to its ink and fitted
  into a fixed box; one mean template per character.
* `Prototypes` — the verifier's second opinion. Each glyph keeps its height and
  place inside the text line (so `1`, `I` and `L` keep their real widths and
  positions), and every character has several prototypes (k-means), so it is
  a genuinely different classifier, not the first one re-run.

The crops are only ~13 px tall, so neighbouring glyphs often touch and a
blank-column split finds 9 pieces, not 10. When that happens the reader picks
the cut points itself: it tries every cut at a low-ink column and keeps the
split into exactly ten glyphs whose template matches are best overall.

Template sets are per rendering ("style"): the Kannada roll prints EPICs ~13 px
tall, the English roll ~18 px in a heavier weight. `templates.npz` is the
Kannada set, `templates-eng.npz` the English one.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

GH, GW = 24, 18           # every glyph is normalised into this box (main reader)
PH, PW = 24, 24           # ...and into this one by the prototype reader
ALPHA = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DIGIT = '0123456789'
INK = 0.35
MIN_SAMPLES = 20          # a letter seen fewer times than this has no template
HERE = Path(__file__).parent
DEFAULT_FILE = HERE / 'templates.npz'


def template_file(style: str = 'kan', kind: str = 'templates') -> Path:
    """templates.npz / templates-eng.npz / prototypes.npz / prototypes-eng.npz"""
    return HERE / (f'{kind}.npz' if style == 'kan' else f'{kind}-{style}.npz')


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


def _norm_line(g: np.ndarray) -> np.ndarray | None:
    """The prototype reader's view of a glyph: the full text-band height is kept
    (no vertical trim), scaled to PH, width scaled by the same factor and the
    glyph centred in PW. Narrow and wide glyphs stay narrow and wide."""
    cols = np.where(g.max(axis=0) > INK)[0]
    if len(cols) == 0:
        return None
    g = g[:, cols[0]:cols[-1] + 1]
    h, w = g.shape
    s = PH / h
    nw = max(1, min(PW, round(w * s)))
    im = Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize((nw, PH), Image.BILINEAR)
    box = np.zeros((PH, PW), np.float32)
    x = (PW - nw) // 2
    box[:, x:x + nw] = np.asarray(im, np.float32) / 255.0
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


# Two pairs the template averages cannot tell apart reliably at ~13 px, each
# settled instead by the one stroke that differs (measured 2026-10-10 on the
# held-out half of the 224-part sample; no overlap in either):
#
#   O / Q   Q's tail puts ink in the glyph's bottom-right corner.
#           Kannada roll: O max 0.217, Q min 0.366 (1,500 of each).
#   6 / 8   8 closes its upper loop on the right; 6 leaves it open.
#           Kannada roll: 6 max 0.203, 8 min 0.362 (3,000 of each).
#
# The margin reported is the feature's distance from the threshold, so a glyph
# that sits between the two clusters gets a small margin and `crops.fuse`
# will not accept it without Tesseract's support.
def _trim(g: np.ndarray) -> np.ndarray:
    rows = np.where(g.max(axis=1) > INK)[0]
    cols = np.where(g.max(axis=0) > INK)[0]
    return g[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1] if len(rows) and len(cols) else g


def tail_ink(g: np.ndarray) -> float:
    t = _trim(g)
    return float(t[-2:, -2:].mean())


def upper_loop_ink(g: np.ndarray) -> float:
    t = _trim(g)
    h, w = t.shape
    return float(t[int(round(h * 0.22)):int(round(h * 0.42)), int(w * 0.6):].mean())


PAIR_RULES = {   # style -> pair -> (feature, threshold, char when feature >= threshold)
    'kan': {'OQ': (tail_ink, 0.29, 'Q'), '68': (upper_loop_ink, 0.28, '8')},
}


def pair_of(style: str, ch: str) -> str | None:
    for pair in PAIR_RULES.get(style, {}):
        if ch in pair:
            return pair
    return None


def _outside(chars: list[str], scores: np.ndarray, order, style: str) -> float:
    """Lead of the best character over the best one *outside* its O/Q or 6/8
    pair — what is left of the margin once the pair is settled by stroke."""
    pair = pair_of(style, chars[order[0]])
    rest = [scores[i] for i in order[1:] if not (pair and chars[i] in pair)]
    return float(scores[order[0]] - (rest[0] if rest else -2.0))


def refine(style: str, ch: str, score: float, margin: float, outside: float, g: np.ndarray):
    """Settle O/Q and 6/8 by their distinguishing stroke (see PAIR_RULES).

    Returns (character, score, margin). For a pair character the margin is the
    smaller of the stroke test's own distance from its threshold and the lead
    over every character outside the pair: a G that the templates mistake for
    an O must not become a confident Q just because G has a tail-like curve.
    """
    pair = pair_of(style, ch)
    if pair:
        feature, threshold, high = PAIR_RULES[style][pair]
        f = feature(g)
        low = pair.replace(high, '')
        return (high if f >= threshold else low), score, min(abs(f - threshold), outside)
    return ch, score, margin


class Reading(list):
    """Per-character (character, score, margin) tuples, plus how the glyphs
    were found. `touching` is True when the ten glyphs were not separated by
    blank columns and the reader chose the cut points itself. The prototype
    reader reads the same cut, so on such a crop the two are one witness, not
    two independent ones (`crops.fuse` treats them that way)."""
    touching = False
    own_cut = False           # a prototype reading on a cut it chose itself


class Templates:
    def __init__(self, style: str = 'kan'):
        self.style = style
        self.sum: dict[str, np.ndarray] = {}
        self.n: dict[str, int] = {}
        self._mats = None

    # ------------------------------------------------------------ learning
    def add(self, crop: Image.Image, epic: str, relabel: bool = False) -> bool:
        """Average this card's ten glyphs into the templates. `relabel` lets the
        O/Q and 6/8 stroke tests override the given label for those pairs."""
        a = text_band(crop)
        spans = clean_segments(a)
        if len(spans) != 10:
            return False
        vs = [_norm(a[:, s:e]) for s, e in spans]
        if any(v is None for v in vs):
            return False
        if relabel:
            epic = ''.join(refine(self.style, ch, 0.0, 0.0, 1.0, a[:, s:e])[0]
                           for ch, (s, e) in zip(epic, spans))
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
    def load(cls, path: Path = DEFAULT_FILE, style: str = 'kan') -> 'Templates':
        t = cls(style)
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

    def _classify(self, v: np.ndarray | None, pos: int):
        if v is None:
            return None
        (achars, am), (dchars, dm) = self._matrices()
        chars, m = (achars, am) if pos < 3 else (dchars, dm)
        if not chars:
            return None
        sc = m @ v
        o = np.argsort(sc)[::-1]
        second = sc[o[1]] if len(o) > 1 else -1.0
        return chars[o[0]], float(sc[o[0]]), float(sc[o[0]] - second), _outside(chars, sc, o, self.style)

    def read(self, crop: Image.Image) -> tuple[str | None, float, float]:
        """(EPIC, weakest match score, weakest best-vs-runner-up margin)."""
        d = self.read_detail(crop)
        if d is None:
            return None, 0.0, 0.0
        return ''.join(r[0] for r in d), min(r[1] for r in d), min(r[2] for r in d)

    def read_detail(self, crop: Image.Image, spans_out: list | None = None,
                    force_search: bool = False) -> list[tuple[str, float, float]] | None:
        """Per character: (best character, its match score, lead over runner-up).

        `spans_out`, if given, receives the text band and the ten glyph spans
        chosen, so a second classifier can look at the same glyphs.
        `force_search` makes even a cleanly separated crop go through the cut
        search (the verifier uses this as an independent segmentation).
        """
        a = text_band(crop)
        spans = clean_segments(a)
        if not spans or len(spans) > 10:
            return None
        if len(spans) == 10 and not force_search:      # the common, fast case
            res = []
            for pos, (s, e) in enumerate(spans):
                v = _norm(a[:, s:e])
                r = self._classify(v, pos) if v is not None else None
                if r is None:
                    return None
                res.append(refine(self.style, *r, a[:, s:e]))
            if spans_out is not None:
                spans_out[:] = [a, spans]
            return Reading(res)
        found = self._read_touching(a, spans)
        if found is None:
            return None
        res, chosen = found
        res = Reading(refine(self.style, *r, a[:, s:e]) for r, (s, e) in zip(res, chosen))
        res.touching = True
        if spans_out is not None:
            spans_out[:] = [a, chosen]
        return res

    def _read_touching(self, a: np.ndarray, spans):
        return best_cut(a, spans, lambda g, pos: self._classify(_norm(g), pos))


def best_cut(a: np.ndarray, spans, classify):
    """Split a text band whose glyphs touch into exactly ten glyphs.

    Candidate cuts are the blank-column boundaries plus every local minimum of
    column ink inside a run too wide to be one glyph; dynamic programming keeps
    the ten-glyph split whose match scores add up best. `classify(glyph, pos)`
    returns (character, score, ...) or None. Returns (results, spans) or None.
    """
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
                cache[key] = classify(a[:, s:e], pos)
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
    out, chosen = [], []
    for k in range(10, 0, -1):
        i, r = back[k][j]
        out.append(r)
        chosen.append((cuts[i], cuts[j]))
        j = i
    out.reverse()
    chosen.reverse()
    return out, chosen


class Prototypes:
    """Several prototypes per character, on the line-preserving glyph view."""

    def __init__(self, protos: dict[str, np.ndarray] | None = None, style: str = 'kan'):
        self.protos = protos or {}
        self.style = style
        self._mats = None

    @staticmethod
    def vectors(band: np.ndarray, spans) -> list[np.ndarray | None]:
        return [_norm_line(band[:, s:e]) for s, e in spans]

    @classmethod
    def learn(cls, samples: dict[str, list[np.ndarray]], k: int = 6, iters: int = 12,
              cap: int = 4000, seed: int = 0) -> 'Prototypes':
        rng = np.random.default_rng(seed)
        protos = {}
        for ch, vs in samples.items():
            if len(vs) < MIN_SAMPLES:
                continue
            x = np.stack(vs)
            if len(x) > cap:
                x = x[rng.choice(len(x), cap, replace=False)]
            kk = min(k, max(1, len(x) // 20))
            c = x[rng.choice(len(x), kk, replace=False)]
            for _ in range(iters):            # spherical k-means
                lab = np.argmax(x @ c.T, axis=1)
                for j in range(kk):
                    m = x[lab == j]
                    if len(m):
                        v = m.mean(axis=0)
                        c[j] = v / (np.linalg.norm(v) or 1)
            protos[ch] = c.astype(np.float32)
        return cls(protos)

    def save(self, path: Path) -> None:
        chars = sorted(self.protos)
        np.savez_compressed(path, chars=np.array(chars),
                            counts=np.array([len(self.protos[c]) for c in chars]),
                            protos=np.concatenate([self.protos[c] for c in chars]))

    @classmethod
    def load(cls, path: Path, style: str = 'kan') -> 'Prototypes':
        z = np.load(path)
        out, i = {}, 0
        for c, n in zip(z['chars'], z['counts']):
            out[str(c)] = z['protos'][i:i + int(n)].astype(np.float32)
            i += int(n)
        return cls(out, style)

    def _matrices(self):
        if self._mats is None:
            out = []
            for alphabet in (ALPHA, DIGIT):
                chars = [c for c in alphabet if c in self.protos]
                owner = np.array([ci for ci, c in enumerate(chars) for _ in self.protos[c]])
                m = np.concatenate([self.protos[c] for c in chars]) if chars else np.zeros((0, PH * PW))
                out.append((chars, owner, m))
            self._mats = out
        return self._mats

    def classify(self, v: np.ndarray | None, pos: int):
        """(character, score, margin over the best *other* character)."""
        if v is None:
            return None
        chars, owner, m = self._matrices()[0 if pos < 3 else 1]
        if not chars:
            return None
        sc = m @ v
        best = np.full(len(chars), -2.0)
        np.maximum.at(best, owner, sc)
        o = np.argsort(best)[::-1]
        return (chars[o[0]], float(best[o[0]]), float(best[o[0]] - (best[o[1]] if len(o) > 1 else -2.0)),
                _outside(chars, best, o, self.style))

    def read(self, band: np.ndarray, spans) -> list[tuple[str, float, float]] | None:
        out = []
        for pos, (v, (s, e)) in enumerate(zip(self.vectors(band, spans), spans)):
            r = self.classify(v, pos)
            if r is None:
                return None
            out.append(refine(self.style, *r, band[:, s:e]))
        return Reading(out)

    def read_touching(self, band: np.ndarray) -> 'Reading | None':
        """Read a band whose glyphs touch by choosing the cut itself, with its
        own scores, so it can disagree with the template reader's cut: an
        independent witness on exactly the crops where one is needed."""
        spans = clean_segments(band)
        if not spans or len(spans) > 10:
            return None
        found = best_cut(band, spans, lambda g, pos: self.classify(_norm_line(g), pos))
        if found is None:
            return None
        res, chosen = found
        out = Reading(refine(self.style, *r, band[:, s:e]) for r, (s, e) in zip(res, chosen))
        out.touching = out.own_cut = True
        return out
