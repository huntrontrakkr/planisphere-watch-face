"""What a feast day brings to the face beyond its name on the almanac's line (proto/feasts.py says which day is
which): fireworks over the village, fires on the hills, a light in every window. Drawn with the watch's own random
numbers (rng.py), so its C can follow.
"""
import math

import numpy as np

from rng import Rng


def c8(r, g, b):
    return np.array([r * 85, g * 85, b * 85])


# the fireworks' colours, by the feast's tradition
SPARKS = {
    "independence": (c8(3, 0, 0), c8(3, 3, 3), c8(1, 2, 3)),          # red, white and blue
    "bonfire": (c8(3, 3, 1), c8(3, 2, 0), c8(3, 3, 3)),               # gold, orange, white
    "new year": (c8(3, 3, 1), c8(3, 3, 3), c8(3, 1, 1), c8(1, 3, 1)),
}


def _free(avoid, inside, x0, y0, x1, y1):
    """A box wholly in the window and clear of everything drawn there (and a pixel round it)."""
    H, W = inside.shape
    if x0 < 1 or y0 < 1 or x1 >= W - 1 or y1 >= H - 1:
        return False
    if not inside[y0:y1 + 1, x0:x1 + 1].all():
        return False
    return not avoid[y0 - 1:y1 + 2, x0 - 1:x1 + 2].any()


def fireworks(img, inside, avoid, edge, col, sparks, seed, ink=None):
    """Bursts over the village in the evening: each a rocket's dotted trail rising and a ring of sparks, in the clear
    sky between the names and the stars. `ink` (one colour) for a printed chart, where they are engraved."""
    H, W = inside.shape
    rng = Rng(seed)
    placed = 0
    for _ in range(60):
        if placed == 3:
            break
        R = rng.integers(7, 11)
        dx = rng.integers(-60, 61)
        rise = rng.integers(36, 110)                      # how high over the window's foot there
        if dx not in edge:
            continue
        cx, cy = col + dx, edge[dx] - rise
        if not _free(avoid, inside, cx - R - 2, cy - R - 2, cx + R + 2, cy + R + 4):
            continue
        n = 16 if R >= 9 else 12
        turn = rng.random() * math.pi / n
        colours = [ink] if ink is not None else list(sparks)
        first = rng.integers(0, len(colours))
        for k in range(n):
            a = turn + 2 * math.pi * k / n
            colour = colours[(first + k) % len(colours)] if len(colours) > 1 else colours[0]
            # each spark a short stroke at the burst's edge, an inner ring of single sparks, and the lower ones
            # falling a pixel more (the willow's droop)
            droop = 1 if math.cos(a) < -0.5 else 0
            for r in (R - 4, R - 1, R):
                if r == R - 4 and k % 2:
                    continue
                x, y = int(round(cx + r * math.sin(a))), int(round(cy - r * math.cos(a))) + (droop if r == R else 0)
                if 0 <= y < H and 0 <= x < W and inside[y, x]:
                    img[y, x] = colour
                    avoid[y, x] = True
        img[cy, cx] = ink if ink is not None else c8(3, 3, 3)
        # the rocket's last climb: a short dotted trail under the burst
        trail = ink if ink is not None else c8(2, 1, 0)
        for y in range(cy + R + 3, cy + R + 14, 2):
            if 0 <= y < H and inside[y, cx] and not avoid[y, cx]:
                img[y, cx] = trail
        placed += 1


FLAME = ["..Y..",                                          # a fire on the hill: its flame, a spark over it
         ".YOY.",
         ".ORO.",
         "ORRRO"]
FLAME_C = {"Y": c8(3, 3, 1), "O": c8(3, 2, 0), "R": c8(3, 0, 0)}


def bonfires(img, inside, edge, heights, col, seed, ink=None):
    """Fires on the hilltops either side of the village, as the old fire festivals lit them: on the three highest
    tops at least twenty pixels from the church, each with a spark that moves with the minute."""
    H, W = inside.shape
    rng = Rng(seed)
    tops = sorted(((h, dx) for dx, h in heights.items() if abs(dx) >= 20 and h >= 3), reverse=True)
    chosen = []
    for h, dx in tops:
        if all(abs(dx - c) >= 18 for c in chosen):
            chosen.append(dx)
        if len(chosen) == 3:
            break
    for dx in chosen:
        x0, base = col + dx - 2, edge[dx] - heights[dx]
        if ink is None:                                    # the fire's glow on the hill and the sky round it
            for j in range(-6, 2):
                for i in range(-4, 9):
                    y, x = base + j, x0 + i
                    d = math.hypot(i - 2, (j + 2) * 1.3)
                    if 0 <= y < H and 0 <= x < W and inside[y, x] and d < 5.2 and (i + j) % 2 == 0:
                        img[y, x] = c8(2, 1, 0) if d < 3.5 else c8(1, 0, 0)
        for j, row in enumerate(FLAME):
            for i, ch in enumerate(row):
                y, x = base - len(FLAME) + 1 + j, x0 + i
                if ch != "." and 0 <= y < H and 0 <= x < W and inside[y, x]:
                    img[y, x] = ink if ink is not None else FLAME_C[ch]
        y, x = base - len(FLAME) - 1 - rng.integers(0, 3), x0 + 2 + rng.integers(-1, 2)
        if 0 <= y < H and 0 <= x < W and inside[y, x]:
            img[y, x] = ink if ink is not None else FLAME_C["Y"]
