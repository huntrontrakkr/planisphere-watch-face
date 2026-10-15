/* The calendars' days (proto/feasts.py, line for line): which of the kept calendars' feasts a day is, by the rule
 * each calendar keeps. Gregorian ordinals throughout (1 January of year 1 is 1, as Python's date.toordinal());
 * moments are seconds since 1970. The Hebrew and Islamic calendars by their arithmetic; the Chinese by its new moons
 * and solar terms on Beijing's clock (after Reingold and Dershowitz); Diwali by the Sun's entry into sidereal Libra
 * and the new moon's lunar day at Delhi's dusk. Looked up once a day (plan_feast), from feasts.bin. */
#include "plan.h"
#include "plan_data.h"
#include "plan_math.h"

#define SYNODIC_MS 2551442877LL            /* the mean lunation, milliseconds */
#define NEW_MOON_2000 947182440LL          /* 2000-01-06 18:14 UTC (Meeus 49) */
#define EPOCH_ORDINAL 719163               /* 1 January 1970 */

/* ---- the Gregorian calendar ---------------------------------------------------------------------------------- */

static int32_t floor_div(int64_t a, int64_t b) { return (int32_t)(a >= 0 ? a / b : -((-a + b - 1) / b)); }

/* days since 1970 from a civil date, and back (Howard Hinnant's days_from_civil and civil_from_days) */
static int32_t ordinal_of(int y, int m, int d) {
  y -= m <= 2;
  int era = (y >= 0 ? y : y - 399) / 400, yoe = y - era * 400;
  int doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1, doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  return era * 146097 + doe - 719468 + EPOCH_ORDINAL;
}
static void civil_of(int32_t o, int *y, int *m, int *d) {
  int32_t z = o - EPOCH_ORDINAL + 719468, era = (z >= 0 ? z : z - 146096) / 146097;
  int32_t doe = z - era * 146097, yoe = (doe - doe / 1460 + doe / 36524 - doe / 146096) / 365;
  int32_t doy = doe - (365 * yoe + yoe / 4 - yoe / 100), mp = (5 * doy + 2) / 153;
  *d = doy - (153 * mp + 2) / 5 + 1, *m = mp < 10 ? mp + 3 : mp - 9, *y = yoe + era * 400 + (*m <= 2);
}
static int weekday(int32_t o) { return (int)((o - 1) % 7); }   /* 0 Monday */

/* Easter, by the anonymous Gregorian computus (Meeus) */
static int32_t easter(int y) {
  int a = y % 19, b = y / 100, c = y % 100, d = b / 4, e = b % 4, f = (b + 8) / 25, g = (b - f + 1) / 3;
  int h = (19 * a + b - d - g + 15) % 30, i = c / 4, k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7;
  int m = (a + 11 * h + 22 * l) / 451, n = h + l - 7 * m + 114;
  return ordinal_of(y, n / 31, n % 31 + 1);
}
/* the Orthodox churches' Easter: the Julian computus, its date moved to the Gregorian calendar */
static int32_t julian_easter(int y) {
  int a = y % 4, b = y % 7, c = y % 19, d = (19 * c + 15) % 30, e = (2 * a + 4 * b - d + 34) % 7, n = d + e + 114;
  return ordinal_of(y, n / 31, n % 31 + 1) + (y / 100 - y / 400 - 2);
}
static int32_t nth_weekday(int y, int m, int wd, int n) {
  if (n > 0) {
    int32_t first = ordinal_of(y, m, 1);
    return first + ((wd - weekday(first)) % 7 + 7) % 7 + 7 * (n - 1);
  }
  int32_t last = (m == 12 ? ordinal_of(y + 1, 1, 1) : ordinal_of(y, m + 1, 1)) - 1;
  return last - ((weekday(last) - wd) % 7 + 7) % 7;
}
static int32_t weekday_after(int32_t o, int wd) { return o + 1 + ((wd - weekday(o + 1)) % 7 + 7) % 7; }
static int32_t advent_sunday(int y) {
  int32_t christmas = ordinal_of(y, 12, 25);
  int back = (weekday(christmas) + 1) % 7;
  return christmas - (back ? back : 7) - 21;
}

/* ---- the Hebrew calendar ------------------------------------------------------------------------------------- */
#define HEBREW_EPOCH (-1373427)

