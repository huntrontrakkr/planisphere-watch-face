/* The arithmetic the face needs, the same on the watch, the host and the settings page's WebAssembly: the
 * library's own functions differ from one to the next (and the watch's are large), so these are our own.
 *
 *   m_*   double precision, for the sky's positions: fdlibm's, bit for bit wherever they run (Groundtrack's)
 *   f_*   single precision approximations, for the work done for every pixel or every few
 *   py_*  Python's rounding and remainder, so the C lands on the prototype's pixels
 */
#pragma once
#include <stdint.h>

#define M_PI_ 3.14159265358979323846
#define D2R (M_PI_ / 180.0)
#define R2D (180.0 / M_PI_)

double m_sin(double x);
double m_cos(double x);
double m_asin(double x);
double m_acos(double x);
double m_atan(double x);
double m_atan2(double y, double x);
double m_sqrt(double x);
double m_floor(double x);
double m_fabs(double x);

static inline double m_sind(double a) { return m_sin(a * D2R); }
static inline double m_cosd(double a) { return m_cos(a * D2R); }
static inline double m_atan2d(double y, double x) { return m_atan2(y, x) * R2D; }
/* the arcsine as an arctangent (the watch has room for only the one) */
static inline double m_asind(double x) {
  x = x < -1.0 ? -1.0 : x > 1.0 ? 1.0 : x;
  return m_atan2(x, m_sqrt(1.0 - x * x)) * R2D;
}

/* x modulo y, from 0 up to y (Python's %, for y > 0) */
static inline double py_mod(double x, double y) { return x - y * m_floor(x / y); }
/* Python's round(): to the nearest whole number, halves to the even one */
int py_round(double x);
static inline int py_floor(double x) { return (int)m_floor(x); }

/* the same in single precision, for the screen's coordinates */
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
