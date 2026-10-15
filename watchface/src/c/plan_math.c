/* The face's arithmetic (plan_math.h). The double precision functions are fdlibm's (FreeBSD msun), as
 * Groundtrack carries them, in plain IEEE arithmetic; build without fused multiply-adds (-ffp-contract=off).
 *
 * Copyright (C) 1993 by Sun Microsystems, Inc. All rights reserved.
 * Developed at SunPro, a Sun Microsystems, Inc. business. Permission to use, copy, modify, and distribute this
 * software is freely granted, provided that this notice is preserved.
 */
#include "plan_math.h"
#include <string.h>

/* Built for size: little of this runs per pixel, and the app's code must stay under 64 KB. */
#if defined(__arm__)
#pragma GCC optimize("Os")
#endif

static uint32_t high(double x) { uint64_t u; memcpy(&u, &x, 8); return (uint32_t)(u >> 32); }
static uint32_t low(double x) { uint64_t u; memcpy(&u, &x, 8); return (uint32_t)u; }
static double from_words(uint32_t hi, uint32_t lo) { uint64_t u = (uint64_t)hi << 32 | lo; double x; memcpy(&x, &u, 8); return x; }
static double nan_(void) { return from_words(0x7ff80000u, 0); }

double m_fabs(double x) { return from_words(high(x) & 0x7fffffffu, low(x)); }

double m_floor(double x) {
  if (!(x > -9.0e15 && x < 9.0e15)) return x;
  double t = (double)(int64_t)x;
  return t > x ? t - 1 : t;
}

int py_round(double x) {
  double f = m_floor(x), d = x - f;
  int n = (int)f;
  if (d > 0.5) return n + 1;
  if (d < 0.5) return n;
  return (n & 1) ? n + 1 : n;
}

int pyf_round(float x) {
  int n = pyf_floor(x);
  float d = x - (float)n;
  if (d > 0.5f) return n + 1;
  if (d < 0.5f) return n;
  return (n & 1) ? n + 1 : n;
}

/* fdlibm's e_sqrt.c: correctly rounded, bit by bit in integers */
double m_sqrt(double x) {
  int32_t ix0 = (int32_t)high(x), s0, q, m, t, i;
  uint32_t r, t1, s1, ix1 = low(x), q1;
  const int32_t sign = (int32_t)0x80000000;
  if ((ix0 & 0x7ff00000) == 0x7ff00000) return x * x + x;
  if (ix0 <= 0) {
    if (((ix0 & (~sign)) | ix1) == 0) return x;
    else if (ix0 < 0) return nan_();
  }
  m = (ix0 >> 20);
  if (m == 0) {
    while (ix0 == 0) { m -= 21; ix0 |= (int32_t)(ix1 >> 11); ix1 <<= 21; }
    for (i = 0; (ix0 & 0x00100000) == 0; i++) ix0 <<= 1;
    m -= i - 1; ix0 |= (int32_t)(ix1 >> (32 - i)); ix1 <<= i;
  }
  m -= 1023; ix0 = (ix0 & 0x000fffff) | 0x00100000;
  if (m & 1) { ix0 += ix0 + (int32_t)((ix1 & (uint32_t)sign) >> 31); ix1 += ix1; }
  m >>= 1;
  ix0 += ix0 + (int32_t)((ix1 & (uint32_t)sign) >> 31); ix1 += ix1;
  q = s0 = 0; q1 = s1 = 0; r = 0x00200000;
  while (r != 0) {
    t = s0 + (int32_t)r;
    if (t <= ix0) { s0 = t + (int32_t)r; ix0 -= t; q += (int32_t)r; }
    ix0 += ix0 + (int32_t)((ix1 & (uint32_t)sign) >> 31); ix1 += ix1; r >>= 1;
  }
  r = (uint32_t)sign;
  while (r != 0) {
    t1 = s1 + r; t = s0;
    if ((t < ix0) || ((t == ix0) && (t1 <= ix1))) {
      s1 = t1 + r;
      if (((t1 & (uint32_t)sign) == (uint32_t)sign) && (s1 & (uint32_t)sign) == 0) s0 += 1;
      ix0 -= t; if (ix1 < t1) ix0 -= 1; ix1 -= t1; q1 += r;
    }
    ix0 += ix0 + (int32_t)((ix1 & (uint32_t)sign) >> 31); ix1 += ix1; r >>= 1;
  }
  if ((ix0 | (int32_t)ix1) != 0) {
    if (q1 == (uint32_t)0xffffffff) { q1 = 0; q += 1; }
    else if (q1 == (uint32_t)0xfffffffe) { q1 += 2; }
    else q1 += (q1 & 1);
  }
  ix0 = (q >> 1) + 0x3fe00000; ix1 = q1 >> 1;
  if (q & 1) ix1 |= (uint32_t)sign;
  ix0 += (m << 20);
  return from_words((uint32_t)ix0, ix1);
}

