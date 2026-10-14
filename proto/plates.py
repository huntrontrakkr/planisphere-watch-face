"""The planisphere in plates, each after a real tradition of sky charts, with
the type of its time, the way Groundtrack's plates follow real charts:

  planisphere   the paper planispheres of the early 1900s: a cream card printed
                in black and red, a deep blue star disc behind its window
                (Old Standard, a revival of the period's scientific type)
  burritt       Burritt's Geography of the Heavens (1835): white stars and
                figures on a blue ground (Playfair, after copperplate lettering)
  flamsteed     Flamsteed's Atlas Coelestis (London, 1729): engraved stars and
                figures, ink on paper (Libre Caslon: Caslon cut his type in
                London in the same decade)
  observatory   red light for eyes adapted to the dark (Old Standard)
  night         the first take: a black jacket, white type

Each shows the time as almanacs and astronomers write it, 9ʰ 30ᵐ (21ʰ 30ᵐ on
the 24-hour clock), large in the jacket above the window, the date in italic, the Sun's next rising or setting in
small capitals, and names in the sky: constellations in spaced capitals,
stars in italic, planets in small capitals.

    uv run python proto/plates.py
"""
import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import astro
from render import Dial, load_sky
from render2 import (COOL, WARM, bn_tile, sky_scalar, banded, smooth, star_names, next_sun_event, wu_line, c8)
from typeset import ink, astro_time
from pixeltext import pixel_text, time_text, concat, stamp, box_of
import frame
import sprites

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")

OLD, OLD_I = "OldStandard-Regular.ttf", "OldStandard-Italic.ttf"
PLATES = {
    "planisphere": dict(jacket=c8(3, 3, 2), ink=c8(0, 0, 0), accent=c8(2, 0, 0), window="sky", night=c8(0, 0, 1),
                        star=c8(3, 3, 3), glyph="cross", line=c8(1, 1, 2), milky=c8(1, 1, 2), label=c8(3, 3, 2),
                        const=c8(2, 2, 3), planet=c8(3, 2, 1), rule=c8(0, 0, 0), font=(OLD, None), italic=(OLD_I, None),
                        ring="roman"),
    "burritt": dict(jacket=c8(0, 0, 1), ink=c8(3, 3, 2), accent=c8(3, 2, 1), window="paper", night=c8(0, 1, 2),
                    star=c8(3, 3, 3), glyph="rays", line=c8(2, 2, 3), milky=c8(1, 2, 3), label=c8(3, 3, 3),
                    const=c8(3, 3, 2), planet=c8(3, 3, 1), rule=c8(3, 3, 2), font=("PlayfairDisplay[wght].ttf", 450),
                    italic=("PlayfairDisplay-Italic[wght].ttf", 450), ring="roman"),
    "flamsteed": dict(jacket=c8(3, 3, 2), ink=c8(1, 0, 0), accent=c8(2, 0, 0), window="paper", night=c8(3, 3, 3),
                      star=c8(0, 0, 0), glyph="rays", line=c8(2, 1, 1), milky=c8(2, 2, 2), label=c8(1, 0, 0),
                      const=c8(2, 0, 0), planet=c8(2, 0, 0), rule=c8(1, 0, 0), font=("LibreCaslonText[wght].ttf", 450),
                      italic=("LibreCaslonText-Italic[wght].ttf", 450), ring="roman"),
    "observatory": dict(jacket=c8(0, 0, 0), ink=c8(2, 0, 0), accent=c8(3, 0, 0), window="red", night=c8(0, 0, 0),
                        star=c8(3, 0, 0), glyph="cross", line=c8(1, 0, 0), milky=c8(1, 0, 0), label=c8(2, 0, 0),
                        const=c8(1, 0, 0), planet=c8(3, 1, 0), rule=c8(1, 0, 0), font=(OLD, None), italic=(OLD_I, None),
                        ring="hours"),
    "night": dict(jacket=c8(0, 0, 0), ink=c8(3, 3, 3), accent=c8(3, 2, 0), window="sky", night=c8(0, 0, 1),
                  star=c8(3, 3, 3), glyph="cross", line=c8(0, 1, 2), milky=c8(1, 1, 2), label=c8(2, 2, 2),
                  const=c8(1, 1, 2), planet=c8(3, 2, 1), rule=c8(1, 1, 1), font=(OLD, None), italic=(OLD_I, None),
                  ring="hours"),
}

CONSTELLATIONS = None


