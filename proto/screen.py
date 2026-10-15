"""The screens' outlines as the watches have them. The Time 2's is its whole rectangle; the Round 2's display lights
the pixels its datasheet lists (LS013B7DD02, table 6-6-2), as PebbleOS has them (fw/board/displays/display_getafix.c,
g_gbitmap_data_row_infos): a little wider than a circle through the pixels' middles. Standard library only (the C
harnesses take it through tools/blobs_h.py)."""

# the first lit pixel of each row, from the top row down to the middle; the rows below mirror these, and each row is
# lit symmetrically, from this pixel to W - 1 - it
ROUND2_TOPLEFT = [
    113, 107, 102, 98, 94, 90, 87, 85, 82, 80, 77, 75, 73, 71, 69, 67, 65, 64,
    62, 60, 59, 57, 56, 54, 53, 52, 50, 49, 48, 46, 45, 44, 43, 42, 41, 40, 39,
    38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 29, 28, 27, 26, 26, 25, 24, 23, 23,
    22, 21, 21, 20, 19, 19, 18, 18, 17, 16, 16, 15, 15, 14, 14, 13, 13, 12, 12,
    11, 11, 10, 10, 10, 9, 9, 8, 8, 8, 7, 7, 6, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4, 3,
    3, 3, 3, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0,
]
assert len(ROUND2_TOPLEFT) == 130


def round2_row(y):
    """(first, last) lit pixel of row y on the Round 2 (260 x 260)."""
    a = ROUND2_TOPLEFT[y] if y < 130 else ROUND2_TOPLEFT[259 - y]
    return a, 259 - a
