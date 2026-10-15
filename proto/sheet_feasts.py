"""Sheets of the feasts' pieces, for looking over: every emblem (proto/feast_emblems.py) in the Planisphere's red ink
with the days that carry it, and what the feasts bring to the sky, as the watch's own C draws it (build/host): the
first star, the Weaver and the Cowherd, the rabbit in the Moon, and frames of the fireworks displays. Writes
research/holidays/emblems.png and research/holidays/feast-sky.png.

    tools/build-host.sh && (cd proto && uv run python sheet_feasts.py)
"""
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import feast_emblems
import feasts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "holidays"
HOST = ROOT / "build" / "host"
PAPER, INK, RED, RULE = (242, 232, 204), (31, 27, 20), (168, 41, 31), (138, 122, 90)
FONT = ImageFont.truetype(str(ROOT / "fonts" / "pixel" / "NotJamOldStyle14.ttf"), 14)


def label(draw, x, y, text, width, fill=INK):
    """Centred words, broken to fit the width."""
    words, lines, line = text.split(), [], ""
    for w in words:
        if line and draw.textlength(line + " " + w, font=FONT) > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    lines.append(line)
    for i, ln in enumerate(lines):
        draw.text((x + (width - draw.textlength(ln, font=FONT)) / 2, y + 15 * i), ln, font=FONT, fill=fill)


