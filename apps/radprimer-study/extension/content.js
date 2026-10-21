(function () {
  'use strict';
  let host, ui, current = '', busy = false, timer;
  const drafts = new Map();
  const message = value => chrome.runtime.sendMessage(value);
  function draft() { if (!drafts.has(current)) drafts.set(current, { notes: '', highlights: [] }); return drafts.get(current); }
  function status(text) { ui.querySelector('[role=status]').textContent = text; }
  async function save(anki) {
    if (busy) return;
    busy = true;
    const key = current, options = { ...draft(), highlights: [...draft().highlights], anki };
    ui.querySelectorAll('button,textarea').forEach(b => { b.disabled = true; });
    try {
      const capture = await RadCapture.capture(document, RadCapture.fetchImage, status);
      status('Writing your private library…');
      const result = await message({ type: 'rp:save', capture, options });
      if (!result?.ok) throw new Error(result?.error || 'Extension unavailable. Reload this page after reloading the extension.');
      drafts.delete(key);
      if (current === key) { ui.querySelector('textarea').value = ''; ui.querySelector('[data-highlights]').replaceChildren(); }
      const missing = result.media.failed || result.media.saved < result.media.total;
      const firstImageError = capture.groups.flatMap(g => g.images).find(i => i.error)?.error;
      status((anki ? 'Saved + queued for Anki. ' : 'Saved. ') + result.media.saved + '/' + result.media.total + ' images offline.' +
        (missing ? ' Some image files failed—save again to retry.' + (firstImageError ? ' ' + firstImageError + '.' : '') : '') +
        (!result.answered ? ' Question only: answer it, then save again for explanations and keys.' : ' Answers, explanations and image keys included.'));
    } catch (error) { status('Not saved: ' + error.message); }
    finally { busy = false; ui.querySelectorAll('button,textarea').forEach(b => { b.disabled = false; }); refresh(); }
  }
  function addHighlight() {
    const selected = window.getSelection()?.toString().trim();
    if (!selected) { status('Select a specific fact on the page, then choose Add selected fact.'); return; }
    const d = draft(); if (!d.highlights.includes(selected)) d.highlights.push(selected);
    renderHighlights(); status('Selected fact added. Save case or Save + Anki to keep it.');
  }
  function renderHighlights() {
    const list = ui.querySelector('[data-highlights]'); list.replaceChildren();
    draft().highlights.forEach((text, index) => {
      const li = document.createElement('li'), button = document.createElement('button');
      li.append(document.createTextNode(text + ' ')); button.textContent = '×'; button.title = 'Remove selected fact';
      button.onclick = () => { draft().highlights.splice(index, 1); renderHighlights(); };
      li.append(button); list.append(li);
    });
  }
  function mount() {
    host = document.createElement('section'); host.id = 'rp-case-library'; host.setAttribute('aria-label', 'Private case library');
    ui = host.attachShadow({ mode: 'open' });
    ui.innerHTML = `<style>
      :host{display:block;margin:14px 0 20px;color:#e5e7e8;font:14px/1.5 Arial,sans-serif}*{box-sizing:border-box}
      .panel{background:#232a2d;border:1px solid #465157;border-left:3px solid #39b9dd;border-radius:5px;padding:12px 15px}
      .bar{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.brand{color:#55cae9;font-weight:bold;margin-right:auto}
      button,summary{cursor:pointer}button{font:inherit;padding:7px 13px;border:1px solid #50616a;background:#303b41;color:#edf6f8;border-radius:4px}
      button:hover{background:#3d515a}button.primary{background:#32b5db;color:#102b35;border-color:#32b5db;font-weight:bold}button:disabled{opacity:.55;cursor:wait}
      button:focus-visible,textarea:focus-visible,summary:focus-visible{outline:2px solid #77d8ef;outline-offset:2px}
      details{margin-top:8px}summary{color:#bacbd1;font-size:13px}textarea{width:100%;min-height:65px;margin-top:8px;background:#1d2326;color:#edf3f5;border:1px solid #50616a;border-radius:4px;padding:9px;font:inherit}
      .help,[role=status]{font-size:12px;color:#b7cbd3;margin:7px 0 0}ul{padding-left:20px;margin:8px 0}li{margin:6px 0}li button{padding:0 7px}
    </style><div class="panel"><div class="bar"><span class="brand">CASE LIBRARY</span>
      <button class="primary" data-save>Save case</button><button data-anki>Save + Anki</button><button data-open>My cases ↗</button></div>
      <details><summary>Add a note or select facts for Anki</summary><textarea aria-label="What do you want to remember?" placeholder="What exactly do I want to remember from this case?"></textarea>
      <button data-highlight>Add selected fact</button><ul data-highlights></ul><p class="help">Select text anywhere in the question or explanation, then add it here. Notes stay with this case.</p></details>
      <p role="status" aria-live="polite">Save this case for occasional review. Reserve Anki for the facts you choose.</p></div>`;
    ui.querySelector('[data-save]').onclick = () => save(false);
    ui.querySelector('[data-anki]').onclick = () => save(true);
    ui.querySelector('[data-open]').onclick = () => message({ type: 'rp:open' }).catch(() => status('Reload RadPrimer after reloading the extension.'));
    ui.querySelector('[data-highlight]').onpointerdown = e => e.preventDefault();
    ui.querySelector('[data-highlight]').onclick = addHighlight;
    ui.querySelector('textarea').oninput = e => { draft().notes = e.target.value; };
  }
  function refresh() {
    if (busy) return;
    const row = document.querySelector('.mcq-title-row');
    if (!row || !document.querySelector('#mcq-question-stem')) { host?.remove(); return; }
    if (!host) mount();
    if (!host.isConnected) row.after(host);
    const sig = RadCapture.signature(document);
    if (sig !== current) {
      current = sig; ui.querySelector('textarea').value = draft().notes; renderHighlights();
      status('Save this case for occasional review. Reserve Anki for the facts you choose.');
    }
  }
  const observer = new MutationObserver(() => { clearTimeout(timer); timer = setTimeout(refresh, 200); });
  observer.observe(document.body, { childList: true, subtree: true }); refresh();
})();
