"""Build the code blobs for the watch: watchface/resources/data/plan_code.bin, the renderer (plan_render.c,
plan_astro.c, plan_math.c), which main.c keeps loaded; feast_code.bin, the calendars (plan_feasts.c and the
ephemeris it asks), which main.c loads once a day to look up the day's feast and lets go; and show_code.bin, the
fireworks display (plan_show.c), which it loads for the few seconds of a display; decor_code.bin, the woodcuts'
themes behind the face and their roundels (plan_decor.c), and labours_code.bin, the labours and the Time 2's corner
tools (plan_labours.c), one or the other loaded for the moment the renderer asks for it.

Each is compiled with the Pebble SDK's own compiler and flags, its entry table first (watchface/blob/*_blob.c) and
the C library's few functions it uses (blob_libc.c), linked at address 0 with libgcc's arithmetic
(watchface/blob/blob.ld), and packed as

    header   magic "PLNC", the image's size, the zeroed memory after it (bss), the relocations' count, the entry
             table's offset: five little-endian uint32s
    image    the code and its constant data (and initialised data, if any)
    relocs   one uint16 for each word holding an absolute address: its offset / 4

main.c loads it into memory, adds the load address to each listed word, flushes the caches (memory_cache_flush) and
calls the entry table. Only R_ARM_ABS32 relocations need it (calls and branches are relative); anything else
absolute fails the build. Standard library only.

    python3 tools/build_blob.py [--cc PATH-TO-arm-none-eabi-gcc]

The wscript passes the compiler `pebble build` uses; by hand it is the Pebble SDK's (PEBBLE_SDK, or the SDK the Pebble
tool installed last).
"""
import argparse
import os
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "watchface" / "src" / "c"
BLOB = ROOT / "watchface" / "blob"
OUT_DIR = ROOT / "watchface" / "resources" / "data"
WORK = ROOT / "build" / "blob"
SDK = Path(os.environ.get("PEBBLE_SDK", Path.home() / ".local/share/pebble-sdk/SDKs/current"))
TC = SDK / "toolchain" / "arm-none-eabi" / "bin"     # (or --cc's directory)
CFLAGS = ["-mcpu=cortex-m3", "-mthumb", "-Os", "-std=c11", "-ffunction-sections", "-fdata-sections",
          "-ffp-contract=off", "-fno-common", "-Wall", "-Wextra", "-Wno-unused-parameter", "-Werror",
          "-fno-tree-loop-distribute-patterns", f"-I{SRC}",
          # each layer in a frame of its own, not all of them in plan_render's: the watch's stack is 2 KB
          "-fno-inline-functions-called-once"]
# for tools/emulator.py profile: every function its own, to count where the time goes; else link-time optimisation
CFLAGS += ["-fno-inline"] if os.environ.get("PLAN_PROFILE") else ["-flto"]
# each blob: its sources (the entry table's first) and its entry table's name
BLOBS = {
    "plan_code": ([BLOB / "plan_blob.c", SRC / "plan_render.c", SRC / "plan_astro.c", SRC / "plan_math.c",
                   BLOB / "blob_libc.c"], "plan_api"),
    "feast_code": ([BLOB / "feast_blob.c", SRC / "plan_feasts.c", SRC / "plan_astro.c", SRC / "plan_math.c",
                    BLOB / "blob_libc.c"], "feast_api"),
    "show_code": ([BLOB / "show_blob.c", SRC / "plan_show.c", SRC / "plan_math.c", BLOB / "blob_libc.c"], "show_api"),
    "decor_code": ([BLOB / "decor_blob.c", SRC / "plan_decor.c", SRC / "plan_math.c", BLOB / "blob_libc.c"],
                   "decor_api"),
    "labours_code": ([BLOB / "labours_blob.c", SRC / "plan_labours.c", SRC / "plan_math.c", BLOB / "blob_libc.c"],
                     "labours_api"),
}
SOURCES = BLOBS["plan_code"][0]
MAGIC = 0x434E4C50          # "PLNC"


def run(*args):
    out = subprocess.run([str(a) for a in args], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"build_blob: {Path(str(args[0])).name} failed:\n{out.stderr.strip()}")
    return out.stdout


