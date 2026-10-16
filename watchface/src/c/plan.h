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

/* plan.bin: its sections (SEC_*, from a table of their offsets), and a star's place at the head of a record of one
 * (the stars', their names', the constellations'), in 1/65536 of a turn and of the half turn from the south pole */
static inline const uint8_t *sec(const uint8_t *blob, int i) { return blob + ((const uint32_t *)(const void *)blob)[i]; }
static inline float star_ra(const uint8_t *s) { return (s[0] | s[1] << 8) * 360.0f / 65536; }
static inline float star_dec(const uint8_t *s) { return (s[2] | s[3] << 8) * 180.0f / 65535 - 90; }
/* a figure of the time in plan.bin (SEC_FIGURE_INDEX, its bits in SEC_FIGURE_DATA): a bit a pixel, row by row */
typedef struct { uint32_t bit; uint8_t w, h, base, pad; } FigureIndex;

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

struct DecorCtx;
/* the card's themes: none, the labours of the months, the zodiac, the astronomer, the sea and the Moon, the herbal */
enum { THEME_NONE, THEME_LABOURS, THEME_ZODIAC, THEME_ASTRONOMER, THEME_SEA, THEME_HERBAL, THEME_COUNT };
/* The tide where the phone is (watchface/src/pkjs/tides.js): its turns in order, each when (minutes since 1970, the
 * top bit set for a high water) and how high (centimetres). */
#define TIDE_TURNS 8
#define TIDE_HIGH 0x80000000u
typedef struct { uint8_t n; uint32_t at[TIDE_TURNS]; int16_t cm[TIDE_TURNS]; } Tides;

/* What the face shows, settled from the owner's settings and the watch. */
typedef struct {
  uint8_t plate;               /* PLATE_* */
  bool clock24, names, fahrenheit;
  uint8_t theme;               /* the scene in the card behind the face (THEME_*), and the Time 2's corner pieces' */
  float lat, lon;              /* degrees, north and east positive */
  const char *city, *country;  /* the place's names on the ring (NULL or "": none) */
  bool coords;                 /* its latitude and longitude on the ring (false while the place is not yet known) */
  const Weather *weather;      /* NULL: none */
  uint32_t calendars;          /* the calendars whose days the face keeps: bit n for CAL_* n (plan_data.h) */
  bool scribe;                 /* the minute's new figures kept to be written as a scribe writes (plan_scribe) */
  uint8_t events;              /* the passing events the face may bring (EV_*: Plan.event), and the village's life */
  uint8_t figs_part;           /* the figures drawn in at dusk: drawn this many EVENT_FIGS_FRAMES-ths along (0: all) */
  bool tools;                  /* the Time 2's corners: the month's tools instead of the sprigs (tools.bin) */
  const Tides *tides;          /* the tide here (NULL: none known, or inland) */
  bool tide_times;             /* the next high and low waters set low on the face (on the Round 2 for the coordinates) */
  /* the scene blob (plan_decor.c), called where the card is laid when the labours or the tools are asked for: the
   * watch loads it for the moment and lets it go; elsewhere it is plan_decor itself. NULL: neither drawn. */
  bool (*decor)(void *ctx, const struct DecorCtx *dc);
  void *decor_ctx;
} Face;
/* The Labours' tools for the Time 2's corners (an option): tools.bin (proto/labour_tools.py) holds the corner's
 * clearance (TOOLS_CLIP bytes: how far in from the side each row from the edge is clear of the ring), twelve month
 * offsets and an end (uint16), then each month's top piece and bottom piece; the scene blob reads the month's as it
 * draws. The month is the labours' own: half a year round in the south. */
#define TOOLS_CLIP 22
/* The passing events, now and then: a meteor on a clear dark night (often in a shower's peak), the figures drawn in
 * at dusk once an evening, a skein of birds at twilight in the months they migrate; and the village's windows lit and
 * dark as its people come and go. */
enum { EV_METEOR = 1, EV_FIGURES = 2, EV_BIRDS = 4, EV_VILLAGE = 8 };
#define EVENT_FIGS_FRAMES 6

