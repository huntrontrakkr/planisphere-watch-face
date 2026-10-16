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


def packbits(b):
    """PackBits (as Apple's): a count n then n + 1 bytes as they are (n < 128), or 257 - n then a byte to repeat."""
    out, i = bytearray(), 0
    while i < len(b):
        j = i
        while j < len(b) and j - i < 128 and b[j] == b[i]:
            j += 1
        if j - i >= 3:
            out += bytes([257 - (j - i), b[i]])
            i = j
            continue
        lit = bytearray()
        while i < len(b) and len(lit) < 128 and not (i + 2 < len(b) and b[i] == b[i + 1] == b[i + 2]):
            lit.append(b[i])
            i += 1
        out += bytes([len(lit) - 1]) + lit
    return bytes(out)


_SCENES = None


def scenes():
    """Every woodcut, in order: the zodiac's twelve (Aries first). (key, ink, dx, dy: its middle right of and below the
    window's middle)"""
    global _SCENES
    if _SCENES is None:
        _SCENES = [(f"zodiac{k}", digitize(THEMES / "zodiac" / "images" / file, crop, wipe, width=width, rotate=rot),
                    dx, dy) for k, (file, crop, wipe, rot, width, dx, dy) in enumerate(ZODIAC)]
    return _SCENES


def blob():
    """scenes.bin: the count (uint16), then for each its offset (uint32, from the file's start), width and height
    (uint16), and where its middle stands right of and below the window's middle (int16 each, pixels), then the images:
    rows of bits, the first pixel the high bit, each row ceil(width / 8) bytes, the whole PackBits-coded."""
    items = scenes()
    head = 2 + 12 * len(items)
    table, data = bytearray(len(items).to_bytes(2, "little")), bytearray()
    for key, ink, dx, dy in items:
        h, w = ink.shape
        table += ((head + len(data)).to_bytes(4, "little") + w.to_bytes(2, "little") + h.to_bytes(2, "little") +
                  dx.to_bytes(2, "little", signed=True) + dy.to_bytes(2, "little", signed=True))
        data += packbits(np.packbits(ink, axis=1).tobytes())
    return bytes(table + data)
