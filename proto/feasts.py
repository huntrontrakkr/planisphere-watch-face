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


def chinese_month_start(year, term):
    """The first day of the Chinese month holding the solar term at the Sun's longitude `term` (China's time, UTC+8):
    the last new moon on or before the term's day. (The first month holds Yushui, 330 degrees; the eighth the autumn
    equinox, 180.) Right but in the rare years the calendar's leap months are argued over."""
    day = sun_longitude_day(year, term, 8)
    moons = moon_phase_days(day - 31, day, 0, 8)
    return moons[-1] if moons else None


def chinese_new_year(year):
    return chinese_month_start(year, 330)


def mid_autumn(year):
    """The fifteenth day of the eighth month."""
    return chinese_month_start(year, 180) + 14


def diwali(year):
    """Lakshmi Puja: the evening that falls in the new moon's lunar day (amavasya) of Kartika, as India keeps it
    (UTC+5:30). The lunar day runs about a day up to the new moon, so it is the evening before a new moon that comes
    before about six in the evening, and that evening's day if the new moon is later."""
    days = moon_phase_days(date(year, 10, 15).toordinal(), date(year, 11, 15).toordinal(), 0, 5.5, -18)
    return days[0] if days else None


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
