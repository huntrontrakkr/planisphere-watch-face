/* The face's arithmetic (plan_math.h): single precision approximations, the same wherever they run in plain IEEE
 * arithmetic (build without fused multiply-adds: -ffp-contract=off). */
#include "plan_math.h"
#include <string.h>

/* Built for size: little of this runs per pixel, and the app's code must stay under 64 KB. */
#if defined(__arm__)
#pragma GCC optimize("Os")
#endif

int pyf_round(float x) {
  int n = pyf_floor(x);
  float d = x - (float)n;
  if (d > 0.5f) return n + 1;
  if (d < 0.5f) return n;
  return (n & 1) ? n + 1 : n;
}

/* ---- single precision, approximate (a few parts in ten million) and the same everywhere ---------------------- */
static uint32_t fbits(float x) { uint32_t u; memcpy(&u, &x, 4); return u; }
static float ffrom(uint32_t u) { float x; memcpy(&x, &u, 4); return x; }

float f_sqrt(float x) {
  if (!(x > 0.0f)) return 0.0f;
  float y = ffrom(0x5f3759dfu - (fbits(x) >> 1));          /* 1/sqrt(x), refined three times, then x/sqrt(x) */
  for (int i = 0; i < 3; i++) y = y * (1.5f - 0.5f * x * y * y);
  float r = x * y;
  return 0.5f * (r + x / r);
}

float f_exp(float x) {
  if (x < -87.0f) return 0.0f;
  if (x > 88.0f) x = 88.0f;
  float t = x * 1.44269504f;                                  /* x / ln 2 = n + f */
  int n = (int)(t < 0 ? t - 0.5f : t + 0.5f);
  float r = x - (float)n * 0.693145752f - (float)n * 1.42860677e-6f;
  float p = 1.0f + r * (1.0f + r * (0.5f + r * (0.166666672f + r * (0.0416666679f + r * (0.00833333377f + r * 0.00138888892f)))));
  return p * ffrom((uint32_t)(n + 127) << 23);
}

float f_log(float x) {
  if (!(x > 0.0f)) return -1e30f;
  uint32_t u = fbits(x);
  int e = (int)((u >> 23) & 255) - 127;
  float m = ffrom((u & 0x007fffffu) | 0x3f800000u);         /* 1 <= m < 2 */
  if (m > 1.41421356f) { m *= 0.5f; e++; }
  float s = (m - 1.0f) / (m + 1.0f), s2 = s * s;
  float l = 2.0f * s * (1.0f + s2 * (0.333333343f + s2 * (0.2f + s2 * (0.142857149f + s2 * 0.111111112f))));
  return l + (float)e * 0.693147182f;
}

float f_pow(float x, float y) { return x > 0.0f ? f_exp(y * f_log(x)) : 0.0f; }

/* sine and cosine of x radians for |x| <= pi/4 (Taylor to x^9 and x^10: within 2e-9 there) */
static float sin_kernel(float x) {
  float z = x * x;
  return x * (1.0f + z * (-0.166666672f + z * (0.00833333377f + z * (-0.000198412701f + z * 2.75573188e-6f))));
}
static float cos_kernel(float x) {
  float z = x * x;
  return 1.0f + z * (-0.5f + z * (0.0416666679f + z * (-0.00138888892f + z * (2.48015876e-5f + z * -2.75573188e-7f))));
}
/* sin of a (2^-20 of a turn), Q30 (proto/iq.py isin_q30, bit for bit) */
int32_t isin_q30(uint32_t a) {
  static const int64_t Q[5] = {1686629681, -693597962, 85565130, -5017110, 162088};   /* sin(pi x / 2) on 0..1 */
  a &= BRAD_TURN - 1;
  uint32_t q = a >> 18, f = a & (BRAD_QUARTER - 1);
  if (q & 1) f = BRAD_QUARTER - f;
  int64_t x = (int64_t)f << 12, x2 = (x * x) >> 30, acc = Q[4];
  for (int k = 3; k >= 0; k--) acc = Q[k] + ((x2 * acc) >> 30);
  int64_t s = (x * acc) >> 30;
  return (int32_t)(q >= 2 ? -s : s);
}

