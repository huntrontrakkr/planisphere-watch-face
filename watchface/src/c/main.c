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

#define SETTINGS_VERSION 2
#define KEY_SETTINGS 1
#define KEY_PLACE 2
#define KEY_WEATHER 3
#define INBOX 320                        /* bytes: the whole settings message (about 150), with room to grow */
#define WEATHER_FRESH (3 * 3600)         /* s: the weather is shown this long after it came */
#define ASK_EVERY (30 * 60)              /* and the phone asked for it again after this */
#define ASK_RETRY (10 * 60)              /* asking at most this often */

typedef struct {
  uint8_t version, plate, clock, names, weather, units, place, labours;
  int32_t lat_e4, lon_e4;               /* the place given on the settings page (PLACE 1) */
  uint32_t calendars;                   /* the calendars whose days the face keeps (bit n for CAL_* n) */
  char city[24], country[20];
} Settings;

typedef struct {                        /* where the phone last was */
  int32_t lat_e4, lon_e4;
  char city[24], country[20];
  uint32_t time;                        /* 0: never */
} Place;

typedef struct { Weather w; uint32_t time; } Stored;

/* diagnostics, readable over GDB in the emulator (g_code: where the renderer's code was loaded; g_utc, g_offset:
 * the moment last drawn, for tools/host to draw again) */
volatile uint32_t g_render_ms = 0, g_render_max = 0, g_heap_free = 0, g_heap_low = 0, g_code = 0, g_utc = 0;
volatile int32_t g_offset = 0;
/* the stack's deepest (stack_deepest), ever and by the end of init; and how deep it is where the renderer is called */
volatile uint32_t g_stack = 0, g_stack_init = 0, g_stack_at = 0;
volatile uint32_t g_feast_heap = 0;      /* the heap free while the calendars' code and table are loaded */
/* the fireworks displays: frames drawn, the slowest frame (ms), the heap free while one plays */
volatile uint32_t g_show_frames = 0, g_show_ms = 0, g_show_heap = 0, g_show_end = 0;   /* (1 played out, 2 gave way) */
volatile uint32_t g_show_px = 0;         /* the most pixels a frame covered */

static Window *s_window;
static Layer *s_layer;
static Plan *s_plan;
static const PlanApi *s_api;
static uint8_t *s_code, *s_data, *s_geom;
static Settings s_settings;
static Place s_place;
static Stored s_weather;
static uint32_t s_asked;

