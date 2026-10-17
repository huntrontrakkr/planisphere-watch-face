/* The scene blob: what the card shows behind the face on the woodcuts' themes, drawn early in a frame (plan_render.c
 * calls Face.decor where the card is laid, before the window's grid takes its memory): the zodiac's, the astronomer's
 * and the sea's woodcuts, faint in the card round the window, and their roundels in the Time 2's corners. On the watch
 * a code blob of its own (tools/build_blob.py), loaded for the moment it draws and let go; the woodcuts read from their
 * table (scenes.bin) as it goes. The labours are plan_labours.c's. */
#include <string.h>
#include "plan_card.h"
#include "decor_data.h"

/* ---- the zodiac: behind the face the woodcut of the sign the Sun is in, from Ratdolt's Hyginus (Venice, 1482),
 * faint, showing wherever the card is open; in the Time 2's corners the Sun and the Moon and the signs they are in,
 * their glyphs as the Venetian printers cut them (Sacrobosco, 1490: proto/zodiac_art.py), each in its roundel ----- */
/* the woodcut `k` of scenes.bin (proto/woodcuts.py) behind the face, faint, its middle where it was placed from the
 * window's middle, wherever the card is open: streamed from the table a few bytes at a time and decoded as it goes,
 * each pixel by the range coder from the chance of ink its context gives (woodcuts.py encode: seven neighbours, three
 * rows kept) */
typedef struct { const FeastReader *rd; uint32_t at; uint8_t buf[64]; int have, pos; uint32_t range, code; } Stream;
static uint32_t next_byte(Stream *s) {
  if (s->pos == s->have) s->rd->read(s->rd->ctx, s->at, s->buf, sizeof s->buf), s->at += sizeof s->buf, s->have = sizeof s->buf, s->pos = 0;
  return s->buf[s->pos++];
}
static int next_bit(Stream *s, uint16_t *prob) {
  uint32_t p = *prob, bound = (s->range >> 12) * p;
  int b = s->code >= bound;
  if (b) s->code -= bound, s->range -= bound, *prob = (uint16_t)(p - (p >> 4));
  else s->range = bound, *prob = (uint16_t)(p + ((4096 - p) >> 4));
  while (s->range < 1u << 24) s->range <<= 8, s->code = s->code << 8 | next_byte(s);
  return b;
}
/* the sea's plates (woodcuts.py SEA) hang by their waterline SEA_ABOVE rows above the window's top at mean water,
 * riding up to TIDE_SHIFT higher at high water and lower at low; how many pixels above its mean the plate rides now,
 * from the tide's turns: between two as the smooth step 3s^2 - 2s^3 goes, in integers (woodcuts.py tide_shift); 0
 * with none about now */
#define SEA_ABOVE 4
#define TIDE_SHIFT 12
static int tide_shift(const Tides *t, uint32_t minute) {
  for (int i = 0; t && i + 1 < t->n; i++) {
    uint32_t t0 = t->at[i] & ~TIDE_HIGH, t1 = t->at[i + 1] & ~TIDE_HIGH;
    bool h0 = t->at[i] & TIDE_HIGH, h1 = t->at[i + 1] & TIDE_HIGH;
    if (minute < t0 || minute >= t1 || h0 == h1) continue;
    int s = (int)((minute - t0) * 1024 / (t1 - t0)), e = s * s / 1024 * (3072 - 2 * s) / 1024, f = h1 ? e : 1024 - e;
    return (TIDE_SHIFT * 2 * f + 512) / 1024 - TIDE_SHIFT;
  }
  return 0;
}
/* the sea below the waterline, across the card, as Hollar etches open water (woodcuts.py SEA_STROKES, sea_stroke):
 * rows of strokes close and long by the waterline, shorter and further apart as they come nearer, each stretch of a
 * row holding one stroke set along it by a hash, the ends of a stroke of four or more a row lower: a wavelet's crest */
static const uint8_t SEA_STROKES[8][3] = {{1, 14, 12}, {3, 13, 10}, {5, 12, 8}, {8, 11, 6}, {11, 10, 5}, {15, 10, 4},
                                          {20, 9, 3}, {26, 9, 2}};
