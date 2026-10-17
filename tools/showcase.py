"""A showcase reel of the face, drawn by the watch's own C (build/host): the Time 2 beside the Round 2, a caption
under each part. A day over Norfolk; every plate; the scenes behind the face; the constellations shown and the sky
spun, as a flick plays them; a holiday's fireworks; the almanac's days; the weather; meteors and birds; the time gilt
and the battery's candle. Written to out/showcase/showcase.gif (and .mp4, if ffmpeg is about); the README shows it (docs/showcase.gif).

    tools/build-host.sh && cd proto && uv run python ../tools/showcase.py
"""
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

import store_gallery as sg

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "showcase"
HOST = ROOT / "build" / "host"
NORFOLK, NORFOLK_NAME = (36.85, -76.29), ("NORFOLK", "VIRGINIA")
NY = sg.NY
S = 2                                               # (each watch pixel 2 x 2)
BG, INK, DIM = (22, 22, 34), (236, 226, 200), (150, 140, 120)
FONT = ImageFont.truetype(str(ROOT / "fonts" / "IMFeENrm28P.ttf"), 30)
SMALL = ImageFont.truetype(str(ROOT / "fonts" / "IMFeENit28P.ttf"), 22)
NAMES = ["Planisphere", "Burritt", "Flamsteed", "Observatory", "Astrolabe", "Book of Hours", "Orloj", "Cyanotype",
         "Apian", "Night", "Lantern slide", "Shagreen"]


def face(platform, plate, when, place, offset, *extra, city=None):
    """One face as the watch draws it (build/host), with the host's own options after."""
    import names
    path = OUT / f"{platform}.ppm"
    city = city or sg.plates.place_name(*place)
    args = [str(HOST), platform, str(plate), str(int(when.timestamp())), str(place[0]), str(place[1]), str(offset),
            str(path), *map(str, extra)]
    if city and city[0]:
        args += ["--city", names.city_ladder(city[0]), "--country", names.region_ladder("", "", city[1])]
    subprocess.run(args, check=True, capture_output=True)
    return Image.open(path).convert("RGB")


def both(plate, when, place, offset, *extra, city=None):
    return face("emery", plate, when, place, offset, *extra, city=city), \
        face("gabbro", plate, when, place, offset, *extra, city=city)


