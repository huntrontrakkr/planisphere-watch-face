"""What else is happening in the sky: Jupiter's four great moons, the meteor showers' peaks, eclipses, and planets
meeting. Everything comes from the same ephemeris the faces draw from (astro.py), so nothing needs a table but
the showers', which are fixed to the Earth's place in its orbit.
"""
import math
from datetime import datetime, timedelta, timezone

import astro
from astro import sind, cosd, asind, rev

# ---- Jupiter's moons: Meeus, Astronomical Algorithms ch. 44, the lower-accuracy theory (a few hundredths of a
# Jupiter radius; the faces draw them magnified, far coarser) ------------------------------------------------------
GALILEAN = ("Io", "Europa", "Ganymede", "Callisto")


def galilean(t):
    """[(name, X, Y)] for the four moons: apparent offsets from Jupiter in Jupiter's equatorial radii, X positive
    toward the west, Y toward the north; and whether each is hidden behind Jupiter or in its shadow-free front."""
    d = astro.julian(t) - 2451545.0
    V = 172.74 + 0.00111588 * d
    M = 357.529 + 0.9856003 * d
    N = 20.020 + 0.0830853 * d + 0.329 * sind(V)
    J = 66.115 + 0.9025179 * d - 0.329 * sind(V)
    A = 1.915 * sind(M) + 0.020 * sind(2 * M)
    B = 5.555 * sind(N) + 0.168 * sind(2 * N)
    K = J + A - B
    R = 1.00014 - 0.01671 * cosd(M) - 0.00014 * cosd(2 * M)
    r = 5.20872 - 0.25208 * cosd(N) - 0.00611 * cosd(2 * N)
    delta = math.sqrt(r * r + R * R - 2 * r * R * cosd(K))
    psi = asind(R / delta * sind(K))
    lam = 34.35 + 0.083091 * d + 0.329 * sind(V) + B
    Ds = 3.12 * sind(lam + 42.8)
    De = Ds - 2.22 * sind(psi) * cosd(lam + 22) - 1.30 * (r - delta) / delta * sind(lam - 100.5)
    dd = d - delta / 173
    u1 = 163.8069 + 203.4058646 * dd + psi - B
    u2 = 358.4140 + 101.2916335 * dd + psi - B
    u3 = 5.7176 + 50.2345180 * dd + psi - B
    u4 = 224.8092 + 21.4879800 * dd + psi - B
    G = 331.18 + 50.310482 * dd
    H = 87.45 + 21.569231 * dd
    u1 += 0.473 * sind(2 * (u1 - u2))
    u2 += 1.065 * sind(2 * (u2 - u3))
    u3 += 0.165 * sind(G)
    u4 += 0.843 * sind(H)
    r1 = 5.9057 - 0.0244 * cosd(2 * (u1 - u2))
    r2 = 9.3966 - 0.0882 * cosd(2 * (u2 - u3))
    r3 = 14.9883 - 0.0216 * cosd(G)
    r4 = 26.3627 - 0.1939 * cosd(H)
    out = []
    for name, u, rr in zip(GALILEAN, (u1, u2, u3, u4), (r1, r2, r3, r4)):
        X, Y = rr * sind(u), -rr * cosd(u) * sind(De)
        behind = cosd(u) > 0 and abs(X) < 1.0           # beyond Jupiter (u near 0) and within its disc
        out.append((name, X, Y, behind))
    return out


# ---- the meteor showers: their peaks by the Sun's ecliptic longitude, and their radiants (IMO working list) -------
SHOWERS = [
    ("Quadrantids", 283.15, 230.0, 49.0),
    ("Lyrids", 32.32, 271.0, 34.0),
    ("Eta Aquariids", 45.5, 338.0, -1.0),
    ("Delta Aquariids", 127.0, 340.0, -16.0),
    ("Perseids", 140.0, 48.0, 58.0),
    ("Draconids", 195.4, 262.0, 54.0),
    ("Orionids", 208.0, 95.0, 16.0),
    ("Leonids", 235.27, 152.0, 22.0),
    ("Geminids", 262.2, 112.0, 33.0),
    ("Ursids", 270.7, 217.0, 76.0),
]


def shower_at(sun_lon, within=1.0):
    """The shower at or near its peak (the Sun within `within` degrees, about a day, of the peak's longitude)."""
    for name, peak, ra, dec in SHOWERS:
        if abs((sun_lon - peak + 180) % 360 - 180) <= within:
            return name, ra, dec
    return None


# ---- eclipses, from the Sun's and the Moon's places ---------------------------------------------------------------
SUN_RADIUS = 0.2666                                      # degrees at 1 AU (959.6 arcseconds)