static void sea_strokes(const DecorCtx *r, const int16_t *inner, int line) {
  for (int n = 0; n < 8; n++) {
    int y = line + SEA_STROKES[n][0], span = SEA_STROKES[n][1], len = SEA_STROKES[n][2];
    uint8_t card[2][4] = {{1, 0, 0, 0}, {1, 0, 0, 0}};   /* (the card's spans on the stroke's row and the next) */
    for (int i = 0; i < 2; i++)
      if ((unsigned)(y + i) < (unsigned)r->p->h) card_row(r, inner, y + i, card[i]);
    for (int x = 0; x < r->p->w; x++) {
      int cell = (x + 64 * span) / span, at = (x + 64 * span) % span;
      int start = (int)(((uint32_t)cell * 40503u + (uint32_t)n * 9973u) & 0xFFFFu) % (span - len + 1);
      if (at < start || at >= start + len) continue;
      int dip = len >= 4 && (at == start || at == start + len - 1), yy = y + dip;
      if (on_screen(r, x, yy) && in_card(card[dip], x)) put(r, x, yy, r->tone);
    }
  }
}
static int bit_at(const uint8_t *row, int x, int w) { return x >= 0 && x < w && row[x >> 3] >> (7 - (x & 7)) & 1; }
/* where the water meets the hulls (woodcuts.py hull_water): the hulls what is inked in the plate's last two rows, `a`
 * and `b`; under one (and SEA_UNDER either side) the row below the waterline washed solid, beside one (within
 * SEA_BESIDE) the waterline's own row lapped, three pixels in four */
#define SEA_UNDER 2
#define SEA_BESIDE 6
/* the far sea, a row of strokes every third row from two above the waterline up to the horizon (woodcuts.py
 * far_stroke): shorter and closer as they near the horizon, none where the plate is inked on its row (`a`) or the one
 * above (`b`), a pixel round, so the farthest ships sit in it too */
