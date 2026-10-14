"""The compass view: a flick turns the compass on for half a minute and the face
becomes a window onto the sky where the watch points, horizon at the bottom,
names on what is bright; then the compass goes off and the planisphere returns.

    uv run python proto/look.py
"""
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import astro
from render import load_sky
from render2 import (PAL, COOL, WARM, PLANETS, c8, tint, bn_tile, sky_scalar, banded, smooth, star_names,
                     stamp_text, clock_text, nearest, wu_line, sky_state)

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")
GNP = (192.85948, 27.12825)                  # the galactic north pole (J2000)


def altaz(ra, dec, lst, lat):
    """(altitude, azimuth from north through east), degrees."""
    h = math.radians(lst - ra)
    d, p = math.radians(dec), math.radians(lat)
    alt = math.asin(math.sin(p) * math.sin(d) + math.cos(p) * math.cos(d) * math.cos(h))
    az = math.atan2(-math.cos(d) * math.sin(h), math.sin(d) * math.cos(p) - math.cos(d) * math.cos(h) * math.sin(p))
    return math.degrees(alt), math.degrees(az) % 360


def look(when, w, h, lat, lon, heading, sky, tz, fov=100.0, round_screen=True):
    stars, lines, mw, named = sky
    lst = astro.sidereal(when, lon)
    pos = astro.positions(when)
    sun_alt, sun_az = altaz(*pos["sun"], lst, lat)
    _, faintest, figs = sky_state(sun_alt)
    cx = w / 2
    k = w / fov                                        # pixels per degree, both ways
    hy = h * 0.72                                      # the horizon
    def scr(alt, az):
        d = (az - heading + 540) % 360 - 180
        return cx + d * k, hy - alt * k, d
    img = np.zeros((h, w, 3))

    # the sky: per pixel altitude and azimuth, the same banded sky model as the dial's window
    yy, xx = np.mgrid[0:h, 0:w]
    palt = (hy - (yy + 0.5)) / k
    paz = (heading + (xx + 0.5 - cx) / k) % 360
    above = palt > 0
    a, z = np.radians(np.clip(palt, -90, 90)), np.radians(paz)
    # direction vectors (east, north, up) and the Sun's
    v = np.stack([np.cos(a) * np.sin(z), np.cos(a) * np.cos(z), np.sin(a)], -1)
    sa, sz = math.radians(sun_alt), math.radians(sun_az)
    vs = np.array([math.cos(sa) * math.sin(sz), math.cos(sa) * math.cos(sz), math.sin(sa)])
    gamma = np.degrees(np.arccos(np.clip(v @ vs, -1, 1)))
    bval, warm = sky_scalar(palt, gamma, sun_alt)
    tt = bn_tile(h, w)
    skyq = banded(bval, COOL, tt)
    wv = warm * len(WARM) + 0.2
    hot = wv >= 1.0
    if hot.any():
        wq = banded(np.clip(wv - 1, 0, len(WARM) - 1), WARM, tt)
        skyq = np.where((hot & (smooth(0, 0.5, wv - 1) > tt))[..., None], wq, skyq)
    img[above] = skyq[above]

    # the Milky Way, from galactic latitude (brighter toward the galaxy's centre), as grain, after dark
    if sun_alt < -15:
        # pixel directions to equatorial: rotate (east, north, up) by the local sidereal time and latitude
        p = math.radians(lat)
        # hour angle and declination of each pixel
        dec = np.arcsin(np.clip(np.sin(p) * v[..., 2] + np.cos(p) * v[..., 1], -1, 1))
        ha = np.arctan2(-v[..., 0], np.cos(p) * v[..., 2] - np.sin(p) * v[..., 1])
        ra = np.radians(lst) - ha
        ng_ra, ng_de = map(math.radians, GNP)
        sinb = np.sin(dec) * math.sin(ng_de) + np.cos(dec) * math.cos(ng_de) * np.cos(ra - ng_ra)
        b = np.degrees(np.arcsin(np.clip(sinb, -1, 1)))
        # galactic longitude, roughly, for the centre's glow: angle from the centre (RA 266.4, Dec -28.9)
        gc_ra, gc_de = math.radians(266.40), math.radians(-28.94)
        cgc = np.sin(dec) * math.sin(gc_de) + np.cos(dec) * math.cos(gc_de) * np.cos(ra - gc_ra)
        centre = (1 + np.clip(cgc, -1, 1)) / 2
        dens = np.exp(-(b / (6 + 5 * centre)) ** 2) * (0.10 + 0.22 * centre)
        img[(dens > tt) & above & (palt > 3)] = PAL["milky"]

    # figures
    def visible(alt, d):
        return alt > 0.5 and abs(d) < fov / 2 + 2
    if figs > 0:
        bright = {(round(ra, 2), round(de, 2)): m for ra, de, m, bv in stars}
        cov = np.zeros((h, w))
        for ls in lines:
            for (ra0, de0), (ra1, de1) in zip(ls, ls[1:]):
                if max(bright.get((round(ra0, 2), round(de0, 2)), 9), bright.get((round(ra1, 2), round(de1, 2)), 9)) > 3.8:
                    continue
                al0, az0 = altaz(ra0, de0, lst, lat)
                al1, az1 = altaz(ra1, de1, lst, lat)
                x0, y0, d0 = scr(al0, az0)
                x1, y1, d1 = scr(al1, az1)
                if not (visible(al0, d0) or visible(al1, d1)) or abs(d0 - d1) > 60:
                    continue
                L = math.hypot(x1 - x0, y1 - y0)
                if L < 4:
                    continue
                g = 2.2 / L
                wu_line(cov, x0 + (x1 - x0) * g, y0 + (y1 - y0) * g, x1 - (x1 - x0) * g, y1 - (y1 - y0) * g)
        img[(cov > 0.55) & above] = PAL["line"]

    # stars, a touch larger than on the dial: this view is closer
    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h and above[y, x]:
            img[y, x] = c
    for ra, de, m, bv in sorted(stars, key=lambda s: -s[2]):
        if m > faintest:
            continue
        al, az = altaz(ra, de, lst, lat)
        x, y, d = scr(al, az)
        if not visible(al, d):
            continue
        xi, yi = int(x), int(y)
        c = tint(bv)
        if m < 1.0:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(xi + ox, yi + oy, c * 0.67)
            put(xi, yi, c8(3, 3, 3))
        elif m < 2.2:
            for ox, oy in ((1, 0), (0, 1)):
                put(xi + ox, yi + oy, PAL["faint"])
            put(xi, yi, c)
        elif m < 3.4:
            put(xi, yi, PAL["mid"] if bv < 0.9 else c8(2, 2, 1))
        else:
            put(xi, yi, PAL["faint"])
    # planets, the Moon and the Sun
    items = []
    for pn, c in PLANETS.items():
        al, az = altaz(*pos[pn], lst, lat)
        x, y, d = scr(al, az)
        if visible(al, d) and sun_alt < -3:
            for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
                put(int(x) + ox, int(y) + oy, c)
            items.append((pn.upper(), x, y, c8(3, 2, 1)))
    mal, maz = altaz(*pos["moon"], lst, lat)
    mx, my, md = scr(mal, maz)
    if visible(mal, md):
        rm = 4.5
        sx, sy, _ = scr(sun_alt, sun_az)
        ux, uy = sx - mx, sy - my
        n = math.hypot(ux, uy) or 1
        ux, uy = ux / n, uy / n
        kk = 1 - 2 * pos["moon_phase"]
        for yi in range(int(my - rm - 1), int(my + rm + 2)):
            for xi in range(int(mx - rm - 1), int(mx + rm + 2)):
                if not (0 <= xi < w and 0 <= yi < h):
                    continue
                px, py = xi + 0.5 - mx, yi + 0.5 - my
                if math.hypot(px, py) > rm:
                    continue
                al_, ac_ = (px * ux + py * uy) / rm, (-px * uy + py * ux) / rm
                if al_ > kk * math.sqrt(max(0, 1 - ac_ * ac_)):
                    img[yi, xi] = PAL["moon"]
                elif sun_alt < -12:
                    img[yi, xi] = c8(1, 1, 1)
        items.insert(0, ("MOON", mx + 3, my, c8(3, 3, 2)))
    sx, sy, sd = scr(sun_alt, sun_az)
    if sun_alt > -0.8 and abs(sd) < fov / 2 + 6:
        dd = np.hypot(xx + 0.5 - sx, yy + 0.5 - sy)
        rs = 5.0
        glow = np.clip(1 - (dd - rs) / 12.0, 0, 1) ** 1.5 * 0.85
        img[(glow > tt) & above & (dd > rs)] = c8(2, 3, 3)
        img[(dd <= rs + 0.4) & above] = PAL["sun_core"]

    # names: the Moon, the planets, the brightest stars in view
    names = star_names()
    if sun_alt < -9:
        shown = 0
        for ra, de, m, bv, hip in sorted(named, key=lambda s: s[2]):
            if shown >= 5 or m > 1.6:
                break
            al, az = altaz(ra, de, lst, lat)
            x, y, d = scr(al, az)
            if visible(al, d) and al > 5 and hip in names and 8 < x < w - 8 and y > 22:
                items.append((names[hip].upper(), x, y, c8(2, 2, 2)))
                shown += 1
    boxes = []
    from render import glyph_alpha
    for text, x, y, col in items:
        al = glyph_alpha(text, 7)
        hh, ww = al.shape
        for lx in (x + 5, x - 5 - ww):
            box = (lx - 1, y - hh / 2 - 1, lx + ww + 1, y + hh / 2 + 1)
            if box[0] < 4 or box[2] > w - 4 or box[3] > hy - 1 or box[1] < 20:
                continue
            if round_screen and any(math.hypot(bx - cx, by - h / 2) > w / 2 - 4 for bx in (box[0], box[2]) for by in (box[1], box[3])):
                continue
            if any(box[0] < b[2] and b[0] < box[2] and box[1] < b[3] and b[1] < box[3] for b in boxes):
                continue
            boxes.append(box)
            stamp_text(img, text, lx, y, 7, col, mask=above, align="left")
            break

    # the ground: the horizon, the compass points along it, and where the watch points
    img[(yy >= hy) & (yy < hy + 1)] = c8(1, 1, 1)
    for az in range(0, 360, 15):
        x, _, d = scr(0, az)
        if abs(d) > fov / 2 + 4:
            continue
        xi = int(x)
        tick = 5 if az % 45 == 0 else 2
        for j in range(tick):
            if 0 <= xi < w:
                img[int(hy) + 1 + j, xi] = c8(2, 2, 2) if az % 45 == 0 else c8(1, 1, 1)
        if az % 45 == 0:
            label = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][az // 45]
            stamp_text(img, label, x, hy + 14, 8, c8(2, 2, 2))
    # the pointer: where the watch points, and the time, small
    for j in range(5):
        for i in range(-j, j + 1):
            y, x = int(hy + 22 + j), int(cx + i)
            img[y, x] = PAL["sun"]
    stamp_text(img, f"{int(round(heading)) % 360}", cx, hy + 36, 8, PAL["sun"])
    stamp_text(img, clock_text(when.astimezone(tz)), cx, h * 0.075 + 4, 9, c8(2, 2, 2))
    # altitude: faint dots at 30 and 60 degrees
    for alt in (30, 60):
        y = int(hy - alt * k)
        for x in range(0, w, 6):
            if 0 <= y < h and above[y, x] and (img[y, x] == skyq[y, x]).all():
                img[y, x] = np.minimum(skyq[y, x] + 85, 255) if sun_alt < -6 else c8(3, 3, 3)
    if round_screen:
        img[np.hypot(xx + 0.5 - cx, yy + 0.5 - h / 2) > w / 2] = 0
    return nearest(img).astype(np.uint8)


if __name__ == "__main__":
    sky = load_sky(4.6)
    out = ROOT / "out"
    t = datetime(2026, 10, 14, 21, 30, tzinfo=NY).astimezone(timezone.utc)
    frames = []
    for hd in range(0, 360, 4):
        frames.append(Image.fromarray(look(t, 260, 260, 40.71, -74.01, hd, sky, NY)).resize((520, 520), Image.NEAREST))
    pal = [f.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(ROOT / "docs" / "compass-turn.gif", save_all=True, append_images=pal[1:], duration=60, loop=0, optimize=True)
    stills = [Image.fromarray(look(t, 260, 260, 40.71, -74.01, hd, sky, NY)) for hd in (45, 135, 225, 300)]
    S = Image.new("RGB", (4 * 266, 266), (24, 24, 26))
    for i, im in enumerate(stills):
        S.paste(im, (i * 266 + 3, 3))
    S.resize((S.width * 2, S.height * 2), Image.NEAREST).save(ROOT / "docs" / "compass-views.png")
    S.save(out / "compass-views.png")
    print(len(frames), "frames")