static int32_t hebrew_elapsed(int32_t y) {
  int32_t months = (235 * y - 234) / 19, parts = 12084 + 13753 * months, day = 29 * months + parts / 25920;
  return (3 * (day + 1)) % 7 < 3 ? day + 1 : day;
}
static int32_t hebrew_new_year(int32_t y) {
  int32_t ny0 = hebrew_elapsed(y - 1), ny1 = hebrew_elapsed(y), ny2 = hebrew_elapsed(y + 1);
  return HEBREW_EPOCH + ny1 + (ny2 - ny1 == 356 ? 2 : ny1 - ny0 == 382 ? 1 : 0);
}
static bool hebrew_leap(int32_t y) { return (7 * y + 1) % 19 < 7; }
/* the first day of a month (from Nisan as 1; Tishri 7; Adar II 13), the year running from Tishri */
static int32_t hebrew_date(int32_t y, int month, int day) {
  int32_t length = hebrew_new_year(y + 1) - hebrew_new_year(y);
  bool long_heshvan = length % 10 == 5, short_kislev = length % 10 == 3;
  int last = hebrew_leap(y) ? 13 : 12;
  int32_t at = hebrew_new_year(y);
  for (int i = 0; i < last; i++) {
    int m = i <= last - 7 ? 7 + i : i - last + 7;
    if (m == month) return at + day - 1;
    int days = 30;
    if (m == 2 || m == 4 || m == 6 || m == 10 || m == 13 || (m == 12 && !hebrew_leap(y)) || (m == 8 && !long_heshvan) ||
        (m == 9 && short_kislev))
      days = 29;
    at += days;
  }
  return at;
}
static int32_t hebrew_year_of(int32_t o) {
  int32_t y = (int32_t)(((int64_t)(o - HEBREW_EPOCH) * 98496) / 35975351) + 1;
  while (hebrew_new_year(y + 1) <= o) y++;
  while (hebrew_new_year(y) > o) y--;
  return y;
}

/* ---- the Islamic calendar, by its arithmetic --------------------------------------------------------------- */
#define ISLAMIC_EPOCH 227015

static int32_t islamic_ordinal(int32_t y, int m, int d) {
  return d + 29 * (m - 1) + (6 * m - 1) / 11 + (y - 1) * 354 + (3 + 11 * y) / 30 + ISLAMIC_EPOCH - 1;
}
static void islamic_of(int32_t o, int *m, int *d) {
  int32_t y = (30 * (o - ISLAMIC_EPOCH) + 10646) / 10631;
  int mm = (11 * (o - islamic_ordinal(y, 1, 1)) + 330) / 325;
  if (mm > 12) mm = 12;
  *m = mm, *d = o - islamic_ordinal(y, mm, 1) + 1;
}

/* ---- the Sun and the Moon ------------------------------------------------------------------------------------ */

static float wrap180(float a) { return pyf_mod(a + 180, 360) - 180; }

static int64_t new_moon_near(int64_t utc) {
  int64_t ms = (utc - NEW_MOON_2000) * 1000, k = (ms + (ms >= 0 ? SYNODIC_MS / 2 : -SYNODIC_MS / 2)) / SYNODIC_MS;
  int64_t t = NEW_MOON_2000 + k * SYNODIC_MS / 1000;
  for (int i = 0; i < 4; i++) {
    float sl, ml;
    plan_lons(t, &sl, &ml);
    t -= (int64_t)(wrap180(ml - sl) / 12.190749f * 86400.0f);
  }
  return t;
}
static int64_t elongation_moment(int64_t t, float target) {
  for (int i = 0; i < 5; i++) {
    float sl, ml;
    plan_lons(t, &sl, &ml);
    t -= (int64_t)(wrap180(ml - sl - target) / 12.190749f * 86400.0f);
  }
  return t;
}
static int64_t sun_moment(int64_t t, float target) {
  for (int i = 0; i < 5; i++) {
    float sl, ml;
    plan_lons(t, &sl, &ml);
    t -= (int64_t)(wrap180(sl - target) / 0.98564736f * 86400.0f);
  }
  return t;
}
/* dates on a zone's clock (minutes ahead of UTC) */
static int32_t zone_date(int64_t utc, int minutes) { return floor_div(utc + minutes * 60, 86400) + EPOCH_ORDINAL; }
static int64_t zone_midnight(int32_t o, int minutes) { return (int64_t)(o - EPOCH_ORDINAL) * 86400 - minutes * 60; }

static float ayanamsa(int year) { return 23.857f + 50.29f / 3600 * (float)(year - 2000); }

/* the date (on a zone's clock) the Sun reaches a longitude in a year, tropical or sidereal (Lahiri) */
static int32_t sun_day(int year, float lon, int minutes, bool sidereal) {
  float target = pyf_mod(lon + (sidereal ? ayanamsa(year) : 0), 360);
  int64_t t = zone_midnight(ordinal_of(year, 1, 1), 0) + (int64_t)(pyf_mod(target - 280, 360) / 0.98564736f * 86400.0f);
  return zone_date(sun_moment(t, target), minutes);
}

