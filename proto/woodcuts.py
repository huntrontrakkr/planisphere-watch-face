"""The card's woodcuts: real period woodcuts digitized for the card behind the face, one at a time filling the card
behind the window, faint, so that only what falls on the open card shows (plan_decor.c scene). Each is read from its
scan in research/themes, cropped, its printed words wiped, smoothed to the watch's scale and thresholded against the
paper, then cleared of the scan's leavings (specks, slivers of the page's edge): line work, a bit a pixel.

tools/gen_tables.py packs them into scenes.bin (blob()); the watch streams the one it needs from its resources.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "research" / "themes"
WIDTH = 200                      # pixels: the Time 2's width (the Round 2 centres them)

# the zodiac (THEME_ZODIAC), the Sun's sign: Ratdolt's woodcuts for Hyginus, Poeticon astronomicon (Venice, 1482),
# each (file, crop as fractions (x0, y0, x1, y1) or None, the printed words to wipe as fractions of the crop, then its
# placing: turned anticlockwise (degrees), its width (pixels), and how far its middle stands right of and below the
# window's middle). The placings were found by a search over both watches at 40 degrees north (each figure about the
# window's width, a quarter of it or so showing on the open card in pieces as whole as may be, the two sides balanced,
# its head whole), the crab turned to raise its claws, then looked over; Libra, as Hyginus has it, the Scorpion
# holding the balance in its claw, set high so both show above the window.
ZODIAC = [
    ("hyginus1482-aries.jpg", None, [(0.42, 0.17, 0.66, 0.30)], 0, 210, 10, -40),
    ("hyginus1482-taurus.jpg", None, [(0.38, 0.88, 0.68, 1.0)], 0, 210, -5, -35),
    ("hyginus1482-gemini.jpg", None, [(0.0, 0.0, 1.0, 0.07), (0.33, 0.89, 0.92, 1.0)], 0, 195, 5, -15),
    ("hyginus1482-cancer.jpg", None, [(0.28, 0.89, 0.62, 1.0)], 90, 210, 10, -15),
    ("hyginus1482-leo.jpg", None, [(0.38, 0.88, 0.88, 1.0)], 0, 210, 20, -5),
    ("hyginus1482-virgo.jpg", None, [(0.0, 0.0, 1.0, 0.06), (0.33, 0.91, 0.67, 1.0)], 0, 195, 0, 5),
    ("hyginus1482-scorpio-libra.jpg", None, [(0.28, 0.85, 0.72, 1.0)], 0, 210, 0, -75),   # Libra: the balance in its claw
    ("hyginus1482-scorpio-libra.jpg", None, [(0.28, 0.85, 0.72, 1.0)], 0, 210, 10, -35),
    ("hyginus1482-sagittarius.jpg", None, [(0.18, 0.87, 0.67, 1.0)], 0, 210, -15, 0),
    ("hyginus1482-capricorn.jpg", None, [(0.44, 0.07, 0.82, 0.20)], 10, 210, 5, 0),
    ("hyginus1482-aquarius.jpg", None, [(0.13, 0.89, 0.62, 1.0)], 0, 195, 5, 10),
    ("hyginus1482-pisces.jpg", None, [], 0, 210, 0, -15),
]

# the astronomer (THEME_ASTRONOMER), the month's: Tycho Brahe's instruments at Uraniborg as his Astronomiae instauratae
# mechanica (Nuremberg, 1602) engraves them, January first, each (file, crop inside the plate's frame, words to wipe,
# width, dx, dy) as the zodiac's
PLATE = (0.05, 0.04, 0.95, 0.93)
ASTRONOMER = [
    ("brahe1602-armillary-equatorial.jpg", PLATE, [], 210, 0, 0),
    ("brahe1602-armillary-zodiacal.jpg", PLATE, [], 210, 0, 0),
    ("brahe1602-great-globe.jpg", PLATE, [], 210, 0, 0),
    ("brahe1602-armillary-great-equatorial.jpg", PLATE, [], 210, 0, -60),
    ("brahe1602-sextant-trigonic.jpg", PLATE, [], 210, 0, -40),
    ("brahe1602-quadrant-revolving.jpg", PLATE, [], 210, 0, 0),
    ("brahe1602-mural-quadrant.jpg", PLATE, [], 210, 0, -40),
    ("brahe1602-semicircle-azimuthal.jpg", PLATE, [], 210, 0, -60),
    ("brahe1602-quadrant-augsburg.jpg", PLATE, [], 210, 0, -20),
    ("brahe1602-uraniborg-elevation.jpg", PLATE, [], 210, 0, -60),
    ("brahe1602-quadrant-great-steel-square.jpg", PLATE, [], 210, 0, -20),
    ("brahe1602-quadrant-small-gilt.jpg", PLATE, [], 210, 0, -20),
]
ASTRONOMER_BASE = len(ZODIAC)                            # (its first in scenes.bin)

# the sea (THEME_SEA), the month's, January first: ships afloat as the Dutch etchers drew them, Wenceslaus Hollar's
# from his Navium variae figurae et formae (Antwerp, 1647) and his calm sea of the 1630s, between them Reinier Nooms's
# ("Zeeman", the 1650s), each (file, crop, words to wipe as fractions of the crop, its horizon and its waterline: where the
# farthest ships and the nearest hulls meet the sea, fractions of the crop's height). The plate is cut below its waterline and hung by it a little above the
# window's top (SEA_ABOVE), rising and falling with the tide (TIDE_SHIFT); the watch draws the sea itself, across the
# card (plan_decor.c sea_strokes), so the water is clean and runs ring to ring.
HOLLAR = (0.02, 0.06, 0.98, 0.97)
TITLE = (0.0, 0.0, 1.0, 0.06)                            # (the plate's engraved title, across its top)
NOOMS = (0.02, 0.04, 0.98, 0.95)
SEA = [
    ("hollar1647-354-fluyt-under-sail.jpg", HOLLAR, [TITLE], 0.82, 0.865),
    ("nooms1652-salamander-eastindiaman.jpg", (0.01, 0.03, 0.99, 0.86), [], 0.86, 0.928),
    ("hollar1647-350-schelde-antwerp-heu.jpg", HOLLAR, [TITLE, (0.08, 0.55, 0.32, 0.63), (0.70, 0.58, 0.86, 0.67)], 0.845,
     0.89),
    ("nooms1650-fluyt-calm-water.jpg", (0.05, 0.06, 0.95, 0.95), [], 0.72, 0.753),
    ("hollar1647-345-eastindiaman-and-warships.jpg", HOLLAR, [TITLE, (0.0, 0.08, 0.26, 0.17)], 0.84, 0.895),
    ("nooms1650-ship-at-anchor-rowing-boat.jpg", NOOMS, [], 0.76, 0.813),
    ("hollar1647-353-boeiers.jpg", HOLLAR, [TITLE], 0.82, 0.905),
    ("nooms1650-warships-and-yacht.jpg", (0.03, 0.04, 0.96, 0.95), [(0.45, 0.0, 1.0, 0.13), (0.28, 0.28, 0.62, 0.47)],
     0.71, 0.747),
    ("hollar1647-348-warship.jpg", HOLLAR, [TITLE], 0.84, 0.885),
    ("nooms1650-two-warships-under-sail.jpg", NOOMS, [], 0.76, 0.868),
    ("hollar1647-351-warships-sea-fight.jpg", HOLLAR, [TITLE], 0.86, 0.925),
    ("hollar1636-ships-at-anchor-calm-sea.jpg", (0.04, 0.09, 0.945, 0.77), [], 0.82, 0.853),
]
SEA_WIDTH = 150
SEA_BASE = ASTRONOMER_BASE + len(ASTRONOMER)
SEA_ABOVE = 4                                            # the waterline's rows above the window's top at mean water
TIDE_SHIFT = 12                                          # pixels the plate rises at high water and falls at low


def tide_shift(tides, minute):
    """How many pixels above its mean the plate rides at `minute` (since 1970), from the tide's turns (minute, high,
    cm) in order: between two turns as the smooth step 3s^2 - 2s^3 goes, in integers (plan_decor.c tide_shift); 0
    with no turns about the minute."""
    for (t0, h0, _), (t1, h1, _) in zip(tides, tides[1:]):
        if t0 <= minute < t1 and h0 != h1:
            s = (minute - t0) * 1024 // (t1 - t0)
            e = s * s // 1024 * (3072 - 2 * s) // 1024
            f = e if h1 else 1024 - e
            return (TIDE_SHIFT * 2 * f + 512) // 1024 - TIDE_SHIFT
    return 0


# the sea's strokes below the waterline, as Hollar etches open water: each (rows below the waterline, the stretch a
# stroke falls in, its length), close and long by the waterline, shorter and further apart as they come nearer
SEA_STROKES = [(1, 14, 12), (3, 13, 10), (5, 12, 8), (8, 11, 6), (11, 10, 5), (15, 10, 4), (20, 9, 3), (26, 9, 2)]


SEA_UNDER, SEA_BESIDE = 2, 6                             # (the wash under a hull and the lapping beside it, pixels)


def hull_water(ink):
    """Where the water meets the hulls, as the watch draws it (plan_decor.c hull_water), by the image's columns: the
    hulls are what is inked in the plate's last two rows (its waterline and the row above). Under a hull (and SEA_UNDER
    either side) the row below the waterline is washed solid; beside it, within SEA_BESIDE, the waterline's own row is
    lapped, three pixels in four. (under, beside): bool arrays over the image's columns."""
    hull = ink[-1] | ink[-2]
    w = len(hull)

    def near(k):
        return np.array([hull[max(0, i - k):i + k + 1].any() for i in range(w)])
    beside = near(SEA_BESIDE) & ~hull & (np.arange(w) % 4 != 3)
    return near(SEA_UNDER), beside


