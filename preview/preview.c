/* The settings page's live preview: the watch's own drawing (watchface/src/c), built to WebAssembly by
 * preview/build.sh. The page sets what the face shows, asks for a moment, and gets the screen back as Pebble
 * colours (GColor8 bytes, 0b11rrggbb), a row of the screen's width at a time. */
#include <emscripten.h>
#include <stdlib.h>
#include <string.h>
#include "plan.h"
#include "plan_blobs.h"

static Plan P;
static Face F;
static Weather WX;
static bool round_screen;
static int W = 200, H = 228;
static uint8_t fb[MAX_W * MAX_H];
static int16_t row_x0[MAX_H], row_x1[MAX_H];
static char city[32], country[32];

static uint8_t *pv_row(void *ctx, int y, int *x0, int *x1) {
  (void)ctx;
  *x0 = row_x0[y], *x1 = row_x1[y];
  return fb + y * W;
}

/* The screen: the Time 2 (200 x 228) or the Round 2 (260 x 260, its rows cut to the circle). */
EMSCRIPTEN_KEEPALIVE void pv_screen(int round) {
  round_screen = round != 0;
  W = round_screen ? 260 : 200, H = round_screen ? 260 : 228;
  for (int y = 0; y < H; y++) {
    int a = 0, b = W - 1;
    if (round_screen) {
      a = W, b = -1;
      for (int x = 0; x < W; x++) {
        double dx = x + 0.5 - W / 2.0, dy = y + 0.5 - H / 2.0;
        if (dx * dx + dy * dy <= (W / 2.0) * (W / 2.0)) { if (x < a) a = x; b = x; }
      }
    }
    row_x0[y] = (int16_t)a, row_x1[y] = (int16_t)b;
  }
  memset(fb, 0, sizeof fb);
  plan_init(&P, W, H, BLOB_PLAN, round_screen ? BLOB_GABBRO : BLOB_EMERY);
}

EMSCRIPTEN_KEEPALIVE int pv_width(void) { return W; }
EMSCRIPTEN_KEEPALIVE int pv_height(void) { return H; }
EMSCRIPTEN_KEEPALIVE int pv_row_x0(int y) { return row_x0[y]; }
EMSCRIPTEN_KEEPALIVE int pv_row_x1(int y) { return row_x1[y]; }
EMSCRIPTEN_KEEPALIVE int pv_plates(void) { return PLATE_COUNT; }

/* What the face shows: the plate, the clock, names in the sky, the temperature's scale, the place, the labours. */
EMSCRIPTEN_KEEPALIVE void pv_face(int plate, int clock24, int names, int fahrenheit, float lat, float lon, int coords,
                                  int labours) {
  F.plate = (uint8_t)(plate >= 0 && plate < PLATE_COUNT ? plate : 0);
  F.clock24 = clock24 != 0, F.names = names != 0, F.fahrenheit = fahrenheit != 0, F.labours = labours != 0;
  F.lat = lat, F.lon = lon, F.coords = coords != 0;
  F.city = city, F.country = country;
}
/* the place's names for the ring: buffers the page writes into (UTF-8, at most 31 bytes) */
EMSCRIPTEN_KEEPALIVE char *pv_city(void) { return city; }
EMSCRIPTEN_KEEPALIVE char *pv_country(void) { return country; }

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
  if (!plan_render(&P, &F, (int64_t)utc, offset * 60, &(Target){pv_row, NULL}, malloc, free)) return NULL;
  return fb;
}
