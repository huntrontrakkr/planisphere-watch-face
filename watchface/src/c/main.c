/* Planisphere: the sky over where you are, turning with the hours under the card's oval window, the Sun riding
 * the ring as the hour hand. The face is drawn by plan_render.c, the same C the settings page's preview runs.
 *
 * The phone sends where it is (and the weather there, from Open-Meteo) and the owner's settings; the watch keeps
 * them, and draws the face every minute.
 */
#include <pebble.h>
#include "plan.h"

/* Nothing here is in a hot loop: built for size (the app's code and data must stay under 64 KB). */
#pragma GCC optimize("Os")

#define SETTINGS_VERSION 1
#define KEY_SETTINGS 1
#define KEY_PLACE 2
#define KEY_WEATHER 3
#define INBOX 1024                       /* bytes: the whole settings message, with room to grow */
#define WEATHER_FRESH (3 * 3600)         /* s: the weather is shown this long after it came */
#define ASK_EVERY (30 * 60)              /* and the phone asked for it again after this */
#define ASK_RETRY (10 * 60)              /* asking at most this often */

typedef struct {
  uint8_t version, plate, clock, names, weather, units, place, labours;
  int32_t lat_e4, lon_e4;               /* the place given on the settings page (PLACE 1) */
  char city[24], country[20];
} Settings;

typedef struct {                        /* where the phone last was */
  int32_t lat_e4, lon_e4;
  char city[24], country[20];
  uint32_t time;                        /* 0: never */
} Place;

typedef struct { Weather w; uint32_t time; } Stored;

/* diagnostics, readable over GDB in the emulator */
volatile uint32_t g_render_ms = 0, g_render_max = 0, g_heap_free = 0, g_heap_low = 0;

static Window *s_window;
static Layer *s_layer;
static Plan *s_plan;
static uint8_t *s_data, *s_geom;
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

static void face_of(Face *f) {
  memset(f, 0, sizeof *f);
  f->plate = s_settings.plate < PLATE_COUNT ? s_settings.plate : 0;
  f->clock24 = s_settings.clock == 0 ? clock_is_24h_style() : s_settings.clock == 2;
  f->names = s_settings.names;
  f->fahrenheit = s_settings.units == 2;
  if (s_settings.place == 1) {
    f->lat = (float)s_settings.lat_e4 * 1e-4f, f->lon = (float)s_settings.lon_e4 * 1e-4f;
    f->city = s_settings.city, f->country = s_settings.country, f->coords = true;
  } else if (s_place.time) {
    f->lat = (float)s_place.lat_e4 * 1e-4f, f->lon = (float)s_place.lon_e4 * 1e-4f;
    f->city = s_place.city, f->country = s_place.country, f->coords = true;
  } else {
    /* not yet told where it is: a northern sky, at the longitude the time zone suggests */
    f->lat = 40.0f, f->lon = (float)(utc_offset(time(NULL)) / 240);
  }
  uint32_t now = (uint32_t)time(NULL);
  if (s_settings.weather && s_weather.time && now - s_weather.time < WEATHER_FRESH) f->weather = &s_weather.w;
}

static void update(Layer *layer, GContext *ctx) {
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
  plan_render(s_plan, &f, (int64_t)now, utc_offset(now), &tg, malloc, free);
  graphics_release_frame_buffer(ctx, fb);
  g_render_ms = now_ms() - t0;
  if (g_render_ms > g_render_max) g_render_max = g_render_ms;
}

static void tick(struct tm *t, TimeUnits changed) {
  if (s_layer) layer_mark_dirty(s_layer);
  if (t->tm_min % 10 == 0) ask_phone(false);
}

/* ---- messages from the phone ---- */

static int tuple_int(const Tuple *t) {
  return t->type == TUPLE_CSTRING ? atoi(t->value->cstring) : (int)t->value->int32;
}
static void tuple_text(const Tuple *t, char *out, size_t n) {
  if (t->type == TUPLE_CSTRING) strncpy(out, t->value->cstring, n - 1), out[n - 1] = 0;
  else out[0] = 0;
}