def far_stroke(x, d, ink, j, ox):
    """Whether the far sea's strokes ink screen column `x` on the image's row `j`, `d` rows above the waterline (a row
    of them every third row, from two above it up to the horizon): shorter and closer as they near the horizon, each
    stretch holding one, set by a hash, and none where the plate is inked on its row or the one above, a pixel round
    (plan_decor.c far_strokes)."""
    n = d // 3
    length = max(2, 7 - n)
    span = length + 3 + n
    cell, at = divmod(x + 64 * span, span)
    start = ((cell * 40503 + (16 + n) * 9973) & 0xFFFF) % (span - length + 1)
    if not start <= at < start + length:
        return False
    i = x - ox
    w = ink.shape[1]
    return not any(0 <= i + e < w and (ink[j, i + e] or ink[j - 1, i + e]) for e in (-1, 0, 1))


def sea_stroke(x, n):
    """Where the n-th row of strokes inks screen column `x`: None, or 0 on the row, or 1 a row below (the ends of a
    stroke of four or more dip, so each is a wavelet's crest). Each stretch holds one stroke, set along it by a hash of
    the stretch and the row so the strokes don't line up (plan_decor.c sea_strokes)."""
    _, span, length = SEA_STROKES[n]
    cell, at = divmod(x + 64 * span, span)
    start = ((cell * 40503 + n * 9973) & 0xFFFF) % (span - length + 1)
    if not start <= at < start + length:
        return None
    return int(length >= 4 and (at == start or at == start + length - 1))


