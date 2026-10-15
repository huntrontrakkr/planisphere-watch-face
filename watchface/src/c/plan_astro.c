/* Where things are in the sky, as the prototype finds them (proto/astro.py, proto/lunar.py): the Sun and the Moon
 * from Meeus (Astronomical Algorithms, ch. 47 and 25, nutation from ch. 22) in dynamical time, the planets from
 * Paul Schlyter's elements with Jupiter's and Saturn's great inequality. Degrees throughout.
 *
 * In single precision, as the watch has room for: the angles that turn fast (the Moon's arguments, sidereal time,
 * the planets' mean anomalies) are kept as binary angles (2^32ths of a turn), advanced from J2000.0 by exact 64-bit
 * integer arithmetic, so no large angle is ever held in a float; what is left is small. Within 0.001 degree of the
 * prototype's double precision: well under a pixel. */
#include "plan.h"
#include "plan_math.h"

#if defined(__arm__)
#pragma GCC optimize("Os")
#endif

#define J2000 946728000              /* 2000-01-01 12:00 UTC, as seconds since 1970 */
#define CENTURY 3155760000.0f        /* seconds in a Julian century */

/* the fast angles at J2000.0 (2^32ths of a turn) and their rates (2^64ths of a turn a second), from the formulae's
 * degrees (in the comments) exactly */
enum { A_MOON_LP, A_MOON_D, A_MOON_M, A_MOON_MP, A_MOON_F, A_MOON_A1, A_MOON_A2, A_MOON_A3, A_SUN_L0, A_SUN_M, A_NUT_OM,
       A_NUT_L, A_NUT_LP, A_NODE, A_SIDEREAL, A_M_SUN, A_M_MERCURY, A_M_VENUS, A_M_MARS, A_M_JUPITER, A_M_SATURN };
static const struct { uint32_t a0; int64_t rate; } ANGLES[21] = {
  {0x9b3f4be3u, 7814480889287LL},    /* the Moon's mean longitude: 218.3164477 + 481267.88123421 T */
  {0xd3cdf906u, 7229926343239LL},    /* its mean elongation D: 297.8501921 + 445267.1114034 T */
  {0xfe3e3025u, 584526625399LL},     /* the Sun's mean anomaly M: 357.5291092 + 35999.0502909 T */
  {0x5ff95626u, 7748411177883LL},    /* the Moon's mean anomaly M': 134.9633964 + 477198.8675055 T */
  {0x4253aaaeu, 7845885999950LL},    /* its argument of latitude F: 93.2720950 + 483202.0175233 T */
  {0x5527d27du, 2140869007LL},       /* A1: 119.75 + 131.849 T */
  {0x25c0bd54u, 7781948019299LL},    /* A2: 53.09 + 479264.290 T */
  {0xdee5d4c4u, 7814458202006LL},    /* A3: 313.45 + 481266.484 T */
  {0xc7715c64u, 584554546035LL},     /* the Sun's mean longitude L0: 280.46646 + 36000.76983 T */
  {0xfe3e302eu, 584526625384LL},     /* its mean anomaly: 357.52911 + 35999.05029 T */
  {0x58eba901u, -31405110206LL},     /* nutation's node: 125.04452 - 1934.136261 T */
  {0xc7715e41u, 584554545548LL},     /* L: 280.4665 + 36000.7698 T */
  {0x9b3f4e53u, 7814480890356LL},    /* L': 218.3165 + 481267.8813 T */
  {0x58ebaa4eu, -31405110662LL},     /* the Moon's mean node: 125.0445479 - 1934.1362891 T */
  {0xc7704c26u, 214088536884269LL},  /* sidereal time at Greenwich: 280.46061837 + 360.98564736629 d */
  {0xfe3d834du, 584526611610LL},     /* Schlyter's Sun, M: 356.0470 + 0.9856002585 d (d from 2000 Jan 0.0) */
  {0x7c4c6784u, 2427026942505LL},    /* Mercury: 168.6562 + 4.0923344368 d */
  {0x23d8917eu, 950169953133LL},     /* Venus: 48.0052 + 1.6021302244 d */
  {0x0dc98067u, 310779229528LL},     /* Mars: 18.6021 + 0.5240207766 d */
  {0x0e3c7649u, 49275117902LL},      /* Jupiter: 19.8950 + 0.0830853001 d */
  {0xe16f36c4u, 19834655297LL},      /* Saturn: 316.9670 + 0.0334442282 d */
};

