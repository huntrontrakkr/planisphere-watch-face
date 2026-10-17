// End-to-end check of the phone's side and the settings page, without a phone.
//
// Runs the built phone bundle (pebble-js-app.js from the .pbw) in node with a small Pebble shim (a position, and
// canned answers from the place and weather services), checks what it sends the watch, opens the page it makes in
// headless Chromium, waits for the live preview, changes settings by tapping as a person would, saves, and hands the
// page's answer back to the bundle, which sends the settings. Screenshots to out/page/.
//
//   node tools/check-page.mjs [--platform emery|gabbro]
//
// Needs Playwright (borrowed from ~/code/groundtrack-watch-face) and, on this box, libasound staged in /tmp/alsa.
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const arg = (k, d) => (process.argv.includes(k) ? process.argv[process.argv.indexOf(k) + 1] : d);
const platform = arg('--platform', 'emery');
const out = path.join(root, 'out/page');
mkdirSync(out, { recursive: true });
const pbw = path.join(root, 'watchface/build/watchface.pbw');
const member = (name) => execFileSync('python3', ['-c', 'import sys,zipfile;sys.stdout.buffer.write(zipfile.ZipFile(sys.argv[1]).read(sys.argv[2]))', pbw, name], { maxBuffer: 1 << 26 }).toString();
const bundle = member('pebble-js-app.js');
const appinfo = JSON.parse(member('appinfo.json'));
const names = Object.fromEntries(Object.entries(appinfo.appKeys).map(([k, v]) => [v, k]));
let failed = false;
const check = (ok, what) => { console.log((ok ? 'OK   ' : 'FAIL ') + what); if (!ok) failed = true; };

// ---- the phone, in node ----
const handlers = {};
let openedUrl = null;
const sent = [];
const store = {};
const ANSWERS = {
  'api.bigdatacloud.net': { city: 'Zürich', countryName: 'Switzerland', countryCode: 'CH' },
  'api.open-meteo.com': { current: { temperature_2m: -3.4, weather_code: 73, cloud_cover_low: 90, cloud_cover_mid: 60,
    cloud_cover_high: 20, wind_speed_10m: 12.4, wind_direction_10m: 20, pressure_msl: 1003.2, snow_depth: 0.08,
    visibility: 2500 } },
};
class XMLHttpRequest {
  open(method, url) { this.url = url; }
  send() {
    const host = new URL(this.url).host;
    setTimeout(() => { this.responseText = JSON.stringify(ANSWERS[host] || {}); this.onload && this.onload(); }, 5);
  }
}
const Pebble = {
  platform: 'pypkjs',
  addEventListener: (ev, fn) => (handlers[ev] = handlers[ev] || []).push(fn),
  openURL: (u) => { openedUrl = u; },
  sendAppMessage: (d, ok) => { sent.push(d); setTimeout(() => ok && ok({}), 1); },
  getActiveWatchInfo: () => ({ platform, model: platform === 'gabbro' ? 'pebble_round_2' : 'pebble_time_2', language: 'en_US' }),
};
const localStorage = {
  getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); },
  removeItem: (k) => { delete store[k]; },
};
const navigator = { language: 'en-US', geolocation: {
  getCurrentPosition: (ok) => setTimeout(() => ok({ coords: { latitude: 47.3769, longitude: 8.5417 } }), 5) } };
const context = { Pebble, localStorage, console, setTimeout, clearTimeout, navigator, XMLHttpRequest,
                  encodeURIComponent, decodeURIComponent, JSON, Math, Date, String, Number };
context.window = context;
vm.createContext(context);
vm.runInContext(bundle, context, { filename: 'pebble-js-app.js' });
const fire = (ev, e = {}) => (handlers[ev] || []).forEach((fn) => fn(e));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const byName = (m) => Object.fromEntries(Object.entries(m).map(([k, v]) => [names[k] ?? k, v]));

fire('ready');
await sleep(300);
const got = Object.assign({}, ...sent.map(byName));
check(got.LAT === 473769 && got.LON === 85417, `the place sent: ${got.LAT}, ${got.LON}`);
check(got.CITY === 'ZURICH|ZUR.' && got.COUNTRY === 'SWITZERL.|SWITZ.|CH', `its name engraved: ${got.CITY}, ${got.COUNTRY}`);
check(got.WX_TEMP === -34 && got.WX_CODE === 73 && got.WX_SNOW === 80 && got.WX_VIS === 250 && got.WX_FROM === 20,
      `the weather sent: ${JSON.stringify(Object.fromEntries(Object.entries(got).filter(([k]) => k.startsWith('WX_'))))}`);
