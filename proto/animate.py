"""The face's animations, each a second or a few, then still again (a watch has no battery for more):

  meteors      now and then at night a falling star; at a shower's peak, many, streaking out from its radiant
  birds        now and then by day a little flock crossing the sky, wings beating
  the turn     at the top of the hour the star disc spins through a whole day and settles back to now, as a
               planisphere turns in the hand

    uv run python proto/animate.py          # writes docs/anim-*.gif, at the watch's own frame rate
"""
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import astro
import sprites
from plates import render, RectDial, RoundDial, NY
from render import load_sky
from render2 import c8

ROOT = Path(__file__).resolve().parents[1]
FPS = 12
TRAIL = [c8(3, 3, 3), c8(3, 3, 3), c8(3, 3, 3), c8(3, 3, 2), c8(3, 3, 2), c8(3, 3, 2), c8(2, 2, 2), c8(2, 2, 2),
         c8(2, 2, 2), c8(1, 1, 2), c8(1, 1, 2), c8(1, 1, 2)]


def line_pixels(x0, y0, x1, y1):
    """The pixels along a line, in order from (x0, y0), each once."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    out = []
    for k in range(n + 1):
        t = k / n
        p = (int(math.floor(x0 + (x1 - x0) * t)), int(math.floor(y0 + (y1 - y0) * t)))
        if not out or out[-1] != p:
            out.append(p)
    return out


def meteor(img, inside, m, frame):
    """A falling star, `m` = (start frame, x, y, angle, length, frames): its bright head moving along its path,
    the trail behind it fading into the sky, and at the end the whole of it dimming out."""
    k = frame - m[0]
    if not 0 <= k < m[5]:
        return
    _, x, y, a, L, n = m
    dx, dy = math.cos(a), math.sin(a)
    head = L * (k + 1) / n
    tail = max(0.0, head - L * 0.7)
    pts = line_pixels(x + dx * head, y + dy * head, x + dx * tail, y + dy * tail)
    fade = max(0, k - (n - 3))                           # the last frames, one step dimmer each
    H, W = inside.shape
    for i, (px, py) in reversed(list(enumerate(pts))):
        c = TRAIL[min(len(TRAIL) - 1, i + fade)]
        if 0 <= px < W and 0 <= py < H and inside[py, px]:
            img[py, px] = c
    if fade == 0 and pts:                                # the head burning bright, a small cross of light
        hx, hy = pts[0]
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= hx + ox < W and 0 <= hy + oy < H and inside[hy + oy, hx + ox]:
                img[hy + oy, hx + ox] = c8(3, 3, 2)


def meteors_for(seed, frames, ctx_guess, radiant=None, count=6):
    """Falling stars across `frames`: from the radiant outward if a shower is at its peak, else here and there."""
    rng = np.random.default_rng(seed)
    out = []
    for i in range(count):
        start = int(rng.uniform(0, frames - 10))
        if radiant is not None and i < count - 1:
            a = rng.uniform(0, 2 * math.pi)
            r0 = rng.uniform(9, 26)
            x, y = radiant[0] + r0 * math.cos(a), radiant[1] + r0 * math.sin(a)
        else:
            x, y = ctx_guess[0] + rng.uniform(-40, 40), ctx_guess[1] + rng.uniform(-30, 30)
            a = rng.uniform(0, 2 * math.pi)
        out.append((start, x, y, a, rng.uniform(18, 32), int(rng.uniform(6, 9))))
    return out


def birds(img, inside, colour, frame, y0, x_from, x_to, frames, wing=3):
    """A flock of four in a loose V crossing from x_from to x_to over `frames` frames, wings beating."""
    H, W = inside.shape
    x = x_from + (x_to - x_from) * frame / frames
    for j, (ox, oy) in enumerate(((0, 0), (-7, 3), (-7, -4), (-14, 6))):
        drawing = sprites.BIRD[((frame // wing) + j) % 2]
        bx, by = int(round(x + ox * np.sign(x_to - x_from))), int(round(y0 + oy + math.sin(frame / 4 + j) * 0.8))
        for r, c in zip(*np.nonzero(drawing)):
            X, Y = bx - 2 + c, by - 1 + r
            if 0 <= X < W and 0 <= Y < H and inside[Y, X]:
                img[Y, X] = colour


def save(frames, path, size):
    pal = [Image.fromarray(f).resize(size, Image.NEAREST).quantize(colors=64, method=Image.Quantize.MEDIANCUT,
                                                                    dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0, optimize=True)


def main():
    sky = load_sky(4.6)
    t2 = RectDial(200, 228, 40.71, -74.01)
    r2 = RoundDial(260, 260, 40.71, -74.01)

    # meteors: the Orionids' peak night, falling stars from their radiant (and one stray)
    when = datetime(2026, 10, 22, 2, 0, tzinfo=NY).astimezone(timezone.utc)
    lst = astro.sidereal(when, t2.lon)
    rad = t2.project(95.0, 16.0, lst)
    falls = meteors_for(7, 96, (t2.cx, t2.cy + 20), radiant=rad, count=7)
    frames = [render(when, t2, sky, NY, "planisphere", False,
                     extras=lambda img, ctx, k=k: [meteor(img, ctx["inside"], m, k) for m in falls]) for k in range(96)]
    save(frames, ROOT / "docs" / "anim-meteors.gif", (400, 456))

    # birds: a flock crossing the day sky
    when = datetime(2026, 10, 14, 11, 20, tzinfo=NY).astimezone(timezone.utc)
    frames = [render(when, t2, sky, NY, "planisphere", False,
                     extras=lambda img, ctx, k=k: birds(img, ctx["inside"], c8(0, 0, 1), k, 128, 20, 190, 72))
              for k in range(72)]
    save(frames, ROOT / "docs" / "anim-birds.gif", (400, 456))

    # the turn: at the top of the hour the sky spins through a day and back to now; the clock keeps its time
    when = datetime(2026, 10, 14, 21, 0, tzinfo=NY).astimezone(timezone.utc)
    for name, dial, rnd, size in (("time2", t2, False, (400, 456)), ("round2", r2, True, (390, 390))):
        frames = [render(when, dial, sky, NY, "planisphere", rnd) for _ in range(1)] * 10
        n = 40
        for k in range(1, n):
            ease = (1 - math.cos(math.pi * k / n)) / 2         # slow away, fast through the day, slow home
            frames.append(render(when, dial, sky, NY, "planisphere", rnd, sky_offset=timedelta(hours=24 * ease),
                                 names=False))
        frames += [render(when, dial, sky, NY, "planisphere", rnd)] * 12
        save(frames, ROOT / "docs" / f"anim-turn-{name}.gif", size)
    print("ok")


if __name__ == "__main__":
    main()
