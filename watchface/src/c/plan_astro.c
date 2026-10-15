/* Where things are in the sky, as the prototype finds them (proto/astro.py, proto/lunar.py): the Sun and the Moon
 * from Meeus (Astronomical Algorithms, ch. 47 and 25, nutation from ch. 22) in dynamical time, the planets from
 * Paul Schlyter's elements with Jupiter's and Saturn's great inequality. Degrees throughout. */
#include "plan.h"
#include "plan_math.h"

#if defined(__arm__)
#pragma GCC optimize("Os")
#endif

static double rev(double a) { return py_mod(a, 360.0); }

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

static double delta_t(double year) { return 69.2 + 0.25 * (year - 2025); }

/* The Moon's geocentric ecliptic longitude and latitude of date (without nutation) and distance (km). */
static void moon(double jde, double *lam, double *beta, double *dist) {
  double T = (jde - 2451545.0) / 36525, T2 = T * T, T3 = T2 * T, T4 = T3 * T;
  double Lp = 218.3164477 + 481267.88123421 * T - 0.0015786 * T2 + T3 / 538841 - T4 / 65194000;
  double D = 297.8501921 + 445267.1114034 * T - 0.0018819 * T2 + T3 / 545868 - T4 / 113065000;
  double M = 357.5291092 + 35999.0502909 * T - 0.0001536 * T2 + T3 / 24490000;
  double Mp = 134.9633964 + 477198.8675055 * T + 0.0087414 * T2 + T3 / 69699 - T4 / 14712000;
  double F = 93.2720950 + 483202.0175233 * T - 0.0036539 * T2 - T3 / 3526000 + T4 / 863310000;
  double A1 = 119.75 + 131.849 * T, A2 = 53.09 + 479264.290 * T, A3 = 313.45 + 481266.484 * T;
  double E = 1 - 0.002516 * T - 0.0000074 * T2;
  double sl = 0, sr = 0, sb = 0;
  for (int i = 0; i < 60; i++) {
    double e = LR_ARG[i][1] ? (LR_ARG[i][1] == 1 || LR_ARG[i][1] == -1 ? E : E * E) : 1.0;
    double arg = LR_ARG[i][0] * D + LR_ARG[i][1] * M + LR_ARG[i][2] * Mp + LR_ARG[i][3] * F;
    if (LR_L[i]) sl += LR_L[i] * e * m_sind(arg);
    if (LR_R[i]) sr += LR_R[i] * e * m_cosd(arg);
  }
  for (int i = 0; i < 60; i++) {
    double e = B_ARG[i][1] ? (B_ARG[i][1] == 1 || B_ARG[i][1] == -1 ? E : E * E) : 1.0;
    sb += B_B[i] * e * m_sind(B_ARG[i][0] * D + B_ARG[i][1] * M + B_ARG[i][2] * Mp + B_ARG[i][3] * F);
  }
  sl += 3958 * m_sind(A1) + 1962 * m_sind(Lp - F) + 318 * m_sind(A2);
  sb += -2235 * m_sind(Lp) + 382 * m_sind(A3) + 175 * m_sind(A1 - F) + 175 * m_sind(A1 + F) + 127 * m_sind(Lp - Mp)
        - 115 * m_sind(Lp + Mp);
  *lam = rev(Lp + sl / 1e6);
  *beta = sb / 1e6;
  *dist = 385000.56 + sr / 1000;
}

/* The Sun's apparent ecliptic longitude of date (with the aberration, without nutation). */
static double sun(double jde) {
  double T = (jde - 2451545.0) / 36525;
  double L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  double M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  double C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * m_sind(M) + (0.019993 - 0.000101 * T) * m_sind(2 * M)
             + 0.000289 * m_sind(3 * M);
  return rev(L0 + C - 0.00569);
}

static void nutation(double jde, double *dpsi, double *eps) {
  double T = (jde - 2451545.0) / 36525;
  double om = 125.04452 - 1934.136261 * T;
  double L = 280.4665 + 36000.7698 * T, Lp = 218.3165 + 481267.8813 * T;
  *dpsi = (-17.20 * m_sind(om) - 1.32 * m_sind(2 * L) - 0.23 * m_sind(2 * Lp) + 0.21 * m_sind(2 * om)) / 3600;
  double deps = (9.20 * m_cosd(om) + 0.57 * m_cosd(2 * L) + 0.10 * m_cosd(2 * Lp) - 0.09 * m_cosd(2 * om)) / 3600;
  *eps = 23.4392911 - 0.0130042 * T - 1.64e-7 * T * T + 5.04e-7 * T * T * T + deps;
}

double plan_moon_node(double jd) {
  double T = (jd - 2451545.0) / 36525;
  return rev(125.0445479 - 1934.1362891 * T + 0.0020754 * T * T + T * T * T / 467441 - T * T * T * T / 60616000);
}

