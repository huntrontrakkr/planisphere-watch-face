"""The plates for the README: a day on the paper planisphere, every plate at night and noon on both watches,
and every plate on the Time 2.

    uv run python proto/film_plates.py
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from render import Dial, load_sky
from plates import render, PLATES, RectDial, RoundDial
import astro

ROOT = Path(__file__).resolve().parents[1]
NY = ZoneInfo("America/New_York")


def main():
    sky = load_sky(4.6)
    r2, t2 = RoundDial(260, 260, 40.71, -74.01), RectDial(200, 228, 40.71, -74.01)
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
    # every plate on the Time 2 at 9:30 pm, then the paper planisphere at dusk and at noon
    night, dusk, noon = (datetime(2026, 10, 14, h, m, tzinfo=NY) for h, m in ((21, 30), (18, 40), (12, 15)))
    shots = [(night, pl) for pl in PLATES] + [(dusk, "planisphere"), (noon, "planisphere")]
    sheet = Image.new("RGB", (len(shots) * 412, 464), (24, 24, 26))
    for i, (t, pl) in enumerate(shots):
        im = Image.fromarray(render(t.astimezone(timezone.utc), t2, sky, NY, pl, False)).resize((400, 456), Image.NEAREST)
        sheet.paste(im, (i * 412 + 6, 4))
    sheet.save(ROOT / "docs" / "time2-plates.png")
    # the 12-hour and 24-hour clocks side by side at 9:30 pm, on the Time 2 and the Round 2
    shots = [(t2, False, False), (t2, False, True), (r2, True, False), (r2, True, True)]
    sizes = [(400, 456) if not rnd else (456, 456) for _, rnd, _ in shots]
    sheet = Image.new("RGB", (sum(w + 12 for w, _ in sizes), 464), (24, 24, 26))
    x = 6
    for (dial, rnd, c24), size in zip(shots, sizes):
        im = Image.fromarray(render(night.astimezone(timezone.utc), dial, sky, NY, "planisphere", rnd, clock24=c24))
        sheet.paste(im.resize(size, Image.NEAREST), (x, 4))
        x += size[0] + 12
    sheet.save(ROOT / "docs" / "clock-12-24.png")
    # the almanac's news on the Time 2: a meteor shower's peak, an eclipse of each kind, planets meeting, and
    # Jupiter's moons and the skyline by day up close
    shots = [datetime(2026, 10, 22, 2, 0, tzinfo=NY), datetime(2026, 3, 3, 5, 50, tzinfo=NY),
             datetime(2024, 4, 8, 15, 20, tzinfo=NY), datetime(2026, 6, 8, 21, 40, tzinfo=NY)]
    sheet = Image.new("RGB", (len(shots) * 412, 464 + 220), (24, 24, 26))
    for i, t in enumerate(shots):
        im = Image.fromarray(render(t.astimezone(timezone.utc), t2, sky, NY, "planisphere", False))
        sheet.paste(im.resize((400, 456), Image.NEAREST), (i * 412 + 6, 4))
    jup = datetime(2027, 2, 1, 22, 0, tzinfo=NY).astimezone(timezone.utc)
    im = Image.fromarray(render(jup, t2, sky, NY, "planisphere", False))
    p_ = astro.positions(jup)
    x, y = t2.project(*p_["jupiter"], astro.sidereal(jup, t2.lon))
    sheet.paste(im.crop((int(x) - 30, int(y) - 20, int(x) + 30, int(y) + 20)).resize((300, 200), Image.NEAREST), (6, 474))
    day = Image.fromarray(render(datetime(2026, 10, 14, 12, 15, tzinfo=NY).astimezone(timezone.utc), t2, sky, NY, "planisphere", False))
    sheet.paste(day.crop((40, 178, 160, 218)).resize((600, 200), Image.NEAREST), (318, 474))
    fl = Image.fromarray(render(datetime(2026, 10, 14, 12, 15, tzinfo=NY).astimezone(timezone.utc), r2, sky, NY, "flamsteed", True))
    p_ = astro.positions(datetime(2026, 10, 14, 16, 15, tzinfo=timezone.utc))
    sheet.paste(fl.crop((95, 175, 165, 235)).resize((233, 200), Image.NEAREST), (930, 474))
    sheet.save(ROOT / "docs" / "almanac.png")
    # eclipses: Dallas on 8 April 2024 through totality on the Time 2; the Sun eclipsed at sunset in Burgos on
    # 12 August 2026; the blood Moon over New York on 14 March 2025
    CT, MAD = ZoneInfo("America/Chicago"), ZoneInfo("Europe/Madrid")
    dal, bur = RectDial(200, 228, 32.7767, -96.797), RectDial(200, 228, 42.34, -3.70)
    shots = [(dal, datetime(2024, 4, 8, 13, 20, tzinfo=CT), CT), (dal, datetime(2024, 4, 8, 13, 36, tzinfo=CT), CT),
             (dal, datetime(2024, 4, 8, 13, 40, 25, tzinfo=CT), CT), (dal, datetime(2024, 4, 8, 13, 42, tzinfo=CT), CT),
             (bur, datetime(2026, 8, 12, 20, 29, 30, tzinfo=MAD), MAD), (t2, datetime(2025, 3, 14, 2, 50, tzinfo=NY), NY)]
    sheet = Image.new("RGB", (3 * 412, 2 * 464), (24, 24, 26))
    for i, (dial, t, tz) in enumerate(shots):
        im = Image.fromarray(render(t.astimezone(timezone.utc), dial, sky, tz, "planisphere", False))
        sheet.paste(im.resize((400, 456), Image.NEAREST), ((i % 3) * 412 + 6, (i // 3) * 464 + 4))
    sheet.save(ROOT / "docs" / "eclipses.png")
    # the weather on the Time 2: fair, broken cloud at dusk, overcast, rain; snow, fog, the Moon's halo in thin high
    # cloud, and a frosty night with snow lying
    import weather as wx
    shots = [(datetime(2026, 10, 14, 12, 15, tzinfo=NY), "fair"), (datetime(2026, 10, 14, 18, 25, tzinfo=NY), "cloudy"),
             (datetime(2026, 10, 14, 12, 15, tzinfo=NY), "overcast"), (datetime(2026, 10, 14, 12, 15, tzinfo=NY), "rain"),
             (datetime(2027, 1, 20, 11, 0, tzinfo=NY), "snow"), (datetime(2026, 10, 14, 8, 0, tzinfo=NY), "fog"),
             (datetime(2026, 10, 26, 21, 30, tzinfo=NY), "cirrus"), (datetime(2027, 1, 20, 22, 0, tzinfo=NY), "frost")]
    sheet = Image.new("RGB", (4 * 412, 2 * 464), (24, 24, 26))
    for i, (t, w) in enumerate(shots):
        im = Image.fromarray(render(t.astimezone(timezone.utc), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w],
                                    fahrenheit=True))
        sheet.paste(im.resize((400, 456), Image.NEAREST), ((i % 4) * 412 + 6, (i // 4) * 464 + 4))
    sheet.save(ROOT / "docs" / "weather.png")
    # the year on the Time 2 at eleven in the morning: blossom in April, leaf in July, gold in October, bare twigs
    # and snow in January; below, the village through the year up close
    shots = [(datetime(2026, 4, 22, 11, 0, tzinfo=NY), "fair"), (datetime(2026, 7, 4, 11, 0, tzinfo=NY), "cloudy"),
             (datetime(2026, 10, 14, 11, 0, tzinfo=NY), "fair"), (datetime(2027, 1, 20, 11, 0, tzinfo=NY), "snow")]
    sheet = Image.new("RGB", (4 * 412, 464 + 2 * 172 + 8), (24, 24, 26))
    for i, (t, w) in enumerate(shots):
        im = render(t.astimezone(timezone.utc), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w], fahrenheit=True)
        sheet.paste(Image.fromarray(im).resize((400, 456), Image.NEAREST), (i * 412 + 6, 4))
    village = [(datetime(2026, 4, 22, 12, 0, tzinfo=NY), "fair"), (datetime(2026, 8, 20, 12, 0, tzinfo=NY), "cloudy"),
               (datetime(2026, 10, 24, 12, 0, tzinfo=NY), "fair"), (datetime(2027, 1, 20, 12, 0, tzinfo=NY), "frost"),
               (datetime(2026, 10, 14, 19, 40, tzinfo=NY), "frost"), (datetime(2026, 10, 14, 7, 30, tzinfo=NY), "fog"),
               (datetime(2026, 6, 20, 12, 0, tzinfo=NY), "gale"), (datetime(2027, 1, 20, 22, 0, tzinfo=NY), "frost")]
    for i, (t, w) in enumerate(village):
        im = render(t.astimezone(timezone.utc), t2, sky, NY, "planisphere", False, weather=wx.SAMPLES[w], fahrenheit=True)
        crop = Image.fromarray(im[168:210, 50:150]).resize((400, 168), Image.NEAREST)
        sheet.paste(crop, ((i % 4) * 412 + 6, 464 + 4 + (i // 4) * 172))
    sheet.save(ROOT / "docs" / "seasons.png")
    # the distant hills behind the village catching the light: the drawn hills over New York at noon, as the Sun
    # sets, in the afterglow and at night; then Chamonix's own skyline, the Mont Blanc massif from its terrain, at
    # noon, at sunset, in the afterglow, and on a winter's night
    PAR = ZoneInfo("Europe/Paris")
    cham = RectDial(200, 228, 45.9237, 6.8694)
    shots = [(t2, datetime(2026, 10, 14, 12, 15, tzinfo=NY), NY), (t2, datetime(2026, 10, 14, 18, 10, tzinfo=NY), NY),
             (t2, datetime(2026, 10, 14, 18, 25, tzinfo=NY), NY), (t2, datetime(2026, 10, 14, 21, 30, tzinfo=NY), NY),
             (cham, datetime(2026, 10, 14, 13, 0, tzinfo=PAR), PAR), (cham, datetime(2026, 10, 14, 19, 5, tzinfo=PAR), PAR),
             (cham, datetime(2026, 10, 14, 19, 25, tzinfo=PAR), PAR), (cham, datetime(2027, 1, 20, 22, 0, tzinfo=PAR), PAR)]
    sheet = Image.new("RGB", (4 * 412, 2 * 464), (24, 24, 26))
    for i, (dial, t, tz) in enumerate(shots):
        w = wx.SAMPLES["frost" if t.month == 1 else "fair"]
        im = Image.fromarray(render(t.astimezone(timezone.utc), dial, sky, tz, "planisphere", False, weather=w,
                                    fahrenheit=tz is NY))
        sheet.paste(im.resize((400, 456), Image.NEAREST), ((i % 4) * 412 + 6, (i // 4) * 464 + 4))
    sheet.save(ROOT / "docs" / "mountains.png")
    print(len(frames), "frames")


if __name__ == "__main__":
    main()
