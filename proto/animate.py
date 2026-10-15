"""The face's animations, each a second or a few, then still again (a watch has no battery for more):

  meteors      now and then at night a falling star; at a shower's peak, many, streaking out from its radiant
  birds        now and then by day a little flock crossing the sky, wings beating
  the village  the hour and the season's passers-by: swallows on summer mornings, a bat at dusk, the owl on
               the church roof by night (fireflies on summer nights), leaves and geese in autumn
  the weather  rain and snow falling, the clouds drifting downwind, the mill's sails turning, chimney smoke
  the village  the hour and the season's passers-by: swallows on summer mornings, a bat at dusk, the owl on
               the church roof by night (fireflies on summer nights), leaves and geese in autumn
  the weather  rain and snow falling, the clouds drifting downwind, the mill's sails turning, chimney smoke
  the hour     at the top of the hour, one of two, as the owner chooses:
                 the constellations  the figures in the window traced one by one, star to star, each over a
                                     second, without their names (the ones just risen first), then fading back
                 the turn            the star disc spins through a whole day and settles back to now, as a
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
import json
from plates import render, RectDial, RoundDial, NY, window_mask
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


# ---- the hours and the seasons: what passes over the village ------------------------------------------------------
def village_top(ctx, i):
    """The screen point just above the skyline's column `i` (its first drawn pixel), or None outside the window."""
    land, bottoms = ctx["land"], ctx["bottoms"]
    if i not in bottoms:
        return None
    rows = np.nonzero(land[:, i])[0]
    j = int(rows.min()) if len(rows) else land.shape[0] - 1
    return ctx["land_x0"] + i, bottoms[i] - (land.shape[0] - 1 - j) - 1


def window_box(inside):
    ys, xs = np.nonzero(inside)
    return xs.min(), xs.max(), ys.min(), ys.max()


def paint_in(img, inside, drawing, x, y, colours):
    sprites.paint(img, drawing, int(round(x)), int(round(y)), colours, where=inside)


def swallows(img, ctx, frame):
    """Two swallows hawking low over the fields at dawn, in long swooping curves."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    cx = (x0 + x1) / 2
    colour = c8(0, 0, 0) if ctx["night_land"] else c8(0, 0, 1)
    for j, (ph, amp, spd) in enumerate(((0.0, 46, 1.0), (2.4, 38, 1.25))):
        t = frame / FPS * spd + ph
        x = cx + amp * math.sin(t * 1.05)
        y = y1 - 17 - 7 * math.sin(t * 2.2 + j) - 3 * math.cos(t * 0.7)
        paint_in(img, inside, sprites.SWALLOW[(frame // 2 + j) % 2], x, y, {1: colour})


def bat(img, ctx, frame):
    """A bat at dusk, jinking above the roofs."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    cx = (x0 + x1) / 2
    t = frame / FPS
    x = cx + 30 * math.sin(0.9 * t) + 6 * math.sin(5.3 * t)
    y = y1 - 21 + 6 * math.sin(1.7 * t) + 3 * math.sin(7.1 * t)
    paint_in(img, inside, sprites.BAT[frame % 2], x, y, {1: c8(0, 0, 0)})


def owl(img, ctx, frame, perch=51):
    """The owl on the church's roof by night, blinking now and then."""
    at = village_top(ctx, perch)
    if at is None:
        return
    x, y = at
    drawing = sprites.OWL[1 if frame % 40 in (26, 27, 28) else 0]
    sprites.paint(img, drawing, x - 1, y - drawing.shape[0] + 1, {1: ctx["silhouette"], 3: c8(3, 3, 1)}, anchor="corner",
                  where=ctx["inside"])


def fireflies(img, ctx, frame, n=12, seed=5):
    """Fireflies over the fields on a summer night: points of light low over the land, each glowing and going out
    in its own time, drifting a little."""
    inside, bottoms = ctx["inside"], ctx["bottoms"]
    rng = np.random.default_rng(seed)
    keys = sorted(bottoms)
    for k in range(n):
        i = keys[int(rng.integers(len(keys)))]
        ph, period = int(rng.integers(0, 30)), int(rng.integers(16, 26))
        rise = rng.uniform(3, 12)
        on = (frame + ph) % period
        if on >= 5:
            continue
        x = ctx["land_x0"] + i + 1.5 * math.sin(frame / 9 + k)
        y = bottoms[i] - ctx["land"].shape[0] + 2 - rise + math.sin(frame / 7 + 2 * k)
        X, Y = int(round(x)), int(round(y))
        if 0 <= Y < inside.shape[0] and 0 <= X < inside.shape[1] and inside[Y, X]:
            img[Y, X] = c8(3, 3, 1) if on in (1, 2, 3) else c8(2, 2, 0)


