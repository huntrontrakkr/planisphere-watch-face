"""Almanac vignettes in pixels for the Time 2's corners, drawn as woodcuts are
cut: solid shapes, hatching for shade, a face on the Sun. Each returns a small
array of palette roles (0 ground, 1 ink, 2 accent) to colour as the plate likes."""
import math

import numpy as np


def sun(r=5):
    """The Sun with a face, as woodcuts cut it: an outlined disc, eight long rays and eight short,
    two eyes and a smile."""
    n = 2 * (r + 6) + 1
    c = n // 2
    a = np.zeros((n, n), np.uint8)
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c)
            if d <= r + 0.5:
                a[y, x] = 1 if d > r - 0.55 else 3        # outline; the face (3: the ground's colour)
    for k in range(16):
        ang = k * math.pi / 8
        L = 4.8 if k % 2 == 0 else 2.8
        for t in np.linspace(r + 1.7, r + 1.4 + L, 14):
            x, y = int(round(c + t * math.sin(ang))), int(round(c - t * math.cos(ang)))
            if 0 <= x < n and 0 <= y < n:
                a[y, x] = 2 if k % 2 == 0 else 1
    for x, y in ((c - 2, c - 1), (c + 2, c - 1), (c - 2, c + 2), (c - 1, c + 3), (c, c + 3), (c + 1, c + 3), (c + 2, c + 2)):
        a[y, x] = 1                                    # eyes and a smile
    return a


def moon(phase, waxing, r=8):
    """The Moon in its phase: its lit part solid, the rest hatched as an engraver would shade it, outlined."""
    n = 2 * r + 3
    c = n // 2
    a = np.zeros((n, n), np.uint8)
    k = 1 - 2 * phase                                  # the terminator: x = k sqrt(r^2 - y^2), lit beyond it
    for y in range(n):
        for x in range(n):
            px, py = x - c, y - c
            d = math.hypot(px, py)
            if d > r + 0.5:
                continue
            half = math.sqrt(max(0.0, r * r - py * py))
            side = px if waxing else -px
            lit = side > k * half
            if d > r - 0.6:
                a[y, x] = 1                            # the outline
            elif lit:
                a[y, x] = 2
            elif (x + y) % 3 == 0:
                a[y, x] = 1                            # hatching
    return a


def star(r=7):
    """An eight-pointed star: four long points, four short."""
    n = 2 * r + 1
    c = r
    a = np.zeros((n, n), np.uint8)
    for k in range(8):
        ang = k * math.pi / 4
        L = r if k % 2 == 0 else r * 0.55
        for t in np.linspace(0, L, 3 * r):
            w = max(0.0, 1.2 * (1 - t / L))
            for o in np.linspace(-w, w, 5):
                x = int(round(c + t * math.sin(ang) + o * math.cos(ang)))
                y = int(round(c - t * math.cos(ang) + o * math.sin(ang)))
                if 0 <= x < n and 0 <= y < n:
                    a[y, x] = 2 if k % 2 == 0 else 1
    a[c, c] = 1
    return a


def quadrant(r=13):
    """An astronomer's quadrant: two edges, the arc with its degrees, and a plumb line."""
    n = r + 2
    a = np.zeros((n, n), np.uint8)
    for t in range(r + 1):
        a[1, 1 + t] = 1                                # the top edge
        a[1 + t, 1] = 1                                # the left edge
    for k in range(40):
        ang = k * (math.pi / 2) / 39
        x, y = int(round(1 + r * math.cos(ang))), int(round(1 + r * math.sin(ang)))
        if x < n and y < n:
            a[y, x] = 1
    for k in range(1, 9):                              # degree ticks
        ang = k * (math.pi / 2) / 9
        x, y = int(round(1 + (r - 1.6) * math.cos(ang))), int(round(1 + (r - 1.6) * math.sin(ang)))
        a[y, x] = 1
    ang = math.radians(50)                             # the plumb line, and its bob
    for t in np.linspace(0, r - 3, 20):
        x, y = int(round(1 + t * math.cos(ang))), int(round(1 + t * math.sin(ang)))
        a[y, x] = 2
    bx, by = int(round(1 + (r - 3) * math.cos(ang))), int(round(1 + (r - 3) * math.sin(ang)))
    for ox, oy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        if by + oy < n and bx + ox < n:
            a[by + oy, bx + ox] = 2
    return a


def paint(img, emblem, x, y, colours):
    """Paint `emblem` centred at (x, y) with colours for roles 1 and 2."""
    h, w = emblem.shape
    x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    for j in range(h):
        for i in range(w):
            v = emblem[j, i]
            if v and v in colours and 0 <= y0 + j < img.shape[0] and 0 <= x0 + i < img.shape[1]:
                img[y0 + j, x0 + i] = colours[v]
    return x0, y0, x0 + w, y0 + h