/* degrees as a binary angle (taken to within half a turn first, as a signed 32-bit number holds it) */
static uint32_t bam(float d) { return (uint32_t)(int32_t)((pyf_mod(d + 180, 360) - 180) * 11930464.71f); }
/* a binary angle in degrees, 0..360 */
static float deg(uint32_t a) { return (float)(a >> 8) * (360.0f / 16777216.0f); }
/* a fast angle at `t` seconds from J2000.0, plus a correction in degrees: a binary angle */
static uint32_t angle(int i, int32_t t, float plus) {
  uint64_t q = (uint64_t)ANGLES[i].rate * (uint64_t)(int64_t)t;
  return ANGLES[i].a0 + (uint32_t)(q >> 32) + bam(plus);
}
static float rev(float a) { return pyf_mod(a, 360); }

/* Table 47.A: D, M, M', F; the longitude (1e-6 degree) and distance (0.001 km) coefficients */
static const int8_t LR_ARG[60][4] = {
  {0, 0, 1, 0}, {2, 0, -1, 0}, {2, 0, 0, 0}, {0, 0, 2, 0}, {0, 1, 0, 0}, {0, 0, 0, 2}, {2, 0, -2, 0}, {2, -1, -1, 0},
  {2, 0, 1, 0}, {2, -1, 0, 0}, {0, 1, -1, 0}, {1, 0, 0, 0}, {0, 1, 1, 0}, {2, 0, 0, -2}, {0, 0, 1, 2}, {0, 0, 1, -2},
  {4, 0, -1, 0}, {0, 0, 3, 0}, {4, 0, -2, 0}, {2, 1, -1, 0}, {2, 1, 0, 0}, {1, 0, -1, 0}, {1, 1, 0, 0}, {2, -1, 1, 0},
  {2, 0, 2, 0}, {4, 0, 0, 0}, {2, 0, -3, 0}, {0, 1, -2, 0}, {2, 0, -1, 2}, {2, -1, -2, 0}, {1, 0, 1, 0}, {2, -2, 0, 0},
  {0, 1, 2, 0}, {0, 2, 0, 0}, {2, -2, -1, 0}, {2, 0, 1, -2}, {2, 0, 0, 2}, {4, -1, -1, 0}, {0, 0, 2, 2}, {3, 0, -1, 0},
  {2, 1, 1, 0}, {4, -1, -2, 0}, {0, 2, -1, 0}, {2, 2, -1, 0}, {2, 1, -2, 0}, {2, -1, 0, -2}, {4, 0, 1, 0}, {0, 0, 4, 0},
  {4, -1, 0, 0}, {1, 0, -2, 0}, {2, 1, 0, -2}, {0, 0, 2, -2}, {1, 1, 1, 0}, {3, 0, -2, 0}, {4, 0, -3, 0}, {2, -1, 2, 0},
  {0, 2, 1, 0}, {1, 1, -1, 0}, {2, 0, 3, 0}, {2, 0, -1, -2}};
static const int32_t LR_L[60] = {
  6288774, 1274027, 658314, 213618, -185116, -114332, 58793, 57066, 53322, 45758, -40923, -34720, -30383, 15327,
  -12528, 10980, 10675, 10034, 8548, -7888, -6766, -5163, 4987, 4036, 3994, 3861, 3665, -2689, -2602, 2390, -2348,
  2236, -2120, -2069, 2048, -1773, -1595, 1215, -1110, -892, -810, 759, -713, -700, 691, 596, 549, 537, 520, -487,
  -399, -381, 351, -340, 330, 327, -323, 299, 294, 0};
static const int32_t LR_R[60] = {
  -20905355, -3699111, -2955968, -569925, 48888, -3149, 246158, -152138, -170733, -204586, -129620, 108743, 104755,
  10321, 0, 79661, -34782, -23210, -21636, 24208, 30824, -8379, -16675, -12831, -10445, -11650, 14403, -7003, 0,
  10056, 6322, -9884, 5751, 0, -4950, 4130, 0, -3958, 0, 3258, 2616, -1897, -2117, 2354, 0, 0, -1423, -1117, -1571,
  -1739, 0, -4421, 0, 0, 0, 0, 1165, 0, 0, 8752};
