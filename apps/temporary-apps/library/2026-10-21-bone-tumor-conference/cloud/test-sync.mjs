import { strict as assert } from 'node:assert';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { handleProgress } from './progress-api.mjs';

const sqlite=new DatabaseSync(':memory:');
sqlite.exec(readFileSync(new URL('./0000_study_progress.sql',import.meta.url),'utf8'));
const db={prepare(sql){return {bind(...args){return {all:async()=>({results:sqlite.prepare(sql).all(...args)}),run:()=>sqlite.prepare(sql).run(...args)};}};},async batch(statements){sqlite.exec('BEGIN');try{for(const statement of statements)statement.run();sqlite.exec('COMMIT');}catch(error){sqlite.exec('ROLLBACK');throw error;}}};
const origin='https://study.example';
const req=(user,method='GET',records=[],extra={})=>new Request(origin+'/api/progress',{method,headers:{...(user?{'oai-authenticated-user-id':user}:{}),...(method==='POST'?{'origin':origin,'Content-Type':'application/json'}:{}),...extra},...(method==='POST'?{body:JSON.stringify({records})}:{})});
const post=async(user,records)=>{const response=await handleProgress(req(user,'POST',records),db);assert.equal(response.status,200);return response.json();};
const row=(field,value,updated=1)=>({key:'g:case-approach',field,value,updated});
assert.equal((await handleProgress(req(null),db)).status,401);
assert.equal((await handleProgress(req('a','POST',[],{origin:'https://other.example'}),db)).status,403);
assert.equal((await handleProgress(req('a','POST',[row('note',false)]),db)).status,400);
assert.equal((await handleProgress(req('a','POST',[row('key',true,Date.now()+900000)]),db)).status,400);
await post('a',[row('key',true,20),row('note','Keep the cortex in mind',30)]);
await post('a',[row('key',false,10)]);
let saved=await (await handleProgress(req('a'),db)).json();
assert.equal(saved.records.find(r=>r.field==='key').value,true,'Stale writes must not replace newer progress');
assert.equal((await (await handleProgress(req('b'),db)).json()).records.length,0,'Users must be isolated');
await post('a',[row('key',false,40),row('note','',50)]);
saved=await (await handleProgress(req('a'),db)).json();
assert.equal(saved.records.find(r=>r.field==='key').value,false,'Unflagging must persist');
assert.equal(saved.records.find(r=>r.field==='note').value,'','Clearing notes must persist');

const sandbox={module:{exports:{}},AbortSignal,TextEncoder,navigator:{onLine:true},setTimeout,clearTimeout,console};
vm.runInNewContext(readFileSync(new URL('../sync.js',import.meta.url),'utf8'),sandbox);
const {create}=sandbox.module.exports;
let offline=false,delayPost=null;
function device(initial=[],persisted=new Map()){
  const model=new Map(initial.map(r=>[JSON.stringify([r.key,r.field]),r]));let status;
  const storage={getItem:key=>persisted.get(key)||null,setItem:(key,value)=>persisted.set(key,value)};
  const client=create({automatic:false,storage,now:Date.now,snapshot:()=>[...model.values()],apply:records=>{for(const r of records)model.set(JSON.stringify([r.key,r.field]),r);},status:value=>status=value,fetcher:async(_url,options)=>{
    if(offline)throw Error('Offline');
    if(options.method==='POST'&&delayPost){const wait=delayPost;delayPost=null;await wait;}
    return handleProgress(req('study-user',options.method,options.body?JSON.parse(options.body).records:[]),db);
  }});
  return {client,model,persisted,status:()=>status,set(field,value){model.set(JSON.stringify(['g:case-approach',field]),row(field,value,Date.now()));client.capture(false);},value:field=>model.get(JSON.stringify(['g:case-approach',field]))?.value};
}
const phone=device([row('key',true,10),row('note','Legacy note',10)]);
await phone.client.sync();assert.equal(phone.status(),'synced');
const computer=device();await computer.client.sync();assert.equal(computer.value('note'),'Legacy note','Fresh device must restore cloud notes');
phone.set('note','New note from phone');computer.set('review',true);
await phone.client.sync();await computer.client.sync();await phone.client.sync();
assert.equal(computer.value('note'),'New note from phone');assert.equal(phone.value('review'),true,'Separate fields must merge');
computer.set('key',false);await computer.client.sync();await phone.client.sync();assert.equal(phone.value('key'),false);
offline=true;phone.set('note','Edited offline');await phone.client.sync();assert.equal(phone.status(),'error');
assert.ok(phone.client.inspect().pending.length);
const restarted=device([...phone.model.values()],phone.persisted);offline=false;await restarted.client.sync();await computer.client.sync();assert.equal(computer.value('note'),'Edited offline','Offline queue must survive a browser restart');
const stale=device([row('note','Old browser backup',1)]);await stale.client.sync();assert.equal(stale.value('note'),'Edited offline','Old device migration must not overwrite newer cloud progress');
let release;delayPost=new Promise(resolve=>release=resolve);phone.set('note','First edit');const sending=phone.client.sync();
// Let GET finish and the POST pause, then edit while that earlier version is in flight.
await new Promise(resolve=>setTimeout(resolve,5));phone.set('note','Edited while syncing');release();await sending;await computer.client.sync();assert.equal(computer.value('note'),'Edited while syncing');
assert.equal(phone.client.inspect().pending.length,0);
sqlite.close();
console.log('PASS: account isolation, origin checks, validation, stale writes, cleared flags/notes, device merge, offline restart, legacy migration, and edits during sync.');