/* ---- the Chinese calendar, on Beijing's clock (Calendrical Calculations, ch. 19) ---------------------------- */
#define BJ (8 * 60)

static int32_t cn_new_moon_on_or_after(int32_t o) {
  int64_t t = new_moon_near(zone_midnight(o, BJ));
  if (zone_date(t, BJ) < o) t = new_moon_near(t + SYNODIC_MS / 1000);
  return zone_date(t, BJ);
}
static int32_t cn_new_moon_before(int32_t o) {
  int64_t t = new_moon_near(zone_midnight(o, BJ));
  if (zone_date(t, BJ) >= o) t = new_moon_near(t - SYNODIC_MS / 1000);
  return zone_date(t, BJ);
}
static int cn_major_term(int32_t o) {
  float sl, ml;
  plan_lons(zone_midnight(o, BJ), &sl, &ml);
  return (2 + (int)(sl / 30) - 1) % 12 + 1;
}
static bool cn_no_major_term(int32_t o) { return cn_major_term(o) == cn_major_term(cn_new_moon_on_or_after(o + 1)); }
static bool cn_prior_leap(int32_t first, int32_t m) {
  for (int i = 0; i < 14 && m >= first; i++) {
    if (cn_no_major_term(m)) return true;
    m = cn_new_moon_before(m);
  }
  return false;
}
static int32_t cn_solstice_on_or_before(int32_t o) {
  int64_t t = sun_moment(zone_midnight(o, BJ), 270);
  if (zone_date(t, BJ) > o) t = sun_moment(t - 31556926LL, 270);
  else if (zone_date(t, BJ) + 366 <= o) t = sun_moment(t + 31556926LL, 270);
  return zone_date(t, BJ);
}
/* the month (leap months marked) and day of a Beijing date */
static void chinese_of(int32_t o, int *month, bool *leap, int *day) {
  int32_t s1 = cn_solstice_on_or_before(o), s2 = cn_solstice_on_or_before(s1 + 370);
  int32_t m12 = cn_new_moon_on_or_after(s1 + 1), next_m11 = cn_new_moon_before(s2 + 1), m = cn_new_moon_before(o + 1);
  bool leap_year = pyf_round((float)(next_m11 - m12) / 29.530588853f) == 12;
  int k = pyf_round((float)(m - m12) / 29.530588853f) - (leap_year && cn_prior_leap(m12, m) ? 1 : 0);
  *month = ((k - 1) % 12 + 12) % 12 + 1;
  *leap = leap_year && cn_no_major_term(m) && !cn_prior_leap(m12, cn_new_moon_before(m));
  *day = o - m + 1;
}

/* ---- Diwali: the new moon ending the amanta month that holds the Sun's entry into sidereal Libra; the IST evening
 * whose pradosh (Delhi's sunset and 144 minutes after) its lunar day (elongation 348 to 360) overlaps ---------- */
#define IST 330

/* a place's sunset on a local date: the Sun's hour angle at the horizon (refracted), from its place at noon */
static int64_t sunset(int32_t o, float lat, float lon, int minutes) {
  int64_t noon = zone_midnight(o, minutes) + (int64_t)((12 - lon / 15) * 3600 + minutes * 60);
  Sky s;
  for (int i = 0; i < 2; i++) {                  /* (the declination the last noon's, as the prototype has it) */
    plan_sun_moon(&s, noon, lon);
    noon -= (int64_t)(wrap180(s.lst - s.sun_ra) / 15.04107f * 3600);
  }
  float c = (f_sind(-0.833f) - f_sind(lat) * f_sind(s.sun_dec)) / (f_cosd(lat) * f_cosd(s.sun_dec));
  return noon + (int64_t)(f_acosd(f_clamp(c, -1, 1)) / 15.04107f * 3600);
}
static int32_t diwali(int year) {
  int64_t ingress = sun_moment(zone_midnight(ordinal_of(year, 10, 17), 0), 180 + ayanamsa(year));
  int64_t end = new_moon_near(ingress);
  if (end < ingress) end = new_moon_near(end + SYNODIC_MS / 1000);
  int64_t start = elongation_moment(end - 84672, 348);
  int32_t days[2], n = 0;
  int64_t overlaps[2];
  for (int32_t d = zone_date(end, IST) - 1; d <= zone_date(end, IST); d++) {
    int64_t a = sunset(d, 28.6139f, 77.2090f, IST), b = a + 144 * 60;
    int64_t overlap = (b < end ? b : end) - (a > start ? a : start);
    if (overlap > 0) days[n] = d, overlaps[n++] = overlap;
  }
  if (n == 2) return overlaps[1] >= 24 * 60 ? days[1] : days[0];
  return n ? days[0] : zone_date(end, IST);
}

