(() => {
  'use strict';
  const defaults = { enabled: true, speed: 2 };
  const speeds = [1, 1.25, 1.5, 1.75, 2];
  let prefs = { ...defaults };
  let initialized = false;
  let scanPending = false;
  const records = new Map();
  const nativeEvents = ['loadedmetadata', 'play', 'ratechange', 'emptied'];
  const vimeoEvents = ['loaded', 'play', 'playbackratechange'];

  function settings(value) {
    return {
      enabled: typeof value.enabled === 'boolean' ? value.enabled : true,
      speed: speeds.includes(Number(value.speed)) ? Number(value.speed) : 2
    };
  }

  function isVimeo(frame) {
    try {
      const url = new URL(frame.getAttribute('src') || '', document.baseURI);
      return url.protocol === 'https:' && url.hostname === 'player.vimeo.com' && /^\/video\/\d+/.test(url.pathname);
    } catch { return false; }
  }

  function timeout(promise) {
    let timer;
    return Promise.race([
      promise,
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Player did not respond.')), 5000); })
    ]).finally(() => clearTimeout(timer));
  }

  async function apply(record) {
    if (!initialized || !prefs.enabled || record.busy || !record.ready || !record.element.isConnected) return;
    record.busy = true;
    const desired = prefs.speed;
    try {
      if (record.kind === 'vimeo') {
        const current = await timeout(record.player.getPlaybackRate());
        if (!prefs.enabled || prefs.speed !== desired || !record.element.isConnected) return;
        if (Math.abs(current - desired) > 0.01) {
          await timeout(record.player.setPlaybackRate(desired));
        }
        record.actual = await timeout(record.player.getPlaybackRate());
      } else {
        record.element.defaultPlaybackRate = desired;
        if (Math.abs(record.element.playbackRate - desired) > 0.01) record.element.playbackRate = desired;
        record.actual = record.element.playbackRate;
      }
      record.error = Math.abs(record.actual - desired) < 0.01 ? '' : 'Player has not accepted the selected speed.';
    } catch (error) {
      record.actual = null;
      record.error = String(error?.message || error);
    } finally {
      record.busy = false;
    }
  }

  function attach(element, kind) {
    if (records.has(element)) return;
    const record = { element, kind, actual: null, ready: kind === 'native', busy: false, error: '' };
    record.update = () => { void apply(record); };
    records.set(element, record);
    if (kind === 'native') {
      nativeEvents.forEach(event => element.addEventListener(event, record.update));
      record.update();
    } else {
      try {
        record.player = new Vimeo.Player(element);
        vimeoEvents.forEach(event => record.player.on(event, record.update));
        record.player.ready().then(() => {
          record.ready = true;
          record.update();
        }).catch(error => { record.error = String(error?.message || error); });
      } catch (error) { record.error = String(error?.message || error); }
    }
  }

  function scan() {
    scanPending = false;
    for (const [element, record] of records) {
      if (!element.isConnected || (record.kind === 'vimeo' && !isVimeo(element))) {
        if (record.kind === 'native') nativeEvents.forEach(event => element.removeEventListener(event, record.update));
        else if (record.player) vimeoEvents.forEach(event => record.player.off(event, record.update));
        // Player.destroy() removes the site's iframe; never call it here.
        records.delete(element);
      }
    }
    document.querySelectorAll('iframe').forEach(frame => { if (isVimeo(frame)) attach(frame, 'vimeo'); });
    document.querySelectorAll('video').forEach(video => attach(video, 'native'));
  }

  function scheduleScan() {
    if (!scanPending) {
      scanPending = true;
      queueMicrotask(scan);
    }
  }

  chrome.storage.onChanged.addListener((changes, area) => {
    if (area !== 'local') return;
    prefs = settings({
      enabled: changes.enabled ? changes.enabled.newValue : prefs.enabled,
      speed: changes.speed ? changes.speed.newValue : prefs.speed
    });
    records.forEach(record => record.update());
  });

  chrome.runtime.onMessage.addListener((message, _sender, reply) => {
    if (message?.type !== 'medality-speed-status') return;
    scan();
    reply({
      enabled: prefs.enabled,
      speed: prefs.speed,
      players: [...records.values()].map(record => ({
        kind: record.kind,
        ready: record.ready,
        actual: record.actual,
        error: record.error
      }))
    });
  });

  new MutationObserver(scheduleScan).observe(document.documentElement, {
    childList: true, subtree: true, attributes: true, attributeFilter: ['src']
  });
  chrome.storage.local.get(defaults).then(value => {
    // Re-read the final stored values before first applying any speed.
    prefs = settings(value);
    initialized = true;
    scan();
    records.forEach(record => record.update());
  }).catch(() => {
    initialized = true;
    scan();
  });
  // Covers player resets, same-frame lesson changes, and delayed media setup.
  setInterval(() => { scan(); records.forEach(record => record.update()); }, 2000);
})();
