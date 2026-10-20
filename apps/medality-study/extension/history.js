(() => {
  'use strict';
  const storage = globalThis.chrome?.storage || globalThis.MedalityStorage;
  const H = MedalityHistory, $ = id => document.getElementById(id), selected = new Set();
  let rows = [], visible = [], state = {};
  const notice = text => { $('status').textContent = text; };
  function download(name, text, type) {
    const url = URL.createObjectURL(new Blob([text], {type}));
    const a = document.createElement('a'); a.href = url; a.download = name; a.click();
    setTimeout(()=>URL.revokeObjectURL(url),10000);
  }
  function packet() {
    const chosen = rows.filter(row=>selected.has(row.url));
    const result = H.packet(chosen,{timestamps:$('timestamps').checked,prompt:$('prompt').checked});
    $('preview').value = result.text;
    $('selected-count').textContent = `${chosen.length} selected · ${chosen.filter(r=>r.text.trim()).length} transcript${chosen.filter(r=>r.text.trim()).length===1?'':'s'}`;
    $('warning').textContent = result.missing ? `${result.missing} selected lecture${result.missing===1?' has':'s have'} no saved transcript and will be omitted from copied text. Open the lesson and use Save transcript to retry.` : '';
    $('copy').disabled = !result.text; $('text-download').disabled = !result.text;
  }
  function render() {
    rows = H.entries(state);
    const query = $('search').value.toLowerCase();
    visible = rows.filter(row=>`${row.title} ${row.course}`.toLowerCase().includes(query));
    $('count').textContent = `${rows.filter(r=>r.watchedAt).length} watched lecture${rows.filter(r=>r.watchedAt).length===1?'':'s'} · ${rows.filter(r=>r.text.trim()).length} saved transcript${rows.filter(r=>r.text.trim()).length===1?'':'s'}`;
    $('automatic').checked = state.autoCapture !== false;
    const list = $('lectures'); list.replaceChildren();
    visible.forEach((row,index)=>{
      const card = document.createElement('article'); card.className = 'lecture';
      const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.id = `lecture-${index}`; checkbox.checked = selected.has(row.url);
      checkbox.addEventListener('change',()=>{checkbox.checked?selected.add(row.url):selected.delete(row.url);packet();});
      const content = document.createElement('div');
      const label = document.createElement('label'); label.htmlFor = checkbox.id; label.className = 'title'; label.textContent = row.title;
      const meta = document.createElement('p'); meta.className = 'meta';
      const when = row.watchedAt || row.capturedAt;
      meta.textContent = `${row.course} · ${row.watchedAt?'Watched':'Manually saved'}${when?' '+new Date(when).toLocaleString():''}`;
      const badge = document.createElement('p'); badge.className = `meta ${row.text.trim()?'badge':'missing'}`; badge.textContent = row.text.trim()?'Transcript saved':'Transcript unavailable — lecture recorded';
      const source = document.createElement('a'); source.href = row.url; source.target = '_blank'; source.rel = 'noopener noreferrer'; source.textContent = row.text.trim()?'Open lecture ↗':'Open lecture to retry transcript ↗';
      content.append(label,meta,badge,source);
      if (row.text.trim()) {
        const details = document.createElement('details'), summary = document.createElement('summary'), text = document.createElement('pre');
        summary.textContent = 'Preview transcript'; text.textContent = row.text;
        details.append(summary,text); content.append(details);
      }
      card.append(checkbox,content); list.append(card);
    });
    if (!visible.length) {
      const empty = document.createElement('p'); empty.className = 'empty';
      empty.textContent = rows.length?'No matching lectures. Try another search.':'Your next lectures will appear here automatically at 90% playback. You can also use Save transcript on any lesson now. Past watching is not reconstructed.';
      list.append(empty);
    }
    packet();
  }
  async function load() {
    try { state = await storage.local.get(null); render(); }
    catch { notice('Could not read the local library. Reopen this page.'); }
  }
  $('search').addEventListener('input',render);
  $('latest').addEventListener('click',()=>{selected.clear();visible.slice(0,5).forEach(r=>selected.add(r.url));render();});
  $('all').addEventListener('click',()=>{visible.forEach(r=>selected.add(r.url));render();});
  $('none').addEventListener('click',()=>{selected.clear();render();});
  ['timestamps','prompt'].forEach(id=>$(id).addEventListener('change',packet));
  $('automatic').addEventListener('change',async()=>{
    try { await storage.local.set({autoCapture:$('automatic').checked}); notice($('automatic').checked?'Automatic saving enabled.':'Automatic saving paused. Your saved library is kept.'); }
    catch { notice('Could not save this preference.'); void load(); }
  });
  $('copy').addEventListener('click',async()=>{
    try { await navigator.clipboard.writeText($('preview').value); notice('Copied in viewing order. Paste into ChatGPT.'); }
    catch { $('preview').focus();$('preview').select();notice('Text selected. Press Ctrl+C or Command+C to copy.'); }
  });
  $('text-download').addEventListener('click',()=>download('medality-review-packet.txt',$('preview').value,'text/plain'));
  $('backup').addEventListener('click',()=>{
    if (!rows.length) return notice('No lectures saved yet.');
    download('medality-watched-library.json',JSON.stringify({format:'medality-study-v1',items:rows},null,2),'application/json');
    notice('Library backup downloaded. Keep it before removing the extension.');
  });
  $('restore').addEventListener('click',()=>$('file').click());
  $('file').addEventListener('change',async()=>{
    try {
      const file = $('file').files[0]; if (!file) return;
      if (file.size>10000000) throw new Error('Choose a library smaller than 10 MB.');
      const raw = JSON.parse(await file.text()), entries = Array.isArray(raw)?raw:raw.items;
      if (!Array.isArray(entries) || entries.length>500) throw new Error('Choose an exported Medality library file.');
      const clean = entries.map(H.clean), next = {};
      for (const row of clean) {
        const old = state[`transcript:${row.url}`];
        if (row.text.trim()) next[`transcript:${row.url}`] = {...old,...row};
        if (row.watchedAt) next[`watch:${row.url}`] = {url:row.url,title:row.title,course:row.course,watchedAt:row.watchedAt,transcriptStatus:row.transcriptStatus};
      }
      await storage.local.set(next); await load(); notice(`Imported ${clean.length} lecture entries.`);
    } catch (error) { notice(`Import failed: ${error.message}`); }
    finally { $('file').value = ''; }
  });
  storage.onChanged.addListener((_changes,area)=>{if(area==='local') void load();});
  void load();
})();
