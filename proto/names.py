"""The place's names for the ring as ladders of ever shorter forms, the forms joined by "|", longest first: the same
rules as the phone's (watchface/src/pkjs/names.js, which explains them); tools/check_names.py holds the two to the
same answers. The face shows the longest form that fits the room beside MIDNIGHT."""
import re
import unicodedata

CITY_CAP, REGION_CAP = 39, 27

GENERIC = {"SAINT": "ST.", "SAINTE": "STE.", "FORT": "FT.", "MOUNT": "MT.", "PORT": "PT.", "POINT": "PT.",
           "NORTH": "N.", "SOUTH": "S.", "EAST": "E.", "WEST": "W.", "SANTA": "STA."}


def engrave(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if not ("̀" <= c <= "ͯ"))
    s = re.sub(r"[^A-Z0-9 .'-]", "", s.upper())
    return re.sub(r"\s+", " ", s).strip(" ")


def vowel(c):
    return c in "AEIOUY"


def cuts(w):
    out, i = [], 0
    while i < len(w):
        while i < len(w) and not vowel(w[i]):
            i += 1
        while i < len(w) and vowel(w[i]):
            i += 1
        j = i
        while j < len(w) and not vowel(w[j]):
            j += 1
        if j >= len(w):
            break
        for k in ([i + 1, j - 1] if j - i >= 3 else [j]):
            if k >= 4 and len(w) - k >= 3 and k not in out:
                out.append(k)
        i = j
    return sorted(out)


def initial(w):
    return w[0] + "."


def join(forms, cap):
    seen, out = set(), []
    for f in forms:
        if f and f not in seen and (not out or len(f) < len(out[-1])):
            seen.add(f)
            out.append(f)
    if out and len(out[0]) > cap:
        out[0] = out[0][:cap].rstrip(" ")
    while len(out) > 1 and len("|".join(out)) > cap:
        out.pop(0)
    return "|".join(out)


def city_ladder(name):
    name = engrave(name).replace("|", "")
    if not name:
        return ""
    words = name.split(" ")
    forms = [name]
    gen = [GENERIC.get(w, w) for w in words] if len(words) > 1 else list(words)
    forms.append(" ".join(gen))
    for k in range(1, len(gen)):
        forms.append(" ".join([w if w.endswith(".") else initial(w) for w in gen[:k]] + gen[k:]))
    lead = [w if w.endswith(".") else initial(w) for w in gen[:-1]]
    last = gen[-1]
    if "-" in last:
        last = last.split("-")[0]
        forms.append(" ".join(lead + [last]))
    if not last.endswith("."):
        for c in reversed(cuts(last)):
            forms.append(" ".join(lead + [last[:c] + "."]))
    if len(words) > 1:
        forms.append("".join(initial(w) for w in words))
    return join(forms, CITY_CAP)


def _regions():
    """The states and provinces from the phone's own table (names.js), so the two cannot drift."""
    from pathlib import Path
    import json
    text = (Path(__file__).resolve().parents[1] / "watchface" / "src" / "pkjs" / "names.js").read_text()
    block = text[text.index("var REGIONS = {") + len("var REGIONS = "): text.index("};", text.index("var REGIONS")) + 1]
    short = text[text.index("var SHORT = {") + len("var SHORT = "): text.index("};", text.index("var SHORT")) + 1]
    def js(o):
        o = re.sub(r"'([^']*)'", lambda m: json.dumps(m.group(1)), o)
        return json.loads(re.sub(r"([{,]\s*)([A-Z]+)(\s*:)", r'\1"\2"\3', o))
    return js(block), js(short)


REGIONS, SHORT = _regions()


def region_ladder(code, region, country):
    code = str(code or "").upper()
    states, r = REGIONS.get(code), engrave(region)
    if states:
        sub = re.sub(r"^[A-Z]{2}-", "", r)
        for name, forms in states.items():
            if name == r or forms[1] == sub:
                return join([name] + forms, REGION_CAP)
    c = engrave(re.split(r"[(,]", str(country or ""))[0]) or engrave(SHORT.get(code, ""))
    if not c:
        return ""
    forms = city_ladder(c).split("|")
    if re.fullmatch(r"[A-Z]{2}", code) and len(forms[-1]) > 2:
        forms.append(code)
    return join(forms, REGION_CAP)
