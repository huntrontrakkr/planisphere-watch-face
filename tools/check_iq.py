"""The integer trigonometry on both sides, bit for bit: the watch's C (plan_math.c isin_q30, built for the host) against
the prototype's (proto/iq.py), over a sweep of angles; and the projection's parts.

    uv run python tools/check_iq.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import iq                                   # noqa: E402

SRC = """
#include <stdio.h>
#include "plan_math.h"
int main(void) {
  for (uint32_t a = 0; a < (1u << 20); a += 61) printf("%d\\n", (int)isin_q30(a));
  for (int y = -32768; y <= 32768; y += 1543) for (int x = -32768; x <= 32768; x += 977) printf("%d\\n", (int)iatan2_brad(y, x));
  for (int64_t s = -(1 << 30); s <= (1 << 30); s += 2654435) printf("%d\\n", (int)iasin_brad((int32_t)s));
  return 0;
}
"""


def main():
    with tempfile.TemporaryDirectory() as d:
        c = Path(d) / "iq.c"
        c.write_text(SRC)
        exe = Path(d) / "iq"
        subprocess.run(["cc", "-O2", "-ffp-contract=off", f"-I{ROOT / 'watchface/src/c'}", "-o", str(exe), str(c),
                        str(ROOT / "watchface/src/c/plan_math.c")], check=True)
        got = [int(v) for v in subprocess.run([str(exe)], capture_output=True, text=True, check=True).stdout.split()]
    want = [iq.isin_q30(a) for a in range(0, 1 << 20, 61)]
    want += [iq.iatan2_brad(y, x) for y in range(-32768, 32769, 1543) for x in range(-32768, 32769, 977)]
    want += [iq.iasin_brad(s) for s in range(-(1 << 30), (1 << 30) + 1, 2654435)]
    bad = sum(1 for g, w in zip(got, want) if g != w)
    print(f"isin_q30, iatan2_brad, iasin_brad: {len(want)} values, {bad} differ")
    if bad or len(got) != len(want):
        sys.exit("check_iq: the watch's and the prototype's sines differ")


if __name__ == "__main__":
    main()
