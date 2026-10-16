/* The labours' blob: the labours of the months, faint in the card round the window, and the Time 2's corner tools
 * (the theme's or, with no theme, the season's tools), drawn early in a frame (plan_render.c calls Face.decor where the
 * card is laid, before the window's grid takes its memory). On the watch a code blob of its own (tools/build_blob.py),
 * loaded only for these, for the moment it draws; the corner tools' table (tools.bin) read from the resources as it
 * goes. The woodcuts' themes are plan_decor.c's. */
#include <string.h>
#include "plan_card.h"

typedef struct { uint32_t bit; uint8_t w, h; uint16_t pad; } MaskIndex;
static const MaskIndex *mask(const DecorCtx *r, int m) { return (const MaskIndex *)(const void *)sec(r->p->data, SEC_MASK_INDEX) + m; }
static bool mask_at(const DecorCtx *r, const MaskIndex *mi, int i, int j) {
  const uint8_t *data = sec(r->p->data, SEC_MASK_DATA);
  uint32_t n = mi->bit + (uint32_t)(j * mi->w + i);
  return (data[n >> 3] >> (n & 7)) & 1;
}
/* ---- the labours of the months (proto/plates.py labour_scene), an option: faint in the card between the window and
 * the ring, the month's field running on behind the window from a point hidden behind its top, the labourer in the
 * left of it and the month's thing in the right ---------------------------------------------------------------- */
typedef struct { const MaskIndex *mi; bool mirror; int x0, y0; } LabFig;
typedef struct {
  const DecorCtx *r;
  const uint8_t (*card)[4];
  LabFig fig[6];
  int nfig;
  uint8_t tone;
} Lab;

/* in row v, how far x stands from the nearest pixel off the field's ground (the card below the hills): 0 on one */
static int lab_room(const DecorCtx *r, const uint8_t c[4], bool ok, int x) {
  if (!ok || !in_card(c, x)) return 0;
  int a = c[0], b = c[1];
  if (c[2] <= c[3]) {
    if (x < c[2]) b = b < c[2] - 1 ? b : c[2] - 1;
    else a = a > c[3] + 1 ? a : c[3] + 1;
  }
  int left = a > 0 ? x - a + 1 : NONE16, right = b < r->p->w - 1 ? b - x + 1 : NONE16;
  return left < right ? left : right;
}

/* where the labourer and the month's thing stand: on each side of the middle, the pixel of the field's ground standing
 * clearest of its edges (Chebyshev, up to 14 px), the first such in reading order */
static void labour_places(const DecorCtx *r, const uint8_t (*card)[4], int vy) {
  Plan *p = r->p;
  int best[2] = {0, 0};
  for (int s = 0; s < 2; s++) p->lab_at[s][0] = 0, p->lab_at[s][1] = 0;
  for (int y = vy + 3; y < r->p->h; y++)
    for (int x = card[y][0]; x <= card[y][1]; x++) {
      if (!in_card(card[y], x)) continue;
      int d = 14;
      for (int v = y - 13; v <= y + 13 && d > 0; v++) {
        if (v < 0 || v >= r->p->h) continue;
        int dv = v < y ? y - v : v - y;
        if (dv >= d) continue;
        int h = lab_room(r, card[v], v > vy + 2, x), e = h > dv ? h : dv;
        if (e < d) d = e;
      }
      int s = x >= r->col;
      if (d > best[s]) best[s] = d, p->lab_at[s][0] = (int16_t)x, p->lab_at[s][1] = (int16_t)y;
    }
}

