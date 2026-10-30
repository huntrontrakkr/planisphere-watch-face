/* Planisphere: the sky over where you are, turning with the hours under the card's oval window, the Sun riding
 * the ring as the hour hand. The face is drawn by plan_render.c, the same C the settings page's preview runs; on
 * the watch it is not linked in here but kept among the app's resources as code, loaded at start (load_code).
 *
 * The phone sends where it is (and the weather there, from Open-Meteo) and the owner's settings; the watch keeps
 * them, and draws the face every minute.
 */
#include <pebble.h>
#include "plan.h"

/* Nothing here is in a hot loop: built for size. */
#pragma GCC optimize("Os")

#define SETTINGS_VERSION 12
/* the animations, a bit each (Settings.animations): the passing events (from version 5) are Face.events' bits, two up */
enum { ANIM_MINUTE = 1, ANIM_FIREWORKS = 2, ANIM_METEORS = 4, ANIM_FIGURES = 8, ANIM_BIRDS = 16, ANIM_VILLAGE = 32 };
#define ANIM_ALL 63
#define ANIM_EVENTS 60
#define KEY_SETTINGS 1
#define KEY_PLACE 2
#define KEY_WEATHER 3
#define KEY_TIDES 4
#define INBOX 320                        /* bytes: the whole settings message (about 150), with room to grow */
#define WEATHER_FRESH (3 * 3600)         /* s: the weather is shown this long after it came */
#define ASK_EVERY (30 * 60)              /* and the phone asked for it again after this */
#define ASK_RETRY (10 * 60)              /* asking at most this often */

typedef struct {
  uint8_t version, plate, clock, names, weather, units, place;
  uint8_t theme;                        /* the card's scene, THEME_* (to version 7: 1 the labours, so as before) */
  int32_t lat_e4, lon_e4;               /* the place given on the settings page (PLACE 1) */
  uint32_t calendars;                   /* the calendars whose days the face keeps (bit n for CAL_* n) */
  char city[40], country[28];           /* each a ladder of shorter forms, "|" between (from version 7) */
  uint8_t animations;                   /* a bit an animation, ANIM_* (from version 3; these bits from 4 and 5) */
  uint8_t corners;                      /* the Time 2's corners: whose pieces, THEME_* (Face.corners; 0 the sprigs). To
                                         * version 7 a switch, the theme's (no theme: the labours' tools; to 6, theirs) */
  uint8_t tide_times;                   /* the next high and low waters low on the face (in version 7's spare byte: 0 before) */
  uint8_t gild;                         /* the time gilt (from version 9, in the record's last spare byte) */
  uint8_t figures;                      /* the figures drawn in again: 0 at dusk alone, 1 each hour, 2 each half hour,
                                         * 3 each quarter (from version 10) */
  uint8_t flick;                        /* a flick of the wrist: 0 nothing, 1 the figures drawn in, 2 the sky spun (11) */
  uint8_t candle;                       /* the battery's candle in the card (from version 11; off unless chosen) */
  uint8_t flicks;                       /* the flicks it takes: 1, or 2 (the second within FLICK_PAIR_MS of the first,
                                         * which may only have lit the screen) (from version 12) */
} Settings;
typedef struct {                        /* versions 2 to 6, the names' room smaller (version 2's ends at animations) */
  uint8_t version, plate, clock, names, weather, units, place, labours;
  int32_t lat_e4, lon_e4;
  uint32_t calendars;
  char city[24], country[20];
  uint8_t animations, tools;
} SettingsOld;
_Static_assert(offsetof(SettingsOld, city) == offsetof(Settings, city), "the settings' head as before");
_Static_assert(sizeof(Settings) == ((offsetof(Settings, flicks) + 1 + 3) & ~3u), "the settings' record: no stray padding");

typedef struct {                        /* where the phone last was */
  int32_t lat_e4, lon_e4;
  char city[40], country[28];           /* the ladders, as Settings' */
  uint32_t time;                        /* 0: never */
} Place;
typedef struct { int32_t lat_e4, lon_e4; char city[24], country[20]; uint32_t time; } PlaceOld;   /* (to 0.1.6) */

typedef struct { Weather w; uint32_t time; } Stored;

/* diagnostics, readable over GDB in the emulator (g_code: where the renderer's code was loaded; g_utc, g_offset:
 * the moment last drawn, for tools/host to draw again) */
volatile uint32_t g_render_ms = 0, g_render_max = 0, g_heap_free = 0, g_heap_low = 0, g_code = 0, g_utc = 0;
volatile uint32_t g_frames_failed = 0;   /* frames the renderer had no room for */
volatile int32_t g_offset = 0;
/* the stack's deepest (stack_deepest), ever and by the end of init; and how deep it is where the renderer is called */
volatile uint32_t g_stack = 0, g_stack_init = 0, g_stack_at = 0;
volatile uint32_t g_feast_heap = 0;      /* the heap free while the calendars' code and table are loaded */
/* the fireworks displays: frames drawn, the slowest frame (ms), the heap free while one plays */
volatile uint32_t g_show_frames = 0, g_show_ms = 0, g_show_heap = 0, g_show_end = 0;   /* (1 played out, 2 gave way) */
volatile uint32_t g_show_px = 0;         /* the most pixels a frame covered */
volatile uint32_t g_scribe_frames = 0;   /* the minute written: frames drawn */
volatile uint32_t g_events = 0, g_event_frames = 0;   /* the passing events begun (each EV_* bit once seen), frames */

static Window *s_window;
static Layer *s_layer;
static Plan *s_plan;
static const PlanApi *s_api;
static uint8_t *s_code, *s_data, *s_geom;
static Settings s_settings;
static Place s_place;
static Stored s_weather;
static Tides s_tides;                   /* the tide here, as the phone last sent it (n 0: none) */
static uint32_t s_asked;

