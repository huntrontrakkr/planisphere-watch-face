"""The Labours of the Months' tools, for the Time 2's corners (an option): each month a tool hanging in the top
corners (its head up, as on a peg) and one propped in the bottom corners (its head on the floor), after the woodcuts of
the Shepherds' Calendar and the Paris Books of Hours (research/labours/README.md). Drawn by hand on a 24 x 22 grid per
corner, in the top-left corner's frame (x in from the side, y down; the bottom grid's last row the screen's bottom
edge); the right corners mirror the left. Hafts are a one-pixel core outlined on both sides; iron has a dark back and a
bright edge; everything is lit from the top left.

tools/gen_tables.py packs them into tools.bin (blob()); plan_render.c draws them (corner_tools).
"""
import math
import struct

def C(r, g, b): return (r * 85, g * 85, b * 85)
PAL = {'o': C(1, 0, 0), 'w': C(3, 2, 1), 'W': C(2, 1, 0),                 # wood: outline, light, shade
       'd': C(1, 1, 1), 'i': C(2, 2, 2), 'h': C(3, 3, 3),                 # iron: back, body, edge
       'y': C(3, 2, 0), 'Y': C(2, 1, 0), 'z': C(3, 3, 1),                 # straw: body, shade, light
       'G': C(0, 1, 0), 'l': C(1, 2, 0), 'L': C(2, 3, 1),                 # leaves: outline, body, light
       'r': C(3, 0, 0), 'R': C(2, 0, 0), 'p': C(3, 1, 1),                 # red: flower, shade, light
       'k': C(1, 1, 0), 'c': C(2, 2, 1), 'C': C(3, 3, 2), 'K': C(1, 1, 0),  # linen: outline, body, light
       'f': C(3, 2, 0), 'F': C(3, 0, 0), 'P': C(1, 0, 1), 'q': C(2, 1, 2), 'Q': C(3, 2, 3),   # fire; grapes
       'n': C(0, 0, 0), 'N': C(1, 1, 1), 'b': C(2, 1, 1), 'B': C(1, 0, 0), 'e': C(3, 3, 2)}   # iron pot; feathers
# the outlines: on a printed plate these alone are drawn, in its ink (an engraving of the tools)
LINE = set("odkKGBnP")
W_, H_ = 24, 22
class Grid:
    def __init__(self): self.g = [['.'] * W_ for _ in range(H_)]
    def put(self, x, y, c, over=True):
        if 0 <= y < H_ and 0 <= x < W_ and (over or self.g[y][x] == '.'): self.g[y][x] = c
    def pts(self, pts, c, over=True):
        for x, y in pts: self.put(x, y, c, over)
    def rows(self, x0, y0, art):                 # hand-drawn art pasted (its '.' leaves what is there)
        for j, r in enumerate(art):
            for i, ch in enumerate(r):
                if ch != '.': self.put(x0 + i, y0 + j, ch)
    def haft(self, a, b, core='w', side='o'):     # a straight haft of singles from a to b, outlined either side
        (xa, ya), (xb, yb) = a, b
        n = max(abs(xb - xa), abs(yb - ya))
        line = [(round(xa + (xb - xa) * k / n), round(ya + (yb - ya) * k / n)) for k in range(n + 1)]
        steep = abs(yb - ya) > abs(xb - xa)
        for x, y in line:
            for dx, dy in (((1, 0), (-1, 0)) if steep or abs(yb - ya) == abs(xb - xa) else ((0, 1), (0, -1))):
                self.put(x + dx, y + dy, side, False)
        for x, y in line: self.put(x, y, core)
    def show(self): return '\n'.join(''.join(r) for r in self.g)