def constellations():
    global CONSTELLATIONS
    if CONSTELLATIONS is None:
        CONSTELLATIONS = []
        for f in json.load(open(ROOT / "data" / "constellations.json"))["features"]:
            p = f["properties"]
            ra, de = f["geometry"]["coordinates"]
            CONSTELLATIONS.append((p["name"], int(p.get("rank", 3)), ra % 360, de))
    return CONSTELLATIONS


def track_point(dial, a_deg, inset, shape=None):
    """Where the ray from the pole at dial angle `a_deg` (from the bottom, anticlockwise) meets the ring's
    track `inset` pixels in from the screen's edge: a circle, or on the Time 2 a parallel of its outline
    (or of `shape`, as the inner edge)."""
    a = math.radians(a_deg)
    dx, dy = math.sin(a), math.cos(a)
    if not getattr(dial, "rect", False):
        r = dial.R - inset
        return dial.cx + r * dx, dial.cy + r * dy
    shape = shape or dial.outline
    lo, hi = 0.0, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if shape.dist(dial.cx + mid * dx, dial.cy + mid * dy)[0] > inset:
            lo = mid
        else:
            hi = mid
    return dial.cx + lo * dx, dial.cy + lo * dy


def band_curve(dial, inset, top=True):
    """The ring's track `inset` pixels in, as a function of the distance s along it from its top (or bottom)
    centre, rightward positive: returns s -> (x, y, angle), the angle the track's turn there in radians
    (positive clockwise for the top, anticlockwise for the bottom: the way letters lean to follow it)."""
    if getattr(dial, "rect", False):
        key = (inset, top)
        if key not in dial.curves:
            xs = np.linspace(-dial.w * 0.36, dial.w * 0.36, 289)
            ys = []
            for x in xs:
                lo, hi = 0.0, dial.h / 2                # down from the edge (top) or up from it (bottom)
                for _ in range(36):
                    mid = (lo + hi) / 2
                    yv = mid if top else dial.h - mid
                    if dial.outline.dist(dial.w / 2 + x, yv)[0] > inset:
                        hi = mid
                    else:
                        lo = mid
                ys.append(dial.h / 2 - hi)              # height above the centre (for either edge)
            dial.curves[key] = (xs, np.array(ys))
        xs, ys = dial.curves[key]
        cx, cy = dial.w / 2, dial.h / 2
    else:
        t = np.linspace(-math.pi / 2, math.pi / 2, 4001)
        r = dial.R - inset
        xs, ys = r * np.sin(t), r * np.cos(t)
        cx, cy = dial.cx, dial.cy
    seg = np.hypot(np.diff(xs), np.diff(ys))
    s = np.concatenate([[0], np.cumsum(seg)])
    s -= np.interp(0.0, xs, s)
    ang = np.arctan2(-np.gradient(ys), np.gradient(xs))           # the tangent's turn from level
    def at(d):
        x, y, g = np.interp(d, s, xs), np.interp(d, s, ys), np.interp(d, s, ang)
        return (cx + x, cy - y, g) if top else (cx + x, cy + y, g)
    return at


class RectDial(Dial):
    """The Time 2's layout: the ring's outline filling the screen (frame.py), the time across the top, and
    the window as large as the rest of the card allows, the pole placed to suit it."""

    def __init__(self, w, h, lat, lon, band=17.0, block=62.0, shape=None):
        super().__init__(w, h, lat, lon)
        self.rect, self.band, self.curves = True, band, {}
        self.outline = shape or frame.cushion(w, h, 240.0, 800.0, 24.0)
        # the band's inner edge: the parallel `band` in, its corners rounder than the outline's so the band
        # widens there, room for the hours that fall in the corners
        self.inner = frame.cushion(w, h, 240.0, 800.0, 24.0, d=band, rho=17.0) if shape is None else None
        top, bottom = band + block, h - band - 5        # clear of the ring's inner rule by the window's two rims
        self.k = (bottom - top) / 180.0                # the window spans 180 degrees from its top to its bottom
        self.k = min(self.k, (w / 2 - band - 6) / 90.0)
        self.cy = top + abs(lat) * self.k
        self.r_disc = self.reach * self.k
        self.R = min(w, h) / 2


class RoundDial(Dial):
    """The Round 2's layout: the ring round the screen's edge, the window inside it, clear of its inner rule
    by the window's own two rims."""

    def __init__(self, w, h, lat, lon):
        super().__init__(w, h, lat, lon)
        self.r_disc = self.R - ring_params(self)["in"] - 6
        self.k = self.r_disc / self.reach