static void defaults(Settings *s) {
  memset(s, 0, sizeof *s);
  s->version = SETTINGS_VERSION;
  s->plate = PLATE_PLANISPHERE, s->names = 1, s->weather = 1, s->animations = ANIM_ALL, s->flicks = 2;
}

static uint32_t now_ms(void) {
  time_t s;
  uint16_t ms;
  time_ms(&s, &ms);
  return (uint32_t)s * 1000u + ms;
}

/* How deep the stack has been, in bytes (after Groundtrack). PebbleOS gives an app 2 KB of it less a 32-byte guard
 * (APP_STACK_NORMAL_SIZE in its app_manager.c), just below the app itself, whose header leads it, and the system's
 * own calls run on it too. Past the guard a watch stops the app; the emulator does not, so the app marks what it
 * has not yet used as it starts, and g_stack says how much of that has since been written over. */
#define STACK_BYTES (2048 - 32)
#define STACK_MARK 0xA5
extern const uint8_t __pbl_app_info[];
static void stack_mark(void) {
  volatile uint8_t here = 0;
  const uintptr_t top = (uintptr_t)__pbl_app_info;
  for (uintptr_t a = top - STACK_BYTES; a < (uintptr_t)&here - 96; a++) *(volatile uint8_t *)a = STACK_MARK;
}
static uint32_t stack_deepest(void) {
  const uintptr_t top = (uintptr_t)__pbl_app_info;
  uintptr_t a = top - STACK_BYTES;
  while (a < top && *(volatile const uint8_t *)a == STACK_MARK) a++;
  return (uint32_t)(top - a);
}

/* ---- the place and the weather ---- */

/* the phone looks up where it is and the weather there; asked when what we have is old */
/* the phone asked for the weather and the place when they are old; and told the watch's own 12/24-hour clock when it
 * has not heard it (the settings page's preview follows it) */
static int8_t s_told24 = -1;
static void ask_phone(bool force) {
  uint32_t now = (uint32_t)time(NULL);
  if (!connection_service_peek_pebble_app_connection()) return;
  bool c24 = clock_is_24h_style(), tell = s_told24 != (int8_t)c24;
  bool ask = !(!force && s_weather.time && now - s_weather.time < ASK_EVERY && s_place.time) &&
             !(!force && s_asked && now - s_asked < ASK_RETRY);
  if (!ask && !tell) return;
  DictionaryIterator *out;
  if (app_message_outbox_begin(&out) != APP_MSG_OK) return;
  if (ask) dict_write_uint8(out, MESSAGE_KEY_REQUEST, 1);
  dict_write_uint8(out, MESSAGE_KEY_CLOCK24, c24);
  if (app_message_outbox_send() == APP_MSG_OK) {
    if (ask) s_asked = now;
    s_told24 = (int8_t)c24;
  }
}
static void ask_later(void *data) { ask_phone(false); }

/* ---- drawing ---- */

static uint8_t *fb_row(void *ctx, int y, int *x0, int *x1) {
  GBitmapDataRowInfo info = gbitmap_get_data_row_info((GBitmap *)ctx, (uint16_t)y);
  *x0 = info.min_x, *x1 = info.max_x;
  return info.data;
}

/* local time ahead of UTC, in seconds */
static int32_t utc_offset(time_t now) {
  struct tm *t = localtime(&now);
  int y = t->tm_year + 1900, m = t->tm_mon + 1, d = t->tm_mday;
  /* days from 1970-01-01 to the local date (Howard Hinnant's days_from_civil) */
  y -= m <= 2;
  int era = (y >= 0 ? y : y - 399) / 400, yoe = y - era * 400;
  int doy = (153 * (m + (m > 2 ? -3 : 9)) + 2) / 5 + d - 1, doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
  int32_t days = era * 146097 + doe - 719468;
  int64_t local = (int64_t)days * 86400 + t->tm_hour * 3600 + t->tm_min * 60 + t->tm_sec;
  return (int32_t)(local - (int64_t)now);
}

/* the animations the settings keep, if the battery is not low (under a fifth and not charging: none) */
static int animations(void) {
  BatteryChargeState battery = battery_state_service_peek();
  return battery.charge_percent >= 20 || battery.is_charging ? s_settings.animations : 0;
}

/* the scene blob (plan_decor.c, the woodcuts' themes) and the labours' (plan_labours.c, the labours and the corner
 * tools): loaded when the renderer asks for the card's backdrop or the corners (Face.decor), one, or one after the
 * other where the backdrop and the corners are each's (decor_run), for the moment each draws, and let go; on the Time 2
 * the labours' reads the month's tools from their table as it goes */
static const void *load_blob(uint32_t resource, uint8_t **mem);
static void resource_read(void *ctx, uint32_t at, void *buf, uint32_t n);
/* a resource's handle, kept once got: the firmware checks a resource through on each getting, and the scene blob
 * and its tables are got every minute */