def main():
    global TC
    ap = argparse.ArgumentParser()
    ap.add_argument("--cc", help="the SDK's arm-none-eabi-gcc")
    a = ap.parse_args()
    sdks = sorted(Path.home().glob(".local/share/pebble-sdk/SDKs/*/toolchain/arm-none-eabi/bin/arm-none-eabi-gcc"))
    cc = (a.cc or (str(TC / "arm-none-eabi-gcc") if (TC / "arm-none-eabi-gcc").exists() else None) or
          shutil.which("arm-none-eabi-gcc") or (str(sdks[-1]) if sdks else None))
    if not cc:
        sys.exit("build_blob: no arm-none-eabi-gcc (install the Pebble SDK, or pass --cc)")
    TC = Path(cc).resolve().parent
    for name, (sources, api_name) in BLOBS.items():
        build(name, sources, api_name)


def build(name, sources, api_name):
    work = WORK / name
    work.mkdir(parents=True, exist_ok=True)
    gcc = TC / "arm-none-eabi-gcc"
    objs = []
    for src in sources:
        obj = work / (src.stem + ".o")
        run(gcc, *CFLAGS, "-c", src, "-o", obj)
        objs.append(obj)
    elf = WORK / f"{name}.elf"
    run(gcc, *CFLAGS, "-nostdlib", "-nostartfiles", f"-Wl,-T,{BLOB / 'blob.ld'}", "-Wl,--gc-sections", "-Wl,-q",
        "-o", elf, *objs, "-lgcc")
    # the sections: the image is .text then .data, contiguous; .bss after them is only zeroed memory
    sec = {}
    for line in run(TC / "arm-none-eabi-readelf", "-SW", elf).splitlines():
        m = re.match(r"\s*\[\s*\d+\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+[0-9a-f]+\s+([0-9a-f]+)", line)
        if m:
            sec[m.group(1)] = (int(m.group(2), 16), int(m.group(3), 16))
    text_a, text_n = sec[".text"]
    data_a, data_n = sec.get(".data", (text_a + text_n, 0))
    bss_a, bss_n = sec.get(".bss", (data_a + data_n, 0))
    assert text_a == 0 and data_a == text_a + text_n, "the image must start at 0 and run on unbroken"
    image_bin = work / "image.bin"
    run(TC / "arm-none-eabi-objcopy", "-O", "binary", "-j", ".text", "-j", ".data", elf, image_bin)
    image = image_bin.read_bytes()
    assert len(image) == text_n + data_n, (len(image), text_n, data_n)
    bss = bss_n + (bss_a - (data_a + data_n))
    # the absolute addresses to relocate
    relocs, section = [], None
    for line in run(TC / "arm-none-eabi-readelf", "-rW", elf).splitlines():
        m = re.match(r"Relocation section '\.rel\.(\S+)'", line)
        if m:
            section = m.group(1)
            continue
        m = re.match(r"\s*([0-9a-f]+)\s+[0-9a-f]+\s+(R_ARM_\S+)", line)
        if not m or section is None:
            continue
        off, kind = int(m.group(1), 16), m.group(2)
        if not (section.startswith("text") or section.startswith("data") or section.startswith("rodata")):
            continue
        if kind == "R_ARM_ABS32":
            assert off % 4 == 0 and off < len(image), (hex(off), section)
            relocs.append(off)
        elif kind not in ("R_ARM_THM_CALL", "R_ARM_THM_JUMP24", "R_ARM_THM_JUMP11", "R_ARM_THM_JUMP8",
                          "R_ARM_THM_JUMP19", "R_ARM_REL32", "R_ARM_PREL31", "R_ARM_THM_PC8", "R_ARM_THM_PC12",
                          "R_ARM_THM_ALU_PREL_11_0", "R_ARM_V4BX", "R_ARM_NONE"):
            sys.exit(f"build_blob: an absolute relocation the loader cannot apply: {kind} at {off:#x} in {section}")
    relocs = sorted(set(relocs))
    syms = {n: int(a, 16) for a, n in re.findall(r"^([0-9a-f]+) \S (\S+)$", run(TC / "arm-none-eabi-nm", elf), re.M)}
    api = syms[api_name]
    assert len(image) < 4 * 65536, "relocation offsets are kept as uint16 words"
    blob = struct.pack("<5I", MAGIC, len(image), bss, len(relocs), api) + image + \
        b"".join(struct.pack("<H", r // 4) for r in relocs)
    out = OUT_DIR / f"{name}.bin"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists() or out.read_bytes() != blob:
        out.write_bytes(blob)
    print(f"{name}.bin: {len(blob):,} bytes ({len(image):,} image, {bss} bss, {len(relocs)} relocations)")


if __name__ == "__main__":
    main()
