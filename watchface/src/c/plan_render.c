/* The face, drawn as the prototype draws it (proto/plates.py render()), layer on layer into the screen: the card,
 * the window's sky, the Milky Way, the circles and figures, the stars, the planets, the Moon and the Sun, the hills
 * and the village, the names, the window's rims, the ring with its hours and the Sun's hand, the time, the date and
 * the almanac's line. The pieces and the ring's geometry come from the prototype (plan_data.h, the blobs).
 *
 * Still to come from the prototype: the weather's clouds, rain and snow; eclipses, meteor showers and the sky's
 * news; Jupiter's moons; the labours of the months; the real skyline; the animations.
 */
#include "plan.h"
#include "plan_math.h"
#include <string.h>

#define C8(r, g, b) ((uint8_t)(0xC0 | (r) << 4 | (g) << 2 | (b)))
#define LV(c, s) (((c) >> (s)) & 3)
#define MAX_BOXES 80
#define VILLAGE_DX 72                    /* the village and hills reach this far either side of the south point */
#define NONE16 0x7fff

/* ---- the blobs ------------------------------------------------------------------------------------------------ */
static const uint8_t *sec(const uint8_t *blob, int i) { return blob + ((const uint32_t *)(const void *)blob)[i]; }
static const int16_t *sec16(const uint8_t *blob, int i) { return (const int16_t *)(const void *)sec(blob, i); }

typedef struct { uint16_t off; uint8_t w, h; } DrawIndex;
typedef struct { uint32_t bit; uint8_t w, h; uint16_t pad; } MaskIndex;
typedef struct { uint16_t bit; uint8_t w, adv; } GlyphIndex;
typedef struct { uint32_t bit; uint8_t w, h, base, pad; } FigureIndex;

/* ---- a line of type: 14 rows, up to 256 pixels ---------------------------------------------------------------- */
typedef struct { int w; uint32_t bits[FONT_ROWS][8]; } Text;

/* ---- the drawing's state -------------------------------------------------------------------------------------- */
typedef struct {
  Plan *p;
  const Face *f;
  const Plate *P;
  Sky sky;
  Civil local;
  int64_t utc;
  int32_t offset;
  int W, H;
  bool rect, south, paper, live, red, light_paper, dark, figs, lit_moon, closed_sky, rete, woodcut, clock24;
  float cx, cy, k, lst, alat, sl, cl;
  float sun_alt, s_eff, sdec, sha, mphase;   /* the Sun's declination and hour angle in the chart's frame */
  uint8_t sun_c[8], planet_c[8], moon_c[8];  /* colours by role; 0 none */
  uint8_t tint, ramp[6];
  int nramp;
  const uint8_t *bn;
  int32_t thresh12[256];                     /* each blue-noise level's threshold for the Milky Way */
  /* the window's ground: two values on a grid every 4 pixels over the window */
  int gx0, gy0, gnx, gny;
  int16_t *ga, *gb, *gra, *gdec;
  float ik, sk_day, sk_lift, sk_twf, sk_warm, ssd, csd, csh, ssh, sl0, cl0;
  int16_t bright[96][2];                     /* the stars brighter than 2.1 on the screen, for the zodiac to avoid */
  int nbright;
  /* what names keep clear of */
  int16_t box[MAX_BOXES][4];
  int nbox;
  int16_t btop[MAX_W];                       /* the land's top in each column (hills, village), NONE16 none */
  int16_t edge[2 * VILLAGE_DX + 1];          /* the window's lowest row at each column from the south point, -1 none */
  int16_t vtop[2 * VILLAGE_DX + 1], vground[2 * VILLAGE_DX + 1];
  int col;
  /* the weather, as the sky shows it */
  bool wx, fog, falls, rain_or_hail, thunder, snow_lying, frost, smoke, snow_falls;
  float stratus, cumulus, haze, wind, wind_from;
  Text t1, t2, t3, t4;
} R;

/* ---- pixels --------------------------------------------------------------------------------------------------- */
static inline void put(R *r, int x, int y, uint8_t c) {
  Plan *p = r->p;
  if ((unsigned)y < (unsigned)r->H && x >= p->rx0[y] && x <= p->rx1[y]) p->rows[y][x] = c;
}
static inline uint8_t get(R *r, int x, int y) {
  Plan *p = r->p;
  if ((unsigned)y < (unsigned)r->H && x >= p->rx0[y] && x <= p->rx1[y]) return p->rows[y][x];
  return 0;
}
static inline bool inside(R *r, int x, int y) {
  return (unsigned)y < (unsigned)r->H && x >= r->p->wx0[y] && x <= r->p->wx1[y];
}
static inline bool on_screen(R *r, int x, int y) { return (unsigned)x < (unsigned)r->W && (unsigned)y < (unsigned)r->H; }

/* the blue-noise threshold at a pixel, 0..1 */
static inline float tt(R *r, int x, int y) { return ((float)r->bn[(y & 63) * 64 + (x & 63)] + 0.5f) * (1.0f / 256); }

/* a colour mixed with another, a parts in one, then put to the nearest of the palette's levels */
static uint8_t mix(uint8_t c1, uint8_t c2, float a) {
  uint8_t out = 0xC0;
  for (int s = 0; s <= 4; s += 2) {
    float v = (float)(LV(c1, s) * 85) * a + (float)(LV(c2, s) * 85) * (1.0f - a);
    int l = pyf_floor(v / 85 + 0.5f);
    out |= (uint8_t)((l < 0 ? 0 : l > 3 ? 3 : l) << s);
  }
  return out;
}
static int level_sum(uint8_t c) { return LV(c, 0) + LV(c, 2) + LV(c, 4); }

/* ---- pieces ---------------------------------------------------------------------------------------------------- */
static const DrawIndex *drawing(R *r, int d) { return (const DrawIndex *)(const void *)sec(r->p->data, SEC_DRAW_INDEX) + d; }
static int role_at(R *r, const DrawIndex *di, int i, int j) {
  const uint8_t *data = sec(r->p->data, SEC_DRAW_DATA) + di->off;
  int n = j * di->w + i;
  return (data[n >> 1] >> ((n & 1) * 4)) & 15;
}
/* the drawing with its top-left at (x0, y0), turned: flip bit 1 mirrors it left to right, bit 2 top to bottom */
static void paint_at(R *r, int d, int x0, int y0, const uint8_t col[8], bool in_window, int flip) {
  const DrawIndex *di = drawing(r, d);
  for (int j = 0; j < di->h; j++)
    for (int i = 0; i < di->w; i++) {
      int v = role_at(r, di, (flip & 1) ? di->w - 1 - i : i, (flip & 2) ? di->h - 1 - j : j);
      int x = x0 + i, y = y0 + j;
      if (v && v < 8 && col[v] && on_screen(r, x, y) && (!in_window || inside(r, x, y))) put(r, x, y, col[v]);
    }
}
/* centred on (x, y) as the prototype centres: its middle pixel there, halves rounded to even */
static void paint(R *r, int d, float x, float y, const uint8_t col[8], bool in_window) {
  const DrawIndex *di = drawing(r, d);
  paint_at(r, d, pyf_round(x - (di->w - 1) / 2.0f), pyf_round(y - (di->h - 1) / 2.0f), col, in_window, 0);
}

static const MaskIndex *mask(R *r, int m) { return (const MaskIndex *)(const void *)sec(r->p->data, SEC_MASK_INDEX) + m; }
static bool mask_at(R *r, const MaskIndex *mi, int i, int j) {
  const uint8_t *data = sec(r->p->data, SEC_MASK_DATA);
  uint32_t n = mi->bit + (uint32_t)(j * mi->w + i);
  return (data[n >> 3] >> (n & 7)) & 1;
}
static void mask_put(R *r, int m, int x0, int y0, uint8_t c, bool in_window, bool mirror) {
  const MaskIndex *mi = mask(r, m);
  for (int j = 0; j < mi->h; j++)
    for (int i = 0; i < mi->w; i++)
      if (mask_at(r, mi, mirror ? mi->w - 1 - i : i, j)) {
        int x = x0 + i, y = y0 + j;
        if (on_screen(r, x, y) && (!in_window || inside(r, x, y))) put(r, x, y, c);
      }
}

/* the screen position of (ra, dec): a planisphere seen from below, south at the bottom, east on the left */
static void project(R *r, float ra, float dec, float *x, float *y) {
  float h = r->lst - ra;
  if (r->south) dec = -dec, h = -h;
  float rho = (90.0f - dec) * r->k;
  *x = r->cx + rho * (float)f_sind((float)h);
  *y = r->cy + rho * (float)f_cosd((float)h);
}
/* a point of the ecliptic at longitude `lon`, as right ascension and declination (for drawing: single precision) */
static void ecl_point(R *r, float lon, float *ra, float *dec) {
  float sl = f_sind(lon), e = (float)r->sky.eps;
  *ra = pyf_mod(f_atan2d(sl * f_cosd(e), f_cosd(lon)), 360);
  *dec = f_asind(sl * f_sind(e));
}
/* a point's altitude here (for drawing's decisions: single precision) */
static float altitude(R *r, double ra, double dec) {
  float d = (float)dec;
  return f_asind(r->sl0 * f_sind(d) + r->cl0 * f_cosd(d) * f_cosd(r->lst - (float)ra));
}
#define STAR_SIZE 6
static int star_mag(const uint8_t *s) { return ((s[4] | s[5] << 8) >> 3) - 200; }   /* hundredths */
static int star_class(const uint8_t *s) { return s[4] & 7; }                      /* by colour */
static float star_ra(const uint8_t *s) { return (s[0] | s[1] << 8) * 360.0f / 65536; }
static float star_dec(const uint8_t *s) { return (s[2] | s[3] << 8) * 180.0f / 65535 - 90; }

/* ---- type ------------------------------------------------------------------------------------------------------ */
static void t_clear(Text *t) { memset(t, 0, sizeof *t); }
static inline void t_set(Text *t, int x, int y) {
  if ((unsigned)x < 256 && (unsigned)y < FONT_ROWS) t->bits[y][x >> 5] |= 1u << (x & 31);
}
static inline bool t_get(const Text *t, int x, int y) {
  return (unsigned)x < 256 && (unsigned)y < FONT_ROWS && ((t->bits[y][x >> 5] >> (x & 31)) & 1);
}
/* the inked rows: first and last (0, 0 for none) */
static void t_rows(const Text *t, int *r0, int *r1) {
  *r0 = *r1 = -1;
  for (int y = 0; y < FONT_ROWS; y++)
    for (int i = 0; i < 8; i++)
      if (t->bits[y][i]) { if (*r0 < 0) *r0 = y; *r1 = y; break; }
  if (*r0 < 0) *r0 = *r1 = 0;
}
static void t_mask(Text *t, R *r, int m, int x0, int y0) {
  const MaskIndex *mi = mask(r, m);
  for (int j = 0; j < mi->h; j++)
    for (int i = 0; i < mi->w; i++)
      if (mask_at(r, mi, i, j)) t_set(t, x0 + i, y0 + j);
}
/* the glyphs of `s` set from column x, each its advance (and `track`) on, into t (or only measured, t NULL):
 * returns the column after the last ink */
static int t_run(Text *t, R *r, int x, const char *s, int track) {
  const GlyphIndex *gi = (const GlyphIndex *)(const void *)sec(r->p->data, SEC_GLYPHS);
  const uint8_t *font = sec(r->p->data, SEC_FONT_DATA);
  int last = 0;
  for (; *s; s++) {
    int ch = (uint8_t)*s;
    if (ch < 32 || ch > 126) ch = '?';
    const GlyphIndex *g = gi + (ch - 32);
    for (int i = 0; i < g->w; i++)
      for (int j = 0; j < FONT_ROWS; j++) {
        uint32_t n = g->bit + (uint32_t)(j * g->w + i);
        if ((font[n >> 3] >> (n & 7)) & 1) {
          if (t) t_set(t, x + i, j);
          if (x + i + 1 > last) last = x + i + 1;
        }
      }
    x += g->adv + track;
  }
  return last;
}
/* a name in the pixel type, upright or oblique (leaning a pixel every three rows above the baseline) */
static void pixel_text(Text *t, R *r, const char *s, bool oblique, int track) {
  t_clear(t);
  int w = t_run(t, r, 0, s, track);
  t->w = w > 0 ? w : 1;
  if (!oblique) return;
  for (int y = 0; y < FONT_ROWS; y++) {
    int sh = FONT_ASC - y >= 0 ? (FONT_ASC - y) / 3 : 0;
    if (!sh) continue;
    for (int i = 7; i >= 0; i--) {
      uint32_t lo = i > 0 ? t->bits[y][i - 1] : 0;
      t->bits[y][i] = (t->bits[y][i] << sh) | (lo >> (32 - sh));
    }
  }
  t->w += 3;
}
static void number(char *out, int v, int digits) {
  char tmp[8];
  int n = 0;
  do { tmp[n++] = (char)('0' + v % 10); v /= 10; } while (v || n < digits);
  for (int i = 0; i < n; i++) out[i] = tmp[n - 1 - i];
  out[n] = 0;
}
/* 6h17m: the figures, then raised h and m */
static void time_text(Text *t, R *r, int h, int m) {
  char a[8], b[8];
  number(a, h, 1), number(b, m, 2);
  t_clear(t);
  int x = t_run(t, r, 0, a, 0) + 1;
  t_mask(t, r, M_SUP_H, x, 0);
  x += 3 + 2;
  int wb = t_run(NULL, r, 0, b, 0);
  t_run(t, r, x, b, 0);
  x += wb + 1;
  t_mask(t, r, M_SUP_M, x, 2);
  t->w = x + 5;
}
/* 61°: the figures (a minus before frost), then a raised ring */
static void temp_text(Text *t, R *r, int n) {
  char a[8];
  number(a, n < 0 ? -n : n, 1);
  t_clear(t);
  int x = 0;
  if (n < 0) {
    for (int i = 0; i < 3; i++) t_set(t, i, FONT_ASC - 4);
    x = 4;
  }
  int wa = t_run(NULL, r, 0, a, 0);
  t_run(t, r, x, a, 0);
  x += wa + 1;
  t_mask(t, r, M_SUP_DEG, x, 1);
  t->w = x + 3;
}
/* append `b` to `a`, `gap` pixels after it */
static void t_append(Text *a, const Text *b, int gap) {
  int x0 = a->w ? a->w + gap : 0;
  for (int y = 0; y < FONT_ROWS; y++)
    for (int x = 0; x < b->w; x++)
      if (t_get(b, x, y)) t_set(a, x0 + x, y);
  a->w = x0 + b->w;
}

static uint8_t ground_at(R *r, int x, int y);

static int anchor_x(const Text *t, float x, int anchor) {
  return anchor == 0 ? pyf_round(x - t->w / 2.0f) : anchor == 1 ? pyf_round(x) : pyf_round(x - t->w);
}
/* lay a line of type at (x, y): anchor 0 centre, 1 its left end, 2 its right end; y on the inked rows' middle; a
 * halo (a pixel all round each letter, within its own box) of the ground beneath when asked */
static void stamp(R *r, const Text *t, float x, float y, uint8_t c, bool halo, bool in_window, int anchor) {
  int r0, r1;
  t_rows(t, &r0, &r1);
  int x0 = anchor_x(t, x, anchor), y0 = pyf_round(y - (r0 + r1) / 2.0f);
  if (halo)
    for (int j = 0; j < FONT_ROWS; j++)
      for (int i = 0; i < t->w; i++) {
        if (t_get(t, i, j)) continue;
        bool near = false;
        for (int dj = -1; dj <= 1 && !near; dj++)
          for (int di = -1; di <= 1; di++)
            if (i + di >= 0 && i + di < t->w && t_get(t, i + di, j + dj)) { near = true; break; }
        int X = x0 + i, Y = y0 + j;
        if (near && on_screen(r, X, Y) && (!in_window || inside(r, X, Y))) put(r, X, Y, ground_at(r, X, Y));
      }
  for (int j = 0; j < FONT_ROWS; j++)
    for (int i = 0; i < t->w; i++)
      if (t_get(t, i, j)) {
        int X = x0 + i, Y = y0 + j;
        if (on_screen(r, X, Y) && (!in_window || inside(r, X, Y))) put(r, X, Y, c);
      }
}
static void box_of(const Text *t, float x, float y, int anchor, int16_t b[4]) {
  int r0, r1;
  t_rows(t, &r0, &r1);
  int x0 = anchor_x(t, x, anchor), y0 = pyf_round(y - (r0 + r1) / 2.0f);
  b[0] = (int16_t)(x0 - 1), b[1] = (int16_t)(y0 + r0 - 1), b[2] = (int16_t)(x0 + t->w + 1), b[3] = (int16_t)(y0 + r1 + 2);
}

