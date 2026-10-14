"""The drafting table for the large time's figures: each plate's typeface rendered at each watch's size (lining
and old-style figures, and the small raised h and m), thresholded into pixels, written out as text art with a
zoomed preview. The drafts are a guide: the figures are then drawn by hand, pixel by pixel, and kept in
figures.py, which is what the faces draw.

    uv run python proto/foundry.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FACES = {                                   # style: (font file, weight)
    "modern": ("OldStandard-Regular.ttf", None),         # the planisphere, observatory and night plates
    "copperplate": ("PlayfairDisplay[wght].ttf", 450),   # Burritt
    "caslon": ("LibreCaslonText[wght].ttf", 450),        # Flamsteed
}
SIZES = {"time2": 26, "round2": 30}


def font(name, px, weight=None, ss=8):
    f = ImageFont.truetype(str(ROOT / "fonts" / name), px * ss)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except Exception:
            pass
    return f


def draft(ch, name, px, weight=None, feats=None, ss=8):
    """The glyph's pixels at `px`, by area (8x8 samples a pixel, kept if half covered), and where its baseline
    falls (rows from the top of a box px tall above and a third below)."""
    f = font(name, px, weight, ss)
    H, W = int(px * 1.5) * ss, int(px * 1.2) * ss
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    base = int(px * 1.05) * ss
    d.text((ss * 2, base), ch, font=f, fill=255, anchor="ls", features=feats)
    a = np.asarray(im, np.float64) / 255
    cov = a.reshape(H // ss, ss, W // ss, ss).mean(axis=(1, 3))
    m = cov >= 0.5
    rows, cols = np.nonzero(m)
    return m[rows.min(): rows.max() + 1, cols.min(): cols.max() + 1], base // ss - rows.min(), cov


def text_art(m):
    return ["".join("#" if v else "." for v in r) for r in m]


if __name__ == "__main__":
    out_txt = []
    previews = []
    for style, (name, weight) in FACES.items():
        for screen, px in SIZES.items():
            for kind, feats in (("lining", ["lnum"]), ("oldstyle", ["onum"])):
                row = []
                for ch in "0123456789":
                    m, base, _ = draft(ch, name, px, weight, feats)
                    out_txt.append(f"# {style} {screen} {kind} {ch} baseline {base}")
                    out_txt += text_art(m)
                    row.append((m, base))
                for ch in "hm":
                    m, base, _ = draft(ch, name, max(6, round(px * 0.46)), weight)
                    out_txt.append(f"# {style} {screen} small {ch} baseline {base}")
                    out_txt += text_art(m)
                    row.append((m, base))
                # a preview strip, all on one baseline
                top = max(b for _, b in row); bottom = max(m.shape[0] - b for m, b in row)
                strip = np.zeros((top + bottom + 4, sum(m.shape[1] + 2 for m, _ in row) + 4), bool)
                x = 2
                for m, b in row:
                    strip[2 + top - b: 2 + top - b + m.shape[0], x: x + m.shape[1]] = m
                    x += m.shape[1] + 2
                previews.append((f"{style} {screen} {kind}", strip))
    (ROOT / "out" / "foundry-drafts.txt").write_text("\n".join(out_txt) + "\n")
    S = 5
    W = max(p.shape[1] for _, p in previews) * S
    H = sum(p.shape[0] * S + 14 for _, p in previews)
    sheet = Image.new("RGB", (W, H), (40, 40, 44))
    d = ImageDraw.Draw(sheet)
    y = 0
    for label, p in previews:
        a = (np.zeros(p.shape + (3,)) + (255, 255, 170)).astype(np.uint8)
        a[p] = (0, 0, 0)
        big = np.repeat(np.repeat(a, S, 0), S, 1)
        big[::S] = (big[::S] * 0.85).astype(np.uint8); big[:, ::S] = (big[:, ::S] * 0.85).astype(np.uint8)
        d.text((2, y), label, fill=(220, 220, 220))
        sheet.paste(Image.fromarray(big), (0, y + 12))
        y += p.shape[0] * S + 14
    sheet.save(ROOT / "out" / "foundry-drafts.png")
    print("ok", sheet.size)
