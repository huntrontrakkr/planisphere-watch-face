"""The watch's feast lookup (plan_feasts.c, through build/feast_check) against the prototype's (proto/feasts.py),
day by day: every calendar kept, eight years.

    tools/build-host.sh && (cd proto && uv run python ../tools/check_feasts.py [first-year] [years])
"""
import functools
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import feasts as F                                         # noqa: E402

F.diwali = functools.lru_cache(None)(F.diwali)
F.sun_day = functools.lru_cache(None)(F.sun_day)


def index_of(o, mask, hours):
    best = None
    for i, f in enumerate(F.FEASTS):
        if not mask >> F.CAL[f["cal"]] & 1:
            continue
        if (best is None or f["rank"] < F.FEASTS[best]["rank"]) and F.matches(f["rule"], o, hours):
            best = i
    return -1 if best is None else best


def main():
    first_year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    years = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    first = date(first_year, 1, 1).toordinal()
    days = date(first_year + years, 1, 1).toordinal() - first
    mask, hours = (1 << len(F.CALENDARS)) - 1, -5.0
    out = subprocess.run([str(ROOT / "build" / "feast_check"), str(first), str(days), str(mask), str(hours)],
                         capture_output=True, text=True, check=True).stdout.split()
    bad = 0
    for k in range(days):
        c, p = int(out[k]), index_of(first + k, mask, hours)
        if c != p:
            bad += 1
            name = lambda i: F.FEASTS[i]["words"][0] if i >= 0 else "-"
            print(f"{date.fromordinal(first + k)}: watch {name(c)}, prototype {name(p)}")
    print(f"{days} days, {sum(1 for v in out if v != '-1')} feast days: " + ("all agree" if not bad else f"{bad} disagree"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
