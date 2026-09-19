'use strict';
const KEY = 'radiology-video-library-v2';
const OLD_KEY = 'neuroradish-catalog-v1';
const SUMMARY = `Summarize this radiology teaching transcript for a radiology resident. Be concise and stay grounded in the transcript.
For each pathology discussed, list:
1. Pathology name and the main teaching point.
2. Radiologic features emphasized (modality, sequence, signal/density, enhancement, location, and pattern when stated).
3. Distinguishing findings, differentials, pitfalls, and exam pearls explicitly emphasized.
Finish with 3–5 high-yield takeaways. If this is an anatomy or physics lesson, summarize its concepts instead of inventing pathologies. Do not infer findings from images you cannot see or silently add outside facts. Flag unclear automatic-caption terminology. Include useful transcript timestamps.`;
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const natural = (a,b) => String(a).localeCompare(String(b),undefined,{numeric:true,sensitivity:'base'});
const defaultPrefs = () => ({search:'',series:'',topic:'',playlist:'',sort:'study',status:'need',format:'all',filterOpen:false,queue:[],current:null,scroll:0,legacy:null});
const fresh = () => ({version:2,channel:null,page:'channels',channels:{},watched:{},favorites:{},notes:{},transcripts:{},prompt:SUMMARY});
let state=fresh(), catalog, byId=new Map(), limit=40, toastTimer, transcriptRequest=0;
let storageOK=true;