/* ---- the window ---------------------------------------------------------------------------------------------- */
/* how many of a pixel's sixteen sample points see the sky above the horizon, inside the star disc */
static int window_cover(const Plan *p, int x, int y, float sl, float cl) {
  int n = 0;
  for (int j = 0; j < 4; j++)
    for (int i = 0; i < 4; i++) {
      float dx = (4 * x + i + 0.5f) / 4 - p->cx, dy = (4 * y + j + 0.5f) / 4 - p->cy;
      float rho = f_sqrt(dx * dx + dy * dy);
      if (rho > p->r_disc) continue;
      float dec = 90.0f - rho / p->k;
      float ch = rho > 0 ? dy / rho : 1.0f;
      if (sl * f_sind(dec) + cl * f_cosd(dec) * ch > 0) n++;
    }
  return n;
}

/* ---- the ring for the latitude ---------------------------------------------------------------------------- */
enum { TRACK_INNER, TRACK_OUT1, TRACK_THREAD, TRACK_BEAD };
static const int8_t NUMERAL_HOURS[6] = {3, 6, 9, 15, 18, 21};

/* where the hour ray from the pole at dial angle `a` (degrees from the bottom, anticlockwise) meets a track */
static void track_hit(const Plan *p, int track, float a, float *x, float *y) {
  const int16_t *t = sec16(p->geom, GEO_TRACKS) + track * 720;
  float ux = f_sind(a), uy = f_cosd(a), px = p->cx, py = p->cy;
  int i0 = ((int)(float)pyf_floor(a) % 360 + 360) % 360;
  for (int k = 0; k < 360; k++)
    for (int side = 0; side < 2; side++) {
      int i = side ? (i0 - k - 1 + 720) % 360 : (i0 + k) % 360, j = (i + 1) % 360;
      float qx = t[2 * i] / 16.0f - px, qy = t[2 * i + 1] / 16.0f - py, rx = t[2 * j] / 16.0f - px, ry = t[2 * j + 1] / 16.0f - py;
      float si = ux * qy - uy * qx, sj = ux * ry - uy * rx;
      if ((si > 0 && sj > 0) || (si < 0 && sj < 0) || si == sj) continue;
      float f = si / (si - sj), hx = qx + (rx - qx) * f, hy = qy + (ry - qy) * f;
      if (hx * ux + hy * uy > 0) { *x = px + hx, *y = py + hy; return; }
    }
  *x = px, *y = py;
}
/* where the hour ray crosses the ring's inner edge, moved `out` pixels further along it */
static void edge_point(const Plan *p, float a, float out, float *x, float *y) {
  track_hit(p, TRACK_INNER, a, x, y);
  *x += out * f_sind(a), *y += out * f_cosd(a);
}

/* the ticks and studs for where the pole stands */
static void ring_geometry(Plan *p) {
  p->nticks = 0;
  for (int half = 0; half < 48; half++) {
    int hour2 = half;                             /* the hour, floatd */
    if (hour2 == 0 || hour2 == 24) continue;      /* MIDNIGHT and NOON */
    bool numbered = false;
    for (int i = 0; i < 6; i++) numbered |= half % 2 == 0 && hour2 == 2 * NUMERAL_HOURS[i];
    if (numbered) continue;
    float a = (hour2 / 2.0f - 12) * 15;
    if (a < -180) a += 360;
    if (!(a >= 0 && a <= 180)) continue;         /* one side; the other is its mirror */
    float len = half % 2 == 0 ? 2 : 1, x0, y0, x1, y1;
    edge_point(p, a, 0.5f, &x0, &y0);
    edge_point(p, a, 0.5f + len - 0.01f, &x1, &y1);
    float adx = f_abs(x1 - x0), ady = f_abs(y1 - y0);
    int n = (int)(adx > ady ? adx : ady) + 1;
    for (int k = 0; k <= n; k++) {
      float t = (float)k / (n > 0 ? n : 1);
      int16_t tx = (int16_t)pyf_floor(x0 + (x1 - x0) * t), ty = (int16_t)pyf_floor(y0 + (y1 - y0) * t);
      bool seen = false;
      for (int j = 0; j < p->nticks; j++) seen |= p->ticks[j][0] == tx && p->ticks[j][1] == ty;
      if (!seen && p->nticks < 64) p->ticks[p->nticks][0] = tx, p->ticks[p->nticks][1] = ty, p->nticks++;
    }
  }
  for (int i = 0; i < 6; i++) {
    float x, y;
    edge_point(p, (NUMERAL_HOURS[i] - 12) * 15.0f, 0, &x, &y);
    p->studs[i][0] = (int16_t)pyf_floor(x), p->studs[i][1] = (int16_t)pyf_floor(y);
  }
  p->num_style = -1;
}

void plan_init(Plan *p, int w, int h, const uint8_t *data, const uint8_t *geom) {
  memset(p, 0, sizeof *p);
  p->w = w, p->h = h, p->data = data, p->geom = geom;
  p->rect = w != h;
  p->lat_key = 1e9f;
  p->ev_kind = -1;
}

void plan_window(Plan *p, double lat) {
  if (p->lat_key == lat) return;
  p->lat_key = lat;
  float alat = f_abs((float)lat), reach = 180.0f - alat;
  int W = p->w, H = p->h;
  if (p->rect) {
    float top = 17.0f + 62.0f, bottom = H - 17.0f - 5.0f;
    float k = (bottom - top) / 180.0f, k2 = (W / 2.0f - 17.0f - 6.0f) / 90.0f;
    p->k = (float)(k < k2 ? k : k2);
    p->cx = W / 2.0f, p->cy = (float)(top + alat * p->k);
    p->r_disc = (float)(reach * p->k);
    p->R = (W < H ? W : H) / 2.0f;
  } else {
    p->R = (W < H ? W : H) / 2.0f;
    p->cx = W / 2.0f, p->cy = H / 2.0f;
    p->r_disc = p->R - 18.0f - 6.0f;
    p->k = (float)(p->r_disc / reach);
  }
  float sl = f_sind((float)alat), cl = f_cosd((float)alat);
  p->win_top = -1, p->win_bottom = -1;
  int half = W / 2;
  for (int y = 0; y < H; y++) {
    p->wx0[y] = 1, p->wx1[y] = 0;
    if (window_cover(p, half - 1, y, sl, cl) < 9) continue;
    int lo = 0, hi = half - 1;                   /* the first pixel in from the left that is mostly sky */
    if (window_cover(p, 0, y, sl, cl) >= 9) hi = 0;
    else
      while (hi - lo > 1) {
        int mid = (lo + hi) / 2;
        if (window_cover(p, mid, y, sl, cl) >= 9) hi = mid;
        else lo = mid;
      }
    p->wx0[y] = (int16_t)hi, p->wx1[y] = (int16_t)(W - 1 - hi);
    if (p->win_top < 0) p->win_top = (int16_t)y;
    p->win_bottom = (int16_t)y;
  }
  ring_geometry(p);
}

/* ---- the sky's ground ------------------------------------------------------------------------------------------ */
static const uint8_t COOL[6] = {C8(0, 0, 1), C8(0, 0, 2), C8(0, 1, 2), C8(0, 2, 3), C8(1, 2, 3), C8(2, 3, 3)};
static const uint8_t WARM[5] = {C8(1, 1, 2), C8(2, 1, 2), C8(3, 1, 1), C8(3, 2, 1), C8(3, 3, 2)};
static const uint8_t GREY[4] = {0, C8(1, 1, 1), C8(2, 2, 2), C8(3, 3, 3)};
static const uint8_t REDS[3] = {C8(0, 0, 0), C8(1, 0, 0), C8(2, 0, 0)};

/* the sky's brightness on the COOL ramp (0 night .. 5 palest) and a warm glow 0..1 (proto/render2.py sky_scalar), the
 * Sun's part worked out once a drawing (sky_constants) */
static void sky_constants(R *r, float s) {
  r->sk_day = f_smooth(-3, 7, s), r->sk_lift = f_smooth(-18, -1, s);
  r->sk_twf = 0.6f + 0.4f * r->sk_lift;
  r->sk_warm = f_smooth(-11, -1, s) * (1 - f_smooth(-1, 5, s)) * 1.25f;
}
static void sky_scalar(R *r, float alt, float gamma, float *b, float *warm) {
  float a = f_clamp(alt, 0, 90), b_tw = 0, b_day = 0;
  if (r->sk_day < 1 && r->sk_lift > 0) {
    float horizon = f_exp(-a * (1.0f / 32)), sunside = f_exp(-gamma * (1.0f / 80));
    b_tw = r->sk_lift * (0.8f + 3.0f * horizon * (0.25f + 0.75f * sunside) * r->sk_twf);
  }
  if (r->sk_day > 0) {
    float q = 1 - a * (1.0f / 90);
    b_day = 2.3f + 2.1f * q * q * q + 1.4f * f_exp(-gamma * (1.0f / 11));
  }
  *b = f_clamp(b_tw * (1 - r->sk_day) + b_day * r->sk_day, 0, 5);
  *warm = r->sk_warm > 0 ? f_clamp(r->sk_warm * f_exp(-a * (1.0f / 15) - gamma * (1.0f / 42)), 0, 1) : 0;
}

static int q12(float v) { return (int)(v * 4096 + (v < 0 ? -0.5f : 0.5f)); }

/* the grid's values at a node (pixel coordinates of the point): the ground's (Q12, the woodcut's ecliptic latitude Q8)
 * and its warmth (Q12); with the Milky Way, the point's right ascension (Q6) and declination (Q8) */
static void node_values(R *r, float x, float y, int16_t *va, int16_t *vb, int16_t *vra, int16_t *vdec) {
  float dx = x - r->cx, dy = y - r->cy, rho = f_sqrt(dx * dx + dy * dy), irho = rho > 0 ? 1 / rho : 0;
  float dec = 90.0f - rho * r->ik, ch = rho > 0 ? dy * irho : 1, sh = dx * irho;
  *va = *vb = 0;
  if (vra || r->woodcut) {
    float ha = f_atan2d(dx, dy), ra = r->south ? r->lst + ha : r->lst - ha;
    ra = pyf_mod(ra, 360);
    if (vra) *vra = (int16_t)(int)(ra * 64), *vdec = (int16_t)(int)((r->south ? -dec : dec) * 256);
    if (r->woodcut) {                             /* the ecliptic latitude, for the zodiac's band */
      float d = r->south ? -dec : dec, e = (float)r->sky.eps;
      *va = (int16_t)(int)(f_asind(f_sind(d) * f_cosd(e) - f_cosd(d) * f_sind(e) * f_sind(ra)) * 256);
      return;
    }
  }
  if (r->P->window != WIN_SKY && r->P->window != WIN_RED) return;
  if (r->closed_sky) {                            /* an even grey under a closed sky, paler overhead */
    float k = f_smooth(-9, 5, r->s_eff);
    if (k <= 0) return;
    float lift = r->fog ? 0.75f : (r->thunder || r->rain_or_hail) ? -1.0f : 0.0f;
    float palt = f_asind(r->sl * f_sind(dec) + r->cl * f_cosd(dec) * ch);
    *va = (int16_t)q12(f_clamp((2.0f + 0.45f * f_sind(f_clamp(palt, 0, 90)) + lift) * k, 0, 3));
    return;
  }
  if (r->sk_lift <= 0 && r->sk_day <= 0 && r->sk_warm <= 0) return;   /* night: the sky's darkest everywhere */
  float sd = f_sind(dec), cd = f_cosd(dec);
  float palt = f_asind(r->sl * sd + r->cl * cd * ch);
  float gamma = f_acosd(sd * r->ssd + cd * r->csd * (ch * r->csh + sh * r->ssh));
  float b, w;
  sky_scalar(r, palt, gamma, &b, &w);
  if (r->P->window == WIN_RED) *va = (int16_t)q12(f_clamp(b * 0.5f, 0, 2));
  else *va = (int16_t)q12(f_clamp(b, 0, (float)(r->nramp - 1))), *vb = (int16_t)q12(w);
}

/* the grid cell holding a pixel: its corners' values, and where in it the pixel is (0..3 each way) */
typedef struct { int v00, v10, v01, v11, dx, dy; } Cell;
static void cell_at(R *r, const int16_t *g, int x, int y, Cell *c) {
  int gx = x - r->gx0, gy = y - r->gy0;
  int i = gx >> 2, j = gy >> 2;
  if (i < 0) i = 0;
  if (j < 0) j = 0;
  if (i > r->gnx - 2) i = r->gnx - 2;
  if (j > r->gny - 2) j = r->gny - 2;
  c->dx = gx - 4 * i, c->dy = gy - 4 * j;
  const int16_t *a = g + j * r->gnx + i;
  c->v00 = a[0], c->v10 = a[1], c->v01 = a[r->gnx], c->v11 = a[r->gnx + 1];
}
static int cell_value(const Cell *c) {
  int l = c->v00 * (4 - c->dy) + c->v01 * c->dy, rr = c->v10 * (4 - c->dy) + c->v11 * c->dy;
  return (l * (4 - c->dx) + rr * c->dx) >> 4;
}
static uint32_t isqrt(uint32_t v) {
  uint32_t r = 0, b = 1u << 30;
  while (b > v) b >>= 2;
  while (b) {
    if (v >= r + b) v -= r + b, r = (r >> 1) + b;
    else r >>= 1;
    b >>= 2;
  }
  return r;
}
/* how fast the value changes at the pixel, per pixel (in the value's units) */
static int cell_grad(const Cell *c) {
  int gx = ((c->v10 - c->v00) * (4 - c->dy) + (c->v11 - c->v01) * c->dy) >> 4;
  int gy = ((c->v01 - c->v00) * (4 - c->dx) + (c->v11 - c->v10) * c->dx) >> 4;
  return (int)isqrt((uint32_t)(gx * gx + gy * gy));
}

/* the prototype's banded(), in Q12: flat bands along the value, each edge dithered about 1.6 pixels wide; `wmax`
 * bounds the edge's width over the cell (pixels further than that from an edge are their band's, the width not
 * worked out) */
static int band_q(const Cell *c, int t, int n, int wmax) {
  int fl = cell_value(c) + 2048, k = fl >> 12, f = fl & 4095, idx = k;
  if (f < wmax || 4096 - f < wmax) {
    int w = (cell_grad(c) * 1638) >> 10;
    w = w < 4 ? 4 : w > 2048 ? 2048 : w;
    int up = 2048 - (4096 - f) * 2048 / w, dn = 2048 - f * 2048 / w;
    up = up < 0 ? 0 : up, dn = dn < 0 ? 0 : dn;
    idx = k + (t < up) - (t > 4096 - dn);
  }
  return idx < 0 ? 0 : idx >= n ? n - 1 : idx;
}
/* the widest an edge's dither can be anywhere in a cell: the gradient is largest at a corner */
static int cell_wmax(const Cell *c0) {
  Cell c = *c0;
  int m = 0;
  for (int k = 0; k < 4; k++) {
    c.dx = (k & 1) * 4, c.dy = (k >> 1) * 4;
    int g = cell_grad(&c);
    if (g > m) m = g;
  }
  m = (m * 1638) >> 10;
  return m < 4 ? 4 : m > 2048 ? 2048 : m;
}
/* the warm glow's band value, wv - 1 clipped to 0..4 (Q12), at each corner */
static void warm_corners(Cell *w) {
  int *v[4] = {&w->v00, &w->v10, &w->v01, &w->v11};
  for (int i = 0; i < 4; i++) {
    int x = *v[i] * 5 + 819 - 4096;
    *v[i] = x < 0 ? 0 : x > 16384 ? 16384 : x;
  }
}

