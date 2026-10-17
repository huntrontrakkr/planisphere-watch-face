/* The settings page's live preview: the watch's own drawing (watchface/src/c), built to WebAssembly by
 * preview/build.sh. The page sets what the face shows, asks for a moment, and gets the screen back as Pebble
 * colours (GColor8 bytes, 0b11rrggbb), a row of the screen's width at a time. */
#include <emscripten.h>
#include <stdlib.h>
#include <string.h>
#include "plan.h"
#include "plan_blobs.h"
#include "plan_data.h"

static Plan P;
static Face F;
static Weather WX;
static bool round_screen;
static int W = 200, H = 228;
static uint8_t fb[MAX_W * MAX_H];
static int16_t row_x0[MAX_H], row_x1[MAX_H];
static char city[48], country[48];

static uint8_t *pv_row(void *ctx, int y, int *x0, int *x1) {
  (void)ctx;
  *x0 = row_x0[y], *x1 = row_x1[y];
  return fb + y * W;
}

/* The screen: the Time 2 (200 x 228) or the Round 2 (260 x 260, its rows cut to what its display lights). */
EMSCRIPTEN_KEEPALIVE void pv_screen(int round) {
  round_screen = round != 0;
  W = round_screen ? 260 : 200, H = round_screen ? 260 : 228;
  for (int y = 0; y < H; y++) {
    int a = round_screen ? ROUND2_TOPLEFT[y < 130 ? y : 259 - y] : 0;
    row_x0[y] = (int16_t)a, row_x1[y] = (int16_t)(W - 1 - a);
  }
  memset(fb, 0, sizeof fb);
  plan_init(&P, W, H, BLOB_PLAN, round_screen ? BLOB_GABBRO : BLOB_EMERY);
}

EMSCRIPTEN_KEEPALIVE int pv_width(void) { return W; }
EMSCRIPTEN_KEEPALIVE int pv_height(void) { return H; }
EMSCRIPTEN_KEEPALIVE int pv_row_x0(int y) { return row_x0[y]; }
EMSCRIPTEN_KEEPALIVE int pv_row_x1(int y) { return row_x1[y]; }
EMSCRIPTEN_KEEPALIVE int pv_plates(void) { return PLATE_COUNT; }
/* whether a plate's figures are drawn in at dusk (not on a printed chart's, always there, nor under a rete) */
EMSCRIPTEN_KEEPALIVE int pv_draws_in(int plate) { return PLATES[plate].window != WIN_PAPER && !PLATES[plate].rete; }

/* the scene blobs, linked in: the labours and the corner tools (tools.bin from memory), the woodcuts (scenes.bin) */
/* a table in memory, read as the watch reads its resources (zeros past its end) */
typedef struct { const uint8_t *at; uint32_t size; } Mem;
static void mem_read(void *ctx, uint32_t at, void *buf, uint32_t n) {
  const Mem *m = ctx;
  for (uint32_t i = 0; i < n; i++) ((uint8_t *)buf)[i] = at + i < m->size ? m->at[at + i] : 0;
}
static bool pv_call(void *ctx, bool labours, const DecorCtx *dc) {
  (void)ctx;
  static Mem tools_mem = {BLOB_TOOLS, sizeof BLOB_TOOLS}, scenes_mem = {BLOB_SCENES, sizeof BLOB_SCENES};
  FeastReader rd = {mem_read, &tools_mem}, scenes = {mem_read, &scenes_mem};
  return (labours ? plan_labours : plan_decor)(dc, &rd, &scenes);
}
static bool pv_decor(void *ctx, const DecorCtx *dc) { return decor_run(ctx, dc, pv_call); }
/* What the face shows: the plate, the clock, names in the sky, the temperature's scale, the place, the labours, the
 * minute written, the village's life (of the events, EV_VILLAGE alone: the passing ones are left to the watch) and
 * whose pieces are in the Time 2's corners (THEME_*, 0 the sprigs), and whether the time is gilt. */