def ring_params(dial):
    """The ring's band, in pixels in from the screen's edge: its outer and inner edges (a rule along each),
    where the words' centre line and the numerals' centres run, and the hour and half-hour ticks' lengths
    (standing out from the inner rule). Words and ticks are kept a clear pixel or more apart."""
    if getattr(dial, "rect", False):
        return dict(out=1.5, **{"in": dial.band}, word=8.25, num=(2.5 + dial.band - 1) / 2, tick=2, tick2=1)
    return dict(out=1.5, **{"in": 18.0}, word=8.75, num=(2.5 + 18.0 - 1) / 2, tick=2, tick2=1)


def word_inset(dial):
    return ring_params(dial)["word"]


def nearest(img):
    return (np.clip(np.floor(np.clip(img, 0, 255) / 85 + 0.5), 0, 3) * 85).astype(np.uint8)


# ---- colours of the hand-drawn pieces, by plate ----------------------------------------------------
def piece_colours(P):
    """Colours for the drawings' roles (sprites.ROLE): K ink, R red, Y gold, O deep gold, W light, M ground, S silver."""
    red = P["window"] == "red"
    light_paper = P["window"] == "paper" and P["night"].sum() > 400
    if red:
        sun = {1: c8(1, 0, 0), 2: c8(3, 0, 0), 3: c8(3, 0, 0), 4: c8(2, 0, 0), 5: c8(3, 1, 1)}
        planets = {1: c8(1, 0, 0), 2: c8(3, 0, 0), 3: c8(3, 0, 0), 4: c8(1, 0, 0), 5: c8(3, 0, 0), 7: c8(2, 0, 0)}
        moon = {1: c8(1, 0, 0), 5: c8(3, 0, 0)}
    elif light_paper:
        sun = {1: c8(1, 0, 0), 2: c8(2, 0, 0), 3: c8(3, 2, 0), 4: c8(2, 1, 0), 5: c8(3, 3, 1)}
        planets = {1: P["ink"], 2: c8(2, 0, 0), 3: c8(2, 1, 0), 4: c8(1, 0, 0), 5: c8(1, 1, 1), 7: c8(1, 1, 1)}
        moon = {1: P["ink"], 5: c8(3, 3, 3)}
    else:
        sun = {1: c8(0, 0, 0), 2: c8(2, 0, 0), 3: c8(3, 2, 0), 4: c8(2, 1, 0), 5: c8(3, 3, 2)}
        planets = {1: c8(2, 2, 2), 2: c8(3, 1, 0), 3: c8(3, 2, 0), 4: c8(2, 1, 0), 5: c8(3, 3, 2), 7: c8(2, 2, 2)}
        moon = {1: c8(1, 1, 1), 5: c8(3, 3, 2)}
    return sun, planets, moon


def outline(mask):
    """The pixels just outside a region, touching it along an edge: a clean one-pixel rule round it."""
    grow = mask.copy()
    grow[1:] |= mask[:-1]; grow[:-1] |= mask[1:]; grow[:, 1:] |= mask[:, :-1]; grow[:, :-1] |= mask[:, 1:]
    return grow & ~mask


def grow(mask, n):
    m = mask.copy()
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        m = g
    return m


def ring_shape(dial, inset):
    """The region inside the ring's track `inset` pixels in from its outer edge (a disc, or a rounded rectangle)."""
    H, W = dial.h, dial.w
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + 0.5, yy + 0.5
    if not getattr(dial, "rect", False):
        return np.hypot(px - dial.cx, py - dial.cy) <= dial.R - inset
    return dial.outline.grid(W, H) >= inset


def clear_distance(mask, most=6):
    """For every pixel, how many pixels clear of `mask` it stands (0 on it, 1 touching it, ...), up to `most`."""
    out = np.full(mask.shape, most, np.int16)
    m = mask.copy()
    for d in range(most):
        out[m & (out == most)] = d
        g = m.copy()
        g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]
        g[1:, 1:] |= m[:-1, :-1]; g[1:, :-1] |= m[:-1, 1:]; g[:-1, 1:] |= m[1:, :-1]; g[:-1, :-1] |= m[1:, 1:]
        m = g
    return out


def inner_region(dial):
    """Inside the ring's inner edge."""
    if getattr(dial, "rect", False) and dial.inner is not None:
        return dial.inner.grid(dial.w, dial.h) >= 0
    return ring_shape(dial, ring_params(dial)["in"])


