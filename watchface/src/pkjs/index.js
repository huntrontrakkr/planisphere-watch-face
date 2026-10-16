// Planisphere on the phone: where the phone is, the place's name and the weather there, sent to the watch; and the
// settings page with its live preview of the face (page.js, built by tools/build_page.py).
var page = require('./page');
var keys = require('message_keys');

var STORE = 'plan-settings', PLACE = 'plan-place', WEATHER = 'plan-weather', WATCH24 = 'plan-watch24';

function saved(k) {
  try { return JSON.parse(localStorage.getItem(k)) || null; } catch (e) { return null; }
}

// ---- to the watch, one message at a time (each waits for the last to be taken), trying again if it was busy ----
var queue = [], sending = false;
function send(message) {
  queue.push({m: message, tries: 3});
  pump();
}
function pump() {
  if (sending || !queue.length) return;
  sending = true;
  var q = queue[0];
  Pebble.sendAppMessage(q.m, function () {
    queue.shift();
    sending = false;
    pump();
  }, function () {
    sending = false;
    if (--q.tries <= 0) queue.shift();
    setTimeout(pump, 1500);
  });
}

// degrees Fahrenheit where people read their thermometers in them
function fahrenheitHere() {
  var lang = (navigator.language || '').toUpperCase();
  return /-(US|LR|MM|BS|BZ|KY|PW)\b/.test(lang);
}

