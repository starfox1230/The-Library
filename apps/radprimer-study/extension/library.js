(async function () {
  'use strict';
  const $ = selector => document.querySelector(selector);
  let cases = [], view = 'all', active = '', revealed = false, chosen = -1, pane = 'question', casesCollapsed = false, fitFrame;
  const noteDrafts = new Map(), groupState = new Map(), imageViews = new Map();
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
      const card = button('', () => { active = c.id; chosen = -1; revealed = false; pane = 'question'; renderAll(); }, 'case-card' + (active === c.id ? ' active' : ''));
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
    $('.work').classList.toggle('single-case', filtered.length <= 1);
    $('.work').classList.toggle('cases-collapsed', casesCollapsed);
    $('#toggle-cases').textContent = 'Cases (' + filtered.length + ')';
    $('#toggle-cases').disabled = filtered.length <= 1;
    $('#toggle-cases').setAttribute('aria-expanded', String(filtered.length > 1 && !casesCollapsed));
    return filtered;
  }
  function renderAll() {
    const labels = { all: ['YOUR COLLECTION','Saved cases'], due: ['KEEP IT FAMILIAR','Ready to revisit'], anki: ['ONLY WHAT MATTERS','Your Anki queue'], archive: ['SET ASIDE, STILL HERE','Archived cases'] };
    $('#view-label').textContent = labels[view][0]; $('#collection-title').textContent = labels[view][1];
    const filtered = renderList();
    if (!filtered.some(c => c.id === active)) { active = filtered[0]?.id || ''; chosen = -1; revealed = false; pane = 'question'; renderList(); }
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
    const topbar = el('div', undefined, 'review-topbar'), meta = el('div', undefined, 'meta');
    meta.append(el('span', c.questionLabel + ' · ' + (c.sourceLabel || 'RADPrimer'), 'eyebrow'));
    const source = RadCore.safeSource(c.sourceUrl);
    if (source) { const link = el('a','Source assessment ↗'); link.href = source; link.target = '_blank'; link.rel = 'noreferrer'; link.title = 'Opens the assessment; use the saved question number to return to this question.'; meta.append(link); }
    const mc = RadCore.mediaCount(c);
    meta.append(el('span', mc.saved + '/' + mc.total + ' images offline' + (mc.failed ? ' · Media incomplete: save again on RadPrimer to retry.' : ''), 'save-info'));
    const focus = button(document.body.classList.contains('images-focus') ? 'Exit image focus' : 'Focus images', () => setImageFocus(!document.body.classList.contains('images-focus')), 'focus-images');
    focus.id = 'focus-images'; focus.setAttribute('aria-pressed', String(document.body.classList.contains('images-focus')));
    topbar.append(meta, focus); container.append(topbar);
    const layout = el('div', undefined, 'review-layout'), inspector = el('section', undefined, 'case-inspector');
    inspector.setAttribute('aria-label', 'Question, explanations and notes');
    const tabs = el('div', undefined, 'inspector-tabs'); tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', 'Case information');
    for (const [key, title] of [['question','Question'],['explanation','Explanation'],['notes','Notes']]) {
      const tab = button(title, () => { pane = key; renderDetail(); $('#inspector-tab-' + key)?.focus(); });
      tab.id = 'inspector-tab-' + key; tab.setAttribute('role', 'tab'); tab.setAttribute('aria-selected', String(pane === key));
      tab.setAttribute('aria-controls', 'inspector-panel-' + key); tab.tabIndex = pane === key ? 0 : -1; tabs.append(tab);
    }
    tabKeys(tabs);
    const scroll = el('div', undefined, 'inspector-scroll'); inspector.append(tabs, scroll);
    function addPane(section, key) {
      section.id = 'inspector-panel-' + key; section.setAttribute('role', 'tabpanel'); section.setAttribute('aria-labelledby', 'inspector-tab-' + key);
      section.hidden = pane !== key; scroll.append(section);
    }
    layout.append(renderImages(c), inspector); container.append(layout);
    const head = el('section', undefined, 'detail-head');
    head.append(el('p', c.stem, 'stem'));
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
    if (revealed) head.append(button('Read explanations →', () => { pane = 'explanation'; renderDetail(); }));
    addPane(head, 'question');
    const explanation = el('section', undefined, 'detail-section explanation-pane');
    if (revealed) {
      explanation.append(el('h3','Why this answer'));
      if (c.teachingPoint) explanation.append(el('p', c.teachingPoint, 'teaching'));
      c.answers.forEach(a => {
        const d = el('details'), s = el('summary', (a.correctness === 'correct' ? '✓ Correct · ' : a.correctness ? a.correctness + ' · ' : '') + a.text);
        d.open = a.correctness === 'correct';
        d.append(s, el('p', a.explanation || 'No explanation was available in the saved page.')); explanation.append(d);
      });
    } else if (c.answered) explanation.append(el('h3','Try the case first'), el('p','Reveal the answer when you are ready to read the explanations and image keys.'), button('Reveal answer & keys', () => { revealed = true; renderDetail(); }, 'accent'));
    else explanation.append(el('p','No answer explanation was saved yet. Answer on RadPrimer, then save this case again.'));
    addPane(explanation, 'explanation');
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
    notes.append(el('p', 'Saved ' + date(c.savedAt) + (c.author ? ' · ' + c.author : '') + ' · ' + c.id.slice(0,15), 'save-info')); addPane(notes, 'notes');
    queueImageFit();
  }
  function queueImageFit() {
    cancelAnimationFrame(fitFrame);
    fitFrame = requestAnimationFrame(() => {
      const panels = Array.from(document.querySelectorAll('.image-grid > .group')).filter(g => !g.hidden);
      // Measure actual chrome and controls, including a wrapped web-viewer notice.
      // Reserve the controls below the image so group/image navigation stays visible.
      const heights = panels.map(panel => {
        const stage = panel.querySelector('.image-stage').getBoundingClientRect();
        const footer = panel.getBoundingClientRect().bottom - stage.bottom;
        return innerHeight - (stage.top + scrollY) - footer - 32;
      });
      const height = Math.max(220, Math.floor(Math.min(...heights, 1200)));
      panels.forEach(panel => { panel.querySelector('.image-stage').style.height = height + 'px'; });
      const inspector = $('.inspector-scroll');
      if (inspector) inspector.style.maxHeight = innerWidth > 640 ? Math.max(220, innerHeight - (inspector.getBoundingClientRect().top + scrollY) - 32) + 'px' : 'none';
    });
  }
  function setImageFocus(value) {
    document.body.classList.toggle('images-focus', value);
    const b = $('#focus-images');
    if (b) { b.textContent = value ? 'Exit image focus' : 'Focus images'; b.setAttribute('aria-pressed', String(value)); }
    queueImageFit();
  }
  function tabKeys(tabs) {
    tabs.onkeydown = e => {
      if (!['ArrowLeft','ArrowRight','Home','End'].includes(e.key) || e.target.getAttribute('role') !== 'tab') return;
      const buttons = Array.from(tabs.querySelectorAll('[role=tab]')), index = buttons.indexOf(e.target);
      const next = e.key === 'Home' ? 0 : e.key === 'End' ? buttons.length - 1 : (index + (e.key === 'ArrowRight' ? 1 : -1) + buttons.length) % buttons.length;
      e.preventDefault(); buttons[next].click();
    };
  }
  function renderImages(c) {
    const workspace = el('section', undefined, 'image-workspace'); workspace.setAttribute('aria-label', 'Case images');
    if (!c.groups.length) { workspace.append(el('div','This case has no saved image groups.','empty')); return workspace; }
    const state = imageViews.get(c.id) || { group: 0, compare: innerWidth > 900 && c.groups.length === 2 && c.groups.every(g => g.images.length === 1) };
    state.group = Math.min(state.group, c.groups.length - 1); imageViews.set(c.id, state);
    const toolbar = el('div', undefined, 'image-toolbar'), tabs = el('div', undefined, 'group-tabs');
    tabs.setAttribute('role', 'tablist'); tabs.setAttribute('aria-label', 'Image groups');
    const grid = el('div', undefined, 'image-grid' + (state.compare && c.groups.length > 1 ? ' comparing' : ''));
    c.groups.forEach((g, index) => {
      const tab = button(g.title + ' · ' + g.images.length, () => { state.group = index; renderDetail(); $('#image-group-tab-' + index)?.focus(); });
      tab.id = 'image-group-tab-' + index; tab.setAttribute('role', 'tab'); tab.setAttribute('aria-selected', String(state.group === index));
      tab.setAttribute('aria-controls', 'image-group-panel-' + index); tab.tabIndex = state.group === index ? 0 : -1; tabs.append(tab);
      const panel = renderGroup(g); panel.id = 'image-group-panel-' + index; panel.classList.toggle('primary-group', index === state.group);
      // In comparison mode show only the selected group and its next neighbor.
      panel.hidden = index !== state.group && !(state.compare && index === (state.group + 1) % c.groups.length);
      panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', tab.id); grid.append(panel);
    });
    tabKeys(tabs); toolbar.append(tabs);
    if (c.groups.length > 1) {
      const compare = button(state.compare ? 'Single group' : 'Compare groups', () => { state.compare = !state.compare; renderDetail(); $('.compare-groups')?.focus(); }, 'compare-groups');
      compare.setAttribute('aria-pressed', String(state.compare)); toolbar.append(compare);
    }
    workspace.onkeydown = e => {
      if (!['ArrowLeft','ArrowRight'].includes(e.key) || e.target.getAttribute('role') === 'tab' || e.target.matches('input,textarea,select')) return;
      const panel = grid.querySelector('#image-group-panel-' + state.group);
      const b = panel?.querySelector(e.key === 'ArrowRight' ? '[data-image-next]' : '[data-image-previous]');
      if (b && !b.disabled) { e.preventDefault(); b.click(); }
    };
    workspace.append(toolbar, grid); return workspace;
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
    previous.dataset.imagePrevious = ''; next.dataset.imageNext = ''; counter.setAttribute('aria-live','polite');
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
    const key = el('details', undefined, 'image-key'); key.append(el('summary','Image key'), caption);
    section.append(stage,controls,thumbs,key);draw();return section;
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
  $('#toggle-cases').onclick=()=>{casesCollapsed=!casesCollapsed;renderList();queueImageFit();};
  $('#views').querySelectorAll('button').forEach(b=>{b.onclick=()=>{view=b.dataset.view;revealed=false;chosen=-1;pane='question';renderAll();};});
  $('#close-image').onclick=()=>$('#image-dialog').close();
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('#image-dialog').open)setImageFocus(false);});
  window.addEventListener('resize',queueImageFit);
  // Refresh after another tab saves a case, without discarding an unsaved note.
  window.addEventListener('focus',async()=>{if(noteDrafts.size)return;try{cases=await RadDB.all();renderAll();}catch(e){showError(e);}});
  try{cases=await RadDB.all();renderAll();}catch(e){showError(e);}
})();