/* Where things are in the sky at a moment (degrees). The planets in the order they are drawn. */
enum { VENUS, JUPITER, MARS, SATURN, MERCURY, PLANETS };
typedef struct {
  int64_t utc;                 /* the moment, seconds since 1970 */
  float lst;                   /* local sidereal time */
  float eps;                   /* the true obliquity */
  float sun_ra, sun_dec, sun_lon, sun_dist;          /* sun_dist in AU */
  float moon_ra, moon_dec, moon_dist, moon_phase;    /* moon_dist in Earth radii, moon_phase the lit fraction */
  bool moon_waxing;
  float pl_ra[PLANETS], pl_dec[PLANETS];
  float pl_far[PLANETS];       /* each its distance from the Sun times its distance from us (AU squared): its light */
} Sky;

void plan_sky(Sky *s, int64_t utc, float lon);
void plan_sun_moon(Sky *s, int64_t utc, float lon);    /* the Sun and the Moon alone */
float plan_separation(float ra1, float dec1, float ra2, float dec2);
/* An eclipse seen from here: of the Sun (cover the fraction of its disc covered, east and north the Moon's centre
 * from the Sun's in Sun radii, ratio the Moon's radius over the Sun's) or of the Moon (east and north the shadow's
 * centre from the Moon's, degrees); magnitude how deep. */
enum { ECLIPSE_PARTIAL, ECLIPSE_ANNULAR, ECLIPSE_TOTAL };
typedef struct { uint8_t kind; float magnitude, cover, east, north, ratio; } Eclipse;
bool plan_solar(const Sky *s, float lat, Eclipse *e);
bool plan_lunar(const Sky *s, float lat, Eclipse *e);
/* Jupiter's moons: X (west) and Y (north) in Jupiter's radii, and whether each is behind Jupiter */
void plan_galilean(int64_t utc, float X[4], float Y[4], bool behind[4]);
#define SHOWER_COUNT 10
typedef struct { const char *name; float peak, ra, dec; } Shower;
extern const Shower SHOWERS[SHOWER_COUNT];
int plan_shower(float sun_lon);
float plan_altitude(float ra, float dec, float lst, float lat);
void plan_ecl_to_eq(float lon, float lat, float eps, float *ra, float *dec);
float plan_moon_node(int64_t utc);
/* The Sun's next rising (1) or setting (2) after `utc`, within 27 hours (0: none), its moment in *at. */
int plan_sun_event(int64_t utc, float lat, float lon, int64_t *at);
/* The Sun's and the Moon's apparent longitudes (degrees, nutation included) at a moment. */
void plan_lons(int64_t utc, float *sun, float *moon);
/* The local calendar from seconds since 1970 (local time): year, month 1..12, day, Python's weekday (0 Monday),
 * hour, minute, second, and the proleptic Gregorian ordinal of the day (Python's date.toordinal()). */
typedef struct { int year, month, day, wday, hour, minute, second; int32_t ordinal; } Civil;
void plan_civil(int64_t local, Civil *c);

/* The feast of a local date (a Gregorian ordinal) in the calendars `cal` (bit n for CAL_* n), from the calendars'
 * table (feasts.bin): its record's index, or -1. `hours` is the place's clock ahead of UTC (for the days set by
 * the Sun where it is). */
typedef struct FeastReader FeastReader;
int plan_feast_on(const FeastReader *rd, int32_t ordinal, uint32_t cal, float hours);

/* A rocket of a fireworks display (proto/feast_draw.py show_plan): launched at frame f0 from (x0, foot), it climbs
 * rise pixels in up frames, drifting aside, and bursts into n sparks reaching R pixels; kind 0 a peony, 1 a gold
 * willow, 2 crackling; its colour among the feast's sparks, the turn of its ring of sparks, the colour of the margin
 * round them (the window's ground where it bursts). */
typedef struct {
  uint8_t f0, rise, up, R, n, kind, colour, halo;
  int8_t drift;
  int16_t x0, foot;
  float turn;
} Rocket;
#define SHOW_ROCKETS 8
#define SHOW_FPS 12
#define SHOW_SPREAD 7                        /* frames a burst takes to open */
#define SHOW_LIFE 12                         /* frames its sparks then hang, drooping and fading */

