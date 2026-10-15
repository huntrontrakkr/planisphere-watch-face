/* The arithmetic the face needs, the same on the watch, the host and the settings page's WebAssembly: the
 * library's own functions differ from one to the next (and the watch's are large), so these are our own, in single
 * precision (the watch has no room for double precision's library: plan_astro.c keeps its large angles exact in
 * integers instead).
 *
 *   f_*    approximations, to a few parts in ten million
 *   pyf_*  Python's rounding and remainder, so the C lands on the prototype's pixels
 */
#pragma once
#include <stdint.h>

static inline int pyf_floor(float x) { int i = (int)x; return (float)i > x ? i - 1 : i; }
int pyf_round(float x);
static inline float pyf_mod(float x, float y) { return x - y * (float)pyf_floor(x / y); }
static inline float f_abs(float x) { return x < 0 ? -x : x; }

float f_sqrt(float x);
float f_exp(float x);
float f_log(float x);
float f_pow(float x, float y);          /* x > 0; 0 for x <= 0 */
float f_sind(float deg);
float f_cosd(float deg);
float f_atan2d(float y, float x);       /* degrees, -180..180 */
float f_asind(float x);                 /* degrees; x clamped to -1..1 */
float f_acosd(float x);
static inline float f_clamp(float v, float lo, float hi) { return v < lo ? lo : v > hi ? hi : v; }
/* the smoothstep of the prototype: 0 below e0, 1 above e1 */
static inline float f_smooth(float e0, float e1, float x) {
  float t = f_clamp((x - e0) / (e1 - e0), 0.0f, 1.0f);
  return t * t * (3.0f - 2.0f * t);
}

/* the random numbers the prototype draws too (proto/rng.py, xorshift32), so both scatter the weather, the stars of
 * the labours and the fireworks alike */
typedef struct { uint32_t x; } Rng;
static inline uint32_t rng_next(Rng *g) {
  uint32_t x = g->x;
  x ^= x << 13, x ^= x >> 17, x ^= x << 5;
  return g->x = x;
}
static inline void rng_start(Rng *g, uint32_t seed) {
  g->x = seed ^ 0x9E3779B9u;
  if (!g->x) g->x = 1;
  for (int i = 0; i < 4; i++) rng_next(g);
}
static inline float rng_random(Rng *g) { return (float)(rng_next(g) >> 8) * (1.0f / 16777216); }   /* 0 <= u < 1 */
static inline float rng_uniform(Rng *g, float a, float b) { return a + (b - a) * rng_random(g); }
static inline int rng_int(Rng *g, int a, int b) {                                               /* a <= n < b */
  return a + (int)(((uint64_t)(rng_next(g) >> 8) * (uint32_t)(b - a)) >> 24);
}
