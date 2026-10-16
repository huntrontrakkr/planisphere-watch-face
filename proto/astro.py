"""Where things are in the sky, to the precision a 260-pixel dial needs
(well under a pixel): the stars from the catalogue (J2000; precession over
these decades moves them a third of a pixel); the planets from Paul
Schlyter's orbital elements ("How to compute planetary positions") with
the largest perturbations; the Sun and the Moon from Meeus (lunar.py),
closely enough to find where an eclipse is total. Angles in degrees."""
import math
from datetime import datetime, timezone

import lunar

D2R = math.pi / 180


def sind(a): return math.sin(a * D2R)
def cosd(a): return math.cos(a * D2R)
def atan2d(y, x): return math.atan2(y, x) / D2R
def asind(x): return math.asin(max(-1.0, min(1.0, x))) / D2R
def rev(a): return a % 360.0


def julian(t: datetime) -> float:
    return t.timestamp() / 86400.0 + 2440587.5


def sidereal(t: datetime, lon: float) -> float:
    """Local sidereal time (degrees) at east longitude `lon`."""
    d = julian(t) - 2451545.0
    T = d / 36525
    return rev(280.46061837 + 360.98564736629 * d + 0.000387933 * T * T - T ** 3 / 38710000 + lon)


def ecl_to_eq(lon, lat, eps):
    """Ecliptic (lon, lat) to equatorial (ra, dec), all degrees."""
    x = cosd(lon) * cosd(lat)
    y = sind(lon) * cosd(lat) * cosd(eps) - sind(lat) * sind(eps)
    z = sind(lon) * cosd(lat) * sind(eps) + sind(lat) * cosd(eps)
    return rev(atan2d(y, x)), asind(z)


# Schlyter's elements: N, i, w, a, e, M as (value, rate per day) from 2000 Jan 0.0 UT
ELEMENTS = {
    "sun":     ((0, 0), (0, 0), (282.9404, 4.70935e-5), (1.0, 0), (0.016709, -1.151e-9), (356.0470, 0.9856002585)),
    "moon":    ((125.1228, -0.0529538083), (5.1454, 0), (318.0634, 0.1643573223), (60.2666, 0), (0.054900, 0),
                (115.3654, 13.0649929509)),
    "mercury": ((48.3313, 3.24587e-5), (7.0047, 5.00e-8), (29.1241, 1.01444e-5), (0.387098, 0), (0.205635, 5.59e-10),
                (168.6562, 4.0923344368)),
    "venus":   ((76.6799, 2.46590e-5), (3.3946, 2.75e-8), (54.8910, 1.38374e-5), (0.723330, 0), (0.006773, -1.302e-9),
                (48.0052, 1.6021302244)),
    "mars":    ((49.5574, 2.11081e-5), (1.8497, -1.78e-8), (286.5016, 2.92961e-5), (1.523688, 0), (0.093405, 2.516e-9),
                (18.6021, 0.5240207766)),
    "jupiter": ((100.4542, 2.76854e-5), (1.3030, -1.557e-7), (273.8777, 1.64505e-5), (5.20256, 0), (0.048498, 4.469e-9),
                (19.8950, 0.0830853001)),
    "saturn":  ((113.6634, 2.38980e-5), (2.4886, -1.081e-7), (339.3939, 2.97661e-5), (9.55475, 0), (0.055546, -9.499e-9),
                (316.9670, 0.0334442282)),
}


def elements(body, d):
    return [v + r * d for v, r in ELEMENTS[body]]


def kepler(M, e):
    E = M + e / D2R * sind(M) * (1 + e * cosd(M))
    for _ in range(8):
        E = E - (E - e / D2R * sind(E) - M) / (1 - e * cosd(E))
    return E


def orbit(body, d):
    """Position in the body's frame: ecliptic x, y, z (heliocentric; geocentric for the Moon), and the elements."""
    N, i, w, a, e, M = elements(body, d)
    E = kepler(rev(M), e)
    xv, yv = a * (cosd(E) - e), a * math.sqrt(1 - e * e) * sind(E)
    v, r = atan2d(yv, xv), math.hypot(xv, yv)
    x = r * (cosd(N) * cosd(v + w) - sind(N) * sind(v + w) * cosd(i))
    y = r * (sind(N) * cosd(v + w) + cosd(N) * sind(v + w) * cosd(i))
    z = r * sind(v + w) * sind(i)
    return x, y, z, (N, i, w, a, e, M)