/* Table 47.B: D, M, M', F; the latitude coefficients (1e-6 degree) */
static const int8_t B_ARG[60][4] = {
  {0, 0, 0, 1}, {0, 0, 1, 1}, {0, 0, 1, -1}, {2, 0, 0, -1}, {2, 0, -1, 1}, {2, 0, -1, -1}, {2, 0, 0, 1}, {0, 0, 2, 1},
  {2, 0, 1, -1}, {0, 0, 2, -1}, {2, -1, 0, -1}, {2, 0, -2, -1}, {2, 0, 1, 1}, {2, 1, 0, -1}, {2, -1, -1, 1},
  {2, -1, 0, 1}, {2, -1, -1, -1}, {0, 1, -1, -1}, {4, 0, -1, -1}, {0, 1, 0, 1}, {0, 0, 0, 3}, {0, 1, -1, 1},
  {1, 0, 0, 1}, {0, 1, 1, 1}, {0, 1, 1, -1}, {0, 1, 0, -1}, {1, 0, 0, -1}, {0, 0, 3, 1}, {4, 0, 0, -1}, {4, 0, -1, 1},
  {0, 0, 1, -3}, {4, 0, -2, 1}, {2, 0, 0, -3}, {2, 0, 2, -1}, {2, -1, 1, -1}, {2, 0, -2, 1}, {0, 0, 3, -1},
  {2, 0, 2, 1}, {2, 0, -3, -1}, {2, 1, -1, 1}, {2, 1, 0, 1}, {4, 0, 0, 1}, {2, -1, 1, 1}, {2, -2, 0, -1},
  {0, 0, 1, 3}, {2, 1, 1, -1}, {1, 1, 0, -1}, {1, 1, 0, 1}, {0, 1, -2, -1}, {2, 1, -1, -1}, {1, 0, 1, 1},
  {2, -1, -2, -1}, {0, 1, 2, 1}, {4, 0, -2, -1}, {4, -1, -1, -1}, {1, 0, 1, -1}, {4, 0, 1, -1}, {1, 0, -1, -1},
  {4, -1, 0, -1}, {2, -2, 0, 1}};
static const int32_t B_B[60] = {
  5128122, 280602, 277693, 173237, 55413, 46271, 32573, 17198, 9266, 8822, 8216, 4324, 4200, -3359, 2463, 2211, 2065,
  -1870, 1828, -1794, -1749, -1565, -1491, -1475, -1410, -1344, -1335, 1107, 1021, 833, 777, 671, 607, 596, 491, -451,
  439, 422, 421, -366, -351, 331, 315, 302, -283, -229, 223, 223, -220, -220, -185, 181, -177, 176, 166, -164, 132,
  -119, 115, 107};

/* the moment in dynamical time (TT = UT + delta T, about 69 s these decades), seconds from J2000.0 */
static int32_t tt_of(int32_t t) {
  float year = 2000.0f + (float)t / 31557600.0f;
  return t + (int32_t)(69.2f + 0.25f * ((float)(int)year - 2025) + 0.5f);
}

/* a term's argument: D, M, M' and F so many times over */
static uint32_t term(const int8_t a[4], uint32_t D, uint32_t M, uint32_t Mp, uint32_t F) {
  return (uint32_t)(int32_t)a[0] * D + (uint32_t)(int32_t)a[1] * M + (uint32_t)(int32_t)a[2] * Mp + (uint32_t)(int32_t)a[3] * F;
}

/* the Moon's geocentric ecliptic longitude and latitude of date (without nutation) and distance (km) */
static void moon(int32_t tt, float *lam, float *beta, float *dist) {
  float T = (float)tt / CENTURY, T2 = T * T, T3 = T2 * T, T4 = T3 * T;
  uint32_t Lp = angle(A_MOON_LP, tt, -0.0015786f * T2 + T3 / 538841 - T4 / 65194000);
  uint32_t D = angle(A_MOON_D, tt, -0.0018819f * T2 + T3 / 545868 - T4 / 113065000);
  uint32_t M = angle(A_MOON_M, tt, -0.0001536f * T2 + T3 / 24490000);
  uint32_t Mp = angle(A_MOON_MP, tt, 0.0087414f * T2 + T3 / 69699 - T4 / 14712000);
  uint32_t F = angle(A_MOON_F, tt, -0.0036539f * T2 - T3 / 3526000 + T4 / 863310000.0f);
  uint32_t A1 = angle(A_MOON_A1, tt, 0), A2 = angle(A_MOON_A2, tt, 0), A3 = angle(A_MOON_A3, tt, 0);
  float E = 1 - 0.002516f * T - 0.0000074f * T2, EE[3] = {1, E, E * E};
  float sl = 0, sr = 0, sb = 0;
  for (int i = 0; i < 60; i++) {
    float e = EE[LR_ARG[i][1] < 0 ? -LR_ARG[i][1] : LR_ARG[i][1]], a = deg(term(LR_ARG[i], D, M, Mp, F));
    if (LR_L[i]) sl += (float)LR_L[i] * e * f_sind(a);
    if (LR_R[i]) sr += (float)LR_R[i] * e * f_cosd(a);
    sb += (float)B_B[i] * EE[B_ARG[i][1] < 0 ? -B_ARG[i][1] : B_ARG[i][1]] * f_sind(deg(term(B_ARG[i], D, M, Mp, F)));
  }
  sl += 3958 * f_sind(deg(A1)) + 1962 * f_sind(deg(Lp - F)) + 318 * f_sind(deg(A2));
  sb += -2235 * f_sind(deg(Lp)) + 382 * f_sind(deg(A3)) + 175 * f_sind(deg(A1 - F)) + 175 * f_sind(deg(A1 + F)) +
        127 * f_sind(deg(Lp - Mp)) - 115 * f_sind(deg(Lp + Mp));
  *lam = deg(Lp + bam(sl / 1e6f));
  *beta = sb / 1e6f;
  *dist = 385000.56f + sr / 1000;
}

