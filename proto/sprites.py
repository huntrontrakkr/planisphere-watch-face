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

# ---- the Moon in its phases, drawn waxing (lit on the right); waning is the mirror -----------------------
# W the lit face, reaching the limb; K the limb on the dark side; d the dark face, hatched by the engraver
# (every other pixel). The terminator curves as it does on the real Moon: a crescent's inner edge bows the
# same way as the limb, so the horns thin to points; a gibbous Moon's bows the other way.
MOON_PHASES = {
    "new": ["...KKKKK...",
            "..KdddddK..",
            ".KdddddddK.",
            "KdddddddddK",
            "KdddddddddK",
            "KdddddddddK",
            "KdddddddddK",
            "KdddddddddK",
            ".KdddddddK.",
            "..KdddddK..",
            "...KKKKK..."],
    "thin": ["...KKKKW...",     # a young crescent, a seventh lit
             "..KdddddW..",
             ".KdddddddW.",
             "KddddddddWW",
             "KddddddddWW",
             "KddddddddWW",
             "KddddddddWW",
             "KddddddddWW",
             ".KdddddddW.",
             "..KdddddW..",
             "...KKKKW..."],
    "crescent": ["...KKKKW...",
                 "..KddddWW..",
                 ".KdddddWWW.",
                 "KdddddddWWW",
                 "KdddddddWWW",
                 "KdddddddWWW",
                 "KdddddddWWW",
                 "KdddddddWWW",
                 ".KdddddWWW.",
                 "..KddddWW..",
                 "...KKKKW..."],
    "quarter": ["...KKKWW...",
                "..KdddWWW..",
                ".KddddWWWW.",
                "KdddddWWWWW",
                "KdddddWWWWW",
                "KdddddWWWWW",
                "KdddddWWWWW",
                "KdddddWWWWW",
                ".KddddWWWW.",
                "..KdddWWW..",
                "...KKKWW..."],
    "gibbous": ["...KKWWW...",
                "..KdWWWWW..",
                ".KddWWWWWW.",
                "KddWWWWWWWW",
                "KddWWWWWWWW",
                "KddWWWWWWWW",
                "KddWWWWWWWW",
                "KddWWWWWWWW",
                ".KddWWWWWW.",
                "..KdWWWWW..",
                "...KKWWW..."],
    "fat": ["...KWWWW...",       # nearly full: a sliver of dark on the left
            "..KWWWWWW..",
            ".KWWWWWWWW.",
            "KdWWWWWWWWW",
            "KdWWWWWWWWW",
            "KdWWWWWWWWW",
            "KdWWWWWWWWW",
            "KdWWWWWWWWW",
            ".KWWWWWWWW.",
            "..KWWWWWW..",
            "...KWWWW..."],
    "full": ["...WWWWW...",      # full, with the face the almanacs give it, in a quiet line
             "..WWWWWWW..",
             ".WWSSWSSWW.",
             "WWWWWWWWWWW",
             "WWWSWWWSWWW",
             "WWWWWSWWWWW",
             "WWWWWSWWWWW",
             "WWWWWWWWWWW",
             ".WWWSSSWWW.",
             "..WWWWWWW..",
             "...WWWWW..."],
}
# which drawing for how much of the face is lit (its illuminated fraction), up to each bound
_MOON_BY_LIGHT = [(0.04, "new"), (0.22, "thin"), (0.40, "crescent"), (0.60, "quarter"), (0.78, "gibbous"),
                  (0.96, "fat"), (1.01, "full")]