def unframe(ink, depth=6, run=0.3):
    """The plate's frame away: any row or column within `depth` of an edge holding an unbroken run of ink over `run` of
    its length (a ruled line, where the drawing's lines are short), then any patch of ink lying wholly within `depth`
    of an edge (what is left of the frame, a corner of a cloud cut by it)."""
    ink = ink.copy()
    h, w = ink.shape

    def longest(v):
        best = cur = 0
        for b in v:
            cur = cur + 1 if b else 0
            best = max(best, cur)
        return best
    for k in list(range(depth)) + list(range(h - depth, h)):
        if longest(ink[k]) > run * w:
            ink[k] = False
    for k in list(range(depth)) + list(range(w - depth, w)):
        if longest(ink[:, k]) > run * h:
            ink[:, k] = False
    seen = np.zeros_like(ink)
    for y0, x0 in zip(*np.nonzero(ink)):
        if seen[y0, x0]:
            continue
        stack, cells = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for v in (y - 1, y, y + 1):
                for u in (x - 1, x, x + 1):
                    if 0 <= v < h and 0 <= u < w and ink[v, u] and not seen[v, u]:
                        seen[v, u] = True
                        stack.append((v, u))
        ys, xs = zip(*cells)
        if max(ys) < depth or min(ys) >= h - depth or max(xs) < depth or min(xs) >= w - depth:
            for y, x in cells:
                ink[y, x] = False
    return ink


SEA_INK = 0.13                                           # the share of the plate above its waterline inked


def sea_plate(file, crop, wipe, line):
    """A sea plate digitized (engraving), cut below its waterline and its frame away, its threshold sought so that its
    ink above the waterline covers SEA_INK of it whatever the etcher's tone: (ink, the waterline's row, the plate's
    height before the cut)."""
    lo, hi = 0.35, 0.85
    for _ in range(9):
        th = (lo + hi) / 2
        ink = unframe(engraving(THEMES / "sea" / "images" / file, crop, wipe, width=SEA_WIDTH, thresh=th, grow=0.15))
        water = round(line * ink.shape[0])
        if ink[:water + 1].mean() > SEA_INK:
            hi = th
        else:
            lo = th
    return clean(ink[:water + 1]), water, ink.shape[0]


