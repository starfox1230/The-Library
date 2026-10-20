(() => {
  'use strict';
  if (window.top !== window) return;
  const players = new Map(), attempted = new Set();
  let enabled = true, initialized = false, pending = false;
  function lesson() {
    try { return MedalityTranscript.canonical(location.href); } catch { return null; }
  }
  function progress(record, data) {
    const url = lesson();
    if (!initialized || !enabled || !url || record.url !== url || !record.element.isConnected) return;
    const duration = Number(data.duration), seconds = Number(data.seconds);
    // Playback position is the requested heuristic; seeking past 90% also qualifies.
    if (!(duration > 0) || !Number.isFinite(seconds) || seconds / duration < 0.9) return;
    if (attempted.has(url)) return;
    attempted.add(url);
    Promise.resolve(MedalityAutoCapture(url, Math.min(1, seconds / duration))).catch(() => {});
  }
  function frameURL(element) {
    try {
      const url = new URL(element.getAttribute('src'));
      return url.protocol === 'https:' && url.hostname === 'player.vimeo.com' && /^\/video\/\d+$/.test(url.pathname) ? url.href : null;
    } catch { return null; }
  }
  function detach(record) {
    if (record.player) {
      record.player.off('timeupdate', record.progress);
      record.player.off('loaded', record.loaded);
    } else {
      record.element.removeEventListener('timeupdate', record.progress);
      record.element.removeEventListener('loadedmetadata', record.loaded);
    }
  }
  function scan() {
    pending = false;
    for (const [element, record] of players) {
      if (!element.isConnected || (record.src && record.src !== frameURL(element))) {
        detach(record); players.delete(element);
      }
    }
    if (!lesson()) return;
    const elements = [...document.querySelectorAll('iframe')].filter(frameURL).concat([...document.querySelectorAll('video')]);
    for (const element of elements) {
      if (players.has(element)) continue;
      const record = { element, url: lesson(), src: element.tagName === 'IFRAME' ? frameURL(element) : null };
      record.loaded = () => { record.url = lesson(); };
      record.progress = data => progress(record, record.src ? data : {seconds:element.currentTime, duration:element.duration});
      players.set(element, record);
      if (record.src) {
        try {
          record.player = new Vimeo.Player(element);
          record.player.on('timeupdate', record.progress);
          record.player.on('loaded', record.loaded);
        } catch { players.delete(element); }
      } else {
        element.addEventListener('timeupdate', record.progress);
        element.addEventListener('loadedmetadata', record.loaded);
      }
    }
  }
  new MutationObserver(() => {
    if (!pending) { pending = true; queueMicrotask(scan); }
  }).observe(document.documentElement, {childList:true, subtree:true, attributes:true, attributeFilter:['src']});
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.autoCapture) enabled = changes.autoCapture.newValue !== false;
  });
  chrome.storage.local.get({autoCapture:true}).then(value => {
    enabled = value.autoCapture !== false; initialized = true; scan();
  }).catch(() => { initialized = true; scan(); });
})();