def moon(name, waning=False):
    """The Moon drawn in phase `name` (MOON_PHASES), lit on the right; waning, the mirror (lit on the left)."""
    rows = MOON_PHASES[name]
    a = np.zeros((len(rows), len(rows[0])), np.uint8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == "d":
                a[y, x] = ROLE["K"] if (x + y) % 2 == 0 else ROLE["M"]
            else:
                a[y, x] = ROLE[ch]
    return a[:, ::-1] if waning else a


def moon_for(lit, waxing):
    """The drawing for a Moon with fraction `lit` of its face lit, waxing or waning."""
    name = next(n for bound, n in _MOON_BY_LIGHT if lit < bound)
    return moon(name, waning=not waxing)


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


# ---- the signs of the zodiac, set along the ecliptic in the window, Aries first (7 x 7) ----------------------
ZODIAC = [
    [".##.##.", "#..#..#", "#..#..#", "...#...", "...#...", "...#...", "...#..."],     # Aries
    ["#.....#", ".#...#.", "..###..", ".#...#.", ".#...#.", ".#...#.", "..###.."],     # Taurus
    ["#######", ".#...#.", ".#...#.", ".#...#.", ".#...#.", ".#...#.", "#######"],     # Gemini
    [".#####.", "#.....#", "##.....", ".......", ".....##", "#.....#", ".#####."],     # Cancer
    ["..###..", ".#...#.", ".#...#.", "##...#.", "#.#..#.", "##...#.", ".....##"],     # Leo
    ["##.#...", "#.#.#..", "#.#.#.#", "#.#.###", "#.#.#.#", "#.#.##.", "....#.."],     # Virgo
    ["..###..", ".#...#.", ".#...#.", "##...##", ".......", "#######", "......."],     # Libra
    ["##.#...", "#.#.#..", "#.#.#..", "#.#.#..", "#.#.#.#", "....#.#", ".....##"],     # Scorpio
    ["...####", ".....##", "..#.#.#", "...#...", "..#.#..", ".#.....", "#......"],     # Sagittarius
    ["#...#..", ".#.#.#.", ".#.#..#", "..#..##", "..#.#.#", "..#.##.", "...#..."],     # Capricorn
    [".......", "..#...#", ".#.#.#.", "#...#..", "..#...#", ".#.#.#.", "#...#.."],     # Aquarius
    ["#.....#", ".#...#.", ".#...#.", "#######", ".#...#.", ".#...#.", "#.....#"],     # Pisces
]

# ---- the planet that rules each day of the week, as the almanacs mark the days, Monday first (7 x 7) ---------
DAY_SIGNS = [
    [".###...", "...##..", "....##.", "....##.", "....##.", "...##..", ".###..."],     # the Moon, Monday
    ["...####", ".....##", ".###.#.", "#...#..", "#...#..", "#...#..", ".###..."],     # Mars, Tuesday
    [".#...#.", "..###..", ".#...#.", "..###..", "...#...", ".#####.", "...#..."],     # Mercury, Wednesday
    [".##..#.", "#..#.#.", "...#.#.", "..#..#.", ".#...#.", "#######", ".....#."],     # Jupiter, Thursday
    ["..###..", ".#...#.", ".#...#.", "..###..", "...#...", ".#####.", "...#..."],     # Venus, Friday
    [".#.....", "###....", ".#.##..", ".##..#.", ".#...#.", ".....#.", "....#.."],     # Saturn, Saturday
    ["..###..", ".#...#.", "#.....#", "#..#..#", "#.....#", ".#...#.", "..###.."],     # the Sun, Sunday
]


def sign(rows):
    return np.array([[c == "#" for c in r] for r in rows])


# ---- small marks: the south point's star, the studs on the ring at every third hour, a meteor shower's radiant
SOUTH_STAR = art([
    "..R..",
    "..R..",
    "RR.RR",
    "..R..",
    "..R..",
])
DIAMOND = art([                 # the diamond ring's diamond: the Sun's last light at the Moon's edge
    "....W....",
    "....W....",
    "....W....",
    "...WWW...",
    "WWWWWWWWW",
    "...WWW...",
    "....W....",
    "....W....",
    "....W....",
])
ZENITH = art([                  # the point overhead: a small cross turned on its side, not to be taken for a star
    "K...K",
    ".K.K.",
    ".....",
    ".K.K.",
    "K...K",
])
STUD = art([                    # set on the ring's inner rule, half in the band and half out, like a jewel
    "..K..",
    ".KKK.",
    "KKRKK",
    ".KKK.",
    "..K..",
])
RADIANT = art([                 # where a shower's meteors seem to come from: a point, the streaks leaving it
    "R...R...R",
    ".R..R..R.",
    ".........",
    ".........",
    "RR..R..RR",
    ".........",
    ".........",
    ".R..R..R.",
    "R...R...R",
])


def _diag(points, size=9):
    """A drawing symmetric about a corner's diagonal: the points (row, col) and their mirrors."""
    g = [["."] * size for _ in range(size)]
    for r, c in points:
        g[r][c] = "R"
        g[c][r] = "R"
    return ["".join(row) for row in g]


# a leaf turning into the Time 2's top-left corner, its midrib left light, on a short forked stem; the other
# corners have its mirror images
CORNER_LEAF = art(_diag([(0, 0), (0, 1), (0, 2), (1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4), (3, 5), (4, 5),
                         (5, 5), (6, 6), (7, 7), (7, 8)]))


# ---- an engraved glory round the Sun on the printed charts: fine rays beyond its own, one eighth drawn ----------
_GLORY_LONG = [(0, y) for y in range(13, 21)] + [(k, k) for k in range(9, 15)] + \
              [(5, 12), (5, 13), (6, 14), (6, 15), (7, 16), (7, 17), (7, 18)]                  # 0, 45, 22.5 degrees
_GLORY_SHORT = [(3, 13), (3, 14), (3, 15), (3, 16), (3, 17)] + \
               [(7, 11), (8, 12), (9, 13), (9, 14), (10, 15)]                                  # 11.25, 33.75 degrees


def glory():
    n, c = 41, 20
    a = np.zeros((n, n), np.uint8)
    for x, y in _eightfold(_GLORY_LONG + _GLORY_SHORT):
        a[c - y, c + x] = ROLE["K"]
    return a


# ---- the southern horizon's skyline: hills, trees, a house, the church, a windmill, drawn as pieces and set on
# hills of hand-chosen height; the faces bend it along the window's lower edge -----------------------------------
_LAND_PIECES = {                # kept low: at the chart's scale a pixel is a degree and a half of sky
    "church": [".#......",
               "###.....",
               ".#......",
               ".#......",
               "###.....",
               "###.###.",
               "########"],
    "mill":   ["#...#",
               ".#.#.",
               "..#..",
               ".###.",
               ".###.",
               "#####"],
    "tree":   [".###.",
               "#####",
               ".###.",
               "..#.."],
    "mound":  [".##.",
               "####"],
    "poplar": [".#.",
               "###",
               "###",
               "###",
               ".#."],
    "house":  ["..#..",
               ".###.",
               "##.##"],
}
_LAND_HILLS = [(0, 1), (8, 2), (16, 2), (24, 1), (32, 1), (40, 2), (48, 2), (56, 1), (64, 2), (72, 2), (80, 2),
               (88, 1), (99, 1)]
_LAND_PLACES = [("tree", 7), ("poplar", 14), ("house", 23), ("mound", 31), ("tree", 37), ("church", 46),
                ("mound", 57), ("tree", 63), ("mill", 73), ("tree", 83), ("poplar", 91)]


def landscape():
    """The skyline as a mask, 100 wide; its bottom row stands on the horizon, its middle column at the south."""
    W, H = 100, 9
    g = np.zeros((H, W), bool)
    xs, hs = zip(*_LAND_HILLS)
    ground = np.round(np.interp(np.arange(W), xs, hs)).astype(int)
    for x in range(W):
        g[H - ground[x]:, x] = True
    for name, x0 in _LAND_PLACES:
        rows = _LAND_PIECES[name]
        h, w = len(rows), len(rows[0])
        base = H - ground[x0 + w // 2]
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == "#":
                    g[base - h + j, x0 + i] = True
    return g


# ---- small capitals five pixels tall, for the place's inscription on the ring (A to Z, figures, degree, minute)
TINY = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."], "C": [".##", "#..", "#..", "#..", ".##"],
    "D": ["##.", "#.#", "#.#", "#.#", "##."], "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"], "I": ["###", ".#.", ".#.", ".#.", "###"],
    "J": ["..#", "..#", "..#", "#.#", ".#."], "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": [".#.", "#.#", "#.#", "#.#", ".#."], "P": ["##.", "#.#", "##.", "#..", "#.."], "Q": [".#.", "#.#", "#.#", "#.#", ".##"],
    "R": ["##.", "#.#", "##.", "#.#", "#.#"], "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", ".#."], "V": ["#.#", "#.#", "#.#", ".#.", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"], "Y": ["#.#", "#.#", ".#.", ".#.", ".#."],
    "Z": ["###", "..#", ".#.", "#..", "###"], "0": [".#.", "#.#", "#.#", "#.#", ".#."], "1": [".#", "##", ".#", ".#", ".#"],
    "2": ["##.", "..#", ".#.", "#..", "###"], "3": ["##.", "..#", ".#.", "..#", "##."], "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "##.", "..#", "##."], "6": [".##", "#..", "##.", "#.#", ".#."], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": [".#.", "#.#", ".#.", "#.#", ".#."], "9": [".#.", "#.#", ".##", "..#", "##."], "°": ["##", "##", "..", "..", ".."],
    "'": ["#", "#", ".", ".", "."], ".": [".", ".", ".", ".", "#"], "-": ["..", "..", "##", "..", ".."],
}


