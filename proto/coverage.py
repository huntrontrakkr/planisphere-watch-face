"""A guide for drawing the curved words by hand: how much of each screen pixel each letter covers when the
upright capital (sprites.CAPS9) is turned to its exact place on the ring, printed as digits 0-9.

    uv run python proto/coverage.py round MIDNIGHT"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import sprites
import letterer
from plates import RectDial, RoundDial, band_curve, word_inset


def coverage(dial, word, top, ss=12):
    curve = band_curve(dial, word_inset(dial), top)
    cov = {}
    for ch, x, y, g in letterer.layout(curve, word):
        m = np.array([[c == "#" for c in r] for r in sprites.CAPS9[ch]])
        h, w = m.shape
        th = math.radians(g if top else -g)
        c, s = math.cos(th), math.sin(th)
        for j in range(int(y) - 10, int(y) + 11):
            for i in range(int(x) - 10, int(x) + 11):
                n = 0
                for sj in range(ss):
                    for si in range(ss):
                        px, py = i + (si + 0.5) / ss - x, j + (sj + 0.5) / ss - y
                        u, v = c * px + s * py + w / 2, -s * px + c * py + h / 2
                        if 0 <= u < w and 0 <= v < h and m[int(v), int(u)]:
                            n += 1
                if n:
                    cov[(i, j)] = max(cov.get((i, j), 0), n / ss / ss)
    return cov


if __name__ == "__main__":
    screen, word = sys.argv[1], sys.argv[2]
    dial = RoundDial(260, 260, 40.71, -74.01) if screen == "round" else RectDial(200, 228, 40.71, -74.01)
    top = word == "MIDNIGHT"
    cov = coverage(dial, word, top)
    xs = [k[0] for k in cov]; ys = [k[1] for k in cov]
    print(f"# x {min(xs)}..{max(xs)}  y {min(ys)}..{max(ys)}")
    for j in range(min(ys), max(ys) + 1):
        print(f"{j:4d} " + "".join(str(min(9, int(cov.get((i, j), 0) * 10))) if cov.get((i, j), 0) > 0.05 else "." for i in range(min(xs), max(xs) + 1)))