/* the woodcut's zodiac band at a pixel: 0 outside, 1 the band, 2 its edge (inked), 3 the ecliptic (red) */
static int zodiac_at(R *r, int x, int y) {
  Cell c;
  cell_at(r, r->ga, x, y, &c);
  int beta = cell_value(&c), g = cell_grad(&c);
  if (beta < 1536 && beta > -1536) return (g > 0 && (beta < 0 ? -beta : beta) * 100 < 57 * g) ? 3 : 1;
  static const int8_t N4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  for (int n = 0; n < 4; n++) {
    int X = x + N4[n][0], Y = y + N4[n][1];
    if (!inside(r, X, Y)) continue;
    cell_at(r, r->ga, X, Y, &c);
    int b2 = cell_value(&c);
    if (b2 < 1536 && b2 > -1536) return 2;
  }
  return 0;
}

/* the window's ground at a pixel in it (the prototype's `ground` there) */
static uint8_t sky_pixel(R *r, int x, int y, int wa, int wb, bool warm) {
  const Plate *P = r->P;
  int t = r->bn[(y & 63) * 64 + (x & 63)] * 16 + 8;      /* the blue-noise threshold, Q12 */
  Cell c;
  switch (P->window) {
  case WIN_SKY: {
    cell_at(r, r->ga, x, y, &c);
    if (r->closed_sky) {
      int i = band_q(&c, t, 4, wa);
      return i ? GREY[i] : P->night;
    }
    uint8_t col = r->ramp[band_q(&c, t, r->nramp, wa)];
    if (warm) {
      Cell w;
      cell_at(r, r->gb, x, y, &w);
      int wv = cell_value(&w) * 5 + 819;
      if (wv >= 4096) {
        int sm = (wv - 4096) * 2;                   /* smooth(0, 0.5, wv - 1) */
        sm = sm > 4096 ? 4096 : sm;
        sm = ((sm * sm >> 12) * (12288 - 2 * sm)) >> 12;
        if (sm > t) {
          warm_corners(&w);
          col = WARM[band_q(&w, t, 5, wb)];
        }
      }
    }
    return col;
  }
  case WIN_ORLOJ:
    return r->s_eff > -0.833f ? C8(1, 2, 3) : r->s_eff > -18 ? C8(2, 1, 0) : C8(0, 0, 0);
  case WIN_RED:
    cell_at(r, r->ga, x, y, &c);
    return REDS[band_q(&c, t, 3, wa)];
  default:
    if (r->woodcut) {
      int z = zodiac_at(r, x, y);
      if (z == 1) return C8(3, 3, 1);
      if (z == 2) return P->ink;
      if (z == 3) return P->accent;
    }
    return P->night;
  }
}

/* the card where nothing is drawn: the jacket, foxed on the old rag paper */
static uint8_t card_at(R *r, int x, int y) {
  const Plate *P = r->P;
  if (P->fox) {
    int fy = (r->H - 1 - y) & 63, fx = (r->W - 1 - x) & 63;
    if ((r->bn[fy * 64 + fx] * 16 + 8) < P->fox) return P->fox_c;
  }
  return P->jacket;
}

static uint8_t ground_at(R *r, int x, int y) { return inside(r, x, y) ? sky_pixel(r, x, y, 4096, 4096, true) : card_at(r, x, y); }

/* the grid over the window: its nodes' values, and with the Milky Way the nodes' places in the sky */
static bool make_grid(R *r, bool coords, void *(*alloc)(size_t)) {
  Plan *p = r->p;
  int minx = r->W, maxx = -1;
  for (int y = p->win_top; y <= p->win_bottom && y >= 0; y++) {
    if (p->wx0[y] > p->wx1[y]) continue;
    if (p->wx0[y] < minx) minx = p->wx0[y];
    if (p->wx1[y] > maxx) maxx = p->wx1[y];
  }
  if (maxx < 0) return false;
  r->gx0 = minx, r->gy0 = p->win_top;
  r->gnx = (maxx - minx) / 4 + 2, r->gny = (p->win_bottom - p->win_top) / 4 + 2;
  size_t n = (size_t)r->gnx * (size_t)r->gny;
  r->ga = alloc((coords ? 4 : 2) * n * sizeof(int16_t));
  if (!r->ga) return false;
  r->gb = r->ga + n;
  r->gra = coords ? r->ga + 2 * n : NULL, r->gdec = coords ? r->ga + 3 * n : NULL;
  for (int j = 0; j < r->gny; j++)
    for (int i = 0; i < r->gnx; i++) {
      size_t k = (size_t)j * r->gnx + i;
      node_values(r, r->gx0 + 4 * i + 0.5f, r->gy0 + 4 * j + 0.5f, r->ga + k, r->gb + k,
                  coords ? r->gra + k : NULL, coords ? r->gdec + k : NULL);
    }
  return true;
}

/* the window's ground, a grid cell at a time (each cell's edges' widths and warmth worked out once) */
static void window_ground(R *r) {
  Plan *p = r->p;
  bool banded = r->P->window == WIN_SKY || r->P->window == WIN_RED;
  for (int j = 0; j < r->gny - 1; j++)
    for (int i = 0; i < r->gnx - 1; i++) {
      int x0 = r->gx0 + 4 * i, y0 = r->gy0 + 4 * j, wa = 4096, wb = 4096;
      bool warm = false;
      if (banded) {
        Cell c;
        cell_at(r, r->ga, x0, y0, &c);
        wa = cell_wmax(&c);
        if (r->P->window == WIN_SKY && !r->closed_sky) {
          cell_at(r, r->gb, x0, y0, &c);
          warm = c.v00 >= 656 || c.v10 >= 656 || c.v01 >= 656 || c.v11 >= 656;
          if (warm) warm_corners(&c), wb = cell_wmax(&c);
        }
      }
      for (int y = y0; y < y0 + 4 && y <= p->win_bottom; y++) {
        int a = p->wx0[y] > x0 ? p->wx0[y] : x0, b = p->wx1[y] < x0 + 3 ? p->wx1[y] : x0 + 3;
        for (int x = a; x <= b; x++) put(r, x, y, sky_pixel(r, x, y, wa, wb, warm));
      }
    }
}

/* ---- the Milky Way --------------------------------------------------------------------------------------------- */
/* a cell of the Milky Way's grid (its level 0..5): each row of declination keeps only its stretches that have any */
static int milky_cell(const uint8_t *g, int i, int j) {
  const uint8_t *e = g + 6 * j, *data = g + 6 * MILKY_H + (e[0] | e[1] << 8);
  int d = i - e[2];
  if (d < 0) d += MILKY_W;
  if (d >= e[3]) {
    data += (e[3] + 1) >> 1;
    d = i - e[4];
    if (d < 0) d += MILKY_W;
    if (d >= e[5]) return 0;
  }
  return (data[d >> 1] >> ((d & 1) * 4)) & 15;
}
/* the Milky Way's level at (ra Q6, dec Q8), between its cells' middles: 0 .. 5 x 16384 */
static int milky_level(const uint8_t *g, int ra, int dec) {
  int u = (ra >> 1) - 32, v = ((dec + 23040) >> 1) - 128;
  int i0 = u >> 6, fu = u & 63, j0 = v >> 8, fv = v & 255;
  int i1 = i0 + 1, j1 = j0 + 1;
  if (i0 < 0) i0 += MILKY_W;
  if (i1 >= MILKY_W) i1 -= MILKY_W;
  if (j0 < 0) j0 = 0, fv = 0;
  if (j1 >= MILKY_H) j1 = MILKY_H - 1;
  if (j0 >= MILKY_H) j0 = MILKY_H - 1;
  int c00 = milky_cell(g, i0, j0), c10 = milky_cell(g, i1, j0), c01 = milky_cell(g, i0, j1), c11 = milky_cell(g, i1, j1);
  if (!(c00 | c10 | c01 | c11)) return 0;
  return (c00 * (64 - fu) + c10 * fu) * (256 - fv) + (c01 * (64 - fu) + c11 * fu) * fv;
}

/* the sky's place at a pixel's middle: right ascension (Q6, 0..360) and declination (Q8) */
static void pixel_radec(R *r, int x, int y, int *ra, int *dec) {
  float dx = x + 0.5f - r->cx, dy = y + 0.5f - r->cy;
  float rho = f_sqrt(dx * dx + dy * dy), h = f_atan2d(dx, dy), d = 90.0f - rho * r->ik;
  float a = pyf_mod(r->south ? r->lst + h : r->lst - h, 360);
  *ra = (int)(a * 64), *dec = (int)((r->south ? -d : d) * 256);
}

static void milky_way(R *r) {
  const Plate *P = r->P;
  Plan *p = r->p;
  const uint8_t *g = sec(p->data, SEC_MILKY);
  /* dens^1.2 > t, as level > t^(1/1.2), in the level's units: each threshold's root worked out once */
  float scale = (r->paper ? 0.30f : 0.42f) / MILKY_LEVELS / 16384;
  for (int i = 0; i < 256; i++) r->thresh12[i] = (int32_t)(f_pow((i + 0.5f) * (1.0f / 256), 1.0f / 1.2f) / scale);
  /* a cell of the grid at a time: its corners' places in the sky, and none of it if no part of the Milky Way is near */
  for (int j = 0; j < r->gny - 1; j++)
    for (int i = 0; i < r->gnx - 1; i++) {
      int x0 = r->gx0 + 4 * i, y0 = r->gy0 + 4 * j;
      Cell a, d;
      cell_at(r, r->gra, x0, y0, &a);
      cell_at(r, r->gdec, x0, y0, &d);
      int lo = a.v00, hi = a.v00, dlo = d.v00, dhi = d.v00;
      int *v[3] = {&a.v10, &a.v01, &a.v11}, *w[3] = {&d.v10, &d.v01, &d.v11};
      for (int k = 0; k < 3; k++) {              /* the corners' right ascensions taken round with the first */
        if (*v[k] - a.v00 > 11520) *v[k] -= 23040;
        else if (a.v00 - *v[k] > 11520) *v[k] += 23040;
        lo = *v[k] < lo ? *v[k] : lo, hi = *v[k] > hi ? *v[k] : hi;
        dlo = *w[k] < dlo ? *w[k] : dlo, dhi = *w[k] > dhi ? *w[k] : dhi;
      }
      bool exact = hi - lo > 5760;               /* by the pole, where they turn too fast to take between */
      if (!exact) {
        int i0 = ((lo >> 1) - 32) >> 6, i1 = (((hi >> 1) - 32) >> 6) + 1;
        int j0 = (((dlo + 23040) >> 1) - 128) >> 8, j1 = ((((dhi + 23040) >> 1) - 128) >> 8) + 1;
        bool any = false;
        for (int jj = j0 < 0 ? 0 : j0; jj <= (j1 >= MILKY_H ? MILKY_H - 1 : j1) && !any; jj++)
          for (int ii = i0; ii <= i1 && !any; ii++) any = milky_cell(g, (ii % MILKY_W + MILKY_W) % MILKY_W, jj) != 0;
        if (!any) continue;
      }
      for (int y = y0; y < y0 + 4 && y <= p->win_bottom; y++) {
        int xa = p->wx0[y] > x0 ? p->wx0[y] : x0, xb = p->wx1[y] < x0 + 3 ? p->wx1[y] : x0 + 3;
        for (int x = xa; x <= xb; x++) {
          int ra, dec;
          if (exact) pixel_radec(r, x, y, &ra, &dec);
          else {
            a.dx = d.dx = x - x0, a.dy = d.dy = y - y0;
            ra = cell_value(&a), dec = cell_value(&d);
            if (ra < 0) ra += 23040;
            else if (ra >= 23040) ra -= 23040;
          }
          int m = milky_level(g, ra, dec);
          if (!m) continue;
          if (r->woodcut) {
            if (m > 14745 && get(r, x, y) != C8(3, 3, 1)) put(r, x, y, P->milky);
          } else if (m > r->thresh12[r->bn[(y & 63) * 64 + (x & 63)]])
            put(r, x, y, P->milky);
        }
      }
    }
}

/* ---- lines ----------------------------------------------------------------------------------------------------- */
/* the pixels within `d` of the segment, in the window */
static void thick_segment(R *r, float x0, float y0, float x1, float y1, float d, uint8_t c) {
  int ax = pyf_floor((x0 < x1 ? x0 : x1) - d - 1), bx = pyf_floor((x0 > x1 ? x0 : x1) + d + 1);
  int ay = pyf_floor((y0 < y1 ? y0 : y1) - d - 1), by = pyf_floor((y0 > y1 ? y0 : y1) + d + 1);
  float vx = x1 - x0, vy = y1 - y0, L2 = vx * vx + vy * vy;
  for (int y = ay; y <= by; y++)
    for (int x = ax; x <= bx; x++) {
      if (!inside(r, x, y)) continue;
      float px = x + 0.5f - x0, py = y + 0.5f - y0;
      float t = L2 > 0 ? (px * vx + py * vy) / L2 : 0;
      t = t < 0 ? 0 : t > 1 ? 1 : t;
      float ex = px - t * vx, ey = py - t * vy;
      if (ex * ex + ey * ey < d * d) put(r, x, y, c);
    }
}

/* the prototype's line_pixels: the pixels along a line, each once */
typedef void (*PixelFn)(R *r, int x, int y, void *ctx);
static void line_pixels(R *r, float x0, float y0, float x1, float y1, PixelFn fn, void *ctx) {
  float ax = x1 - x0 < 0 ? x0 - x1 : x1 - x0, ay = y1 - y0 < 0 ? y0 - y1 : y1 - y0;
  int n = (int)((ax > ay ? ax : ay) * 2) + 1;
  int lx = 0x7fffffff, ly = 0;
  for (int k = 0; k <= n; k++) {
    float t = (float)k / n;
    int px = pyf_floor(x0 + (x1 - x0) * t), py = pyf_floor(y0 + (y1 - y0) * t);
    if (px == lx && py == ly) continue;
    lx = px, ly = py;
    fn(r, px, py, ctx);
  }
}

/* ---- boxes the names keep clear of ----------------------------------------------------------------------------- */
static void add_box(R *r, int x0, int y0, int x1, int y1) {
  if (r->nbox >= MAX_BOXES) return;
  int16_t *b = r->box[r->nbox++];
  b[0] = (int16_t)x0, b[1] = (int16_t)y0, b[2] = (int16_t)x1, b[3] = (int16_t)y1;
}
/* anything of the land (grown a pixel) in the box */
static bool blocked(R *r, const int16_t b[4]) {
  for (int x = b[0] - 1; x <= b[2]; x++) {
    if (x < 0 || x >= r->W) continue;
    int top = r->btop[x];
    if (top != NONE16 && top - 1 < b[3]) return true;
  }
  return false;
}
static bool overlaps(R *r, const int16_t b[4], int skip) {
  for (int i = 0; i < r->nbox; i++) {
    if (i == skip) continue;
    const int16_t *q = r->box[i];
    if (b[0] < q[2] && q[0] < b[2] && b[1] < q[3] && q[1] < b[3]) return true;
  }
  return false;
}
static bool free_box(R *r, int x0, int y0, int x1, int y1) {
  int16_t b[4] = {(int16_t)x0, (int16_t)y0, (int16_t)x1, (int16_t)y1};
  return !overlaps(r, b, -1) && !blocked(r, b);
}

/* set a name beside (x, y): right of it or else left, clear of the window's edge, other names and what is drawn; a
 * name of something drawn (own) is not kept off its own drawing and may go above or below it */