# ---- the tools: (top, bottom) for each month -------------------------------------------------------------------
def scythe():                                     # June, hanging: the snath, its side grip, the crescent blade
    g = Grid(); g.haft((2, 19), (15, 6)); g.pts([(1, 20), (2, 20)], 'o')
    g.pts([(12, 11), (13, 12)], 'W'); g.pts([(13, 11), (14, 12), (14, 13), (13, 13), (12, 12)], 'o', False)
    g.pts([(17, 5), (17, 4), (16, 3), (15, 2), (14, 1), (13, 1), (12, 0), (11, 0), (10, 0), (9, 0), (8, 0), (7, 1),
           (6, 1), (5, 2), (4, 3), (3, 4)], 'd')
    g.pts([(16, 5), (16, 4), (15, 3), (14, 2), (13, 2), (12, 1), (11, 1), (10, 1), (9, 1), (8, 1), (7, 2), (6, 2),
           (5, 3), (4, 4)], 'i')
    g.pts([(15, 4), (14, 3), (12, 2), (11, 2), (10, 2), (9, 2), (8, 2), (7, 3), (6, 3)], 'h')
    g.put(15, 5, 'd'); g.put(16, 6, 'o')
    return g
def hayrake():                                    # June, propped: head down, teeth on the floor
    g = Grid(); g.haft((11, 18), (2, 9)); g.put(1, 9, 'o'); g.put(2, 8, 'o')
    for x in range(5, 18): g.put(x, 19, 'o'); g.put(x, 20, 'W')
    g.put(4, 20, 'o'); g.put(18, 20, 'o'); g.put(11, 19, 'w')
    for x in range(5, 18, 2): g.put(x, 21, 'o')
    return g
import math
def ring(g, cx, cy, r, a0, a1, cols, taper=False):
    """An arc of a crescent: pixels whose centre lies between radii, between angles a0..a1 (degrees, 0 = right,
    counter-clockwise, y up): `cols` the colours from the outside in, a pixel ring each."""
    for y in range(H_):
        for x in range(W_):
            dx, dy = x + 0.5 - cx, cy - (y + 0.5)
            d = math.hypot(dx, dy)
            a = math.degrees(math.atan2(dy, dx)) % 360
            if not (a0 <= a <= a1 or (a0 > a1 and (a >= a0 or a <= a1))): continue
            k = int(r - d)
            span = (a1 - a) % 360 / ((a1 - a0) % 360)          # 0 at the tip (a1), 1 at the root (a0)
            n = len(cols) if not taper else 1 + round((len(cols) - 1 + 0.4) * min(1, (1 - span) * 1.6))
            if 0 <= k < n and d <= r: g.put(x, y, cols[k] if k < n - 1 or n == len(cols) else cols[-1])
def _sickle_old():                                     # July, hanging by its handle's ring: a toothed crescent
    g = Grid(); g.haft((4, 18), (7, 15)); g.pts([(3, 19)], 'o')
    arc_back = [(8, 13), (9, 11), (9, 9), (10, 7), (11, 5), (12, 4), (14, 3), (16, 3), (18, 4), (19, 5), (20, 7)]
    arc_body = [(8, 14), (9, 13), (9, 12), (10, 10), (10, 9), (11, 7), (12, 6), (13, 5), (14, 4), (16, 4), (17, 4),
                (18, 5), (19, 6), (19, 7)]
    g.pts(arc_back, 'd'); g.pts(arc_body, 'i')
    g.pts([(10, 11), (11, 9), (12, 8), (13, 7), (14, 6), (15, 5), (17, 5)], 'h')          # the toothed edge
    g.pts([(10, 12), (11, 10), (12, 9), (14, 7), (16, 6)], 'd', False)                      # its teeth, dark
    g.put(20, 8, 'd')
    return g
def sickle():                                     # July, hanging by its handle: a smooth crescent, a toothed edge
    g = Grid()
    ring(g, 12.5, 10.5, 8.6, 345, 215, ['d', 'i', 'i', 'h'], taper=True)   # back, body, the bright toothed edge
    for y in range(H_):                                                  # its teeth: every other edge pixel dark
        for x in range(W_):
            if g.g[y][x] == 'h' and (x + y) % 2 == 0: g.put(x, y, 'i')
    g.haft((1, 19), (6, 14)); g.put(0, 20, 'o')
    return g
def sheaf():                                      # July, standing: a sheaf tied at the waist, its ears spread
    g = Grid()
    g.rows(3, 7, [
        "....z..z..z.....",
        "..z.y.zy.yz.z...",
        "...yzy.yzy.yz...",
        "..yyzyyyzyyzyy..",
        "...yyzyyzyyzy...",
        "....yyzyyzyy....",
        ".....yzyyzy.....",
        ".....kkkkkk.....",          # the band of twisted straw
        ".....yYyYyY.....",
        "....yYyYyYyY....",
        "...yYyYyYyYyY...",
        "..yYyYyYyYyYyY..",
        "..YYYYYYYYYYYY..",
        "...Y.Y.Y.Y.Y.Y..",
        "................"])
    return g
