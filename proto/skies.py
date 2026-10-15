"""The weather drawn into the window, in the engraver's own lines: Howard's clouds (cumulus heaps, flattening
into banks as they thicken, the stratus sheet in ruled lines, cirrus hair strokes), rain cut as Hiroshige cut it,
fine lines in two tones leaning
with the wind, snow pecked in dots, and the halo that thin high cloud puts round the Moon. Clouds are the
place's weather, not the sky's: they drift downwind across the chart (east to the left, north up) while the
stars turn beneath them.

Everything is placed from the day and the place (the same clouds all day, drifting), so a face redrawn a
minute later shows the same clouds a little further on.
"""
import math
from dataclasses import dataclass, field

import numpy as np

import sprites
from render2 import c8

CLOUD_SPEED = 0.0015            # pixels a second per km/h of wind: a 20 km/h breeze crosses the window in an hour
RAIN_FALL, DRIZZLE_FALL, SNOW_FALL, HAIL_FALL = 40.0, 25.0, 4.0, 30.0      # pixels a second down the screen


def seed_of(day, lat, lon, salt):
    return (day * 7919 + int(round(lat * 10)) * 104729 + int(round(lon * 10)) * 1299709 + salt * 15485863) % (2 ** 32)


def drift(wsky):
    """The clouds' drift on the chart, pixels a second: downwind, east to the left and north up."""
    to = math.radians(wsky.wind_from + 180)
    v = CLOUD_SPEED * max(wsky.wind, 3.0)
    return -math.sin(to) * v, -math.cos(to) * v


def wrap(v, lo, hi):
    return lo + (v - lo) % (hi - lo)


@dataclass
class Layer:
    """The clouds and what falls from them, placed for one moment: what hides the stars (`body`, the cumulus),
    what thins them (`band`, the stratus), and the drawings."""
    body: np.ndarray
    band: np.ndarray
    cumulus: list = field(default_factory=list)      # (roles, x0, y0)
    stratus: list = field(default_factory=list)      # (y, x0, x1): ruled lines
    cirrus: list = field(default_factory=list)       # (roles, x0, y0)
    falls: list = field(default_factory=list)        # (kind, x, y, tone)


