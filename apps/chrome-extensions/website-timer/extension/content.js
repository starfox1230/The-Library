(() => {
  "use strict";
  const T = SiteTimer;
  const site = T.siteForUrl(location.href);
  if (!site || document.getElementById("library-website-timer")) return;
  const host = document.createElement("div");
  host.id = "library-website-timer";
  host.style.cssText = "all:initial!important;position:fixed!important;top:10px!important;right:12px!important;z-index:2147483647!important;display:block!important;";
  const shadow = host.attachShadow({ mode: "closed" });
  shadow.innerHTML = `<style>
    :host{color-scheme:light}
    .bar{box-sizing:border-box;display:flex;align-items:center;gap:15px;flex-wrap:wrap;max-width:calc(100vw - 24px);padding:10px 14px;border:1px solid #ff8b8b;border-radius:12px;background:#b91c1c;color:#fff;box-shadow:0 5px 22px #450a0a44;font:13px/1.35 system-ui,sans-serif}
    .name{font-weight:750}.clock{font-variant-numeric:tabular-nums;font-size:18px;font-weight:750}
    .label{font-size:10px;text-transform:uppercase;letter-spacing:.08em;opacity:.8;display:block}
    button{font:inherit;color:#fff;background:#ffffff1a;border:1px solid #ffffff66;border-radius:7px;padding:7px 10px;cursor:pointer}
    button:hover,button:focus-visible{background:#ffffff35;outline:2px solid #fff;outline-offset:2px}
    .state{font-size:10px;opacity:.85;display:block;max-width:110px}
    @media(max-width:460px){.bar{gap:10px;padding:8px 10px}.clock{font-size:15px}.name{font-size:11px}}
  </style><div class="bar" role="region" aria-label="Website time">
    <div><span class="name"></span><span class="state">Connecting…</span></div>
    <div><span class="label">This visit</span><span class="clock visit">00:00</span></div>
    <div><span class="label">Today</span><span class="clock today">00:00</span></div>
    <button type="button" aria-label="Set website time limits">Limits</button>
  </div>`;
  shadow.querySelector(".name").textContent = T.SITES[site].name;
  shadow.querySelector("button").addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "openSettings" }).catch(() => {});
  });
  document.documentElement.append(host);
  let busy = false, stopped = false;
  async function pulse() {
    if (busy || stopped) return;
    if (!host.isConnected) document.documentElement.append(host);
    busy = true;
    try {
      const result = await chrome.runtime.sendMessage({ type: "pulse" });
      if (!result?.ok) throw new Error("unavailable");
      shadow.querySelector(".visit").textContent = T.format(result.visitMs);
      shadow.querySelector(".today").textContent = T.format(result.sites[site].todayMs);
      shadow.querySelector(".state").textContent = result.sites[site].blocked ? "Limit reached" : result.counting ? "Counting active time" : "Paused";
    } catch {
      shadow.querySelector(".state").textContent = "Refresh page to reconnect";
      stopped = true;
      clearInterval(interval);
    } finally { busy = false; }
  }
  const interval = setInterval(() => { if (!document.hidden) pulse(); }, 1000);
  document.addEventListener("visibilitychange", pulse);
  window.addEventListener("pageshow", pulse);
  pulse();
})();
