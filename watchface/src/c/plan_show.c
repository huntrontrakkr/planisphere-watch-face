/* The motion blob: the fireworks display, and the minute written.
 *
 * The fireworks display, frame by frame (proto/feast_draw.py fireworks_show): each rocket climbing on its bright head
 * and fading trail, then bursting with a white flash, its sparks flying out as bright heads with fading streaks behind
 * them, then drooping and dimming out. The willows droop longest, gold; the crackling ones twinkle as they go; the
 * peonies have a white pistil. On a printed chart the whole of it is engraved, in its ink.
 *
 * The rockets are the Plan's (plan_render.c show_plan, at the top of the hour). Each frame is drawn over the face as
 * last drawn: first the pixels the last frame covered are put back (a ShowUndo keeps them), then this frame's go down,
 * a margin of the rocket's ground round every spark and then the sparks, in the prototype's order. On the watch this
 * is a code blob of its own (tools/build_blob.py), loaded for the few seconds a display lasts. */
#include "plan.h"
#include "plan_math.h"

#define WHITE 0xFF                                   /* GColor8: 0xC0 | red << 4 | green << 2 | blue */
#define C8(r, g, b) (uint8_t)(0xC0 | (r) << 4 | (g) << 2 | (b))

typedef struct {
  Plan *p;
  ShowUndo *undo;
  int pass;                                          /* 0 the margins, 1 the sparks */
  uint8_t halo;                                      /* the rocket's */
} Frame;

/* a colour a step or two toward the night sky */
static uint8_t dim(uint8_t c, int steps) {
  uint8_t out = 0xC0;
  for (int s = 0; s <= 4; s += 2) {
    int l = (c >> s & 3) - steps;
    out |= (uint8_t)((l < 0 ? 0 : l) << s);
  }
  return out;
}

/* a pixel of the window, its old colour kept to be put back */
static void put(Frame *fr, int x, int y, uint8_t c) {
  Plan *p = fr->p;
  if ((unsigned)y >= (unsigned)p->h || x < p->wx0[y] || x > p->wx1[y] || x < p->rx0[y] || x > p->rx1[y]) return;
  ShowUndo *u = fr->undo;
  uint8_t *px = &p->rows[y][x];
  if (*px == c || u->n >= u->cap) return;            /* (as it is; or no room to put it back: left out) */
  u->px[u->n++] = (uint32_t)x | (uint32_t)y << 9 | (uint32_t)*px << 18;
  *px = c;
}

/* a spark at (x, y) to the nearest pixel (Python's rounding), as the prototype's _put notes it: in the first pass its
 * margin, in the second the spark */
static void spark(Frame *fr, float x, float y, uint8_t c) {
  int xi = pyf_round(x), yi = pyf_round(y);
  Plan *p = fr->p;
  if ((unsigned)yi >= (unsigned)p->h || xi < p->wx0[yi] || xi > p->wx1[yi]) return;
  if (fr->pass == 1) {
    put(fr, xi, yi, c);
    return;
  }
  static const int8_t N4[4][2] = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
  for (int d = 0; d < 4; d++) put(fr, xi + N4[d][0], yi + N4[d][1], fr->halo);
}

/* the burst's reach after q frames: opening fast and slowing, then spreading a little as it hangs */
static float reach(const Rocket *k, int q) {
  float u = 1 - (float)(q < SHOW_SPREAD ? q : SHOW_SPREAD) / SHOW_SPREAD;
  return (float)k->R * (1 - u * u) + 0.3f * (float)(q > SHOW_SPREAD ? q - SHOW_SPREAD : 0);
}