/* the Sun's apparent ecliptic longitude of date (with the aberration, without nutation), and its distance (AU) */
static uint32_t sun(int32_t tt, float *dist) {
  float T = (float)tt / CENTURY;
  uint32_t L0 = angle(A_SUN_L0, tt, 0.0003032f * T * T);
  float M = deg(angle(A_SUN_M, tt, -0.0001537f * T * T));
  float C = (1.914602f - 0.004817f * T - 0.000014f * T * T) * f_sind(M) + (0.019993f - 0.000101f * T) * f_sind(2 * M) +
            0.000289f * f_sind(3 * M);
  if (dist) {
    float e = 0.016708634f - 0.000042037f * T - 0.0000001267f * T * T;
    *dist = 1.000001018f * (1 - e * e) / (1 + e * f_cosd(M + C));
  }
  return L0 + bam(C - 0.00569f);
}

static void nutation(int32_t tt, float *dpsi, float *eps) {
  float T = (float)tt / CENTURY;
  float om = deg(angle(A_NUT_OM, tt, 0)), L = deg(angle(A_NUT_L, tt, 0)), Lp = deg(angle(A_NUT_LP, tt, 0));
  *dpsi = (-17.20f * f_sind(om) - 1.32f * f_sind(2 * L) - 0.23f * f_sind(2 * Lp) + 0.21f * f_sind(2 * om)) / 3600;
  float deps = (9.20f * f_cosd(om) + 0.57f * f_cosd(2 * L) + 0.10f * f_cosd(2 * Lp) - 0.09f * f_cosd(2 * om)) / 3600;
  *eps = 23.4392911f - 0.0130042f * T - 1.64e-7f * T * T + 5.04e-7f * T * T * T + deps;
}

float plan_moon_node(int64_t utc) {
  int32_t t = (int32_t)(utc - J2000);
  float T = (float)t / CENTURY;
  return deg(angle(A_NODE, t, 0.0020754f * T * T + T * T * T / 467441 - T * T * T * T / 60616000));
}

void plan_ecl_to_eq(float lon, float lat, float eps, float *ra, float *dec) {
  float cl = f_cosd(lat), sl = f_sind(lat), ce = f_cosd(eps), se = f_sind(eps);
  float x = f_cosd(lon) * cl, y = f_sind(lon) * cl * ce - sl * se, z = f_sind(lon) * cl * se + sl * ce;
  *ra = rev(f_atan2d(y, x));
  *dec = f_asind(z);
}

float plan_altitude(float ra, float dec, float lst, float lat) {
  return f_asind(f_sind(lat) * f_sind(dec) + f_cosd(lat) * f_cosd(dec) * f_cosd(lst - ra));
}

/* local sidereal time at east longitude `lon` */
static float sidereal(int32_t t, float lon) {
  float T = (float)t / CENTURY;
  return deg(angle(A_SIDEREAL, t, 0.000387933f * T * T - T * T * T / 38710000 + lon));
}

/* Schlyter's elements: N, i, w, a, e as (value, rate per day) from 2000 Jan 0.0 UT; M (fast) a binary angle */
enum { E_SUN, E_MERCURY, E_VENUS, E_MARS, E_JUPITER, E_SATURN };
static const float ELEMENTS[6][5][2] = {
  {{0, 0}, {0, 0}, {282.9404f, 4.70935e-5f}, {1.0f, 0}, {0.016709f, -1.151e-9f}},
  {{48.3313f, 3.24587e-5f}, {7.0047f, 5.00e-8f}, {29.1241f, 1.01444e-5f}, {0.387098f, 0}, {0.205635f, 5.59e-10f}},
  {{76.6799f, 2.46590e-5f}, {3.3946f, 2.75e-8f}, {54.8910f, 1.38374e-5f}, {0.723330f, 0}, {0.006773f, -1.302e-9f}},
  {{49.5574f, 2.11081e-5f}, {1.8497f, -1.78e-8f}, {286.5016f, 2.92961e-5f}, {1.523688f, 0}, {0.093405f, 2.516e-9f}},
  {{100.4542f, 2.76854e-5f}, {1.3030f, -1.557e-7f}, {273.8777f, 1.64505e-5f}, {5.20256f, 0}, {0.048498f, 4.469e-9f}},
  {{113.6634f, 2.38980e-5f}, {2.4886f, -1.081e-7f}, {339.3939f, 2.97661e-5f}, {9.55475f, 0}, {0.055546f, -9.499e-9f}},
};
static float element(int body, int k, float d) { return ELEMENTS[body][k][0] + ELEMENTS[body][k][1] * d; }

