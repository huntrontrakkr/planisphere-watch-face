"""A monoline stroke font in the manner of the reference dial: round ends,
geometric bowls, a 3 of two stacked rounds, 6 and 9 as a round bowl with a
straight tangent tail. Digits, the capitals of the weekdays, and an emblem
(an open hand, our own drawing) for the 12 o'clock place.

Glyphs are strokes in a box one unit tall (y down, 0 = cap top, 1 = baseline);
`render(ch, cap_px)` draws them with round caps and returns alpha 0..1.
"""
import math
import numpy as np
from PIL import Image, ImageDraw

STROKE = 0.17          # stroke width, in cap heights


def arc(cx, cy, rx, ry, a0, a1, n=None):
    """Points along an ellipse arc; angles in degrees, 0 = right, 90 = down."""
    n = n or max(6, int(abs(a1 - a0) / 8))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def tangent_tail(cx, cy, r, px, py, side):
    """From (px, py) to the tangent point on the circle (cx, cy, r); side picks which tangent."""
    dx, dy = px - cx, py - cy
    d = math.hypot(dx, dy)
    a = math.atan2(dy, dx) + side * math.acos(r / d)
    return (cx + r * math.cos(a), cy + r * math.sin(a)), math.degrees(a)


S = STROKE / 2         # keep strokes inside the box


def glyph(ch):
    """(advance width, list of polylines)."""
    w = 0.62
    t, b = S, 1 - S                     # stroke centre lines at the top and the baseline
    if ch == "0":
        r = (w - 2 * S) / 2
        return w, [arc(w / 2, t + r, r, r, 180, 360) + arc(w / 2, b - r, r, r, 0, 180) + [(S, t + r)]]
    if ch == "1":
        x = w * 0.58
        return w, [[(x - 0.2, t + 0.16), (x, t), (x, b)]]
    if ch == "2":
        r = (w - 2 * S) / 2
        top = arc(w / 2, t + r, r, r, 190, 360 + 30)
        return w, [top + [(S, b), (w - S, b)]]
    if ch == "3":
        r1 = (w - 2 * S) / 2 * 0.86
        r2 = (w - 2 * S) / 2
        mid = t + 2 * r1
        upper = arc(S + r2 * 0.95, t + r1, r1, r1, 200, 450)              # ends at the waist, pointing left
        lower = arc(S + r2, b - r2, r2, (b - mid) / 2, 270, 270 + 235)
        return w, [upper, lower]
    if ch == "4":
        x = w * 0.68
        return w, [[(x, b), (x, t), (S, 0.68), (w - S + 0.02, 0.68)]]
    if ch == "5":
        r = (w - 2 * S) / 2
        bowl_cy = b - r * 1.05
        return w, [[(w - S, t), (S + 0.05, t), (S, bowl_cy - r * 0.55)] +
                   arc(w / 2, bowl_cy, r, r * 1.05, 200, 360 + 145)]
    if ch == "6":
        r = (w - 2 * S) / 2
        cx, cy = w / 2, b - r
        (tx, ty), a = tangent_tail(cx, cy, r, w * 0.70, t, -1)
        return w, [arc(cx, cy, r, r, 0, 360), [(tx, ty), (w * 0.70, t)]]
    if ch == "7":
        return w, [[(S, t), (w - S, t), (w * 0.34, b)]]
    if ch == "8":
        r1 = (w - 2 * S) / 2 * 0.82
        r2 = (w - 2 * S) / 2
        return w, [arc(w / 2, t + r1, r1, r1, 0, 360), arc(w / 2, b - r2, r2, r2 * 1.02, 0, 360)]
    if ch == "9":
        r = (w - 2 * S) / 2
        cx, cy = w / 2, t + r
        (tx, ty), a = tangent_tail(cx, cy, r, w * 0.30, b, -1)
        return w, [arc(cx, cy, r, r, 0, 360), [(tx, ty), (w * 0.30, b)]]
    # weekday capitals
    W = 0.64
    if ch == "A":
        return W, [[(S, b), (W / 2, t), (W - S, b)], [(W * 0.22, 0.68), (W * 0.78, 0.68)]]
    if ch == "D":
        r = (b - t) / 2
        return W, [[(S, t), (W - S - r, t)] + arc(W - S - r, t + r, r, r, 270, 450) + [(S, b), (S, t)]]
    if ch == "E":
        return W * 0.85, [[(W * 0.85 - S, t), (S, t), (S, b), (W * 0.85 - S, b)], [(S, 0.5), (W * 0.75, 0.5)]]
    if ch == "F":
        return W * 0.85, [[(W * 0.85 - S, t), (S, t), (S, b)], [(S, 0.5), (W * 0.72, 0.5)]]
    if ch == "H":
        return W, [[(S, t), (S, b)], [(W - S, t), (W - S, b)], [(S, 0.5), (W - S, 0.5)]]
    if ch == "I":
        return 0.24, [[(0.12, t), (0.12, b)]]
    if ch == "M":
        return 0.82, [[(S, b), (S, t), (0.41, 0.72), (0.82 - S, t), (0.82 - S, b)]]
    if ch == "N":
        return W, [[(S, b), (S, t), (W - S, b), (W - S, t)]]
    if ch == "O":
        r = (b - t) / 2
        return 1 - 2 * S + 2 * S, [arc(0.5, 0.5, r, r, 0, 360)]
    if ch == "R":
        r = 0.25 - S / 2
        return W, [[(S, b), (S, t), (W - S - r, t)] + arc(W - S - r, t + r, r, r, 270, 450) + [(S, t + 2 * r)],
                   [(W * 0.5, t + 2 * r), (W - S, b)]]
    if ch == "S":
        r1 = 0.25 - S / 2
        r2 = 0.25 - S / 2
        return W * 0.9, [arc(W * 0.45, t + r1, r1 * 1.1, r1, 340, 90 + 180 + 0) [:0] +
                         arc(W * 0.45, t + r1, r1 * 1.15, r1, -20, -270) +
                         arc(W * 0.45, b - r2, r2 * 1.15, r2, -90, 160)]
    if ch == "T":
        return W, [[(S, t), (W - S, t)], [(W / 2, t), (W / 2, b)]]
    if ch == "U":
        r = (W - 2 * S) / 2
        return W, [[(S, t), (S, b - r)] + arc(W / 2, b - r, r, r, 180, 0) + [(W - S, t)]]
    if ch == "V":
        return W, [[(S, t), (W / 2, b), (W - S, t)]]
    if ch == "X":
        return W, [[(S, t), (W - S, b)], [(W - S, t), (S, b)]]
    if ch == "K":
        return W, [[(S, t), (S, b)], [(W - S, t), (S + 0.02, 0.6)], [(S + 0.16, 0.5), (W - S, b)]]
    if ch == "W":
        return 0.9, [[(S, t), (0.25, b), (0.45, t + 0.2), (0.65, b), (0.9 - S, t)]]
    raise KeyError(ch)


