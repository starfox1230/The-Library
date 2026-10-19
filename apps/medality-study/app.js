(() => {
  'use strict';
  const C = MedalityCore, key = 'medality-study-v1';
  const $ = id => document.getElementById(id);
  const selected = new Set();
  let saved = {}, editing = null, visible = [], request = null;
  try { saved = JSON.parse(localStorage.getItem(key) || '{}'); if (!saved || typeof saved !== 'object' || Array.isArray(saved)) saved = {}; } catch { saved = {}; }
  function message(text) { $('message').textContent = text; }
  function persist(next) {
    try { localStorage.setItem(key, JSON.stringify(next)); saved = next; return true; }
    catch { message('Could not save: browser storage may be full or blocked. Export a backup before closing this page.'); return false; }
  }
  function items() {
    const known = new Map(MEDALITY_COURSE.map(item => [item.url, { ...item, ...saved[item.url], url: item.url }]));
    Object.values(saved).forEach(item => { try { const clean = C.normalize(item); if (!known.has(clean.url)) known.set(clean.url, { ...clean, note: String(item.note || ''), group: 'Other', focus: '' }); } catch {} });
    return [...known.values()];
  }
  function render() {
    const all = items(), search = $('search').value.toLowerCase(), group = $('group').value;
    visible = all.filter(item => (!group || item.group === group) && (!$('only-saved').checked || item.text?.trim()) && `${item.title} ${item.focus || ''} ${item.note || ''}`.toLowerCase().includes(search));
    $('saved-count').textContent = `${all.filter(item => item.text?.trim()).length} / ${all.length}`;
    const list = $('lesson-list'); list.replaceChildren();
    for (const item of visible) {
      const row = document.createElement('div'); row.className = 'lesson';
      const box = document.createElement('input'); box.type = 'checkbox'; box.checked = selected.has(item.url); box.id = `lesson-${all.indexOf(item)}`;
      box.addEventListener('change', () => { box.checked ? selected.add(item.url) : selected.delete(item.url); updatePacket(); });
      const label = document.createElement('label'); label.htmlFor = box.id; label.append(document.createTextNode(item.title));
      const meta = document.createElement('span'); meta.className = 'meta';
      const availability = item.text?.trim() ? 'Transcript saved' : 'Transcript not captured';
      meta.textContent = `${item.minutes ? `${item.minutes} min · ` : ''}${item.group || 'Imported'} · ${availability}`;
      if (item.text?.trim()) meta.classList.add('ready'); label.append(meta);
      const edit = document.createElement('button'); edit.textContent = item.text?.trim() ? 'View / edit' : 'Add text'; edit.setAttribute('aria-label', `Edit ${item.title}`); edit.addEventListener('click', () => editItem(item));
      row.append(box, label, edit); list.append(row);
    }
    if (!visible.length) { const empty = document.createElement('p'); empty.className = 'empty'; empty.textContent = 'No lessons match. Clear the search or change the filters.'; list.append(empty); }
    updatePacket();
  }
  function updatePacket() {
    const chosen = items().filter(item => selected.has(item.url));
    const output = C.packet(chosen, { mode: $('mode').value, timestamps: $('timestamps').checked, prompt: $('prompt').checked });
    $('preview').value = output.text;
    $('selection-count').textContent = `${chosen.length} selected`;
    const words = output.text.trim() ? output.text.trim().split(/\s+/).length : 0;
    $('word-count').textContent = `${words.toLocaleString()} words`;
    const hiddenCount = chosen.filter(item => !visible.some(v => v.url === item.url)).length;
    $('packet-warning').textContent = [output.missing.length ? `${output.missing.length} selected lessons have no captured transcript; missing transcript text is omitted.` : '', hiddenCount ? `${hiddenCount} selected lessons are outside the current filter.` : '', words > 12000 ? 'Large packet: consider splitting it into smaller groups for ChatGPT.' : ''].filter(Boolean).join(' ');
    $('copy-packet').disabled = !output.text; $('download-packet').disabled = !output.text;
  }
  async function copy(text, target = message, area = $('preview')) {
    try { await navigator.clipboard.writeText(text); target('Copied to clipboard.'); }
    catch { area.focus(); area.select(); target('Automatic copying was blocked. The text is selected; press Ctrl+C (Command+C on Mac).'); }
  }
  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const link = document.createElement('a'); link.href = url; link.download = name; link.click(); setTimeout(() => URL.revokeObjectURL(url), 10000);
  }
  function editItem(item) {
    editing = item; $('edit-title').textContent = item.title; $('edit-link').href = item.url;
    $('edit-focus').textContent = item.focus || ''; $('edit-text').value = item.text || ''; $('edit-note').value = item.note || ''; $('editor-message').textContent = '';
    $('editor').showModal();
  }
  function importItems(raw) {
    const clean = C.imported(raw), next = { ...saved };
    for (const item of clean) {
      if (!item.text.trim()) continue;
      next[item.url] = { ...saved[item.url], ...item, note: saved[item.url]?.note || '' };
    }
    if (persist(next)) { render(); message(`Imported ${clean.filter(item => item.text.trim()).length} transcripts. Existing notes were kept.`); }
  }
  $('search').addEventListener('input', render); $('group').addEventListener('change', render); $('only-saved').addEventListener('change', render);
  $('select-all').addEventListener('click', () => { visible.forEach(item => selected.add(item.url)); render(); });
  $('select-none').addEventListener('click', () => { selected.clear(); render(); });
  $('select-first').addEventListener('click', () => { selected.clear(); MEDALITY_COURSE.filter(item => item.firstPass).forEach(item => selected.add(item.url)); render(); });
  ['mode','timestamps','prompt'].forEach(id => $(id).addEventListener('change', updatePacket));
  $('copy-packet').addEventListener('click', () => void copy($('preview').value));
  $('download-packet').addEventListener('click', () => download('liver-mri-study-packet.txt', $('preview').value, 'text/plain'));
  $('export-backup').addEventListener('click', () => download('liver-mri-study-backup.json', JSON.stringify({ format: 'medality-study-v1', items: Object.values(saved) }, null, 2), 'application/json'));
  $('save-editor').addEventListener('click', () => {
    if (!editing) return;
    const old = saved[editing.url] || {}, text = $('edit-text').value;
    const updated = { ...editing, ...old, title: editing.title, url: editing.url, text, note: $('edit-note').value, cues: text === (old.text || '') ? old.cues || [] : [], capturedAt: new Date().toISOString() };
    if (persist({ ...saved, [editing.url]: updated })) { $('editor').close(); render(); message('Saved in this browser.'); }
  });
  $('copy-one').addEventListener('click', () => {
    const text = $('edit-text').value.trim();
    if (!text) { $('editor-message').textContent = 'Add a transcript first.'; return; }
    void copy(`${editing.title}\n${editing.url}\n\n${text}`, text => { $('editor-message').textContent = text; }, $('edit-text'));
  });
  $('import-file').addEventListener('click', () => $('file').click());
  $('file').addEventListener('change', async () => {
    const file = $('file').files[0]; if (!file) return;
    try {
      if (file.size > 10000000) throw new Error('Choose a JSON file smaller than 10 MB.');
      const raw = JSON.parse(await file.text());
      // Preserve notes from a workspace backup, including entries without a transcript.
      const clean = C.imported(raw); const next = { ...saved };
      for (const item of clean) {
        const original = (Array.isArray(raw) ? raw : raw.items).find(entry => { try { return C.url(entry.url) === item.url; } catch { return false; } });
        next[item.url] = { ...saved[item.url], ...item, note: typeof original?.note === 'string' ? original.note.slice(0,200000) : saved[item.url]?.note || '' };
      }
      if (persist(next)) { render(); message(`Imported ${clean.length} lesson entries.`); }
    } catch (error) { message(`Import failed: ${error.message}`); }
    $('file').value = '';
  });
  $('import-extension').addEventListener('click', () => {
    if (request) return;
    request = crypto.randomUUID(); const id = request;
    message('Looking for saved extension captures…');
    window.postMessage({ channel: 'medality-study', type: 'request-captures', requestId: id }, location.origin);
    setTimeout(() => {
      if (request !== id) return; request = null;
      message('Extension not detected. Update to v1.1, refresh this page and try again. You can also export JSON from the extension popup and use Import JSON file.');
    }, 2500);
  });
  window.addEventListener('message', event => {
    if (event.source !== window || event.origin !== location.origin || event.data?.channel !== 'medality-study' || event.data.requestId !== request || !request) return;
    if (!['captures','capture-error'].includes(event.data.type)) return;
    request = null;
    if (event.data.type === 'capture-error') { message('Could not read extension storage. Try the JSON export/import route.'); return; }
    try { importItems(event.data.items); } catch (error) { message(`Import failed: ${error.message}`); }
  });
  render();
})();
