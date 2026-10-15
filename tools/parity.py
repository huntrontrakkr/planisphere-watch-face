"""The watch's C (build/host) against the prototype (proto/plates.py), pixel for pixel: for each case, the two faces
and where they differ, side by side in out/parity/, and the count of differing pixels.

    tools/build-host.sh && uv run python tools/parity.py [names...]
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import plates                      # noqa: E402
import weather as meteo           # noqa: E402
from render import load_sky        # noqa: E402

OUT = ROOT / "out" / "parity"
NY = (40.71, -74.01, -240)         # New York in October: four hours behind
PLATE_ID = {n: i for i, n in enumerate(plates.PLATES)}

# name: (screen, plate, UTC moment, (lat, lon, offset minutes), options)
CASES = {
    "night-t2": ("emery", "planisphere", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "night-r2": ("gabbro", "planisphere", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "noon-t2": ("emery", "planisphere", datetime(2026, 10, 14, 16, 15, tzinfo=timezone.utc), NY, {}),
    "dusk-t2": ("emery", "planisphere", datetime(2026, 10, 14, 22, 40, tzinfo=timezone.utc), NY, {}),
    "burritt-t2": ("emery", "burritt", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "flamsteed-r2": ("gabbro", "flamsteed", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "observatory-t2": ("emery", "observatory", datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc), NY, {}),
    "astrolabe-t2": ("emery", "astrolabe", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "hours-t2": ("emery", "hours", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "orloj-t2": ("emery", "orloj", datetime(2026, 10, 14, 22, 40, tzinfo=timezone.utc), NY, {}),
    "cyanotype-t2": ("emery", "cyanotype", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "apian-t2": ("emery", "apian", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {}),
    "night24-t2": ("emery", "night", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {"clock24": True}),
    "sydney-t2": ("emery", "planisphere", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660), {}),
    "sydney-dusk-r2": ("gabbro", "planisphere", datetime(2026, 10, 15, 8, 20, tzinfo=timezone.utc), (-33.87, 151.21, 660), {}),
    "sydney-astro-t2": ("emery", "astrolabe", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660), {}),
    "sydney-apian-t2": ("emery", "apian", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660), {}),
    "rain-t2": ("emery", "planisphere", datetime(2026, 10, 14, 19, 10, tzinfo=timezone.utc), NY, {"weather": "rain"}),
    "snow-r2": ("gabbro", "planisphere", datetime(2026, 10, 14, 15, 10, tzinfo=timezone.utc), NY, {"weather": "snow"}),
    "fog-t2": ("emery", "planisphere", datetime(2026, 10, 14, 14, 30, tzinfo=timezone.utc), NY, {"weather": "fog"}),
    "thunder-t2": ("emery", "night", datetime(2026, 10, 15, 0, 40, tzinfo=timezone.utc), NY, {"weather": "thunder"}),
    "cirrus-night-t2": ("emery", "planisphere", datetime(2026, 10, 15, 2, 30, tzinfo=timezone.utc), NY, {"weather": "cirrus"}),
    "fair-dusk-r2": ("gabbro", "planisphere", datetime(2026, 10, 14, 22, 40, tzinfo=timezone.utc), NY, {"weather": "fair"}),
    "overcast-obs-t2": ("emery", "observatory", datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc), NY, {"weather": "overcast"}),
    "gale-t2": ("emery", "planisphere", datetime(2026, 10, 14, 17, 0, tzinfo=timezone.utc), NY, {"weather": "gale"}),
    "frost-apian-t2": ("emery", "apian", datetime(2026, 10, 15, 11, 0, tzinfo=timezone.utc), NY, {"weather": "frost"}),
    "weather-t2": ("emery", "planisphere", datetime(2026, 10, 14, 20, 10, tzinfo=timezone.utc), NY, {"weather": "cloudy"}),
}


def c_render(screen, plate, when, place, opts, path):
    lat, lon, off = place
    args = [str(ROOT / "build" / "host"), screen, str(PLATE_ID[plate]), str(int(when.timestamp())), str(lat), str(lon),
            str(off), str(path)]
    if opts.get("clock24"):
        args.append("--24")
    city, country = plates.place_name(lat, lon)
    if city:
        args += ["--city", city, "--country", country]
    w = opts.get("weather")
    if w:
        s = meteo.SAMPLES[w]
        args += ["--weather", ",".join(str(int(round(v))) for v in (
            s.temp * 10, s.code, s.low * 100, s.mid * 100, s.high * 100, s.wind, s.wind_from, s.pressure,
            s.snow_depth * 1000, s.visibility / 10))]
    subprocess.run(args, check=True)
    return np.asarray(Image.open(path).convert("RGB"))


def py_render(screen, plate, when, place, opts, sky):
    lat, lon, off = place
    dial = plates.RectDial(200, 228, lat, lon) if screen == "emery" else plates.RoundDial(260, 260, lat, lon)
    tz = timezone(timedelta(minutes=off))
    w = meteo.SAMPLES[opts["weather"]] if opts.get("weather") else None
    return plates.render(when, dial, sky, tz, plate, round_screen=screen == "gabbro", clock24=opts.get("clock24", False),
                         weather=w).astype(np.uint8)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sky = load_sky(4.6)
    names = sys.argv[1:] or list(CASES)
    for name in names:
        screen, plate, when, place, opts = CASES[name]
        a = py_render(screen, plate, when, place, opts, sky)
        b = c_render(screen, plate, when, place, opts, OUT / f"{name}-c.ppm")
        diff = (a != b).any(axis=2)
        d = np.zeros_like(a)
        d[diff] = (255, 0, 255)
        d[~diff] = a[~diff] // 3
        S = np.concatenate([a, np.full((a.shape[0], 4, 3), 40, np.uint8), b, np.full((a.shape[0], 4, 3), 40, np.uint8), d], axis=1)
        Image.fromarray(S).resize((S.shape[1] * 2, S.shape[0] * 2), Image.NEAREST).save(OUT / f"{name}.png")
        print(f"{name:16s} {int(diff.sum()):6d} pixels differ ({100 * diff.mean():.2f}%)", flush=True)


if __name__ == "__main__":
    main()
