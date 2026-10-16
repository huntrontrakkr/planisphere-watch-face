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
 *     --show FRAME      the fireworks display due at the top of this hour, played over the face (plan_show, as the
 *                       watch plays it) to that frame
 *     --show-check      play the whole display and check the face is put back exactly; print its frames and the
 *                       most pixels a frame covered
 *     --scribe          the minute written: draw the minute before first, then this one, keeping its new figures
 *     --scribe-frame K  and play the minute written (plan_scribe, as the watch plays it) to frame K
 *     --scribe-check    play all of it and check the face is written back exactly; print what was written
 *     --events MASK     the passing events the face may bring and the village's life (EV_* in plan.h): print the
 *                       event this minute chose, if any
 *     --event-frame K   and play it to frame K, as the watch plays it (the meteor or the birds over the face, plan_event;
 *                       the figures drawn in, the face drawn again so far along)
 *     --event-check     play all of it and check the face is put back exactly (the meteor, the birds)
 *     --tools           the theme's pieces in the Time 2's corners (the labours': tools.bin's record for the month)
 *     --theme N         the card's scene, THEME_* (1 the labours, as --labours)
 *     --tides LIST      the tide's turns: MINUTES-SINCE-1970:H|L:CM, comma-separated
 *     --tide-times      the next high and low waters set low on the face (as Face.tide_times)
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
static size_t decor_peak;                 /* the most held while the scene blob draws (it loaded besides, on the watch) */
static bool in_decor;
static void *counted(size_t n) {
  size_t *b = malloc(n + sizeof(size_t));
  if (!b) return NULL;
  *b = ((n + 3) & ~(size_t)3) + 4;
  if (getenv("PLAN_MEM_LOG")) fprintf(stderr, "alloc %zu\n", n);
  mem_now += *b, mem_blocks++;
  if (in_decor && mem_now > decor_peak) decor_peak = mem_now;
  if (mem_now > mem_peak) mem_peak = mem_now, mem_peak_blocks = mem_blocks;
  return b + 1;
}
static void uncounted(void *p) {
  if (!p) return;
  size_t *b = (size_t *)p - 1;
  mem_now -= *b, mem_blocks--;
  free(b);
}