static const double S1 = -1.66666666666666324348e-01, S2 = 8.33333333332248946124e-03, S3 = -1.98412698298579493134e-04,
  S4 = 2.75573137070700676789e-06, S5 = -2.50507602534068634195e-08, S6 = 1.58969099521155010221e-10;
static const double C1 = 4.16666666666666019037e-02, C2 = -1.38888888888741095749e-03, C3 = 2.48015872894767294178e-05,
  C4 = -2.75573143513906633035e-07, C5 = 2.08757232129817482790e-09, C6 = -1.13596475577881948265e-11;
static const double INVPIO2 = 6.36619772367581382433e-01, PIO2_1 = 1.57079632673412561417e+00,
  PIO2_1T = 6.07710050650619224932e-11, PIO2_2 = 6.07710050630396597660e-11, PIO2_2T = 2.02226624879595063154e-21,
  PIO2_3 = 2.02226624871116645580e-21, PIO2_3T = 8.47842766036889956997e-32, ROUND = 6755399441055744.0,
  TWO_PI = 6.28318530717958647692;

static double kernel_sin(double x, double y, int iy) {
  const double z = x * x, w = z * z, r = S2 + z * (S3 + z * S4) + z * w * (S5 + z * S6), v = z * x;
  if (iy == 0) return x + v * (S1 + z * r);
  return x - ((z * (0.5 * y - v * r) - y) - v * S1);
}
static double kernel_cos(double x, double y) {
  const double z = x * x;
  double w = z * z;
  const double r = z * (C1 + z * (C2 + z * C3)) + w * w * (C4 + z * (C5 + z * C6)), hz = 0.5 * z;
  w = 1.0 - hz;
  return w + (((1.0 - w) - hz) + (z * r - x * y));
}
static int reduce(double x, double *y0, double *y1) {
  if (m_fabs(x) > 1e6) x = py_mod(x, TWO_PI);
  volatile double t0 = x * INVPIO2 + ROUND;
  const double fn = t0 - ROUND;
  const int n = (int)fn;
  double r = x - fn * PIO2_1, w = fn * PIO2_1T, y = r - w;
  const int j = (int)((high(x) >> 20) & 0x7ff);
  if (j - (int)((high(y) >> 20) & 0x7ff) > 16) {
    double t = r; w = fn * PIO2_2; r = t - w; w = fn * PIO2_2T - ((t - r) - w); y = r - w;
    if (j - (int)((high(y) >> 20) & 0x7ff) > 49) { t = r; w = fn * PIO2_3; r = t - w; w = fn * PIO2_3T - ((t - r) - w); y = r - w; }
  }
  *y0 = y; *y1 = (r - y) - w;
  return n;
}
double m_sin(double x) {
  const uint32_t ix = high(x) & 0x7fffffff;
  if (ix <= 0x3fe921fb) { if (ix < 0x3e500000) return x; return kernel_sin(x, 0, 0); }
  if (ix >= 0x7ff00000) return nan_();
  double a, b;
  const int n = reduce(x, &a, &b);
  switch (n & 3) {
  case 0: return kernel_sin(a, b, 1);
  case 1: return kernel_cos(a, b);
  case 2: return -kernel_sin(a, b, 1);
  default: return -kernel_cos(a, b);
  }
}
double m_cos(double x) {
  const uint32_t ix = high(x) & 0x7fffffff;
  if (ix <= 0x3fe921fb) { if (ix < 0x3e46a09e) return 1.0; return kernel_cos(x, 0); }
  if (ix >= 0x7ff00000) return nan_();
  double a, b;
  const int n = reduce(x, &a, &b);
  switch (n & 3) {
  case 0: return kernel_cos(a, b);
  case 1: return -kernel_sin(a, b, 1);
  case 2: return -kernel_cos(a, b);
  default: return kernel_sin(a, b, 1);
  }
}

