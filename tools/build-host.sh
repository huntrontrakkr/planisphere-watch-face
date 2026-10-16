#!/bin/sh
# Build the host harness (build/host) from the watch's core sources.
set -e
cd "$(dirname "$0")/.."
mkdir -p build
C=watchface/src/c
python3 tools/blobs_h.py
cc -O2 -g -ffp-contract=off -Wall -Wextra -Wno-unused-parameter -I$C -Ibuild -o build/host tools/host.c \
  $C/plan_render.c $C/plan_astro.c $C/plan_math.c $C/plan_feasts.c $C/plan_show.c $C/plan_decor.c "$@"
cc -O2 -ffp-contract=off -I$C -Ibuild -o build/feast_check tools/feast_check.c $C/plan_feasts.c $C/plan_astro.c $C/plan_math.c
