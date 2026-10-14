"""The planisphere, drawn with restraint, as the watch would draw it: flat
palette colours (two bits a channel), one dithered glow (the Milky Way),
stars stamped by brightness, and figures only between the brighter stars.

    uv run python proto/render2.py
"""
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import astro
import stroke_font
from render import Dial, load_sky, glyph_alpha

ROOT = Path(__file__).resolve().parents[1]
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16
SS = 4


def c8(r, g, b):
    """A Pebble colour from 0..3 levels."""
    return np.array((r, g, b), np.float64) * 85


PAL = {
    "jacket": c8(0, 0, 0), "night": c8(0, 0, 1), "naut": c8(0, 0, 2), "civil": c8(0, 1, 2), "day": c8(1, 2, 3),
    "milky": c8(1, 1, 2), "line": c8(0, 1, 2), "line_day": c8(1, 2, 3), "ecl": c8(2, 2, 1), "rim": c8(1, 1, 1),
    "num": c8(2, 2, 2), "tick": c8(1, 1, 1), "tick_major": c8(1, 1, 1), "sun": c8(3, 2, 0), "sun_core": c8(3, 3, 1),
    "card": c8(1, 1, 1), "moon": c8(3, 3, 2), "moon_dark": c8(0, 0, 1), "date": c8(2, 2, 2),
    "faint": c8(1, 1, 2), "mid": c8(2, 2, 2),
}
STAR_TINT = [(-0.1, c8(2, 2, 3)), (0.3, c8(3, 3, 3)), (0.7, c8(3, 3, 2)), (1.2, c8(3, 2, 1)), (9, c8(3, 1, 0))]
PLANETS = {"venus": c8(3, 3, 2), "jupiter": c8(3, 3, 2), "saturn": c8(3, 2, 1), "mars": c8(3, 1, 0), "mercury": c8(2, 2, 2)}


def blue_noise(n=64, seed=7):
    """Thresholds 0..1 on an n x n tile with no clumps (void and cluster, gaussian energy on the torus)."""
    rng = np.random.default_rng(seed)
    f = np.fft.fftfreq(n)
    g = np.exp(-(f[:, None] ** 2 + f[None, :] ** 2) * (n / 1.9) ** 2 / 2)       # gaussian filter, sigma ~1.9 px
    def energy(m):
        return np.real(np.fft.ifft2(np.fft.fft2(m) * g))
    m = rng.random((n, n)) < 0.1
    for _ in range(4 * n * n):                         # settle the initial pattern
        e = energy(m)
        a = np.argmax(np.where(m, e, -1e9)); b = np.argmin(np.where(~m, e, 1e9))
        m.flat[a] = False; m.flat[b] = True
        e2 = energy(m)
        if np.argmax(np.where(m, e2, -1e9)) == b:
            m.flat[b] = False; m.flat[a] = True
            break
    rank = np.zeros(n * n)
    ones = int(m.sum())
    mm = m.copy()
    for r in range(ones - 1, -1, -1):                  # remove the tightest clusters first
        e = energy(mm)
        a = np.argmax(np.where(mm, e, -1e9)); mm.flat[a] = False; rank[a] = r
    mm = m.copy()
    for r in range(ones, n * n):                       # then fill the largest voids
        e = energy(mm)
        b = np.argmin(np.where(~mm, e, 1e9)); mm.flat[b] = True; rank[b] = r
    return ((rank + 0.5) / (n * n)).reshape(n, n)


_BN = None