/* The face's state: its data, the screen, and the window for the latitude (kept from one drawing to the next). */
typedef struct {
  const uint8_t *data, *geom;  /* the blobs: plan.bin and this screen's geom_*.bin */
  int w, h;
  bool rect;                   /* the Time 2's cushion ring, else the Round 2's circle */
  float lat_key;               /* the latitude the window was worked out for */
  float cx, cy, k, r_disc, R;
  float ceiling;               /* the window's top, at most, above the pole (the Round 2's almanac keeps its room) */
  int16_t wx0[MAX_H], wx1[MAX_H];      /* the window's span in each row (wx0 > wx1: none) */
  int16_t win_top, win_bottom;
  /* the ring for the latitude: the hours' rays leave the pole, which on the Time 2 moves with it */
  int16_t ticks[64][2];                /* the hour and half-hour ticks on one side (mirrored when drawn) */
  int nticks;
  int16_t studs[6][2];                 /* at 3, 6, 9, 15, 18 and 21 o'clock */
  int8_t num_style;                    /* the numerals placed for this style (-1: not yet) */
  int16_t numerals[6][2];              /* their top-left corners */
  int16_t ins_lo[4], ins_hi[4];        /* the inscriptions' room along the band (1/16 px) */
  bool lab_ok;                         /* the labours' places worked out for this window: */
  int16_t lab_at[2][2];                /* the labourer's (left) and the month's thing's (right) middles */
  /* the Sun's next rising or setting, kept until it passes (or the place changes) */
  int64_t ev_from, ev_at;
  int ev_kind;                         /* 1 rising, 2 setting, 0 none within a day; -1 not yet worked out */
  float ev_lat, ev_lon;
  /* the sky's news for the day (noon to noon), kept: what (NEWS_*), and its particulars */
  int32_t news_day;
  float news_lat, news_lon;
  uint8_t news, news_a, news_b;
  /* the day's feast in the kept calendars (plan_feast), kept until the day, the calendars or the place change */
  int32_t feast_day;                   /* the local date it is for (-1: not yet looked for) */
  uint32_t feast_cal;
  float feast_lat, feast_lon;          /* the place: its hemisphere, and its sky for the evening's first star */
  bool feast;                          /* there is one */
  uint8_t feast_flags, feast_sky;      /* FF_*; FS_* */
  int8_t feast_first;                  /* the evening's first star (FS_FIRST_STAR): a named star's index + 1, a
                                        * planet's -(index + 1), 0 none */
  uint8_t feast_eve;                   /* the day before's feast's FF_* if it ends at midnight with fireworks, or 0 */
  uint8_t feast_art_w, feast_art_h;    /* its emblem (0 wide: none): a bit a pixel, row by row, the low bit first */
  uint8_t feast_art[32];
  char feast_words[2][20];             /* its long and short words for the almanac's line */
  /* the minute written: the figures that changed since the last drawing, their pixels in a scribe's order (each
   * figure's outline from its top round clockwise, then its fill from the outline in), for plan_scribe to unveil a
   * few frames at a time; each x | y << 9 | the colour under it << 18 (GColor8's six bits) | its figure << 24. Made by
   * plan_render when Face.scribe asks, with its alloc; the next drawing releases it (or the caller, once played) */
  uint32_t *scribe;
  uint16_t scribe_n;                   /* its pixels */
  uint16_t scribe_lines;               /* how many of them (the first) are outlines, once ordered (0xFFFF: not yet) */
  uint8_t scribe_ink;                  /* their colour */
  /* the figures last drawn while a scribe was asked for (0..9, 10 h, 11 m), where, and for what time */
  int8_t time_c[8], time_n, time_style;
  int16_t time_x[8], time_y[8], time_hour, time_minute;
  /* the fireworks display at the top of this hour, if there is one: plan_render works it out then (from the window's
   * edge and ground), the display's own code (plan_show) plays it */
  int32_t show_hour;                   /* the local hour it is for (the date's ordinal * 24 + the hour), -1 none */
  uint8_t show_rockets, show_ink;      /* how many; 0 in colour, else the ink a printed chart engraves it in */
  uint8_t show_sparks[4];              /* the feast's colours (0 ends them) */
  uint16_t show_end;                   /* the frames it lasts, at SHOW_FPS */
  Rocket show[SHOW_ROCKETS];
  /* the passing event plan_render chose for this minute (EV_*, 0 none), played over event_frames frames: a meteor from
   * (event_x0, event_y0) the way of (event_x1, event_y1), or the birds crossing from row event_y0 to event_y1 (eastward
   * if event_x0), by the motion blob (plan_event), which works out their paths in the window; the figures, drawn
   * again along by the caller (Face.figs_part) */
  uint8_t event, event_frames, event_ink;      /* event_ink: the meteor's or the birds' colour (0: the meteor's own) */
  int16_t event_x0, event_y0, event_x1, event_y1;
  int32_t event_minute;                /* the minute last chosen for (local minutes since 1970: once a minute) */
  int32_t figs_day, birds_mark;        /* the day the figures were drawn in; the twilight the birds last flew */
  /* while drawing */
  uint8_t *rows[MAX_H];
  int16_t rx0[MAX_H], rx1[MAX_H];
} Plan;

