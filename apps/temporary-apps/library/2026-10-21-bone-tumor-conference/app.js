/* All study annotations remain in this browser. No tracking or remote writes. */
(() => {
  'use strict';
  const STORAGE_KEY = 'library-bone-tumor-conference-2026-v1';
  const PRIVATE_URL = 'https://bone-tumor-conference-oct22.glut4.chatgpt.site';
  const $ = (selector, root = document) => root.querySelector(selector);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const plain = value => Array.isArray(value) ? value.map(plain).join('\n\n') : (value && typeof value === 'object' ? Object.values(value).map(plain).join('\n') : String(value ?? ''));
  const safeURL = value => { try { const u = new URL(value, location.href); return ['http:', 'https:'].includes(u.protocol) ? u.href : ''; } catch { return ''; } };
  const link = (url, label, cls = '') => safeURL(url) ? `<a class="${cls}" href="${esc(safeURL(url))}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>` : '';
  const state = {view:'guide', query:'', topic:'all', source:'all', scope:'pending', flag:'all', caption:true, imageLimit:24, readerSource:null, readerIndex:0, readerHideRead:true, notes:new Set(), annotations:{}, guide:[], corpus:null};
  let toastTimer, searchTimer, lastFocus;
  function toast(message) { const el = $('#toast'); el.textContent = message; el.hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => el.hidden = true, 4200); }
  function storageStatus(ok) { $('#save-status').textContent = ok ? 'Saved on this device' : 'Saving unavailable · export your progress'; $('#save-status').classList.toggle('error', !ok); }
  function save() { try { localStorage.setItem(STORAGE_KEY, JSON.stringify({version:1, annotations:state.annotations})); storageStatus(true); } catch { storageStatus(false); } updateNav(); }
  function readStored() { try { const raw = localStorage.getItem(STORAGE_KEY); if (raw) state.annotations = cleanAnnotations(JSON.parse(raw).annotations); } catch { storageStatus(false); } }
  function cleanAnnotations(raw) {
    const clean = Object.create(null);
    if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return clean;
    for (const [id, item] of Object.entries(raw).slice(0, 50000)) {
      if (!/^(g|f|b|p):/.test(id) || id.length > 300 || !item || typeof item !== 'object') continue;
      const out = {updated:Number.isFinite(item.updated) ? item.updated : 0};
      for (const prop of ['done','key','review']) if (typeof item[prop] === 'boolean') out[prop] = item[prop];
      if (typeof item.note === 'string') out.note = item.note.slice(0, 100000);
      clean[id] = out;
    }
    return clean;
  }
  const ann = id => state.annotations[id] || {};
  function setAnnotation(id, prop, value) { state.annotations[id] = {...ann(id), [prop]:value, updated:Date.now()}; save(); }
  const countDone = items => items.filter(item => ann(item).done).length;
  const sources = () => state.corpus?.sources || [];
  const figures = () => state.corpus?.figures || [];
  const sourceById = id => sources().find(source => String(source.id) === String(id));
  const sourceTitle = id => sourceById(id)?.title || state.guide.flatMap(x => x.refs || []).find(r => r.source === id)?.title || ({helms2:'Helms · imaging features',helms3:'Helms · tumors',helms4:'Helms · mimics',acr:'ACR Bone-RADS',rsna:'RSNA exhibit'})[id] || id || 'Source';
  const pageKey = (source, page) => `p:${source.id}:${page.id ?? page.page}`;
  const blockKey = (source, page, block, index) => `b:${block.id || `${source.id}:${page.id ?? page.page}:${index}`}`;
  const allPages = () => sources().flatMap(source => (source.pages || []).map(page => ({source, page})));
  const bodyText = item => plain(item.body || item.text || '');
  const match = text => !state.query || plain(text).toLowerCase().includes(state.query.toLowerCase());
  const pageLabel = page => `Page ${page.page ?? page.printed ?? ''}${page.printed && String(page.printed) !== String(page.page) ? ` · printed ${page.printed}` : ''}`;
  function updateNav() {
    $('#guide-count').textContent = `${countDone(state.guide.map(g => `g:${g.id}`))}/${state.guide.length}`;
    $('#image-count').textContent = figures().length || '';
    $('#flag-count').textContent = Object.values(state.annotations).filter(a => a.key || a.review || a.note).length || '';
    document.querySelectorAll('.nav-item').forEach(el => { const active = el.dataset.view === state.view; el.classList.toggle('active', active); if (active) el.setAttribute('aria-current','page'); else el.removeAttribute('aria-current'); });
    $('#section-label').textContent = ({guide:'YOUR STUDY ROUTE',reader:'THE COMPLETE SOURCE MATERIAL',images:'VISUAL PATTERN RECOGNITION',flags:'YOUR PERSONAL REVIEW LIST'})[state.view];
  }
  const btn = (action, text, attrs = '', cls = 'secondary') => `<button type="button" class="${cls}" data-action="${action}" ${attrs}>${text}</button>`;
  const check = (id, doneLabel = 'Mark complete', undoLabel = 'Mark incomplete') => `<button type="button" class="done-control" data-action="toggle" data-id="${esc(id)}" data-prop="done" aria-pressed="${!!ann(id).done}" aria-label="${ann(id).done ? undoLabel : doneLabel}"><span class="done-ring" aria-hidden="true">${ann(id).done ? '✓' : ''}</span></button>`;
  function actions(id, kind = 'guide', extra = '') {
    const a = ann(id), image = kind === 'image';
    return `<div class="card-footer">${btn('toggle',image ? '☆ Favorite' : '☆ Key point',`data-id="${esc(id)}" data-prop="key" aria-pressed="${!!a.key}"`,'action')}${btn('toggle','↺ Review',`data-id="${esc(id)}" data-prop="review" aria-pressed="${!!a.review}"`,'action review')}${image ? btn('toggle','✓ Reviewed',`data-id="${esc(id)}" data-prop="done" aria-pressed="${!!a.done}"`,'action reviewed') : ''}${btn('note',a.note ? '✎ Note saved' : '✎ Add note',`data-id="${esc(id)}" aria-expanded="${state.notes.has(id)}"`,'action note-action')}${extra}</div>${note(id)}`;
  }
  function note(id) { return state.notes.has(id) ? `<div class="notes-wrap"><label for="note-${esc(id)}">Your note · saved as you type</label><textarea id="note-${esc(id)}" data-note="${esc(id)}" placeholder="The clue I want to remember…">${esc(ann(id).note || '')}</textarea></div>` : ''; }
  function refs(item) { return (item.refs || []).map(ref => btn('reference',`${esc(ref.title || sourceTitle(ref.source))}${ref.page != null ? ` · p. ${esc(ref.page)}` : ''}`,`data-source="${esc(ref.source)}" data-page="${esc(ref.page ?? '')}"`,'ref-link')).join(''); }
  function guideCard(item, inFlags = false) {
    const id = `g:${item.id}`, a = ann(id);
    return `<article id="item-${esc(id)}" class="study-card ${a.done ? 'is-done' : ''}"><div class="card-inner">${check(id)}<div><div class="topic-label">${esc(item.topic || 'Case approach')}</div><h3>${esc(item.title)}</h3><div class="card-body">${esc(bodyText(item))}</div>${item.overlap ? `<p class="overlap-note">↔ ${esc(item.overlap)}</p>` : ''}${(item.related || []).map(related => {const match=state.guide.find(g=>g.id===related);return match?btn('jump-guide','Related principle: '+esc(match.title),`data-item="${esc(related)}"`,'ref-link'):'';}).join('')}${item.prompt ? `<div class="case-prompt"><span>AT THE VIEWBOX</span>${esc(plain(item.prompt))}${item.answer ? `<details><summary>Reveal the follow-up</summary><p>${esc(plain(item.answer))}</p></details>` : ''}</div>` : ''}<div class="ref-row">${refs(item)}</div></div></div>${actions(id,'guide',inFlags ? btn('jump-guide','In study route ↗',`data-item="${esc(item.id)}"`,'action flag-jump') : '')}</article>`;
  }
  function hero(eyebrow, title, description, stamp = '') { return `<section class="hero"><div><span class="eyebrow">${eyebrow}</span><h2>${title}</h2><p>${description}</p></div>${stamp ? `<div class="hero-stamp">${stamp}</div>` : ''}</section>`; }
  function progress() {
    const gDone = countDone(state.guide.map(g => `g:${g.id}`)), pages = allPages(), pDone = pages.filter(({source,page}) => ann(pageKey(source,page)).done).length, fDone = countDone(figures().map(f => `f:${f.id}`));
    return `<div class="stats-grid"><div class="stat"><div class="stat-label">Study route <span>SYNTHESIS</span></div><strong>${gDone} <small>of ${state.guide.length} points checked</small></strong><div class="progress-track"><i style="width:${state.guide.length ? gDone/state.guide.length*100 : 0}%"></i></div></div><div class="stat"><div class="stat-label">Source reading <span>FULL DOCUMENTS</span></div><strong>${pDone} <small>${pages.length ? `of ${pages.length} pages complete` : 'open the private reader'}</small></strong><div class="progress-track"><i style="width:${pages.length ? pDone/pages.length*100 : 0}%"></i></div></div><div class="stat"><div class="stat-label">Image practice <span>VISUAL REVIEW</span></div><strong>${fDone} <small>${figures().length ? `of ${figures().length} images reviewed` : 'open the private atlas'}</small></strong><div class="progress-track"><i style="width:${figures().length ? fDone/figures().length*100 : 0}%"></i></div></div></div>`;
  }
  function missingCorpus() { return `<div class="banner"><p><strong>Your complete reading room is private.</strong><br>The source pages and image atlas are available in your private study site. This public Library page contains the study route. Progress is saved separately in each browser and site; use Export / Import to transfer it.</p>${link(PRIVATE_URL,'Open private reading room ↗','primary')}</div>`; }
  function filters(view) {
    let html = `<div class="toolbar"><label class="search"><span class="sr-only" hidden>Search ${view === 'images' ? 'images and captions' : 'study material'}</span><input id="search-input" type="search" aria-label="Search ${view === 'images' ? 'images and captions' : 'study material'}" placeholder="${view === 'images' ? 'Search captions, diagnoses, patterns…' : 'Search a diagnosis, clue, or question…'}" value="${esc(state.query)}"></label>`;
    if (view === 'guide') html += `<select id="topic-filter" aria-label="Filter by study topic"><option value="all">All topics</option>${[...new Set(state.guide.map(g => g.topic).filter(Boolean))].map(t => `<option value="${esc(t)}" ${state.topic === t ? 'selected' : ''}>${esc(t)}</option>`).join('')}</select>`;
    if (view === 'images') html += `<select id="source-filter" aria-label="Filter by source"><option value="all">All sources</option>${sources().map(s => `<option value="${esc(s.id)}" ${state.source === String(s.id) ? 'selected' : ''}>${esc(s.title)}</option>`).join('')}</select>`;
    if (view === 'guide' || view === 'images') {
      const options = view === 'guide' ? [['pending','To study'],['all','Show all'],['done','Completed']] : [['pending','To review'],['all','All images'],['done','Reviewed'],['favorites','Favorites']];
      html += `<div class="segmented" role="group" aria-label="Completion filter">${options.map(([value,title]) => btn('scope',title,`data-value="${value}" aria-pressed="${state.scope === value}"`,state.scope === value ? 'active' : '')).join('')}</div>`;
    }
    if (view === 'flags') html += `<select id="flag-filter" aria-label="Filter flags"><option value="all">All saved items</option><option value="key" ${state.flag==='key'?'selected':''}>Key points & favorite images</option><option value="review" ${state.flag==='review'?'selected':''}>Needs review</option><option value="note" ${state.flag==='note'?'selected':''}>With notes</option></select>`;
    return html + '</div>';
  }
  function renderGuide() {
    const visible = state.guide.filter(g => (state.topic === 'all' || g.topic === state.topic) && match([g.title, g.topic, bodyText(g), g.prompt, g.answer]) && (state.scope === 'all' || (state.scope === 'done' ? ann(`g:${g.id}`).done : !ann(`g:${g.id}`).done)));
    return hero('OCTOBER 22 · CONFERENCE PREPARATION','A clear route through bone tumors.','Work through the case approach, then use the source reader for every page and the atlas for visual recall. Check off what you know; flag what deserves another look.','OCT<strong>22</strong>2026') + progress() + (!state.corpus ? missingCorpus() : '') + filters('guide') + `<div class="list-meta"><strong>${visible.length} ${visible.length === 1 ? 'point' : 'points'} in this view</strong><span>Check it off → it leaves your to-study list.</span></div><div class="study-list">${visible.map(g => guideCard(g)).join('') || `<div class="empty"><h3>${state.scope === 'pending' && !state.query && state.topic === 'all' ? 'A clean slate. Well studied.' : 'No points in this view.'}</h3><p>${state.scope === 'pending' ? 'Switch to Show all to revisit completed points, or open Your flags for the details you saved.' : 'Try another topic or search term.'}</p>${btn('scope','Show all points','data-value="all"')}</div>`}</div>`;
  }
  function renderReader() {
    const heading = hero('READ IT IN FULL','Every page. Nothing skipped.','The original page sits above its extracted text. Mark individual passages as you go, or complete a whole page. Source reading is tracked separately from the study route.');
    if (!state.corpus) return heading + missingCorpus();
    if (!sources().length) return heading + '<div class="empty"><h3>No source documents are available yet.</h3></div>';
    let source = sourceById(state.readerSource) || sources()[0]; state.readerSource = String(source.id);
    const pages = source.pages || []; state.readerIndex = Math.max(0,Math.min(state.readerIndex,pages.length-1)); const page = pages[state.readerIndex];
    const sidebar = `<div class="source-list" aria-label="Source documents">${sources().map(s => {const done = (s.pages || []).filter(p => ann(pageKey(s,p)).done).length;return btn('source',`${esc(s.title)}<small>${done} / ${(s.pages || []).length} pages complete</small>`,`data-source="${esc(s.id)}" ${s.id === source.id ? 'aria-current="true"' : ''}`,'source-button'+(s.id === source.id ? ' active' : ''));}).join('')}</div>`;
    const intro = `<div class="source-intro"><h3>${esc(source.title)}</h3>${source.description ? `<p>${esc(source.description)}</p>` : ''}${link(source.url,'Open original source ↗')}</div>`;
    if (!page) return heading+`<div class="reader-layout">${sidebar}<div>${intro}<div class="empty"><h3>Source still pending</h3><p>The document has not been added to the reader yet.</p></div></div></div>`;
    const key = pageKey(source,page), blocks = page.blocks?.length ? page.blocks : (page.text ? [{id:`${source.id}:${page.id ?? page.page}:text`,text:page.text}] : []), doneBlocks = blocks.filter((b,i) => ann(blockKey(source,page,b,i)).done).length;
    const controls = `<div class="page-controls"><div class="page-nav">${btn('page-prev','← Previous',state.readerIndex === 0 ? 'disabled' : '')}${btn('page-next','Next →',state.readerIndex === pages.length-1 ? 'disabled' : '')}</div><select id="page-select" aria-label="Select source page">${pages.map((p,i) => `<option value="${i}" ${i===state.readerIndex?'selected':''}>${esc(pageLabel(p))}</option>`).join('')}</select>${btn('page-done',ann(key).done ? '✓ Page complete' : 'Mark page complete',`data-id="${esc(key)}" aria-pressed="${!!ann(key).done}"`,ann(key).done ? 'primary' : 'secondary')}</div>`;
    return heading + `<div class="reader-layout">${sidebar}<div>${intro}${page.warning ? `<div class="banner"><p><strong>Source correction</strong><br>${esc(page.warning)}</p></div>` : ''}${controls}<label class="toggle-label reader-toggle"><input type="checkbox" id="hide-read" ${state.readerHideRead?'checked':''}> Hide checked passages (${doneBlocks} checked)</label><article class="reader-page" id="reader-page">${page.image ? `<div class="page-image-wrap"><img class="page-image" data-action="page-image" src="${esc(safeURL(page.image))}" alt="Original ${esc(pageLabel(page))} from ${esc(source.title)}" loading="eager">${btn('page-image','Expand original page ↗','','image-expand')}</div>` : ''}<div class="text-heading"><span>${esc(pageLabel(page))} · SOURCE TEXT</span><span>${doneBlocks}/${blocks.length} passages checked</span></div>${blocks.map((block,i) => {const id=blockKey(source,page,block,i);if(state.readerHideRead&&ann(id).done)return '';return `<section id="item-${esc(id)}" class="source-block ${ann(id).done?'is-done':''}">${check(id,'Mark passage read','Mark passage unread')}<div><div class="block-copy">${esc(block.text)}</div><div class="block-tools">${btn('toggle','☆ Key point',`data-id="${esc(id)}" data-prop="key" aria-pressed="${!!ann(id).key}"`,'action')}${btn('toggle','↺ Review',`data-id="${esc(id)}" data-prop="review" aria-pressed="${!!ann(id).review}"`,'action review')}${btn('note',ann(id).note?'✎ Note saved':'✎ Add note',`data-id="${esc(id)}" aria-expanded="${state.notes.has(id)}"`,'action')}</div>${note(id)}</div></section>`;}).join('') || '<div class="page-figures"><p class="block-copy">This page has no extracted text. Review the original page image above.</p></div>'}${page.figures?.length ? `<div class="page-figures"><h4>Figures on this page</h4><div class="ref-row">${page.figures.map(id => {const f=figures().find(f => String(f.id)===String(id));return f?btn('figure',esc(f.label || f.title || 'Open figure'),`data-figure="${esc(f.id)}"`,'ref-link'):'';}).join('')}</div></div>` : ''}</article>${controls.replace('id="page-select"','id="page-select-bottom"')}</div></div>`;
  }
  function figureCard(f, inFlags = false) {
    const id = `f:${f.id}`;
    return `<article class="image-card" id="item-${esc(id)}"><button type="button" class="figure-open" data-action="figure" data-figure="${esc(f.id)}" aria-label="Open ${esc(state.caption ? f.title || f.label || 'figure' : `figure from ${sourceTitle(f.source)}, page ${f.page}`)}"><img src="${esc(safeURL(f.image || f.contextImage))}" alt="${esc(state.caption ? f.title || f.label || 'Source figure' : 'Source image · separate caption hidden')}" loading="lazy" decoding="async"></button><div class="image-copy"><div class="image-source">${esc(sourceTitle(f.source))} · p. ${esc(f.page)}</div>${state.caption ? `<h3>${esc([f.label,f.title].filter(Boolean).join(' · '))}</h3><p>${esc(f.caption || 'Open the figure to see its full source context.')}</p>` : '<p class="hidden-caption">Case mode · name the pattern before revealing the caption.</p>'}${inFlags ? `<div class="ref-row">${btn('reference','Read in context ↗',`data-source="${esc(f.source)}" data-page="${esc(f.page)}"`,'ref-link')}</div>` : ''}</div>${actions(id,'image')}</article>`;
  }
  function renderImages() {
    let html = hero('THE IMAGE ATLAS','Train your eye. Then explain why.','Review the source figures with their captions, or hide the labels to rehearse a case. Favorite the images that teach you the most and mark the ones to revisit.');
    if (!state.corpus) return html + missingCorpus();
    const filtered = figures().filter(f => (state.source === 'all' || String(f.source) === state.source) && match([f.label,f.title,f.caption,sourceTitle(f.source)]) && (state.scope==='all' || (state.scope==='done' ? ann(`f:${f.id}`).done : state.scope==='favorites' ? ann(`f:${f.id}`).key : !ann(`f:${f.id}`).done)));
    html += filters('images') + `<div class="atlas-tools"><label class="toggle-label"><input type="checkbox" id="caption-toggle" ${state.caption?'checked':''}> Show diagnoses & captions</label><span>${state.caption ? 'Turn off for case rehearsal.' : 'Case mode hides separate captions; some source slides contain embedded labels.'}</span></div><div class="list-meta"><strong>${filtered.length} ${filtered.length === 1 ? 'image' : 'images'} in this view</strong><span>Click any image for its full page context.</span></div><div class="gallery">${filtered.slice(0,state.imageLimit).map(f => figureCard(f)).join('')}</div>`;
    if (!filtered.length) html += '<div class="empty"><h3>No images in this view.</h3><p>Try All images, another source, or a different search.</p></div>';
    if (filtered.length > state.imageLimit) html += btn('more',`Show next ${Math.min(24,filtered.length-state.imageLimit)} images (${filtered.length-state.imageLimit} remaining)`,'','secondary show-more');
    return html;
  }
  const isFlagged = id => {const a=ann(id); return state.flag==='all' ? !!(a.key || a.review || a.note) : !!a[state.flag];};
  function renderFlags() {
    const gs=state.guide.filter(g => isFlagged(`g:${g.id}`) && match([g.title,bodyText(g),ann(`g:${g.id}`).note]));
    const fs=figures().filter(f => isFlagged(`f:${f.id}`) && match([f.title,f.caption,ann(`f:${f.id}`).note]));
    const bs=[];
    for (const source of sources()) for (const [pi,page] of (source.pages || []).entries()) { const blocks=page.blocks?.length?page.blocks:(page.text?[{id:`${source.id}:${page.id ?? page.page}:text`,text:page.text}]:[]); blocks.forEach((b,i)=>{const id=blockKey(source,page,b,i);if(isFlagged(id)&&match([b.text,ann(id).note]))bs.push({source,page,pi,b,id});}); }
    let html = hero('THE DETAILS THAT MATTER TO YOU','Make your second pass count.','Your key points, favorite images, review flags, and personal notes stay together here. Every saved item includes a route back to its original context.') + filters('flags');
    const count=gs.length+fs.length+bs.length;
    html += `<div class="list-meta"><strong>${count} saved ${count===1?'item':'items'}</strong><span>☆ Key / favorite &nbsp; ↺ Needs review &nbsp; ✎ Notes</span></div>`;
    if (!count) return html + `<div class="empty"><h3>A place for what needs to stick.</h3><p>Tap Key point, Favorite, Review, or Add note anywhere in the study route or reader. Your saved items will appear here with their context.</p>${btn('go-guide','Return to study route')}</div>` + (!state.corpus?missingCorpus():'');
    if (gs.length) html += `<section class="flag-group"><div class="section-heading"><h3>Study points</h3><span>${gs.length} saved</span></div><div class="study-list">${gs.map(g=>guideCard(g,true)).join('')}</div></section>`;
    if (bs.length) html += `<section class="flag-group"><div class="section-heading"><h3>Source passages</h3><span>${bs.length} saved</span></div><div class="study-list">${bs.map(({source,page,pi,b,id})=>`<article id="item-${esc(id)}" class="study-card"><div class="card-inner">${check(id)}<div><p class="flag-context">${esc(source.title)} · ${esc(pageLabel(page))}</p><div class="card-body">${esc(b.text)}</div><div class="ref-row">${btn('jump-block','Read in context ↗',`data-source="${esc(source.id)}" data-index="${pi}" data-id="${esc(id)}"`,'ref-link')}</div></div></div>${actions(id)}</article>`).join('')}</div></section>`;
    if (fs.length) html += `<section class="flag-group"><div class="section-heading"><h3>Saved images</h3><span>${fs.length} saved</span></div><div class="gallery">${fs.slice(0,state.imageLimit).map(f=>figureCard(f,true)).join('')}</div>${fs.length>state.imageLimit?btn('more','Show more saved images','','secondary show-more'):''}</section>`;
    return html;
  }
  function render(options={}) {
    const scroll = options.keepScroll ? window.scrollY : null;
    $('#main').innerHTML = ({guide:renderGuide,reader:renderReader,images:renderImages,flags:renderFlags})[state.view]();
    updateNav();
    if (scroll !== null) window.scrollTo(0,scroll);
    document.querySelectorAll('img').forEach(img=>img.addEventListener('error',()=>{img.alt='Image unavailable. Open the original source or private reading room to view it.'; img.classList.add('error-image');},{once:true}));
  }
  function changeView(view) { state.view=view; state.query='';state.scope='pending';state.imageLimit=24; render(); window.scrollTo({top:0,behavior:'instant'}); }
  function scrollItem(id) { const el=document.getElementById(`item-${id}`); if(el){el.scrollIntoView({block:'center',behavior:'smooth'});el.classList.add('jump-highlight');setTimeout(()=>el.classList.remove('jump-highlight'),2200);} }
  function openReference(sourceId,pageNumber) {
    if(!state.corpus){state.view='reader';render();window.scrollTo(0,0);return;}
    const source=sourceById(sourceId);
    if(!source){toast('This source is not in the reader yet. Check the source availability notes.');return;}
    const index=(source.pages||[]).findIndex(p=>String(p.page)===String(pageNumber)||String(p.printed)===String(pageNumber));
    state.readerSource=String(source.id);state.readerIndex=index<0?0:index;state.view='reader';render();window.scrollTo(0,0);
    if(index<0&&pageNumber!=='')toast('That page is not available; opened the beginning of this source.');
  }
  function openDialog(html) {lastFocus=document.activeElement;$('#dialog-content').innerHTML=html;const d=$('#detail-dialog');if(!d.open)d.showModal();}
  function dialogShell(title,content){return `<div class="dialog-head"><h2 id="dialog-title">${esc(title)}</h2>${btn('close-dialog','×','aria-label="Close dialog"','dialog-close')}</div><div class="dialog-body">${content}</div>`;}
  function openFigure(id, reveal=false) {
    const f=figures().find(f=>String(f.id)===String(id));if(!f)return;
    const show=state.caption||reveal;
    openDialog(dialogShell(show?[f.label,f.title].filter(Boolean).join(' · ')||'Source figure':'Case rehearsal',`<img class="dialog-image" src="${esc(safeURL(f.image||f.contextImage))}" alt="${esc(show?f.title||'Source figure':'Source figure · separate caption hidden')}">${show?`<div class="dialog-caption"><p>${esc(f.caption||'')}</p><p class="flag-context">${esc(sourceTitle(f.source))} · page ${esc(f.page)}</p></div>`:`<div class="dialog-actions">${btn('reveal-figure','Reveal diagnosis & caption',`data-figure="${esc(f.id)}"`,'primary')}</div>`}<div class="dialog-actions">${btn('reference','Read source page ↗',`data-source="${esc(f.source)}" data-page="${esc(f.page)}"`)}${btn('dialog-toggle',ann(`f:${f.id}`).key?'★ Favorited':'☆ Favorite',`data-id="f:${esc(f.id)}" data-prop="key" data-figure="${esc(f.id)}" data-reveal="${show}" aria-pressed="${!!ann(`f:${f.id}`).key}"`)}${btn('dialog-toggle',ann(`f:${f.id}`).review?'↺ Flagged for review':'↺ Needs review',`data-id="f:${esc(f.id)}" data-prop="review" data-figure="${esc(f.id)}" data-reveal="${show}" aria-pressed="${!!ann(`f:${f.id}`).review}"`)}${btn('dialog-toggle',ann(`f:${f.id}`).done?'✓ Reviewed':'Mark reviewed',`data-id="f:${esc(f.id)}" data-prop="done" data-figure="${esc(f.id)}" data-reveal="${show}" aria-pressed="${!!ann(`f:${f.id}`).done}"`)}</div>${f.contextImage&&show?`<details class="context-details"><summary>Show full page context</summary><img src="${esc(safeURL(f.contextImage))}" alt="Full source page context" loading="lazy"></details>`:''}`));
  }
  function pageDialog(){const s=sourceById(state.readerSource),p=s?.pages?.[state.readerIndex];if(p?.image)openDialog(dialogShell(`${s.title} · ${pageLabel(p)}`,`<a href="${esc(safeURL(p.image))}" target="_blank" rel="noopener noreferrer"><img class="dialog-image" src="${esc(safeURL(p.image))}" alt="Full original page"></a><p class="flag-context">Open the page image to zoom further in your browser.</p>`));}
  function progressJSON(){return JSON.stringify({app:'bone-tumor-conference',version:1,exported:new Date().toISOString(),annotations:state.annotations},null,2);}
  function exportProgress(){openDialog(dialogShell('Move your study progress',`<p>Download a backup file, or copy the text below and paste it into Import on your other device. Your current notes and flags are included.</p><div class="dialog-actions">${btn('download-progress','Download JSON backup','','primary')}${btn('copy-progress','Copy backup text')}</div><label for="backup-json">Complete progress backup</label><textarea id="backup-json" readonly rows="12" style="width:100%;font:12px monospace">${esc(progressJSON())}</textarea>`));}
  function downloadProgress(){const blob=new Blob([progressJSON()],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`bone-tumor-study-progress-${new Date().toISOString().slice(0,10)}.json`;document.body.appendChild(a);a.click();setTimeout(()=>{a.remove();URL.revokeObjectURL(url);},10000);toast('Backup download requested. Copy the backup text if your browser blocks downloads.');}
  function showImport(){openDialog(dialogShell('Import study progress',`<p>Choose a JSON backup file or paste the backup text. The newest saved version of each whole item is kept.</p><div class="dialog-actions">${btn('choose-progress','Choose backup file','','primary')}</div><label for="import-json">Or paste your progress backup</label><textarea id="import-json" rows="12" style="width:100%;font:12px monospace"></textarea><div class="dialog-actions">${btn('import-text','Import pasted backup','','primary')}</div>`));}
  async function importProgress(file){if(!file)return;if(file.size>15000000){toast('This file is too large to be a study progress export.');return;}try{const data=JSON.parse(await file.text());if(data.app!=='bone-tumor-conference'||data.version!==1||!data.annotations||typeof data.annotations!=='object'||Array.isArray(data.annotations))throw Error('Invalid');const incoming=cleanAnnotations(data.annotations);let count=0;for(const [id,item]of Object.entries(incoming)){if(!state.annotations[id]||item.updated>=(ann(id).updated||0)){state.annotations[id]=item;count++;}}save();render({keepScroll:true});toast(`Imported ${count} saved items. The newest version of each item was kept.`);}catch{toast('Could not import this file. Choose a progress JSON exported from this study app.');}$('#import-file').value='';}
  function help(){openDialog(dialogShell('Your study workspace',`<div class="dialog-help"><p><strong>Study route:</strong> a synthesis for conference preparation. Check a point to remove it from To study; Show all brings it back. Reveal follow-up answers after rehearsing aloud.</p><p><strong>Source reader:</strong> every available source page, its original image, and extracted passages. Check individual passages or mark the whole page complete. Completing the study route does not complete the full source reading.</p><p><strong>Image atlas:</strong> browse source figures with captions. Turn captions off for case rehearsal, then open an image to reveal the diagnosis. Some diagnosis text may be printed in the source image itself.</p><p><strong>Key / Favorite and Review are independent.</strong> A key point is worth keeping; a review flag means you want another pass. Completed items keep their flags and notes. Your flags links each item back to its source context.</p><p><strong>Progress is local to this browser and this site.</strong> There is no automatic sync. Export progress, transfer the JSON file, and import it on your other device or site. Import merges saved items and keeps the newest saved version of each whole item. Export from each device before merging if both have new changes.</p><p>If your browser blocks storage or you use private browsing, export before closing. Source text is extracted from the original pages; use the page image to verify tables, layout, and figure relationships.</p><p><strong>Coverage:</strong> 200 consolidated study points; 61 textbook pages, 17 ACR pages including the correction, and all 59 RSNA slides. The atlas has 129 textbook figures, 10 ACR figures, and 59 complete slides with panels grouped. Report templates are on RSNA slides 47–48. The original ACR Figure 9 is flagged as superseded; the atlas uses the correction.</p></div>`));}
  document.addEventListener('click',e=>{
    const target=e.target.closest('[data-action]');if(!target||target.disabled)return;const action=target.dataset.action;e.preventDefault();
    if(action==='view'){changeView(target.dataset.view);return;}
    if(action==='toggle'){const{id,prop}=target.dataset;setAnnotation(id,prop,!ann(id)[prop]);render({keepScroll:true});return;}
    if(action==='note'){const id=target.dataset.id;state.notes.has(id)?state.notes.delete(id):state.notes.add(id);render({keepScroll:true});if(state.notes.has(id))document.getElementById(`note-${id}`)?.focus({preventScroll:true});return;}
    if(action==='scope'){state.scope=target.dataset.value;state.imageLimit=24;render({keepScroll:true});return;}
    if(action==='source'){state.readerSource=target.dataset.source;state.readerIndex=0;render({keepScroll:true});return;}
    if(action==='page-prev'||action==='page-next'){state.readerIndex+=action==='page-next'?1:-1;render();$('#reader-page')?.scrollIntoView({block:'start',behavior:'instant'});return;}
    if(action==='page-done'){const s=sourceById(state.readerSource),p=s.pages[state.readerIndex],done=!ann(pageKey(s,p)).done;setAnnotation(pageKey(s,p),'done',done);const blocks=p.blocks?.length?p.blocks:(p.text?[{id:`${s.id}:${p.id??p.page}:text`,text:p.text}]:[]);blocks.forEach((b,i)=>state.annotations[blockKey(s,p,b,i)]={...ann(blockKey(s,p,b,i)),done,updated:Date.now()});save();render({keepScroll:true});toast(done?'Page completed. Your full-source progress has been updated.':'Page returned to reading.');return;}
    if(action==='reference'){if($('#detail-dialog').open)$('#detail-dialog').close();openReference(target.dataset.source,target.dataset.page);return;}
    if(action==='jump-guide'){state.view='guide';state.scope='all';state.query='';state.topic='all';render();scrollItem(`g:${target.dataset.item}`);return;}
    if(action==='jump-block'){state.readerSource=target.dataset.source;state.readerIndex=Number(target.dataset.index);state.readerHideRead=false;state.view='reader';render();scrollItem(target.dataset.id);return;}
    if(action==='more'){state.imageLimit+=24;render({keepScroll:true});return;}
    if(action==='figure'){openFigure(target.dataset.figure);return;}
    if(action==='reveal-figure'){openFigure(target.dataset.figure,true);return;}
    if(action==='dialog-toggle'){const{id,prop}=target.dataset;setAnnotation(id,prop,!ann(id)[prop]);render({keepScroll:true});openFigure(target.dataset.figure,target.dataset.reveal==='true');return;}
    if(action==='page-image'){pageDialog();return;}
    if(action==='close-dialog'){$('#detail-dialog').close();return;}
    if(action==='export'){exportProgress();return;}
    if(action==='import'){showImport();return;}
    if(action==='choose-progress'){$('#import-file').click();return;}
    if(action==='download-progress'){downloadProgress();return;}
    if(action==='import-text'){const value=$('#import-json').value;$('#detail-dialog').close();importProgress(new Blob([value],{type:'application/json'}));return;}
    if(action==='copy-progress'){const field=$('#backup-json');field.focus();field.select();if(navigator.clipboard?.writeText){navigator.clipboard.writeText(field.value).then(()=>toast('Backup copied. Paste it into Import on your other device.')).catch(()=>toast('Select and copy the highlighted backup text.'));}else toast('Select and copy the highlighted backup text.');return;}
    if(action==='help'){help();return;}
    if(action==='go-guide'){changeView('guide');return;}
  });
  document.addEventListener('input',e=>{
    if(e.target.matches('[data-note]')){setAnnotation(e.target.dataset.note,'note',e.target.value);return;}
    if(e.target.id==='search-input'){const value=e.target.value,start=e.target.selectionStart;clearTimeout(searchTimer);searchTimer=setTimeout(()=>{state.query=value;state.imageLimit=24;render({keepScroll:true});const input=$('#search-input');input.focus({preventScroll:true});try{input.setSelectionRange(start,start);}catch{}},220);}
  });
  document.addEventListener('change',e=>{
    const id=e.target.id;
    if(id==='import-file'){importProgress(e.target.files[0]);return;}
    if(id==='topic-filter')state.topic=e.target.value;
    else if(id==='source-filter')state.source=e.target.value;
    else if(id==='flag-filter')state.flag=e.target.value;
    else if(id==='page-select'||id==='page-select-bottom')state.readerIndex=Number(e.target.value);
    else if(id==='hide-read')state.readerHideRead=e.target.checked;
    else if(id==='caption-toggle')state.caption=e.target.checked;
    else return;
    state.imageLimit=24;render({keepScroll:true});
  });
  $('#detail-dialog').addEventListener('close',()=>{if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});});
  $('#detail-dialog').addEventListener('click',e=>{if(e.target===$('#detail-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}});
  window.addEventListener('storage',e=>{if(e.key===STORAGE_KEY){try{const incoming=cleanAnnotations(JSON.parse(e.newValue||'{}').annotations);for(const[id,a]of Object.entries(incoming))if(!state.annotations[id]||a.updated>=(ann(id).updated||0))state.annotations[id]=a;const active=document.activeElement;if(!active?.matches('[data-note]'))render({keepScroll:true});else updateNav();}catch{}}});
  async function init(){readStored();const results=await Promise.allSettled([fetch('guide.json', {cache:'no-store'}).then(r=>{if(!r.ok)throw Error('guide');return r.json();}),fetch('corpus.json', {cache:'no-store'}).then(r=>{if(!r.ok)throw Error('corpus');return r.json();})]);if(results[0].status==='fulfilled'){const data=results[0].value;state.guide=Array.isArray(data)?data:(data.guide||data.points||[]);}if(results[1].status==='fulfilled'&&Array.isArray(results[1].value.sources)){state.corpus=results[1].value;}if(!state.guide.length){$('#main').innerHTML=hero('STUDY MATERIAL','The study route could not be loaded.','Refresh this page to try again. The private reading room may still be available.')+missingCorpus();updateNav();return;}render();}
  init();
})();
