/* The motion blob's entry table (tools/build_blob.py): the fireworks display and the minute written, loaded by the
 * watch for the seconds they play, then let go. Built only into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const ShowApi show_api = {
  SHOW_API_MAGIC, PLAN_LAYOUT, plan_show, plan_scribe,
};