// the watch must take each message in: a dictionary is a count byte, then 7 bytes a tuple and its value
const inbox = Number(readFileSync(path.join(root, 'watchface/src/c/main.c'), 'utf8').match(/#define INBOX (\d+)/)[1]);
const size = (m) => 1 + Object.values(m).reduce((n, v) => n + 7 + (typeof v === 'string' ? v.length + 1 : 4), 0);
check(sent.every((m) => size(m) <= inbox), `every message fits the watch's inbox (${inbox} bytes)`);
// asked again in the same place (the face opened again): the name comes with the place each time, so a watch that
// missed it, or was reinstalled, has it again; and the tide, where the face shows it, sent again from what was kept
store['plan-settings'] = store['plan-settings'] || JSON.stringify({ TIDE_TIMES: 1 });
const s0 = JSON.parse(store['plan-settings']); s0.TIDE_TIMES = 1; store['plan-settings'] = JSON.stringify(s0);
const n1 = sent.length;
fire('ready');
await sleep(300);
const again = Object.assign({}, ...sent.slice(n1).map(byName));
check(again.CITY === 'ZURICH|ZUR.' && again.LAT === 473769, `the name sent again with the place (${again.CITY})`);
const n2 = sent.length;
fire('ready');
await sleep(300);
const third = Object.assign({}, ...sent.slice(n2).map(byName));
check(third.TIDES !== undefined, `the tide sent again from what the phone kept (${JSON.stringify(third.TIDES)})`);

// the watch tells its own clock (24-hour here, while the test's phone guesses 12): the page follows the watch
fire('appmessage', { payload: { CLOCK24: 1 } });
fire('showConfiguration');
check(openedUrl && openedUrl.startsWith('data:text/html'), `the page opened (${(openedUrl.length / 1024).toFixed(0)} KB)`);
check(decodeURIComponent(openedUrl).includes('"watch24":1'), "the watch's own clock handed to the page");

// ---- the page, in Chromium ----
// Playwright from this repository's node_modules (CI: npm install --no-save playwright), else Groundtrack's
const playwright = (() => {
  for (const from of [import.meta.url, path.join(process.env.HOME, 'code/groundtrack-watch-face/package.json')]) {
    try { return createRequire(from)('playwright'); } catch (e) { /* the next */ }
  }
  throw new Error('Playwright not found: npm install --no-save playwright');
})();
const { chromium } = playwright;
const RETURN = 'http://page.return/?';
const html = decodeURIComponent(openedUrl.replace(/^data:text\/html;charset=utf-8,/, '')).split('$$$RETURN_TO$$$').join(RETURN);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
let answer = null;
await page.route('http://page.return/**', (route) => {
  answer = decodeURIComponent(route.request().url().slice(RETURN.length));
  route.fulfill({ status: 200, body: 'ok' });
});
const errors = [];
page.on('pageerror', (e) => errors.push(e.stack || e.message));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.setContent(html, { waitUntil: 'load' });
await page.waitForTimeout(1500);
await page.screenshot({ path: path.join(out, `${platform}-top.png`) });
await page.screenshot({ path: path.join(out, `${platform}-full.png`), fullPage: true });
const lit = await page.evaluate(() => {
  const c = document.getElementById('screen'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let n = 0;
  for (let i = 0; i < d.length; i += 4) if (d[i] + d[i + 1] + d[i + 2] > 0) n++;
  return n;
});
check(lit > 10000, `the preview drew the face (${lit} lit pixels)`);

const tap = async (sel, text) => { await page.locator(sel, { hasText: text }).first().click(); await page.waitForTimeout(200); };
await tap('.plate', 'Astrolabe');
await tap('.seg button', '24-hour');
await tap('[data-key=LABOURS] .seg button', 'The labours');
await tap('.calendar label.switch', 'The United States');
// the fireworks display: from the first of July the United States' next day is Independence Day, which its button
// shows at nine at night
await page.locator('#date').fill('2027-07-01');
await page.waitForTimeout(300);
await page.locator('button.next', { hasText: 'Independence' }).first().click();
const grab = () => page.evaluate(() => {
  const c = document.getElementById('screen');
  return Array.from(c.getContext('2d').getImageData(0, 0, c.width, c.height).data);
});
const differ = (a, b) => { let n = 0; for (let i = 0; i < a.length; i += 4) n += a[i] !== b[i] || a[i + 1] !== b[i + 1] || a[i + 2] !== b[i + 2]; return n; };
const shots = [];
for (let i = 0; i < 6; i++) { await page.waitForTimeout(400); shots.push(await grab()); }
const moved = shots.slice(1).map((f, i) => differ(f, shots[i]));
await page.waitForTimeout(9000);
const end1 = await grab();
await page.waitForTimeout(500);
const still = differ(end1, await grab());
check(moved.filter((n) => n > 0).length >= 3 && still === 0,
      `the fireworks display played in the preview (pixels changed between frames: ${moved.join(', ')}; after: ${still})`);
// the fireworks switched off alone: the evening hour plays no display (and the minute written stays on)
await page.locator('label.switch', { hasText: 'Fireworks displays' }).first().click();
await page.evaluate(() => { const t = document.getElementById('time'); t.value = 21 * 60; t.dispatchEvent(new Event('input')); });
const quiet = [];
for (let i = 0; i < 4; i++) { await page.waitForTimeout(250); quiet.push(await grab()); }
const calm = quiet.slice(1).map((f, i) => differ(f, quiet[i]));
check(calm.every((n) => n === 0), `no display with the fireworks switched off (pixels changed: ${calm.join(', ')})`);
await page.locator('label.switch', { hasText: 'Fireworks displays' }).first().click();
// the minute written: from 21:09 a minute on by the slider, and the preview writes the new figures (1 and 0), then
// holds still
await page.evaluate(() => { const t = document.getElementById('time'); t.value = 21 * 60 + 9; t.dispatchEvent(new Event('input')); });
await page.waitForTimeout(400);
await page.locator('#time').focus();
await page.keyboard.press('ArrowRight');
const scribed = [];
for (let i = 0; i < 5; i++) { scribed.push(await grab()); await page.waitForTimeout(90); }
await page.waitForTimeout(700);
const written = await grab();
const wrote = scribed.map((f) => differ(f, written));
const settled = differ(written, await grab());
check(wrote[0] > 0 && settled === 0,               // (the new figures not there at once; then written and still)
      `the minute written in the preview (pixels still to write: ${wrote.join(', ')}; after: ${settled})`);
// the Labours' tools in the corners: the Time 2's corners change, and only its corners; the Round 2 has none
const plain = await grab();
await tap('[data-key=CORNERS] .seg button', 'Tools');
await page.waitForTimeout(400);
const tooled = await grab();
const cw = await page.evaluate(() => document.getElementById('screen').width);
let corner = 0, elsewhere = 0;
for (let i = 0; i < plain.length; i += 4) {
  const x = (i / 4) % cw, y = Math.floor(i / 4 / cw), ch = cw / 200, cH = plain.length / 4 / cw;
  const near = (x < 26 * ch || x >= cw - 26 * ch) && (y < 24 * ch || y >= cH - 24 * ch);
  const d = plain[i] !== tooled[i] || plain[i + 1] !== tooled[i + 1] || plain[i + 2] !== tooled[i + 2];
  if (d && near) corner++; else if (d) elsewhere++;
}
check(platform === 'gabbro' ? corner + elsewhere === 0 : corner > 0 && elsewhere === 0,
      `the tools in the corners (pixels changed in the corners: ${corner}; elsewhere: ${elsewhere})`);
await tap('[data-key=CORNERS] .seg button', 'Sprigs');
await page.waitForTimeout(300);
// the time gilt: the time's figures change, and nothing below the time
const ungilt = await grab();
await page.locator('label.switch', { hasText: 'Gild the time' }).first().click();
await page.waitForTimeout(400);
const gilt = await grab();
const gw = await page.evaluate(() => document.getElementById('screen').width);
let nearTime = 0, belowTime = 0;
for (let i = 0; i < ungilt.length; i += 4) {
  const y = Math.floor(i / 4 / gw) * 200 / gw;      // (in the watch's pixels)
  const d = ungilt[i] !== gilt[i] || ungilt[i + 1] !== gilt[i + 1] || ungilt[i + 2] !== gilt[i + 2];
  if (d && y < 75) nearTime++; else if (d) belowTime++;
}
check(nearTime > 30 && belowTime === 0, `the time gilt (pixels changed by the time: ${nearTime}; below it: ${belowTime})`);
await page.locator('label.switch', { hasText: 'Gild the time' }).first().click();
await page.waitForTimeout(300);
// the animations played when asked ("See them play"): each moves the preview over several frames, then the face comes
// back as it was, still (on a plate whose figures are drawn in; the Astrolabe's, under its rete, never are)
const greyed = await page.locator('.play button', { hasText: 'Figures' }).first().isDisabled();
check(greyed, 'the figures not offered to play on the Astrolabe');
await tap('.plate', 'Planisphere');
await page.waitForTimeout(300);
const atRest = await grab();
for (const name of ['Minute', 'Figures', 'Spin', 'Shooting star', 'Birds', 'Fireworks']) {
  await page.locator('.play button', { hasText: name }).first().click();
  const seen = [];                               // (as fast as the page can be read, for the first second and a half)
  for (const t0 = Date.now(); Date.now() - t0 < 1500;) seen.push(await grab());
  await page.waitForTimeout(name === 'Fireworks' ? 9000 : name === 'Birds' ? 7000 : 500);
  const back = await grab();
  const moving = seen.slice(1).map((f, i) => differ(f, seen[i])).filter((n) => n > 0).length;
  await page.waitForTimeout(300);
  check(moving >= 2 && differ(back, atRest) === 0 && differ(back, await grab()) === 0,
        `${name} played in the preview (frames that moved: ${moving}; the face back after: ${differ(back, atRest)})`);
}
// the candle, when chosen: drawn in the card's upper corner, nothing else changed far from it
await page.locator('label.switch', { hasText: 'candle' }).first().click();
await page.waitForTimeout(400);
const lit2 = await grab();
const lw = await page.evaluate(() => document.getElementById('screen').width);
let up = 0, low = 0;
for (let i = 0; i < atRest.length; i += 4) {
  const d = atRest[i] !== lit2[i] || atRest[i + 1] !== lit2[i + 1] || atRest[i + 2] !== lit2[i + 2];
  if (d && Math.floor(i / 4 / lw) < lw / 2) up++; else if (d) low++;
}
check(up > 20 && low === 0, `the candle in the preview (pixels changed in the upper half: ${up}; lower: ${low})`);
await page.locator('label.switch', { hasText: 'candle' }).first().click();
await tap('.plate', 'Astrolabe');
await page.waitForTimeout(300);
// the zodiac behind the face: the card changes from the labours' (its woodcut), and back
const withLabours = await grab();
await tap('[data-key=LABOURS] .seg button', 'The zodiac');
await page.waitForTimeout(400);
const zodiacal = differ(withLabours, await grab());
await tap('[data-key=LABOURS] .seg button', 'The labours');
await page.waitForTimeout(400);
check(zodiacal > 50 && differ(withLabours, await grab()) === 0,
      `the zodiac behind the face (pixels changed from the labours: ${zodiacal}; back again: the same)`);
// the astronomer behind the face: the card changes from the labours' (Tycho's instrument)
await tap('[data-key=LABOURS] .seg button', 'The astronomer');
await page.waitForTimeout(400);
const astronomical = differ(withLabours, await grab());
check(astronomical > 50, `the astronomer behind the face (pixels changed from the labours: ${astronomical})`);
const said = await page.locator('[data-key=LABOURS] .desc').first().textContent();
check(/Tycho/.test(said), `the chosen backdrop explained beneath it ("${said.slice(0, 40)}...")`);
// the sea behind the face: the card changes from the labours'
await tap('[data-key=LABOURS] .seg button', 'The sea');
await page.waitForTimeout(400);
const nautical = differ(withLabours, await grab());
check(nautical > 50, `the sea behind the face (pixels changed from the labours: ${nautical})`);
// the corners apart from the backdrop: the sea's Moon and tide with the zodiac behind (saved so, below)
await tap('[data-key=CORNERS] .seg button', 'Moon & tide');
await tap('[data-key=FIGURES] .seg button', 'Every half hour');
await tap('[data-key=FLICK] .seg button', 'Spins the sky');
await tap('[data-key=LABOURS] .seg button', 'The zodiac');          // (saved so: the theme reaches the watch as itself, not as a switch)
await tap('.calendar label.switch', 'The Hebrew calendar');
await tap('.seg button', 'Snow');
await tap('.seg button', '°C');
await tap('.seg button', 'A place I choose');
// a place by name: the search answered here as Open-Meteo's place names would answer
await page.route('https://geocoding-api.open-meteo.com/**', (route) => route.fulfill({ status: 200,
  contentType: 'application/json', headers: { 'access-control-allow-origin': '*' },
  body: JSON.stringify({ results: [{ name: 'Edinburgh', latitude: 55.95206, longitude: -3.19648, country: 'United Kingdom',
                                     admin1: 'Scotland' }] }) }));
await page.locator('.find input').fill('Edinb');
await page.locator('.places button', { hasText: 'Edinburgh' }).first().click({ timeout: 5000 });
await page.waitForTimeout(300);
const chosen = await page.evaluate(() => Array.from(document.querySelectorAll('.fields input')).map((i) => i.value));
check(chosen[0] === '55.9521' && chosen[2] === 'EDINBURGH' && chosen[3] === 'UNITED KINGDOM',
      `a place found by name: ${chosen.join(', ')}`);
await page.locator('.fields input').nth(0).fill('-33.87');
await page.locator('.fields input').nth(1).fill('151.21');
await page.locator('.fields input').nth(2).fill('Sydney');
await page.locator('.fields input').nth(3).fill('Australia');
await tap('#which button', platform === 'gabbro' ? 'Time 2' : 'Round 2');
await page.waitForTimeout(600);
await page.evaluate(() => window.scrollTo(0, 0));
await page.waitForTimeout(300);
await page.screenshot({ path: path.join(out, `${platform}-changed.png`) });
await tap('#save', 'Save');
await page.waitForTimeout(300);
await browser.close();

check(!errors.length, 'no errors on the page' + (errors.length ? ':\n  ' + errors.join('\n  ') : ''));
check(!!answer, 'the page returned the settings');
const before = sent.length;
fire('webviewclosed', { response: encodeURIComponent(answer) });
await sleep(100);
const msg = byName(sent[before] || {});
console.log('sent:', JSON.stringify(msg));
const want = { PLATE: 4, CLOCK: 2, UNITS: 1, PLACE: 1, PLACE_LAT: -338700, PLACE_LON: 1512100, PLACE_CITY: 'SYDNEY|SYD.',
               PLACE_COUNTRY: 'AUSTRALIA|AUST.', NAMES: 1, LABOURS: 2, CORNERS: 4, FIGURES: 2, FLICK: 2, CANDLE: 0, CALENDARS: (1 << 6) | (1 << 8), WEATHER: 1,
               ANIMATIONS: 63 };
const bad = Object.entries(want).filter(([k, v]) => msg[k] !== v);
check(!bad.length, 'page -> watch: ' + (bad.length ? 'MISMATCH ' + JSON.stringify(bad) : 'the settings as set'));
check(size(sent[before] || {}) <= inbox, `the settings fit the watch's inbox (${size(sent[before] || {})} of ${inbox} bytes)`);
// settings kept from before the passing events (0.1.4's: no ANIMV) have them turned on; later ones are as kept
const animSent = async (kept) => {
  const n = sent.length;
  fire('webviewclosed', { response: encodeURIComponent(JSON.stringify(Object.assign({}, JSON.parse(answer), kept))) });
  await sleep(100);
  return byName(sent[n] || {}).ANIMATIONS;
};
const old = await animSent({ ANIMATIONS: 2, ANIMV: undefined }), kept = await animSent({ ANIMATIONS: 1, ANIMV: 2 });
check(old === 62 && kept === 1, `the passing events turned on in settings from before them (sent ${old}; kept ${kept})`);
// settings from before the corners' choice (0.3: a switch, the theme's pieces) keep them: the astronomer's planets
const n0 = sent.length;
const keptAnswer = Object.assign({}, JSON.parse(answer), { LABOURS: 3, TOOLS: 1 });
delete keptAnswer.CORNERS;
fire('webviewclosed', { response: encodeURIComponent(JSON.stringify(keptAnswer)) });
await sleep(100);
const oldCorners = byName(sent[n0] || {}).CORNERS;
check(oldCorners === 3, `the corners from before the choice kept as the theme's (sent ${oldCorners})`);
// a place in the United States, chosen by hand: the state in the old newspapers' style, then its postal code; the
// city cut back a syllable
const us = byName((() => {
  const n = sent.length;
  fire('webviewclosed', { response: encodeURIComponent(JSON.stringify(Object.assign({}, JSON.parse(answer),
    { PLACE: 1, PLACE_CITY: 'NORFOLK', PLACE_COUNTRY: 'VIRGINIA', PLACE_CC: 'US' }))) });
  return n;
})() >= 0 ? (await sleep(100), [...sent].reverse().find((m) => byName(m).PLACE_CITY !== undefined)) : {});
check(us.PLACE_CITY === 'NORFOLK|NORF.' && us.PLACE_COUNTRY === 'VIRGINIA|VA.|VA',
      `a place in Virginia: ${us.PLACE_CITY}, ${us.PLACE_COUNTRY}`);
process.exitCode = failed ? 1 : 0;