def flail():                                      # August, hanging: a long handstaff, the swingle dangling from its tip
    g = Grid(); g.haft((2, 18), (14, 6)); g.put(1, 19, 'o')
    g.pts([(15, 5), (16, 5)], 'k'); g.put(17, 6, 'k')                    # the leather thong over the cap
    g.rows(16, 7, [                                                      # the swingle: a short thick club, hanging
        "owwo",
        "owWo",
        "owWo",
        "owWo",
        "owWo",
        "owWo",
        ".oo."])
    return g
def sack():                                       # August, standing: the grain in a tied sack
    g = Grid()
    g.rows(4, 8, [
        ".....k.k.....",
        "......k......",
        ".....kCk.....",
        "....kCcck....",
        "...kCccccK...",
        "..kCcccccck..",
        ".kCcccccccck.",
        ".kCcccccccck.",
        "kCcccccccccck",
        "kCcccccccccck",
        "kccccccccccck",
        "kccccccccccck",
        ".kkkkkkkkkkk.",
        "...y.y..yy...",])
    return g
def stook():                                      # August, standing: threshed straw bound in a stook
    return sheaf()
def spade():                                      # March, propped: blade down on the floor, the T-handle up
    g = Grid(); g.haft((9, 14), (3, 4)); g.pts([(1, 3), (2, 3), (3, 3), (4, 3), (5, 3)], 'o'); g.pts([(2, 2), (3, 2), (4, 2)], 'o')
    g.pts([(2, 3), (3, 3), (4, 3)], 'w')
    g.rows(7, 14, [
        "ddddddd",
        "diiiiid",
        "dihhhid",
        "dihhhid",
        "diiiiid",
        "diiiiid",
        ".diiid.",
        "..ddd.."])
    return g
def pruninghook():                                # March, hanging: a short handle, a broad blade hooked at the end
    g = Grid(); g.haft((4, 19), (8, 15)); g.put(3, 20, 'o')
    g.rows(8, 2, [
        ".....dddd...",
        "....dhiiid..",
        "....dh..did.",
        "........did.",
        ".......dhid.",
        "......dhiid.",
        ".....dhiid..",
        "....dhiid...",
        "...dhiid....",
        "..dhiid.....",
        ".dhiid......",
        "dhiid.......",
        "diid........",
        ".dd.........",])
    return g
def _pruninghook_old():
    g = Grid(); g.haft((5, 18), (9, 14)); g.put(4, 19, 'o')
    g.pts([(10, 12), (11, 11), (12, 10), (13, 9), (14, 8), (15, 7), (16, 6), (16, 5), (16, 4), (15, 3), (14, 3), (13, 4)], 'd')
    g.pts([(10, 13), (11, 12), (12, 11), (13, 10), (14, 9), (15, 8), (16, 7), (17, 6), (17, 5), (17, 4)], 'i')
    g.pts([(11, 13), (12, 12), (13, 11), (14, 10), (15, 9), (16, 8), (17, 7), (18, 6), (18, 5), (18, 4), (17, 3), (16, 2), (15, 2), (14, 2), (13, 3), (12, 4)], 'h')
    g.pts([(18, 3), (17, 2), (16, 1), (15, 1), (14, 1), (13, 2), (12, 3), (11, 4), (12, 5)], 'd', False)
    return g
def flagon():                                     # January: the pewter flagon of the feast, its lid domed
    g = Grid()
    g.rows(4, 3, [
        "....ddd.....",
        "...dhhid.d..",
        "..dddddddd..",
        "...dhiid..d.",
        "...dhiid..d.",
        "..dhiiiid.d.",
        ".dhhiiiiiddd",
        ".dhiiiiiid..",
        ".dhiiiiiid..",
        "..dhiiiid...",
        "...ddddd....",
        "..ddddddd...",])
    return g
