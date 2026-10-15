/* The face on the desktop, from the watch's own C: renders to a PPM for comparing with the prototype
 * (tools/parity.py) and for looking at.
 *
 *   build/host emery|gabbro PLATE UNIX_SECONDS LAT LON OFFSET_MINUTES OUT.ppm [options]
 *     --24              the 24-hour clock
 *     --no-names        no names in the sky
 *     --city NAME --country NAME
 *     --weather T10,CODE,LOW,MID,HIGH,WIND,FROM,PRESSURE,SNOW_MM,VIS_DAM
 *     --fahrenheit
 *     --time N          render N times and print the mean milliseconds
 *     --labours         the labours of the months
 *     --no-coords       no latitude and longitude on the ring
 *     --calendars MASK  the calendars whose days it keeps (bit n for CAL_* n), as a number
 *     --mem             print the most memory the drawing held at once (as the watch's heap counts it: each block
 *                       rounded to 4 bytes, with its 4-byte header), and its blocks
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "plan.h"
#include "plan_blobs.h"

static uint8_t fb[MAX_W * MAX_H];
static int16_t rx0[MAX_H], rx1[MAX_H];
static int W, H;

/* the drawing's memory, counted as PebbleOS's heap counts it (lib/util/heap.c: 4-byte units, a 4-byte header) */
static size_t mem_now, mem_peak, mem_blocks, mem_peak_blocks;
static void *counted(size_t n) {
  size_t *b = malloc(n + sizeof(size_t));
  if (!b) return NULL;
  *b = ((n + 3) & ~(size_t)3) + 4;
  if (getenv("PLAN_MEM_LOG")) fprintf(stderr, "alloc %zu\n", n);
  mem_now += *b, mem_blocks++;
  if (mem_now > mem_peak) mem_peak = mem_now, mem_peak_blocks = mem_blocks;
  return b + 1;
}
static void uncounted(void *p) {
  if (!p) return;
  size_t *b = (size_t *)p - 1;
  mem_now -= *b, mem_blocks--;
  free(b);
}

static uint8_t *row(void *ctx, int y, int *x0, int *x1) {
  (void)ctx;
  *x0 = rx0[y], *x1 = rx1[y];
  return fb + y * W;
}

int main(int argc, char **argv) {
  if (argc < 8) {
    fprintf(stderr, "usage: host emery|gabbro PLATE UNIX LAT LON OFFSET_MIN OUT.ppm [--24] [--no-names] ...\n");
    return 2;
  }
  bool round = strcmp(argv[1], "gabbro") == 0;
  W = round ? 260 : 200, H = round ? 260 : 228;
  Face f = {0};
  f.plate = (uint8_t)atoi(argv[2]);
  int64_t utc = atoll(argv[3]);
  f.lat = (float)atof(argv[4]), f.lon = (float)atof(argv[5]);
  int32_t offset = atoi(argv[6]) * 60;
  const char *out = argv[7];
  f.names = true, f.coords = true;
  Weather wx;
  int repeat = 1;
  bool mem = false;
  for (int i = 8; i < argc; i++) {
    if (!strcmp(argv[i], "--24")) f.clock24 = true;
    else if (!strcmp(argv[i], "--no-names")) f.names = false;
    else if (!strcmp(argv[i], "--no-coords")) f.coords = false;
    else if (!strcmp(argv[i], "--labours")) f.labours = true;
    else if (!strcmp(argv[i], "--fahrenheit")) f.fahrenheit = true;
    else if (!strcmp(argv[i], "--city") && i + 1 < argc) f.city = argv[++i];
    else if (!strcmp(argv[i], "--country") && i + 1 < argc) f.country = argv[++i];
    else if (!strcmp(argv[i], "--time") && i + 1 < argc) repeat = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--mem")) mem = true;
    else if (!strcmp(argv[i], "--calendars") && i + 1 < argc) f.calendars = (uint32_t)strtoul(argv[++i], NULL, 0);
    else if (!strcmp(argv[i], "--weather") && i + 1 < argc) {
      int v[10] = {0};
      sscanf(argv[++i], "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d", &v[0], &v[1], &v[2], &v[3], &v[4], &v[5], &v[6], &v[7], &v[8], &v[9]);
      wx = (Weather){(int16_t)v[0], (uint8_t)v[1], (uint8_t)v[2], (uint8_t)v[3], (uint8_t)v[4], (uint8_t)v[5],
                     (uint16_t)v[6], (uint16_t)v[7], (uint16_t)v[8], (uint16_t)v[9]};
      f.weather = &wx;
    }
  }
  for (int y = 0; y < H; y++) {
    rx0[y] = 0, rx1[y] = (int16_t)(W - 1);
    if (!round) continue;
    /* the round screen: the pixels its display lights (proto/screen.py) */
    int a = ROUND2_TOPLEFT[y < 130 ? y : 259 - y];
    rx0[y] = (int16_t)a, rx1[y] = (int16_t)(259 - a);
  }
  static Plan p;
  plan_init(&p, W, H, BLOB_PLAN, round ? BLOB_GABBRO : BLOB_EMERY);
  Target t = {row, NULL};
  struct timespec t0, t1;
  clock_gettime(CLOCK_MONOTONIC, &t0);
  FeastReader rd;
  plan_feast_memory(&rd, BLOB_FEASTS);
  plan_feast(&p, &f, utc, offset, &rd);
  for (int i = 0; i < repeat; i++)
    if (!plan_render(&p, &f, utc, offset, &t, counted, uncounted)) { fprintf(stderr, "render failed\n"); return 1; }
  if (mem) printf("peak %zu bytes in %zu blocks\n", mem_peak, mem_peak_blocks);
  clock_gettime(CLOCK_MONOTONIC, &t1);
  if (repeat > 1)
    printf("%.2f ms a render\n", ((t1.tv_sec - t0.tv_sec) * 1e3 + (t1.tv_nsec - t0.tv_nsec) / 1e6) / repeat);
  FILE *o = fopen(out, "wb");
  if (!o) { perror(out); return 1; }
  fprintf(o, "P6\n%d %d\n255\n", W, H);
  for (int i = 0; i < W * H; i++) {
    uint8_t c = fb[i], px[3] = {(uint8_t)(((c >> 4) & 3) * 85), (uint8_t)(((c >> 2) & 3) * 85), (uint8_t)((c & 3) * 85)};
    fwrite(px, 1, 3, o);
  }
  fclose(o);
  return 0;
}