static void far_strokes(const DecorCtx *r, const uint8_t card[4], const uint8_t *a, const uint8_t *b, int w, int ox,
                        int y, int d) {
  int n = d / 3, len = 7 - n < 2 ? 2 : 7 - n, span = len + 3 + n;
  for (int x = 0; x < r->p->w; x++) {
    int cell = (x + 64 * span) / span, at = (x + 64 * span) % span;
    int start = (int)(((uint32_t)cell * 40503u + (uint32_t)(16 + n) * 9973u) & 0xFFFFu) % (span - len + 1);
    if (at < start || at >= start + len || !on_screen(r, x, y) || !in_card(card, x)) continue;
    int i = x - ox, inked = 0;
    for (int e = -1; e <= 1; e++) inked |= bit_at(a, i + e, w) | bit_at(b, i + e, w);
    if (!inked) put(r, x, y, r->tone);
  }
}
static void hull_water(const DecorCtx *r, const int16_t *inner, const uint8_t *a, const uint8_t *b, int w, int ox,
                       int line) {
  uint8_t card[2][4] = {{1, 0, 0, 0}, {1, 0, 0, 0}};
  for (int i = 0; i < 2; i++)
    if ((unsigned)(line + i) < (unsigned)r->p->h) card_row(r, inner, line + i, card[i]);
  for (int x = 0; x < w; x++) {
    int near = SEA_BESIDE + 1;                   /* (the nearest hull column, up to SEA_BESIDE away) */
    for (int d = -SEA_BESIDE; d <= SEA_BESIDE; d++)
      if ((bit_at(a, x + d, w) || bit_at(b, x + d, w)) && (d < 0 ? -d : d) < near) near = d < 0 ? -d : d;
    if (near <= SEA_UNDER && on_screen(r, ox + x, line + 1) && in_card(card[1], ox + x))
      put(r, ox + x, line + 1, r->tone);
    if (near > 0 && near <= SEA_BESIDE && x % 4 != 3 && on_screen(r, ox + x, line) && in_card(card[0], ox + x))
      put(r, ox + x, line, r->tone);
  }
}
static void scene(const DecorCtx *r, const int16_t *inner, const FeastReader *rd, int k) {
  Plan *p = r->p;
  uint8_t e[16];
  rd->read(rd->ctx, 2 + 16 * (uint32_t)k, e, 16);
  int w = e[4] | e[5] << 8, h = e[6] | e[7] << 8, dx = (int16_t)(e[8] | e[9] << 8), dy = (int16_t)(e[10] | e[11] << 8);
  int water = (int16_t)(e[12] | e[13] << 8), far = (int16_t)(e[14] | e[15] << 8), rowb = (w + 7) / 8;
  int ox = (p->w - w) / 2 + dx;
  int oy = water < 0 ? (p->win_top + p->win_bottom) / 2 - h / 2 + dy
                     : p->win_top - SEA_ABOVE - water - tide_shift(r->tides, r->minute);
  uint16_t *prob = r->alloc(128 * sizeof *prob + 3 * (size_t)rowb);
  if (!prob) return;
  uint8_t *up2 = (uint8_t *)(prob + 128), *up = up2 + rowb, *row = up + rowb;
  for (int i = 0; i < 128; i++) prob[i] = 2048;
  for (int i = 0; i < 3 * rowb; i++) up2[i] = 0;
  Stream st = {rd, e[0] | e[1] << 8 | e[2] << 16 | (uint32_t)e[3] << 24, {0}, 0, 0, 0xFFFFFFFFu, 0};
  for (int i = 0; i < 5; i++) st.code = st.code << 8 | next_byte(&st);
  for (int j = 0, y = oy; j < h; j++, y++) {
    uint8_t card[4] = {1, 0, 0, 0};                /* (the card's span on this row: none off the screen) */
    if ((unsigned)y < (unsigned)p->h) card_row(r, inner, y, card);
    /* the context carried along the row: the four of the row above from x - 1 to x + 2 (uw, the first its high bit),
     * the two of this row before x (rw), and the one two rows up over x */
    int uw = bit_at(up, 0, w) << 2 | bit_at(up, 1, w) << 1 | bit_at(up, 2, w), rw = 0;
    for (int x = 0; x < w; x++) {
      int c = bit_at(up2, x, w) << 6 | uw << 2 | rw, b = next_bit(&st, &prob[c]);
      uw = (uw << 1 | bit_at(up, x + 3, w)) & 15, rw = (rw << 1 | b) & 3;
      if (!b) continue;
      row[x >> 3] |= (uint8_t)(0x80 >> (x & 7));
      if (on_screen(r, ox + x, y) && in_card(card, ox + x)) put(r, ox + x, y, r->tone);
    }
    if (water >= 0 && j >= far && j >= 1 && j < water && (water - j) % 3 == 2)
      far_strokes(r, card, row, up, w, ox, y, water - j);
    uint8_t *t = up2;
    up2 = up, up = row, row = t;
    for (int i = 0; i < rowb; i++) row[i] = 0;
  }
  if (water >= 0) hull_water(r, inner, up, up2, w, ox, oy + water);   /* (the last two rows, as the loop leaves them) */
  r->release(prob);
  if (water >= 0) sea_strokes(r, inner, oy + water);
}
static void glyph(const DecorCtx *r, const uint8_t *bits, int w, int h, int x0, int y0, uint8_t c) {
  for (int j = 0; j < h; j++)
    for (int i = 0; i < w; i++) {
      int b = j * w + i;
      if (bits[b >> 3] >> (b & 7) & 1) put(r, x0 + i, y0 + j, c);
    }
}
/* four glyphs (decor_data.h ZODIAC_GLYPHS), each in its roundel, in the Time 2's corners: the top two, then the
 * bottom two, left first */
static void roundels(const DecorCtx *r, const uint8_t which[4]) {
  int W = r->p->w, H = r->p->h;
  for (int k = 0; k < 4; k++) {
    int x0 = k & 1 ? W - 17 : 2, y0 = k & 2 ? H - 17 : 2;
    glyph(r, ZODIAC_ROUNDEL, 15, 15, x0, y0, r->ink);
    glyph(r, ZODIAC_GLYPHS[which[k]], 9, 9, x0 + 3, y0 + 3, r->accent);
  }
}
static void zodiac_corners(const DecorCtx *r) {
  const uint8_t which[4] = {12, r->sun_sign, 13, r->moon_sign};   /* the Sun, its sign; the Moon, its sign */
  roundels(r, which);
}
/* the sea's: the Moon's phase, the tide (rising or falling, as the next turn is a high or a low water; an hourglass
 * where it is not known), the compass rose and the anchor */
