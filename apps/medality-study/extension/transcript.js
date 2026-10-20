(() => {
  'use strict';
  if (window.top !== window) return;
  const workspace = 'https://starfox1230.github.io/The-Library/apps/medality-study/';
  let host, root, label, timer;
  function notice(text) { if (label) label.textContent = text; }
  function waitForCues(milliseconds = 1800) {
    return new Promise(resolve => {
      let observer;
      const finish = () => { observer?.disconnect(); clearTimeout(expiry); resolve(); };
      const expiry = setTimeout(finish, milliseconds);
      observer = new MutationObserver(() => { if (MedalityTranscript.extract(document).length) finish(); });
      observer.observe(document.documentElement, { subtree: true, childList: true, characterData: true });
      if (MedalityTranscript.extract(document).length) finish();
    });
  }
  async function current() {
    for (let attempt = 0; attempt < 2 && !MedalityTranscript.extract(document).length; attempt++) {
      const buttons = [...document.querySelectorAll('button')].filter(button => /Transcript/.test(button.textContent) && !button.closest('[hidden], [aria-hidden="true"]'));
      const button = buttons.find(button => button.textContent.trim() === 'Transcript') || buttons[0];
      if (!button) break;
      button.click();
      await waitForCues();
    }
    return MedalityTranscript.capture(document, location.href);
  }
  async function copy(text) {
    try { await navigator.clipboard.writeText(text); }
    catch {
      const area = document.createElement('textarea');
      area.value = text; area.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;opacity:0';
      const focused = document.activeElement;
      document.body.append(area); area.select();
      const ok = document.execCommand('copy'); area.remove(); focused?.focus();
      if (!ok) throw new Error('Clipboard unavailable. Use the extension popup or copy manually.');
    }
  }
  async function run(action) {
    try {
      notice('Reading transcript…');
      const item = await current();
      if (action === 'copy') {
        await copy(MedalityTranscript.format(item)); notice('Transcript copied');
      } else if (action === 'save') {
        await chrome.storage.local.set({ [`transcript:${item.url}`]: item }); notice('Saved — import it in Study workspace');
      }
      return { ok: true, title: item.title, cues: item.cues.length };
    } catch (error) {
      const message = String(error?.message || error); notice(message); return { ok: false, error: message };
    }
  }
  let downloading = false;
  async function downloadVideo() {
    if (downloading) return;
    const button = root.querySelector('#download');
    try {
      const frame = [...document.querySelectorAll('iframe[src]')].find(f => {
        try { const u = new URL(f.src); return u.protocol === 'https:' && u.hostname === 'player.vimeo.com' && /^\/video\/[0-9]+$/.test(u.pathname); } catch { return false; }
      });
      if (!frame) throw new Error('No supported video found on this lesson.');
      const video = new URL(frame.src);
      const hash = video.searchParams.get('h');
      video.search = hash ? new URLSearchParams({h:hash}).toString() : '';
      downloading = true; button.disabled = true; notice('Starting video download…');
      let result = await chrome.runtime.sendMessage({type:'medality-download',video:video.href});
      if (!result?.ok) throw new Error(result?.error || 'Download helper unavailable.');
      const job = result.job;
      do {
        await new Promise(resolve => setTimeout(resolve, 1500));
        result = await chrome.runtime.sendMessage({type:'medality-download-status',job});
        if (!result?.ok) throw new Error(result?.error || 'Lost connection to download helper.');
        notice(result.message);
      } while (result.state === 'working');
      if (result.state === 'error') throw new Error(result.message);
    } catch (error) { notice(String(error.message || error)); }
    finally { downloading = false; button.disabled = false; }
  }
  function mount() {
    const heading = document.querySelector('h1');
    if (!heading || !location.pathname.includes('/unit/')) { host?.remove(); return; }
    if (!host?.isConnected) {
      host = document.createElement('div'); host.id = 'medality-transcript-tools';
      root = host.attachShadow({ mode: 'open' });
      root.innerHTML = `<style>:host{display:block;margin:12px 0;font:13px/1.45 system-ui,sans-serif;color:#e4f5f1}.bar{display:flex;align-items:center;flex-wrap:wrap;gap:8px}button,a{font:inherit;font-weight:650;border:1px solid #658c8c;border-radius:6px;padding:8px 11px;background:#173e47;color:#e4f5f1;cursor:pointer;text-decoration:none}button:hover,a:hover{background:#255765}button:focus-visible,a:focus-visible{outline:2px solid #7fe6c3;outline-offset:3px}span{color:#c9dadb;max-width:500px}</style><div class="bar"><button id="copy">Copy transcript</button><button id="save">Save transcript</button><button id="download">Download video</button><a href="${workspace}" target="_blank" rel="noopener noreferrer">Study workspace ↗</a><span role="status" aria-live="polite"></span></div>`;
      root.querySelector('#copy').addEventListener('click', () => void run('copy'));
      root.querySelector('#save').addEventListener('click', () => void run('save'));
      root.querySelector('#download').addEventListener('click', downloadVideo);
      label = root.querySelector('span'); heading.after(host);
    }
    const count = MedalityTranscript.extract(document).length;
    const next = count ? `${count} transcript lines ready · Ctrl+Shift+Y to copy` : 'Open Transcript to capture available text';
    if (!label.textContent || /transcript lines ready|Open Transcript to capture/.test(label.textContent)) notice(next);
  }
  chrome.runtime.onMessage.addListener((message, _sender, reply) => {
    if (message?.type === 'medality-transcript-action' && ['copy', 'save'].includes(message.action)) {
      run(message.action).then(reply); return true;
    }
    if (message?.type === 'medality-transcript-status') {
      reply({ available: MedalityTranscript.extract(document).length > 0 });
    }
  });
  new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(mount, 120); })
    .observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  mount();
})();
