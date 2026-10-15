"""Generate the watch's data from the Python prototype (proto/), so the C draws what the prototype designed.

  watchface/resources/data/plan.bin          the shared data: the hand-drawn pieces (four bits a pixel, the
                                              prototype's roles) and masks (a bit a pixel), the pixel type, the large
                                              time's figures, the star catalogue and the figures' lines, the names,
                                              the Milky Way, the blue-noise tile
  watchface/resources/data/geom~emery.bin    each watch's ring, worked out by the prototype's own geometry: the band's
  watchface/resources/data/geom~gabbro.bin   edges by row, the ticks, beads and studs, where each style's numerals
                                              stand, MIDNIGHT and NOON, the Sun hand's path round the band, the
                                              inscriptions' room, the corner sprigs
  watchface/src/c/plan_data.h                 the sections' numbers, the pieces' names, the plates' colours

Each blob starts with its sections' offsets (uint32, little-endian), each section 4-byte aligned. Colours are
Pebble's GColor8 bytes, 0b11rrggbb.

    uv run python tools/gen_tables.py
"""
import math
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))

import figures                     # noqa: E402
import pixeltext                   # noqa: E402
import plates                      # noqa: E402
import sprites                     # noqa: E402
from render import load_sky        # noqa: E402
from render2 import star_names     # noqa: E402

C_DIR = ROOT / "watchface" / "src" / "c"
RES = ROOT / "watchface" / "resources" / "data"


def g8(c):
    """An RGB colour (0..255 levels of 85) as a GColor8 byte."""
    r, g, b = (int(round(float(v) / 85)) for v in c)
    return 0xC0 | r << 4 | g << 2 | b