static void rocket(Frame *fr, const Rocket *k, int frame) {
  Plan *p = fr->p;
  uint8_t ink = p->show_ink;
  int t = frame - k->f0;
  if (t < 0) return;
  fr->halo = k->halo;
  if (t < k->up) {                                   /* climbing, slowing toward the top */
    static const uint8_t TRAIL[5] = {WHITE, C8(3, 3, 1), C8(3, 2, 0), C8(2, 1, 0), C8(1, 0, 0)};
    for (int back = 0; back < 5; back++) {
      if (ink && back % 2) continue;
      float u = (float)(t - back > 0 ? t - back : 0) / (float)k->up, e = 1 - (1 - u) * (1 - u);
      spark(fr, (float)k->x0 + (float)k->drift * e, (float)k->foot - (float)k->rise * e, ink ? ink : TRAIL[back]);
    }
    return;
  }
  int s = t - k->up;                                 /* bursting */
  if (s >= SHOW_SPREAD + SHOW_LIFE) return;
  float bx = (float)(k->x0 + k->drift), by = (float)(k->foot - k->rise);
  uint8_t colour = ink ? ink : k->kind == 1 ? C8(3, 3, 1) : p->show_sparks[k->colour];
  float g = k->kind == 1 ? 0.08f : 0.035f;           /* how fast the sparks fall once spent */
  Rng twinkle;
  rng_start(&twinkle, (uint32_t)(k->f0 * 7919 + frame));
  if (s < 2) {                                       /* the flash */
    static const int8_t FLASH[9][2] = {{0, 0}, {1, 0}, {-1, 0}, {0, 1}, {0, -1}, {1, 1}, {-1, -1}, {1, -1}, {-1, 1}};
    for (int i = 0; i < (s == 0 ? 9 : 5); i++) spark(fr, bx + FLASH[i][0], by + FLASH[i][1], ink ? ink : WHITE);
  }
  uint8_t head = s < 2 && !ink ? WHITE : s < SHOW_SPREAD + 5 ? colour :
                 ink ? ink : dim(colour, s < SHOW_SPREAD + 9 ? 1 : 2);
  float r1 = reach(k, s + 1), fall = g * (float)(s > 2 ? (s - 2) * (s - 2) : 0);
  for (int i = 0; i < k->n; i++) {
    if (k->kind == 2 && s >= 3 && rng_int(&twinkle, 0, 3) == 0) continue;   /* crackling: winking out and back */
    if (ink && s >= SHOW_SPREAD + 6 && i % 2) continue;                       /* engraved: the fading as fewer */
    float a = 360.0f * ((float)i + k->turn) / (float)k->n, sa = f_sind(a), ca = f_cosd(a);
    /* the spark's head, and its streak back toward where it came from: two pixels while it flies, one after */
    for (int back = 0; back < 3; back++) {
      if (back == 2 && (s >= SHOW_SPREAD || ink)) continue;
      float rb = r1 - (float)back * (s < SHOW_SPREAD ? 1.3f : 0.9f), fb = (float)(s - 2 - back);
      if (rb < 0) rb = 0;
      fb = fb > 0 ? g * fb * fb : 0;
      spark(fr, bx + rb * sa, by - rb * ca + fb, back == 0 ? head : ink ? ink : dim(head, back));
    }
    if (k->kind == 0 && i % 2 == 0 && s < SHOW_SPREAD + 6)                     /* a peony's pistil, white */
      spark(fr, bx + 0.5f * r1 * f_sind(a + 11.459156f), by - 0.5f * r1 * f_cosd(a + 11.459156f) + fall,
            ink ? ink : s < SHOW_SPREAD + 3 ? WHITE : C8(2, 2, 3));
  }
}

/* the screen's rows, and the last frame's pixels put back, last first */
static void put_back(Plan *p, const Target *t, ShowUndo *undo) {
  for (int y = 0; y < p->h; y++) {
    int x0, x1;
    p->rows[y] = t->row(t->ctx, y, &x0, &x1);
    p->rx0[y] = (int16_t)x0, p->rx1[y] = (int16_t)x1;
    if (!p->rows[y]) p->rx0[y] = 1, p->rx1[y] = 0;
  }
  while (undo->n) {
    uint32_t v = undo->px[--undo->n];
    int x = v & 511, y = v >> 9 & 511;
    if (x >= p->rx0[y] && x <= p->rx1[y]) p->rows[y][x] = (uint8_t)(v >> 18);
  }
}

