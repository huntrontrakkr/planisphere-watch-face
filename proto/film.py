"""A day on the wrist: the planisphere every few minutes for 24 hours, as a GIF,
and stills for both watches.

    uv run python proto/film.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from render import Dial, load_sky
from render2 import render

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
NY = ZoneInfo("America/New_York")
LAT, LON = 40.71, -74.01                    # New York


def gif(frames, path, ms):
    pal = [f.convert("RGB").quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(path, save_all=True, append_images=pal[1:], duration=ms, loop=0, optimize=True)


def main():
    sky = load_sky(4.6)
    round2, time2 = Dial(260, 260, LAT, LON), Dial(200, 228, LAT, LON)
    start = datetime(2026, 10, 14, 12, 0, tzinfo=NY)
    frames = []
    for k in range(0, 24 * 60, 8):
        t = start + timedelta(minutes=k)
        im, _ = render(t.astimezone(timezone.utc), round2, sky, NY)
        frames.append(Image.fromarray(im))
    gif(frames, OUT / "planisphere-day-round2.gif", 70)
    print(len(frames), "frames")
    # stills: the evening sky on both watches, and the four moods of the Round 2
    for name, dial, rnd in (("round2", round2, True), ("time2", time2, False)):
        for label, t in (("evening", datetime(2026, 10, 14, 21, 30, tzinfo=NY)), ("noon", datetime(2026, 10, 14, 12, 15, tzinfo=NY)),
                         ("dusk", datetime(2026, 10, 14, 18, 52, tzinfo=NY)), ("dawn", datetime(2026, 10, 15, 6, 28, tzinfo=NY))):
            im, _ = render(t.astimezone(timezone.utc), dial, sky, NY, round_screen=rnd)
            Image.fromarray(im).save(OUT / f"{name}-{label}.png")


if __name__ == "__main__":
    main()