static ResHandle handle_of(uint32_t id) {
  static struct { uint32_t id; ResHandle h; } kept[5];   /* (the scene blobs, their two tables, the motion blob) */
  static int n;
  for (int i = 0; i < n; i++)
    if (kept[i].id == id) return kept[i].h;
  ResHandle h = resource_get_handle(id);
  if (n < 5 && id != RESOURCE_ID_PLAN_CODE && id != RESOURCE_ID_PLAN_FEAST_CODE && id != RESOURCE_ID_PLAN_FEASTS)
    kept[n].id = id, kept[n].h = h, n++;
  return h;
}
volatile uint32_t g_decor_heap = 0;      /* the heap free while the scene blob is loaded */
static bool decor_call(void *ctx, bool labours, const DecorCtx *dc) {
  uint8_t *mem;
  const DecorApi *api = load_blob(labours ? RESOURCE_ID_PLAN_LABOURS_CODE : RESOURCE_ID_PLAN_DECOR_CODE, &mem);
  bool ok = false;
  if (api && api->magic == DECOR_API_MAGIC && api->layout == PLAN_LAYOUT) {
    g_decor_heap = heap_bytes_free();
    ResHandle sh = handle_of(RESOURCE_ID_PLAN_SCENES);
    FeastReader scenes = {resource_read, &sh};
#if PBL_RECT
    ResHandle h = handle_of(RESOURCE_ID_PLAN_TOOLS);
    FeastReader rd = {resource_read, &h};
    ok = api->draw(dc, &rd, &scenes);
#else
    ok = api->draw(dc, NULL, &scenes);
#endif
  }
  free(mem);
  return ok;
}
static bool decor_draw(void *ctx, const DecorCtx *dc) { return decor_run(ctx, dc, decor_call); }

/* a flick of the wrist (the accelerometer's tap): the sky as a chart shows it (Face.chart) dissolving in over the
 * face out from the pole, held a moment, and the face back the same way (Face.reveal; 0 the whole); or the sky spun a
 * day round (SPIN_TURNS), then the face at rest. Their frames the window's alone (Face.window_only) but the last, each
 * CHART_MS or SPIN_MS after the one before began, or as soon after as its drawing allows */
static int s_flick;                     /* a flick's wish, till the next frame takes it: Settings.flick */
static int s_spin_k;                    /* the spin's frames drawn (0: none playing) */
static const int16_t SPIN[SPIN_FRAMES] = SPIN_TURNS;
static int s_chart_k;                   /* the chart's frames drawn: 1..CHART_STEPS in, then as many out (0: none) */
static const uint8_t CHART_REVEAL[CHART_STEPS] = CHART_REVEALS;
#define CHART_MS 80
#define CHART_HOLD_MS 2500
static uint32_t s_frame_t0;             /* when the frame being drawn began (now_ms) */
#define FLICK_PAIR_MS 4000           /* (two flicks: the second within four seconds, time to see the screen lit) */
static int32_t s_where[2];              /* the face's place as face_of sets it, 1e-4 degrees (latitude, longitude) */
static void face_of(Face *f) {
  memset(f, 0, sizeof *f);
  f->plate = s_settings.plate < PLATE_COUNT ? s_settings.plate : 0;
  f->clock24 = s_settings.clock == 0 ? clock_is_24h_style() : s_settings.clock == 2;
  f->names = s_settings.names, f->theme = s_settings.theme < THEME_COUNT ? s_settings.theme : 0, f->calendars = s_settings.calendars;
  f->scribe = animations() & ANIM_MINUTE;
  f->events = (uint8_t)((animations() & ANIM_EVENTS) >> 2);
  f->fahrenheit = s_settings.units == 2;
  if (s_settings.place == 1) {
    s_where[0] = s_settings.lat_e4, s_where[1] = s_settings.lon_e4;
    f->city = s_settings.city, f->country = s_settings.country, f->coords = true;
  } else if (s_place.time) {
    s_where[0] = s_place.lat_e4, s_where[1] = s_place.lon_e4;
    f->city = s_place.city, f->country = s_place.country, f->coords = true;
  } else {
    /* not yet told where it is: a northern sky, at the longitude the time zone suggests */
    s_where[0] = 400000, s_where[1] = utc_offset(time(NULL)) / 240 * 10000;
  }
  s_api->place(f, s_where[0], s_where[1]);
  f->gild = s_settings.gild != 0, f->figures_every = s_settings.figures & 3;
  BatteryChargeState bat = battery_state_service_peek();
  f->battery = bat.charge_percent, f->charging = bat.is_charging, f->candle = s_settings.candle != 0;
  f->turn = s_spin_k ? SPIN[s_spin_k - 1] : 0;
  f->corners = PBL_IF_RECT_ELSE(s_settings.corners < THEME_COUNT ? s_settings.corners : 0, 0);
  f->decor = decor_draw;
  uint32_t now = (uint32_t)time(NULL);
  if (s_settings.weather && s_weather.time && now - s_weather.time < WEATHER_FRESH) f->weather = &s_weather.w;
  f->tides = s_tides.n ? &s_tides : NULL, f->tide_times = s_settings.tide_times;
}

static const void *load_blob(uint32_t resource, uint8_t **mem);

/* the calendars' table read straight from the resources, a few bytes at a time */
static void resource_read(void *ctx, uint32_t at, void *buf, uint32_t n) {
  memset(buf, 0, n);
  resource_load_byte_range(*(ResHandle *)ctx, at, buf, n);
}

/* the day's feast in the kept calendars, looked up once a day (when the day, the calendars or the place change: the
 * place for its hemisphere and its evening's first star): the calendars' code loaded for that from the resources, and
 * let go before the face is drawn. (The key in integers, as the Plan's in floats would bring libgcc's compares.) */