static void sea_corners(const DecorCtx *r) {
  uint8_t tide = 30;
  for (int i = 0; r->tides && i < r->tides->n; i++)
    if ((r->tides->at[i] & ~TIDE_HIGH) > r->minute) {
      tide = r->tides->at[i] & TIDE_HIGH ? 28 : 29;
      break;
    }
  const uint8_t which[4] = {(uint8_t)(20 + r->moon_phase), tide, 31, 32};
  roundels(r, which);
}
/* the herbal's, the gardener's Moon: its phase; sow while it waxes (new to the last before full), gather while it
 * wanes (the phase drawn mirrored in the south, the waxing the same); the spade and the watering pot */
static void herbal_corners(const DecorCtx *r) {
  int k = r->south ? (8 - r->moon_phase) % 8 : r->moon_phase;
  const uint8_t which[4] = {(uint8_t)(20 + r->moon_phase), (uint8_t)(k < 4 ? 33 : 34), 35, 36};
  roundels(r, which);
}
/* the astronomer's: the brightest planets above the horizon, brightest first, and in a corner none takes Tycho's new
 * star of 1572 */
static void astronomer_corners(const DecorCtx *r) {
  uint8_t which[4];
  for (int k = 0; k < 4; k++) which[k] = r->planets[k] < 5 ? (uint8_t)(14 + r->planets[k]) : 19;
  roundels(r, which);
}
/* ---- the battery's candle clock (proto/plates.py candle), an option, drawn once the face is: a candle banded as the
 * hour-candles were, burnt down as far as the charge, its figure in the tiny type beneath. Placed in the first clear
 * place of the card's upper right: row by row from the top, each from the ring's side inward, where its block
 * (CANDLE_W wide, the widest figure's, CANDLE_H tall) and a pixel round lie inside the ring's rule by two, out of the
 * window, on nothing but the card or what is faint in it ---------------------------------------------------------- */
