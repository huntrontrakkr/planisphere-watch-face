"""Build the settings page: tools/page/ (HTML, CSS, JS, the type), the live preview (preview/plan-preview.js, built by
preview/build.sh), the plates' names and colours and the face's own ornaments into one HTML string,
watchface/src/pkjs/page.js, which the phone opens as a data: URL with its state filled in.

    preview/build.sh && (cd proto && uv run python ../tools/build_page.py)
"""
import base64
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "tools" / "page"
sys.path.insert(0, str(ROOT / "proto"))

# each plate's name, a line on where it comes from, and the page's colours when it is chosen (the paper, the ink, the
# red ink, the deep colour, the rules: as each original was printed, softer than the watch's 64 colours), in the order
# of proto/plates.py PLATES (the watch's numbers)
PLATES = {
    "planisphere": ("Planisphere", "The paper planispheres of the early 1900s: a cream card in black and red over a deep "
                                   "blue sky",
                    dict(paper="#f2e8cc", ink="#1f1b14", accent="#a8291f", deep="#1d2b5e", rule="#8a7a5a")),
    "burritt": ("Burritt", "Burritt’s Geography of the Heavens (1835): white stars and figures on blue",
                dict(paper="#18284f", ink="#eef0f4", accent="#f0d27a", deep="#0c1633", rule="#7e8db5", dark=True)),
    "flamsteed": ("Flamsteed", "Flamsteed’s Atlas Coelestis (London, 1729): copper engraving, black on white",
                  dict(paper="#f7f5ef", ink="#161616", accent="#161616", deep="#3a3a3a", rule="#8c8c8c")),
    "observatory": ("Observatory", "Red light, for eyes kept dark",
                    dict(paper="#140707", ink="#e0533f", accent="#ff6a52", deep="#3a0d08", rule="#7a2a20", dark=True)),
    "astrolabe": ("Astrolabe", "A brass astrolabe after the Sloane astrolabe (c. 1300): the rete’s flames over "
                               "engraved circles",
                  dict(paper="#dcc283", ink="#2a1c06", accent="#7a2412", deep="#3b2a0e", rule="#8c6a2a")),
    "hours": ("Book of Hours", "After the Très Riches Heures (c. 1412–16): gold stars on ultramarine, "
                               "vellum, vermilion",
              dict(paper="#f1e5c6", ink="#2b1f14", accent="#b23a24", deep="#1f3d8f", rule="#b8962e")),
    "orloj": ("Orloj", "Prague’s astronomical clock (1410): gold on black, the sky in its three zones",
              dict(paper="#0f0d0a", ink="#e2c46f", accent="#e2c46f", deep="#22396b", rule="#8a6f30", dark=True)),
    "cyanotype": ("Cyanotype", "Herschel’s blueprint, as Anna Atkins printed her algae (1843): white on cobalt",
                  dict(paper="#1d4f8f", ink="#f3f6fa", accent="#ffffff", deep="#123566", rule="#9cb5d6", dark=True)),
    "apian": ("Apian", "Apian’s Astronomicum Caesareum (1540): a woodcut coloured by hand, the dragon at the "
                       "nodes",
              dict(paper="#ead9ae", ink="#1b140d", accent="#b02c1c", deep="#3f7fb8", rule="#1b140d")),
    "night": ("Night", "The first take: white type on a black card",
              dict(paper="#0d0d0f", ink="#ecebe6", accent="#ecebe6", deep="#1e2330", rule="#5a5a62", dark=True)),
}

# the face's pieces' roles (proto/sprites.py ROLE) as the page draws them: in its own inks, or the Sun's gilding
INKS = {1: "var(--ink)", 2: "var(--accent)", 3: "var(--accent)", 4: "var(--accent)", 5: "var(--paper)",
        6: "var(--accent)", 7: "var(--ink)"}
GILT = {1: "#3a2a10", 3: "#e3b341", 4: "#b0681a", 5: "#fff6d8"}


def svg(sprite, scale, fills):
    """A piece of the face, its pixels as squares (crisp at any size), each role in its fill."""
    h, w = sprite.shape
    paths = []
    for role, fill in fills.items():
        d = "".join(f"M{x} {y}h1v1h-1z" for y, x in zip(*np.nonzero(sprite == role)))
        if d:
            paths.append(f'<path style="fill:{fill}" d="{d}"/>' if fill.startswith("var") else
                         f'<path fill="{fill}" d="{d}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w * scale:g}" '
            f'height="{h * scale:g}" shape-rendering="crispEdges" aria-hidden="true">{"".join(paths)}</svg>')