bool plan_show(Plan *p, const Target *t, int frame, ShowUndo *undo) {
  put_back(p, t, undo);
  if (frame >= p->show_end) return false;
  Frame fr = {p, undo, 0, 0};
  for (fr.pass = 0; fr.pass < 2; fr.pass++)
    for (int i = 0; i < p->show_rockets; i++) rocket(&fr, &p->show[i], frame);
  return true;
}

/* ---- the passing events (Plan.event, chosen by plan_render): a meteor, its head flying the path in four frames on a
 * fading trail that then fades out after it; a skein of seven birds in a V crossing the window, their wings beating.
 * Drawn as the display is, over the face as last drawn. ------------------------------------------------------- */
bool plan_event(Plan *p, const Target *t, int frame, ShowUndo *undo) {
  put_back(p, t, undo);
  if (frame >= p->event_frames || !(p->event & (EV_METEOR | EV_BIRDS))) return false;
  Frame fr = {p, undo, 1, 0};
  float x0 = p->event_x0, y0 = p->event_y0, dx = p->event_x1, dy = p->event_y1;
  uint8_t ink = p->event_ink;
  if (p->event == EV_METEOR) {
    /* its path: 22 to 36 pixels its way, as far as it stays in the window */
    float d = f_sqrt(dx * dx + dy * dy);
    if (d == 0) dy = d = 1;
    Rng g;
    rng_start(&g, (uint32_t)(p->event_x0 * 512 + p->event_y0));
    int L = rng_int(&g, 22, 37), ex = 0, ey = 0;
    for (; L > 12; L -= 3) {
      ex = p->event_x0 + pyf_round(dx / d * (float)L), ey = p->event_y0 + pyf_round(dy / d * (float)L);
      if ((unsigned)ey < (unsigned)p->h && ex >= p->wx0[ey] && ex <= p->wx1[ey]) break;
    }
    if (L <= 12) return false;
    dx = (float)(ex - p->event_x0), dy = (float)(ey - p->event_y0);
    float Lf = (float)L, head = Lf * (float)(frame < 4 ? frame + 1 : 4) / 4;
    int fade = frame < 4 ? 0 : frame - 3;             /* the head spent: the trail going from its far end */
    static const uint8_t TRAIL[4] = {WHITE, C8(2, 3, 3), C8(1, 2, 3), C8(1, 1, 2)};
    for (int b = 0; b < 12 - 4 * fade && head >= (float)b; b++)
      if (!ink || b % 2 == 0)
        spark(&fr, x0 + dx * (head - (float)b) / Lf, y0 + dy * (head - (float)b) / Lf,
              ink ? ink : TRAIL[fade ? 1 + fade : b < 2 ? 0 : b < 5 ? 1 : b < 8 ? 2 : 3]);
    return true;
  }
  /* the birds: from beyond one side of the window to beyond the other, the leader on the path and three to each side
   * behind it, each pair beating their wings together */
  int y = p->event_y0;
  x0 = p->event_x0 ? p->wx0[y] - 4 : p->wx1[y] + 4, dx = (p->event_x0 ? p->wx1[y] + 34 : p->wx0[y] - 34) - x0;
  dy = (float)(p->event_y1 - y);
  float u = (float)frame / (float)p->event_frames, L = f_sqrt(dx * dx + dy * dy), ax = dx / L, ay = dy / L;
  for (int i = 0; i < 7; i++) {
    int rank = (i + 1) / 2, side = i % 2 ? 1 : -1;
    float bx = x0 + dx * u - ax * 4 * rank - ay * 3 * rank * side, by = y0 + dy * u - ay * 4 * rank + ax * 3 * rank * side;
    int up = (frame / 3 + rank) % 2;                  /* the wings up and level, each pair together */
    spark(&fr, bx, by, ink);
    spark(&fr, bx - 1, by - up, ink);
    spark(&fr, bx + 1, by - up, ink);
  }
  return true;
}

/* ---- the minute written (Plan.scribe, kept by plan_render as it drew the figures that changed): each figure's
 * outline from its top round clockwise, figure after figure, then the fill from the outlines in, a ring of pixels at a
 * time, as a scribe outlines a letter and fills it. Frame 0 takes the new figures away; the rest write them. ------ */