def tiny(text, track=1):
    """Capitals five pixels tall (a space is three pixels), `track` pixels apart."""
    cols = []
    for ch in text.upper():
        if ch == " ":
            cols.append(np.zeros((5, 3), bool))
            continue
        g = TINY.get(ch)
        if g is None:
            continue
        cols.append(np.array([[c == "#" for c in row] for row in g]))
    W = sum(c.shape[1] for c in cols) + track * (len(cols) - 1)
    out = np.zeros((5, max(W, 1)), bool)
    x = 0
    for c in cols:
        out[:, x: x + c.shape[1]] = c
        x += c.shape[1] + track
    return out


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


# figures for the 24-hour ring (and the plain plates' ring), five pixels wide, drawn in the same thin stroke
FIGURES = {
    "0": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "1": [".#.", "##.", ".#.", ".#.", ".#.", ".#.", "###"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": [".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "..###"],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "#...#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
}


def figures(text, gap=1):
    glyphs = [np.array([[c == "#" for c in r] for r in FIGURES[ch]]) for ch in text]
    W = sum(g.shape[1] for g in glyphs) + gap * (len(glyphs) - 1)
    out = np.zeros((7, W), bool)
    x = 0
    for g in glyphs:
        out[:, x: x + g.shape[1]] = g
        x += g.shape[1] + gap
    return out


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
         block(LOZENGE, gold, cream)]
        + [mask_block(numerals(t), ink_, cream) for t in ("III", "VI", "IX")]
        + [mask_block(figures(t), ink_, cream) for t in ("3", "6", "9", "15", "18", "21")],
        [block(moon(n, w), {1: (85, 85, 85), 5: (255, 255, 170), 6: None}, sky)
         for n, w in [(n, False) for n in MOON_PHASES] + [(n, True) for n in list(MOON_PHASES)[-2:0:-1]]]
        + [block(st, {5: (255, 255, 255)}, sky) for st in STAR]
        + [block(PLANET[k], {1: (170, 85, 0), 2: (255, 85, 0), 3: (255, 170, 0), 4: (170, 85, 0), 5: (255, 255, 170),
                             7: (170, 170, 170)}, sky) for k in ("saturn", "jupiter", "mars", "venus", "mercury")],
        [mask_block(sign(z), (85, 85, 170), sky) for z in ZODIAC],
        [mask_block(sign(d), red, cream) for d in DAY_SIGNS]
        + [block(a, gold, cream) for a in (SOUTH_STAR, STUD, CORNER_LEAF)]
        + [block(ZENITH, {1: (170, 170, 255)}, sky), block(RADIANT, {2: (255, 85, 85)}, sky)],
        [block(glory(), {1: (170, 85, 85)}, (255, 255, 255)), mask_block(landscape(), (0, 0, 85), (85, 170, 255))],
        [mask_block(word_art(w, 200, 228)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
        [mask_block(word_art(w, 260, 260)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
    ]
    labels = ["The Sun after the Sun of May, its pointer, the fleur-de-lis, a lozenge, the ring's hours (12 and 24-hour)",
              "The Moon through a month, the stars by brightness, Saturn, Jupiter, Mars, Venus, Mercury",
              "The signs of the zodiac, set along the ecliptic",
              "The days' planets (Monday's Moon to Sunday's Sun), the south star, a stud, a corner leaf, the zenith, a radiant",
              "The engraved glory round the Sun on the printed charts, and the village on the southern horizon",
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