static int32_t s_looked[2];             /* the place the Plan's feast was looked up for (as s_where) */
static void feast_of_day(const Face *f, time_t now, int32_t offset) {
  int32_t day = (int32_t)((now + offset) / 86400) + 719163;     /* (32-bit arithmetic: the watch's clock is) */
  if (!f->calendars) {                                          /* none kept, as plan_feast keeps it */
    s_plan->feast = false, s_plan->feast_cal = 0;
    return;
  }
  if (s_plan->feast_day == day && s_plan->feast_cal == f->calendars && s_looked[0] == s_where[0] &&
      s_looked[1] == s_where[1])
    return;
  /* the lookup borrows the screen's geometry's memory, which only the drawing reads and which lies against the free
   * memory (load_data): let go for the lookup's few milliseconds and loaded again, so the calendars' code has room
   * beside the renderer's */
  ResHandle g = resource_get_handle(RESOURCE_ID_PLAN_GEOM);
  free(s_geom), s_geom = NULL, s_plan->geom = NULL;
  uint8_t *mem;
  const FeastApi *api = load_blob(RESOURCE_ID_PLAN_FEAST_CODE, &mem);
  if (api && api->magic == FEAST_API_MAGIC && api->layout == PLAN_LAYOUT) {
    ResHandle h = handle_of(RESOURCE_ID_PLAN_FEASTS);
    FeastReader rd = {resource_read, &h};
    g_feast_heap = heap_bytes_free();
    if (api->feast(s_plan, f, (int64_t)now, offset, &rd)) s_looked[0] = s_where[0], s_looked[1] = s_where[1];
  }
  free(mem);
  if ((s_geom = malloc(resource_size(g)))) resource_load(g, s_geom, resource_size(g));
  s_plan->geom = s_geom;
}

/* the renderer's memory, and how little was left */
static void *alloc(size_t n) {
  void *p = malloc(n);
  if (heap_bytes_free() < g_heap_low) g_heap_low = heap_bytes_free();
  return p;
}

/* ---- the animations: the minute written as a scribe writes (Plan.scribe, the figures that changed, kept by the
 * renderer when the settings ask and the battery allows) and the fireworks display at the top of an hour that brings
 * one (Plan.show_hour). Their code is the motion blob, loaded while either plays; each plays SHOW_FPS frames a second
 * over the face as drawn (a frame a tick of the timer: the clock may jump). A drawing asked for meanwhile (the weather,
 * the settings, the next minute) waits for their end. One the system asks for (as the app opens, say) is made at once,
 * as the face and the animations have no room for both: the minute is then simply drawn, and the display gives way
 * and takes up its time again. ---- */
static const ShowApi *s_motion;
static uint8_t *s_motion_mem;
static AppTimer *s_anim_timer;
static bool s_anim_due;                 /* the timer's frame is due at the next drawing */
static bool s_redraw_after;
static int s_scribe_k;                  /* the minute written: its next frame (0: none playing) */
static bool s_show;                     /* a display playing */
static ShowUndo *s_undo;
static int32_t s_show_played = -1;      /* the hour whose display has begun, */
static bool s_show_done;                /* and played out */
static int s_show_last = -1;            /* its frame last drawn */

static int s_event_k;                   /* the meteor or the birds: its next frame + 1 (0: none playing) */
static ShowUndo *s_event_undo;
static int s_figs_k;                    /* the figures drawn in: the frames drawn (0: none playing) */

static bool animating(void) { return s_show || s_scribe_k || s_event_k || s_figs_k || s_spin_k || s_chart_k; }

static void redraw(void) {
  if (animating()) s_redraw_after = true;
  else if (s_layer) layer_mark_dirty(s_layer);
}
/* a drawing soon: the phone's messages come a few at a time (the place and its name, the weather, the tide), and
 * one drawing serves them all */
static AppTimer *s_redraw_timer;
static void redraw_now(void *data) { s_redraw_timer = NULL, redraw(); }
static void redraw_soon(void) {
  if (s_redraw_timer) app_timer_reschedule(s_redraw_timer, 400);
  else s_redraw_timer = app_timer_register(400, redraw_now, NULL);
}

static bool motion_load(void) {
  if (s_motion) return true;
  s_motion = load_blob(RESOURCE_ID_PLAN_SHOW_CODE, &s_motion_mem);
  if (s_motion && s_motion->magic == SHOW_API_MAGIC && s_motion->layout == PLAN_LAYOUT) return true;
  free(s_motion_mem), s_motion_mem = NULL, s_motion = NULL;
  return false;
}

/* the motion blob let go (anims_settle, once nothing plays; and when the animations give way to a whole face, which
 * has no room beside it) */
static void motion_unload(void) { free(s_motion_mem), s_motion_mem = NULL, s_motion = NULL; }

static void anim_tick(void *data) {
  s_anim_timer = NULL, s_anim_due = true;
  if (s_layer) layer_mark_dirty(s_layer);
}

static void scribe_end(void) {
  free(s_plan->scribe), s_plan->scribe = NULL, s_plan->scribe_n = 0, s_scribe_k = 0;
}

static void show_end(void) { free(s_undo), s_undo = NULL, s_show = false; }

static void event_end(void) {
  free(s_event_undo), s_event_undo = NULL, s_event_k = 0, s_figs_k = 0, s_spin_k = 0, s_chart_k = 0;
}

/* when nothing plays: the timer stopped, the blob let go, and a drawing that waited made */
static void anims_settle(bool redraw_now) {
  if (animating()) {
    int ms = s_figs_k ? 150 : s_spin_k ? SPIN_MS : s_chart_k ? (s_chart_k == CHART_STEPS ? CHART_HOLD_MS : CHART_MS)
           : 1000 / SHOW_FPS;
    ms -= (int)(now_ms() - s_frame_t0);          /* (the drawing's own time counted in) */
    if (!s_anim_timer) s_anim_timer = app_timer_register(ms > 10 ? ms : 10, anim_tick, NULL);
    return;
  }
  if (s_anim_timer) app_timer_cancel(s_anim_timer), s_anim_timer = NULL;
  s_anim_due = false;
  motion_unload();
  if (s_redraw_after && redraw_now && s_layer) layer_mark_dirty(s_layer);
  s_redraw_after = false;
}