function normalize(raw) {
  const s=fresh();
  if(!raw || typeof raw!=='object' || Array.isArray(raw)) return s;
  for(const key of ['watched','favorites','notes','transcripts']) {
    if(raw[key] && typeof raw[key]==='object' && !Array.isArray(raw[key])) {
      for(const [id,value] of Object.entries(raw[key])) {
        if(!/^[\w-]{11}$/.test(id)) continue;
        if(['notes','transcripts'].includes(key) ? typeof value==='string' : typeof value==='boolean') s[key][id]=value;
      }
    }
  }
  if(typeof raw.prompt==='string') s.prompt=raw.prompt;
  if(typeof raw.channel==='string') s.channel=raw.channel;
  if(['channels','library','study'].includes(raw.page)) s.page=raw.page;
  for(const id of ['neuroradish','learn','neuroradiologist','tutorials']) {
    const p=raw.channels?.[id]; if(!p || typeof p!=='object') continue;
    const next=defaultPrefs();
    for(const field of ['search','series','topic','playlist','sort','status','format']) if(typeof p[field]==='string') next[field]=p[field];
    next.filterOpen=Boolean(p.filterOpen);
    next.queue=Array.isArray(p.queue)?p.queue.filter(x=>typeof x==='string' && /^[\w-]{11}$/.test(x)):[];
    next.current=typeof p.current==='string'?p.current:null;
    next.scroll=Number.isFinite(p.scroll)?Math.max(0,p.scroll):0;
    if(p.legacy && typeof p.legacy==='object') next.legacy=p.legacy;
    s.channels[id]=next;
  }
  return s;
}
function read() {
  try {
    const raw=localStorage.getItem(KEY);
    if(raw) return normalize(JSON.parse(raw));
    const old=JSON.parse(localStorage.getItem(OLD_KEY)||'null');
    if(!old) return fresh();
    return migrateOld(old);
  } catch { storageOK=false; return fresh(); }
}
function migrateOld(old) {
    const s=normalize({watched:old.watched,favorites:old.favorites,notes:old.notes});
    s.channel='neuroradish'; s.page='library';
    const p=defaultPrefs(), u=old.ui||{};
    p.search=typeof u.search==='string'?u.search:'';
    p.sort=u.sort==='topic'?'study':u.sort||'study';
    p.status={need:'need',all:'all',seen:'seen',favorites:'favorites',shorts:'all'}[u.view]||'need';
    if(u.view==='shorts') p.format='Short';
    p.filterOpen=Boolean(u.filterOpen);
    // Preserve arbitrary old multi-select filters, not merely the named preset.
    if(u.filters && Object.values(u.filters).some(x=>Array.isArray(x)&&x.length)) p.legacy=u.filters;
    s.channels.neuroradish=p;
    return s;
}
function save() {
  try { localStorage.setItem(KEY,JSON.stringify(state)); storageOK=true; }
  catch { storageOK=false; }
  $('storageStatus').textContent=storageOK?'Saved on this browser/device. Backup lets you move your progress.':'Your browser could not save changes. Keep this page open and download a backup.';
  $('storageStatus').classList.toggle('error',!storageOK);
}
const prefs=()=>state.channels[state.channel]||(state.channels[state.channel]=defaultPrefs());
const channelVideos=()=>catalog.videos.filter(v=>v.channel===state.channel);
const current=()=>byId.get(prefs().current);
function duration(s) { if(!Number.isFinite(s)) return 'Length unknown'; const n=Math.round(s); return n>=3600?`${Math.floor(n/3600)}:${String(Math.floor(n/60)%60).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`:`${Math.floor(n/60)}:${String(n%60).padStart(2,'0')}`; }
function date(v) {return (v.upload_date||'').replace(/^(\d{4})(\d{2})(\d{2})$/,'$1-$2-$3');}
function legacyMatch(v,p) {
  if(!p.legacy) return true;
  const old=catalog.legacy?.[v.id];
  return ['track','category','format'].every(k=>!Array.isArray(p.legacy[k])||!p.legacy[k].length||p.legacy[k].includes(old?.[k]));
}
function selected() {
  const p=prefs(), term=p.search.trim().toLowerCase();
  const rows=channelVideos().filter(v=>
    (p.format==='all'||v.format===p.format) && (!p.series||v.series===p.series) &&
    (!p.topic||v.topics.includes(p.topic)) && (!p.playlist||v.playlists.some(x=>x.id===p.playlist)) &&
    (!term||[v.title,v.series,...v.topics,v.description].join(' ').toLowerCase().includes(term)) &&
    (p.status!=='need'||!state.watched[v.id]) && (p.status!=='seen'||state.watched[v.id]) &&
    (p.status!=='favorites'||state.favorites[v.id]) && legacyMatch(v,p));
  const missingLast=(a,b,field,desc=false)=> {
    const x=field(a),y=field(b); if(!x && x!==0)return (!y && y!==0)?0:1;if(!y&&y!==0)return -1;
    return (typeof x==='number'?x-y:natural(x,y))*(desc?-1:1);
  };
  rows.sort((a,b)=>{
    if(p.sort==='playlist'&&p.playlist)return a.playlists.find(x=>x.id===p.playlist).position-b.playlists.find(x=>x.id===p.playlist).position;
    if(p.sort==='title')return natural(a.title,b.title);
    if(p.sort==='newest'||p.sort==='oldest')return missingLast(a,b,date,p.sort==='newest')||natural(a.title,b.title);
    if(p.sort==='shortest'||p.sort==='longest')return missingLast(a,b,x=>x.duration,p.sort==='longest')||natural(a.title,b.title);
    return a.study_order-b.study_order||natural(a.series,b.series)||natural(a.title,b.title);
  });
  return rows;
}
function showPage(page,top=true) {
  if(state.page==='library' && page!=='library') prefs().scroll=window.scrollY;
  if(page!=='channels'&&!state.channel) page='channels';
  if(page==='study'&&!current()) {startSelection();return;}
  state.page=page;
  for(const name of ['channels','library','study']) $(name+'Page').hidden=page!==name;
  if(page!=='study') {$('player').innerHTML='';transcriptRequest++;}
  document.querySelectorAll('[data-page]').forEach(b=>b.setAttribute('aria-current',b.dataset.page===page?'page':'false'));
  if(page==='channels') renderChannels();
  if(page==='library') renderLibrary();
  if(page==='study') renderStudy();
  save();
  if(top) window.scrollTo(0,page==='library'?prefs().scroll:0);
}
function renderChannels() {
  $('channelCards').innerHTML=catalog.channels.map((c,i)=>{
    const list=catalog.videos.filter(v=>v.channel===c.id), n=list.filter(v=>state.watched[v.id]).length;
    const shorts=list.filter(v=>v.format==='Short').length, saved=list.filter(v=>v.transcript.status==='saved').length;
    return `<button class="channel-card" data-channel="${c.id}"><span class="initials">0${i+1} / ${['NR','LN','TN','RT'][i]}</span><div><h2>${esc(c.name)}</h2><p>${list.length} lessons · ${shorts} Shorts · ${saved} transcripts</p></div><span class="card-bottom"><span>${n} of ${list.length} watched</span><span>Enter library →</span></span></button>`;
  }).join('');
  $('channelCards').querySelectorAll('button').forEach(b=>b.onclick=()=>{state.channel=b.dataset.channel;limit=40;showPage('library');});
  $('coverage').textContent=`Inventory checked ${catalog.fetched_at.slice(0,10)} · ${catalog.videos.length} unique public uploads. Videos, Shorts and live tabs checked separately. Private/deleted videos are not available.`;
}
function options(id,values,placeholder,value) {
  const entries=values.map(x=>typeof x==='string'?{id:x,title:x}:x);
  $(id).innerHTML=`<option value="">${placeholder}</option>`+entries.map(x=>`<option value="${esc(x.id)}">${esc(x.title)}</option>`).join('');
  $(id).value=value;
}
function renderLibrary() {
  const c=catalog.channels.find(x=>x.id===state.channel), all=channelVideos(), p=prefs(), rows=selected();
  $('channelEyebrow').textContent='YOUR CHANNEL LIBRARY';$('channelName').textContent=c.name;
  const watched=all.filter(v=>state.watched[v.id]).length;
  $('progressText').textContent=`${watched} / ${all.length} watched`;$('progress').value=all.length?watched/all.length*100:0;
  const last=rows.find(v=>v.id===p.current&&!state.watched[v.id]);
  const next=last||rows.find(v=>!state.watched[v.id]);
  $('resume').innerHTML=next?`<p class="eyebrow">${last?'CONTINUE YOUR SELECTION':'NEXT IN YOUR SELECTION'}</p><h2>${esc(next.title)}</h2><p>${esc(next.series)} · ${next.format} · ${duration(next.duration)}</p><button class="primary" id="resumeButton">${last?'Resume lesson':'Start lesson'} →</button>`:`<h2>${rows.length?'Selection complete':'No lessons in this selection'}</h2><p>Your saved filters stay in place. Choose another series or change the status to revisit lessons.</p>`;
  if(next)$('resumeButton').onclick=()=>openLesson(next.id,rows);
  options('series',[...new Set(all.map(x=>x.series))].sort(natural),'Every series',p.series);
  options('topic',[...new Set(all.flatMap(x=>x.topics))].sort(natural),'Every topic',p.topic);
  options('playlist',c.playlists.filter(x=>x.count),'Every playlist',p.playlist);
  for(const key of ['search','sort','status'])$(key).value=p[key];
  $('filters').hidden=!p.filterOpen;$('filterButton').setAttribute('aria-expanded',String(p.filterOpen));
  document.querySelectorAll('[data-format]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.format===p.format)));
  const count=[p.series,p.topic,p.playlist,p.search,p.format==='all'?'':p.format,p.legacy].filter(Boolean).length;
  $('filterCount').textContent=count?`(${count})`:'';
  const approach=[p.series||'Every series',p.format==='all'?'All formats':p.format,p.topic,p.playlist?c.playlists.find(x=>x.id===p.playlist)?.title:'',$('sort').selectedOptions[0]?.textContent,p.legacy?'Previous custom filters retained; Clear filters to replace them':''].filter(Boolean);
  $('savedApproach').textContent=approach.join(' · ');
  $('resultCount').textContent=`${rows.length} lessons in this selection`;$('startQueue').disabled=!rows.length;
  $('videoList').innerHTML=rows.length?rows.slice(0,limit).map(v=>`<article class="lesson ${state.watched[v.id]?'watched':''}"><img loading="lazy" src="https://i.ytimg.com/vi/${v.id}/mqdefault.jpg" alt=""><div><span class="tag">${v.format} · ${esc(v.series)}</span><button class="lesson-title" data-lesson="${v.id}">${esc(v.title)}</button><p class="meta">${duration(v.duration)} · ${state.watched[v.id]?'✓ Watched · ':''}${v.transcript.status==='saved'?'Transcript saved':'Transcript fallback available'}</p></div><button data-lesson="${v.id}">Study →</button></article>`).join(''):'<div class="empty">No matches. Your selection is saved; use Refine to adjust it.</div>';
  $('videoList').querySelectorAll('[data-lesson]').forEach(b=>b.onclick=()=>openLesson(b.dataset.lesson,rows));
  $('showMore').hidden=rows.length<=limit;
}
function openLesson(id,rows) {
  const p=prefs();p.queue=rows.map(v=>v.id);p.current=id;showPage('study');
}
function startSelection() {
  if(!state.channel){showPage('channels');return;}
  const rows=selected();if(!rows.length){showPage('library');toast('No lessons match your saved selection.');return;}
  openLesson(rows[0].id,rows);
}
function move(step,done=false) {
  const p=prefs(),v=current();if(!v)return;
  if(done)state.watched[v.id]=true;
  const pos=p.queue.indexOf(v.id), next=byId.get(p.queue[pos+step]);
  if(next&&next.channel===state.channel){p.current=next.id;showPage('study');}
  else {save();showPage('library');toast('You reached the end of this selection.');}
}
async function renderStudy() {
  const v=current();if(!v)return;
  const p=prefs(),pos=p.queue.indexOf(v.id), token=++transcriptRequest;
  $('studyPosition').textContent=`${catalog.channels.find(c=>c.id===v.channel).name} / ${pos+1} OF ${p.queue.length} IN YOUR QUEUE`;
  $('studyTitle').textContent=v.title;$('studyMeta').textContent=`${v.series} · ${v.format} · ${duration(v.duration)}`;
  $('player').innerHTML=`<img src="https://i.ytimg.com/vi/${v.id}/hqdefault.jpg" alt=""><button id="embedPlay">▶ Play here</button>`;
  $('embedPlay').onclick=()=>{$('player').innerHTML=`<iframe src="https://www.youtube-nocookie.com/embed/${v.id}?autoplay=1" title="${esc(v.title)}" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>`;};
  $('previous').disabled=pos<=0;$('next').disabled=pos>=p.queue.length-1;
  updateStudyButtons();$('notes').value=state.notes[v.id]||'';$('summaryPrompt').value=state.prompt;
  $('originalDescription').textContent=v.title+'\n\n'+(v.description||'No description saved.');
  $('transcriptText').value='';setCopyAvailable(false);
  if(state.transcripts[v.id]) {
    $('transcriptText').value=state.transcripts[v.id];$('transcriptStatus').textContent='Your pasted transcript is saved on this device.';setCopyAvailable(true);return;
  }
  if(v.transcript.status!=='saved') {
    $('transcriptStatus').textContent=v.transcript.status==='no_english_captions'?'No English captions were available when checked. Use the transcript service below.':v.transcript.status==='fetch_failed'?'Transcript retrieval failed during collection; captions may still be available. Use the transcript service below.':'This transcript has not been collected yet. Use the transcript service below.';return;
  }
  $('transcriptStatus').textContent='Loading saved transcript…';
  try {
    const response=await fetch(v.transcript.path);if(!response.ok)throw Error('unavailable');
    const data=await response.json();if(data.video_id!==v.id||!data.text?.trim())throw Error('invalid');
    if(token!==transcriptRequest||state.page!=='study')return;
    $('transcriptText').value=data.text;$('transcriptStatus').textContent=`Saved transcript · ${data.source||v.transcript.source} · ${data.language||'English'}`;setCopyAvailable(true);
  } catch {
    if(token===transcriptRequest){$('transcriptStatus').textContent='Could not load the saved transcript. Use the link fallback below.';setCopyAvailable(false);}
  }
}
function updateStudyButtons() {
  const v=current();if(!v)return;
  $('studyFavorite').textContent=state.favorites[v.id]?'★ Saved':'☆ Save';$('studyFavorite').setAttribute('aria-pressed',String(!!state.favorites[v.id]));
  $('studyWatched').textContent=state.watched[v.id]?'✓ Watched (undo)':'Mark watched';
}
function setCopyAvailable(yes) {$('copyTranscript').disabled=!yes;$('copyPrompt').disabled=!yes;}
async function copyText(text) {
  try {await navigator.clipboard.writeText(text);toast('Copied.');return true;}
  catch {$('manualCopy').value=text;$('copyDialog').showModal();$('manualCopy').focus();$('manualCopy').select();return false;}
}
function transcriptCopy(withPrompt) {
  const v=current(), text=$('transcriptText').value.trim();if(!v||!text){toast('No transcript loaded.');return;}
  copyText((withPrompt?state.prompt+'\n\n':'')+v.title+'\n'+v.url+'\n\n'+text);
}
function fallback() {
  const v=current();if(!v)return;
  // Open synchronously within the tap so mobile popup blockers allow it.
  const tab=window.open('https://www.youtube-transcript.io/','_blank');if(tab)tab.opener=null;
  copyText(v.url).then(ok=>{if(ok)toast(tab?'Video link copied. Paste it in the transcript site.':'Link copied. Allow popups to open the transcript site.');});
}
function toast(message) {clearTimeout(toastTimer);$('toast').textContent=message;$('toast').classList.add('visible');toastTimer=setTimeout(()=>$('toast').classList.remove('visible'),4500);}
function changeFilter(key,value) {const p=prefs();p[key]=value;p.current=null;p.queue=[];p.scroll=0;limit=40;save();renderLibrary();}
function wire() {
  document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>showPage(b.dataset.page));
  $('backChannels').onclick=()=>showPage('channels');$('backBrowse').onclick=()=>showPage('library');
  $('filterButton').onclick=()=>{prefs().filterOpen=!prefs().filterOpen;save();renderLibrary();};
  $('search').oninput=e=>changeFilter('search',e.target.value);
  for(const key of ['series','topic','playlist','sort','status'])$(key).onchange=e=>{if(key==='playlist'&&e.target.value)prefs().sort='playlist';changeFilter(key,e.target.value);};
  document.querySelectorAll('[data-format]').forEach(b=>b.onclick=()=>changeFilter('format',b.dataset.format));
  $('clear').onclick=()=>{state.channels[state.channel]=defaultPrefs();limit=40;save();renderLibrary();};
  $('startQueue').onclick=startSelection;$('showMore').onclick=()=>{limit+=40;renderLibrary();};
  $('watch').onclick=()=>{const v=current();if(v){save();window.open(v.url,'_blank','noopener');}};
  $('previous').onclick=()=>move(-1);$('next').onclick=()=>move(1);$('doneNext').onclick=()=>move(1,true);
  $('studyWatched').onclick=()=>{const v=current();state.watched[v.id]=!state.watched[v.id];save();updateStudyButtons();};
  $('studyFavorite').onclick=()=>{const v=current();state.favorites[v.id]=!state.favorites[v.id];save();updateStudyButtons();};
  $('notes').oninput=()=>{const v=current();if(v){state.notes[v.id]=$('notes').value;save();}};
  $('copyTranscript').onclick=()=>transcriptCopy(false);$('copyPrompt').onclick=()=>transcriptCopy(true);$('transcriptFallback').onclick=fallback;
  $('saveTranscript').onclick=()=>{const v=current(),text=$('transcriptText').value.trim();if(!text){toast('Paste a transcript first.');return;}state.transcripts[v.id]=text;save();setCopyAvailable(true);$('transcriptStatus').textContent=storageOK?'Your transcript is saved on this device.':'Transcript kept in this page only; download a backup.';};
  $('savePrompt').onclick=()=>{state.prompt=$('summaryPrompt').value.trim()||SUMMARY;save();toast('Summary prompt saved.');};
  $('backupOpen').onclick=()=>$('backupDialog').showModal();$('closeBackup').onclick=()=>$('backupDialog').close();$('closeCopy').onclick=()=>$('copyDialog').close();
  $('exportBackup').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify({app:'radiology-video-library',state},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='radiology-video-library-backup.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000);};
  $('importBackup').onchange=async e=>{
    try{const file=e.target.files[0];if(!file)return;const data=JSON.parse(await file.text());const old=data.catalog==='neuroradish'&&data.version===1&&data.state&&typeof data.state==='object';if(!old&&(data.app!=='radiology-video-library'||data.state?.version!==2))throw Error('format');if(!confirm('Replace your local progress and notes with this backup?'))return;state=old?migrateOld(data.state):normalize(data.state);reconcile();save();$('backupDialog').close();showPage(state.page);toast('Backup restored.');}
    catch{toast('This is not a valid Radiology Video Library backup.');}finally{e.target.value='';}
  };
  window.addEventListener('pagehide',()=>{if(state.page==='library')prefs().scroll=window.scrollY;save();});
}
function reconcile() {
  if(!catalog.channels.some(c=>c.id===state.channel)){state.channel=null;state.page='channels';}
  for(const [id,p] of Object.entries(state.channels)) {
    p.queue=p.queue.filter(vid=>byId.get(vid)?.channel===id);
    if(!p.queue.includes(p.current))p.current=null;
    if(!['study','playlist','title','newest','oldest','shortest','longest'].includes(p.sort))p.sort='study';
    if(!['need','all','seen','favorites'].includes(p.status))p.status='need';
    if(!['all','Video','Short','Live archive'].includes(p.format))p.format='all';
  }
  if(state.page==='study'&&!current())state.page='library';
}
async function init() {
  try {
    const response=await fetch('catalog.json');if(!response.ok)throw Error('Catalog unavailable');catalog=await response.json();
    byId=new Map(catalog.videos.map(v=>[v.id,v]));state=read();reconcile();wire();showPage(state.page);
  } catch(error) {$('channelCards').innerHTML='<p class="error">The library could not load. Refresh when connected to the internet.</p>';console.error(error);}
}
init();