def bits(flat):
    """Bools as a bit string, the first in the lowest bit."""
    flat = np.asarray(flat, bool).ravel()
    out = bytearray((len(flat) + 7) // 8)
    for i in np.nonzero(flat)[0]:
        out[i >> 3] |= 1 << (i & 7)
    return bytes(out)


def nibbles(roles):
    """A role drawing (0..15 a pixel) two pixels a byte, the first in the low nibble."""
    flat = np.asarray(roles, np.uint8).ravel()
    if len(flat) % 2:
        flat = np.append(flat, 0)
    return bytes(int(flat[i]) | int(flat[i + 1]) << 4 for i in range(0, len(flat), 2))


def ident(name):
    return name.upper().replace(" ", "_").replace(":", "_").replace("'", "")


class Blob:
    """Sections laid end to end after a table of their offsets."""

    def __init__(self, prefix):
        self.prefix, self.names, self.data = prefix, [], []

    def add(self, name, data):
        self.names.append(name)
        self.data.append(bytes(data))

    def bytes(self):
        n = len(self.data)
        out = bytearray(4 * n)
        for i, d in enumerate(self.data):
            while len(out) % 4:
                out.append(0)
            struct.pack_into("<I", out, 4 * i, len(out))
            out += d
        return bytes(out)

    def enum(self):
        return "enum { " + ", ".join(f"{self.prefix}_{n}" for n in self.names) + f", {self.prefix}_COUNT }};"


# ---- the shared data ------------------------------------------------------------------------------------------------
def moon_drawings():
    out = []
    for _, n in sprites._MOON_BY_LIGHT:
        out.append((f"MOON_{n.upper()}", sprites.moon(n, False)))
        out.append((f"MOON_{n.upper()}_WANING", sprites.moon(n, True)))
    return out


def flame_drawings():
    out, tips = [], []
    for k in range(8):
        a = math.radians(k * 45)
        d, j, i = sprites.flame(math.cos(a) * 10, math.sin(a) * 10)
        out.append((f"FLAME{k}", d))
        tips.append((j, i))
    return out, tips


def village_drawings():
    out = []
    for key, rows in sprites.VILLAGE_PIECES.items():
        out.append(("V_" + ident(key), sprites.art([r.replace("#", "K") for r in rows])))
    return out


def shared(h):
    blob = Blob("SEC")
    # the plates, in the order of plates.PLATES
    names = list(plates.PLATES)
    fields = ["jacket", "ink", "accent", "night", "star", "line", "milky", "label", "const", "planet", "rule"]
    h.append("enum { " + ", ".join(f"PLATE_{n.upper()}" for n in names) + ", PLATE_COUNT };")
    h.append("enum { WIN_SKY, WIN_PAPER, WIN_RED, WIN_ORLOJ };")
    h.append("enum { RING_ROMAN, RING_HOURS, RING_GOTHIC, RING_MINUSCULE };")
    h.append("enum { FIG_MODERN, FIG_COPPERPLATE, FIG_CASLON };")
    h.append("enum { GLYPH_CROSS, GLYPH_RAYS, GLYPH_POINTER, GLYPH_WOODCUT };")
    h.append("enum { CORNER_SEASON, CORNER_IVY, CORNER_FROND };")
    h.append("enum { FILL_HATCH, FILL_COLOUR, FILL_ZONES, FILL_WASH };")
    h.append("/* A plate: its colours (GColor8), and what kind of window, ring, figures, stars and corners it has; fill_c\n"
             " * the ring's flat colour or wash, ring_ink its lettering, fox_c and fox (in 4096ths) the foxing. */")
    h.append("typedef struct {\n  uint8_t " + ", ".join("cons" if f == "const" else f for f in fields) + ";\n"
             "  uint8_t window, ring, figures, glyph, corner, fill, fill_c, ring_ink, fox_c;\n"
             "  uint16_t fox;\n  uint8_t rete, throne, unequal, woodcut, dragon, thread;\n} Plate;")
    rows = []
    for n in names:
        P = plates.PLATES[n]
        win = {"sky": 0, "paper": 1, "red": 2, "orloj": 3}[P["window"]]
        ring = {"roman": 0, "hours": 1, "gothic": 2, "minuscule": 3}[P["ring"]]
        fig = {"modern": 0, "copperplate": 1, "caslon": 2}[P.get("figures", "modern")]
        glyph = {"cross": 0, "rays": 1, "pointer": 2, "woodcut": 3}[P["glyph"]]
        corner = {None: 0, "ivy": 1, "frond": 2}[P.get("corner")]
        rf, wash = P.get("ringfill"), P.get("ringwash")
        if isinstance(rf, np.ndarray):
            fill, fill_c = 1, g8(rf)
        elif isinstance(rf, str) and rf == "zones":
            fill, fill_c = 2, 0
        elif wash is not None:
            fill, fill_c = 3, g8(wash)
        else:
            fill, fill_c = 0, 0
        ring_ink = g8(P.get("ring_ink", P["ink"]))
        fox = P.get("foxing")
        fox_c, fox_n = (g8(fox[0]), int(round(fox[1] * 4096))) if fox else (0, 0)
        vals = [g8(P[f]) for f in fields] + [win, ring, fig, glyph, corner, fill, fill_c, ring_ink, fox_c, fox_n,
                                             int(bool(P.get("rete"))), int(P.get("north") == "throne"),
                                             int(P.get("beads") == "unequal"), int(bool(P.get("woodcut"))),
                                             int(bool(P.get("dragon"))), int(P.get("hand") == "thread")]
        rows.append("  {" + ", ".join(str(v) for v in vals) + f"}},  /* {n} */")
    h.append("static const Plate PLATES[PLATE_COUNT] = {\n" + "\n".join(rows) + "\n};")
    h.append("")

    # role drawings
    drawings = [("STAR0", sprites.STAR[0]), ("STAR1", sprites.STAR[1]), ("STAR2", sprites.STAR[2]),
                ("STAR3", sprites.STAR[3]), ("SUN", sprites.sun_of_may()), ("SUN_HAND", sprites.SUN_HAND),
                ("FLEUR", sprites.FLEUR), ("THRONE", sprites.THRONE), ("LOZENGE", sprites.LOZENGE),
                ("SOUTH_STAR", sprites.SOUTH_STAR), ("STUD", sprites.STUD), ("ZENITH", sprites.ZENITH),
                ("RADIANT", sprites.RADIANT), ("DIAMOND", sprites.DIAMOND), ("PEARL", sprites.PEARL),
                ("DRAGON_HEAD", sprites.DRAGON_HEAD), ("DRAGON_TAIL", sprites.DRAGON_TAIL)]
    drawings += [(f"PLANET_{p.upper()}", sprites.PLANET[p]) for p in ("venus", "jupiter", "mars", "saturn", "mercury")]
    drawings += moon_drawings()
    for k in ("blossom", "leaf", "autumn", "bare"):
        drawings.append((f"CORNER_{k.upper()}", sprites.CORNER_SEASONS[k]))
    drawings += [("CORNER_IVY", sprites.CORNER_IVY), ("CORNER_FROND", sprites.CORNER_FROND)]
    fl, tips = flame_drawings()
    drawings += fl
    drawings += village_drawings()
    drawings += [(f"CUMULUS{i}", sprites.cloud(c)) for i, c in enumerate(sprites.CUMULUS)]
    drawings += [(f"STRATUS{i}", sprites.cloud(c)) for i, c in enumerate(sprites.STRATUS)]
    drawings += [(f"CIRRUS{i}", sprites.stroke(c)) for i, c in enumerate(sprites.CIRRUS)]
    drawings += [("SNOWFLAKE", sprites.SNOWFLAKE)]
    index, data = bytearray(), bytearray()
    for name, a in drawings:
        a = np.asarray(a, np.uint8)
        assert len(data) < 65536 and a.shape[0] < 256 and a.shape[1] < 256
        index += struct.pack("<HBB", len(data), a.shape[1], a.shape[0])
        data += nibbles(a)
    blob.add("DRAW_INDEX", index)
    blob.add("DRAW_DATA", data)
    h.append("enum { " + ", ".join(f"D_{n}" for n, _ in drawings) + ", D_COUNT };")
    h.append("static const uint8_t FLAME_TIP[8][2] = {" + ", ".join(f"{{{j}, {i}}}" for j, i in tips) + "};  /* row, col */")
    h.append("#define MOON_PHASES 7\nstatic const float MOON_BY_LIGHT[MOON_PHASES] = {"
             + ", ".join(f"{b}f" for b, _ in sprites._MOON_BY_LIGHT) + "};")
    seasons = ["bare", "blossom", "leaf", "harvest", "turning", "autumn"]
    h.append("enum { " + ", ".join(f"SEASON_{s.upper()}" for s in seasons) + " };")
    # the village: its pieces by season, where each stands, the hills under it, the distant range behind it
    vrows = []
    for name, at in sprites.VILLAGE_LAYOUT:
        per = []
        for s in seasons:
            variant = sprites.VILLAGE_SEASON.get(s, "")
            key = f"{name}:{variant}" if f"{name}:{variant}" in sprites.VILLAGE_PIECES else name
            per.append("D_V_" + ident(key))
        tree = int(name in sprites.VILLAGE_TREES)
        kind = {"church": 1, "house": 2}.get(name, 0)
        vrows.append(f"  {{{at}, {tree}, {kind}, {{{', '.join(per)}}}}},")
    h.append("typedef struct { int8_t at; uint8_t tree, kind; uint8_t piece[6]; } VillagePiece;  /* kind 1 church, 2 house */")
    h.append(f"#define VILLAGE_PIECES {len(sprites.VILLAGE_LAYOUT)}")
    h.append("static const VillagePiece VILLAGE[VILLAGE_PIECES] = {\n" + "\n".join(vrows) + "\n};")
    h.append(f"#define VILLAGE_HILL_COUNT {len(sprites.VILLAGE_HILLS)}")
    h.append("static const int8_t VILLAGE_HILLS[VILLAGE_HILL_COUNT][2] = {"
             + ", ".join(f"{{{x}, {v}}}" for x, v in sprites.VILLAGE_HILLS) + "};")
    h.append(f"#define DISTANT_COUNT {len(sprites.DISTANT_RANGE)}")
    h.append("static const int8_t DISTANT[DISTANT_COUNT][2] = {"
             + ", ".join(f"{{{x}, {v}}}" for x, v in sprites.DISTANT_RANGE) + "};")
    h.append("")

    # masks
    masks = []
    for i, d in enumerate(sprites.DAY_SIGNS):
        masks.append((f"DAY{i}", sprites.sign(d)))
    for i, z in enumerate(sprites.ZODIAC):
        masks.append((f"ZODIAC{i}", sprites.sign(z)))
    for t in ("III", "VI", "IX"):
        masks.append((f"ROMAN_{t}", sprites.numerals(t)))
    for t in ("3", "6", "9", "15", "18", "21"):
        masks.append((f"FIG_{t}", sprites.figures(t)))
    for t in ("3", "6", "9"):
        masks.append((f"GOTHIC_{t}", sprites.gothic(t)))
    for t in ("iij", "vj", "ix"):
        masks.append((f"SMALL_{t.upper()}", sprites.minuscule(t)))
    needle = list(sprites.NEEDLEWORK)
    for k in needle:
        masks.append((f"NEEDLE_{ident(k)}", sprites.needlework(k)))
    for k in ("h", "m", "deg"):
        masks.append((f"SUP_{k.upper()}", pixeltext.sup(k)))
    masks.append(("LOZENGE_MASK", np.asarray(sprites.LOZENGE) > 0))
    masks.append(("GLORY", sprites.glory() > 0))
    tiny_chars = list(sprites.TINY)
    for i, c in enumerate(tiny_chars):
        masks.append((f"TINY{i}", sprites.tiny(c, 1)))
    for k in ("left", "right", "end"):
        masks.append((f"VANE_{k.upper()}", sprites.sign(sprites.VANE[k])))
    for k in sprites.LABOUR_FIGURES:
        masks.append((f"LABOUR_{ident(k)}", sprites.labour_figure(k)))
    index, flat = bytearray(), []
    bit = 0
    for name, m in masks:
        m = np.asarray(m, bool)
        index += struct.pack("<IBBH", bit, m.shape[1], m.shape[0], 0)
        flat.append(m.ravel())
        bit += m.size
    blob.add("MASK_INDEX", index)
    blob.add("MASK_DATA", bits(np.concatenate(flat)))
    h.append("enum { " + ", ".join(f"M_{n}" for n, _ in masks) + ", M_COUNT };")
    tiny_map = "".join(c if c != "°" else "\\x01" for c in tiny_chars)
    h.append(f'static const char TINY_CHARS[] = "{tiny_map}";  /* \\x01 the degree sign; M_TINY0 onward */')
    h.append("enum { " + ", ".join(f"NW_{ident(k)}" for k in needle) + ", NW_COUNT };")
    # the labours of the months: each side's figure (a mask) and where its copies stand, and the field behind
    grounds = ["snow", "vines", "grass", "stubble", "furrows"]
    h.append("enum { " + ", ".join(f"FIELD_{g.upper()}" for g in grounds) + " };")
    h.append("typedef struct { uint8_t mask, n; int8_t at[3][2]; } LabourFigure;   /* at: dx, dy */")
    h.append("typedef struct { LabourFigure side[2]; uint8_t field; } Labour;      /* left, right */")
    rows = []
    for month in range(1, 13):
        scene = sprites.LABOURS[month]
        sides = []
        for side in ("left", "right"):
            name = scene[side]
            at = sprites.LABOUR_COPIES.get(name, [(0, 0)])
            assert len(at) <= 3
            cells = ", ".join(f"{{{dx}, {dy}}}" for dx, dy in at)
            sides.append(f"{{M_LABOUR_{ident(name)}, {len(at)}, {{{cells}}}}}")
        rows.append(f"  {{{{{sides[0]}, {sides[1]}}}, FIELD_{scene['ground'].upper()}}},")
    h.append("static const Labour LABOURS[12] = {\n" + "\n".join(rows) + "\n};")

    def ids(lst):
        return "{" + ", ".join(f"NW_{ident(k)}" for k in lst) + "}"
    h.append(f"static const uint8_t NW_ANY_TIME[] = {ids(sprites.ANY_TIME)};")
    for s in seasons:
        h.append(f"static const uint8_t NW_{s.upper()}[] = {ids(sprites.OF_SEASON[s])};")
    h.append("static const uint8_t *const NW_OF_SEASON[6] = {" + ", ".join(f"NW_{s.upper()}" for s in seasons) + "};")
    h.append("static const uint8_t NW_OF_SEASON_N[6] = {" + ", ".join(str(len(sprites.OF_SEASON[s])) for s in seasons) + "};")
    weathers = ["thunder", "snow", "rain", "fog", "wind"]
    h.append("enum { WXP_NONE, " + ", ".join(f"WXP_{w.upper()}" for w in weathers) + " };")
    for w in weathers:
        h.append(f"static const uint8_t NW_W_{w.upper()}[] = {ids(sprites.OF_WEATHER[w])};")
    h.append("static const uint8_t *const NW_OF_WEATHER[6] = {0, " + ", ".join(f"NW_W_{w.upper()}" for w in weathers) + "};")
    h.append("static const uint8_t NW_OF_WEATHER_N[6] = {0, " + ", ".join(str(len(sprites.OF_WEATHER[w])) for w in weathers) + "};")
    h.append("")

    # the pixel type: each printable character, 14 rows from column 0, its inked width and its advance
    font = pixeltext.FONT11
    index, flat = bytearray(), []
    bit = 0
    for code in range(32, 127):
        img = Image.new("1", (16, 14), 0)
        d = ImageDraw.Draw(img)
        d.fontmode = "1"
        d.text((0, 0), chr(code), font=font, fill=1)
        m = np.asarray(img, bool)
        cols = np.nonzero(m.any(axis=0))[0]
        w = int(cols.max()) + 1 if len(cols) else 0
        adv = int(round(d.textlength(chr(code), font=font)))
        index += struct.pack("<HBB", bit, w, adv)
        if w:
            flat.append(m[:, :w].ravel())
            bit += 14 * w
    blob.add("GLYPHS", index)
    blob.add("FONT_DATA", bits(np.concatenate(flat)))
    h.append(f"#define FONT_ASC {pixeltext.ASC}\n#define FONT_ROWS 14")

    # the large time's figures: each style on each watch, '0'..'9', then the raised h and m
    index, flat = bytearray(), []
    bit = 0
    for style in ("modern", "copperplate", "caslon"):
        for screen in ("time2", "round2"):
            s = figures.figure_set(style, screen)
            for ch in "0123456789hm":
                m = figures.mask(s[ch])
                base = figures.baseline(style, screen, ch, s[ch])
                index += struct.pack("<IBBBB", bit, m.shape[1], m.shape[0], base, 0)
                flat.append(m.ravel())
                bit += m.size
    blob.add("FIGURE_INDEX", index)
    blob.add("FIGURE_DATA", bits(np.concatenate(flat)))
    widest = []
    for style in ("modern", "copperplate", "caslon"):
        for screen in ("time2", "round2"):
            widest.append([plates.widest_time(style, screen, c24) for c24 in (False, True)])
    h.append("/* the widest the large time can be: [style * 2 + screen][24-hour] */")
    h.append("static const uint8_t WIDEST_TIME[6][2] = {" + ", ".join(f"{{{a}, {b}}}" for a, b in widest) + "};")

    # the stars to magnitude 4.6, faintest first (the order they are drawn): right ascension in 65536ths of a turn,
    # declination in 65535ths of a half turn from the south pole, then the magnitude in hundredths (the catalogue's own
    # precision, so the prototype's thresholds fall the same way) plus 2, times 8, plus the colour's class by B-V
    # (blue-white, white, cream, gold, orange: the prototype's bounds -0.1, 0.5, 1.15, 1.6)
    stars, lines, mw, named = load_sky(4.6)
    order = sorted(range(len(stars)), key=lambda i: -stars[i][2])
    stars = [stars[i] for i in order]
    data = bytearray()
    for ra, dec, mg, bv in stars:
        r = int(round(ra / 360 * 65536)) % 65536
        d = int(round((dec + 90) / 180 * 65535))
        cls = 0 if bv < -0.1 else 1 if bv < 0.5 else 2 if bv < 1.15 else 3 if bv < 1.6 else 4
        m100 = int(round(mg * 100))
        assert -200 <= m100 < 8000 // 8 * 8 - 200
        data += struct.pack("<HHH", r, d, (m100 + 200) << 3 | cls)
    blob.add("STARS", data)
    h.append(f"#define STAR_COUNT {len(stars)}")
    # the figures' lines, between stars of magnitude 3.8 or brighter (as the prototype draws them): star pairs
    where = {}
    for i, (ra, de, mg, bv) in enumerate(stars):
        where.setdefault((round(ra, 2), round(de, 2)), i)
    pairs = []
    for ls in lines:
        for (ra0, de0), (ra1, de1) in zip(ls, ls[1:]):
            a, b = where.get((round(ra0, 2), round(de0, 2))), where.get((round(ra1, 2), round(de1, 2)))
            if a is None or b is None or max(stars[a][2], stars[b][2]) > 3.8:
                continue
            pairs.append((a, b))
    blob.add("LINES", b"".join(struct.pack("<HH", a, b) for a, b in pairs))
    h.append(f"#define LINE_COUNT {len(pairs)}")
    # the bright stars' names (the prototype names up to three, magnitude 1.3 or brighter), brightest first
    nm = star_names()
    rows = []
    for ra, de, mg, bv, hip in sorted(named, key=lambda s: s[2]):
        if mg > 1.3 or hip not in nm:
            continue
        name = nm[hip].encode("ascii", "replace").decode()
        assert len(name) < 16, name
        rows.append(struct.pack("<HH", int(round(ra / 360 * 65536)) % 65536, int(round((de + 90) / 180 * 65535)))
                    + name.encode().ljust(16, b"\0"))
    blob.add("STAR_NAMES", b"".join(rows))
    h.append(f"#define STAR_NAME_COUNT {len(rows)}")
    # the constellations' names, rank 1, in the catalogue's order (the prototype's)
    rows = []
    for name, rank, ra, de in sorted(plates.constellations(), key=lambda c: c[1]):
        if rank > 1:
            continue
        up = name.upper().replace("Ö", "O")
        assert len(up) < 16, up
        rows.append(struct.pack("<HH", int(round(ra / 360 * 65536)) % 65536, int(round((de + 90) / 180 * 65535)))
                    + up.encode().ljust(16, b"\0"))
    blob.add("CONSTELLATIONS", b"".join(rows))
    h.append(f"#define CONSTELLATION_COUNT {len(rows)}")
    # the Milky Way: its level (0 none .. 5 the brightest of d3-celestial's contours) on a 2-degree grid, the cells'
    # middles at odd degrees: 180 in right ascension by 90 in declination, two cells a byte
    # stored by rows of declination, each only where it has any: up to two stretches of right ascension (from a cell,
    # so many cells, running on round through 0), their cells two a byte
    grid = milky_grid(mw, 2.0)
    blob.add("MILKY", milky_rows(grid))
    h.append(f"#define MILKY_LEVELS {len(mw)}\n#define MILKY_STEP 2\n#define MILKY_W 180\n#define MILKY_H 90")
    # the blue-noise tile: each cell's level, 0..255 (the threshold is (level + 0.5) / 256), as render2.bn_tile
    bn = np.load(ROOT / "data" / "bluenoise64.npy")
    ranks = np.round(bn * 4096 - 0.5).astype(np.int64)
    assert sorted(ranks.ravel().tolist()) == list(range(4096))
    blob.add("BLUE_NOISE", bytes(int(v) >> 4 for v in ranks.ravel()))
    h.insert(0, blob.enum())
    return blob


def milky_rows(grid):
    """Each row: its data's offset (u16), then two stretches (start, count; u8 each, count 0 for none); then the
    cells. A row's cells are its stretches' in turn, two a byte, each stretch starting on a fresh byte."""
    H, W = grid.shape
    index, data = bytearray(), bytearray()
    for j in range(H):
        row = grid[j]
        on = [i for i in range(W) if row[i]]
        stretches = []
        if on:
            # the gaps between lit cells, round the circle; keep the two widest as the breaks
            gaps = sorted(((on[(k + 1) % len(on)] - on[k]) % W, k) for k in range(len(on)))[::-1]
            breaks = sorted(k for g, k in gaps[:2] if g > 1) if len(on) > 1 else [0]
            if not breaks:
                stretches = [(0, W)]
            else:
                for n, k in enumerate(breaks):
                    start = on[(k + 1) % len(on)]
                    end = on[breaks[(n + 1) % len(breaks)]]
                    stretches.append((start, (end - start) % W + 1))
        stretches = (stretches + [(0, 0), (0, 0)])[:2]
        index += struct.pack("<HBBBB", len(data), stretches[0][0], stretches[0][1], stretches[1][0], stretches[1][1])
        for start, count in stretches:
            data += nibbles([row[(start + i) % W] for i in range(count)])
        # every lit cell must be in a stretch
        covered = {(s + i) % W for s, c in stretches for i in range(c)}
        assert set(on) <= covered, j
    return index + data


def milky_grid(mw, step):
    """The highest contour level holding each cell's middle, even-odd within a level as the prototype fills it: in
    the chart's polar projection, where the band's edges (two loops round the sky) are closed curves."""
    W, H = int(360 / step), int(180 / step)
    ra = (np.arange(W) + 0.5) * step
    de = -90 + (np.arange(H) + 0.5) * step
    RA, DE = np.meshgrid(ra, de)
    X, Y = polar(RA, DE)
    out = np.zeros((H, W), np.uint8)
    for level, polys in enumerate(mw):
        acc = np.zeros((H, W), bool)
        for poly in polys:
            for ring in poly:
                pts = np.array(ring, float)
                acc ^= inside_ring(X, Y, *polar(pts[:, 0], pts[:, 1]))
        out[acc] = level + 1
    return out


def polar(ra, dec):
    """The north polar equidistant projection (the chart's, up to its scale and turn)."""
    rho = 90.0 - np.asarray(dec, float)
    a = np.radians(np.asarray(ra, float))
    return rho * np.sin(a), rho * np.cos(a)


def inside_ring(x, y, rx, ry):
    """Points inside a closed polygon, even-odd."""
    res = np.zeros(x.shape, bool)
    for i in range(len(rx)):
        x0, y0, x1, y1 = rx[i - 1], ry[i - 1], rx[i], ry[i]
        if y0 == y1:
            continue
        cond = (y0 > y) != (y1 > y)
        xc = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
        res ^= cond & (x < xc)
    return res


# ---- each watch's ring ----------------------------------------------------------------------------------------------
def spans(mask):
    out = []
    for y in range(mask.shape[0]):
        xs = np.nonzero(mask[y])[0]
        if len(xs) == 0:
            out.append((1, 0))
            continue
        assert xs.max() - xs.min() + 1 == len(xs), f"row {y} is broken"
        out.append((int(xs.min()), int(xs.max())))
    return out


def track_from(dial, centre, a_deg, inset, shape=None):
    """plates.track_point, its ray cast from `centre` rather than the pole."""
    a = math.radians(a_deg)
    dx, dy = math.sin(a), math.cos(a)
    cx, cy = centre
    if not getattr(dial, "rect", False):
        r = dial.R - inset
        return dial.cx + r * dx, dial.cy + r * dy
    shape = shape or dial.outline
    lo, hi = 0.0, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if shape.dist(cx + mid * dx, cy + mid * dy)[0] > inset:
            lo = mid
        else:
            hi = mid
    return cx + lo * dx, cy + lo * dy


def geometry(dial, rect):
    """The ring's fixed geometry. What depends on where the pole stands (on the Time 2 it moves with the latitude:
    the hour rays, so the ticks, studs, numerals, the Sun hand's path and the beads' order) the watch works out from
    these: the tracks the rays meet, the beads' track, the inscriptions' walks."""
    blob = Blob("GEO")
    H, W = dial.h, dial.w
    rp = plates.ring_params(dial)
    r_out = rp["out"]
    inner = plates.inner_region(dial)
    outer = plates.ring_shape(dial, r_out)
    outer1 = plates.ring_shape(dial, r_out + 1)
    for label, m in (("OUTER", outer), ("OUTER1", outer1), ("INNER", inner)):
        blob.add(label, b"".join(struct.pack("<hh", a, b) for a, b in spans(m)))
    # the tracks the hour rays meet, each sampled every degree round the screen's middle (1/16 px): the inner edge,
    # the outer rule's inside (r_out + 1), the thread's outer end (r_out + 0.6), the beads' track
    centre = (W / 2, H / 2)
    tracks = bytearray()
    for inset, shape in ((None, "inner"), (r_out + 1, None), (r_out + 0.6, None), (rp["bead"], None)):
        for a in range(360):
            if shape == "inner":
                x, y = (track_from(dial, centre, a, 0.0, dial.inner) if rect
                        else track_from(dial, centre, a, rp["in"]))
            else:
                x, y = track_from(dial, centre, a, inset)
            tracks += struct.pack("<hh", int(round(x * 16)), int(round(y * 16)))
    blob.add("TRACKS", tracks)
    # the beads: every third pixel along their track, traced round the screen's middle (the same at every latitude)
    beads = plates.bead_pixels(dial, rp["bead"])
    blob.add("BEADS", struct.pack("<H", len(beads)) + b"".join(struct.pack("<hh", int(x), int(y)) for y, x in beads))
    # MIDNIGHT and NOON, the lozenges either side, and the inscriptions' walks out from beyond them
    words = {0: "MIDNIGHT", 12: "NOON"}
    index, wbits = bytearray(), []
    bit = 0
    loz = bytearray()
    curves, halves = {}, {}
    for hr, word in words.items():
        m, x0, y0 = sprites.word_art(word, W, H)
        index += struct.pack("<hhBBH", x0, y0, m.shape[1], m.shape[0], bit)
        wbits.append(m.ravel())
        bit += m.size
        top = hr == 0
        curve = plates.band_curve(dial, rp["word"], top)
        curves[top] = curve
        half_w = (sum(len(sprites.CAPS9[ch][0]) for ch in word) + 2 * (len(word) - 1)) / 2
        halves[top] = half_w
        for sgn in (-1, 1):
            lx, ly, _ = curve(sgn * (half_w + 6))
            loz += struct.pack("<hh", int(round(lx * 16)), int(round(ly * 16)))
    blob.add("WORDS", index)
    blob.add("WORD_BITS", bits(np.concatenate(wbits)))
    blob.add("WORD_LOZENGES", loz)
    # each inscription's walk along the band, every half pixel of the curve from its start until the screen's edge
    # (or 140 pixels): the start's x and the count, then the points (x in 1/16 px, the column, the row), each pixel
    # once; a row of -1 ends it
    walks = bytearray()
    for top, side in ((True, -1), (True, 1), (False, -1), (False, 1)):
        curve = curves[top]
        s0 = halves[top] + 6 + 4.5
        pts_, last = [], None
        s1 = s0
        while True:
            x_, y_, _ = curve(side * s1)
            xi_, yi_ = int(math.floor(x_)), int(math.floor(y_))
            if s1 >= 140 or not (0 <= xi_ < W and 3 <= yi_ < H - 3):
                pts_.append((int(round(x_ * 16)), 0, -1))
                break
            if (xi_, yi_) != last:
                pts_.append((int(round(x_ * 16)), xi_, yi_))
                last = (xi_, yi_)
            s1 += 0.5
        xa = curve(side * s0)[0]
        walks += struct.pack("<hh", int(round(xa * 16)), len(pts_)) + b"".join(struct.pack("<hhh", *q) for q in pts_)
    blob.add("WALKS", walks)
    # the word track's height at each column, top and bottom (1/16 px), for the inscriptions' letters
    cy = bytearray()
    for top in (True, False):
        curve = curves[top]
        ss = np.linspace(-200, 200, 8001)
        pts2 = np.array([curve(v)[:2] for v in ss])
        order = np.argsort(pts2[:, 0], kind="stable")
        ys = np.interp(np.arange(W), pts2[order, 0], pts2[order, 1])
        cy += b"".join(struct.pack("<h", int(round(v * 16))) for v in ys)
    blob.add("CURVES", cy)
    corners = bytearray()
    if rect:
        spandrel = dial.outline.grid(W, H) < 0.5
        edge = np.zeros((H, W), bool)
        edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
        croom = np.minimum(plates.clear_distance(~spandrel, most=12), plates.clear_distance(edge, most=12))
        for ys_, xs_ in ((slice(0, H // 2), slice(0, W // 2)), (slice(0, H // 2), slice(W // 2, W)),
                         (slice(H // 2, H), slice(0, W // 2)), (slice(H // 2, H), slice(W // 2, W))):
            r = croom[ys_, xs_]
            j, i = np.unravel_index(np.argmax(r), r.shape)
            corners += struct.pack("<hhhh", xs_.start + int(i), ys_.start + int(j), 1 if r.max() >= 5 else 0, 0)
    else:
        corners += bytes(32)
    blob.add("CORNERS", corners)
    return blob


FEAST_KINDS = ["fixed", "easter", "orthodox", "nth", "after", "window", "advent", "sun", "sidereal", "hebrew",
               "chinese", "islamic", "diwali"]
FEAST_ZONES = ["local", "bj", "ist"]
SPARK_SETS = ["independence", "bonfire", "new year"]


def feasts_blob(h):
    """The calendars' days (proto/feasts.py) for the watch: feasts.bin, a resource the watch reads once a day.

    header   uint16 count, the words' offset, the emblems' offset, the table's size
    records  24 bytes each: uint8 calendar, kind, span, emblem (255 none), flags (FF_*), rank, zone, 0;
             int16 a, b, c (the rule's numbers), 0; uint16 the words (long, short, south's long, south's short;
             65535 none) as offsets into the words
    words    NUL-terminated
    emblems  uint16 count, then each one's offset (from the emblems' start); each emblem uint8 width, height, then
             its pixels row by row, a bit each (the low bit first)"""
    import feasts
    import feast_emblems
    names = [n for n in feast_emblems.EMBLEMS if any(f.get("emblem") == n for f in feasts.FEASTS)]
    words, at = bytearray(), {}

    def word(w):
        if w is None:
            return 0xFFFF
        if w not in at:
            at[w] = len(words)
            words.extend(w.encode("ascii") + b"\0")
        return at[w]
    recs = bytearray()
    for f in feasts.FEASTS:
        rule = f["rule"]
        kind = FEAST_KINDS.index(rule[0])
        a = b = c = 0
        span, zone = 1, 0
        if rule[0] in ("fixed", "hebrew"):
            a, b = rule[1], rule[2]
            span = rule[3] if len(rule) > 3 else 1
        elif rule[0] in ("easter", "orthodox", "advent"):
            a = rule[1]
        elif rule[0] in ("nth", "after", "window"):
            a, b, c = rule[1], rule[2], rule[3]
        elif rule[0] in ("sun", "sidereal"):
            a, zone = rule[1], FEAST_ZONES.index(rule[2])
        elif rule[0] in ("chinese", "islamic"):
            a, b = rule[1], rule[2]
        flags = (1 if "lights" in f.get("brings", ()) else 0) | (2 if "bonfires" in f.get("brings", ()) else 0)
        if f.get("fireworks"):
            flags |= 4 | (SPARK_SETS.index(f["fireworks"]) << 4)
        if f.get("midnight"):
            flags |= 8
        wl = list(f["words"]) + [None] * (2 - len(f["words"]))
        sl = list(f.get("south", (None, None))) + [None] * 2
        emblem = names.index(f["emblem"]) if f.get("emblem") else 255
        if f["rank"] == 1:
            flags |= 64                                     # a great feast: its date in red
        if f.get("emblem") == "hanukkiah":
            flags |= 128                                    # the emblem shows the night's lights
        recs += struct.pack("<8B3hH4H", feasts.CAL[f["cal"]], kind, span, emblem, flags, f["rank"], zone, 0, a, b, c, 0,
                            word(wl[0]), word(wl[1] or wl[0]), word(sl[0]), word(sl[1] or sl[0]) if sl[0] else 0xFFFF)
    n = len(feasts.FEASTS)
    emb = bytearray(struct.pack("<H", len(names)))
    offs, data = [], bytearray()
    for name in names:
        a = np.array([[c == "#" for c in r] for r in feast_emblems.EMBLEMS[name]])   # (the lamp's lights: the watch's)
        h_, w_ = a.shape
        assert w_ <= 16 and h_ + (2 if name == "hanukkiah" else 0) <= 16, name
        offs.append(2 + 2 * len(names) + len(data))
        bits = bytearray((w_ * h_ + 7) // 8)
        for k, v in enumerate(a.ravel()):
            if v:
                bits[k >> 3] |= 1 << (k & 7)
        data += bytes([w_, h_]) + bits
    emb += b"".join(struct.pack("<H", o) for o in offs) + data
    words_at = 8 + len(recs)
    total = 8 + len(recs) + len(words) + len(emb)
    out = struct.pack("<HHHH", n, words_at, words_at + len(words), total) + recs + words + emb
    h.append("enum { " + ", ".join(f"CAL_{k.upper()}" for k, _, _ in feasts.CALENDARS) + ", CAL_COUNT };")
    h.append("enum { " + ", ".join(f"FK_{k.upper()}" for k in FEAST_KINDS) + " };")
    h.append("enum { " + ", ".join(f"FZ_{k.upper()}" for k in FEAST_ZONES) + " };")
    h.append("enum { FF_LIGHTS = 1, FF_BONFIRES = 2, FF_FIREWORKS = 4, FF_MIDNIGHT = 8, FF_RED = 64, FF_NIGHTS = 128 };"
             "   /* sparks: flags >> 4 & 3 */")
    h.append("typedef struct { uint8_t cal, kind, span, emblem, flags, rank, zone, pad; int16_t a, b, c, pad2; "
             "uint16_t words[4]; } FeastRecord;")
    return out


def main():
    h = []
    sh = shared(h)
    feast_bin = feasts_blob(h)
    t2 = plates.RectDial(200, 228, 40.71, -74.01)
    r2 = plates.RoundDial(260, 260, 40.71, -74.01)
    ge, gg = geometry(t2, True), geometry(r2, False)
    assert ge.names == gg.names
    RES.mkdir(parents=True, exist_ok=True)
    blobs = {"plan.bin": sh.bytes(), "geom~emery.bin": ge.bytes(), "geom~gabbro.bin": gg.bytes(), "feasts.bin": feast_bin}
    for name, data in blobs.items():
        (RES / name).write_bytes(data)
    for old in ("geom_emery.bin", "geom_gabbro.bin"):
        (RES / old).unlink(missing_ok=True)
    header = ("/* Generated by tools/gen_tables.py from proto/; do not edit. */\n#pragma once\n#include <stdint.h>\n\n"
              + ge.enum() + "\n" + "\n".join(h) + "\n")
    (C_DIR / "plan_data.h").write_text(header)
    for name, data in blobs.items():
        print(f"{name}: {len(data):,} bytes")
    for old in ("plan_tables.h", "plan_geom.h"):
        (C_DIR / old).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