def bn_tile(h, w):
    global _BN
    if _BN is None:
        cache = ROOT / "out" / "bluenoise64.npy"
        if cache.exists():
            _BN = np.load(cache)
        else:
            _BN = blue_noise(64)
            np.save(cache, _BN)
    return np.tile(_BN, (h // 64 + 1, w // 64 + 1))[:h, :w]


def tint(bv):
    for b, c in STAR_TINT:
        if bv <= b:
            return c
    return STAR_TINT[-1][1]


def nearest(img):
    return (np.clip(np.floor(np.clip(img, 0, 255) / 85 + 0.5), 0, 3) * 85)


def wu_line(cov, x0, y0, x1, y1, w=1.0):
    """Coverage of an antialiased line into `cov` (max)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 3) + 1
    h, wd = cov.shape
    for k in range(n + 1):
        t = k / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        xi, yi = int(math.floor(x)), int(math.floor(y))
        for dx in (0, 1):
            for dy in (0, 1):
                xx, yy = xi + dx, yi + dy
                if 0 <= xx < wd and 0 <= yy < h:
                    a = (1 - abs(x - 0.5 - xx + 0) if False else 1) and max(0.0, 1 - math.hypot(x - (xx + 0.5), y - (yy + 0.5)) / (0.75 * w))
                    if a > cov[yy, xx]:
                        cov[yy, xx] = a


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def sky_model(alt, gamma, s):
    """The sky's colour (0..1 RGB) at altitude `alt` and `gamma` degrees from the Sun, the Sun at altitude `s`:
    deep at the zenith and pale at the horizon by day; through twilight a blue that brightens toward the
    horizon on the Sun's side, warm close to it; flat night blue below -18 degrees."""
    night = np.array((0.0, 0.0, 1 / 3))
    a = np.clip(alt, 0, 90)[..., None]
    g = gamma[..., None]
    low = np.clip(1 - a / 90, 0, 1) ** 3
    day = np.array((0.04, 0.30, 0.72)) * (1 - low) + np.array((0.50, 0.74, 1.0)) * low
    day = day + np.array((0.45, 0.32, 0.10)) * np.exp(-g / 14)
    side = np.exp(-g / 75)
    blue = np.array((0.03, 0.17, 0.47)) * np.exp(-a / 22) * (0.35 + 0.65 * side)
    warm = np.array((0.62, 0.30, 0.10)) * np.exp(-a / 8) * np.exp(-g / 32)
    tw = night + blue * smooth(-18, -3, s) + warm * smooth(-13, -1, s)
    w_day = smooth(-3, 7, s)
    return tw * (1 - w_day) + day * w_day


COOL = [c8(0, 0, 1), c8(0, 0, 2), c8(0, 1, 2), c8(0, 2, 3), c8(1, 2, 3), c8(2, 3, 3)]     # night .. pale day
WARM = [c8(1, 1, 2), c8(2, 1, 2), c8(3, 1, 1), c8(3, 2, 1), c8(3, 3, 2)]                   # dusk's glow, faint to bright


def sky_scalar(alt, gamma, s):
    """Sky brightness on the COOL ramp (0 night .. 5 palest) and a warm glow 0..1, from the Sun's altitude `s`,
    a point's altitude and its distance `gamma` from the Sun (degrees)."""
    a = np.clip(alt, 0, 90)
    day = smooth(-3, 7, s)
    horizon = np.exp(-a / 32)
    sunside = np.exp(-gamma / 80)
    lift = smooth(-18, -1, s)
    b_tw = lift * (0.8 + 3.0 * horizon * (0.25 + 0.75 * sunside) * (0.6 + 0.4 * lift))
    b_day = 2.3 + 2.1 * (1 - a / 90) ** 3 + 1.4 * np.exp(-gamma / 11)
    b = b_tw * (1 - day) + b_day * day
    warm = smooth(-11, -1, s) * (1 - smooth(-1, 5, s)) * np.exp(-a / 15) * np.exp(-gamma / 42) * 1.25
    return np.clip(b, 0, 5), np.clip(warm, 0, 1)


def banded(v, ramp, t, px=1.6):
    """Flat bands of the ramp's colours along `v`, each edge softened by a dither about `px` pixels wide
    (the value's own gradient sets how wide that is in value: edges stay fine where it changes slowly)."""
    gy, gx = np.gradient(v)
    w = np.clip(np.hypot(gx, gy) * px, 1e-3, 0.5)
    k = np.floor(v + 0.5).astype(int)                 # bands centred on whole values, edges at the halves
    f = v + 0.5 - k                                   # 0..1 across a band; its upper edge at 1
    lo = np.clip(1 - f, 0, None)                      # distance below the upper edge
    hi = f                                            # above the lower edge
    p_up = np.clip(0.5 - lo / (2 * w), 0, 1)          # chance of the band above, near the upper edge
    p_dn = np.clip(0.5 - hi / (2 * w), 0, 1)          # of the band below, near the lower edge
    idx = k + (t < p_up) - (t > 1 - p_dn)
    return np.array(ramp)[np.clip(idx, 0, len(ramp) - 1)]


def sky_state(sun_alt):
    """(the sky's main colour, faintest star shown, figures 0..1) by the Sun's height."""
    faintest = float(np.interp(sun_alt, [-16, -10, -5, -1.5], [4.6, 3.4, 2.0, 0.4]))
    if sun_alt > -1.5:
        faintest = -9
    figs = 1.0 if sun_alt < -10.5 else 0.0
    return PAL["night"], faintest, figs


def render(when, dial, sky, tz, fig_mag=3.8, show_ecliptic=True, round_screen=True):
    stars, lines, mw = sky
    Wp, Hp = dial.w, dial.h
    lst = astro.sidereal(when, dial.lon)
    pos = astro.positions(when)
    sun_alt = astro.altitude(*pos["sun"], lst, dial.lat)
    sky_c, faintest, figs = sky_state(sun_alt)
    lat = abs(dial.lat) * astro.D2R

    # the window, with its edge's coverage from a finer grid
    ys, xs = np.mgrid[0:Hp * SS, 0:Wp * SS]
    dx, dy = (xs + 0.5) / SS - dial.cx, (ys + 0.5) / SS - dial.cy
    rho = np.hypot(dx, dy)
    dec = (90 - rho / dial.k) * astro.D2R
    sin_alt = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(np.arctan2(dx, dy))
    win_ss = ((sin_alt > 0) & (rho <= dial.r_disc)).astype(np.float64)
    win = win_ss.reshape(Hp, SS, Wp, SS).mean(axis=(1, 3))
    inside = win > 0.5

    img = np.zeros((Hp, Wp, 3))
    img[:] = PAL["jacket"]
    # the sky through the window, dithered from the sky model (flat night blue after dark)
    yy1, xx1 = np.mgrid[0:Hp, 0:Wp]
    pdx, pdy = xx1 + 0.5 - dial.cx, yy1 + 0.5 - dial.cy
    pdec = (90 - np.hypot(pdx, pdy) / dial.k) * astro.D2R
    pha = np.arctan2(pdx, pdy)
    palt = np.degrees(np.arcsin(np.clip(np.sin(lat) * np.sin(pdec) + np.cos(lat) * np.cos(pdec) * np.cos(pha), -1, 1)))
    sdec, sha = pos["sun"][1] * astro.D2R, (lst - pos["sun"][0]) * astro.D2R
    cg = np.sin(pdec) * np.sin(sdec) + np.cos(pdec) * np.cos(sdec) * np.cos(pha - sha)
    gamma = np.degrees(np.arccos(np.clip(cg, -1, 1)))
    bval, warm = sky_scalar(palt, gamma, sun_alt)
    tt = bn_tile(Hp, Wp)
    skyq = banded(bval, COOL, tt)
    wv = warm * len(WARM) + 0.2
    hot = wv >= 1.0
    if hot.any():
        wq = banded(np.clip(wv - 1, 0, len(WARM) - 1), WARM, tt)
        edge = smooth(0.0, 0.5, wv - 1.0) > tt
        skyq = np.where((hot & edge)[..., None], wq, skyq)
    img[inside] = skyq[inside]

    # the Milky Way, dithered between the night sky and a milky blue-grey (night only)
    if sun_alt < -15:
        # each level's rings filled even-odd: the band wraps the sky, so its edges are two loops round the pole
        lay = np.zeros((Hp * SS, Wp * SS))
        for level, polys in enumerate(mw):
            acc = np.zeros((Hp * SS, Wp * SS), bool)
            for poly in polys:
                for ring in poly:
                    pts = [(p[0] * SS, p[1] * SS) for p in (dial.project(ra, de, lst) for ra, de in ring)]
                    if len(pts) > 2:
                        l = Image.new("1", (Wp * SS, Hp * SS), 0)
                        ImageDraw.Draw(l).polygon(pts, fill=1)
                        acc ^= np.asarray(l, bool)
            lay = np.maximum(lay, acc * (level + 1) / len(mw))
        m = lay.reshape(Hp, SS, Wp, SS).mean(axis=(1, 3))
        dens = np.clip(m * 0.42, 0, 1) ** 1.2
        on = (dens > bn_tile(Hp, Wp)) & inside
        img[on] = PAL["milky"]

    # figures: lines between stars of at least `fig_mag`, stopping short of each star
    if figs > 0:
        bright = {}
        for ra, de, mg, bv in stars:
            bright[(round(ra, 2), round(de, 2))] = mg
        cov = np.zeros((Hp, Wp))
        for ls in lines:
            for (ra0, de0), (ra1, de1) in zip(ls, ls[1:]):
                m0 = bright.get((round(ra0, 2), round(de0, 2)), 9)
                m1 = bright.get((round(ra1, 2), round(de1, 2)), 9)
                if max(m0, m1) > fig_mag:
                    continue
                x0, y0 = dial.project(ra0, de0, lst)
                x1, y1 = dial.project(ra1, de1, lst)
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 3.2:
                    continue
                gap = 1.6 / L
                wu_line(cov, x0 + (x1 - x0) * gap, y0 + (y1 - y0) * gap, x1 - (x1 - x0) * gap, y1 - (y1 - y0) * gap)
        on = (cov > 0.55) & inside
        img[on] = PAL["line"]

    # the ecliptic, dotted
    if show_ecliptic and sun_alt < -0.8:
        for lam in range(0, 360, 6):
            ra, de = astro.ecl_to_eq(lam, 0, pos["eps"])
            x, y = dial.project(ra, de, lst)
            xi, yi = int(x), int(y)
            if 0 <= xi < Wp and 0 <= yi < Hp and inside[yi, xi] and sun_alt < -12 and (img[yi, xi] == sky_c).all():
                img[yi, xi] = PAL["ecl"] * 0.5 + sky_c * 0.5

    # stars, stamped by brightness
    def put(x, y, c):
        if 0 <= x < Wp and 0 <= y < Hp and inside[y, x]:
            img[y, x] = c
    for ra, de, mg, bv in sorted(stars, key=lambda s: -s[2]):
        if mg > faintest:
            continue
        x, y = dial.project(ra, de, lst)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        c = tint(bv)
        if mg < 0.6:                                         # the brightest: a small cross with a bright heart
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(xi + ox, yi + oy, c * 0.67)
            put(xi, yi, np.maximum(c, 255 * 0.99))
        elif mg < 1.6:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(xi + ox, yi + oy, PAL["faint"] if bv < 0.9 else c8(1, 1, 1))
            put(xi, yi, c)
        elif mg < 2.6:
            put(xi, yi, c)
        elif mg < 3.6:
            put(xi, yi, PAL["mid"] if bv < 0.9 else c8(2, 2, 1))
        else:
            put(xi, yi, PAL["faint"])

    # the planets
    for p, c in PLANETS.items():
        if sun_alt > -3 or (p == "mercury" and sun_alt > -8):
            continue
        x, y = dial.project(*pos[p], lst)
        xi, yi = int(math.floor(x)), int(math.floor(y))
        big = p in ("venus", "jupiter")
        for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)) if big else ((0, 0), (1, 0), (0, 1)):
            put(xi + ox, yi + oy, c)

    # the Moon: its lit side toward the Sun
    mx, my = dial.project(*pos["moon"], lst)
    sx, sy = dial.project(*pos["sun"], lst)
    rm = 3.3
    ra_m, de_m = pos["moon"]
    ra_s, de_s = pos["sun"]
    vec = lambda ra, de: np.array([math.cos(math.radians(de)) * math.cos(math.radians(ra)),
                                   math.cos(math.radians(de)) * math.sin(math.radians(ra)), math.sin(math.radians(de))])
    vm, vs = vec(ra_m, de_m), vec(ra_s, de_s)
    st = vm + 0.02 * (vs - vm)
    st /= np.linalg.norm(st)
    tx, ty = dial.project(math.degrees(math.atan2(st[1], st[0])) % 360, math.degrees(math.asin(st[2])), lst)
    ux, uy = tx - mx, ty - my
    n = math.hypot(ux, uy) or 1
    ux, uy = ux / n, uy / n
    k = 1 - 2 * pos["moon_phase"]
    for yi in range(int(my - rm - 2), int(my + rm + 3)):
        for xi in range(int(mx - rm - 2), int(mx + rm + 3)):
            if not (0 <= xi < Wp and 0 <= yi < Hp and inside[yi, xi]):
                continue
            px, py = xi + 0.5 - mx, yi + 0.5 - my
            d = math.hypot(px, py)
            if d > rm:
                continue
            along, across = (px * ux + py * uy) / rm, (-px * uy + py * ux) / rm
            lit = along > k * math.sqrt(max(0.0, 1 - across * across))
            if lit:
                img[yi, xi] = PAL["moon"]
            elif sun_alt < -12:
                img[yi, xi] = c8(1, 1, 1)                    # earthshine, after dark

    # the Sun, by day: a warm disc with a dithered glow
    if sun_alt > -0.8:
        t = np.tile(BAYER, (Hp // 4 + 1, Wp // 4 + 1))[:Hp, :Wp]
        yy, xx = np.mgrid[0:Hp, 0:Wp]
        dd = np.hypot(xx + 0.5 - sx, yy + 0.5 - sy)
        rs = 3.6
        glow = np.clip(1 - (dd - rs) / 9.0, 0, 1) ** 1.5 * 0.85
        img[(glow > t) & inside & (dd > rs)] = c8(2, 3, 3)
        img[(dd <= rs + 0.4) & inside] = PAL["sun_core"]

    # the window's rim: the jacket's cut edge
    edge = Image.new("L", (Wp * SS, Hp * SS), 0)
    pts = []
    for a in np.linspace(-180, 180, 721):
        de = math.degrees(math.atan(-math.cos(math.radians(a)) / math.tan(lat)))
        r = min((90 - de) * dial.k, dial.r_disc)
        pts.append(((dial.cx + r * math.sin(math.radians(a))) * SS, (dial.cy + r * math.cos(math.radians(a))) * SS))
    ImageDraw.Draw(edge).line(pts, fill=255, width=round(SS * 0.8), joint="curve")
    e = np.asarray(edge, np.float64).reshape(Hp, SS, Wp, SS).mean(axis=(1, 3)) / 255
    img[(e > 0.5) & ~inside] = PAL["rim"]

    # the jacket: a 24-hour ring set to civil time; the Sun's pip reads it
    sun_ang = lst - pos["sun"][0]
    local = when.astimezone(tz)
    minutes = local.hour * 60 + local.minute + local.second / 60
    ring = lambda m: sun_ang + (m - minutes) * 0.25
    R = dial.R
    tick = Image.new("L", (Wp * SS, Hp * SS), 0)
    tickm = Image.new("L", (Wp * SS, Hp * SS), 0)
    for hh in range(48):
        if hh % 4 == 0:
            continue                                          # even hours carry their numerals
        a = math.radians(ring(hh * 30))
        s, c = math.sin(a), math.cos(a)
        rr = R * 0.950
        x, y = (dial.cx + rr * s) * SS, (dial.cy + rr * c) * SS
        r = SS * (1.05 if hh % 2 == 0 else 0.6)
        ImageDraw.Draw(tickm if hh % 2 == 0 else tick).ellipse([x - r, y - r, x + r, y + r], fill=255)
    for lay, col in ((tick, PAL["tick"]), (tickm, PAL["num"])):
        a = np.asarray(lay, np.float64).reshape(Hp, SS, Wp, SS).mean(axis=(1, 3)) / 255
        img[(a > 0.4) & ~inside] = col
    for hr in range(0, 24, 2):
        a = math.radians(ring(hr * 60))
        rr = R * 0.950
        x, y = dial.cx + rr * math.sin(a), dial.cy + rr * math.cos(a)
        al = glyph_alpha(str(hr), 8)
        h, w = al.shape
        x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
        for j in range(h):
            for i in range(w):
                if al[j, i] > 0.42 and 0 <= y0 + j < Hp and 0 <= x0 + i < Wp:
                    img[y0 + j, x0 + i] = PAL["num"] if al[j, i] > 0.7 else PAL["num"] * 0.5
    # the Sun's pip
    a = math.radians(sun_ang)
    s, c = math.sin(a), math.cos(a)
    pip = Image.new("L", (Wp * SS, Hp * SS), 0)
    tip, base_r, half = R * 0.872, R * 0.915, R * 0.024
    poly = [((dial.cx + tip * s) * SS, (dial.cy + tip * c) * SS),
            ((dial.cx + base_r * s - half * c) * SS, (dial.cy + base_r * c + half * s) * SS),
            ((dial.cx + base_r * s + half * c) * SS, (dial.cy + base_r * c - half * s) * SS)]
    ImageDraw.Draw(pip).polygon(poly, fill=255)
    pa = np.asarray(pip, np.float64).reshape(Hp, SS, Wp, SS).mean(axis=(1, 3)) / 255
    img[pa > 0.45] = PAL["sun"]
    # the cardinal points, outside the window
    for label, ang in (("N", 180), ("E", -90), ("S", 0), ("W", 90)):
        de = math.degrees(math.atan(-math.cos(math.radians(ang)) / math.tan(lat)))
        r = (90 - de) * dial.k + 6.5
        if label == "S":
            continue                                          # the south point meets the ring: the ring says it
        x, y = dial.cx + r * math.sin(math.radians(ang)), dial.cy + r * math.cos(math.radians(ang))
        al = glyph_alpha(label, 7)
        h, w = al.shape
        x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
        for j in range(h):
            for i in range(w):
                if al[j, i] > 0.45 and 0 <= y0 + j < Hp and 0 <= x0 + i < Wp:
                    img[y0 + j, x0 + i] = PAL["card"]
    days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    date = f"{days[local.weekday()]} {local.day}"
    al = glyph_alpha(date, 8)
    h, w = al.shape
    top_of_window = dial.cy - abs(dial.lat) * dial.k
    yc = (dial.cy - R * 0.80 + top_of_window) / 2
    x0, y0 = int(round(dial.cx - w / 2)), int(round(yc - h / 2))
    for j in range(h):
        for i in range(w):
            if al[j, i] > 0.45:
                img[y0 + j, x0 + i] = PAL["date"]
    if round_screen:
        yy, xx = np.mgrid[0:Hp, 0:Wp]
        img[np.hypot(xx + 0.5 - dial.cx, yy + 0.5 - dial.cy) > Wp / 2] = 0
    return nearest(img).astype(np.uint8), sun_alt


if __name__ == "__main__":
    ny = ZoneInfo("America/New_York")
    sky = load_sky(4.6)
    out = ROOT / "out"
    dial = Dial(260, 260, 40.71, -74.01)
    for label, t in (("night", datetime(2026, 10, 14, 21, 30, tzinfo=ny)), ("day", datetime(2026, 10, 14, 12, 15, tzinfo=ny)),
                     ("dusk", datetime(2026, 10, 14, 19, 10, tzinfo=ny)), ("predawn", datetime(2026, 10, 15, 5, 40, tzinfo=ny))):
        im, alt = render(t.astimezone(timezone.utc), dial, sky, ny)
        Image.fromarray(im).save(out / f"v2-round2-{label}.png")
        Image.fromarray(im).resize((780, 780), Image.NEAREST).save(out / f"v2-round2-{label}-3x.png")
        print(label, round(alt, 1))
