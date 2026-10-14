"""The drafting table for the ring's curved words. It sets the hand-drawn upright capitals (sprites.CAPS9)
along a dial's ring, each letter's pixels turned to the curve's angle at its place and dropped into the
nearest screen pixel, and writes the draft as text art to out/draft-<word>-<screen>.txt with a zoomed
preview. The drafts are a guide only: the letters are then drawn turned by hand, stroke by stroke and pixel
by pixel (proto/coverage.py prints how much of each pixel a turned letter covers, to check against), and
the finished art kept in sprites.WORDS, which is all the faces draw. Only a screen with no finished art
falls back to the draft.

    uv run python proto/letterer.py
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import sprites


def turn_pixels(ch, deg, x, y):
    """The upright capital's ink pixels, each pixel's centre turned `deg` degrees clockwise (on screen) about the
    letter's centre and the letter set with its centre at (x, y): the screen pixels they land in. Keeps the
    strokes' widths (a nearest-pixel turn), the draft for the hand to finish."""
    m = np.array([[c == "#" for c in r] for r in sprites.CAPS9[ch]])
    h, w = m.shape
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    out = set()
    for j, i in zip(*np.nonzero(m)):
        dx, dy = i + 0.5 - w / 2, j + 0.5 - h / 2
        out.add((int(math.floor(x + c * dx - s * dy)), int(math.floor(y + s * dx + c * dy))))
    return out


def layout(curve, word, gap=2):
    """Letter centres along `curve` (from plates.band_curve): [(letter, x, y, angle_deg)]."""
    widths = [len(sprites.CAPS9[ch][0]) for ch in word]
    total = sum(widths) + gap * (len(word) - 1)
    out, s = [], -total / 2
    for ch, w in zip(word, widths):
        x, y, g = curve(s + w / 2)
        out.append((ch, x, y, math.degrees(g)))
        s += w + gap
    return out


def draft_pixels(curve, word, top=True, gap=2):
    """The word set along the curve, every letter turned to its exact angle by turn_pixels: {letter index:
    pixels}."""
    return {k: turn_pixels(ch, g if top else -g, x, y) for k, (ch, x, y, g) in enumerate(layout(curve, word, gap))}


def draft_mask(curve, word, top=True, gap=2):
    """The draft as one drawing: (mask, left, top) on the screen."""
    px = set().union(*draft_pixels(curve, word, top, gap).values())
    x0, y0 = min(p[0] for p in px), min(p[1] for p in px)
    m = np.zeros((max(p[1] for p in px) - y0 + 1, max(p[0] for p in px) - x0 + 1), bool)
    for X, Y in px:
        m[Y - y0, X - x0] = True
    return m, x0, y0


def text_art(m):
    return ["".join("#" if v else "." for v in r) for r in m]


if __name__ == "__main__":
    from PIL import Image
    from plates import RectDial, band_curve, word_inset
    from render import Dial
    ROOT = Path(__file__).resolve().parents[1]
    for name, dial in (("round", Dial(260, 260, 40.71, -74.01)), ("time2", RectDial(200, 228, 40.71, -74.01))):
        for word, top in (("MIDNIGHT", True), ("NOON", False)):
            m, x0, y0 = draft_mask(band_curve(dial, word_inset(dial), top), word, top)
            art = text_art(m)
            (ROOT / "out" / f"draft-{word.lower()}-{name}.txt").write_text(f"# at ({x0}, {y0})\n" + "\n".join(art) + "\n")
            a = np.zeros(m.shape + (3,), np.uint8) + 230
            a[m] = (150, 0, 0)
            Image.fromarray(np.repeat(np.repeat(a, 10, 0), 10, 1)).save(ROOT / "out" / f"draft-{word.lower()}-{name}.png")
            print(name, word, (x0, y0), m.shape)