def card(t2, r2, caption, note=""):
    """The two watches side by side on the dark ground, the Round 2 cut round, the caption beneath."""
    w = 40 + 200 * S + 48 + 260 * S + 40
    out = Image.new("RGB", (w, 30 + 260 * S + 96), BG)
    out.paste(t2.resize((200 * S, 228 * S), Image.NEAREST), (40, 30 + (260 - 228) * S // 2))
    mask = Image.new("L", (260 * S, 260 * S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 260 * S - 1, 260 * S - 1), fill=255)
    out.paste(r2.resize((260 * S, 260 * S), Image.NEAREST), (40 + 200 * S + 48, 30), mask)
    d = ImageDraw.Draw(out)
    d.text((w // 2, 30 + 260 * S + 30), caption, font=FONT, fill=INK, anchor="mm")
    if note:
        d.text((w // 2, 30 + 260 * S + 66), note, font=SMALL, fill=DIM, anchor="mm")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, times = [], []

    def add(im, ms):
        frames.append(im), times.append(ms)

    # a winter's day over Norfolk, noon to noon, the labours of the months in the card
    start = sg.local(2026, 12, 20, 12, 0, -300)
    for k in range(0, 24 * 60, 15):
        when = start + timedelta(minutes=k)
        t2, r2 = both(0, when, NORFOLK, -300, "--labours", city=NORFOLK_NAME)
        add(card(t2, r2, "A day over Norfolk", "the sky as it is, for where you are"), 70)
    # every plate, at half past seven of a December evening
    when = sg.local(2026, 12, 20, 19, 30, -300)
    for i, name in enumerate(NAMES):
        t2, r2 = both(i, when, NORFOLK, -300, city=NORFOLK_NAME)
        add(card(t2, r2, name, "twelve plates, after old star charts and almanacs"), 700)
    # the scenes behind the face, with their corners on the Time 2
    for theme, name in [(1, "The labours of the months"), (2, "The zodiac"), (3, "The astronomer"), (4, "The sea"),
                        (5, "The herbal")]:
        plate = [0, 2, 8, 1, 11][theme - 1]
        t2, r2 = both(plate, when, NORFOLK, -300, "--theme", theme, "--corners", theme, city=NORFOLK_NAME)
        add(card(t2, r2, name, "a woodcut in the card, and in the corners"), 1100)
    # the constellations, as a flick shows them: out from the pole and back, at midday under a grey sky
    noon, grey = sg.local(2026, 12, 21, 11, 40, -300), "3,40,100,90,60,4,200,1008,0,800"
    base = both(0, noon, NORFOLK, -300, "--weather", grey, city=NORFOLK_NAME)
    chart = both(0, noon, NORFOLK, -300, "--weather", grey, "--chart", 0, city=NORFOLK_NAME)
    steps = [both(0, noon, NORFOLK, -300, "--weather", grey, "--chart", 0, "--reveal", k, city=NORFOLK_NAME)
             for k in (48, 96, 144, 192, 240)]
    cap, note = "Flick for the constellations", "whatever the hour or the weather"
    add(card(*base, cap, note), 900)
    for s in steps:
        add(card(*s, cap, note), 90)
    add(card(*chart, cap, note), 2200)
    for s in steps:                                 # (back: the face out from the pole over the chart, as far as the
        back = [Image.composite(b, c, ImageChops.difference(st, c).convert("L").point(lambda v: 255 if v == 0 else 0))
                for st, b, c in zip(s, base, chart)]  # chart had come in: the face where the step showed the chart)
        add(card(*back, cap, note), 90)
    add(card(*base, cap, note), 700)
    # the sky spun a day round, as the other flick plays it
    turns = [-356, -345, -327, -304, -277, -246, -214, -180, -146, -114, -83, -56, -33, -15, -4]
    day = sg.local(2026, 12, 21, 10, 0, -300)
    add(card(*both(0, day, NORFOLK, -300, city=NORFOLK_NAME), "Or spin the sky a day round", "and home to the hour"), 600)
    for t in turns:
        add(card(*both(0, day, NORFOLK, -300, "--turn", t, "--window-only", city=NORFOLK_NAME),
                 "Or spin the sky a day round", "and home to the hour"), 110)
    add(card(*both(0, day, NORFOLK, -300, city=NORFOLK_NAME), "Or spin the sky a day round", "and home to the hour"), 700)
    # New Year's fireworks over New York, as the watch plays them
    eve = sg.local(2027, 1, 1, 0, 0, -300)
    for k in range(0, 99, 2):
        add(card(*both(9, eve, NY, -300, "--calendars", 64, "--show", k), "Fireworks on the holidays",
                 "the almanac keeps twelve calendars"), 80)
    # the almanac's days
    for plate, when, place, offset in sg.FEASTS[:6]:
        add(card(*both(sg.PLATE[plate], when, place, offset, "--calendars", sg.ALL), "The almanac's days",
                 "Christmas Eve, Diwali, Qixi, Hanukkah, the Mid-Autumn moon, St John's fires"), 800)
    # the weather
    when = sg.local(2026, 12, 20, 15, 0, -300)
    for kind in ["fair", "cloudy", "rain", "snow", "fog", "thunder"]:
        s = sg.meteo.SAMPLES[kind]
        w = ",".join(str(int(round(v))) for v in (s.temp * 10, s.code, s.low * 100, s.mid * 100, s.high * 100, s.wind,
                                                    s.wind_from, s.pressure, s.snow_depth * 1000, s.visibility / 10))
        add(card(*both(0, when, NORFOLK, -300, "--weather", w, city=NORFOLK_NAME), "The weather, in the sky",
                 kind), 650)
    # meteors on the Geminids' night, and birds at twilight
    for kind, start, cap in [(1, sg.local(2026, 12, 13, 23, 0, -300), "Meteors on a shower's night"),
                             (4, sg.local(2026, 10, 18, 17, 50, -240), "Birds crossing at twilight")]:
        off = -300 if kind == 1 else -240
        for at, n in sg.event_minutes("emery", start, NORFOLK, off, kind, 3 if kind == 1 else 1):
            for k in range(0, n + 1, 1 if kind == 1 else 2):
                t2 = face("emery", 0, at, NORFOLK, off, "--events", kind, "--event-frame", k, city=NORFOLK_NAME)
                r2 = face("gabbro", 0, at, NORFOLK, off, "--events", kind, "--event-frame", k, city=NORFOLK_NAME)
                add(card(t2, r2, cap, "now and then, as the sky brings them"), 110 if kind == 1 else 70)
    # the time gilt, and the battery's candle
    when = sg.local(2026, 12, 20, 21, 10, -300)
    for plate in (0, 10, 11):
        add(card(*both(plate, when, NORFOLK, -300, "--gild", "--battery", 64, city=NORFOLK_NAME),
                 "The time gilt, and a candle clock", "for the battery, if you like"), 1100)
    # the end card
    end = Image.new("RGB", frames[0].size, BG)
    d = ImageDraw.Draw(end)
    d.text((end.width // 2, end.height // 2 - 40), "Planisphere", font=ImageFont.truetype(
        str(ROOT / "fonts" / "IMFeENrm28P.ttf"), 64), fill=INK, anchor="mm")
    d.text((end.width // 2, end.height // 2 + 30), "for the Pebble Time 2 and Round 2", font=FONT, fill=DIM,
           anchor="mm")
    add(end, 2500)

    pal = [im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for im in frames]
    gif = OUT / "showcase.gif"
    pal[0].save(gif, save_all=True, append_images=pal[1:], duration=times, loop=0, optimize=True)
    print(f"{gif}: {len(frames)} frames, {sum(times) / 1000:.1f} s, {gif.stat().st_size / 1e6:.1f} MB")
    if shutil.which("ffmpeg"):                      # the same as a video, for sites that take one
        mp4 = OUT / "showcase.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(gif), "-movflags", "faststart",
                        "-pix_fmt", "yuv420p", "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2:flags=neighbor",
                        "-crf", "18", str(mp4)], check=True)
        print(f"{mp4}: {mp4.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
