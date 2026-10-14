"""Ornament in pixels.

  sol(r)        the Sun with a face, its rays alternately straight and wavy (after the Sun of May)
  wind(facing)  a wind's head blowing, as old maps put the winds round their edges
  tiny(text)    capitals five pixels tall, for small names on the card
  little_sun()  a small rayed Sun, for the pointer on the ring

Each returns an array of roles: 0 nothing, 1 ink (outline), 2 colour (fill), 3 light (highlight),
4 ground (paper showing through)."""
import math

import numpy as np

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
    "8": [".#.", "#.#", ".#.", "#.#", ".#."], "9": [".#.", "#.#", ".##", "..#", "##."], "°": ["#", ".", ".", ".", "."],
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


def sol(r=5, rays=16):
    """The Sun of May: a disc with a face, and rays turning between straight and wavy."""
    reach = r + 7
    n = 2 * reach + 1
    c = reach
    a = np.zeros((n, n), np.uint8)
    for k in range(rays):
        ang = 2 * math.pi * k / rays - math.pi / 2
        wavy = k % 2 == 1
        L = 6.0 if wavy else 5.0
        for t in np.linspace(r + 1.2, r + 1.0 + L, 30):
            off = math.sin((t - r) * 2.3) * 0.9 if wavy else 0.0
            x = c + t * math.cos(ang) - off * math.sin(ang)
            y = c + t * math.sin(ang) + off * math.cos(ang)
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < n and 0 <= yi < n and a[yi, xi] == 0:
                a[yi, xi] = 2 if not wavy else 1
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - c, y - c)
            if d <= r + 0.5:
                a[y, x] = 1 if d > r - 0.5 else 2
    # the face: brows, eyes, nose, mouth; a light on the upper cheek
    for x, y in ((c - 3, c - 3), (c - 2, c - 3), (c + 2, c - 3), (c + 3, c - 3)):
        a[y, x] = 1
    for x, y in ((c - 2, c - 1), (c + 2, c - 1)):
        a[y, x] = 1
    a[c, c] = 1
    a[c + 1, c] = 1
    for x in (c - 1, c, c + 1):
        a[c + 3, x] = 1
    a[c + 2, c - 2] = 1
    a[c + 2, c + 2] = 1
    for x, y in ((c - 3, c - 1), (c + 3, c - 1), (c - 1, c - 2), (c + 1, c - 2)):
        if a[y, x] == 2:
            a[y, x] = 3
    return a


def little_sun():
    """A small rayed Sun for the ring's pointer."""
    return np.array([[{".": 0, "#": 1, "o": 2}[ch] for ch in row] for row in [
        "...#...",
        ".#...#.",
        "..ooo..",
        "#.ooo.#",
        "..ooo..",
        ".#...#.",
        "...#...",
    ]], np.uint8)


