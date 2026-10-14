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

Each shows the time as astronomers write it, 21ʰ 30ᵐ, large in the jacket
above the window, the date in italic, the Sun's next rising or setting in
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
from typeset import run_alpha, ink, astro_time, arc_text
from pixeltext import pixel_text, time_text, concat, stamp, box_of, degrees_text, bounds
import emblems
import flair

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


def nearest(img):
    return (np.clip(np.floor(np.clip(img, 0, 255) / 85 + 0.5), 0, 3) * 85).astype(np.uint8)


def render(when, dial, sky, tz, plate="planisphere", round_screen=True, corners="glory"):
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
    SS = 4

    # where the window is
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
    night_level = 0.0
    if P["window"] == "sky":
        bval, warm = sky_scalar(palt, gamma, sun_alt)
        ramp = [P["night"]] + [c for c in COOL if (c != P["night"]).any() and c.sum() > P["night"].sum()]
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
        dark = True                                    # a printed chart shows its stars by day and night alike
    ground = img.copy()
    faint = float(np.interp(sun_alt, [-16, -10, -5, -1.5], [4.6, 3.4, 2.0, 0.4])) if P["window"] != "paper" else 4.6
    if P["window"] != "paper" and sun_alt > -1.5:
        faint = -9
    figs = P["window"] == "paper" or sun_alt < -10.5

    # the Milky Way, stippled as the engravers did
    if (P["window"] == "paper") or sun_alt < -15:
        acc_all = np.zeros((H * SS, W * SS))
        for level, polys in enumerate(mw):
            acc = np.zeros((H * SS, W * SS), bool)
            for poly in polys:
                for ring in poly:
                    pts = [(p[0] * SS, p[1] * SS) for p in (dial.project(ra, de, lst) for ra, de in ring)]
                    if len(pts) > 2:
                        l = Image.new("1", (W * SS, H * SS), 0)
                        ImageDraw.Draw(l).polygon(pts, fill=1)
                        acc ^= np.asarray(l, bool)
            acc_all = np.maximum(acc_all, acc * (level + 1) / len(mw))
        m = acc_all.reshape(H, SS, W, SS).mean(axis=(1, 3))
        dens = np.clip(m * (0.30 if P["window"] == "paper" else 0.42), 0, 1) ** 1.2
        img[(dens > tt) & inside] = P["milky"]

    # the celestial equator and the ecliptic, as charts rule them: fine dots
    for lam in range(0, 360, 3):
        for kind, (ra, de) in (("ecl", astro.ecl_to_eq(lam, 0, pos["eps"])), ("eq", (lam, 0.0))):
            if kind == "eq" and lam % 6:
                continue
            x, y = dial.project(ra, de, lst)
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and inside[yi, xi] and (dark or P["window"] == "paper"):
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
                if L < 3.2:
                    continue
                g = 1.7 / L
                wu_line(cov, x0 + (x1 - x0) * g, y0 + (y1 - y0) * g, x1 - (x1 - x0) * g, y1 - (y1 - y0) * g)
        img[(cov > 0.55) & inside] = P["line"]

    # stars, in the plate's symbols: a cross of light, or the engraver's rayed star
    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H and inside[y, x]:
            img[y, x] = c
    paper = P["window"] == "paper"
    for ra, de, mg, bv in sorted(stars, key=lambda s: -s[2]):
        if mg > faint:
            continue
        x, y = dial.project(ra, de, lst)
        xi, yi = int(x), int(y)
        c = P["star"]
        light_paper = paper and P["night"].sum() > 400
        dim = c8(1, 1, 1) if light_paper else c * 0.67 + P["night"] * 0.33
        if mg < 0.6:
            if P["glyph"] == "rays":
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
                    put(xi + ox, yi + oy, c)
                for ox, oy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
                    put(xi + ox, yi + oy, dim)
            else:
                for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(xi + ox, yi + oy, dim)
            put(xi, yi, c)
        elif mg < 1.6:
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                put(xi + ox, yi + oy, c if P["glyph"] == "rays" else dim)
            put(xi, yi, c)
        elif mg < 2.6:
            if P["glyph"] == "rays":
                for ox, oy in ((1, 0), (0, 1)):
                    put(xi + ox, yi + oy, dim)
            put(xi, yi, c)
        elif mg < 3.6:
            put(xi, yi, c if light_paper else dim)
        else:
            put(xi, yi, dim if light_paper else c * 0.40 + P["night"] * 0.6)

    # the planets, the Moon with its phase, and the Sun
    for pn in ("venus", "jupiter", "mars", "saturn", "mercury"):
        if not paper and sun_alt > -3:
            continue
        x, y = dial.project(*pos[pn], lst)
        xi, yi = int(x), int(y)
        for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
            put(xi + ox, yi + oy, P["planet"])
    mx, my = dial.project(*pos["moon"], lst)
    sx, sy = dial.project(*pos["sun"], lst)
    vm = np.array([math.cos(math.radians(pos["moon"][1])) * math.cos(math.radians(pos["moon"][0])),
                   math.cos(math.radians(pos["moon"][1])) * math.sin(math.radians(pos["moon"][0])), math.sin(math.radians(pos["moon"][1]))])
    vs = np.array([math.cos(math.radians(pos["sun"][1])) * math.cos(math.radians(pos["sun"][0])),
                   math.cos(math.radians(pos["sun"][1])) * math.sin(math.radians(pos["sun"][0])), math.sin(math.radians(pos["sun"][1]))])
    st = vm + 0.02 * (vs - vm)
    st /= np.linalg.norm(st)
    tx, ty = dial.project(math.degrees(math.atan2(st[1], st[0])) % 360, math.degrees(math.asin(st[2])), lst)
    ux, uy = tx - mx, ty - my
    n = math.hypot(ux, uy) or 1
    ux, uy = ux / n, uy / n
    kk = 1 - 2 * pos["moon_phase"]
    rm = 3.3
    moon_lit = c8(3, 3, 2) if not paper else c8(3, 3, 3)
    for yi in range(int(my - rm - 1), int(my + rm + 2)):
        for xi in range(int(mx - rm - 1), int(mx + rm + 2)):
            if not (0 <= xi < W and 0 <= yi < H and inside[yi, xi]):
                continue
            px, py = xi + 0.5 - mx, yi + 0.5 - my
            dd = math.hypot(px, py)
            if dd > rm + 0.3:
                continue
            al, ac = (px * ux + py * uy) / rm, (-px * uy + py * ux) / rm
            lit = al > kk * math.sqrt(max(0, 1 - ac * ac))
            if paper:                                  # an engraved Moon: an outline, the dark part hatched
                img[yi, xi] = P["star"] if (dd > rm - 0.9 or (not lit and (xi + yi) % 2 == 0)) else P["night"]
            elif lit:
                img[yi, xi] = moon_lit if P["window"] != "red" else c8(3, 0, 0)
            elif dark:
                img[yi, xi] = c8(1, 1, 1) if P["window"] == "sky" else c8(1, 0, 0)
    if sun_alt > -0.8 or paper:
        # the Sun with its face, its rays turning between straight and wavy (after the Sun of May)
        if P["window"] == "red":
            sc = {1: c8(1, 0, 0), 2: c8(3, 0, 0), 3: c8(3, 1, 1)}
        elif paper and P["night"].sum() > 400:
            sc = {1: P["ink"], 2: c8(3, 2, 0), 3: c8(3, 3, 1)}
        else:
            sc = {1: c8(2, 1, 0), 2: c8(3, 2, 0), 3: c8(3, 3, 1)}
        flair.paint(img, flair.sol(5), sx, sy, sc, where=inside)

    # the window's edge: a double rule, as a printed chart's neatline
    for off, wdt in ((0.0, 0.8), (2.4, 0.6)):
        edge = Image.new("L", (W * SS, H * SS), 0)
        pts = []
        for a in np.linspace(-180, 180, 721):
            de = math.degrees(math.atan(-math.cos(math.radians(a)) / math.tan(lat)))
            r = min((90 - de) * dial.k, dial.r_disc) + off
            pts.append(((dial.cx + r * math.sin(math.radians(a))) * SS, (dial.cy + r * math.cos(math.radians(a))) * SS))
        ImageDraw.Draw(edge).line(pts, fill=255, width=max(1, round(SS * wdt)), joint="curve")
        e = np.asarray(edge, np.float64).reshape(H, SS, W, SS).mean(axis=(1, 3)) / 255
        img[(e > 0.45) & ~inside] = P["rule"]

    # names in the sky, in pixel type: stars leaning (oblique), planets in roman, constellations in capitals
    boxes = []
    def place(mask, x, y, colour, centred=False):
        for anchor, lx in ([("centre", x)] if centred else [("left", x + 4), ("right", x - 3)]):
            bx = box_of(mask, lx, y, anchor)
            corners = [(bx[0], bx[1]), (bx[2] - 1, bx[1]), (bx[0], bx[3] - 1), (bx[2] - 1, bx[3] - 1)]
            if not all(0 <= cx_ < W and 0 <= cy_ < H and inside[cy_, cx_] for cx_, cy_ in corners):
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
        place(pixel_text(pn.capitalize()), x + 1, y, P["planet"])
    if dark or paper:
        names = star_names()
        shown = 0
        for ra, de, mg, bv, hip in sorted(named, key=lambda s: s[2]):
            if shown >= 3 or mg > 1.3:
                break
            if astro.altitude(ra, de, lst, dial.lat) < 8 or hip not in names:
                continue
            x, y = dial.project(ra, de, lst)
            if place(pixel_text(names[hip], oblique=True), x, y, P["label"]):
                shown += 1
        cshown = 0
        for name, rank, ra, de in sorted(constellations(), key=lambda c: c[1]):
            if cshown >= 3 or rank > 1 or astro.altitude(ra, de, lst, dial.lat) < 12:
                continue
            x, y = dial.project(ra, de, lst)
            if place(pixel_text(name.upper(), track=1), x, y, P["const"], centred=True):
                cshown += 1

    # the jacket: the 24-hour ring, set for civil time, read by the Sun's pointer
    R = dial.R
    sun_ang = lst - pos["sun"][0]
    minutes = local.hour * 60 + local.minute + local.second / 60
    ring = lambda m: sun_ang + (m - minutes) * 0.25
    dots = Image.new("L", (W * SS, H * SS), 0)
    for q in range(96):
        a = math.radians(ring(q * 15))
        s, c = math.sin(a), math.cos(a)
        r0, r1 = (R * 0.875, R * 0.905) if q % 4 == 0 else (R * 0.875, R * 0.888)
        if q % 4 == 0 and (q // 4) % 3 == 0:
            continue
        ImageDraw.Draw(dots).line([((dial.cx + r0 * s) * SS, (dial.cy + r0 * c) * SS), ((dial.cx + r1 * s) * SS, (dial.cy + r1 * c) * SS)],
                                  fill=255, width=max(1, round(SS * (0.9 if q % 4 == 0 else 0.6))))
    d = np.asarray(dots, np.float64).reshape(H, SS, W, SS).mean(axis=(1, 3)) / 255
    img[(d > 0.42) & ~inside] = P["ink"]
    # a fine circle closing the scale
    circ = Image.new("L", (W * SS, H * SS), 0)
    rr = R * 0.873 * SS
    ImageDraw.Draw(circ).ellipse([dial.cx * SS - rr, dial.cy * SS - rr, dial.cx * SS + rr, dial.cy * SS + rr], outline=255, width=max(1, round(SS * 0.6)))
    cimg = np.asarray(circ, np.float64).reshape(H, SS, W, SS).mean(axis=(1, 3)) / 255
    img[(cimg > 0.42) & ~inside] = P["ink"]
    if P["ring"] == "roman":
        labels = {0: "MIDNIGHT", 12: "NOON", 3: "III", 6: "VI", 9: "IX", 15: "III", 18: "VI", 21: "IX"}
    else:
        labels = {h: str(h) for h in range(0, 24, 3)}
    for hr, text in labels.items():
        ang = ring(hr * 60)
        a = math.radians(ang)
        rr = R * 0.948
        if len(text) > 3:                              # words follow the ring, each letter upright
            up = math.cos(a) < 0
            masks = [pixel_text(ch) for ch in text]
            gap = 2
            total = sum(m.shape[1] for m in masks) + gap * (len(masks) - 1)
            s = -total / 2
            for m in masks:
                mid = s + m.shape[1] / 2
                aa = math.radians(ang + (-1 if up else 1) * math.degrees(mid / rr))
                stamp(img, m, dial.cx + rr * math.sin(aa), dial.cy + rr * math.cos(aa), P["accent"])
                s += m.shape[1] + gap
        else:
            stamp(img, pixel_text(text), dial.cx + rr * math.sin(a), dial.cy + rr * math.cos(a), P["ink"])
    # the Sun's pointer
    a = math.radians(sun_ang)
    s, c = math.sin(a), math.cos(a)
    pip = Image.new("L", (W * SS, H * SS), 0)
    tip, base_r, half = R * 0.873, R * 0.915, R * 0.026
    ImageDraw.Draw(pip).polygon([((dial.cx + tip * s) * SS, (dial.cy + tip * c) * SS),
                                 ((dial.cx + base_r * s - half * c) * SS, (dial.cy + base_r * c + half * s) * SS),
                                 ((dial.cx + base_r * s + half * c) * SS, (dial.cy + base_r * c - half * s) * SS)], fill=255)
    px_, py_ = dial.cx + R * 0.895 * s, dial.cy + R * 0.895 * c
    flair.paint(img, flair.little_sun(), px_, py_, {1: P["accent"], 2: c8(3, 2, 0) if P["window"] != "red" else c8(3, 0, 0)})

    # the time, as an astronomer writes it, with the date and the Sun's next rising or setting
    top_of_window = dial.cy - abs(dial.lat) * dial.k
    ring_in = dial.cy - R * 0.875
    span = top_of_window - ring_in
    big = 30 if W >= 240 else 25
    ink(img, astro_time(str(local.hour), f"{local.minute:02d}", fn, big, fw, feats=("onum", "lnum")[:1]), dial.cx, ring_in + span * 0.36, P["ink"])
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    date = pixel_text(f"{days[local.weekday()]} {local.day} {months[local.month - 1]}", oblique=True)
    if date.shape[1] > span * 2.1:
        date = pixel_text(f"{days[local.weekday()][:3]} {local.day} {months[local.month - 1][:3]}", oblique=True)
    stamp(img, date, dial.cx, ring_in + span * 0.665, P["ink"])
    kind, at = next_sun_event(when, dial.lat, dial.lon)
    if kind:
        t_ = at.astimezone(tz)
        stamp(img, concat(pixel_text(kind), time_text(t_.hour, t_.minute), gap=3), dial.cx, ring_in + span * 0.845, P["accent"])
    # the Time 2's corners: a quiet woodcut texture on the card, nothing to read
    if not round_screen and corners:
        ornament(img, dial, P, corners)
    if round_screen:
        img[np.hypot(xx + 0.5 - dial.cx, yy + 0.5 - dial.cy) > W / 2] = 0
    return nearest(img)



def ornament(img, dial, P, kind):
    """Woodcut texture in the card's corners (outside the ring), in a tint a little away from the card's own:
    'glory' fine rays from the instrument, as engraved frontispieces put rays behind their centrepiece;
    'stars' a field of small engraved stars; 'hatch' an engraver's diagonal shading."""
    H, W = img.shape[:2]
    jacket = P["jacket"]
    light = jacket.sum() > 400
    tint = c8(3, 3, 1) if light else (c8(0, 0, 2) if jacket[2] > 0 else c8(1, 0, 0) if P["window"] == "red" else c8(1, 1, 1))
    yy, xx = np.mgrid[0:H, 0:W]
    dx, dy = xx + 0.5 - dial.cx, yy + 0.5 - dial.cy
    r = np.hypot(dx, dy)
    outside = r > dial.R + 1.5
    if kind == "glory":
        ang = np.degrees(np.arctan2(dy, dx)) % 360
        step = 4.0
        frac = (ang % step) / step
        line = np.abs(frac - 0.5) * step * np.radians(1) * r < 0.55
        long_ = (np.round(ang / step).astype(int) % 2 == 0) | (r < dial.R + 18)
        img[outside & line & long_] = tint
    elif kind == "hatch":
        img[outside & ((xx + yy) % 3 == 0)] = tint
    elif kind == "stars":
        rng = np.random.default_rng(11)
        pts = []
        for _ in range(400):
            x, y = rng.uniform(2, W - 3), rng.uniform(2, H - 3)
            if math.hypot(x - dial.cx, y - dial.cy) < dial.R + 5 or any(math.hypot(x - a, y - b) < 9 for a, b in pts):
                continue
            pts.append((x, y))
        for x, y in pts:
            xi, yi = int(x), int(y)
            big = (xi * 7 + yi * 13) % 3 == 0
            for ox, oy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)) + (((2, 0), (-2, 0), (0, 2), (0, -2)) if big else ()):
                if 0 <= yi + oy < H and 0 <= xi + ox < W and outside[yi + oy, xi + ox]:
                    img[yi + oy, xi + ox] = tint

if __name__ == "__main__":
    sky = load_sky(4.6)
    out = ROOT / "out"
    when = datetime(2026, 10, 14, 21, 30, tzinfo=NY)
    noon = datetime(2026, 10, 14, 12, 15, tzinfo=NY)
    r2, t2 = Dial(260, 260, 40.71, -74.01), Dial(200, 228, 40.71, -74.01)
    names = list(PLATES)
    S = Image.new("RGB", (len(names) * 266, 266 * 2 + 236), (24, 24, 26))
    for i, pl in enumerate(names):
        for row, (t, dial, rnd) in enumerate(((when, r2, True), (noon, r2, True), (when, t2, False))):
            im = Image.fromarray(render(t.astimezone(timezone.utc), dial, sky, NY, pl, rnd, "glory"))
            im.save(out / f"plate-{pl}-{['night', 'noon', 'time2'][row]}.png")
            S.paste(im, (i * 266 + (3 if rnd else 33), row * 266 + 3))
    S.save(out / "plates.png")
    S.resize((S.width * 2, S.height * 2), Image.NEAREST).save(out / "plates-2x.png")
    print("ok")