static float kepler(float M, float e) {
  float E = M + e * 57.2957795f * f_sind(M) * (1 + e * f_cosd(M));
  for (int i = 0; i < 8; i++) E = E - (E - e * 57.2957795f * f_sind(E) - M) / (1 - e * f_cosd(E));
  return E;
}

/* the body's heliocentric ecliptic position */
static void orbit(int body, float d, float M, float *x, float *y, float *z) {
  float N = element(body, 0, d), i = element(body, 1, d), w = element(body, 2, d), a = element(body, 3, d);
  float e = element(body, 4, d);
  float E = kepler(M, e);
  float xv = a * (f_cosd(E) - e), yv = a * f_sqrt(1 - e * e) * f_sind(E);
  float v = f_atan2d(yv, xv), r = f_sqrt(xv * xv + yv * yv);
  *x = r * (f_cosd(N) * f_cosd(v + w) - f_sind(N) * f_sind(v + w) * f_cosd(i));
  *y = r * (f_sind(N) * f_cosd(v + w) + f_cosd(N) * f_sind(v + w) * f_cosd(i));
  *z = r * f_sind(v + w) * f_sind(i);
}

/* the great inequality's terms: sine (or cosine) of a Mj + b Msat + c */
static float great(uint32_t Mj, uint32_t Msat, int a, int b, float c, bool cosine) {
  float x = deg((uint32_t)a * Mj + (uint32_t)b * Msat + bam(c));
  return cosine ? f_cosd(x) : f_sind(x);
}

/* the Sun and the Moon alone (for the eclipses' search through a day) */
void plan_sun_moon(Sky *s, int64_t utc, float lon) {
  int32_t t = (int32_t)(utc - J2000), tt = tt_of(t);
  s->utc = utc;
  s->lst = sidereal(t, lon);
  float dpsi, eps;
  nutation(tt, &dpsi, &eps);
  s->eps = eps;
  float lam_s = deg(sun(tt, &s->sun_dist) + bam(dpsi));
  float lam_m, beta_m, dist_km;
  moon(tt, &lam_m, &beta_m, &dist_km);
  lam_m = rev(lam_m + dpsi);
  plan_ecl_to_eq(lam_s, 0.0f, eps, &s->sun_ra, &s->sun_dec);
  s->sun_lon = lam_s;
  plan_ecl_to_eq(lam_m, beta_m, eps, &s->moon_ra, &s->moon_dec);
  s->moon_dist = dist_km / 6378.14f;
  s->moon_phase = (1 - f_cosd(lam_m - lam_s) * f_cosd(beta_m)) / 2;   /* (1 - cos elongation) / 2 */
  s->moon_waxing = rev(lam_m - lam_s) < 180;
}

