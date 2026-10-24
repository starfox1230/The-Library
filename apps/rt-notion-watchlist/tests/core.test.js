import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import * as core from '../extension/core.js';

const media = {title: 'The Wild Robot', url: 'https://www.rottentomatoes.com/m/the_wild_robot', type: 'Movie'};
const page = {id: '12345678-1234-1234-1234-123456789abc'};
const schema = {properties: {
  Name: {type: 'title'}, Status: {type: 'select', select: {options: [{name: 'For Later'}]}},
  Type: {type: 'select', select: {options: [{name: 'Movie'}, {name: 'TV Show'}]}},
  'Rotten Tomatoes': {type: 'url'}, 'Date Added to Watchlist': {type: 'date'}
}};

test('normalizes source URLs and TV season URLs; rejects other origins and credentials', () => {
  assert.equal(core.canonicalMediaUrl(media.url + '/?utm_source=test#reviews'), media.url);
  assert.equal(core.canonicalMediaUrl('https://rottentomatoes.com/tv/severance/s01/e02'), 'https://www.rottentomatoes.com/tv/severance');
  for (const url of ['http://www.rottentomatoes.com/m/x', 'https://www.rottentomatoes.com.evil.test/m/x', 'https://evil.test/m/x', 'https://user@www.rottentomatoes.com/m/x', 'https://www.rottentomatoes.com/browse/movies']) {
    assert.throws(() => core.canonicalMediaUrl(url));
  }
});
test('validates sender/page agreement and normalizes titles', () => {
  assert.deepEqual(core.validateMedia({...media, title: '  The\nWild Robot '}, media.url), media);
  assert.throws(() => core.validateMedia(media, 'https://www.rottentomatoes.com/m/other'));
  assert.throws(() => core.validateMedia({...media, title: ' '}, media.url));
  assert.throws(() => core.validateMedia({...media, title: 'x'.repeat(501)}, media.url));
});
test('uses real Watchlist properties, local date, For Later and source link only', () => {
  const payload = core.createPayload(media, new Date(2026, 9, 23, 23, 30));
  assert.equal(payload.parent.data_source_id, core.DATA_SOURCE_ID);
  assert.equal(payload.properties.Status.select.name, 'For Later');
  assert.equal(payload.properties['Date Added to Watchlist'].date.start, '2026-10-23');
  assert.equal(payload.properties['Rotten Tomatoes'].url, media.url);
  assert.deepEqual(Object.keys(payload.properties).sort(), ['Name', 'Status', 'Type', 'Rotten Tomatoes', 'Date Added to Watchlist'].sort());
  assert.equal(payload.children[0].paragraph.rich_text[0].text.link.url, media.url);
});
test('fails closed on schema drift or missing For Later', () => {
  assert.equal(core.validateSchema(schema), schema);
  const drift = structuredClone(schema); drift.properties.Status.type = 'status';
  assert.throws(() => core.validateSchema(drift), /Status/);
  const missing = structuredClone(schema); missing.properties.Status.select.options = [];
  assert.throws(() => core.validateSchema(missing), /For Later/);
});
test('exact source match opens existing entry without creating or changing status', async () => {
  const calls = [];
  const result = await core.saveMedia(async (...args) => { calls.push(args); return {results: [page]}; }, media);
  assert.equal(result.state, 'existing'); assert.equal(calls.length, 1);
  assert.equal(calls[0][1].filter.url.equals, media.url);
});
test('older title matches require an explicit choice', async () => {
  const calls = [];
  const result = await core.saveMedia(async (...args) => { calls.push(args); return {results: calls.length === 1 ? [] : [page]}; }, media);
  assert.equal(result.state, 'possible'); assert.equal(calls.length, 2);
  assert.equal(calls[1][1].filter.and[0].title.equals, media.title);
  assert.equal(calls[1][1].filter.and[2].url.is_empty, true);
});
test('separate entry still checks exact URL and uses a single create request', async () => {
  const calls = [];
  const result = await core.saveMedia(async (path, body) => { calls.push({path, body}); return path === 'pages' ? page : {results: []}; }, media, true);
  assert.equal(result.state, 'created'); assert.equal(calls.length, 2);
  assert.equal(calls[1].path, 'pages');
});
test('new title checks URL and legacy match before inserting', async () => {
  const calls = [];
  const result = await core.saveMedia(async (path, body) => { calls.push({path, body}); return path === 'pages' ? page : {results: []}; }, media);
  assert.equal(result.state, 'created'); assert.equal(calls.length, 3);
  assert.equal(calls[2].body.properties.Name.title[0].text.content, media.title);
});
test('Notion API errors are actionable and never expose bodies/tokens', async () => {
  for (const code of [401, 403, 404, 429, 500]) {
    const api = core.createNotionClient('test-secret', async () => ({ok: false, status: code, json: () => { throw new Error('secret-body'); }}));
    await assert.rejects(api('pages', {}), error => !/test-secret|secret-body/.test(error.message));
  }
  let attempts = 0;
  const api = core.createNotionClient('test-secret', async () => { attempts++; throw new Error('test-secret'); });
  await assert.rejects(api('pages', {}), /next save checks/);
  assert.equal(attempts, 1);
});
test('API requests pin version, omit cookies and disallow redirects', async () => {
  let request;
  const api = core.createNotionClient('test-secret', async (...args) => { request = args; return {ok: true, json: async () => page}; });
  await api('pages', {});
  assert.equal(request[0], 'https://api.notion.com/v1/pages');
  assert.equal(request[1].headers['Notion-Version'], core.API_VERSION);
  assert.equal(request[1].credentials, 'omit');
  assert.equal(request[1].redirect, 'error');
});

