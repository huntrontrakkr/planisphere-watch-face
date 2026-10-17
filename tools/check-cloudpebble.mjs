// The settings page as CloudPebble's emulator opens it: the phone's side (pebble-js-app.js from the .pbw, in node, as
// an emulator's phone: Pebble.platform 'pypkjs') asks for the page on the web, its state in the address's hash; a
// stand-in CloudPebble on another origin runs CloudPebble's own code for it (ide/static/ide/js/libpebble/libpebble.js
// manipulate_url and handle_config_message, and ide/templates/ide/qemu-config.html, as they are), opening the page in
// a popup with return_to added, waiting for the page to come back to its origin and taking the answer by postMessage;
// the answer goes back to the phone's side, which sends the settings to the watch. The published page is the release's
// own (watchface/src/pkjs/page.js with no state filled in), served here from a local address in place of GitHub Pages.
//
//   node tools/check-cloudpebble.mjs
import { execFileSync } from 'node:child_process';
import { createServer } from 'node:http';
import { createRequire } from 'node:module';
import path from 'node:path';
import vm from 'node:vm';

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const require = createRequire(import.meta.url);
const pbw = path.join(root, 'watchface/build/watchface.pbw');
const member = (name) => execFileSync('python3', ['-c', 'import sys,zipfile;sys.stdout.buffer.write(zipfile.ZipFile(sys.argv[1]).read(sys.argv[2]))', pbw, name], { maxBuffer: 1 << 26 }).toString();
const bundle = member('pebble-js-app.js');
const appinfo = JSON.parse(member('appinfo.json'));
const names = Object.fromEntries(Object.entries(appinfo.appKeys).map(([k, v]) => [v, k]));
let failed = false;
const check = (ok, what) => { console.log((ok ? 'OK   ' : 'FAIL ') + what); if (!ok) failed = true; };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ---- the emulator's phone, in node, with settings already kept (the Burritt plate, the zodiac) ----
const handlers = {}, sent = [], store = { 'plan-settings': JSON.stringify({ PLATE: 1, LABOURS: 2, CORNERS: 2 }) };
let openedUrl = null;
const Pebble = {
  platform: 'pypkjs',
  addEventListener: (ev, fn) => (handlers[ev] = handlers[ev] || []).push(fn),
  openURL: (u) => { openedUrl = u; },
  sendAppMessage: (d, ok) => { sent.push(d); setTimeout(() => ok && ok({}), 1); },
  getActiveWatchInfo: () => ({ platform: 'gabbro', model: 'pebble_round_2', language: 'en_US' }),
};
const localStorage = { getItem: (k) => (k in store ? store[k] : null), setItem: (k, v) => { store[k] = String(v); },
                       removeItem: (k) => { delete store[k]; } };
const context = { Pebble, localStorage, console, setTimeout, clearTimeout, encodeURIComponent, decodeURIComponent,
                  JSON, Math, Date, String, Number,
                  navigator: { language: 'en-US', geolocation: { getCurrentPosition: () => {} } },
                  XMLHttpRequest: class { open() {} send() {} } };
context.window = context;
vm.createContext(context);
vm.runInContext(bundle, context, { filename: 'pebble-js-app.js' });
const fire = (ev, e = {}) => (handlers[ev] || []).forEach((fn) => fn(e));
fire('showConfiguration');
const PUBLISHED = 'https://huntrontrakkr.github.io/planisphere-watch-face/settings/';
check(openedUrl && openedUrl.startsWith(PUBLISHED + '#state='), `the emulator asked for the page on the web (${(openedUrl || '').slice(0, 72)}...)`);
check(openedUrl.length < 4000, `its state in the address (${openedUrl.length} characters)`);

// ---- the web: the published page on one origin, the stand-in CloudPebble on another ----
const settingsHtml = require(path.join(root, 'watchface/src/pkjs/page.js'))(null);
// CloudPebble's own code, word for word (but its jQuery and prompts): manipulate_url, the popup and its polling
const CLOUDPEBBLE = `<!DOCTYPE html><html><body><script>
var got = null, closed = false;
var manipulate_url = function(url) {
    var hash_parts = url.split('#');
    var query_parts = hash_parts[0].split('?');
    if(query_parts.length == 1) {
        query_parts.push('');
    }
    if(query_parts[1] != '') {
        query_parts[1] += '&';
    }
    query_parts[1] += 'return_to=' + escape(location.protocol + '//' + location.host + '/ide/emulator/config?');
    var new_url = query_parts.join('?');
    if(hash_parts.length > 1) {
        new_url += '#' + hash_parts[1];
    }
    return new_url;
};
function openConfig(url) {
    var new_url = manipulate_url(url);
    var configWindow = window.open(new_url, "emu_config", "width=375,height=567");
    var spamInterval = setInterval(function () {
        if (configWindow.location && configWindow.location.host) {
            clearInterval(spamInterval);
            configWindow.postMessage('hi', '*');
            window.addEventListener('message', function (event) { got = event.data; configWindow.close(); }, { once: true });
        } else if (configWindow.closed) {
            clearInterval(spamInterval);
            closed = true;
        }
    }, 1000);
}
</script></body></html>`;
const QEMU_CONFIG = `<!DOCTYPE html><html><head lang="en"><meta charset="UTF-8"><script>
        var data = location.search.substr(1);
        window.addEventListener('message', function(e) {
            e.source.postMessage(data, '*');
        }, false);
    </script></head><body>almost done...</body></html>`;