static bool place(R *r, const Text *t, float x, float y, uint8_t colour, bool centred, int c0, int c1, bool own) {
  int mine = -1;
  if (own)
    for (int i = r->nbox - 1; i >= 0; i--) {
      const int16_t *q = r->box[i];
      if (q[0] <= x && x < q[2] && q[1] <= y && y < q[3]) { mine = i; break; }
    }
  int8_t an[8];
  float sx[8], sy[8];
  int n = 0, h = FONT_ROWS;
  if (centred) an[n] = 0, sx[n] = x, sy[n++] = y;
  else {
    an[n] = 1, sx[n] = x + 5 + c1, sy[n++] = y;
    an[n] = 2, sx[n] = x - 4 + c0, sy[n++] = y;
  }
  if (own) {
    int lift = c0 + 3 < 0 ? c0 + 3 : 0;
    an[n] = 1, sx[n] = x + 5 + c1, sy[n++] = y - h + 2;
    an[n] = 2, sx[n] = x - 4 + c0, sy[n++] = y - h + 2;
    an[n] = 1, sx[n] = x + 5 + c1, sy[n++] = y + h - 2;
    an[n] = 2, sx[n] = x - 4 + c0, sy[n++] = y + h - 2;
    an[n] = 0, sx[n] = x, sy[n++] = y - h - 3 + lift;
    an[n] = 0, sx[n] = x, sy[n++] = y + h + 3 - lift;
  }
  for (int s = 0; s < n; s++) {
    int16_t b[4];
    box_of(t, sx[s], sy[s], an[s], b);
    if (!inside(r, b[0], b[1]) || !inside(r, b[2] - 1, b[1]) || !inside(r, b[0], b[3] - 1) || !inside(r, b[2] - 1, b[3] - 1))
      continue;
    if (overlaps(r, b, mine) || blocked(r, b)) continue;
    add_box(r, b[0], b[1], b[2], b[3]);
    stamp(r, t, sx[s], sy[s], colour, true, true, an[s]);
    return true;
  }
  return false;
}

/* ---- the colours of the pieces, by plate ----------------------------------------------------------------------- */
static void piece_colours(R *r) {
  const Plate *P = r->P;
  static const uint8_t RED[3][8] = {
    {0, C8(1, 0, 0), C8(3, 0, 0), C8(3, 0, 0), C8(2, 0, 0), C8(3, 1, 1)},
    {0, C8(1, 0, 0), C8(3, 0, 0), C8(3, 0, 0), C8(1, 0, 0), C8(3, 0, 0), 0, C8(2, 0, 0)},
    {0, C8(1, 0, 0), 0, 0, 0, C8(3, 0, 0), 0, C8(2, 0, 0)}};
  static const uint8_t LIGHT[3][8] = {
    {0, C8(1, 0, 0), C8(2, 0, 0), C8(3, 2, 0), C8(2, 1, 0), C8(3, 3, 1)},
    {0, 0, C8(2, 0, 0), C8(2, 1, 0), C8(1, 0, 0), C8(1, 1, 1), 0, C8(1, 1, 1)},
    {0, 0, 0, 0, 0, C8(3, 3, 3), 0, C8(2, 2, 2)}};
  static const uint8_t DARK[3][8] = {
    {0, C8(0, 0, 0), C8(2, 0, 0), C8(3, 2, 0), C8(2, 1, 0), C8(3, 3, 2)},
    {0, C8(2, 2, 2), C8(3, 1, 0), C8(3, 2, 0), C8(2, 1, 0), C8(3, 3, 2), 0, C8(2, 2, 2)},
    {0, C8(1, 1, 1), 0, 0, 0, C8(3, 3, 2), 0, C8(2, 2, 1)}};
  const uint8_t (*t)[8] = r->red ? RED : r->light_paper ? LIGHT : DARK;
  memcpy(r->sun_c, t[0], 8), memcpy(r->planet_c, t[1], 8), memcpy(r->moon_c, t[2], 8);
  if (!r->red && r->light_paper) r->planet_c[1] = P->ink, r->moon_c[1] = P->ink;
}

/* a colour a step from the card's own, for the engraver's hatching on it */
static uint8_t tint_of(const Plate *P) {
  if (P->jacket == C8(2, 2, 1)) return C8(1, 1, 0);
  if (P->jacket == C8(3, 3, 3)) return C8(2, 2, 2);
  if (level_sum(P->jacket) * 85 > 400) return C8(2, 2, 1);
  if (P->window == WIN_RED) return C8(1, 0, 0);
  return LV(P->jacket, 0) > 0 ? C8(0, 0, 2) : C8(1, 1, 1);
}

/* ---- the weather, as the sky shows it (proto/weather.py sky_of) ------------------------------------------------ */
static void weather_sky(R *r) {
  const Weather *w = r->f->weather;
  if (!w) return;
  r->wx = true;
  int code = w->code;
  bool drizzle = code >= 51 && code <= 57;
  bool rain = (code >= 61 && code <= 67) || (code >= 80 && code <= 82) || code == 95;
  bool snow = (code >= 71 && code <= 77) || code == 85 || code == 86;
  bool hail = code == 96 || code == 99;
  r->falls = drizzle || rain || snow || hail;
  r->rain_or_hail = rain || hail;
  r->snow_falls = snow;
  r->fog = code == 45 || code == 48 || w->vis_dam < 100;
  float low = w->low / 100.0f, mid = w->mid / 100.0f, high = w->high / 100.0f;
  if (mid * 0.6f > low) low = mid * 0.6f;
  float sheet = r->falls ? 1.0f : f_smooth(0.55f, 0.9f, low);
  float clear = r->fog ? 0.0f : 1.0f;
  r->haze = 1.6f * high + (r->fog ? 2.5f : w->vis_dam < 500 ? 1.2f : 0.0f);
  r->cumulus = low * (1 - sheet) * clear, r->stratus = low * sheet * clear;
  r->thunder = code >= 95;
  r->snow_lying = w->snow_mm > 5 || snow;
  r->frost = w->temp10 <= 0;
  r->smoke = w->temp10 < 120;
  r->wind = w->wind, r->wind_from = w->wind_from;
}

/* ---- the face -------------------------------------------------------------------------------------------------- */
static const char *const DAYS[7] = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"};
static const char *const MONTHS[12] = {"January", "February", "March", "April", "May", "June", "July", "August",
                                       "September", "October", "November", "December"};
static const char *const PLANET_NAMES[PLANETS] = {"Venus", "Jupiter", "Mars", "Saturn", "Mercury"};
static const uint8_t PLANET_DRAWINGS[PLANETS] = {D_PLANET_VENUS, D_PLANET_JUPITER, D_PLANET_MARS, D_PLANET_SATURN,
                                                 D_PLANET_MERCURY};

static int season_of(float sun_lon, float lat) {
  float lam = pyf_mod(sun_lon + (lat < 0 ? 180.0f : 0.0f), 360.0f);
  if (lam < 15) return SEASON_BARE;
  if (lam < 45) return SEASON_BLOSSOM;
  if (lam < 120) return SEASON_LEAF;
  if (lam < 165) return SEASON_HARVEST;
  if (lam < 195) return SEASON_TURNING;
  if (lam < 240) return SEASON_AUTUMN;
  return SEASON_BARE;
}

static float interp(float x, const int8_t (*t)[2], int n) {
  if (x <= t[0][0]) return t[0][1];
  if (x >= t[n - 1][0]) return t[n - 1][1];
  for (int i = 1; i < n; i++)
    if (x <= t[i][0]) return t[i - 1][1] + (t[i][1] - t[i - 1][1]) * (x - t[i - 1][0]) / (float)(t[i][0] - t[i - 1][0]);
  return t[n - 1][1];
}

static inline bool span_has(const int16_t *s, int y, int x) { return x >= s[2 * y] && x <= s[2 * y + 1]; }

static void figure_lines(R *r) {
  const uint8_t *st = sec(r->p->data, SEC_STARS);
  const uint16_t *ln = (const uint16_t *)(const void *)sec(r->p->data, SEC_LINES);
  for (int i = 0; i < LINE_COUNT; i++) {
    float x[2], y[2];
    for (int e = 0; e < 2; e++) {
      const uint8_t *s = st + STAR_SIZE * ln[2 * i + e];
      project(r, star_ra(s), star_dec(s), &x[e], &y[e]);
    }
    float L = f_sqrt((x[1] - x[0]) * (x[1] - x[0]) + (y[1] - y[0]) * (y[1] - y[0]));
    if (L < 4.5f) continue;
    float g = 2.6f / L;
    float ax = x[0] + (x[1] - x[0]) * g, ay = y[0] + (y[1] - y[0]) * g;
    float bx = x[1] - (x[1] - x[0]) * g, by = y[1] - (y[1] - y[0]) * g;
    /* the prototype's antialiased line, its coverage over 0.55: within 0.3375 px of a sample point (in 1/256 px) */
    float adx = f_abs(bx - ax), ady = f_abs(by - ay);
    int n = (int)((adx > ady ? adx : ady) * 3) + 1;
    int axq = (int)(ax * 256), ayq = (int)(ay * 256), dxq = (int)(bx * 256) - axq, dyq = (int)(by * 256) - ayq;
    for (int k = 0; k <= n; k++) {
      int pxq = axq + dxq * k / n, pyq = ayq + dyq * k / n, xi = pxq >> 8, yi = pyq >> 8;
      for (int dy = 0; dy <= 1; dy++)
        for (int dx = 0; dx <= 1; dx++) {
          int X = xi + dx, Y = yi + dy, ex = pxq - (X * 256 + 128), ey = pyq - (Y * 256 + 128);
          if (ex * ex + ey * ey < 7465 && inside(r, X, Y)) put(r, X, Y, r->P->line);
        }
    }
  }
}

/* the woodcut's star: the drawing coloured, an inked line round it */
static void woodcut_star(R *r, int d, int xi, int yi, uint8_t c) {
  static const int8_t N4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  const DrawIndex *di = drawing(r, d);
  int y0 = yi - (di->h - 1) / 2, x0 = xi - (di->w - 1) / 2;
  for (int j = -1; j <= di->h; j++)
    for (int i = -1; i <= di->w; i++) {
      if (i >= 0 && j >= 0 && i < di->w && j < di->h && role_at(r, di, i, j)) continue;
      bool near = false;
      for (int n = 0; n < 4 && !near; n++) {
        int a = i + N4[n][0], b = j + N4[n][1];
        near = a >= 0 && b >= 0 && a < di->w && b < di->h && role_at(r, di, a, b);
      }
      if (near && inside(r, x0 + i, y0 + j)) put(r, x0 + i, y0 + j, r->P->ink);
    }
  for (int j = 0; j < di->h; j++)
    for (int i = 0; i < di->w; i++)
      if (role_at(r, di, i, j) && inside(r, x0 + i, y0 + j)) put(r, x0 + i, y0 + j, c);
}

static const uint8_t STAR_COLOURS[5] = {C8(2, 2, 3), C8(3, 3, 3), C8(3, 3, 2), C8(3, 2, 1), C8(3, 2, 0)};

static void stars(R *r, float faint, float mx, float my, float moon_reach) {
  const Plate *P = r->P;
  const uint8_t *st = sec(r->p->data, SEC_STARS);
  for (int i = 0; i < STAR_COUNT; i++) {
    const uint8_t *s = st + STAR_SIZE * i;
    int mg = star_mag(s), cls = star_class(s);
    if ((float)mg * 0.01f > faint && mg >= 210) continue;
    float x, y;
    project(r, star_ra(s), star_dec(s), &x, &y);
    int xi = pyf_floor(x), yi = pyf_floor(y);
    if (mg < 210 && r->nbright < 96) r->bright[r->nbright][0] = (int16_t)xi, r->bright[r->nbright][1] = (int16_t)yi, r->nbright++;
    if ((float)mg * 0.01f > faint) continue;
    if (r->lit_moon && mg > 220 && (x - mx) * (x - mx) + (y - my) * (y - my) < (6 + moon_reach) * (6 + moon_reach)) continue;
    uint8_t c = (r->paper || r->red) ? P->star
                : STAR_COLOURS[cls];
    if (r->rete) {                                /* the rete's flame pointers, for the bright stars only */
      if (mg >= 200) continue;
      float a = pyf_mod((float)f_atan2d((float)(yi - r->cy), (float)(xi - r->cx)), 360.0f);
      int k = (int)(pyf_mod(a + 22.5f, 360.0f) / 45) & 7;
      int d = D_FLAME0 + k, tj = FLAME_TIP[k][0], ti = FLAME_TIP[k][1];
      uint8_t col[8] = {0, 0, 0, P->star};
      paint_at(r, d, xi - ti, yi - tj, col, true, 0);
      const DrawIndex *di = drawing(r, d);
      add_box(r, xi - ti - 1, yi - tj - 1, xi - ti + di->w + 1, yi - tj + di->h + 1);
      continue;
    }
    if (r->woodcut) {                             /* cut in outline and coloured by hand; the faint ones dots */
      if (mg < 210) {
        woodcut_star(r, mg < 50 ? D_STAR0 : mg < 140 ? D_STAR1 : D_STAR2, xi, yi, c);
        if (mg < 140) add_box(r, xi - 3, yi - 3, xi + 4, yi + 4);
      } else if (inside(r, xi, yi))
        put(r, xi, yi, P->ink);
      continue;
    }
    uint8_t col[8] = {0};
    col[5] = c;
    if (mg < 50) {
      paint(r, D_STAR0, xi, yi, col, true);
      add_box(r, xi - 3, yi - 3, xi + 4, yi + 4);
    } else if (mg < 140) {
      paint(r, D_STAR1, xi, yi, col, true);
      add_box(r, xi - 2, yi - 2, xi + 3, yi + 3);
    } else if (mg < 210) paint(r, D_STAR2, xi, yi, col, true);
    else if (mg < 340) paint(r, D_STAR3, xi, yi, col, true);
    else {
      col[5] = r->light_paper ? C8(1, 1, 1) : mix(c, P->night, 0.40f);
      paint(r, D_STAR3, xi, yi, col, true);
    }
  }
}

/* the window's lowest row in each column near the south point, from the bottom up (the window is convex) */
static void window_edge(R *r) {
  Plan *p = r->p;
  for (int i = 0; i <= 2 * VILLAGE_DX; i++) r->edge[i] = -1;
  for (int y = p->win_bottom; y >= p->win_top && y >= 0; y--) {
    if (p->wx0[y] > p->wx1[y]) continue;
    for (int dx = -VILLAGE_DX; dx <= VILLAGE_DX; dx++) {
      int x = r->col + dx;
      if (r->edge[dx + VILLAGE_DX] < 0 && x >= p->wx0[y] && x <= p->wx1[y] && x >= 0 && x < r->W)
        r->edge[dx + VILLAGE_DX] = (int16_t)y;
    }
  }
}

static void land(R *r, int x, int y) {
  if (x >= 0 && x < r->W && (r->btop[x] == NONE16 || y < r->btop[x])) r->btop[x] = (int16_t)y;
}

/* the distant hills behind the village, low and far, one quiet tone taking the hour's light; by night the ridge */
static void hills(R *r) {
  const Plate *P = r->P;
  if (r->wx && (r->fog || r->falls)) return;
  bool closed = r->wx && r->stratus >= 0.6f;
  bool moon_up = altitude(r, r->sky.moon_ra, r->sky.moon_dec) > 0;
  uint8_t tone = 0, ridge = 0;
  float s = r->s_eff;
  if (r->red) tone = C8(1, 0, 0);
  else if (r->paper) ridge = P->line;
  else if (closed && s >= -6) tone = C8(2, 2, 2);
  else if (s >= 6) tone = C8(2, 2, 3);
  else if (s >= 1) tone = C8(3, 2, 2);
  else if (s >= -2) tone = C8(3, 2, 1);
  else if (s >= -5) tone = C8(3, 1, 1);
  else if (s >= -9) tone = C8(2, 1, 2);
  else if (s >= -12) tone = C8(1, 1, 2);
  else ridge = (r->mphase > 0.4f && moon_up) ? C8(2, 2, 2) : C8(1, 1, 2);
  for (int dx = -VILLAGE_DX; dx <= VILLAGE_DX; dx++) {
    int e = r->edge[dx + VILLAGE_DX];
    if (e < 0) continue;
    int hgt = pyf_round(interp(dx, DISTANT, DISTANT_COUNT)), x = r->col + dx;
    for (int y = e - hgt + 1; y <= e; y++) {
      if (!inside(r, x, y)) continue;
      if (tone) put(r, x, y, tone);
      else put(r, x, y, y == e - hgt + 1 ? ridge : ground_at(r, x, y));
      land(r, x, y);
    }
  }
}