def platter():                                    # January: a round loaf, a knife driven into it on the slant
    g = Grid()
    g.rows(3, 12, [
        ".....ooooooo.....",
        "...oowwzwwwwoo...",
        "..owwzwwwwwwwWo..",
        ".owzwwwwwwwwwWWo.",
        ".owwwoowwwwwWWWo.",
        ".oWwwwwooWwWWWWo.",
        ".oWWwwwwwwWWWWWo.",
        "..oWWWWWWWWWWWo..",
        "...ooWWWWWWWoo...",
        ".....ooooooo.....",])
    g.haft((13, 13), (17, 9), core='i', side='d'); g.put(13, 14, 'd', False)            # the blade, in the loaf
    g.haft((18, 8), (21, 5)); g.put(22, 4, 'o'); g.pts([(17, 7), (19, 9)], 'd', False)   # its handle
    return g

def pothook():                                    # February: the cauldron on its pothook over the fire
    g = Grid()
    g.pts([(10, y) for y in range(0, 6)], 'd'); g.pts([(11, 1), (11, 3), (11, 5)], 'd')        # the ratchet bar
    g.rows(5, 6, [
        ".....d.....",
        "..ddddddd..",
        ".dnNNNNNnd.",
        "dnNNNNNNNnd",
        "dnnNNNNNnnd",
        ".dnnnnnnnd.",
        "..ddddddd..",
        "...f.F.f...",
        "..fFfFfFf..",
        "...FfFfF...",])
    return g
def logs():                                       # February: a faggot of firewood, bound in the middle, on the slant
    g = Grid()
    for k in (0, 2, 4):
        g.haft((2 + k, 21), (14 + k, 9), core='W' if k == 2 else 'w')
    g.pts([(7, 13), (8, 14), (9, 15), (10, 16), (11, 17), (12, 18)], 'l')                 # the withy round it
    g.pts([(8, 13), (9, 14), (10, 15), (11, 16), (12, 17), (13, 18)], 'G')
    return g

def garland():                                    # April: a garland of leaves and flowers hung from a peg
    g = Grid()
    g.put(10, 0, 'o'); g.put(10, 1, 'k'); g.put(9, 2, 'k'); g.put(11, 2, 'k')
    g.rows(4, 3, [
        "....GlGlG....",
        "..GlLrGLlG...",
        ".GLpr...GlG..",
        ".lG.......rG.",
        "Gl.........lG",
        "GL.........pr",
        "rp.........lG",
        ".lG.......GL.",
        ".GlG.....Glr.",
        "..GrlGlGlLG..",
        "....GlpGl....",])
    return g
def posy():                                       # April: a posy of flowers laid on the ground
    g = Grid()
    g.rows(3, 10, [
        "........pr.......",
        "......pr.rp.Gl...",
        ".......rpGL.pr...",
        ".....Gl.GlG.rp...",
        "......GlLG.......",
        ".......Gl........",
        "......Gl.........",
        ".....GlG.........",
        "....kkk..........",
        "...Gl............",
        "..Gl.............",
        ".G...............",])
    return g
def falcon():                                     # May: the hooded falcon on its perch, jesses hanging
    g = Grid()
    g.rows(5, 1, [
        "....BB.....",
        "...BrrB....",
        "...BrnbY...",
        "..BbbbbB...",
        "..BbeebbB..",
        ".BbeeebbB..",
        ".BbeeebbbB.",
        ".BbeeebbbB.",
        "..BbeebbbbB",
        "...BbbbbbbB",
        "....YBYBBBB",
        "oooooooooooo",
        "owwwwwwwwwwo",
        "oooooooooooo",
        ".....ow.....",
        ".....ow.....",
        ".....ow.....",])
    g.pts([(9, 13), (10, 14)], 'B')
    return g

def maybough():                                   # May: the May bough, a leafy branch stood in the corner
    g = Grid()
    g.haft((5, 21), (5, 11), core='W')
    g.rows(0, 1, [
        ".....GlG.....",
        "...GlLlLlG...",
        "..GlLGlGLlG..",
        ".GlLlGlGlLlG.",
        ".GLlGlLlGlLG.",
        "..GlLlGlLlG..",
        "...GlGlGlG...",
        ".....GlG.....",
        "......o......",])
    return g
