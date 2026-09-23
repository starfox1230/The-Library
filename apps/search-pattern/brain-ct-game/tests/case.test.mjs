import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {validateCheckpoints,createGame,contains} from '../game.mjs';
import {project,unproject,planeBounds,sliceNormal} from '../geometry.mjs';
const m=JSON.parse(await readFile(new URL('../cases/normal-head/manifest.json',import.meta.url)));
const c=JSON.parse(await readFile(new URL('../cases/normal-head/checkpoints.json',import.meta.url)));
test('fractional recenter scores the slice actually rendered',()=>{
 const t=c.phases[0].targets[0],r=t.representative;
 const focus=[...r.patient];focus[2]+=.1;
 assert.equal(contains(t.regions[0],focus,'axial'),false);
 const p=[...focus];p[2]=sliceNormal(focus,m,'axial');
 assert.ok(contains(t.regions[0],p,'axial'));
});
test('shipped case completes all 70 targets in practice and timed modes',()=>{
 validateCheckpoints(m,c);
 for(const mode of ['practice','timed']){
  const g=createGame({phases:c.phases,mode,now:()=>1000});g.start(true);
  for(const ph of c.phases)for(const t of ph.targets){
   assert.equal(g.snapshot().phaseId,ph.id);
   assert.deepEqual(g.click(t.representative),{kind:'hit',targetId:t.id},t.id);
  }
  assert.equal(g.snapshot().status,'complete');assert.equal(g.snapshot().completed.length,70);
  assert.equal(g.snapshot().eligible,mode==='timed');
 }
});
test('all shipped representative points are inside the real volume and intervals are reachable',()=>{
 for(const t of c.phases.flatMap(p=>p.targets)){
  const r=t.representative;
  r.patient.forEach((x,i)=>assert.ok(x>=m.originLPS[i]&&x<=m.originLPS[i]+m.spacing[i]*(m.dimensions[i]-1),t.id));
  for(const region of t.regions){
   const [u,v]=project(r.patient,region.plane);
   for(const n of region.normal)assert.ok(contains(region,unproject([u,v,n],region.plane),region.plane));
   const b=planeBounds(m,region.plane);
   for(const [x,y] of region.polygon)assert.ok(x>=b[0]&&x<=b[2]&&y>=b[1]&&y<=b[3],t.id+' polygon outside image');
  }
 }
});
