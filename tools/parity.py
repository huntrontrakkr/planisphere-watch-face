"""The watch's C (build/host) against the prototype (proto/plates.py), pixel for pixel: for each case, the two faces
and where they differ, side by side in out/parity/, and the count of differing pixels, against the count last accepted
(tools/parity-baseline.json). A case with more than before fails the run: the two are deterministic, so any rise is a
change to look at (a small slip hides easily among a few hundred pixels). --accept takes the counts as the baseline;
--slack N lets a case rise by N pixels before it fails (CI, where another machine's arithmetic may land a pixel apart).

    tools/build-host.sh && uv run python tools/parity.py [names...] [--accept] [--slack N]
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import feast_draw                  # noqa: E402
import plates                      # noqa: E402
import weather as meteo           # noqa: E402
from render import load_sky        # noqa: E402

OUT = ROOT / "out" / "parity"
BASELINE = ROOT / "tools" / "parity-baseline.json"
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
    "dallas-total-t2": ("emery", "planisphere", datetime(2024, 4, 8, 18, 42, tzinfo=timezone.utc), (32.7767, -96.797, -300), {}),
    "dallas-diamond-r2": ("gabbro", "planisphere", datetime(2024, 4, 8, 18, 40, tzinfo=timezone.utc), (32.7767, -96.797, -300), {}),
    "ny-partial-t2": ("emery", "planisphere", datetime(2024, 4, 8, 19, 25, tzinfo=timezone.utc), NY, {}),
    "burgos-total-t2": ("emery", "observatory", datetime(2026, 8, 12, 18, 29, 30, tzinfo=timezone.utc), (42.3439, -3.6969, 120), {}),
    "annular-t2": ("emery", "planisphere", datetime(2023, 10, 14, 16, 35, tzinfo=timezone.utc), (35.0844, -106.6504, -360), {}),
    "lunar-total-t2": ("emery", "planisphere", datetime(2025, 3, 14, 6, 50, tzinfo=timezone.utc), NY, {}),
    "lunar-partial-r2": ("gabbro", "night", datetime(2025, 3, 14, 5, 40, tzinfo=timezone.utc), NY, {}),
    "orionids-t2": ("emery", "planisphere", datetime(2026, 10, 22, 6, 0, tzinfo=timezone.utc), NY, {}),
    "conjunction-t2": ("emery", "planisphere", datetime(2023, 3, 2, 0, 20, tzinfo=timezone.utc), NY, {}),
    "weather-t2": ("emery", "planisphere", datetime(2026, 10, 14, 20, 10, tzinfo=timezone.utc), NY, {"weather": "cloudy"}),
    # the labours of the months: each kind of field, the figures drawn more than once, the south, the Round 2
    "labours-jan-t2": ("emery", "planisphere", datetime(2026, 1, 16, 2, 30, tzinfo=timezone.utc), NY, {"labours": True}),
    "labours-mar-r2": ("gabbro", "burritt", datetime(2026, 3, 16, 1, 30, tzinfo=timezone.utc), NY, {"labours": True}),
    "labours-jul-t2": ("emery", "hours", datetime(2026, 7, 16, 1, 30, tzinfo=timezone.utc), NY, {"labours": True}),
    "labours-oct-t2": ("emery", "planisphere", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {"labours": True}),
    "labours-nov-r2": ("gabbro", "apian", datetime(2026, 11, 16, 2, 30, tzinfo=timezone.utc), NY, {"labours": True}),
    "labours-sydney-t2": ("emery", "flamsteed", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660),
                          {"labours": True}),
    # the zodiac: the Sun's sign's woodcut behind the face, the glyphs in the Time 2's corners
    "zodiac-jul-t2": ("emery", "planisphere", datetime(2026, 7, 13, 15, 33, tzinfo=timezone.utc), NY, {"theme": 2, "tools": True}),
    "zodiac-oct-r2": ("gabbro", "hours", datetime(2026, 10, 15, 1, 30, tzinfo=timezone.utc), NY, {"theme": 2}),
    "zodiac-apr-paper-t2": ("emery", "flamsteed", datetime(2026, 4, 12, 23, 20, tzinfo=timezone.utc), NY,
                            {"theme": 2, "tools": True}),
    # the astronomer: the month's instrument of Tycho's behind the face (the south: the same month)
    "astronomer-jan-t2": ("emery", "planisphere", datetime(2026, 1, 20, 2, 30, tzinfo=timezone.utc), NY, {"theme": 3}),
    "astronomer-aug-r2": ("gabbro", "hours", datetime(2026, 8, 16, 1, 30, tzinfo=timezone.utc), NY, {"theme": 3}),
    "astronomer-sydney-r2": ("gabbro", "apian", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660),
                             {"theme": 3}),
    "astronomer-may-paper-t2": ("emery", "flamsteed", datetime(2026, 5, 12, 23, 20, tzinfo=timezone.utc), NY,
                                {"theme": 3, "tools": True}),
    # the astronomer's corners: the brightest planets up in roundels, the new star where none is
    "astronomer-planets-t2": ("emery", "hours", datetime(2026, 11, 16, 2, 30, tzinfo=timezone.utc), NY,
                              {"theme": 3, "tools": True}),
    "astronomer-dawn-t2": ("emery", "planisphere", datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc), NY,
                           {"theme": 3, "tools": True}),
    # near the equator: the Time 2's window cut by its ring, the place's names beside the fleur-de-lis
    "quito-t2": ("emery", "planisphere", datetime(2026, 10, 15, 3, 0, tzinfo=timezone.utc), (-0.1807, -78.4678, -300), {}),
    "quito-hours-t2": ("emery", "hours", datetime(2026, 10, 14, 22, 0, tzinfo=timezone.utc), (-0.1807, -78.4678, -300),
                       {"labours": True}),
    # the Labours' tools in the Time 2's corners: in colour, on a printed plate (their outlines in its ink), the south
    "tools-jun-t2": ("emery", "planisphere", datetime(2026, 6, 16, 3, 30, tzinfo=timezone.utc), NY, {"tools": True}),
    "tools-feb-paper-t2": ("emery", "burritt", datetime(2026, 2, 16, 2, 30, tzinfo=timezone.utc), NY, {"tools": True}),
    "tools-sydney-t2": ("emery", "hours", datetime(2026, 10, 15, 10, 30, tzinfo=timezone.utc), (-33.87, 151.21, 660),
                        {"tools": True}),
    # the calendars' days (all kept): the name on the almanac's line, the emblem, the lights and the fires
    "feast-july4-t2": ("emery", "planisphere", datetime(2026, 7, 5, 1, 40, tzinfo=timezone.utc), NY, {"calendars": 4095}),
    "feast-christmas-eve-r2": ("gabbro", "planisphere", datetime(2026, 12, 25, 2, 0, tzinfo=timezone.utc), (40.71, -74.01, -300),
                               {"calendars": 4095}),
    "feast-st-johns-t2": ("emery", "planisphere", datetime(2026, 6, 23, 22, 15, tzinfo=timezone.utc), (50.12, -5.53, 60),
                          {"calendars": 1 << 3}),
    "feast-hanukkah-t2": ("emery", "night", datetime(2025, 12, 15, 23, 0, tzinfo=timezone.utc), (40.71, -74.01, -300),
                          {"calendars": 4095}),
    "feast-diwali-r2": ("gabbro", "planisphere", datetime(2026, 11, 8, 14, 30, tzinfo=timezone.utc), (28.61, 77.21, 330),
                        {"calendars": 4095}),
    "feast-spring-festival-t2": ("emery", "orloj", datetime(2026, 2, 17, 12, 0, tzinfo=timezone.utc), (39.90, 116.40, 480),
                                 {"calendars": 4095}),
    "feast-bonfire-night-t2": ("emery", "apian", datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc), (51.51, -0.13, 0),
                               {"calendars": 4095}),
    "feast-solstice-south-t2": ("emery", "planisphere", datetime(2026, 6, 21, 9, 0, tzinfo=timezone.utc), (-33.87, 151.21, 600),
                                {"calendars": 1}),
    # what the feasts mark in the sky: Christmas Eve's first star, the Weaver and the Cowherd, the rabbit in the Moon
    "sky-first-star-t2": ("emery", "planisphere", datetime(2026, 12, 24, 22, 15, tzinfo=timezone.utc), (40.71, -74.01, -300),
                          {"calendars": 4095}),
    "sky-holy-evening-r2": ("gabbro", "planisphere", datetime(2027, 1, 6, 15, 0, tzinfo=timezone.utc), (50.45, 30.52, 120),
                            {"calendars": 4095}),
    "sky-qixi-t2": ("emery", "planisphere", datetime(2026, 8, 19, 13, 0, tzinfo=timezone.utc), (39.90, 116.40, 480),
                    {"calendars": 4095}),
    "sky-qixi-r2": ("gabbro", "burritt", datetime(2026, 8, 19, 14, 0, tzinfo=timezone.utc), (39.90, 116.40, 480),
                    {"calendars": 4095}),
    "sky-mid-autumn-t2": ("emery", "night", datetime(2026, 9, 25, 13, 0, tzinfo=timezone.utc), (39.90, 116.40, 480),
                          {"calendars": 4095}),
    # the Round 2 near a pole, where its window shrinks rather than rising into the almanac
    "arctic-r2": ("gabbro", "planisphere", datetime(2026, 10, 15, 20, 0, tzinfo=timezone.utc), (69.65, 18.96, 120), {}),
    "antarctic-r2": ("gabbro", "burritt", datetime(2026, 7, 15, 20, 0, tzinfo=timezone.utc), (-77.85, 166.67, 720), {}),
    # frames of the fireworks displays at the top of an evening hour (and New Year's midnight), as the watch plays them
    "show-july4-t2": ("emery", "planisphere", datetime(2026, 7, 5, 1, 0, tzinfo=timezone.utc), NY,
                      {"calendars": 64, "show": 20}),
    "show-july4-finale-r2": ("gabbro", "planisphere", datetime(2026, 7, 5, 2, 0, tzinfo=timezone.utc), NY,
                             {"calendars": 64, "show": 66}),
    "show-flamsteed-t2": ("emery", "flamsteed", datetime(2026, 7, 5, 1, 0, tzinfo=timezone.utc), NY,
                          {"calendars": 64, "show": 30}),
    "show-bonfire-t2": ("emery", "planisphere", datetime(2026, 11, 5, 20, 0, tzinfo=timezone.utc), (51.51, -0.13, 0),
                        {"calendars": 128, "show": 40}),
    "show-new-year-r2": ("gabbro", "burritt", datetime(2027, 1, 1, 0, 0, tzinfo=timezone.utc), (51.51, -0.13, 0),
                         {"calendars": 128, "show": 50}),
}


def c_render(screen, plate, when, place, opts, path):
    lat, lon, off = place
    args = [str(ROOT / "build" / "host"), screen, str(PLATE_ID[plate]), str(int(when.timestamp())), str(lat), str(lon),
            str(off), str(path)]
    if opts.get("clock24"):
        args.append("--24")
    if opts.get("labours"):
        args.append("--labours")
    if opts.get("tools"):
        args.append("--tools")
    if opts.get("theme"):
        args += ["--theme", str(opts["theme"])]
    if opts.get("calendars"):
        args += ["--calendars", str(opts["calendars"])]
    if opts.get("show") is not None:
        args += ["--show", str(opts["show"])]
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

    def face(extras=None):
        return plates.render(when, dial, sky, tz, plate, round_screen=screen == "gabbro",
                             clock24=opts.get("clock24", False), weather=w, labours=opts.get("labours", False),
                             calendars=opts.get("calendars", 0), tools=opts.get("tools", False),
                             theme=opts.get("theme"),
                             extras=extras).astype(np.uint8)
    if opts.get("show") is None:
        return face()
    # a frame of the fireworks display due at the top of the hour, over the face as drawn then
    probe = {}
    face(lambda img, ctx: probe.update(ctx))
    seed, sparks = feast_draw.display_at(when.astimezone(tz), probe["sun_alt"], opts.get("calendars", 0), lat)
    plan, _ = feast_draw.show_plan(seed, probe["edge"], probe["col"], sparks, probe["ground"], probe["inside"])
    ink = probe["P"]["accent"] if probe["paper"] else None
    return face(lambda img, ctx: feast_draw.fireworks_show(img, ctx, opts["show"], plan, sparks, ink))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sky = load_sky(4.6)
    args = sys.argv[1:]
    accept = "--accept" in args
    slack = int(args[args.index("--slack") + 1]) if "--slack" in args else 0
    if "--slack" in args:
        del args[args.index("--slack"): args.index("--slack") + 2]
    names = [a for a in args if a != "--accept"] or list(CASES)
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
    worse = []
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
        n, was = int(diff.sum()), base.get(name)
        note = "" if was is None or n == was else f"  (was {was}{', worse' if n > was + slack else ''})"
        if was is not None and n > was + slack:
            worse.append(name)
        print(f"{name:16s} {n:6d} pixels differ ({100 * diff.mean():.2f}%){note}", flush=True)
        base[name] = n
    if accept:
        BASELINE.write_text(json.dumps(base, indent=1, sort_keys=True) + "\n")
    elif worse:
        sys.exit(f"parity: more pixels differ than before in {', '.join(worse)} (--accept if that is meant)")


if __name__ == "__main__":
    main()
