"""The renderer's deepest stack, worked out from the compiler: each function's frame (-fstack-usage) along the call
graph (-fcallgraph-info), for the code blob as tools/build_blob.py builds it. Prints the deepest chains from each
entry, and the depth at each call the renderer makes out of itself (the memory and the screen's rows, which run the
system's code on the same stack).

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
    with tempfile.TemporaryDirectory() as tmp:
        objs = []
        for src in build_blob.SOURCES:
            obj = Path(tmp) / (src.stem + ".o")
            subprocess.run([gcc, *flags, "-c", str(src), "-o", str(obj)], check=True)
            objs.append(str(obj))
        elf = Path(tmp) / "plan.elf"
        subprocess.run([gcc, *flags, "-fstack-usage", "-fcallgraph-info=su", "-nostdlib", "-nostartfiles",
                        f"-Wl,-T,{build_blob.BLOB / 'blob.ld'}", "-Wl,--gc-sections", "-Wl,-q", "-save-temps", "-o",
                        str(elf), *objs, "-lgcc"], check=True, cwd=tmp, capture_output=True)
        # the functions whose addresses the code takes: what a call through a pointer inside the renderer may reach
        readelf = str(Path(gcc).parent / "arm-none-eabi-readelf")
        funcs = set(re.findall(r"\sFUNC\s+\S+\s+\S+\s+\S+\s+(\S+)$",
                               subprocess.run([readelf, "-sW", str(elf)], capture_output=True, text=True).stdout, re.M))
        taken = set()
        for line in subprocess.run([readelf, "-rW", str(elf)], capture_output=True, text=True).stdout.splitlines():
            m = re.match(r"\s*[0-9a-f]+\s+[0-9a-f]+\s+R_ARM_ABS32\s+[0-9a-f]+\s+(\S+)", line)
            if m and m.group(1) in funcs and m.group(1) not in ("plan_init", "plan_render"):
                taken.add(m.group(1))
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

    for entry in ("plan_render", "plan_init"):
        total, chain = deepest(entry)
        print(f"{entry}: {total} bytes deep at most")
        print("   " + " > ".join(f"{f} {frame.get(f, LIBGCC if f.startswith('__') else 0)}" for f in chain))
    # the deepest ways down from plan_render, one per first call
    print("plan_render's calls, deepest first:")
    rows = sorted(((deepest(g)[0], g) for g in calls.get("plan_render", ())), reverse=True)
    for d, g in rows[:a.top]:
        print(f"   {frame['plan_render'] + d:5d}  {' > '.join(deepest(g)[1])}")
    # where the renderer calls out (function pointers): the depth there, before the system's own frames
    def outs(f, depth, path, found):
        depth += frame.get(f, 0)
        if "__indirect_call" in calls.get(f, ()):
            found.append((depth, " > ".join(path + (f,))))
        for g in calls.get(f, ()):
            if g in frame and g not in path:
                outs(g, depth, path + (f,), found)
        return found
    found = sorted(set(outs("plan_render", 0, (), [])), reverse=True)
    print("calls out of the renderer (alloc, release, the screen's rows), deepest first:")
    for d, p in found[:a.top]:
        print(f"   {d:5d}  {p}")
    print("called through pointers:", ", ".join(sorted(taken)) or "none")
    if dynamic:
        print("frames sized at run time:", ", ".join(sorted(dynamic)))
    worst = max(deepest(e)[0] for e in ("plan_render", "plan_init"))
    if dynamic or (a.budget and worst > a.budget):
        sys.exit(f"The renderer goes {worst} bytes deep (budget {a.budget}), or has frames sized at run time.")


if __name__ == "__main__":
    main()
