/* The renderer's entry table, at the start of its code blob (tools/build_blob.py). Built only into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const PlanApi plan_api = {
  PLAN_API_MAGIC, PLAN_LAYOUT, plan_init, plan_render, plan_place,
};
