"""Hand-drawn pixel art for the planisphere. Every piece is drawn pixel by pixel
as text below (the Sun's rays drawn for one eighth of the circle and turned
round it, so they are exactly symmetric), never generated from shapes.

Roles in the drawings:  .  nothing   K  ink   R  red   Y  gold   O  deep gold
                        W  light     M  the sky's ground, kept clear  S  silver
"""
import math

import numpy as np

ROLE = {".": 0, "K": 1, "R": 2, "Y": 3, "O": 4, "W": 5, "M": 6, "S": 7}


def art(rows):
    return np.array([[ROLE[c] for c in r] for r in rows], np.uint8)


def mirror_h(rows):
    """A drawing and its mirror image side by side (the middle column shared): for left-right symmetry."""
    return [r + r[-2::-1] for r in rows]


# ---- the Sun with a face, after the Sun of May ------------------------------------------------
# one eighth of the rays, from straight up turning toward the upper right (x right, y up), at the
# distances that clear the disc; the other seven eighths are mirror images of it: sixteen rays, straight
# and flaming in turn, as on the Sun of May
_RAYS_STRAIGHT = [(0, 7), (0, 8), (0, 9), (0, 10), (0, 11)]                         # up
_RAYS_DIAGONAL = [(5, 5), (6, 6), (7, 7), (8, 8)]                                   # to the corner
_RAYS_WAVY = [(3, 7), (4, 8), (3, 9), (4, 10)]                                     # a flame, halfway between


def _eightfold(points):
    out = set()
    for x, y in points:
        for a, b in ((x, y), (y, x)):
            for sx in (1, -1):
                for sy in (1, -1):
                    out.add((sx * a, sy * b))
    return out


_FACE = [                         # the disc's inside, x -4..4, y -4..4 (rows top to bottom); drawn by hand:
    "..YYYYY..",                  # a serene face: brows, almond eyes, a long nose, a small mouth
    ".YOOYOOY.",
    "YYYYYYYYY",
    "YOKYYYKOY",
    "YYYYOYYYY",
    "YYYYOYYYY",
    "YWYYYYYWY",
    ".YYOOOYY.",
    "..YYYYY..",
]
_DISC = [                         # radius 5: the outline of a true pixel circle
    (-2, -5), (-1, -5), (0, -5), (1, -5), (2, -5), (-3, -4), (3, -4), (-4, -3), (4, -3),
    (-5, -2), (5, -2), (-5, -1), (5, -1), (-5, 0), (5, 0), (-5, 1), (5, 1), (-5, 2), (5, 2),
    (-4, 3), (4, 3), (-3, 4), (3, 4), (-2, 5), (-1, 5), (0, 5), (1, 5), (2, 5)]


def sun_of_may():
    n, c = 25, 12
    a = np.zeros((n, n), np.uint8)
    for x, y in _eightfold(_RAYS_STRAIGHT + _RAYS_DIAGONAL):
        a[c - y, c + x] = ROLE["Y"]
    for x, y in _eightfold(_RAYS_WAVY):
        a[c - y, c + x] = ROLE["O"]
    for j, row in enumerate(_FACE):
        for i, ch in enumerate(row):
            if ch != ".":
                a[c - 4 + j, c - 4 + i] = ROLE[ch]
    for x, y in _DISC:
        a[c + y, c + x] = ROLE["O"]
    return a


LITTLE_SUN = art([               # the Sun's pointer on the ring: a disc and eight rays
    "...Y...",
    ".Y.Y.Y.",
    "..OOO..",
    "YYOYOYY",
    "..OOO..",
    ".Y.Y.Y.",
    "...Y...",
])

# ---- the Moon in eight phases, lit side to the right while it waxes ----------------------------
# W the lit face, K the outline and the engraver's hatching on the dark part, M the dark ground
_MOON_LIT = {                    # per row (y -4..4) the leftmost lit x of the inside (x -4..4), by phase
    1: [3, 3, 2, 2, 2, 2, 2, 3, 3],          # a crescent
    2: [0, 0, 0, 0, 0, 0, 0, 0, 0],          # first quarter
    3: [-2, -3, -3, -3, -3, -3, -3, -3, -2],  # gibbous
}


