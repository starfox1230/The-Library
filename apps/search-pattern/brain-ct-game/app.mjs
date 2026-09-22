import {loadVolume} from './volume.mjs';
import {PLANES,AXES,project,unproject,clampFocus,planeBounds,createViewTransform} from './geometry.mjs';
import {paintViewport} from './renderer.mjs';
import {createGame,validateCheckpoints} from './game.mjs';
import {normalizeWheel,isGameShortcut,isClick} from './input.mjs';
import {recordKey,readBest,saveBest} from './records.mjs';

const $=id=>document.getElementById(id),preset={brain:[80,40],subdural:[200,75],bone:[2500,500]};
const canvases=Object.fromEntries(PLANES.map(p=>[p,$(p)])),transforms={},panels=Object.fromEntries(PLANES.map(p=>[p,document.querySelector(`[data-viewport="${p}"]`)]));
let brain,bone,checkpoints,game,ready=false,active='axial',focus=[0,0,0],width=80,level=40,selected=null,hint=false,frame=0,feedbackTimer,loadGeneration=0,gestures=new Map();
const views=Object.fromEntries(PLANES.map(p=>[p,{zoom:1,pan:[0,0],carry:0}]));
let storage;try{storage=window.localStorage;}catch{storage={getItem:()=>null,setItem:()=>{throw Error('Storage unavailable')}};}
const format=ms=>`${String(Math.floor(ms/60000)).padStart(2,'0')}:${String(Math.floor(ms/1000)%60).padStart(2,'0')}.${Math.floor(ms/100)%10}`;
const phase=()=>checkpoints.phases.find(p=>p.id===game.snapshot().phaseId);
const record=()=>recordKey({caseId:brain.manifest.id,caseVersion:brain.manifest.version,checkpointVersion:checkpoints.version,mode:'timed'});
const volume=()=>width>=1500?bone:brain;
function currentTarget(){const p=phase(),done=game.snapshot().completed;return p.targets.find(t=>t.id===selected&&!done.includes(t.id))||p.targets.find(t=>!done.includes(t.id));}
function flash(message,miss=false){clearTimeout(feedbackTimer);$('feedback').textContent=message;$('feedback').className='feedback show'+(miss?' miss':'');feedbackTimer=setTimeout(()=>$('feedback').className='feedback',1300);}
function requestDraw(){if(!frame)frame=requestAnimationFrame(draw);}
function draw(){
 frame=0;if(!ready)return;const start=performance.now(),v=volume(),snap=game.snapshot();
 for(const p of PLANES){
  if(panels[p].hidden)continue;
  const target=hint&&snap.mode==='practice'&&snap.status==='running'?currentTarget():null;
  const n=project(focus,p)[2],region=target?.regions.find(r=>r.plane===p&&n>=r.normal[0]&&n<=r.normal[1]);
  transforms[p]=paintViewport(canvases[p],v,{...views[p],focus,plane:p,width,level},{crosshairs:$('crosshairs').checked,region});
 }
 performance.measure('ct-render',{start,end:performance.now()});
 if(performance.getEntriesByName('ct-render').length>200)performance.clearMeasures('ct-render');
 updateImageControls();
}
function updateImageControls(){
 if(!ready)return;const m=brain.manifest,n=AXES[active][2],i=Math.round((focus[n]-m.originLPS[n])/m.spacing[n]);
 $('slice').max=m.dimensions[n]-1;$('slice').value=i;$('slice-position').textContent=`${i+1} / ${m.dimensions[n]}`;$('slice-label').textContent=active[0].toUpperCase()+active.slice(1);
 $('width').value=Math.round(width);$('level').value=Math.round(level);$('zoom').value=views[active].zoom;$('kernel').textContent=width>=1500?'Bone reconstruction':'Brain reconstruction';
 document.querySelectorAll('[data-preset]').forEach(b=>b.setAttribute('aria-pressed',String(preset[b.dataset.preset][0]===width&&preset[b.dataset.preset][1]===level)));
}
function setPlane(p){
 active=p;const three=$('three').checked&&innerWidth>700;
 $('viewports').classList.toggle('three',three);
 for(const name of PLANES){panels[name].hidden=!three&&name!==p;panels[name].classList.toggle('active',name===p);}
 document.querySelectorAll('[data-plane]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.plane===p)));
 requestDraw();
}
function scroll(steps){if(!ready)return;const m=brain.manifest,n=AXES[active][2];focus=[...focus];focus[n]+=steps*m.spacing[n]*(active==='axial'?-1:1);focus=clampFocus(focus,m);requestDraw();}
function setWindow(w,l){if(!Number.isFinite(w)||!Number.isFinite(l))return; width=Math.max(1,Math.min(8000,w));level=Math.max(-1500,Math.min(3000,l));requestDraw();}
function sync(){
 if(!ready)return;const s=game.snapshot(),p=phase(),phaseIndex=checkpoints.phases.indexOf(p),done=new Set(s.completed),target=currentTarget();
 selected=target?.id||null;$('timer').textContent=format(s.elapsedMs);$('mode').value=s.mode;$('mode').disabled=s.status==='running'||s.status==='paused';
 $('start').textContent=s.status==='running'?'Pause':s.status==='paused'?'Resume':'Start';$('start').disabled=s.status==='complete';$('restart').disabled=false;
 $('count').textContent=`${done.size} / ${checkpoints.phases.reduce((sum,p)=>sum+p.targets.length,0)}`;
 $('phase-number').textContent=`${String(phaseIndex+1).padStart(2,'0')} / 10`;$('phase-label').textContent=s.status==='complete'?'Search complete':p.label;
 $('instruction').textContent=s.status==='idle'?'Press Start when ready. '+p.instruction:s.status==='paused'?'Paused · this attempt is now practice.':s.status==='complete'?'Every checkpoint reviewed. Restart to try again.':p.instruction;
 $('phase-completion').textContent=`${s.status==='complete'?10:phaseIndex} of 10`;
 const practice=s.mode==='practice',canHint=practice&&s.status==='running';
 $('hint-controls').hidden=!practice;$('hint').disabled=!canHint;$('locate').disabled=!canHint;
 $('hint').textContent=hint?'Hide hint':'Show hint';$('hint').setAttribute('aria-pressed',String(hint));
 $('hint-note').textContent=practice?(canHint?(target?'Selected: '+target.label:'All checkpoints complete.'):'Start practice to use hints.'):'Timed · complete every checkpoint without target hints.';
 $('phase-list').replaceChildren();
 for(const [i,ph] of checkpoints.phases.entries()){
  const all=ph.targets.every(t=>done.has(t.id)),current=ph.id===p.id;
  const section=document.createElement('section');section.className='phase'+(current?' current':'')+(all?' complete':'');
  const title=document.createElement('div');title.className='phase-title';const number=document.createElement('span');number.className='phase-index';number.textContent=all?'✓':String(i+1).padStart(2,'0');title.append(number,document.createTextNode(ph.label));section.append(title);
  if(current&&!all){const list=document.createElement('div');list.className='targets';
   for(const t of ph.targets){const button=document.createElement('button');button.className='target'+(done.has(t.id)?' done':'')+(t.id===selected&&practice?' selected':'');button.disabled=!practice||done.has(t.id);button.setAttribute('aria-label',t.label+(done.has(t.id)?', completed':''));const dot=document.createElement('span');dot.className='dot';dot.textContent=done.has(t.id)?'✓':'○';button.append(dot,document.createTextNode(t.label));button.onclick=()=>{selected=t.id;sync();requestDraw();};list.append(button);}section.append(list);
  }$('phase-list').append(section);
 }
 const best=readBest(storage,record());$('best').textContent=best===null?'—':format(best);
 $('result').hidden=s.status!=='complete';if(s.status==='complete'){$('result').replaceChildren();const strong=document.createElement('strong');strong.textContent=format(s.elapsedMs);$('result').append(strong,document.createTextNode(`${s.mode==='timed'?'Timed':'Practice'} · ${s.misses} missed clicks`));}
 requestDraw();
}
async function load(){
 const generation=++loadGeneration;ready=false;brain=bone=game=null;$('start').disabled=true;$('restart').disabled=true;$('hint').disabled=true;$('locate').disabled=true;$('loading').hidden=false;$('retry').hidden=true;
 $('loading').querySelector('h1').textContent='Preparing your case';$('load-message').textContent='Loading brain and bone images';$('load-progress').value=0;
 try{
  const base=new URL('cases/normal-head/',location.href);const progress=[0,0];
  const onProgress=i=>v=>{if(generation===loadGeneration){progress[i]=v;$('load-progress').value=(progress[0]+progress[1])/2;}};
  const [b,bn,res]=await Promise.all([loadVolume(new URL('manifest.json',base),{onProgress:onProgress(0)}),loadVolume(new URL('bone/manifest.json',base),{onProgress:onProgress(1)}),fetch(new URL('checkpoints.json',base),{cache:'no-store'})]);
  if(!res.ok)throw Error(`Checkpoints: HTTP ${res.status}`);const c=validateCheckpoints(b.manifest,await res.json());
  for(const key of ['dimensions','spacing','originLPS'])if(JSON.stringify(b.manifest[key])!==JSON.stringify(bn.manifest[key]))throw Error('Brain and bone volumes do not align');
  if(generation!==loadGeneration)return;
  brain=b;bone=bn;checkpoints=c;game=createGame({phases:c.phases,mode:$('mode').value});ready=true;
  const m=b.manifest;focus=m.originLPS.map((o,i)=>o+m.spacing[i]*(i===2?99:190));focus=clampFocus(focus,m);
  $('loading').hidden=true;$('start').disabled=false;setPlane(active);sync();
 }catch(e){if(generation!==loadGeneration)return;$('loading').querySelector('h1').textContent='Case could not load';$('load-message').textContent=e.message;$('retry').hidden=false;}
}
$('retry').onclick=load;
$('start').onclick=()=>{if(!ready)return;const s=game.snapshot();if(s.status==='running'){game.pause();hint=false;gestures.clear();flash('Paused · attempt changed to practice',true);}else if(s.status==='paused')game.resume();else game.start(true);sync();};
$('restart').onclick=()=>{if(!ready)return;game.restart($('mode').value);hint=false;selected=null;gestures.clear();sync();};
$('mode').onchange=()=>{if(ready){game.restart($('mode').value);hint=false;selected=null;sync();}};
$('hint').onclick=()=>{if(!ready||game.snapshot().mode!=='practice')return;hint=!hint;sync();};
$('locate').onclick=()=>{if(!ready||game.snapshot().mode!=='practice'||game.snapshot().status!=='running')return;const t=currentTarget();if(!t)return;const r=t.representative;focus=[...r.patient];setPlane(r.plane);setWindow(r.width,r.level);views[active].zoom=1;views[active].pan=[0,0];hint=true;sync();};
$('checklist-toggle').onclick=()=>{const hidden=$('workspace').classList.toggle('checklist-hidden');$('checklist-toggle').setAttribute('aria-pressed',String(!hidden));requestDraw();};
document.querySelectorAll('[data-plane]').forEach(b=>b.onclick=()=>setPlane(b.dataset.plane));
document.querySelectorAll('[data-preset]').forEach(b=>b.onclick=()=>setWindow(...preset[b.dataset.preset]));
$('width').onchange=()=>setWindow(Number($('width').value),level);$('level').onchange=()=>setWindow(width,Number($('level').value));
$('slice').oninput=()=>{if(!ready)return;const m=brain.manifest,n=AXES[active][2];focus[n]=m.originLPS[n]+Number($('slice').value)*m.spacing[n];requestDraw();};
$('zoom').oninput=()=>{views[active].zoom=Number($('zoom').value);requestDraw();};
$('reset-view').onclick=()=>{for(const p of PLANES){views[p].zoom=1;views[p].pan=[0,0];}setWindow(80,40);};
$('three').onchange=()=>setPlane(active);$('crosshairs').onchange=requestDraw;
for(const planeName of PLANES){
 const canvas=canvases[planeName];
 canvas.oncontextmenu=e=>e.preventDefault();
 canvas.addEventListener('wheel',e=>{if(!ready)return;e.preventDefault();setPlane(planeName);const r=normalizeWheel(e,views[planeName].carry);views[planeName].carry=r.carry;scroll(r.steps);},{passive:false});
 canvas.onpointerdown=e=>{if(!ready)return;setPlane(planeName);canvas.focus({preventScroll:true});canvas.setPointerCapture(e.pointerId);gestures.set(e.pointerId,{plane:planeName,start:[e.clientX,e.clientY],last:[e.clientX,e.clientY],button:e.button,width,level,pan:[...views[planeName].pan],moved:false});};
 canvas.onpointermove=e=>{const g=gestures.get(e.pointerId);if(!g)return;const dx=e.clientX-g.start[0],dy=e.clientY-g.start[1];if(Math.hypot(dx,dy)>4)g.moved=true;g.last=[e.clientX,e.clientY];if(g.button===2)setWindow(g.width+dx*2,g.level-dy);if(g.button===1){views[g.plane].pan=[g.pan[0]+dx,g.pan[1]+dy];requestDraw();}};
 canvas.onpointercancel=e=>gestures.delete(e.pointerId);
 canvas.onlostpointercapture=e=>gestures.delete(e.pointerId);
 canvas.onpointerup=e=>{
  const g=gestures.get(e.pointerId);gestures.delete(e.pointerId);if(!g||g.button!==0||g.moved||!isClick(g.start,[e.clientX,e.clientY]))return;
  const rect=canvas.getBoundingClientRect(),screen=[e.clientX-rect.left,e.clientY-rect.top];
  const transform=createViewTransform({width:rect.width,height:rect.height,bounds:planeBounds(volume().manifest,planeName),...views[planeName]});
  const [u,v]=transform.toPlane(screen),n=project(focus,planeName)[2],patient=unproject([u,v,n],planeName);
  if(e.shiftKey){focus=clampFocus(patient,brain.manifest);requestDraw();return;}
  const result=game.click({patient,plane:planeName,width,level});
  if(result.kind==='hit'){focus=clampFocus(patient,brain.manifest);const t=checkpoints.phases.flatMap(p=>p.targets).find(t=>t.id===result.targetId);flash('✓ '+t.label);if(game.snapshot().status==='complete'){hint=false;saveBest(storage,record(),game.snapshot());}}
  else if(result.kind==='window')flash('Right region · adjust your window',true);
  else if(result.kind==='miss')flash('No checkpoint here in this phase',true);
  sync();
 };
}
document.addEventListener('keydown',e=>{if(!ready||!isGameShortcut(e))return;const p={a:'axial',s:'sagittal',c:'coronal'}[e.key.toLowerCase()];if(p){e.preventDefault();setPlane(p);}else if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();scroll(e.key==='ArrowDown'?1:-1);}});
document.addEventListener('visibilitychange',()=>{if(document.hidden&&ready){gestures.clear();game.pause();hint=false;sync();}});
new ResizeObserver(requestDraw).observe($('viewports'));window.addEventListener('resize',()=>setPlane(active));
setInterval(()=>{if(ready)$('timer').textContent=format(game.snapshot().elapsedMs);},100);
load();