static const double PIO2_HI = 1.57079632679489655800e+00, PIO2_LO = 6.12323399573676603587e-17,
  PIO4_HI = 7.85398163397448278999e-01, PI_ = 3.14159265358979311600e+00, PS0 = 1.66666666666666657415e-01,
  PS1 = -3.25565818622400915405e-01, PS2 = 2.01212532134862925881e-01, PS3 = -4.00555345006794114027e-02,
  PS4 = 7.91534994289814532176e-04, PS5 = 3.47933107596021167570e-05, QS1 = -2.40339491173441421878e+00,
  QS2 = 2.02094576023350569471e+00, QS3 = -6.88283971605453293030e-01, QS4 = 7.70381505559019352791e-02;
static double high_only(double x) { return from_words(high(x), 0); }
static double rat_p(double t) { return t * (PS0 + t * (PS1 + t * (PS2 + t * (PS3 + t * (PS4 + t * PS5))))); }
static double rat_q(double t) { return 1.0 + t * (QS1 + t * (QS2 + t * (QS3 + t * QS4))); }
double m_asin(double x) {
  const int32_t hx = (int32_t)high(x), ix = hx & 0x7fffffff;
  if (ix >= 0x3ff00000) {
    if (((ix - 0x3ff00000) | (int32_t)low(x)) == 0) return x * PIO2_HI + x * PIO2_LO;
    return nan_();
  }
  if (ix < 0x3fe00000) {
    if (ix < 0x3e400000) return x;
    const double t = x * x, w = rat_p(t) / rat_q(t);
    return x + x * w;
  }
  double w = 1.0 - m_fabs(x), t = w * 0.5;
  const double p = rat_p(t), q = rat_q(t), s = m_sqrt(t);
  if (ix >= 0x3FEF3333) { w = p / q; t = PIO2_HI - (2.0 * (s + s * w) - PIO2_LO); }
  else {
    w = high_only(s);
    const double c = (t - w * w) / (s + w), r = p / q, pp = 2.0 * s * r - (PIO2_LO - 2.0 * c), qq = PIO4_HI - 2.0 * w;
    t = PIO4_HI - (pp - qq);
  }
  return hx > 0 ? t : -t;
}
double m_acos(double x) {
  const int32_t hx = (int32_t)high(x), ix = hx & 0x7fffffff;
  if (ix >= 0x3ff00000) {
    if (((ix - 0x3ff00000) | (int32_t)low(x)) == 0) return hx > 0 ? 0.0 : PI_ + 2.0 * PIO2_LO;
    return nan_();
  }
  if (ix < 0x3fe00000) {
    if (ix <= 0x3c600000) return PIO2_HI + PIO2_LO;
    const double z = x * x, r = rat_p(z) / rat_q(z);
    return PIO2_HI - (x - (PIO2_LO - x * r));
  }
  if (hx < 0) {
    const double z = (1.0 + x) * 0.5, s = m_sqrt(z), r = rat_p(z) / rat_q(z), w = r * s - PIO2_LO;
    return PI_ - 2.0 * (s + w);
  }
  const double z = (1.0 - x) * 0.5, s = m_sqrt(z), df = high_only(s), c = (z - df * df) / (s + df),
               r = rat_p(z) / rat_q(z), w = r * s + c;
  return 2.0 * (df + w);
}
static const double ATANHI[4] = {4.63647609000806093515e-01, 7.85398163397448278999e-01, 9.82793723247329054082e-01,
                                 1.57079632679489655800e+00},
  ATANLO[4] = {2.26987774529616870924e-17, 3.06161699786838301793e-17, 1.39033110312309984516e-17,
               6.12323399573676603587e-17},
  AT[11] = {3.33333333333329318027e-01, -1.99999999998764832476e-01, 1.42857142725034663711e-01,
            -1.11111104054623557880e-01, 9.09088713343650656196e-02, -7.69187620504482999495e-02,
            6.66107313738753120669e-02, -5.83357013379057348645e-02, 4.97687799461593236017e-02,
            -3.65315727442169155270e-02, 1.62858201153657823623e-02};