/* atan z for z in Q16, 0..1, in 2^-20 of a turn (proto/iq.py atan_q): an odd polynomial of degree 11, Q14, within
 * 1.3 units */
static int32_t atan_q(uint32_t z) {
  static const int64_t Q[6] = {2734205957, -909566774, 529544042, -318951500, 144429673, -32182182};
  int64_t z2 = ((int64_t)z * z) >> 16, acc = Q[5];
  for (int k = 4; k >= 0; k--) acc = Q[k] + ((z2 * acc) >> 16);
  return (int32_t)(((int64_t)z * acc) >> 30);
}
int32_t iatan2_brad(int32_t y, int32_t x) {
  uint32_t ax = (uint32_t)(x < 0 ? -x : x), ay = (uint32_t)(y < 0 ? -y : y);
  if (!ax && !ay) return 0;
  int32_t a = ay <= ax ? atan_q((ay << 16) / ax) : (int32_t)BRAD_QUARTER - atan_q((ax << 16) / ay);
  if (x < 0) a = (int32_t)(BRAD_TURN / 2) - a;
  return y < 0 ? -a : a;
}
int32_t iasin_brad(int32_t s) {
  int32_t s15 = s >> 15;                                       /* (floors: the same on both sides) */
  if (s15 > 32768) s15 = 32768;
  if (s15 < -32768) s15 = -32768;
  return iatan2_brad(s15, (int32_t)isqrt32((uint32_t)((1 << 30) - s15 * s15)));
}

float f_sind(float deg) {
  float a = deg - 360.0f * (float)(int)(deg * (1.0f / 360));  /* -360 < a < 360 */
  if (a >= 180.0f) a -= 360.0f;
  else if (a < -180.0f) a += 360.0f;
  /* to within 45 degrees of an axis, then the kernel for that axis */
  if (a > 135.0f) return -sin_kernel((a - 180.0f) * 0.0174532925f);
  if (a > 45.0f) return cos_kernel((a - 90.0f) * 0.0174532925f);
  if (a >= -45.0f) return sin_kernel(a * 0.0174532925f);
  if (a >= -135.0f) return -cos_kernel((a + 90.0f) * 0.0174532925f);
  return -sin_kernel((a + 180.0f) * 0.0174532925f);
}
float f_cosd(float deg) { return f_sind(deg + 90.0f); }

/* Abramowitz and Stegun 4.4.49: the arctangent of 0 <= z <= 1, radians, within 2e-8 */
static float atan_kernel(float z) {
  float s = z * z;
  return z * (1.0f + s * (-0.3333314528f + s * (0.1999355085f + s * (-0.1420889944f + s * (0.1065626393f
              + s * (-0.0752896400f + s * (0.0429096138f + s * (-0.0161657367f + s * 0.0028662257f))))))));
}
float f_atan2d(float y, float x) {
  float ax = x < 0 ? -x : x, ay = y < 0 ? -y : y;
  if (ax == 0.0f && ay == 0.0f) return x < 0 ? (y < 0 ? -180.0f : 180.0f) : 0.0f;
  float a = ay <= ax ? atan_kernel(ay / ax) : 1.57079633f - atan_kernel(ax / ay);
  if (x < 0) a = 3.14159265f - a;
  if (y < 0) a = -a;
  return a * 57.2957795f;
}

/* Abramowitz and Stegun 4.4.46: acos(x) for 0 <= x <= 1, within 2e-8 */
static float acos_kernel(float x) {
  float p = 1.5707963050f + x * (-0.2145988016f + x * (0.0889789874f + x * (-0.0501743046f + x * (0.0308918810f
            + x * (-0.0170881256f + x * (0.0066700901f + x * -0.0012624911f))))));
  return f_sqrt(1.0f - x) * p;
}
float f_acosd(float x) {
  x = f_clamp(x, -1.0f, 1.0f);
  float a = x >= 0 ? acos_kernel(x) : 3.14159265f - acos_kernel(-x);
  return a * 57.2957795f;
}
float f_asind(float x) { return 90.0f - f_acosd(x); }