def layer(inside, wsky, t, day, lat, lon, t_falls=None):
    """The weather's drawings in the window at `t` seconds into the local day (rain and snow at `t_falls`, if
    given: a film may hurry the clouds and let the rain fall at its own pace)."""
    t_falls = t if t_falls is None else t_falls
    H, W = inside.shape
    body, band = np.zeros((H, W), bool), np.zeros((H, W), bool)
    out = Layer(body, band)
    if wsky is None:
        return out
    ys, xs = np.nonzero(inside)
    x_lo, x_hi, y_lo, y_hi = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    area = len(xs)
    dx, dy = drift(wsky)
    margin = 28
    # cumulus heaps, each set where the window has room for it, kept apart from the others, more and larger as the
    # low cloud grows; as it thickens the heaps flatten into banks (Howard's cumulo-stratus). Nothing shows behind
    def scatter(drawings, n, salt, weights, thin):
        """`n` clouds in the window at any moment: as many again for the margins they drift through."""
        rng = np.random.default_rng(seed_of(day, lat, lon, salt))
        n = int(round(n * (x_hi - x_lo + 2 * margin) * (y_hi - y_lo + 16) / area))
        placed = []
        for _ in range(n * 12):
            if len(placed) >= n:
                break
            k = int(rng.choice(len(drawings), p=weights))
            a = sprites.cloud(drawings[k])
            if rng.random() < 0.5:
                a = a[:, ::-1]
            u, v = rng.uniform(x_lo - margin, x_hi + margin), rng.uniform(y_lo - 10, y_hi + 6)
            if any(abs(u - pu) < (a.shape[1] + pa.shape[1]) / 2 + 3 and abs(v - pv) < (a.shape[0] + pa.shape[0]) / 2 + 3
                   for pu, pv, pa in placed):
                continue
            placed.append((u, v, a))
        for u, v, a in placed:
            x = wrap(u + dx * t, x_lo - margin, x_hi + margin)
            y = wrap(v + dy * t, y_lo - 10, y_hi + 6)
            x0, y0 = int(round(x - a.shape[1] / 2)), int(round(y - a.shape[0] / 2))
            out.cumulus.append((a, x0, y0))
            for j, i in zip(*np.nonzero(a)):
                if 0 <= y0 + j < H and 0 <= x0 + i < W:
                    body[y0 + j, x0 + i] = True
    if wsky.cumulus > 0.05:
        big = min(1.0, wsky.cumulus * 1.4)
        scatter(sprites.CUMULUS, int(round(1 + 6 * wsky.cumulus)), 1, (0.15 + 0.3 * big, 0.45, 0.4 - 0.3 * big), False)
        if wsky.cumulus > 0.35:
            scatter(sprites.STRATUS, int(round(6 * (wsky.cumulus - 0.3))), 5, (0.45, 0.35, 0.2), False)
    # stratus: the sheet drawn as the engravers drew it, in ruled lines, a lens of three to five lines to each band,
    # more bands as it closes; through it only the brightest stars
    if wsky.stratus > 0.08:
        rng = np.random.default_rng(seed_of(day, lat, lon, 2))
        nb = int(round(1 + 4 * wsky.stratus))
        span = (y_hi - y_lo) / nb
        for b in range(nb):
            nl = int(rng.integers(3, 6))
            yc = y_lo + span * (b + 0.5) + rng.uniform(-span * 0.2, span * 0.2)
            half = (x_hi - x_lo) * (0.22 + 0.3 * wsky.stratus) * rng.uniform(0.8, 1.15)
            xc = wrap(rng.uniform(x_lo - margin, x_hi + margin) + dx * t, x_lo - margin, x_hi + margin)
            for l in range(nl):
                y = int(round(yc + 2 * (l - (nl - 1) / 2)))
                prof = math.sin(math.pi * (l + 1) / (nl + 1)) ** 0.6
                x0 = int(round(xc - half * prof + rng.uniform(-3, 3)))
                x1 = int(round(xc + half * prof + rng.uniform(-3, 3)))
                out.stratus.append((y, x0, x1))
                if 0 <= y < H:
                    band[max(0, y - 1): min(H, y + 2), max(0, x0): max(0, min(W, x1 + 1))] = True
    # cirrus: a few hair strokes
    if wsky.cirrus > 0.1:
        rng = np.random.default_rng(seed_of(day, lat, lon, 3))
        for _ in range(int(round(5 * wsky.cirrus))):
            a = sprites.stroke(sprites.CIRRUS[int(rng.integers(len(sprites.CIRRUS)))])
            if rng.random() < 0.5:
                a = a[:, ::-1]
            x = wrap(rng.uniform(x_lo - margin, x_hi + margin) + 1.6 * dx * t, x_lo - margin, x_hi + margin)
            y = wrap(rng.uniform(y_lo, y_hi) + 1.6 * dy * t, y_lo - 4, y_hi)
            out.cirrus.append((a, int(round(x)), int(round(y))))
    # rain and snow, falling down the screen past the village, leaning with the wind
    if wsky.falls:
        rng = np.random.default_rng(seed_of(day, lat, lon, 4))
        east = -math.sin(math.radians(wsky.wind_from + 180))          # the wind's push across the chart (left +)
        lean = max(-0.7, min(0.7, -east * wsky.wind / 45.0))          # pixels across per pixel down
        if wsky.falls in ("rain", "drizzle"):
            n = int((22 if wsky.falls == "drizzle" else 34) * wsky.heavy * area / 14000)
            fall = DRIZZLE_FALL if wsky.falls == "drizzle" else RAIN_FALL
            for k in range(n):
                u, v = rng.uniform(x_lo, x_hi), rng.uniform(y_lo, y_hi)
                length = int(rng.integers(2, 4)) if wsky.falls == "drizzle" else int(rng.integers(3, 7))
                y = wrap(v + fall * t_falls, y_lo, y_hi)
                x = wrap(u + lean * fall * t_falls, x_lo, x_hi)
                out.falls.append(("streak", x, y, k % 3 == 0, length, lean))
        else:
            n = int((22 if wsky.falls == "snow" else 30) * wsky.heavy * area / 14000)
            fall = SNOW_FALL if wsky.falls == "snow" else HAIL_FALL
            for k in range(n):
                u, v, ph = rng.uniform(x_lo, x_hi), rng.uniform(y_lo, y_hi), rng.uniform(0, 2 * math.pi)
                y = wrap(v + fall * t_falls, y_lo, y_hi)
                x = wrap(u + lean * fall * t_falls + (1.5 * math.sin(t_falls * 0.8 + ph) if wsky.falls == "snow" else 0), x_lo, x_hi)
                out.falls.append(("flake" if wsky.falls == "snow" else "dot", x, y, False, 1, 0))
    return out