/* after a whole face: the minute's new figures taken away (on the same screen, before it is shown), to be written */
static void scribe_begin(const Target *tg) {
  if (!s_plan->scribe) return;
  uint32_t *room = malloc(s_plan->scribe_n * sizeof *room);
  if (room && motion_load() && s_motion->scribe(s_plan, tg, 0, room)) s_scribe_k = 1;
  else scribe_end();
  free(room);
}

static void show_begin(void) {
  if (s_show || s_figs_k || s_spin_k || s_chart_k || s_plan->show_hour < 0 || !(animations() & ANIM_FIREWORKS)) return;
  if (s_plan->show_hour != s_show_played) s_show_played = s_plan->show_hour, s_show_last = -1, s_show_done = false;
  else if (s_show_done) return;                  /* (else it gave way, and goes on from its last frame) */
  s_undo = malloc(sizeof(ShowUndo) + SHOW_UNDO * sizeof(uint32_t));
  if (!s_undo || !motion_load()) {
    show_end();
    return;
  }
  s_undo->n = 0, s_undo->cap = SHOW_UNDO, s_show = true;
  g_show_heap = heap_bytes_free();
}

/* after a whole face: the passing event it chose, begun (the figures drawn in are drawn again, the face and all; the
 * meteor or the birds played over it once the minute is written) */
static void event_begin(void) {
  uint8_t ev = s_plan->event;
  g_events |= ev;
  if (ev == EV_FIGURES) {
    scribe_end(), s_figs_k = 1;                  /* (the minute simply drawn) */
    return;
  }
  if (!(ev & (EV_METEOR | EV_BIRDS)) || s_show) return;
  s_event_undo = malloc(sizeof(ShowUndo) + EVENT_UNDO * sizeof(uint32_t));
  if (!s_event_undo || !motion_load()) {
    event_end();
    return;
  }
  s_event_undo->n = 0, s_event_undo->cap = EVENT_UNDO, s_event_k = 1;
}

/* a frame of each animation playing */
static void animate(GContext *ctx) {
  uint32_t t0 = now_ms();
  GBitmap *fb = graphics_capture_frame_buffer(ctx);
  if (!fb) {                                     /* (no screen to draw on: they end, the face is drawn again) */
    if (s_show) s_show_done = true;
    scribe_end(), show_end(), event_end(), s_redraw_after = true;
    anims_settle(true);
    return;
  }
  Target tg = {fb_row, fb};
  if (s_scribe_k) {
    g_scribe_frames++;
    if (!s_motion->scribe(s_plan, &tg, s_scribe_k++, NULL)) scribe_end();
  } else if (s_event_k) {                        /* (after the minute is written) */
    g_event_frames++;
    if (!s_motion->event(s_plan, &tg, s_event_k++ - 1, s_event_undo)) event_end();
  }
  if (s_show) {
    bool more = s_motion->frame(s_plan, &tg, ++s_show_last, s_undo);
    g_show_frames++;
    if (s_undo->n > g_show_px) g_show_px = s_undo->n;
    if (!more) g_show_end = 1, s_show_done = true, show_end();
  }
  graphics_release_frame_buffer(ctx, fb);
  if (now_ms() - t0 > g_show_ms) g_show_ms = now_ms() - t0;
  anims_settle(true);
}

static void update(Layer *layer, GContext *ctx) {
  s_frame_t0 = now_ms();
  int figs = 0;                                  /* the figures' frame drawn in, if they are being (Face.figs_part) */
  if (s_anim_due && s_figs_k) {
    s_anim_due = false;
    figs = ++s_figs_k < EVENT_FIGS_FRAMES ? s_figs_k : 0;
    if (!figs) s_figs_k = 0;
  } else if (s_anim_due && s_chart_k) {          /* the chart's next step; past the last, the face at rest */
    s_anim_due = false;
    if (++s_chart_k > 2 * CHART_STEPS) s_chart_k = 0;
  } else if (s_anim_due && s_spin_k) {           /* the spin's next turn; past the last, the face at rest */
    s_anim_due = false;
    if (++s_spin_k > SPIN_FRAMES) s_spin_k = 0;
  } else if (s_anim_due) {
    s_anim_due = false;
    animate(ctx);
    return;
  } else if (animating()) {                      /* the system asks for the whole face: the animations give way */
    if (s_show) g_show_end = 2;
    scribe_end(), show_end(), event_end(), s_redraw_after = false;
    if (!animating()) motion_unload();           /* (their code too: the face has no room beside it) */
  }
  if (s_flick && !animating()) {                 /* a flick of the wrist: the figures drawn in, or the sky spun */
    if (s_flick == 1) scribe_end(), s_chart_k = 1;
    else s_spin_k = 1;
  }
  s_flick = 0;
  time_t now = time(NULL);
  if (s_plan && !s_geom) {                       /* (the geometry not loaded again after a lookup: once more) */
    ResHandle g = resource_get_handle(RESOURCE_ID_PLAN_GEOM);
    if ((s_geom = malloc(resource_size(g)))) resource_load(g, s_geom, resource_size(g));
    s_plan->geom = s_geom;
  }
  if (!s_plan || !s_geom) {                      /* no memory for the face's data: the time alone */
    graphics_context_set_fill_color(ctx, GColorBlack);
    graphics_fill_rect(ctx, layer_get_bounds(layer), 0, GCornerNone);
    char text[8];
    strftime(text, sizeof text, clock_is_24h_style() ? "%H:%M" : "%I:%M", localtime(&now));
    graphics_context_set_text_color(ctx, GColorWhite);
    GRect b = layer_get_bounds(layer);
    graphics_draw_text(ctx, text, fonts_get_system_font(FONT_KEY_LECO_42_NUMBERS), GRect(0, b.size.h / 2 - 28, b.size.w, 50),
                       GTextOverflowModeFill, GTextAlignmentCenter, NULL);
    return;
  }
  uint32_t t0 = now_ms();
  GBitmap *fb = graphics_capture_frame_buffer(ctx);
  if (!fb) return;
  Face f;
  face_of(&f);
  if (s_figs_k) f.scribe = false, f.figs_part = (uint8_t)figs;
  if (s_spin_k) f.scribe = false, f.window_only = true;
  if (s_chart_k)                                 /* (in, then out; the last the whole face) */
    f.scribe = false, f.chart = s_chart_k <= CHART_STEPS, f.reveal = CHART_REVEAL[(s_chart_k - 1) % CHART_STEPS],
    f.window_only = s_chart_k < 2 * CHART_STEPS;
  Target tg = {fb_row, fb};
  if (heap_bytes_free() < g_heap_low || !g_heap_low) g_heap_low = heap_bytes_free();
  g_utc = (uint32_t)now, g_offset = utc_offset(now);
  g_stack_at = (uint32_t)((uintptr_t)__pbl_app_info - (uintptr_t)&tg);
  feast_of_day(&f, now, g_offset);
  bool drawn = s_api->render(s_plan, &f, (int64_t)now, g_offset, &tg, alloc, free);
  /* no room for the frame (the face stays as it was): tried again soon, twice at most, then at the next minute */
  static int failed;
  if (!drawn) { g_frames_failed++; if (++failed <= 2) redraw_soon(); }
  else failed = 0;
  if (drawn && !s_figs_k && !s_spin_k && !s_chart_k && s_plan->event == EV_FIGURES) event_begin();   /* (frame 1 of the figures drawn in) */
  /* a fireworks display due takes its memory first; the minute's figures then simply appear (written, they would
   * hold the motion blob's and their record's room while the display asks for its own, and the display went
   * without: the heap is short, and in pieces by then) */
  if (drawn) show_begin();
  if (drawn && !s_show) scribe_begin(&tg);
  else scribe_end();
  graphics_release_frame_buffer(ctx, fb);
  g_render_ms = now_ms() - t0;
  if (g_render_ms > g_render_max) g_render_max = g_render_ms;
  g_stack = stack_deepest();
  if (drawn && !s_figs_k && !s_spin_k && !s_chart_k && s_plan->event != EV_FIGURES) event_begin();
  anims_settle(false);
}

