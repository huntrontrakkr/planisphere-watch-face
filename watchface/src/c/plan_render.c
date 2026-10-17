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
enum { FALL_NONE, FALL_DRIZZLE, FALL_RAIN, FALL_SNOW, FALL_HAIL };
enum { NEWS_NONE, NEWS_SUN, NEWS_MOON, NEWS_PLANETS, NEWS_SHOWER, NEWS_MOON_BY };

/* ---- the blobs ------------------------------------------------------------------------------------------------ */
static const int16_t *sec16(const uint8_t *blob, int i) { return (const int16_t *)(const void *)sec(blob, i); }

typedef struct { uint16_t off; uint8_t w, h; } DrawIndex;
typedef struct { uint32_t bit; uint8_t w, h; uint16_t pad; } MaskIndex;
typedef struct { uint16_t bit; uint8_t w, adv; } GlyphIndex;

/* ---- a line of type: 14 rows, up to 256 pixels ---------------------------------------------------------------- */
typedef struct { int w; uint32_t bits[FONT_ROWS][8]; } Text;

typedef struct { float day, lift, twf, warm; } SkyK;

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
  uint32_t lst20;                            /* the sidereal time in 2^-20 of a turn, and the projection's integer */
  int32_t kq, cxq, cyq;                      /* scale and centre (plan_math.h, project_u) */
  int32_t cx2, cy2, ikq;                     /* the pole in half pixels, the degrees per pixel Q18 (place_radec) */
  float sun_alt, s_eff, sdec, sha, mphase;   /* the Sun's declination and hour angle in the chart's frame */
  uint8_t sun_c[8], planet_c[8], moon_c[8];  /* colours by role; 0 none */
  uint8_t tint, ramp[6];
  int nramp;
  const uint8_t *bn;
  /* the window's ground: two values on a grid every 4 pixels over the window */
  int gx0, gy0, gnx, gny;
  int16_t *ga, *gb;                          /* each node row only as far as the window's cells need it: */
  int16_t glo[MAX_H / 4 + 2], ghi[MAX_H / 4 + 2];   /* its first and last node, */
  uint16_t goff[MAX_H / 4 + 2];              /* and where it starts in ga and gb */
  float ik, ssd, csd, csh, ssh, sl0, cl0;
  SkyK sk, sk6;                              /* the sky's Sun-dependent parts, now and (under an eclipse) at -6 */
  int16_t bright[96][2];                     /* the stars brighter than 2.1 on the screen, for the zodiac to avoid */
  int nbright;
  /* what names keep clear of */
  int16_t box[MAX_BOXES][4];
  int nbox;
  int16_t btop[MAX_W];                       /* the land's top in each column (hills, village), NONE16 none */
  int col;
  /* the weather, as the sky shows it */
  bool wx, fog, falls, rain_or_hail, thunder, snow_lying, frost, smoke, snow_falls, halo;
  uint8_t fall_kind, heavy;                  /* FALL_*, 1 light .. 3 heavy */
  float stratus, cumulus, cirrus, haze, wind, wind_from;
  int secs;                                  /* the local clock's seconds into the day */
  /* the weather's drawings for the moment: the cumulus heaps and banks, the stratus's ruled lines, the cirrus */
  struct { uint8_t d, flip; int16_t x0, y0; } cloud[24], hair[8];
  int ncloud, nhair;
  int16_t strat[28][3];                      /* y, x0, x1 */
  int nstrat;
  uint8_t cc[3], c_line, c_hair, c_rain[2], c_snow;   /* the clouds' colours for the hour (K, W, S roles; 0 the sky) */
  int16_t drawn[96][3];                      /* the drawn bright stars (x, y, half their size): the clouds keep off */
  int ndrawn;
  int16_t chimney_x, chimney_y;
  bool chimney, night_land;
  /* the sky's events: an eclipse under way here, the umbra's dimming, Jupiter's moons' reach, a shower */
  bool have_sol, have_lun, totality;
  Eclipse sol, lun;
  float umbra;
  int jlo, jhi, nmoons, shower;
  int16_t moonbox[4][2];                     /* Jupiter's moons, where names keep off */
  int16_t marks[24][2];                      /* a feast's marks in the sky (the glint, the magpies), names keep off */
  int nmarks;
  int8_t first;                              /* Christmas Eve's first star, as Plan.feast_first, once it is out */
  int16_t fl_x0, fl_y0, fl_w, fl_h;          /* the fleur-de-lis at the window's top, as rims drew it */
  bool weaver;                               /* Qixi's Weaver and Cowherd, named */
  /* memory the layers take in turn (the watch's is short): the Milky Way's first, then Jupiter's moons' lane in its
   * room (the moons are drawn after the Milky Way, and the lane read only while they are); then the village's; then
   * the lines of type for the names, the ring and the time. (Only what nothing reads once the names begin: the halos'
   * ground_at reads the clouds and the stars' places, so those keep their own.) */
  union {
    uint64_t lane[40];                       /* the lane cleared round Jupiter for its moons (bit x of row y) */
    struct {
      uint16_t thresh_h[256];                /* each blue-noise level's threshold for the Milky Way, halved, and its
                                              * odd bit (the thresholds past the Milky Way's deepest, 81920, all
                                              * alike: none is met): half the room of 32-bit thresholds */
      uint32_t thresh_odd[8];
      int16_t mra[2][MAX_W / 4 + 3], mdec[2][MAX_W / 4 + 3];   /* its nodes' places, two rows at a time */
    };
    struct {
      int16_t edge[2 * VILLAGE_DX + 1];      /* the window's lowest row at each column from the south point, -1 none */
      /* the village's pieces as placed: the ground's top and the buildings' bases by column, and its pixels in
       * each column, a bit a row up from its edge */
      int16_t vtop[2 * VILLAGE_DX + 1], vground[2 * VILLAGE_DX + 1];
      uint32_t vmask[2 * VILLAGE_DX + 1];
    };
    struct { Text t1, t2, t3; };
  };
} R;