/* the scene blob, linked in: the labours and the corner tools (tools.bin from memory) */
static bool host_decor(void *ctx, const DecorCtx *dc) {
  (void)ctx;
  FeastReader rd;
  plan_feast_memory(&rd, BLOB_TOOLS);
  in_decor = true;
  if (mem_now > decor_peak) decor_peak = mem_now;
  bool ok = plan_decor(dc, &rd);
  in_decor = false;
  return ok;
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
  bool mem = false, show_check = false, scribe_check = false;
  int show = -1, scribe_frame = -1, event_frame = -1;
  bool event_check = false, tools = false;
  for (int i = 8; i < argc; i++) {
    if (!strcmp(argv[i], "--24")) f.clock24 = true;
    else if (!strcmp(argv[i], "--no-names")) f.names = false;
    else if (!strcmp(argv[i], "--no-coords")) f.coords = false;
    else if (!strcmp(argv[i], "--labours")) f.theme = THEME_LABOURS;
    else if (!strcmp(argv[i], "--theme") && i + 1 < argc) f.theme = (uint8_t)atoi(argv[++i]);
    else if (!strcmp(argv[i], "--fahrenheit")) f.fahrenheit = true;
    else if (!strcmp(argv[i], "--city") && i + 1 < argc) f.city = argv[++i];
    else if (!strcmp(argv[i], "--country") && i + 1 < argc) f.country = argv[++i];
    else if (!strcmp(argv[i], "--time") && i + 1 < argc) repeat = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--mem")) mem = true;
    else if (!strcmp(argv[i], "--show") && i + 1 < argc) show = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--show-check")) show_check = true;
    else if (!strcmp(argv[i], "--scribe")) f.scribe = true;
    else if (!strcmp(argv[i], "--scribe-frame") && i + 1 < argc) f.scribe = true, scribe_frame = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--scribe-check")) f.scribe = true, scribe_check = true;
    else if (!strcmp(argv[i], "--events") && i + 1 < argc) f.events = (uint8_t)strtoul(argv[++i], NULL, 0);
    else if (!strcmp(argv[i], "--event-frame") && i + 1 < argc) event_frame = atoi(argv[++i]);
    else if (!strcmp(argv[i], "--event-check")) event_check = true;
    else if (!strcmp(argv[i], "--tools")) tools = true;
    else if (!strcmp(argv[i], "--tide-times")) f.tide_times = true;
    else if (!strcmp(argv[i], "--tides") && i + 1 < argc) {       /* turns: "MINUTES:H|L:CM,..." */
      static Tides td;
      memset(&td, 0, sizeof td);
      for (char *q = argv[++i]; *q && td.n < TIDE_TURNS;) {
        unsigned long m = strtoul(q, &q, 10);
        bool high = q[0] == ':' && q[1] == 'H';
        q += 3;
        td.at[td.n] = (uint32_t)m | (high ? TIDE_HIGH : 0), td.cm[td.n] = (int16_t)strtol(q, &q, 10), td.n++;
        if (*q == ',') q++;
      }
      f.tides = &td;
    }
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
  f.tools = tools;
  f.decor = host_decor;
  static Plan p;
  plan_init(&p, W, H, BLOB_PLAN, round ? BLOB_GABBRO : BLOB_EMERY);
  Target t = {row, NULL};
  struct timespec t0, t1;
  clock_gettime(CLOCK_MONOTONIC, &t0);
  FeastReader rd;
  plan_feast_memory(&rd, BLOB_FEASTS);
  plan_feast(&p, &f, utc, offset, &rd);
  if (f.scribe && !plan_render(&p, &f, utc - 60, offset, &t, counted, uncounted)) { fprintf(stderr, "render failed\n"); return 1; }
  for (int i = 0; i < repeat; i++)
    if (!plan_render(&p, &f, utc, offset, &t, counted, uncounted)) { fprintf(stderr, "render failed\n"); return 1; }
  if (mem) printf("peak %zu bytes in %zu blocks; the scene blob drawing %zu\n", mem_peak, mem_peak_blocks, decor_peak);
  if (getenv("PLAN_ROOMS"))                     /* the room each inscription has along the ring, in pixels */
    printf("rooms: city %.1f, country %.1f, latitude %.1f, longitude %.1f\n", (p.ins_hi[0] - p.ins_lo[0]) / 16.0,
           (p.ins_hi[1] - p.ins_lo[1]) / 16.0, (p.ins_hi[2] - p.ins_lo[2]) / 16.0, (p.ins_hi[3] - p.ins_lo[3]) / 16.0);
  if (f.events && p.event)
    printf("event %d: %d frames, %d,%d, %d,%d\n", p.event, p.event == EV_FIGURES ? EVENT_FIGS_FRAMES : p.event_frames,
           p.event_x0, p.event_y0, p.event_x1, p.event_y1);
  if ((event_frame >= 0 || event_check) && p.event == EV_FIGURES) {
    f.figs_part = (uint8_t)(event_frame < EVENT_FIGS_FRAMES ? event_frame + 1 : 0);
    if (f.figs_part != 1 && !plan_render(&p, &f, utc, offset, &t, counted, uncounted)) { fprintf(stderr, "render failed\n"); return 1; }
  } else if ((event_frame >= 0 || event_check) && p.event) {
    static uint8_t base[MAX_W * MAX_H];
    memcpy(base, fb, sizeof fb);
    static struct { ShowUndo u; uint32_t px[EVENT_UNDO]; } undo = {{0, EVENT_UNDO}, {0}};
    int last = event_check ? p.event_frames : event_frame, most = 0;
    for (int k = 0; k <= last; k++) {
      plan_event(&p, &t, k, &undo.u);
      if (undo.u.n > most) most = undo.u.n;
    }
    if (event_check) {
      int off = 0;
      for (int i = 0; i < W * H; i++) off += fb[i] != base[i];
      printf("event: %d frames, at most %d pixels a frame; %s\n", p.event_frames, most,
             off ? "NOT put back" : "the face put back exactly");
      if (off || most >= EVENT_UNDO) return 1;
    }
  }
  if (scribe_frame >= 0 || scribe_check) {
    static uint8_t drawn[MAX_W * MAX_H];
    memcpy(drawn, fb, sizeof fb);
    uint32_t *room = p.scribe_n ? malloc(p.scribe_n * sizeof *room) : NULL;
    int n = p.scribe_n, last = scribe_check ? SCRIBE_FRAMES - 1 : scribe_frame;
    for (int k = 0; k <= last && p.scribe; k++) plan_scribe(&p, &t, k, room);
    if (scribe_check) {
      int off = 0;
      for (int i = 0; i < W * H; i++) off += fb[i] != drawn[i];
      printf("scribe: %d pixels written (%d of them outlines) in %d frames; %s\n", n, n ? p.scribe_lines : 0,
             SCRIBE_FRAMES, off ? "NOT written back" : "the face written back exactly");
      if (off) return 1;
    }
    free(room);
  }
  if (show >= 0 || show_check) {
    int32_t hour = (int32_t)((utc + offset) / 86400 + 719163) * 24 + (int32_t)((utc + offset) % 86400 / 3600);
    if (p.show_hour != hour) { fprintf(stderr, "no display due at this moment\n"); return 1; }
    static uint8_t base[MAX_W * MAX_H];
    memcpy(base, fb, sizeof fb);
    static struct { ShowUndo u; uint32_t px[4096]; } undo = {{0, 4096}, {0}};
    int last = show_check ? p.show_end : show, most = 0;
    for (int k = 0; k <= last; k++) {
      plan_show(&p, &t, k, &undo.u);
      if (undo.u.n > most) most = undo.u.n;
    }
    if (show_check) {
      int off = 0;
      for (int i = 0; i < W * H; i++) off += fb[i] != base[i];
      printf("display: %d rockets, %d frames, at most %d pixels a frame; %s\n", p.show_rockets, p.show_end, most,
             off ? "NOT put back" : "the face put back exactly");
      if (off) return 1;
    }
  }
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