def colours(sun_alt, red, overcast, moonlit):
    """The clouds' colours for the hour (roles K top, W body, S base; None keeps the sky's own colour), the
    stratus lines', the cirrus', and the rain's two tones."""
    if red:
        return dict(K=c8(1, 0, 0), W=None, S=None, line=c8(1, 0, 0), hair=c8(1, 0, 0), rain=(c8(1, 0, 0), c8(2, 0, 0)),
                    snow=c8(2, 0, 0))
    if sun_alt >= 6:
        return dict(K=c8(3, 3, 3), W=c8(3, 3, 3), S=c8(2, 2, 2) if overcast else c8(2, 2, 3),
                    line=c8(3, 3, 3) if overcast else c8(2, 3, 3), hair=c8(3, 3, 3),
                    rain=(c8(1, 1, 2), c8(3, 3, 3)) if overcast else (c8(1, 1, 2), c8(2, 2, 3)), snow=c8(3, 3, 3))
    if sun_alt >= -2:
        return dict(K=c8(3, 3, 2), W=c8(3, 2, 2), S=c8(3, 1, 1), line=c8(3, 2, 2), hair=c8(3, 2, 2),
                    rain=(c8(1, 1, 2), c8(2, 2, 3)), snow=c8(3, 3, 3))
    if sun_alt >= -8:
        return dict(K=c8(2, 1, 2), W=c8(1, 1, 2), S=c8(3, 1, 1), line=c8(2, 1, 2), hair=c8(3, 1, 1),
                    rain=(c8(1, 1, 2), c8(2, 2, 3)), snow=c8(3, 3, 3))
    lit = c8(2, 2, 2) if moonlit else c8(1, 1, 2)          # by night a dark cloud, its edge silvered
    return dict(K=lit, W=c8(0, 0, 0), S=c8(0, 0, 0), line=lit, hair=c8(0, 1, 2),
                rain=(c8(1, 1, 2), c8(0, 1, 2)), snow=c8(2, 2, 2) if moonlit else c8(1, 1, 2))


def paint_clouds(img, ground, inside, lay, col, keep=None):
    """The clouds over the stars: the cumulus filled (hiding what is behind), the stratus ruled, the cirrus
    stroked. `keep` marks pixels left alone (round the bright stars a stratus line passes)."""
    H, W = inside.shape
    for a, x0, y0 in lay.cumulus:
        for j, i in zip(*np.nonzero(a)):
            Y, X = y0 + j, x0 + i
            if 0 <= Y < H and 0 <= X < W and inside[Y, X]:
                c = col[{1: "K", 5: "W", 7: "S"}[int(a[j, i])]]
                img[Y, X] = ground[Y, X] if c is None else c
                if c is not None:
                    ground[Y, X] = c
    for y, x0, x1 in lay.stratus:
        if not 0 <= y < H:
            continue
        for X in range(max(0, x0), min(W, x1 + 1)):
            if inside[y, X] and not (keep is not None and keep[y, X]):
                img[y, X] = col["line"]
                ground[y, X] = col["line"]
    for a, x0, y0 in lay.cirrus:
        for j, i in zip(*np.nonzero(a)):
            Y, X = y0 + j, x0 + i
            if 0 <= Y < H and 0 <= X < W and inside[Y, X] and not (keep is not None and keep[Y, X]):
                img[Y, X] = col["hair"]


def paint_falls(img, inside, lay, col, keep=None):
    """Rain and snow over the sky (not over what `keep` marks)."""
    H, W = inside.shape
    for kind, x, y, dark, length, lean in lay.falls:
        if kind == "streak":
            c = col["rain"][0 if dark else 1]
            for s in range(length):
                X, Y = int(math.floor(x + lean * s)), int(math.floor(y + s))
                if 0 <= Y < H and 0 <= X < W and inside[Y, X] and not (keep is not None and keep[Y, X]):
                    img[Y, X] = c
        elif kind == "flake":
            sprites.paint(img, sprites.SNOWFLAKE, int(math.floor(x)), int(math.floor(y)), {5: col["snow"]}, anchor="corner",
                          where=inside & (~keep if keep is not None else inside))
        else:
            X, Y = int(math.floor(x)), int(math.floor(y))
            if 0 <= Y < H and 0 <= X < W and inside[Y, X] and not (keep is not None and keep[Y, X]):
                img[Y, X] = col["snow"]


def halo_ring(pdec, pha, dec, ha, k, radius=22.0):
    """The pixels of the ring `radius` degrees round a body at (dec, ha), in the chart's own projection (so it
    stretches as the chart does): a pixel wide."""
    d0, h0 = math.radians(dec), math.radians(ha)
    g = np.degrees(np.arccos(np.clip(np.sin(pdec) * math.sin(d0) + np.cos(pdec) * math.cos(d0) * np.cos(pha - h0), -1, 1)))
    return np.abs(g - radius) < 0.5 / k