static bool lab_px(const DecorCtx *r, const LabFig *f, int i, int j) {
  if (i < 0 || j < 0 || i >= f->mi->w || j >= f->mi->h) return false;
  return mask_at(r, f->mi, f->mirror ? f->mi->w - 1 - i : i, j);
}
/* 2: the figure's pixel; 1: one touching it (kept clear); 0: neither */
static int lab_fig_at(const DecorCtx *r, const LabFig *f, int x, int y) {
  int i = x - f->x0, j = y - f->y0;
  if (i < -1 || j < -1 || i > f->mi->w || j > f->mi->h) return 0;
  if (lab_px(r, f, i, j)) return 2;
  return lab_px(r, f, i - 1, j) || lab_px(r, f, i + 1, j) || lab_px(r, f, i, j - 1) || lab_px(r, f, i, j + 1);
}
/* a mark of the field, unless a figure stands there or beside it */
static void lab_mark(Lab *l, int x, int y) {
  if (!on_screen(l->r, x, y) || !in_card(l->card[y], x)) return;
  for (int k = 0; k < l->nfig; k++)
    if (lab_fig_at(l->r, &l->fig[k], x, y)) return;
  put(l->r, x, y, l->tone);
}

static void labours(const DecorCtx *r) {
  Plan *p = r->p;
  const int16_t *inner = sec16(p->geom, GEO_INNER);
  uint8_t (*card)[4] = r->alloc((size_t)r->p->h * sizeof *card);
  if (!card) return;
  for (int y = 0; y < r->p->h; y++) card_row(r, inner, y, card[y]);
  int month = r->month;                                            /* (half a year round in the south) */
  const Labour *L = &LABOURS[month];
  int top = 0;
  for (int y = 0; y < r->p->h; y++)
    if (inside(r, r->col, y)) { top = y; break; }
  float vx = r->cx;
  int vy = top + 6;
  if (!p->lab_ok) labour_places(r, (const uint8_t (*)[4])card, vy), p->lab_ok = true;
  Lab l = {r, (const uint8_t (*)[4])card, {{0}}, 0, r->tone};
  for (int s = 0; s < 2; s++) {
    const LabourFigure *lf = &L->side[s];
    const MaskIndex *mi = mask(r, lf->mask);
    for (int c = 0; c < lf->n; c++)
      l.fig[l.nfig++] = (LabFig){mi, s == 1, p->lab_at[s][0] - mi->w / 2 + lf->at[c][0],
                                 p->lab_at[s][1] - mi->h / 2 + lf->at[c][1]};
  }
  /* the far hills, a gentle line across behind the window's top */
  for (int x = 0; x < r->p->w; x++) {
    int y = pyf_round(vy - 3 + 1.5f * f_sind(x * (57.29577951f / 7)) + f_sind(x * (57.29577951f / 3.1f)));
    lab_mark(&l, x, y);
  }
  /* the field */
  if (L->field == FIELD_FURROWS) {                 /* the sown field: dotted furrows */
    for (int a = -84; a <= 84; a += 7) {
      float ex = vx + 260 * f_sind((float)a), ey = vy + 260 * f_cosd((float)a);
      float adx = f_abs(ex - vx), ady = f_abs(ey - vy);
      int n = (int)((adx > ady ? adx : ady) * 2) + 1, lx = -NONE16, ly = -NONE16, at = 0;
      for (int k = 0; k <= n; k++) {
        float t = (float)k / (float)n;
        int px = pyf_floor(vx + (ex - vx) * t), py = pyf_floor(vy + (ey - vy) * t);
        if (px == lx && py == ly) continue;
        lx = px, ly = py;
        if (at++ % 2 == 0) lab_mark(&l, px, py);
      }
    }
  } else if (L->field == FIELD_VINES || L->field == FIELD_STUBBLE) {   /* rows of vine stakes, or of stubble */
    bool vines = L->field == FIELD_VINES;
    int step = vines ? 12 : 6;
    float every = vines ? 6.0f : 3.0f;
    for (int a = -84; a <= 84; a += step) {
      float sa = f_sind((float)a), ca = f_cosd((float)a);
      for (float d = 6; d < 260; d += every * (1 + d / 60)) {
        int x = pyf_round(vx + d * sa), y = pyf_round(vy + d * ca);
        int h = vines ? 1 + (int)(d / 30) : d < 60 ? 1 : 2;
        for (int k = 0; k < h; k++) lab_mark(&l, x, y - k);
      }
    }
  } else {                                         /* tufts of grass, or the pecked dots of snow */
    bool grass = L->field == FIELD_GRASS;
    Rng g;
    rng_start(&g, (uint32_t)(month + 1));
    for (int gy = vy + 4; gy < r->p->h; gy += 5)
      for (int gx = rng_int(&g, 0, 6); gx < r->p->w; gx += 7) {
        int x = gx + rng_int(&g, -2, 3), y = gy + rng_int(&g, -1, 2);
        if (x < 1 || x >= r->p->w - 1 || y < 1 || y >= r->p->h) continue;
        if (grass) lab_mark(&l, x - 1, y - 1), lab_mark(&l, x + 1, y - 1);
        lab_mark(&l, x, y);
      }
  }
  /* the figures, each over those before it with a pixel kept clear round it */
  for (int k = 0; k < l.nfig; k++) {
    const LabFig *f = &l.fig[k];
    for (int j = 0; j < f->mi->h; j++)
      for (int i = 0; i < f->mi->w; i++) {
        int x = f->x0 + i, y = f->y0 + j, q = k + 1;
        if (!lab_px(r, f, i, j) || !on_screen(r, x, y) || !in_card(card[y], x)) continue;
        while (q < l.nfig && !lab_fig_at(r, &l.fig[q], x, y)) q++;
        if (q == l.nfig) put(r, x, y, l.tone);
      }
  }
  r->release(card);
}