static int figure_ink(const uint8_t *bits, const FigureIndex *f, int i, int j) {
  if (i < 0 || j < 0 || i >= f->w || j >= f->h) return 0;
  uint32_t b = f->bit + (uint32_t)(j * f->w + i);
  return (bits[b >> 3] >> (b & 7)) & 1;
}
/* a point's place round a middle, clockwise from the top, 0 to 4 (u to the right, v up) */
static float round_from_top(float u, float v) {
  float d = f_abs(u) + f_abs(v);
  if (d == 0) return 0;
  if (v > 0 && u >= 0) return u / d;
  if (u > 0) return 1 - v / d;
  if (v < 0) return 2 - u / d;
  return 3 + v / d;
}
static void scribe_order(Plan *p, uint32_t *key) {
  uint32_t *px = p->scribe;
  const FigureIndex *fi = (const FigureIndex *)(const void *)sec(p->data, SEC_FIGURE_INDEX) + p->time_style * 12;
  const uint8_t *bits = sec(p->data, SEC_FIGURE_DATA);
  int n = p->scribe_n, lines = 0;
  for (int e = 0; e < n; e++) {
    int g = (int)(px[e] >> 24 & 7);
    const FigureIndex *f = &fi[p->time_c[g]];
    int i = (int)(px[e] & 511) - p->time_x[g], j = (int)(px[e] >> 9 & 511) - p->time_y[g], ring = 0;
    for (int d = 1; !ring && d < 64; d++)              /* its ring: the nearest pixel without ink, so far in */
      for (int t = 0; t < d && !ring; t++)
        if (!figure_ink(bits, f, i + t, j + d - t) || !figure_ink(bits, f, i + d - t, j - t) ||
            !figure_ink(bits, f, i - t, j - d + t) || !figure_ink(bits, f, i - d + t, j + t))
          ring = d;
    uint32_t at = (uint32_t)(j * f->w + i) & 0xFFFF;
    key[e] = ring == 1 ? (uint32_t)g << 28 | (uint32_t)(round_from_top(i - (f->w - 1) / 2.0f, (f->h - 1) / 2.0f - j) * 1023) << 16 | at
                       : 1u << 31 | (uint32_t)ring << 20 | (uint32_t)g << 16 | at;
    lines += ring == 1;
  }
  for (int a = 1; a < n; a++) {                      /* in the pen's order (an insertion sort: a few hundred pixels) */
    uint32_t k = key[a], v = px[a];
    int b = a - 1;
    for (; b >= 0 && key[b] > k; b--) key[b + 1] = key[b], px[b + 1] = px[b];
    key[b + 1] = k, px[b + 1] = v;
  }
  p->scribe_lines = (uint16_t)lines;
}
/* frame k (1 ..) writes the pixels up to scribe_cut(k): four frames of outline, then the rest of fill */
static int scribe_cut(const Plan *p, int k) {
  int lines = p->scribe_lines, fill = p->scribe_n - lines;
  return k <= 4 ? lines * k / 4 : lines + fill * (k - 4) / (SCRIBE_FRAMES - 1 - 4);
}
bool plan_scribe(Plan *p, const Target *t, int frame, uint32_t *room) {
  if (!p->scribe || frame < 0 || frame >= SCRIBE_FRAMES) return false;
  if (p->scribe_lines == 0xFFFF) {
    if (!room) return false;
    scribe_order(p, room);
  }
  int a = frame ? scribe_cut(p, frame - 1) : 0, b = frame ? scribe_cut(p, frame) : p->scribe_n;
  for (int i = a; i < b; i++) {
    uint32_t v = p->scribe[i];
    int x = (int)(v & 511), y = (int)(v >> 9 & 511), x0, x1;
    uint8_t *row = t->row(t->ctx, y, &x0, &x1);
    if (row && x >= x0 && x <= x1) row[x] = frame ? p->scribe_ink : (uint8_t)(0xC0 | (v >> 18 & 63));
  }
  return frame + 1 < SCRIBE_FRAMES;
}