def moon(phase):
    """phase 0 new, 1 crescent, 2 first quarter, 3 gibbous, 4 full, 5..7 waning (the mirror of 3..1)."""
    waning = phase > 4
    p = 8 - phase if waning else phase
    a = np.zeros((11, 11), np.uint8)
    c = 5
    for x, y in _DISC:
        a[c + y, c + x] = ROLE["K"]
    inner = {-4: 2, -3: 3, -2: 4, -1: 4, 0: 4, 1: 4, 2: 4, 3: 3, 4: 2}
    for y in range(-4, 5):
        for x in range(-inner[y], inner[y] + 1):
            if p == 4:
                lit = True
            elif p == 0:
                lit = False
            else:
                lit = x >= _MOON_LIT[p][y + 4]
            if lit:
                a[c + y, c + x] = ROLE["W"]
            else:
                a[c + y, c + x] = ROLE["K"] if (x + y) % 2 == 0 else ROLE["M"]
    return a[:, ::-1] if waning else a


# ---- stars, by brightness; and the planets' little pictures --------------------------------------
STAR = [
    art(["...W...",                # the brightest: eight points
         ".W.W.W.",
         "..WWW..",
         "WWWWWWW",
         "..WWW..",
         ".W.W.W.",
         "...W..."]),
    art(["..W..",                  # first magnitude: four long points
         "..W..",
         "WWWWW",
         "..W..",
         "..W.."]),
    art([".W.",                    # second: a small cross
         "WWW",
         ".W."]),
    art(["W"]),                    # third and fainter: a point
]
PLANET = {
    "saturn": art(["...YYY...",     # the globe and its ring, reaching out past it
                   "..YYYYY..",
                   "KKKKKKKKK",
                   "..YYYYY..",
                   "...YYY..."]),
    "jupiter": art([".WWW.",        # banded
                    "OOOOO",
                    "WWWWW",
                    "OOOOO",
                    ".WWW."]),
    "mars": art([".R.",
                 "RRR",
                 ".R."]),
    "venus": art(["..W..",          # the brightest planet, sparkling
                  ".WWW.",
                  "WWYWW",
                  ".WWW.",
                  "..W.."]),
    "mercury": art([".S.",
                    "SSS",
                    ".S."]),
}

# ---- ornaments: a fleur-de-lis for the north, lozenges for east and west -------------------------
FLEUR = art(mirror_h([          # the left half and the middle column; the right is its mirror
    "......R",                  # the middle petal, a lance
    ".....RR",
    ".....RR",
    "....RRR",
    "....RRR",
    ".RR..RR",                  # the side petals rise from the band and curl over, tips hanging out
    "R.RR.RR",
    "R..RRRR",
    "....RRR",
    "...KKKK",                  # the band
    "...R.RR",                  # below it, the feet curling out and the middle point
    "..R...R",
]))
CORNER = art([                  # a compass star for the Time 2's corners, as a printer finishes a border
    "...R...",
    "...R...",
    "..RKR..",
    "RRK.KRR",
    "..RKR..",
    "...R...",
    "...R...",
])
LOZENGE = art([
    "..R..",
    ".RKR.",
    "RK.KR",
    ".RKR.",
    "..R..",
])

# ---- the ring's words, MIDNIGHT and NOON: larger roman capitals, thick stems and thin hairlines with serifs
# (9 rows), drawn upright here; the faces draw them turned along the ring from the finished art in WORDS
CAPS9 = {
    "M": ["##.......##",
          ".##.....##.",
          ".###...###.",
          ".#.##.##.#.",
          ".#.##.##.#.",
          ".#..###..#.",
          ".#...#...#.",
          ".#.......#.",
          "###.....###"],
    "I": ["####",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          ".##.",
          "####"],
    "D": ["######..",
          ".##..##.",
          ".##...##",
          ".##...##",
          ".##...##",
          ".##...##",
          ".##...##",
          ".##..##.",
          "######.."],
    "N": ["##....###",
          ".##....#.",
          ".###...#.",
          ".#.##..#.",
          ".#..##.#.",
          ".#...###.",
          ".#....##.",
          ".#.....#.",
          "###....#."],
    "G": ["..#####.",
          ".##...##",
          "##.....#",
          "##......",
          "##..####",
          "##....##",
          "##....##",
          ".##..##.",
          "..####.."],
    "H": ["####.####",
          ".##...##.",
          ".##...##.",
          ".##...##.",
          ".#######.",
          ".##...##.",
          ".##...##.",
          ".##...##.",
          "####.####"],
    "T": ["##########",
          "#...##...#",
          "....##....",
          "....##....",
          "....##....",
          "....##....",
          "....##....",
          "....##....",
          "...####..."],
    "O": ["..####..",
          ".##..##.",
          "##....##",
          "##....##",
          "##....##",
          "##....##",
          "##....##",
          ".##..##.",
          "..####.."],
}