/* the Labours' tools in the Time 2's corners (tools.bin, proto/labour_tools.py): the top piece in the top corners and
 * the bottom piece in the bottom ones, mirrored on the right, where the corner is clear of the ring; on a printed or
 * a red plate their outlines alone, in its ink */
static void corner_tools(const DecorCtx *r, const uint8_t *rec) {
  const uint8_t *pc = rec + TOOLS_CLIP;
  bool ink = r->line_only;
  for (int k = 0; k < 2; k++) {
    int w = pc[0], h = pc[1], x0 = pc[2], y0 = pc[3], n = pc[4];
    const uint8_t *cols = pc + 5, *px = cols + n;
    for (int j = 0; j < h; j++)
      for (int i = 0; i < w; i++) {
        int b = j * w + i, v = (px[b >> 1] >> ((b & 1) * 4)) & 15, x = x0 + i, row = y0 + j;
        if (!v || x >= rec[k ? TOOLS_CLIP - 1 - row : row]) continue;
        uint8_t c = cols[v - 1];
        if (ink && (c & 0x40)) continue;
        c = ink ? r->ink : (uint8_t)(c | 0xC0);
        int y = k ? r->p->h - TOOLS_CLIP + row : row;
        put(r, x, y, c), put(r, r->p->w - 1 - x, y, c);
      }
    pc = px + (w * h + 1) / 2;
  }
}

bool plan_labours(const DecorCtx *d, const FeastReader *tools, const FeastReader *scenes) {
  if (d->theme == THEME_LABOURS) labours(d);
  if (d->tools && tools) {   /* the month's record of tools.bin: its clearance, its two pieces */
    uint8_t o[4];
    tools->read(tools->ctx, TOOLS_CLIP + 2 * (uint32_t)d->month, o, 4);
    int a = o[0] | o[1] << 8, n = (o[2] | o[3] << 8) - a;
    uint8_t *rec = n > 0 ? d->alloc(TOOLS_CLIP + (size_t)n) : NULL;
    if (rec) {
      tools->read(tools->ctx, 0, rec, TOOLS_CLIP);
      tools->read(tools->ctx, (uint32_t)a, rec + TOOLS_CLIP, (uint32_t)n);
      corner_tools(d, rec);
      d->release(rec);
    }
  }
  return true;
}