def emblems():
    days = {}
    for f in feasts.FEASTS:
        if f.get("emblem"):
            w = f["words"][-1].title().replace("'S", "'s")
            if w not in days.setdefault(f["emblem"], []):
                days[f["emblem"]].append(w)
    names, cols, cw, ch, s = list(feast_emblems.EMBLEMS), 8, 150, 130, 5
    rows = -(-len(names) // cols)
    img = Image.new("RGB", (cols * cw + 40, rows * ch + 80), PAPER)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "The feasts' emblems, after the calendar sticks: one ink, one strong outline", font=FONT, fill=INK)
    for i, name in enumerate(names):
        x0, y0 = 20 + (i % cols) * cw, 50 + (i // cols) * ch
        a = feast_emblems.emblem(name, 3 if name == "hanukkiah" else None)
        h, w = a.shape
        ox, oy = x0 + (cw - w * s) // 2, y0 + (70 - h * s) // 2
        for y, x in zip(*np.nonzero(a)):
            d.rectangle((ox + x * s, oy + y * s, ox + x * s + s - 1, oy + y * s + s - 1), fill=RED)
        label(d, x0 + 4, y0 + 74, name, cw - 8, INK)
        label(d, x0 + 4, y0 + 90, ", ".join(days.get(name, [])), cw - 8, RULE)
    img.save(OUT / "emblems.png", optimize=True)
    print("emblems.png", img.size)


def host(screen, plate, when, place, calendars, show=None):
    """A face from the watch's C at a local moment (when, naive; place (lat, lon, offset minutes))."""
    lat, lon, off = place
    utc = int((when - timedelta(minutes=off)).replace(tzinfo=timezone.utc).timestamp())
    with tempfile.NamedTemporaryFile(suffix=".ppm") as f:
        args = [str(HOST), screen, str(plate), str(utc), str(lat), str(lon), str(off), f.name, "--calendars",
                str(calendars)] + (["--show", str(show)] if show is not None else [])
        subprocess.run(args, check=True)
        return Image.open(f.name).convert("RGB")


def inset(feast, plain, crop, only=None, margin=6, most=(250, 240)):
    """The part of a window a feast changed (against the same face with no calendars; `only` the pixels of that
    colour), enlarged as far as fits in `most`."""
    a, b = np.asarray(feast.crop(crop)), np.asarray(plain.crop(crop))
    changed = (a != b).any(axis=2)
    if only is not None:
        changed &= (a == only).all(axis=2)
    ys, xs = np.nonzero(changed)
    if not len(xs):
        return None
    box = (max(0, xs.min() - margin), max(0, ys.min() - margin), min(a.shape[1], xs.max() + margin + 1),
           min(a.shape[0], ys.max() + margin + 1))
    im = feast.crop(crop).crop(box)
    k = max(1, min(8, most[0] // im.width, most[1] // im.height))
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def busiest(screen, plate, when, place, calendars):
    """The display's frame that covers the most of the window (its finale, as a rule)."""
    base, best = np.asarray(host(screen, plate, when, place, calendars)), (0, 0)
    for k in range(0, 110, 2):
        n = int((np.asarray(host(screen, plate, when, place, calendars, k)) != base).any(axis=2).sum())
        best = max(best, (n, k))
    return best[1]


def sky():
    NY, BEIJING, LONDON = (40.71, -74.01, -300), (39.90, 116.40, 480), (51.51, -0.13, 0)
    T2, R2 = (14, 92, 186, 214), (45, 90, 215, 250)
    marks = [  # (words, screen, plate, local moment, place, crop, the inset's colour and margin): each with what the
        # feast added, enlarged
        ("Christmas Eve: the first star out, named in red with its glint", "emery", 0, datetime(2026, 12, 24, 17, 15),
         NY, T2, None, 6),
        ("Qixi: the Weaver and the Cowherd, the magpies' bridge between them", "emery", 0,
         datetime(2026, 8, 19, 21, 0), BEIJING, T2, (255, 255, 255), 9),
        ("Mid-Autumn: the rabbit in the full Moon", "emery", 9, datetime(2026, 9, 25, 21, 0), BEIJING, T2, None, 4),
    ]
    shows = [  # (words, screen, plate, local moment, place, calendars, crop): each at its busiest frame
        ("Independence Day, 10 pm", "gabbro", 0, datetime(2026, 7, 4, 22, 0), NY[:2] + (-240,), 64, R2),
        ("Bonfire Night, 8 pm, with the fires on the hills", "emery", 0, datetime(2026, 11, 5, 20, 0), LONDON, 128, T2),
        ("Diwali, 9 pm: gold, orange and white, as before the 1830s", "emery", 5, datetime(2026, 11, 8, 21, 0),
         (28.61, 77.21, 330), 2048, T2),
        ("New Year's Eve on a printed chart: engraved in its ink", "emery", 2, datetime(2026, 12, 31, 21, 0),
         NY[:2] + (-300,), 64, T2),
    ]
    s, cw = 2, 380
    row1 = []
    for words, screen, plate, when, place, crop, only, margin in marks:
        feast, plain = host(screen, plate, when, place, 4095), host(screen, plate, when, place, 0)
        im = feast.crop(crop)
        row1.append((words, im.resize((im.width * s, im.height * s), Image.NEAREST),
                     inset(feast, plain, crop, only, margin)))
    row2 = []
    for words, screen, plate, when, place, cal, crop in shows:
        k = busiest(screen, plate, when, place, cal)
        im = host(screen, plate, when, place, cal, k).crop(crop)
        row2.append((f"{words} (frame {k})", im.resize((im.width * s, im.height * s), Image.NEAREST)))
    h1 = max(t.height for _, t, _ in row1) + 50
    h2 = max(t.height for _, t in row2) + 50
    w1 = 20 + sum(t.width + (i.width + 12 if i else 0) + 30 for _, t, i in row1)
    img = Image.new("RGB", (max(w1, 4 * cw + 40), h1 + h2 + 70), PAPER)
    d = ImageDraw.Draw(img)
    d.text((20, 18), "What the feasts bring to the sky, as the watch draws it", font=FONT, fill=INK)
    x = 20
    for words, t, ins in row1:
        w = t.width + (ins.width + 12 if ins else 0)
        img.paste(t, (x, 46))
        if ins:
            img.paste(ins, (x + t.width + 12, 46))
        label(d, x, 46 + t.height + 6, words, w)
        x += w + 30
    for i, (words, t) in enumerate(row2):
        x0, y0 = 20 + i * cw, 46 + h1 + 10
        img.paste(t, (x0 + (cw - t.width) // 2, y0))
        label(d, x0 + 6, y0 + t.height + 6, words, cw - 12)
    img.save(OUT / "feast-sky.png", optimize=True)
    print("feast-sky.png", img.size)


if __name__ == "__main__":
    emblems()
    sky()
