/* The planisphere's core: where things are in the sky (plan_astro.c) and the face drawn from it (plan_render.c),
 * the same C on the watch (main.c), the host harness (tools/host.c) and the settings page's preview
 * (preview/preview.c, WebAssembly). The drawing is the Python prototype's (proto/plates.py), its pieces and the
 * ring's geometry generated from it (tools/gen_tables.py: the blobs in resources/data, plan_data.h).
 */
#pragma once
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include "plan_data.h"

#define MAX_W 260
#define MAX_H 260

/* The screen: a row's GColor8 pixels (index x), and the columns it has from x0 to x1 (the Round 2's rows are
 * cut to the circle). */
typedef uint8_t *(*RowFn)(void *ctx, int y, int *x0, int *x1);
typedef struct { RowFn row; void *ctx; } Target;

/* The weather, as the phone sends it (Open-Meteo's current conditions). */
typedef struct {
  int16_t temp10;              /* tenths of a degree Celsius, at two metres */
  uint8_t code;                /* the WMO weather code */
  uint8_t low, mid, high;      /* cloud cover by height, percent */
  uint8_t wind;                /* km/h at ten metres */
  uint16_t wind_from;          /* degrees east of north */
  uint16_t pressure;           /* hPa at sea level */
  uint16_t snow_mm;            /* snow lying */
  uint16_t vis_dam;            /* visibility, tens of metres */
} Weather;

/* What the face shows, settled from the owner's settings and the watch. */
typedef struct {
  uint8_t plate;               /* PLATE_* */
  bool clock24, names, labours, fahrenheit;
  double lat, lon;             /* degrees, north and east positive */
  const char *city, *country;  /* the place's names on the ring (NULL or "": none) */
  bool coords;                 /* its latitude and longitude on the ring (false while the place is not yet known) */
  const Weather *weather;      /* NULL: none */
} Face;

/* Where things are in the sky at a moment (degrees). The planets in the order they are drawn. */
enum { VENUS, JUPITER, MARS, SATURN, MERCURY, PLANETS };
typedef struct {
  double jd;                   /* Julian day (UT) */
  double lst;                  /* local sidereal time */
  double eps;                  /* the true obliquity */
  double sun_ra, sun_dec, sun_lon;
  double moon_ra, moon_dec, moon_dist, moon_phase;   /* moon_dist in Earth radii, moon_phase the lit fraction */
  bool moon_waxing;
  double pl_ra[PLANETS], pl_dec[PLANETS];
} Sky;

void plan_sky(Sky *s, int64_t utc, double lon);
double plan_altitude(double ra, double dec, double lst, double lat);
void plan_ecl_to_eq(double lon, double lat, double eps, double *ra, double *dec);
double plan_moon_node(double jd);
/* The Sun's next rising (1) or setting (2) after `utc`, within 27 hours (0: none), its moment in *at. */
int plan_sun_event(int64_t utc, double lat, double lon, int64_t *at);
/* The local calendar from seconds since 1970 (local time): year, month 1..12, day, Python's weekday (0 Monday),
 * hour, minute, second, and the proleptic Gregorian ordinal of the day (Python's date.toordinal()). */
typedef struct { int year, month, day, wday, hour, minute, second; int32_t ordinal; } Civil;
void plan_civil(int64_t local, Civil *c);

/* The face's state: its data, the screen, and the window for the latitude (kept from one drawing to the next). */
typedef struct {
  const uint8_t *data, *geom;  /* the blobs: plan.bin and this screen's geom_*.bin */
  int w, h;
  bool rect;                   /* the Time 2's cushion ring, else the Round 2's circle */
  double lat_key;              /* the latitude the window was worked out for (NaN: none yet) */
  float cx, cy, k, r_disc, R;
  int16_t wx0[MAX_H], wx1[MAX_H];      /* the window's span in each row (wx0 > wx1: none) */
  int16_t win_top, win_bottom;
  /* the ring for the latitude: the hours' rays leave the pole, which on the Time 2 moves with it */
  int16_t ticks[64][2];                /* the hour and half-hour ticks on one side (mirrored when drawn) */
  int nticks;
  int16_t studs[6][2];                 /* at 3, 6, 9, 15, 18 and 21 o'clock */
  int8_t num_style;                    /* the numerals placed for this style (-1: not yet) */
  int16_t numerals[6][2];              /* their top-left corners */
  int16_t ins_lo[4], ins_hi[4];        /* the inscriptions' room along the band (1/16 px) */
  /* the Sun's next rising or setting, kept until it passes (or the place changes) */
  int64_t ev_from, ev_at;
  int ev_kind;                         /* 1 rising, 2 setting, 0 none within a day; -1 not yet worked out */
  double ev_lat, ev_lon;
  /* while drawing */
  uint8_t *rows[MAX_H];
  int16_t rx0[MAX_H], rx1[MAX_H];
} Plan;

/* Set up for a screen of w x h (200 x 228 the Time 2, 260 x 260 the Round 2) with its blobs. */
void plan_init(Plan *p, int w, int h, const uint8_t *data, const uint8_t *geom);
/* The window for a latitude (worked out again only when it changes: about a tenth of a second on the watch). */
void plan_window(Plan *p, double lat);
/* Draw the face at `utc` (seconds since 1970), the local clock `offset` seconds ahead of UTC. The working memory
 * (a few kilobytes, freed before returning) comes from `alloc`; false if there was none. */
bool plan_render(Plan *p, const Face *f, int64_t utc, int32_t offset, const Target *t, void *(*alloc)(size_t),
                 void (*release)(void *));
