import test from 'node:test';
import assert from 'node:assert/strict';
import {gzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {project,unproject,createViewTransform,planeBounds} from '../geometry.mjs';
import {windowHU,sampleHU,sampleSlice} from '../renderer.mjs';
import {loadVolume} from '../volume.mjs';

const manifest={id:'test',version:'1',checkpointVersion:'1',dimensions:[2,3,4],spacing:[1,2,3],originLPS:[10,20,30],encoding:'gzip-i16le-hu',volumeUrl:'v.gz'};
const values=Int16Array.from({length:24},(_,i)=>i);
const volume={manifest,values};
test('distinct patient coordinates round trip through each plane',()=>{
 for(const p of ['axial','coronal','sagittal'])assert.deepEqual(unproject(project([11,23,37],p),p),[11,23,37]);
 assert.deepEqual(project([11,23,37],'coronal'),[11,-37,23]);
 assert.deepEqual(project([11,23,37],'sagittal'),[23,-37,11]);
});
test('physical display mapping inverts zoom pan and resize',()=>{
 for(const [w,h] of [[900,700],[390,520],[1800,1400]]){
  const t=createViewTransform({width:w,height:h,bounds:[-90,-120,90,120],zoom:1.7,pan:[31,-17]});
  const p=t.toPlane(t.toScreen([13,-29]));assert.ok(Math.hypot(p[0]-13,p[1]+29)<1e-8);
 }
});
test('sampled HU follows X-fastest order and physical spacing',()=>{
 assert.equal(sampleHU(volume,[11,24,39]),23);
 assert.equal(sampleHU(volume,[10.5,21,31.5]),4.5);
 assert.equal(sampleHU(volume,[0,0,0]),-1000);
});
test('axial and coronal slices put patient left on screen right',()=>{
 const a=sampleSlice(volume,'axial',30);assert.deepEqual(Array.from(a.hu),[0,1,2,3,4,5]);
 const c=sampleSlice(volume,'coronal',20);assert.equal(c.hu[0],18);assert.equal(c.hu[1],19);assert.equal(c.hu.at(-1),1);
 assert.deepEqual(planeBounds(manifest,'axial'),[9.5,19,11.5,25]);
});
test('windowing clips HU with exact width 1 threshold',()=>{
 assert.equal(windowHU(-1000,80,40),0);assert.equal(windowHU(1000,80,40),255);
 assert.equal(windowHU(40,80,40),129);assert.equal(windowHU(39.5,1,40),0);assert.equal(windowHU(40,1,40),255);
 assert.throws(()=>windowHU(0,0,40));
});
function fetcher(changes={},raw=new Uint8Array(values.buffer)){
 const m={...manifest,sha256:createHash('sha256').update(raw).digest('hex'),...changes};
 return async u=>String(u).endsWith('manifest.json')?Response.json(m):new Response(gzipSync(raw));
}
test('loader checks byte length, checksum, encoding, and metadata',async()=>{
 const v=await loadVolume('https://test.invalid/manifest.json',{fetcher:fetcher()});assert.deepEqual(v.values,values);
 await assert.rejects(loadVolume('https://test.invalid/manifest.json',{fetcher:fetcher({sha256:'0'.repeat(64)})}),/checksum/i);
 await assert.rejects(loadVolume('https://test.invalid/manifest.json',{fetcher:fetcher({},new Uint8Array(4))}),/length|size/i);
 await assert.rejects(loadVolume('https://test.invalid/manifest.json',{fetcher:fetcher({spacing:[0,2,3]})}),/spacing/i);
 await assert.rejects(loadVolume('https://test.invalid/manifest.json',{fetcher:fetcher({encoding:'jpeg'})}),/encoding/i);
 await assert.rejects(loadVolume('https://test.invalid/manifest.json',{fetcher:async()=>new Response('',{status:404})}),/404/);
});