static void inbox(DictionaryIterator *it, void *context) {
  bool settings = false, place = false, weather = false;
  for (Tuple *t = dict_read_first(it); t; t = dict_read_next(it)) {
    uint32_t k = t->key;
    int v = tuple_int(t);
    if (k == MESSAGE_KEY_PLATE) s_settings.plate = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_CLOCK) s_settings.clock = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_NAMES) s_settings.names = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_WEATHER) s_settings.weather = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_UNITS) s_settings.units = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_PLACE) s_settings.place = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_LABOURS) s_settings.labours = (uint8_t)v, settings = true;
    else if (k == MESSAGE_KEY_PLACE_LAT) s_settings.lat_e4 = v, settings = true;
    else if (k == MESSAGE_KEY_PLACE_LON) s_settings.lon_e4 = v, settings = true;
    else if (k == MESSAGE_KEY_PLACE_CITY) tuple_text(t, s_settings.city, sizeof s_settings.city), settings = true;
    else if (k == MESSAGE_KEY_PLACE_COUNTRY) tuple_text(t, s_settings.country, sizeof s_settings.country), settings = true;
    else if (k == MESSAGE_KEY_LAT) s_place.lat_e4 = v, place = true;
    else if (k == MESSAGE_KEY_LON) s_place.lon_e4 = v, place = true;
    else if (k == MESSAGE_KEY_CITY) tuple_text(t, s_place.city, sizeof s_place.city), place = true;
    else if (k == MESSAGE_KEY_COUNTRY) tuple_text(t, s_place.country, sizeof s_place.country), place = true;
    else if (k == MESSAGE_KEY_WX_TEMP) s_weather.w.temp10 = (int16_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_CODE) s_weather.w.code = (uint8_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_LOW) s_weather.w.low = (uint8_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_MID) s_weather.w.mid = (uint8_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_HIGH) s_weather.w.high = (uint8_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_WIND) s_weather.w.wind = (uint8_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_FROM) s_weather.w.wind_from = (uint16_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_PRESSURE) s_weather.w.pressure = (uint16_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_SNOW) s_weather.w.snow_mm = (uint16_t)v, weather = true;
    else if (k == MESSAGE_KEY_WX_VIS) s_weather.w.vis_dam = (uint16_t)v, weather = true;
  }
  uint32_t now = (uint32_t)time(NULL);
  if (settings) persist_write_data(KEY_SETTINGS, &s_settings, sizeof s_settings);
  if (place) s_place.time = now, persist_write_data(KEY_PLACE, &s_place, sizeof s_place);
  if (weather) s_weather.time = now, persist_write_data(KEY_WEATHER, &s_weather, sizeof s_weather);
  if (s_layer) layer_mark_dirty(s_layer);
}

/* ---- life cycle ---- */

/* the face's data from the app's resources: the pieces, the stars, the type (shared) and this watch's ring */
static bool load_data(void) {
  ResHandle d = resource_get_handle(RESOURCE_ID_PLAN_DATA), g = resource_get_handle(RESOURCE_ID_PLAN_GEOM);
  size_t nd = resource_size(d), ng = resource_size(g);
  s_data = malloc(nd), s_geom = malloc(ng), s_plan = malloc(sizeof(Plan));
  if (!s_data || !s_geom || !s_plan) {
    free(s_data), free(s_geom), free(s_plan);
    s_data = s_geom = NULL, s_plan = NULL;
    return false;
  }
  resource_load(d, s_data, nd);
  resource_load(g, s_geom, ng);
  plan_init(s_plan, PBL_DISPLAY_WIDTH, PBL_DISPLAY_HEIGHT, s_data, s_geom);
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
  window_set_window_handlers(s_window, (WindowHandlers){.load = window_load, .unload = window_unload});
  window_stack_push(s_window, false);
  tick_timer_service_subscribe(MINUTE_UNIT, tick);
  app_timer_register(4000, ask_later, NULL);     /* once the phone's side has started */
}

static void deinit(void) {
  tick_timer_service_unsubscribe();
  window_destroy(s_window);
  free(s_plan), free(s_data), free(s_geom);
}

int main(void) {
  init();
  app_event_loop();
  deinit();
}
