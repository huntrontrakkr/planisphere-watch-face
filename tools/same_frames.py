"""The same frames, to the byte, as an earlier build: for changes that should not move a pixel (memory, code size,
refactoring). Builds the host harness from a commit (default HEAD) in a temporary worktree, draws a fixed spread of
frames with it and with this tree's build/host (both watches, every plate, night, day and dusk, latitudes from -60 to
66, clear skies and five kinds of weather, the labours on) and lists any that differ. Parity with the prototype
(tools/parity.py) cannot see such slips: its few hundred pixels of difference hide a few dozen more.

    tools/build-host.sh && python3 tools/same_frames.py [commit]
"""
import itertools
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TIMES = (1792027800, 1792000800, 1792015200, 1792044000)    # 15 October 2026 at 01:30, 18:00, 22:00 and 06:00 UTC
LATS = (-60, -34, 0, 40, 51, 66)
WEATHER = (None, "-20,73,90,60,20,12,20,1003,80,250",        # snow
           "150,3,100,80,30,8,200,1012,0,3000",              # overcast
           "120,61,90,90,90,30,250,998,0,800",               # rain
           "80,45,100,100,100,2,90,1020,0,20",               # fog
           "220,2,30,40,10,5,180,1015,0,3000")               # broken cloud


def frames():
    for n, (screen, plate, t, lat) in enumerate(itertools.product(("emery", "gabbro"), range(10), TIMES, LATS)):
        w = WEATHER[n % len(WEATHER)]
        yield [screen, str(plate), str(t), str(lat), "-74", "-240"], ["--labours"] + (["--weather", w] if w else [])


def draw(host, args, flags, out):
    r = subprocess.run([str(host), *args, str(out), *flags], capture_output=True)
    return r.returncode == 0 and out.read_bytes()


def main():
    ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "ref"
        subprocess.run(["git", "-C", str(ROOT), "worktree", "add", "--detach", str(tree), ref], check=True,
                       capture_output=True)
        try:
            subprocess.run(["python3", "tools/blobs_h.py"], cwd=tree, check=True, capture_output=True)
            subprocess.run(["sh", "tools/build-host.sh"], cwd=tree, check=True, capture_output=True)
            bad = n = 0
            for args, flags in frames():
                n += 1
                a = draw(tree / "build" / "host", args, flags, Path(tmp) / "a.ppm")
                b = draw(ROOT / "build" / "host", args, flags, Path(tmp) / "b.ppm")
                if a != b or not a:
                    bad += 1
                    print("differs:", " ".join(args + flags))
        finally:
            subprocess.run(["git", "-C", str(ROOT), "worktree", "remove", "--force", str(tree)], capture_output=True)
    print(f"{n} frames against {ref}: {'all the same' if not bad else f'{bad} differ'}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
