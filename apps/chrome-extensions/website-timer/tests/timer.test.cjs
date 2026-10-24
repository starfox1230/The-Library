const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const extension = path.resolve(__dirname, "../extension");
const coreContext = { URL, Date };
vm.createContext(coreContext);
vm.runInContext(fs.readFileSync(path.join(extension, "core.js"), "utf8"), coreContext);
const T = coreContext.SiteTimer;
const noon = () => new Date(2026, 9, 24, 12).getTime();
let passed = 0;
async function test(name, task) {
  await task();
  passed++;
  console.log("PASS " + name);
}
function event() { return { listeners: [], addListener(fn) { this.listeners.push(fn); }, fire(...args) { return Promise.all(this.listeners.map(fn => fn(...args))); } }; }
function harness(existing) {
  let time = noon();
  const store = existing || { local: {}, session: {} };
  const env = { focused: true, idle: "active", activeId: 1, tabs: new Map([[1, { id: 1, url: "https://www.facebook.com/", windowId: 1 }]]), rules: [], redirects: [], options: 0 };
  class Clock extends Date {
    constructor(...args) { super(...(args.length ? args : [time])); }
    static now() { return time; }
  }
  function area(name) {
    return {
      async get(keys) { return Object.fromEntries((Array.isArray(keys) ? keys : [keys]).map(key => [key, structuredClone(store[name][key])])); },
      async set(value) { Object.assign(store[name], structuredClone(value)); },
      async setAccessLevel() {}
    };
  }
  const chrome = {
    storage: { local: area("local"), session: area("session") },
    runtime: { id: "test", getURL: file => "chrome-extension://test/" + file, onMessage: event(), onStartup: event(), onInstalled: event(), async openOptionsPage() { env.options++; } },
    tabs: {
      onActivated: event(), onUpdated: event(), onRemoved: event(),
      async query(filter) {
        return [...env.tabs.values()].filter(tab => !filter.active || tab.id === env.activeId).filter(tab => !filter.url || filter.url.some(pattern => tab.url.startsWith("http") && T.siteForUrl(tab.url) === (pattern.includes("facebook") ? "facebook" : "rottentomatoes")));
      },
      async update(id, changes) { env.redirects.push({ id, ...changes }); Object.assign(env.tabs.get(id), changes); }
    },
    windows: { onFocusChanged: event(), async getLastFocused() { return { id: 1, focused: env.focused, state: "normal" }; } },
    idle: { setDetectionInterval() {}, async queryState() { return env.idle; }, onStateChanged: event() },
    alarms: { async create() {}, onAlarm: event() },
    declarativeNetRequest: { async updateDynamicRules(value) { env.rules = value.addRules; } }
  };
  const context = { chrome, URL, Date: Clock, console };
  vm.createContext(context);
  context.importScripts = filename => vm.runInContext(fs.readFileSync(path.join(extension, filename), "utf8"), context);
  vm.runInContext(fs.readFileSync(path.join(extension, "background.js"), "utf8"), context);
  const popup = { id: "test", url: chrome.runtime.getURL("popup.html") };
  function message(data = { type: "status" }, sender = popup) {
    return new Promise(resolve => {
      const accepted = chrome.runtime.onMessage.listeners[0](data, sender, resolve);
      if (accepted !== true) resolve(null);
    });
  }
  return {
    env, store, chrome, context, message,
    siteMessage: (id = 1, overrides = {}) => message({ type: "pulse" }, { id: "test", frameId: 0, url: env.tabs.get(id)?.url, tab: env.tabs.get(id), ...overrides }),
    advance(ms) { time += ms; }, setTime(ms) { time = ms; }
  };
}
(async () => {
  await test("matches only supported roots/subdomains and HTTP(S)", () => {
    assert.equal(T.siteForUrl("https://m.facebook.com/a"), "facebook");
    assert.equal(T.siteForUrl("http://rottentomatoes.com/"), "rottentomatoes");
    for (const url of ["https://facebook.com.evil.example/", "https://notfacebook.com/", "file://facebook.com/", "not a url"]) assert.equal(T.siteForUrl(url), null);
  });
  await test("defaults leave blocking off and clamp malformed settings", () => {
    const settings = T.settingsFor({ facebook: { dailyMinutes: -1, cutoff: "25:00", dailyEnabled: "true" } });
    assert.equal(settings.facebook.dailyEnabled, false);
    assert.equal(settings.facebook.dailyMinutes, 1);
    assert.equal(settings.facebook.cutoff, "22:00");
    assert.equal(T.settingsFor().rottentomatoes.dailyMinutes, 30);
  });
  await test("daily totals split at local midnight while visits can continue", () => {
    const start = new Date(2026, 9, 24, 23, 59, 59).getTime();
    const data = T.freshData(start);
    data.totals.facebook = 60000;
    T.credit(data, "facebook", start, start + 2000);
    assert.equal(data.day, "2026-10-25");
    assert.equal(data.totals.facebook, 1000);
    assert.equal(data.totals.rottentomatoes, 0);
  });
  await test("daylight-saving days use local calendar boundaries", () => {
    const start = new Date(2026, 10, 1).getTime();
    const end = new Date(2026, 10, 2).getTime();
    const data = T.freshData(start);
    T.credit(data, "facebook", start, end - 1);
    assert.equal(data.totals.facebook, end - start - 1);
    T.rollDay(data, end);
    assert.equal(data.totals.facebook, 0);
  });
  await test("daily cap and time cutoff are independent and reset next day", () => {
    const data = T.freshData(noon());
    data.totals.facebook = 60000;
    const settings = T.settingsFor({ facebook: { dailyEnabled: true, dailyMinutes: 1 }, rottentomatoes: { cutoffEnabled: true, cutoff: "12:00" } });
    assert.match(T.reasonFor(data, settings, "facebook", noon()), /daily limit/);
    assert.match(T.reasonFor(data, settings, "rottentomatoes", noon()), /cutoff/);
    assert.equal(T.reasonFor(data, settings, "facebook", new Date(2026, 9, 25, 0).getTime()), "");
    assert.equal(T.reasonFor(data, settings, "rottentomatoes", new Date(2026, 9, 25, 0).getTime()), "");
  });
  await test("one focused tab counts once even when multiple tabs send pulses", async () => {
    const h = harness();
    h.env.tabs.set(2, { id: 2, url: "https://m.facebook.com/", windowId: 1 });
    await h.siteMessage();
    h.advance(1000);
    await h.siteMessage(2);
    const result = await h.siteMessage();
    assert.equal(result.sites.facebook.todayMs, 1000);
    assert.equal(result.visitMs, 1000);
  });
  await test("losing window focus or becoming idle pauses counting", async () => {
    const h = harness();
    await h.siteMessage();
    h.advance(1000);
    h.env.focused = false;
    await h.chrome.windows.onFocusChanged.fire(-1);
    h.advance(20000);
    assert.equal((await h.message()).sites.facebook.todayMs, 1000);
    h.env.focused = true;
    h.env.idle = "idle";
    await h.message();
    h.advance(20000);
    assert.equal((await h.message()).sites.facebook.todayMs, 1000);
  });
  await test("switching sites separates daily totals and preserves tab visits", async () => {
    const h = harness();
    h.env.tabs.set(2, { id: 2, url: "https://www.rottentomatoes.com/m/a", windowId: 1 });
    await h.siteMessage();
    h.advance(1000);
    h.env.activeId = 2;
    await h.chrome.tabs.onActivated.fire({ tabId: 2 });
    h.advance(2000);
    const result = await h.siteMessage(2);
    assert.equal(result.sites.facebook.todayMs, 1000);
    assert.equal(result.sites.rottentomatoes.todayMs, 2000);
    assert.equal(result.visitMs, 2000);
    h.env.activeId = 1;
    await h.chrome.tabs.onActivated.fire({ tabId: 1 });
    assert.equal((await h.siteMessage()).visitMs, 1000);
  });
  await test("refresh/internal navigation preserves visits; leaving clears them", async () => {
    const h = harness();
    await h.siteMessage();
    h.advance(1000);
    h.env.tabs.get(1).url = "https://www.facebook.com/some-page";
    await h.chrome.tabs.onUpdated.fire(1, { url: h.env.tabs.get(1).url });
    assert.equal((await h.siteMessage()).visitMs, 1000);
    h.env.tabs.get(1).url = "https://example.com";
    await h.chrome.tabs.onUpdated.fire(1, { url: "https://example.com" });
    await h.message();
    h.env.tabs.get(1).url = "https://www.facebook.com/";
    await h.chrome.tabs.onUpdated.fire(1, { url: h.env.tabs.get(1).url });
    assert.equal((await h.siteMessage()).visitMs, 0);
  });
  await test("sleep or suspended heartbeat never adds the entire gap", async () => {
    const h = harness();
    await h.siteMessage();
    h.advance(3600000);
    assert.equal((await h.siteMessage()).sites.facebook.todayMs, 2500);
  });
  await test("service worker restart preserves totals and visit state", async () => {
    const h = harness();
    await h.siteMessage();
    h.advance(1000);
    await h.siteMessage();
    const restored = harness(h.store);
    restored.setTime(noon() + 2000);
    const result = await restored.siteMessage();
    assert.equal(result.sites.facebook.todayMs, 2000);
    assert.equal(result.visitMs, 2000);
  });
  await test("cutoff creates persistent main-frame redirect and redirects open tabs", async () => {
    const h = harness();
    const result = await h.message({ type: "saveSettings", settings: { facebook: { cutoffEnabled: true, cutoff: "12:00" } } });
    assert.match(result.sites.facebook.blocked, /cutoff/);
    assert.equal(h.env.rules.length, 1);
    assert.equal(h.env.rules[0].condition.requestDomains[0], "facebook.com");
    assert.equal(h.env.rules[0].action.redirect.extensionPath, "/blocked.html?site=facebook");
    assert.equal(h.env.redirects.length, 1);
    assert.match(h.env.redirects[0].url, /blocked.html/);
    const cleared = await h.message({ type: "saveSettings", settings: {} });
    assert.equal(cleared.sites.facebook.blocked, "");
    assert.equal(h.env.rules.length, 0);
  });
  await test("daily budget stops counting at the limit and blocks all same-site tabs", async () => {
    const h = harness();
    h.env.tabs.set(2, { id: 2, url: "https://m.facebook.com/", windowId: 1 });
    await h.message({ type: "saveSettings", settings: { facebook: { dailyEnabled: true, dailyMinutes: 1 } } });
    for (let i = 0; i < 60; i++) { h.advance(1000); await h.message(); }
    assert.equal(h.store.local.usage.totals.facebook, 60000);
    assert.equal(h.env.redirects.length, 2);
    assert.equal(h.env.rules.length, 1);
  });
  await test("alarm clears blocks at midnight without a website heartbeat", async () => {
    const h = harness();
    await h.message({ type: "saveSettings", settings: { facebook: { cutoffEnabled: true, cutoff: "12:00" } } });
    h.setTime(new Date(2026, 9, 25, 0, 0, 1).getTime());
    await h.chrome.alarms.onAlarm.fire({ name: "reconcile" });
    assert.equal(h.env.rules.length, 0);
    assert.equal(h.store.local.usage.day, "2026-10-25");
  });
  await test("website frames and unrelated senders cannot change settings", async () => {
    const h = harness();
    const payload = { type: "saveSettings", settings: { facebook: { dailyEnabled: true } } };
    assert.equal(await h.message(payload, { id: "test", frameId: 0, url: "https://www.facebook.com/", tab: h.env.tabs.get(1) }), null);
    assert.equal(await h.siteMessage(1, { frameId: 1 }), null);
    assert.equal(await h.siteMessage(1, { id: "another-extension" }), null);
    assert.equal(await h.message({ type: "status" }, { id: "test", url: "https://example.com" }), null);
  });
  await test("settings and break pages work when opened as browser tabs", async () => {
    const h = harness();
    const sender = { id: "test", url: "chrome-extension://test/popup.html", tab: { id: 9 } };
    const saved = await h.message({ type: "saveSettings", settings: { facebook: { dailyMinutes: 17 } } }, sender);
    assert.equal(saved.settings.facebook.dailyMinutes, 17);
    assert.equal((await h.message({ type: "status" }, { ...sender, url: "chrome-extension://test/blocked.html?site=facebook" })).ok, true);
  });
  await test("formats hours and seconds without negative time", () => {
    assert.equal(T.format(3661000), "1:01:01");
    assert.equal(T.format(-10), "00:00");
  });
  console.log("\n" + passed + " tests passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