EMSCRIPTEN_KEEPALIVE void pv_face(int plate, int clock24, int names, int fahrenheit, float lat, float lon, int coords,
                                  int labours, int calendars, int scribe, int events, int corners, int gild) {
  F.plate = (uint8_t)(plate >= 0 && plate < PLATE_COUNT ? plate : 0);
  F.clock24 = clock24 != 0, F.names = names != 0, F.fahrenheit = fahrenheit != 0, F.theme = (uint8_t)(labours >= 0 && labours < THEME_COUNT ? labours : 0);
  F.calendars = (uint32_t)calendars, F.scribe = scribe != 0, F.events = (uint8_t)(events & EV_VILLAGE);
  F.corners = (uint8_t)(corners > 0 && corners < THEME_COUNT ? corners : 0), F.decor = pv_decor, F.gild = gild != 0;
  F.lat = lat, F.lon = lon, F.coords = coords != 0;
  F.city = city, F.country = country;
}
/* the place's names for the ring: buffers the page writes into (UTF-8, at most 47 bytes; each a ladder of shorter
 * forms, "|" between) */
EMSCRIPTEN_KEEPALIVE char *pv_city(void) { return city; }
EMSCRIPTEN_KEEPALIVE char *pv_country(void) { return country; }

/* The tide's turns (as the phone sends them: six bytes each, tides.js), one at a time from the first, and whether the
 * face sets the next high and low water (Face.tide_times). */
static Tides TD;
EMSCRIPTEN_KEEPALIVE void pv_tide(int k, double minutes_high, int cm, int on) {
  if (k <= 0) memset(&TD, 0, sizeof TD);         /* (k < 0: none, only the switch) */
  if (k >= 0 && k < TIDE_TURNS) TD.at[k] = (uint32_t)minutes_high, TD.cm[k] = (int16_t)cm, TD.n = (uint8_t)(k + 1);
  F.tides = TD.n ? &TD : NULL, F.tide_times = on != 0;
}

/* The weather (as the phone sends it), or none with code < 0. */
EMSCRIPTEN_KEEPALIVE void pv_weather(int code, int temp10, int low, int mid, int high, int wind, int from, int pressure,
                                     int snow_mm, int vis_dam) {
  if (code < 0) { F.weather = NULL; return; }
  WX = (Weather){(int16_t)temp10, (uint8_t)code, (uint8_t)low, (uint8_t)mid, (uint8_t)high, (uint8_t)wind,
                 (uint16_t)from, (uint16_t)pressure, (uint16_t)snow_mm, (uint16_t)vis_dam};
  F.weather = &WX;
}

/* The face at `utc` (seconds since 1970), the local clock `offset` minutes ahead: the screen, W x H bytes. */
EMSCRIPTEN_KEEPALIVE uint8_t *pv_render(double utc, int offset) {
  FeastReader rd;
  plan_feast_memory(&rd, BLOB_FEASTS);
  plan_feast(&P, &F, (int64_t)utc, offset * 60, &rd);
  if (!plan_render(&P, &F, (int64_t)utc, offset * 60, &(Target){pv_row, NULL}, malloc, free)) return NULL;
  return fb;
}

/* The first feast of the calendars `mask` on or after a local date (days since 1970), within `days`: its date (days
 * since 1970), or -1; its words then in pv_feast_words. `offset` the clock's minutes ahead of UTC. */
static char feast_words[24];
EMSCRIPTEN_KEEPALIVE int pv_next_feast(int mask, int from, int days, int offset) {
  for (int d = from; d < from + days; d++) {
    FeastReader rd;
    plan_feast_memory(&rd, BLOB_FEASTS);
    int i = plan_feast_on(&rd, d + 719163, (uint32_t)mask, offset / 60.0f);
    if (i < 0) continue;
    const FeastRecord *r = (const FeastRecord *)(const void *)(BLOB_FEASTS + 8) + i;
    const char *w = (const char *)BLOB_FEASTS + (BLOB_FEASTS[2] | BLOB_FEASTS[3] << 8) + r->words[0];
    strncpy(feast_words, w, sizeof feast_words - 1);
    return d;
  }
  return -1;
}
EMSCRIPTEN_KEEPALIVE char *pv_feast_words(void) { return feast_words; }

