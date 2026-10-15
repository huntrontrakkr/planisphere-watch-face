"""Render the store gallery with the watch's own C (build/host), at the screens' own sizes, named <platform>_<n>_...
as the store expects (docs/screenshots/store). For each watch:

  1  a day: the planisphere over New York from noon to noon, twenty minutes a frame
  2  the ten plates at half past nine in the evening
  3  the total eclipse of 8 April 2024, from Dallas
  4  a snowy morning: the flakes falling past the Sun, the village under snow
  5  the labours of the months: October's sowing on the Book of Hours

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


def frame(platform, plate, when, place, offset, labours=False, weather=None):
    """One face, as the watch draws it: when (aware datetime), place (lat, lon), offset (minutes ahead of UTC)."""
    lat, lon = place
    path = TMP / f"{platform}.ppm"
    args = [str(HOST), platform, str(PLATE[plate]), str(int(when.timestamp())), str(lat), str(lon), str(offset),
            str(path)]
    city, country = plates.place_name(lat, lon)
    if city:
        args += ["--city", city, "--country", country]
    if labours:
        args.append("--labours")
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*_*"):
        old.unlink()
    for p in ("emery", "gabbro"):
        noon = datetime(2026, 10, 15, 16, 0, tzinfo=timezone.utc)        # noon in New York (four hours behind)
        day = [frame(p, "planisphere", noon + timedelta(minutes=20 * k), NY, -240) for k in range(72)]
        save_gif(day, OUT / f"{p}_1_a_day.gif", 140)
        evening = datetime(2026, 10, 16, 1, 30, tzinfo=timezone.utc)
        save_gif([frame(p, name, evening, NY, -240) for name in plates.PLATES], OUT / f"{p}_2_plates.gif", 1600)
        frame(p, "planisphere", datetime(2024, 4, 8, 18, 42, tzinfo=timezone.utc), DALLAS, -300).save(OUT / f"{p}_3.png")
        frame(p, "planisphere", datetime(2026, 1, 15, 16, 30, tzinfo=timezone.utc), NY, -300,
              weather="snow").save(OUT / f"{p}_4.png")
        frame(p, "hours", evening, NY, -240, labours=True).save(OUT / f"{p}_5.png")
    for f in sorted(OUT.iterdir()):
        print(f"{f.stat().st_size:>9,}  {f.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