static void vput(R *r, int dx, int y, uint8_t c) {
  if (dx >= -VILLAGE_DX && dx <= VILLAGE_DX && y < r->vtop[dx + VILLAGE_DX]) r->vtop[dx + VILLAGE_DX] = (int16_t)y;
  int x = r->col + dx;
  if (inside(r, x, y)) put(r, x, y, c), land(r, x, y);
}

/* the village on the window's lower edge: a church at the south point, a house, trees in the season's dress */
static void village(R *r, int season) {
  const Plate *P = r->P;
  int snow = 0, vane = M_VANE_END;
  if (r->wx) {
    float e = f_sind(r->wind_from);
    vane = (r->wind < 2 || f_abs(e) < 0.38f) ? M_VANE_END : e > 0 ? M_VANE_LEFT : M_VANE_RIGHT;
    snow = r->snow_lying;
  }
  int hour = r->local.hour;
  bool lit = r->sun_alt < -4 && ((hour >= 17 && hour <= 22) || (hour >= 5 && hour <= 7));
  bool night_land = r->sun_alt < -6 || r->red;
  bool foggy = r->wx && r->fog && r->live;
  uint8_t silhouette = r->paper ? P->line : night_land ? C8(0, 0, 0) : C8(0, 0, 1);
  if (foggy && r->sun_alt > 4) silhouette = C8(1, 1, 1);
  uint8_t leaf = (r->paper || night_land || foggy) ? silhouette : season == SEASON_BLOSSOM ? C8(3, 2, 3) : C8(3, 1, 0);
  uint8_t snow_c = (r->paper || !night_land) ? (r->light_paper ? P->night : C8(3, 3, 3)) : C8(2, 2, 2);
  const uint8_t col[8] = {0, silhouette, leaf, C8(3, 3, 1), 0, snow_c};
  int16_t *top = r->vground;
  for (int i = 0; i <= 2 * VILLAGE_DX; i++) r->vtop[i] = NONE16;
  for (int dx = -VILLAGE_DX; dx <= VILLAGE_DX; dx++) {
    int e = r->edge[dx + VILLAGE_DX];
    if (e < 0) continue;
    top[dx + VILLAGE_DX] = (int16_t)(e - pyf_round(interp(dx, VILLAGE_HILLS, VILLAGE_HILL_COUNT)));
    for (int y = top[dx + VILLAGE_DX] + 1; y <= e; y++) vput(r, dx, y, col[1]);
  }
  int mast_x = 0, mast_y = 0;
  bool mast = false;
  for (int v = 0; v < VILLAGE_PIECES; v++) {
    const VillagePiece *vp = &VILLAGE[v];
    int d = vp->piece[season];
    const DrawIndex *di = drawing(r, d);
    int x0 = vp->at - di->w / 2;
    bool fits = true;
    for (int i = 0; i < di->w; i++) {
      int c = x0 + i;
      if (c < -VILLAGE_DX || c > VILLAGE_DX || r->edge[c + VILLAGE_DX] < 0) fits = false;
    }
    if (!fits) continue;
    int base = top[vp->at + VILLAGE_DX];
    if (!vp->tree)
      for (int i = 0; i < di->w; i++)
        if (top[x0 + i + VILLAGE_DX] > base) base = top[x0 + i + VILLAGE_DX];
    int y0 = base - di->h + 1;
    for (int j = 0; j < di->h; j++)
      for (int i = 0; i < di->w; i++) {
        int role = role_at(r, di, i, j);
        if (!role) continue;
        if (role == 3 && !lit) role = 1;
        vput(r, x0 + i, y0 + j, col[role]);
      }
    if (!vp->tree)
      for (int i = 0; i < di->w; i++)
        for (int y = base + 1; y <= r->edge[x0 + i + VILLAGE_DX]; y++) vput(r, x0 + i, y, col[1]);
    if (vp->kind == 1) mast = true, mast_x = x0 + 5, mast_y = y0;
  }
  int vx[16], vy[16], nv = 0;
  if (mast) {                                     /* the vane on the mast, turned into the wind */
    const MaskIndex *mi = mask(r, vane);
    for (int j = 0; j < mi->h; j++)
      for (int i = 0; i < mi->w; i++)
        if (mask_at(r, mi, i, j)) {
          vput(r, mast_x - 2 + i, mast_y - 3 + j, col[1]);
          if (nv < 16) vx[nv] = mast_x - 2 + i, vy[nv] = mast_y - 3 + j, nv++;
        }
  }
  if (snow)                                      /* snow on every top: the first ink down each column */
    for (int dx = -VILLAGE_DX; dx <= VILLAGE_DX; dx++) {
      int y = r->vtop[dx + VILLAGE_DX];
      if (y == NONE16) continue;
      bool on_vane = false;
      for (int i = 0; i < nv; i++) on_vane |= vx[i] == dx && vy[i] == y;
      if (!on_vane && inside(r, r->col + dx, y)) put(r, r->col + dx, y, snow_c);
    }
}

static void names(R *r, float mx, float my) {
  const Plate *P = r->P;
  Sky *k = &r->sky;
  if (altitude(r, k->moon_ra, k->moon_dec) > 0) {
    pixel_text(&r->t1, r, "Moon", false, 0);
    place(r, &r->t1, pyf_floor(mx), pyf_floor(my), P->planet, false, -3, 3, true);
  }
  for (int pn = 0; pn < PLANETS; pn++) {
    if ((!r->paper && r->s_eff > -3) || altitude(r, k->pl_ra[pn], k->pl_dec[pn]) <= 2) continue;
    float x, y;
    project(r, k->pl_ra[pn], k->pl_dec[pn], &x, &y);
    int hw = drawing(r, PLANET_DRAWINGS[pn])->w / 2;
    pixel_text(&r->t1, r, PLANET_NAMES[pn], false, 0);
    place(r, &r->t1, pyf_floor(x), pyf_floor(y), P->planet, false, -hw + 1, hw - 2, true);
  }
  if (!(r->dark || r->paper)) return;
  const uint8_t *sn = sec(r->p->data, SEC_STAR_NAMES);
  int shown = 0;
  for (int i = 0; i < STAR_NAME_COUNT && shown < 3; i++) {
    const uint8_t *s = sn + 20 * i;
    if (altitude(r, star_ra(s), star_dec(s)) < 8) continue;
    float x, y;
    project(r, star_ra(s), star_dec(s), &x, &y);
    pixel_text(&r->t1, r, (const char *)s + 4, true, 0);
    if (place(r, &r->t1, pyf_floor(x) + 1, pyf_floor(y), P->label, false, 0, 0, true)) shown++;
  }
  const uint8_t *cn = sec(r->p->data, SEC_CONSTELLATIONS);
  shown = 0;
  for (int i = 0; i < CONSTELLATION_COUNT && shown < 3; i++) {
    const uint8_t *s = cn + 20 * i;
    if (altitude(r, star_ra(s), star_dec(s)) < 12) continue;
    float x, y;
    project(r, star_ra(s), star_dec(s), &x, &y);
    pixel_text(&r->t1, r, (const char *)s + 4, false, 1);
    if (place(r, &r->t1, x, y, P->cons, true, 0, 0, false)) shown++;
  }
}

/* a 7 x 7 sign (or 5 x 5 glyph) with a pixel of the ground cleared round it */
static void sign_with_halo(R *r, int xi, int yi, int half, int m, int d, uint8_t c) {
  bool on[9][9];
  memset(on, 0, sizeof on);
  int n = 2 * half + 1;
  for (int j = 0; j < n; j++)
    for (int i = 0; i < n; i++)
      on[j + 1][i + 1] = m >= 0 ? mask_at(r, mask(r, m), i, j) : role_at(r, drawing(r, d), i, j) != 0;
  for (int j = 0; j <= n + 1; j++)
    for (int i = 0; i <= n + 1; i++) {
      if (on[j][i]) continue;
      bool near = (i + 1 <= n && on[j][i + 1]) || (i >= 1 && on[j][i - 1]) || (j + 1 <= n && on[j + 1][i]) || (j >= 1 && on[j - 1][i]);
      int X = xi - half - 1 + i, Y = yi - half - 1 + j;
      if (near && inside(r, X, Y)) put(r, X, Y, ground_at(r, X, Y));
    }
  for (int j = 1; j <= n; j++)
    for (int i = 1; i <= n; i++)
      if (on[j][i] && on_screen(r, xi - half - 1 + i, yi - half - 1 + j)) put(r, xi - half - 1 + i, yi - half - 1 + j, c);
}

static bool all_inside(R *r, int x0, int y0, int x1, int y1) {
  for (int y = y0; y <= y1; y++)
    if (!inside(r, x0, y) || !inside(r, x1, y)) return false;
  return true;
}

/* anything drawn near (xi, yi): the Sun, the Moon, a planet or a bright star within 7 pixels each way */
static bool near_body(R *r, int xi, int yi) {
  Sky *k = &r->sky;
  float x, y;
  for (int i = -2; i < PLANETS; i++) {
    if (i == -2) project(r, k->sun_ra, k->sun_dec, &x, &y);
    else if (i == -1) project(r, k->moon_ra, k->moon_dec, &x, &y);
    else project(r, k->pl_ra[i], k->pl_dec[i], &x, &y);
    if (f_abs(x - xi) < 7 && f_abs(y - yi) < 7) return true;
  }
  for (int i = 0; i < r->nbright; i++) {          /* (to the pixel: within 7 of a star's place is within 7 of its pixel) */
    int dx = r->bright[i][0] - xi, dy = r->bright[i][1] - yi;
    if (dx > -8 && dx < 8 && dy > -8 && dy < 8) {
      const uint8_t *st = sec(r->p->data, SEC_STARS);
      for (int j = STAR_COUNT - 1; j >= 0; j--) {   /* near the edge of the square: the star's exact place decides */
        const uint8_t *s = st + STAR_SIZE * j;
        if (star_mag(s) >= 210) break;
        project(r, star_ra(s), star_dec(s), &x, &y);
        if (f_abs(x - xi) < 7 && f_abs(y - yi) < 7) return true;
      }
      return false;
    }
  }
  return false;
}

/* the zenith's cross, the signs of the zodiac and (on Apian's plate) the dragon: drawn after the names, where no
 * name or body is */
static void ornaments(R *r) {
  const Plate *P = r->P;
  Sky *k = &r->sky;
  int zx = r->col, zy = pyf_floor(r->cy + (90 - r->alat) * r->k);
  if (inside(r, zx, zy) && free_box(r, zx - 3, zy - 3, zx + 4, zy + 4)) {
    for (int y = zy - 3; y <= zy + 3; y++)
      for (int x = zx - 3; x <= zx + 3; x++)
        if (on_screen(r, x, y)) put(r, x, y, ground_at(r, x, y));
    uint8_t col[8] = {0, P->cons};
    paint(r, D_ZENITH, zx, zy, col, true);
  }
  if (r->dark || r->paper)
    for (int s = 0; s < 12; s++) {
      float ra, dec, x, y;
      ecl_point(r, 30.0f * s + 15, &ra, &dec);
      project(r, ra, dec, &x, &y);
      int xi = pyf_floor(x), yi = pyf_floor(y);
      if (!(xi >= 4 && xi < r->W - 4 && yi >= 4 && yi < r->H - 4) || !all_inside(r, xi - 4, yi - 4, xi + 4, yi + 4)) continue;
      if (near_body(r, xi, yi) || !free_box(r, xi - 4, yi - 4, xi + 5, yi + 5)) continue;
      sign_with_halo(r, xi, yi, 3, M_ZODIAC0 + s, 0, P->cons);
      add_box(r, xi - 4, yi - 4, xi + 5, yi + 5);
    }
  if (P->dragon) {                                /* in an eclipse season, at the Moon's nodes */
    float om = plan_moon_node(k->jd);
    float sl = (float)k->sun_lon;
    float g1 = f_abs(pyf_mod(sl - om + 180, 360) - 180), g2 = f_abs(pyf_mod(sl - om, 360) - 180);
    if ((g1 < g2 ? g1 : g2) < 18) {
      static const int8_t OFF[9] = {0, 3, -3, 6, -6, 9, -9, 12, -12};
      for (int e = 0; e < 2; e++)
        for (int o = 0; o < 9; o++) {
          float ra, dec, x, y;
          ecl_point(r, om + 180.0f * e + OFF[o], &ra, &dec);
          project(r, ra, dec, &x, &y);
          int xi = pyf_floor(x), yi = pyf_floor(y);
          if (xi >= 3 && xi < r->W - 3 && yi >= 3 && yi < r->H - 3 && all_inside(r, xi - 3, yi - 3, xi + 3, yi + 3) &&
              free_box(r, xi - 3, yi - 3, xi + 4, yi + 4)) {
            sign_with_halo(r, xi, yi, 2, -1, e ? D_DRAGON_TAIL : D_DRAGON_HEAD, P->ink);
            add_box(r, xi - 3, yi - 3, xi + 4, yi + 4);
            break;
          }
        }
    }
  }
}

/* the window's two rules, and the ornaments on them: the fleur-de-lis (or an astrolabe's throne), lozenges at the
 * east and west, a star at the south. Returns the top of the fleur. */
static bool near_window(R *r, int x, int y) {
  for (int dy = -2; dy <= 2; dy++) {
    int ady = dy < 0 ? -dy : dy;
    for (int dx = ady - 2; dx <= 2 - ady; dx++)
      if (inside(r, x + dx, y + dy)) return true;
  }
  return false;
}
static int rims(R *r) {
  const Plate *P = r->P;
  Plan *p = r->p;
  static const int8_t N4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  for (int y = p->win_top - 3; y <= p->win_bottom + 3; y++) {
    if (y < 0 || y >= r->H) continue;
    int lo = r->W, hi = -1;
    for (int dy = -3; dy <= 3; dy++) {
      int yy = y + dy;
      if (yy < 0 || yy >= r->H || p->wx0[yy] > p->wx1[yy]) continue;
      if (p->wx0[yy] < lo) lo = p->wx0[yy];
      if (p->wx1[yy] > hi) hi = p->wx1[yy];
    }
    for (int x = lo - 3; x <= hi + 3; x++) {
      if (x < 0 || x >= r->W || inside(r, x, y)) continue;
      bool rim1 = false;
      for (int n = 0; n < 4; n++) rim1 |= inside(r, x + N4[n][0], y + N4[n][1]);
      if (rim1) { put(r, x, y, P->rule); continue; }
      if (near_window(r, x, y)) continue;
      bool rim2 = false;
      for (int n = 0; n < 4 && !rim2; n++) rim2 = near_window(r, x + N4[n][0], y + N4[n][1]);
      if (rim2) put(r, x, y, P->rule);
    }
  }
  int col = r->col, first = -1, last = -1;
  for (int y = 0; y < r->H; y++)
    if (inside(r, col, y)) { if (first < 0) first = y; last = y; }
  if (first < 0) first = pyf_floor(r->cy - r->alat * r->k);
  int fl = P->throne ? D_THRONE : D_FLEUR;
  const DrawIndex *di = drawing(r, fl);
  int fx0 = pyf_round(r->cx - di->w / 2.0f), fy0 = first - 4 - (di->h - 1);
  uint8_t c2[8] = {0, P->ink, P->accent};
  paint_at(r, fl, fx0, fy0, c2, false, 0);
  float ew = 90 * r->k;
  for (int s = -1; s <= 1; s += 2) paint(r, D_LOZENGE, r->cx - 0.5f + s * (ew + 1.5f), r->cy - 0.5f, c2, false);
  uint8_t c3[8] = {0, 0, P->accent};
  if (last >= 0) paint(r, D_SOUTH_STAR, col, last + 3, c3, false);
  return fy0;
}

/* the Sun hand's points at an angle: field 0 the hand's middle (midway across the band), 1 the index's foot on the
 * inner rule, 2 the thread's outer end, 3 the beads' track */