def grapebasket():                                # September: a basket of grapes hung by its arched handle
    g = Grid()
    g.rows(3, 1, [
        "......YYYY......",
        ".....Y....Y.....",
        "....Y......Y....",
        "....Y......Y....",
        "...YPqPqPqPqY...",
        "..YqQqPqQqPqPY..",
        "..YYYYYYYYYYYY..",
        "..YyzyYyzyYyzY..",
        "...YyYyYyYyYY...",
        "...YzyYzyYzyY...",
        "....YYYYYYYY....",])
    return g
def vat():                                        # September: the hooped vat, its grapes heaped
    g = Grid()
    g.rows(2, 9, [
        ".....PqPqP.......",
        "...PqQqPqQqP.....",
        "..PqPqPqPqPqP....",
        ".oooooooooooooo..",
        ".owwWwwWwwWwwWo..",
        "..ddddddddddddd..",
        "..owwWwwWwwWwwo..",
        "..owwWwwWwwWwwo..",
        "...ddddddddddd...",
        "...owwWwwWwwWo...",
        "...owwWwwWwwWo...",
        "....ooooooooo....",])
    return g
def seedbag():                                    # October: the sower's seed bag on its strap, seed spilling
    g = Grid()
    g.pts([(3, 5), (3, 4), (4, 3), (5, 2), (6, 1), (7, 1), (8, 1), (9, 1), (10, 2), (11, 3), (12, 4), (12, 5)], 'B')
    g.rows(1, 5, [
        "..kkkkkkkkkkk...",
        ".kCCCCCCCCCcck..",
        "kCCcccccccccck..",
        "kCcccccccccccck.",
        "kCcccccccccccck.",
        "kCcccccccccccck.",
        ".kccccccccccck..",
        "..kkkkkkkkkkkz..",
        "...........z.z..",
        "............z.z.",
        "...........z..z.",])
    return g

def harrow():                                     # October: the harrow propped on its teeth, a frame of bars
    g = Grid()
    g.rows(2, 9, [
        "ooooooooooooooo.",
        "owwwwwwwwwwwwwo.",
        "oo.o.oo.oo.o.oo.",
        "ow.w.ow.ow.w.wo.",
        "oooooooooooooooo",
        "owwwwwwwwwwwwwo.",
        "oo.o.oo.oo.o.oo.",
        "ow.w.ow.ow.w.wo.",
        "ooooooooooooooo.",
        "owwwwwwwwwwwwwo.",
        "ooooooooooooooo.",
        ".d..d..d..d..d..",
        ".d..d..d..d..d..",])
    return g
def acornpole():                                  # November: the long pole that beats the acorns down, acorns falling
    g = Grid(); g.haft((2, 20), (16, 6)); g.put(1, 21, 'o'); g.put(17, 5, 'o')
    for x, y in ((8, 3), (17, 10), (4, 9)):
        g.rows(x, y, [".ooo.", "oWWWo", "oyyyo", "oyzyo", ".oyo.", "..o.."])
    return g

def axe():                                        # November: the woodman's axe propped head-down, leaning
    g = Grid(); g.haft((11, 14), (2, 5)); g.put(1, 4, 'o')
    g.rows(8, 12, [
        "...ddd.....",
        "..diiidd...",
        ".diiiiiid..",
        "ddiiiiiiid.",
        "dhhiiiiiid.",
        "dhhhiiiid..",
        ".ddhhiid...",
        "...dhid....",
        "....dd.....",])
    return g

def peel():                                       # December: the baker's peel hung by its long haft, the blade a flat square
    g = Grid(); g.haft((2, 20), (10, 12)); g.put(1, 21, 'o')
    g.rows(10, 2, [
        ".....o.....",
        "....owo....",
        "...owwwo...",
        "..owwwwwo..",
        ".owwwwwwWo.",
        "owwwwwwwWWo",
        ".owwwwwWWo.",
        "..owwwWWo..",
        "...owWWo...",
        "...oWWo....",
        "..oWo......",])
    return g

def block():                                      # December: the cleaver struck into the chopping block
    g = Grid()
    g.rows(3, 7, [
        "......ddddddd..",
        ".....dhiiiiid..",
        ".....dhiiiiid..",
        ".....dhiiiiid..",
        "...oooddddddo..",
        "..owwo.........",
        "oowwo..........",])
    g.rows(2, 13, [
        "..oooooooooo....",
        ".owwzwwwwzwwo...",
        ".oWwwwzwwwwWo...",
        ".oWWWWWWWWWWo...",
        ".oWwWWWwWWWWo...",
        ".oWWWWWWWwWWo...",
        ".oWWwWWWWWWWo...",
        ".oWWWWWWWWWWo...",
        "..oooooooooo....",])
    return g