def engraving(path, crop=None, wipe=(), width=WIDTH, thresh=0.78, grow=0.3):
    """A copper engraving's line work at `width` pixels wide, kept where a woodcut's reading would lose it: the dark
    lines first thickened by `grow` of a pixel's span on the scan (so a hair line survives the reduction), each pixel
    then judged against the paper round it (the plate's tone varies), and solid masses (close hatching run together)
    lightened to every other pixel, as an engraver tints. A bool array, True where the plate printed."""
    im = Image.open(path).convert("L")
    if crop:
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    im = ImageOps.autocontrast(im, cutoff=1)
    if wipe:
        a = np.asarray(im).copy()
        H, W = a.shape
        for x0, y0, x1, y1 in wipe:
            a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = int(np.percentile(a, 90))
        im = Image.fromarray(a)
    im = im.filter(ImageFilter.MinFilter(max(3, int(im.width / width * grow) | 1)))
    h = round(im.height * width / im.width)
    small = np.asarray(im.resize((width, h), Image.BOX), float)
    paper = np.asarray(Image.fromarray(small.astype("uint8")).filter(ImageFilter.MaxFilter(9))
                       .filter(ImageFilter.GaussianBlur(4)), float)
    ink = small < paper * thresh
    full = ink.copy()                                   # solid: inked with all eight neighbours inked
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            full &= np.roll(np.roll(ink, dy, 0), dx, 1)
    yy, xx = np.indices(ink.shape)
    ink &= ~(full & ((xx + yy) % 2 == 1))
    return clean(ink)


def digitize(path, crop=None, wipe=(), width=WIDTH, thresh=0.62, blur=1.2, rotate=0):
    """A woodcut's line work at `width` pixels wide (after turning it `rotate` degrees anticlockwise, the scan itself,
    before it is brought down to pixels): a bool array, True where the block printed. The words are wiped first, in
    the crop's own frame."""
    im = Image.open(path).convert("L")
    if crop:
        W, H = im.size
        im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
    im = ImageOps.autocontrast(im, cutoff=1)
    if wipe:                                            # (on the scan: the paper's tone over each word)
        a = np.asarray(im).copy()
        H, W = a.shape
        paper0 = int(np.percentile(a, 90))
        for x0, y0, x1, y1 in wipe:
            a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)] = paper0
        im = Image.fromarray(a)
        wipe = ()
    if rotate:
        im = im.rotate(rotate, resample=Image.BICUBIC, expand=True, fillcolor=int(np.percentile(np.asarray(im), 90)))
    paper = np.percentile(np.asarray(im, float) / 255, 90)
    im = im.filter(ImageFilter.GaussianBlur(blur * im.width / width / 3))
    h = round(im.height * width / im.width)
    ink = np.asarray(im.resize((width, h), Image.BOX), float) / 255 < paper * thresh
    for x0, y0, x1, y1 in wipe:
        ink[int(y0 * h):int(y1 * h), int(x0 * width):int(x1 * width)] = False
    return clean(ink)


def clean(ink, least=5):
    """The scan's leavings away: every patch of ink (eight ways connected) smaller than `least` pixels (the stars are
    larger), and every thin sliver (two pixels across or less) touching the edge, a neighbouring cut or the page's
    border."""
    h, w = ink.shape
    seen = np.zeros(ink.shape, bool)
    out = ink.copy()
    for y0, x0 in zip(*np.nonzero(ink)):
        if seen[y0, x0]:
            continue
        stack, cells = [(y0, x0)], []
        seen[y0, x0] = True
        while stack:
            y, x = stack.pop()
            cells.append((y, x))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    v, u = y + dy, x + dx
                    if 0 <= v < h and 0 <= u < w and ink[v, u] and not seen[v, u]:
                        seen[v, u] = True
                        stack.append((v, u))
        ys, xs = zip(*cells)
        edge = min(ys) == 0 or min(xs) == 0 or max(ys) == h - 1 or max(xs) == w - 1
        thin = max(xs) - min(xs) <= 2 or max(ys) - min(ys) <= 2
        if len(cells) < least or (edge and thin):
            for y, x in cells:
                out[y, x] = False
    return out