/* The face's place from the phone's numbers (1e-4 degrees): here, so the app itself does no arithmetic in floats
 * (libgcc's would cost it a kilobyte and more). */
void plan_place(Face *f, int32_t lat_e4, int32_t lon_e4);
/* Set up for a screen of w x h (200 x 228 the Time 2, 260 x 260 the Round 2) with its blobs. */
void plan_init(Plan *p, int w, int h, const uint8_t *data, const uint8_t *geom);
/* The window for a latitude (worked out again only when it changes: about a tenth of a second on the watch). */
void plan_window(Plan *p, float lat);
/* Draw the face at `utc` (seconds since 1970), the local clock `offset` seconds ahead of UTC. The working memory
 * (a few kilobytes, freed before returning) comes from `alloc`; false if there was none. */
bool plan_render(Plan *p, const Face *f, int64_t utc, int32_t offset, const Target *t, void *(*alloc)(size_t),
                 void (*release)(void *));

/* ---- the renderer as the watch loads it ---------------------------------------------------------------------------
 * On the watch the renderer (plan_render.c, plan_astro.c, plan_math.c, plan_blob.c) is not linked into the app: it is
 * a code blob among the app's resources (tools/build_blob.py), which main.c loads into memory at start, relocates,
 * hands to memory_cache_flush() (the SDK's call for code an app loads to run) and calls through this table. So the
 * app's own binary stays small (PebbleOS caps it at 64 KB) and the renderer has the rest of the app's memory. The
 * layout number keeps a blob from one build from running with another's structures. */
#define PLAN_API_MAGIC 0x4e414c50u           /* "PLAN" */
#define PLAN_API_VERSION 5u
#define PLAN_LAYOUT ((PLAN_API_VERSION << 28) ^ ((uint32_t)sizeof(Plan) << 12) ^ ((uint32_t)sizeof(Face) << 4) ^ \
                     (uint32_t)sizeof(Weather))
typedef struct {
  uint32_t magic, layout;
  void (*init)(Plan *p, int w, int h, const uint8_t *data, const uint8_t *geom);
  bool (*render)(Plan *p, const Face *f, int64_t utc, int32_t offset, const Target *t, void *(*alloc)(size_t),
                 void (*release)(void *));
  void (*place)(Face *f, int32_t lat_e4, int32_t lon_e4);
} PlanApi;
/* The calendars' code, a blob of its own (plan_feasts.c and the ephemeris it asks), which the watch loads only to look
 * up the day's feast, once a day, with the calendars' table (feasts.bin), and lets go: the renderer reads the answer
 * the Plan keeps. True when the Plan's answer is for this day, these calendars and this place (so a NULL table asks
 * only whether a look is needed). */
#define FEAST_API_MAGIC 0x54534546u          /* "FEST" */
/* how the calendars' code reads the calendars' table (feasts.bin), a few bytes at a time: from the resources on the
 * watch, so the whole table is never in memory; from memory elsewhere (plan_feast_memory) */
struct FeastReader { void (*read)(void *ctx, uint32_t at, void *buf, uint32_t n); void *ctx; };
void plan_feast_memory(FeastReader *rd, const uint8_t *table);
typedef struct {
  uint32_t magic, layout;
  bool (*feast)(Plan *p, const Face *f, int64_t utc, int32_t offset, const FeastReader *rd);
} FeastApi;
bool plan_feast(Plan *p, const Face *f, int64_t utc, int32_t offset, const FeastReader *rd);

