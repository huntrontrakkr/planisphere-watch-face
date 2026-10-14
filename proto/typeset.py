"""Type at the watch's size: text set at four times the size and brought down
to whole pixels, inked in the watch's 64 colours.

astro_time("21", "30") sets a time as astronomers write it: 21ʰ 30ᵐ, the
h and m small and raised."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
FONTS = ROOT / "fonts"
SS = 4
_cache = {}


def font(name, px, weight=None):
    key = (name, px, weight)
    if key not in _cache:
        f = ImageFont.truetype(str(FONTS / name), px * SS)
        if weight is not None:
            try:
                f.set_variation_by_axes([weight])
            except Exception:
                pass
        _cache[key] = f
    return _cache[key]


def run_alpha(parts, track=0.0):
    """Alpha (h x w, 0..1) of a run of (text, font name, px, weight, raise_px, features) parts, set together."""
    canvas = Image.new("L", (2000, 400), 0)
    d = ImageDraw.Draw(canvas)
    x = 20 * SS
    base = 300
    for text, name, px, weight, rise, feats in parts:
        f = font(name, px, weight)
        for ch in (text if track else [text]):
            d.text((x, base - rise * SS), ch, font=f, fill=255, anchor="ls", features=feats or None)
            x += d.textlength(ch, font=f, features=feats or None) + track * SS * px
    a = np.asarray(canvas, np.float64) / 255
    ys, xs = np.nonzero(a > 0.02)
    if len(xs) == 0:
        return np.zeros((1, 1))
    y0, y1 = (ys.min() // SS) * SS, ((ys.max() // SS) + 1) * SS
    x0, x1 = (xs.min() // SS) * SS, ((xs.max() // SS) + 1) * SS
    a = a[y0:y1, x0:x1]
    h, w = a.shape[0] // SS, a.shape[1] // SS
    return a[: h * SS, : w * SS].reshape(h, SS, w, SS).mean(axis=(1, 3))


def ink(img, alpha, cx, cy, colour, align="centre", gamma=0.85):
    """Lay `colour` through `alpha` onto float image `img` (0..255) at (cx, cy); returns the box."""
    h, w = alpha.shape
    x0 = int(round(cx - w / 2)) if align == "centre" else int(round(cx)) if align == "left" else int(round(cx - w))
    y0 = int(round(cy - h / 2))
    H, W = img.shape[:2]
    a = np.clip(alpha, 0, 1) ** gamma
    ys, xs = slice(max(0, y0), min(H, y0 + h)), slice(max(0, x0), min(W, x0 + w))
    sub = a[ys.start - y0: ys.stop - y0, xs.start - x0: xs.stop - x0][..., None]
    img[ys, xs] = img[ys, xs] * (1 - sub) + np.array(colour, np.float64) * sub
    return x0, y0, x0 + w, y0 + h


def astro_time(hh, mm, name, px, weight=None, feats=("onum",)):
    """21ʰ 30ᵐ: the figures, then small raised h and m."""
    small = max(6, round(px * 0.46))
    rise = px * 0.38
    return run_alpha([(hh, name, px, weight, 0, list(feats)), ("h", name, small, weight, rise, None),
                      (" ", name, px, weight, 0, None),
                      (mm, name, px, weight, 0, list(feats)), ("m", name, small, weight, rise, None)])


def quant(img):
    return (np.clip(np.floor(np.clip(img, 0, 255) / 85 + 0.5), 0, 3) * 85).astype(np.uint8)


if __name__ == "__main__":
    cream, ink_c, navy, gold = (255, 255, 170), (0, 0, 0), (0, 0, 85), (255, 255, 170)
    faces = [("OldStandard-Regular.ttf", None, "OldStandard-Italic.ttf", "Old Standard (1890s scientific type)"),
             ("IMFeENrm28P.ttf", None, "IMFeENit28P.ttf", "IM Fell (1670s Oxford type)"),
             ("EBGaramond[wght].ttf", 500, "EBGaramond-Italic[wght].ttf", "EB Garamond"),
             ("LibreCaslonText[wght].ttf", 500, "LibreCaslonText-Italic[wght].ttf", "Libre Caslon (1730s)"),
             ("PlayfairDisplay[wght].ttf", 500, "PlayfairDisplay-Italic[wght].ttf", "Playfair (copperplate 1800s)")]
    rows = []
    for regular, wt, italic, label in faces:
        for bg, fg, accent in ((cream, ink_c, (170, 0, 0)), (navy, gold, (255, 170, 85))):
            img = np.zeros((70, 260, 3)) + np.array(bg, np.float64)
            ink(img, astro_time("21", "30", regular, 26, wt), 70, 26, fg)
            ink(img, run_alpha([("Wednesday 14 October", italic, 10, wt, 0, None)]), 70, 52, fg)
            ink(img, run_alpha([("SUNSET 6", regular, 8, wt, 0, ["smcp"]), ("h", regular, 5, wt, 3, None), ("17", regular, 8, wt, 0, ["onum"]), ("m", regular, 5, wt, 3, None)]), 70, 63, accent)
            ink(img, run_alpha([("CYGNUS", regular, 8, wt, 0, None)], track=0.35), 195, 16, fg)
            ink(img, run_alpha([("Vega", italic, 10, wt, 0, None)]), 195, 32, fg)
            ink(img, run_alpha([("XII  III  VI  IX", regular, 9, wt, 0, None)]), 195, 48, fg)
            ink(img, run_alpha([("NOON", regular, 7, wt, 0, None)], track=0.3), 195, 62, accent)
            rows.append(quant(img))
    S = np.concatenate(rows, axis=0)
    Image.fromarray(S).resize((S.shape[1] * 3, S.shape[0] * 3), Image.NEAREST).save(ROOT / "out" / "type-specimen.png")
    print([f[3] for f in faces])


def arc_text(shape, text, name, px, weight, cx, cy, r, centre_deg, outside_up=True, track=0.25):
    """Alpha (shape h x w) of `text` set along a circle of radius `r` round (cx, cy), centred at
    `centre_deg` (the dial's angle: from the bottom, anticlockwise), upright: tops outward on the
    upper half of the ring, inward on the lower half."""
    import math
    H, W = shape
    f = font(name, px, weight)
    layer = Image.new("L", (W * SS, H * SS), 0)
    adv = [f.getlength(ch) / SS + track * px for ch in text]
    total = sum(adv) - track * px
    s = -total / 2
    for ch, a_px in zip(text, adv):
        mid = s + (a_px - track * px) / 2
        a = centre_deg + (-1 if outside_up else 1) * math.degrees(mid / r)
        theta = a + 180 if outside_up else a
        g = Image.new("L", (int(px * SS * 2), int(px * SS * 2)), 0)
        ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=255, anchor="mm")
        g = g.rotate(theta, resample=Image.BICUBIC, expand=False)
        x = (cx + r * math.sin(math.radians(a))) * SS
        y = (cy + r * math.cos(math.radians(a))) * SS
        box = (int(x - g.width / 2), int(y - g.height / 2))
        layer.paste(Image.fromarray(np.maximum(np.asarray(layer.crop((box[0], box[1], box[0] + g.width, box[1] + g.height))),
                                               np.asarray(g))), box)
        s += a_px
    a = np.asarray(layer, np.float64) / 255
    return a.reshape(H, SS, W, SS).mean(axis=(1, 3))
