"""Render the store gallery with the watch's own C (build/host), at the screens' own sizes, named <platform>_<n>_...
as the store expects (docs/screenshots/store), and the same reels for the README with both watches side by side
(docs/gallery-*.gif). For each watch:

  1  a day: the planisphere over New York from noon to noon, twenty minutes a frame
  2  the minute written: the new figures outlined and filled as a scribe writes them, as the watch plays it
  3  the almanac's days: feasts of the twelve calendars, each on its own plate, with the labours of the months
  4  the variations: the options together, each frame another plate, clock, names, labours, place and sky
  5  anywhere: the place moving from the equator to the north pole and back, then to the south pole, the window
     cut again for each latitude
  6  the weather: fair, cirrus, cloudy, overcast, rain, snow, fog, frost, a gale, thunder
  7  a fireworks display at the top of an evening hour, as the watch plays it: Independence Day in New York
  8  the ten plates at half past nine in the evening
  9  the sky's news: a total eclipse of the Sun, the Moon eclipsed, Venus meeting Jupiter, a meteor shower's peak
 10  the passing events, as the watch plays them: the figures drawn in at dusk, a skein of birds at twilight, meteors
     out of the Orionids' radiant on the night of their peak
and for the README alone: the Time 2's Labours' tools in its corners, month by month (docs/gallery-tools.gif), and the
zodiac behind the face, sign by sign (docs/gallery-zodiac.gif); the astronomer, month by month
(docs/gallery-astronomer.gif); the sea, month by month and through a tide (docs/gallery-sea.gif, gallery-sea-tide.gif); the herbal
(docs/gallery-herbal.gif).

    tools/build-host.sh && cd proto && uv run python ../tools/store_gallery.py
"""
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import plates                      # noqa: E402
import weather as meteo           # noqa: E402

OUT = ROOT / "docs" / "screenshots" / "store"
TMP = ROOT / "out" / "gallery"
HOST = ROOT / "build" / "host"
PLATE = {n: i for i, n in enumerate(plates.PLATES)}
NY = (40.71, -74.01)
DALLAS = (32.7767, -96.797)


def frame(platform, plate, when, place, offset, labours=False, weather=None, calendars=0, show=None, clock24=False,
          names=True, fahrenheit=False, city=None, scribe=None, events=0, event=None, tools=False, theme=0,
          tides=()):
    """One face, as the watch draws it: when (aware datetime), place (lat, lon), offset (minutes ahead of UTC); the
    calendars kept (bit n for feasts.CALENDARS[n]), the frame of the fireworks display due then, if any; the clock,
    the names in the sky, the temperature's scale, and the place's name on the ring ((city, country); else the
    prototype's name for it, if it has one)."""
    lat, lon = place
    path = TMP / f"{platform}.ppm"
    args = [str(HOST), platform, str(PLATE[plate]), str(int(when.timestamp())), str(lat), str(lon), str(offset),
            str(path)]
    if city:                                        # (a name given: as the phone would send it)
        import names
        city = (names.city_ladder(city[0]), names.region_ladder("", "", city[1]))
    city, country = city or plates.place_name(lat, lon)
    if city:
        args += ["--city", city, "--country", country]
    if clock24:
        args.append("--24")
    if not names:
        args.append("--no-names")
    if fahrenheit:
        args.append("--fahrenheit")
    if labours:
        args.append("--labours")
    if calendars:
        args += ["--calendars", str(calendars)]
    if show is not None:
        args += ["--show", str(show)]
    if scribe is not None:                          # the minute written (the minute before drawn first), to a frame
        args += ["--scribe-frame", str(scribe)]
    if tools:
        args.append("--tools")
    if theme:
        args += ["--theme", str(theme)]
    if tides:                                       # the tide's turns, (minutes from `when`, high, cm)
        now = int(when.timestamp()) // 60
        args += ["--tides", ",".join(f"{now + m}:{'H' if hi else 'L'}:{cm}" for m, hi, cm in tides)]
    if events:                                      # the passing events allowed (EV_*), and the one chosen to a frame
        args += ["--events", str(events)] + (["--event-frame", str(event)] if event is not None else [])
    if weather:
        s = meteo.SAMPLES[weather]
        args += ["--weather", ",".join(str(int(round(v))) for v in (
            s.temp * 10, s.code, s.low * 100, s.mid * 100, s.high * 100, s.wind, s.wind_from, s.pressure,
            s.snow_depth * 1000, s.visibility / 10))]
    subprocess.run(args, check=True)
    return Image.open(path).convert("RGB")


