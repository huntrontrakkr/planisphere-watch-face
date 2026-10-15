"""The weather, read the way the almanacs and the instruments of their day read it: the temperature as a
thermometer's figures with the degree sign (Cavendish's, 1776), the barometer's words, and the sky's state
in Howard's clouds (1803): cumulus heaps, stratus sheets, cirrus hair.

On the watch the phone fetches it (Open-Meteo, which needs no key) and sends these few numbers; here
`fetch` does the same, and SAMPLES holds named states for the plates and films.

    uv run python proto/weather.py            # the weather at New York now
"""
import json
import math
import urllib.request
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Weather:
    temp: float                 # degrees Celsius, at two metres
    code: int                   # the WMO weather code, as Open-Meteo gives it
    low: float = 0.0            # cloud cover by height, 0..1: low (stratus, cumulus), middle, high (cirrus)
    mid: float = 0.0
    high: float = 0.0
    wind: float = 0.0           # km/h at ten metres
    wind_from: float = 270.0    # where the wind comes from, degrees east of north
    pressure: float = 1013.0    # hPa, reduced to the sea, as a barometer is set
    snow_depth: float = 0.0     # metres of snow lying
    visibility: float = 30000.0  # metres


SAMPLES = {
    "fair": Weather(16, 1, low=0.18, high=0.05, wind=9, wind_from=250, pressure=1026),
    "cloudy": Weather(12, 2, low=0.5, mid=0.25, high=0.2, wind=17, wind_from=230, pressure=1011),
    "overcast": Weather(9, 3, low=0.95, mid=0.7, high=0.3, wind=14, wind_from=60, pressure=1004),
    "rain": Weather(11, 63, low=0.9, mid=0.85, high=0.5, wind=26, wind_from=110, pressure=994),
    "snow": Weather(-2, 73, low=0.9, mid=0.6, high=0.2, wind=12, wind_from=20, pressure=1003, snow_depth=0.08,
                    visibility=2500),
    "fog": Weather(7, 45, low=1.0, wind=3, wind_from=180, pressure=1020, visibility=300),
    "thunder": Weather(27, 95, low=0.7, mid=0.7, high=0.6, wind=31, wind_from=270, pressure=999),
    "cirrus": Weather(14, 1, high=0.75, wind=11, wind_from=200, pressure=1017),
    "frost": Weather(-7, 0, wind=4, wind_from=330, pressure=1034, snow_depth=0.12),
    "gale": Weather(8, 3, low=0.8, mid=0.4, wind=68, wind_from=290, pressure=972),
}


# the barometer's dial, as the banjo barometers engrave it, at whole and half inches of mercury
BAROMETER = [(28.0, "STORMY"), (28.5, "MUCH RAIN"), (29.0, "RAIN"), (29.5, "CHANGE"), (30.0, "FAIR"),
             (30.5, "SET FAIR"), (31.0, "VERY DRY")]
# and the thermometer's scale, as Nairne and his peers engraved its marks (degrees Fahrenheit)
THERMOMETER = [(0, "SEVERE FROST"), (32, "FREEZING"), (55, "TEMPERATE"), (76, "SUMMER HEAT"), (98, "BLOOD HEAT")]


def barometer_word(w):
    """The word the barometer's hand points nearest."""
    inches = w.pressure / 33.8639
    return min(BAROMETER, key=lambda b: abs(b[0] - inches))[1]


def thermometer_word(w):
    """The word of the thermometer's mark at or below the temperature."""
    f = w.temp * 9 / 5 + 32
    word = THERMOMETER[0][1]
    for at, name in THERMOMETER:
        if f >= at - 1e-9:
            word = name
    return word


def degrees(w, fahrenheit=False):
    """The temperature in whole degrees, on the chosen scale."""
    return int(round(w.temp * 9 / 5 + 32 if fahrenheit else w.temp))