void plan_sky(Sky *s, int64_t utc, float lon) {
  plan_sun_moon(s, utc, lon);
  int32_t t = (int32_t)(utc - J2000);
  float d = ((float)t + 1.5f * 86400) / 86400, eps = s->eps;      /* days from 2000 Jan 0.0 UT */
  /* Schlyter's Sun, to carry the planets from the Sun's frame to ours */
  float ws = element(E_SUN, 2, d), es = element(E_SUN, 4, d);
  float E = kepler(deg(angle(A_M_SUN, t, 0)), es);
  float xv = f_cosd(E) - es, yv = f_sqrt(1 - es * es) * f_sind(E);
  float v = f_atan2d(yv, xv), rs = f_sqrt(xv * xv + yv * yv);
  float lon_sun = rev(v + ws), xs = rs * f_cosd(lon_sun), ys = rs * f_sind(lon_sun);
  uint32_t Mj = angle(A_M_JUPITER, t, 0), Ms = angle(A_M_SATURN, t, 0);
  static const uint8_t BODY[PLANETS] = {E_VENUS, E_JUPITER, E_MARS, E_SATURN, E_MERCURY};
  static const uint8_t MEAN[PLANETS] = {A_M_VENUS, A_M_JUPITER, A_M_MARS, A_M_SATURN, A_M_MERCURY};
  for (int k = 0; k < PLANETS; k++) {
    float x, y, z;
    orbit(BODY[k], d, deg(angle(MEAN[k], t, 0)), &x, &y, &z);
    float lo = f_atan2d(y, x), la = f_atan2d(z, f_sqrt(x * x + y * y)), r = f_sqrt(x * x + y * y + z * z);
    if (BODY[k] == E_JUPITER)
      lo += -0.332f * great(Mj, Ms, 2, -5, -67.6f, 0) - 0.056f * great(Mj, Ms, 2, -2, 21, 0) +
            0.042f * great(Mj, Ms, 3, -5, 21, 0) - 0.036f * great(Mj, Ms, 1, -2, 0, 0) +
            0.022f * great(Mj, Ms, 1, -1, 0, 1) + 0.023f * great(Mj, Ms, 2, -3, 52, 0) - 0.016f * great(Mj, Ms, 1, -5, -69, 0);
    if (BODY[k] == E_SATURN) {
      lo += 0.812f * great(Mj, Ms, 2, -5, -67.6f, 0) - 0.229f * great(Mj, Ms, 2, -4, -2, 1) +
            0.119f * great(Mj, Ms, 1, -2, -3, 0) + 0.046f * great(Mj, Ms, 2, -6, -69, 0) + 0.014f * great(Mj, Ms, 1, -3, 32, 0);
      la += -0.020f * great(Mj, Ms, 2, -4, -2, 1) + 0.018f * great(Mj, Ms, 2, -6, -49, 0);
    }
    x = r * f_cosd(lo) * f_cosd(la), y = r * f_sind(lo) * f_cosd(la), z = r * f_sind(la);
    float xg = x + xs, yg = y + ys, zg = z;
    plan_ecl_to_eq(rev(f_atan2d(yg, xg)), f_atan2d(zg, f_sqrt(xg * xg + yg * yg)), eps, &s->pl_ra[k], &s->pl_dec[k]);
  }
}

/* the Sun's altitude plus the refraction and its radius (0.833 degrees): zero as it rises or sets */
static float sun_height(int32_t t, float lat, float lon) {
  int32_t tt = tt_of(t);
  float dpsi, eps, ra, dec;
  nutation(tt, &dpsi, &eps);
  plan_ecl_to_eq(deg(sun(tt, NULL) + bam(dpsi)), 0.0f, eps, &ra, &dec);
  return plan_altitude(ra, dec, sidereal(t, lon), lat) + 0.833f;
}

int plan_sun_event(int64_t utc, float lat, float lon, int64_t *at) {
  int32_t t0 = (int32_t)(utc - J2000);
  float prev = 0;
  for (int k = 0; k < 27 * 60; k += 3) {
    int32_t t = t0 + k * 60;
    float alt = sun_height(t, lat, lon);
    if (k > 0 && (prev < 0) != (alt < 0)) {
      float back = 180.0f * (1 - prev / (prev - alt));   /* seconds before t; whole seconds before, rounded up, */
      int whole = (int)back;                             /* fall in the same minute as the exact moment */
      *at = (int64_t)t + J2000 - whole - ((float)whole < back);
      return alt > 0 ? 1 : 2;
    }
    prev = alt;
  }
  return 0;
}

void plan_civil(int64_t local, Civil *c) {
  int32_t s = (int32_t)(local - 946684800);              /* seconds from 2000-01-01 00:00 (to 2068) */
  int32_t days = s / 86400, secs = s % 86400;
  if (secs < 0) secs += 86400, days--;
  days += 10957;                                         /* from 1970-01-01 */
  c->hour = secs / 3600, c->minute = secs / 60 % 60, c->second = secs % 60;
  c->wday = (int)(((days % 7) + 7 + 3) % 7);             /* 1970-01-01 was a Thursday: 3 from Monday */
  /* Howard Hinnant's civil_from_days */
  int32_t z = days + 719468, era = (z >= 0 ? z : z - 146096) / 146097;
  int32_t doe = z - era * 146097, yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  int32_t y = yoe + era * 400, doy = doe - (365 * yoe + yoe / 4 - yoe / 100), mp = (5 * doy + 2) / 153;
  int32_t d = doy - (153 * mp + 2) / 5 + 1, m = mp < 10 ? mp + 3 : mp - 9;
  c->year = (int)(y + (m <= 2)), c->month = (int)m, c->day = (int)d;
  c->ordinal = days + 719163;                            /* date(1970, 1, 1).toordinal() */
}

/* ---- the sky's events (proto/events.py) ------------------------------------------------------------------------ */
#define SUN_RADIUS 0.2666f                     /* degrees at 1 AU */

/* the angle between two places, by the haversine (exact for the small ones eclipses turn on) */
float plan_separation(float ra1, float dec1, float ra2, float dec2) {
  float a = f_sind((dec2 - dec1) / 2), b = f_sind((ra2 - ra1) / 2);
  float h = a * a + f_cosd(dec1) * f_cosd(dec2) * b * b;
  return 2 * f_asind(f_sqrt(h < 1 ? h : 1));
}