def solar(t, lat, lon):
    """The Sun and the Moon seen from here: None if the Moon is not across the Sun (or the Sun is down), else
    {'kind': partial | annular | total, 'magnitude': fraction of the Sun's diameter covered, 'obscuration':
    fraction of its disc covered, 'offset': the Moon's centre from the Sun's in Sun radii (east, north),
    'ratio': the Moon's apparent radius over the Sun's}."""
    pos = astro.positions(t)
    lst = astro.sidereal(t, lon)
    if astro.altitude(*pos["sun"], lst, lat) < -0.8:
        return None
    dist = pos["moon_dist"]
    tm = astro.topocentric_moon(*pos["moon"], dist, lst, lat)
    # the Moon's apparent size from here: nearer by about an Earth radius times the sine of its height
    near = dist - math.sin(math.radians(max(0.0, astro.altitude(*tm, lst, lat))))
    rm = math.degrees(math.asin(0.2725076 / near))
    rs = SUN_RADIUS / pos["sun_dist"]
    sep = astro.separation(tm, pos["sun"])
    if sep >= rs + rm:
        return None
    if sep <= rm - rs:
        kind, cover = "total", 1.0
    elif sep <= rs - rm:
        kind, cover = "annular", (rm / rs) ** 2
    else:                                                # two circles overlapping: the lens's area
        d, r1, r2 = sep, rs, rm
        a1 = r1 * r1 * math.acos(max(-1, min(1, (d * d + r1 * r1 - r2 * r2) / (2 * d * r1))))
        a2 = r2 * r2 * math.acos(max(-1, min(1, (d * d + r2 * r2 - r1 * r1) / (2 * d * r2))))
        a3 = 0.5 * math.sqrt(max(0.0, (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)))
        kind, cover = "partial", (a1 + a2 - a3) / (math.pi * r1 * r1)
    east = (tm[0] - pos["sun"][0] + 180) % 360 - 180
    off = (east * math.cos(math.radians(pos["sun"][1])) / rs, (tm[1] - pos["sun"][1]) / rs)
    return {"kind": kind, "magnitude": (rs + rm - sep) / (2 * rs), "obscuration": min(1.0, cover), "offset": off,
            "ratio": rm / rs}


def lunar(t, lat, lon):
    """The Moon in the Earth's shadow, if it is up: None, or {'kind': partial | total, 'magnitude': how far into
    the umbra it reaches, in Moon diameters, 'toward': the shadow's centre from the Moon's, as (east, north)}."""
    pos = astro.positions(t)
    lst = astro.sidereal(t, lon)
    if astro.altitude(*pos["moon"], lst, lat) < 0:
        return None
    dist = pos["moon_dist"]
    rm = math.degrees(math.asin(0.2725076 / dist))
    anti = (astro.rev(pos["sun"][0] + 180), -pos["sun"][1])
    sep = astro.separation(pos["moon"], anti)
    umbra = 1.02 * (0.998340 * math.degrees(math.asin(1 / dist)) + 0.00244 - SUN_RADIUS / pos["sun_dist"])
    if sep >= umbra + rm:
        return None
    east = (anti[0] - pos["moon"][0] + 180) % 360 - 180
    toward = (east * math.cos(math.radians(pos["moon"][1])), anti[1] - pos["moon"][1])
    return {"kind": "total" if sep <= umbra - rm else "partial", "magnitude": (umbra + rm - sep) / (2 * rm),
            "toward": toward}


def eclipse_at(t, lat, lon):
    """('sun' | 'moon', details) for an eclipse under way here, else None."""
    m = lunar(t, lat, lon)
    if m:
        return "moon", m
    s_ = solar(t, lat, lon)
    if s_:
        return "sun", s_
    return None


# ---- planets meeting -----------------------------------------------------------------------------------------------
PLANETS = ("mercury", "venus", "mars", "jupiter", "saturn")


def pairings(pos, lst, lat, close=2.0, moon_close=1.6):
    """Bright bodies close together and both above the horizon: [(a, b, separation)], nearest first."""
    out = []
    bodies = ("moon",) + PLANETS
    for i, a in enumerate(bodies):
        for b in bodies[i + 1:]:
            lim = moon_close if a == "moon" else close
            sep = astro.separation(pos[a], pos[b])
            if sep < lim and astro.altitude(*pos[a], lst, lat) > 3 and astro.altitude(*pos[b], lst, lat) > 3:
                out.append((a, b, sep))
    return sorted(out, key=lambda p: p[2])


# ---- the day's news, for the line above the window ---------------------------------------------------------------
_CACHE = {}