static void tap(AccelAxisType axis, int32_t direction) {
  if (!s_settings.flick || !animations() || animating()) return;
  static uint32_t first;                         /* (the first of two flicks, when two are asked: its time, 0 none) */
  uint32_t now = now_ms();
  if (s_settings.flicks != 1 && (!first || now - first > FLICK_PAIR_MS)) { first = now ? now : 1; return; }
  first = 0;
  s_flick = s_settings.flick;
  if (s_layer) layer_mark_dirty(s_layer);
}
static void on_battery(BatteryChargeState b) { redraw_soon(); }

static void tick(struct tm *t, TimeUnits changed) {
  redraw();
  if (t->tm_min % 10 == 0) ask_phone(false);
}

/* ---- messages from the phone ---- */

/* what each message key sets: a byte, a 16-bit or 32-bit number, or text, at an offset in one of the three records */
enum { IN_SETTINGS, IN_PLACE, IN_WEATHER };
enum { IN_U8, IN_I16, IN_I32, IN_TEXT };
#define IN(key, rec, type, s, f) {&MESSAGE_KEY_##key, rec, type, (uint8_t)offsetof(s, f), (uint8_t)sizeof(((s *)0)->f)}
static const struct { const uint32_t *key; uint8_t rec, type, off, size; } KEYS[] = {
  IN(PLATE, IN_SETTINGS, IN_U8, Settings, plate), IN(CLOCK, IN_SETTINGS, IN_U8, Settings, clock),
  IN(NAMES, IN_SETTINGS, IN_U8, Settings, names), IN(WEATHER, IN_SETTINGS, IN_U8, Settings, weather),
  IN(UNITS, IN_SETTINGS, IN_U8, Settings, units), IN(PLACE, IN_SETTINGS, IN_U8, Settings, place),
  IN(LABOURS, IN_SETTINGS, IN_U8, Settings, theme), IN(CORNERS, IN_SETTINGS, IN_U8, Settings, corners), IN(GILD, IN_SETTINGS, IN_U8, Settings, gild), IN(FIGURES, IN_SETTINGS, IN_U8, Settings, figures),
  IN(FLICK, IN_SETTINGS, IN_U8, Settings, flick), IN(CANDLE, IN_SETTINGS, IN_U8, Settings, candle), IN(FLICKS, IN_SETTINGS, IN_U8, Settings, flicks), IN(TIDE_TIMES, IN_SETTINGS, IN_U8, Settings, tide_times), IN(PLACE_LAT, IN_SETTINGS, IN_I32, Settings, lat_e4),
  IN(PLACE_LON, IN_SETTINGS, IN_I32, Settings, lon_e4), IN(PLACE_CITY, IN_SETTINGS, IN_TEXT, Settings, city),
  IN(PLACE_COUNTRY, IN_SETTINGS, IN_TEXT, Settings, country), IN(CALENDARS, IN_SETTINGS, IN_I32, Settings, calendars),
  IN(ANIMATIONS, IN_SETTINGS, IN_U8, Settings, animations),
  IN(LAT, IN_PLACE, IN_I32, Place, lat_e4), IN(LON, IN_PLACE, IN_I32, Place, lon_e4),
  IN(CITY, IN_PLACE, IN_TEXT, Place, city), IN(COUNTRY, IN_PLACE, IN_TEXT, Place, country),
  IN(WX_TEMP, IN_WEATHER, IN_I16, Stored, w.temp10), IN(WX_CODE, IN_WEATHER, IN_U8, Stored, w.code),
  IN(WX_LOW, IN_WEATHER, IN_U8, Stored, w.low), IN(WX_MID, IN_WEATHER, IN_U8, Stored, w.mid),
  IN(WX_HIGH, IN_WEATHER, IN_U8, Stored, w.high), IN(WX_WIND, IN_WEATHER, IN_U8, Stored, w.wind),
  IN(WX_FROM, IN_WEATHER, IN_I16, Stored, w.wind_from), IN(WX_PRESSURE, IN_WEATHER, IN_I16, Stored, w.pressure),
  IN(WX_SNOW, IN_WEATHER, IN_I16, Stored, w.snow_mm), IN(WX_VIS, IN_WEATHER, IN_I16, Stored, w.vis_dam),
};

