import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const context={window:{}};
vm.runInNewContext(fs.readFileSync(path.join(root,'bank.js'),'utf8'),context);
const bank=context.window.LECTURE_BANK;
const manifest=JSON.parse(fs.readFileSync(path.join(root,'figure-manifest.json'),'utf8'));
assert.equal(bank.figures.length,42);assert.equal(manifest.length,42);
assert.equal(new Set(bank.figures.map(f=>f.id)).size,42);
assert.equal(new Set(manifest.map(f=>f.id)).size,42);
let total=0,clinical=0;
for(const f of bank.figures){
 const media=manifest.find(m=>m.id===f.id);
 assert(media,`Missing mapping: ${f.id}`);assert(fs.existsSync(path.join(root,media.file)));
 assert(media.width>150&&media.height>150,`Image too small: ${f.id}`);
 assert(f.look&&f.meaning&&f.pitfall,`Incomplete explanation: ${f.id}`);
 assert(media.page>=1&&media.page<=bank.papers[media.paper].pages);
 assert(!f.diagram||f.questions.length===0,'Do not quiz on answer-bearing diagrams');
 if(!f.diagram){clinical++;assert(f.questions.length>=4,`Missing coverage: ${f.id}`);}
 const stems=new Set();
 for(const q of f.questions){assert.equal(q.length,2);assert(q[0].length>15&&q[1].length>3);assert(!stems.has(q[0]),`Duplicate stem: ${f.id}`);stems.add(q[0]);total++;}
}
assert.equal(clinical,39);assert.equal(total,162);
for(const [id,p] of Object.entries(bank.papers)){
 assert(fs.existsSync(path.join(root,p.file)));
 for(let n=1;n<=p.pages;n++)assert(fs.existsSync(path.join(root,'reader',`${id}-${String(n).padStart(2,'0')}.webp`)));
}
for(const l of bank.lessons)for(const id of l.figures)assert(manifest.some(f=>f.id===id));
for(const c of bank.comparisons)for(const id of [c.left,c.right])assert(manifest.some(f=>f.id===id));
const lessonCoverage=new Set(bank.lessons.flatMap(l=>l.figures));
assert.equal(lessonCoverage.size,42,'Guided lessons must include all figures');
new vm.Script(fs.readFileSync(path.join(root,'app.js'),'utf8'));
// Corrupt imports must not overwrite valid progress or attach ratings to a
// different bank. Also exercise a completed one-question round and JSON transfer.
const sandbox=vm.createContext({window:{LECTURE_BANK:bank,addEventListener(){}},document:{querySelector(){return {addEventListener(){}};},addEventListener(){}},setTimeout,clearTimeout,console});
vm.runInContext(fs.readFileSync(path.join(root,'app.js'),'utf8').replace(/\ninit\(\);\s*$/,''),sandbox);
const first='ct-1-q1';
const good={version:1,ratings:{[first]:'known'},session:{ids:[first],index:1,revealed:false,results:{[first]:'known'}}};
sandbox.input=JSON.stringify(good);
assert.equal(vm.runInContext('JSON.stringify(validState(JSON.parse(input)))',sandbox),JSON.stringify(good));
for(const bad of [{...good,version:2},{...good,ratings:{'unknown-question':'known'}},{...good,ratings:{[first]:'wrong-rating'}},{...good,session:{...good.session,ids:[first,first]}},{...good,session:{...good.session,index:0}},{...good,session:{...good.session,index:2}}]){
 sandbox.input=JSON.stringify(bad);
 assert.throws(()=>vm.runInContext('validState(JSON.parse(input))',sandbox));
}
const shuffled=JSON.parse(vm.runInContext('JSON.stringify(shuffle(questions.map(q=>q.id)))',sandbox));
assert.equal(shuffled.length,162);assert.equal(new Set(shuffled).size,162);
const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
for(const match of html.matchAll(/<(?:script|link)[^>]+(?:src|href)="([^"]+)"/g))if(!match[1].startsWith('http'))assert(fs.existsSync(path.join(root,match[1])));
console.log(`OK: ${clinical} clinical figures + 3 diagrams, ${total} source-linked questions, all 42 figures in lessons, 29 PDF pages, and valid JavaScript.`);
console.log('OK: progress JSON round trip, six corrupt-import cases, completed-round state, and shuffle without replacement.');