/* The fireworks display due at the top of the hour last drawn (pv_render), if there is one: its frames (0: none), at
 * SHOW_FPS. Then each frame over the face as last drawn (pv_show_frame), the screen back each time; frame `frames`
 * puts the face back as it was. */
static struct { ShowUndo u; uint32_t px[SHOW_UNDO]; } undo = {{0, SHOW_UNDO}, {0}};
EMSCRIPTEN_KEEPALIVE int pv_show_frames(void) {
  undo.u.n = 0;
  return P.show_hour >= 0 ? P.show_end : 0;
}
EMSCRIPTEN_KEEPALIVE uint8_t *pv_show_frame(int frame) {
  plan_show(&P, &(Target){pv_row, NULL}, frame, &undo.u);
  return fb;
}

/* The animations when asked (the page's "Play"): the face with the figures drawn in so far (k of EVENT_FIGS_FRAMES,
 * 0 all), or the sky turned on (degrees, as a flick spins it); a passing event planned (EV_METEOR, EV_BIRDS: its
 * frames, then each over the face as drawn, pv_event_frame), or a display at the hour (pv_show_frames after
 * pv_render_show); and the Sun's altitude at a moment, to choose an hour that suits them. */
extern int pv_force_show, pv_force_event;
/* the battery's candle (Face.candle), at the charge given (percent) */
EMSCRIPTEN_KEEPALIVE void pv_candle(int on, int pct) { F.candle = on != 0, F.battery = (uint8_t)pct, F.charging = false; }
EMSCRIPTEN_KEEPALIVE uint8_t *pv_render_figs(double utc, int offset, int k) {
  F.figs_part = (uint8_t)k;
  uint8_t *out = pv_render(utc, offset);
  F.figs_part = 0;
  return out;
}
EMSCRIPTEN_KEEPALIVE uint8_t *pv_render_turn(double utc, int offset, float degrees) {
  F.turn = degrees;
  uint8_t *out = pv_render(utc, offset);
  F.turn = 0;
  return out;
}
EMSCRIPTEN_KEEPALIVE uint8_t *pv_render_show(double utc, int offset) {
  pv_force_show = 1;
  uint8_t *out = pv_render(utc, offset);
  pv_force_show = 0;
  return out;
}
EMSCRIPTEN_KEEPALIVE int pv_event(double utc, int offset, int kind) {
  pv_force_event = kind, P.event = 0;
  uint8_t *out = pv_render(utc, offset);
  pv_force_event = 0, undo.u.n = 0;
  return out && P.event ? P.event_frames : 0;
}
EMSCRIPTEN_KEEPALIVE uint8_t *pv_event_frame(int frame) {
  plan_event(&P, &(Target){pv_row, NULL}, frame, &undo.u);
  return fb;
}
EMSCRIPTEN_KEEPALIVE float pv_sun(double utc) {
  Sky sky;
  plan_sky(&sky, (int64_t)utc, (float)F.lon);
  return plan_altitude(sky.sun_ra, sky.sun_dec, sky.lst, (float)F.lat);
}

/* The minute written, when the face last drawn has new figures kept (pv_face's scribe): its frames (0: none); then each
 * over the face as drawn (pv_scribe_frame), frame 0 taking the new figures away. */
EMSCRIPTEN_KEEPALIVE int pv_scribe_frames(void) { return P.scribe ? SCRIBE_FRAMES : 0; }
EMSCRIPTEN_KEEPALIVE uint8_t *pv_scribe_frame(int frame) {
  uint32_t *room = frame == 0 && P.scribe ? malloc(P.scribe_n * sizeof *room) : NULL;
  plan_scribe(&P, &(Target){pv_row, NULL}, frame, room);
  free(room);
  return fb;
}