/* The fireworks display's code, a blob of its own (plan_show.c), which the watch loads at the top of an hour that
 * brings one and plays SHOW_FPS times a second over the face as last drawn: each frame puts back the pixels the last
 * covered (kept in a ShowUndo) and draws its own. Frame `end` (Plan.show_end) only puts back. True while the display
 * goes on. */
#define SHOW_API_MAGIC 0x574f4853u           /* "SHOW" */
typedef struct { uint16_t n, cap; uint32_t px[]; } ShowUndo;   /* each x | y << 9 | the colour << 18 */
#define SHOW_UNDO 1024                       /* the pixels a frame may cover (the most seen is under 450: check_memory) */
/* The minute written, from the same blob: a frame over the face as last drawn (Plan.scribe, which frame 0 first puts
 * in a scribe's order, with `room` for a word a pixel to sort them in): frame 0 takes away the figures that changed,
 * the next SCRIBE_FRAMES - 1 write them again, their outlines and then their fill. True while frames remain. */
#define SCRIBE_FRAMES 8
typedef struct {
  uint32_t magic, layout;
  bool (*frame)(Plan *p, const Target *t, int frame, ShowUndo *undo);
  bool (*scribe)(Plan *p, const Target *t, int frame, uint32_t *room);
  bool (*event)(Plan *p, const Target *t, int frame, ShowUndo *undo);
} ShowApi;
bool plan_show(Plan *p, const Target *t, int frame, ShowUndo *undo);
bool plan_scribe(Plan *p, const Target *t, int frame, uint32_t *room);
/* The meteor or the birds (Plan.event), from the same blob, as the display is played: frame event_frames only puts
 * back. True while the event goes on. */
#define EVENT_UNDO 96
bool plan_event(Plan *p, const Target *t, int frame, ShowUndo *undo);

/* The scene blob (plan_decor.c): what plan_render asks of it, where the card is laid: the labours (faint in the card
 * round the window) and the Time 2's corner tools, drawn into the Plan's rows. */
typedef struct DecorCtx {
  Plan *p;
  int month;                   /* the labours' month, 0..11 (half a year round in the south) */
  int col;                     /* the meridian's column */
  float cx;                    /* the pole's x */
  uint8_t tone, ink, accent;   /* the scene's tone (the ring hatching's); the plate's ink and its red */
  uint8_t sun_sign, moon_sign; /* the signs the Sun and the Moon are in, 0 Aries .. 11 Pisces */
  uint8_t theme;               /* the scene to draw (THEME_*) */
  bool tools, line_only;       /* the theme's corner pieces; those as their outlines alone, in the ink */
  void *(*alloc)(size_t);
  void (*release)(void *);
  const FeastReader *scenes;   /* (set by plan_decor: the woodcuts' table) */
  uint8_t planets[4];          /* the brightest planets above the horizon, brightest first (VENUS ..; 255 none) */
  const Tides *tides;          /* the tide here (NULL: none), and the minute (since 1970), for the sea's water */
  uint32_t minute;
  uint8_t moon_phase;          /* the Moon's phase as the sea's corner draws it, 0 new .. 4 full .. 7 (mirrored south) */
} DecorCtx;
#define DECOR_API_MAGIC 0x524F4344u          /* "DCOR" */
typedef struct {
  uint32_t magic, layout;
  bool (*draw)(const DecorCtx *d, const FeastReader *tools, const FeastReader *scenes);
} DecorApi;
/* tools: tools.bin, scenes: scenes.bin (proto/woodcuts.py), each read as it goes (NULL: none). Two blobs: the labours
 * and the corner tools (plan_labours.c) for the plain card and the labours, the woodcuts and their roundels
 * (plan_decor.c) for the rest; decor_labours says which a theme's is. */
bool plan_decor(const DecorCtx *d, const FeastReader *tools, const FeastReader *scenes);
bool plan_labours(const DecorCtx *d, const FeastReader *tools, const FeastReader *scenes);
static inline bool decor_labours(int theme) { return theme <= THEME_LABOURS; }