static void path_at(R *r, float a, int field, float *x, float *y) {
  Plan *p = r->p;
  if (field == 0) {
    float ex, ey, ox, oy;
    edge_point(p, a, 0, &ex, &ey);
    track_hit(p, TRACK_OUT1, a, &ox, &oy);
    *x = (ex + ox) / 2, *y = (ey + oy) / 2;
  } else if (field == 1) edge_point(p, a, 0.6f, x, y);
  else track_hit(p, field == 2 ? TRACK_THREAD : TRACK_BEAD, a, x, y);
}

static const uint8_t NUM[5][6] = {
  {M_ROMAN_III, M_ROMAN_VI, M_ROMAN_IX, M_ROMAN_III, M_ROMAN_VI, M_ROMAN_IX},
  {M_FIG_3, M_FIG_6, M_FIG_9, M_FIG_3, M_FIG_6, M_FIG_9},
  {M_FIG_3, M_FIG_6, M_FIG_9, M_FIG_15, M_FIG_18, M_FIG_21},
  {M_GOTHIC_3, M_GOTHIC_6, M_GOTHIC_9, M_GOTHIC_3, M_GOTHIC_6, M_GOTHIC_9},
  {M_SMALL_IIJ, M_SMALL_VJ, M_SMALL_IX, M_SMALL_IIJ, M_SMALL_VJ, M_SMALL_IX}};

/* the ring's rules: inside the outer rule and not inside its inner one; outline of the inner region */
static bool rule_at(R *r, int x, int y) {
  if (!on_screen(r, x, y)) return false;
  const int16_t *outer = sec16(r->p->geom, GEO_OUTER), *outer1 = sec16(r->p->geom, GEO_OUTER1);
  const int16_t *inner = sec16(r->p->geom, GEO_INNER);
  if (span_has(outer, y, x) && !span_has(outer1, y, x)) return true;
  if (span_has(inner, y, x) || inside(r, x, y)) return false;
  return span_has(inner, y, x - 1) || span_has(inner, y, x + 1) || (y > 0 && span_has(inner, y - 1, x)) ||
         (y + 1 < r->H && span_has(inner, y + 1, x));
}

/* the numerals and studs (grown a pixel) the inscriptions stop short of */
static bool in_marks(R *r, int x, int y) {
  Plan *p = r->p;
  for (int i = 0; i < 6; i++) {
    const MaskIndex *mi = mask(r, NUM[p->num_style][i]);
    int i0 = x - p->numerals[i][0], j0 = y - p->numerals[i][1];
    if (i0 >= 0 && j0 >= 0 && i0 < mi->w && j0 < mi->h && mask_at(r, mi, i0, j0)) return true;
    const DrawIndex *di = drawing(r, D_STUD);
    int i1 = x - p->studs[i][0] + 2, j1 = y - p->studs[i][1] + 2;
    if (i1 >= 0 && j1 >= 0 && i1 < di->w && j1 < di->h && role_at(r, di, i1, j1)) return true;
  }
  return false;
}
static bool keep_off(R *r, int x, int y) {
  return in_marks(r, x, y) || in_marks(r, x - 1, y) || in_marks(r, x + 1, y) || in_marks(r, x, y - 1) || in_marks(r, x, y + 1);
}

/* each numeral set on its hour's ray where it stands clearest of the rules, studs, beads and ticks (nearest the
 * band's middle among equals); then the inscriptions' room, out along the band until a numeral or stud is near */
#define NR 48
static bool numeral_layout(R *r, int style, void *(*alloc)(size_t), void (*release)(void *)) {
  Plan *p = r->p;
  if (p->num_style == style) return true;
  uint8_t *room = alloc(NR * NR);
  if (!room) return false;
  const uint8_t *beads = sec(p->geom, GEO_BEADS);
  int nb = beads[0] | beads[1] << 8;
  const float step = (0.8f - 0.2f) / 48;
  for (int i = 0; i < 6; i++) {
    const MaskIndex *mi = mask(r, NUM[style][i]);
    int w = mi->w, h = mi->h;
    float a = (NUMERAL_HOURS[i] - 12) * 15.0f, x0, y0, x1, y1;
    edge_point(p, a, 0, &x0, &y0);
    track_hit(p, TRACK_OUT1, a, &x1, &y1);
    int ox = 1 << 20, oy = 1 << 20;
    for (int k = 0; k <= 48; k++) {
      float f = k == 48 ? 0.8f : k * step + 0.2f;
      int lx = pyf_round(x0 + (x1 - x0) * f - w / 2.0f), ty = pyf_round(y0 + (y1 - y0) * f - h / 2.0f);
      if (lx < ox) ox = lx;
      if (ty < oy) oy = ty;
    }
    ox -= 6, oy -= 6;
    for (int gy = 0; gy < NR; gy++)
      for (int gx = 0; gx < NR; gx++) room[gy * NR + gx] = rule_at(r, ox + gx, oy + gy) ? 0 : 255;
#define HOLD(X, Y) do { int gx_ = (X) - ox, gy_ = (Y) - oy;     if ((unsigned)gx_ < NR && (unsigned)gy_ < NR && on_screen(r, (X), (Y))) room[gy_ * NR + gx_] = 0; } while (0)
    const DrawIndex *sd = drawing(r, D_STUD);
    for (int s = 0; s < 6; s++)
      for (int j = 0; j < sd->h; j++)
        for (int k = 0; k < sd->w; k++)
          if (role_at(r, sd, k, j)) HOLD(p->studs[s][0] - 2 + k, p->studs[s][1] - 2 + j);
    for (int b = 0; b < nb; b++) {
      int16_t bx, by;
      memcpy(&bx, beads + 2 + 4 * b, 2), memcpy(&by, beads + 4 + 4 * b, 2);
      HOLD(bx, by);
    }
    for (int t = 0; t < p->nticks; t++) {
      HOLD(p->ticks[t][0], p->ticks[t][1]);
      HOLD(r->W - 1 - p->ticks[t][0], p->ticks[t][1]);
    }
#undef HOLD
    /* how far each pixel stands clear of all that, in pixels (8-connected), up to six */
    for (int gy = 0; gy < NR; gy++)
      for (int gx = 0; gx < NR; gx++) {
        int v = room[gy * NR + gx];
        if (gy > 0) {
          if (gx > 0 && room[(gy - 1) * NR + gx - 1] + 1 < v) v = room[(gy - 1) * NR + gx - 1] + 1;
          if (room[(gy - 1) * NR + gx] + 1 < v) v = room[(gy - 1) * NR + gx] + 1;
          if (gx + 1 < NR && room[(gy - 1) * NR + gx + 1] + 1 < v) v = room[(gy - 1) * NR + gx + 1] + 1;
        }
        if (gx > 0 && room[gy * NR + gx - 1] + 1 < v) v = room[gy * NR + gx - 1] + 1;
        room[gy * NR + gx] = (uint8_t)v;
      }
    for (int gy = NR - 1; gy >= 0; gy--)
      for (int gx = NR - 1; gx >= 0; gx--) {
        int v = room[gy * NR + gx];
        if (gy + 1 < NR) {
          if (gx + 1 < NR && room[(gy + 1) * NR + gx + 1] + 1 < v) v = room[(gy + 1) * NR + gx + 1] + 1;
          if (room[(gy + 1) * NR + gx] + 1 < v) v = room[(gy + 1) * NR + gx] + 1;
          if (gx > 0 && room[(gy + 1) * NR + gx - 1] + 1 < v) v = room[(gy + 1) * NR + gx - 1] + 1;
        }
        if (gx + 1 < NR && room[gy * NR + gx + 1] + 1 < v) v = room[gy * NR + gx + 1] + 1;
        room[gy * NR + gx] = (uint8_t)(v > 6 ? 6 : v);
      }
    int best_c = -1, best_x = 0, best_y = 0;
    float best_d = 0;
    for (int k = 0; k <= 48; k++) {
      float f = k == 48 ? 0.8f : k * step + 0.2f;
      int lx = pyf_round(x0 + (x1 - x0) * f - w / 2.0f), ty = pyf_round(y0 + (y1 - y0) * f - h / 2.0f);
      if (lx < 0 || ty < 0 || lx + w > r->W || ty + h > r->H) continue;
      int c = 6;
      for (int j = 0; j < h; j++)
        for (int k2 = 0; k2 < w; k2++)
          if (mask_at(r, mi, k2, j)) {
            int gx = lx + k2 - ox, gy = ty + j - oy;
            int v = (unsigned)gx < NR && (unsigned)gy < NR ? room[gy * NR + gx] : 6;
            if (v < c) c = v;
          }
      float d = f_abs(f - 0.5f);
      if (c > best_c || (c == best_c && d < best_d)) best_c = c, best_d = d, best_x = lx, best_y = ty;
    }
    p->numerals[i][0] = (int16_t)best_x, p->numerals[i][1] = (int16_t)best_y;
  }
  release(room);
  p->num_style = (int8_t)style;
  const uint8_t *wk = sec(p->geom, GEO_WALKS);
  for (int slot = 0; slot < 4; slot++) {
    int16_t xa, n;
    memcpy(&xa, wk, 2), memcpy(&n, wk + 2, 2);
    wk += 4;
    float xb = xa / 16.0f;
    for (int e = 0; e < n; e++) {
      int16_t x16, xi, yi;
      memcpy(&x16, wk + 6 * e, 2), memcpy(&xi, wk + 6 * e + 2, 2), memcpy(&yi, wk + 6 * e + 4, 2);
      bool stop = yi < 0;
      for (int dy = -3; dy <= 3 && !stop; dy++) stop = keep_off(r, xi, yi + dy);
      if (stop) { xb = x16 / 16.0f; break; }
    }
    wk += 6 * n;
    float lo = xa / 16.0f < xb ? xa / 16.0f : xb, hi = xa / 16.0f < xb ? xb : xa / 16.0f;
    p->ins_lo[slot] = (int16_t)pyf_round(lo * 16), p->ins_hi[slot] = (int16_t)pyf_round(hi * 16);
  }
  return true;
}

/* a small capital for the inscriptions: its mask, or -1 (a space is three pixels) */
static int tiny_mask(char ch) {
  if (ch >= 'a' && ch <= 'z') ch = (char)(ch - 32);
  for (int i = 0; TINY_CHARS[i]; i++)
    if (TINY_CHARS[i] == ch) return M_TINY0 + i;
  return -1;
}
static int tiny_width(R *r, const char *s) {
  int w = 0, k = 0;
  for (; *s; s++) {
    int m = tiny_mask(*s);
    if (*s != ' ' && m < 0) continue;
    w += (*s == ' ' ? 3 : mask(r, m)->w) + (k ? 1 : 0);
    k++;
  }
  return w;
}

/* a name, then shorter forms of it (form 1, 2, ...): its leading words cut to their initials one by one (NEW YORK,
 * N. YORK), then its initials alone (N.Y.); "" past the last */
static void shortened(const char *name, int form, char *out, int n) {
  const char *w[8];
  int len[8], nw = 0;
  for (const char *s = name; *s && nw < 8;) {
    while (*s == ' ') s++;
    if (!*s) break;
    w[nw] = s;
    while (*s && *s != ' ') s++;
    len[nw] = (int)(s - w[nw]), nw++;
  }
  int k = 0;
#define ADD(c) do { if (k < n - 1) out[k++] = (c); } while (0)
  if (form == 0) {
    for (const char *s = name; *s; s++) ADD(*s);
  } else if (form < nw) {
    for (int i = 0; i < nw; i++) {
      if (i) ADD(' ');
      if (i < form) { ADD(w[i][0]); ADD('.'); }
      else for (int c = 0; c < len[i]; c++) ADD(w[i][c]);
    }
  } else if (form == nw && nw > 1) {
    for (int i = 0; i < nw; i++) { ADD(w[i][0]); ADD('.'); }
  }
#undef ADD
  out[k] = 0;
}

/* the place on the ring: city and country either side of MIDNIGHT, latitude and longitude either side of NOON, in
 * small capitals following the band's curve, each centred in the room there, a city too long shortened */
static void inscriptions(R *r, int style) {
  char dms[2][16];
  for (int k = 0; k < 2; k++) {
    float v = k ? r->f->lon : r->f->lat, d = f_abs(v);
    int deg = (int)d, mins = pyf_round((d - deg) * 60);
    if (mins == 60) deg++, mins = 0;
    number(dms[k], deg, 1);
    int n = (int)strlen(dms[k]);
    dms[k][n++] = '\x01';
    dms[k][n++] = (char)('0' + mins / 10), dms[k][n++] = (char)('0' + mins % 10);
    dms[k][n++] = '\'', dms[k][n++] = k ? (v >= 0 ? 'E' : 'W') : (v >= 0 ? 'N' : 'S'), dms[k][n] = 0;
  }
  const char *texts[4] = {r->f->city, r->f->country, r->f->coords ? dms[0] : NULL, r->f->coords ? dms[1] : NULL};
  (void)style;
  const int16_t *curves = sec16(r->p->geom, GEO_CURVES);
  for (int slot = 0; slot < 4; slot++) {
    const char *text = texts[slot];
    if (!text || !*text) continue;
    float lo = r->p->ins_lo[slot] / 16.0f, hi = r->p->ins_hi[slot] / 16.0f;
    char form[40];
    int width = 0;
    bool ok = false;
    for (int f = 0; f < 8; f++) {
      shortened(text, f, form, sizeof form);
      if (!form[0]) break;
      width = tiny_width(r, form);
      if (width <= hi - lo) { ok = true; break; }
    }
    if (!ok) continue;
    const int16_t *cy = curves + (slot < 2 ? 0 : r->W);
    float gx = (lo + hi) / 2 - width / 2.0f;
    for (const char *s = form; *s; s++) {
      int m = tiny_mask(*s), gw;
      if (*s == ' ') gw = 3;
      else if (m < 0) continue;
      else gw = mask(r, m)->w;
      float xc = gx + gw / 2.0f;
      int xi = pyf_floor(xc);
      float f = xc - xi;
      if (xi < 0) xi = 0, f = 0;
      if (xi >= r->W - 1) xi = r->W - 2, f = 1;
      float yc = (cy[xi] * (1 - f) + cy[xi + 1] * f) / 16.0f;
      if (m >= 0 && *s != ' ') mask_put(r, m, pyf_round(gx), pyf_round(yc - 2.5f), r->P->ring_ink, false, false);
      gx += gw + 1;
    }
  }
}

static void put_thread(R *r, int x, int y, void *ctx) {
  (void)ctx;
  if (on_screen(r, x, y) && !inside(r, x, y)) put(r, x, y, r->P->ink);
}

typedef struct { int x0, y0, n; uint32_t bits[32]; int16_t pts[48][2]; } HandMask;
static void hand_index(R *r, int x, int y, void *ctx) {
  (void)r;
  HandMask *h = ctx;
  int i = x - h->x0, j = y - h->y0;
  bool on = (unsigned)i < 32 && (unsigned)j < 32 && ((h->bits[j] >> i) & 1);
  if (!on && h->n < 48) h->pts[h->n][0] = (int16_t)x, h->pts[h->n][1] = (int16_t)y, h->n++;
}