# the finished curved words, drawn by hand for each screen's ring: (word, screen width, height) ->
# (left, top, rows), the rows' top-left pixel on the screen; filled in below the drawings' section
WORDS = {}


def word_art(word, W, H):
    a = WORDS.get((word, W, H))
    if a is None:
        return None
    x0, y0, rows = a
    return np.array([[c == "#" for c in r] for r in rows]), x0, y0


# narrower numerals for the ring's band: V and X five pixels wide, with their serifs
NUMERALS = {
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "V": ["##.##", "#...#", "#...#", ".#.#.", ".#.#.", "..#..", "..#.."],
    "X": ["##.##", ".#.#.", ".#.#.", "..#..", ".#.#.", ".#.#.", "##.##"],
}


def numerals(text, gap=1):
    glyphs = [np.array([[c == "#" for c in r] for r in NUMERALS[ch]]) for ch in text]
    W = sum(g.shape[1] for g in glyphs) + gap * (len(glyphs) - 1)
    out = np.zeros((7, W), bool)
    x = 0
    for g in glyphs:
        out[:, x: x + g.shape[1]] = g
        x += g.shape[1] + gap
    return out


def paint(img, a, x, y, colours, anchor="centre", where=None):
    """Paint drawing `a` (roles) at (x, y) with colours by role; roles without a colour are skipped."""
    h, w = a.shape
    x0, y0 = (int(round(x - (w - 1) / 2)), int(round(y - (h - 1) / 2))) if anchor == "centre" else (int(x), int(y))
    H, W_ = img.shape[:2]
    for j in range(h):
        for i in range(w):
            v = int(a[j, i])
            yy, xx = y0 + j, x0 + i
            if v and v in colours and colours[v] is not None and 0 <= yy < H and 0 <= xx < W_ and (where is None or where[yy, xx]):
                img[yy, xx] = colours[v]


# ---- the finished curved words (each drawn pixel by pixel for its screen's ring) -------------------------
WORDS[("MIDNIGHT", 200, 228)] = (61, 5, [
    "..............................##....###..####.................................",
    ".............####..######......##....#....##.....#####...####.####............",
    ".........##...##....##..##.....###...#....##....##...##...##...##...####......",
    "##......##....##....##...##....#.##..#....##...##.....#...##...##...#...######",
    ".###...###....##....##...##....#..##.#....##...##.........##...##.......##...#",
    ".#.##..###....##.....##...##...#...###....##...##..####...#######.......##....",
    ".#..##.#..#....##....##...##...#....##....##...##....##..##...##.......##.....",
    "..#..###..#....##....##...##...#.....#....##...##....##..##...##.......##.....",
    "..#...#...#....##....##..##...###....#...####...##..##...##...##.......##.....",
    "..#.......#...####..######.......................####...####.####......##.....",
    "..#......###..........................................................###.....",
    ".###...................................................................###....",
])
WORDS[("NOON", 200, 228)] = (80, 213, [
    ".##....###....................##....###",
    "..##....#....####......####....##....#.",
    "..###...#...##..##....##..##...###...#.",
    "..#.##..#..##....##..##....##..#.##..#.",
    "..#..##.#..##....##..##....##..#..##.#.",
    ".#...###...##....##..##....##...#...###",
    ".#....##...##....##..##....##...#....##",
    ".#.....#...##....##..##....##...#.....#",
    "###....#....##..##....##..##...###....#",
    ".............####......####............",
])
WORDS[("MIDNIGHT", 260, 260)] = (91, 4, [
    "..............................##....###..####.................................",
    "...................######......##....#....##....#####.........................",
    "....................##..##.....###...#....##...##...##...####.................",
    ".............####...##...##....#.##..#....##..##.....#....##..####............",
    ".........##...##....##...##....#..##.#....##..##..........##..##....###.......",
    ".......###....##.....##...##...#...###....##..##..####....##..##....#..###....",
    "##.....###.....##....##...##...#....##....##..##....##...#######........######",
    ".###...##.#....##....##...##...#.....#....##..##....##...##...##........##...#",
    ".#.##..#..#....##....##..##...###....#...####..##..##....##...##.......##.....",
    "..#.##.#..#....##...######......................####.....##..##........##.....",
    "..#..###...#..####......................................####.##........##.....",
    "..#...#....#.................................................####.....##......",
    "...#......###........................................................###......",
    "...#..................................................................###.....",
    "..###.........................................................................",
])
WORDS[("NOON", 260, 260)] = (110, 246, [
    ".##....###....................##....###",
    "..##....#....####......####....##....#.",
    "..###...#...##..##....##..##...###...#.",
    "..#.##..#..##....##..##....##..#.##..#.",
    "..#..##.#..##....##..##....##..#..##.#.",
    ".#...###...##....##..##....##...#...###",
    ".#....##...##....##..##....##...#....##",
    ".#.....#...##....##..##....##...#.....#",
    "###....#....##..##....##..##...###....#",
    ".............####......####............",
])


