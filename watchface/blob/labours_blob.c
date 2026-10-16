/* The labours' blob's entry table (tools/build_blob.py): the labours of the months and the Time 2's corner tools,
 * loaded by the watch for the moment plan_render asks for them (Face.decor) on the plain card or the labours, then let
 * go. Built only into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const DecorApi labours_api = {
  DECOR_API_MAGIC, PLAN_LAYOUT, plan_labours,
};