def news(t, tz, lat, lon):
    """The sky's news today (the night that belongs to this day: from noon to the next noon), as wordings from the
    longest to the shortest, or None: an eclipse first, then planets meeting, then a meteor shower's peak, then
    the Moon by a planet."""
    local = t.astimezone(tz)
    start = local.replace(hour=12, minute=0, second=0, microsecond=0)
    if local.hour < 12:
        start -= timedelta(days=1)
    key = (start.date(), round(lat, 2), round(lon, 2))
    if key in _CACHE:
        return _CACHE[key]
    found = {}
    for k in range(0, 24 * 6):                           # every ten minutes through the day and its night
        u = (start + timedelta(minutes=10 * k)).astimezone(timezone.utc)
        e = eclipse_at(u, lat, lon)
        if e:
            kind = e[1]["kind"]
            prev = found.get("eclipse")
            rank = {"partial": 0, "annular": 1, "total": 2}
            if prev is None or rank[kind] > rank[prev[1]]:
                found["eclipse"] = (e[0], kind)
        if k % 6 == 0:                                   # hourly: planets meeting in a dark sky
            pos = astro.positions(u)
            lst = astro.sidereal(u, lon)
            if astro.altitude(*pos["sun"], lst, lat) < -6:
                for a, b, sep in pairings(pos, lst, lat):
                    found.setdefault("moon" if a == "moon" else "planets", (a, b))
    midnight = (start + timedelta(hours=12)).astimezone(timezone.utc)
    sh = shower_at(astro.positions(midnight)["sun_lon"])
    line = None                                          # the news, longest wording first, then shorter ones
    if "eclipse" in found:
        body, kind = found["eclipse"]
        if body == "sun":
            line = {"total": ("TOTAL ECLIPSE OF THE SUN", "TOTAL ECLIPSE"), "annular": ("ANNULAR ECLIPSE", "RING OF FIRE"),
                    "partial": ("ECLIPSE OF THE SUN", "SUN ECLIPSED")}[kind]
        else:
            line = ("TOTAL ECLIPSE OF THE MOON", "BLOOD MOON") if kind == "total" else \
                ("ECLIPSE OF THE MOON", "MOON ECLIPSED")
    elif "planets" in found:
        a, b = (n.upper() for n in found["planets"])
        line = (f"{a} MEETS {b}", f"{a} & {b}")
    elif sh:
        line = (f"{sh[0].upper()} PEAK", sh[0].upper())
    elif "moon" in found:
        b = found["moon"][1].upper()
        line = (f"THE MOON BY {b}", f"MOON BY {b}")
    _CACHE[key] = line
    return line


if __name__ == "__main__":
    from zoneinfo import ZoneInfo
    NY = ZoneInfo("America/New_York")
    lat, lon = 40.71, -74.01
    # known events, to check the eclipses against
    from datetime import timedelta
    def scan(t0, minutes, lat_, lon_):
        seen = {}
        for k in range(minutes):
            u = t0 + timedelta(minutes=k)
            e = eclipse_at(u, lat_, lon_)
            if e:
                kind = e[1]["kind"]
                seen.setdefault(kind, [u, u])[1] = u
        return {k: (v[0].strftime("%H:%M"), v[1].strftime("%H:%M")) for k, v in seen.items()}
    utc = timezone.utc
    print("Dallas 2024-04-08 (total 18:41-18:44 UTC):", scan(datetime(2024, 4, 8, 17, 20, tzinfo=utc), 150, 32.7767, -96.797))
    print("New York 2024-04-08 (partial, 0.90 at 19:25 UTC):", scan(datetime(2024, 4, 8, 18, 0, tzinfo=utc), 150, lat, lon))
    print("Burgos 2026-08-12 (total about 18:28 UTC, Sun low):", scan(datetime(2026, 8, 12, 17, 20, tzinfo=utc), 100, 42.34, -3.70))
    print("New York 2025-03-14 lunar (total 06:26-07:31 UTC):", scan(datetime(2025, 3, 14, 4, 0, tzinfo=utc), 240, lat, lon))
    t = datetime(2026, 10, 14, 21, 30, tzinfo=NY).astimezone(timezone.utc)
    for name, X, Y, behind in galilean(t):
        print(f"  {name:9s} X {X:+6.2f}  Y {Y:+5.2f}{'  behind' if behind else ''}")
    print("Orionids peak night:", news(datetime(2026, 10, 21, 22, 0, tzinfo=NY).astimezone(timezone.utc), NY, lat, lon))
    print("tonight:", news(t, NY, lat, lon))
