importScripts("core.js");
const T = SiteTimer;
let ready, data, settings, runtime, ruleKey = null;
let queue = Promise.resolve();
function serial(task) {
  const result = queue.then(task);
  queue = result.catch(error => console.error("Website Timer:", error.message));
  return result;
}
async function initialize() {
  if (!ready) ready = (async () => {
    const [local, session] = await Promise.all([
      chrome.storage.local.get(["usage", "settings"]),
      chrome.storage.session.get("runtime")
    ]);
    data = local.usage || T.freshData(Date.now());
    settings = T.settingsFor(local.settings);
    runtime = session.runtime || { active: null, visits: {} };
    await chrome.storage.local.setAccessLevel({ accessLevel: "TRUSTED_CONTEXTS" });
    chrome.idle.setDetectionInterval(60);
    await chrome.alarms.create("reconcile", { periodInMinutes: 0.5 });
  })().catch(error => { ready = null; throw error; });
  return ready;
}
function settle(now) {
  const active = runtime.active;
  if (active) {
    // Never count a sleep, suspended tab, or missing heartbeat as browsing time.
    const end = Math.min(now, active.at + 2500);
    let start = active.at;
    const policy = settings[active.site];
    if (policy.cutoffEnabled) {
      const date = new Date(start);
      const [h, m] = policy.cutoff.split(":").map(Number);
      const cutoff = new Date(date.getFullYear(), date.getMonth(), date.getDate(), h, m).getTime();
      if (start < cutoff) start = Math.min(start, cutoff);
      if (end > cutoff && cutoff >= active.at) {
        creditActive(active, start, cutoff);
        T.rollDay(data, now);
        runtime.active = null;
        return;
      }
    }
    creditActive(active, start, end);
  }
  T.rollDay(data, now);
  runtime.active = null;
}
function creditActive(active, start, end) {
  const policy = settings[active.site];
  if (policy.dailyEnabled) {
    const remaining = Math.max(0, policy.dailyMinutes * 60000 - (data.day === T.dayKey(start) ? data.totals[active.site] : 0));
    end = Math.min(end, start + remaining);
  }
  T.credit(data, active.site, start, end);
  const visit = runtime.visits[active.tabId];
  if (visit && visit.site === active.site) visit.ms += Math.max(0, end - start);
}
async function focusedTab() {
  const window = await chrome.windows.getLastFocused();
  if (!window.focused || window.state === "minimized" || await chrome.idle.queryState(60) !== "active") return null;
  const [tab] = await chrome.tabs.query({ active: true, windowId: window.id });
  return tab;
}
async function selectActive(now) {
  const tab = await focusedTab();
  const site = tab && T.siteForUrl(tab.url);
  if (!site || T.reasonFor(data, settings, site, now)) return;
  const old = runtime.visits[tab.id];
  if (!old || old.site !== site) runtime.visits[tab.id] = { site, ms: 0 };
  runtime.active = { tabId: tab.id, site, at: now };
}
async function rulesAndBlocks(now) {
  const blocked = Object.keys(T.SITES).filter(site => T.reasonFor(data, settings, site, now));
  const key = blocked.join(",");
  if (key === ruleKey) return;
  const rules = blocked.map(site => ({
    id: Object.keys(T.SITES).indexOf(site) + 1, priority: 1,
    action: { type: "redirect", redirect: { extensionPath: "/blocked.html?site=" + site } },
    condition: { requestDomains: [T.SITES[site].domain], resourceTypes: ["main_frame"] }
  }));
  await chrome.declarativeNetRequest.updateDynamicRules({ removeRuleIds: [1, 2], addRules: rules });
  ruleKey = key;
  for (const site of blocked) {
    const tabs = await chrome.tabs.query({ url: ["*://*." + T.SITES[site].domain + "/*"] });
    await Promise.all(tabs.map(tab => chrome.tabs.update(tab.id, { url: chrome.runtime.getURL("blocked.html?site=" + site) }).catch(() => {})));
  }
}
async function persist(now) {
  await rulesAndBlocks(now);
  await Promise.all([
    chrome.storage.local.set({ usage: data, settings }),
    chrome.storage.session.set({ runtime })
  ]);
}
function snapshot(tabId, now) {
  return {
    day: data.day, settings,
    sites: Object.fromEntries(Object.keys(T.SITES).map(site => [site, {
      todayMs: data.totals[site] || 0,
      blocked: T.reasonFor(data, settings, site, now)
    }])),
    visitMs: runtime.visits[tabId]?.ms || 0,
    counting: runtime.active?.tabId === tabId
  };
}
async function reconcile() {
  await initialize();
  const now = Date.now();
  settle(now);
  await selectActive(now);
  await persist(now);
}
function trustedPage(sender) {
  return sender.id === chrome.runtime.id &&
    [chrome.runtime.getURL("popup.html"), chrome.runtime.getURL("blocked.html")].some(url => (sender.url || "").split("?")[0] === url);
}
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  const fromPage = trustedPage(sender);
  const fromSite = sender.id === chrome.runtime.id && sender.frameId === 0 && T.siteForUrl(sender.url) && sender.tab;
  if (!fromPage && !fromSite) return false;
  if (!["pulse", "status", "saveSettings", "openSettings"].includes(message?.type)) return false;
  if (["saveSettings"].includes(message.type) && (!fromPage || sender.url !== chrome.runtime.getURL("popup.html"))) return false;
  serial(async () => {
    await initialize();
    const now = Date.now();
    settle(now);
    if (message.type === "saveSettings") settings = T.settingsFor(message.settings);
    if (message.type === "openSettings") await chrome.runtime.openOptionsPage();
    await selectActive(now);
    await persist(now);
    return snapshot(sender.tab?.id, now);
  }).then(result => respond({ ok: true, ...result }), () => respond({ ok: false, error: "Timer could not update. Reload the extension and this page." }));
  return true;
});
chrome.tabs.onActivated.addListener(() => serial(reconcile));
chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (!change.url) return;
  serial(async () => {
    await initialize();
    const now = Date.now();
    settle(now);
    if (runtime.visits[tabId]?.site !== T.siteForUrl(change.url)) delete runtime.visits[tabId];
    await selectActive(now);
    await persist(now);
  });
});
chrome.tabs.onRemoved.addListener(tabId => serial(async () => {
  await initialize();
  const now = Date.now();
  settle(now);
  delete runtime.visits[tabId];
  await selectActive(now);
  await persist(now);
}));
chrome.windows.onFocusChanged.addListener(() => serial(reconcile));
chrome.idle.onStateChanged.addListener(() => serial(reconcile));
chrome.alarms.onAlarm.addListener(() => serial(reconcile));
chrome.runtime.onStartup.addListener(() => serial(reconcile));
chrome.runtime.onInstalled.addListener(() => serial(reconcile));
