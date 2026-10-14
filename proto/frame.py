"""The Time 2's ring outline: a convex shape filling the screen, kept as a closed polyline, with exact
distances to it, so the ring's rules, ticks and lettering run along true parallels of its edge.

  squircle(w, h, n)          a superellipse (n 2 an ellipse, larger n squarer)
  cushion(w, h, rt, rs, rc)  a cushion: top and bottom edges arcs of radius rt, the sides arcs of radius
                             rs (None straight), the corners rounded with radius rc
"""
import math

import numpy as np

MARGIN = 1.5            # the outline's distance in from the screen's edges


class Outline:
    def __init__(self, pts):
        p = np.asarray(pts, float)
        if np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]) < 0:
            p = p[::-1]                                  # anticlockwise in (x right, y down) maths terms
        self.p = p
        self.a, self.b = p, np.roll(p, -1, axis=0)
        self._grid = {}

    def dist(self, x, y):
        """Signed distance from points to the outline: positive inside."""
        x = np.atleast_1d(np.asarray(x, float)).ravel()
        y = np.atleast_1d(np.asarray(y, float)).ravel()
        out = np.empty(len(x))
        ax, ay = self.a[:, 0][None], self.a[:, 1][None]
        dx, dy = (self.b[:, 0] - self.a[:, 0])[None], (self.b[:, 1] - self.a[:, 1])[None]
        L2 = dx * dx + dy * dy
        for i in range(0, len(x), 2048):
            px, py = x[i:i + 2048, None], y[i:i + 2048, None]
            t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
            d = np.hypot(px - ax - t * dx, py - ay - t * dy).min(axis=1)
            cross = dx * (py - ay) - dy * (px - ax)
            inside = (cross >= 0).all(axis=1) | (cross <= 0).all(axis=1)
            out[i:i + 2048] = np.where(inside, d, -d)
        return out

    def grid(self, w, h):
        """The signed distance at every pixel's centre (cached)."""
        if (w, h) not in self._grid:
            yy, xx = np.mgrid[0:h, 0:w]
            self._grid[(w, h)] = self.dist(xx.ravel() + 0.5, yy.ravel() + 0.5).reshape(h, w)
        return self._grid[(w, h)]


def squircle(w, h, n, k=2400):
    a, b = w / 2 - MARGIN, h / 2 - MARGIN
    t = np.linspace(0, 2 * math.pi, k, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return Outline(np.stack([w / 2 + a * np.sign(c) * np.abs(c) ** (2 / n),
                             h / 2 + b * np.sign(s) * np.abs(s) ** (2 / n)], 1))


def cushion(w, h, rt, rs=None, rc=16.0, d=0.0, rho=None, k=1440):
    """The outline moved in by `d` (a true parallel of it), its corners rounded with radius `rho` (by default
    the parallel's own, rc - d; larger rounds the corners more, widening a band between the two there).

    The core (the outline shrunk by rc) is where four discs overlap (or two discs and two half-planes); a
    parallel is the core shrunk by e = rho + d - rc and grown again by rho."""
    rho = rc - d if rho is None else rho
    e = rho + d - rc
    cx, cy = w / 2, h / 2
    top, bot = MARGIN + rc, h - MARGIN - rc
    left, right = MARGIN + rc + e, w - MARGIN - rc - e
    R = rt - rc
    discs = [(cx, top + R, R - e), (cx, bot - R, R - e)]
    if rs:
        S = rs - rc
        discs += [(MARGIN + rc + S, cy, S - e), (w - MARGIN - rc - S, cy, S - e)]
    # the core's boundary, sampled: each disc's arc where it lies inside the others (and the side lines)
    pts = []
    for (ox, oy, r) in discs:
        t = np.linspace(0, 2 * math.pi, 8000, endpoint=False)
        pts.append(np.stack([ox + r * np.cos(t), oy + r * np.sin(t)], 1))
    if not rs:
        yv = np.linspace(0, h, 1500)
        pts += [np.stack([np.full_like(yv, left), yv], 1), np.stack([np.full_like(yv, right), yv], 1)]
    P = np.concatenate(pts)
    ok = (P[:, 0] >= left - 1e-6) & (P[:, 0] <= right + 1e-6)
    for (ox, oy, r) in discs:
        ok &= np.hypot(P[:, 0] - ox, P[:, 1] - oy) <= r + 1e-6
    C = P[ok]
    # grown by rho: for each outward direction, the core's farthest point that way, moved rho along it
    th = np.linspace(0, 2 * math.pi, k, endpoint=False)
    u = np.stack([np.cos(th), np.sin(th)], 1)
    best = np.argmax(C @ u.T, axis=0)
    return Outline(C[best] + rho * u)