void plan_ecl_to_eq(double lon, double lat, double eps, double *ra, double *dec) {
  double x = m_cosd(lon) * m_cosd(lat);
  double y = m_sind(lon) * m_cosd(lat) * m_cosd(eps) - m_sind(lat) * m_sind(eps);
  double z = m_sind(lon) * m_cosd(lat) * m_sind(eps) + m_sind(lat) * m_cosd(eps);
  *ra = rev(m_atan2d(y, x));
  *dec = m_asind(z);
}

double plan_altitude(double ra, double dec, double lst, double lat) {
  return m_asind(m_sind(lat) * m_sind(dec) + m_cosd(lat) * m_cosd(dec) * m_cosd(lst - ra));
}

static double julian(int64_t utc) { return (double)utc / 86400.0 + 2440587.5; }

static double sidereal(double jd, double lon) {
  double d = jd - 2451545.0, T = d / 36525;
  return rev(280.46061837 + 360.98564736629 * d + 0.000387933 * T * T - T * T * T / 38710000 + lon);
}

/* Schlyter's elements: N, i, w, a, e, M as (value, rate per day) from 2000 Jan 0.0 UT */
enum { E_SUN, E_MERCURY, E_VENUS, E_MARS, E_JUPITER, E_SATURN };
static const double ELEMENTS[6][6][2] = {
  {{0, 0}, {0, 0}, {282.9404, 4.70935e-5}, {1.0, 0}, {0.016709, -1.151e-9}, {356.0470, 0.9856002585}},
  {{48.3313, 3.24587e-5}, {7.0047, 5.00e-8}, {29.1241, 1.01444e-5}, {0.387098, 0}, {0.205635, 5.59e-10},
   {168.6562, 4.0923344368}},
  {{76.6799, 2.46590e-5}, {3.3946, 2.75e-8}, {54.8910, 1.38374e-5}, {0.723330, 0}, {0.006773, -1.302e-9},
   {48.0052, 1.6021302244}},
  {{49.5574, 2.11081e-5}, {1.8497, -1.78e-8}, {286.5016, 2.92961e-5}, {1.523688, 0}, {0.093405, 2.516e-9},
   {18.6021, 0.5240207766}},
  {{100.4542, 2.76854e-5}, {1.3030, -1.557e-7}, {273.8777, 1.64505e-5}, {5.20256, 0}, {0.048498, 4.469e-9},
   {19.8950, 0.0830853001}},
  {{113.6634, 2.38980e-5}, {2.4886, -1.081e-7}, {339.3939, 2.97661e-5}, {9.55475, 0}, {0.055546, -9.499e-9},
   {316.9670, 0.0334442282}},
};

static double element(int body, int k, double d) { return ELEMENTS[body][k][0] + ELEMENTS[body][k][1] * d; }

static double kepler(double M, double e) {
  double E = M + e * R2D * m_sind(M) * (1 + e * m_cosd(M));
  for (int i = 0; i < 8; i++) E = E - (E - e * R2D * m_sind(E) - M) / (1 - e * m_cosd(E));
  return E;
}

/* the body's heliocentric ecliptic position */
static void orbit(int body, double d, double *x, double *y, double *z) {
  double N = element(body, 0, d), i = element(body, 1, d), w = element(body, 2, d), a = element(body, 3, d);
  double e = element(body, 4, d), M = element(body, 5, d);
  double E = kepler(rev(M), e);
  double xv = a * (m_cosd(E) - e), yv = a * m_sqrt(1 - e * e) * m_sind(E);
  double v = m_atan2d(yv, xv), r = m_sqrt(xv * xv + yv * yv);
  *x = r * (m_cosd(N) * m_cosd(v + w) - m_sind(N) * m_sind(v + w) * m_cosd(i));
  *y = r * (m_sind(N) * m_cosd(v + w) + m_cosd(N) * m_sind(v + w) * m_cosd(i));
  *z = r * m_sind(v + w) * m_sind(i);
}

