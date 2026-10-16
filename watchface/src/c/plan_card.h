/* The card's helpers shared by the scene blobs (plan_decor.c, plan_labours.c): drawing into the Plan's rows, the window,
 * and the card round it row by row. */
#pragma once
#include "plan.h"
#include "plan_math.h"

#define NONE16 0x7fff
static inline void put(const DecorCtx *r, int x, int y, uint8_t c) {
  Plan *p = r->p;
  if ((unsigned)y < (unsigned)p->h && x >= p->rx0[y] && x <= p->rx1[y]) p->rows[y][x] = c;
}
static inline bool on_screen(const DecorCtx *r, int x, int y) { return (unsigned)x < (unsigned)r->p->w && (unsigned)y < (unsigned)r->p->h; }
static inline bool inside(const DecorCtx *r, int x, int y) {
  return (unsigned)y < (unsigned)r->p->h && x >= r->p->wx0[y] && x <= r->p->wx1[y];
}
static inline const int16_t *sec16(const uint8_t *blob, int i) { return (const int16_t *)(const void *)sec(blob, i); }

/* the card in row y, as the prototype grows things (a pixel at a time, four ways): inside the ring's inner edge by
 * 3 px, [c0, c1], and not within 3 px of the window, [c2, c3] */
static inline void card_row(const DecorCtx *r, const int16_t *inner, int y, uint8_t c[4]) {
  Plan *p = r->p;
  int lo = -NONE16, hi = NONE16, glo = NONE16, ghi = -NONE16;
  for (int dy = -3; dy <= 3; dy++) {
    int v = y + dy, g = 3 - (dy < 0 ? -dy : dy);
    if (v < 0 || v >= r->p->h) continue;
    if (inner[2 * v] > inner[2 * v + 1]) lo = 1, hi = 0;
    if (inner[2 * v] + g > lo) lo = inner[2 * v] + g;
    if (inner[2 * v + 1] - g < hi) hi = inner[2 * v + 1] - g;
    if (p->wx0[v] > p->wx1[v]) continue;
    if (p->wx0[v] - g < glo) glo = p->wx0[v] - g;
    if (p->wx1[v] + g > ghi) ghi = p->wx1[v] + g;
  }
  /* (a byte each: the screens' pixels from 0 to 259 and the card's from 3 in; no window: 255, 0) */
  c[0] = (uint8_t)(lo < 0 ? 0 : lo > 255 ? 255 : lo), c[1] = (uint8_t)(hi < 0 ? 0 : hi > 255 ? 255 : hi);
  c[2] = (uint8_t)(glo < 0 ? 0 : glo > 255 ? 255 : glo), c[3] = (uint8_t)(ghi < 0 ? 0 : ghi > 255 ? 255 : ghi);
}
static inline bool in_card(const uint8_t c[4], int x) { return x >= c[0] && x <= c[1] && (x < c[2] || x > c[3]); }

