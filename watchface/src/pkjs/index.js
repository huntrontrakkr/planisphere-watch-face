// Planisphere on the phone: where the phone is, the place's name and the weather there, sent to the watch; and the
// settings page with its live preview of the face (page.js, built by tools/build_page.py).
var page = require('./page');
var names = require('./names');
var tides = require('./tides');
var keys = require('message_keys');

var STORE = 'plan-settings', PLACE = 'plan-place', WEATHER = 'plan-weather', WATCH24 = 'plan-watch24';
var LADDERS = 'plan-ladders';
var TIDES = 'plan-tides';

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

var engrave = names.engrave;           // a name as the ring engraves it: capitals, without accents

// whose pieces in the Time 2's corners (THEME_*, 0 the season's sprigs); settings from before the choice (0.3's
// switch, TOOLS) keep the theme's, with no theme the labours' tools
function corners(s) {
  return s.CORNERS !== undefined ? s.CORNERS | 0 : s.TOOLS ? (s.LABOURS | 0) || 1 : 0;
}

function settingsMessage(s) {
  var m = {};
  m[keys.PLATE] = s.PLATE | 0;
  m[keys.CLOCK] = s.CLOCK | 0;
  m[keys.NAMES] = s.NAMES ? 1 : 0;
  m[keys.LABOURS] = s.LABOURS | 0;              // the theme behind the face (THEME_*: 2 the zodiac), not a switch
  m[keys.CORNERS] = corners(s);
  m[keys.GILD] = s.GILD ? 1 : 0;
  m[keys.TIDE_TIMES] = s.TIDE_TIMES ? 1 : 0;
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
  // the names as ladders of shorter forms (names.js): the state in the old newspapers' style where the place is
  // in one (PLACE_CC its country's code, from the page's search)
  m[keys.PLACE_CITY] = names.cityLadder(s.PLACE_CITY);
  m[keys.PLACE_COUNTRY] = names.regionLadder(s.PLACE_CC, s.PLACE_COUNTRY, s.PLACE_COUNTRY);
  return m;
}

Pebble.addEventListener('showConfiguration', function () {
  var info = Pebble.getActiveWatchInfo ? Pebble.getActiveWatchInfo() : null;
  var state = {
    settings: saved(STORE) || {},
    platform: info && info.platform ? info.platform : 'emery',
    place: saved(PLACE),
    weather: saved(WEATHER),
    tides: (saved(TIDES) || {}).bytes || null,   // the tide's turns as last sent (the preview's high and low water)
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
  else tide(s.PLACE_LAT / 1e4, s.PLACE_LON / 1e4, s.PLACE_CC);
});

Pebble.addEventListener('ready', function () {
  // settings kept from before the names' ladders (0.1.7): sent again once, so a place chosen by hand gets them
  var s = saved(STORE);
  if (s && s.PLACE && !saved(LADDERS)) send(settingsMessage(s));
  localStorage.setItem(LADDERS, '1');
  refresh();
});

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
    if (!moved && place.city) {                               // (its name with it, each time: a watch that missed
      m[keys.CITY] = names.cityLadder(place.city);            // it, or was reinstalled, has it again)
      m[keys.COUNTRY] = names.regionLadder(place.cc, place.regionCode || place.region, place.country);
    }
    send(m);
    if (moved || !place.city || place.cc === undefined) named(lat, lon);
    weather(lat, lon);
    var s = saved(STORE) || {};                               // (the tide is for the face's place)
    if (s.PLACE) tide(s.PLACE_LAT / 1e4, s.PLACE_LON / 1e4, s.PLACE_CC);
    else tide(lat, lon, place.cc);
  }, function (err) { console.log('No location: ' + (err && err.message)); },
  {timeout: 20000, maximumAge: 30 * 60 * 1000});
}

// the place's name, from BigDataCloud's free lookup for a device's own position (to a kilometre or so)
function named(lat, lon) {
  get('https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=' + lat.toFixed(2) + '&longitude=' +
      lon.toFixed(2) + '&localityLanguage=en', function (r) {
    var place = saved(PLACE) || {};
    // its names as the page shows them (the state, where the place is in one), and its country's code
    var cc = String(r.countryCode || '').toUpperCase();
    place.city = engrave(r.city || r.locality || ''), place.cc = cc;
    place.region = engrave(r.principalSubdivision || ''), place.regionCode = String(r.principalSubdivisionCode || '');
    place.country = (names.REGIONS[cc] || cc === 'GB') && place.region ? place.region :      // (Britain: its nation)
      engrave(names.SHORT[cc] || String(r.countryName || '').split(/[(,]/)[0]);
    localStorage.setItem(PLACE, JSON.stringify(place));
    var m = {};
    m[keys.CITY] = names.cityLadder(place.city);
    m[keys.COUNTRY] = names.regionLadder(cc, place.regionCode || place.region, place.country);
    send(m);
  });
}

// the tide here (tides.js), when the face shows it, asked again every six hours or when the phone has moved
function tide(lat, lon, cc) {
  var s = saved(STORE) || {};
  if (!s.TIDE_TIMES && s.LABOURS !== 4 && corners(s) !== 4) return;   // (the tide's times, nor the sea's backdrop or
                                                                      // corners)
  var sendTides = function (bytes) {
    var m = {};
    m[keys.TIDES] = bytes.length ? bytes : [0];          // (one byte: no tide here)
    send(m);
  };
  var t = saved(TIDES);                                  // (asked again after six hours; till then sent again as
  if (t && Math.abs(t.lat - lat) < 0.05 && Math.abs(t.lon - lon) < 0.05 && Date.now() - t.time < 6 * 3600 * 1000) {
    sendTides(t.bytes || []);                            // they were, for a watch that missed them)
    return;
  }
  tides.fetch(get, lat, lon, cc === undefined || cc === 'US', function (bytes) {
    localStorage.setItem(TIDES, JSON.stringify({lat: lat, lon: lon, time: Date.now(), bytes: bytes}));
    sendTides(bytes);
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