def wind(toward_deg=0.0):
    """A wind's head blowing toward `toward_deg` (screen degrees, 0 to the right, 90 down): an outlined
    face, eyes shut with the effort, cheeks puffed pink, a round mouth on the side it blows toward,
    a scalloped edge of cloud behind it, and three streams fanning out from just beyond the lips."""
    W = H = 42
    ux, uy = math.cos(math.radians(toward_deg)), math.sin(math.radians(toward_deg))
    px_, py_ = -uy, ux
    r = 6.5
    cx, cy = W / 2 - 6.5 * ux, H / 2 - 6.5 * uy
    a = np.zeros((H, W), np.uint8)
    def put(x, y, v, over=False):
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < W and 0 <= yi < H and (over or a[yi, xi] == 0):
            a[yi, xi] = v
    # a scalloped edge of cloud round the back of the head
    for off in range(-90, 91, 30):
        ang = math.radians(toward_deg + 180 + off)
        bx, by = cx + (r + 1.2) * math.cos(ang), cy + (r + 1.2) * math.sin(ang)
        for t in np.linspace(-95, 95, 14):
            aa = ang + math.radians(t)
            put(bx + 2.1 * math.cos(aa), by + 2.1 * math.sin(aa), 1)
    # the face: paper inside an outline
    for y in range(H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d <= r + 0.45:
                a[y, x] = 1 if d > r - 0.55 else 2
    # eyes shut with the effort: a little arch each, either side, a touch toward the wind
    for side in (-1, 1):
        ex = cx + 0.8 * ux + side * 2.5
        ey = cy - 1.6 + 0.6 * uy
        for dx, dy in ((-1, 0), (0, -1), (1, 0)):
            put(ex + dx, ey + dy, 1, over=True)
    # puffed cheeks, pink
    for side in (-1, 1):
        bx = cx + 2.6 * ux + side * 2.6 * abs(uy if abs(uy) > 0.3 else 1) * (1 if abs(ux) < 0.9 else 0) + side * 2.4 * (1 if abs(ux) >= 0.9 else 0)
        by = cy + 1.6 + 1.6 * uy
        for ox, oy in ((0, 0), (1, 0)):
            xi, yi = int(round(bx)) + ox, int(round(by)) + oy
            if 0 <= xi < W and 0 <= yi < H and a[yi, xi] == 2:
                a[yi, xi] = 3
    # the round mouth at the face's edge toward the wind
    lx, ly = cx + (r + 0.4) * ux, cy + (r + 0.4) * uy + 0.8
    for y in range(int(ly) - 2, int(ly) + 3):
        for x in range(int(lx) - 2, int(lx) + 3):
            d = math.hypot(x - lx, y - ly)
            if 0 <= x < W and 0 <= y < H:
                if 0.6 < d <= 1.6:
                    a[y, x] = 1
                elif d <= 0.6:
                    a[y, x] = 4
    # three streams fanning out from just beyond the lips, curling apart, each broken once
    for k, spread in enumerate((-24, 0, 24)):
        ang = math.radians(toward_deg + spread)
        vx, vy = math.cos(ang), math.sin(ang)
        curl = (-1, 0, 1)[k]
        for t in np.linspace(4.2, 17.0, 60):
            if 9.5 < t < 10.8:
                continue
            bend = 0.025 * (t - 4) ** 2 * curl
            put(lx + t * vx + bend * px_, ly + t * vy + bend * py_, 1)
    return a


def paint(img, art, x, y, colours, where=None):
    """Paint `art` centred at (x, y); colours maps role -> RGB (roles missing from it are skipped)."""
    h, w = art.shape
    x0, y0 = int(round(x - w / 2)), int(round(y - h / 2))
    for j in range(h):
        for i in range(w):
            v = art[j, i]
            yy, xx = y0 + j, x0 + i
            if v and v in colours and 0 <= yy < img.shape[0] and 0 <= xx < img.shape[1] and (where is None or where[yy, xx]):
                img[yy, xx] = colours[v]
    return x0, y0, x0 + w, y0 + h


if __name__ == "__main__":
    from pathlib import Path
    from PIL import Image
    ROOT = Path(__file__).resolve().parents[1]
    img = np.zeros((48, 240, 3)) + (255, 255, 170)
    paint(img, sol(), 20, 20, {1: (170, 85, 0), 2: (255, 170, 0), 3: (255, 255, 85)})
    for i, ang in enumerate((40, 140, -40, -140)):
        paint(img, wind(ang), 64 + i * 42, 22, {1: (0, 0, 0), 2: (255, 255, 255), 3: (255, 170, 170), 4: (170, 170, 170)})
    paint(img, little_sun(), 228, 22, {1: (170, 85, 0), 2: (255, 170, 0)})
    t = tiny("KAIKIAS SKIRON EUROS LIPS")
    for j, i in zip(*np.nonzero(t)):
        img[42 + j, 60 + i] = (170, 0, 0)
    Image.fromarray(img.astype(np.uint8)).resize((960, 192), Image.NEAREST).save(ROOT / "out" / "flair.png")
    print("ok")
