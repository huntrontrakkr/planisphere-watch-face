#!/usr/bin/env bash
# Build the settings page's preview (preview/plan-preview.js, the WebAssembly inlined) from the watch's own C.
# Needs Emscripten (~/code/ext/emsdk).
set -e
cd "$(dirname "$0")/.."
. "${EMSDK:-$HOME/code/ext/emsdk}/emsdk_env.sh" >/dev/null 2>&1
C=watchface/src/c
python3 tools/blobs_h.py
emcc -O2 -ffp-contract=off -I$C -Ibuild preview/preview.c $C/plan_render.c $C/plan_astro.c $C/plan_math.c $C/plan_feasts.c \
  $C/plan_show.c \
  -o preview/plan-preview.js \
  -sMODULARIZE=1 -sEXPORT_NAME=PlanPreview -sSINGLE_FILE=1 -sENVIRONMENT=web,node -sFILESYSTEM=0 \
  -sALLOW_MEMORY_GROWTH=1 -sINITIAL_MEMORY=4MB -sEXPORTED_FUNCTIONS=_malloc,_free \
  -sEXPORTED_RUNTIME_METHODS=HEAPU8,stringToUTF8,UTF8ToString -sASSERTIONS=0 -sSINGLE_FILE_BINARY_ENCODE=0
ls -l preview/plan-preview.js | awk '{print $5 " bytes: preview/plan-preview.js"}'
