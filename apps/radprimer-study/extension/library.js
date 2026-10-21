(async function () {
  'use strict';
  const $ = selector => document.querySelector(selector);
  let cases = [], view = 'all', active = '', revealed = false, chosen = -1;
  const noteDrafts = new Map(), groupState = new Map();
  const isExtension = location.protocol === 'chrome-extension:';
  $('#web-notice').hidden = isExtension;
  if (isExtension) {
    $('.wordmark').href = 'library.html';
    $('.wordmark').title = 'Your private case library';
  }
  function el(tag, text, cls) { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; if (cls) e.className = cls; return e; }
  function button(text, action, cls) { const b = el('button', text, cls); b.type = 'button'; b.onclick = () => Promise.resolve(action()).catch(showError); return b; }
  function showStatus(text) { $('#status').textContent = text; }
  function showError(error) { showStatus(error.message || String(error)); }
  function date(value) { return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' }); }
  function due(c) { return !c.archived && c.tier !== 'reference' && (!c.dueAt || Date.parse(c.dueAt) <= Date.now()); }
  function matches(c) {
    if (view === 'archive' ? !c.archived : c.archived) return false;
    if (view === 'anki' && c.ankiStatus !== 'queued') return false;
    if (view === 'due' && !due(c)) return false;
    if ($('#tier-filter').value !== 'all' && c.tier !== $('#tier-filter').value) return false;
    const query = $('#search').value.trim().toLowerCase();
    // Search the full saved case, including explanations, notes and image keys.
    const haystack = [c.stem,c.sourceLabel,c.notes,...c.highlights,c.teachingPoint,...c.answers.map(a => a.text + ' ' + a.explanation),...c.groups.flatMap(g => g.images.map(i => i.caption))].join(' ').toLowerCase();
    return !query || haystack.includes(query);
  }
  function current() { return cases.find(c => c.id === active); }
  async function update(changes, render = false, id = active) {
    const c = await RadDB.patch(id, changes);
    if (!c) throw new Error('Case no longer exists. Reload your library.');
    cases = cases.map(item => item.id === id ? c : item);
    if (render) renderAll(); else renderList();
    return c;
  }
  function renderList() {
    const counts = { all: cases.filter(c => !c.archived).length, due: cases.filter(due).length,
      anki: cases.filter(c => !c.archived && c.ankiStatus === 'queued').length, archive: cases.filter(c => c.archived).length };
    $('#views').querySelectorAll('button').forEach(b => { b.classList.toggle('active', b.dataset.view === view); b.querySelector('span').textContent = counts[b.dataset.view]; });
    const list = $('#case-list'); list.replaceChildren();
    const filtered = cases.filter(matches).sort((a,b) => Date.parse(b.savedAt) - Date.parse(a.savedAt));
    for (const c of filtered) {
      const card = button('', () => { active = c.id; chosen = -1; revealed = false; renderAll(); }, 'case-card' + (active === c.id ? ' active' : ''));
      card.setAttribute('aria-pressed', active === c.id ? 'true' : 'false');
      const meta = el('div', undefined, 'card-meta'); meta.append(el('span', date(c.savedAt)), el('span', c.sourceLabel || 'RADPrimer'));
      card.append(meta, el('span', c.stem.length > 125 ? c.stem.slice(0,122) + '…' : c.stem, 'stem'));
      const badges = el('div', undefined, 'card-meta');
      if (c.ankiStatus === 'queued') badges.append(el('span', 'Anki queued', 'badge queued'));
      else if (c.ankiStatus === 'done') badges.append(el('span', 'Anki done', 'badge'));
      const count = RadCore.mediaCount(c);
      if (!c.answered || count.failed || count.saved < count.total) badges.append(el('span', !c.answered ? 'Question only' : 'Media incomplete', 'badge warning'));
      badges.append(el('span', count.total + ' images · ' + c.groups.length + ' groups'));
      card.append(badges); list.append(card);
    }
    if (!filtered.length) {
      const empty = el('div', undefined, 'empty'); empty.append(el('h3', cases.length ? 'No matching cases' : 'Your next good case starts here'), el('p', cases.length ? 'Try another filter or search.' : 'On RadPrimer, answer a question and choose Save case. It will appear here with its images and explanations.')); list.append(empty);
    }
    return filtered;
  }
  function renderAll() {
    const labels = { all: ['YOUR COLLECTION','Saved cases'], due: ['KEEP IT FAMILIAR','Ready to revisit'], anki: ['ONLY WHAT MATTERS','Your Anki queue'], archive: ['SET ASIDE, STILL HERE','Archived cases'] };
    $('#view-label').textContent = labels[view][0]; $('#collection-title').textContent = labels[view][1];
    const filtered = renderList();
    if (!filtered.some(c => c.id === active)) { active = filtered[0]?.id || ''; chosen = -1; revealed = false; renderList(); }
    renderDetail();
  }
  function renderDetail() {
    const container = $('#case-detail'); container.replaceChildren();
    const c = current();
    if (!c) {
      const empty = el('div', undefined, 'empty'); empty.append(el('div','▤','empty-mark'), el('h3','A place for useful cases'), el('p','Save freely. Review occasionally. Make Anki cards only for the facts you decide are essential.'));
      const link = el('a','Open RadPrimer ↗'); link.href = 'https://app.radprimer.com/'; link.target = '_blank'; link.rel = 'noreferrer'; empty.append(link);
      if (!isExtension) { const setup = el('a','Install the extension'); setup.href = '../index.html'; empty.append(setup); }
      container.append(empty); return;
    }
    const head = el('section', undefined, 'detail-head'), meta = el('div', undefined, 'meta');
    meta.append(el('span', c.questionLabel + ' · ' + (c.sourceLabel || 'RADPrimer'), 'eyebrow'));
    const source = RadCore.safeSource(c.sourceUrl);
    if (source) { const link = el('a','Source assessment ↗'); link.href = source; link.target = '_blank'; link.rel = 'noreferrer'; link.title = 'Opens the assessment; use the saved question number to return to this question.'; meta.append(link); }
    head.append(meta, el('p', c.stem, 'stem'));
    const choices = el('div', undefined, 'choice-list');
    c.answers.forEach((a,index) => {
      const b = button('', () => { chosen = index; renderDetail(); }, 'choice' + (chosen === index ? ' selected' : '') + (revealed && a.correctness === 'correct' ? ' correct' : revealed && chosen === index && a.correctness !== 'correct' ? ' wrong' : ''));
      b.append(el('span', String.fromCharCode(65 + index), 'letter'), document.createTextNode(a.text));
      if (revealed && a.correctness === 'correct') b.append(el('span','  ✓ Correct'));
      b.setAttribute('aria-pressed', chosen === index ? 'true' : 'false'); choices.append(b);
    }); head.append(choices);
    const reveal = el('div', undefined, 'reveal-row');
    if (c.answered) reveal.append(button(revealed ? 'Hide answer & keys' : 'Reveal answer & keys', () => { revealed = !revealed; renderDetail(); }, 'accent'), el('small','Your practice answer stays on this screen only.'));
    else reveal.append(el('p','Question-only save. Answer on RadPrimer, then save this case again to add explanations and image keys.', 'badge warning'));
    head.append(reveal);
    const mc = RadCore.mediaCount(c);
    head.append(el('p', mc.saved + '/' + mc.total + ' original images saved offline · ' + c.groups.length + ' image groups' + (mc.failed ? ' · ' + mc.failed + ' images have missing files; save again on RadPrimer to retry.' : ''), 'save-info'));
    container.append(head);
    c.groups.forEach(g => container.append(renderGroup(g)));
    if (revealed) {
      const section = el('section', undefined, 'detail-section'); section.append(el('h3','Why this answer'));
      if (c.teachingPoint) section.append(el('p', c.teachingPoint, 'teaching'));
      c.answers.forEach(a => {
        const d = el('details'), s = el('summary', (a.correctness === 'correct' ? '✓ Correct · ' : a.correctness ? a.correctness + ' · ' : '') + a.text);
        d.append(s, el('p', a.explanation || 'No explanation was available in the saved page.')); section.append(d);
      }); container.append(section);
    }
    const notes = el('section', undefined, 'detail-section'); notes.append(el('h3','What I want to remember'));
    const label = el('label','Your note','field-label'); label.htmlFor = 'case-notes';
    const textarea = el('textarea'); textarea.id = 'case-notes'; textarea.value = noteDrafts.get(c.id) ?? c.notes; textarea.placeholder = 'A specific fact, a pattern to notice, or why this case matters…';
    const noteStatus = el('span','', 'note-status'), noteId = c.id;
    let revision = 0;
    async function saveNote() {
      const value = textarea.value, requestRevision = ++revision;
      await update({ notes: value }, false, noteId);
      if (noteDrafts.get(noteId) === value) noteDrafts.delete(noteId);
      if (requestRevision === revision) noteStatus.textContent = 'Saved on this device';
    }
    textarea.oninput = () => { noteDrafts.set(noteId, textarea.value); noteStatus.textContent = 'Unsaved note'; };
    textarea.onblur = () => saveNote().catch(showError);
    const noteActions = el('div', undefined, 'note-actions'); noteActions.append(button('Save note', saveNote), noteStatus);
    notes.append(label, textarea, noteActions);
    const facts = el('ul', undefined, 'facts');
    c.highlights.forEach((fact,index) => {
      const li = el('li',fact); li.append(button('Remove', async () => { const h = [...current().highlights]; h.splice(index,1); await update({highlights:h},true); })); facts.append(li);
    }); notes.append(facts);
    let selectedText = '';
    const add = button('Add selected fact', async () => {
      const text = selectedText.trim();
      if (!text) { showStatus('Select a fact in this case, then choose Add selected fact.'); return; }
      await update({ highlights: [...new Set([...current().highlights, text])] }, true); showStatus('Selected fact saved.');
    });
    add.onpointerdown = e => { selectedText = window.getSelection()?.toString() || ''; e.preventDefault(); };
    // Keyboard activation retains the current document selection.
    add.onkeydown = () => { selectedText = window.getSelection()?.toString() || ''; };
    notes.append(add, el('p','Select a sentence in an explanation or key, then add it as a fact for your agent.', 'legend'));
    const settings = el('div', undefined, 'settings');
    settings.append(selectField('Knowledge tier', 'case-tier', [['review','Occasional review'],['essential','Must remember'],['reference','Reference only']], c.tier, value => update({tier:value},true)),
      selectField('Anki', 'anki-status', [['none','Not queued'],['queued','Queued for creation'],['done','Cards created']], c.ankiStatus, value => update({ankiStatus:value},true)));
    notes.append(settings);
    if (c.ankiStatus === 'queued' && !c.highlights.length && !c.notes.trim()) notes.append(el('p','Queued without selected facts. Add a note or highlight to tell your agent exactly what deserves a card.', 'badge warning'));
    notes.append(el('p', 'Last reviewed: ' + (c.reviewedAt ? date(c.reviewedAt) : 'Not yet') + ' · Next visit: ' + (c.tier === 'reference' ? 'On demand' : c.dueAt ? date(c.dueAt) : 'Ready now'), 'small muted'));
    const review = el('div', undefined, 'review-actions');
    if (c.tier !== 'reference') for (const [days,label] of [[1,'Again tomorrow'],[7,'Revisit in 1 week'],[30,'Revisit in 1 month']]) review.append(button(label, async () => {
      const dueAt = new Date(); dueAt.setDate(dueAt.getDate() + days);
      await update({ reviewedAt: RadCore.now(), dueAt: dueAt.toISOString() }, true); showStatus('Review recorded. Next visit: ' + date(dueAt) + '.');
    }));
    notes.append(review, button(c.archived ? 'Restore case' : 'Archive case', async () => { await update({archived:!c.archived},true); showStatus(c.archived ? 'Case restored.' : 'Case archived. You can restore it from Archive.'); }, 'archive-action'));
    notes.append(el('p', 'Saved ' + date(c.savedAt) + (c.author ? ' · ' + c.author : '') + ' · ' + c.id.slice(0,15), 'save-info')); container.append(notes);
  }
  function selectField(title,id,options,value,change) {
    const label = el('label',title), select = el('select'); select.id = id; select.setAttribute('aria-label',title);
    for (const [v,t] of options) { const o = el('option',t); o.value=v; select.append(o); } select.value=value;
    select.onchange = () => Promise.resolve(change(select.value)).catch(showError); label.append(select); return label;
  }
  function renderGroup(g) {
    const section = el('section',undefined,'group');
    const stateKey = active + '/' + g.id, state = groupState.get(stateKey) || {index:0,annotated:false};
    let index=Math.min(state.index, Math.max(0,g.images.length-1)), annotated=state.annotated;
    const groupHead = el('div',undefined,'group-head'); groupHead.append(el('h3',g.title),el('span',g.images.length+' images','badge')); section.append(groupHead);
    const stage = el('div',undefined,'image-stage'), controls=el('div',undefined,'image-controls'), thumbs=el('div',undefined,'thumbs'), caption=el('p','', 'caption');
    const previous = button('← Previous', () => { index=Math.max(0,index-1); draw(); }), next=button('Next →',()=>{index=Math.min(g.images.length-1,index+1);draw();}), counter=el('span');
    const toggle=button('Show annotations',()=>{annotated=!annotated;draw();},'annotation');
    controls.append(previous,counter,next,toggle);
    g.images.forEach((i,n)=>{
      const b=button('',()=>{index=n;draw();}); b.setAttribute('aria-label', g.title + ', image '+(n+1));
      if(RadCore.imageData(i.original)){const img=el('img');img.src=i.original;img.alt=i.alt; b.append(img);} else b.textContent=String(n+1);
      thumbs.append(b);
    });
    function draw(){
      groupState.set(stateKey,{index,annotated});
      stage.replaceChildren(); const i=g.images[index]; if(!i){stage.append(el('p','No images saved.','missing'));return;}
      const data=annotated&&revealed?i.annotated:i.original;
      if(RadCore.imageData(data)){
        const img=el('img');img.src=data;img.alt=i.alt;
        const zoom=button('',()=>{const dialog=$('#image-dialog');$('#enlarged').src=data;$('#enlarged').alt=i.alt;$('#enlarged-caption').textContent=revealed?i.caption:'';dialog.showModal();});zoom.setAttribute('aria-label','Enlarge '+g.title+' image '+(index+1));zoom.append(img);stage.append(zoom);
      } else stage.append(el('p',annotated?'Annotated image unavailable. Save this case again on RadPrimer to retry.':'Image unavailable offline. Save this case again on RadPrimer to retry.','missing'));
      counter.textContent=(index+1)+' / '+g.images.length;previous.disabled=index===0;next.disabled=index===g.images.length-1;
      toggle.hidden=!revealed||!i.annotationExpected;toggle.textContent=annotated?'Hide annotations':'Show annotations';
      Array.from(thumbs.children).forEach((b,n)=>{b.classList.toggle('active',n===index);b.setAttribute('aria-pressed',n===index?'true':'false');});
      caption.textContent=revealed?(i.caption||'No image key was available for this image.'):'Reveal the answer to see the image key.';
    }
    section.append(stage,controls,thumbs,caption);draw();return section;
  }
  function download(data,name){const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),url=URL.createObjectURL(blob),a=el('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);}
  $('#backup').onclick=async()=>{
    try{const data=await RadDB.all();if(!data.length){showStatus('No cases to back up yet. Save a case on RadPrimer first.');return;}
      download({format:'radprimer-library',schema:1,exportedAt:RadCore.now(),cases:data},'radprimer-library-'+new Date().toISOString().slice(0,10)+'.json');showStatus('Backup downloaded with saved images and notes. Keep it outside this repository.');}catch(e){showError(e);}
  };
  $('#export-anki').onclick=async()=>{
    try{const packet=RadCore.packet(await RadDB.all());if(!packet.cases.length){showStatus('Your Anki queue is empty. Queue a case and add the facts you want to remember.');return;}
      download(packet,'radprimer-anki-packet-'+new Date().toISOString().slice(0,10)+'.json');showStatus('Exported '+packet.cases.length+' queued cases. Give this file to your agent. Mark Cards created after the cards are made.');}catch(e){showError(e);}
  };
  $('#import-open').onclick=()=>$('#import').click();
  $('#import').onchange=async e=>{
    const file=e.target.files[0];if(!file)return;
    try{if(file.size>250*1024*1024)throw new Error('This backup exceeds the 250 MB import limit. Split it into smaller packets.');
      const count=await RadDB.importBackup(JSON.parse(await file.text()));cases=await RadDB.all();renderAll();showStatus('Imported '+count+' cases. Existing notes, review dates and queue status were preserved.');}catch(error){showError(error);}finally{e.target.value='';}
  };
  $('#search').oninput=renderAll;$('#tier-filter').onchange=renderAll;
  $('#views').querySelectorAll('button').forEach(b=>{b.onclick=()=>{view=b.dataset.view;revealed=false;chosen=-1;renderAll();};});
  $('#close-image').onclick=()=>$('#image-dialog').close();
  // Refresh after another tab saves a case, without discarding an unsaved note.
  window.addEventListener('focus',async()=>{if(noteDrafts.size)return;try{cases=await RadDB.all();renderAll();}catch(e){showError(e);}});
  try{cases=await RadDB.all();renderAll();}catch(e){showError(e);}
})();
