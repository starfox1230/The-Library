(() => {
  if (globalThis.__nextUpInstalled) return;
  globalThis.__nextUpInstalled = true;
  const host = document.createElement('div');
  host.id = 'next-up-notion-watchlist';
  const root = host.attachShadow({mode: 'closed'});
  root.innerHTML = `<style>
    :host{all:initial;position:fixed;right:24px;bottom:24px;z-index:2147483646;color-scheme:light}
    *{box-sizing:border-box}section{width:300px;max-width:calc(100vw - 32px);background:#faf8f1;color:#19372c;border:1px solid #d4d9cb;border-radius:18px;padding:20px;box-shadow:0 8px 40px #0003;font:14px/1.5 system-ui,sans-serif}
    header{display:flex;align-items:center;justify-content:space-between}.brand{font:italic 26px Georgia,serif}small{font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#667766}
    h2{font:600 17px/1.4 system-ui;margin:14px 0 4px;overflow-wrap:anywhere}p{margin:6px 0 14px;color:#546356;font-size:12px}
    button,a{font:600 13px/1.4 system-ui;cursor:pointer;border-radius:9px}button{border:0;padding:12px;background:#234b3a;color:white;width:100%}button:hover{background:#163b2b}button:disabled{opacity:.6;cursor:wait}
    button.secondary{margin-top:8px;background:#e6ebdf;color:#234b3a}a{display:block;text-align:center;padding:10px;color:#234b3a;text-underline-offset:3px}a[hidden],button[hidden],:host([hidden]){display:none}
    #settings{background:none;color:#546356;padding:4px;width:auto;font-size:12px}button:focus-visible,a:focus-visible{outline:3px solid #b78036;outline-offset:3px}
    @media(max-width:600px){:host{right:16px;bottom:16px}section{width:260px;padding:16px}}
  </style><section aria-label="Notion Watchlist"><header><span class="brand">Next up.</span><button id="settings" aria-label="Open Next Up settings">Settings</button></header><h2></h2><p id="status" role="status" aria-live="polite">Save to Notion · For Later</p><button id="save">+ Add to Watchlist</button><a id="open" hidden target="_blank" rel="noopener noreferrer">Open in Notion ↗</a><button class="secondary" id="separate" hidden>Add as a separate entry</button></section>`;
  const titleElement = root.querySelector('h2');
  const status = root.querySelector('#status');
  const save = root.querySelector('#save');
  const open = root.querySelector('#open');
  const separate = root.querySelector('#separate');
  let current = null;
  let busy = false;
  let needsSetup = false;

  function readMedia() {
    const path = location.pathname.match(/^\/(m|tv)\/([a-zA-Z0-9_-]+)(?:\/.*)?$/);
    if (!path) return null;
    const suffix = location.pathname.split('/').filter(Boolean).slice(2);
    if (suffix.length && (path[1] === 'm' || !/^s\d+$/i.test(suffix[0]))) return null;
    const url = `https://www.rottentomatoes.com/${path[1]}/${path[2]}`;
    // TV seasons/episodes are saved as their parent show with the parent title.
    let title = '';
    if (path[1] === 'tv' && location.pathname.split('/').filter(Boolean).length > 2) {
      title = [...document.querySelectorAll('a[href]')].find(a => {
        try { return new URL(a.href).pathname.replace(/\/$/, '') === `/tv/${path[2]}` && a.textContent.trim(); } catch { return false; }
      })?.textContent.trim() || '';
      if (!title) return null;
    } else {
      title = document.querySelector('h1')?.textContent.trim() || '';
      if (!title) {
        for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
          try {
            const data = JSON.parse(script.textContent);
            const items = Array.isArray(data) ? data : [data, ...(data['@graph'] || [])];
            const item = items.find(item => ['Movie', 'TVSeries'].includes(item?.['@type']));
            if (item?.name) { title = item.name; break; }
          } catch { /* A malformed unrelated metadata block should not break the widget. */ }
        }
      }
    }
    return title ? {url, title: title.replace(/\s+/g, ' ').trim()} : null;
  }

  function refresh() {
    const media = readMedia();
    host.hidden = !media;
    if (!host.isConnected && document.body) document.body.append(host);
    if (media && (media.url !== current?.url || media.title !== current?.title)) {
      current = media;
      busy = false; needsSetup = false;
      titleElement.textContent = media.title;
      status.textContent = 'Save to Notion · For Later';
      save.hidden = false; save.disabled = false; save.textContent = '+ Add to Watchlist';
      open.hidden = true; separate.hidden = true;
    }
  }

  const settings = () => chrome.runtime.sendMessage({type: 'OPEN_SETTINGS'}).catch(() => { status.textContent = 'Extension updated. Refresh this page to reconnect.'; });
  root.querySelector('#settings').addEventListener('click', settings);
  async function add(allowSeparate = false) {
    if (needsSetup) { await settings(); return; }
    if (busy || !current) return;
    const media = current;
    busy = true; save.disabled = true; separate.disabled = true;
    status.textContent = 'Checking your Watchlist…';
    try {
      const result = await chrome.runtime.sendMessage({type: 'SAVE_MEDIA', media, allowSeparate});
      if (current !== media || location.pathname.split('/').slice(0,3).join('/') !== new URL(media.url).pathname) return;
      if (!result?.ok) throw new Error(result?.error || 'No response from the extension. Refresh and retry.');
      if (result.state === 'setup') {
        needsSetup = true; save.textContent = 'Connect Notion';
        status.textContent = 'Connect your Notion Watchlist once to start saving.';
        await settings();
        return;
      }
      open.href = result.url; open.hidden = false;
      if (result.state === 'possible') {
        status.textContent = 'An older entry has this title. Open it to check, or add a separate entry.';
        save.hidden = true; separate.hidden = false;
      } else {
        status.textContent = result.state === 'existing' ? 'Already on your Watchlist. Open it to edit.' : 'Saved as For Later. Add your thoughts in Notion.';
        save.hidden = true; separate.hidden = true;
      }
    } catch (error) {
      if (current === media) status.textContent = error.message;
    } finally {
      if (current === media) { busy = false; save.disabled = false; separate.disabled = false; }
    }
  }
  save.addEventListener('click', () => add());
  separate.addEventListener('click', () => add(true));
  refresh();
  let scheduled = false;
  new MutationObserver(() => {
    if (scheduled) return;
    scheduled = true;
    setTimeout(() => { scheduled = false; refresh(); }, 300);
  }).observe(document.documentElement, {childList: true, subtree: true});
  window.addEventListener('popstate', refresh);
  // Also detects pushState navigation without running code in the site's main world.
  setInterval(() => { if (location.href !== globalThis.__nextUpLastUrl) { globalThis.__nextUpLastUrl = location.href; refresh(); } }, 1500);
})();
