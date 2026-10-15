"""Pixel-perfect type: Not Jam Old Style (CC0), a pixel serif after the old
Garalde faces, set at its own size with no anti-aliasing. Star names lean
as an oblique made by shearing the bitmap a pixel at a time; times carry
tiny raised h and m, as astronomers write them.

    mask = pixel_text("Capella", oblique=True)
    stamp(img, mask, x, y, colour, halo=ground)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONT11 = ImageFont.truetype(str(ROOT / "fonts" / "pixel" / "NotJamOldStyle11.ttf"), 11)
ASC = 8                                            # rows above the baseline

# raised h and m for times (3 and 4 rows tall)
SUP = {"h": ["#..", "#..", "##.", "#.#", "#.#"], "m": ["##.#.", "#.#.#", "#.#.#"], "deg": [".#.", "#.#", ".#."]}


def _glyph_run(text, track=0):
    """Mask (rows x cols, bool) of `text`, the baseline at row ASC, letters `track` pixels further apart."""
    W = 12 * max(1, len(text)) + 4
    img = Image.new("1", (W, 14), 0)
    d = ImageDraw.Draw(img)
    d.fontmode = "1"
    x = 0
    for ch in text:
        d.text((x, 0), ch, font=FONT11, fill=1)
        x += int(round(d.textlength(ch, font=FONT11))) + track
    m = np.asarray(img, bool)
    cols = np.nonzero(m.any(axis=0))[0]
    if len(cols) == 0:
        return np.zeros((14, 1), bool)
    return m[:, : cols.max() + 1]


def shear(m):
    """An oblique: rows lean right a pixel every three rows above the baseline."""
    h, w = m.shape
    out = np.zeros((h, w + 3), bool)
    for r in range(h):
        s = max(0, (ASC - r) // 3)
        out[r, s: s + w] = m[r]
    return out


def pixel_text(text, oblique=False, track=0):
    m = _glyph_run(text, track)
    return shear(m) if oblique else m


def time_text(h, m_):
    """6ʰ17ᵐ in pixels: the figures, then raised h and m."""
    parts = [_glyph_run(str(h)), None, _glyph_run(f"{m_:02d}"), None]
    sup_h = np.array([[c == "#" for c in row] for row in SUP["h"]])
    sup_m = np.array([[c == "#" for c in row] for row in SUP["m"]])
    W = parts[0].shape[1] + 1 + sup_h.shape[1] + 2 + parts[2].shape[1] + 1 + sup_m.shape[1]
    out = np.zeros((14, W), bool)
    x = 0
    out[:, x: x + parts[0].shape[1]] = parts[0]
    x += parts[0].shape[1] + 1
    out[0: sup_h.shape[0], x: x + sup_h.shape[1]] = sup_h            # raised to the figures' top
    x += sup_h.shape[1] + 2
    out[:, x: x + parts[2].shape[1]] = parts[2]
    x += parts[2].shape[1] + 1
    out[2: 2 + sup_m.shape[0], x: x + sup_m.shape[1]] = sup_m
    return out


def sup(name):
    return np.array([[c == "#" for c in row] for row in SUP[name]])


def degrees_text(d, hemi):
    """40°N in pixels."""
    a, b = _glyph_run(str(d)), _glyph_run(hemi)
    dg = sup("deg")
    W = a.shape[1] + 1 + dg.shape[1] + 2 + b.shape[1]
    out = np.zeros((14, W), bool)
    out[:, : a.shape[1]] = a
    x = a.shape[1] + 1
    out[1: 1 + dg.shape[0], x: x + dg.shape[1]] = dg
    x += dg.shape[1] + 2
    out[:, x: x + b.shape[1]] = b
    return out


def temp_text(n):
    """61° in pixels: the figures (a minus before frost on the Celsius scale), then a raised degree ring."""
    a = _glyph_run(str(abs(n)))
    dg = sup("deg")
    minus = n < 0
    W = (4 if minus else 0) + a.shape[1] + 1 + dg.shape[1]
    out = np.zeros((14, W), bool)
    x = 0
    if minus:
        out[ASC - 4, 0:3] = True                      # a minus at the middle of the old-style figures
        x = 4
    out[:, x: x + a.shape[1]] = a
    x += a.shape[1] + 1
    out[1: 1 + dg.shape[0], x: x + dg.shape[1]] = dg
    return out


def ornament(m, top=2):
    """A small drawing set among the letters (a lozenge between two facts), `top` rows down from the caps' top."""
    out = np.zeros((14, m.shape[1]), bool)
    out[top: top + m.shape[0]] = m
    return out


