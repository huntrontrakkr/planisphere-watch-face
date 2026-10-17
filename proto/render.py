"""A planisphere for the wrist, drawn as the watch would: 64 colours (two
bits a channel), ordered dither, the screen's own pixels.

The star disc carries the sky as a planisphere does (an equidistant polar
map, the celestial pole at the centre) and turns with the sidereal time
under a black jacket. The jacket's oval window is your horizon: through it
the sky as it is now, deep blue at night and day-blue by day. The Sun rides
the ecliptic as the hour hand; a pip on the jacket's 24-hour ring reads it.
"""
import json

import iq
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import astro
import stroke_font

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SS = 4                                          # supersampling for coverage
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16


def quantised(ra, dec):
    """A star's place as the watch's table keeps it (tools/gen_tables.py): right ascension in 65536ths of a turn,
    declination in 65535ths of a half turn from the south pole; the prototype draws the same stars."""
    r = int(round(ra % 360 / 360 * 65536)) % 65536
    d = int(round((dec + 90) / 180 * 65535))
    return r * 360 / 65536, d * 180 / 65535 - 90


def load_sky(mag_limit=5.0):
    stars = []
    for f in json.load(open(DATA / "stars.6.json"))["features"]:
        m = f["properties"]["mag"]
        if m > mag_limit:
            continue
        ra, dec = quantised(*f["geometry"]["coordinates"])
        bv = float(f["properties"].get("bv") or 0.6)
        stars.append((ra, dec, m, bv))
    lines = []
    for f in json.load(open(DATA / "constellations.lines.json"))["features"]:
        for ls in f["geometry"]["coordinates"]:
            lines.append([quantised(ra, dec) for ra, dec in ls])
    named = []
    for f in json.load(open(DATA / "stars.6.json"))["features"]:
        m = f["properties"]["mag"]
        if m <= 2.0:
            ra, dec = quantised(*f["geometry"]["coordinates"])
            named.append((ra, dec, m, float(f["properties"].get("bv") or 0.6), int(f["id"])))
    mw = []
    for f in json.load(open(DATA / "mw.json"))["features"]:
        polys = []
        for poly in f["geometry"]["coordinates"]:
            polys.append([[(ra % 360, dec) for ra, dec in ring] for ring in poly])
        mw.append(polys)
    return stars, lines, mw, named


def star_colour(bv):
    """B-V to a gentle tint: blue-white, white, cream, gold, orange."""
    stops = [(-0.3, (0.75, 0.85, 1.0)), (0.0, (0.9, 0.93, 1.0)), (0.4, (1.0, 1.0, 1.0)), (0.8, (1.0, 0.95, 0.8)),
             (1.2, (1.0, 0.82, 0.55)), (1.8, (1.0, 0.62, 0.35))]
    for (b0, c0), (b1, c1) in zip(stops, stops[1:]):
        if bv <= b1:
            t = max(0.0, min(1.0, (bv - b0) / (b1 - b0)))
            return np.array(c0) * (1 - t) + np.array(c1) * t
    return np.array(stops[-1][1])


class Dial:
    """The layout for a screen of w x h with the instrument of radius `r_face`."""

    def __init__(self, w, h, lat, lon, r_face=None):
        self.w, self.h, self.lat, self.lon = w, h, lat, lon
        self.cx, self.cy = w / 2, h / 2
        self.R = r_face or min(w, h) / 2             # the jacket's outer edge
        self.r_disc = self.R * 0.846                 # the window can reach this far (the star disc)
        self.south = lat < 0
        self.reach = 180 - abs(lat)                  # degrees from the pole to the southernmost horizon point
        self.k = self.r_disc / self.reach            # pixels per degree

    def project(self, ra, dec, lst):
        """Screen position (pixels) of (ra, dec); a planisphere seen from below, south at the bottom: in integers, to
        1/256 pixel, as the watch projects (proto/iq.py, plan_render.c project), the same bits."""
        if self.south:
            dec = -dec
        ra20 = iq.floor_half(iq.f32(iq.f32(ra) * iq.f32(1048576.0 / 360)))
        colat = iq.floor_half(iq.f32(iq.f32(90.0 - iq.f32(dec)) * iq.f32(65535.0 / 180)))
        xq, yq = iq.project_u(ra20, colat, iq.lst20(lst), self.south, iq.kq(self.k),
                              iq.floor_half(iq.f32(self.cx) * 256), iq.floor_half(iq.f32(self.cy) * 256))
        return xq / 256, yq / 256


