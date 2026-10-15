"""The real skyline: the hills and mountains round a place, standing where they stand above its horizon.

For each bearing across the window's lower edge (southeast through south to southwest), the ground is
sampled along the ray from 5 to 140 km (Open-Meteo's elevation service, the Copernicus 90 m terrain, no key needed); the
skyline's height there is the steepest angle up to any of it, with the Earth's curve taken off and the air's
refraction (it bends the light round the curve a little) put back. On the watch the phone would work this out
once for each new place and keep it. Kept here in data/horizons/.

    uv run python proto/horizon.py          # the skylines of a few places
"""
import json
import math
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "horizons"
R_EARTH = 6371000.0
REFRACTION = 0.13                       # the light's path curves with about a seventh of the Earth's curvature
EYE = 2.0                               # metres above the ground
AZIMUTHS = list(range(126, 235, 2))     # bearings east of north across the window's lower edge, SE to SW
DISTANCES = [5000, 6500, 8000, 10500, 13500, 17000, 21000, 26000, 32000, 40000, 50000, 65000, 85000, 110000, 140000]
# from 5 km out only: the terrain model is of the surface, buildings and woods included, and the skyline wanted is
# the distant hills and mountains, not the street's


def destination(lat, lon, az, d):
    """The point `d` metres from (lat, lon) along bearing `az` (great circle)."""
    p1, l1, a, s = math.radians(lat), math.radians(lon), math.radians(az), d / R_EARTH
    p2 = math.asin(math.sin(p1) * math.cos(s) + math.cos(p1) * math.sin(s) * math.cos(a))
    l2 = l1 + math.atan2(math.sin(a) * math.sin(s) * math.cos(p1), math.cos(s) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), (math.degrees(l2) + 540) % 360 - 180


def elevations(points, batch=100, timeout=20, pace=11.0):
    """Ground heights (metres) at [(lat, lon)], from Open-Meteo, a hundred at a time, paced to stay inside its
    free allowance (it counts every point), waiting a minute and trying again when it asks to slow down."""
    import time
    import urllib.error
    out = []
    for i in range(0, len(points), batch):
        chunk = points[i: i + batch]
        lats = ",".join(f"{p[0]:.4f}" for p in chunk)
        lons = ",".join(f"{p[1]:.4f}" for p in chunk)
        url = f"https://api.open-meteo.com/v1/elevation?latitude={lats}&longitude={lons}"
        for attempt in range(6):
            try:
                with urllib.request.urlopen(url, timeout=timeout) as r:
                    out += json.load(r)["elevation"]
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 5:
                    raise
                time.sleep(65)
        time.sleep(pace)
    return out


def skyline(lat, lon, refresh=False):
    """{bearing: (the skyline's height there in degrees above the horizon, 0 where the land falls away; the height
    in metres of the ground that makes it)}. The bearings are the chart's: round the south for a northern place;
    a southern place's planisphere has the north at the bottom, so its rays go out half a turn round."""
    path = CACHE / f"{lat:.3f}_{lon:.3f}.json"
    if path.exists() and not refresh:
        return {int(k): tuple(v) for k, v in json.loads(path.read_text()).items()}
    ring = [(lat, lon)] + [destination(lat, lon, az, 250) for az in (0, 90, 180, 270)]
    turn = 180 if lat < 0 else 0
    pts = ring + [destination(lat, lon, (az + turn) % 360, d) for az in AZIMUTHS for d in DISTANCES]
    h = elevations(pts)
    h0 = min(h[:5]) + EYE                               # the ground here: the lowest nearby, not a rooftop
    out, k = {}, 5
    for az in AZIMUTHS:
        best, top = 0.0, h0
        for d in DISTANCES:
            drop = d * d / (2 * R_EARTH) * (1 - REFRACTION)
            a = math.degrees(math.atan2(h[k] - h0 - drop, d))
            if a > best:
                best, top = a, h[k]
            k += 1
        out[az] = (round(best, 3), round(top))
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out))
    return out


def cached(lat, lon):
    """The place's skyline if it has been worked out (the faces never fetch it while drawing), else None."""
    path = CACHE / f"{lat:.3f}_{lon:.3f}.json"
    if not path.exists():
        return None
    return {int(k): tuple(v) for k, v in json.loads(path.read_text()).items()}


def snowline(lat, season):
    """Roughly where the snow lies down to, in metres: near 5,000 at the equator, lower toward the poles, lower in
    winter and higher in summer."""
    mean = 5000 - 4500 * abs(math.sin(math.radians(lat))) ** 1.5
    return mean + {"bare": -900, "blossom": -300, "leaf": 500, "harvest": 700, "turning": 200, "autumn": -400}.get(season, 0)


def at(sky, az, field=0):
    """The skyline's height (or with field=1 its ground's height in metres) at bearing `az`, between the bearings
    worked out."""
    keys = sorted(sky)
    if az <= keys[0]:
        return sky[keys[0]][field]
    if az >= keys[-1]:
        return sky[keys[-1]][field]
    for a, b in zip(keys, keys[1:]):
        if a <= az <= b:
            return sky[a][field] + (sky[b][field] - sky[a][field]) * (az - a) / (b - a)
    return 0.0


if __name__ == "__main__":
    for name, lat, lon in (("Chamonix", 45.9237, 6.8694), ("Salt Lake City", 40.7608, -111.8910),
                           ("Denver", 39.7392, -104.9903), ("Innsbruck", 47.2692, 11.4041)):
        s = skyline(lat, lon)
        top = max(s, key=lambda a: s[a][0])
        print(f"{name:15s} highest {s[top][0]:5.2f} deg ({s[top][1]} m) at {top:3d}; south {at(s, 180):5.2f}; "
              + " ".join(f"{at(s, a):.1f}" for a in range(130, 231, 10)), flush=True)