#define CANDLE_W 15
#define CANDLE_UP 14                             /* rows above the saucer: the wax, the wick, the tallest flame */
#define CANDLE_H (CANDLE_UP + 7)                 /* and the figure below it, two down, five tall */
typedef struct { uint32_t bit; uint8_t w, h; uint16_t pad; } MaskIndex;
static inline uint8_t get(const DecorCtx *r, int x, int y) {
  const Plan *p = r->p;
  return (unsigned)y < (unsigned)p->h && x >= p->rx0[y] && x <= p->rx1[y] ? ROW(p, y)[x] : 0;
}
/* the card where nothing is drawn: the jacket, foxed on the old rag paper (plan_render.c card_at) */
static uint8_t card_at(const DecorCtx *r, int x, int y) {
  const Plate *P = r->plate;
  if (P->fox) {
    const uint8_t *bn = sec(r->p->data, SEC_BLUE_NOISE);
    int fy = (r->p->h - 1 - y) & 63, fx = (r->p->w - 1 - x) & 63;
    if ((bn[fy * 64 + fx] * 16 + 8) < P->fox) return P->fox_c;
  }
  return P->jacket;
}
static const MaskIndex *tiny_glyph(const DecorCtx *r, char ch) {
  for (int i = 0; TINY_CHARS[i]; i++)
    if (TINY_CHARS[i] == ch) return (const MaskIndex *)(const void *)sec(r->p->data, SEC_MASK_INDEX) + M_TINY0 + i;
  return NULL;
}
static bool candle_clear(const DecorCtx *r, const int16_t *inner, int bx, int by) {
  for (int y = by - 1; y <= by + CANDLE_H; y++) {
    if ((unsigned)y >= (unsigned)r->p->h || inner[2 * y] > inner[2 * y + 1]) return false;
    for (int x = bx - 1; x <= bx + CANDLE_W; x++) {
      if (x < inner[2 * y] + 2 || x > inner[2 * y + 1] - 2 || inside(r, x, y)) return false;
      uint8_t c = get(r, x, y);
      if (c != card_at(r, x, y) && c != r->tone) return false;
    }
  }
  return true;
}
static void candle(const DecorCtx *r) {
  const int16_t *inner = sec16(r->p->geom, GEO_INNER);
  int bx = -1, by = -1, W = r->p->w, H = r->p->h;
  for (int y = 1; y + CANDLE_H < H && bx < 0; y++) {
    if (inner[2 * y] > inner[2 * y + 1]) continue;
    int right = inner[2 * y + 1] - 3 - CANDLE_W;
    for (int x = right; x >= right - 24 && x >= W / 2 && bx < 0; x--)
      if (candle_clear(r, inner, x, y)) bx = x, by = y;
  }
  if (bx < 0) return;
  /* set off from what is behind it by the card round the candle and round its figure, then drawn */
  int pct = r->battery, n = (pct + 5) / 10, x0 = bx + CANDLE_W / 2 - 2, base = by + CANDLE_UP;
  if (pct && n < 1) n = 1;
  char fig[6];
  int k = 0;
  if (pct >= 100) fig[k++] = '1';
  if (pct >= 10) fig[k++] = (char)('0' + pct / 10 % 10);
  fig[k++] = (char)('0' + pct % 10), fig[k++] = '%', fig[k] = 0;
  int fw = -1;
  for (const char *c = fig; *c; c++) fw += tiny_glyph(r, *c)->w + 1;
  int fx = x0 + 2 - fw / 2;
  for (int y = base - n - (r->charging ? 5 : 4); y <= base + 7; y++)
    for (int x = (y > base ? fx : x0) - 1; x <= (y > base ? fx + fw : x0 + 5); x++) put(r, x, y, card_at(r, x, y));
  uint8_t ink = r->ink, flame = pct <= 20 ? r->accent : r->planet;
  for (int i = 0; i < 5; i++) put(r, x0 + i, base, ink);           /* the saucer */
  for (int j = 0; j < 10; j++) {                                    /* the wax: inked as far as the charge; the rest */
    int y = base - 10 + j;                                          /* burnt away, its outline dotted in the ink */
    bool lit = j >= 10 - n;
    if (lit) for (int i = 1; i <= 3; i++) put(r, x0 + i, y, ink);
    else if (j == 0) put(r, x0 + 1, y, ink), put(r, x0 + 3, y, ink);
    else if (j % 2 == 0) put(r, x0 + 1, y, ink), put(r, x0 + 3, y, ink);
    if (lit && j % 2) put(r, x0, y, ink);                           /* the bands, a fifth each */
  }
  if (n) {
    put(r, x0 + 2, base - n - 1, ink);                              /* the wick, the flame */
    for (int q = 2; q <= (r->charging ? 4 : 3); q++) put(r, x0 + 2, base - n - q, flame);
  }
  const uint8_t *bits = sec(r->p->data, SEC_MASK_DATA);
  for (const char *c = fig; *c; c++) {                              /* the figure */
    const MaskIndex *mi = tiny_glyph(r, *c);
    for (int j = 0; j < mi->h; j++)
      for (int i = 0; i < mi->w; i++) {
        uint32_t b = mi->bit + (uint32_t)(j * mi->w + i);
        if ((bits[b >> 3] >> (b & 7)) & 1) put(r, fx + i, base + 2 + j, ink);
      }
    fx += mi->w + 1;
  }
}

bool plan_decor(const DecorCtx *dc, const FeastReader *tools, const FeastReader *scenes) {
  if (dc->candle) {                              /* (the candle's own call, once the face is drawn) */
    candle(dc);
    return true;
  }
  DecorCtx copy = *dc;                           /* (the woodcuts' table with it) */
  copy.scenes = scenes;
  const DecorCtx *d = &copy;
  if (d->scenes && d->theme >= THEME_ZODIAC) {   /* the woodcut: the Sun's sign's, or the month's of the theme's twelve
                                                    after the zodiac's (the herbal's by the seasons: in the south half
                                                    a year round) */
    int m = d->theme == THEME_HERBAL && d->south ? (d->month + 6) % 12 : d->month;
    scene(d, sec16(d->p->geom, GEO_INNER), d->scenes, d->theme == THEME_ZODIAC ? d->sun_sign
                                                      : 12 * (d->theme - THEME_ZODIAC) + m);
  }
  if (d->corners == THEME_ZODIAC) {
    zodiac_corners(d);
    return true;
  }
  if (d->corners == THEME_ASTRONOMER) {
    astronomer_corners(d);
    return true;
  }
  if (d->corners == THEME_HERBAL) {
    herbal_corners(d);
    return true;
  }
  if (d->corners == THEME_SEA) {
    sea_corners(d);
    return true;
  }
  return true;
}