def save_gif(ims, path, duration):
    # every pixel is one of the watch's 64 colours, so the palette loses nothing
    pal = [im.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for im in ims]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=duration, loop=0, optimize=True)


def display_frames(platform, when, place, offset, calendars):
    """The frames of the fireworks display due at a moment (build/host --show-check)."""
    out = subprocess.run([str(HOST), platform, "0", str(int(when.timestamp())), str(place[0]), str(place[1]),
                          str(offset), str(TMP / "check.ppm"), "--calendars", str(calendars), "--show-check"],
                         capture_output=True, text=True, check=True).stdout
    return int(out.split(" frames")[0].split()[-1])


def event_minutes(platform, start, place, offset, kind, count):
    """The first minutes from `start` (aware) that bring the passing event `kind` (EV_*), and its frames."""
    found, when = [], start
    while len(found) < count and when < start + timedelta(hours=3):
        out = subprocess.run([str(HOST), platform, "0", str(int(when.timestamp())), str(place[0]), str(place[1]),
                              str(offset), str(TMP / "check.ppm"), "--events", str(kind)],
                             capture_output=True, text=True, check=True).stdout
        if out.startswith(f"event {kind}:"):
            found.append((when, int(out.split(": ")[1].split()[0])))
        when += timedelta(minutes=1)
    return found


def local(y, mo, d, h, mi, offset):
    """A local moment (offset minutes ahead of UTC), as an aware datetime."""
    return datetime(y, mo, d, h, mi, tzinfo=timezone(timedelta(minutes=offset)))


ALL = (1 << 12) - 1                 # every calendar kept
BEIJING, DELHI, LONDON, ROME, CORNWALL = (39.90, 116.40), (28.61, 77.21), (51.51, -0.13), (41.90, 12.50), (50.12, -5.53)
# the almanac's days: (plate, local moment, place, offset), each on a plate of its own
FEASTS = [
    ("planisphere", local(2026, 12, 24, 17, 15, -300), NY, -300),          # Christmas Eve: holly, the first star
    ("hours", local(2026, 11, 8, 20, 0, 330), DELHI, 330),                 # Diwali: the lamp, every window lit
    ("burritt", local(2026, 8, 19, 21, 0, 480), BEIJING, 480),             # Qixi: the Weaver, the Cowherd, the magpies
    ("night", local(2025, 12, 15, 18, 0, -300), NY, -300),                 # Hanukkah: the night's lights
    ("orloj", local(2026, 9, 25, 21, 0, 480), BEIJING, 480),               # Mid-Autumn: the rabbit in the Moon
    ("apian", local(2026, 6, 23, 23, 15, 60), CORNWALL, 60),               # St John's Eve: fires on the hills
    ("astrolabe", local(2026, 12, 17, 19, 0, 60), ROME, 60),               # Saturnalia: the cap of liberty
    ("cyanotype", local(2027, 2, 6, 20, 0, 480), BEIJING, 480),            # the Spring Festival: the lantern
    ("planisphere", local(2026, 10, 31, 20, 0, -240), NY, -240),           # Samhain (over Halloween): fires on the hills
]


# the variations: (plate, local moment, place, offset, city and country, options)
VARIATIONS = [
    ("planisphere", local(2026, 10, 15, 21, 30, -240), NY, -240, None, dict(weather="fair")),
    ("burritt", local(2026, 12, 10, 20, 0, 0), LONDON, 0, None, dict(clock24=True, weather="cloudy")),
    ("flamsteed", local(2026, 10, 15, 21, 0, 660), (-33.87, 151.21), 660, None, dict(labours=True)),
    ("observatory", local(2026, 11, 20, 22, 0, 0), (64.15, -21.94), 0, ("REYKJAVIK", "ICELAND"),
     dict(clock24=True, weather="frost")),
    ("astrolabe", local(2026, 10, 15, 21, 0, 180), (30.04, 31.24), 180, ("CAIRO", "EGYPT"),
     dict(clock24=True, labours=True)),
    ("hours", local(2026, 12, 20, 18, 0, 60), (48.86, 2.35), 60, None, dict(labours=True, weather="snow")),
    ("orloj", local(2026, 10, 15, 22, 0, 120), (50.09, 14.42), 120, ("PRAGUE", "CZECHIA"), dict(clock24=True)),
    ("cyanotype", local(2026, 7, 15, 20, 0, 120), (-33.92, 18.42), 120, ("CAPE TOWN", "SOUTH AFRICA"),
     dict(weather="rain")),
    ("apian", local(2026, 10, 15, 21, 30, 120), (48.77, 11.43), 120, ("INGOLSTADT", "GERMANY"),
     dict(labours=True, weather="fair", fahrenheit=True)),
    ("night", local(2026, 10, 15, 23, 0, 540), (35.68, 139.69), 540, None, dict(clock24=True, names=False,
                                                                                weather="cirrus")),
]


