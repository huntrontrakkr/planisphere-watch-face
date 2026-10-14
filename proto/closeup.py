"""Close-ups of the hand-drawn pieces as the faces draw them, for checking pixel by pixel.

    uv run python proto/closeup.py [plate] [hour]

Writes out/closeup-time2.png and out/closeup-round2.png: the whole face at 3x, and crops of the ring's
lettering, numerals, ornaments and the sky's pieces at 8x, with a faint pixel grid."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from plates import render, RectDial, RoundDial, NY, ROOT
from render import Dial, load_sky


def grid(im, s):
    a = np.asarray(im.resize((im.width * s, im.height * s), Image.NEAREST)).copy()
    if s >= 6:
        a[::s, :] = (a[::s, :] * 0.82).astype(np.uint8)
        a[:, ::s] = (a[:, ::s] * 0.82).astype(np.uint8)
    return Image.fromarray(a)


def sheet(img, crops, s=8):
    im = Image.fromarray(img)
    whole = grid(im, 3)
    tiles = [grid(im.crop(c), s) for c in crops]
    w = max(whole.width, sum(t.width for t in tiles[:2]) + 8)
    rows, row, x = [], [], 0
    for t in tiles:
        if row and x + t.width > w:
            rows.append(row); row, x = [], 0
        row.append(t); x += t.width + 8
    if row:
        rows.append(row)
    h = whole.height + sum(max(t.height for t in r) + 8 for r in rows) + 8
    out = Image.new("RGB", (w, h), (40, 40, 44))
    out.paste(whole, (0, 0))
    y = whole.height + 8
    for r in rows:
        x = 0
        for t in r:
            out.paste(t, (x, y)); x += t.width + 8
        y += max(t.height for t in r) + 8
    return out


def words_sheet(t2img, r2img, path):
    """The ring's words up close: each band at 10x with a pixel grid, and at 1x and 2x beside."""
    tiles = []
    for img, box in ((t2img, (40, 0, 160, 26)), (t2img, (40, 202, 160, 228)), (r2img, (60, 0, 200, 30)),
                     (r2img, (80, 230, 180, 260))):
        im = Image.fromarray(img).crop(box)
        tiles.append(grid(im, 10))
        small = Image.new("RGB", (im.width * 3 + 12, im.height * 2), (40, 40, 44))
        small.paste(im, (0, 0)); small.paste(im.resize((im.width * 2, im.height * 2), Image.NEAREST), (im.width + 12, 0))
        tiles.append(small)
    w = max(t.width for t in tiles)
    out = Image.new("RGB", (w, sum(t.height + 10 for t in tiles)), (40, 40, 44))
    y = 0
    for t in tiles:
        out.paste(t, (0, y)); y += t.height + 10
    out.save(path)


if __name__ == "__main__":
    plate = sys.argv[1] if len(sys.argv) > 1 else "planisphere"
    hour = float(sys.argv[2]) if len(sys.argv) > 2 else 21.5
    when = datetime(2026, 10, 14, int(hour), int(round((hour % 1) * 60)), tzinfo=NY).astimezone(timezone.utc)
    sky = load_sky(4.6)
    t2 = RectDial(200, 228, 40.71, -74.01)
    img = t2img = render(when, t2, sky, NY, plate, False)
    sheet(img, [(44, 0, 156, 30), (0, 0, 56, 56), (144, 0, 200, 56), (0, 92, 30, 132), (44, 198, 156, 228),
                (0, 172, 56, 228), (78, 58, 122, 86)]).save(ROOT / "out" / "closeup-time2.png")
    r2 = RoundDial(260, 260, 40.71, -74.01)
    img = r2img = render(when, r2, sky, NY, plate, True)
    sheet(img, [(70, 0, 190, 28), (85, 232, 175, 260), (0, 110, 34, 150), (226, 110, 260, 150)]).save(
        ROOT / "out" / "closeup-round2.png")
    words_sheet(t2img, r2img, ROOT / "out" / "closeup-words.png")
    print("ok")
