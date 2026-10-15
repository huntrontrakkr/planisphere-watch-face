// Planisphere's settings: a live preview of the face (the watch's own C, as WebAssembly: preview/preview.c) above
// settings that redraw it as you go. The page returns {MESSAGE_KEY: value} to the phone, which sends it on.
(function () {
  'use strict';
  var STATE = window.PLAN_STATE || {};
  var PLATES = window.PLAN_PLATES || [];
  var returnTo = STATE.returnTo || 'pebblejs://close#';
  var owned = STATE.platform === 'gabbro' ? 'round2' : 'time2';
  var which = owned;
  var $ = function (id) { return document.getElementById(id); };
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  var DEFAULTS = {PLATE: 0, CLOCK: 0, NAMES: 1, LABOURS: 0, WEATHER: 1, UNITS: 0, PLACE: 0, PLACE_LAT: 0, PLACE_LON: 0,
                  PLACE_CITY: '', PLACE_COUNTRY: ''};
  var settings = {};
  function reset(from) {
    settings = {};
    for (var k in DEFAULTS) settings[k] = from && from[k] !== undefined ? from[k] : DEFAULTS[k];
  }
  reset(STATE.settings);
  var phonePlace = STATE.place || null;      // where the phone last was: {lat, lon, city, country}
  var phoneWeather = STATE.weather || null;  // the weather it last found there (as the watch is sent it)

  // the preview's weather to try (the phone's own, or a sample of each kind), as the watch is sent it
  var SAMPLES = {
    fair: [1, 160, 18, 0, 5, 9, 250, 1026, 0, 3000], cloudy: [2, 120, 50, 25, 20, 17, 230, 1011, 0, 3000],
    overcast: [3, 90, 95, 70, 30, 14, 60, 1004, 0, 3000], rain: [63, 110, 90, 85, 50, 26, 110, 994, 0, 3000],
    snow: [73, -20, 90, 60, 20, 12, 20, 1003, 80, 250], fog: [45, 70, 100, 0, 0, 3, 180, 1020, 0, 30],
    thunder: [95, 270, 70, 70, 60, 31, 270, 999, 0, 3000]
  };
  var trySky = phoneWeather ? 'phone' : 'fair';

  // places that read their thermometers in degrees Fahrenheit
  function fahrenheitHere() {
    var lang = (navigator.language || 'en-US').toUpperCase();
    return /-(US|LR|MM|BS|BZ|KY|PW)\b/.test(lang);
  }
  function fahrenheit() { return settings.UNITS === 2 || (settings.UNITS === 0 && fahrenheitHere()); }

  // a name as the ring engraves it: capitals, without accents
  function engrave(s) {
    s = String(s || '');
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    return s.toUpperCase().replace(/[^A-Z0-9 .'-]/g, '').replace(/\s+/g, ' ').trim().slice(0, 23);
  }

  // ---- what can be set ----
  var SECTIONS = [
    {title: 'Plate', items: [{type: 'plates'}]},
    {title: 'The clock', items: [
      {key: 'CLOCK', type: 'seg', options: [[0, 'As the watch'], [1, '12-hour'], [2, '24-hour']],
       desc: 'The hours on the ring, and the time as an astronomer writes it: 9ʰ 30ᵐ, or 21ʰ 30ᵐ.'}
    ]},
    {title: 'The sky', items: [
      {key: 'NAMES', type: 'switch', label: 'Names in the sky',
       desc: 'The Moon and the planets, the brightest stars and three constellations, set where there is room.'}
    ]},
    {title: 'The card', items: [
      {key: 'LABOURS', type: 'switch', label: 'The labours of the months',
       desc: 'The month’s work, faint in the card round the window, as the old calendars’ woodcuts show it: ' +
             'January’s feast, the March pruning, October’s sowing. In the south, by the seasons there.'}
    ]},
    {title: 'Weather', items: [
      {key: 'WEATHER', type: 'switch', label: 'Show the weather',
       desc: 'The temperature on the almanac’s line and the weather in the sky and on the village, from ' +
             'Open-Meteo for where your phone is, every half hour while the phone is near.'},
      {key: 'UNITS', type: 'seg', label: 'Temperature', options: [[0, 'As the phone'], [1, '°C'], [2, '°F']],
       show: function (s) { return !!s.WEATHER; }},
      {type: 'trysky', label: 'Try a sky on the preview', show: function (s) { return !!s.WEATHER; }}
    ]},
    {title: 'Place', items: [
      {key: 'PLACE', type: 'seg', options: [[0, 'Where my phone is'], [1, 'A place I choose']]},
      {type: 'phoneplace', show: function (s) { return s.PLACE === 0; }},
      {type: 'place', show: function (s) { return s.PLACE === 1; }}
    ]}
  ];

  var dirty = [];
  function section(sec) {
    var s = el('section');
    s.appendChild(el('h2', null, sec.title));
    var body = el('div', 'body');
    sec.items.forEach(function (it) { body.appendChild(item(it)); });
    s.appendChild(body);
    return s;
  }
  function item(it) {
    var box = el('div', 'item');
    if (it.label && it.type !== 'switch') box.appendChild(el('div', 'label', it.label));
    if (it.type === 'seg') {
      var seg = el('div', 'seg');
      it.options.forEach(function (o) {
        var b = el('button', null, o[1]);
        b.type = 'button';
        b.onclick = function () { settings[it.key] = o[0]; changed(); };
        seg.appendChild(b);
        dirty.push(function () { b.classList.toggle('on', settings[it.key] === o[0]); });
      });
      box.appendChild(seg);
    } else if (it.type === 'switch') {
      var row = el('label', 'switch');
      row.appendChild(el('span', null, it.label));
      var cb = el('input');
      cb.type = 'checkbox';
      cb.onchange = function () { settings[it.key] = cb.checked ? 1 : 0; changed(); };
      row.appendChild(cb);
      box.appendChild(row);
      dirty.push(function () { cb.checked = !!settings[it.key]; });
    } else if (it.type === 'plates') {
      var grid = el('div', 'plates');
      PLATES.forEach(function (p, i) {
        var card = el('button', 'plate');
        card.type = 'button';
        var cv = el('canvas');
        card.appendChild(cv);
        card.appendChild(el('div', 'name', p.name));
        card.appendChild(el('div', 'words', p.words));
        card.onclick = function () { settings.PLATE = i; changed(); };
        grid.appendChild(card);
        thumbs.push({canvas: cv, plate: i, card: card});
        dirty.push(function () { card.classList.toggle('on', settings.PLATE === i); });
      });
      box.appendChild(grid);
    } else if (it.type === 'trysky') {
      var seg2 = el('div', 'seg small');
      var kinds = (phoneWeather ? [['phone', 'Now']] : []).concat([['fair', 'Fair'], ['cloudy', 'Cloudy'],
        ['overcast', 'Overcast'], ['rain', 'Rain'], ['snow', 'Snow'], ['fog', 'Fog'], ['thunder', 'Thunder']]);
      kinds.forEach(function (k) {
        var b = el('button', null, k[1]);
        b.type = 'button';
        b.onclick = function () { trySky = k[0]; draw(); refresh(); };
        seg2.appendChild(b);
        dirty.push(function () { b.classList.toggle('on', trySky === k[0]); });
      });
      box.appendChild(seg2);
      box.appendChild(el('div', 'desc', 'The preview only: the watch shows the weather where you are.'));
    } else if (it.type === 'phoneplace') {
      var d = el('div', 'desc');
      dirty.push(function () {
        d.textContent = phonePlace
          ? 'Your phone was last at ' + phonePlace.lat.toFixed(2) + '°, ' + phonePlace.lon.toFixed(2) + '°' +
            (phonePlace.city ? ' (' + phonePlace.city + ')' : '') + '. The watch keeps up as you travel.'
          : 'The watch will ask your phone where it is (allow it the location). Until then it shows a northern sky.';
      });
      box.appendChild(d);
    } else if (it.type === 'place') {
      var f = el('div', 'fields');
      [['PLACE_LAT', 'Latitude (°, north +)', 'number'], ['PLACE_LON', 'Longitude (°, east +)', 'number'],
       ['PLACE_CITY', 'Name on the ring', 'text'], ['PLACE_COUNTRY', 'Country on the ring', 'text']].forEach(function (q) {
        var lab = el('label', null, q[1]);
        var inp = el('input');
        inp.type = q[2];
        if (q[2] === 'number') inp.step = 'any';
        inp.oninput = function () {
          if (q[2] === 'number') {
            var v = parseFloat(inp.value);
            if (isNaN(v)) return;
            var lim = q[0] === 'PLACE_LAT' ? 89.9 : 180;
            settings[q[0]] = Math.round(Math.max(-lim, Math.min(lim, v)) * 1e4);
          } else settings[q[0]] = engrave(inp.value);
          draw();
          refreshThumbs();
        };
        lab.appendChild(inp);
        f.appendChild(lab);
        dirty.push(function () {
          if (document.activeElement === inp) return;
          inp.value = q[2] === 'number' ? (settings[q[0]] / 1e4).toString() : settings[q[0]];
        });
      });
      box.appendChild(f);
      var use = el('button', 'ghost', 'Start from where my phone is');
      use.type = 'button';
      use.style.marginTop = '10px';
      use.onclick = function () {
        if (!phonePlace) return;
        settings.PLACE_LAT = Math.round(phonePlace.lat * 1e4), settings.PLACE_LON = Math.round(phonePlace.lon * 1e4);
        settings.PLACE_CITY = engrave(phonePlace.city), settings.PLACE_COUNTRY = engrave(phonePlace.country);
        changed();
      };
      if (phonePlace) box.appendChild(use);
    }
    if (it.desc) box.appendChild(el('div', 'desc', it.desc));
    if (it.show) dirty.push(function () { box.classList.toggle('hidden', !it.show(settings)); });
    return box;
  }

  var thumbs = [];
  SECTIONS.forEach(function (sec) { $('sections').appendChild(section(sec)); });

  // which watch the preview shows
  [['time2', 'Time 2'], ['round2', 'Round 2']].forEach(function (w) {
    var b = el('button', null, w[1]);
    b.type = 'button';
    b.onclick = function () { which = w[0]; screen(); changed(); };
    $('which').appendChild(b);
    dirty.push(function () { b.classList.toggle('on', which === w[0]); });
  });

  // ---- the moment shown ----
  var day = new Date();
  var minute = day.getHours() * 60 + day.getMinutes();
  var following = true;                       // following the clock
  function moment() {
    var d = new Date(day.getFullYear(), day.getMonth(), day.getDate(), Math.floor(minute / 60), minute % 60, 0);
    return {utc: Math.floor(d.getTime() / 1000), offset: -d.getTimezoneOffset()};
  }
  function pad(n) { return (n < 10 ? '0' : '') + n; }
  function showTime() {
    $('time').value = minute;
    var h = Math.floor(minute / 60), m = minute % 60, c24 = settings.CLOCK === 2;
    $('timelabel').textContent = c24 ? pad(h) + ':' + pad(m) : ((h % 12) || 12) + ':' + pad(m) + (h < 12 ? 'a' : 'p');
    $('date').value = day.getFullYear() + '-' + pad(day.getMonth() + 1) + '-' + pad(day.getDate());
  }
  $('time').oninput = function () { minute = +$('time').value; following = false; stopLapse(); draw(); showTime(); };
  $('time').onchange = refreshThumbs;
  $('date').onchange = function () {
    var p = $('date').value.split('-');
    if (p.length === 3) day = new Date(+p[0], +p[1] - 1, +p[2]), following = false;
    draw(); refreshThumbs(); showTime();
  };
  $('now').onclick = function () {
    day = new Date(); minute = day.getHours() * 60 + day.getMinutes(); following = true;
    stopLapse(); draw(); refreshThumbs(); showTime();
  };
  var lapse = null;
  function stopLapse() { if (lapse) clearInterval(lapse), lapse = null; $('lapse').classList.remove('on'); }
  $('lapse').onclick = function () {
    if (lapse) { stopLapse(); refreshThumbs(); return; }
    following = false;
    $('lapse').classList.add('on');
    lapse = setInterval(function () { minute = (minute + 4) % 1440; draw(); showTime(); }, 40);
  };
  setInterval(function () {                   // keep up with the clock while following it
    if (!following || lapse) return;
    var now = new Date(), m = now.getHours() * 60 + now.getMinutes();
    if (m !== minute) { day = now; minute = m; draw(); refreshThumbs(); showTime(); }
  }, 15000);

  // ---- the preview ----
  var M = null;
  function screen() {
    $('watch').className = which;
    var w = which === 'round2' ? 260 : 200, h = which === 'round2' ? 260 : 228;
    $('screen').width = w, $('screen').height = h;
    thumbs.forEach(function (t) { t.canvas.width = w, t.canvas.height = h; t.card.className = 'plate ' + which; });
    if (M) M._pv_screen(which === 'round2' ? 1 : 0);
  }
  function place() {
    if (settings.PLACE === 1)
      return {lat: settings.PLACE_LAT / 1e4, lon: settings.PLACE_LON / 1e4, city: settings.PLACE_CITY,
              country: settings.PLACE_COUNTRY, coords: true};
    if (phonePlace) return {lat: phonePlace.lat, lon: phonePlace.lon, city: engrave(phonePlace.city),
                            country: engrave(phonePlace.country), coords: true};
    return {lat: 40, lon: -new Date().getTimezoneOffset() / 4, city: '', country: '', coords: false};
  }
  function setup(plate) {
    var p = place();
    M._pv_face(plate, settings.CLOCK === 2 || (settings.CLOCK === 0 && clock24Here()) ? 1 : 0, settings.NAMES ? 1 : 0,
               fahrenheit() ? 1 : 0, p.lat, p.lon, p.coords ? 1 : 0, settings.LABOURS ? 1 : 0);
    M.stringToUTF8(p.city || '', M._pv_city(), 32);
    M.stringToUTF8(p.country || '', M._pv_country(), 32);
    var w = !settings.WEATHER ? null : trySky === 'phone' ? phoneWeather && [phoneWeather.code, phoneWeather.temp10,
      phoneWeather.low, phoneWeather.mid, phoneWeather.high, phoneWeather.wind, phoneWeather.from, phoneWeather.pressure,
      phoneWeather.snow_mm, phoneWeather.vis_dam] : SAMPLES[trySky];
    if (w) M._pv_weather(w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8], w[9]);
    else M._pv_weather(-1, 0, 0, 0, 0, 0, 0, 0, 0, 0);
  }
  // the clock as the phone keeps it, for "as the watch" (the watch follows the phone)
  function clock24Here() {
    try { return !/[ap]m/i.test(new Date(2026, 0, 1, 15).toLocaleTimeString()); } catch (e) { return false; }
  }
  function paint(canvas, plate) {
    setup(plate);
    var t = moment();
    var ptr = M._pv_render(t.utc, t.offset);
    if (!ptr) return;
    var w = M._pv_width(), h = M._pv_height(), ctx = canvas.getContext('2d'), img = ctx.createImageData(w, h);
    var px = img.data, round = which === 'round2';
    for (var y = 0; y < h; y++) {
      var x0 = round ? M._pv_row_x0(y) : 0, x1 = round ? M._pv_row_x1(y) : w - 1;
      for (var x = 0; x < w; x++) {
        var i = y * w + x, o = 4 * i;
        if (x < x0 || x > x1) { px[o + 3] = 0; continue; }
        var c = M.HEAPU8[ptr + i];
        px[o] = ((c >> 4) & 3) * 85, px[o + 1] = ((c >> 2) & 3) * 85, px[o + 2] = (c & 3) * 85, px[o + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }
  function draw() {
    if (!M) return;
    paint($('screen'), settings.PLATE);
    var p = place();
    $('caption').textContent = PLATES[settings.PLATE] ? PLATES[settings.PLATE].name + ' · ' +
      Math.abs(p.lat).toFixed(1) + '°' + (p.lat >= 0 ? 'N' : 'S') + ' ' + Math.abs(p.lon).toFixed(1) + '°' +
      (p.lon >= 0 ? 'E' : 'W') : '';
  }
  var thumbTimer = null;
  function refreshThumbs() {
    if (!M) return;
    clearTimeout(thumbTimer);
    thumbTimer = setTimeout(function () { thumbs.forEach(function (t) { paint(t.canvas, t.plate); }); }, 30);
  }
  function refresh() { dirty.forEach(function (f) { f(); }); }
  function changed() { refresh(); draw(); refreshThumbs(); showTime(); }

  // the header shrinks as the settings scroll beneath it
  function layoutHead() {
    var head = $('top');
    var k = Math.max(0.55, 1 - window.scrollY / 420);
    head.style.setProperty('--k', k.toFixed(3));
    document.documentElement.style.setProperty('--head', ($('top').offsetHeight / k) + 'px');
  }
  window.addEventListener('scroll', function () {
    var k = Math.max(0.55, 1 - window.scrollY / 420);
    $('top').style.setProperty('--k', k.toFixed(3));
  }, {passive: true});

  $('reset').onclick = function () { reset(null); changed(); };
  $('save').onclick = function () {
    var out = {};
    for (var k in DEFAULTS) out[k] = settings[k];
    document.location = returnTo + encodeURIComponent(JSON.stringify(out));
  };

  screen();
  refresh();
  showTime();
  layoutHead();
  window.addEventListener('resize', layoutHead);
  if (typeof PlanPreview === 'function')
    PlanPreview().then(function (mod) { M = mod; screen(); draw(); refreshThumbs(); });
})();