/* the Moon as seen from the ground rather than from the Earth's centre (its parallax is up to a degree) */
static void topocentric_moon(const Sky *s, float lat, float *ra, float *dec) {
  float mpar = f_asind(1 / s->moon_dist), gclat = lat - 0.1924f * f_sind(2 * lat);
  float rho = 0.99833f + 0.00167f * f_cosd(2 * lat), ha = s->lst - s->moon_ra, ch = f_cosd(ha);
  float g = f_abs(ch) > 1e-9f ? f_atan2d(f_sind(gclat) / f_cosd(gclat), ch) : 90.0f;
  *ra = s->moon_ra - mpar * rho * f_cosd(gclat) * f_sind(ha) / f_cosd(s->moon_dec);
  *dec = f_abs(f_sind(g)) > 1e-9f ? s->moon_dec - mpar * rho * f_sind(gclat) * f_sind(g - s->moon_dec) / f_sind(g) : s->moon_dec;
}

static float lens_cover(float d, float r1, float r2) {
  float a1 = r1 * r1 * f_acosd(f_clamp((d * d + r1 * r1 - r2 * r2) / (2 * d * r1), -1, 1)) * 0.0174532925f;
  float a2 = r2 * r2 * f_acosd(f_clamp((d * d + r2 * r2 - r1 * r1) / (2 * d * r2), -1, 1)) * 0.0174532925f;
  float q = (-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2);
  return (a1 + a2 - 0.5f * f_sqrt(q > 0 ? q : 0)) / (3.14159265f * r1 * r1);
}

bool plan_solar(const Sky *s, float lat, Eclipse *e) {
  if (plan_altitude(s->sun_ra, s->sun_dec, s->lst, lat) < -0.8f) return false;
  float tra, tdec;
  topocentric_moon(s, lat, &tra, &tdec);
  float h = plan_altitude(tra, tdec, s->lst, lat);
  float near = s->moon_dist - f_sind(h > 0 ? h : 0);         /* nearer by about an Earth radius times its height's sine */
  float rm = f_asind(0.2725076f / near), rs = SUN_RADIUS / s->sun_dist;
  float sep = plan_separation(tra, tdec, s->sun_ra, s->sun_dec);
  if (sep >= rs + rm) return false;
  if (sep <= rm - rs) e->kind = ECLIPSE_TOTAL, e->cover = 1;
  else if (sep <= rs - rm) e->kind = ECLIPSE_ANNULAR, e->cover = (rm / rs) * (rm / rs);
  else e->kind = ECLIPSE_PARTIAL, e->cover = lens_cover(sep, rs, rm);
  e->cover = e->cover < 1 ? e->cover : 1;
  e->magnitude = (rs + rm - sep) / (2 * rs);
  e->east = (pyf_mod(tra - s->sun_ra + 180, 360) - 180) * f_cosd(s->sun_dec) / rs, e->north = (tdec - s->sun_dec) / rs;
  e->ratio = rm / rs;
  return true;
}

bool plan_lunar(const Sky *s, float lat, Eclipse *e) {
  if (plan_altitude(s->moon_ra, s->moon_dec, s->lst, lat) < 0) return false;
  float rm = f_asind(0.2725076f / s->moon_dist), ara = rev(s->sun_ra + 180), adec = -s->sun_dec;
  float sep = plan_separation(s->moon_ra, s->moon_dec, ara, adec);
  float umbra = 1.02f * (0.998340f * f_asind(1 / s->moon_dist) + 0.00244f - SUN_RADIUS / s->sun_dist);
  if (sep >= umbra + rm) return false;
  e->kind = sep <= umbra - rm ? ECLIPSE_TOTAL : ECLIPSE_PARTIAL;
  e->magnitude = (umbra + rm - sep) / (2 * rm);
  e->east = (pyf_mod(ara - s->moon_ra + 180, 360) - 180) * f_cosd(s->moon_dec), e->north = adec - s->moon_dec;
  e->cover = 0, e->ratio = 0;
  return true;
}

