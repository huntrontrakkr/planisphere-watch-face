/* The renderer's entry table, at the start of its code blob (tools/build_blob.py), and the few functions of the C
 * library it uses: the blob carries no library but libgcc's arithmetic. Built only into the blob. */
#include "plan.h"

void *memcpy(void *d, const void *s, size_t n) {
  uint8_t *a = d;
  const uint8_t *b = s;
  while (n--) *a++ = *b++;
  return d;
}
void *memset(void *d, int c, size_t n) {
  uint8_t *a = d;
  while (n--) *a++ = (uint8_t)c;
  return d;
}
size_t strlen(const char *s) {
  const char *p = s;
  while (*p) p++;
  return (size_t)(p - s);
}
char *strcpy(char *d, const char *s) {
  char *r = d;
  while ((*d++ = *s++)) {}
  return r;
}
char *strcat(char *d, const char *s) {
  strcpy(d + strlen(d), s);
  return d;
}

__attribute__((used, section(".plan_api"))) const PlanApi plan_api = {
  PLAN_API_MAGIC, PLAN_LAYOUT, plan_init, plan_render,
};
