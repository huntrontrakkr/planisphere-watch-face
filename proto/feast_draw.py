"""What a feast day brings to the face beyond its name on the almanac's line (proto/feasts.py says which day is
which): fireworks over the village at the top of each hour of its evening, fires on the hills, a light in every
window. Drawn with the watch's own random numbers (rng.py), so its C can follow.
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


# ---- the fireworks display: at the top of each hour of the feast's evening, a few seconds of rockets ---------------
FPS = 12
UP = (10, 15)                      # frames a rocket climbs (it slows as it goes)
SPREAD = 7                         # frames a burst takes to open
LIFE = 12                          # frames its sparks then hang, drooping and fading
DISPLAY = (19, 23)                 # the evening's hours it is given, from sunset; and midnight on New Year's Eve


def display_hours(local_hour, sun_alt, midnight=False):
    """Whether this hour's top brings the display: every hour of the evening once the Sun has set, until eleven
    (and at midnight, for a feast that turns the year)."""
    if midnight and local_hour == 0:
        return True
    return sun_alt < -1 and DISPLAY[0] <= local_hour <= DISPLAY[1]


def show_plan(seed, edge, col, sparks, rockets=5, finale=3):
    """The display's rockets: each (launch frame, x, foot, rise, frames up, drift, radius, sparks, kind, colour,
    turn). Five one after another, then a finale of three together. Returns (rockets, frames the display lasts)."""
    rng = Rng(seed)
    starts, f = [], 0
    for _ in range(rockets):
        starts.append(f)
        f += rng.integers(8, 13)
    starts += [f + 4 + 2 * i for i in range(finale)]
    plan = []
    for f0 in starts:
        dx = rng.integers(-50, 51)
        if dx not in edge:
            continue
        rise, up, drift = rng.integers(44, 92), rng.integers(*UP), rng.integers(-6, 7)
        R = rng.integers(11, 18)
        kind = rng.integers(0, 3)                         # 0 a peony, 1 a gold willow, 2 crackling
        plan.append((f0, col + dx, edge[dx] - 3, rise, up, drift, R, 20 if R >= 14 else 16, kind,
                     rng.integers(0, len(sparks)), rng.random()))
    end = max(p[0] + p[4] + SPREAD + LIFE for p in plan) + 1 if plan else 0
    return plan, end


def _dim(c, steps):
    """A colour a step or two toward the night sky."""
    return np.maximum(np.array(c) - 85 * steps, (0, 0, 0))


def _put(out, inside, x, y, c):
    """Note a pixel of the display (drawn together at the end of the frame, each with the ground cleared round it)."""
    H, W = inside.shape
    x, y = int(round(x)), int(round(y))
    if 0 <= y < H and 0 <= x < W and inside[y, x]:
        out[(x, y)] = c


def _draw(img, inside, ground, out):
    """The frame's display: a pixel of the window's own ground round every spark (as the names have), so the sparks
    read against a busy chart and wash out the faint stars beside them, as a bright display does; then the sparks."""
    H, W = inside.shape
    for (x, y) in out:
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            X, Y = x + ox, y + oy
            if 0 <= Y < H and 0 <= X < W and inside[Y, X] and (X, Y) not in out:
                img[Y, X] = ground[Y, X]
    for (x, y), c in out.items():
        img[y, x] = c


def fireworks_show(img, ctx, frame, plan, sparks, ink=None):
    """One frame of the display: each rocket climbing on its bright head and fading trail, then bursting with a white
    flash, its sparks flying out as bright heads with fading streaks behind them, then drooping and dimming out.
    The willows droop longest, gold; the crackling ones twinkle as they go; the peonies have a white pistil. On a
    printed chart the whole of it is engraved, in its ink."""
    inside = ctx["inside"]
    img_, img = img, {}                                  # (the pixels gathered, then drawn with their margins)
    for (f0, x0, foot, rise, up, drift, R, n, kind, ci, turn) in plan:
        t = frame - f0
        if t < 0:
            continue
        if t < up:                                       # climbing, slowing toward the top
            for back, c in ((0, c8(3, 3, 3)), (1, c8(3, 3, 1)), (2, c8(3, 2, 0)), (3, c8(2, 1, 0)), (4, c8(1, 0, 0))):
                u = max(0, t - back) / up
                e = 1 - (1 - u) ** 2
                if ink is not None and back % 2:
                    continue
                _put(img, inside, x0 + drift * e, foot - rise * e, ink if ink is not None else c)
            continue
        s = t - up                                       # bursting
        if s >= SPREAD + LIFE:
            continue
        bx, by = x0 + drift, foot - rise
        colour = (c8(3, 3, 1) if kind == 1 else sparks[ci]) if ink is None else ink
        g = 0.08 if kind == 1 else 0.035                 # how fast the sparks fall once spent
        twinkle = Rng(f0 * 7919 + frame)

        def radius(q):
            return R * (1 - (1 - min(q, SPREAD) / SPREAD) ** 2) + 0.3 * max(0, q - SPREAD)
        if s < 2:                                        # the flash
            for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) + (((1, 1), (-1, -1), (1, -1), (-1, 1)) if s == 0 else ()):
                _put(img, inside, bx + ox, by + oy, c8(3, 3, 3) if ink is None else ink)
        if s < 2 and ink is None:
            head = c8(3, 3, 3)
        elif s < SPREAD + 5:
            head = colour
        else:
            head = _dim(colour, 1 if s < SPREAD + 9 else 2) if ink is None else ink
        for k in range(n):
            if kind == 2 and s >= 3 and twinkle.integers(0, 3) == 0:
                continue                                 # crackling: sparks winking out and back
            if ink is not None and s >= SPREAD + 6 and k % 2:
                continue                                 # engraved: the fading as fewer strokes
            a = 2 * math.pi * (k + turn) / n
            sa, ca = math.sin(a), math.cos(a)
            r1 = radius(s + 1)
            fall = g * max(0, s - 2) ** 2
            # the spark's head, and its streak back toward where it came from: two pixels while it flies, one after
            for back, c in ((0, head), (1, _dim(head, 1) if ink is None else ink), (2, _dim(head, 2) if ink is None else ink)):
                if back == 2 and s >= SPREAD:
                    continue
                if ink is not None and back == 2:
                    continue
                rb = max(0.0, r1 - back * (1.3 if s < SPREAD else 0.9))
                fb = g * max(0, s - 2 - back) ** 2
                _put(img, inside, bx + rb * sa, by - rb * ca + fb, c)
            if kind == 0 and k % 2 == 0 and s < SPREAD + 6:   # a peony's pistil: an inner ring, white
                _put(img, inside, bx + 0.5 * r1 * math.sin(a + 0.2), by - 0.5 * r1 * math.cos(a + 0.2) + fall,
                     (c8(3, 3, 3) if s < SPREAD + 3 else c8(2, 2, 3)) if ink is None else ink)
    _draw(img_, inside, ctx["ground"], img)


# ---- what a feast marks in the sky ----------------------------------------------------------------------------------
PLANET_MAG = {"venus": -4.2, "jupiter": -2.2, "mercury": 0.2, "mars": 0.6, "saturn": 0.7}   # their usual brightness


def first_star(lat, lst, sun, stars, planets):
    """The first star out this evening (the Polish and Ukrainian Christmas Eve supper waits for it): the brightest of
    the named stars and the planets standing 10 degrees up when the Sun is 6 degrees down (the end of civil twilight),
    the sky given at any hour of the day (`lst`, the Sun and the planets then; the face takes the place's mean noon)
    and turned to that one. `sun` (ra, dec); `stars` [(key, ra, dec, mag)]; `planets` {name: (ra, dec)}. Returns
    ("star", key), ("planet", name) or None (the Sun never so low, or nothing up)."""
    D = math.radians
    sd = math.sin(D(lat)) * math.sin(D(sun[1]))
    cd = math.cos(D(lat)) * math.cos(D(sun[1]))
    c = (math.sin(D(-6)) - sd) / cd if cd else 2
    if not -1 < c < 1:
        return None
    h6 = math.degrees(math.acos(c))
    ha = ((lst - sun[0] + 180) % 360) - 180
    lst6 = lst + (h6 - ha) * 15.04107 / 15.0                # the sky's turn by then (the Sun's hour angle at 15 an hour)

    def up(ra, dec):
        hh = math.radians(lst6 - ra)
        return math.degrees(math.asin(math.sin(D(lat)) * math.sin(D(dec)) +
                                      math.cos(D(lat)) * math.cos(D(dec)) * math.cos(hh))) >= 10
    best = None
    for name, (ra, dec) in planets.items():
        if up(ra, dec) and (best is None or PLANET_MAG[name] < best[0]):
            best = (PLANET_MAG[name], ("planet", name))
    for key, ra, dec, mag in stars:
        if up(ra, dec) and (best is None or mag < best[0]):
            best = (mag, ("star", key))
    return best[1] if best else None


def glint(img, inside, blocked, x, y, colour):
    """A small glint round the first star: four short rays, standing off its own picture."""
    H, W = inside.shape
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for r in (4, 5):
            X, Y = x + dx * r, y + dy * r
            if 0 <= Y < H and 0 <= X < W and inside[Y, X]:
                img[Y, X] = colour
                blocked[Y, X] = True


def bridge(img, inside, blocked, a, b, centre, colour):
    """The magpies' bridge between the Weaver and the Cowherd (Vega and Altair): a gentle arc across the Milky Way of
    small birds five pixels apart, kept off the two stars and off what is drawn (`blocked`, which then keeps the names
    off the birds)."""
    (ax, ay), (bx, by) = a, b
    L = math.hypot(bx - ax, by - ay)
    if L < 16:
        return
    mx, my = (ax + bx) / 2, (ay + by) / 2
    nx, ny = -(by - ay) / L, (bx - ax) / L                  # the arc bows toward the window's middle
    if (centre[0] - mx) * nx + (centre[1] - my) * ny < 0:
        nx, ny = -nx, -ny
    cx, cy = mx + nx * 0.22 * L, my + ny * 0.22 * L
    H, W = inside.shape
    steps = int(L * 2)
    last = (ax, ay)                                          # (none yet: the first must be clear of the star anyway)
    for k in range(steps + 1):
        t = k / steps
        x = (1 - t) ** 2 * ax + 2 * (1 - t) * t * cx + t * t * bx
        y = (1 - t) ** 2 * ay + 2 * (1 - t) * t * cy + t * t * by
        if min((x - px_) ** 2 + (y - py_) ** 2 for px_, py_ in ((ax, ay), (bx, by), last)) < 25:
            continue                                         # clear of the two stars and the last bird
        px, py = int(math.floor(x)), int(math.floor(y))
        bird = ((px - 1, py - 1), (px, py), (px + 1, py - 1))
        if all(0 <= Y < H and 0 <= X < W and inside[Y, X] and not blocked[Y, X] for X, Y in bird):
            last = (x, y)
            for X, Y in bird:
                img[Y, X] = colour
                blocked[Y, X] = True