def side_by_side(a, b):
    """The Time 2's frame beside the Round 2's, for the README."""
    out = Image.new("RGB", (a.width + 16 + b.width, max(a.height, b.height)), (255, 255, 255))
    out.paste(a, (0, (out.height - a.height) // 2))
    out.paste(b, (a.width + 16, (out.height - b.height) // 2))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*_*"):
        old.unlink()
    reels = {}                                      # (name, platform): (frames, ms a frame)
    for p in ("emery", "gabbro"):
        noon = datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)        # noon in New York (four hours behind)
        reels["a_day", p] = ([frame(p, "planisphere", noon + timedelta(minutes=20 * k), NY, -240) for k in range(72)],
                             140)
        # the minute written: half past nine and ten o'clock coming, the face a moment before each, at 12 frames a second
        written = []
        for when in (local(2026, 10, 15, 21, 30, -240), local(2026, 10, 15, 22, 0, -240)):
            before = frame(p, "planisphere", when - timedelta(minutes=1), NY, -240)
            written += [before] * 14 + [frame(p, "planisphere", when, NY, -240, scribe=k) for k in range(8)]
            written += [written[-1]] * 14
        reels["minute", p] = (written, 83)
        reels["almanac", p] = ([frame(p, plate, when, place, off, labours=True, calendars=ALL)
                                for plate, when, place, off in FEASTS], 2000)
        reels["variations", p] = ([frame(p, plate, when, place, off, city=city, **opts)
                                   for plate, when, place, off, city, opts in VARIATIONS], 1800)
        # anywhere: from the equator north to the pole and back, then south to the pole and back, held a little at
        # the turns
        night = datetime(2026, 10, 15, 22, 0, tzinfo=timezone.utc)
        lats = [0] * 4 + list(range(2, 89, 2)) + [88] * 6 + list(range(86, -1, -2)) + [0] * 4
        lats += list(range(-2, -89, -2)) + [-88] * 6 + list(range(-86, 1, 2))
        reels["anywhere", p] = ([frame(p, "planisphere", night, (lat, 0.0), 0) for lat in lats], 110)
        dusk = local(2026, 10, 15, 18, 40, -240)
        reels["weather", p] = ([frame(p, "planisphere", dusk, NY, -240, weather=w) for w in
                                ("fair", "cirrus", "cloudy", "overcast", "rain", "snow", "fog", "frost", "gale",
                                 "thunder")], 1600)
        # the display at ten on Independence Day, a second of the face before it and after
        july4 = local(2026, 7, 4, 22, 0, -240)
        lead = frame(p, "planisphere", july4, NY, -240, calendars=64)
        shows = [frame(p, "planisphere", july4, NY, -240, calendars=64, show=k)
                 for k in range(display_frames(p, july4, NY, -240, 64) + 1)]
        reels["fireworks", p] = ([lead] * 12 + shows + [lead] * 12, 83)
        evening = datetime(2026, 10, 16, 1, 30, tzinfo=timezone.utc)
        reels["plates", p] = ([frame(p, name, evening, NY, -240) for name in plates.PLATES], 1600)
        reels["news", p] = ([frame(p, "planisphere", datetime(2024, 4, 8, 18, 42, tzinfo=timezone.utc), DALLAS, -300),
                             frame(p, "planisphere", datetime(2025, 3, 14, 6, 50, tzinfo=timezone.utc), NY, -240),
                             frame(p, "planisphere", datetime(2023, 3, 2, 0, 20, tzinfo=timezone.utc), NY, -300),
                             frame(p, "planisphere", datetime(2026, 10, 22, 6, 0, tzinfo=timezone.utc), NY, -240)],
                            2000)
        events = []
        for kind, start, place, off, k in ((2, local(2026, 10, 15, 19, 0, 60), LONDON, 60, 1),
                                           (4, local(2026, 10, 15, 18, 0, 60), LONDON, 60, 1),
                                           (1, local(2026, 10, 21, 2, 0, 60), LONDON, 60, 4)):
            for when, n in event_minutes(p, start, place, off, kind, k):
                still = frame(p, "planisphere", when - timedelta(minutes=kind == 2), place, off)   # (no figures yet)
                played = [frame(p, "planisphere", when, place, off, events=kind, event=f) for f in range(n + 1)]
                events += [still] * 10 + [x for x in played for _ in range(2 if kind == 2 else 1)] + [played[-1]] * 6
        reels["events", p] = (events, 83)
    order = ["a_day", "minute", "almanac", "variations", "anywhere", "weather", "fireworks", "plates", "news", "events"]
    for n, name in enumerate(order, 1):
        for p in ("emery", "gabbro"):
            save_gif(*reels[name, p][:1], OUT / f"{p}_{n}_{name}.gif", reels[name, p][1])
        if name == "events":                        # (each watch's events last their own time: the Time 2's alone)
            save_gif(*reels[name, "emery"][:1], ROOT / "docs" / f"gallery-{name}.gif", reels[name, "emery"][1])
        if name in ("minute", "variations", "anywhere", "weather", "fireworks", "almanac"):
            (a, ms), (b, _) = reels[name, "emery"], reels[name, "gabbro"]
            save_gif([side_by_side(x, y) for x, y in zip(a, b)], ROOT / "docs" / f"gallery-{name}.gif", ms)
    # the zodiac behind the face, sign by sign (a day in the middle of each), on both watches side by side
    signs = [(2026, 4, 5), (2026, 5, 6), (2026, 6, 6), (2026, 7, 8), (2026, 8, 8), (2026, 9, 8), (2026, 10, 8),
             (2026, 11, 7), (2026, 12, 7), (2027, 1, 5), (2027, 2, 4), (2027, 3, 6)]
    save_gif([side_by_side(*(frame(p, "planisphere", local(y, m, d, 21, 30, -240 if 3 < m < 11 else -300), NY,
                                   -240 if 3 < m < 11 else -300, theme=2, tools=True) for p in ("emery", "gabbro")))
              for y, m, d in signs], ROOT / "docs" / "gallery-zodiac.gif", 1200)
    astronomer_gallery()
    sea_gallery()
    herbal_gallery()
    save_gif([frame("emery", "planisphere", local(2026, m, 15, 21, 30, -240 if 3 < m < 11 else -300), NY,
                    -240 if 3 < m < 11 else -300, tools=True) for m in range(1, 13)], ROOT / "docs" / "gallery-tools.gif", 1200)
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size:>9,}  {f.relative_to(ROOT)}")
    for f in sorted((ROOT / "docs").glob("gallery-*.gif")):
        print(f"{f.stat().st_size:>9,}  {f.relative_to(ROOT)}")


def astronomer_gallery():
    """The astronomer behind the face, month by month (Tycho's instrument; the planets up in the Time 2's corners), on
    both watches side by side (docs/gallery-astronomer.gif)."""
    save_gif([side_by_side(*(frame(p, "planisphere", local(2026, m, 15, 21, 30, -240 if 3 < m < 11 else -300), NY,
                                   -240 if 3 < m < 11 else -300, theme=3, tools=True) for p in ("emery", "gabbro")))
              for m in range(1, 13)], ROOT / "docs" / "gallery-astronomer.gif", 1200)


def sea_gallery():
    """The sea behind the face, month by month, each at another hour of the tide (the Time 2 with the sea's corners),
    and one month's ship through a tide, hour by hour, both watches side by side (docs/gallery-sea.gif,
    docs/gallery-sea-tide.gif)."""
    def tide(at):                                   # turns about a moment `at` minutes after a low water
        return [(-at, False, 25), (372 - at, True, 180), (745 - at, False, 20)]

    def faces(m, at):
        when = local(2026, m, 15, 21, 30, -240 if 3 < m < 11 else -300)
        return side_by_side(*(frame(p, "planisphere", when, NY, -240 if 3 < m < 11 else -300, theme=4, tools=True,
                                    tides=tide(at)) for p in ("emery", "gabbro")))
    save_gif([faces(m, m * 61 % 745) for m in range(1, 13)], ROOT / "docs" / "gallery-sea.gif", 1200)
    save_gif([faces(1, h * 31) for h in range(24)], ROOT / "docs" / "gallery-sea-tide.gif", 300)


def herbal_gallery():
    """The herbal behind the face, month by month (Fuchs's plant; the gardener's Moon in the Time 2's corners), on
    both watches side by side (docs/gallery-herbal.gif)."""
    save_gif([side_by_side(*(frame(p, "planisphere", local(2026, m, 15, 21, 30, -240 if 3 < m < 11 else -300), NY,
                                   -240 if 3 < m < 11 else -300, theme=5, tools=True) for p in ("emery", "gabbro")))
              for m in range(1, 13)], ROOT / "docs" / "gallery-herbal.gif", 1200)


if __name__ == "__main__":
    main()