def falling_leaves(img, ctx, frame, n=7, seed=3):
    """Leaves loosed from the trees on an autumn day, tumbling, carried off by the wind."""
    inside = ctx["inside"]
    wsky = ctx["wsky"]
    push = -math.sin(math.radians(wsky.wind_from)) if wsky is not None else -0.6    # downwind, east to the left
    push *= 1.0 + (wsky.wind / 15 if wsky is not None else 0.6)
    rng = np.random.default_rng(seed)
    trees = [9, 39, 65, 85]
    colour = c8(3, 1, 0) if not ctx["night_land"] else ctx["silhouette"]
    for k in range(n):
        at = village_top(ctx, trees[k % len(trees)] + int(rng.integers(-1, 2)))
        if at is None:
            continue
        start = int(rng.integers(0, 40))
        t = (frame - start) / FPS
        if t < 0:
            continue
        x = at[0] - push * 9 * t + 2 * math.sin(3 * t + k)
        y = at[1] - 6 * math.sin(min(t, 1.2) * 1.3) + 5 * max(0, t - 1.2)
        paint_in(img, inside, sprites.FALLING_LEAF[(frame // 2 + k) % 4], x, y, {2: colour})


def geese(img, ctx, frame, frames, southward=True):
    """Geese in a long V on their way south in autumn (north in spring), their wings slow."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    f = frame / frames
    if southward:
        x, y = x0 - 20 + (x1 - x0 + 40) * f, y0 + 14 + (y1 - y0) * 0.45 * f
    else:
        x, y = x1 + 20 - (x1 - x0 + 40) * f, y1 - 30 - (y1 - y0) * 0.45 * f
    colour = c8(0, 0, 1)
    d = 1 if southward else -1
    for j in range(7):
        side = 1 if j % 2 else -1
        rank = (j + 1) // 2
        bx, by = x - d * 6 * rank, y + side * 4 * rank - d * 2 * rank
        paint_in(img, inside, sprites.BIRD[((frame // 4) + j) % 2], bx, by, {5: colour})


def passing(local, sun_alt, sun_rising, season, wsky):
    """Which of the passing things the hour and the season bring (the watch plays one now and then): swallows on
    summer mornings, bats on warm evenings, by night the owl (and fireflies on warm summer nights), by day birds,
    in autumn falling leaves and geese going south, in spring geese going north."""
    warm = wsky is None or wsky.wind < 40
    if sun_alt < -12:
        mild = wsky is None or True
        return ["owl"] + (["fireflies"] if season in ("leaf", "harvest") and warm else [])
    if -8 <= sun_alt < 8 and sun_rising and season in ("blossom", "leaf", "harvest"):
        return ["swallows"]
    if -10 <= sun_alt < 3 and not sun_rising and season in ("blossom", "leaf", "harvest", "turning"):
        return ["bat"]
    out = ["birds"]
    if season in ("turning", "autumn"):
        out += ["leaves", "geese south"]
    if season == "bare" and local.month in (2, 3) or season == "blossom" and local.month == 4:
        out += ["geese north"]
    return out


# ---- the hours and the seasons: what passes over the village ------------------------------------------------------
def village_top(ctx, i):
    """The screen point just above the skyline's column `i` (its first drawn pixel), or None outside the window."""
    land, bottoms = ctx["land"], ctx["bottoms"]
    if i not in bottoms:
        return None
    rows = np.nonzero(land[:, i])[0]
    j = int(rows.min()) if len(rows) else land.shape[0] - 1
    return ctx["land_x0"] + i, bottoms[i] - (land.shape[0] - 1 - j) - 1


def window_box(inside):
    ys, xs = np.nonzero(inside)
    return xs.min(), xs.max(), ys.min(), ys.max()


def paint_in(img, inside, drawing, x, y, colours):
    sprites.paint(img, drawing, int(round(x)), int(round(y)), colours, where=inside)


def swallows(img, ctx, frame):
    """Two swallows hawking low over the fields at dawn, in long swooping curves."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    cx = (x0 + x1) / 2
    colour = c8(0, 0, 0) if ctx["night_land"] else c8(0, 0, 1)
    for j, (ph, amp, spd) in enumerate(((0.0, 46, 1.0), (2.4, 38, 1.25))):
        t = frame / FPS * spd + ph
        x = cx + amp * math.sin(t * 1.05)
        y = y1 - 17 - 7 * math.sin(t * 2.2 + j) - 3 * math.cos(t * 0.7)
        paint_in(img, inside, sprites.SWALLOW[(frame // 2 + j) % 2], x, y, {1: colour})


def bat(img, ctx, frame):
    """A bat at dusk, jinking above the roofs."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    cx = (x0 + x1) / 2
    t = frame / FPS
    x = cx + 30 * math.sin(0.9 * t) + 6 * math.sin(5.3 * t)
    y = y1 - 21 + 6 * math.sin(1.7 * t) + 3 * math.sin(7.1 * t)
    paint_in(img, inside, sprites.BAT[frame % 2], x, y, {1: c8(0, 0, 0)})


def owl(img, ctx, frame, perch=51):
    """The owl on the church's roof by night, blinking now and then."""
    at = village_top(ctx, perch)
    if at is None:
        return
    x, y = at
    drawing = sprites.OWL[1 if frame % 40 in (26, 27, 28) else 0]
    sprites.paint(img, drawing, x - 1, y - drawing.shape[0] + 1, {1: ctx["silhouette"], 3: c8(3, 3, 1)}, anchor="corner",
                  where=ctx["inside"])


def fireflies(img, ctx, frame, n=12, seed=5):
    """Fireflies over the fields on a summer night: points of light low over the land, each glowing and going out
    in its own time, drifting a little."""
    inside, bottoms = ctx["inside"], ctx["bottoms"]
    rng = np.random.default_rng(seed)
    keys = sorted(bottoms)
    for k in range(n):
        i = keys[int(rng.integers(len(keys)))]
        ph, period = int(rng.integers(0, 30)), int(rng.integers(16, 26))
        rise = rng.uniform(3, 12)
        on = (frame + ph) % period
        if on >= 5:
            continue
        x = ctx["land_x0"] + i + 1.5 * math.sin(frame / 9 + k)
        y = bottoms[i] - ctx["land"].shape[0] + 2 - rise + math.sin(frame / 7 + 2 * k)
        X, Y = int(round(x)), int(round(y))
        if 0 <= Y < inside.shape[0] and 0 <= X < inside.shape[1] and inside[Y, X]:
            img[Y, X] = c8(3, 3, 1) if on in (1, 2, 3) else c8(2, 2, 0)


def falling_leaves(img, ctx, frame, n=7, seed=3):
    """Leaves loosed from the trees on an autumn day, tumbling, carried off by the wind."""
    inside = ctx["inside"]
    wsky = ctx["wsky"]
    push = -math.sin(math.radians(wsky.wind_from)) if wsky is not None else -0.6    # downwind, east to the left
    push *= 1.0 + (wsky.wind / 15 if wsky is not None else 0.6)
    rng = np.random.default_rng(seed)
    trees = [9, 39, 65, 85]
    colour = c8(3, 1, 0) if not ctx["night_land"] else ctx["silhouette"]
    for k in range(n):
        at = village_top(ctx, trees[k % len(trees)] + int(rng.integers(-1, 2)))
        if at is None:
            continue
        start = int(rng.integers(0, 40))
        t = (frame - start) / FPS
        if t < 0:
            continue
        x = at[0] - push * 9 * t + 2 * math.sin(3 * t + k)
        y = at[1] - 6 * math.sin(min(t, 1.2) * 1.3) + 5 * max(0, t - 1.2)
        paint_in(img, inside, sprites.FALLING_LEAF[(frame // 2 + k) % 4], x, y, {2: colour})


def geese(img, ctx, frame, frames, southward=True):
    """Geese in a long V on their way south in autumn (north in spring), their wings slow."""
    inside = ctx["inside"]
    x0, x1, y0, y1 = window_box(inside)
    f = frame / frames
    if southward:
        x, y = x0 - 20 + (x1 - x0 + 40) * f, y0 + 14 + (y1 - y0) * 0.45 * f
    else:
        x, y = x1 + 20 - (x1 - x0 + 40) * f, y1 - 30 - (y1 - y0) * 0.45 * f
    colour = c8(0, 0, 1)
    d = 1 if southward else -1
    for j in range(7):
        side = 1 if j % 2 else -1
        rank = (j + 1) // 2
        bx, by = x - d * 6 * rank, y + side * 4 * rank - d * 2 * rank
        paint_in(img, inside, sprites.BIRD[((frame // 4) + j) % 2], bx, by, {5: colour})


def passing(local, sun_alt, sun_rising, season, wsky):
    """Which of the passing things the hour and the season bring (the watch plays one now and then): by night the
    owl (and fireflies on warm summer nights), swallows on summer mornings, bats on warm evenings, by day birds,
    in autumn falling leaves and geese going south, in late winter and spring geese going north."""
    if sun_alt < -12:
        warm = wsky is None or wsky.temp >= 15                      # fireflies fly on warm nights
        return ["owl"] + (["fireflies"] if season in ("leaf", "harvest") and warm else [])
    if -8 <= sun_alt < 8 and sun_rising and season in ("blossom", "leaf", "harvest"):
        return ["swallows"]
    if -10 <= sun_alt < 3 and not sun_rising and season in ("blossom", "leaf", "harvest", "turning") and \
            (wsky is None or wsky.temp >= 8):                       # bats hunt insects on mild evenings
        return ["bat"]
    out = ["birds"]
    if season in ("turning", "autumn"):
        out += ["leaves", "geese south"]
    if (season == "bare" and local.month in (2, 3)) or (season == "blossom" and local.month == 4):
        out += ["geese north"]
    return out


# ---- the hour's constellations ------------------------------------------------------------------------------------
HOURLY = "constellations"                                # or "turn": the owner's choice of the hour's animation
TRACE, HOLD, FADE, STEP = 12, 3, 6, 10                   # frames: drawing one figure, holding it, fading; and the stagger


def figures():
    """{id: (name, rank, polylines)} for the constellations' figures (d3-celestial)."""
    root = Path(__file__).resolve().parents[1] / "data"
    names = {f["id"]: (f["properties"]["name"], int(f["properties"].get("rank", 3)))
             for f in json.load(open(root / "constellations.json"))["features"]}
    out = {}
    for f in json.load(open(root / "constellations.lines.json"))["features"]:
        name, rank = names.get(f["id"], (f["id"], 3))
        out[f["id"]] = (name, rank, [[(ra % 360, de) for ra, de in ls] for ls in f["geometry"]["coordinates"]])
    return out


def reveal_plan(when, dial, sky, count=5):
    """The figures to trace on the hour: those (nearly) all in the window, the ones that came into it during the
    hour first (east to west), then the highest in the sky. Each as its drawn segments in order."""
    stars = sky[0]
    bright = {(round(ra, 2), round(de, 2)): mg for ra, de, mg, bv in stars}
    inside = window_mask(dial)
    H, W = inside.shape
    lst = astro.sidereal(when, dial.lon)

    def share_in(polys, lst_):
        pts = [dial.project(ra, de, lst_) for poly in polys for ra, de in poly]
        ok = [0 <= int(x) < W and 0 <= int(y) < H and inside[int(y), int(x)] for x, y in pts]
        return sum(ok) / max(1, len(ok)), float(np.mean([x for x, _ in pts]))

    plan = []
    for cid, (name, rank, polys) in figures().items():
        segs = [((ra0, de0), (ra1, de1)) for poly in polys for (ra0, de0), (ra1, de1) in zip(poly, poly[1:])
                if max(bright.get((round(ra0, 2), round(de0, 2)), 9), bright.get((round(ra1, 2), round(de1, 2)), 9)) <= 3.8]
        if len(segs) < 2:
            continue
        now, mean_x = share_in(polys, lst)
        before, _ = share_in(polys, lst - 15.04)
        if now >= 0.75:
            height = float(np.mean([astro.altitude(ra, de, lst, dial.lat) for seg in segs for ra, de in seg]))
            plan.append((before < 0.75, mean_x, -height, name, segs))
    risen = sorted((p for p in plan if p[0]), key=lambda p: p[1])          # east (left) first
    rest = sorted((p for p in plan if not p[0]), key=lambda p: p[2])       # the highest in the sky first
    return [(p[3], p[4]) for p in (risen + rest)[:count]]


def reveal(img, ctx, plan, frame, lead=6):
    """One frame of the hour's constellations: each figure drawn star to star in a brighter line, its pen tip
    white, each star flashing as the line reaches it; held a moment, then faded back."""
    inside, dial, lst, P = ctx["inside"], ctx["dial"], ctx["lst"], ctx["P"]
    H, W = inside.shape
    day = not ctx["dark"] and not ctx["paper"]
    if ctx["paper"]:
        trace, tip, fades = P["accent"], P["accent"], [P["accent"], P["line"]]
    elif P["window"] == "red":
        trace, tip, fades = c8(3, 0, 0), c8(3, 1, 1), [c8(2, 0, 0), P["line"]]
    elif day:
        trace, tip, fades = c8(3, 3, 3), c8(3, 3, 3), [c8(2, 3, 3), None]
    else:
        trace, tip, fades = c8(3, 3, 2), c8(3, 3, 3), [c8(2, 2, 3), P["line"]]
    for i, (name, segs) in enumerate(plan):
        t = frame - (lead + i * STEP)
        if t < 0 or t >= TRACE + HOLD + FADE:
            continue
        if t < TRACE + HOLD:
            colour = trace
        else:
            colour = fades[min(len(fades) - 1, (t - TRACE - HOLD) * len(fades) // FADE)]
            if colour is None:
                continue
        pieces, total = [], 0.0                              # the segments on the screen, stopping short of stars
        for (ra0, de0), (ra1, de1) in segs:
            x0, y0 = dial.project(ra0, de0, lst)
            x1, y1 = dial.project(ra1, de1, lst)
            L = math.hypot(x1 - x0, y1 - y0)
            if L < 4.5:
                continue
            g = 2.6 / L
            a, b = (x0 + (x1 - x0) * g, y0 + (y1 - y0) * g), (x1 - (x1 - x0) * g, y1 - (y1 - y0) * g)
            pieces.append((a, b, (x0, y0), total))
            total += math.hypot(b[0] - a[0], b[1] - a[1])
        drawn = total * min(1.0, (t + 1) / TRACE)
        for a, b, star, at in pieces:
            if at > drawn:
                break
            seg_len = math.hypot(b[0] - a[0], b[1] - a[1])
            f = min(1.0, (drawn - at) / max(seg_len, 1e-6))
            pts = line_pixels(a[0], a[1], a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            for j, (px, py) in enumerate(pts):
                if 0 <= px < W and 0 <= py < H and inside[py, px]:
                    img[py, px] = tip if (t < TRACE and drawn - at - j < 2.5 and f < 1) else colour
            if t < TRACE + HOLD and drawn - at < seg_len + 6 and not day:   # the star it leaves, flashing
                sx, sy = int(math.floor(star[0])), int(math.floor(star[1]))
                for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    if 0 <= sx + ox < W and 0 <= sy + oy < H and inside[sy + oy, sx + ox]:
                        img[sy + oy, sx + ox] = c8(3, 3, 3) if (ox, oy) == (0, 0) else tip


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

    # the hour's constellations: at nine at night, and at noon (the figures shown faintly over the day sky)
    for name, when in (("night", datetime(2026, 10, 14, 21, 0, tzinfo=NY)), ("day", datetime(2026, 10, 14, 12, 0, tzinfo=NY))):
        u = when.astimezone(timezone.utc)
        plan = reveal_plan(u, t2, sky)
        n = 6 + STEP * len(plan) + TRACE + HOLD + FADE + 6
        frames = [render(u, t2, sky, NY, "planisphere", False, names=k >= n - 6,
                         extras=lambda img, ctx, k=k: reveal(img, ctx, plan, k)) for k in range(n)]
        save(frames, ROOT / "docs" / f"anim-constellations-{name}.gif", (400, 456))
        print(name, [p[0] for p in plan])

    # the weather in motion: rain at noon, snow falling at dusk with smoke from the chimney, fair-weather clouds
    # hurried across an evening sky (the clouds a quarter-minute a frame, the rest at its own pace)
    import weather as wx
    frames = []
    for when, w, hurry, n in ((datetime(2026, 10, 14, 12, 15, tzinfo=NY), "rain", 6, 36),
                              (datetime(2027, 1, 20, 16, 40, tzinfo=NY), "snow", 6, 48),
                              (datetime(2026, 10, 14, 18, 5, tzinfo=NY), "fair", 15, 48)):
        u = when.astimezone(timezone.utc)
        s0 = when.hour * 3600 + when.minute * 60
        frames += [render(u + timedelta(seconds=k / FPS), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w],
                          fahrenheit=True, weather_clock=(s0 + k * hurry, s0 + k / FPS)) for k in range(n)]
    save(frames, ROOT / "docs" / "anim-weather.gif", (400, 456))

    # the hours and seasons over the village: swallows on a June morning, a bat on an August evening, the owl on
    # an October night, fireflies on a July night, leaves and geese on an October afternoon
    film = [(datetime(2026, 6, 21, 5, 40, tzinfo=NY), "fair", lambda img, ctx, k: swallows(img, ctx, k), 36),
            (datetime(2026, 8, 12, 20, 25, tzinfo=NY), "fair", lambda img, ctx, k: bat(img, ctx, k), 36),
            (datetime(2026, 10, 14, 22, 30, tzinfo=NY), "frost", lambda img, ctx, k: owl(img, ctx, k), 48),
            (datetime(2026, 7, 10, 22, 30, tzinfo=NY), "fair", lambda img, ctx, k: (owl(img, ctx, k), fireflies(img, ctx, k)), 48),
            (datetime(2026, 10, 24, 15, 0, tzinfo=NY), "cloudy",
             lambda img, ctx, k: (falling_leaves(img, ctx, k), geese(img, ctx, k, 48)), 48)]
    frames = []
    for when, w, fn, n in film:
        u = when.astimezone(timezone.utc)
        s0 = when.hour * 3600 + when.minute * 60
        frames += [render(u + timedelta(seconds=k / FPS), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w],
                          fahrenheit=True, weather_clock=(s0 + k / FPS, s0 + k / FPS),
                          extras=lambda img, ctx, k=k, fn=fn: fn(img, ctx, k)) for k in range(n)]
    save(frames, ROOT / "docs" / "anim-village.gif", (400, 456))

    # the weather in motion: rain at noon, snow falling at dusk with smoke from the chimney, fair-weather clouds
    # hurried across an evening sky (the clouds a few seconds a frame, the rest at its own pace)
    import weather as wx
    frames = []
    for when, w, hurry, n in ((datetime(2026, 10, 14, 12, 15, tzinfo=NY), "rain", 6, 36),
                              (datetime(2027, 1, 20, 16, 40, tzinfo=NY), "snow", 6, 48),
                              (datetime(2026, 10, 14, 18, 5, tzinfo=NY), "cloudy", 15, 48)):
        u = when.astimezone(timezone.utc)
        s0 = when.hour * 3600 + when.minute * 60
        frames += [render(u + timedelta(seconds=k / FPS), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w],
                          fahrenheit=True, weather_clock=(s0 + k * hurry, s0 + k / FPS)) for k in range(n)]
    save(frames, ROOT / "docs" / "anim-weather.gif", (400, 456))

    # the hours and seasons over the village: swallows on a June morning, a bat on an August evening, the owl on
    # an October night, fireflies on a July night, leaves and geese on an October afternoon
    film = [(datetime(2026, 6, 21, 5, 40, tzinfo=NY), "fair", lambda img, ctx, k: swallows(img, ctx, k), 36),
            (datetime(2026, 8, 12, 20, 25, tzinfo=NY), "fair", lambda img, ctx, k: bat(img, ctx, k), 36),
            (datetime(2026, 10, 14, 22, 30, tzinfo=NY), "frost", lambda img, ctx, k: owl(img, ctx, k), 48),
            (datetime(2026, 7, 10, 22, 30, tzinfo=NY), "fair",
             lambda img, ctx, k: (owl(img, ctx, k), fireflies(img, ctx, k)), 48),
            (datetime(2026, 10, 24, 15, 0, tzinfo=NY), "cloudy",
             lambda img, ctx, k: (falling_leaves(img, ctx, k), geese(img, ctx, k, 48)), 48)]
    frames = []
    for when, w, fn, n in film:
        u = when.astimezone(timezone.utc)
        s0 = when.hour * 3600 + when.minute * 60
        frames += [render(u + timedelta(seconds=k / FPS), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w],
                          fahrenheit=True, weather_clock=(s0 + k / FPS, s0 + k / FPS),
                          extras=lambda img, ctx, k=k, fn=fn: fn(img, ctx, k)) for k in range(n)]
    save(frames, ROOT / "docs" / "anim-village.gif", (400, 456))

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
