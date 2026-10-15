"""The calendar's feasts: when each falls, by the rule its own calendar keeps. Written for the watch's C to follow:
whole numbers, and the Sun and the Moon from the face's own ephemeris where a feast is set by them.

Dates are proleptic Gregorian ordinals (Python's date.toordinal(): 1 January of year 1 is 1).

    uv run python proto/feasts.py          # checks against the published dates
"""
from datetime import date, datetime, timedelta, timezone

import astro
import lunar


def _sun_lon(t):
    """The Sun's apparent longitude at a moment (degrees), from the face's Meeus Sun."""
    return lunar.sun(astro.julian(t) + lunar.delta_t(t.year) / 86400)[0]


def _moon_lon(t):
    return lunar.moon(astro.julian(t) + lunar.delta_t(t.year) / 86400)[0]

# ---- the Christian year: Easter, by the computus, and the days hung on it ----------------------------------------


def easter(year):
    """Easter Sunday in the Gregorian calendar (the anonymous Gregorian computus, as Meeus gives it)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = (h + l_ - 7 * m + 114) % 31 + 1
    return date(year, month, day).toordinal()


def julian_easter(year):
    """Easter in the Julian calendar (the Orthodox churches'), as a Gregorian date (Meeus's Julian computus)."""
    a, b, c = year % 4, year % 7, year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month, day = (d + e + 114) // 31, (d + e + 114) % 31 + 1
    # the Julian date to the Gregorian: the calendars drift a day apart in each century year not divisible by 400
    return date(year, month, day).toordinal() + (year // 100 - year // 400 - 2)


def nth_weekday(year, month, weekday, n):
    """The n-th `weekday` (0 Monday) of a month; n = -1 the last."""
    if n > 0:
        first = date(year, month, 1)
        return first.toordinal() + (weekday - first.weekday()) % 7 + 7 * (n - 1)
    last = date(year + month // 12, month % 12 + 1, 1).toordinal() - 1
    return last - (date.fromordinal(last).weekday() - weekday) % 7


def weekday_after(ordinal, weekday):
    """The first `weekday` after (not on) a day."""
    return ordinal + 1 + (weekday - date.fromordinal(ordinal + 1).weekday()) % 7


def advent_sunday(year):
    """The fourth Sunday before Christmas."""
    christmas = date(year, 12, 25).toordinal()
    return christmas - ((date.fromordinal(christmas).weekday() + 1) % 7 or 7) - 21


# ---- the Hebrew calendar, by its arithmetic (after Reingold and Dershowitz, Calendrical Calculations) -------------

HEBREW_EPOCH = -1373427              # 1 Tishri AM 1, as a proleptic Gregorian ordinal


def _hebrew_elapsed(y):
    months = (235 * y - 234) // 19
    parts = 12084 + 13753 * months
    day = 29 * months + parts // 25920
    return day + 1 if (3 * (day + 1)) % 7 < 3 else day


def _hebrew_delay(y):
    ny0, ny1, ny2 = _hebrew_elapsed(y - 1), _hebrew_elapsed(y), _hebrew_elapsed(y + 1)
    return 2 if ny2 - ny1 == 356 else 1 if ny1 - ny0 == 382 else 0


def hebrew_new_year(y):
    """1 Tishri of Hebrew year y."""
    return HEBREW_EPOCH + _hebrew_elapsed(y) + _hebrew_delay(y)


def hebrew_leap(y):
    return (7 * y + 1) % 19 < 7


def hebrew_date(y, month, day):
    """A Hebrew date (months numbered from Nisan as 1, Tishri 7; Adar II 13 in leap years) as an ordinal."""
    length = hebrew_new_year(y + 1) - hebrew_new_year(y)
    long_heshvan, short_kislev = length % 10 == 5, length % 10 == 3

    def month_days(m):
        if m in (2, 4, 6, 10, 13):
            return 29
        if m == 12 and not hebrew_leap(y):
            return 29
        if m == 8 and not long_heshvan:
            return 29
        if m == 9 and short_kislev:
            return 29
        return 30
    last = 13 if hebrew_leap(y) else 12
    order = list(range(7, last + 1)) + list(range(1, 7))      # the year runs from Tishri
    at = hebrew_new_year(y)
    for m in order:
        if m == month:
            return at + day - 1
        at += month_days(m)
    raise ValueError(month)


def hebrew_year_of(year):
    """The Hebrew year whose Tishri falls in the autumn of Gregorian `year`."""
    return year + 3761


# ---- the Sun and the Moon: the seasons' turning points, new and full moons ---------------------------------------


def sun_longitude_day(year, target, offset_hours=0):
    """The local date (ordinal) on which the Sun's longitude passes `target` degrees, in the given year."""
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    prev = None
    for d in range(0, 367):
        t = start + timedelta(days=d)
        lon = _sun_lon(t)
        if prev is not None and ((prev - target) % 360) > 300 and ((lon - target) % 360) < 60:
            # crossed during the last day: find the hour
            lo, hi = t - timedelta(days=1), t
            for _ in range(20):
                mid = lo + (hi - lo) / 2
                ml = _sun_lon(mid)
                if ((ml - target) % 360) > 180:
                    lo = mid
                else:
                    hi = mid
            return (hi + timedelta(hours=offset_hours)).date().toordinal()
        prev = lon
    return None


