"""The place-name ladders: the phone's rules (watchface/src/pkjs/names.js, run in node) and the prototype's
(proto/names.py) give the same forms for a spread of cities and countries, US states, provinces and the like; and
the forms behave (each shorter than the last, engraved, within the watch's buffers). Prints any that differ.

    python3 tools/check_names.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "proto"))
import names                       # noqa: E402

CITIES = ["Norfolk", "New York", "Virginia Beach", "Philadelphia", "Baltimore", "Pittsburgh", "Jacksonville",
          "Albuquerque", "Sacramento", "Indianapolis", "San Francisco", "Los Angeles", "Salt Lake City", "Fort Worth",
          "Saint Louis", "St. Petersburg", "Washington", "Manchester", "Birmingham", "Edinburgh", "London", "Paris",
          "Amsterdam", "Copenhagen", "Reykjavík", "Stockholm", "Montréal", "Melbourne", "Johannesburg", "Singapore",
          "Buenos Aires", "Rio de Janeiro", "Mexico City", "Christchurch", "Vladivostok", "Zürich", "Tokyo",
          "Stratford-upon-Avon", "Winston-Salem", "Coeur d'Alene", "São Paulo", "Kraków", "Llanfairpwllgwyngyll",
          "Ho Chi Minh City", "Port Moresby", "Mount Isa", "Sainte-Foy", "Ōsaka", "", "A"]
REGIONS = [("US", "Virginia", "United States of America"), ("US", "US-NY", ""), ("US", "California", ""),
           ("US", "District of Columbia", ""), ("US", "Ohio", ""), ("CA", "Ontario", "Canada"), ("CA", "CA-QC", ""),
           ("AU", "New South Wales", "Australia"), ("AU", "Western Australia", ""), ("GB", "Scotland", "United Kingdom"),
           ("GB", "", "United Kingdom"), ("CH", "", "Switzerland"), ("NL", "", "Netherlands"), ("DE", "", "Germany"),
           ("ZA", "", "South Africa"), ("NZ", "", "New Zealand"), ("FR", "", "France"), ("GE", "", "Georgia"),
           ("BD", "", "Bangladesh"), ("BR", "São Paulo", "Brazil"), ("", "", "Typed By Hand"), ("", "", "")]


def main():
    js = ("const n = require(%s); const out = {cities: %s.map(n.cityLadder), regions: %s.map(r => n.regionLadder(...r))};"
          " console.log(JSON.stringify(out));" % (json.dumps(str(ROOT / "watchface/src/pkjs/names.js")),
                                                   json.dumps(CITIES), json.dumps(REGIONS)))
    got = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
    bad = 0
    for name, j in zip(CITIES, got["cities"]):
        p = names.city_ladder(name)
        if p != j:
            bad += 1
            print(f"differs: {name!r}: js {j!r}, py {p!r}")
    for r, j in zip(REGIONS, got["regions"]):
        p = names.region_ladder(*r)
        if p != j:
            bad += 1
            print(f"differs: {r!r}: js {j!r}, py {p!r}")
    for lad, cap in [(x, names.CITY_CAP) for x in got["cities"]] + [(x, names.REGION_CAP) for x in got["regions"]]:
        forms = lad.split("|") if lad else []
        ok = len(lad) <= cap and all(len(b) < len(a) for a, b in zip(forms, forms[1:])) and \
            all(f == names.engrave(f) and f for f in forms)
        if not ok:
            bad += 1
            print(f"misformed: {lad!r}")
    print(f"{len(CITIES)} cities, {len(REGIONS)} regions: {'the same' if not bad else f'{bad} problems'}")
    for name, j in list(zip(CITIES, got["cities"]))[:12]:
        print(f"  {name:18} {j}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
