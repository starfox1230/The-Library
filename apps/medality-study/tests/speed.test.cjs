const { JSDOM } = require('jsdom');
const { readFileSync } = require('node:fs');
const assert = require('node:assert/strict');
const { resolve } = require('node:path');
const root = resolve(__dirname, '../extension');
const source = readFileSync(resolve(root, 'content.js'), 'utf8');
const sdk = readFileSync(resolve(root, 'vendor/vimeo-player.min.js'), 'utf8');
const tick = () => new Promise(done => setImmediate(done));

async function environment(stored = {}, html = '', realSdk = false) {
  const dom = new JSDOM(html, { url: 'https://medality.com/course/test/', runScripts: 'outside-only' });
  const w = dom.window;
  const observers = [];
  const OriginalObserver = w.MutationObserver;
  w.MutationObserver = class extends OriginalObserver {
    constructor(callback) { super(callback); observers.push(this); }
  };
  let storageHandler, messageHandler, interval;
  w.setInterval = fn => { interval = fn; return 1; };
  const players = [];
  class Player {
    constructor(element) { this.element = element; this.rate = 1; this.handlers = {}; this.sets = []; players.push(this); }
    ready() { return Promise.resolve(); }
    on(event, fn) { this.handlers[event] = fn; }
    off(event) { delete this.handlers[event]; }
    async getPlaybackRate() { if (this.fail) throw new Error('Speed is disabled for this video.'); return this.rate; }
    async setPlaybackRate(rate) { this.sets.push(rate); this.rate = rate; return rate; }
    emit(event) { this.handlers[event]?.(); }
  }
  w.chrome = {
    storage: { local: { get: async defaults => ({ ...defaults, ...stored }) }, onChanged: { addListener: fn => { storageHandler = fn; } } },
    runtime: { onMessage: { addListener: fn => { messageHandler = fn; } } }
  };
  if (realSdk) w.eval(sdk); else w.Vimeo = { Player };
  w.eval(source);
  await tick(); await tick();
  return {
    w, players, close: () => { observers.forEach(observer => observer.disconnect()); w.close(); },
    status() { let reply; messageHandler({ type: 'medality-speed-status' }, {}, value => { reply = value; }); return reply; },
    async change(changes) { storageHandler(Object.fromEntries(Object.entries(changes).map(([key, value]) => [key, { newValue: value }])), 'local'); await tick(); await tick(); },
    async poll() { interval(); await tick(); await tick(); }
  };
}

const { test } = require('node:test');
const frame = '<iframe src="https://player.vimeo.com/video/391233202?controls=0"></iframe>';

test('default 2x is applied and verified without playing the video', async () => {
  const e = await environment({}, frame);
  assert.equal(e.players[0].rate, 2);
  assert.equal(e.status().players[0].actual, 2);
  assert.deepEqual(e.players[0].sets, [2]);
  e.close();
});
test('stored speed is used from first application', async () => {
  const e = await environment({ speed: 1.5 }, frame);
  assert.deepEqual(e.players[0].sets, [1.5]); e.close();
});
test('delayed iframe insertion and replacement both receive the preference', async () => {
  const e = await environment();
  e.w.document.body.innerHTML = frame;
  await tick(); await tick();
  assert.equal(e.players[0].rate, 2);
  e.w.document.body.innerHTML = frame.replace('391233202', '391233203');
  await tick(); await tick();
  assert.equal(e.players.length, 2);
  assert.equal(e.players[1].rate, 2);
  assert.equal(e.status().players.length, 1); e.close();
});
test('same-frame next-video reset is corrected by loaded event', async () => {
  const e = await environment({}, frame);
  e.players[0].rate = 1; e.players[0].emit('loaded');
  await tick(); await tick();
  assert.equal(e.players[0].rate, 2); e.close();
});
test('silent rate reset is corrected by fallback check', async () => {
  const e = await environment({}, frame);
  e.players[0].rate = 1; await e.poll();
  assert.equal(e.players[0].rate, 2); e.close();
});
test('disable stops enforcement; re-enable uses new saved speed', async () => {
  const e = await environment({}, frame);
  await e.change({ enabled: false });
  e.players[0].rate = 1.25; e.players[0].emit('playbackratechange'); await e.poll();
  assert.equal(e.players[0].rate, 1.25);
  await e.change({ enabled: true, speed: 1.75 });
  assert.equal(e.players[0].rate, 1.75); e.close();
});
test('disabled stored preference never forces 2x at startup', async () => {
  const e = await environment({ enabled: false }, frame);
  assert.deepEqual(e.players[0].sets, []); e.close();
});
test('ordinary video receives rate, preserves paused state, and handles replacement', async () => {
  const e = await environment({}, '<video></video>');
  const video = e.w.document.querySelector('video');
  assert.equal(video.playbackRate, 2); assert.equal(video.paused, true);
  video.playbackRate = 1; video.dispatchEvent(new e.w.Event('loadedmetadata'));
  await tick(); assert.equal(video.playbackRate, 2);
  e.w.document.body.innerHTML = '<video></video>'; await tick();
  assert.equal(e.w.document.querySelector('video').playbackRate, 2); e.close();
});
test('errors are surfaced and never reported as confirmed', async () => {
  const e = await environment({}, frame);
  e.players[0].fail = true; await e.poll();
  assert.match(e.status().players[0].error, /disabled/);
  assert.equal(e.status().players[0].actual, null); e.close();
});
test('unrelated and lookalike iframe origins are ignored', async () => {
  const e = await environment({}, '<iframe src="https://player.vimeo.com.evil.test/video/123"></iframe><iframe src="https://app.hubspot.com/feedback-web-fetcher"></iframe>');
  assert.equal(e.players.length, 0); e.close();
});
test('invalid stored speed falls back to supported default', async () => {
  const e = await environment({ speed: -5 }, frame);
  assert.equal(e.players[0].rate, 2); e.close();
});
test('bundled official Vimeo SDK exchanges real protocol messages and verifies rate', async () => {
  const e = await environment({}, '', true);
  const iframe = e.w.document.createElement('iframe');
  iframe.src = 'https://player.vimeo.com/video/391233202?controls=0';
  e.w.document.body.append(iframe);
  let rate = 1;
  const methods = [];
  iframe.contentWindow.postMessage = data => {
    if (typeof data === 'string') data = JSON.parse(data);
    methods.push(data.method);
    if (data.method === 'setPlaybackRate') rate = data.value;
    const response = { method: data.method, value: data.method === 'getPlaybackRate' ? rate : data.value };
    queueMicrotask(() => e.w.dispatchEvent(new e.w.MessageEvent('message', {
      origin: 'https://player.vimeo.com', source: iframe.contentWindow, data: JSON.stringify(response)
    })));
  };
  await tick(); await tick(); await tick();
  assert.equal(rate, 2);
  assert.equal(e.status().players[0].actual, 2);
  assert.ok(methods.includes('setPlaybackRate'));
  assert.ok(!methods.includes('play'));
  e.close();
});
test('manifest limits site access and bundles all referenced files', async () => {
  const manifest = JSON.parse(readFileSync(resolve(root, 'manifest.json'), 'utf8'));
  assert.equal(manifest.manifest_version, 3);
  assert.deepEqual(manifest.permissions, ['storage', 'clipboardWrite']);
  assert.deepEqual(manifest.content_scripts[0].matches, ['https://*.medality.com/*', 'https://*.mrionline.com/*']);
  for (const file of [...manifest.content_scripts[0].js, manifest.action.default_popup]) assert.ok(readFileSync(resolve(root, file)).length);
});
