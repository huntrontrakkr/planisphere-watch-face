// Planisphere's settings: a live preview of the face (the watch's own C, as WebAssembly: preview/preview.c) above
// settings that redraw it as you go. The page returns {MESSAGE_KEY: value} to the phone, which sends it on.
(function () {
  'use strict';
  var STATE = window.PLAN_STATE || {};
  var PLATES = window.PLAN_PLATES || [];
  var ART = window.PLAN_ART || {};
  var CALENDARS = window.PLAN_CALENDARS || [];
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

  // ANIMATIONS: a bit an animation (ANIM_*); 0.1.3's ANIMATE (the minute written alone) read into it, and the passing
  // events (0.1.5, ANIMV 2) turned on in settings from before them
  var ANIM_MINUTE = 1, ANIM_FIREWORKS = 2, ANIM_METEORS = 4, ANIM_FIGURES = 8, ANIM_BIRDS = 16, ANIM_VILLAGE = 32;
  var ANIM_EVENTS = 60;
  var DEFAULTS = {PLATE: 0, CLOCK: 0, NAMES: 1, LABOURS: 0, TOOLS: 0, CALENDARS: 0, ANIMATIONS: 63, ANIMV: 2,
                  WEATHER: 1, UNITS: 0, PLACE: 0, PLACE_LAT: 0, PLACE_LON: 0, PLACE_CITY: '', PLACE_COUNTRY: ''};
  var settings = {};
  function reset(from) {
    settings = {};
    for (var k in DEFAULTS) settings[k] = from && from[k] !== undefined ? from[k] : DEFAULTS[k];
    if (from && from.ANIMATIONS === undefined && from.ANIMATE !== undefined)
      settings.ANIMATIONS = (from.ANIMATE ? ANIM_MINUTE : 0) | ANIM_FIREWORKS;
    if (from && from.ANIMV === undefined && (from.ANIMATIONS !== undefined || from.ANIMATE !== undefined))
      settings.ANIMATIONS |= ANIM_EVENTS;
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

  // the page in the chosen plate's paper and inks (tools/build_page.py PLATES), the faded ink mixed here
  function hex(c) { return [1, 3, 5].map(function (i) { return parseInt(c.substr(i, 2), 16); }); }
  function mix(a, b, t) {
    var x = hex(a), y = hex(b);
    return 'rgb(' + x.map(function (v, i) { return Math.round(v * t + y[i] * (1 - t)); }).join(',') + ')';
  }
  var themed = -1;
  function theme(i) {
    var t = PLATES[i] && PLATES[i].theme;
    if (!t || themed === i) return;
    themed = i;
    var root = document.documentElement;
    ['paper', 'ink', 'accent', 'deep', 'rule'].forEach(function (k) { root.style.setProperty('--' + k, t[k]); });
    root.style.setProperty('--dim', mix(t.ink, t.paper, 0.66));
    root.style.setProperty('--faint', mix(t.ink, t.paper, 0.09));
    root.classList.toggle('dark', !!t.dark);
  }
  function roman(n) {
    var out = '', v = [[10, 'X'], [9, 'IX'], [5, 'V'], [4, 'IV'], [1, 'I']];
    v.forEach(function (p) { while (n >= p[0]) out += p[1], n -= p[0]; });
    return out;
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]; });
  }

  // a name as the ring engraves it: capitals, without accents
  function engrave(s) {
    s = String(s || '');
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '');
    return s.toUpperCase().replace(/[^A-Z0-9 .'-]/g, '').replace(/\s+/g, ' ').trim().slice(0, 23);
  }

  // ---- what can be set ----
  var SECTIONS = [
    {title: 'The plate', items: [{type: 'plates'}]},
    {title: 'The clock', items: [
      {key: 'CLOCK', type: 'seg', options: [[0, 'As the watch'], [1, '12-hour'], [2, '24-hour']],
       descHtml: 'The hours on the ring, and the time as an astronomer writes it: 9<sup>h</sup> 30<sup>m</sup>, or ' +
                 '21<sup>h</sup> 30<sup>m</sup>.'},
    ]},
    {title: 'Animations', items: [
      {key: 'ANIMATIONS', bit: ANIM_MINUTE, type: 'switch', label: 'The minute written',
       desc: 'Each new figure written as a scribe writes it: outlined, then filled in. Under a second, a few hundred ' +
             'pixels.'},
      {key: 'ANIMATIONS', bit: ANIM_FIREWORKS, type: 'switch', label: 'Fireworks displays',
       desc: 'On the calendars’ fireworks days, a few seconds of rockets at the top of each evening hour.'},
      {key: 'ANIMATIONS', bit: ANIM_METEORS, type: 'switch', label: 'Shooting stars',
       desc: 'Now and then on a clear dark night a meteor crosses the window, as the minute turns: one minute in ' +
             'five at a meteor shower’s peak, flying out of its radiant; rarely on other nights.'},
      {key: 'ANIMATIONS', bit: ANIM_FIGURES, type: 'switch', label: 'The figures drawn in',
       desc: 'Once an evening, as dusk brings out the stars, the constellations’ figures are drawn in, star to star.'},
      {key: 'ANIMATIONS', bit: ANIM_BIRDS, type: 'switch', label: 'Birds at twilight',
       desc: 'In the months birds migrate (March to May, September to November), a skein of them may cross low ' +
             'through the window at dawn or dusk, once a twilight.'},
      {key: 'ANIMATIONS', bit: ANIM_VILLAGE, type: 'switch', label: 'The village’s life',
       desc: 'The windows lit and dark as the village’s people come and go, ten minutes at a time, and smoke from ' +
             'the hearth on a cool evening. All the animations are left out while the battery runs low.'}
    ]},
    {title: 'The sky', items: [
      {key: 'NAMES', type: 'switch', label: 'Names in the sky',
       desc: 'The Moon and the planets, the brightest stars and three constellations, set where there is room.'}
    ]},
    {title: 'The card', items: [
      {key: 'LABOURS', type: 'switch', label: 'The labours of the months',
       desc: 'The month’s work, faint in the card round the window, as the old calendars’ woodcuts show it: ' +
             'January’s feast, the March pruning, October’s sowing. In the south, by the seasons there.'},
      {key: 'TOOLS', type: 'switch', label: 'The labours’ tools in the corners',
       desc: 'On the Time 2: the month’s tools in the four corners instead of the season’s sprigs, as the ' +
             'Shepherds’ Calendar draws them: the scythe and the hay rake in June, the flail in August, the baker’s ' +
             'peel in December.'}
    ]},
    {title: 'The calendar', items: [
      {type: 'calendars', desc: 'Keep the days of the calendars you choose: the almanac’s line names the day in red, ' +
       'its emblem stands beside the time, and some bring lights in the windows, fires on the hills, or fireworks at ' +
       'the top of each hour of the evening.'}
    ]},
    {title: 'The weather', items: [
      {key: 'WEATHER', type: 'switch', label: 'Show the weather',
       desc: 'The temperature on the almanac’s line and the weather in the sky and on the village, from ' +
             'Open-Meteo for where your phone is, every half hour while the phone is near.'},
      {key: 'UNITS', type: 'seg', label: 'Temperature', options: [[0, 'As the phone'], [1, '°C'], [2, '°F']],
       show: function (s) { return !!s.WEATHER; }},
      {type: 'trysky', label: 'Try a sky on the preview', show: function (s) { return !!s.WEATHER; }}
    ]},
    {title: 'The place', items: [
      {key: 'PLACE', type: 'seg', options: [[0, 'Where my phone is'], [1, 'A place I choose']]},
      {type: 'phoneplace', show: function (s) { return s.PLACE === 0; }},
      {type: 'place', show: function (s) { return s.PLACE === 1; }}
    ]}
  ];

  var dirty = [];
  function section(sec) {
    var s = el('section');
    var h = el('h2');
    var fleur = el('span', 'fleur'), title = el('span', 'title');
    fleur.innerHTML = ART.fleur || '';
    title.innerHTML = (ART.star || '') + '<span>' + escapeHtml(sec.title) + '</span>' + (ART.star || '');
    h.appendChild(fleur);
    h.appendChild(title);
    s.appendChild(h);
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
      cb.onchange = function () {
        settings[it.key] = it.bit ? (settings[it.key] & ~it.bit) | (cb.checked ? it.bit : 0) : cb.checked ? 1 : 0;
        changed();
      };
      row.appendChild(cb);
      box.appendChild(row);
      dirty.push(function () { cb.checked = it.bit ? !!(settings[it.key] & it.bit) : !!settings[it.key]; });
    } else if (it.type === 'plates') {
      var grid = el('div', 'plates');
      PLATES.forEach(function (p, i) {
        var card = el('button', 'plate');
        card.type = 'button';
        var frame = el('div', 'frame'), cv = el('canvas');
        frame.appendChild(cv);
        card.appendChild(frame);
        card.appendChild(el('div', 'no', 'Plate ' + roman(i + 1)));
        card.appendChild(el('div', 'name', p.name));
        card.appendChild(el('div', 'words', p.words));
        card.onclick = function () { settings.PLATE = i; changed(); };
        grid.appendChild(card);
        thumbs.push({canvas: cv, plate: i, card: card});
        dirty.push(function () { card.classList.toggle('on', settings.PLATE === i); });
      });
      box.appendChild(grid);
    } else if (it.type === 'calendars') {
      var list = el('div', 'calendars');
      CALENDARS.forEach(function (c, i) {
        var row = el('div', 'calendar');
        var sw = el('label', 'switch');
        sw.appendChild(el('span', null, c.name));
        var cb = el('input');
        cb.type = 'checkbox';
        cb.onchange = function () { settings.CALENDARS = (settings.CALENDARS ^ (1 << i)) >>> 0; changed(); };
        sw.appendChild(cb);
        row.appendChild(sw);
        row.appendChild(el('div', 'desc', c.desc));
        var next = el('button', 'next');
        next.type = 'button';
        row.appendChild(next);
        list.appendChild(row);
        dirty.push(function () {
          cb.checked = !!(settings.CALENDARS >> i & 1);
          var n = nextFeast(1 << i);
          next.textContent = n ? 'Next: ' + n.words.toLowerCase().replace(/(^|[ \-])([a-z])/g, function (m, a, b) {
            return a + b.toUpperCase(); }).replace(/'S\b/g, '’s') + ', ' + n.when + ' →' : '';
          next.onclick = n ? function () {
            day = n.date; minute = 21 * 60; following = false;
            if (!(settings.CALENDARS >> i & 1)) settings.CALENDARS = (settings.CALENDARS | 1 << i) >>> 0;
            stopLapse(); changed(); window.scrollTo({top: 0, behavior: 'smooth'});
          } : null;
        });
      });
      box.appendChild(list);
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
          ? 'Your phone was last at ' + Math.abs(phonePlace.lat).toFixed(2) + '° ' + (phonePlace.lat >= 0 ? 'N' : 'S') +
            ', ' + Math.abs(phonePlace.lon).toFixed(2) + '° ' + (phonePlace.lon >= 0 ? 'E' : 'W') +
            (phonePlace.city ? ' (' + phonePlace.city + ')' : '') + '. The watch keeps up as you travel.'
          : 'The watch will ask your phone where it is (allow it the location). Until then it shows a northern sky.';
      });
      box.appendChild(d);
    } else if (it.type === 'place') {
      // a town or city by name (Open-Meteo's place names, as Groundtrack's and Dymaxion's pages): a moment after the
      // typing stops, the latest answer only
      var find = el('label', 'find', 'Search for a town or city');
      var q = el('input');
      q.type = 'search', q.autocomplete = 'off', q.spellcheck = false, q.placeholder = 'Kyoto, or Reykjavik';
      find.appendChild(q);
      box.appendChild(find);
      var list = el('ul', 'places'), note = el('div', 'desc', "The search goes to Open-Meteo's place names.");
      box.appendChild(list);
      box.appendChild(note);
      var findTimer = null, asked = 0;
      var found = function (places, message) {
        list.textContent = '';
        places.forEach(function (pl) {
          var li = el('li'), b = el('button', null, pl.name);
          b.type = 'button';
          var where = [pl.admin1, pl.country].filter(function (v) { return typeof v === 'string' && v && v !== pl.name; });
          if (where.length) b.appendChild(el('small', null, where.join(', ')));
          b.onclick = function () {
            settings.PLACE_LAT = Math.round(Math.max(-89.9, Math.min(89.9, pl.latitude)) * 1e4);
            settings.PLACE_LON = Math.round(pl.longitude * 1e4);
            settings.PLACE_CITY = engrave(pl.name), settings.PLACE_COUNTRY = engrave(pl.country || '');
            q.value = '';
            found([], pl.name + (pl.country ? ', ' + pl.country : '') + ' chosen.');
            changed();
          };
          li.appendChild(b);
          list.appendChild(li);
        });
        note.textContent = message;
      };
      q.oninput = function () {
        clearTimeout(findTimer);
        var text = q.value.trim(), mine = ++asked;
        if (text.length < 3) { found([], text ? 'Three letters or more to search.' : "The search goes to Open-Meteo's place names."); return; }
        note.textContent = 'Searching…';
        findTimer = setTimeout(function () {
          if (!window.fetch) { found([], 'The search is not available here: enter the latitude and longitude.'); return; }
          var stop = typeof AbortController === 'function' ? new AbortController() : null;
          var late = setTimeout(function () { if (stop) stop.abort(); }, 8000);
          fetch('https://geocoding-api.open-meteo.com/v1/search?name=' + encodeURIComponent(text.slice(0, 100)) +
                '&count=8&language=en&format=json', stop ? {signal: stop.signal} : {})
            .then(function (r) { if (!r.ok) throw new Error('search'); return r.json(); })
            .then(function (data) {
              if (mine !== asked) return;
              var places = (data && Array.isArray(data.results) ? data.results : []).filter(function (pl) {
                return pl && typeof pl.name === 'string' && isFinite(pl.latitude) && Math.abs(pl.latitude) <= 90 &&
                  isFinite(pl.longitude) && Math.abs(pl.longitude) <= 180;
              }).slice(0, 8);
              found(places, places.length ? 'Choose the one you mean.' : 'Nothing found. Try a nearby town, or add the country.');
            })
            .catch(function () {
              if (mine === asked) found([], 'The search is out of reach: enter the latitude and longitude.');
            })
            .then(function () { clearTimeout(late); });
        }, 350);
      };
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
    if (it.descHtml) { var dh = el('div', 'desc'); dh.innerHTML = it.descHtml; box.appendChild(dh); }
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
    refresh(); draw(); refreshThumbs(); showTime();             // (the calendars' next days count from it)
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
  function setup(plate, main) {
    var p = place();
    M._pv_face(plate, settings.CLOCK === 2 || (settings.CLOCK === 0 && clock24Here()) ? 1 : 0, settings.NAMES ? 1 : 0,
               fahrenheit() ? 1 : 0, p.lat, p.lon, p.coords ? 1 : 0, settings.LABOURS ? 1 : 0, settings.CALENDARS >>> 0,
               main && settings.ANIMATIONS & ANIM_MINUTE ? 1 : 0, settings.ANIMATIONS & ANIM_VILLAGE ? 8 : 0,
               settings.TOOLS ? 1 : 0);
    M.stringToUTF8(p.city || '', M._pv_city(), 32);
    M.stringToUTF8(p.country || '', M._pv_country(), 32);
    var w = !settings.WEATHER ? null : trySky === 'phone' ? phoneWeather && [phoneWeather.code, phoneWeather.temp10,
      phoneWeather.low, phoneWeather.mid, phoneWeather.high, phoneWeather.wind, phoneWeather.from, phoneWeather.pressure,
      phoneWeather.snow_mm, phoneWeather.vis_dam] : SAMPLES[trySky];
    if (w) M._pv_weather(w[0], w[1], w[2], w[3], w[4], w[5], w[6], w[7], w[8], w[9]);
    else M._pv_weather(-1, 0, 0, 0, 0, 0, 0, 0, 0, 0);
  }
  // a calendar's next day, from the preview's own C: from the day shown, within a year
  var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October',
                'November', 'December'];
  function nextFeast(mask) {
    if (!M) return null;
    var from = new Date(day.getFullYear(), day.getMonth(), day.getDate());
    var days = Math.round((from.getTime() - from.getTimezoneOffset() * 60000) / 86400000);
    var found = M._pv_next_feast(mask, days, 400, -from.getTimezoneOffset());
    if (found < 0) return null;
    var d = new Date((found + 1) * 86400000 + from.getTimezoneOffset() * 60000 - 43200000);
    var date = new Date(d.getFullYear(), d.getMonth(), d.getDate());
    return {date: date, words: M.UTF8ToString(M._pv_feast_words()),
            when: date.getDate() + ' ' + MONTHS[date.getMonth()] + (date.getFullYear() !== from.getFullYear() ? ' ' +
                  date.getFullYear() : '')};
  }
  // the clock as the phone keeps it, for "as the watch" (the watch follows the phone)
  // the watch's own clock, as it last told the phone; else a guess from the phone's
  function clock24Here() {
    if (STATE.watch24 === 0 || STATE.watch24 === 1) return STATE.watch24 === 1;
    try { return !/[ap]m/i.test(new Date(2026, 0, 1, 15).toLocaleTimeString()); } catch (e) { return false; }
  }
  function paint(canvas, plate, main) {
    stopShow();                                  // (the preview draws one face at a time)
    setup(plate, main);
    var t = moment();
    var ptr = M._pv_render(t.utc, t.offset);
    if (ptr) blit(canvas, ptr);
  }
  function blit(canvas, ptr) {
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
  // the animations, in the preview as on the watch: the minute written when the preview moves on a minute (as when
  // it follows the clock), and the fireworks display at the top of an hour that brings one; their frames over the
  // face as drawn then (the plates below wait for them)
  var show = null, thumbsWaiting = false, lastUtc = null;
  function stopShow() { if (show) clearInterval(show.timer), show = null; }
  function startShow(scribe) {
    var frames = settings.ANIMATIONS & ANIM_FIREWORKS ? M._pv_show_frames() : 0;
    if (lapse || (!scribe && !frames)) return;
    var s = show = {frame: 0, k: 1};
    s.timer = setInterval(function () {
      var ptr = 0;
      if (s.k < scribe) ptr = M._pv_scribe_frame(s.k++);
      if (frames && s.frame <= frames) ptr = M._pv_show_frame(s.frame++);
      if (ptr) blit($('screen'), ptr);
      if (s.k < scribe || (frames && s.frame <= frames)) return;
      stopShow();
      if (thumbsWaiting) refreshThumbs();
    }, 1000 / 12);
  }
  function draw() {
    if (!M) return;
    paint($('screen'), settings.PLATE, true);
    var t = moment().utc, scribe = lastUtc !== null && t - lastUtc === 60 ? M._pv_scribe_frames() : 0;
    lastUtc = t;
    if (scribe && !lapse) blit($('screen'), M._pv_scribe_frame(0));   // (the new figures away before they show)
    startShow(scribe && !lapse ? scribe : 0);
    var p = place();
    $('caption').innerHTML = PLATES[settings.PLATE] ? '<b>Plate ' + roman(settings.PLATE + 1) + '</b>' +
      escapeHtml(PLATES[settings.PLATE].name) + ' · ' + Math.abs(p.lat).toFixed(1) + '° ' + (p.lat >= 0 ? 'N' : 'S') +
      ', ' + Math.abs(p.lon).toFixed(1) + '° ' + (p.lon >= 0 ? 'E' : 'W') : '';
  }
  var thumbTimer = null;
  function refreshThumbs() {
    if (!M) return;
    clearTimeout(thumbTimer);
    thumbTimer = setTimeout(function () {
      thumbsWaiting = !!show;
      if (!show) thumbs.forEach(function (t) { paint(t.canvas, t.plate); });
    }, 30);
  }
  function refresh() { theme(settings.PLATE); dirty.forEach(function (f) { f(); }); }
  function changed() { refresh(); draw(); refreshThumbs(); showTime(); }

  // the header shrinks as the settings scroll beneath it
  // (measured at the top, where it is full size: when the page opens, once its type has come, once the preview has)
  function layoutHead() {
    if (window.scrollY > 0) return;
    $('top').style.setProperty('--k', '1');
    document.documentElement.style.setProperty('--head', $('top').offsetHeight + 'px');
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
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(layoutHead);
  if (typeof PlanPreview === 'function')
    PlanPreview().then(function (mod) { M = mod; screen(); refresh(); draw(); refreshThumbs(); layoutHead(); });
})();
