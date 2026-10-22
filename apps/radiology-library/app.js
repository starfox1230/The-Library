'use strict';
(() => {
  const data = window.RADIOLOGY_CATALOG;
  if (!data) return;
  const $ = id => document.getElementById(id);
  const items = data.items;
  const key = 'radiology-library-saved-v1';
  let saved;
  try { saved = new Set(JSON.parse(localStorage.getItem(key) || '[]').filter(id => items.some(x => x.id === id))); }
  catch { saved = new Set(); }
  const initial = new URLSearchParams(location.search);
  let view = ['all','teaching','helpful','saved'].includes(initial.get('view')) ? initial.get('view') : 'all';
  let group = initial.get('group') === 'edited' ? 'edited' : initial.get('group') === 'subject' ? 'subjects' : 'types';
  const sortModes = ['recommended','newest','oldest','name'];
  $('sort').value = sortModes.includes(initial.get('sort')) ? initial.get('sort') : group === 'edited' ? 'newest' : 'recommended';
  const descriptions = {
    'Learn & visualize':'Focused lessons, interactive explanations, and concept tools',
    'Quiz & recall':'Question banks, chapter quizzes, and retrieval practice',
    'Images & cases':'Pattern recognition, image exploration, and case practice',
    'Read & watch':'Textbooks, articles, lectures, and listening tools',
    'Flashcards & Anki':'Card workflows, package tools, and review games',
    'Study organization':'Plans, progress trackers, capture workflows, and timers',
    'Clinical reference':'Algorithms, checklists, and pocket references',
    'Reporting & workflow':'Report builders, templates, phrases, and revision tools',
    'Residency & logistics':'Schedules, shifts, and residency planning'
  };
  const views = {
    all:['All resources','Expand a category to see what’s inside. Resources can appear in more than one category.'],
    teaching:['Teaches a subject','The range of your focused lessons and explanations. Each resource describes what it teaches; quizzes and trackers have their own categories.'],
    helpful:['Particularly helpful','Suggested starting points based on the material and study features available. Each selection includes a reason; these are judgments, not measured rankings.'],
    saved:['My saved links','Your personal shortlist, saved in this browser. Use the star on any resource to keep it here.']
  };
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link = (url, text, cls='') => `<a href="${esc(url)}" target="_blank" rel="noopener"${cls ? ` class="${cls}"` : ''}>${esc(text)}</a>`;
  const subjects = [...new Set(items.flatMap(x => x.subjects))].sort();
  const timestamp = item => item.lastEdited?.at ? Date.parse(item.lastEdited.at) : NaN;
  const dateText = item => Number.isFinite(timestamp(item)) ? new Intl.DateTimeFormat('en-US',{month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(timestamp(item)) : 'Date unverified';
  const editMonth = item => Number.isFinite(timestamp(item)) ? new Date(timestamp(item)).toISOString().slice(0,7) : 'unknown';
  const monthText = month => month === 'unknown' ? 'Edit date unverified' : new Intl.DateTimeFormat('en-US',{month:'long',year:'numeric',timeZone:'UTC'}).format(new Date(month+'-01T00:00:00Z'));
  function compare(a,b) {
    const mode=$('sort').value;
    if(mode==='newest'||mode==='oldest') {
      const at=timestamp(a),bt=timestamp(b);
      if(Number.isFinite(at)!==Number.isFinite(bt))return Number.isFinite(at)?-1:1;
      if(Number.isFinite(at)&&at!==bt)return mode==='newest'?bt-at:at-bt;
    }
    if(mode==='recommended')return Number(!!b.recommendation)-Number(!!a.recommendation)||a.title.localeCompare(b.title);
    return a.title.localeCompare(b.title);
  }
  for (const [id,options] of [['subject',subjects],['type',data.types]]) {
    for (const text of options) { const option = document.createElement('option'); option.value=text;option.textContent=text;$(id).append(option); }
    $(id).value = options.includes(initial.get(id)) ? initial.get(id) : '';
  }
  $('search').value = initial.get('q') || '';
  $('total').textContent = items.length;
  $('teaching-total').textContent = items.filter(x => x.teaches).length;
  $('audit-method').textContent = `${data.audit.repositoriesScanned} GitHub repositories and ${data.audit.sitesScanned} Sites reviewed. ${data.audit.method}`;
  $('audit-limits').textContent = data.audit.limits;
  $('audit-duplicates').textContent = data.audit.duplicates;
  if(data.audit.editDates) {
    $('edit-date-method').textContent=`Edit dates verified for ${data.audit.editDates.known}/${data.audit.editDates.total} resources. ${data.audit.editDates.method}`;
    $('edit-date-limits').textContent=`${data.audit.editDates.limits} Last checked: ${data.audit.editDates.checkedAt.slice(0,10)} (UTC).`;
  }
  const featuredTitles = ['Ultrasound Physics Interactive Modules','Germ Cell & Inclusion Cyst Arcade','AI for Radiology Study OS'];
  $('featured').innerHTML = featuredTitles.map((title,i) => {
    const x=items.find(x => x.title===title);
    return `<article class="feature"><span class="number">0${i+1} / ${esc(x.subjects[0].toUpperCase())}</span><h3>${esc(x.title)}</h3><p>${esc(x.recommendation)}</p>${link(x.url,'Open existing resource ↗')}</article>`;
  }).join('');
  let noticeTimer;
  function notify(message) { $('notice').textContent=message;$('notice').style.display='block';clearTimeout(noticeTimer);noticeTimer=setTimeout(() => {$('notice').style.display='none';},3500); }
  function updateCounts() {
    const counts={all:items.length,teaching:items.filter(x=>x.teaches).length,helpful:items.filter(x=>x.recommendation).length,saved:saved.size};
    for (const [name,count] of Object.entries(counts)) document.querySelector(`[data-count="${name}"]`).textContent=count;
  }
  function saveUrl() {
    const p=new URLSearchParams();
    if(view!=='all')p.set('view',view);
    if(group!=='types')p.set('group',group==='edited'?'edited':'subject');
    if($('sort').value!=='recommended')p.set('sort',$('sort').value);
    for(const [id,param] of [['search','q'],['subject','subject'],['type','type']])if($(id).value)p.set(param,$(id).value);
    try{history.replaceState(null,'',location.pathname+(p.size?'?'+p:'')+location.hash);}catch{}
  }
  function card(x) {
    const edit=x.lastEdited;
    const date=Number.isFinite(timestamp(x))?`<time datetime="${esc(edit.at)}">Last edited ${esc(dateText(x))}</time>`:'Edit date unverified';
    const provenance=edit?.at?`<p>${esc(edit.label)} · ${esc(edit.at)}${edit.versionNumber?' · saved version '+esc(edit.versionNumber):''}</p>${edit.path?`<p>Tracked path: ${esc(edit.path)}</p>`:''}${edit.commitSha?`<p>Commit: <code>${esc(edit.commitSha.slice(0,12))}</code></p>`:''}${link(edit.url,'View edit evidence ↗')}`:'<p>No verified edit date is available.</p>';
    return `<article class="resource"><button class="bookmark" data-save="${x.id}" aria-pressed="${saved.has(x.id)}" aria-label="${saved.has(x.id)?'Unsave':'Save'} ${esc(x.title)}">${saved.has(x.id)?'★':'☆'}</button><h4>${link(x.url,x.title+' ↗')}</h4><div class="chips">${x.teaches?'<span class="chip teaching">Teaches a subject</span>':''}${x.subjects.map(s=>`<span class="chip">${esc(s)}</span>`).join('')}</div><div class="edit-date">${date}</div><p>${esc(x.scope)}</p>${x.coverage?`<details><summary>Full topic range</summary><ul>${x.coverage.map(topic=>`<li>${esc(topic)}</li>`).join('')}</ul></details>`:''}${x.recommendation?`<div class="recommend"><b>Why it may help</b>${esc(x.recommendation)}</div>`:''}<div class="resource-meta"><span>${esc(x.status)}</span>${link(x.url,x.status==='Source / setup required'?'View source ↗':'Open resource ↗')}</div><details><summary>Source, edit date & ${x.related.length?'other versions':'catalog notes'}</summary><p>${esc(x.evidence)} · ${esc(data.updated)}</p>${provenance}${link(x.source,'Source / provenance ↗')}${x.related.map(r=>link(r.url,r.label+' ↗')).join('')}</details></article>`;
  }
  function render(resetOpen=false) {
    const open = new Set([...document.querySelectorAll('.category[open]')].map(x=>x.dataset.category));
    const query = $('search').value.trim().toLowerCase();
    const words=query.split(/\s+/).filter(Boolean);
    const matched=items.filter(x => (view!=='teaching'||x.teaches) && (view!=='helpful'||x.recommendation) && (view!=='saved'||saved.has(x.id)) && (!$('subject').value||x.subjects.includes($('subject').value)) && (!$('type').value||x.types.includes($('type').value)) && words.every(w=>[x.title,x.scope,x.recommendation,...x.subjects,...x.types,...(x.coverage||[])].join(' ').toLowerCase().includes(w)));
    $('view-title').textContent=views[view][0];$('view-description').textContent=group==='edited'&&view==='all'?'Browse by the month each resource was last edited. Dates come from source history; expand a resource’s source notes for the exact metric.':views[view][1];
    $('start').hidden=view!=='all'||!!query||!!$('subject').value||!!$('type').value||group==='edited'||$('sort').value!=='recommended';
    $('result-count').textContent=`${matched.length} unique ${matched.length===1?'resource':'resources'}`;
    $('clear').hidden=!query&&!$('subject').value&&!$('type').value;
    $('empty').hidden=matched.length>0;
    $('empty-message').textContent=view==='saved'&&!saved.size?'Use the star beside a resource to save a link here.':'Try a broader search or clear the filters.';
    $('empty-clear').textContent=view==='saved'&&!saved.size?'Browse all resources':'Clear filters';
    document.querySelectorAll('[data-view]').forEach(b => {b.classList.toggle('selected',b.dataset.view===view);b.setAttribute('aria-pressed',String(b.dataset.view===view));});
    for(const [name,value] of [['type','types'],['subject','subjects'],['edited','edited']]) {const active=group===value;$('group-'+name).classList.toggle('active',active);$('group-'+name).setAttribute('aria-pressed',String(active));}
    const categories=group==='types'?data.types:group==='subjects'?subjects:[...new Set(matched.map(editMonth))].sort((a,b)=>a==='unknown'?1:b==='unknown'?-1:$('sort').value==='oldest'?a.localeCompare(b):b.localeCompare(a));
    let index=0;
    $('groups').innerHTML=categories.map(category=>{
      const entries=matched.filter(x=>group==='edited'?editMonth(x)===category:x[group].includes(category)).sort(compare);
      if(!entries.length)return '';
      const isOpen=query||$('subject').value||$('type').value||view==='helpful'||view==='saved'||(resetOpen?(group==='edited'||view!=='all')&&index===0:open.has(category));index++;
      return `<details class="category" data-category="${esc(category)}"${isOpen?' open':''}><summary><div><h3>${esc(group==='edited'?monthText(category):category)}</h3>${group==='types'?`<p>${esc(descriptions[category])}</p>`:''}</div><span class="count">${entries.length}</span></summary><div class="resources">${entries.map(card).join('')}</div></details>`;
    }).join('');updateCounts();saveUrl();
  }
  function setView(next){view=next;if(next==='teaching')group='subjects';render(true);}
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
  $('see-helpful').addEventListener('click',()=>{setView('helpful');$('browse').scrollIntoView({behavior:'instant'});});
  for(const id of ['search','subject','type'])$(id).addEventListener(id==='search'?'input':'change',()=>render(true));
  for(const [id,value] of [['group-type','types'],['group-subject','subjects'],['group-edited','edited']])$(id).addEventListener('click',()=>{group=value;if(group==='edited'&&!['newest','oldest'].includes($('sort').value))$('sort').value='newest';render(true);});
  $('sort').addEventListener('change',()=>{if(['newest','oldest'].includes($('sort').value))group='edited';else if(group==='edited')group='types';render(true);});
  function clear(){if(view==='saved'&&!saved.size)view='all';for(const id of ['search','subject','type'])$(id).value='';render(true);}
  $('clear').addEventListener('click',clear);$('empty-clear').addEventListener('click',clear);
  $('expand').addEventListener('click',()=>document.querySelectorAll('.category').forEach(x=>x.open=true));
  $('collapse').addEventListener('click',()=>document.querySelectorAll('.category').forEach(x=>x.open=false));
  $('groups').addEventListener('click',e=>{
    const button=e.target.closest('[data-save]');if(!button)return;
    const id=button.dataset.save;const adding=!saved.has(id);adding?saved.add(id):saved.delete(id);
    try{localStorage.setItem(key,JSON.stringify([...saved]));}catch{notify('This browser cannot retain saved links after you close the page.');}
    if(view==='saved'&&!adding){render();return;}
    document.querySelectorAll(`[data-save="${id}"]`).forEach(b=>{b.textContent=adding?'★':'☆';b.setAttribute('aria-pressed',String(adding));b.setAttribute('aria-label',`${adding?'Unsave':'Save'} ${items.find(x=>x.id===id).title}`);});updateCounts();
  });
  $('export').addEventListener('click',()=>{
    const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='radiology-link-catalog.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  render(true);
})();