const serve = (routes) => new Promise((ok) => {
  const server = createServer((req, res) => {
    const body = routes[new URL(req.url, 'http://x').pathname];
    res.writeHead(body ? 200 : 404, { 'content-type': 'text/html; charset=utf-8' });
    res.end(body || 'not found');
  });
  server.listen(0, '127.0.0.1', () => ok(server));
});
const pages = await serve({ '/planisphere-watch-face/settings/': settingsHtml });
const cloud = await serve({ '/ide': CLOUDPEBBLE, '/ide/emulator/config': QEMU_CONFIG });
// (two origins: the page at localhost, CloudPebble at 127.0.0.1)
const pagesAt = `http://localhost:${pages.address().port}/planisphere-watch-face/settings/`;
const cloudAt = `http://127.0.0.1:${cloud.address().port}/ide`;

const playwright = (() => {
  for (const from of [import.meta.url, path.join(process.env.HOME, 'code/groundtrack-watch-face/package.json')]) {
    try { return createRequire(from)('playwright'); } catch (e) { /* the next */ }
  }
  throw new Error('Playwright not found: npm install --no-save playwright');
})();
const browser = await playwright.chromium.launch();
const ide = await browser.newPage();
const errors = [];
await ide.goto(cloudAt);
const popupComing = ide.waitForEvent('popup');
await ide.evaluate((u) => openConfig(u), openedUrl.replace(PUBLISHED, pagesAt));
const popup = await popupComing;
popup.on('pageerror', (e) => errors.push(e.message));
await popup.waitForLoadState('load');
await popup.waitForTimeout(1500);
check(/[?&]return_to=/.test(popup.url()) && popup.url().includes('#state='), 'CloudPebble opened the page with its return_to');
const shown = await popup.evaluate(() => {
  const c = document.getElementById('screen'), d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
  let lit = 0;
  for (let i = 0; i < d.length; i += 4) if (d[i] + d[i + 1] + d[i + 2] > 0) lit++;
  return { lit, round: document.getElementById('watch').className };
});
check(shown.lit > 10000 && shown.round === 'round2', `the page drew the Round 2's face from the state it was given (${shown.lit} lit pixels)`);
await popup.locator('[data-key=FLICK] .seg button', { hasText: 'Spins the sky' }).first().click();
await popup.locator('#save').click();
for (let i = 0; i < 40 && ide && !(await ide.evaluate(() => got !== null)); i++) await sleep(250);
const got = await ide.evaluate(() => got);
check(typeof got === 'string' && got.length > 0, `CloudPebble took the page's answer (${(got || '').length} characters)`);
let answer = null;
try { answer = JSON.parse(decodeURIComponent(got)); } catch (e) { /* checked below */ }
check(answer && answer.PLATE === 1 && answer.LABOURS === 2 && answer.FLICK === 2,
      `the answer kept the settings given and the change made (PLATE ${answer && answer.PLATE}, LABOURS ${answer && answer.LABOURS}, FLICK ${answer && answer.FLICK})`);
// the answer handed to the phone's side as CloudPebble's emulator hands it (webviewclosed), and sent to the watch
const before = sent.length;
fire('webviewclosed', { response: got });
await sleep(100);
const message = Object.fromEntries(Object.entries(Object.assign({}, ...sent.slice(before))).map(([k, v]) => [names[k] ?? k, v]));
check(message.PLATE === 1 && message.FLICK === 2, `the settings sent to the watch (PLATE ${message.PLATE}, FLICK ${message.FLICK})`);
check(errors.length === 0, `no errors on the page${errors.length ? ': ' + errors.join('; ') : ''}`);
await browser.close();
pages.close(), cloud.close();
process.exitCode = failed ? 1 : 0;