class Pen:
    """Unit-box drawing (cap height 1, y down) onto a supersampled canvas."""
    def __init__(self, d, scale, pad):
        self.d, self.s, self.p = d, scale, pad

    def pt(self, x, y):
        return (self.p + x * self.s, self.p + y * self.s)

    def line(self, x0, y0, x1, y1, w, fill=255):
        a, b = self.pt(x0, y0), self.pt(x1, y1)
        r = w * self.s / 2
        self.d.line([a, b], fill=fill, width=max(1, int(round(w * self.s))))
        for x, y in (a, b):
            self.d.ellipse([x - r, y - r, x + r, y + r], fill=fill)

    def path(self, pts, w, fill=255):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            self.line(x0, y0, x1, y1, w, fill)

    def disc(self, x, y, r, fill=255):
        (cx, cy) = self.pt(x, y)
        self.d.ellipse([cx - r * self.s, cy - r * self.s, cx + r * self.s, cy + r * self.s], fill=fill)

    def box(self, x0, y0, x1, y1, r, fill=255):
        self.d.rounded_rectangle([*self.pt(x0, y0), *self.pt(x1, y1)], radius=r * self.s, fill=fill)

    def poly(self, pts, fill=255):
        self.d.polygon([self.pt(x, y) for x, y in pts], fill=fill)