static void inbox(DictionaryIterator *it, void *context) {
  uint8_t *rec[3] = {(uint8_t *)&s_settings, (uint8_t *)&s_place, (uint8_t *)&s_weather};
  bool got[3] = {false, false, false};
  for (Tuple *t = dict_read_first(it); t; t = dict_read_next(it)) {
    if (t->key == MESSAGE_KEY_TIDES && t->type == TUPLE_BYTE_ARRAY) {    /* the tide's turns, six bytes each */
      const uint8_t *b = t->value->data;
      memset(&s_tides, 0, sizeof s_tides);
      for (int k = 0; k < TIDE_TURNS && 6 * k + 6 <= t->length; k++, b += 6)
        s_tides.at[k] = b[0] | b[1] << 8 | b[2] << 16 | (uint32_t)b[3] << 24, s_tides.cm[k] = (int16_t)(b[4] | b[5] << 8),
        s_tides.n = (uint8_t)(k + 1);
      persist_write_data(KEY_TIDES, &s_tides, sizeof s_tides);
      continue;
    }
    for (unsigned i = 0; i < sizeof KEYS / sizeof KEYS[0]; i++) {
      if (t->key != *KEYS[i].key) continue;
      uint8_t *at = rec[KEYS[i].rec] + KEYS[i].off;
      int32_t v = t->type == TUPLE_CSTRING ? atoi(t->value->cstring) : t->value->int32;
      if (KEYS[i].type == IN_TEXT) {
        at[0] = 0;
        if (t->type == TUPLE_CSTRING) strncpy((char *)at, t->value->cstring, KEYS[i].size - 1), at[KEYS[i].size - 1] = 0;
      } else memcpy(at, &v, KEYS[i].type == IN_U8 ? 1 : KEYS[i].type == IN_I16 ? 2 : 4);   /* (little-endian) */
      got[KEYS[i].rec] = true;
      break;
    }
  }
  uint32_t now = (uint32_t)time(NULL);
  if (got[IN_SETTINGS]) persist_write_data(KEY_SETTINGS, &s_settings, sizeof s_settings);
  if (got[IN_PLACE]) s_place.time = now, persist_write_data(KEY_PLACE, &s_place, sizeof s_place);
  if (got[IN_WEATHER]) s_weather.time = now, persist_write_data(KEY_WEATHER, &s_weather, sizeof s_weather);
  redraw_soon();
}

/* ---- life cycle ---- */

/* Code from the app's resources (tools/build_blob.py): linked at address 0, then a list of the words in it that hold
 * absolute addresses, to which we add where it landed. PebbleOS lets an app run code in its own memory;
 * memory_cache_flush is the SDK's call for code it has loaded. Two blobs: the renderer, kept loaded, and the
 * calendars, loaded once a day to look up the day's feast. Returns the blob's entry table (its memory in *mem, to
 * free), or NULL. */
typedef struct { uint32_t magic, image, bss, nrel, api; } CodeHeader;
#define CODE_MAGIC 0x434E4C50u           /* "PLNC" */

static const void *load_blob(uint32_t resource, uint8_t **mem) {
  ResHandle h = handle_of(resource);
  CodeHeader hd;
  *mem = NULL;
  if (resource_load_byte_range(h, 0, (uint8_t *)&hd, sizeof hd) != sizeof hd || hd.magic != CODE_MAGIC) return NULL;
  uint32_t n = hd.image + hd.bss;
  *mem = malloc(n + 4);                          /* the heap gives 4-byte alignment; the code was linked for 8 */
  if (!*mem) return NULL;
  uint8_t *code = (uint8_t *)(((uintptr_t)*mem + 7) & ~(uintptr_t)7);
  if (resource_load_byte_range(h, sizeof hd, code, hd.image) != hd.image) goto fail;
  memset(code + hd.image, 0, hd.bss);
  uint16_t at[32];                               /* the relocations, a few at a time: the stack is small */
  for (uint32_t i = 0; i < hd.nrel; i += 32) {
    uint32_t k = hd.nrel - i < 32 ? hd.nrel - i : 32;
    if (resource_load_byte_range(h, sizeof hd + hd.image + 2 * i, (uint8_t *)at, 2 * k) != 2 * k) goto fail;
    for (uint32_t j = 0; j < k; j++) ((uint32_t *)code)[at[j]] += (uint32_t)(uintptr_t)code;
  }
  memory_cache_flush(code, n);
  return code + hd.api;
fail:
  free(*mem), *mem = NULL;
  return NULL;
}

static bool load_code(void) {
  s_api = load_blob(RESOURCE_ID_PLAN_CODE, &s_code);
  if (!s_api || s_api->magic != PLAN_API_MAGIC || s_api->layout != PLAN_LAYOUT) {
    free(s_code), s_code = NULL, s_api = NULL;
    return false;
  }
  g_code = (uint32_t)(uintptr_t)s_api;
  return true;
}