def hour_angle_screen(dial, angle_deg):
    """Point on a circle round the centre at screen angle measured from the bottom, anticlockwise (as hour angle runs)."""
    return math.sin(angle_deg * astro.D2R), math.cos(angle_deg * astro.D2R)


def sky_colour(sun_alt):
    """The window's sky by the Sun's height: night, three twilights, day (RGB 0..1)."""
    keys = [(-18, (0.0, 0.0, 0.20)), (-12, (0.0, 0.03, 0.30)), (-6, (0.02, 0.12, 0.45)), (0, (0.18, 0.35, 0.70)),
            (6, (0.40, 0.62, 0.92)), (90, (0.45, 0.68, 0.98))]
    if sun_alt <= keys[0][0]:
        return np.array(keys[0][1])
    for (a0, c0), (a1, c1) in zip(keys, keys[1:]):
        if sun_alt <= a1:
            t = (sun_alt - a0) / (a1 - a0)
            return np.array(c0) * (1 - t) + np.array(c1) * t
    return np.array(keys[-1][1])


def glyph_alpha(text, cap):
    """Alpha mask (h x w) of `text` in the stroke font at cap height `cap` px."""
    parts = [stroke_font.render(ch, cap) if ch != " " else (np.zeros((cap, max(1, round(cap * 0.35)))), 0) for ch in text]
    hmax = max(a.shape[0] for a, _ in parts)
    gap = max(1, round(cap * 0.18))
    W = sum(a.shape[1] for a, _ in parts) + gap * (len(parts) - 1)
    out = np.zeros((hmax, W))
    x = 0
    for a, _ in parts:
        out[: a.shape[0], x: x + a.shape[1]] = np.maximum(out[: a.shape[0], x: x + a.shape[1]], a)
        x += a.shape[1] + gap
    return out


def paste_alpha(img, alpha, cx, cy, colour):
    """Blend `colour` into float image `img` through `alpha`, centred at (cx, cy)."""
    h, w = alpha.shape
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    for j in range(h):
        y = y0 + j
        if not 0 <= y < img.shape[0]:
            continue
        for i in range(w):
            x = x0 + i
            if 0 <= x < img.shape[1] and alpha[j, i] > 0:
                a = alpha[j, i]
                img[y, x] = img[y, x] * (1 - a) + np.array(colour) * a