static void defaults(Settings *s) {
  memset(s, 0, sizeof *s);
  s->version = SETTINGS_VERSION;
  s->plate = PLATE_PLANISPHERE, s->names = 1, s->weather = 1;
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
static void ask_phone(bool force) {
  uint32_t now = (uint32_t)time(NULL);
  if (!connection_service_peek_pebble_app_connection()) return;
  if (!force && s_weather.time && now - s_weather.time < ASK_EVERY && s_place.time) return;
  if (!force && s_asked && now - s_asked < ASK_RETRY) return;
  DictionaryIterator *out;
  if (app_message_outbox_begin(&out) != APP_MSG_OK) return;
  dict_write_uint8(out, MESSAGE_KEY_REQUEST, 1);
  if (app_message_outbox_send() == APP_MSG_OK) s_asked = now;
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

static int32_t s_where[2];              /* the face's place as face_of sets it, 1e-4 degrees (latitude, longitude) */
static void face_of(Face *f) {
  memset(f, 0, sizeof *f);
  f->plate = s_settings.plate < PLATE_COUNT ? s_settings.plate : 0;
  f->clock24 = s_settings.clock == 0 ? clock_is_24h_style() : s_settings.clock == 2;
  f->names = s_settings.names, f->labours = s_settings.labours, f->calendars = s_settings.calendars;
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
  uint32_t now = (uint32_t)time(NULL);
  if (s_settings.weather && s_weather.time && now - s_weather.time < WEATHER_FRESH) f->weather = &s_weather.w;
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
  uint8_t *mem;
  const FeastApi *api = load_blob(RESOURCE_ID_PLAN_FEAST_CODE, &mem);
  if (api && api->magic == FEAST_API_MAGIC && api->layout == PLAN_LAYOUT) {
    ResHandle h = resource_get_handle(RESOURCE_ID_PLAN_FEASTS);
    FeastReader rd = {resource_read, &h};
    g_feast_heap = heap_bytes_free();
    if (api->feast(s_plan, f, (int64_t)now, offset, &rd)) s_looked[0] = s_where[0], s_looked[1] = s_where[1];
  }
  free(mem);
}

/* the renderer's memory, and how little was left */
static void *alloc(size_t n) {
  void *p = malloc(n);
  if (heap_bytes_free() < g_heap_low) g_heap_low = heap_bytes_free();
  return p;
}

/* ---- the fireworks display: at the top of an hour that brings one (Plan.show_hour, worked out by the renderer as it
 * drew the hour's first face), its code is loaded and plays SHOW_FPS frames a second over the face as drawn, each
 * putting back what the last covered. A drawing asked for meanwhile (the weather, the settings) waits for its end.
 * One the system asks for (as the app opens, say) is made at once, as the face and the display have no room for
 * both: the display gives way to it and then takes up its time again. ---- */
static const ShowApi *s_show;
static uint8_t *s_show_mem;
static ShowUndo *s_undo;
static AppTimer *s_show_timer;
static int32_t s_show_played = -1;      /* the hour whose display has begun, */
static bool s_show_done;                /* and played out */
static int s_show_frame = -1;           /* the frame the next drawing is for (-1: a whole face) */
static int s_show_last = -1;            /* the frame last drawn (a frame a tick of the timer: the clock may jump) */
static bool s_redraw_after;

static void redraw(void) {
  if (s_show) s_redraw_after = true;
  else if (s_layer) layer_mark_dirty(s_layer);
}

static void show_end(bool redraw_now) {
  if (s_show_timer) app_timer_cancel(s_show_timer);
  free(s_undo), free(s_show_mem);
  s_show_timer = NULL, s_undo = NULL, s_show_mem = NULL, s_show = NULL, s_show_frame = -1;
  if (s_redraw_after && redraw_now && s_layer) layer_mark_dirty(s_layer);
  s_redraw_after = false;
}

static void show_tick(void *data) {
  s_show_timer = NULL;
  s_show_frame = s_show_last + 1;
  if (s_layer) layer_mark_dirty(s_layer);
}

static void show_begin(void) {
  if (s_show || s_plan->show_hour < 0) return;
  if (s_plan->show_hour != s_show_played) s_show_played = s_plan->show_hour, s_show_last = -1, s_show_done = false;
  else if (s_show_done) return;                  /* (else it gave way, and goes on from its last frame) */
  s_show = load_blob(RESOURCE_ID_PLAN_SHOW_CODE, &s_show_mem);
  s_undo = malloc(sizeof(ShowUndo) + SHOW_UNDO * sizeof(uint32_t));
  if (!s_show || s_show->magic != SHOW_API_MAGIC || s_show->layout != PLAN_LAYOUT || !s_undo) {
    show_end(false);
    return;
  }
  s_undo->n = 0, s_undo->cap = SHOW_UNDO;
  g_show_heap = heap_bytes_free();
  s_show_timer = app_timer_register(1, show_tick, NULL);
}

static void show_frame(GContext *ctx) {
  uint32_t t0 = now_ms();
  GBitmap *fb = graphics_capture_frame_buffer(ctx);
  if (!fb) {                                     /* (no screen to draw on: the display ends, the face is drawn again) */
    s_show_done = true, s_redraw_after = true;
    show_end(true);
    return;
  }
  Target tg = {fb_row, fb};
  bool more = s_show->frame(s_plan, &tg, s_show_frame, s_undo);
  graphics_release_frame_buffer(ctx, fb);
  g_show_frames++, s_show_last = s_show_frame;
  if (s_undo->n > g_show_px) g_show_px = s_undo->n;
  if (now_ms() - t0 > g_show_ms) g_show_ms = now_ms() - t0;
  if (!more) {
    g_show_end = 1, s_show_done = true;
    show_end(true);
    return;
  }
  s_show_frame = -1;
  s_show_timer = app_timer_register(1000 / SHOW_FPS, show_tick, NULL);
}

static void update(Layer *layer, GContext *ctx) {
  if (s_show && s_show_frame >= 0) {
    show_frame(ctx);
    return;
  }
  if (s_show) g_show_end = 2, show_end(false);   /* the system asks for the whole face: the display gives way */
  time_t now = time(NULL);
  if (!s_plan) {                                 /* no memory for the face's data: the time alone */
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
  Target tg = {fb_row, fb};
  if (heap_bytes_free() < g_heap_low || !g_heap_low) g_heap_low = heap_bytes_free();
  g_utc = (uint32_t)now, g_offset = utc_offset(now);
  g_stack_at = (uint32_t)((uintptr_t)__pbl_app_info - (uintptr_t)&tg);
  feast_of_day(&f, now, g_offset);
  bool drawn = s_api->render(s_plan, &f, (int64_t)now, g_offset, &tg, alloc, free);
  graphics_release_frame_buffer(ctx, fb);
  g_render_ms = now_ms() - t0;
  if (g_render_ms > g_render_max) g_render_max = g_render_ms;
  g_stack = stack_deepest();
  if (drawn) show_begin();
}

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
  IN(LABOURS, IN_SETTINGS, IN_U8, Settings, labours), IN(PLACE_LAT, IN_SETTINGS, IN_I32, Settings, lat_e4),
  IN(PLACE_LON, IN_SETTINGS, IN_I32, Settings, lon_e4), IN(PLACE_CITY, IN_SETTINGS, IN_TEXT, Settings, city),
  IN(PLACE_COUNTRY, IN_SETTINGS, IN_TEXT, Settings, country), IN(CALENDARS, IN_SETTINGS, IN_I32, Settings, calendars),
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
  for (Tuple *t = dict_read_first(it); t; t = dict_read_next(it))
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
  uint32_t now = (uint32_t)time(NULL);
  if (got[IN_SETTINGS]) persist_write_data(KEY_SETTINGS, &s_settings, sizeof s_settings);
  if (got[IN_PLACE]) s_place.time = now, persist_write_data(KEY_PLACE, &s_place, sizeof s_place);
  if (got[IN_WEATHER]) s_weather.time = now, persist_write_data(KEY_WEATHER, &s_weather, sizeof s_weather);
  redraw();
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
  ResHandle h = resource_get_handle(resource);
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
  s_data = malloc(nd), s_geom = malloc(ng), s_plan = malloc(sizeof(Plan));
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
  if (persist_read_data(KEY_SETTINGS, &s, sizeof s) == (int)sizeof s && s.version == SETTINGS_VERSION) s_settings = s;
  if (persist_read_data(KEY_PLACE, &s_place, sizeof s_place) != (int)sizeof s_place) memset(&s_place, 0, sizeof s_place);
  if (persist_read_data(KEY_WEATHER, &s_weather, sizeof s_weather) != (int)sizeof s_weather) memset(&s_weather, 0, sizeof s_weather);
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
  app_timer_register(4000, ask_later, NULL);     /* once the phone's side has started */
  g_stack_init = stack_deepest();
}

static void deinit(void) {
  show_end(false);
  tick_timer_service_unsubscribe();
  window_destroy(s_window);
  free(s_plan), free(s_data), free(s_geom), free(s_code);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}
