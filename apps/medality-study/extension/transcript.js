(() => {
  'use strict';
  if (window.top !== window) return;
  const workspace = 'https://starfox1230.github.io/The-Library/apps/medality-study/';
  let host, root, label, timer, toolbarURL = location.href;
  globalThis.MedalityTrackingNotice = text => { if (!downloading) notice(text); };
  globalThis.MedalityAudioNotice = text => notice(text);
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
  async function current(expectedURL = null) {
    const guard = () => { if (expectedURL && MedalityTranscript.canonical(location.href) !== expectedURL) throw new Error("Lesson changed before capture finished."); };
    guard();
    for (let attempt = 0; attempt < 2 && !MedalityTranscript.extract(document).length; attempt++) {
      const buttons = [...document.querySelectorAll('button')].filter(button => /Transcript/.test(button.textContent) && !button.closest('[hidden], [aria-hidden="true"]'));
      const button = buttons.find(button => button.textContent.trim() === 'Transcript') || buttons[0];
      if (!button) break;
      guard(); button.click();
      await waitForCues(); guard();
    }
    guard(); return MedalityTranscript.capture(document, location.href);
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
        await chrome.storage.local.set({ [`transcript:${item.url}`]: item }); notice('Saved — open Recently watched to review');
      }
      return { ok: true, title: item.title, cues: item.cues.length };
    } catch (error) {
      const message = String(error?.message || error); notice(message); return { ok: false, error: message };
    }
  }
  globalThis.MedalityAutoCapture = async (expectedURL, progress) => {
    const sameLesson = () => { try { return MedalityTranscript.canonical(location.href) === expectedURL; } catch { return false; } };
    if (!sameLesson()) return;
    const key = `watch:${expectedURL}`, transcriptKey = `transcript:${expectedURL}`;
    let watch, recorded = false;
    try {
      const existing = await chrome.storage.local.get([key,transcriptKey]);
      if (!sameLesson()) return;
      if (existing[key] && existing[transcriptKey]?.text?.trim()) {notice('Already saved — open Recently watched to review'); return;}
      watch = existing[key] || {url:expectedURL,title:document.querySelector('h1')?.textContent.trim() || 'Medality lesson',course:document.querySelector('[aria-label="breadcrumb"] a')?.textContent.trim() || 'Medality',watchedAt:new Date().toISOString(),progress};
      // Save the watch first so a missing transcript still leaves a useful record.
      await chrome.storage.local.set({[key]:{...watch,transcriptStatus:'pending'}});
      recorded = true;
      let item;
      if (existing[transcriptKey]?.text?.trim()) {
        item = existing[transcriptKey];
      } else if (MedalityTranscript.extract(document,{includeHidden:true}).length) {
        item = MedalityTranscript.capture(document,location.href,{includeHidden:true});
      } else {
        // Use the site's panel, then restore Cases without touching playback.
        const cases = [...document.querySelectorAll('button')].find(b => /^Cases(?:\s|\()/.test(b.textContent.trim()));
        const restoreCases = cases && (cases.getAttribute('aria-selected') === 'true' || cases.getAttribute('data-state') === 'active' || [...document.querySelectorAll('a[href*="ambrahealth"]')].some(a => a.getClientRects().length)) && !cases.closest('[hidden], [aria-hidden="true"]');
        let interacted = false;
        const changed = event => {if(event.isTrusted) interacted = true;};
        document.addEventListener('pointerdown',changed,true);
        document.addEventListener('keydown',changed,true);
        try { item = await current(expectedURL); }
        finally {
          document.removeEventListener('pointerdown',changed,true);
          document.removeEventListener('keydown',changed,true);
          if (restoreCases && !interacted && sameLesson() && cases.isConnected) cases.click();
        }
      }
      if (!sameLesson() || item.url !== expectedURL) {
        await chrome.storage.local.set({[key]:{...watch,transcriptStatus:'unavailable'}}); return;
      }
      await chrome.storage.local.set({[transcriptKey]:item,[key]:{...watch,transcriptStatus:'saved'}});
      notice('Saved at 90% — open Recently watched to review');
    } catch (error) {
      if (watch) {
        try { await chrome.storage.local.set({[key]:{...watch,transcriptStatus:'unavailable'}}); } catch {}
      }
      if (sameLesson()) notice(recorded ? 'Watched lecture recorded; transcript unavailable. Use Save transcript to retry.' : 'Could not save your watched lecture. Extension storage may be full; export a backup.');
    }
  };
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
    if (toolbarURL !== location.href) {toolbarURL = location.href; if(label)label.textContent='Waiting for this lesson’s player…';}
    const heading = document.querySelector('h1');
    if (!heading || !location.pathname.includes('/unit/')) { host?.remove(); return; }
    if (!host?.isConnected) {
      host = document.createElement('div'); host.id = 'medality-transcript-tools';
      root = host.attachShadow({ mode: 'open' });
      root.innerHTML = `<style>:host{display:block;margin:12px 0;font:13px/1.45 system-ui,sans-serif;color:#e4f5f1}.bar{display:flex;align-items:center;flex-wrap:wrap;gap:8px}button,a{font:inherit;font-weight:650;border:1px solid #658c8c;border-radius:6px;padding:8px 11px;background:#173e47;color:#e4f5f1;cursor:pointer;text-decoration:none}button:hover,a:hover{background:#255765}button:focus-visible,a:focus-visible{outline:2px solid #7fe6c3;outline-offset:3px}span{color:#c9dadb;max-width:500px}</style><div class="bar"><button id="copy">Copy transcript</button><button id="save">Save transcript</button><button id="download">Download video</button><button id="history">Recently watched ↗</button><button id="audio">Restore sound</button><a href="${workspace}" target="_blank" rel="noopener noreferrer">Study workspace ↗</a><span role="status" aria-live="polite"></span></div>`;
      root.querySelector('#copy').addEventListener('click', () => void run('copy'));
      root.querySelector('#save').addEventListener('click', () => void run('save'));
      root.querySelector('#history').addEventListener('click', async () => {
        try { const result = await chrome.runtime.sendMessage({type:'medality-open-history'}); if (!result?.ok) throw new Error('Could not open Recently watched. Use the extension popup.'); }
        catch (error) { notice(error.message); }
      });
      root.querySelector('#audio').addEventListener('click', async () => {
        const ok = await globalThis.MedalityRestoreAudio?.(); notice(ok ? 'Sound restored. Press Play if the video is paused.' : 'Use Medality’s Unmute control, then press Play.');
      });
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
