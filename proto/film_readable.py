"""The readable planisphere through a day, and its stills, for the README.

    uv run python proto/film_readable.py
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
NY = ZoneInfo("America/New_York")


def main():
    sky = load_sky(4.6)
    dial = Dial(260, 260, 40.71, -74.01)
    start = datetime(2026, 10, 14, 12, 0, tzinfo=NY)
    frames = []
    for k in range(0, 24 * 60, 8):
        im, _ = render((start + timedelta(minutes=k)).astimezone(timezone.utc), dial, sky, NY, readable=True)
        frames.append(Image.fromarray(im).resize((520, 520), Image.NEAREST))
    pal = [f.quantize(colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(ROOT / "docs" / "readable-day.gif", save_all=True, append_images=pal[1:], duration=70, loop=0, optimize=True)
    sheet = Image.open(ROOT / "out" / "readable-sheet.png")
    sheet.save(ROOT / "docs" / "readable-moods.png")
    Image.open(ROOT / "out" / "readable-round2-evening.png").resize((780, 780), Image.NEAREST).save(ROOT / "docs" / "readable-evening.png")
    print(len(frames), "frames")


if __name__ == "__main__":
    main()