static void ring(R *r, int season) {
  const Plate *P = r->P;
  Plan *p = r->p;
  const int16_t *outer1 = sec16(p->geom, GEO_OUTER1), *outer = sec16(p->geom, GEO_OUTER), *inner = sec16(p->geom, GEO_INNER);
  /* the night on the ring: hatched where the Sun will be down, closer through the twilights; each pixel's hour angle
   * (its cosine) against those of the Sun's altitude's thresholds */
  float A = r->sl * (float)f_sind(r->sdec), B = r->cl * (float)f_cosd(r->sdec);
  static const float THRESH[4] = {-0.833f, -6, -12, -18};
  /* the thresholds' cosines, as their squares (Q16) and signs, against each pixel's (1/16 px from the pole) */
  int64_t c2[4];
  bool cpos[4];
  for (int i = 0; i < 4; i++) {
    float sv = f_sind(THRESH[i]) - A, c = B > 1e-9f ? sv / B : (sv > 0 ? 9 : -9);
    c = c > 9 ? 9 : c < -9 ? -9 : c;
    cpos[i] = c >= 0, c2[i] = (int64_t)(c * c * 65536);
  }
  int cxq = pyf_floor(r->cx * 16 + 0.5f), cyq = pyf_floor(r->cy * 16 + 0.5f);
  static const uint8_t STEP[5] = {0, 9, 7, 5, 4};
  uint8_t ink = P->ring_ink, fc = P->fill_c;
  uint8_t hatch_c = P->fill == FILL_COLOUR ? (uint8_t)(0xC0 | (LV(fc, 4) ? LV(fc, 4) - 1 : 0) << 4 | (LV(fc, 2) ? LV(fc, 2) - 1 : 0) << 2 |
                                                       (LV(fc, 0) ? LV(fc, 0) - 1 : 0))
                    : P->fill == FILL_WASH ? C8(2, 2, 1) : r->tint;
  for (int y = 0; y < r->H; y++)
    for (int x = outer[2 * y]; x <= outer[2 * y + 1]; x++) {
      if (span_has(inner, y, x)) { x = inner[2 * y + 1]; continue; }
      bool rule_in = span_has(inner, y, x - 1) || span_has(inner, y, x + 1) || (y > 0 && span_has(inner, y - 1, x)) ||
                     (y + 1 < r->H && span_has(inner, y + 1, x));
      if (!span_has(outer1, y, x)) { put(r, x, y, ink); continue; }
      if (rule_in) { if (!inside(r, x, y)) put(r, x, y, ink); continue; }
      if (inside(r, x, y)) continue;
      int dyq = y * 16 + 8 - cyq, dxq = x * 16 + 8 - cxq;
      int64_t rho2 = (int64_t)(dxq * dxq + dyq * dyq), dy2 = (int64_t)(dyq * dyq) << 16;
      int band = 0;
      while (band < 4 && !(cpos[band] ? dyq > 0 && dy2 > c2[band] * rho2 : dyq >= 0 || dy2 < c2[band] * rho2)) band++;
      int step = STEP[band];
      bool hatch = step && (x + y) % step == 0;
      if (P->fill == FILL_COLOUR || P->fill == FILL_WASH) put(r, x, y, hatch ? hatch_c : fc);
      else if (P->fill == FILL_ZONES) {
        if (band == 0) put(r, x, y, C8(0, 1, 2));
        else if (band < 4) put(r, x, y, C8(2, 1, 0));
      } else if (hatch)
        put(r, x, y, hatch_c);
    }
  /* beads: every third pixel along a track just inside the outer rule; on an astrolabe, at the unequal hours */
  if (P->unequal) {
    float c0 = -f_sind(r->alat) / f_cosd(r->alat) * (f_sind(r->sdec) / f_cosd(r->sdec));
    float h0 = f_acosd(c0 < -1 ? -1 : c0 > 1 ? 1 : c0);
    for (int kk = 0; kk < 24; kk++) {
      float a = (h0 > 0 && h0 < 180) ? (kk < 12 ? -h0 + kk * 2 * h0 / 12 : h0 + (kk - 12) * (360 - 2 * h0) / 12) : kk * 15.0f;
      float bx, by;
      path_at(r, a, 3, &bx, &by);
      for (int oy = 0; oy < 2; oy++)
        for (int ox = 0; ox < 2; ox++) put(r, pyf_floor(bx - 0.5f) + ox, pyf_floor(by - 0.5f) + oy, ink);
    }
  } else {
    const uint8_t *b = sec(p->geom, GEO_BEADS);
    int n = b[0] | b[1] << 8;
    for (int i = 0; i < n; i++) {
      int16_t bx, by;
      memcpy(&bx, b + 2 + 4 * i, 2), memcpy(&by, b + 4 + 4 * i, 2);
      put(r, bx, by, ink);
    }
  }
  for (int i = 0; i < p->nticks; i++)              /* the ticks, mirrored across the meridian: exactly symmetric */
    for (int m = 0; m < 2; m++) {
      int tx = m ? r->W - 1 - p->ticks[i][0] : p->ticks[i][0], ty = p->ticks[i][1];
      if (on_screen(r, tx, ty) && !inside(r, tx, ty) && !span_has(inner, ty, tx)) put(r, tx, ty, ink);
    }
  uint8_t scol[8] = {0, ink, P->accent};
  for (int i = 0; i < 6; i++) paint(r, D_STUD, p->studs[i][0], p->studs[i][1], scol, false);
  /* the hours every three: roman, figures (on the 24-hour clock running on through the day), Gothic, small roman */
  int style = r->clock24 ? 2 : P->ring == RING_ROMAN ? 0 : P->ring == RING_GOTHIC ? 3 : P->ring == RING_MINUSCULE ? 4 : 1;
  for (int i = 0; i < 6; i++) mask_put(r, NUM[style][i], p->numerals[i][0], p->numerals[i][1], ink, false, false);
  /* MIDNIGHT and NOON, a lozenge either side */
  const uint8_t *words = sec(p->geom, GEO_WORDS), *wbits = sec(p->geom, GEO_WORD_BITS);
  for (int wd = 0; wd < 2; wd++) {
    const uint8_t *e = words + 8 * wd;
    int16_t x0, y0;
    uint16_t bit;
    memcpy(&x0, e, 2), memcpy(&y0, e + 2, 2), memcpy(&bit, e + 6, 2);
    int w = e[4], h = e[5];
    for (int j = 0; j < h; j++)
      for (int i = 0; i < w; i++) {
        uint32_t n = bit + (uint32_t)(j * w + i);
        if ((wbits[n >> 3] >> (n & 7)) & 1) put(r, x0 + i, y0 + j, P->accent);
      }
  }
  const int16_t *loz = sec16(p->geom, GEO_WORD_LOZENGES);
  for (int i = 0; i < 4; i++) paint(r, D_LOZENGE, loz[2 * i] / 16.0f - 0.5f, loz[2 * i + 1] / 16.0f - 0.5f, scol, false);
  inscriptions(r, style);
  /* the Time 2's corners: a sprig in each, in the season's dress */
  if (r->rect) {
    const int16_t *cs = sec16(p->geom, GEO_CORNERS);
    static const uint8_t CORNER_OF_SEASON[6] = {D_CORNER_BARE, D_CORNER_BLOSSOM, D_CORNER_LEAF, D_CORNER_LEAF,
                                                D_CORNER_AUTUMN, D_CORNER_AUTUMN};
    int d = P->corner == CORNER_IVY ? D_CORNER_IVY : P->corner == CORNER_FROND ? D_CORNER_FROND : CORNER_OF_SEASON[season];
    uint8_t ccol[8] = {0, P->ink, P->accent, r->sun_c[3]};
    const DrawIndex *di = drawing(r, d);
    for (int i = 0; i < 4; i++)
      if (cs[4 * i + 2])
        paint_at(r, d, pyf_round(cs[4 * i] - (di->w - 1) / 2.0f), pyf_round(cs[4 * i + 1] - (di->h - 1) / 2.0f), ccol, false,
                 (i & 1 ? 1 : 0) | (i & 2 ? 2 : 0));
  }
  /* the Sun's hand: a gilded Sun riding the band at the Sun's hour, an index to the inner rule, over everything */
  float a = r->sha, hx, hy, ix, iy;
  path_at(r, a, 0, &hx, &hy);
  path_at(r, a, 1, &ix, &iy);
  if (P->thread) {                                /* Apian's: a silk thread across the band, a seed pearl */
    float tx, ty;
    path_at(r, a, 2, &tx, &ty);
    line_pixels(r, ix, iy, tx, ty, put_thread, NULL);
    for (int y = pyf_floor(hy) - 4; y <= pyf_floor(hy) + 4; y++)
      for (int x = pyf_floor(hx) - 4; x <= pyf_floor(hx) + 4; x++) {
        float ddx = x + 0.5f - hx, ddy = y + 0.5f - hy;
        if (f_abs(ddx) + f_abs(ddy) <= 2.6f && on_screen(r, x, y) && !inside(r, x, y)) put(r, x, y, P->ink);
      }
    uint8_t pc[8] = {0, 0, 0, 0, 0, C8(3, 3, 3), 0, C8(2, 2, 2)};
    paint(r, D_PEARL, hx - 0.5f, hy - 0.5f, pc, false);
  } else {
    HandMask *hm = (HandMask *)(void *)&r->t4;    /* the spare line of type holds the hand's mask */
    memset(hm, 0, sizeof *hm);
    const DrawIndex *di = drawing(r, D_SUN_HAND);
    int hx0 = pyf_round(hx - di->w / 2.0f), hy0 = pyf_round(hy - di->h / 2.0f);
    hm->x0 = hx0 - 10, hm->y0 = hy0 - 10;
    for (int j = 0; j < di->h; j++)
      for (int i = 0; i < di->w; i++)
        if (role_at(r, di, i, j)) hm->bits[j + 10] |= 1u << (i + 10);
    line_pixels(r, hx, hy, ix, iy, hand_index, hm);
    for (int i = 0; i < hm->n; i++) {
      int bi = hm->pts[i][0] - hm->x0, bj = hm->pts[i][1] - hm->y0;
      if ((unsigned)bi < 32 && (unsigned)bj < 32) hm->bits[bj] |= 1u << bi;
    }
    for (int j = 0; j < 32; j++)                  /* cleared round: the hand and index grown a pixel, to the card */
      for (int i = 0; i < 32; i++) {
        bool near = ((hm->bits[j] >> i) & 1) || (i > 0 && ((hm->bits[j] >> (i - 1)) & 1)) ||
                    (i < 31 && ((hm->bits[j] >> (i + 1)) & 1)) || (j > 0 && ((hm->bits[j - 1] >> i) & 1)) ||
                    (j < 31 && ((hm->bits[j + 1] >> i) & 1));
        int X = hm->x0 + i, Y = hm->y0 + j;
        if (near && on_screen(r, X, Y) && !inside(r, X, Y)) put(r, X, Y, P->jacket);
      }
    for (int i = 0; i < hm->n; i++)
      if (on_screen(r, hm->pts[i][0], hm->pts[i][1])) put(r, hm->pts[i][0], hm->pts[i][1], r->sun_c[4]);
    paint_at(r, D_SUN_HAND, hx0, hy0, r->sun_c, false, 0);
  }
}

/* the large time in the plate's own figures, its top-left at (x0, y0) (only measured unless `draw`): its width */
static int compose(R *r, int style, int screen, int hour, int minute, int *asc_out, int *small_out, bool draw, int x0, int y0) {
  const FigureIndex *fi = (const FigureIndex *)(const void *)sec(r->p->data, SEC_FIGURE_INDEX) + (style * 2 + screen) * 12;
  const uint8_t *bits = sec(r->p->data, SEC_FIGURE_DATA);
  int parts[8], n = 0;                            /* 0..9 figures, 10 h, 11 m, -1 the gap */
  if (hour >= 10) parts[n++] = hour / 10;
  parts[n++] = hour % 10;
  parts[n++] = 10, parts[n++] = -1;
  parts[n++] = minute / 10, parts[n++] = minute % 10, parts[n++] = 11;
  int asc = 0, small = fi[0].base, W = 0;
  for (int i = 0; i < n; i++) {
    int c = parts[i];
    if (c >= 0 && c <= 9 && fi[c].base > asc) asc = fi[c].base;
    W += c < 0 ? 5 : fi[c].w;
  }
  W += 2 * (n - 1);
  if (asc_out) *asc_out = asc;
  if (small_out) *small_out = small;
  if (!draw) return W;
  int x = 0;
  for (int i = 0; i < n; i++) {
    int c = parts[i];
    if (c < 0) { x += 5 + 2; continue; }
    const FigureIndex *g = fi + c;
    int top = c <= 9 ? asc - g->base : asc - small;
    for (int j = 0; j < g->h; j++)
      for (int i2 = 0; i2 < g->w; i2++) {
        uint32_t b = g->bit + (uint32_t)(j * g->w + i2);
        if ((bits[b >> 3] >> (b & 7)) & 1) put(r, x0 + x + i2, y0 + top + j, r->P->ink);
      }
    x += g->w + (c == 10 ? 1 : 2);
  }
  return W;
}

static int hour_of(int h, bool clock24) { return clock24 ? h : (h % 12 ? h % 12 : 12); }

/* the time as an astronomer writes it, the needlework either side, the date, the almanac's line */
static void time_block(R *r, int fy0, int season) {
  const Plate *P = r->P;
  Plan *p = r->p;
  float ring_in = r->rect ? 17.0f : r->cy - (r->p->R - 18.0f);
  float span = (fy0 - 1) - ring_in;
  int screen = r->rect ? 0 : 1;
  int hour = hour_of(r->local.hour, r->clock24);
  int asc, small;
  int Wt = compose(r, P->figures, screen, hour, r->local.minute, &asc, &small, false, 0, 0);
  float cy_ = ring_in + span * 0.345f;
  compose(r, P->figures, screen, hour, r->local.minute, NULL, NULL, true, pyf_round(r->cx - Wt / 2.0f),
          pyf_round(cy_ - (asc - small / 2.0f)));
  /* the needlework either side, changing on the hour: the season's (or the weather's), or one for any time */
  int widest = WIDEST_TIME[P->figures * 2 + screen][r->clock24 ? 1 : 0];
  int yc = pyf_round(cy_);
  int kind = WXP_NONE;
  if (r->wx)
    kind = r->thunder ? WXP_THUNDER : (r->snow_lying || r->frost || r->snow_falls) ? WXP_SNOW : r->falls ? WXP_RAIN
           : r->fog ? WXP_FOG : r->wind >= 30 ? WXP_WIND : WXP_NONE;
  const uint8_t *seasonal = kind ? NW_OF_WEATHER[kind] : NW_OF_SEASON[season];
  int ns = kind ? NW_OF_WEATHER_N[kind] : NW_OF_SEASON_N[season];
  uint8_t general[12];
  int ng = 0;
  for (unsigned i = 0; i < sizeof NW_ANY_TIME; i++) general[ng++] = NW_ANY_TIME[i];
  if (r->s_eff < -6) general[ng++] = NW_MOON;
  int32_t count = r->local.ordinal * 24 + r->local.hour;
  int kk = count / 2;
  bool even = count % 2 == 0;
  uint8_t order[24];
  int no = 0;
  for (int pass = 0; pass < 2; pass++) {
    const uint8_t *lst = (pass == 0) == even ? seasonal : general;
    int nl = (pass == 0) == even ? ns : ng;
    for (int i = 0; i < nl; i++) {
      uint8_t v = lst[(kk + i) % nl];
      bool seen = false;
      for (int j = 0; j < no; j++) seen |= order[j] == v;
      if (!seen) order[no++] = v;
    }
  }
  const int16_t *inner = sec16(p->geom, GEO_INNER);
  for (int i = 0; i < no; i++) {
    int m = M_NEEDLE_LOZENGE + order[i];
    const MaskIndex *mi = mask(r, m);
    int h = mi->h, w = mi->w, lo = -1, hi = 1 << 20;
    bool ok = widest > 0;
    for (int y = yc - h / 2; y <= yc + h / 2 && ok; y++) {
      if (y < 0 || y >= r->H || inner[2 * y] > inner[2 * y + 1]) { ok = false; break; }
      if (inner[2 * y] > lo) lo = inner[2 * y];
      if (inner[2 * y + 1] < hi) hi = inner[2 * y + 1];
    }
    if (!ok || lo > hi) break;
    float lo_ = lo + 2, hi_ = r->cx - widest / 2.0f - 2;
    if (hi_ - lo_ < w + 2) continue;
    int x0 = pyf_round((lo_ + hi_) / 2 - (w - 1) / 2.0f), y0 = pyf_round(cy_ - (h - 1) / 2.0f);
    mask_put(r, m, x0, y0, P->accent, false, false);
    mask_put(r, m, r->W - x0 - w, y0, P->accent, false, true);
    break;
  }
  /* the date, after the sign of the planet that rules the day */
  char date[40];
  const MaskIndex *ds = mask(r, M_DAY0 + r->local.wday);
  for (int pass = 0; pass < 2; pass++) {
    const char *dn = DAYS[r->local.wday], *mn = MONTHS[r->local.month - 1];
    int n = 0, lim = pass ? 3 : 99;
    for (int i = 0; dn[i] && i < lim; i++) date[n++] = dn[i];
    date[n++] = ' ';
    number(date + n, r->local.day, 1);
    n += (int)strlen(date + n);
    date[n++] = ' ';
    for (int i = 0; mn[i] && i < lim; i++) date[n++] = mn[i];
    date[n] = 0;
    pixel_text(&r->t1, r, date, true, 0);
    if (r->t1.w + ds->w + 4 <= (r->W - 2 * ring_in) * 0.80f) break;
  }
  float y_date = ring_in + span * 0.675f;
  float left = r->cx - (ds->w + 4 + r->t1.w) / 2.0f;
  int16_t db[4];
  box_of(&r->t1, left + ds->w + 4, y_date, 1, db);
  t_clear(&r->t2);
  t_mask(&r->t2, r, M_DAY0 + r->local.wday, 0, 0);
  r->t2.w = ds->w;
  stamp(r, &r->t2, left + ds->w / 2.0f, (db[1] + db[3]) / 2.0f - 1, P->accent, false, false, 0);
  stamp(r, &r->t1, left + ds->w + 4, y_date, P->ink, false, false, 1);
  /* the almanac's line: the Sun's next rising or setting; with the weather, the temperature after a lozenge (the
   * line alone when the two will not fit together, the temperature alone when neither does) */
  if (p->ev_kind < 0 || r->utc < p->ev_from || r->utc >= p->ev_at || p->ev_lat != r->f->lat || p->ev_lon != r->f->lon) {
    p->ev_kind = plan_sun_event(r->utc, r->f->lat, r->f->lon, &p->ev_at);
    if (!p->ev_kind) p->ev_at = r->utc + 3600;     /* the Sun neither rises nor sets today: look again in an hour */
    p->ev_from = r->utc, p->ev_lat = r->f->lat, p->ev_lon = r->f->lon;
  }
  int64_t at = p->ev_at;
  int ev = p->ev_kind;
  float room = (r->W - 2 * ring_in) * 0.84f;
  Text *line = &r->t1, *both = &r->t2, *temp = &r->t3, *tmp = &r->t4;
  if (ev) {
    Civil c;
    plan_civil(at + r->offset, &c);
    pixel_text(line, r, ev == 1 ? "SUNRISE" : "SUNSET", false, 0);
    time_text(tmp, r, hour_of(c.hour, r->clock24), c.minute);
    t_append(line, tmp, 3);
  }
  const Text *fits = NULL;
  if (r->f->weather) {
    float cel = r->f->weather->temp10 / 10.0f;
    temp_text(temp, r, pyf_round(r->f->fahrenheit ? cel * 9 / 5 + 32 : cel));
    if (ev) {
      *both = *line;
      t_clear(tmp);
      t_mask(tmp, r, M_LOZENGE_MASK, 0, 2);
      tmp->w = mask(r, M_LOZENGE_MASK)->w;
      t_append(both, tmp, 3);
      t_append(both, temp, 3);
      if (both->w <= room) fits = both;
      else if (line->w <= room) fits = line;
    }
    if (!fits && temp->w <= room) fits = temp;
  } else if (ev && line->w <= room)
    fits = line;
  if (fits) stamp(r, fits, r->cx, ring_in + span * 0.915f, P->accent, false, false, 0);
}