# Emblems for the 12 o'clock place: bold silhouettes with gaps of at least a
# pixel at 11 px. All our own drawings. Each entry: (width, draw(pen)).
def _hand(p):                      # a raised open hand
    fw, pitch = 0.15, 0.235
    xs = [0.30 + k * pitch for k in range(3)]
    for x, tp in zip(xs, [0.16, 0.08, 0.16]):
        p.line(x, tp, x, 0.62, fw)
    p.box(xs[0] - fw / 2, 0.55, xs[-1] + fw / 2, 0.98, 0.16)
    p.line(0.17, 0.42, xs[0] - 0.02, 0.74, fw)


def _vulcan(p):                    # the Vulcan salute: fingers parted between middle and ring
    p.box(0.22, 0.52, 0.86, 0.98, 0.15)
    p.line(0.40, 0.62, 0.30, 0.10, 0.25)          # index and middle together
    p.line(0.70, 0.62, 0.82, 0.14, 0.25)          # ring and little finger together
    p.line(0.30, 0.14, 0.38, 0.62, 0.035, fill=0)  # the seams within each pair
    p.line(0.82, 0.18, 0.72, 0.62, 0.035, fill=0)
    p.line(0.26, 0.76, 0.06, 0.48, 0.16)          # thumb


def _thumbs(p):                    # thumbs up
    p.box(0.33, 0.44, 0.94, 0.97, 0.14)           # fist
    p.line(0.42, 0.50, 0.44, 0.07, 0.22)          # thumb
    for y in (0.60, 0.73, 0.86):                  # finger creases
        p.line(0.62, y, 0.96, y, 0.05, fill=0)
    p.box(0.06, 0.48, 0.27, 0.97, 0.04)           # cuff


def _peace(p):                     # two fingers raised in a V
    p.box(0.24, 0.55, 0.86, 0.98, 0.15)
    p.line(0.44, 0.64, 0.28, 0.07, 0.17)
    p.line(0.64, 0.64, 0.80, 0.09, 0.17)
    p.line(0.34, 0.70, 0.78, 0.70, 0.05, fill=0)  # folded fingers' edge


def _heart(p):
    p.disc(0.30, 0.34, 0.25)
    p.disc(0.70, 0.34, 0.25)
    p.poly([(0.06, 0.42), (0.94, 0.42), (0.50, 0.96)])


def _star(p):
    pts = []
    for k in range(10):
        r = 0.52 if k % 2 == 0 else 0.21
        a = math.radians(-90 + k * 36)
        pts.append((0.5 + r * math.cos(a), 0.55 + r * math.sin(a)))
    p.poly(pts)


def _bolt(p):
    p.poly([(0.62, 0.0), (0.16, 0.58), (0.46, 0.58), (0.34, 1.0), (0.84, 0.40), (0.54, 0.40), (0.72, 0.0)])


def _moon(p):
    p.disc(0.48, 0.5, 0.47)
    p.disc(0.70, 0.38, 0.40, fill=0)


def _sun(p):
    p.disc(0.5, 0.5, 0.21)
    for k in range(8):
        a = math.radians(k * 45)
        p.line(0.5 + 0.33 * math.cos(a), 0.5 + 0.33 * math.sin(a), 0.5 + 0.46 * math.cos(a), 0.5 + 0.46 * math.sin(a), 0.11)


def _infinity(p):
    pts = []
    for k in range(65):
        t = 2 * math.pi * k / 64
        den = 1 + math.sin(t) ** 2
        pts.append((0.65 + 0.58 * math.cos(t) / den, 0.5 + 0.58 * math.sin(t) * math.cos(t) / den))
    p.path(pts, 0.15)


def _spiral(p):                    # a little labyrinth turn: the face's own sign
    pts = []
    for k in range(80):
        t = k / 79
        a = 2 * math.pi * 2.0 * t
        r = 0.05 + 0.40 * t
        pts.append((0.5 + r * math.cos(a), 0.5 + r * math.sin(a)))
    p.path(pts, 0.12)


def _eye(p):
    p.poly([(0.02, 0.5)] + [(0.5 + 0.48 * math.cos(math.radians(a)), 0.5 - 0.34 * math.sin(math.radians(a)))
                             for a in range(180, -1, -15)][1:-1] + [(0.98, 0.5)] +
           [(0.5 + 0.48 * math.cos(math.radians(a)), 0.5 + 0.34 * math.sin(math.radians(a)))
            for a in range(0, 181, 15)][1:-1])
    p.disc(0.5, 0.5, 0.23, fill=0)
    p.disc(0.5, 0.5, 0.13)


