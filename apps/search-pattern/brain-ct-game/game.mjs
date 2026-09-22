import {project,PLANES} from './geometry.mjs';
const finitePoint=(p,n=3)=>Array.isArray(p)&&p.length===n&&p.every(Number.isFinite);
const area=p=>Math.abs(p.reduce((sum,a,i)=>{const b=p[(i+1)%p.length];return sum+a[0]*b[1]-b[0]*a[1];},0))/2;
function segmentDistance(p,a,b){const dx=b[0]-a[0],dy=b[1]-a[1],len=dx*dx+dy*dy,t=len?Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/len)):0;return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);}
export function contains(region,patient,plane){
 if(plane!==region.plane)return false;
 const [x,y,n]=project(patient,plane);if(n<region.normal[0]-1e-6||n>region.normal[1]+1e-6)return false;
 let inside=false;const p=region.polygon;
 for(let i=0,j=p.length-1;i<p.length;j=i++){
  const a=p[i],b=p[j];if(segmentDistance([x,y],a,b)<=region.toleranceMm+1e-7)return true;
  if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])inside=!inside;
 }
 return inside;
}
const acceptsWindow=(t,w,l)=>t.windows.some(a=>w>=a.width[0]&&w<=a.width[1]&&l>=a.level[0]&&l<=a.level[1]);
export function validateCheckpoints(manifest,c){
 if(c.caseId!==manifest.id||c.caseVersion!==manifest.version||c.version!==manifest.checkpointVersion)throw Error('Case / checkpoint version mismatch');
 if(!Array.isArray(c.phases)||!c.phases.length)throw Error('Missing phases');const ids=new Set(),phaseIds=new Set();
 for(const phase of c.phases){
  if(!phase.id||phaseIds.has(phase.id)||!phase.targets?.length)throw Error('Invalid phase');phaseIds.add(phase.id);
  for(const t of phase.targets){
   if(!t.id||ids.has(t.id))throw Error('Duplicate target ID');ids.add(t.id);
   if(!t.windows?.length||t.windows.some(w=>[w.width,w.level].some(a=>!finitePoint(a,2)||a[0]>a[1])||w.width[0]<1))throw Error('Invalid target window');
   if(!t.regions?.length)throw Error('Missing target region');
   for(const r of t.regions){
    if(!PLANES.includes(r.plane)||!finitePoint(r.normal,2)||r.normal[0]>r.normal[1]||!Number.isFinite(r.toleranceMm)||r.toleranceMm<0)throw Error('Invalid region geometry');
    if(!Array.isArray(r.polygon)||r.polygon.length<3||!r.polygon.every(p=>finitePoint(p,2))||area(r.polygon)<1e-5)throw Error('Invalid polygon');
   }
   const p=t.representative;
   if(!p||!finitePoint(p.patient)||!t.regions.some(r=>contains(r,p.patient,p.plane))||!acceptsWindow(t,p.width,p.level))throw Error('Invalid representative point or window');
  }
 }
 return c;
}
export function createGame({phases,mode='practice',now=()=>performance.now()}){
 let status='idle',runMode=mode,eligible=mode==='timed',done=new Set(),index=0,total=0,started=0,misses=0;
 const elapsed=()=>total+(status==='running'?Math.max(0,now()-started):0);
 return {
  start(ready){if(!ready||status!=='idle')return false;started=now();status='running';return true;},
  click({patient,plane,width,level}){
   if(status!=='running'||!finitePoint(patient)||!PLANES.includes(plane)||!Number.isFinite(width)||!Number.isFinite(level))return {kind:'ignored'};
   const targets=phases[index].targets;
   const candidates=targets.filter(t=>!done.has(t.id)).flatMap(t=>t.regions.filter(r=>contains(r,patient,plane)).map(r=>({t,area:area(r.polygon)}))).sort((a,b)=>a.area-b.area||a.t.id.localeCompare(b.t.id));
   if(!candidates.length){
    if(phases.some(p=>p.targets.some(t=>done.has(t.id)&&t.regions.some(r=>contains(r,patient,plane)))))return {kind:'ignored'};
    misses++;return {kind:'miss'};
   }
   const t=candidates[0].t;if(!acceptsWindow(t,width,level))return {kind:'window',targetId:t.id};
   done.add(t.id);
   if(targets.every(t=>done.has(t.id))){if(index===phases.length-1){total=elapsed();status='complete';}else index++;}
   return {kind:'hit',targetId:t.id};
  },
  pause(){if(status!=='running')return;total=elapsed();status='paused';eligible=false;runMode='practice';},
  resume(){if(status!=='paused')return;started=now();status='running';},
  restart(newMode=runMode){runMode=newMode;eligible=newMode==='timed';done=new Set();index=0;total=0;misses=0;status='idle';},
  snapshot(){return {status,mode:runMode,eligible,phaseId:phases[index].id,completed:[...done],elapsedMs:elapsed(),misses};}
 };
}
