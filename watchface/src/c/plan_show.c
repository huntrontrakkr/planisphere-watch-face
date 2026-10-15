/* The fireworks display, frame by frame (proto/feast_draw.py fireworks_show): each rocket climbing on its bright head
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

bool plan_show(Plan *p, const Target *t, int frame, ShowUndo *undo) {
  for (int y = 0; y < p->h; y++) {
    int x0, x1;
    p->rows[y] = t->row(t->ctx, y, &x0, &x1);
    p->rx0[y] = (int16_t)x0, p->rx1[y] = (int16_t)x1;
    if (!p->rows[y]) p->rx0[y] = 1, p->rx1[y] = 0;
  }
  while (undo->n) {                                  /* the last frame's pixels put back, last first */
    uint32_t v = undo->px[--undo->n];
    int x = v & 511, y = v >> 9 & 511;
    if (x >= p->rx0[y] && x <= p->rx1[y]) p->rows[y][x] = (uint8_t)(v >> 18);
  }
  if (frame >= p->show_end) return false;
  Frame fr = {p, undo, 0, 0};
  for (fr.pass = 0; fr.pass < 2; fr.pass++)
    for (int i = 0; i < p->show_rockets; i++) rocket(&fr, &p->show[i], frame);
  return true;
}
