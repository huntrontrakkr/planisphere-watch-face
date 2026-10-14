"""The readable planisphere: the time large above the window, the date and
the Sun's next rising or setting, and names on what is bright in the sky.

    uv run python proto/readable.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from render import Dial, load_sky
from render2 import render

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
NY = ZoneInfo("America/New_York")

if __name__ == "__main__":
    sky = load_sky(4.6)
    shots = []
    for name, dial, rnd in (("round2", Dial(260, 260, 40.71, -74.01), True), ("time2", Dial(200, 228, 40.71, -74.01), False)):
        for label, t in (("evening", datetime(2026, 10, 14, 21, 30, tzinfo=NY)), ("noon", datetime(2026, 10, 14, 12, 15, tzinfo=NY)),
                         ("dusk", datetime(2026, 10, 14, 18, 38, tzinfo=NY)), ("predawn", datetime(2026, 10, 15, 5, 40, tzinfo=NY))):
            im, _ = render(t.astimezone(timezone.utc), dial, sky, NY, round_screen=rnd, readable=True)
            Image.fromarray(im).save(OUT / f"readable-{name}-{label}.png")
            shots.append((name, label, Image.fromarray(im)))
    r = [im for n, l, im in shots if n == "round2"]
    t = [im for n, l, im in shots if n == "time2"]
    S = Image.new("RGB", (4 * 268, 268 + 236), (24, 24, 26))
    for i, im in enumerate(r):
        S.paste(im, (i * 268 + 4, 4))
    for i, im in enumerate(t):
        S.paste(im, (i * 268 + 34, 272))
    S.resize((S.width * 2, S.height * 2), Image.NEAREST).save(OUT / "readable-sheet.png")
    print("ok")