def _paw(p):
    p.disc(0.5, 0.70, 0.24)
    for x, y in ((0.18, 0.40), (0.38, 0.20), (0.62, 0.20), (0.82, 0.40)):
        p.disc(x, y, 0.12)


def _anchor(p):
    p.line(0.5, 0.20, 0.5, 0.92, 0.12)
    p.d.ellipse([*p.pt(0.38, 0.0), *p.pt(0.62, 0.24)], outline=255, width=int(round(0.09 * p.s)))
    p.line(0.28, 0.36, 0.72, 0.36, 0.10)
    p.path([(0.10, 0.62), (0.18, 0.80), (0.36, 0.92), (0.5, 0.94), (0.64, 0.92), (0.82, 0.80), (0.90, 0.62)], 0.11)


EMBLEM_SHAPES = {"h": (0.92, _hand), "v": (0.92, _vulcan), "t": (1.0, _thumbs), "p": (0.92, _peace),
                 "q": (1.0, _heart), "s": (1.0, _star), "b": (0.88, _bolt), "m": (0.96, _moon), "u": (1.0, _sun),
                 "i": (1.3, _infinity), "z": (1.0, _spiral), "e": (1.0, _eye), "w": (1.0, _paw), "a": (1.0, _anchor)}


def render(ch, cap, ss=8):
    """Alpha (h x w, 0..1) of `ch` at a cap height of `cap` pixels."""
    if ch in EMBLEM_SHAPES:
        width, draw = EMBLEM_SHAPES[ch]
        scale = cap * ss
        pad = int(math.ceil(STROKE * scale))
        W, H = int(math.ceil(width * scale)) + 2 * pad, int(math.ceil(scale)) + 2 * pad
        img = Image.new("L", (W, H), 0)
        draw(Pen(ImageDraw.Draw(img), scale, pad))
        a = np.asarray(img, np.float32) / 255
        h2, w2 = H // ss, W // ss
        return a[: h2 * ss, : w2 * ss].reshape(h2, ss, w2, ss).mean(axis=(1, 3)), pad / ss
    adv, lines = glyph(ch)
    scale = cap * ss
    pad = int(math.ceil(STROKE * scale))
    W = int(math.ceil(adv * scale)) + 2 * pad
    H = int(math.ceil(scale)) + 2 * pad
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    sw = STROKE * scale
    for pl in lines:
        pts = [(pad + x * scale, pad + y * scale) for x, y in pl]
        if len(pts) > 1:
            d.line(pts, fill=255, width=max(1, int(round(sw))), joint="curve")
        for x, y in (pts[0], pts[-1]):
            d.ellipse([x - sw / 2, y - sw / 2, x + sw / 2, y + sw / 2], fill=255)
    a = np.asarray(img, np.float32) / 255
    h2, w2 = H // ss, W // ss
    a = a[: h2 * ss, : w2 * ss].reshape(h2, ss, w2, ss).mean(axis=(1, 3))
    return a, pad / ss


if __name__ == "__main__":
    # specimen
    import sys
    chars = "0123456789 ADEFHIMNORSTUVWX " + "".join(EMBLEM_SHAPES)
    rows = []
    for cap in (11, 13, 40):
        tiles = []
        for c in chars:
            if c == " ":
                tiles.append(np.zeros((int(cap * 1.6), cap // 2)))
                continue
            a, _ = render(c, cap)
            t = np.zeros((int(cap * 1.6), a.shape[1] + 2))
            t[: a.shape[0], 1: 1 + a.shape[1]] = a[: t.shape[0]]
            tiles.append(t)
        rows.append(np.hstack(tiles))
    W = max(r.shape[1] for r in rows)
    sheet = np.vstack([np.pad(r, ((4, 4), (0, W - r.shape[1]))) for r in rows])
    Image.fromarray((255 - sheet * 255).astype(np.uint8)).resize((sheet.shape[1] * 2, sheet.shape[0] * 2), Image.NEAREST).save(sys.argv[1] if len(sys.argv) > 1 else "specimen.png")