@dataclass(frozen=True)
class Sky:
    """What the weather puts in the sky and on the land, for the faces to draw."""
    falls: str = ""             # "", "drizzle", "rain", "snow", "hail"
    heavy: int = 0              # 1 light, 2 moderate, 3 heavy
    thunder: bool = False
    fog: bool = False
    cumulus: float = 0.0        # how much of the sky each of Howard's clouds covers
    stratus: float = 0.0
    cirrus: float = 0.0
    haze: float = 0.0           # magnitudes the faintest stars lose to the air (thin cloud, mist)
    halo: bool = False          # thin high cloud: a ring round the Moon (or Sun) at 22 degrees
    snow_lying: bool = False
    frost: bool = False
    smoke: bool = False         # cold enough for fires: smoke from the chimneys
    wind: float = 0.0           # km/h
    wind_from: float = 270.0
    temp: float = 15.0          # degrees Celsius


FALLS = {51: ("drizzle", 1), 53: ("drizzle", 2), 55: ("drizzle", 3), 56: ("drizzle", 1), 57: ("drizzle", 2),
         61: ("rain", 1), 63: ("rain", 2), 65: ("rain", 3), 66: ("rain", 1), 67: ("rain", 3),
         71: ("snow", 1), 73: ("snow", 2), 75: ("snow", 3), 77: ("snow", 1),
         80: ("rain", 1), 81: ("rain", 2), 82: ("rain", 3), 85: ("snow", 1), 86: ("snow", 3),
         95: ("rain", 2), 96: ("hail", 2), 99: ("hail", 3)}


def sky_of(w):
    """The weather as the sky shows it. Low cloud heaps into cumulus while it is broken and spreads into a
    stratus sheet as it closes (or when rain falls from it); high cloud is cirrus, thin enough to see the
    brightest stars through, and when it covers much of the sky it rings the Moon with a halo."""
    falls, heavy = FALLS.get(w.code, ("", 0))
    fog = w.code in (45, 48) or w.visibility < 1000
    low = max(w.low, w.mid * 0.6)                            # middle cloud drawn as the low (both hide stars)
    sheet = smooth01(0.55, 0.9, low) if not falls else 1.0
    haze = 1.6 * w.high + (2.5 if fog else 1.2 if w.visibility < 5000 else 0.0)
    clear = 0.0 if fog else 1.0                              # in fog no cloud is seen, only the fog
    return Sky(falls=falls, heavy=heavy, thunder=w.code >= 95, fog=fog,
               cumulus=low * (1 - sheet) * clear, stratus=low * sheet * clear, cirrus=w.high * clear, haze=haze,
               halo=w.high >= 0.45 and low < 0.5 and not falls,
               snow_lying=w.snow_depth > 0.005 or falls == "snow", frost=w.temp <= 0.0,
               smoke=w.temp < 12.0, wind=w.wind, wind_from=w.wind_from, temp=w.temp)


def smooth01(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


CURRENT = ("temperature_2m,weather_code,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,"
           "wind_direction_10m,pressure_msl,snow_depth,visibility")


def fetch(lat, lon, timeout=10):
    """The weather now at (lat, lon) from Open-Meteo, as the phone would fetch it."""
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat:.3f}&longitude={lon:.3f}&current={CURRENT}"
           "&wind_speed_unit=kmh")
    with urllib.request.urlopen(url, timeout=timeout) as r:
        c = json.load(r)["current"]
    return Weather(temp=c["temperature_2m"], code=int(c["weather_code"]), low=c["cloud_cover_low"] / 100,
                   mid=c["cloud_cover_mid"] / 100, high=c["cloud_cover_high"] / 100, wind=c["wind_speed_10m"],
                   wind_from=c["wind_direction_10m"], pressure=c["pressure_msl"], snow_depth=c.get("snow_depth") or 0.0,
                   visibility=c.get("visibility") or 30000.0)


if __name__ == "__main__":
    w = fetch(40.71, -74.01)
    print(w)
    print(degrees(w, True), "°F", barometer_word(w), thermometer_word(w))
    print(sky_of(w))