/* Jupiter's four great moons: Meeus ch. 44, the lower-accuracy theory; X (west) and Y (north) in Jupiter's radii */
static const struct { uint32_t a0; int64_t rate; } JOVIAN[11] = {
  {0x7ad65b7au, 661791177LL},        /* V: 172.74 + 0.00111588 d */
  {0xfe3e2b0eu, 584526636223LL},     /* M: 357.529 + 0.9856003 d */
  {0x0e3c87a0u, 49275117843LL},      /* N: 20.020 + 0.0830853 d */
  {0x2f03de52u, 535253238273LL},     /* J: 66.115 + 0.9025179 d */
  {0x186d3a07u, 49278498323LL},      /* lambda: 34.35 + 0.083091 d */
  {0x747c22d8u, 120633228117535LL},  /* u1: 163.8069 + 203.4058646 d */
  {0xfedf470bu, 60072686470630LL},   /* u2: 358.4140 + 101.2916335 d */
  {0x0410db79u, 29792415676831LL},   /* u3: 5.7176 + 50.2345180 d */
  {0x9fdd4413u, 12743803617573LL},   /* u4: 224.8092 + 21.4879800 d */
  {0xeb817aa7u, 29837467389370LL},   /* G: 331.18 + 50.310482 d */
  {0x3e2fc963u, 12791990873319LL},   /* H: 87.45 + 21.569231 d */
};
static float jovian(int i, int32_t t) {
  uint64_t q = (uint64_t)JOVIAN[i].rate * (uint64_t)(int64_t)t;
  return deg(JOVIAN[i].a0 + (uint32_t)(q >> 32));
}
void plan_galilean(int64_t utc, float X[4], float Y[4], bool behind[4]) {
  int32_t t = (int32_t)(utc - J2000);
  float V = jovian(0, t), M = jovian(1, t), N = jovian(2, t) + 0.329f * f_sind(V), J = jovian(3, t) - 0.329f * f_sind(V);
  float A = 1.915f * f_sind(M) + 0.020f * f_sind(2 * M), B = 5.555f * f_sind(N) + 0.168f * f_sind(2 * N);
  float K = J + A - B;
  float R = 1.00014f - 0.01671f * f_cosd(M) - 0.00014f * f_cosd(2 * M);
  float r = 5.20872f - 0.25208f * f_cosd(N) - 0.00611f * f_cosd(2 * N);
  float delta = f_sqrt(r * r + R * R - 2 * r * R * f_cosd(K)), psi = f_asind(R / delta * f_sind(K));
  float lam = jovian(4, t) + 0.329f * f_sind(V) + B, Ds = 3.12f * f_sind(lam + 42.8f);
  float De = Ds - 2.22f * f_sind(psi) * f_cosd(lam + 22) - 1.30f * (r - delta) / delta * f_sind(lam - 100.5f);
  int32_t tl = t - (int32_t)(delta / 173 * 86400);       /* the light's time from Jupiter */
  float u[4], G = jovian(9, tl), H = jovian(10, tl);
  for (int i = 0; i < 4; i++) u[i] = jovian(5 + i, tl) + psi - B;
  float u1 = u[0], u2 = u[1], u3 = u[2];
  u[0] += 0.473f * f_sind(2 * (u1 - u2)), u[1] += 1.065f * f_sind(2 * (u2 - u3));
  u[2] += 0.165f * f_sind(G), u[3] += 0.843f * f_sind(H);
  float rr[4] = {5.9057f - 0.0244f * f_cosd(2 * (u1 - u2)), 9.3966f - 0.0882f * f_cosd(2 * (u2 - u3)),
                 14.9883f - 0.0216f * f_cosd(G), 26.3627f - 0.1939f * f_cosd(H)};
  for (int i = 0; i < 4; i++) {
    X[i] = rr[i] * f_sind(u[i]), Y[i] = -rr[i] * f_cosd(u[i]) * f_sind(De);
    behind[i] = f_cosd(u[i]) > 0 && f_abs(X[i]) < 1.0f;  /* beyond Jupiter and within its disc */
  }
}

/* the meteor showers: their peaks by the Sun's ecliptic longitude, and their radiants (the IMO's working list) */
const Shower SHOWERS[SHOWER_COUNT] = {
  {"Quadrantids", 283.15f, 230.0f, 49.0f}, {"Lyrids", 32.32f, 271.0f, 34.0f}, {"Eta Aquariids", 45.5f, 338.0f, -1.0f},
  {"Delta Aquariids", 127.0f, 340.0f, -16.0f}, {"Perseids", 140.0f, 48.0f, 58.0f}, {"Draconids", 195.4f, 262.0f, 54.0f},
  {"Orionids", 208.0f, 95.0f, 16.0f}, {"Leonids", 235.27f, 152.0f, 22.0f}, {"Geminids", 262.2f, 112.0f, 33.0f},
  {"Ursids", 270.7f, 217.0f, 76.0f}};
/* the shower at or near its peak (the Sun within a degree, about a day, of its peak): its number, or -1 */
int plan_shower(float sun_lon) {
  for (int i = 0; i < SHOWER_COUNT; i++)
    if (f_abs(pyf_mod(sun_lon - SHOWERS[i].peak + 180, 360) - 180) <= 1.0f) return i;
  return -1;
}