SETS = {1: (flagon, platter), 2: (pothook, logs), 4: (garland, posy), 5: (falcon, maybough), 9: (grapebasket, vat),
        10: (seedbag, harrow), 11: (acornpole, axe), 12: (peel, block), 3: (pruninghook, spade), 6: (scythe, hayrake), 7: (sickle, sheaf), 8: (flail, sack)}


MONTHS = {1: (flagon, platter), 2: (pothook, logs), 3: (pruninghook, spade), 4: (garland, posy), 5: (falcon, maybough),
          6: (scythe, hayrake), 7: (sickle, sheaf), 8: (flail, sack), 9: (grapebasket, vat), 10: (seedbag, harrow),
          11: (acornpole, axe), 12: (peel, block)}


def piece(g):
    """A drawing packed: its box in the grid (w, h, x0, y0), its colours (GColor8; the outlines' alpha bits 10, the
    rest's 11), then a nibble a pixel, row by row, the low nibble first (0 none, k the colour k - 1)."""
    cells = [(x, y, ch) for y, r in enumerate(g.g) for x, ch in enumerate(r) if ch != '.']
    x0, x1 = min(c[0] for c in cells), max(c[0] for c in cells)
    y0, y1 = min(c[1] for c in cells), max(c[1] for c in cells)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    letters = sorted({c[2] for c in cells})
    assert len(letters) <= 15, letters
    def g8(ch):
        r_, g_, b_ = PAL[ch]
        return (0x80 if ch in LINE else 0xC0) | (r_ // 85) << 4 | (g_ // 85) << 2 | b_ // 85
    nib = [0] * (w * h)
    for x, y, ch in cells:
        nib[(y - y0) * w + (x - x0)] = letters.index(ch) + 1
    if len(nib) % 2:
        nib.append(0)
    px = bytes(nib[i] | nib[i + 1] << 4 for i in range(0, len(nib), 2))
    return bytes([w, h, x0, y0, len(letters)] + [g8(ch) for ch in letters]) + px


def clip(dial):
    """How far in from the side the corner is clear of the ring in each of its rows from the top (or bottom) edge:
    outside the ring's outline (plates.ring_shape at half a pixel, the band's outer rule left whole). The corners are
    alike (the outline is symmetric both ways)."""
    import plates
    free = ~plates.ring_shape(dial, 0.5)
    out = []
    for y in range(H_):
        n = 0
        while n < W_ and free[y, n]:
            n += 1
        out.append(n)
    assert all((~plates.ring_shape(dial, 0.5))[dial.h - 1 - y, :out[y]].all() for y in range(H_))
    return bytes(out)


def blob(dial):
    """tools.bin: the corner's clearance (H_ bytes), then twelve month offsets (uint16, from the file's start) and an
    end, then each month's record: its top piece and its bottom piece."""
    records = [piece(MONTHS[m][0]()) + piece(MONTHS[m][1]()) for m in range(1, 13)]
    head = len(clip(dial)) + 2 * 13
    offs, at = [], head
    for rec in records:
        offs.append(at)
        at += len(rec)
    offs.append(at)
    return clip(dial) + struct.pack("<13H", *offs) + b"".join(records)


def paint(img, dial, month, ink=None):
    """The month's tools into a Time 2 face (as plan_render.c corner_tools): the top piece in the top corners, the
    bottom piece in the bottom ones, mirrored on the right, where the corner is clear of the ring; with `ink` (a
    printed or a red plate) their outlines alone, in it."""
    H, W = img.shape[:2]
    lim = clip(dial)
    for k, make in enumerate(MONTHS[month]):
        for y, r in enumerate(make().g):
            for x, ch in enumerate(r):
                if ch == '.' or x >= lim[H_ - 1 - y if k else y] or (ink is not None and ch not in LINE):
                    continue
                yy = H - H_ + y if k else y
                img[yy, x] = img[yy, W - 1 - x] = ink if ink is not None else PAL[ch]