/* ---- pixels --------------------------------------------------------------------------------------------------- */
static inline void put(R *r, int x, int y, uint8_t c) {
  Plan *p = r->p;
  if ((unsigned)y < (unsigned)r->H && x >= p->rx0[y] && x <= p->rx1[y]) ROW(p, y)[x] = c;
}
static inline uint8_t get(R *r, int x, int y) {
  Plan *p = r->p;
  if ((unsigned)y < (unsigned)r->H && x >= p->rx0[y] && x <= p->rx1[y]) return ROW(p, y)[x];
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

/* the screen position of a point of the sky: a planisphere seen from below, south at the bottom, east on the left.
 * In integers (proto/iq.py project_u, the same bits): the right ascension in 2^-20 of a turn, the distance from the
 * pole in 65535ths of a half turn (the star table's own unit), the result in 1/256 pixel; the sidereal time (lst20)
 * and the scale (kq: pixels per unit of colatitude, Q16 of Q8) taken once a frame. */
static void project_u(R *r, uint32_t ra20, int colat_u, float *x, float *y) {
  uint32_t h = (r->lst20 - ra20) & (BRAD_TURN - 1);
  if (r->south) h = (0u - h) & (BRAD_TURN - 1);
  int64_t rho = ((int64_t)colat_u * r->kq) >> 16;
  int32_t xq = r->cxq + (int32_t)((rho * isin_q30(h)) >> 30), yq = r->cyq + (int32_t)((rho * icos_q30(h)) >> 30);
  *x = (float)xq * (1.0f / 256), *y = (float)yq * (1.0f / 256);
}
static void project(R *r, float ra, float dec, float *x, float *y) {
  if (r->south) dec = -dec;
  uint32_t ra20 = (uint32_t)pyf_floor(ra * (1048576.0f / 360) + 0.5f);
  project_u(r, ra20, pyf_floor((90.0f - dec) * (65535.0f / 180) + 0.5f), x, y);
}
/* a star of the table, from its own units */
static void project_star(R *r, const uint8_t *s, float *x, float *y) {
  int raw = s[2] | s[3] << 8;
  project_u(r, (uint32_t)(s[0] | s[1] << 8) << 4, r->south ? raw : 65535 - raw, x, y);
}
/* pyf_mod(x, 360) for -180 < x < 540 (a sidereal time, 0 to 360, less or plus an angle to 180): the same bits
 * without the division. (x / 360 in single precision never rounds up to 1 for x below 360, nor to 0 for x below 0, so
 * its floor is -1, 0 or 1 by x's range alone, and x - 360 * that is x + 360, x - 0 or x - 360.) */
static inline float mod360_near(float x) { return x < 0 ? x + 360.0f : x >= 360.0f ? x - 360.0f : x; }

/* a point of the ecliptic at longitude `lon`, as right ascension and declination (for drawing: single precision) */
static void ecl_point(R *r, float lon, float *ra, float *dec) {   /* (in integers: 2^-20 of a turn, Q30) */
  uint32_t l = (uint32_t)pyf_floor(lon * (1048576.0f / 360) + 0.5f), e = (uint32_t)pyf_floor((float)r->sky.eps * (1048576.0f / 360) + 0.5f);
  int32_t sl = isin_q30(l);
  int32_t y = (int32_t)(((int64_t)sl * icos_q30(e)) >> 30), x = icos_q30(l);
  int32_t a = iatan2_brad(y >> 15, x >> 15);
  *ra = (float)(a < 0 ? a + (int32_t)BRAD_TURN : a) * (360.0f / 1048576);
  *dec = (float)iasin_brad((int32_t)(((int64_t)sl * isin_q30(e)) >> 30)) * (360.0f / 1048576);
}
/* a point's altitude here (for drawing's decisions: single precision) */
static float altitude(R *r, float ra, float dec) {
  return f_asind(r->sl0 * f_sind(dec) + r->cl0 * f_cosd(dec) * f_cosd(r->lst - ra));
}
#define STAR_SIZE 6
static int star_mag(const uint8_t *s) { return ((s[4] | s[5] << 8) >> 3) - 200; }   /* hundredths */
static int star_class(const uint8_t *s) { return s[4] & 7; }                      /* by colour */

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
      if (rho > p->r_disc || dy < -p->ceiling) continue;
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

void plan_place(Face *f, int32_t lat_e4, int32_t lon_e4) {
  f->lat = (float)lat_e4 / 10000.0f, f->lon = (float)lon_e4 / 10000.0f;
}

void plan_init(Plan *p, int w, int h, const uint8_t *data, const uint8_t *geom) {
  memset(p, 0, sizeof *p);
  p->w = w, p->h = h, p->data = data, p->geom = geom;
  p->rect = w != h;
  p->lat_key = 1e9f;
  p->ev_kind = -1;
  p->news_day = -1;
  p->feast_day = -1, p->show_hour = -1;
}

#define WINDOW_FIT 40.0f                  /* the Round 2's star disc fits this latitude's whole window to the ring */
#define WINDOW_ROOM (56.0f / 124.0f)       /* and its window rises at most this part of the disc above the pole */
/* the Time 2's window kept inside the ring: in each row, WINDOW_CLEAR pixels in from the band's inner edge at least
 * (its row spans, GEO_INNER), so the window's rims meet the band's rule and never cross it (proto/plates.py
 * window_clip). Nearer the equator the window widens past the ring and is cut here, as the Round 2's star disc is cut
 * by its ring. */
#define WINDOW_CLEAR 3

void plan_window(Plan *p, float lat) {
  if (p->lat_key == lat) return;
  p->lat_key = lat;
  p->lab_ok = false;
  float alat = f_abs(lat), reach = 180.0f - alat;
  int W = p->w, H = p->h;
  if (p->rect) {
    float top = 17.0f + 62.0f, bottom = H - 17.0f - 5.0f;
    float k = (bottom - top) / 180.0f, k2 = (W / 2.0f - 17.0f - 6.0f) / 90.0f;
    p->k = (float)(k < k2 ? k : k2);
    p->cx = W / 2.0f, p->cy = (float)(top + alat * p->k);
    p->r_disc = (float)(reach * p->k);
    p->R = (W < H ? W : H) / 2.0f;
    p->ceiling = 1e9f;
  } else {
    /* one scale for every place, as one planisphere's star disc: the disc fits WINDOW_FIT degrees' whole window to
     * the ring (the commonest planisphere's), so nearer the equator the ring's edge hides the farthest sky, as a star
     * disc's edge does, and nearer a pole than about 63 degrees the card hides the window's top, where the almanac
     * keeps its room; north and south alike (proto/plates.py RoundDial) */
    p->R = (W < H ? W : H) / 2.0f;
    p->cx = W / 2.0f, p->cy = H / 2.0f;
    p->r_disc = p->R - 18.0f - 6.0f;
    p->k = p->r_disc / (180.0f - WINDOW_FIT);
    p->ceiling = p->r_disc * WINDOW_ROOM;
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
    if (p->rect) {                               /* the Time 2's window kept inside the ring */
      const int16_t *inner = sec16(p->geom, GEO_INNER);
      int clip = inner[2 * y] + WINDOW_CLEAR;
      if (inner[2 * y] > inner[2 * y + 1] || clip >= half) continue;
      if (hi < clip) hi = clip;
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
static void sky_constants(SkyK *k, float s) {
  k->day = f_smooth(-3, 7, s), k->lift = f_smooth(-18, -1, s);
  k->twf = 0.6f + 0.4f * k->lift;
  k->warm = f_smooth(-11, -1, s) * (1 - f_smooth(-1, 5, s)) * 1.25f;
}
static void sky_scalar(const SkyK *k, float alt, float gamma, float *b, float *warm) {
  float a = f_clamp(alt, 0, 90), b_tw = 0, b_day = 0;
  if (k->day < 1 && k->lift > 0) {
    float horizon = f_exp(-a * (1.0f / 32)), sunside = f_exp(-gamma * (1.0f / 80));
    b_tw = k->lift * (0.8f + 3.0f * horizon * (0.25f + 0.75f * sunside) * k->twf);
  }
  if (k->day > 0) {
    float q = 1 - a * (1.0f / 90);
    b_day = 2.3f + 2.1f * q * q * q + 1.4f * f_exp(-gamma * (1.0f / 11));
  }
  *b = f_clamp(b_tw * (1 - k->day) + b_day * k->day, 0, 5);
  *warm = k->warm > 0 ? f_clamp(k->warm * f_exp(-a * (1.0f / 15) - gamma * (1.0f / 42)), 0, 1) : 0;
}

static int q12(float v) { return (int)(v * 4096 + (v < 0 ? -0.5f : 0.5f)); }

/* the grid's values at a node (pixel coordinates of the point): the ground's (Q12, the woodcut's ecliptic latitude Q8)
 * and its warmth (Q12); with the Milky Way, the point's right ascension (Q6) and declination (Q8) */
static void node_values(R *r, float x, float y, int16_t *va, int16_t *vb) {
  float dx = x - r->cx, dy = y - r->cy, rho = f_sqrt(dx * dx + dy * dy), irho = rho > 0 ? 1 / rho : 0;
  float dec = 90.0f - rho * r->ik, ch = rho > 0 ? dy * irho : 1, sh = dx * irho;
  *va = *vb = 0;
  if (r->woodcut) {                               /* the ecliptic latitude, for the zodiac's band */
    float ha = f_atan2d(dx, dy), ra = r->south ? r->lst + ha : r->lst - ha;
    ra = pyf_mod(ra, 360);
    float d = r->south ? -dec : dec, e = (float)r->sky.eps;
    *va = (int16_t)(int)(f_asind(f_sind(d) * f_cosd(e) - f_cosd(d) * f_sind(e) * f_sind(ra)) * 256);
    return;
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
  if (r->sk.lift <= 0 && r->sk.day <= 0 && r->sk.warm <= 0) return;   /* night: the sky's darkest everywhere */
  float sd = f_sind(dec), cd = f_cosd(dec);
  float palt = f_asind(r->sl * sd + r->cl * cd * ch);
  float gamma = f_acosd(sd * r->ssd + cd * r->csd * (ch * r->csh + sh * r->ssh));
  float b, w;
  sky_scalar(&r->sk, palt, gamma, &b, &w);
  if (r->umbra > 0 && r->P->window == WIN_SKY) {  /* twilight from all round the horizon, a sunset all round */
    float b2, w2;
    sky_scalar(&r->sk6, palt, 90, &b2, &w2);
    b = b * (1 - r->umbra) + b2 * r->umbra;
    float glow = r->umbra * f_exp(-f_clamp(palt, 0, 90) * (1.0f / 9)) * (r->sol.kind == ECLIPSE_TOTAL ? 1.0f : 0.55f);
    w = w * (1 - r->umbra) > glow ? w * (1 - r->umbra) : glow;
  }
  if (r->P->window == WIN_RED) *va = (int16_t)q12(f_clamp(b * 0.5f, 0, 2));
  else *va = (int16_t)q12(f_clamp(b, 0, (float)(r->nramp - 1))), *vb = (int16_t)q12(w);
}

/* the grid cell holding a pixel: its corners' values, and where in it the pixel is (0..3 each way) */
typedef struct { int v00, v10, v01, v11, dx, dy; } Cell;
/* a node's value (plane 0 the ground, 1 the warmth). The grid keeps each node row only as far as the window's cells
 * need it, and only window pixels are read, so every node asked for is kept; one outside (none is) takes its row's
 * nearest kept node rather than reading beyond it. */
static int grid_node(R *r, int plane, int i, int j) {
  if (r->ghi[j] < r->glo[j]) return 0;
  if (i < r->glo[j]) i = r->glo[j];
  if (i > r->ghi[j]) i = r->ghi[j];
  return (plane ? r->gb : r->ga)[r->goff[j] + i - r->glo[j]];
}
static void cell_at(R *r, int plane, int x, int y, Cell *c) {
  int gx = x - r->gx0, gy = y - r->gy0;
  int i = gx >> 2, j = gy >> 2;
  if (i < 0) i = 0;
  if (j < 0) j = 0;
  if (i > r->gnx - 2) i = r->gnx - 2;
  if (j > r->gny - 2) j = r->gny - 2;
  c->dx = gx - 4 * i, c->dy = gy - 4 * j;
  c->v00 = grid_node(r, plane, i, j), c->v10 = grid_node(r, plane, i + 1, j);
  c->v01 = grid_node(r, plane, i, j + 1), c->v11 = grid_node(r, plane, i + 1, j + 1);
}
static int cell_value(const Cell *c) {
  int l = c->v00 * (4 - c->dy) + c->v01 * c->dy, rr = c->v10 * (4 - c->dy) + c->v11 * c->dy;
  return (l * (4 - c->dx) + rr * c->dx) >> 4;
}
/* how fast the value changes at the pixel, per pixel (in the value's units) */
static int cell_grad(const Cell *c) {
  int gx = ((c->v10 - c->v00) * (4 - c->dy) + (c->v11 - c->v01) * c->dy) >> 4;
  int gy = ((c->v01 - c->v00) * (4 - c->dx) + (c->v11 - c->v10) * c->dx) >> 4;
  return (int)isqrt32((uint32_t)(gx * gx + gy * gy));
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
  cell_at(r, 0, x, y, &c);
  int beta = cell_value(&c), g = cell_grad(&c);
  if (beta < 1536 && beta > -1536) return (g > 0 && (beta < 0 ? -beta : beta) * 100 < 57 * g) ? 3 : 1;
  static const int8_t N4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  for (int n = 0; n < 4; n++) {
    int X = x + N4[n][0], Y = y + N4[n][1];
    if (!inside(r, X, Y)) continue;
    cell_at(r, 0, X, Y, &c);
    int b2 = cell_value(&c);
    if (b2 < 1536 && b2 > -1536) return 2;
  }
  return 0;
}

/* the window's ground at a pixel of a banded sky (WIN_SKY, WIN_RED), its cell's corners fetched already: ca the
 * ground's, cw the warmth's and cww the warmth's as warm_corners has them (each with the pixel's dx, dy set) */
static uint8_t sky_pixel_cells(R *r, int x, int y, Cell *ca, Cell *cw, Cell *cww, int wa, int wb, bool warm) {
  const Plate *P = r->P;
  int t = r->bn[(y & 63) * 64 + (x & 63)] * 16 + 8;      /* the blue-noise threshold, Q12 */
  if (P->window == WIN_RED) return REDS[band_q(ca, t, 3, wa)];
  if (r->closed_sky) {
    int i = band_q(ca, t, 4, wa);
    return i ? GREY[i] : P->night;
  }
  uint8_t col = r->ramp[band_q(ca, t, r->nramp, wa)];
  if (warm) {
    int wv = cell_value(cw) * 5 + 819;
    if (wv >= 4096) {
      int sm = (wv - 4096) * 2;                   /* smooth(0, 0.5, wv - 1) */
      sm = sm > 4096 ? 4096 : sm;
      sm = ((sm * sm >> 12) * (12288 - 2 * sm)) >> 12;
      if (sm > t) col = WARM[band_q(cww, t, 5, wb)];
    }
  }
  return col;
}
/* the window's ground at a pixel in it (the prototype's `ground` there) */
static uint8_t sky_pixel(R *r, int x, int y, int wa, int wb, bool warm) {
  const Plate *P = r->P;
  if (P->window == WIN_SKY || P->window == WIN_RED) {
    Cell ca, cw, cww;
    cell_at(r, 0, x, y, &ca);
    cw.v00 = cw.v10 = cw.v01 = cw.v11 = 0, cww = cw;
    if (warm && P->window == WIN_SKY && !r->closed_sky) cell_at(r, 1, x, y, &cw), cww = cw, warm_corners(&cww);
    return sky_pixel_cells(r, x, y, &ca, &cw, &cww, wa, wb, warm);
  }
  if (P->window == WIN_ORLOJ) return r->s_eff > -0.833f ? C8(1, 2, 3) : r->s_eff > -18 ? C8(2, 1, 0) : C8(0, 0, 0);
  if (r->woodcut) {
    int z = zodiac_at(r, x, y);
    if (z == 1) return C8(3, 3, 1);
    if (z == 2) return P->ink;
    if (z == 3) return P->accent;
  }
  return P->night;
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

static uint8_t cloud_ground(R *r, int x, int y);
static uint8_t ground_at(R *r, int x, int y) {
  if (!inside(r, x, y)) return card_at(r, x, y);
  uint8_t c = (r->ncloud || r->nstrat) ? cloud_ground(r, x, y) : 0;
  return c ? c : sky_pixel(r, x, y, 4096, 4096, true);
}

/* the grid over the window: its nodes' values, and with the Milky Way the nodes' places in the sky */
/* a node's place in the sky, for the Milky Way: right ascension (1/64 degree) and declination (1/256 degree) */
/* (in integers: the point in half pixels, x2 = 2x; the distance from the pole in 1/64 pixel, the hour angle in
 * 2^-20 of a turn, ikq the degrees per pixel Q18) */
static void place_radec(R *r, int x2, int y2, int *ra, int *dec) {
  int dx2 = x2 - r->cx2, dy2 = y2 - r->cy2;
  uint32_t rho = isqrt32((uint32_t)(dx2 * dx2 + dy2 * dy2) << 10);
  int d = 90 * 256 - (int)(((int64_t)rho * r->ikq) >> 16);
  uint32_t ha = (uint32_t)iatan2_brad(dx2, dy2), a = (r->south ? r->lst20 + ha : r->lst20 - ha) & (BRAD_TURN - 1);
  *ra = (int)((a * 45) >> 11), *dec = r->south ? -d : d;
}
static void node_radec(R *r, int x2, int y2, int16_t *vra, int16_t *vdec) {
  int ra, dec;
  place_radec(r, x2, y2, &ra, &dec);
  *vra = (int16_t)ra, *vdec = (int16_t)dec;
}

static bool make_grid(R *r, void *(*alloc)(size_t)) {
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
  /* each node row as far as the cells either side of it hold window pixels (a cell's pixels need its four nodes) */
  for (int j = 0; j < r->gny; j++) r->glo[j] = (int16_t)r->gnx, r->ghi[j] = -1;
  for (int c = 0; c < r->gny - 1; c++) {
    int lo = 1 << 20, hi = -1;
    for (int y = r->gy0 + 4 * c; y < r->gy0 + 4 * c + 4 && y <= p->win_bottom; y++)
      if (p->wx0[y] <= p->wx1[y]) {
        if (p->wx0[y] < lo) lo = p->wx0[y];
        if (p->wx1[y] > hi) hi = p->wx1[y];
      }
    if (hi < 0) continue;
    int i0 = (lo - r->gx0) >> 2, i1 = ((hi - r->gx0) >> 2) + 1;
    if (i1 > r->gnx - 1) i1 = r->gnx - 1;
    for (int j = c; j <= c + 1; j++) {
      if (i0 < r->glo[j]) r->glo[j] = (int16_t)i0;
      if (i1 > r->ghi[j]) r->ghi[j] = (int16_t)i1;
    }
  }
  size_t n = 0;
  for (int j = 0; j < r->gny; j++) {
    r->goff[j] = (uint16_t)n;
    if (r->ghi[j] >= r->glo[j]) n += (size_t)(r->ghi[j] - r->glo[j] + 1);
  }
  r->ga = alloc(2 * (n ? n : 1) * sizeof(int16_t));
  if (!r->ga) return false;
  r->gb = r->ga + n;
  for (int j = 0; j < r->gny; j++)
    for (int i = r->glo[j]; i <= r->ghi[j]; i++) {
      size_t k = r->goff[j] + (size_t)(i - r->glo[j]);
      node_values(r, r->gx0 + 4 * i + 0.5f, r->gy0 + 4 * j + 0.5f, r->ga + k, r->gb + k);
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
      bool warm = false, any = false;
      for (int y = y0; y < y0 + 4 && y <= p->win_bottom && !any; y++) any = p->wx0[y] <= x0 + 3 && p->wx1[y] >= x0 &&
                                                                              p->wx0[y] <= p->wx1[y];
      if (!any) continue;
      Cell ca, cw, cww;                            /* (the cell's corners, once for its pixels) */
      cw.v00 = cw.v10 = cw.v01 = cw.v11 = 0, cww = cw;
      if (banded) {
        cell_at(r, 0, x0, y0, &ca);
        wa = cell_wmax(&ca);
        if (r->P->window == WIN_SKY && !r->closed_sky) {
          cell_at(r, 1, x0, y0, &cw);
          warm = cw.v00 >= 656 || cw.v10 >= 656 || cw.v01 >= 656 || cw.v11 >= 656;
          if (warm) cww = cw, warm_corners(&cww), wb = cell_wmax(&cww);
        }
      }
      for (int y = y0; y < y0 + 4 && y <= p->win_bottom; y++) {
        int a = p->wx0[y] > x0 ? p->wx0[y] : x0, b = p->wx1[y] < x0 + 3 ? p->wx1[y] : x0 + 3;
        for (int x = a; x <= b; x++) {
          if (!banded) { put(r, x, y, sky_pixel(r, x, y, wa, wb, warm)); continue; }
          ca.dx = cw.dx = cww.dx = x - x0, ca.dy = cw.dy = cww.dy = y - y0;
          put(r, x, y, sky_pixel_cells(r, x, y, &ca, &cw, &cww, wa, wb, warm));
        }
      }
    }
}

static bool hidden(R *r, int x, int y);
static bool in_band(R *r, int x, int y);

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
/* whether either stretch of the map's row j (where its cells may be other than 0) meets the cells i0..i1 (unwrapped:
 * i0 may be below 0 or i1 past the row's end) */
static bool milky_row_meets(const uint8_t *g, int j, int i0, int i1) {
  const uint8_t *e = g + 6 * j;
  for (int s = 0; s < 2; s++) {
    int start = e[2 + 2 * s], len = e[3 + 2 * s];
    if (!len) continue;
    for (int k = -MILKY_W; k <= MILKY_W; k += MILKY_W)
      if (start + k <= i1 && start + k + len - 1 >= i0) return true;
  }
  return false;
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
static void pixel_radec(R *r, int x, int y, int *ra, int *dec) { place_radec(r, 2 * x + 1, 2 * y + 1, ra, dec); }

/* the grid's row j of nodes' places in the sky, into the Milky Way's row n (the nodes the window's cells need, as
 * the grid keeps them) */
static void milky_nodes(R *r, int j, int n) {
  for (int i = r->glo[j]; i <= r->ghi[j]; i++)
    node_radec(r, 2 * (r->gx0 + 4 * i) + 1, 2 * (r->gy0 + 4 * j) + 1, &r->mra[n][i], &r->mdec[n][i]);
}
static void milky_way(R *r) {
  const Plate *P = r->P;
  Plan *p = r->p;
  const uint8_t *g = sec(p->data, SEC_MILKY);
  /* dens^1.2 > t, as level > t^(1/1.2), in the level's units: each threshold's root worked out once */
  float scale = (r->paper ? 0.30f : 0.42f) / MILKY_LEVELS / 16384;
  for (int i = 0; i < 256; i++) {
    int32_t v = (int32_t)(f_pow((i + 0.5f) * (1.0f / 256), 1.0f / 1.2f) / scale);
    if (v > 5 * 16384 + 1) v = 5 * 16384 + 1;    /* (no level exceeds it: the same test, in 17 bits) */
    r->thresh_h[i] = (uint16_t)(v >> 1);
    if (v & 1) r->thresh_odd[i >> 5] |= 1u << (i & 31);
    else r->thresh_odd[i >> 5] &= ~(1u << (i & 31));
  }
  /* a cell of the grid at a time: its corners' places in the sky (worked out a row of nodes ahead), and none of it
   * if no part of the Milky Way is near */
  milky_nodes(r, 0, 0);
  for (int j = 0; j < r->gny - 1; j++) {
    int n0 = j & 1, n1 = n0 ^ 1;
    milky_nodes(r, j + 1, n1);
    for (int i = 0; i < r->gnx - 1; i++) {
      int x0 = r->gx0 + 4 * i, y0 = r->gy0 + 4 * j;
      bool any_px = false;                       /* (a cell with no window pixel draws nothing) */
      for (int y = y0; y < y0 + 4 && y <= p->win_bottom && !any_px; y++)
        any_px = p->wx0[y] <= x0 + 3 && p->wx1[y] >= x0 && p->wx0[y] <= p->wx1[y];
      if (!any_px) continue;
      Cell a = {r->mra[n0][i], r->mra[n0][i + 1], r->mra[n1][i], r->mra[n1][i + 1], 0, 0};
      Cell d = {r->mdec[n0][i], r->mdec[n0][i + 1], r->mdec[n1][i], r->mdec[n1][i + 1], 0, 0};
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
        for (int jj = j0 < 0 ? 0 : j0; jj <= (j1 >= MILKY_H ? MILKY_H - 1 : j1) && !any; jj++) {
          if (!milky_row_meets(g, jj, i0, i1)) continue;   /* (the row's stretches clear of the cell: no cell read) */
          for (int ii = i0; ii <= i1 && !any; ii++) any = milky_cell(g, (ii % MILKY_W + MILKY_W) % MILKY_W, jj) != 0;
        }
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
          if (!m || ((r->ncloud || r->nstrat) && (hidden(r, x, y) || in_band(r, x, y)))) continue;
          if (r->woodcut) {
            if (m > 14745 && get(r, x, y) != C8(3, 3, 1)) put(r, x, y, P->milky);
          } else {
            int bn = r->bn[(y & 63) * 64 + (x & 63)];
            if (m > 2 * r->thresh_h[bn] + (int)(r->thresh_odd[bn >> 5] >> (bn & 31) & 1)) put(r, x, y, P->milky);
          }
        }
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
/* anything of the land (grown a pixel), or one of Jupiter's moons, in the box */
static bool blocked(R *r, const int16_t b[4]) {
  for (int i = 0; i < r->nmarks; i++)
    if (r->marks[i][0] >= b[0] && r->marks[i][0] < b[2] && r->marks[i][1] >= b[1] && r->marks[i][1] < b[3]) return true;
  for (int i = 0; i < r->nmoons; i++) {
    int mx = r->moonbox[i][0], my = r->moonbox[i][1];
    if ((b[0] <= mx + 2 && mx - 2 < b[2] && b[1] <= my + 1 && my - 1 < b[3]) ||
        (b[0] <= mx + 1 && mx - 1 < b[2] && b[1] <= my + 2 && my - 2 < b[3]))
      return true;
  }
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


/* ---- the weather, as the sky shows it (proto/weather.py sky_of) ------------------------------------------------ */
static void weather_sky(R *r) {
  const Weather *w = r->f->weather;
  if (!w) return;
  r->wx = true;
  int code = w->code;
  /* the WMO codes that fall: (code, kind << 2 | how heavy), as proto/weather.py FALLS */
  static const uint8_t FALLS[22][2] = {
    {51, FALL_DRIZZLE << 2 | 1}, {53, FALL_DRIZZLE << 2 | 2}, {55, FALL_DRIZZLE << 2 | 3}, {56, FALL_DRIZZLE << 2 | 1},
    {57, FALL_DRIZZLE << 2 | 2}, {61, FALL_RAIN << 2 | 1}, {63, FALL_RAIN << 2 | 2}, {65, FALL_RAIN << 2 | 3},
    {66, FALL_RAIN << 2 | 1}, {67, FALL_RAIN << 2 | 3}, {71, FALL_SNOW << 2 | 1}, {73, FALL_SNOW << 2 | 2},
    {75, FALL_SNOW << 2 | 3}, {77, FALL_SNOW << 2 | 1}, {80, FALL_RAIN << 2 | 1}, {81, FALL_RAIN << 2 | 2},
    {82, FALL_RAIN << 2 | 3}, {85, FALL_SNOW << 2 | 1}, {86, FALL_SNOW << 2 | 3}, {95, FALL_RAIN << 2 | 2},
    {96, FALL_HAIL << 2 | 2}, {99, FALL_HAIL << 2 | 3}};
  for (int i = 0; i < 22; i++)
    if (FALLS[i][0] == code) r->fall_kind = FALLS[i][1] >> 2, r->heavy = FALLS[i][1] & 3;
  bool snow = r->fall_kind == FALL_SNOW;
  r->falls = r->fall_kind != FALL_NONE;
  r->rain_or_hail = r->fall_kind == FALL_RAIN || r->fall_kind == FALL_HAIL;
  r->snow_falls = snow;
  r->fog = code == 45 || code == 48 || w->vis_dam < 100;
  float low = w->low / 100.0f, mid = w->mid / 100.0f, high = w->high / 100.0f;
  if (mid * 0.6f > low) low = mid * 0.6f;
  float sheet = r->falls ? 1.0f : f_smooth(0.55f, 0.9f, low);
  float clear = r->fog ? 0.0f : 1.0f;
  r->haze = 1.6f * high + (r->fog ? 2.5f : w->vis_dam < 500 ? 1.2f : 0.0f);
  r->cumulus = low * (1 - sheet) * clear, r->stratus = low * sheet * clear, r->cirrus = high * clear;
  r->halo = high >= 0.45f && low < 0.5f && !r->falls;
  r->thunder = code >= 95;
  r->snow_lying = w->snow_mm > 5 || snow;
  r->frost = w->temp10 <= 0;
  r->smoke = w->temp10 < 120;
  r->wind = w->wind, r->wind_from = w->wind_from;
}

/* ---- the weather in the window (proto/skies.py): Howard's clouds drifting downwind, rain and snow ---------------- */
/* the day's generator for a layer of the weather (plan_math.h Rng, the prototype's), so both scatter it alike */
static void rng_seed(Rng *g, R *r, int salt) {
  rng_start(g, (uint32_t)r->local.ordinal * 7919u + (uint32_t)pyf_round((float)r->f->lat * 10) * 104729u +
               (uint32_t)pyf_round((float)r->f->lon * 10) * 1299709u + (uint32_t)salt * 15485863u);
}


#define CLOUD_SPEED 0.0015f                  /* pixels a second per km/h of wind */
#define MARGIN 28
static float wrap(float v, float lo, float hi) { return lo + pyf_mod(v - lo, hi - lo); }

typedef struct { int x_lo, x_hi, y_lo, y_hi, area; float dx, dy; } Bounds;
static void bounds(R *r, Bounds *b) {
  Plan *p = r->p;
  b->x_lo = r->W, b->x_hi = 0, b->area = 0;
  for (int y = p->win_top; y >= 0 && y <= p->win_bottom; y++) {
    if (p->wx0[y] > p->wx1[y]) continue;
    if (p->wx0[y] < b->x_lo) b->x_lo = p->wx0[y];
    if (p->wx1[y] + 1 > b->x_hi) b->x_hi = p->wx1[y] + 1;
    b->area += p->wx1[y] - p->wx0[y] + 1;
  }
  b->y_lo = p->win_top, b->y_hi = p->win_bottom + 1;
  float to = r->wind_from + 180, v = CLOUD_SPEED * (r->wind > 3 ? r->wind : 3);    /* downwind: east left, north up */
  b->dx = -f_sind(to) * v, b->dy = -f_cosd(to) * v;
}

/* `n` clouds in the window at any moment (as many again for the margins they drift through), kept apart */
static void scatter(R *r, const Bounds *b, int first, int n, int salt, const float w[3]) {
  Rng g;
  rng_seed(&g, r, salt);
  n = pyf_round((float)n * (float)(b->x_hi - b->x_lo + 2 * MARGIN) * (float)(b->y_hi - b->y_lo + 16) / (float)b->area);
  float pu[24], pv[24];
  uint8_t pd[24], pf[24];
  int placed = 0;
  for (int k = 0; k < n * 12 && placed < n && placed < 24; k++) {
    float u = rng_random(&g), acc = 0;
    int d = 2;
    for (int i = 0; i < 3; i++)
      if (u < (acc += w[i])) { d = i; break; }
    bool flip = rng_random(&g) < 0.5f;
    float cu = rng_uniform(&g, (float)(b->x_lo - MARGIN), (float)(b->x_hi + MARGIN));
    float cv = rng_uniform(&g, (float)(b->y_lo - 10), (float)(b->y_hi + 6));
    const DrawIndex *di = drawing(r, first + d);
    bool apart = true;
    for (int q = 0; q < placed && apart; q++) {
      const DrawIndex *dq = drawing(r, pd[q]);
      apart = !(f_abs(cu - pu[q]) < (di->w + dq->w) / 2.0f + 3 && f_abs(cv - pv[q]) < (di->h + dq->h) / 2.0f + 3);
    }
    if (!apart) continue;
    pu[placed] = cu, pv[placed] = cv, pd[placed] = (uint8_t)(first + d), pf[placed] = flip, placed++;
  }
  float t = (float)r->secs;
  for (int q = 0; q < placed && r->ncloud < 24; q++) {
    const DrawIndex *di = drawing(r, pd[q]);
    float x = wrap(pu[q] + b->dx * t, (float)(b->x_lo - MARGIN), (float)(b->x_hi + MARGIN));
    float y = wrap(pv[q] + b->dy * t, (float)(b->y_lo - 10), (float)(b->y_hi + 6));
    r->cloud[r->ncloud].d = pd[q], r->cloud[r->ncloud].flip = pf[q];
    r->cloud[r->ncloud].x0 = (int16_t)pyf_round(x - di->w / 2.0f), r->cloud[r->ncloud].y0 = (int16_t)pyf_round(y - di->h / 2.0f);
    r->ncloud++;
  }
}

/* the weather's drawings at this moment (the same clouds all day, drifting on) */
static void weather_layer(R *r) {
  if (!r->wx || !r->live) return;
  Bounds b;
  bounds(r, &b);
  if (r->cumulus > 0.05f) {                      /* heaps, flattening into banks as the low cloud thickens */
    float big = r->cumulus * 1.4f < 1 ? r->cumulus * 1.4f : 1;
    const float w1[3] = {0.15f + 0.3f * big, 0.45f, 0.4f - 0.3f * big}, w2[3] = {0.45f, 0.35f, 0.2f};
    scatter(r, &b, D_CUMULUS0, pyf_round(1 + 6 * r->cumulus), 1, w1);
    if (r->cumulus > 0.35f) scatter(r, &b, D_STRATUS0, pyf_round(6 * (r->cumulus - 0.3f)), 5, w2);
  }
  float t = (float)r->secs;
  if (r->stratus > 0.08f) {                      /* the sheet in ruled lines, a lens of three to five to each band */
    Rng g;
    rng_seed(&g, r, 2);
    int nb = pyf_round(1 + 4 * r->stratus);
    float span = (float)(b.y_hi - b.y_lo) / (float)nb;
    for (int k = 0; k < nb; k++) {
      int nl = rng_int(&g, 3, 6);
      float yc = (float)b.y_lo + span * (k + 0.5f) + rng_uniform(&g, -span * 0.2f, span * 0.2f);
      float half = (float)(b.x_hi - b.x_lo) * (0.22f + 0.3f * r->stratus) * rng_uniform(&g, 0.8f, 1.15f);
      float xc = wrap(rng_uniform(&g, (float)(b.x_lo - MARGIN), (float)(b.x_hi + MARGIN)) + b.dx * t,
                      (float)(b.x_lo - MARGIN), (float)(b.x_hi + MARGIN));
      for (int l = 0; l < nl; l++) {
        int y = pyf_round(yc + 2 * (l - (nl - 1) / 2.0f));
        float prof = f_pow(f_sind(180.0f * (l + 1) / (nl + 1)), 0.6f);
        int x0 = pyf_round(xc - half * prof + rng_uniform(&g, -3, 3));
        int x1 = pyf_round(xc + half * prof + rng_uniform(&g, -3, 3));
        if (r->nstrat < 28) r->strat[r->nstrat][0] = (int16_t)y, r->strat[r->nstrat][1] = (int16_t)x0, r->strat[r->nstrat][2] = (int16_t)x1, r->nstrat++;
      }
    }
  }
  if (r->cirrus > 0.1f) {                        /* a few hair strokes, drifting faster */
    Rng g;
    rng_seed(&g, r, 3);
    int n = pyf_round(5 * r->cirrus);
    for (int k = 0; k < n && r->nhair < 8; k++) {
      int d = D_CIRRUS0 + rng_int(&g, 0, 3);
      bool flip = rng_random(&g) < 0.5f;
      float x = wrap(rng_uniform(&g, (float)(b.x_lo - MARGIN), (float)(b.x_hi + MARGIN)) + 1.6f * b.dx * t,
                     (float)(b.x_lo - MARGIN), (float)(b.x_hi + MARGIN));
      float y = wrap(rng_uniform(&g, (float)b.y_lo, (float)b.y_hi) + 1.6f * b.dy * t, (float)(b.y_lo - 4), (float)b.y_hi);
      r->hair[r->nhair].d = (uint8_t)d, r->hair[r->nhair].flip = flip;
      r->hair[r->nhair].x0 = (int16_t)pyf_round(x), r->hair[r->nhair].y0 = (int16_t)pyf_round(y);
      r->nhair++;
    }
  }
}

/* the cumulus's role at a pixel (0 none): what hides the stars */
static int cloud_role(R *r, int x, int y) {
  int role = 0;
  for (int i = 0; i < r->ncloud; i++) {
    const DrawIndex *di = drawing(r, r->cloud[i].d);
    int ii = x - r->cloud[i].x0, jj = y - r->cloud[i].y0;
    if (ii < 0 || jj < 0 || ii >= di->w || jj >= di->h) continue;
    int v = role_at(r, di, r->cloud[i].flip ? di->w - 1 - ii : ii, jj);
    if (v) role = v;
  }
  return role;
}
static bool hidden(R *r, int x, int y) { return r->ncloud && cloud_role(r, x, y) != 0; }
/* under the stratus's ruled lines (a row either side): only the brightest stars show */
static bool in_band(R *r, int x, int y) {
  for (int i = 0; i < r->nstrat; i++) {
    int ly = r->strat[i][0], x0 = r->strat[i][1] < 0 ? 0 : r->strat[i][1], x1 = r->strat[i][2];
    if (y >= ly - 1 && y <= ly + 1 && x >= x0 && x <= x1) return true;
  }
  return false;
}
/* a pixel the clouds keep off: round a bright star a stratus line or a hair stroke passes */
static bool kept(R *r, int x, int y) {
  for (int i = 0; i < r->ndrawn; i++) {
    int h = r->drawn[i][2];
    if (x >= r->drawn[i][0] - h - 1 && x <= r->drawn[i][0] + h + 1 && y >= r->drawn[i][1] - h - 1 && y <= r->drawn[i][1] + h + 1)
      return true;
  }
  return false;
}
/* the clouds' colour at a pixel, as the ground under the names (0: none there) */
static uint8_t cloud_ground(R *r, int x, int y) {
  uint8_t c = 0;
  if (r->ncloud) {
    int role = cloud_role(r, x, y);
    if (role) c = r->cc[role == 1 ? 0 : role == 5 ? 1 : 2];
  }
  for (int i = 0; i < r->nstrat; i++)
    if (y == r->strat[i][0] && x >= r->strat[i][1] && x <= r->strat[i][2] && !kept(r, x, y)) c = r->c_line;
  return c;
}

/* the clouds' colours for the hour: the top lit, the base shaded; by night dark, the edge silvered */
static void cloud_colours(R *r, bool moonlit) {
  bool overcast = r->stratus > 0.5f || r->falls;
  float s = r->s_eff;
  if (r->red) {
    r->cc[0] = r->c_line = r->c_hair = C8(1, 0, 0), r->cc[1] = r->cc[2] = 0;
    r->c_rain[0] = C8(1, 0, 0), r->c_rain[1] = C8(2, 0, 0), r->c_snow = C8(2, 0, 0);
  } else if (s >= 6) {
    r->cc[0] = r->cc[1] = C8(3, 3, 3), r->cc[2] = overcast ? C8(2, 2, 2) : C8(2, 2, 3);
    r->c_line = overcast ? C8(3, 3, 3) : C8(2, 3, 3), r->c_hair = C8(3, 3, 3);
    r->c_rain[0] = C8(1, 1, 2), r->c_rain[1] = overcast ? C8(3, 3, 3) : C8(2, 2, 3), r->c_snow = C8(3, 3, 3);
  } else if (s >= -2) {
    r->cc[0] = C8(3, 3, 2), r->cc[1] = C8(3, 2, 2), r->cc[2] = C8(3, 1, 1), r->c_line = r->c_hair = C8(3, 2, 2);
    r->c_rain[0] = C8(1, 1, 2), r->c_rain[1] = C8(2, 2, 3), r->c_snow = C8(3, 3, 3);
  } else if (s >= -8) {
    r->cc[0] = C8(2, 1, 2), r->cc[1] = C8(1, 1, 2), r->cc[2] = C8(3, 1, 1), r->c_line = C8(2, 1, 2), r->c_hair = C8(3, 1, 1);
    r->c_rain[0] = C8(1, 1, 2), r->c_rain[1] = C8(2, 2, 3), r->c_snow = C8(3, 3, 3);
  } else {
    uint8_t lit = moonlit ? C8(2, 2, 2) : C8(1, 1, 2);
    r->cc[0] = r->c_line = lit, r->cc[1] = r->cc[2] = C8(0, 0, 0), r->c_hair = C8(0, 1, 2);
    r->c_rain[0] = C8(1, 1, 2), r->c_rain[1] = C8(0, 1, 2), r->c_snow = lit;
  }
}

/* the clouds over the stars: the cumulus filled, the stratus ruled, the cirrus stroked (the lines kept off the
 * bright stars) */
static void paint_clouds(R *r) {
  for (int i = 0; i < r->ncloud; i++) {
    const DrawIndex *di = drawing(r, r->cloud[i].d);
    for (int j = 0; j < di->h; j++)
      for (int k = 0; k < di->w; k++) {
        int v = role_at(r, di, r->cloud[i].flip ? di->w - 1 - k : k, j), X = r->cloud[i].x0 + k, Y = r->cloud[i].y0 + j;
        if (!v || !inside(r, X, Y)) continue;
        uint8_t c = r->cc[v == 1 ? 0 : v == 5 ? 1 : 2];
        put(r, X, Y, c ? c : sky_pixel(r, X, Y, 4096, 4096, true));
      }
  }
  for (int i = 0; i < r->nstrat; i++) {
    int y = r->strat[i][0];
    for (int x = r->strat[i][1] < 0 ? 0 : r->strat[i][1]; x <= r->strat[i][2] && x < r->W; x++)
      if (inside(r, x, y) && !kept(r, x, y)) put(r, x, y, r->c_line);
  }
  for (int i = 0; i < r->nhair; i++) {
    const DrawIndex *di = drawing(r, r->hair[i].d);
    for (int j = 0; j < di->h; j++)
      for (int k = 0; k < di->w; k++) {
        int X = r->hair[i].x0 + k, Y = r->hair[i].y0 + j;
        if (role_at(r, di, r->hair[i].flip ? di->w - 1 - k : k, j) && inside(r, X, Y) && !kept(r, X, Y)) put(r, X, Y, r->c_hair);
      }
  }
}

/* thin high cloud rings the Moon (or by day the Sun) with a halo at 22 degrees, in the chart's own projection */
static void paint_halo(R *r, float ra, float dec, uint8_t c) {
  float d0 = r->south ? -dec : dec, h0 = r->south ? -(r->lst - ra) : r->lst - ra;
  float bx, by;
  project(r, ra, dec, &bx, &by);
  float reach = (22 + 1) * r->k * 2.2f, tol = 0.5f / r->k, sd0 = f_sind(d0), cd0 = f_cosd(d0);
  for (int y = pyf_floor(by - reach); y <= pyf_floor(by + reach); y++)
    for (int x = pyf_floor(bx - reach); x <= pyf_floor(bx + reach); x++) {
      if (!inside(r, x, y) || r->bn[(y & 63) * 64 + (x & 63)] * 16 + 8 >= 2867) continue;    /* tt < 0.7 */
      float dx = x + 0.5f - r->cx, dy = y + 0.5f - r->cy, rho = f_sqrt(dx * dx + dy * dy);
      float pd = 90.0f - rho * r->ik, ph = f_atan2d(dx, dy);
      float g = f_acosd(f_sind(pd) * sd0 + f_cosd(pd) * cd0 * f_cosd(ph - h0));
      if (f_abs(g - 22) < tol) put(r, x, y, c);
    }
}

/* rain cut as Hiroshige cut it, leaning with the wind, in two tones; snow pecked in soft squares; hail in dots */
static void paint_falls(R *r) {
  if (!r->wx || !r->live || !r->falls) return;
  Bounds b;
  bounds(r, &b);
  Rng g;
  rng_seed(&g, r, 4);
  /* a day's fall carries a streak millions of pixels before it wraps: the fall itself wrapped in whole pixels, the lean
   * wrapped before the start is added */
  float east = -f_sind(r->wind_from + 180), lean = -east * r->wind / 45.0f;
  lean = lean > 0.7f ? 0.7f : lean < -0.7f ? -0.7f : lean;
  bool drizzle = r->fall_kind == FALL_DRIZZLE, rain = drizzle || r->fall_kind == FALL_RAIN;
  int n = (int)((rain ? (drizzle ? 22 : 34) : (r->fall_kind == FALL_SNOW ? 22 : 30)) * r->heavy * b.area / 14000);
  int fall = drizzle ? 25 : r->fall_kind == FALL_RAIN ? 40 : r->fall_kind == FALL_SNOW ? 4 : 30;
  int span_x = b.x_hi - b.x_lo, span_y = b.y_hi - b.y_lo, F = fall * r->secs;
  float dy = (float)(F % span_y), dx = pyf_mod(lean * (float)F, (float)span_x);
  float sway = r->fall_kind == FALL_SNOW ? 1.5f : 0, turn = pyf_mod((float)r->secs * 45.8366236f, 360);   /* 0.8 rad/s */
  for (int k = 0; k < n; k++) {
    float u = rng_uniform(&g, (float)b.x_lo, (float)b.x_hi), v = rng_uniform(&g, (float)b.y_lo, (float)b.y_hi);
    if (rain) {
      int len = drizzle ? rng_int(&g, 2, 4) : rng_int(&g, 3, 7);
      float y = wrap(v + dy, (float)b.y_lo, (float)b.y_hi), x = wrap(u + dx, (float)b.x_lo, (float)b.x_hi);
      uint8_t c = r->c_rain[k % 3 == 0 ? 0 : 1];
      for (int s2 = 0; s2 < len; s2++) {
        int X = pyf_floor(x + lean * s2), Y = pyf_floor(y + s2);
        if (inside(r, X, Y)) put(r, X, Y, c);
      }
    } else {
      float ph = rng_uniform(&g, 0, 360);
      float y = wrap(v + dy, (float)b.y_lo, (float)b.y_hi);
      float x = wrap(u + dx + sway * f_sind(turn + ph), (float)b.x_lo, (float)b.x_hi);
      int X = pyf_floor(x), Y = pyf_floor(y);
      if (r->fall_kind == FALL_SNOW) {
        uint8_t col[8] = {0, 0, 0, 0, 0, r->c_snow};
        paint_at(r, D_SNOWFLAKE, X, Y, col, true, 0);
      } else if (inside(r, X, Y))
        put(r, X, Y, r->c_snow);
    }
  }
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

static inline __attribute__((always_inline)) bool span_has(const int16_t *s, int y, int x) { return x >= s[2 * y] && x <= s[2 * y + 1]; }

static void figure_lines(R *r, int part) {
  const uint8_t *st = sec(r->p->data, SEC_STARS);
  const uint16_t *ln = (const uint16_t *)(const void *)sec(r->p->data, SEC_LINES);
  for (int i = 0; i < LINE_COUNT; i++) {
    int xq[2], yq[2];                                /* (the ends in 1/256 pixel, as projected) */
    for (int e = 0; e < 2; e++) {
      float fx, fy;
      project_star(r, st + STAR_SIZE * ln[2 * i + e], &fx, &fy);
      xq[e] = (int)(fx * 256), yq[e] = (int)(fy * 256);
    }
    int dx = xq[1] - xq[0], dy = yq[1] - yq[0], dx4 = dx >> 4, dy4 = dy >> 4;
    int L4 = (int)isqrt32((uint32_t)(dx4 * dx4 + dy4 * dy4));   /* the length in 1/16 pixel */
    if (L4 < 72) continue;                                        /* (under 4.5 pixels) */
    /* the ends drawn in 2.6 pixels; the prototype's antialiased line, its coverage over 0.55: within 0.3375 px of a
     * sample point (in 1/256 px) */
    int inx = dx * 208 / (5 * L4), iny = dy * 208 / (5 * L4);   /* (dx within 2^17: no 64-bit division) */
    int axq = xq[0] + inx, ayq = yq[0] + iny, dxq = xq[1] - inx - axq, dyq = yq[1] - iny - ayq;
    int adx = dxq < 0 ? -dxq : dxq, ady = dyq < 0 ? -dyq : dyq;
    int n = (((adx > ady ? adx : ady) * 3) >> 8) + 1;
    for (int k = 0; k <= (part ? n * part / EVENT_FIGS_FRAMES : n); k++) {   /* (drawn in at dusk: so far along) */
      int pxq = axq + dxq * k / n, pyq = ayq + dyq * k / n, xi = pxq >> 8, yi = pyq >> 8;
      for (int dy = 0; dy <= 1; dy++)
        for (int dx = 0; dx <= 1; dx++) {
          int X = xi + dx, Y = yi + dy, ex = pxq - (X * 256 + 128), ey = pyq - (Y * 256 + 128);
          if (ex * ex + ey * ey < 7465 && inside(r, X, Y) && !hidden(r, X, Y) && !in_band(r, X, Y)) put(r, X, Y, r->P->line);
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
    bool too_faint = (float)mg * 0.01f > faint;
    if (too_faint && mg >= 210) continue;
    float x, y;
    project_star(r, s, &x, &y);
    int xi = pyf_floor(x), yi = pyf_floor(y);
    if (mg < 210 && r->nbright < 96) r->bright[r->nbright][0] = (int16_t)xi, r->bright[r->nbright][1] = (int16_t)yi, r->nbright++;
    if (too_faint) continue;
    if (r->lit_moon && mg > 220 && (x - mx) * (x - mx) + (y - my) * (y - my) < (6 + moon_reach) * (6 + moon_reach)) continue;
    if (on_screen(r, xi, yi) && (hidden(r, xi, yi) || (mg > 160 && in_band(r, xi, yi)))) continue;
    int half = r->rete ? 2 : mg < 50 ? 3 : mg < 140 ? 2 : mg < 210 ? 1 : 0;
    if (half && r->ndrawn < 96 && (!r->rete || mg < 200))
      r->drawn[r->ndrawn][0] = (int16_t)xi, r->drawn[r->ndrawn][1] = (int16_t)yi, r->drawn[r->ndrawn][2] = (int16_t)half, r->ndrawn++;
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
  memset(r->vtop, 0, sizeof r->vtop), memset(r->vground, 0, sizeof r->vground);   /* (their memory the sky's till now) */
  memset(r->vmask, 0, sizeof r->vmask);
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

/* whether today's feast (plan_feast) brings this (FF_*) */
static bool feast_brings(R *r, int flag) {
  Plan *p = r->p;
  return p->feast && p->feast_day == r->local.ordinal && (p->feast_flags & flag);
}

/* ---- the fireworks display (proto/feast_draw.py show_plan), worked out at the top of an hour that brings one:
 * each hour of a fireworks feast's evening once the Sun is down, from seven to eleven, and the midnight that ends a
 * feast turning the year. Five rockets one after another from the window's edge either side of the village, then a
 * finale of three; plan_show plays it. ---------------------------------------------------------------------------- */
/* the commonest colour of the window's ground in the five pixels square round a point (the first met, row by row,
 * among equals), or -1 if none of it is in the window: the margin round a rocket's sparks */
static int halo_colour(R *r, int x, int y) {
  uint8_t seen[25];
  int n = 0, best = -1, most = 0;
  for (int j = -2; j <= 2; j++)
    for (int i = -2; i <= 2; i++)
      if (inside(r, x + i, y + j)) seen[n++] = ground_at(r, x + i, y + j);
  for (int a = 0; a < n; a++) {
    int c = 0;
    for (int b = 0; b < n; b++) c += seen[b] == seen[a];
    if (c > most) most = c, best = seen[a];
  }
  return best;
}
static void show_plan(R *r) {
  Plan *p = r->p;
  int hour = r->local.hour, flags = 0;
  if (hour == 0) flags = p->feast_day == r->local.ordinal ? p->feast_eve : 0;
  else if (feast_brings(r, FF_FIREWORKS) && r->sun_alt < -1 && hour >= 19 && hour <= 23) flags = p->feast_flags;
  p->show_hour = -1;
  if (!flags || r->local.minute != 0) return;
  const uint8_t *sparks = SPARK_COLOURS[(flags >> 4) & 3];
  int colours = 0;
  while (colours < 4 && sparks[colours]) p->show_sparks[colours] = sparks[colours], colours++;
  if (colours < 4) p->show_sparks[colours] = 0;
  int32_t at = r->local.ordinal * 24 + hour;
  Rng g;
  rng_start(&g, (uint32_t)at);
  int starts[SHOW_ROCKETS], f = 0, n = 0, end = 0;
  for (int i = 0; i < 5; i++) starts[i] = f, f += rng_int(&g, 8, 13);
  for (int i = 0; i < 3; i++) starts[5 + i] = f + 4 + 2 * i;
  for (int i = 0; i < SHOW_ROCKETS; i++) {
    int dx = rng_int(&g, -50, 51), e = r->edge[dx + VILLAGE_DX];
    if (e < 0) continue;
    Rocket *k = &p->show[n++];
    k->f0 = (uint8_t)starts[i], k->x0 = (int16_t)(r->col + dx), k->foot = (int16_t)(e - 3);
    k->rise = (uint8_t)rng_int(&g, 44, 92), k->up = (uint8_t)rng_int(&g, 10, 15), k->drift = (int8_t)rng_int(&g, -6, 7);
    k->R = (uint8_t)rng_int(&g, 11, 18), k->kind = (uint8_t)rng_int(&g, 0, 3);
    k->colour = (uint8_t)rng_int(&g, 0, colours), k->turn = rng_random(&g);
    k->n = k->R >= 14 ? 20 : 16;
    int h = halo_colour(r, k->x0 + k->drift, k->foot - k->rise);       /* where it bursts, else where it rises */
    if (h < 0) h = halo_colour(r, k->x0, k->foot);
    k->halo = (uint8_t)(h < 0 ? ground_at(r, k->x0, e) : h);
    if (k->f0 + k->up + SHOW_SPREAD + SHOW_LIFE + 1 > end) end = k->f0 + k->up + SHOW_SPREAD + SHOW_LIFE + 1;
  }
  p->show_rockets = (uint8_t)n, p->show_end = (uint16_t)end, p->show_ink = r->paper ? r->P->accent : 0;
  p->show_hour = at;
}

/* the passing event for this minute, now and then (Plan.event, played by plan_event): on a clear dark night a meteor
 * (one minute in five in a shower's peak, out of its radiant when that is up; else one in forty-five); at twilight
 * in the months birds migrate a skein of them crossing the window low, in the twilight's light, once a twilight (one minute in twelve). Chosen
 * once a minute, never with a fireworks display or the figures being drawn in. */
static void passing(R *r, int rad_x, int rad_y) {
  Plan *p = r->p;
  const Face *f = r->f;
  int32_t minute = r->local.ordinal * 1440 + r->local.hour * 60 + r->local.minute;
  if (f->figs_part || p->event || p->show_hour >= 0 || p->event_minute == minute) return;
  p->event_minute = minute;
  if (r->closed_sky || (r->wx && (r->falls || r->fog))) return;
  Rng g;
  rng_seed(&g, r, 7 + r->local.hour * 60 + r->local.minute);
  int top = p->win_top, span = p->win_bottom - p->win_top, month = r->local.month;
  int32_t twilight = r->local.ordinal * 2 + (r->local.hour >= 12);
  if ((f->events & EV_METEOR) && r->sun_alt < -12 && !(r->wx && r->live && r->stratus + r->cumulus > 0.45f) &&
      rng_int(&g, 0, plan_shower(r->sky.sun_lon) >= 0 ? 5 : 45) == 0) {
    int y = top + 6 + rng_int(&g, 0, span / 2 + 1), w = p->wx1[y] - p->wx0[y] - 12;
    int x = p->wx0[y] + 6 + rng_int(&g, 0, w > 1 ? w : 1);
    int dx = rng_int(&g, -16, 17), dy = rng_int(&g, -4, 17);           /* (falling, as a rule) */
    if (r->shower >= 0 && (x - rad_x) * (x - rad_x) + (y - rad_y) * (y - rad_y) > 64) dx = x - rad_x, dy = y - rad_y;
    p->event = EV_METEOR, p->event_frames = 6, p->event_ink = (r->paper || r->red) ? r->P->star : 0;
    p->event_x0 = (int16_t)x, p->event_y0 = (int16_t)y, p->event_x1 = (int16_t)dx, p->event_y1 = (int16_t)dy;
  } else if ((f->events & EV_BIRDS) && r->sun_alt > -6 && r->sun_alt < 4 && month % 6 >= 3 && p->birds_mark != twilight &&
             rng_int(&g, 0, 12) == 0) {
    int y = top + span * 2 / 3 + rng_int(&g, 0, span / 8 + 1), w = p->wx1[y] - p->wx0[y];
    p->birds_mark = twilight;
    p->event = EV_BIRDS, p->event_frames = (uint8_t)((w + 38) * 2 / 5 < 90 ? (w + 38) * 2 / 5 : 90);
    p->event_ink = r->paper ? r->P->line : C8(0, 0, 0);
    p->event_x0 = (int16_t)rng_int(&g, 0, 2), p->event_y0 = (int16_t)y, p->event_y1 = (int16_t)(y - rng_int(&g, 0, 10));
  }
}

/* fires on the hilltops on a fire festival's night (proto/feast_draw.py bonfires): on the three highest tops at least
 * twenty pixels from the church, eighteen apart, each a flame with its glow round it and a spark that moves with the
 * minute; on a printed chart in its red ink */
static void feast_fires(R *r) {
  if (!feast_brings(r, FF_BONFIRES) || r->sun_alt >= -4 || (r->wx && (r->fog || r->falls))) return;
  static const char *const FLAME[4] = {"..Y..", ".YOY.", ".ORO.", "ORRRO"};
  /* the tops in the prototype's order (the highest first, the rightmost of equals), each kept if eighteen from those
   * kept */
  int chosen[3], nc = 0, last_h = 1 << 20, last_dx = 1 << 20;
  while (nc < 3) {
    int bh = -1, bdx = 0;
    for (int dx = -VILLAGE_DX; dx <= VILLAGE_DX; dx++) {
      if (r->edge[dx + VILLAGE_DX] < 0 || (dx < 20 && dx > -20)) continue;
      int h = pyf_round(interp(dx, DISTANT, DISTANT_COUNT));
      if (h < 3 || h > last_h || (h == last_h && dx >= last_dx)) continue;
      if (h > bh || (h == bh && dx > bdx)) bh = h, bdx = dx;
    }
    if (bh < 0) break;
    last_h = bh, last_dx = bdx;
    bool far = true;
    for (int c = 0; c < nc; c++) far &= bdx - chosen[c] >= 18 || chosen[c] - bdx >= 18;
    if (far) chosen[nc++] = bdx;
  }
  Rng g;
  rng_start(&g, (uint32_t)(r->local.ordinal * 1440 + r->local.hour * 60 + r->local.minute));
  uint8_t ink = r->paper ? r->P->accent : 0;
  for (int c = 0; c < nc; c++) {
    int dx = chosen[c], x0 = r->col + dx - 2;
    int base = r->edge[dx + VILLAGE_DX] - pyf_round(interp(dx, DISTANT, DISTANT_COUNT));
    if (!ink)
      for (int j = -6; j < 2; j++)
        for (int i = -4; i < 9; i++) {
          int a = i - 2, b = j + 2, d100 = 100 * a * a + 169 * b * b;   /* (d = hypot(a, 1.3 b), in hundredths squared) */
          if (inside(r, x0 + i, base + j) && d100 < 2704 && ((i + j) % 2 + 2) % 2 == 0)
            put(r, x0 + i, base + j, d100 < 1225 ? C8(2, 1, 0) : C8(1, 0, 0));
        }
    for (int j = 0; j < 4; j++)
      for (int i = 0; i < 5; i++) {
        char ch = FLAME[j][i];
        int y = base - 3 + j, x = x0 + i;
        if (ch != '.' && inside(r, x, y)) put(r, x, y, ink ? ink : ch == 'Y' ? C8(3, 3, 1) : ch == 'O' ? C8(3, 2, 0) : C8(3, 0, 0));
      }
    int y = base - 5 - rng_int(&g, 0, 3), x = x0 + 2 + rng_int(&g, -1, 2);
    if (inside(r, x, y)) put(r, x, y, ink ? ink : C8(3, 3, 1));
  }
}

static void vput(R *r, int dx, int y, uint8_t c) {
  if (dx >= -VILLAGE_DX && dx <= VILLAGE_DX) {
    if (y < r->vtop[dx + VILLAGE_DX]) r->vtop[dx + VILLAGE_DX] = (int16_t)y;
    int up = r->edge[dx + VILLAGE_DX] - y;
    if (up >= 0 && up < 32 && inside(r, r->col + dx, y)) r->vmask[dx + VILLAGE_DX] |= 1u << up;
  }
  int x = r->col + dx;
  if (inside(r, x, y)) put(r, x, y, c), land(r, x, y);
}

/* a window of the village lit: in the evening and the early morning most of them (all, on a feast of lights), but
 * with the village's life (EV_VILLAGE) each comes and goes by the ten minutes, three in four lit then and one in eight
 * through the night */
static bool window_lit(R *r, bool lit, int which) {
  if (!(r->f->events & EV_VILLAGE) || feast_brings(r, FF_LIGHTS) || r->sun_alt >= -4) return lit;
  Rng g;
  rng_seed(&g, r, which * 1440 + r->secs / 600);
  return rng_int(&g, 0, 8) < (lit ? 6 : 1);
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
  if (feast_brings(r, FF_LIGHTS)) lit = r->sun_alt < -4;   /* a feast of lights: a candle in every window, all night */
  bool night_land = r->night_land = r->sun_alt < -6 || r->red;
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
        if (role == 3 && !window_lit(r, lit, v * 256 + j * 16 + i)) role = 1;
        vput(r, x0 + i, y0 + j, col[role]);
      }
    if (!vp->tree)
      for (int i = 0; i < di->w; i++)
        for (int y = base + 1; y <= r->edge[x0 + i + VILLAGE_DX]; y++) vput(r, x0 + i, y, col[1]);
    if (vp->kind == 1) mast = true, mast_x = x0 + 5, mast_y = y0;
    if (vp->kind == 2) r->chimney = true, r->chimney_x = (int16_t)(x0 + 10), r->chimney_y = (int16_t)y0;
  }
  /* the village's life: smoke from the hearth on an evening in, when the weather is cool (or unknown, out of summer) */
  if ((r->f->events & EV_VILLAGE) && lit && r->chimney && window_lit(r, lit, 2 * 256 + 7 * 16 + 3) &&
      (r->wx ? r->f->weather->temp10 < 160 : season != SEASON_LEAF && season != SEASON_HARVEST))
    r->smoke = true;
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

/* smoke from the chimney on a cold day, the puffs rising and leaning with the wind; fog lying over the hills in three
 * ruled lines, behind the roofs */
static void village_weather(R *r) {
  if (!r->wx && !r->smoke) return;
  const Plate *P = r->P;
  if (r->smoke && r->chimney) {
    float lean = f_sind(r->wind_from) * (r->wind / 12.0f < 1.6f ? r->wind / 12.0f : 1.6f), t = (float)r->secs;
    uint8_t c = r->paper ? P->line : r->night_land ? C8(1, 1, 1) : C8(2, 2, 2);
    for (int h = 1; h <= 8; h++) {
      if ((h + r->secs * 2) % 4 == 0) continue;
      float wob = 0.6f * f_sind((h * 1.3f + t * 1.5f) * 57.2957795f) * (1 - (r->wind / 20 < 1 ? r->wind / 20 : 1));
      int X = pyf_floor(r->col + r->chimney_x + 0.5f - lean * f_pow((float)h, 1.15f) + wob), Y = r->chimney_y - h;
      if (inside(r, X, Y)) put(r, X, Y, c);
    }
  }
  if (r->fog) {
    uint8_t c = r->red ? C8(1, 0, 0) : r->paper ? P->line : r->night_land ? C8(1, 1, 1) : C8(2, 2, 2);
    static const uint8_t FRAC[3] = {46, 40, 30};
    for (int l = 0; l < 3; l++)
      for (int dx = -FRAC[l]; dx <= FRAC[l]; dx++) {
        int e = r->edge[dx + VILLAGE_DX];
        if (e < 0) continue;
        int y = e - 3 - 2 * l;
        if (inside(r, r->col + dx, y) && !((r->vmask[dx + VILLAGE_DX] >> (3 + 2 * l)) & 1)) put(r, r->col + dx, y, c);
      }
  }
}

/* the inverse of the ecliptic's tilt: a place's ecliptic longitude and latitude */
static void eq_to_ecl(float ra, float dec, float eps, float *lon, float *lat) {
  float x = f_cosd(dec) * f_cosd(ra), y = f_cosd(dec) * f_sind(ra), z = f_sind(dec);
  *lon = pyf_mod(f_atan2d(y * f_cosd(eps) + z * f_sind(eps), x), 360);
  *lat = f_asind(-y * f_sind(eps) + z * f_cosd(eps));
}

static bool in_lane(R *r, int x, int y, int x0, int y0) {
  int i = x - x0, j = y - y0;
  return (unsigned)i < 64 && (unsigned)j < 40 && ((r->lane[j] >> i) & 1);
}
static void to_lane(R *r, int x, int y, int x0, int y0) {
  int i = x - x0, j = y - y0;
  if ((unsigned)i < 64 && (unsigned)j < 40) r->lane[j] |= 1ull << i;
}
/* beside Jupiter its four great moons where they are now, along its equator (near enough the ecliptic), magnified
 * (at the chart's scale they would sit inside a pixel), in a narrow lane cleared for them so they read as Jupiter's
 * (a star touching the lane goes whole, not cut) */
static void jupiter_moons(R *r, int xi, int yi, int hw) {
  Sky *k = &r->sky;
  float lon, lat, ra, dec, x0, y0, x1, y1;
  eq_to_ecl(k->pl_ra[JUPITER], k->pl_dec[JUPITER], k->eps, &lon, &lat);
  plan_ecl_to_eq(lon - 0.5f, lat, k->eps, &ra, &dec), project(r, ra, dec, &x0, &y0);
  plan_ecl_to_eq(lon + 0.5f, lat, k->eps, &ra, &dec), project(r, ra, dec, &x1, &y1);
  float ex = x1 - x0, ey = y1 - y0, n = f_sqrt(ex * ex + ey * ey);
  if (n <= 0) n = 1;
  float wx = -ex / n, wy = -ey / n;                 /* west on the screen, at Jupiter */
  int lx = xi - 32, ly = yi - 20;
  memset(r->lane, 0, sizeof r->lane);
  for (int s2 = -26; s2 <= 26; s2++) {
    float d = s2 * 0.5f;
    if (d <= 2.5f && d >= -2.5f) continue;
    for (int q = -1; q <= 1; q++) {
      int cx = pyf_round(xi + d * wx - q * wy), cy = pyf_round(yi + d * wy + q * wx);
      if (on_screen(r, cx, cy)) to_lane(r, cx, cy, lx, ly);
    }
  }
  for (int i = 0; i < r->ndrawn; i++) {
    int sx = r->drawn[i][0], sy = r->drawn[i][1], h = r->drawn[i][2];
    bool touch = false;
    for (int dy = -h; dy <= h && !touch; dy++)
      for (int dx = -h; dx <= h && !touch; dx++) touch = in_lane(r, sx + dx, sy + dy, lx, ly);
    if (touch)
      for (int dy = -h; dy <= h; dy++)
        for (int dx = -h; dx <= h; dx++) to_lane(r, sx + dx, sy + dy, lx, ly);
  }
  for (int j = 0; j < 40; j++)
    for (int i = 0; i < 64; i++) {
      int x = lx + i, y = ly + j;
      if (((r->lane[j] >> i) & 1) && inside(r, x, y) && (x - xi < 0 ? xi - x : x - xi) + (y - yi < 0 ? yi - y : y - yi) > 3)
        put(r, x, y, ground_at(r, x, y));
    }
  float X[4], Y[4];
  bool behind[4];
  plan_galilean(r->utc, X, Y, behind);
  int lo = 0, hi = 0;
  for (int m = 0; m < 4; m++) {
    if (behind[m] || f_abs(X[m]) < 1.0f) continue;
    float d = 3.0f + 1.25f * f_sqrt(f_abs(X[m]));
    if (X[m] < 0) d = -d;
    int mx = pyf_round(xi + d * wx), my = pyf_round(yi + d * wy);
    if (inside(r, mx, my)) {
      put(r, mx, my, r->planet_c[5]);
      if (r->nmoons < 4) r->moonbox[r->nmoons][0] = (int16_t)mx, r->moonbox[r->nmoons][1] = (int16_t)my, r->nmoons++;
      lo = mx - xi < lo ? mx - xi : lo, hi = mx - xi > hi ? mx - xi : hi;
    }
  }
  r->jlo = lo < -hw ? lo : -hw, r->jhi = hi > hw ? hi : hw;
}

/* the Moon in the Earth's shadow: its face red in totality, deepest toward the shadow's middle; or the shadow's bite */
static void moon_in_shadow(R *r, int mi, int mj, float mx, float my, uint8_t lit) {
  float ax, ay;
  project(r, r->sky.sun_ra + 180, -r->sky.sun_dec, &ax, &ay);
  float ux = ax - mx, uy = ay - my, n = f_sqrt(ux * ux + uy * uy);
  if (n <= 0) n = 1;
  ux /= n, uy /= n;
  const DrawIndex *di = drawing(r, D_MOON_FULL);
  bool red = r->red;
  for (int j = 0; j < di->h; j++)
    for (int i = 0; i < di->w; i++) {
      int X = mi - 5 + i, Y = mj - 5 + j;
      if (!role_at(r, di, i, j) || !inside(r, X, Y)) continue;
      float along = ((i - 5) * ux + (j - 5) * uy) / 5.5f;   /* +1 at the limb toward the shadow's middle */
      uint8_t c;
      if (r->lun.kind == ECLIPSE_TOTAL)
        c = along > 0.15f ? (red ? C8(1, 0, 0) : C8(2, 0, 0)) : along < -0.55f ? (red ? C8(2, 0, 0) : C8(3, 1, 0))
                                                                               : (red ? C8(1, 0, 0) : C8(2, 1, 0));
      else c = along > 1 - 2 * r->lun.magnitude ? C8(1, 0, 0) : lit;
      put(r, X, Y, c);
    }
}

/* the Moon's centre on the drawn Sun (5 pixels to the Sun's radius), turned to the chart's east and north */
static void sun_offset(R *r, int si, int sj, float *ox, float *oy) {
  float ra = r->sky.sun_ra, dec = r->sky.sun_dec, e0x, e0y, e1x, e1y, n0x, n0y, n1x, n1y;
  project(r, ra - 0.5f, dec, &e0x, &e0y), project(r, ra + 0.5f, dec, &e1x, &e1y);
  project(r, ra, dec - 0.5f, &n0x, &n0y), project(r, ra, dec + 0.5f, &n1x, &n1y);
  float ex = e1x - e0x, ey = e1y - e0y, nx = n1x - n0x, ny = n1y - n0y;
  float le = f_sqrt(ex * ex + ey * ey), ln = f_sqrt(nx * nx + ny * ny);
  le = le > 0 ? le : 1, ln = ln > 0 ? ln : 1;
  *ox = si + 0.5f + 5.0f * (r->sol.east * ex / le + r->sol.north * nx / ln);
  *oy = sj + 0.5f + 5.0f * (r->sol.east * ey / le + r->sol.north * ny / ln);
}

/* the Moon's disc across the Sun, as seen from here; the ring of fire in an annular eclipse */
static void moon_across(R *r, int si, int sj, float ox, float oy) {
  float rr = 5.3f * r->sol.ratio;
  for (int y = sj - 7; y <= sj + 7; y++)
    for (int x = si - 7; x <= si + 7; x++) {
      if (!inside(r, x, y)) continue;
      float dx = x + 0.5f - ox, dy = y + 0.5f - oy, sx = (float)(x - si), sy = (float)(y - sj);
      bool covered = dx * dx + dy * dy <= rr * rr && sx * sx + sy * sy <= 36;
      if (covered) put(r, x, y, r->red ? C8(0, 0, 0) : C8(0, 0, 1));
      else if (r->sol.kind == ECLIPSE_ANNULAR && f_abs(f_sqrt(sx * sx + sy * sy) - 5.0f) < 0.6f)
        put(r, x, y, r->red ? C8(3, 1, 0) : C8(3, 3, 1));
    }
}

/* totality: the black Moon, a pearly ring at its edge, the corona thinning outward in streamers, red prominences;
 * as totality comes or goes, the diamond ring, the Sun's last point of light at the Moon's edge */
static void corona(R *r, int si, int sj, float ox, float oy) {
  static const int16_t STREAMERS[6] = {12, 78, 148, 196, 262, 318};
  static const int8_t PROM[3][5][2] = {{{0, 0}, {1, 0}, {0, -1}, {9, 9}, {9, 9}}, {{0, 0}, {0, -1}, {1, -1}, {1, -2}, {9, 9}},
                                       {{0, 0}, {-1, 0}, {9, 9}, {9, 9}, {9, 9}}};
  static const int16_t PROM_AT[3] = {55, 170, 295};
  bool total = r->sol.kind == ECLIPSE_TOTAL, red = r->red;
  float strength = total ? 1.0f : f_clamp((r->sol.cover - 0.97f) / 0.03f, 0, 1);
  float cx = si + 0.5f, cy = sj + 0.5f;
  uint8_t pearl = red ? C8(3, 1, 1) : C8(3, 3, 3), mist = red ? C8(2, 0, 0) : C8(2, 3, 3);
  for (int y = sj - 30; y <= sj + 30; y++)
    for (int x = si - 30; x <= si + 30; x++) {
      if (!inside(r, x, y)) continue;
      float dx = x + 0.5f - cx, dy = y + 0.5f - cy, dd = f_sqrt(dx * dx + dy * dy);
      if (dd > 5.4f && dd <= 6.6f) { put(r, x, y, total ? pearl : mist); continue; }
      if (dd <= 6.0f || dd > 29) continue;
      float th = pyf_mod(f_atan2d(dx, -dy), 360), stream = 0;
      for (int i = 0; i < 6; i++) {
        float d = f_abs(pyf_mod(th - STREAMERS[i] + 180, 360) - 180) / 11, e = f_exp(-d * d);
        stream = e > stream ? e : stream;
      }
      float g = f_clamp(1 - (dd - 6.0f) / (8.0f + 15.0f * stream), 0, 1), dens = g * f_sqrt(g) * (0.35f + 0.65f * stream) * strength;
      if (dens > tt(r, x, y)) put(r, x, y, dens > 0.45f && dd < 10 ? pearl : mist);
    }
  float mr = 5.4f * r->sol.ratio;
  for (int y = sj - 8; y <= sj + 8; y++)
    for (int x = si - 8; x <= si + 8; x++) {
      float dx = x + 0.5f - ox, dy = y + 0.5f - oy;
      if (dx * dx + dy * dy <= mr * mr && inside(r, x, y)) put(r, x, y, C8(0, 0, 0));
    }
  if (total)
    for (int k = 0; k < 3; k++) {
      int bx = pyf_floor(cx + 5.9f * f_sind(PROM_AT[k])), by = pyf_floor(cy - 5.9f * f_cosd(PROM_AT[k]));
      for (int i = 0; i < 5 && PROM[k][i][0] != 9; i++)
        if (inside(r, bx + PROM[k][i][0], by + PROM[k][i][1])) put(r, bx + PROM[k][i][0], by + PROM[k][i][1], red ? C8(3, 0, 0) : C8(3, 1, 1));
    }
  else {                                             /* the diamond: the last of the Sun, opposite the Moon's middle */
    float vx = ox - cx, vy = oy - cy, n = f_sqrt(vx * vx + vy * vy);
    if (n <= 0) n = 1;
    uint8_t col[8] = {0, 0, 0, 0, 0, red ? C8(3, 1, 1) : C8(3, 3, 3)};
    paint(r, D_DIAMOND, pyf_floor(cx - 5.6f * vx / n), pyf_floor(cy - 5.6f * vy / n), col, true);
  }
}

/* ---- what a feast marks in the sky (proto/feast_draw.py) ----------------------------------------------------- */
static bool feast_marks(R *r, int sky) {
  Plan *p = r->p;
  return p->feast && p->feast_day == r->local.ordinal && p->feast_sky == sky;
}
static void mark(R *r, int x, int y, uint8_t c) {
  put(r, x, y, c);
  if (r->nmarks < 24) r->marks[r->nmarks][0] = (int16_t)x, r->marks[r->nmarks][1] = (int16_t)y, r->nmarks++;
}
static bool pixel_blocked(R *r, int x, int y) {
  int16_t b[4] = {(int16_t)x, (int16_t)y, (int16_t)(x + 1), (int16_t)(y + 1)};
  return blocked(r, b);
}
/* the magpies' bridge between the Weaver and the Cowherd: a gentle arc of small birds, five pixels apart */
static __attribute__((noinline)) bool near5(float x, float y, float ax, float ay) {
  return (x - ax) * (x - ax) + (y - ay) * (y - ay) < 25;
}
static __attribute__((noinline)) float arc_at(float a, float c, float b, float t) {   /* the arc's quadratic Bezier */
  float u = 1 - t;
  return u * u * a + 2 * u * t * c + t * t * b;
}
static void bridge(R *r, float ax, float ay, float bx, float by, uint8_t colour) {
  float dx = bx - ax, dy = by - ay, L = f_sqrt(dx * dx + dy * dy);
  if (L < 16) return;
  float mx = (ax + bx) / 2, my = (ay + by) / 2, nx = -dy / L, ny = dx / L;
  if ((r->cx - mx) * nx + (r->cy - my) * ny < 0) nx = -nx, ny = -ny;
  float cx = mx + nx * 0.22f * L, cy = my + ny * 0.22f * L, lx = ax, ly = ay;   /* (the last bird: none yet) */
  int steps = (int)(L * 2);
  for (int k = 0; k <= steps; k++) {
    float t = (float)k / (float)steps, x = arc_at(ax, cx, bx, t), y = arc_at(ay, cy, by, t);
    if (near5(x, y, ax, ay) || near5(x, y, bx, by) || near5(x, y, lx, ly)) continue;
    int px = pyf_floor(x), py = pyf_floor(y);
    bool ok = true;
    for (int q = -1; q <= 1 && ok; q++) ok = inside(r, px + q, py - (q != 0)) && !pixel_blocked(r, px + q, py - (q != 0));
    if (!ok) continue;
    lx = x, ly = y;
    for (int q = -1; q <= 1; q++) mark(r, px + q, py - (q != 0), colour);
  }
}

/* a feast's marks, before the names: Christmas Eve's first star (from dusk) with its glint; on Qixi the bridge */
static void feast_sky(R *r) {
  Plan *p = r->p;
  const uint8_t *sn = sec(p->data, SEC_STAR_NAMES);
  r->nmarks = 0, r->first = 0;
  r->weaver = feast_marks(r, FS_WEAVER) && (r->dark || r->paper);
  int i = p->feast_first;
  if (feast_marks(r, FS_FIRST_STAR) && i && r->sun_alt < -4 && r->local.hour >= 12) {
    float ra = i < 0 ? r->sky.pl_ra[-1 - i] : star_ra(sn + 20 * (i - 1));
    float dec = i < 0 ? r->sky.pl_dec[-1 - i] : star_dec(sn + 20 * (i - 1)), x, y;
    if (altitude(r, ra, dec) > 2) {
      r->first = (int8_t)i;
      project(r, ra, dec, &x, &y);
      int gx = pyf_floor(x), gy = pyf_floor(y);
      static const int8_t D4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
      for (int d = 0; d < 4; d++)
        for (int rr = 4; rr <= 5; rr++)
          if (inside(r, gx + D4[d][0] * rr, gy + D4[d][1] * rr))
            mark(r, gx + D4[d][0] * rr, gy + D4[d][1] * rr, r->paper ? r->P->accent : C8(3, 3, 1));
    }
  }
  if (r->weaver) {
    const uint8_t *a = sn + 20 * STAR_WEAVER, *b = sn + 20 * STAR_COWHERD;
    if (altitude(r, star_ra(a), star_dec(a)) < 5 || altitude(r, star_ra(b), star_dec(b)) < 5) return;
    float e[4];
    project_star(r, a, &e[0], &e[1]);
    project_star(r, b, &e[2], &e[3]);
    bridge(r, e[0], e[1], e[2], e[3], r->paper ? r->P->ink : C8(3, 3, 3));
  }
}

/* a named star's name on the feast's evening: the first star's own, the Weaver's or the Cowherd's (NULL: none) */
static const char *feast_name(R *r, int i) {
  if (r->first == i + 1) return (const char *)sec(r->p->data, SEC_STAR_NAMES) + 20 * i + 4;
  return !r->weaver ? NULL : i == STAR_WEAVER ? "Weaver" : i == STAR_COWHERD ? "Cowherd" : NULL;
}

static __attribute__((noinline)) void names(R *r, float mx, float my) {
  const Plate *P = r->P;
  Sky *k = &r->sky;
  const uint8_t *sn = sec(r->p->data, SEC_STAR_NAMES);
  for (int i = 0; i < STAR_NAME_COUNT; i++) {            /* the feast's names before all others */
    const uint8_t *s = sn + 20 * i;
    const char *say = feast_name(r, i);
    if (!say || altitude(r, star_ra(s), star_dec(s)) < 5) continue;
    float x, y;
    project_star(r, s, &x, &y);
    pixel_text(&r->t1, r, say, true, 0);
    place(r, &r->t1, pyf_floor(x) + 1, pyf_floor(y), r->first == i + 1 ? P->accent : P->label, false, 0, 0, true);
  }
  if (altitude(r, k->moon_ra, k->moon_dec) > 0) {
    pixel_text(&r->t1, r, "Moon", false, 0);
    place(r, &r->t1, pyf_floor(mx), pyf_floor(my), P->planet, false, -3, 3, true);
  }
  for (int pn = 0; pn < PLANETS; pn++) {
    if ((!r->paper && r->s_eff > -3) || altitude(r, k->pl_ra[pn], k->pl_dec[pn]) <= 2) continue;
    float x, y;
    project(r, k->pl_ra[pn], k->pl_dec[pn], &x, &y);
    int hw = drawing(r, PLANET_DRAWINGS[pn])->w / 2, lo = -hw, hi = hw;
    if (pn == JUPITER) lo = r->jlo, hi = r->jhi;
    pixel_text(&r->t1, r, PLANET_NAMES[pn], false, 0);
    place(r, &r->t1, pyf_floor(x), pyf_floor(y), r->first == -1 - pn ? P->accent : P->planet, false, lo + 1, hi - 2,
          true);
  }
  if (!(r->dark || r->paper)) return;
  int shown = 0;
  for (int i = 0; i < STAR_NAME_COUNT && shown < 3; i++) {
    const uint8_t *s = sn + 20 * i;
    if (feast_name(r, i) || altitude(r, star_ra(s), star_dec(s)) < 8) continue;
    float x, y;
    project_star(r, s, &x, &y);
    pixel_text(&r->t1, r, (const char *)s + 4, true, 0);
    if (place(r, &r->t1, pyf_floor(x) + 1, pyf_floor(y), P->label, false, 0, 0, true)) shown++;
  }
  const uint8_t *cn = sec(r->p->data, SEC_CONSTELLATIONS);
  shown = 0;
  for (int i = 0; i < CONSTELLATION_COUNT && shown < 3; i++) {
    const uint8_t *s = cn + 20 * i;
    if (altitude(r, star_ra(s), star_dec(s)) < 12) continue;
    float x, y;
    project_star(r, s, &x, &y);
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
        project_star(r, s, &x, &y);
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
    float om = plan_moon_node(r->utc);
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
static bool near_window(R *r, int x, int y) {   /* (a diamond of radius 2: each row's run against the window's span) */
  const Plan *p = r->p;
  for (int dy = -2; dy <= 2; dy++) {
    int yy = y + dy, w = 2 - (dy < 0 ? -dy : dy);
    if ((unsigned)yy >= (unsigned)r->H || p->wx0[yy] > p->wx1[yy]) continue;
    if (p->wx0[yy] <= x + w && p->wx1[yy] >= x - w) return true;
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
    bool has = (unsigned)y < (unsigned)r->H && p->wx0[y] <= p->wx1[y];   /* (the row's own span: skipped whole) */
    for (int x = lo - 3; x <= hi + 3; x++) {
      if (has && x == p->wx0[y]) { x = p->wx1[y]; continue; }
      if (x < 0 || x >= r->W) continue;
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
  r->fl_x0 = (int16_t)fx0, r->fl_y0 = (int16_t)fy0, r->fl_w = di->w, r->fl_h = di->h;
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

/* a name's next form from its ladder ("|" between) into `form`; its length (0: none left) */
static int next_form(const char **t, char form[40]) {
  int k = 0;
  while (**t && **t != '|') { if (k < 39) form[k++] = **t; (*t)++; }
  form[k] = 0;
  if (**t == '|') (*t)++;
  return k;
}

/* the window's top in a column (or with `bottom` its foot): its first (last) row there, or -1 */
static int window_top(R *r, int x, bool bottom) {
  Plan *p = r->p;
  for (int k = 0; p->win_top >= 0 && k <= p->win_bottom - p->win_top; k++) {
    int y = bottom ? p->win_bottom - k : p->win_top + k;
    if (x >= p->wx0[y] && x <= p->wx1[y]) return y;
  }
  return -1;
}

/* v / d (d > 0) rounded as Python rounds, halves to the even */
static int round_div(int v, int d) {
  int q = v >= 0 ? v / d : -((d - 1 - v) / d), rem = v - q * d;
  return rem * 2 > d || (rem * 2 == d && (q & 1)) ? q + 1 : q;
}

/* a form engraved letter by letter across `span` pixels from x0 (in 1/32 px), the letters spread evenly to fill it
 * (a pixel apart when span is its own width): each letter's middle on the band's curve `cy` (1/16 px a column), or
 * with cy NULL its foot four pixels above the window's top under it (the higher of the tops under its two edges: clear
 * of the window's rims), as the fleur-de-lis stands. With `draw` false, only whether every letter beside the fleur
 * falls inside the ring's inner edge by two. (Integers: positions are 32nds exactly.) */
static bool engrave(R *r, const char *form, int x0, int span, const int16_t *cy, uint8_t c, bool draw, bool below) {
  const int16_t *inner = sec16(r->p->geom, GEO_INNER);
  int n = 0, ink = tiny_width(r, form);
  for (const char *s = form; *s; s++) n += *s == ' ' || tiny_mask(*s) >= 0;
  int gap = n > 1 ? 32 + (span - ink) * 32 / (n - 1) : 32, gx = n > 1 ? x0 : x0 + (span - ink) * 16;
  for (const char *s = form; *s; s++) {
    int m = tiny_mask(*s), gw = *s == ' ' ? 3 : m < 0 ? -1 : mask(r, m)->w, xl, y0;
    if (gw < 0) continue;
    xl = round_div(gx, 32);
    if (cy) {
      int xc = gx + gw * 16, xi = xc >> 5, f = xc & 31;
      if (xi < 0) xi = 0, f = 0;
      if (xi >= r->W - 1) xi = r->W - 2, f = 32;
      y0 = round_div(cy[xi] * (32 - f) + cy[xi + 1] * f - 1280, 512);   /* (its middle 2.5 below its top) */
    } else {                                     /* clear of the window's rims under its two edges */
      int xr = xl + gw - 1, tl = window_top(r, xl, below), tr = window_top(r, xr, below);
      if (tl < 0 || tr < 0) return false;
      y0 = below ? (tl > tr ? tl : tr) + 4 : (tl < tr ? tl : tr) - 8;
      for (int y = y0; y <= y0 + 4; y += 4)      /* (the band's inner edge convex: its top and foot rows enough) */
        if (y < 0 || xl < inner[2 * y] + 2 || xr > inner[2 * y + 1] - 2) return false;
    }
    if (draw && *s != ' ') mask_put(r, m, xl, y0, c, false, false);
    gx += gw * 32 + gap;
  }
  return true;
}

/* the tide's next high and low waters (an option, Face.tide_times), as tide tables mark them (a triangle up for high water,
 * down for low, after the Dymaxion face), in the ring's smallest figures: on the Time 2 beneath the window, either side
 * of the south star, following the window's foot, as near the star as they fit on the card, each the same way out; on
 * the Round 2, whose window meets its band below, in the band beside NOON in the coordinates' place */
static int hour_of(int h, bool clock24);
/* the tide's next high (text[0]) and low (text[1]) as the marks read: a triangle and the time; false if neither */
static bool tide_texts(R *r, char text[2][12]) {
  const Tides *td = r->f->tide_times ? r->f->tides : NULL;
  text[0][0] = text[1][0] = 0;
  for (int k = 0; td && k < td->n; k++) {
    int64_t at = (int64_t)(td->at[k] & ~TIDE_HIGH) * 60;
    int s = td->at[k] & TIDE_HIGH ? 0 : 1;
    if (at <= r->utc || text[s][0]) continue;
    Civil c;
    plan_civil(at + r->offset, &c);
    char *q = text[s];
    *q++ = (char)(s ? '\x03' : '\x02');
    number(q, hour_of(c.hour, r->clock24), 1);
    q += strlen(q);
    *q++ = ':', *q++ = (char)('0' + c.minute / 10), *q++ = (char)('0' + c.minute % 10), *q = 0;
  }
  return text[0][0] || text[1][0];
}
static void tide_marks(R *r) {
  char text[2][12];
  if (!r->rect || !tide_texts(r, text)) return;  /* (the Round 2's window meets its band below: the marks by NOON) */
  int w[2] = {tiny_width(r, text[0]), tiny_width(r, text[1])};
  for (int off = 6; off < 70; off++) {           /* (as near the star as both fit) */
    bool ok = true;
    for (int s = 0; s < 2 && ok; s++)
      ok = !text[s][0] || engrave(r, text[s], 32 * (s ? r->col + off : r->col - off - w[s]), w[s], NULL, 0, false, true);
    if (!ok) continue;
    for (int s = 0; s < 2; s++)
      if (text[s][0]) engrave(r, text[s], 32 * (s ? r->col + off : r->col - off - w[s]), w[s], NULL, r->P->ink, true, true);
    return;
  }
}

/* the place on the ring: city and country (or state) either side of MIDNIGHT, latitude and longitude either side of
 * NOON, in small capitals following the band's curve, each centred in the room there: of a name's forms (a ladder,
 * longest first, "|" between: proto/names.py) the longest that fits. When the city or its region has no room in the
 * band, both stand either side of the fleur-de-lis instead, along the window's top, five pixels from it, each the
 * longest form whose letters all fall on the card there, the two spread to the same width (the longer's), in the
 * card's ink. */
/* the battery's candle (proto/plates.py candle), an option: standing in the card's lower right, on the lowest row
 * where its five columns lie three clear of the ring's inner rule and of the window for its twelve rows; a saucer,
 * the wax at its full seven rows in the card's faint tone, inked from the base as far as the charge (a row a
 * seventh), the wick on the wax and the flame above it, gold, red when a fifth or less is left; charging, the flame a
 * pixel taller */
static void candle(R *r) {
  const Face *f = r->f;
  Plan *p = r->p;
  if (!f->candle || f->battery > 100) return;
  const int16_t *inner = sec16(p->geom, GEO_INNER);
  int base = -1, x0 = 0;
  for (int y = p->win_bottom; y >= 12 && base < 0; y--) {
    if (y >= r->H) continue;
    int lim = r->W;
    bool ok = true;
    for (int yy = y - 11; yy <= y && ok; yy++) {
      if (inner[2 * yy] > inner[2 * yy + 1]) { ok = false; break; }
      if (inner[2 * yy + 1] - 3 < lim) lim = inner[2 * yy + 1] - 3;
      if (p->wx0[yy] <= p->wx1[yy] && lim - 5 <= p->wx1[yy] + 3) ok = false;
    }
    if (ok) base = y, x0 = lim - 5;
  }
  if (base < 0) return;
  int pct = f->battery, n = pct ? (pct * 7 + 50) / 100 : 0;
  if (pct && n < 1) n = 1;
  uint8_t ink = r->P->ink, flame = pct <= 20 ? r->P->accent : r->P->planet;
  for (int i = 0; i < 5; i++) put(r, x0 + i, base, ink);
  for (int j = 0; j < 7; j++) {
    int y = base - 7 + j;
    bool lit = j >= 7 - n;
    for (int i = 1; i <= 3; i++)
      if (lit) put(r, x0 + i, y, ink);
      else if (i != 2 || j == 0) put(r, x0 + i, y, r->tint);
  }
  if (!n) return;
  put(r, x0 + 2, base - n - 1, ink);
  for (int k = 2; k <= (f->charging ? 4 : 3); k++) put(r, x0 + 2, base - n - k, flame);
}

static void inscriptions(R *r, int style) {
  char dms[2][16], form[40], pick[2][40];
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
  char tides[2][12];
  if (!r->rect && tide_texts(r, tides)) texts[2] = tides[0], texts[3] = tides[1];
  (void)style;
  const int16_t *curves = sec16(r->p->geom, GEO_CURVES);
  bool by_fleur = false;
  for (int slot = 0; slot < 2; slot++) {          /* the city or its region too long for the band? */
    const char *t = texts[slot];
    bool fits = !t || !*t;
    while (t && !fits && next_form(&t, form))
      fits = tiny_width(r, form) * 16 <= r->p->ins_hi[slot] - r->p->ins_lo[slot];
    by_fleur |= !fits;
  }
  if (by_fleur) {                                 /* beside the fleur-de-lis, at the longer's width */
    int span = 0;
    for (int slot = 0; slot < 2; slot++) {
      const char *t = texts[slot];
      pick[slot][0] = 0;
      while (t && next_form(&t, form)) {
        int w = tiny_width(r, form);
        if (engrave(r, form, 32 * (slot ? r->fl_x0 + r->fl_w + 5 : r->fl_x0 - 5 - w), w, NULL, 0, false, false)) {
          memcpy(pick[slot], form, sizeof form);
          if (w > span) span = w;
          break;
        }
      }
    }
    for (int slot = 0; slot < 2; slot++)
      if (pick[slot][0])
        engrave(r, pick[slot], 32 * (slot ? r->fl_x0 + r->fl_w + 5 : r->fl_x0 - 5 - span), span, NULL, r->P->ink, true, false);
  }
  for (int slot = by_fleur ? 2 : 0; slot < 4; slot++) {
    const char *t = texts[slot];
    int lo = r->p->ins_lo[slot], hi = r->p->ins_hi[slot], width = 0;   /* (1/16 px) */
    bool ok = false;
    while (t && !ok && next_form(&t, form)) ok = (width = tiny_width(r, form)) * 16 <= hi - lo;
    if (ok) engrave(r, form, lo + hi - width * 16, width, curves + (slot < 2 ? 0 : r->W), r->P->ring_ink, true, false);
  }
  tide_marks(r);
  candle(r);
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
    cpos[i] = c >= 0, c2[i] = (int32_t)(c * c * 65536);
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
  /* the Time 2's corners: a sprig in each, in the season's dress (unless the month's tools are there) */
  if (r->rect && !r->f->corners) {               /* (a theme's corner pieces drawn with the scene: Face.decor) */
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
    HandMask *hm = (HandMask *)(void *)&r->t1;    /* (a line of type holds the hand's mask: none is set while the
                                                     ring is drawn, after the names and before the time) */
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

/* ---- the sky's news (proto/events.py news) ----------------------------------------------------------------- */
/* the day's news (the night that belongs to this day, noon to noon): an eclipse first, then planets meeting, then a
 * meteor shower's peak, then the Moon by a planet; kept until the day or the place changes */
static void day_news(R *r) {
  Plan *p = r->p;
  int32_t day = r->local.ordinal - (r->local.hour < 12 ? 1 : 0);
  if (p->news_day == day && p->news_lat == r->f->lat && p->news_lon == r->f->lon) return;
  p->news_day = day, p->news_lat = r->f->lat, p->news_lon = r->f->lon, p->news = NEWS_NONE;
  int64_t start = (int64_t)(day - 719163) * 86400 + 12 * 3600 - r->offset;     /* the day's local noon */
  float lat = r->f->lat, lon = r->f->lon;
  Sky s;
  /* an eclipse needs the Moon near the Sun or opposite it: look through the day only then */
  plan_sun_moon(&s, start + 12 * 3600, lon);
  float el = plan_separation(s.moon_ra, s.moon_dec, s.sun_ra, s.sun_dec);
  bool scan = el < 30 || el > 150;
  int found = -1, body = 0, pa = -1, pb = -1, ma = -1;
  static const uint8_t ORDER[PLANETS] = {MERCURY, VENUS, MARS, JUPITER, SATURN};   /* the prototype's order */
  for (int k = 0; k < 24 * 6; k++) {
    int64_t u = start + (int64_t)k * 600;
    if (scan) {
      Eclipse e;
      plan_sun_moon(&s, u, lon);
      int b = plan_lunar(&s, lat, &e) ? 2 : plan_solar(&s, lat, &e) ? 1 : 0;
      if (b && (found < 0 || e.kind > found)) found = e.kind, body = b;
    }
    if (k % 6 == 0) {                            /* hourly: planets meeting in a dark sky, the nearest pair first */
      plan_sky(&s, u, lon);
      if (plan_altitude(s.sun_ra, s.sun_dec, s.lst, lat) >= -6) continue;
      float best_p = 99, best_m = 99;
      int bp_a = -1, bp_b = -1, bm = -1;
      for (int i = -1; i < PLANETS; i++)
        for (int j = i + 1; j < PLANETS; j++) {
          float ra1 = i < 0 ? s.moon_ra : s.pl_ra[ORDER[i]], de1 = i < 0 ? s.moon_dec : s.pl_dec[ORDER[i]];
          float ra2 = s.pl_ra[ORDER[j]], de2 = s.pl_dec[ORDER[j]], sep = plan_separation(ra1, de1, ra2, de2);
          if (sep >= (i < 0 ? 1.6f : 2.0f) || plan_altitude(ra1, de1, s.lst, lat) <= 3 || plan_altitude(ra2, de2, s.lst, lat) <= 3)
            continue;
          if (i < 0 && sep < best_m) best_m = sep, bm = ORDER[j];
          if (i >= 0 && sep < best_p) best_p = sep, bp_a = ORDER[i], bp_b = ORDER[j];
        }
      if (pa < 0 && bp_a >= 0) pa = bp_a, pb = bp_b;
      if (ma < 0 && bm >= 0) ma = bm;
    }
  }
  plan_sun_moon(&s, start + 12 * 3600, lon);
  int sh = plan_shower(s.sun_lon);
  if (found >= 0) p->news = body == 1 ? NEWS_SUN : NEWS_MOON, p->news_a = (uint8_t)found;
  else if (pa >= 0) p->news = NEWS_PLANETS, p->news_a = (uint8_t)pa, p->news_b = (uint8_t)pb;
  else if (sh >= 0) p->news = NEWS_SHOWER, p->news_a = (uint8_t)sh;
  else if (ma >= 0) p->news = NEWS_MOON_BY, p->news_a = (uint8_t)ma;
}

static void upper(char *d, const char *s) {
  for (; *s; s++) *d++ = (char)(*s >= 'a' && *s <= 'z' ? *s - 32 : *s);
  *d = 0;
}
/* the news's wordings, the longest first: wording `w` (0, 1) into `out`; false past the last */
static bool news_wording(R *r, int w, char *out) {
  Plan *p = r->p;
  static const char *const SUN[3][2] = {{"ECLIPSE OF THE SUN", "SUN ECLIPSED"}, {"ANNULAR ECLIPSE", "RING OF FIRE"},
                                        {"TOTAL ECLIPSE OF THE SUN", "TOTAL ECLIPSE"}};
  static const char *const MOON[3][2] = {{"ECLIPSE OF THE MOON", "MOON ECLIPSED"}, {"ECLIPSE OF THE MOON", "MOON ECLIPSED"},
                                         {"TOTAL ECLIPSE OF THE MOON", "BLOOD MOON"}};
  char a[16], b[16];
  out[0] = 0;
  if (r->totality) {
    if (w) return false;
    strcpy(out, "TOTALITY");
    return true;
  }
  if (w > 1) return false;
  /* a feast day names itself, a red-letter day, unless an eclipse is the news */
  if (p->feast && p->feast_day == r->local.ordinal && p->news != NEWS_SUN && p->news != NEWS_MOON) {
    if (w && !strcmp(p->feast_words[1], p->feast_words[0])) return false;
    strcpy(out, p->feast_words[w]);
    return true;
  }
  switch (p->news) {
  case NEWS_SUN: strcpy(out, SUN[p->news_a][w]); return true;
  case NEWS_MOON: strcpy(out, MOON[p->news_a][w]); return true;
  case NEWS_PLANETS:
    upper(a, PLANET_NAMES[p->news_a]), upper(b, PLANET_NAMES[p->news_b]);
    strcpy(out, a), strcat(out, w ? " & " : " MEETS "), strcat(out, b);
    return true;
  case NEWS_SHOWER:
    upper(out, SHOWERS[p->news_a].name);
    if (!w) strcat(out, " PEAK");
    return true;
  case NEWS_MOON_BY:
    upper(b, PLANET_NAMES[p->news_a]);
    strcpy(out, w ? "MOON BY " : "THE MOON BY "), strcat(out, b);
    return true;
  }
  return false;
}

/* the large time in the plate's own figures, its top-left at (x0, y0) (only measured unless `draw`): its width; when
 * the time is gilt (Face.gild), the figures (not the small h and m) first outlined a pixel round in the plate's gilding */
/* the time's figures as drawn: each (0..9, 10 h, 11 m) and its top-left corner */
typedef struct { int n; int8_t c[8]; int16_t x[8], y[8]; } Glyphs;
static inline __attribute__((always_inline)) int compose(R *r, int style, int screen, int hour, int minute, int *asc_out,
                                                          int *small_out, bool draw, int x0, int y0, Glyphs *pos) {
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
  if (!draw && !pos) return W;
  if (pos) pos->n = 0;
  for (int pass = draw && r->f->gild ? 0 : 1; pass < 2; pass++) {   /* (the gilding under all the figures, then ink) */
    int x = 0;
    for (int i = 0; i < n; i++) {
      int c = parts[i];
      if (c < 0) { x += 5 + 2; continue; }
      const FigureIndex *g = fi + c;
      int top = c <= 9 ? asc - g->base : asc - small;
      if (pos && pass) pos->c[pos->n] = (int8_t)c, pos->x[pos->n] = (int16_t)(x0 + x), pos->y[pos->n] = (int16_t)(y0 + top), pos->n++;
      if (draw && (pass || c <= 9))
        for (int j = 0; j < g->h; j++)
          for (int i2 = 0; i2 < g->w; i2++) {
            uint32_t b = g->bit + (uint32_t)(j * g->w + i2);
            if (!((bits[b >> 3] >> (b & 7)) & 1)) continue;
            int X = x0 + x + i2, Y = y0 + top + j;
            if (pass) put(r, X, Y, r->P->ink);
            else
              for (int d = 0; d < 9; d++) put(r, X + d % 3 - 1, Y + d / 3 - 1, r->P->gild);
          }
      x += g->w + (c == 10 ? 1 : 2);
    }
  }
  return W;
}

/* ---- the minute written: the figures that changed since the last drawing, their pixels and the colour under each
 * kept before they are drawn, for the motion blob to put in a scribe's order and unveil (plan_show.c plan_scribe) -- */
static void scribe_record(R *r, const Glyphs *gl, int style, int screen, int hour, int minute, void *(*alloc)(size_t)) {
  Plan *p = r->p;
  int st = style * 2 + screen, total = 0;
  uint8_t changed = 0;                               /* (a bit a figure) */
  if (!r->f->scribe) return;
  /* a figure is written again when its value changed: each against the one in its place last time, counted from the
   * end (the minutes' units, their tens, the hour's figures); one only moved over (the time is centred) is not */
  if (p->time_n > 0 && p->time_style == st && (p->time_hour != hour || p->time_minute != minute))
    for (int g = 0; g < gl->n; g++) {
      int k = p->time_n - (gl->n - g);
      if (k < 0 || p->time_c[k] != gl->c[g]) changed |= (uint8_t)(1 << g);
    }
  p->time_n = (int8_t)gl->n, p->time_style = (int8_t)st, p->time_hour = (int16_t)hour, p->time_minute = (int16_t)minute;
  for (int g = 0; g < gl->n; g++) p->time_c[g] = gl->c[g], p->time_x[g] = gl->x[g], p->time_y[g] = gl->y[g];
  const FigureIndex *fi = (const FigureIndex *)(const void *)sec(p->data, SEC_FIGURE_INDEX) + st * 12;
  const uint8_t *bits = sec(p->data, SEC_FIGURE_DATA);
  uint32_t *out = NULL;
  for (int pass = 0; pass < 2 && changed; pass++) {  /* (counted, then kept) */
    int n = 0;
    for (int g = 0; g < gl->n; g++) {
      const FigureIndex *f = &fi[gl->c[g]];
      for (int k = 0; (changed >> g & 1) && k < f->w * f->h; k++) {
        int x = gl->x[g] + k % f->w, y = gl->y[g] + k / f->w;
        uint32_t b = f->bit + (uint32_t)k;
        if (!((bits[b >> 3] >> (b & 7)) & 1) || !on_screen(r, x, y)) continue;
        if (out) out[n] = (uint32_t)x | (uint32_t)y << 9 | (uint32_t)(get(r, x, y) & 63) << 18 | (uint32_t)g << 24;
        n++;
      }
    }
    if (!pass && !(total = n, out = n ? alloc((size_t)n * 4) : NULL)) return;
  }
  if (!out) return;
  p->scribe = out, p->scribe_n = (uint16_t)total, p->scribe_ink = r->P->ink, p->scribe_lines = 0xFFFF;
}

static int hour_of(int h, bool clock24) { return clock24 ? h : (h % 12 ? h % 12 : 12); }

/* the time as an astronomer writes it, the needlework either side, the date, the almanac's line */
/* the almanac's searches, kept in the Plan until they lapse: the Sun's next rising or setting, and the day's news.
 * Called at the top of the drawing, where the stack is shallowest: they go deep. */
static __attribute__((noinline)) void almanac(R *r) {
  Plan *p = r->p;
  if (p->ev_kind < 0 || r->utc < p->ev_from || r->utc >= p->ev_at || p->ev_lat != r->f->lat || p->ev_lon != r->f->lon) {
    p->ev_kind = plan_sun_event(r->utc, r->f->lat, r->f->lon, &p->ev_at);
    if (!p->ev_kind) p->ev_at = r->utc + 3600;     /* the Sun neither rises nor sets today: look again in an hour */
    p->ev_from = r->utc, p->ev_lat = r->f->lat, p->ev_lon = r->f->lon;
  }
  day_news(r);
}

/* (each of the long layers in a frame of its own, not in plan_render's: the stack is 2 KB) */
static __attribute__((noinline)) void time_block(R *r, int fy0, int season, void *(*alloc)(size_t),
                                                 void (*release)(void *)) {
  const Plate *P = r->P;
  Plan *p = r->p;
  float ring_in = r->rect ? 17.0f : r->cy - (r->p->R - 18.0f);
  float span = (fy0 - 1) - ring_in;
  int screen = r->rect ? 0 : 1;
  int hour = hour_of(r->local.hour, r->clock24);
  int asc, small;
  Glyphs gl;                                         /* (the figures that changed kept for the scribe, then drawn) */
  int Wt = compose(r, P->figures, screen, hour, r->local.minute, &asc, &small, false, 0, 0, &gl);
  float cy_ = ring_in + span * 0.345f;
  int tx = pyf_round(r->cx - Wt / 2.0f), ty = pyf_round(cy_ - (asc - small / 2.0f));
  for (int g = 0; g < gl.n; g++) gl.x[g] = (int16_t)(gl.x[g] + tx), gl.y[g] = (int16_t)(gl.y[g] + ty);
  scribe_record(r, &gl, P->figures, screen, hour, r->local.minute, alloc);
  compose(r, P->figures, screen, hour, r->local.minute, NULL, NULL, true, tx, ty, NULL);
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
  bool art = p->feast && p->feast_day == r->local.ordinal && p->feast_art_w;   /* the feast's emblem first */
  for (int i = art ? -1 : 0; i < no; i++) {
    int m = i < 0 ? 0 : M_NEEDLE_LOZENGE + order[i];
    const MaskIndex *mi = i < 0 ? NULL : mask(r, m);
    int h = mi ? mi->h : p->feast_art_h, w = mi ? mi->w : p->feast_art_w, lo = -1, hi = 1 << 20;
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
    if (mi) {
      mask_put(r, m, x0, y0, P->accent, false, false);
      mask_put(r, m, r->W - x0 - w, y0, P->accent, false, true);
    } else
      for (int j = 0; j < h; j++)
        for (int k = 0; k < w; k++)
          if (p->feast_art[(j * w + k) >> 3] >> ((j * w + k) & 7) & 1) {
            if (on_screen(r, x0 + k, y0 + j)) put(r, x0 + k, y0 + j, P->accent);
            if (on_screen(r, r->W - x0 - w + (w - 1 - k), y0 + j)) put(r, r->W - x0 - w + (w - 1 - k), y0 + j, P->accent);
          }
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
  /* (a great feast's date in red, as the calendars rubricate their principal days: a red-letter day) */
  stamp(r, &r->t1, left + ds->w + 4, y_date, feast_brings(r, FF_RED) ? P->accent : P->ink, false, false, 1);
  /* the almanac's line: the sky's news (its wordings, the longest first), or else the Sun's next rising or setting;
   * with the weather, each with the temperature after a lozenge, then each alone, then the temperature alone */
  r->totality = (r->have_sol && r->sol.kind == ECLIPSE_TOTAL) || (r->have_lun && r->lun.kind == ECLIPSE_TOTAL);
  float room = (r->W - 2 * ring_in) * 0.84f;
  Text *line = &r->t1, *temp = &r->t2, *tmp = &r->t3;   /* (with the weather, the line takes it on in place) */
  char words[2][40];
  int nw = 0;
  while (nw < 2 && news_wording(r, nw, words[nw])) nw++;
  bool weather = r->f->weather != NULL;
  if (weather) {
    float cel = r->f->weather->temp10 / 10.0f;
    temp_text(temp, r, pyf_round(r->f->fahrenheit ? cel * 9 / 5 + 32 : cel));
  }
  int lines = nw ? nw : p->ev_kind ? 1 : 0, ncand = lines * (weather ? 2 : 1) + (weather ? 1 : 0);
  const Text *fits = NULL;
  for (int c = 0; c < ncand && !fits; c++) {
    if (weather && c == ncand - 1) { if (temp->w <= room) fits = temp; break; }
    int which = c % lines;
    if (nw) pixel_text(line, r, words[which], false, 0);
    else {
      Civil ev;
      plan_civil(p->ev_at + r->offset, &ev);
      pixel_text(line, r, p->ev_kind == 1 ? "SUNRISE" : "SUNSET", false, 0);
      time_text(tmp, r, hour_of(ev.hour, r->clock24), ev.minute);
      t_append(line, tmp, 3);
    }
    if (weather && c < lines) {
      t_clear(tmp);
      t_mask(tmp, r, M_LOZENGE_MASK, 0, 2);
      tmp->w = mask(r, M_LOZENGE_MASK)->w;
      t_append(line, tmp, 3);
      t_append(line, temp, 3);
      if (line->w <= room) fits = line;
    } else if (line->w <= room)
      fits = line;
  }
  if (fits) stamp(r, fits, r->cx, ring_in + span * 0.915f, P->accent, false, false, 0);
}

/* the Moon's phase among eight, new first, as the sea's corner draws it (lit on the right as it waxes; in the south,
 * where it is seen the other way up, mirrored) */
static uint8_t moon_phase8(const R *r) {
  float f = r->sky.moon_phase;
  int k = f < 0.06f ? 0 : f > 0.94f ? 4 : r->sky.moon_waxing ? (f < 0.35f ? 1 : f < 0.65f ? 2 : 3)
                                                              : (f > 0.65f ? 5 : f > 0.35f ? 6 : 7);
  return (uint8_t)(r->south ? (8 - k) % 8 : k);
}

/* the planets above the horizon, the brightest first, as many as four (255 past them), for the astronomer's corners:
 * each one's light its full-phase magnitude's, a constant times its distances from the Sun and from us (the constant
 * 10^(H/5) from its magnitude at a unit's distance, Venus -4.40, Jupiter -9.40, Mars -1.52, Saturn -8.88 with its
 * rings, Mercury -0.42), the least the brightest: so no logarithms */
static void brightest_up(const R *r, float lat, uint8_t out[4]) {
  static const float K[PLANETS] = {0.1318f, 0.01318f, 0.4966f, 0.01675f, 0.8241f};
  int n = 0;
  for (int i = 0; i < 4; i++) out[i] = 255;
  for (int k = 0; k < PLANETS; k++) {
    if (plan_altitude(r->sky.pl_ra[k], r->sky.pl_dec[k], r->sky.lst, lat) <= 0) continue;
    float key = K[k] * r->sky.pl_far[k];
    int at = n < 4 ? n : 4;
    while (at > 0 && K[out[at - 1]] * r->sky.pl_far[out[at - 1]] > key) at--;
    if (at >= 4) continue;
    for (int j = (n < 4 ? n : 3); j > at; j--) out[j] = out[j - 1];
    out[at] = (uint8_t)k, n++;
  }
}

bool plan_render(Plan *p, const Face *f, int64_t utc, int32_t offset, const Target *t, void *(*alloc)(size_t),
                 void (*release)(void *)) {
  if (p->scribe) release(p->scribe), p->scribe = NULL, p->scribe_n = 0;   /* (the last minute's, not played) */
  if (!f->figs_part) p->event = 0;
  R *r = alloc(sizeof(R));
  if (!r) return false;
  memset(r, 0, sizeof *r);
  r->p = p, r->f = f, r->P = &PLATES[f->plate < PLATE_COUNT ? f->plate : 0];
  const Plate *P = r->P;
  r->W = p->w, r->H = p->h, r->rect = p->rect;
  r->utc = utc, r->offset = offset, r->clock24 = f->clock24;
  plan_rows(p, t);


  plan_window(p, f->lat);
  plan_sky(&r->sky, utc, f->lon);
  plan_civil(utc + offset, &r->local);
  almanac(r);
  r->bn = sec(p->data, SEC_BLUE_NOISE);
  r->cx = p->cx, r->cy = p->cy, r->k = p->k;
  r->col = (int)p->cx;
  r->south = f->lat < 0;
  r->alat = (float)f_abs(f->lat);
  r->sl = f_sind(r->alat), r->cl = f_cosd(r->alat);
  r->sl0 = f_sind((float)f->lat), r->cl0 = f_cosd((float)f->lat);
  r->lst = pyf_mod((float)r->sky.lst + f->turn, 360);   /* (the sky turned on, as a flick spins it) */
  r->lst20 = (uint32_t)pyf_floor(r->lst * (1048576.0f / 360) + 0.5f) & (BRAD_TURN - 1);
  r->kq = pyf_floor(r->k * (180.0f * 256 * 65536 / 65535) + 0.5f);
  r->cxq = pyf_floor(r->cx * 256 + 0.5f), r->cyq = pyf_floor(r->cy * 256 + 0.5f);
  r->cx2 = pyf_floor(r->cx * 2 + 0.5f), r->cy2 = pyf_floor(r->cy * 2 + 0.5f);
  r->paper = P->window == WIN_PAPER;
  r->red = P->window == WIN_RED;
  r->live = P->window == WIN_SKY || P->window == WIN_RED;
  r->light_paper = r->paper && level_sum(P->night) * 85 > 400;
  r->rete = P->rete, r->woodcut = P->woodcut;
  r->sun_alt = plan_altitude(r->sky.sun_ra, r->sky.sun_dec, r->sky.lst, (float)f->lat);
  /* an eclipse under way here: the sky dims toward twilight as the last of the Sun goes, deepest in totality; or
   * the Moon is in the Earth's shadow */
  r->have_sol = plan_solar(&r->sky, f->lat, &r->sol);
  r->have_lun = plan_lunar(&r->sky, f->lat, &r->lun);
  if (r->have_sol) {
    float u = f_smooth(0.80f, 1.0f, r->sol.cover);
    r->umbra = u * f_sqrt(u);
  }
  r->s_eff = r->umbra > 0 ? r->sun_alt + (-6 - r->sun_alt) * r->umbra : r->sun_alt;
  r->sdec = (float)(r->south ? -r->sky.sun_dec : r->sky.sun_dec);
  r->sha = (float)pyf_mod(r->south ? -(r->sky.lst - r->sky.sun_ra) : r->sky.lst - r->sky.sun_ra, 360.0f);
  r->mphase = (float)r->sky.moon_phase;
  r->tint = P->tint;                             /* (a step from the card's own: proto/plates.py tint_of) */
  r->ramp[r->nramp++] = P->night;
  for (int i = 0; i < 6; i++)
    if (level_sum(COOL[i]) > level_sum(P->night)) r->ramp[r->nramp++] = COOL[i];
  piece_colours(r);
  weather_sky(r);
  r->secs = r->local.hour * 3600 + r->local.minute * 60 + r->local.second;
  weather_layer(r);
  for (int x = 0; x < MAX_W; x++) r->btop[x] = NONE16;
  r->closed_sky = P->window == WIN_SKY && r->wx && (r->stratus >= 0.6f || r->fog || r->falls);

  /* where the numerals stand on the ring for this clock (worked out once, from the ring alone), before the window's
   * grid takes its memory */
  int style = f->clock24 ? 2 : P->ring == RING_ROMAN ? 0 : P->ring == RING_GOTHIC ? 3 : P->ring == RING_MINUSCULE ? 4 : 1;
  if (!numeral_layout(r, style, alloc, release)) { release(r); return false; }
  /* the card, the labours in it (before the grid too: they keep to the card, the grid to the window), and the
   * window's ground */
  for (int y = 0; y < r->H; y++) {
    if (p->rx0[y] > p->rx1[y]) continue;
    if (!P->fox) memset(ROW(p, y) + p->rx0[y], P->jacket, (size_t)(p->rx1[y] - p->rx0[y] + 1));
    else for (int x = p->rx0[y]; x <= p->rx1[y]; x++) ROW(p, y)[x] = card_at(r, x, y);
  }
  /* the scene in the card (the labours) and the Time 2's corner tools, by the scene blob (plan_decor.c, Face.decor):
   * now, while the frame's memory is low, before the grid */
  if (f->decor && (f->theme || (f->corners && r->rect))) {
    float mlon, mlat;
    eq_to_ecl(r->sky.moon_ra, r->sky.moon_dec, r->sky.eps, &mlon, &mlat);
    DecorCtx dc = {p, r->local.month - 1, r->south, r->col, r->cx, r->tint, P->ink, P->accent,
                   (uint8_t)((int)(r->sky.sun_lon / 30) % 12), (uint8_t)((int)(mlon / 30) % 12), f->theme,
                   (uint8_t)(r->rect && f->corners < THEME_COUNT ? f->corners : 0), r->paper || r->red, alloc, release,
                   NULL, {255, 255, 255, 255},
                   f->tides, (uint32_t)utc / 60u, moon_phase8(r)};   /* (32 bits: no 64-bit division) */
    brightest_up(r, (float)f->lat, dc.planets);
    f->decor(f->decor_ctx, &dc);
  }
  r->ik = 1 / r->k;
  r->ikq = pyf_floor(r->ik * 262144.0f + 0.5f);
  sky_constants(&r->sk, P->window == WIN_RED ? r->s_eff : r->sun_alt);
  sky_constants(&r->sk6, -6);
  r->ssd = f_sind(r->sdec), r->csd = f_cosd(r->sdec), r->csh = f_cosd(r->sha), r->ssh = f_sind(r->sha);
  bool milky = !r->rete && (r->paper || (r->sun_alt < -15 &&
               !(r->wx && r->live && (r->haze > 1.0f || r->stratus + r->cumulus > 0.45f))));
  if (!make_grid(r, alloc)) { release(r); return false; }
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
  r->lit_moon = !r->paper && P->window == WIN_SKY && r->s_eff < -10 && r->mphase > 0.3f && moon_up &&
                !(r->have_lun && r->lun.magnitude > 0.5f);
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
        if (inside(r, xi, yi) && r->dark && !hidden(r, xi, yi)) put(r, xi, yi, kind == 0 ? P->cons : P->line);
      }
  /* the meridian, dotted from the north point through the pole and the zenith to the south point */
  int zy = pyf_floor(r->cy + (90 - r->alat) * r->k);
  if (r->dark || r->paper)
    for (int y = 0; y < r->H; y += 3)
      if (inside(r, r->col, y) && (y - zy > 3 || zy - y > 3) && !hidden(r, r->col, y)) put(r, r->col, y, P->line);
  /* the figures, stopping short of their stars; the stars */
  if (r->figs && !r->rete) {
    /* drawn in as dusk brings them out, once an evening (the event's first frame; the caller draws the rest); and
     * again, if asked, at the top of each hour, half hour or quarter while they are out */
    int part = f->figs_part;
    static const uint8_t EVERY[4] = {0, 60, 30, 15};
    int every = EVERY[f->figures_every & 3];
    int32_t minute = r->local.ordinal * 1440 + r->local.hour * 60 + r->local.minute;
    if ((f->events & EV_FIGURES) && !part && !r->paper && r->local.hour >= 12 && r->s_eff > -13 &&
        p->figs_day != r->local.ordinal)
      p->figs_day = r->local.ordinal, p->event = EV_FIGURES, part = 1;
    else if ((f->events & EV_FIGURES) && !part && !r->paper && every && r->dark && r->local.minute % every == 0 &&
             p->figs_minute != minute)
      p->figs_minute = minute, p->event = EV_FIGURES, part = 1;
    figure_lines(r, part);
  }
  stars(r, faint, mx, my, moon_reach);
  /* the clouds over the stars (the Moon and planets shine through them); a halo round the Moon or the Sun */
  cloud_colours(r, r->mphase > 0.4f && moon_up);
  paint_clouds(r);
  if (r->wx && r->live && r->halo) {
    if (r->s_eff < -6 && r->mphase > 0.3f && moon_up)
      paint_halo(r, (float)r->sky.moon_ra, (float)r->sky.moon_dec, r->red ? C8(1, 0, 0) : C8(1, 1, 2));
    else if (r->sun_alt > 0)
      paint_halo(r, (float)r->sky.sun_ra, (float)r->sky.sun_dec, r->red ? C8(1, 0, 0) : r->s_eff < -6 ? C8(1, 1, 2) : C8(3, 3, 3));
  }
  /* the planets, each its little picture */
  for (int pn = 0; pn < PLANETS; pn++) {
    if (!r->paper && r->s_eff > -3) continue;
    float x, y;
    project(r, r->sky.pl_ra[pn], r->sky.pl_dec[pn], &x, &y);
    int xi = pyf_floor(x), yi = pyf_floor(y);
    paint(r, PLANET_DRAWINGS[pn], xi, yi, r->planet_c, true);
    const DrawIndex *di = drawing(r, PLANET_DRAWINGS[pn]);
    add_box(r, xi - di->w / 2 - 1, yi - di->h / 2 - 1, xi + di->w / 2 + 2, yi + di->h / 2 + 2);
    if (pn == JUPITER) jupiter_moons(r, xi, yi, di->w / 2);
  }
  /* the Moon in its phase; by day only its lit face */
  {
    uint8_t mc[8];
    memcpy(mc, r->moon_c, 8);
    if (!r->dark && !r->paper && r->mphase >= 0.04f) mc[1] = 0;
    int phase = 0;
    while (phase < MOON_PHASES - 1 && !(r->mphase < MOON_BY_LIGHT[phase])) phase++;
    int mi = pyf_floor(mx), mj = pyf_floor(my);
    if (r->have_lun && r->lun.magnitude > 0) moon_in_shadow(r, mi, mj, mx, my, mc[5]);
    else if (phase == MOON_PHASES - 1 && feast_marks(r, FS_RABBIT)) paint(r, D_MOON_RABBIT, mi, mj, mc, true);
    else paint(r, D_MOON_NEW + 2 * phase + (r->sky.moon_waxing ? 0 : 1), mi, mj, mc, true);
    add_box(r, mi - 6, mj - 6, mi + 7, mj + 7);
  }
  /* the Sun: in a live sky in its own light, a pale disc and a glow stippled thinner outward; on a printed chart
   * the engraver's glory round it; its face after the Sun of May */
  {
    float sx, sy;
    project(r, r->sky.sun_ra, r->sky.sun_dec, &sx, &sy);
    if (r->sun_alt > -0.8f || r->paper) {
      int si = pyf_floor(sx), sj = pyf_floor(sy);
      float cover = r->have_sol ? r->sol.cover : 0, dim = f_sqrt(1 - cover);
      if (!r->paper && cover < 0.97f) {
        uint8_t light = r->red ? C8(2, 0, 0) : r->sun_alt < 6 ? C8(3, 3, 2) : C8(2, 3, 3);
        for (int y = sj - 18; y <= sj + 18; y++)
          for (int x = si - 18; x <= si + 18; x++) {
            if (!inside(r, x, y)) continue;
            float ddx = (float)(x - si), ddy = (float)(y - sj), dd = f_sqrt(ddx * ddx + ddy * ddy);
            float g = f_clamp(1 - (dd - 4.0f) / 13.0f, 0, 1);
            float glow = g * f_sqrt(g) * 0.85f * dim * (r->closed_sky ? 0.0f : 1.0f);
            if (dd > 4.0f && glow > tt(r, x, y)) put(r, x, y, light);
            if (dd <= 4.4f) put(r, x, y, r->red ? C8(3, 0, 0) : C8(3, 3, 1));
          }
      } else if (r->paper) {
        const MaskIndex *gl = mask(r, M_GLORY);
        int x0 = pyf_round(si - (gl->w - 1) / 2.0f), y0 = pyf_round(sj - (gl->h - 1) / 2.0f);
        for (int j = 0; j < gl->h; j++)
          for (int i = 0; i < gl->w; i++)
            if (mask_at(r, gl, i, j) && inside(r, x0 + i, y0 + j)) put(r, x0 + i, y0 + j, P->line);
      }
      float ox = 0, oy = 0;
      if (r->have_sol) sun_offset(r, si, sj, &ox, &oy);
      if (r->have_sol && !r->paper && cover >= 0.97f) corona(r, si, sj, ox, oy);
      else {
        paint(r, D_SUN, si, sj, r->sun_c, true);
        if (r->have_sol) moon_across(r, si, sj, ox, oy);
      }
      add_box(r, si - 12, sj - 12, si + 13, sj + 13);
    }
  }
  /* a meteor shower at its peak: its radiant, where the meteors seem to come from */
  r->shower = -1;
  int sh = plan_shower(r->sky.sun_lon), rad_x = 0, rad_y = 0;
  if (sh >= 0 && (r->dark || r->paper) && altitude(r, SHOWERS[sh].ra, SHOWERS[sh].dec) > 0) {
    float x, y;
    project(r, SHOWERS[sh].ra, SHOWERS[sh].dec, &x, &y);
    rad_x = pyf_floor(x), rad_y = pyf_floor(y);
    if (inside(r, rad_x, rad_y)) {
      uint8_t col[8] = {0, 0, P->accent};
      paint(r, D_RADIANT, rad_x, rad_y, col, true);
      add_box(r, rad_x - 5, rad_y - 5, rad_x + 6, rad_y + 6);
      r->shower = sh;
    }
  }
  /* rain or snow falling past everything in the sky */
  paint_falls(r);
  /* the southern horizon: the distant hills, the village */
  int season = season_of(r->sky.sun_lon, f->lat);
  window_edge(r);
  hills(r);
  village(r, season);
  village_weather(r);
  feast_fires(r);
  show_plan(r);
  passing(r, rad_x, rad_y);
  /* names in the sky; the ornaments where no name is */
  feast_sky(r);
  if (f->names) names(r, mx, my);
  if (f->names && r->shower >= 0) {
    pixel_text(&r->t1, r, SHOWERS[r->shower].name, true, 0);
    place(r, &r->t1, rad_x + 3, rad_y, P->accent, false, 0, 0, false);
  }
  ornaments(r);
  /* the window's edge, the ring, the time */
  int fy0 = rims(r);
  ring(r, season);
  time_block(r, fy0, season, alloc, release);
  release(r->ga);
  release(r);
  return true;
}
