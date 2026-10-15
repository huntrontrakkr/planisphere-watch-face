"""Render the store gallery with the watch's own C (build/host), at the screens' own sizes, named <platform>_<n>_...
as the store expects (docs/screenshots/store). For each watch:

  1  a day: the planisphere over New York from noon to noon, twenty minutes a frame
  2  the almanac's days: feasts of the twelve calendars, each on its own plate, with the labours of the months
  3  the ten plates at half past nine in the evening
  4  a fireworks display at the top of an evening hour, as the watch plays it: Independence Day in New York
  5  the sky's news and the weather: a total eclipse of the Sun, the Moon eclipsed, Venus meeting Jupiter, a snowy
     morning, a thunderstorm by night

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


def frame(platform, plate, when, place, offset, labours=False, weather=None, calendars=0, show=None):
    """One face, as the watch draws it: when (aware datetime), place (lat, lon), offset (minutes ahead of UTC); the
    calendars kept (bit n for feasts.CALENDARS[n]), and the frame of the fireworks display due then, if any."""
    lat, lon = place
    path = TMP / f"{platform}.ppm"
    args = [str(HOST), platform, str(PLATE[plate]), str(int(when.timestamp())), str(lat), str(lon), str(offset),
            str(path)]
    city, country = plates.place_name(lat, lon)
    if city:
        args += ["--city", city, "--country", country]
    if labours:
        args.append("--labours")
    if calendars:
        args += ["--calendars", str(calendars)]
    if show is not None:
        args += ["--show", str(show)]
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*_*"):
        old.unlink()
    for p in ("emery", "gabbro"):
        noon = datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)        # noon in New York (four hours behind)
        day = [frame(p, "planisphere", noon + timedelta(minutes=20 * k), NY, -240) for k in range(72)]
        save_gif(day, OUT / f"{p}_1_a_day.gif", 140)
        save_gif([frame(p, plate, when, place, off, labours=True, calendars=ALL) for plate, when, place, off in FEASTS],
                 OUT / f"{p}_2_almanac.gif", 2000)
        evening = datetime(2026, 10, 16, 1, 30, tzinfo=timezone.utc)
        save_gif([frame(p, name, evening, NY, -240) for name in plates.PLATES], OUT / f"{p}_3_plates.gif", 1600)
        # the display at ten on Independence Day, a second of the face before it and after
        july4 = local(2026, 7, 4, 22, 0, -240)
        lead = frame(p, "planisphere", july4, NY, -240, calendars=64)
        shows = [frame(p, "planisphere", july4, NY, -240, calendars=64, show=k)
                 for k in range(display_frames(p, july4, NY, -240, 64) + 1)]
        save_gif([lead] * 12 + shows + [lead] * 12, OUT / f"{p}_4_fireworks.gif", 83)
        news = [frame(p, "planisphere", datetime(2024, 4, 8, 18, 42, tzinfo=timezone.utc), DALLAS, -300),
                frame(p, "planisphere", datetime(2025, 3, 14, 6, 50, tzinfo=timezone.utc), NY, -240),
                frame(p, "planisphere", datetime(2023, 3, 2, 0, 20, tzinfo=timezone.utc), NY, -300),
                frame(p, "planisphere", datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc), NY, -300, weather="snow"),
                frame(p, "night", datetime(2026, 10, 15, 0, 40, tzinfo=timezone.utc), NY, -240, weather="thunder")]
        save_gif(news, OUT / f"{p}_5_news.gif", 2000)
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size:>9,}  {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
