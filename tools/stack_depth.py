"""The code blobs' deepest stack, worked out from the compiler: each function's frame (-fstack-usage) along the call
graph (-fcallgraph-info), for each code blob as tools/build_blob.py builds it, from each function its entry table
holds (the renderer's plan_render and plan_init, the calendars' plan_feast, the display's plan_show). Prints the
deepest chains from each entry, and the depth at each call the blob makes out of itself (the memory and the screen's
rows, which run the system's code on the same stack).

    python3 tools/stack_depth.py [--top N] [--budget BYTES]

The watch gives the app 2,016 bytes of stack. The system's event loop and main.c take about 512 of it before the
renderer starts (g_stack_at, over GDB in the emulator), and the system's own calls for memory and the screen run on
what is left, so the renderer keeps to a budget (CI: 1,000 bytes). g_stack measures the whole of a frame.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_blob                 # noqa: E402

APP_FRAME = 96                    # bytes: main.c's decor_draw and its blob loader, between the renderer and the scene blob
LIBGCC = 32                       # bytes: libgcc's float helpers push a few registers at most (checked: up to 24)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--budget", type=int, default=0, help="fail if the renderer goes deeper than this")
    a = ap.parse_args()
    sdks = sorted(Path.home().glob(".local/share/pebble-sdk/SDKs/*/toolchain/arm-none-eabi/bin/arm-none-eabi-gcc"))
    cc = build_blob.TC / "arm-none-eabi-gcc"
    gcc = str(cc if cc.exists() else sdks[-1])
    flags = [f for f in build_blob.CFLAGS if f not in ("-Werror",)]
    worst_all, dynamic_all, depths = 0, set(), {}
    for name, (sources, api) in build_blob.BLOBS.items():
        worst, dynamic, outs = analyse(gcc, flags, sources, api, a.top)
        worst_all, dynamic_all, depths[name] = max(worst_all, worst), dynamic_all | dynamic, (worst, outs)
    # the scene blob runs inside the renderer's frame: called through Face.decor from plan_render itself, by main.c's
    # decor_draw (APP_FRAME for it and its loader)
    at = max((d for d, path in depths["plan_code"][1] if path == "plan_render"), default=0)
    for blob in ("decor_code", "labours_code"):
        nested = at + APP_FRAME + depths[blob][0]
        print(f"{blob} within the renderer: {at} + {APP_FRAME} (main.c) + {depths[blob][0]} = {nested} bytes")
        worst_all = max(worst_all, nested)
    if dynamic_all or (a.budget and worst_all > a.budget):
        sys.exit(f"A blob goes {worst_all} bytes deep (budget {a.budget}), or has frames sized at run time.")


def analyse(gcc, flags, sources, api, top):
    with tempfile.TemporaryDirectory() as tmp:
        objs = []
        for src in sources:
            obj = Path(tmp) / (src.stem + ".o")
            subprocess.run([gcc, *flags, "-c", str(src), "-o", str(obj)], check=True)
            objs.append(str(obj))
        elf = Path(tmp) / "plan.elf"
        subprocess.run([gcc, *flags, "-fstack-usage", "-fcallgraph-info=su", "-nostdlib", "-nostartfiles",
                        f"-Wl,-T,{build_blob.BLOB / 'blob.ld'}", "-Wl,--gc-sections", "-Wl,-q", "-save-temps", "-o",
                        str(elf), *objs, "-lgcc"], check=True, cwd=tmp, capture_output=True)
        # the functions whose addresses the code takes: those in the entry table (the blob's entries), and the rest,
        # what a call through a pointer inside the blob may reach
        readelf = str(Path(gcc).parent / "arm-none-eabi-readelf")
        symtab = subprocess.run([readelf, "-sW", str(elf)], capture_output=True, text=True).stdout
        funcs = set(re.findall(r"\sFUNC\s+\S+\s+\S+\s+\S+\s+(\S+)$", symtab, re.M))
        at, size = (int(v, 16) if i == 0 else int(v) for i, v in
                    enumerate(re.search(r"([0-9a-f]+)\s+(\d+)\s+OBJECT\s+\S+\s+\S+\s+\S+\s+" + api + "$", symtab,
                                        re.M).groups()))
        entries, taken = [], set()
        for line in subprocess.run([readelf, "-rW", str(elf)], capture_output=True, text=True).stdout.splitlines():
            m = re.match(r"\s*([0-9a-f]+)\s+[0-9a-f]+\s+R_ARM_ABS32\s+[0-9a-f]+\s+(\S+)", line)
            if m and m.group(2) in funcs:
                (entries.append if at <= int(m.group(1), 16) < at + size else taken.add)(m.group(2))
        frame, calls, dynamic = {}, {}, set()
        for ci in Path(tmp).glob("*.ci"):
            text = ci.read_text()
            for title, label in re.findall(r'node: \{ title: "([^"]+)" label: "([^"]*)"', text):
                name = title.split(":")[-1]
                m = re.search(r"\\n(\d+) bytes \((static|dynamic[^)]*)\)", label)
                if m:
                    frame[name] = int(m.group(1))
                    if m.group(2) != "static":
                        dynamic.add(name)
            for s, t in re.findall(r'edge: \{ sourcename: "([^"]+)" targetname: "([^"]+)"', text):
                calls.setdefault(s.split(":")[-1], set()).add(t.split(":")[-1])
        # a call through a pointer may go to any function whose address is taken; the rest go out of the renderer
        for f, out in calls.items():
            if "__indirect_call" in out:
                out |= taken

    @lru_cache(None)
    def deepest(f, path=()):
        """(bytes, chain) from f's entry down its deepest call."""
        if f in path:
            raise SystemExit(f"recursion: {' > '.join(path + (f,))}")
        own = frame.get(f, LIBGCC if f.startswith("__") else 0)
        best = (0, ())
        for g in calls.get(f, ()):
            d = deepest(g, path + (f,))
            if d[0] > best[0]:
                best = d
        return own + best[0], (f,) + best[1]

    entries.sort(key=lambda e: -deepest(e)[0])         # (the deepest first, for the report on its calls)
    for entry in entries:
        total, chain = deepest(entry)
        print(f"{entry}: {total} bytes deep at most")
        print("   " + " > ".join(f"{f} {frame.get(f, LIBGCC if f.startswith('__') else 0)}" for f in chain))
    # the deepest ways down from the first entry, one per first call
    first = entries[0]
    print(f"{first}'s calls, deepest first:")
    rows = sorted(((deepest(g)[0], g) for g in calls.get(first, ())), reverse=True)
    for d, g in rows[:top]:
        print(f"   {frame[first] + d:5d}  {' > '.join(deepest(g)[1])}")
    # where the renderer calls out (function pointers): the depth there, before the system's own frames
    def outs(f, depth, path, found):
        depth += frame.get(f, 0)
        if "__indirect_call" in calls.get(f, ()):
            found.append((depth, " > ".join(path + (f,))))
        for g in calls.get(f, ()):
            if g in frame and g not in path:
                outs(g, depth, path + (f,), found)
        return found
    found = sorted(set(outs(first, 0, (), [])), reverse=True)
    if found:
        print("calls through pointers (out of the blob, or to those below), deepest first:")
        for d, p in found[:top]:
            print(f"   {d:5d}  {p}")
    print("called through pointers:", ", ".join(sorted(taken)) or "none")
    if dynamic:
        print("frames sized at run time:", ", ".join(sorted(dynamic)))
    return max(deepest(e)[0] for e in entries), dynamic, found


if __name__ == "__main__":
    main()