def edge_point(dial, a_deg, out=0.0):
    """Where the hour ray at `a_deg` crosses the ring's inner edge, moved `out` pixels further along it."""
    if getattr(dial, "rect", False) and dial.inner is not None:
        x, y = track_point(dial, a_deg, 0.0, dial.inner)
    else:
        x, y = track_point(dial, a_deg, ring_params(dial)["in"])
    a = math.radians(a_deg)
    return x + out * math.sin(a), y + out * math.cos(a)


def tick_pixels(dial, a_deg, length):
    """A tick standing `length` pixels out from the ring's inner edge along the hour's ray: whole pixels."""
    x0, y0 = edge_point(dial, a_deg, 0.5)
    x1, y1 = edge_point(dial, a_deg, 0.5 + length - 0.01)
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    pts = set()
    for k in range(n + 1):
        t = k / max(n, 1)
        pts.add((int(math.floor(x0 + (x1 - x0) * t)), int(math.floor(y0 + (y1 - y0) * t))))
    return pts


def render(when, dial, sky, tz, plate="planisphere", round_screen=True, clock24=False):
    P = PLATES[plate]
    fn, fw = P["font"]
    fi, fiw = P["italic"]
    stars, lines, mw, named = sky
    W, H = dial.w, dial.h
    lst = astro.sidereal(when, dial.lon)
    pos = astro.positions(when)
    sun_alt = astro.altitude(*pos["sun"], lst, dial.lat)
    lat = abs(dial.lat) * astro.D2R
    local = when.astimezone(tz)
    rect = getattr(dial, "rect", False)
    SS = 4
    sun_c, planet_c, moon_c = piece_colours(P)

    # the window: the sky above the horizon (symmetric about the meridian by construction)
    ys, xs = np.mgrid[0:H * SS, 0:W * SS]
    dx, dy = (xs + 0.5) / SS - dial.cx, (ys + 0.5) / SS - dial.cy
    rho = np.hypot(dx, dy)
    dec = (90 - rho / dial.k) * astro.D2R
    sin_alt = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(np.arctan2(dx, dy))
    win = ((sin_alt > 0) & (rho <= dial.r_disc)).astype(np.float64).reshape(H, SS, W, SS).mean(axis=(1, 3))
    inside = win > 0.5
    img = np.zeros((H, W, 3)) + P["jacket"]

    # the window's ground: the live sky, red light, or the paper of a printed chart
    yy, xx = np.mgrid[0:H, 0:W]
    pdx, pdy = xx + 0.5 - dial.cx, yy + 0.5 - dial.cy
    pdec = (90 - np.hypot(pdx, pdy) / dial.k) * astro.D2R
    pha = np.arctan2(pdx, pdy)
    palt = np.degrees(np.arcsin(np.clip(np.sin(lat) * np.sin(pdec) + np.cos(lat) * np.cos(pdec) * np.cos(pha), -1, 1)))
    sdec, sha = pos["sun"][1] * astro.D2R, (lst - pos["sun"][0]) * astro.D2R
    gamma = np.degrees(np.arccos(np.clip(np.sin(pdec) * np.sin(sdec) + np.cos(pdec) * np.cos(sdec) * np.cos(pha - sha), -1, 1)))
    tt = bn_tile(H, W)
    paper = P["window"] == "paper"
    if P["window"] == "sky":
        bval, warm = sky_scalar(palt, gamma, sun_alt)
        ramp = [P["night"]] + [c for c in COOL if c.sum() > P["night"].sum()]
        skyq = banded(np.clip(bval, 0, len(ramp) - 1), ramp, tt)
        wv = warm * len(WARM) + 0.2
        hot = wv >= 1.0
        if hot.any():
            wq = banded(np.clip(wv - 1, 0, len(WARM) - 1), WARM, tt)
            skyq = np.where((hot & (smooth(0, 0.5, wv - 1) > tt))[..., None], wq, skyq)
        img[inside] = skyq[inside]
        dark = sun_alt < -12
    elif P["window"] == "red":
        bval, _ = sky_scalar(palt, gamma, sun_alt)
        skyq = banded(np.clip(bval * 0.5, 0, 2), [c8(0, 0, 0), c8(1, 0, 0), c8(2, 0, 0)], tt)
        img[inside] = skyq[inside]
        dark = sun_alt < -12
    else:
        img[inside] = P["night"]
        dark = True
    ground = img.copy()
    faint = float(np.interp(sun_alt, [-16, -10, -5, -1.5], [4.6, 3.4, 2.0, 0.4])) if not paper else 4.6
    if not paper and sun_alt > -1.5:
        faint = -9
    figs = paper or sun_alt < -10.5

    # the Milky Way, stippled
    if paper or sun_alt < -15:
        acc_all = np.zeros((H * SS, W * SS))
        for level, polys in enumerate(mw):
            acc = np.zeros((H * SS, W * SS), bool)
            for poly in polys:
                for ring_ in poly:
                    pts = [(p[0] * SS, p[1] * SS) for p in (dial.project(ra, de, lst) for ra, de in ring_)]
                    if len(pts) > 2:
                        l = Image.new("1", (W * SS, H * SS), 0)
                        ImageDraw.Draw(l).polygon(pts, fill=1)
                        acc ^= np.asarray(l, bool)
            acc_all = np.maximum(acc_all, acc * (level + 1) / len(mw))
        m = acc_all.reshape(H, SS, W, SS).mean(axis=(1, 3))
        dens = np.clip(m * (0.30 if paper else 0.42), 0, 1) ** 1.2
        img[(dens > tt) & inside] = P["milky"]

    # the equator and the ecliptic, dotted
    for lam in range(0, 360, 3):
        for kind, (ra, de) in (("ecl", astro.ecl_to_eq(lam, 0, pos["eps"])), ("eq", (lam, 0.0))):
            if kind == "eq" and lam % 6:
                continue
            x, y = dial.project(ra, de, lst)
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and inside[yi, xi] and dark:
                img[yi, xi] = P["const"] if kind == "ecl" else P["line"]

    # figures, stopping short of their stars
    if figs:
        bright = {(round(ra, 2), round(de, 2)): mg for ra, de, mg, bv in stars}
        cov = np.zeros((H, W))
        for ls in lines:
            for (ra0, de0), (ra1, de1) in zip(ls, ls[1:]):
                if max(bright.get((round(ra0, 2), round(de0, 2)), 9), bright.get((round(ra1, 2), round(de1, 2)), 9)) > 3.8:
                    continue
                x0, y0 = dial.project(ra0, de0, lst)
                x1, y1 = dial.project(ra1, de1, lst)
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 4.5:
                    continue
                g = 2.6 / L
                wu_line(cov, x0 + (x1 - x0) * g, y0 + (y1 - y0) * g, x1 - (x1 - x0) * g, y1 - (y1 - y0) * g)
        img[(cov > 0.55) & inside] = P["line"]

    # stars, as drawn on the old charts: eight points for the brightest, four, a cross, a point
    light_paper = paper and P["night"].sum() > 400
    for ra, de, mg, bv in sorted(stars, key=lambda s: -s[2]):
        if mg > faint:
            continue
        x, y = dial.project(ra, de, lst)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        c = P["star"] if (paper or P["window"] == "red") else (c8(2, 2, 3) if bv < -0.1 else c8(3, 3, 3) if bv < 0.5 else
                                                              c8(3, 3, 2) if bv < 1.15 else c8(3, 2, 1) if bv < 1.6 else c8(3, 2, 0))
        dim = c8(1, 1, 1) if light_paper else c * 0.67 + P["night"] * 0.33
        if mg < 0.5:
            sprites.paint(img, sprites.STAR[0], xi, yi, {5: c}, where=inside)
        elif mg < 1.4:
            sprites.paint(img, sprites.STAR[1], xi, yi, {5: c}, where=inside)
        elif mg < 2.1:
            sprites.paint(img, sprites.STAR[2], xi, yi, {5: c}, where=inside)
        elif mg < 3.4:
            sprites.paint(img, sprites.STAR[3], xi, yi, {5: c}, where=inside)
        else:
            sprites.paint(img, sprites.STAR[3], xi, yi, {5: dim if light_paper else c * 0.40 + P["night"] * 0.6}, where=inside)

    # the planets, each its little picture
    for pn in ("venus", "jupiter", "mars", "saturn", "mercury"):
        if not paper and sun_alt > -3:
            continue
        x, y = dial.project(*pos[pn], lst)
        sprites.paint(img, sprites.PLANET[pn], int(math.floor(x)), int(math.floor(y)), planet_c, where=inside)

    # the Moon, drawn in its phase (lit side toward the Sun: right while it waxes); by day only its lit face
    mx, my = dial.project(*pos["moon"], lst)
    f = pos["moon_phase"]
    moon_cols = dict(moon_c)
    if not dark and not paper and f >= 0.04:
        moon_cols[1] = None
    sprites.paint(img, sprites.moon_for(f, pos["moon_waxing"]), int(math.floor(mx)), int(math.floor(my)), moon_cols,
                  where=inside)

    # the Sun, with its face (after the Sun of May), by day; on a printed chart always. In a live sky it stands
    # in its own light, as the first takes drew it: a pale disc and a glow stippled thinner outward, the sky
    # brightest round the Sun. The drawn Sun goes over it, the glow showing between the rays and past them.
    sx, sy = dial.project(*pos["sun"], lst)
    if sun_alt > -0.8 or paper:
        si, sj = int(math.floor(sx)), int(math.floor(sy))
        if not paper:
            dd = np.hypot(xx - si, yy - sj)
            glow = np.clip(1 - (dd - 4.0) / 13.0, 0, 1) ** 1.5 * 0.85
            red = P["window"] == "red"
            light = c8(2, 0, 0) if red else c8(3, 3, 2) if sun_alt < 6 else c8(2, 3, 3)   # warm when the Sun is low
            img[(glow > tt) & inside & (dd > 4.0)] = light
            img[(dd <= 4.4) & inside] = c8(3, 0, 0) if red else c8(3, 3, 1)
        sprites.paint(img, sprites.sun_of_may(), si, sj, sun_c, where=inside)

    # names in the sky, in pixel type
    boxes = []
    def place(mask, x, y, colour, centred=False):
        for anchor, lx in ([("centre", x)] if centred else [("left", x + 5), ("right", x - 4)]):
            bx = box_of(mask, lx, y, anchor)
            corners_ = [(bx[0], bx[1]), (bx[2] - 1, bx[1]), (bx[0], bx[3] - 1), (bx[2] - 1, bx[3] - 1)]
            if not all(0 <= cx_ < W and 0 <= cy_ < H and inside[cy_, cx_] for cx_, cy_ in corners_):
                continue
            if any(bx[0] < b[2] and b[0] < bx[2] and bx[1] < b[3] and b[1] < bx[3] for b in boxes):
                continue
            boxes.append(bx)
            stamp(img, mask, lx, y, colour, halo=ground, where=inside, anchor=anchor)
            return True
        return False
    if astro.altitude(*pos["moon"], lst, dial.lat) > 0:
        place(pixel_text("Moon"), mx + 3, my, P["planet"])
    for pn in ("venus", "jupiter", "mars", "saturn", "mercury"):
        if (not paper and sun_alt > -3) or astro.altitude(*pos[pn], lst, dial.lat) <= 2:
            continue
        x, y = dial.project(*pos[pn], lst)
        place(pixel_text(pn.capitalize()), x + 2, y, P["planet"])
    if dark or paper:
        names = star_names()
        shown = 0
        for ra, de, mg, bv, hip in sorted(named, key=lambda s: s[2]):
            if shown >= 3 or mg > 1.3:
                break
            if astro.altitude(ra, de, lst, dial.lat) < 8 or hip not in names:
                continue
            x, y = dial.project(ra, de, lst)
            if place(pixel_text(names[hip], oblique=True), x + 1, y, P["label"]):
                shown += 1
        cshown = 0
        for name, rank, ra, de in sorted(constellations(), key=lambda c: c[1]):
            if cshown >= 3 or rank > 1 or astro.altitude(ra, de, lst, dial.lat) < 12:
                continue
            x, y = dial.project(ra, de, lst)
            if place(pixel_text(name.upper(), track=1), x, y, P["const"], centred=True):
                cshown += 1

    # the window's edge: a clean rule round it and a second a little way out, as a printed neatline
    rim1 = outline(inside)
    rim2 = outline(grow(inside, 2)) & ~grow(inside, 2)
    img[rim1] = P["rule"]
    img[rim2 & ~inside] = P["rule"]
    # ornaments on it: a fleur-de-lis at the north, standing on the outer rule like a finial, lozenges at
    # the east and west
    top_y = dial.cy - abs(dial.lat) * dial.k
    fl = sprites.FLEUR
    col = int(dial.cx)
    first = int(np.argmax(inside[:, col])) if inside[:, col].any() else int(top_y)
    fx0, fy0 = int(round(dial.cx - fl.shape[1] / 2)), first - 4 - (fl.shape[0] - 1)
    sprites.paint(img, fl, fx0, fy0, {2: P["accent"], 1: P["ink"]}, anchor="corner")
    ew_r = 90 * dial.k
    for sgn in (-1, 1):
        sprites.paint(img, sprites.LOZENGE, dial.cx - 0.5 + sgn * (ew_r + 1.5), dial.cy - 0.5, {2: P["accent"], 1: P["ink"]})

    # the ring: the Sun's own time, fixed to the sky (noon under the south point, midnight above the pole),
    # between two rules; hour and half-hour ticks drawn for one side and mirrored
    rp = ring_params(dial)
    r_in, r_out = rp["in"], rp["out"]
    inner, outer = inner_region(dial), ring_shape(dial, r_out)
    rule_in = outline(inner) & ~inside
    rule_out = outer & ~ring_shape(dial, r_out + 1)
    img[rule_in] = P["ink"]
    img[rule_out] = P["ink"]
    words = {0: "MIDNIGHT", 12: "NOON"}
    # the hours every three: on the 12-hour clock twelve and twelve (III, VI, IX each morning and evening, or
    # figures on the plain plates); on the 24-hour clock, figures running on through the day
    roman = P["ring"] == "roman" and not clock24
    if roman:
        numerals = {3: "III", 6: "VI", 9: "IX", 15: "III", 18: "VI", 21: "IX"}
    else:
        numerals = {h: str(h if clock24 else h % 12) for h in (3, 6, 9, 15, 18, 21)}
    ticks = set()
    for half in range(48):
        hour = half / 2
        if hour in words or (half % 2 == 0 and int(hour) in numerals):
            continue
        a = (hour - 12) * 15                            # dial angle: noon at the bottom, turning anticlockwise
        if a < -180:
            a += 360
        if not (0 <= a <= 180):
            continue                                    # draw one side; the other is its mirror image
        ticks |= tick_pixels(dial, a, rp["tick"] if half % 2 == 0 else rp["tick2"])
    for x, y in ticks:
        for xx_ in (x, W - 1 - x):                      # mirrored across the meridian: exactly symmetric
            if 0 <= xx_ < W and 0 <= y < H and not inside[y, xx_] and not inner[y, xx_]:
                img[y, xx_] = P["ink"]
    # the Sun's pointer: a small rayed Sun on the ticks at the Sun's own hour, cleared round so it reads
    # over the rule and the ticks; drawn before the numerals and words, which stay whole over it
    sun_ang = lst - pos["sun"][0]
    px_, py_ = edge_point(dial, sun_ang, 2.5)
    ls = sprites.LITTLE_SUN
    sx0, sy0 = int(round(px_ - ls.shape[1] / 2)), int(round(py_ - ls.shape[0] / 2))
    knock = np.zeros((H, W), bool)
    ys_, xs_ = np.nonzero(ls)
    for j, i in zip(ys_, xs_):
        if 0 <= sy0 + j < H and 0 <= sx0 + i < W:
            knock[sy0 + j, sx0 + i] = True
    knock = grow(knock, 1) & ~inside
    img[knock] = P["jacket"]
    sprites.paint(img, ls, sx0, sy0, sun_c, anchor="corner")

    # the numerals, drawn as engraved roman capitals (or figures on the plain plates), upright, each set on
    # its hour's ray where it stands clearest of the rules and ticks (nearest the band's middle among equals)
    held = rule_in | rule_out
    for x, y in ticks:
        for xx_ in (x, W - 1 - x):
            if 0 <= xx_ < W and 0 <= y < H:
                held[y, xx_] = True
    room = clear_distance(held)
    for hr, text in numerals.items():
        a = (hr - 12) * 15
        m = sprites.numerals(text) if roman else sprites.figures(text)
        x0_, y0_ = edge_point(dial, a)
        x1_, y1_ = track_point(dial, a, r_out + 1)
        best = None
        for f in np.linspace(0.2, 0.8, 49):
            cx_, cy_ = x0_ + (x1_ - x0_) * f, y0_ + (y1_ - y0_) * f
            lx, ty = int(round(cx_ - m.shape[1] / 2)), int(round(cy_ - m.shape[0] / 2))
            if lx < 0 or ty < 0 or lx + m.shape[1] > W or ty + m.shape[0] > H:
                continue
            c = room[ty: ty + m.shape[0], lx: lx + m.shape[1]][m].min()
            key = (c, -abs(f - 0.5))
            if best is None or key > best[0]:
                best = (key, lx, ty)
        _, lx, ty = best
        img[ty: ty + m.shape[0], lx: lx + m.shape[1]][m] = P["ink"]
    # MIDNIGHT and NOON, lettered along the ring (hand-finished art; drafts where none is finished yet),
    # a lozenge either side
    for hr, word in words.items():
        top = hr == 0
        art = sprites.word_art(word, W, H)
        if art is None:                                  # a screen with no finished art: the drafting table's
            import letterer
            m, x0, y0 = letterer.draft_mask(band_curve(dial, rp["word"], top), word, top)
        else:
            m, x0, y0 = art
        for j, i in zip(*np.nonzero(m)):
            if 0 <= y0 + j < H and 0 <= x0 + i < W:
                img[y0 + j, x0 + i] = P["accent"]
        curve = band_curve(dial, rp["word"], top)
        half_w = (sum(len(sprites.CAPS9[ch][0]) for ch in word) + 2 * (len(word) - 1)) / 2
        for sgn in (-1, 1):
            lx, ly, _ = curve(sgn * (half_w + 6))
            sprites.paint(img, sprites.LOZENGE, lx - 0.5, ly - 0.5, {2: P["accent"], 1: P["ink"]})
    # the Time 2's corners, outside the ring: a compass star in each, where the corner has most room
    if rect:
        spandrel = dial.outline.grid(W, H) < 0.5
        edge = np.zeros((H, W), bool)
        edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
        room = np.minimum(clear_distance(~spandrel, most=12), clear_distance(edge, most=12))
        for ys_, xs_ in ((slice(0, H // 2), slice(0, W // 2)), (slice(0, H // 2), slice(W // 2, W)),
                         (slice(H // 2, H), slice(0, W // 2)), (slice(H // 2, H), slice(W // 2, W))):
            r = room[ys_, xs_]
            if r.max() >= 5:
                j, i = np.unravel_index(np.argmax(r), r.shape)
                sprites.paint(img, sprites.CORNER, xs_.start + i, ys_.start + j, {2: P["accent"], 1: P["ink"]})
    # the time, as an astronomer writes it, with the date and the Sun's next rising or setting
    ring_in = dial.cy - (dial.R - r_in) if not rect else r_in
    top_of_window = fy0 - 1                            # above the fleur-de-lis
    span = top_of_window - ring_in
    big = 30 if W >= 240 else 26
    hour = (lambda h: h if clock24 else (h % 12 or 12))
    ink(img, astro_time(str(hour(local.hour)), f"{local.minute:02d}", fn, big, fw, feats=("onum",)), dial.cx,
        ring_in + span * 0.36, P["ink"])
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    date = pixel_text(f"{days[local.weekday()]} {local.day} {months[local.month - 1]}", oblique=True)
    if date.shape[1] > (W - 2 * r_in) * 0.80:
        date = pixel_text(f"{days[local.weekday()][:3]} {local.day} {months[local.month - 1][:3]}", oblique=True)
    stamp(img, date, dial.cx, ring_in + span * 0.70, P["ink"])
    kind, at = next_sun_event(when, dial.lat, dial.lon)
    if kind:
        t_ = at.astimezone(tz)
        stamp(img, concat(pixel_text(kind), time_text(hour(t_.hour), t_.minute), gap=3), dial.cx, ring_in + span * 0.90, P["accent"])
    if round_screen:
        img[np.hypot(xx + 0.5 - dial.cx, yy + 0.5 - dial.cy) > W / 2] = 0
    return nearest(img)


if __name__ == "__main__":
    sky = load_sky(4.6)
    out = ROOT / "out"
    when = datetime(2026, 10, 14, 21, 30, tzinfo=NY)
    noon = datetime(2026, 10, 14, 12, 15, tzinfo=NY)
    r2, t2 = RoundDial(260, 260, 40.71, -74.01), RectDial(200, 228, 40.71, -74.01)
    names = list(PLATES)
    S = Image.new("RGB", (len(names) * 266, 266 * 2 + 236), (24, 24, 26))
    for i, pl in enumerate(names):
        for row, (t, dial, rnd) in enumerate(((when, r2, True), (noon, r2, True), (when, t2, False))):
            im = Image.fromarray(render(t.astimezone(timezone.utc), dial, sky, NY, pl, rnd))
            im.save(out / f"plate-{pl}-{['night', 'noon', 'time2'][row]}.png")
            S.paste(im, (i * 266 + (3 if rnd else 33), row * 266 + 3))
    S.save(out / "plates.png")
    S.resize((S.width * 2, S.height * 2), Image.NEAREST).save(out / "plates-2x.png")
    print("ok")