# the coding of scenes.bin: each pixel foretold from seven of its neighbours already decoded (two rows up: above it;
# one row up: from one left to two right; its own row: the two left of it, the first the high bit of the context), its
# chance of ink kept for each of the 128 contexts in twelve bits and moved a sixteenth of the way to each pixel as it
# comes, and the pixels so weighed coded with a binary range coder (LZMA's): line work in about a fifth of PackBits.
NEIGHBOURS = [(-2, 0), (-1, -1), (-1, 0), (-1, 1), (-1, 2), (0, -2), (0, -1)]
PROB_BITS, PROB_SHIFT = 12, 4


def contexts(ink):
    """Each pixel's context (an int array the image's shape)."""
    h, w = ink.shape
    p = np.pad(ink, ((2, 0), (2, 2))).astype(int)
    c = np.zeros((h, w), int)
    for dy, dx in NEIGHBOURS:
        c = (c << 1) | p[2 + dy:2 + dy + h, 2 + dx:2 + dx + w]
    return c


def encode(ink):
    """The image coded (plan_decor.c scene decodes it)."""
    prob = [1 << (PROB_BITS - 1)] * (1 << len(NEIGHBOURS))
    low, rng, cache, pending, out = 0, 0xFFFFFFFF, 0, 1, bytearray()

    def shift():
        nonlocal low, cache, pending
        if low < 0xFF000000 or low >= 1 << 32:
            carry, t = low >> 32, cache
            while pending:
                out.append((t + carry) & 255)
                t, pending = 0xFF, pending - 1
            cache = (low >> 24) & 255
        pending += 1
        low = (low << 8) & 0xFFFFFFFF
    for k, b in zip(contexts(ink).ravel().tolist(), ink.ravel().tolist()):
        p = prob[k]
        bound = (rng >> PROB_BITS) * p
        if b:
            low, rng, prob[k] = low + bound, rng - bound, p - (p >> PROB_SHIFT)
        else:
            rng, prob[k] = bound, p + (((1 << PROB_BITS) - p) >> PROB_SHIFT)
        while rng < 1 << 24:
            rng = (rng << 8) & 0xFFFFFFFF
            shift()
    for _ in range(5):
        shift()
    return bytes(out)


def decode(data, h, w):
    """encode's inverse (as plan_decor.c scene), to hold the two to each other."""
    prob = [1 << (PROB_BITS - 1)] * (1 << len(NEIGHBOURS))
    data = bytes(data) + bytes(8)
    rng, code, i = 0xFFFFFFFF, int.from_bytes(data[:5], "big") & 0xFFFFFFFF, 5
    p_ = np.zeros((h + 2, w + 4), bool)
    for y in range(h):
        for x in range(w):
            k = 0
            for dy, dx in NEIGHBOURS:
                k = (k << 1) | int(p_[2 + y + dy, 2 + x + dx])
            p = prob[k]
            bound = (rng >> PROB_BITS) * p
            if code < bound:
                rng, prob[k] = bound, p + (((1 << PROB_BITS) - p) >> PROB_SHIFT)
            else:
                code, rng, prob[k] = code - bound, rng - bound, p - (p >> PROB_SHIFT)
                p_[2 + y, 2 + x] = True
            while rng < 1 << 24:
                rng, code, i = (rng << 8) & 0xFFFFFFFF, ((code << 8) | data[i]) & 0xFFFFFFFF, i + 1
    return p_[2:, 2:-2]


# where a scene can ever show: on the card of either watch at any latitude (the Round 2's window moves and changes with
# it, the Time 2's only narrows), a pixel round; what is never on the card is never kept. For each screen a mask of its
# columns by the rows from its window's middle, and another by the rows from its window's top (the sea's plates hang
# from it), each offset by the screen's height, cached in build/ under the windows' own hash.
def reach():
    import hashlib
    import plates
    dials = {"emery": lambda lat: plates.RectDial(200, 228, lat, 0.0),
             "gabbro": lambda lat: plates.RoundDial(260, 260, lat, 0.0)}
    key = hashlib.sha1(b"".join(np.packbits(plates.window_mask(d(lat))).tobytes() + np.packbits(
        plates.inner_region(d(lat))).tobytes() for d in dials.values() for lat in (-90, -41, 0, 23, 67))).hexdigest()[:16]
    path = ROOT / "build" / f"scene-reach2-{key}.npz"
    if path.exists():
        z = np.load(path)
        return {a: {s: z[f"{a}-{s}"] for s in dials} for a in ("mid", "top")}
    out = {"mid": {}, "top": {}}
    for screen, dial in dials.items():
        acc = top = None
        for lat in range(-90, 91):
            d = dial(float(lat))
            inside, inner = plates.window_mask(d), plates.inner_region(d)
            card = inner & ~plates.grow(inside, 3) & ~plates.grow(~inner, 3)
            H, W = card.shape
            if acc is None:
                acc, top = np.zeros((2 * H, W), bool), np.zeros((2 * H, W), bool)
            rows = np.nonzero(inside.any(axis=1))[0]
            wy = (int(rows[0]) + int(rows[-1])) // 2
            acc[H - wy:2 * H - wy] |= card
            top[H - int(rows[0]):2 * H - int(rows[0])] |= card
        out["mid"][screen], out["top"][screen] = plates.grow(acc, 1), plates.grow(top, 1)
    path.parent.mkdir(exist_ok=True)
    np.savez_compressed(path, **{f"{a}-{s}": m for a, d in out.items() for s, m in d.items()})
    return out


