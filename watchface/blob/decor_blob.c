/* The scene blob's entry table (tools/build_blob.py): the woodcuts' themes behind the face and their roundels in the
 * Time 2's corners, loaded by the watch for the moment plan_render asks for them (Face.decor), then let go. Built only
 * into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const DecorApi decor_api = {
  DECOR_API_MAGIC, PLAN_LAYOUT, plan_decor,
};
