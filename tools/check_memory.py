"""The most memory a frame of the face can need, against what the watch has for it.

A frame's memory is the drawing's state and the window's grid (its size set by the window, so by the latitude), with
the numerals' and the labours' scratch before the grid and the minute's new figures kept for the scribe (--scribe:
the minute before drawn first), as build/host --mem counts it (as PebbleOS's heap does). The
day's feast lookup loads the calendars' code; a fireworks display loads its own code and its record of the pixels each
frame covers (SHOW_UNDO of them: some displays are played here to see that none covers more); a passing event (a
meteor, the birds) the same code with a far smaller record (EVENT_UNDO), and the figures drawn in at dusk are whole
frames. This draws every
latitude at night and by day on both watches and fails if any of these needs more than its watch's budget:
the heap left after the face has loaded, measured in the emulator (g_heap_free over GDB, labours on), less 3 KB of
headroom. (Nothing else takes memory once the face has loaded: the messages' buffers, the window and the timers are
all made at the start. The Round 2's frames need the most near the poles, where its window is largest.)

    tools/build-host.sh && python3 tools/check_memory.py

The heap was measured with the sizes in MEASURED; what the code, the data, the app or the face's kept state (the
Plan, its size read from the renderer's entry table) have grown since comes off it here. Measure it again (and update
HEAP and MEASURED) after large changes:

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
HEAP = {"emery": 16712, "gabbro": 15716}     # bytes free after loading, measured 2026-10-16 with:
MEASURED = {"code": 66496, "plan": 24148, "geom": {"emery": 13316, "gabbro": 14312},
            "app": {"emery": 5968, "gabbro": 5968}, "state": 3904}
HEADROOM = 3072
SNOW = "-20,73,90,60,20,12,20,1003,80,250"
MOMENTS = (1792027800, 1792000800)          # 15 October 2026, 01:30 and 18:00 UTC (night and day in the Americas)


def peak(args, flags):
    out = subprocess.run([str(HOST), *args, "/dev/null", *flags, "--mem"], capture_output=True, text=True)
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


def state_size():
    """sizeof(Plan) on the watch, from the layout word in the renderer's entry table (plan.h PLAN_LAYOUT)."""
    blob = (DATA / "plan_code.bin").read_bytes()
    entry = struct.unpack("<5I", blob[:20])[4]
    return (struct.unpack("<I", blob[20 + entry + 4: 20 + entry + 8])[0] >> 12) & 0xFFFF


def heap(screen):
    """The heap free after loading now: as measured, less what has grown since."""
    code = struct.unpack("<5I", (DATA / "plan_code.bin").read_bytes()[:20])[1]
    grown = (code - MEASURED["code"] + (DATA / "plan.bin").stat().st_size - MEASURED["plan"] +
             (DATA / f"geom~{screen}.bin").stat().st_size - MEASURED["geom"][screen] + app_size(screen) -
             MEASURED["app"][screen] + state_size() - MEASURED["state"])
    return HEAP[screen] - grown


def lookup_need(screen):
    """The day's feast lookup: the calendars' code blob loaded (main.c feast_of_day; it reads the table straight from
    the resources), with the heap's header and the code's alignment, less the screen's geometry it borrows (let go for
    the lookup, against the free memory, and loaded again)."""
    code = struct.unpack("<5I", (DATA / "feast_code.bin").read_bytes()[:20])[1]
    return code + 4 + 4 - ((DATA / f"geom~{screen}.bin").stat().st_size + 4)


def show_need():
    """A fireworks display as it plays (main.c show_begin): its code blob, and its record of what a frame covers."""
    code = struct.unpack("<5I", (DATA / "show_code.bin").read_bytes()[:20])[1]
    return code + 4 + 4 + (4 + 4 * SHOW_UNDO) + 4


SHOW_UNDO = int(re.search(r"#define SHOW_UNDO (\d+)", (ROOT / "watchface/src/c/plan.h").read_text()).group(1))
# displays to play through (local date and hour, the place, its offset in minutes, the calendars)
DISPLAYS = [((2026, 7, 4, 21), (40.71, -74.01), -240, 64), ((2026, 11, 5, 19), (51.51, -0.13), 0, 128),
            ((2027, 1, 1, 0), (51.51, -0.13), 0, 128), ((2026, 11, 8, 22), (28.61, 77.21), 330, 2048),
            ((2027, 2, 5, 23), (39.9, 116.4), 480, 512), ((2026, 12, 31, 22), (-33.87, 151.21), 660, 64)]


def show_most():
    """The most pixels a frame covers in DISPLAYS, on both watches and a few plates."""
    from datetime import datetime, timedelta, timezone
    most = 0
    for (y, mo, d, h), (lat, lon), off, cal in DISPLAYS:
        utc = int((datetime(y, mo, d, h) - timedelta(minutes=off)).replace(tzinfo=timezone.utc).timestamp())
        for screen in ("emery", "gabbro"):
            for plate in ("0", "2", "9"):
                out = subprocess.run([str(HOST), screen, plate, str(utc), str(lat), str(lon), str(off), "/dev/null",
                                      "--calendars", str(cal), "--show-check"], capture_output=True, text=True)
                m = re.search(r"at most (\d+) pixels", out.stdout)
                if not m or "put back exactly" not in out.stdout:
                    sys.exit(f"check_memory: the display failed: {screen} {plate} {y}-{mo}-{d} {h}h: {out.stdout}{out.stderr}")
                most = max(most, int(m.group(1)))
    return most


def main():
    bad = False
    for screen in ("emery", "gabbro"):
        worst, at = 0, None
        for lat in range(-89, 90):
            for t in MOMENTS:
                n = peak([screen, "0", str(t), str(lat), "-74", "-240"], ["--labours", "--weather", SNOW, "--scribe"])
                if n > worst:
                    worst, at = n, (lat, t)
        budget = heap(screen) - HEADROOM
        need, show = lookup_need(screen), show_need()
        print(f"{screen}: a frame needs {worst:,} bytes at most (latitude {at[0]}), the day's feast lookup {need:,}, "
              f"a fireworks display {show:,}; budget {budget:,}")
        bad |= worst > budget or need > budget or show > budget
    most = show_most()
    print(f"the displays: a frame covers {most} pixels at most, of the {SHOW_UNDO} kept")
    if bad or most > SHOW_UNDO:
        sys.exit("check_memory: a frame could run out of memory on the watch")


if __name__ == "__main__":
    main()
