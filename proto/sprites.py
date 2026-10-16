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


SUN_HAND = art([                 # the Sun's hand on the ring, gilded as on the old astronomical clocks
    ".....Y.....",
    "..Y..Y..Y..",
    "...Y.Y.Y...",
    "....OOO....",
    "...OYYYO...",
    "YYYOYWYOYYY",
    "...OYYYO...",
    "....OOO....",
    "...Y.Y.Y...",
    "..Y..Y..Y..",
    ".....Y.....",
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


# the full Moon on the Mid-Autumn night: the rabbit sitting in it where the face is (S), its ears up, as China and
# Japan see the dark seas
MOON_RABBIT = ["...WWWWW...",
               "..WWWWWWW..",
               ".WWSWSWWWW.",
               "WWWSWSWWWWW",
               "WWSSSSWWWWW",
               "WWSSSSSSSWW",
               "WWWSSSSSSSW",
               "WWWWSSSSSSW",
               ".WWWSWWSWW.",
               "..WWWWWWW..",
               "...WWWWW..."]


def moon_rabbit():
    return np.array([[ROLE[c] for c in r] for r in MOON_RABBIT], np.uint8)


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


# a printer's flower for either side of the time: the small broken lozenge from Peter Quentel's pattern book (Eyn
# New Kunstlich Boich, Cologne 1529, after its alphabet), stitch for stitch, as a sampler would work it
QUENTEL_FLOWER = art([
    "...R..R...",
    ".RRR..RRR.",
    ".RRR..RRR.",
    "RRR....RRR",
    "....RR....",
    "....RR....",
    "RRR....RRR",
    ".RRR..RRR.",
    ".RRR..RRR.",
    "...R..R...",
])

# ---- the flowers beside the time: charted needlework from research/needlework/, stitch for stitch, a pair either
# side of the time like printer's flowers round a title, changing on the hour. Half the hours bring a piece for the
# season (or the weather's, in snow or frost), half a piece for any time of year; the night adds the Moon. Each is
# drawn facing right (toward the time on the left; the right-hand one is its mirror)
NEEDLEWORK = {      # name: (rows, the library's slug)
    "lozenge": (["...#..#...", ".###..###.", ".###..###.", "###....###", "....##....", "....##....", "###....###",
                 ".###..###.", ".###..###.", "...#..#..."], "quentel1529-lozenge-10"),            # Cologne 1529
    "star": ([".....#.....", "....###....", "..#..#..#..", "...#.#.#...", ".#..###..#.", "###########",
              ".#..###..#.", "...#.#.#...", "..#..#..#..", "....###....", ".....#....."], "ch-18616385-star-11"),
    "star13": (["......#......", ".....#.#.....", "......#......", "...#..#..#...", "....#.#.#....", ".#...###...#.",
                "#.#########.#", ".#...###...#.", "....#.#.#....", "...#..#..#...", "......#......", ".....#.#.....",
                "......#......"], "ch-18616385-star-13"),                                    # an Italian sampler, 1802
    "checker": (["#...#...#", ".#.###.#.", "..#.#.#..", ".#.#.#.#.", "###.#.###", ".#.#.#.#.", "..#.#.#..",
                 ".#.###.#.", "#...#...#"], "quentel1529-checker-lozenge-9"),
    "quatrefoil": (["##...##", "###.###", ".##.##.", "...#...", ".##.##.", "###.###", "##...##"],
                   "bk-1968-11-four-petal-flower"),                                         # Brussels, c. 1875
    "globe": (["...#######...", "..#.#.###.#..", ".#..#.###..#.", "#...#.###...#", "#############", "#...#.###...#",
               ".#..#.###..#.", "..#.#.###.#..", "...#######..."], "bk-1980-63-ship-globe"),   # a Dutch sampler, 1857
    "anchor": (["....#....", "...#.#...", "...#.#...", "....#....", ".#######.", "....#....", "....#....",
                ".#..#..#.", "..#.#.#..", "...###..."], "bk-1980-63-anchor"),
    "bird": (["......###..", "......#.##.", "......#####", ".....####..", "....######.", "...#######.", "..###.#.#..",
              ".###..#.#..", "###..#.#.#."], "quentel1529-small-bird-11x9"),
    "songbird": ([".....###...", ".....##..#.", "...####..##", ".######.##.", "..######.#.", "###..##..##",
                  "....#......"], "ch-18616577-small-bird"),                                # a Dutch sampler, 1844
    "little tree": (["..#.#..", ".#.#.#.", "#.#.#.#", ".#.#.#.", "...#...", "...#...", "...#...", ".#####."],
                    "dmc1890s1-lozenge-tree-7x8"),                                          # DMC, 1890
    "moon": (["....###", "...###.", "..###..", ".###...", ".#.#...", "#####..", "####...", "###....", "####...",
              ".###...", ".###...", "..###..", "...###.", ".....##"], "dmc1890s1-crescent-moon"),
    "rosette": (["....##.##....", "....##.##....", "..####.####..", "..####.####..", "####.....####", "####..#..####",
                 ".....###.....", "####..#..####", "####.....####", "..####.####..", "..####.####..", "....##.##....",
                 "....##.##...."], "quentel1529-rosette-13"),
    "lily": ([".....#.....", "..#.###.#..", ".###.#.###.", "##.#####.##", "##..###..##", ".##..#..##.", "..#..#..#..",
              "....###....", "...#####..."], "quentel1529-lily-11x9"),
    "buds": (["......#......", "....##.##....", "..#.##.##.#..", ".###.#.#.###.", "..#.##.##.#..", "##.##...##.##",
              "####..#..####", ".....###.....", "####..#..####", "##.##...##.##", "..#.##.##.#..", ".###.#.#.###.",
              "..#.##.##.#..", "....##.##....", "......#......"], "dmc1890-four-ring-flower"),
    "tulip": (["....#....", "..#.#.#..", ".#######.", "#########", ".#######.", "..#####..", "...###...", "...###...",
               "....#....", "....#....", "....#....", "....#...."], "bk-1980-63-flower-head"),
    "strawberry": ([".....#.....", "....###....", "...#####...", "..#######..", "..#######..", "..#######..",
                    "...#####...", "..#######..", ".###.#.###.", "###..#..###", ".....#.....", "###########"],
                   "ch-18489537-strawberry"),                                               # Mary Hall's sampler, 1786
    "grapes": (["...#...#...", "..###.###..", "..###.###..", ".#.#.#.#.#.", "###.###.###", "###.###.###",
                ".#.#.#.#.#.", "..###.###..", "..###.###..", "...#.#.#...", "....###....", "....###....",
                ".....#....."], "ch-18616709-grape-bunch"),                                 # a German sampler, 18th c.
    "acorn": (["........##", "........##", "...#####..", "..######..", ".#######..", "##.#####..", ".##.####..",
               "..##.##...", ".#.###....", "##..#....."], "dmc1890-acorn-10"),                # DMC, 1890 (turned)
    "oak leaf": (["...#..#..#...", "..##.##.##...", "..#########..", "#.###########", "##.##.##.###.",
                  "....#..#.#..#"], "bk-1959-142-a-oak-leaf"),                             # c. 1810 (turned)
    "fir": ([".....#.....", "....###....", "...#####...", "..#.###.#..", ".###.#.###.", "###########",
             ".###.#.###.", ".....#.....", "....###....", "...#####..."], "quentel1544-fir-band"),  # Cologne 1544
    "ice": (["..#.#..", "...#...", "#..#..#", ".##.##.", "#..#..#", "...#...", "..#.#.."],
            "petit1819-snowflake-7"),                                                       # Paris, 1819
    "snowflake": (["....#....", "..#.#.#..", ".#######.", "###.#.###", ".#######.", "..#.#.#..", "....#...."],
                  "quentel1532-snowflake-9x7"),                                             # Cologne 1532
    "bud sprig": ([".......##.......", "......####......", "......####......", ".......##.......", "###....##....###",
                   ".###...##...###.", "..###..##..###..", ".....#.##.#.....", "......####......", ".......##.......",
                   ".......##.......", "........##......", ".........##....."], "album1596-bud-sprig"),  # c. 1596
    "berries": ([".##...##.", "####.####", "####.####", ".##...##.", "....#....", "...###...", "...###...",
                 "....#...."], "album1596-berry-cluster"),
    "pennant": (["......#..", "..#####..", ".######..", ".######..", "#######..", "##....#..", "#...#####"],
                "bk-1980-63-pennant"),          # a Dutch sampler, 1857: drawn blowing outward (away from the time)
    # no period chart of rain, thunder or fog is known: these three are drawn here in the samplers' solid stitch,
    # after Mignerak's lacis squares of the elements (Paris, 1605; research/needlework/motifs/mignerak1605-*)
    "rain": (["...##.##...", "..#######..", ".#########.", "###########", ".#########.", "...........", "..#..#..#..",
              ".#..#..#...", "...........", ".#..#..#...", "#..#..#...."], "after mignerak1605-four-elements"),
    "thunder": (["...##.##...", "..#######..", ".#########.", "###########", ".###.#####.", "....##.....", "...##......",
                 "..#######..", ".....##....", "....##.....", "...##......", "...#......."],
                "after mignerak1605-four-elements"),
    "fog": (["##...##...#", "..###..###.", "...........", "#...##...##", ".###..###..", "...........", "##...##...#",
             "..###..###."], "after mignerak1605-four-elements"),
}
ANY_TIME = ["lozenge", "star", "checker", "globe", "quatrefoil", "bird", "star13", "anchor", "songbird", "little tree"]
OF_SEASON = {"blossom": ["rosette", "tulip", "bud sprig", "lily", "buds"], "leaf": ["tulip", "strawberry", "lily", "rosette"],
             "harvest": ["strawberry", "grapes", "tulip"], "turning": ["grapes", "acorn", "oak leaf"],
             "autumn": ["acorn", "oak leaf", "grapes"], "bare": ["fir", "berries", "snowflake", "ice", "star"]}
OF_WEATHER = {"thunder": ["thunder"], "snow": ["ice", "snowflake", "star"], "rain": ["rain"], "fog": ["fog"],
              "wind": ["pennant"]}


def needlework(name):
    rows, _ = NEEDLEWORK[name]
    return np.array([[c == "#" for c in r] for r in rows])


def flank_pieces(season, hour_count, night=False, weather=None):
    """The hour's piece for beside the time, then the rest of its cycle (to take the next that fits): even hours
    the season's (or the weather's: thunder, snow, rain, fog or wind), odd hours one for any time, the night's Moon
    among them after dark."""
    seasonal = OF_WEATHER.get(weather) or OF_SEASON.get(season, ANY_TIME)
    general = ANY_TIME + (["moon"] if night else [])
    k = hour_count // 2
    first, second = (seasonal, general) if hour_count % 2 == 0 else (general, seasonal)
    order = [first[(k + i) % len(first)] for i in range(len(first))] + \
            [second[(k + i) % len(second)] for i in range(len(second))]
    return list(dict.fromkeys(order))


# ---- the astrolabe's pieces: the throne and ring it hangs by, standing at the north; the rete's flame pointers, the
# tip at the star (drawn pointing down and along the diagonal; the other six turned from these); figures as the
# fifteenth century cut them on astrolabes (after Hill's tables, 1915): the 3 a yogh, the 6 a sigma, the 9 tailed
THRONE = art([".....KKK.....",
              "....K...K....",
              "....K...K....",
              ".....KKK.....",
              "......K......",
              ".....KKK.....",
              "....K.K.K....",
              "...K..K..K...",
              "..K.KKKKK.K..",
              ".K.K.....K.K.",
              "KKKKKKKKKKKKK"])
FLAME = art(["..Y..",               # pointing down: the tip (the star) at the bottom
             ".Y.Y.",
             ".YYY.",
             ".YYY.",
             "..Y..",
             "..Y..",
             "..Y.."])
FLAME_DIAG = art(["YY...",          # pointing down and to the right
                  "YYY..",
                  ".YYY.",
                  "..YY.",
                  "...Y.",
                  "....Y"])


def flame(dx, dy):
    """The pointer for a star lying along (dx, dy) from the pole: (drawing, its tip's row and column)."""
    a = math.degrees(math.atan2(dy, dx)) % 360          # 0 right, 90 down (screen)
    k = int(((a + 22.5) % 360) // 45)                   # 0 right, 1 down-right, 2 down, ... 7 up-right
    if k % 2 == 0:
        base = FLAME                                    # down
        d = {2: base, 6: base[::-1, :], 0: base.T[:, ::-1][::-1, :] if False else np.rot90(base, 1), 4: np.rot90(base, -1)}[k]
    else:
        base = FLAME_DIAG                               # down-right
        d = {1: base, 3: base[:, ::-1], 5: base[::-1, ::-1], 7: base[::-1, :]}[k]
    tips = np.argwhere(d)
    ux, uy = math.cos(math.radians(k * 45)), math.sin(math.radians(k * 45))
    j, i = max(tips, key=lambda t: t[1] * ux + t[0] * uy)   # the pixel farthest along the pointing direction
    return d, int(j), int(i)


GOTHIC = {
    "1": [".#.", ".#.", ".#.", ".#.", ".#.", ".#.", "##."],
    "2": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "3": ["#####", "...#.", "..#..", ".###.", "....#", "#...#", ".###."],
    "6": ["..###", ".#...", "#....", "#.##.", "##..#", "#...#", ".###."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", "..#.."],
}


def gothic(text, gap=1):
    glyphs = [np.array([[c == "#" for c in r] for r in GOTHIC[ch]]) for ch in text]
    W = sum(g.shape[1] for g in glyphs) + gap * (len(glyphs) - 1)
    out = np.zeros((7, W), bool)
    x = 0
    for g in glyphs:
        out[:, x: x + g.shape[1]] = g
        x += g.shape[1] + gap
    return out


# ---- the Hours' pieces: the ring's hours in the small roman of the Books of Hours, the last i written j (iij, vj,
# ix); its ivy for the corners is with the other corner pieces
MINUSCULE = {
    "i": ["#", ".", "#", "#", "#", "#", "#"],
    "j": [".#", "..", ".#", ".#", ".#", ".#", "#."],
    "v": ["...", "...", "#.#", "#.#", "#.#", ".#.", ".#."],
    "x": ["...", "...", "#.#", "#.#", ".#.", "#.#", "#.#"],
}


def minuscule(text, gap=1):
    glyphs = [np.array([[c == "#" for c in r] for r in MINUSCULE[ch]]) for ch in text]
    W = sum(g.shape[1] for g in glyphs) + gap * (len(glyphs) - 1)
    out = np.zeros((7, W), bool)
    x = 0
    for g in glyphs:
        out[:, x: x + g.shape[1]] = g
        x += g.shape[1] + gap
    return out


# ---- the Apian plate's pieces: the dragon's head and tail at the Moon's nodes (as on Apian's dragon volvelle, 1540),
# and the seed pearl on the silk thread that serves his volvelles for an index
DRAGON_HEAD = art([".RRR.",           # the ascending node
                   "R...R",
                   "R...R",
                   ".R.R.",
                   "RR.RR"])
DRAGON_TAIL = DRAGON_HEAD[::-1, :].copy()   # the descending node, the head turned over
PEARL = art([".S.",
             "SWS",
             ".S."])


# ---- the labours of the months, drawn faint in the card behind the window as the calendars' woodcuts show them: the
# month's work in a field that runs on behind the oval. Each figure is drawn as the cuts draw it, by its pose and its
# tool (the labourer's wide straw hat, the scythe swept low, the reaper bent double, the flail overhead), facing right
LABOUR_FIGURES = {
    "feaster": [  # January: feasting, seated in his hood, the cup raised
        "....###......",
        "...#####.....",
        "....##....#..",
        "...####..###.",
        "..######.#...",
        "..##.######..",
        "..########...",
        "..#######....",
        "..##########.",
        "..##....#..#.",
        "..##....#..#.",
        ".###....#..#.",
    ],
    "table": [  # the laid table, a jug and a loaf
        "..#.........",
        ".###...##...",
        ".###..####..",
        "############",
        ".#........#.",
        ".#........#.",
        ".#........#.",
    ],
    "warmer": [  # February: warming at the fire, hands held out
        "....###.....",
        "...#####....",
        "...#####....",
        "....##......",
        "...####.....",
        "..#######...",
        "..##.######.",
        "..#####.....",
        "..#######...",
        "..##...###..",
        "..##.....#..",
        ".###.....##.",
    ],
    "fire": [  # the fire on its log
        "...#.....",
        "..##..#..",
        ".####.##.",
        ".######..",
        "..####...",
        "#########",
        ".#.#.#.#.",
    ],
    "pruner": [  # March: pruning the vines, the billhook in hand
        "......###....",
        "....#######..",
        "......##.....",
        ".....####.##.",
        "....#####.#..",
        "...#######...",
        "...##.##.....",
        "...######....",
        "...#######...",
        "....##..##...",
        "...##....##..",
        "..###....###.",
    ],
    "vine": [  # the vine stakes
        ".#.#.#.#.",
        ".#.#.#.#.",
        "#########",
        ".#.#.#.#.",
        ".#.#.#.#.",
        ".#.#.#.#.",
    ],
    "youth": [  # April: the youth in a plumed hat with a flowering branch
        "..##....#.#.#",
        "...###...###.",
        "..#####.#.#.#",
        "....##....#..",
        "...####...#..",
        "..######.##..",
        "..##.#####...",
        "..######.....",
        "..######.....",
        "..#######....",
        "..#######....",
        "..########...",
        "...#....#....",
        "..##....##...",
    ],
    "blossom tree": [  # a tree in blossom
        "..#.#.#..",
        ".#######.",
        "#.#####.#",
        ".###.###.",
        "#.#####.#",
        "..#####..",
        "....#....",
        "....#....",
        "...###...",
    ],
    "rider": [  # May: riding out with a hawk on the fist
        "..........###.#.....",
        "........#######.....",
        "..........##..#.....",
        "..........###.#.....",
        ".........#######....",
        "........########....",
        "..##....#######.....",
        ".####...######......",
        "######..######......",
        ".#############......",
        "..##############....",
        "..##############.##.",
        "...###########...##.",
        "...##.....##......#.",
        "...#.#....#.#.......",
        "...#..#...#..#......",
        "..##..##.##..##.....",
    ],
    "heron": [  # a heron put up
        "##.........",
        ".##........",
        "..######...",
        "...######..",
        "....#..###.",
        "........###",
        ".........#.",
    ],
    "mower": [  # June: mowing, the scythe swept low
        ".........###..........",
        ".......#######........",
        ".........##...........",
        ".........###..........",
        "........#####.........",
        ".......#######........",
        "......########........",
        ".....#..######........",
        "....#...#######.......",
        "...#....#######.......",
        "..#.....##...##.......",
        ".#.....##.....##......",
        "#.....##.......##.....",
        "#....###.......###....",
        ".###..................",
        "....####..............",
    ],
    "haycock": [  # a haycock
        "....###....",
        "..#######..",
        ".#########.",
        "###########",
        "###########",
    ],
    "reaper": [  # July: reaping, bent double with the sickle
        "...........###....",
        ".........#######..",
        "...........##.....",
        "......#######.....",
        "....##########....",
        "...###########....",
        "..##.#####.###....",
        ".##...####..##....",
        "#.#...####...#....",
        "#.#...###....##...",
        "##....##.##..#.#..",
        "......#...#..#.#..",
        ".....##...##.#.#..",
        "....###...###.#...",
    ],
    "sheaf": [  # a sheaf
        "#.#.#.#",
        ".#.#.#.",
        "#.###.#",
        "..###..",
        "#######",
        "..###..",
        ".#####.",
        "#.###.#",
    ],
    "thresher": [  # August: threshing, the flail over his head
        "......#.......",
        ".....#........",
        "....#...###...",
        "...#..#######.",
        "...#.....##...",
        "...#.....##...",
        "....#...####..",
        ".....#######..",
        "........####..",
        "........####..",
        ".......######.",
        ".......##..##.",
        "......##....##",
        ".....###....##",
    ],
    "stook": [  # a stook of sheaves
        "....#....",
        "...###...",
        "..##.##..",
        ".###.###.",
        "##.#.#.##",
        "#..#.#..#",
    ],
    "treader": [  # September: treading the grapes in the vat
        "..#....#..",
        "..#.##.#..",
        "...####...",
        "....##....",
        "...####...",
        "..######..",
        "..######..",
        "#.######.#",
        "##########",
        "#.#.#.#.##",
        "##########",
        ".########.",
        ".#.#..#.#.",
        ".########.",
    ],
    "barrel": [  # a barrel for the wine
        ".#######.",
        "#########",
        "#.#.#.#.#",
        "#########",
        "#.#.#.#.#",
        "#########",
        ".#######.",
    ],
    "sower": [  # October: sowing, the seed bag at his front, the seed falling
        "......###...........",
        "....#######.........",
        "......##............",
        "......###...........",
        ".....#####..........",
        "....#######.###.....",
        "....##.#########....",
        "....##..####...#....",
        "....##.######..#....",
        "....##.######.......",
        ".....#..####........",
        ".....#######...#.#..",
        ".....#######........",
        ".....##...##..#.#...",
        "....##.....##.......",
        "...##.......##.#....",
        "..##.........##.....",
        ".###.........###....",
    ],
    "crow": [  # a crow after the seed
        "..##..",
        ".####.",
        "####..",
        "..#...",
    ],
    "swineherd": [  # November: knocking down acorns for the pigs
        "............#.",
        "...###.....#..",
        ".#######..#...",
        "...##....#....",
        "...###..#.....",
        "..#####.#.....",
        ".#######......",
        ".#.#####......",
        "...#####......",
        "...######.....",
        "...##..##.....",
        "..##....##....",
        ".###....###...",
    ],
    "pig": [  # a pig at the acorns
        ".#.........",
        "#########..",
        ".#########.",
        ".##########",
        "..#.#..#.#.",
    ],
    "baker": [  # December: baking, the peel at the oven's mouth
        ".....###..............",
        "....#####.............",
        ".....##...............",
        "....####..............",
        "...######.............",
        "...##.#############...",
        "...######.........##..",
        "...######.........##..",
        "...#######............",
        "....##.##.............",
        "...##...##............",
        "..###...###...........",
    ],
    "oven": [  # the bread oven
        "...#####...",
        "..#######..",
        ".#########.",
        "###.....###",
        "##.......##",
        "###########",
    ],
}
# each month: the labourer on the left, the month's thing on the right, and the field behind the window (after the
# calendars' cycle, chiefly the Kalender of Shepherdes, Paris 1493, and the English calendars)
LABOURS = {1: dict(left="feaster", right="table", ground="snow"),
           2: dict(left="warmer", right="fire", ground="snow"),
           3: dict(left="pruner", right="vine", ground="vines"),
           4: dict(left="youth", right="blossom tree", ground="grass"),
           5: dict(left="rider", right="heron", ground="grass"),
           6: dict(left="mower", right="haycock", ground="grass"),
           7: dict(left="reaper", right="sheaf", ground="stubble"),
           8: dict(left="thresher", right="stook", ground="stubble"),
           9: dict(left="treader", right="barrel", ground="vines"),
           10: dict(left="sower", right="crow", ground="furrows"),
           11: dict(left="swineherd", right="pig", ground="grass"),
           12: dict(left="baker", right="oven", ground="snow")}


# the figures drawn more than once, at these offsets: a flock of crows over the sowing, the swine under the oaks
LABOUR_COPIES = {"crow": [(0, 0), (-7, 5), (6, 8)], "pig": [(-4, -3), (5, 4)]}


def labour_figure(name):
    return np.array([[c == "#" for c in r] for r in LABOUR_FIGURES[name]])


# ---- small marks: the south point's star, the studs on the ring at every third hour, a meteor shower's radiant
SOUTH_STAR = art([
    "..R..",
    "..R..",
    "RR.RR",
    "..R..",
    "..R..",
])
BIRD = [art(["W...W",           # a bird crossing the day sky, its wings up
              ".W.W.",
              "..W.."]),
        art([".WWW.",           # and down
              "W...W",
              "....."])]
SWALLOW = [art(["K.....K",      # a swallow hawking over the fields: gliding, its wings swept back, its tail forked
                 ".K...K.",
                 "..KKK..",
                 "...K...",
                 "..K.K.."]),
           art([".K...K.",      # wings up
                "..K.K..",
                "..KKK..",
                "...K...",
                "..K.K.."]),
           art([".......",      # wings down
                "..KKK..",
                ".K.K.K.",
                "K..K..K",
                "..K.K.."])]
BAT = [art(["K.......K",            # a bat out of the belfry at dusk: wings up
            ".KK.K.KK.",
            "..KKKKK..",
            "....K...."]),
       art([".........",            # level, its ears up
            "KKK.K.KKK",
            ".KKKKKKK.",
            "K.K...K.K"]),
       art([".........",            # down, the scalloped edges hanging
            "...K.K...",
            ".KKKKKKK.",
            "K..K.K..K"])]
OWL = [art([".K.K.",              # the owl on the church's ridge by night: an egg with two tufts, its eyes gold
            ".KKK.",
            "KYKYK",
            "KKKKK",
            "KKKKK",
            ".KKK.",
            ".K.K."]),
       art([".K.K.",              # blinking
            ".KKK.",
            "KKKKK",
            "KKKKK",
            "KKKKK",
            ".KKK.",
            ".K.K."]),
       art([".K.K.",              # looking east
            ".KKK.",
            "YKYKK",
            "KKKKK",
            "KKKKK",
            ".KKK.",
            ".K.K."]),
       art([".K.K.",              # looking west
            ".KKK.",
            "KKYKY",
            "KKKKK",
            "KKKKK",
            ".KKK.",
            ".K.K."])]
JACKDAW = [art(["K...K",          # jackdaws round the church tower on a winter's day: wings up
                ".KKK.",
                "..K.."]),
           art([".KKK.",          # and down
                "K.K.K",
                "....."])]
FALLING_LEAF = [art(["R..",       # a leaf coming down, tumbling an eighth of a turn a frame
                     ".R.",
                     "..R"]),
                art([".R.",
                     ".R.",
                     ".R."]),
                art(["..R",
                     ".R.",
                     "R.."]),
                art(["...",
                     "RRR",
                     "..."])]
FIREFLY = [art([".O.",            # a firefly's flash: bright with a glow round it, then a point, then a dim point
                "OYO",
                ".O."]),
           art(["...",
                ".Y.",
                "..."]),
           art(["...",
                ".O.",
                "..."])]
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


def _diag_rows(rows):
    """A drawing symmetric about a corner's diagonal, from its upper half (columns at or right of the diagonal)."""
    n = len(rows)
    g = [["."] * n for _ in range(n)]
    for r in range(n):
        for c in range(r, n):
            if rows[r][c] != ".":
                g[r][c] = g[c][r] = rows[r][c]
    return ["".join(x) for x in g]


# the corner's sprig through the year: blossom in spring (two flowers on side stems), the leaf in summer, the
# leaf turned gold in autumn, a bare forked twig in winter
CORNER_SEASONS = {
    "blossom": art(_diag_rows([".R...R...",
                               ".YR.RYR..",
                               "..R.KR...",
                               "...K.....",
                               "....K....",
                               ".....K...",
                               "......K..",
                               ".......KK",
                               "........."])),
    "leaf": CORNER_LEAF,
    "autumn": np.where(CORNER_LEAF == ROLE["R"], ROLE["Y"], CORNER_LEAF).astype(np.uint8),
    "bare": art(_diag_rows(["K..K.....",
                            ".K.K.....",
                            "..KK.K...",
                            "...K.K...",
                            "....KK...",
                            ".....K...",
                            "......K..",
                            ".......KK",
                            "........."])),
}
CORNER_OF_SEASON = {"bare": "bare", "blossom": "blossom", "leaf": "leaf", "harvest": "leaf", "turning": "autumn",
                    "autumn": "autumn"}
# the Cyanotype's corners: a seaweed frond in white, after Anna Atkins's British Algae (1843)
CORNER_FROND = art(_diag_rows(["K..K.....",
                               ".K.K..K..",
                               "..KK.K...",
                               "...K.K...",
                               "....KK.K.",
                               ".....K.K.",
                               "......K..",
                               ".......KK",
                               "........."]))
# the Hours plate's corners: an ivy sprig in gold all the year, after the borders of the Books of Hours
CORNER_IVY = art(_diag_rows(["Y..YY....",
                             "..YYY....",
                             "..K.Y....",
                             "...K..YY.",
                             "....K.YY.",
                             ".....K...",
                             "......K..",
                             ".......KK",
                             "........."]))


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


# ---- the southern horizon: a church and a house among trees, after the cuts of a village on an almanac's page.
# The church stands at the south point, its spire on the meridian and a weather vane on its mast; the house beside
# it has a chimney and windows lit of an evening. The trees keep the year: in blossom, in leaf, turning, gold, bare
# (the firs stay green). Each piece is drawn whole and stood on the ground the faces bend along the window's lower
# edge: a tree where its trunk meets the ground, a building as low as the ground under it goes (the hillside laps
# its uphill side). Roles: K the silhouette, R blossom or turning leaves (coloured by day), Y a window lit at night
VILLAGE_PIECES = {
    "church": [".....#...................",       # the mast (the vane stands on it), the tall spire, pinnacles at
               ".....#...................",       # the tower's corners, the belfry's opening; the nave's ridge and
               ".....#...................",       # eaves, three lancet windows; the west door
               "....###..................",
               "....###..................",
               "....###..................",
               "...#####.................",
               "...#####.................",
               "..#.###.#................",
               "..#######................",
               "..#######................",
               "..###.###................",
               "..###.###..############..",
               "..#######.##############.",
               "..#######################",
               "..#######################",
               "..##########.###.###.###.",
               "..##########.###.###.###.",
               "..######################.",
               "..###.##################.",
               "..###.##################.",
               "..###.##################."],
    "house": ["......#...#..",                    # a gable end with a chimney, two windows up and two down, a door
              ".....###..#..",
              "....#####.#..",
              "...########..",
              "..#########..",
              ".###########.",
              "#############",
              ".##Y#####Y##.",
              ".###########.",
              ".##Y##.##Y##.",
              ".#####.#####.",
              ".#####.#####."],
    "tree": ["...##.##...", "..#######..", ".#########.", "###########", ".##########", "###########",
             ".#########.", "..###.###..", "....#.#....", ".....#.....", ".....#....."],
    "tree:blossom": ["...#R.R#...", "..#R###R#..", ".R###R###R.", "##R#####R##", ".###R#R####", "#R#######R#",
                     ".##R###R##.", "..###.###..", "....#.#....", ".....#.....", ".....#....."],
    "tree:turning": ["...##.R#...", "..##R####..", ".#####R###.", "#R#######R#", ".####R#####", "###R####R##",
                     ".######R##.", "..##R.###..", "....#.#....", ".....#.....", ".....#....."],
    "tree:autumn": ["...#..R#...", "..#R#.##...", ".#.##R#.#R.", "#R#.###R#.#", ".#.##R#.##.", "R##.#.##R##",
                    ".#R##.#R#..", "..##..#.#..", "....#.#....", ".....#.....", ".....#....."],
    "tree:bare": [".#..#.#..#.", "..#.#.#.#..", "#..##.##..#", ".#..###..#.", "..#..#..#..", "...#.#.#...",
                  "....###....", ".....#.....", ".....#.....", ".....#.....", ".....#....."],
    "poplar": ["..#..", "..#..", ".###.", ".###.", ".###.", "#####", "#####", "#####", "#####", ".###.", ".###.",
               "..#..", "..#.."],
    "poplar:turning": ["..#..", "..#..", ".#R#.", ".###.", ".##R.", "#####", "R####", "##R##", "####R", ".###.",
                       ".R##.", "..#..", "..#.."],
    "poplar:autumn": ["..#..", "..R..", ".#.#.", ".R##.", ".#.R.", "#.###", "R#.#.", "##R.#", ".#.#R", ".##..",
                      ".R#..", "..#..", "..#.."],
    "poplar:bare": ["..#..", "..#..", ".#.#.", "..#..", ".#.#.", "#.#.#", ".###.", "#.#.#", ".###.", "..#..",
                    "..#..", "..#..", "..#.."],
    "fir": ["...#...", "...#...", "..###..", "..###..", ".#####.", "..###..", ".#####.", "#######", "..###..",
            "#######", "...#...", "...#..."],
    "small": ["..###..", ".#####.", "#######", "#######", ".#####.", "...#...", "...#..."],
    "small:blossom": ["..#R#..", ".R###R.", "##R#R##", "#R###R#", ".##R##.", "...#...", "...#..."],
    "small:turning": ["..##R..", ".#R###.", "####R##", "#R#####", ".###R#.", "...#...", "...#..."],
    "small:autumn": ["..#.R..", ".R.##..", "#.#R#.#", "R##.#R#", ".#.#.#.", "...#...", "...#..."],
    "small:bare": ["#..#..#", ".#.#.#.", "..###..", "#..#..#", ".#.#.#.", "...#...", "...#..."],
}
VILLAGE_TREES = ("tree", "poplar", "fir", "small")
# where each piece stands, its middle column this many pixels from the south point, and the hills' heights
VILLAGE_LAYOUT = [("fir", -44), ("tree", -33), ("house", -18), ("church", 7), ("tree", 22), ("poplar", 31),
                  ("small", 40)]
VILLAGE_HILLS = [(-62, 1), (-48, 2), (-36, 3), (-24, 2), (-10, 1), (0, 1), (12, 2), (26, 3), (40, 2), (52, 2), (62, 1)]
VILLAGE_SEASON = {"blossom": "blossom", "turning": "turning", "autumn": "autumn", "bare": "bare"}
# the distant hills behind it where the place's own skyline is not known (or is flat): low and far, a long ridge
# rising to a summit either side, the steeple against the sky between; heights in pixels above the window's edge,
# straight ridges between these points
DISTANT_RANGE = [(-72, 3), (-62, 5), (-52, 7), (-43, 10), (-35, 8), (-25, 5), (-13, 4), (0, 3), (12, 4), (21, 6),
                 (31, 10), (40, 8), (51, 6), (62, 4), (72, 3)]


def distant_range(dxs):
    """The drawn hills' height above the window's edge at each column offset."""
    xs, hs = zip(*DISTANT_RANGE)
    return {dx: int(round(np.interp(dx, xs, hs))) for dx in dxs}


VANE = {                        # the church's weather vane on its mast, the arrow pointing where the wind comes from
    "left": [".#..#",           # (seen from the north, looking south: east is to the left), its barb and its tail
             "#####",           # standing up; end on, a cross
             "..#.."],
    "right": ["#..#.",
              "#####",
              "..#.."],
    "end": ["..#..",
            ".###.",
            "..#.."],
}


def season_of(sun_lon, lat):
    """The village's season from the Sun's place in the zodiac (spring's equinox at 0 degrees), turned half a year
    for the southern hemisphere: bare, blossom, leaf, harvest, turning, autumn."""
    lam = (sun_lon + (180.0 if lat < 0 else 0.0)) % 360
    for upto, name in ((15, "bare"), (45, "blossom"), (120, "leaf"), (165, "harvest"), (195, "turning"),
                       (240, "autumn"), (360, "bare")):
        if lam < upto:
            return name
    return "bare"


def village(edge, season="leaf", snow=False, vane="end", lit=False):
    """The village set on the window's lower edge: `edge` maps a column's offset from the south point to the
    window's lowest row there. Returns ({(dx, y): role}, anchors), the anchors being where things perch or rise:
    the vane's top, the church's ridge and belfry, the house's roof peak and chimney, the trees' crowns."""
    xs_, hs_ = zip(*VILLAGE_HILLS)
    top = {dx: e - int(round(np.interp(dx, xs_, hs_))) for dx, e in edge.items()}   # the ground's top row
    px = {}
    for dx, e in edge.items():
        for y in range(top[dx] + 1, e + 1):
            px[(dx, y)] = ROLE["K"]
    anchors = {"trees": []}
    variant = VILLAGE_SEASON.get(season, "")
    for name, at in VILLAGE_LAYOUT:
        key = f"{name}:{variant}" if f"{name}:{variant}" in VILLAGE_PIECES else name
        rows = VILLAGE_PIECES[key]
        h, w = len(rows), len(rows[0])
        x0 = at - w // 2
        cols = [x0 + i for i in range(w)]
        if any(c not in top for c in cols):
            continue                                       # off the window's edge
        base = top[at] if name in VILLAGE_TREES else max(top[c] for c in cols)
        for j, r in enumerate(rows):
            for i, ch in enumerate(r):
                if ch == ".":
                    continue
                role = ROLE["K"] if ch == "#" else ROLE[ch]
                if ch == "Y" and not lit:
                    role = ROLE["K"]
                px[(x0 + i, base - h + 1 + j)] = role
        if name not in VILLAGE_TREES:                      # the ground runs on under a building
            for c in cols:
                for y in range(base + 1, edge[c] + 1):
                    px[(c, y)] = ROLE["K"]
        y0 = base - h + 1
        if name == "church":
            anchors["mast"] = (x0 + 5, y0)
            anchors["ridge"] = (x0 + 16, y0 + 12)
            anchors["belfry"] = (x0 + 5, y0 + 11)
        elif name == "house":
            anchors["peak"] = (x0 + 6, y0)
            anchors["chimney"] = (x0 + 10, y0)
        else:
            anchors["trees"].append((at, y0, name))
    vane_px = set()
    if "mast" in anchors:                                  # the vane on the mast, its pivot over the mast
        mx, my = anchors["mast"]
        for j, r in enumerate(VANE[vane]):
            for i, ch in enumerate(r):
                if ch == "#":
                    px[(mx - 2 + i, my - 3 + j)] = ROLE["K"]
                    vane_px.add((mx - 2 + i, my - 3 + j))
        anchors["vane"] = (mx, my - 3)
    if snow:                                               # snow on every top: the first ink down each column
        for dx in {p[0] for p in px}:
            ys = sorted(y for (x, y) in px if x == dx)
            if ys and (dx, ys[0]) not in vane_px:
                px[(dx, ys[0])] = ROLE["W"]
    return px, anchors


# ---- the weather's clouds, after Howard (1803): cumulus, "convex or conical heaps, increasing upward from a
# horizontal base", drawn as silhouettes by hand; the faces light their tops and shade their bases for the hour
# (roles from the silhouette: K the top edge, W the body, S the base). Cirrus, "a wisp of hair", in single strokes
CUMULUS = [
    ["..........####...........",
     ".......##########........",
     "......############..###..",
     "...#####################.",
     "..#######################",
     ".########################",
     "#########################",
     ".#######################."],
    ["....####.......",
     "..########.##..",
     ".#############.",
     "###############",
     "###############",
     ".#############."],
    ["...###...",
     ".#######.",
     "#########",
     ".#######."],
]
STRATUS = [                     # "a widely extended, continuous, horizontal sheet": long low banks, a little heaped
    ["...........#####...............######.......",
     "......###############.....##############....",
     "..########################################..",
     "############################################"],
    ["........#######................",
     "...######################......",
     "#############################..",
     "..#############################"],
    ["......#####............",
     "..###################..",
     "#######################"],
]
CIRRUS = [
    [".............#",
     "...........##.",
     "......#####...",
     "######........"],
    ["......######",
     "#####.......",
     "............"],
    ["..........##",
     "........##..",
     "#######.....",
     "............"],
]


def cloud(rows):
    """A cloud's silhouette as roles: K where nothing lies above it (the lit top), S along its base, W within."""
    m = np.array([[c == "#" for c in r] for r in rows])
    a = np.where(m, ROLE["W"], 0).astype(np.uint8)
    above = np.zeros_like(m)
    above[1:] = m[:-1]
    a[m & ~above] = ROLE["K"]
    below = np.zeros_like(m)
    below[:-1] = m[1:]
    a[m & ~below & above] = ROLE["S"]
    return a


def stroke(rows):
    return np.array([[ROLE["K"] if c == "#" else 0 for c in r] for r in rows], np.uint8)


SNOWFLAKE = art([               # a flake as the woodcut pecks it: a soft square, never a star's cross
    "WW",
    "WW",
])


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
    ":": [".", "#", ".", "#", "."],
    # high and low water, as tide tables mark them: a solid triangle up, and down (after the Dymaxion face's)
    "▲": [".....", "..#..", ".###.", "#####", "....."], "▼": [".....", "#####", ".###.", "..#..", "....."],
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
        [block(sun_of_may(), gold, cream), block(SUN_HAND, gold, cream), block(FLEUR, gold, cream),
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
        + [block(a, gold, cream) for a in (SOUTH_STAR, STUD, CORNER_LEAF, QUENTEL_FLOWER)]
        + [block(ZENITH, {1: (170, 170, 255)}, sky), block(RADIANT, {2: (255, 85, 85)}, sky)],
        [block(glory(), {1: (170, 85, 85)}, (255, 255, 255))]
        + [block(art([r.replace("#", "K") for r in VILLAGE_PIECES[k]]), {1: (0, 0, 85), 3: (255, 255, 85)}, (85, 170, 255))
           for k in ("church", "house")],
        [block(art([r.replace("#", "K") for r in VILLAGE_PIECES[k]]), {1: (0, 0, 85), 2: (255, 170, 255) if "blossom" in k else (255, 85, 0)},
               (85, 170, 255))
         for k in ("tree", "tree:blossom", "tree:turning", "tree:autumn", "tree:bare", "poplar", "poplar:turning",
                   "poplar:autumn", "poplar:bare", "fir", "small", "small:blossom", "small:turning", "small:autumn",
                   "small:bare")]
        + [block(art([r.replace("#", "K") for r in VANE[k]]), {1: (0, 0, 85)}, (85, 170, 255)) for k in ("left", "end", "right")],
        [mask_block(needlework(k), red, cream) for k in NEEDLEWORK],
        [mask_block(labour_figure(k), (170, 170, 85), cream) for k in LABOUR_FIGURES],
        [block(CORNER_SEASONS[k], gold, cream) for k in ("blossom", "leaf", "autumn", "bare")]
        + [block(cloud(c), {1: (255, 255, 255), 5: (255, 255, 255), 7: (170, 170, 255)}, (85, 170, 255))
           for c in CUMULUS + STRATUS]
        + [block(stroke(c), {1: (255, 255, 255)}, (85, 170, 255)) for c in CIRRUS],
        [block(f, {1: (0, 0, 85)}, (85, 170, 255)) for f in SWALLOW + BAT + JACKDAW]
        + [block(f, {1: (0, 0, 0), 3: (255, 255, 85)}, (0, 0, 85)) for f in OWL]
        + [block(f, {2: (255, 85, 0)}, (85, 170, 255)) for f in FALLING_LEAF]
        + [block(f, {3: (255, 255, 85), 4: (170, 170, 0)}, (0, 0, 85)) for f in FIREFLY]
        + [block(SNOWFLAKE, {5: (255, 255, 255)}, (170, 170, 170))]
        + [block(THRONE, {1: (0, 0, 0)}, (170, 170, 85)), block(FLAME, {3: (255, 255, 170)}, (85, 85, 0)),
           block(FLAME_DIAG, {3: (255, 255, 170)}, (85, 85, 0)), block(CORNER_IVY, {1: (0, 0, 0), 3: (255, 170, 0)}, cream),
           block(CORNER_FROND, {1: (255, 255, 255)}, (0, 85, 170)), block(DRAGON_HEAD, {2: (0, 0, 0)}, (255, 255, 85)),
           block(DRAGON_TAIL, {2: (0, 0, 0)}, (255, 255, 85)), block(PEARL, {5: (255, 255, 255), 7: (170, 170, 170)}, (0, 0, 0))],
        [mask_block(word_art(w, 200, 228)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
        [mask_block(word_art(w, 260, 260)[0], red, cream) for w in ("MIDNIGHT", "NOON")],
    ]
    labels = ["The Sun after the Sun of May, its hand on the ring, the fleur-de-lis, a lozenge, the ring's hours (12 and 24-hour)",
              "The Moon through a month, the stars by brightness, Saturn, Jupiter, Mars, Venus, Mercury",
              "The signs of the zodiac, set along the ecliptic",
              "The days' planets (Monday's Moon to Sunday's Sun), the south star, a stud, a corner leaf, Quentel's flower (1529), the zenith, a radiant",
              "The engraved glory round the Sun on the printed charts; the church (its spire on the meridian) and the house, its windows lit",
              "The trees through the year (in leaf, blossom, turning, gold, bare; the fir stays green), and the vane: wind from the east, north or south, west",
              "The flowers beside the time, charted needlework from the library (1527-1890): for any time, then for the night, the seasons and snow",
              "The labours of the months, after the calendars' woodcuts: each labourer and beside him the month's thing, January to December",
              "The corner sprigs through the year, Howard's cumulus heaps and banks (lit tops, shaded bases), cirrus",
              "The passers-by (a swallow, a bat, a jackdaw, the owl, a leaf, a firefly, a snowflake); the plates' own: the astrolabe's throne and pointers, ivy, a frond, the dragon's head and tail, the pearl",
              "MIDNIGHT and NOON along the Time 2's ring", "MIDNIGHT and NOON along the Round 2's ring"]
    tiles = []
    for r, label in zip(rows, labels):
        h = max(t.shape[0] for t in r)
        big = Image.new("RGB", (max(sum(t.shape[1] * S + 12 for t in r), int(ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(label)) + 8),
                                h * S + h + 34), (40, 40, 44))
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
