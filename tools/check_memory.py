"""The most memory a frame of the face can need, against what the watch has for it.

A frame's memory is the drawing's state and the window's grid (its size set by the window, so by the latitude), with
the numerals' and the labours' scratch before the grid, as build/host --mem counts it (as PebbleOS's heap does). This
draws every latitude at night and by day on both watches and fails if any frame needs more than its watch's budget:
the heap left after the face has loaded, measured in the emulator (g_heap_free over GDB, labours on), less 3 KB of
headroom. (Nothing else takes memory once the face has loaded: the messages' buffers, the window and the timers are
all made at the start. The Round 2's frames need the most near the poles, where its window is largest.)

    tools/build-host.sh && python3 tools/check_memory.py

The heap was measured with the sizes in MEASURED; what the code, the data or the app have grown since comes off it
here. Measure it again (and update HEAP and MEASURED) after large changes:

    <pebble-tool-python> tools/emulator.py emery shots --set LABOURS=1 --gdb g_heap_free g_heap_low
"""
import re
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = ROOT / "build" / "host"
DATA = ROOT / "watchface" / "resources" / "data"
HEAP = {"emery": 23204, "gabbro": 22200}     # bytes free after loading, measured 2026-10-15 with:
MEASURED = {"code": 60900, "plan": 24084, "geom": {"emery": 13316, "gabbro": 14312},
            "app": {"emery": 4784, "gabbro": 4788}}
HEADROOM = 3072
SNOW = "-20,73,90,60,20,12,20,1003,80,250"
MOMENTS = (1792027800, 1792000800)          # 15 October 2026, 01:30 and 18:00 UTC (night and day in the Americas)


def peak(args):
    out = subprocess.run([str(HOST), *args, "/dev/null", "--mem"], capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"check_memory: the drawing failed: {' '.join(args)}: {out.stderr.strip()}")
    return int(re.search(r"peak (\d+)", out.stdout).group(1))


def app_size(screen):
    """The app's own binary as the watch loads it (text, data and bss), if it has been built."""
    elf = ROOT / "watchface" / "build" / screen / "pebble-app.elf"
    sdks = sorted(Path.home().glob(".local/share/pebble-sdk/SDKs/*/toolchain/arm-none-eabi/bin/arm-none-eabi-size"))
    if not elf.exists() or not sdks:
        return MEASURED["app"][screen]
    out = subprocess.run([str(sdks[-1]), str(elf)], capture_output=True, text=True).stdout.splitlines()[1].split()
    return int(out[3])


def heap(screen):
    """The heap free after loading now: as measured, less what has grown since."""
    code = struct.unpack("<5I", (DATA / "plan_code.bin").read_bytes()[:20])[1]
    grown = (code - MEASURED["code"] + (DATA / "plan.bin").stat().st_size - MEASURED["plan"] +
             (DATA / f"geom~{screen}.bin").stat().st_size - MEASURED["geom"][screen] + app_size(screen) -
             MEASURED["app"][screen])
    return HEAP[screen] - grown


def main():
    bad = False
    for screen in ("emery", "gabbro"):
        worst, at = 0, None
        for lat in range(-89, 90):
            for t in MOMENTS:
                n = peak([screen, "0", str(t), str(lat), "-74", "-240", "--labours", "--weather", SNOW])
                if n > worst:
                    worst, at = n, (lat, t)
        budget = heap(screen) - HEADROOM
        print(f"{screen}: a frame needs {worst:,} bytes at most (latitude {at[0]}), budget {budget:,}")
        bad |= worst > budget
    if bad:
        sys.exit("check_memory: a frame could run out of memory on the watch")


if __name__ == "__main__":
    main()