if __name__ == "__main__":
    # every drawing on one sheet, at 6x with its pixel grid and at 1x beneath: docs/pieces.png
    from pathlib import Path
    from PIL import Image, ImageDraw
    ROOT = Path(__file__).resolve().parents[1]
    S = 6
    cream, sky, ink_, red = (255, 255, 170), (0, 0, 85), (0, 0, 0), (170, 0, 0)
    gold = {1: (0, 0, 0), 2: red, 3: (255, 170, 0), 4: (170, 85, 0), 5: (255, 255, 170), 6: None, 7: (170, 170, 170)}

    def block(a, colours, ground):
        h, w = a.shape
        img = np.zeros((h + 2, w + 2, 3)) + ground
        paint(img, a, 1, 1, colours, anchor="corner")
        return img

    def mask_block(m, colour, ground):
        img = np.zeros((m.shape[0] + 2, m.shape[1] + 2, 3)) + ground
        img[1:-1, 1:-1][m] = colour
        return img

    rows = [
        [block(sun_of_may(), gold, cream), block(LITTLE_SUN, gold, cream), block(FLEUR, gold, cream),
         block(LOZENGE, gold, cream), block(CORNER, gold, cream)]
        + [mask_block(numerals(t), ink_, cream) for t in ("III", "VI", "IX")],
        [block(moon(i), {1: (85, 85, 85), 5: (255, 255, 170), 6: None}, sky) for i in range(8)]
        + [block(st, {5: (255, 255, 255)}, sky) for st in STAR]
        + [block(PLANET[k], {1: (170, 85, 0), 2: (255, 85, 0), 3: (255, 170, 0), 4: (170, 85, 0), 5: (255, 255, 170),
                             7: (170, 170, 170)}, sky) for k in ("saturn", "jupiter", "mars", "venus", "mercury")],
        [mask_block(word_art(w, 200, 228)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
        [mask_block(word_art(w, 260, 260)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
    ]
    labels = ["The Sun after the Sun of May, its pointer, the fleur-de-lis, lozenge, compass star, numerals",
              "The Moon's eight phases, the stars by brightness, Saturn, Jupiter, Mars, Venus, Mercury",
              "MIDNIGHT and NOON along the Time 2's ring", "MIDNIGHT and NOON along the Round 2's ring"]
    tiles = []
    for r, label in zip(rows, labels):
        h = max(t.shape[0] for t in r)
        big = Image.new("RGB", (sum(t.shape[1] * S + 12 for t in r), h * S + h + 34), (40, 40, 44))
        x = 0
        for t in r:
            im = Image.fromarray(t.astype(np.uint8))
            g = np.asarray(im.resize((im.width * S, im.height * S), Image.NEAREST)).copy()
            g[::S] = (g[::S] * 0.85).astype(np.uint8)
            g[:, ::S] = (g[:, ::S] * 0.85).astype(np.uint8)
            big.paste(Image.fromarray(g), (x, 22))
            big.paste(im, (x, 22 + h * S + 6))
            x += t.shape[1] * S + 12
        ImageDraw.Draw(big).text((2, 4), label, fill=(220, 220, 220))
        tiles.append(big)
    W = max(t.width for t in tiles)
    sheet = Image.new("RGB", (W, sum(t.height + 10 for t in tiles)), (40, 40, 44))
    y = 0
    for t in tiles:
        sheet.paste(t, (0, y)); y += t.height + 10
    sheet.save(ROOT / "docs" / "pieces.png")
    print("ok", sheet.size)