def concat(*masks, gap=4):
    h = max(m.shape[0] for m in masks)
    W = sum(m.shape[1] for m in masks) + gap * (len(masks) - 1)
    out = np.zeros((h, W), bool)
    x = 0
    for m in masks:
        out[: m.shape[0], x: x + m.shape[1]] = m
        x += m.shape[1] + gap
    return out


def bounds(m):
    rows = np.nonzero(m.any(axis=1))[0]
    return (rows.min(), rows.max()) if len(rows) else (0, 0)


def stamp(img, m, x, y, colour, halo=None, where=None, anchor="centre"):
    """Lay mask `m` onto `img` in exact pixels. (x, y) is the text's centre (anchor "centre"), its left end
    ("left") or right end ("right"), y on the middle of the inked rows. A halo (a pixel round each
    letter in `halo`) keeps it clear of what lies beneath; `where` limits it to a region."""
    r0, r1 = bounds(m)
    h, w = m.shape
    x0 = int(round(x - w / 2)) if anchor == "centre" else int(round(x)) if anchor == "left" else int(round(x - w))
    y0 = int(round(y - (r0 + r1) / 2))
    H, W = img.shape[:2]
    if halo is not None:
        grow = m.copy()
        grow[1:] |= m[:-1]; grow[:-1] |= m[1:]
        g2 = grow.copy()
        g2[:, 1:] |= grow[:, :-1]; g2[:, :-1] |= grow[:, 1:]
        ys, xs = np.nonzero(g2 & ~m)
        per_pixel = isinstance(halo, np.ndarray) and halo.ndim == 3
        for yy, xx in zip(ys + y0, xs + x0):
            if 0 <= yy < H and 0 <= xx < W and (where is None or where[yy, xx]):
                img[yy, xx] = halo[yy, xx] if per_pixel else halo
    ys, xs = np.nonzero(m)
    for yy, xx in zip(ys + y0, xs + x0):
        if 0 <= yy < H and 0 <= xx < W and (where is None or where[yy, xx]):
            img[yy, xx] = colour
    return x0, y0 + r0, x0 + w, y0 + r1 + 1


def box_of(m, x, y, anchor="centre"):
    r0, r1 = bounds(m)
    h, w = m.shape
    x0 = int(round(x - w / 2)) if anchor == "centre" else int(round(x)) if anchor == "left" else int(round(x - w))
    y0 = int(round(y - (r0 + r1) / 2))
    return x0 - 1, y0 + r0 - 1, x0 + w + 1, y0 + r1 + 2


if __name__ == "__main__":
    img = np.zeros((60, 200, 3)) + (255, 255, 170)
    stamp(img, pixel_text("Capella", oblique=True), 40, 10, (0, 0, 0))
    stamp(img, pixel_text("CYGNUS", track=1), 120, 10, (170, 0, 0))
    stamp(img, concat(pixel_text("SUNSET"), time_text(6, 17)), 70, 30, (170, 0, 0))
    stamp(img, pixel_text("Wednesday 14 October", oblique=True), 100, 48, (0, 0, 0))
    Image.fromarray(img.astype(np.uint8)).resize((600, 180), Image.NEAREST).save(ROOT / "out" / "pixeltext-test.png")
    print("ok")
