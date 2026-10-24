/* Shared, dependency-free time and policy logic. */
(function (root) {
  "use strict";
  const SITES = {
    facebook: { name: "Facebook", domain: "facebook.com", home: "https://www.facebook.com/" },
    rottentomatoes: { name: "Rotten Tomatoes", domain: "rottentomatoes.com", home: "https://www.rottentomatoes.com/" }
  };
  function siteForUrl(value) {
    try {
      const url = new URL(value);
      if (!["http:", "https:"].includes(url.protocol)) return null;
      return Object.keys(SITES).find(key => url.hostname === SITES[key].domain || url.hostname.endsWith("." + SITES[key].domain)) || null;
    } catch { return null; }
  }
  function dayKey(ms) {
    const date = new Date(ms);
    return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, "0"), String(date.getDate()).padStart(2, "0")].join("-");
  }
  function settingsFor(input = {}) {
    return Object.fromEntries(Object.keys(SITES).map(site => {
      const value = input[site] || {};
      return [site, {
        dailyEnabled: value.dailyEnabled === true,
        dailyMinutes: Number.isFinite(Number(value.dailyMinutes)) ? Math.min(1440, Math.max(1, Math.round(Number(value.dailyMinutes)))) : 30,
        cutoffEnabled: value.cutoffEnabled === true,
        cutoff: /^([01]\d|2[0-3]):[0-5]\d$/.test(value.cutoff || "") ? value.cutoff : "22:00"
      }];
    }));
  }
  function freshData(now) { return { day: dayKey(now), totals: { facebook: 0, rottentomatoes: 0 } }; }
  function rollDay(data, now) {
    if (data.day !== dayKey(now)) Object.assign(data, freshData(now));
  }
  function credit(data, site, start, end) {
    // Split at local midnight, including 23/25-hour daylight-saving days.
    if (!SITES[site] || end <= start) { rollDay(data, end); return; }
    let cursor = start;
    while (cursor < end) {
      const date = new Date(cursor);
      const midnight = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime();
      const stop = Math.min(end, midnight);
      rollDay(data, cursor);
      data.totals[site] = (data.totals[site] || 0) + stop - cursor;
      cursor = stop;
    }
    rollDay(data, end);
  }
  function reasonFor(data, settings, site, now) {
    const policy = settings[site];
    if (!policy) return "";
    const date = new Date(now);
    const minutes = date.getHours() * 60 + date.getMinutes();
    const [hour, minute] = policy.cutoff.split(":").map(Number);
    if (policy.cutoffEnabled && minutes >= hour * 60 + minute) return "Your " + policy.cutoff + " cutoff has started. Come back tomorrow.";
    const total = data.day === dayKey(now) ? (data.totals[site] || 0) : 0;
    if (policy.dailyEnabled && total >= policy.dailyMinutes * 60000) return "You reached your " + policy.dailyMinutes + "-minute daily limit. Come back tomorrow.";
    return "";
  }
  function format(ms) {
    const seconds = Math.max(0, Math.floor(ms / 1000));
    const h = Math.floor(seconds / 3600);
    const m = Math.floor(seconds / 60) % 60;
    const s = seconds % 60;
    return (h ? h + ":" + String(m).padStart(2, "0") : String(m).padStart(2, "0")) + ":" + String(s).padStart(2, "0");
  }
  root.SiteTimer = { SITES, siteForUrl, dayKey, settingsFor, freshData, rollDay, credit, reasonFor, format };
})(globalThis);