bool plan_render(Plan *p, const Face *f, int64_t utc, int32_t offset, const Target *t, void *(*alloc)(size_t),
                 void (*release)(void *)) {
  R *r = alloc(sizeof(R));
  if (!r) return false;
  memset(r, 0, sizeof *r);
  r->p = p, r->f = f, r->P = &PLATES[f->plate < PLATE_COUNT ? f->plate : 0];
  const Plate *P = r->P;
  r->W = p->w, r->H = p->h, r->rect = p->rect;
  r->utc = utc, r->offset = offset, r->clock24 = f->clock24;
  for (int y = 0; y < r->H; y++) {
    int x0 = 0, x1 = -1;
    p->rows[y] = t->row(t->ctx, y, &x0, &x1);
    p->rx0[y] = (int16_t)x0, p->rx1[y] = (int16_t)x1;
    if (!p->rows[y]) p->rx0[y] = 1, p->rx1[y] = 0;
  }
  plan_window(p, f->lat);
  plan_sky(&r->sky, utc, f->lon);
  plan_civil(utc + offset, &r->local);
  r->bn = sec(p->data, SEC_BLUE_NOISE);
  r->cx = p->cx, r->cy = p->cy, r->k = p->k;
  r->col = (int)p->cx;
  r->south = f->lat < 0;
  r->alat = (float)f_abs(f->lat);
  r->sl = f_sind(r->alat), r->cl = f_cosd(r->alat);
  r->sl0 = f_sind((float)f->lat), r->cl0 = f_cosd((float)f->lat);
  r->lst = (float)r->sky.lst;
  r->paper = P->window == WIN_PAPER;
  r->red = P->window == WIN_RED;
  r->live = P->window == WIN_SKY || P->window == WIN_RED;
  r->light_paper = r->paper && level_sum(P->night) * 85 > 400;
  r->rete = P->rete, r->woodcut = P->woodcut;
  r->sun_alt = (float)plan_altitude(r->sky.sun_ra, r->sky.sun_dec, r->sky.lst, f->lat);
  r->s_eff = r->sun_alt;
  r->sdec = (float)(r->south ? -r->sky.sun_dec : r->sky.sun_dec);
  r->sha = (float)pyf_mod(r->south ? -(r->sky.lst - r->sky.sun_ra) : r->sky.lst - r->sky.sun_ra, 360.0f);
  r->mphase = (float)r->sky.moon_phase;
  r->tint = tint_of(P);
  r->ramp[r->nramp++] = P->night;
  for (int i = 0; i < 6; i++)
    if (level_sum(COOL[i]) > level_sum(P->night)) r->ramp[r->nramp++] = COOL[i];
  piece_colours(r);
  weather_sky(r);
  for (int x = 0; x < MAX_W; x++) r->btop[x] = NONE16;
  r->closed_sky = P->window == WIN_SKY && r->wx && (r->stratus >= 0.6f || r->fog || r->falls);

  /* the card, and the window's ground */
  for (int y = 0; y < r->H; y++)
    for (int x = p->rx0[y]; x <= p->rx1[y]; x++) p->rows[y][x] = card_at(r, x, y);
  r->ik = 1 / r->k;
  sky_constants(r, P->window == WIN_RED ? r->s_eff : r->sun_alt);
  r->ssd = f_sind(r->sdec), r->csd = f_cosd(r->sdec), r->csh = f_cosd(r->sha), r->ssh = f_sind(r->sha);
  bool milky = !r->rete && (r->paper || (r->sun_alt < -15 &&
               !(r->wx && r->live && (r->haze > 1.0f || r->stratus + r->cumulus > 0.45f))));
  if (!make_grid(r, milky, alloc)) { release(r); return false; }
  window_ground(r);
  r->dark = r->paper ? true : r->s_eff < -12;
  r->figs = r->paper || r->s_eff < -10.5f;
  float faint = 4.6f;
  if (!r->paper) {
    float s = r->s_eff;
    faint = s <= -16 ? 4.6f : s <= -10 ? 4.6f + (s + 16) / 6 * (3.4f - 4.6f) : s <= -5 ? 3.4f + (s + 10) / 5 * (2.0f - 3.4f)
          : s <= -1.5f ? 2.0f + (s + 5) / 3.5f * (0.4f - 2.0f) : 0.4f;
    if (s > -1.5f) faint = -9;
  }
  if (r->wx && r->live) faint -= r->haze;
  /* the Moon's light pales the sky round it and hides the faint stars there */
  float mx, my;
  project(r, r->sky.moon_ra, r->sky.moon_dec, &mx, &my);
  bool moon_up = altitude(r, r->sky.moon_ra, r->sky.moon_dec) > 0;
  r->lit_moon = !r->paper && P->window == WIN_SKY && r->s_eff < -10 && r->mphase > 0.3f && moon_up;
  float moon_reach = 7 + 12 * r->mphase;
  if (r->lit_moon)
    for (int y = pyf_floor(my - 6 - moon_reach - 1); y <= pyf_floor(my + 6 + moon_reach + 1); y++)
      for (int x = pyf_floor(mx - 6 - moon_reach - 1); x <= pyf_floor(mx + 6 + moon_reach + 1); x++) {
        if (!inside(r, x, y)) continue;
        float ddx = (float)(x + 0.5f - mx), ddy = (float)(y + 0.5f - my), dd = f_sqrt(ddx * ddx + ddy * ddy);
        if (dd <= 6) continue;
        float g = f_clamp(1 - (dd - 6) / moon_reach, 0, 1);
        if (g > 0 && f_pow(g, 1.6f) * 0.55f * r->mphase > tt(r, x, y)) put(r, x, y, C8(0, 1, 2));
      }
  /* the Milky Way, the first thing haze and cloud take away */
  if (milky) milky_way(r);
  /* an astrolabe's plate: the equator, the tropics and the almucantars engraved, the rete's ecliptic solid */
  if (r->rete) {
    for (int kk = 0; kk < 3; kk++) {
      float d = kk == 0 ? 0.0f : kk == 1 ? 23.44f : -23.44f, rr = (90 - d) * r->k;
      float lo2 = (rr - 0.445f) * (rr - 0.445f), hi2 = (rr + 0.445f) * (rr + 0.445f);
      for (int y = p->win_top; y >= 0 && y <= p->win_bottom; y++)
        for (int x = p->wx0[y]; x <= p->wx1[y]; x++) {
          float ddx = x + 0.5f - r->cx, ddy = y + 0.5f - r->cy, d2 = ddx * ddx + ddy * ddy;
          if (d2 > lo2 && d2 < hi2) put(r, x, y, P->line);
        }
    }
    for (int kk = 0; kk < 2; kk++) {
      float alt = kk ? 60.0f : 30.0f, px = 0, py = 0, la = r->alat;
      for (int az = 0; az <= 360; az += 2) {
        float dec = f_asind(f_sind(la) * f_sind(alt) + f_cosd(la) * f_cosd(alt) * f_cosd((float)az));
        float ha = f_atan2d(-f_sind((float)az) * f_cosd(alt), f_cosd(la) * f_sind(alt) - f_sind(la) * f_cosd(alt) * f_cosd((float)az));
        float rho = (90 - dec) * r->k, x = r->cx + rho * f_sind(ha), y = r->cy + rho * f_cosd(ha);
        if (az) thick_segment(r, px, py, x, y, 0.445f, P->line);
        px = x, py = y;
      }
    }
    float px = 0, py = 0;
    for (int l = 0; l <= 360; l++) {
      float ra, dec, x, y;
      ecl_point(r, l, &ra, &dec);
      project(r, ra, dec, &x, &y);
      if (l) thick_segment(r, px, py, x, y, 0.945f, P->cons);
      px = x, py = y;
    }
  }
  /* the equator and the ecliptic, dotted */
  if (!r->rete)
    for (int lam = 0; lam < 360; lam += 3)
      for (int kind = 0; kind < 2; kind++) {
        float ra, dec, x, y;
        if (kind == 0) {
          if (r->woodcut) continue;
          ecl_point(r, lam, &ra, &dec);
        } else {
          if (lam % 6) continue;
          ra = lam, dec = 0;
        }
        project(r, ra, dec, &x, &y);
        int xi = (int)x, yi = (int)y;
        if (inside(r, xi, yi) && r->dark) put(r, xi, yi, kind == 0 ? P->cons : P->line);
      }
  /* the meridian, dotted from the north point through the pole and the zenith to the south point */
  int zy = pyf_floor(r->cy + (90 - r->alat) * r->k);
  if (r->dark || r->paper)
    for (int y = 0; y < r->H; y += 3)
      if (inside(r, r->col, y) && (y - zy > 3 || zy - y > 3)) put(r, r->col, y, P->line);
  /* the figures, stopping short of their stars; the stars */
  if (r->figs && !r->rete) figure_lines(r);
  stars(r, faint, mx, my, moon_reach);
  /* the planets, each its little picture */
  for (int pn = 0; pn < PLANETS; pn++) {
    if (!r->paper && r->s_eff > -3) continue;
    float x, y;
    project(r, r->sky.pl_ra[pn], r->sky.pl_dec[pn], &x, &y);
    int xi = pyf_floor(x), yi = pyf_floor(y);
    paint(r, PLANET_DRAWINGS[pn], xi, yi, r->planet_c, true);
    const DrawIndex *di = drawing(r, PLANET_DRAWINGS[pn]);
    add_box(r, xi - di->w / 2 - 1, yi - di->h / 2 - 1, xi + di->w / 2 + 2, yi + di->h / 2 + 2);
  }
  /* the Moon in its phase; by day only its lit face */
  {
    uint8_t mc[8];
    memcpy(mc, r->moon_c, 8);
    if (!r->dark && !r->paper && r->mphase >= 0.04f) mc[1] = 0;
    int phase = 0;
    while (phase < MOON_PHASES - 1 && !(r->mphase < MOON_BY_LIGHT[phase])) phase++;
    int mi = pyf_floor(mx), mj = pyf_floor(my);
    paint(r, D_MOON_NEW + 2 * phase + (r->sky.moon_waxing ? 0 : 1), mi, mj, mc, true);
    add_box(r, mi - 6, mj - 6, mi + 7, mj + 7);
  }
  /* the Sun: in a live sky in its own light, a pale disc and a glow stippled thinner outward; on a printed chart
   * the engraver's glory round it; its face after the Sun of May */
  {
    float sx, sy;
    project(r, r->sky.sun_ra, r->sky.sun_dec, &sx, &sy);
    if (r->sun_alt > -0.8f || r->paper) {
      int si = pyf_floor(sx), sj = pyf_floor(sy);
      if (!r->paper) {
        uint8_t light = r->red ? C8(2, 0, 0) : r->sun_alt < 6 ? C8(3, 3, 2) : C8(2, 3, 3);
        for (int y = sj - 18; y <= sj + 18; y++)
          for (int x = si - 18; x <= si + 18; x++) {
            if (!inside(r, x, y)) continue;
            float ddx = (float)(x - si), ddy = (float)(y - sj), dd = f_sqrt(ddx * ddx + ddy * ddy);
            float g = f_clamp(1 - (dd - 4.0f) / 13.0f, 0, 1);
            float glow = g * f_sqrt(g) * 0.85f * (r->closed_sky ? 0.0f : 1.0f);
            if (dd > 4.0f && glow > tt(r, x, y)) put(r, x, y, light);
            if (dd <= 4.4f) put(r, x, y, r->red ? C8(3, 0, 0) : C8(3, 3, 1));
          }
      } else {
        const MaskIndex *gl = mask(r, M_GLORY);
        int x0 = pyf_round(si - (gl->w - 1) / 2.0f), y0 = pyf_round(sj - (gl->h - 1) / 2.0f);
        for (int j = 0; j < gl->h; j++)
          for (int i = 0; i < gl->w; i++)
            if (mask_at(r, gl, i, j) && inside(r, x0 + i, y0 + j)) put(r, x0 + i, y0 + j, P->line);
      }
      paint(r, D_SUN, si, sj, r->sun_c, true);
      add_box(r, si - 12, sj - 12, si + 13, sj + 13);
    }
  }
  /* the southern horizon: the distant hills, the village */
  int season = season_of(r->sky.sun_lon, f->lat);
  window_edge(r);
  hills(r);
  village(r, season);
  /* names in the sky; the ornaments where no name is */
  if (f->names) names(r, mx, my);
  ornaments(r);
  /* the window's edge, the ring, the time */
  int fy0 = rims(r);
  int style = f->clock24 ? 2 : P->ring == RING_ROMAN ? 0 : P->ring == RING_GOTHIC ? 3 : P->ring == RING_MINUSCULE ? 4 : 1;
  if (!numeral_layout(r, style, alloc, release)) { release(r->ga); release(r); return false; }
  ring(r, season);
  time_block(r, fy0, season);
  release(r->ga);
  release(r);
  return true;
}