def positions(t: datetime):
    """{body: (ra, dec)} for the Sun, Moon and the five bright planets; also the Moon's phase:
    ('moon_phase': illuminated fraction 0..1, 'moon_waxing': bool), its distance ('moon_dist', Earth radii) and the
    Sun's ecliptic longitude."""
    d = julian(t) - 2451543.5
    out = {}
    # the Sun and the Moon to the precision eclipses need (lunar.py: Meeus), in dynamical time, apparent places
    jde = julian(t) + lunar.delta_t(t.year) / 86400
    dpsi, eps = lunar.nutation(jde)
    lam_s, R = lunar.sun(jde)
    lam_s = rev(lam_s + dpsi)
    lam_m, beta_m, dist_km = lunar.moon(jde)
    lam_m = rev(lam_m + dpsi)
    out["sun"] = ecl_to_eq(lam_s, 0.0, eps)
    out["sun_lon"] = lam_s
    out["sun_dist"] = R
    out["moon"] = ecl_to_eq(lam_m, beta_m, eps)
    out["moon_dist"] = dist_km / 6378.14                     # Earth radii
    elong = math.acos(max(-1, min(1, cosd(lam_m - lam_s) * cosd(beta_m)))) / D2R
    out["moon_phase"] = (1 - cosd(elong)) / 2
    out["moon_waxing"] = rev(lam_m - lam_s) < 180
    # Schlyter's Sun, to carry the planets from the Sun's frame to ours
    _, _, ws, _, es, Ms = elements("sun", d)
    E = kepler(rev(Ms), es)
    xv, yv = cosd(E) - es, math.sqrt(1 - es * es) * sind(E)
    v, rs = atan2d(yv, xv), math.hypot(xv, yv)
    lon_sun = rev(v + ws)
    xs, ys = rs * cosd(lon_sun), rs * sind(lon_sun)
    # the planets (geocentric), Jupiter and Saturn with their great inequality
    Mj, Msat = elements("jupiter", d)[5], elements("saturn", d)[5]
    for p in ("mercury", "venus", "mars", "jupiter", "saturn"):
        x, y, z, _ = orbit(p, d)
        lon, lat, r = atan2d(y, x), atan2d(z, math.hypot(x, y)), math.sqrt(x * x + y * y + z * z)
        if p == "jupiter":
            lon += (-0.332 * sind(2 * Mj - 5 * Msat - 67.6) - 0.056 * sind(2 * Mj - 2 * Msat + 21) + 0.042 * sind(3 * Mj - 5 * Msat + 21)
                    - 0.036 * sind(Mj - 2 * Msat) + 0.022 * cosd(Mj - Msat) + 0.023 * sind(2 * Mj - 3 * Msat + 52)
                    - 0.016 * sind(Mj - 5 * Msat - 69))
        if p == "saturn":
            lon += (0.812 * sind(2 * Mj - 5 * Msat - 67.6) - 0.229 * cosd(2 * Mj - 4 * Msat - 2) + 0.119 * sind(Mj - 2 * Msat - 3)
                    + 0.046 * sind(2 * Mj - 6 * Msat - 69) + 0.014 * sind(Mj - 3 * Msat + 32))
            lat += -0.020 * cosd(2 * Mj - 4 * Msat - 2) + 0.018 * sind(2 * Mj - 6 * Msat - 49)
        x, y, z = r * cosd(lon) * cosd(lat), r * sind(lon) * cosd(lat), r * sind(lat)
        xg, yg, zg = x + xs, y + ys, z
        out[p] = ecl_to_eq(rev(atan2d(yg, xg)), atan2d(zg, math.hypot(xg, yg)), eps)
        out[p + "_far"] = r * math.sqrt(xg * xg + yg * yg + zg * zg)     # (its light: plan.h Sky pl_far)
    out["eps"] = eps
    return out


def topocentric_moon(ra, dec, dist, lst, lat):
    """The Moon as seen from the ground rather than from the Earth's centre (its parallax is up to a degree)."""
    mpar = asind(1 / dist)
    gclat = lat - 0.1924 * sind(2 * lat)
    rho = 0.99833 + 0.00167 * cosd(2 * lat)
    ha = lst - ra
    g = atan2d(math.tan(gclat * D2R), cosd(ha)) if abs(cosd(ha)) > 1e-9 else 90.0
    tra = ra - mpar * rho * cosd(gclat) * sind(ha) / cosd(dec)
    tdec = dec - mpar * rho * sind(gclat) * sind(g - dec) / sind(g) if abs(sind(g)) > 1e-9 else dec
    return tra, tdec


def separation(a, b):
    """Angle between two (ra, dec) points, degrees."""
    return math.acos(max(-1.0, min(1.0, sind(a[1]) * sind(b[1]) + cosd(a[1]) * cosd(b[1]) * cosd(a[0] - b[0])))) / D2R


def altitude(ra, dec, lst, lat):
    h = lst - ra
    return asind(sind(lat) * sind(dec) + cosd(lat) * cosd(dec) * cosd(h))


if __name__ == "__main__":
    t = datetime(2026, 10, 14, 16, 0, tzinfo=timezone.utc)
    p = positions(t)
    for k in ("sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"):
        print(f"{k:8s} RA {p[k][0] / 15:6.3f} h  Dec {p[k][1]:+7.2f}")
    print("moon phase", round(p["moon_phase"], 3), "waxing" if p["moon_waxing"] else "waning")
    print("LST NYC", sidereal(t, -74.006) / 15)
