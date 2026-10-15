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
check(got.CITY === 'ZURICH' && got.COUNTRY === 'SWITZERLAND', `its name engraved: ${got.CITY}, ${got.COUNTRY}`);
check(got.WX_TEMP === -34 && got.WX_CODE === 73 && got.WX_SNOW === 80 && got.WX_VIS === 250 && got.WX_FROM === 20,
      `the weather sent: ${JSON.stringify(Object.fromEntries(Object.entries(got).filter(([k]) => k.startsWith('WX_'))))}`);
// the watch must take each message in: a dictionary is a count byte, then 7 bytes a tuple and its value
const inbox = Number(readFileSync(path.join(root, 'watchface/src/c/main.c'), 'utf8').match(/#define INBOX (\d+)/)[1]);
const size = (m) => 1 + Object.values(m).reduce((n, v) => n + 7 + (typeof v === 'string' ? v.length + 1 : 4), 0);
check(sent.every((m) => size(m) <= inbox), `every message fits the watch's inbox (${inbox} bytes)`);

fire('showConfiguration');
check(openedUrl && openedUrl.startsWith('data:text/html'), `the page opened (${(openedUrl.length / 1024).toFixed(0)} KB)`);

// ---- the page, in Chromium ----
const require = createRequire(path.join(process.env.HOME, 'code/groundtrack-watch-face/package.json'));
const { chromium } = require('playwright');
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
await tap('.seg button', 'Snow');
await tap('.seg button', '°C');
await tap('.seg button', 'A place I choose');
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
const want = { PLATE: 4, CLOCK: 2, UNITS: 1, PLACE: 1, PLACE_LAT: -338700, PLACE_LON: 1512100, PLACE_CITY: 'SYDNEY',
               PLACE_COUNTRY: 'AUSTRALIA', NAMES: 1, WEATHER: 1 };
const bad = Object.entries(want).filter(([k, v]) => msg[k] !== v);
check(!bad.length, 'page -> watch: ' + (bad.length ? 'MISMATCH ' + JSON.stringify(bad) : 'the settings as set'));
check(size(sent[before] || {}) <= inbox, `the settings fit the watch's inbox (${size(sent[before] || {})} of ${inbox} bytes)`);
process.exitCode = failed ? 1 : 0;