/* ---- the feasts ---------------------------------------------------------------------------------------------- */

static const FeastRecord *record(const uint8_t *table, int i) {
  return (const FeastRecord *)(const void *)(table + 4) + i;
}
static int count_of(const uint8_t *table) { return table[0] | table[1] << 8; }
static const char *words_of(const uint8_t *table, uint16_t at) {
  return at == 0xFFFF ? NULL : (const char *)table + (table[2] | table[3] << 8) + at;
}

/* the converters' answers for a day, worked out only when a feast asks */
typedef struct { int32_t o; int y, m, d; bool heb, cn, isl; int32_t hy; int cm, cd; bool cleap; int im, id; } Day;

static bool matches(const FeastRecord *f, Day *day, float hours) {
  int32_t o = day->o;
  switch (f->kind) {
  case FK_FIXED: {
    int32_t start = ordinal_of(day->y, f->a, f->b);
    return o >= start && o - start < f->span;
  }
  case FK_EASTER: return o == easter(day->y) + f->a;
  case FK_ORTHODOX: return o == julian_easter(day->y) + f->a;
  case FK_NTH: return o == nth_weekday(day->y, f->a, f->b, f->c);
  case FK_AFTER: return o == weekday_after(ordinal_of(day->y, f->a, f->b), f->c);
  case FK_WINDOW: {
    int32_t start = ordinal_of(day->y, f->a, f->b);
    return o == start + ((f->c - weekday(start)) % 7 + 7) % 7;
  }
  case FK_ADVENT: return o == advent_sunday(day->y) + f->a;
  case FK_SUN:
  case FK_SIDEREAL: {
    int minutes = f->zone == FZ_BJ ? BJ : f->zone == FZ_IST ? IST : pyf_round(hours * 60);
    return o == sun_day(day->y, (float)f->a, minutes, f->kind == FK_SIDEREAL);
  }
  case FK_HEBREW: {
    if (!day->heb) day->hy = hebrew_year_of(o), day->heb = true;
    int month = f->a ? f->a : hebrew_leap(day->hy) ? 13 : 12;     /* 0: Adar, the second in a leap year */
    int32_t start = hebrew_date(day->hy, month, f->b);
    return o >= start && o - start < f->span;
  }
  case FK_CHINESE:
    if (!day->cn) chinese_of(o, &day->cm, &day->cleap, &day->cd), day->cn = true;
    return !day->cleap && day->cm == f->a && day->cd == f->b;
  case FK_ISLAMIC:
    if (!day->isl) islamic_of(o, &day->im, &day->id), day->isl = true;
    return day->im == f->a && day->id == f->b;
  case FK_DIWALI: return o == diwali(day->y);
  }
  return false;
}

int plan_feast_on(const uint8_t *table, int32_t ordinal, uint32_t cal, float hours) {
  Day day = {ordinal, 0, 0, 0, false, false, false, 0, 0, 0, false, 0, 0};
  civil_of(ordinal, &day.y, &day.m, &day.d);
  int best = -1, n = count_of(table);
  for (int i = 0; i < n; i++) {
    const FeastRecord *f = record(table, i);
    if (!(cal >> f->cal & 1) || (best >= 0 && f->rank >= record(table, best)->rank)) continue;
    if (matches(f, &day, hours)) best = i;
  }
  return best;
}

static void copy_words(char *out, const char *w) {
  int i = 0;
  if (w)
    for (; w[i] && i < 19; i++) out[i] = w[i];
  out[i] = 0;
}

bool plan_feast(Plan *p, const Face *f, int64_t utc, int32_t offset, const uint8_t *table) {
  int32_t day = floor_div(utc + offset, 86400) + EPOCH_ORDINAL;
  bool south = f->lat < 0;
  if (p->feast_day == day && p->feast_cal == f->calendars && p->feast_south == south) return true;
  if (!f->calendars) {
    p->feast_day = day, p->feast_cal = 0, p->feast_south = south, p->feast = false;
    return true;
  }
  if (!table) return false;
  p->feast_day = day, p->feast_cal = f->calendars, p->feast_south = south, p->feast = false;
  int i = plan_feast_on(table, day, f->calendars, (float)offset / 3600);
  if (i < 0) return true;
  const FeastRecord *r = record(table, i);
  bool alt = south && r->words[2] != 0xFFFF;
  copy_words(p->feast_words[0], words_of(table, r->words[alt ? 2 : 0]));
  copy_words(p->feast_words[1], words_of(table, r->words[alt ? 3 : 1]));
  p->feast_emblem = r->emblem, p->feast_flags = r->flags, p->feast = true;
  return true;
}