double m_atan(double x) {
  const int32_t hx = (int32_t)high(x), ix = hx & 0x7fffffff;
  int id;
  if (ix >= 0x44100000) {
    if (x != x) return x + x;
    return hx > 0 ? ATANHI[3] + ATANLO[3] : -ATANHI[3] - ATANLO[3];
  }
  if (ix < 0x3fdc0000) { if (ix < 0x3e200000) return x; id = -1; }
  else {
    x = m_fabs(x);
    if (ix < 0x3ff30000) {
      if (ix < 0x3fe60000) { id = 0; x = (2.0 * x - 1.0) / (2.0 + x); }
      else { id = 1; x = (x - 1.0) / (x + 1.0); }
    } else if (ix < 0x40038000) { id = 2; x = (x - 1.5) / (1.0 + 1.5 * x); }
    else { id = 3; x = -1.0 / x; }
  }
  const double z = x * x, w = z * z, s1 = z * (AT[0] + w * (AT[2] + w * (AT[4] + w * (AT[6] + w * (AT[8] + w * AT[10]))))),
               s2 = w * (AT[1] + w * (AT[3] + w * (AT[5] + w * (AT[7] + w * AT[9]))));
  if (id < 0) return x - x * (s1 + s2);
  const double r = ATANHI[id] - ((x * (s1 + s2) - ATANLO[id]) - x);
  return hx < 0 ? -r : r;
}
static const double PI_O_4 = 7.8539816339744827900E-01, PI_O_2 = 1.5707963267948965580E+00,
  PI_LO = 1.2246467991473531772E-16, TINY = 1.0e-300;
double m_atan2(double y, double x) {
  if (x != x || y != y) return x + y;
  const int32_t hx = (int32_t)high(x), ix = hx & 0x7fffffff, hy = (int32_t)high(y), iy = hy & 0x7fffffff;
  const uint32_t lx = low(x), ly = low(y);
  if ((((uint32_t)hx - 0x3ff00000u) | lx) == 0) return m_atan(y);
  const int m = (int)((((uint32_t)hy >> 31) & 1) | (((uint32_t)hx >> 30) & 2));
  if (((uint32_t)iy | ly) == 0) { if (m <= 1) return y; return m == 2 ? PI_ + TINY : -PI_ - TINY; }
  if (((uint32_t)ix | lx) == 0) return hy < 0 ? -PI_O_2 - TINY : PI_O_2 + TINY;
  if (ix == 0x7ff00000) {
    if (iy == 0x7ff00000) {
      const double v[4] = {PI_O_4 + TINY, -PI_O_4 - TINY, 3.0 * PI_O_4 + TINY, -3.0 * PI_O_4 - TINY};
      return v[m];
    }
    const double v[4] = {0.0, -0.0, PI_ + TINY, -PI_ - TINY};
    return v[m];
  }
  if (iy == 0x7ff00000) return hy < 0 ? -PI_O_2 - TINY : PI_O_2 + TINY;
  const int k = (iy - ix) >> 20;
  double z;
  if (k > 60) z = PI_O_2 + 0.5 * PI_LO;
  else if (hx < 0 && k < -60) z = 0.0;
  else z = m_atan(m_fabs(y / x));
  switch (m) {
  case 0: return z;
  case 1: return -z;
  case 2: return PI_ - (z - PI_LO);
  default: return (z - PI_LO) - PI_;
  }
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

/* sine of x radians for |x| <= pi/2 */
static float sin_kernel(float x) {
  float z = x * x;
  return x * (1.0f + z * (-0.166666672f + z * (0.00833333377f + z * (-0.000198412701f + z * 2.75573188e-6f))));
}
float f_sind(float deg) {
  float a = deg - 360.0f * (float)(int)(deg * (1.0f / 360));  /* -360 < a < 360 */
  if (a >= 180.0f) a -= 360.0f;
  else if (a < -180.0f) a += 360.0f;
  if (a > 90.0f) a = 180.0f - a;
  else if (a < -90.0f) a = -180.0f - a;
  return sin_kernel(a * 0.0174532925f);
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