def quantize(img):
    """Two bits a channel by ordered dither: what the watch's 64 colours can show."""
    h, w, _ = img.shape
    t = np.tile(BAYER, (h // 4 + 1, w // 4 + 1))[:h, :w, None]
    return (np.clip(np.floor(np.clip(img, 0, 1) * 3 + t), 0, 3) * 85).astype(np.uint8)


def render(when, dial, sky, style=None):
    style = style or {}
    stars, lines, mw = sky[:3]
    W, H = dial.w * SS, dial.h * SS
    lst = astro.sidereal(when, dial.lon)
    pos = astro.positions(when)
    sun_alt = astro.altitude(*pos["sun"], lst, dial.lat)
    S = lambda p: (p[0] * SS, p[1] * SS)

    # per-pixel: where the window is (the sky above the horizon), at the supersampled grid
    ys, xs = np.mgrid[0:H, 0:W]
    dx, dy = (xs + 0.5) / SS - dial.cx, (ys + 0.5) / SS - dial.cy
    rho = np.hypot(dx, dy)
    ha = np.arctan2(dx, dy)                                   # anticlockwise from the bottom
    dec = 90 - rho / dial.k
    lat = abs(dial.lat) * astro.D2R
    sin_alt = np.sin(lat) * np.sin(dec * astro.D2R) + np.cos(lat) * np.cos(dec * astro.D2R) * np.cos(ha)
    window = (sin_alt > 0) & (rho <= dial.r_disc + 0.5)

    night = max(0.0, min(1.0, (-sun_alt - 4) / 10))           # how dark the sky is (0 day .. 1 night)
    base = sky_colour(sun_alt)
    img = np.zeros((H, W, 3))
    img[window] = base

    # the Milky Way: nested contours, each a little brighter
    if night > 0:
        mwi = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(mwi)
        for level, polys in enumerate(mw):
            layer = Image.new("L", (W, H), 0)
            dl = ImageDraw.Draw(layer)
            for poly in polys:
                rings = [[S(dial.project(ra, de, lst)) for ra, de in ring] for ring in poly]
                if len(rings[0]) > 2:
                    dl.polygon(rings[0], fill=255)
                for hole in rings[1:]:
                    if len(hole) > 2:
                        dl.polygon(hole, fill=0)
            mwi = Image.fromarray(np.maximum(np.asarray(mwi), (np.asarray(layer) > 0) * (level + 1) * 40).astype(np.uint8))
        mwa = np.asarray(mwi, np.float64) / 200.0
        glow = np.array(style.get("milky", (0.16, 0.20, 0.34))) * night
        img += (mwa[..., None] * glow) * window[..., None]

    # constellation figures
    if night > 0:
        li = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(li)
        for ls in lines:
            pts = [S(dial.project(ra, de, lst)) for ra, de in ls]
            d.line(pts, fill=255, width=max(1, round(SS * style.get("line_w", 0.8))), joint="curve")
        la = np.asarray(li, np.float64)[..., None] / 255 * window[..., None]
        lc = np.array(style.get("line", (0.30, 0.38, 0.62)))
        mix = la * night * style.get("line_a", 0.85)
        img = img * (1 - mix) + lc * mix

    # the ecliptic: a fine dotted circle, where the Sun, Moon and planets ride
    ei = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(ei)
    for lam in range(0, 360, 4):
        ra, de = astro.ecl_to_eq(lam, 0, pos["eps"])
        x, y = S(dial.project(ra, de, lst))
        r = SS * 0.45
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    ea = np.asarray(ei, np.float64)[..., None] / 255 * window[..., None]
    ec = np.array(style.get("ecliptic", (0.75, 0.6, 0.25)))
    mix = ea * (0.35 + 0.35 * night)
    img = img * (1 - mix) + ec * mix

    # stars: size and strength by magnitude, tint by colour index; faint ones fade in daylight
    si = np.zeros((H, W, 3))
    sa = np.zeros((H, W))
    for ra, de, m, bv in stars:
        x, y = dial.project(ra, de, lst)
        if not (0 <= x < dial.w and 0 <= y < dial.h):
            continue
        vis = night if m > -1 else max(night, 0.0)
        if vis <= 0:
            continue
        r = max(0.42, 1.55 - 0.24 * m)                        # px: mag 0 ~1.5, mag 5 ~0.4
        a = max(0.25, min(1.0, 1.15 - 0.15 * m)) * vis
        lay = Image.new("L", (int(r * 2 * SS) + 4, int(r * 2 * SS) + 4), 0)
        ox, oy = x * SS - lay.width / 2, y * SS - lay.height / 2
        ImageDraw.Draw(lay).ellipse([lay.width / 2 - r * SS, lay.height / 2 - r * SS, lay.width / 2 + r * SS, lay.height / 2 + r * SS], fill=255)
        al = np.asarray(lay, np.float64) / 255 * a
        x0, y0 = int(ox), int(oy)
        x1, y1 = x0 + lay.width, y0 + lay.height
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            continue
        c = star_colour(bv)
        sub = sa[y0:y1, x0:x1]
        upd = al > sub
        sa[y0:y1, x0:x1] = np.where(upd, al, sub)
        si[y0:y1, x0:x1] = np.where(upd[..., None], c, si[y0:y1, x0:x1])
    sa *= window
    img = img * (1 - sa[..., None]) + si * sa[..., None]

    # the planets, the Moon with its phase, the Sun with a glow
    def disc(x, y, r, colour, alpha=1.0, mask=window):
        lay = Image.new("L", (W, H), 0)
        ImageDraw.Draw(lay).ellipse([x * SS - r * SS, y * SS - r * SS, x * SS + r * SS, y * SS + r * SS], fill=255)
        a = np.asarray(lay, np.float64)[..., None] / 255 * alpha * mask[..., None]
        return a, np.array(colour)
    planet_look = {"mercury": (0.75, (0.8, 0.75, 0.7)), "venus": (1.25, (1.0, 1.0, 0.85)), "mars": (1.0, (1.0, 0.45, 0.25)),
                   "jupiter": (1.15, (1.0, 0.92, 0.75)), "saturn": (1.0, (0.95, 0.82, 0.5))}
    for p, (r, c) in planet_look.items():
        x, y = dial.project(*pos[p], lst)
        a, col = disc(x, y, r, c, 0.6 + 0.4 * night)
        img = img * (1 - a) + col * a

    # the Moon: its lit part toward the Sun
    mx, my = dial.project(*pos["moon"], lst)
    sx, sy = dial.project(*pos["sun"], lst)
    rm = style.get("moon_r", 3.2)
    lay = np.zeros((H, W))
    yy, xx = (ys + 0.5) / SS - my, (xs + 0.5) / SS - mx
    inside = xx * xx + yy * yy <= rm * rm
    # direction toward the Sun along the sky (a short step along the great circle, projected)
    ra_m, de_m = pos["moon"]
    ra_s, de_s = pos["sun"]
    vm = np.array([math.cos(math.radians(de_m)) * math.cos(math.radians(ra_m)), math.cos(math.radians(de_m)) * math.sin(math.radians(ra_m)), math.sin(math.radians(de_m))])
    vs = np.array([math.cos(math.radians(de_s)) * math.cos(math.radians(ra_s)), math.cos(math.radians(de_s)) * math.sin(math.radians(ra_s)), math.sin(math.radians(de_s))])
    step = vm + 0.02 * (vs - vm)
    step /= np.linalg.norm(step)
    tx, ty = dial.project(math.degrees(math.atan2(step[1], step[0])) % 360, math.degrees(math.asin(step[2])), lst)
    ux, uy = tx - mx, ty - my
    n = math.hypot(ux, uy) or 1
    ux, uy = ux / n, uy / n
    # the terminator: an ellipse; lit where the point lies sunward of it
    k = 1 - 2 * pos["moon_phase"]                          # 1 new .. -1 full
    along = (xx * ux + yy * uy) / rm                          # toward the Sun
    across = (-xx * uy + yy * ux) / rm
    half = np.sqrt(np.clip(1 - across ** 2, 0, 1))
    lit = inside & (along > k * half)
    moon_lit = np.array((1.0, 0.98, 0.88))
    moon_dark = base * 0.6 + np.array((0.06, 0.06, 0.1))
    a_in = inside[..., None] * window[..., None]
    img = np.where(a_in & lit[..., None], moon_lit, np.where(a_in, moon_dark * 0.7 + img * 0.3, img))

    # the Sun: a warm disc with a dithered glow (by day, the brightest thing in the window)
    rs = style.get("sun_r", 3.4)
    dd = np.hypot((xs + 0.5) / SS - sx, (ys + 0.5) / SS - sy)
    glow = np.clip(1 - (dd - rs) / (rs * 3.2), 0, 1) ** 2 * 0.55
    sunc = np.array((1.0, 0.82, 0.25))
    g = (glow * window)[..., None]
    img = img * (1 - g) + np.array((1.0, 0.9, 0.55)) * g
    core = np.clip(rs + 0.5 - dd, 0, 1)[..., None] * window[..., None]
    img = img * (1 - core) + sunc * core

    # the window's rim: the jacket's cut edge, a fine warm line along the horizon
    rim = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(rim)
    pts = []
    for a in np.linspace(-180, 180, 361):
        de = math.degrees(math.atan(-math.cos(math.radians(lat / astro.D2R and a)) / math.tan(lat))) if lat else 0
        de = math.degrees(math.atan(-math.cos(math.radians(a)) / math.tan(lat)))
        r = (90 - de) * dial.k
        pts.append(S((dial.cx + r * math.sin(math.radians(a)), dial.cy + r * math.cos(math.radians(a)))))
    d.line(pts, fill=255, width=max(1, round(SS * 0.75)), joint="curve")
    ra_ = np.asarray(rim, np.float64)[..., None] / 255
    rc = np.array(style.get("rim", (0.55, 0.47, 0.32)))
    img = img * (1 - ra_) + rc * ra_

    # downsample to the screen
    img = img.reshape(dial.h, SS, dial.w, SS, 3).mean(axis=(1, 3))

    # the jacket: a 24-hour ring, set for civil time (the Sun points at the time now)
    # the Sun's angle on the dial (anticlockwise from the bottom) and the clock's minutes since midnight
    sun_ang = (lst - pos["sun"][0]) if not dial.south else -(lst - pos["sun"][0])
    local = when.astimezone(style.get("tz")) if style.get("tz") else when
    minutes = local.hour * 60 + local.minute + local.second / 60
    # angle of clock time T on the ring: the Sun's angle now, minus the time since then
    def ring_angle(m):
        return sun_ang + (m - minutes) * 0.25 * (-1 if dial.south else 1)
    R = dial.R
    jacket = Image.new("L", (dial.w * SS, dial.h * SS), 0)
    dj = ImageDraw.Draw(jacket)
    for q in range(96):                                       # quarter hours
        m = q * 15
        a = ring_angle(m)
        s, c = math.sin(math.radians(a)), math.cos(math.radians(a))
        if q % 4 == 0:
            r0, r1, w = R * 0.858, R * 0.900, 0.9
        elif q % 2 == 0:
            r0, r1, w = R * 0.858, R * 0.880, 0.7
        else:
            r0, r1, w = R * 0.858, R * 0.868, 0.6
        dj.line([S((dial.cx + r0 * s, dial.cy + r0 * c)), S((dial.cx + r1 * s, dial.cy + r1 * c))], fill=255, width=max(1, round(SS * w)))
    ja = np.asarray(jacket, np.float64).reshape(dial.h, SS, dial.w, SS).mean(axis=(1, 3))[..., None] / 255
    tick = np.array(style.get("tick", (0.62, 0.62, 0.62)))
    img = img * (1 - ja) + tick * ja
    cap = style.get("cap", 8)
    for hr in range(0, 24, style.get("every", 2)):
        a = ring_angle(hr * 60)
        rr = R * 0.948
        x, y = dial.cx + rr * math.sin(math.radians(a)), dial.cy + rr * math.cos(math.radians(a))
        paste_alpha(img, glyph_alpha(f"{hr:02d}" if style.get("pad") else str(hr), cap), x, y, style.get("numeral", (0.8, 0.8, 0.8)))
    # the Sun's pip: a small warm triangle on the ring, pointing in
    a = math.radians(sun_ang)
    s, c = math.sin(a), math.cos(a)
    pip = Image.new("L", (dial.w * SS, dial.h * SS), 0)
    tip, base_r, half = R * 0.862, R * 0.905, R * 0.022
    px, py = -c, s                                            # perpendicular
    poly = [S((dial.cx + tip * s, dial.cy + tip * c)),
            S((dial.cx + base_r * s + half * px, dial.cy + base_r * c + half * py)),
            S((dial.cx + base_r * s - half * px, dial.cy + base_r * c - half * py))]
    ImageDraw.Draw(pip).polygon(poly, fill=255)
    pa = np.asarray(pip, np.float64).reshape(dial.h, SS, dial.w, SS).mean(axis=(1, 3))[..., None] / 255
    img = img * (1 - pa) + sunc * pa
    # the cardinal points, just outside the window
    lat_r = lat
    for label, a in (("N", 180), ("E", -90), ("S", 0), ("W", 90)):
        de = math.degrees(math.atan(-math.cos(math.radians(a)) / math.tan(lat_r)))
        r = (90 - de) * dial.k + style.get("cardinal_out", 6.5)
        if label == "S":
            r = min(r, dial.r_disc + 4)
        x, y = dial.cx + r * math.sin(math.radians(a)), dial.cy + r * math.cos(math.radians(a))
        paste_alpha(img, glyph_alpha(label, style.get("cardinal_cap", 7)), x, y, style.get("cardinal", (0.55, 0.47, 0.32)))
    # round screens show the circle only
    if style.get("round"):
        yy, xx = np.mgrid[0:dial.h, 0:dial.w]
        img[np.hypot(xx + 0.5 - dial.cx, yy + 0.5 - dial.cy) > dial.w / 2] = 0
    return quantize(img), sun_alt


if __name__ == "__main__":
    from zoneinfo import ZoneInfo
    ny = ZoneInfo("America/New_York")
    sky = load_sky(5.0)
    dial = Dial(260, 260, 40.71, -74.01)
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    for label, t in (("night", datetime(2026, 10, 14, 21, 30, tzinfo=ny)), ("day", datetime(2026, 10, 14, 12, 15, tzinfo=ny)),
                     ("dusk", datetime(2026, 10, 14, 19, 0, tzinfo=ny))):
        im, alt = render(t.astimezone(timezone.utc), dial, sky, {"tz": ny, "round": True})
        Image.fromarray(im).save(out / f"round2-{label}.png")
        Image.fromarray(im).resize((780, 780), Image.NEAREST).save(out / f"round2-{label}-3x.png")
        print(label, "sun altitude", round(alt, 1))