def moon_phase_days(start_ordinal, end_ordinal, phase, offset_hours=0, shift_hours=0):
    """The local dates of the new (phase 0) or full (phase 180) moons between two ordinals (each moment moved
    `shift_hours` first)."""
    out = []
    t = datetime.combine(date.fromordinal(start_ordinal), datetime.min.time(), timezone.utc) - timedelta(hours=offset_hours)
    end = datetime.combine(date.fromordinal(end_ordinal + 1), datetime.min.time(), timezone.utc) - timedelta(hours=offset_hours)

    def elong(tt):
        return (_moon_lon(tt) - _sun_lon(tt) - phase) % 360
    prev = elong(t)
    step = timedelta(hours=6)
    while t < end:
        t2 = t + step
        e2 = elong(t2)
        if prev > 300 and e2 < 60:
            lo, hi = t, t2
            for _ in range(20):
                mid = lo + (hi - lo) / 2
                if elong(mid) > 180:
                    lo = mid
                else:
                    hi = mid
            out.append((hi + timedelta(hours=offset_hours + shift_hours)).date().toordinal())
        t, prev = t2, e2
    return out


def chinese_new_year(year):
    """The first day of the first month: the first Beijing date of the year whose Chinese date is 1/1."""
    o = date(year, 1, 20).toordinal()
    while chinese_from_ordinal(o)[:3] != (1, False, 1):
        o += 1
    return o


def mid_autumn(year):
    o = date(year, 9, 5).toordinal()
    while chinese_from_ordinal(o)[:3] != (8, False, 15):
        o += 1
    return o


# ---- converters: a day's date in each calendar (as the watch asks: "is today one of its feasts?") ----------------
# Moments are seconds since 1970 (UT); local dates are Gregorian ordinals of a zone's clock.

SYNODIC = 29.530588853 * 86400               # the mean lunation, seconds
NEW_MOON_2000 = 947182440                    # 2000-01-06 18:14 UTC (Meeus 49)


def lons(utc):
    """The Sun's and the Moon's apparent longitudes (degrees, nutation included) at a moment, from the face's own
    ephemeris, in dynamical time as the watch keeps it (plan_astro.c tt_of: whole seconds of a yearly delta T)."""
    t = utc - 946728000
    tt = t + int(69.2 + 0.25 * (int(2000 + t / 31557600) - 2025) + 0.5)
    jde = 2451545.0 + tt / 86400
    dpsi, _ = lunar.nutation(jde)
    return (lunar.sun(jde)[0] + dpsi) % 360, (lunar.moon(jde)[0] + dpsi) % 360


def new_moon_near(utc):
    """The new moon nearest a moment: the mean lunation's, then a few steps along the Moon's elongation."""
    t = NEW_MOON_2000 + round((utc - NEW_MOON_2000) / SYNODIC) * SYNODIC
    for _ in range(4):
        sl, ml = lons(t)
        t -= ((ml - sl + 180) % 360 - 180) / 12.190749 * 86400
    return t


def elongation_moment(near, target):
    """The moment near `near` at which the Moon stands `target` degrees east of the Sun."""
    t = near
    for _ in range(5):
        sl, ml = lons(t)
        t -= ((ml - sl - target + 180) % 360 - 180) / 12.190749 * 86400
    return t


def sun_moment(near, target):
    """The moment near `near` at which the Sun's longitude is `target` degrees."""
    t = near
    for _ in range(5):
        sl, _ = lons(t)
        t -= ((sl - target + 180) % 360 - 180) / 0.98564736 * 86400
    return t