// a name as the ring engraves it: capitals, without accents
function engrave(s) {
  s = String(s || '');
  if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
  return s.toUpperCase().replace(/[^A-Z0-9 .'-]/g, '').replace(/\s+/g, ' ').replace(/^ | $/g, '').slice(0, 23);
}

function settingsMessage(s) {
  var m = {};
  m[keys.PLATE] = s.PLATE | 0;
  m[keys.CLOCK] = s.CLOCK | 0;
  m[keys.NAMES] = s.NAMES ? 1 : 0;
  m[keys.LABOURS] = s.LABOURS ? 1 : 0;
  m[keys.CALENDARS] = s.CALENDARS | 0;
  // a bit an animation: 1 the minute written, 2 fireworks, 4 .. 32 the passing events and the village's life (0.1.3's
  // ANIMATE was the minute alone; settings from before the events, without ANIMV, have them turned on)
  var anim = s.ANIMATIONS !== undefined ? s.ANIMATIONS | 0 : (s.ANIMATE === 0 ? 0 : 1) | 2;
  m[keys.ANIMATIONS] = s.ANIMV === undefined ? anim | 60 : anim;
  m[keys.WEATHER] = s.WEATHER ? 1 : 0;
  m[keys.UNITS] = (s.UNITS | 0) === 0 ? (fahrenheitHere() ? 2 : 1) : s.UNITS | 0;
  m[keys.PLACE] = s.PLACE | 0;
  m[keys.PLACE_LAT] = s.PLACE_LAT | 0;
  m[keys.PLACE_LON] = s.PLACE_LON | 0;
  m[keys.PLACE_CITY] = engrave(s.PLACE_CITY);
  m[keys.PLACE_COUNTRY] = engrave(s.PLACE_COUNTRY);
  return m;
}

Pebble.addEventListener('showConfiguration', function () {
  var info = Pebble.getActiveWatchInfo ? Pebble.getActiveWatchInfo() : null;
  var state = {
    settings: saved(STORE) || {},
    platform: info && info.platform ? info.platform : 'emery',
    place: saved(PLACE),
    weather: saved(WEATHER),
    watch24: saved(WATCH24),            // the watch's own 12/24-hour clock, as it last said
    // the emulator's phone fills in its own return address
    returnTo: Pebble.platform === 'pypkjs' ? '$$$RETURN_TO$$$' : 'pebblejs://close#'
  };
  Pebble.openURL('data:text/html;charset=utf-8,' + encodeURIComponent(page(state)));
});

Pebble.addEventListener('webviewclosed', function (e) {
  if (!e || !e.response) return;
  var s = null;
  try { s = JSON.parse(decodeURIComponent(e.response)); } catch (err) {
    try { s = JSON.parse(e.response); } catch (err2) { return; }
  }
  if (!s || typeof s !== 'object') return;
  localStorage.setItem(STORE, JSON.stringify(s));
  send(settingsMessage(s));
  if (!s.PLACE) refresh();
});

Pebble.addEventListener('ready', function () { refresh(); });

// the watch asks again when what it has is old
Pebble.addEventListener('appmessage', function (e) {
  var p = (e && e.payload) || {};
  var c24 = p.CLOCK24 !== undefined ? p.CLOCK24 : p[keys.CLOCK24];
  if (c24 !== undefined) localStorage.setItem(WATCH24, JSON.stringify(c24 ? 1 : 0));
  if (p.REQUEST || p[keys.REQUEST]) refresh();
});

// ---- where the phone is, what the place is called, the weather there ----
function get(url, done) {
  var req = new XMLHttpRequest();
  req.onload = function () {
    try { done(JSON.parse(req.responseText)); } catch (e) { console.log('Not read: ' + url); }
  };
  req.onerror = function () { console.log('Not reached: ' + url); };
  req.open('GET', url);
  req.send();
}

function refresh() {
  if (!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function (pos) {
    var lat = pos.coords.latitude, lon = pos.coords.longitude;
    var place = saved(PLACE) || {};
    var moved = place.lat === undefined || Math.abs(place.lat - lat) > 0.05 || Math.abs(place.lon - lon) > 0.05;
    place.lat = lat, place.lon = lon;
    localStorage.setItem(PLACE, JSON.stringify(place));
    var m = {};
    m[keys.LAT] = Math.round(lat * 1e4);
    m[keys.LON] = Math.round(lon * 1e4);
    send(m);
    if (moved || !place.city) named(lat, lon);
    weather(lat, lon);
  }, function (err) { console.log('No location: ' + (err && err.message)); },
  {timeout: 20000, maximumAge: 30 * 60 * 1000});
}

// the countries whose names are long, as a map's border would give them
var SHORT = {US: 'U.S.A.', AE: 'U.A.E.', RU: 'RUSSIA', KR: 'KOREA', KP: 'KOREA', IR: 'IRAN', VN: 'VIETNAM', TW: 'TAIWAN',
             BO: 'BOLIVIA', VE: 'VENEZUELA', TZ: 'TANZANIA', SY: 'SYRIA', LA: 'LAOS', MD: 'MOLDOVA', CZ: 'CZECHIA',
             NL: 'NETHERLANDS', PH: 'PHILIPPINES', DO: 'DOMINICAN REP.', CD: 'CONGO', CG: 'CONGO'};

// the place's name, from BigDataCloud's free lookup for a device's own position (to a kilometre or so)
function named(lat, lon) {
  get('https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=' + lat.toFixed(2) + '&longitude=' +
      lon.toFixed(2) + '&localityLanguage=en', function (r) {
    var city = r.city || r.locality || '';
    var country = SHORT[r.countryCode] ||
      (r.countryCode === 'GB' ? (r.principalSubdivision || 'U.K.') : String(r.countryName || '').split(/[(,]/)[0]);
    var place = saved(PLACE) || {};
    place.city = engrave(city), place.country = engrave(country);
    localStorage.setItem(PLACE, JSON.stringify(place));
    var m = {};
    m[keys.CITY] = place.city;
    m[keys.COUNTRY] = place.country;
    send(m);
  });
}

// the weather now, from Open-Meteo (no key), as the watch draws it
function weather(lat, lon) {
  get('https://api.open-meteo.com/v1/forecast?latitude=' + lat.toFixed(2) + '&longitude=' + lon.toFixed(2) +
      '&current=temperature_2m,weather_code,cloud_cover_low,cloud_cover_mid,cloud_cover_high,wind_speed_10m,' +
      'wind_direction_10m,pressure_msl,snow_depth,visibility&wind_speed_unit=kmh', function (r) {
    var c = r.current || {};
    var clamp = function (v, lo, hi) { v = Math.round(Number(v) || 0); return Math.max(lo, Math.min(hi, v)); };
    var w = {code: clamp(c.weather_code, 0, 255), temp10: clamp(c.temperature_2m * 10, -900, 900),
             low: clamp(c.cloud_cover_low, 0, 100), mid: clamp(c.cloud_cover_mid, 0, 100),
             high: clamp(c.cloud_cover_high, 0, 100), wind: clamp(c.wind_speed_10m, 0, 255),
             from: clamp(c.wind_direction_10m, 0, 360), pressure: clamp(c.pressure_msl, 0, 2000),
             snow_mm: clamp((c.snow_depth || 0) * 1000, 0, 65535),
             vis_dam: clamp(c.visibility === undefined || c.visibility === null ? 30000 : c.visibility / 10, 0, 65535),
             time: Date.now()};
    localStorage.setItem(WEATHER, JSON.stringify(w));
    var m = {};
    m[keys.WX_TEMP] = w.temp10;
    m[keys.WX_CODE] = w.code;
    m[keys.WX_LOW] = w.low;
    m[keys.WX_MID] = w.mid;
    m[keys.WX_HIGH] = w.high;
    m[keys.WX_WIND] = w.wind;
    m[keys.WX_FROM] = w.from;
    m[keys.WX_PRESSURE] = w.pressure;
    m[keys.WX_SNOW] = w.snow_mm;
    m[keys.WX_VIS] = w.vis_dam;
    send(m);
  });
}