async function worker() {
  const store = {token: 'test-secret'}; const calls = []; let listener; let access;
  const context = vm.createContext({...core, Map, Promise, chrome: {
    storage: {local: {
      setAccessLevel: async value => { access = value; },
      get: async () => ({...store}), set: async value => Object.assign(store, value),
      remove: async keys => keys.forEach(key => delete store[key])
    }},
    runtime: {id: 'test', getURL: p => `chrome-extension://test/${p}`, openOptionsPage: async () => {},
      onMessage: {addListener: fn => { listener = fn; }}, onInstalled: {addListener: () => {}}},
    action: {onClicked: {addListener: () => {}}}, tabs: {create: async () => {}}
  }, createNotionClient: () => async (path, body) => {
    calls.push({path, body});
    if (path === 'pages') return page;
    if (path.endsWith('/query')) return {results: []};
    return schema;
  }});
  const source = await readFile(new URL('../extension/background.js', import.meta.url), 'utf8');
  vm.runInContext(source.replace(/^import[^\n]+\n/, ''), context);
  const send = (message, sender) => new Promise(resolve => listener(message, sender, resolve));
  const sender = {id: 'test', url: media.url, tab: {id: 1}, frameId: 0};
  return {store, calls, send, sender, access: () => access};
}
test('worker protects settings and credentials from content scripts', async () => {
  const w = await worker();
  assert.equal(w.access().accessLevel, 'TRUSTED_CONTEXTS');
  for (const type of ['CONFIG_STATUS', 'CONNECT', 'DISCONNECT', 'SAVE_PREFERENCES']) assert.equal((await w.send({type, token: 'other'}, w.sender)).ok, false);
  const result = await w.send({type: 'CONFIG_STATUS'}, {id: 'test', url: 'chrome-extension://test/options.html', tab: {id: 2}});
  assert.equal(result.connected, true); assert.equal('token' in result, false);
});
test('worker rejects subframes, external senders and page mismatch', async () => {
  const w = await worker();
  for (const sender of [{...w.sender, frameId: 1}, {...w.sender, id: 'evil'}, {...w.sender, url: 'https://evil.test/m/x'}]) {
    assert.equal((await w.send({type: 'SAVE_MEDIA', media}, sender)).ok, false);
  }
  assert.equal(w.calls.length, 0);
});
test('worker coalesces simultaneous saves across tabs and reports missing setup', async () => {
  const w = await worker();
  const results = await Promise.all([w.send({type: 'SAVE_MEDIA', media}, w.sender), w.send({type: 'SAVE_MEDIA', media}, {...w.sender, tab: {id: 2}})]);
  assert.equal(results[0].state, 'created'); assert.equal(results[1].url, results[0].url);
  assert.equal(w.calls.filter(call => call.path === 'pages').length, 1);
  delete w.store.token;
  assert.equal((await w.send({type: 'SAVE_MEDIA', media}, w.sender)).state, 'setup');
});
