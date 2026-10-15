/* The calendars' code blob's entry table (tools/build_blob.py): the day's feast, looked up once a day by the watch
 * with the calendars' table, then let go. Built only into the blob. */
#include "plan.h"

__attribute__((used, section(".plan_api"))) const FeastApi feast_api = {
  FEAST_API_MAGIC, PLAN_LAYOUT, plan_feast,
};
