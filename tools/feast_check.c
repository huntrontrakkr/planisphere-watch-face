/* The watch's feast lookup over a run of days, for tools/check_feasts.py to set beside the prototype's:
 *   build/feast_check FIRST_ORDINAL DAYS MASK HOURS   ->  one line a day: the feast's index in feasts.bin, or -1 */
#include <stdio.h>
#include <stdlib.h>
#include "plan.h"
#include "plan_blobs.h"

int main(int argc, char **argv) {
  if (argc < 5) return 2;
  int32_t first = atoi(argv[1]);
  int days = atoi(argv[2]);
  uint32_t mask = (uint32_t)strtoul(argv[3], NULL, 0);
  float hours = (float)atof(argv[4]);
  for (int d = 0; d < days; d++) printf("%d\n", plan_feast_on(BLOB_FEASTS, first + d, mask, hours));
  return 0;
}
