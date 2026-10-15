"""Films of the feasts' animations, at the watch's own frame rate: the fireworks display at the top of an evening
hour. Writes research/holidays/fireworks-*.gif.

    uv run python proto/film_feasts.py
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image

import feast_draw
from plates import render, RectDial, RoundDial
from render import load_sky

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "holidays"
FPS = feast_draw.FPS
NY, LONDON = (40.71, -74.01), (51.51, -0.13)
JULY4 = dict(words=("INDEPENDENCE DAY", "JULY FOURTH"), emblem="star", fireworks="independence")
BONFIRE = dict(words=("BONFIRE NIGHT", "GUY FAWKES"), emblem="star", brings=("bonfires",), fireworks="bonfire")


def film(name, place, local, offset, plate, feast, round_screen=False):
    tz = timezone(timedelta(minutes=offset))
    when = local.replace(tzinfo=tz).astimezone(timezone.utc)
    dial = RoundDial(260, 260, *place) if round_screen else RectDial(200, 228, *place)
    sparks = feast_draw.SPARKS[feast["fireworks"]]
    probe = {}
    render(when, dial, sky, tz, plate, round_screen, feast=feast, extras=lambda img, ctx: probe.update(ctx))
    plan, end = feast_draw.show_plan(local.toordinal() * 24 + local.hour, probe["edge"], probe["col"], sparks)
    ink = probe["P"]["accent"] if probe["paper"] else None
    lead, tail = 6, 10
    frames = []
    for k in range(lead + end + tail):
        f = k - lead
        frames.append(render(when + timedelta(seconds=k / FPS), dial, sky, tz, plate, round_screen, feast=feast,
                             extras=lambda img, ctx, f=f: feast_draw.fireworks_show(img, ctx, f, plan, sparks, ink)))
    size = (390, 390) if round_screen else (400, 456)
    pal = [Image.fromarray(fr.astype("uint8")).resize(size, Image.NEAREST).quantize(
        colors=64, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for fr in frames]
    pal[0].save(OUT / f"fireworks-{name}.gif", save_all=True, append_images=pal[1:], duration=int(1000 / FPS), loop=0,
                optimize=True)
    print(name, len(frames), "frames")


if __name__ == "__main__":
    sky = load_sky(4.6)
    film("july4-time2", NY, datetime(2026, 7, 4, 21, 0), -240, "planisphere", JULY4)
    film("july4-round2", NY, datetime(2026, 7, 4, 22, 0), -240, "planisphere", JULY4, round_screen=True)
    film("july4-flamsteed", NY, datetime(2026, 7, 4, 21, 0), -240, "flamsteed", JULY4)
    film("bonfire-night", LONDON, datetime(2026, 11, 5, 20, 0), 0, "planisphere", BONFIRE)