def within_reach(ink, dx, dy, masks):
    """The image less what can never show, placed as the watch places it: its middle `dx` right of the screen's and
    `dy` below the anchor's row (the window's middle, or its top), with `masks` the anchor's."""
    h, w = ink.shape
    keep = np.zeros_like(ink)
    for m in masks.values():
        H2, W = m.shape
        ys, xs = np.mgrid[0:h, 0:w]
        Y, X = ys - h // 2 + dy + H2 // 2, xs + (W - w) // 2 + dx
        ok = (Y >= 0) & (Y < H2) & (X >= 0) & (X < W)
        keep[ok] |= m[Y[ok], X[ok]]
    return ink & keep


_SCENES = None


def scenes():
    """Every woodcut, in order: the zodiac's twelve (Aries first), the astronomer's (January first), the sea's (January
    first): (key, ink, dx, dy, the waterline's row or -1: then the plate hangs by it from the window's top, its dx, dy
    unused, the horizon's row). (key, ink, dx, dy: its middle right of and below the
    window's middle)"""
    global _SCENES
    if _SCENES is None:
        _SCENES = [(f"zodiac{k}", digitize(THEMES / "zodiac" / "images" / file, crop, wipe, width=width, rotate=rot),
                    dx, dy) for k, (file, crop, wipe, rot, width, dx, dy) in enumerate(ZODIAC)]
        _SCENES += [(f"astronomer{k}", engraving(THEMES / "astronomer" / "images" / file, crop, wipe, width=width),
                     dx, dy) for k, (file, crop, wipe, width, dx, dy) in enumerate(ASTRONOMER)]
        _SCENES = [s + (-1, -1) for s in _SCENES]
        masks = reach()
        _SCENES = [(key, within_reach(ink, dx, dy, masks["mid"]), dx, dy, water, far)
                   for key, ink, dx, dy, water, far in _SCENES]
        for k, (file, crop, wipe, far, line) in enumerate(SEA):
            ink, water, full = sea_plate(file, crop, wipe, line)   # (cut below the waterline: the watch draws the sea)
            keep = np.zeros_like(ink)                    # (where it can show, as the tide carries it)
            for shift in range(-TIDE_SHIFT, TIDE_SHIFT + 1):
                keep |= within_reach(np.ones_like(ink), 0, ink.shape[0] // 2 - (SEA_ABOVE + water + shift), masks["top"])
            _SCENES.append((f"sea{k}", ink & keep, 0, 0, water, round(far * full)))
    return _SCENES


def blob():
    """scenes.bin: the count (uint16), then for each its offset (uint32, from the file's start), width and height
    (uint16), where its middle stands right of and below the window's middle (int16 each, pixels), its waterline's
    and its horizon's rows (int16 each, -1 none), then the images,
    each coded by encode (at most 264 pixels wide: the decoder's rows), then 64 zeros (the watch reads 64 bytes at a time,
    and a read past a resource's end may bring nothing)."""
    items = scenes()
    head = 2 + 16 * len(items)
    table, data = bytearray(len(items).to_bytes(2, "little")), bytearray()
    for key, ink, dx, dy, water, far in items:
        h, w = ink.shape
        table += ((head + len(data)).to_bytes(4, "little") + w.to_bytes(2, "little") + h.to_bytes(2, "little") +
                  dx.to_bytes(2, "little", signed=True) + dy.to_bytes(2, "little", signed=True) +
                  water.to_bytes(2, "little", signed=True) + far.to_bytes(2, "little", signed=True))
        assert w <= 264, key
        data += encode(ink)
    return bytes(table + data + bytes(64))
