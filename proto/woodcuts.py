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
# columns by the rows from its window's middle (offset by the screen's height), cached in build/ under the windows' own
# hash.
def reach():
    import hashlib
    import plates
    dials = {"emery": lambda lat: plates.RectDial(200, 228, lat, 0.0),
             "gabbro": lambda lat: plates.RoundDial(260, 260, lat, 0.0)}
    key = hashlib.sha1(b"".join(np.packbits(plates.window_mask(d(lat))).tobytes() + np.packbits(
        plates.inner_region(d(lat))).tobytes() for d in dials.values() for lat in (-90, -41, 0, 23, 67))).hexdigest()[:16]
    path = ROOT / "build" / f"scene-reach-{key}.npz"
    if path.exists():
        z = np.load(path)
        return {s: z[s] for s in dials}
    out = {}
    for screen, dial in dials.items():
        acc = None
        for lat in range(-90, 91):
            d = dial(float(lat))
            inside, inner = plates.window_mask(d), plates.inner_region(d)
            card = inner & ~plates.grow(inside, 3) & ~plates.grow(~inner, 3)
            H, W = card.shape
            if acc is None:
                acc = np.zeros((2 * H, W), bool)
            rows = np.nonzero(inside.any(axis=1))[0]
            wy = (int(rows[0]) + int(rows[-1])) // 2
            acc[H - wy:2 * H - wy] |= card
        out[screen] = plates.grow(acc, 1)
    path.parent.mkdir(exist_ok=True)
    np.savez_compressed(path, **out)
    return out


def within_reach(ink, dx, dy, masks):
    """The image less what can never show, placed as the watch places it."""
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
    """Every woodcut, in order: the zodiac's twelve (Aries first), the astronomer's (January first). (key, ink, dx, dy: its middle right of and below the
    window's middle)"""
    global _SCENES
    if _SCENES is None:
        _SCENES = [(f"zodiac{k}", digitize(THEMES / "zodiac" / "images" / file, crop, wipe, width=width, rotate=rot),
                    dx, dy) for k, (file, crop, wipe, rot, width, dx, dy) in enumerate(ZODIAC)]
        _SCENES += [(f"astronomer{k}", engraving(THEMES / "astronomer" / "images" / file, crop, wipe, width=width),
                     dx, dy) for k, (file, crop, wipe, width, dx, dy) in enumerate(ASTRONOMER)]
        masks = reach()
        _SCENES = [(key, within_reach(ink, dx, dy, masks), dx, dy) for key, ink, dx, dy in _SCENES]
    return _SCENES


def blob():
    """scenes.bin: the count (uint16), then for each its offset (uint32, from the file's start), width and height
    (uint16), and where its middle stands right of and below the window's middle (int16 each, pixels), then the images,
    each coded by encode (at most 264 pixels wide: the decoder's rows), then 64 zeros (the watch reads 64 bytes at a time,
    and a read past a resource's end may bring nothing)."""
    items = scenes()
    head = 2 + 12 * len(items)
    table, data = bytearray(len(items).to_bytes(2, "little")), bytearray()
    for key, ink, dx, dy in items:
        h, w = ink.shape
        table += ((head + len(data)).to_bytes(4, "little") + w.to_bytes(2, "little") + h.to_bytes(2, "little") +
                  dx.to_bytes(2, "little", signed=True) + dy.to_bytes(2, "little", signed=True))
        assert w <= 264, key
        data += encode(ink)
    return bytes(table + data + bytes(64))