/* the face's data from the app's resources: the pieces, the stars, the type (shared) and this watch's ring */
static bool load_data(void) {
  if (!load_code()) return false;
  ResHandle d = resource_get_handle(RESOURCE_ID_PLAN_DATA), g = resource_get_handle(RESOURCE_ID_PLAN_GEOM);
  size_t nd = resource_size(d), ng = resource_size(g);
  /* (the screen's geometry last, against the free memory: the day's feast lookup borrows it, feast_of_day) */
  s_data = malloc(nd), s_plan = malloc(sizeof(Plan)), s_geom = malloc(ng);
  if (!s_data || !s_geom || !s_plan) {
    free(s_data), free(s_geom), free(s_plan), free(s_code);
    s_data = s_geom = s_code = NULL, s_plan = NULL, s_api = NULL;
    return false;
  }
  resource_load(d, s_data, nd);
  resource_load(g, s_geom, ng);
  s_api->init(s_plan, PBL_DISPLAY_WIDTH, PBL_DISPLAY_HEIGHT, s_data, s_geom);
  return true;
}

static void window_load(Window *window) {
  Layer *root = window_get_root_layer(window);
  s_layer = layer_create(layer_get_bounds(root));
  layer_set_update_proc(s_layer, update);
  layer_add_child(root, s_layer);
}

static void window_unload(Window *window) { layer_destroy(s_layer), s_layer = NULL; }

static void init(void) {
  stack_mark();
  defaults(&s_settings);
  Settings s;
  memset(&s, 0, sizeof s);
  int got = persist_read_data(KEY_SETTINGS, &s, sizeof s);
  if (got == (int)sizeof s && s.version == SETTINGS_VERSION) s_settings = s;
  else if (got >= (int)offsetof(Settings, gild) && s.version >= 7 && s.version < SETTINGS_VERSION) {
    s_settings = s;                              /* versions 7 to 9: the same record, shorter; what each lacked, unset
                                                  * (7's corners a switch, the theme's) */
    if (s.version == 7) s_settings.corners = s.corners ? (s.theme && s.theme < THEME_COUNT ? s.theme : THEME_LABOURS) : 0;
    if (s.version < 9) s_settings.gild = 0;
    if (s.version < 10) s_settings.figures = 0;
    if (s.version < 11) s_settings.flick = 0, s_settings.candle = 0;
    if (s.version < 12) s_settings.flicks = 2;
    s_settings.version = SETTINGS_VERSION;
  }
  else if (got == (int)sizeof(SettingsOld) || got == (int)offsetof(SettingsOld, animations)) {
    SettingsOld o;                               /* versions 2 to 6: the names into their larger room */
    memset(&o, 0, sizeof o);
    persist_read_data(KEY_SETTINGS, &o, sizeof o);
    int v = o.version;
    memcpy(&s_settings, &o, offsetof(SettingsOld, city));
    memcpy(s_settings.city, o.city, sizeof o.city), memcpy(s_settings.country, o.country, sizeof o.country);
    s_settings.animations = v == 2 ? ANIM_ALL : v == 3 ? (o.animations ? ANIM_MINUTE : 0) | ANIM_FIREWORKS | ANIM_EVENTS
                          : v == 4 ? o.animations | ANIM_EVENTS : o.animations;   /* (each version's new ones on) */
    s_settings.corners = v >= 6 && o.tools ? THEME_LABOURS : 0;
    s_settings.version = SETTINGS_VERSION;
  }
  got = persist_read_data(KEY_PLACE, &s_place, sizeof s_place);
  if (got == (int)sizeof(PlaceOld)) {            /* (to 0.1.6: the names' room smaller) */
    PlaceOld o;
    persist_read_data(KEY_PLACE, &o, sizeof o);
    memset(&s_place, 0, sizeof s_place);
    s_place.lat_e4 = o.lat_e4, s_place.lon_e4 = o.lon_e4, s_place.time = o.time;
    memcpy(s_place.city, o.city, sizeof o.city), memcpy(s_place.country, o.country, sizeof o.country);
  } else if (got != (int)sizeof s_place) memset(&s_place, 0, sizeof s_place);
  if (persist_read_data(KEY_WEATHER, &s_weather, sizeof s_weather) != (int)sizeof s_weather) memset(&s_weather, 0, sizeof s_weather);
  if (persist_read_data(KEY_TIDES, &s_tides, sizeof s_tides) != (int)sizeof s_tides) memset(&s_tides, 0, sizeof s_tides);
  app_message_register_inbox_received(inbox);
  app_message_open(INBOX, 64);                   /* before the face's data takes its memory */
  load_data();
  g_heap_free = heap_bytes_free();
  APP_LOG(APP_LOG_LEVEL_INFO, "heap free %u", (unsigned)g_heap_free);
  s_window = window_create();
  window_set_background_color(s_window, GColorClear);   /* (the face as drawn stays under the display's frames) */
  window_set_window_handlers(s_window, (WindowHandlers){.load = window_load, .unload = window_unload});
  window_stack_push(s_window, false);
  tick_timer_service_subscribe(MINUTE_UNIT, tick);
  accel_tap_service_subscribe(tap);
  battery_state_service_subscribe(on_battery);
  app_timer_register(4000, ask_later, NULL);     /* once the phone's side has started */
  g_stack_init = stack_deepest();
}

static void deinit(void) {
  scribe_end(), show_end(), event_end(), anims_settle(false);
  tick_timer_service_unsubscribe();
  accel_tap_service_unsubscribe();
  battery_state_service_unsubscribe();
  window_destroy(s_window);
  free(s_plan), free(s_data), free(s_geom), free(s_code);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}
