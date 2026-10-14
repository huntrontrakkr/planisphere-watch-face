"""The plates for the README: a day on the paper planisphere, and every plate at night and noon on both watches.

    uv run python proto/film_plates.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from render import Dial, load_sky
from plates import render, PLATES, RectDial

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")


def main():
    sky = load_sky(4.6)
    r2, t2 = Dial(260, 260, 40.71, -74.01), RectDial(200, 228, 40.71, -74.01)
    start = datetime(2026, 10, 14, 12, 0, tzinfo=NY)
    for name, dial, rnd, size in (("time2", t2, False, (400, 456)), ("round2", r2, True, (520, 520))):
        frames = [Image.fromarray(render((start + timedelta(minutes=k)).astimezone(timezone.utc), dial, sky, NY, "planisphere", rnd)).resize(size, Image.NEAREST)
                  for k in range(0, 24 * 60, 8)]
        pal = [f.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
        out = "plate-planisphere-day.gif" if name == "round2" else "plate-planisphere-day-time2.gif"
        pal[0].save(ROOT / "docs" / out, save_all=True, append_images=pal[1:], duration=70, loop=0, optimize=True)
    sheet = Image.open(ROOT / "out" / "plates.png")
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(ROOT / "docs" / "plates.png")
    Image.open(ROOT / "out" / "plate-planisphere-night.png").resize((780, 780), Image.NEAREST).save(ROOT / "docs" / "plate-planisphere.png")
    Image.open(ROOT / "out" / "plate-planisphere-time2.png").resize((600, 684), Image.NEAREST).save(ROOT / "docs" / "plate-planisphere-time2.png")
    Image.open(ROOT / "out" / "plate-flamsteed-night.png").resize((780, 780), Image.NEAREST).save(ROOT / "docs" / "plate-flamsteed.png")
    print(len(frames), "frames")


if __name__ == "__main__":
    main()