def zone_date(utc, hours):
    return int((utc + hours * 3600) // 86400) + 719163


def zone_midnight(ordinal, hours):
    return (ordinal - 719163) * 86400 - hours * 3600


# the Chinese calendar, after Reingold and Dershowitz (Calendrical Calculations, ch. 19), on Beijing's dates
BJ = 8


def _cn_new_moon_on_or_after(o):
    t = new_moon_near(zone_midnight(o, BJ))
    if zone_date(t, BJ) < o:
        t = new_moon_near(t + SYNODIC)
    return zone_date(t, BJ)


def _cn_new_moon_before(o):
    t = new_moon_near(zone_midnight(o, BJ))
    if zone_date(t, BJ) >= o:
        t = new_moon_near(t - SYNODIC)
    return zone_date(t, BJ)


def _cn_major_term(o):
    sl, _ = lons(zone_midnight(o, BJ))
    return (2 + int(sl // 30) - 1) % 12 + 1


def _cn_no_major_term(o):
    return _cn_major_term(o) == _cn_major_term(_cn_new_moon_on_or_after(o + 1))


def _cn_prior_leap(m_first, m):
    while m >= m_first:
        if _cn_no_major_term(m):
            return True
        m = _cn_new_moon_before(m)
    return False


def _cn_solstice_on_or_before(o):
    """The Beijing date of the December solstice on or before a day."""
    t = sun_moment(zone_midnight(o, BJ), 270)
    if zone_date(t, BJ) > o:
        t = sun_moment(t - 365.2422 * 86400, 270)
    elif zone_date(t, BJ) + 366 <= o:
        t = sun_moment(t + 365.2422 * 86400, 270)
    return zone_date(t, BJ)


def chinese_from_ordinal(o):
    """(month, leap, day) of a Beijing date in the Chinese calendar."""
    s1 = _cn_solstice_on_or_before(o)
    s2 = _cn_solstice_on_or_before(s1 + 370)
    m12 = _cn_new_moon_on_or_after(s1 + 1)
    next_m11 = _cn_new_moon_before(s2 + 1)
    m = _cn_new_moon_before(o + 1)
    leap_year = round((next_m11 - m12) / 29.530588853) == 12
    month = (round((m - m12) / 29.530588853) - (1 if leap_year and _cn_prior_leap(m12, m) else 0) - 1) % 12 + 1
    leap = leap_year and _cn_no_major_term(m) and not _cn_prior_leap(m12, _cn_new_moon_before(m))
    return month, leap, o - m + 1


# the Islamic calendar by its arithmetic (the tabular calendar: within a day or two of the crescent's sighting)
ISLAMIC_EPOCH = 227015                        # 16 July 622 (Julian), as a proleptic Gregorian ordinal


def islamic_ordinal(y, m, d):
    return d + 29 * (m - 1) + (6 * m - 1) // 11 + (y - 1) * 354 + (3 + 11 * y) // 30 + ISLAMIC_EPOCH - 1


def islamic_from_ordinal(o):
    y = (30 * (o - ISLAMIC_EPOCH) + 10646) // 10631
    m = min(12, (11 * (o - islamic_ordinal(y, 1, 1)) + 330) // 325)
    return y, m, o - islamic_ordinal(y, m, 1) + 1


def hebrew_from_ordinal(o):
    """(year, month, day) of a date in the Hebrew calendar (months from Nisan as 1; Tishri 7; Adar II 13)."""
    y = (o - HEBREW_EPOCH) * 98496 // 35975351 + 1
    while hebrew_new_year(y + 1) <= o:
        y += 1
    while hebrew_new_year(y) > o:
        y -= 1
    last = 13 if hebrew_leap(y) else 12
    for m in list(range(7, last + 1)) + list(range(1, 7)):
        start = hebrew_date(y, m, 1)
        nxt = hebrew_date(y, m % last + 1, 1) if m != 6 else hebrew_new_year(y + 1)
        if start <= o < nxt:
            return y, m, o - start + 1
    raise ValueError(o)


# the Hindu calendar's Diwali (the holidays research's rule): the new moon that ends the amanta month holding the
# Sun's entry into sidereal Libra (Lahiri's ayanamsa); the festival is the IST evening whose pradosh (Delhi's sunset
# and 144 minutes after) the amavasya (elongation 348 to 360 degrees) overlaps; of two, the later if the amavasya
# runs 24 minutes or more into it
IST = 5.5
DELHI = (28.6139, 77.2090)


def ayanamsa(year):
    return 23.857 + 50.29 / 3600 * (year - 2000)


def sunset(ordinal, lat, lon, hours):
    """A place's sunset (the Sun's top at the horizon, refracted) on a local date: an hour angle from the noon Sun."""
    noon = zone_midnight(ordinal, hours) + (12 - lon / 15 + hours) * 3600
    for _ in range(2):
        jd = noon / 86400 + 2440587.5
        ra, dec = astro.positions(datetime.fromtimestamp(noon, timezone.utc))["sun"]
        gmst = astro.sidereal(datetime.fromtimestamp(noon, timezone.utc), lon)
        h_noon = ((gmst - ra + 180) % 360) - 180            # the Sun's hour angle at our guess of noon
        noon -= h_noon / 15.04107 * 3600
    import math
    D = math.radians
    cosh = (math.sin(D(-0.833)) - math.sin(D(lat)) * math.sin(D(dec))) / (math.cos(D(lat)) * math.cos(D(dec)))
    return noon + math.degrees(math.acos(max(-1, min(1, cosh)))) / 15.04107 * 3600


def diwali(year):
    sid = 180 + ayanamsa(year)
    ingress = sun_moment(zone_midnight(date(year, 10, 17).toordinal(), 0), sid)
    end = new_moon_near(ingress)
    if end < ingress:
        end = new_moon_near(end + SYNODIC)
    start = elongation_moment(end - 0.98 * 86400, 348)
    days = []
    for d in (zone_date(end, IST) - 1, zone_date(end, IST)):
        a = sunset(d, *DELHI, IST)
        overlap = min(a + 144 * 60, end) - max(a, start)
        if overlap > 0:
            days.append((d, overlap))
    if len(days) == 2:
        return days[1][0] if days[1][1] >= 24 * 60 else days[0][0]
    return days[0][0] if days else zone_date(end, IST)


# ---- the calendars the owner may keep, and their days ---------------------------------------------------------
# Each calendar is a switch on the settings page (bit n of CALENDARS, in this order). Each day: its calendar, its rule,
# its words for the almanac's line (the longest that fits is used), the needlework emblem set beside the time, what it
# brings (lights in the windows, fires on the hills, a fireworks display at the evening's hours, "midnight" for one at
# midnight too), and its rank (1 a great feast, 3 a small one: the greater wins a shared day).
#
# Rules: ("fixed", month, day[, days]), ("easter", offset), ("orthodox", offset), ("nth", month, weekday, n),
# ("after", month, day, weekday), ("window", month, day, weekday), ("advent", offset), ("sun", longitude, zone),
# ("sidereal", longitude, zone), ("hebrew", month, day[, days]), ("chinese", month, day), ("islamic", month, day),
# ("diwali",). Weekdays 0 Monday; zones "local", "bj" (Beijing), "ist" (India).

CALENDARS = [
    ("sky", "The sky’s year", "The solstices and the equinoxes, named as the seasons turn where you are."),
    ("christian", "The Christian year", "Christmas and Easter and the feasts between: Candlemas, Lady Day, "
                                        "Whitsun, Michaelmas, All Saints, Advent."),
    ("eastern", "The Eastern churches", "Christmas and Pascha as the Orthodox keep them, and Theophany."),
    ("english", "Old English customs", "The days the old almanacs kept and the villages have mostly let go: "
                                       "Plough Monday, Hocktide, Oak Apple Day, Lammas, Martinmas."),
    ("fire", "The fire festivals", "The Celtic and Norse turning points, with fires on the hills: Imbolc, "
                                   "Beltane, Midsummer, Lughnasadh, Samhain, Yule."),
    ("rome", "Ancient Rome", "The Kalends of January, the Lupercalia, the Floralia, the Saturnalia."),
    ("us", "The United States", "New Year, St Valentine’s, Independence Day with its fireworks, Halloween, "
                                "Thanksgiving."),
    ("britain", "Britain and Ireland", "Burns Night, the patron saints’ days, Bonfire Night’s fires and fireworks, "
                                       "Hogmanay."),
    ("hebrew", "The Hebrew calendar", "Rosh Hashanah, Yom Kippur, Sukkot, Hanukkah’s eight nights, Purim, "
                                      "Passover, Shavuot."),
    ("chinese", "The Chinese calendar", "The Spring Festival, the Lantern Festival, Qingming, the Dragon Boat, "
                                        "Qixi, Mid-Autumn."),
    ("islamic", "The Islamic calendar", "The new year, Ramadan, the two Eids, the Mawlid; by the calendar’s "
                                        "arithmetic, so within a day of the crescent’s sighting."),
    ("hindu", "The Hindu calendar", "Makar Sankranti and Diwali’s lamps."),
]
CAL = {k: i for i, (k, _, _) in enumerate(CALENDARS)}

FEASTS = [
    # the sky's year (named for the season where the watch is)
    dict(cal="sky", rule=("sun", 0, "local"), words=("VERNAL EQUINOX", "EQUINOX"), south=("AUTUMN EQUINOX", "EQUINOX"),
         emblem="sun wheel", rank=3),
    dict(cal="sky", rule=("sun", 90, "local"), words=("SUMMER SOLSTICE", "SOLSTICE"),
         south=("WINTER SOLSTICE", "SOLSTICE"), emblem="sun wheel", rank=3),
    dict(cal="sky", rule=("sun", 180, "local"), words=("AUTUMN EQUINOX", "EQUINOX"), south=("VERNAL EQUINOX", "EQUINOX"),
         emblem="sun wheel", rank=3),
    dict(cal="sky", rule=("sun", 270, "local"), words=("WINTER SOLSTICE", "SOLSTICE"),
         south=("SUMMER SOLSTICE", "SOLSTICE"), emblem="sun wheel", rank=3),
    # the Christian year
    dict(cal="christian", rule=("fixed", 1, 6), words=("EPIPHANY", "TWELFTH DAY"), emblem="star6", rank=2),
    dict(cal="christian", rule=("fixed", 2, 2), words=("CANDLEMAS",), emblem="candle", brings=("lights",), rank=2),
    dict(cal="christian", rule=("easter", -47), words=("SHROVE TUESDAY", "SHROVETIDE"), emblem="pancake", rank=2),
    dict(cal="christian", rule=("easter", -46), words=("ASH WEDNESDAY",), emblem=None, rank=2),
    dict(cal="christian", rule=("fixed", 3, 25), words=("LADY DAY", "ANNUNCIATION"), emblem="heart", rank=2),
    dict(cal="christian", rule=("easter", -7), words=("PALM SUNDAY",), emblem="willow", rank=2),
    dict(cal="christian", rule=("easter", -2), words=("GOOD FRIDAY",), emblem="cross", rank=1),
    dict(cal="christian", rule=("easter", 0), words=("EASTER DAY", "EASTER"), emblem="lamb", rank=1),
    dict(cal="christian", rule=("easter", 39), words=("ASCENSION DAY", "ASCENSION"), emblem="cloud", rank=2),
    dict(cal="christian", rule=("easter", 49), words=("WHITSUNDAY", "PENTECOST"), emblem="dove", rank=2),
    dict(cal="christian", rule=("fixed", 9, 29), words=("MICHAELMAS",), emblem="scales", rank=2),
    dict(cal="christian", rule=("fixed", 11, 1), words=("ALL SAINTS",), emblem="church", rank=2),
    dict(cal="christian", rule=("fixed", 11, 2), words=("ALL SOULS",), emblem="candle", rank=3),
    dict(cal="christian", rule=("advent", 0), words=("ADVENT SUNDAY", "ADVENT"), emblem="wreath", rank=2),
    dict(cal="christian", rule=("fixed", 12, 24), words=("CHRISTMAS EVE",), emblem="holly", brings=("lights",), rank=1),
    dict(cal="christian", rule=("fixed", 12, 25), words=("CHRISTMAS DAY", "CHRISTMAS"), emblem="horn",
         brings=("lights",), rank=1),
    # the Eastern churches (the Julian dates as they fall on the civil calendar this century)
    dict(cal="eastern", rule=("fixed", 1, 7), words=("ORTHODOX CHRISTMAS", "CHRISTMAS"), emblem="star6",
         brings=("lights",), rank=1),
    dict(cal="eastern", rule=("fixed", 1, 19), words=("THEOPHANY",), emblem="waves cross", rank=2),
    dict(cal="eastern", rule=("orthodox", -2), words=("GREAT FRIDAY",), emblem="cross", rank=1),
    dict(cal="eastern", rule=("orthodox", 0), words=("PASCHA", "PASCHA"), emblem="egg", brings=("lights",), rank=1),
    # old English customs, mostly let go
    dict(cal="english", rule=("fixed", 1, 5), words=("TWELFTH NIGHT",), emblem="wassail bowl", brings=("lights",), rank=2),
    dict(cal="english", rule=("fixed", 1, 7), words=("ST DISTAFF'S DAY", "DISTAFF DAY"), emblem="distaff", rank=3),
    dict(cal="english", rule=("after", 1, 6, 0), words=("PLOUGH MONDAY",), emblem="plough", rank=2),
    dict(cal="english", rule=("easter", -48), words=("COLLOP MONDAY",), emblem="pancake", rank=3),
    dict(cal="english", rule=("easter", -21), words=("MOTHERING SUNDAY",), emblem="rose", rank=2),
    dict(cal="english", rule=("easter", 15), words=("HOCK MONDAY", "HOCKTIDE"), emblem=None, rank=3),
    dict(cal="english", rule=("easter", 16), words=("HOCK TUESDAY", "HOCKTIDE"), emblem=None, rank=3),
    dict(cal="english", rule=("easter", 36), words=("BEATING THE BOUNDS", "ROGATIONTIDE"), emblem="willow",
         rank=3),
    dict(cal="english", rule=("fixed", 5, 1), words=("MAY DAY",), emblem="maypole", rank=2),
    dict(cal="english", rule=("fixed", 5, 29), words=("OAK APPLE DAY",), emblem="oak apple", rank=2),
    dict(cal="english", rule=("fixed", 6, 23), words=("ST JOHN'S EVE", "MIDSUMMER EVE"), emblem="fire wheel",
         brings=("bonfires",), rank=2),
    dict(cal="english", rule=("fixed", 8, 1), words=("LAMMAS", "LOAF MASS"), emblem="loaf", rank=2),
    dict(cal="english", rule=("fixed", 11, 11), words=("MARTINMAS",), emblem="goose", rank=2),
    dict(cal="english", rule=("fixed", 11, 25), words=("ST CATHERINE'S DAY", "CATTERN DAY"), emblem="wheel",
         rank=3),
    dict(cal="english", rule=("fixed", 12, 28), words=("CHILDERMAS",), emblem=None, rank=3),
    # the fire festivals
    dict(cal="fire", rule=("fixed", 2, 1), words=("IMBOLC",), emblem="brigid cross", brings=("lights",), rank=2),
    dict(cal="fire", rule=("fixed", 4, 30), words=("BELTANE EVE", "BELTANE"), emblem="flames",
         brings=("bonfires",), rank=2),
    dict(cal="fire", rule=("window", 6, 19, 4), words=("MIDSUMMER EVE", "MIDSOMMAR"), emblem="midsummer pole",
         brings=("bonfires",), rank=2),
    dict(cal="fire", rule=("fixed", 8, 1), words=("LUGHNASADH",), emblem="sheaf", rank=2),
    dict(cal="fire", rule=("fixed", 10, 31), words=("SAMHAIN",), emblem="flames", brings=("bonfires",), rank=2),
    dict(cal="fire", rule=("sun", 270, "local"), words=("YULE",), emblem="yule log", brings=("lights", "bonfires"), rank=2),
    # ancient Rome
    dict(cal="rome", rule=("fixed", 1, 1), words=("KALENDS OF JANUARY", "KALENDS"), emblem="laurel", rank=3),
    dict(cal="rome", rule=("fixed", 2, 15), words=("LUPERCALIA",), emblem="wolf", rank=3),
    dict(cal="rome", rule=("fixed", 4, 21), words=("PARILIA",), emblem="flames", brings=("bonfires",), rank=3),
    dict(cal="rome", rule=("fixed", 4, 28, 6), words=("FLORALIA",), emblem="rose", rank=3),
    dict(cal="rome", rule=("fixed", 12, 17, 7), words=("SATURNALIA",), emblem="pileus", brings=("lights",), rank=3),
    # the United States
    dict(cal="us", rule=("fixed", 1, 1), words=("NEW YEAR'S DAY", "NEW YEAR"), emblem="hourglass", rank=2),
    dict(cal="us", rule=("fixed", 2, 14), words=("ST VALENTINE'S DAY", "VALENTINE'S DAY"), emblem="two birds", rank=2),
    dict(cal="us", rule=("fixed", 7, 4), words=("INDEPENDENCE DAY", "JULY FOURTH"), emblem="rocket",
         fireworks="independence", rank=1),
    dict(cal="us", rule=("fixed", 10, 31), words=("HALLOWEEN",), emblem="turnip lantern", brings=("lights",), rank=2),
    dict(cal="us", rule=("nth", 11, 3, 4), words=("THANKSGIVING",), emblem="sheaf", rank=1),
    dict(cal="us", rule=("fixed", 12, 31), words=("NEW YEAR'S EVE",), emblem="rocket", fireworks="new year",
         midnight=True, rank=2),
    # Britain and Ireland
    dict(cal="britain", rule=("fixed", 1, 25), words=("BURNS NIGHT",), emblem="thistle", rank=3),
    dict(cal="britain", rule=("fixed", 3, 1), words=("ST DAVID'S DAY",), emblem="leek", rank=3),
    dict(cal="britain", rule=("fixed", 3, 17), words=("ST PATRICK'S DAY",), emblem="shamrock", rank=2),
    dict(cal="britain", rule=("fixed", 4, 23), words=("ST GEORGE'S DAY",), emblem="rose", rank=3),
    dict(cal="britain", rule=("fixed", 11, 5), words=("BONFIRE NIGHT", "GUY FAWKES"), emblem="flames",
         brings=("bonfires",), fireworks="bonfire", rank=1),
    dict(cal="britain", rule=("fixed", 11, 30), words=("ST ANDREW'S DAY",), emblem="saltire", rank=3),
    dict(cal="britain", rule=("fixed", 12, 31), words=("HOGMANAY",), emblem="rocket", fireworks="new year",
         midnight=True, rank=2),
    # the Hebrew calendar
    dict(cal="hebrew", rule=("hebrew", 7, 1, 2), words=("ROSH HASHANAH",), emblem="shofar", rank=1),
    dict(cal="hebrew", rule=("hebrew", 7, 10), words=("YOM KIPPUR",), emblem=None, rank=1),
    dict(cal="hebrew", rule=("hebrew", 7, 15, 7), words=("SUKKOT",), emblem="booth", rank=2),
    dict(cal="hebrew", rule=("hebrew", 9, 25, 8), words=("HANUKKAH",), emblem="hanukkiah", brings=("lights",), rank=1),
    dict(cal="hebrew", rule=("hebrew", 0, 14), words=("PURIM",), emblem="crown", rank=2),
    dict(cal="hebrew", rule=("hebrew", 1, 15, 7), words=("PASSOVER", "PESACH"), emblem="matzah", rank=1),
    dict(cal="hebrew", rule=("hebrew", 3, 6, 2), words=("SHAVUOT",), emblem="sheaf", rank=2),
    # the Chinese calendar
    dict(cal="chinese", rule=("chinese", 1, 1), words=("SPRING FESTIVAL", "NEW YEAR"), emblem="lantern",
         fireworks="new year", midnight=True, rank=1),
    dict(cal="chinese", rule=("chinese", 1, 15), words=("LANTERN FESTIVAL", "LANTERNS"), emblem="lantern",
         brings=("lights",), rank=1),
    dict(cal="chinese", rule=("sun", 15, "bj"), words=("QINGMING",), emblem="willow", rank=2),
    dict(cal="chinese", rule=("chinese", 5, 5), words=("DRAGON BOAT",), emblem="dragon boat", rank=2),
    dict(cal="chinese", rule=("chinese", 7, 7), words=("QIXI",), emblem="magpie", rank=2),
    dict(cal="chinese", rule=("chinese", 8, 15), words=("MID-AUTUMN",), emblem="rabbit moon", brings=("lights",), rank=1),
    dict(cal="chinese", rule=("chinese", 9, 9), words=("DOUBLE NINTH",), emblem="chrysanthemum", rank=3),
    dict(cal="chinese", rule=("sun", 270, "bj"), words=("DONGZHI",), emblem="sun wheel", rank=3),
    # the Islamic calendar (tabular)
    dict(cal="islamic", rule=("islamic", 1, 1), words=("ISLAMIC NEW YEAR", "HIJRI NEW YEAR"), emblem="crescent", rank=2),
    dict(cal="islamic", rule=("islamic", 3, 12), words=("MAWLID",), emblem="lantern", brings=("lights",), rank=2),
    dict(cal="islamic", rule=("islamic", 9, 1), words=("RAMADAN BEGINS", "RAMADAN"), emblem="crescent", rank=2),
    dict(cal="islamic", rule=("islamic", 10, 1), words=("EID AL-FITR",), emblem="crescent star", brings=("lights",), rank=1),
    dict(cal="islamic", rule=("islamic", 12, 10), words=("EID AL-ADHA",), emblem="crescent star", rank=1),
    # the Hindu calendar
    dict(cal="hindu", rule=("sidereal", 270, "ist"), words=("MAKAR SANKRANTI", "SANKRANTI"), emblem="kite",
         rank=2),
    dict(cal="hindu", rule=("diwali",), words=("DIWALI",), emblem="diya", brings=("lights",), fireworks="bonfire",
         rank=1),
]


def _zone_hours(zone, local_hours):
    return {"local": local_hours, "bj": 8, "ist": 5.5}[zone]


def sun_day(year, lon, hours, sidereal=False):
    """The date (in a zone's clock) on which the Sun reaches a longitude in a year (sidereal by Lahiri's ayanamsa)."""
    target = (lon + (ayanamsa(year) if sidereal else 0)) % 360
    t = sun_moment(zone_midnight(date(year, 1, 1).toordinal(), 0) + ((target - 280) % 360) / 0.98564736 * 86400, target)
    return zone_date(t, hours)


def matches(rule, o, local_hours):
    """Whether a local date (ordinal) is the day a rule names."""
    return day_in(rule, o, local_hours) is not None


def day_in(rule, o, local_hours):
    """The day's place (0 the first) in the days a rule names, or None if it names another day."""
    kind = rule[0]
    d = date.fromordinal(o)
    if kind == "fixed":
        start = date(d.year, rule[1], rule[2]).toordinal()
        span = rule[3] if len(rule) > 3 else 1
        return o - start if 0 <= o - start < span else None
    def one(day):
        return 0 if o == day else None
    if kind in ("easter", "orthodox"):
        return one((easter if kind == "easter" else julian_easter)(d.year) + rule[1])
    if kind == "nth":
        return one(nth_weekday(d.year, rule[1], rule[2], rule[3]))
    if kind == "after":
        return one(weekday_after(date(d.year, rule[1], rule[2]).toordinal(), rule[3]))
    if kind == "window":
        start = date(d.year, rule[1], rule[2]).toordinal()
        return one(start + (rule[3] - date.fromordinal(start).weekday()) % 7)
    if kind == "advent":
        return one(advent_sunday(d.year) + rule[1])
    if kind in ("sun", "sidereal"):
        return one(sun_day(d.year, rule[1], _zone_hours(rule[2], local_hours), kind == "sidereal"))
    if kind == "hebrew":
        y, m, _ = hebrew_from_ordinal(o)
        month = rule[1] or (13 if hebrew_leap(y) else 12)          # month 0: Adar, the second in a leap year
        span = rule[3] if len(rule) > 3 else 1
        k = o - hebrew_date(y, month, rule[2])
        return k if 0 <= k < span else None
    if kind == "chinese":
        m, leap, day = chinese_from_ordinal(o)
        return 0 if not leap and (m, day) == (rule[1], rule[2]) else None
    if kind == "islamic":
        return 0 if islamic_from_ordinal(o)[1:] == (rule[1], rule[2]) else None
    if kind == "diwali":
        return one(diwali(d.year))
    raise ValueError(kind)


def feast_of(o, calendars, lat=40.0, local_hours=0.0):
    """The day's feast among the kept calendars (bit n of `calendars` for CALENDARS[n]): the greatest that falls on
    it, the first in the table among equals, with its words for the hemisphere; or None."""
    best, night = None, None
    for f in FEASTS:
        if not calendars >> CAL[f["cal"]] & 1 or (best is not None and f["rank"] >= best["rank"]):
            continue
        k = day_in(f["rule"], o, local_hours)
        if k is not None:
            best, night = f, k + 1
    if best is None:
        return None
    out = dict(best, night=night)
    if lat < 0 and "south" in best:
        out["words"] = best["south"]
    return out


if __name__ == "__main__":
    def d(o):
        return date.fromordinal(o).isoformat()
    checks = [
        ("Easter 2024", d(easter(2024)), "2024-03-31"), ("Easter 2025", d(easter(2025)), "2025-04-20"),
        ("Easter 2026", d(easter(2026)), "2026-04-05"), ("Easter 2038", d(easter(2038)), "2038-04-25"),
        ("Orthodox Easter 2024", d(julian_easter(2024)), "2024-05-05"),
        ("Orthodox Easter 2026", d(julian_easter(2026)), "2026-04-12"),
        ("US Thanksgiving 2025", d(nth_weekday(2025, 11, 3, 4)), "2025-11-27"),
        ("Plough Monday 2026", d(weekday_after(date(2026, 1, 6).toordinal(), 0)), "2026-01-12"),
        ("Advent Sunday 2026", d(advent_sunday(2026)), "2026-11-29"),
        ("Rosh Hashanah 5786", d(hebrew_new_year(5786)), "2025-09-23"),
        ("Hanukkah 5786 (25 Kislev)", d(hebrew_date(5786, 9, 25)), "2025-12-15"),
        ("Hanukkah 5785 (25 Kislev)", d(hebrew_date(5785, 9, 25)), "2024-12-26"),
        ("Passover 5786 (15 Nisan)", d(hebrew_date(5786, 1, 15)), "2026-04-02"),
        ("Purim 5784 (14 Adar II)", d(hebrew_date(5784, 13, 14)), "2024-03-24"),
        ("Chinese New Year 2024", d(chinese_new_year(2024)), "2024-02-10"),
        ("Chinese New Year 2025", d(chinese_new_year(2025)), "2025-01-29"),
        ("Chinese New Year 2026", d(chinese_new_year(2026)), "2026-02-17"),
        ("Mid-Autumn 2025", d(mid_autumn(2025)), "2025-10-06"),
        ("Mid-Autumn 2026", d(mid_autumn(2026)), "2026-09-25"),
        ("Mid-Autumn 2023", d(mid_autumn(2023)), "2023-09-29"),
        ("Chinese New Year 2023", d(chinese_new_year(2023)), "2023-01-22"),
        ("Chinese New Year 2027", d(chinese_new_year(2027)), "2027-02-06"),
        ("Diwali 2024", d(diwali(2024)), "2024-11-01"),
        ("Diwali 2025", d(diwali(2025)), "2025-10-20"),
        ("Diwali 2026", d(diwali(2026)), "2026-11-08"),
        ("Diwali 1993 (leap Ashvin)", d(diwali(1993)), "1993-11-13"),
        ("Diwali 2001 (leap Ashvin)", d(diwali(2001)), "2001-11-14"),
        ("Diwali 2012 (leap Ashvin)", d(diwali(2012)), "2012-11-13"),
        ("Diwali 2020 (leap Ashvin)", d(diwali(2020)), "2020-11-14"),
        ("Chinese New Year 1985", d(chinese_new_year(1985)), "1985-02-20"),
        ("Chinese New Year 2034 (after the leap 11th month)", d(chinese_new_year(2034)), "2034-02-19"),
        ("Chinese New Year 2053", d(chinese_new_year(2053)), "2053-02-19"),
        ("Islamic: 1 Ramadan 1447 (tabular)", d(islamic_ordinal(1447, 9, 1)), "2026-02-18"),
        ("Islamic date of 2026-03-20 (tabular)", str(islamic_from_ordinal(date(2026, 3, 20).toordinal())), "(1447, 10, 1)"),
        ("Hebrew date of 2025-12-15", str(hebrew_from_ordinal(date(2025, 12, 15).toordinal())), "(5786, 9, 25)"),
        ("Hebrew date of 2024-03-24", str(hebrew_from_ordinal(date(2024, 3, 24).toordinal())), "(5784, 13, 14)"),
        ("June solstice 2026 (UTC)", d(sun_longitude_day(2026, 90)), "2026-06-21"),
        ("December solstice 2026 (UTC)", d(sun_longitude_day(2026, 270)), "2026-12-21"),
        ("March equinox 2026 (UTC)", d(sun_longitude_day(2026, 0)), "2026-03-20"),
    ]
    bad = 0
    for name, got, want in checks:
        ok = got == want
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: {got}" + ("" if ok else f" (published {want})"))
    print("all agree" if not bad else f"{bad} disagree")