void plan_sky(Sky *s, int64_t utc, double lon) {
  double jd = julian(utc);
  s->jd = jd;
  s->lst = sidereal(jd, lon);
  double d = jd - 2451543.5;
  Civil cv;
  plan_civil(utc, &cv);
  double jde = jd + delta_t(cv.year) / 86400;
  double dpsi, eps;
  nutation(jde, &dpsi, &eps);
  s->eps = eps;
  double lam_s = rev(sun(jde) + dpsi);
  double lam_m, beta_m, dist_km;
  moon(jde, &lam_m, &beta_m, &dist_km);
  lam_m = rev(lam_m + dpsi);
  plan_ecl_to_eq(lam_s, 0.0, eps, &s->sun_ra, &s->sun_dec);
  s->sun_lon = lam_s;
  plan_ecl_to_eq(lam_m, beta_m, eps, &s->moon_ra, &s->moon_dec);
  s->moon_dist = dist_km / 6378.14;
  double ce = m_cosd(lam_m - lam_s) * m_cosd(beta_m);
  double elong = m_atan2d(m_sqrt(1 - ce * ce), ce);
  s->moon_phase = (1 - m_cosd(elong)) / 2;
  s->moon_waxing = rev(lam_m - lam_s) < 180;
  /* Schlyter's Sun, to carry the planets from the Sun's frame to ours */
  double ws = element(E_SUN, 2, d), es = element(E_SUN, 4, d), Ms = element(E_SUN, 5, d);
  double E = kepler(rev(Ms), es);
  double xv = m_cosd(E) - es, yv = m_sqrt(1 - es * es) * m_sind(E);
  double v = m_atan2d(yv, xv), rs = m_sqrt(xv * xv + yv * yv);
  double lon_sun = rev(v + ws), xs = rs * m_cosd(lon_sun), ys = rs * m_sind(lon_sun);
  double Mj = element(E_JUPITER, 5, d), Msat = element(E_SATURN, 5, d);
  static const uint8_t body[PLANETS] = {E_VENUS, E_JUPITER, E_MARS, E_SATURN, E_MERCURY};
  for (int k = 0; k < PLANETS; k++) {
    double x, y, z;
    orbit(body[k], d, &x, &y, &z);
    double lo = m_atan2d(y, x), la = m_atan2d(z, m_sqrt(x * x + y * y)), r = m_sqrt(x * x + y * y + z * z);
    if (body[k] == E_JUPITER)
      lo += -0.332 * m_sind(2 * Mj - 5 * Msat - 67.6) - 0.056 * m_sind(2 * Mj - 2 * Msat + 21)
            + 0.042 * m_sind(3 * Mj - 5 * Msat + 21) - 0.036 * m_sind(Mj - 2 * Msat) + 0.022 * m_cosd(Mj - Msat)
            + 0.023 * m_sind(2 * Mj - 3 * Msat + 52) - 0.016 * m_sind(Mj - 5 * Msat - 69);
    if (body[k] == E_SATURN) {
      lo += 0.812 * m_sind(2 * Mj - 5 * Msat - 67.6) - 0.229 * m_cosd(2 * Mj - 4 * Msat - 2)
            + 0.119 * m_sind(Mj - 2 * Msat - 3) + 0.046 * m_sind(2 * Mj - 6 * Msat - 69)
            + 0.014 * m_sind(Mj - 3 * Msat + 32);
      la += -0.020 * m_cosd(2 * Mj - 4 * Msat - 2) + 0.018 * m_sind(2 * Mj - 6 * Msat - 49);
    }
    x = r * m_cosd(lo) * m_cosd(la), y = r * m_sind(lo) * m_cosd(la), z = r * m_sind(la);
    double xg = x + xs, yg = y + ys, zg = z;
    plan_ecl_to_eq(rev(m_atan2d(yg, xg)), m_atan2d(zg, m_sqrt(xg * xg + yg * yg)), eps, &s->pl_ra[k], &s->pl_dec[k]);
  }
}

/* the Sun's altitude plus the refraction and its radius (0.833 degrees): zero as it rises or sets */
static double sun_height(int64_t utc, double lat, double lon) {
  double jd = julian(utc);
  Civil cv;
  plan_civil(utc, &cv);
  double jde = jd + delta_t(cv.year) / 86400;
  double dpsi, eps, ra, dec;
  nutation(jde, &dpsi, &eps);
  plan_ecl_to_eq(rev(sun(jde) + dpsi), 0.0, eps, &ra, &dec);
  return plan_altitude(ra, dec, sidereal(jd, lon), lat) + 0.833;
}

int plan_sun_event(int64_t utc, double lat, double lon, int64_t *at) {
  double prev = 0;
  for (int k = 0; k < 27 * 60; k += 3) {
    int64_t t = utc + (int64_t)k * 60;
    double alt = sun_height(t, lat, lon);
    if (k > 0 && (prev < 0) != (alt < 0)) {
      double f = prev / (prev - alt);
      double back = 180.0 * (1 - f), whole = m_floor(back);  /* seconds before t; whole seconds before, rounded up, */
      *at = t - (int64_t)whole - (whole < back);           /* fall in the same minute as the exact moment */
      return alt > 0 ? 1 : 2;
    }
    prev = alt;
  }
  return 0;
}

void plan_civil(int64_t local, Civil *c) {
  int32_t days = (int32_t)m_floor((double)local / 86400.0);     /* (no 64-bit division: the watch has no room for it) */
  int32_t secs = (int32_t)(local - (int64_t)days * 86400);
  c->hour = secs / 3600, c->minute = secs / 60 % 60, c->second = secs % 60;
  c->wday = (int)(((days % 7) + 7 + 3) % 7);               /* 1970-01-01 was a Thursday: 3 from Monday */
  /* Howard Hinnant's civil_from_days */
  int32_t z = days + 719468, era = (z >= 0 ? z : z - 146096) / 146097;
  int32_t doe = z - era * 146097, yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  int32_t y = yoe + era * 400, doy = doe - (365 * yoe + yoe / 4 - yoe / 100), mp = (5 * doy + 2) / 153;
  int32_t d = doy - (153 * mp + 2) / 5 + 1, m = mp < 10 ? mp + 3 : mp - 9;
  c->year = (int)(y + (m <= 2)), c->month = (int)m, c->day = (int)d;
  c->ordinal = (int32_t)(days + 719163);                   /* date(1970, 1, 1).toordinal() */
}
