/* The fireworks display's code blob's entry table (tools/build_blob.py): loaded by the watch at the top of an hour
 * that brings a display, for the few seconds it lasts, then let go. Built only into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const ShowApi show_api = {
  SHOW_API_MAGIC, PLAN_LAYOUT, plan_show,
};
