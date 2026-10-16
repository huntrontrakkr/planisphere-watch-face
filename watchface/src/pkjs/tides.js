// The tide where the phone is, for the sea's theme: the next high and low waters, as the watch prints them and its
// coast follows them. In the United States from NOAA's nearest tide prediction station (within 30 km: its published
// predictions); elsewhere from Open-Meteo's marine model (its hourly sea level, the turning points found between the
// hours); inland, none. Sent as TIDES, a byte array: each turn six bytes, its time in minutes since 1970 (uint32, the
// top bit set for a high water) and its height in centimetres (int16), little-endian, in order, at most eight.

var MAX = 8;

function noaa(get, lat, lon, done) {
  get('https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/tidepredstations.json?lat=' + lat.toFixed(3) +
      '&lon=' + lon.toFixed(3) + '&radius=30', function (r) {
    var list = (r && r.stationList) || [];
    if (!list.length) { done(null); return; }
    list.sort(function (a, b) { return a.distance - b.distance; });
    var day = new Date(Date.now() - 12 * 3600 * 1000), ymd = day.getUTCFullYear() * 10000 + (day.getUTCMonth() + 1) * 100 +
              day.getUTCDate();
    get('https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions&station=' + list[0].stationId +
        '&begin_date=' + ymd + '&range=72&datum=MLLW&time_zone=gmt&units=metric&interval=hilo&format=json' +
        '&application=planisphere', function (p) {
      var out = ((p && p.predictions) || []).map(function (e) {
        return {t: Date.parse(e.t.replace(' ', 'T') + ':00Z') / 1000, h: Number(e.v), high: e.type === 'H'};
      }).filter(function (e) { return isFinite(e.t) && isFinite(e.h); });
      done(out.length ? out : null);
    });
  });
}

// the turning points of an hourly series: each a local extreme, placed by the parabola through it and its neighbours
function turns(times, levels) {
  var out = [];
  for (var i = 1; i + 1 < levels.length; i++) {
    var a = levels[i - 1], b = levels[i], c = levels[i + 1];
    if (a === null || b === null || c === null) continue;
    var high = b >= a && b > c, low = b <= a && b < c;
    if (!high && !low) continue;
    var den = a - 2 * b + c, off = den ? 0.5 * (a - c) / den : 0;
    out.push({t: times[i] + off * 3600, h: b - 0.25 * (a - c) * off, high: high});
  }
  return out;
}

function model(get, lat, lon, done) {
  get('https://marine-api.open-meteo.com/v1/marine?latitude=' + lat.toFixed(2) + '&longitude=' + lon.toFixed(2) +
      '&hourly=sea_level_height_msl&timezone=GMT&past_days=1&forecast_days=3', function (r) {
    var h = (r && r.hourly) || {}, lv = h.sea_level_height_msl || [], tm = (h.time || []).map(function (s) {
      return Date.parse(s + ':00Z') / 1000;
    });
    var ev = turns(tm, lv);
    done(ev.length >= 2 ? ev : null);
  });
}

// the tides from twelve hours ago on, as the watch takes them (an empty array: none here)
function fetch(get, lat, lon, us, done) {
  var finish = function (ev) {
    var from = Date.now() / 1000 - 12 * 3600;
    ev = (ev || []).filter(function (e) { return e.t >= from; }).slice(0, MAX);
    var bytes = [];
    ev.forEach(function (e) {
      var m = Math.round(e.t / 60) >>> 0, word = (m | (e.high ? 0x80000000 : 0)) >>> 0;
      var cm = Math.max(-32768, Math.min(32767, Math.round(e.h * 100)));
      bytes.push(word & 255, (word >>> 8) & 255, (word >>> 16) & 255, (word >>> 24) & 255, cm & 255, (cm >> 8) & 255);
    });
    done(bytes, ev);
  };
  if (us) noaa(get, lat, lon, function (ev) { if (ev) finish(ev); else model(get, lat, lon, finish); });
  else model(get, lat, lon, finish);
}

module.exports = {fetch: fetch, turns: turns};