def data_uri(mime, data):
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def art():
    """The face's own pieces for the page: the north's fleur-de-lis over each heading, the south's star and the ring's
    stud beside them, the gilded Sun's hand as the clock's slider, and the face's blue noise as the paper's grain."""
    import sprites
    grain = np.load(ROOT / "data" / "bluenoise64.npy")
    grain = (255 - (grain.astype(np.float64) / max(1, grain.max()) * 255)).astype(np.uint8)
    png = io.BytesIO()
    Image.fromarray(grain, "L").save(png, "PNG", optimize=True)
    return {
        "fleur": svg(sprites.FLEUR, 1.5, INKS),
        "star": svg(sprites.SOUTH_STAR, 1.6, INKS),
        "stud": svg(sprites.STUD, 1.6, INKS),
        "sun": data_uri("image/svg+xml", svg(sprites.SUN_HAND, 2, GILT).encode()),
        "grain": data_uri("image/png", png.getvalue()),
    }


def fonts():
    """Old Standard, as the face's large time follows it: the page's type, embedded (tools/page/fonts/README.md)."""
    rules = []
    for style, file in (("normal", "OldStandard-Regular.woff2"), ("italic", "OldStandard-Italic.woff2")):
        uri = data_uri("font/woff2", (PAGE / "fonts" / file).read_bytes())
        rules.append(f"@font-face {{ font-family: 'Old Standard'; font-style: {style}; font-weight: 400; "
                     f"src: url({uri}) format('woff2'); }}")
    return "/* Old Standard TT, (c) 2011 The Old Standard Project Authors, SIL Open Font License 1.1 */\n" + "\n".join(rules)


def main():
    import plates
    order = list(plates.PLATES)
    assert set(order) == set(PLATES), "a plate without its name here"
    plate_list = [{"name": PLATES[k][0], "words": PLATES[k][1], "theme": PLATES[k][2]} for k in order]
    import feasts
    calendar_list = [{"key": k, "name": n, "desc": d} for k, n, d in feasts.CALENDARS]
    pieces = art()
    html = (PAGE / "page.html").read_text()
    preview = (ROOT / "preview" / "plan-preview.js").read_text()
    script = (PAGE / "page.js").read_text()
    for name, text in (("preview", preview), ("page", script)):
        assert "</script" not in text.lower(), f"{name} would end its script tag"
    css = (PAGE / "page.css").read_text().replace("/*FONTS*/", fonts())
    css = css.replace("/*SUN*/", pieces["sun"]).replace("/*GRAIN*/", pieces["grain"])
    html = (html.replace("/*CSS*/", css)
                .replace("/*PREVIEW*/", preview)
                .replace("/*PLATES*/[]", json.dumps(plate_list, separators=(",", ":"), ensure_ascii=False))
                .replace("/*ART*/{}", json.dumps({k: v for k, v in pieces.items() if k in ("fleur", "star", "stud")}))
                .replace("/*CALENDARS*/[]", json.dumps(calendar_list, ensure_ascii=False))
                .replace("/*PAGE*/", script))
    assert html.count("/*STATE*/null") == 1
    licence = (PAGE / "fonts" / "OFL-oldstandardtt.txt").read_text().replace("*/", "* /")
    out = ROOT / "watchface" / "src" / "pkjs" / "page.js"
    out.write_text("// Generated by tools/build_page.py from tools/page/ and preview/; do not edit.\n"
                   "var HTML = " + json.dumps(html) + ";\n"
                   "// The page with the phone's state filled in: {settings, platform, place, weather, returnTo}.\n"
                   "module.exports = function (state) {\n"
                   "  var json = JSON.stringify(state).replace(/</g, '\\\\u003c');\n"
                   "  return HTML.replace('/*STATE*/null', function () { return json; });\n"
                   "};\n"
                   "/* The page's type, Old Standard TT, is embedded in it under this licence:\n\n" + licence + "\n*/\n")
    # the page alone, to open in a browser with a sample state
    sample = {"settings": {}, "platform": "emery", "returnTo": "#",
              "place": {"lat": 40.71, "lon": -74.01, "city": "New York", "country": "U.S.A."},
              "weather": {"code": 2, "temp10": 140, "low": 40, "mid": 20, "high": 10, "wind": 12, "from": 240,
                          "pressure": 1016, "snow_mm": 0, "vis_dam": 3000}}
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "page.html").write_text(html.replace("/*STATE*/null", json.dumps(sample)))
    print(f"{out.relative_to(ROOT)}: {out.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
