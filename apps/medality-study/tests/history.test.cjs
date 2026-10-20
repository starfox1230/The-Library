const {test}=require('node:test');
const assert=require('node:assert/strict');
const {JSDOM}=require('jsdom');
const {readFileSync}=require('node:fs');
const {resolve}=require('node:path');
const root=resolve(__dirname,'..'),read=p=>readFileSync(resolve(root,p),'utf8');
const url='https://medality.com/course/demo/unit/first/';
const rows='<div><div data-item="0"><p>0:01</p><p>Synthetic transcript.</p></div></div>';
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup(html='<h1>First lesson</h1>'+rows,settings={}){
 const dom=new JSDOM(html,{url,runScripts:'outside-only'}),w=dom.window,stored={...settings},changes=[];
 const original=w.MutationObserver,observers=[];
 w.MutationObserver=class extends original{constructor(fn){super(fn);observers.push(this);}};
 w.chrome={storage:{local:{get:async query=>query===null?{...stored}:Array.isArray(query)?Object.fromEntries(query.filter(k=>k in stored).map(k=>[k,stored[k]])):{...query,...stored},set:async obj=>{const delta=Object.fromEntries(Object.entries(obj).map(([k,v])=>[k,{oldValue:stored[k],newValue:v}]));Object.assign(stored,obj);changes.forEach(fn=>fn(delta,'local'));}},onChanged:{addListener:fn=>changes.push(fn)}},runtime:{getURL:p=>'chrome-extension://synthetic/'+p,onMessage:{addListener(){}},sendMessage:async()=>({})}};
 return {w,stored,close(){observers.forEach(o=>o.disconnect());w.close();}};
}
function captureScripts(e){e.w.eval(read('extension/transcript-core.js'));e.w.eval(read('extension/transcript.js'));}
function tracker(e){
 const players=[];
 e.w.Vimeo={Player:class{constructor(element){this.handlers={};this.element=element;players.push(this);}on(event,fn){this.handlers[event]=fn;}off(event){delete this.handlers[event];}emit(event,data){this.handlers[event]?.(data);}}};
 e.w.eval(read('extension/watch-tracker.js'));return players;
}
test('90% event saves a lecture and transcript once, preserving original watch time on replay',async()=>{
 const e=setup('<h1>First lesson</h1><iframe src="https://player.vimeo.com/video/123"></iframe>'+rows);captureScripts(e);const players=tracker(e);await tick();
 players[0].emit('timeupdate',{seconds:89.9,duration:100});await tick();assert.equal(Object.keys(e.stored).length,0);
 players[0].emit('timeupdate',{seconds:90,duration:100});await tick();
 assert.equal(e.stored['transcript:'+url].text,'Synthetic transcript.');assert.equal(e.stored['watch:'+url].transcriptStatus,'saved');
 const at=e.stored['watch:'+url].watchedAt;
 players[0].emit('timeupdate',{seconds:99,duration:100});await tick();assert.equal(e.stored['watch:'+url].watchedAt,at);
 await e.w.MedalityAutoCapture(url,.95);assert.equal(e.stored['watch:'+url].watchedAt,at);e.close();
});
test('disabled tracking, unknown durations and stale events after navigation do not capture',async()=>{
 const e=setup('<h1>First</h1><iframe src="https://player.vimeo.com/video/123"></iframe>',{autoCapture:false});captureScripts(e);const players=tracker(e);await tick();
 players[0].emit('timeupdate',{seconds:95,duration:100});await tick();assert.equal(Object.keys(e.stored).length,1);
 await e.w.chrome.storage.local.set({autoCapture:true});
 players[0].emit('timeupdate',{seconds:95,duration:0});await tick();assert.equal(Object.keys(e.stored).length,1);
 e.w.history.pushState({},'',url.replace('first','next'));players[0].emit('timeupdate',{seconds:99,duration:100});await tick();assert.equal(Object.keys(e.stored).length,1);
 players[0].emit('loaded',{});players[0].emit('timeupdate',{seconds:90,duration:100});await tick();assert.ok(e.stored['watch:'+url.replace('first','next')]);e.close();
});
test('native playback threshold captures without calling playback or completion controls',async()=>{
 const e=setup('<h1>First</h1><video></video>'+rows);captureScripts(e);tracker(e);await tick();
 const video=e.w.document.querySelector('video');let calls=0;video.play=()=>{calls++;};video.pause=()=>{calls++;};
 Object.defineProperty(video,'duration',{value:100});Object.defineProperty(video,'currentTime',{value:90});
 video.dispatchEvent(new e.w.Event('timeupdate'));await tick();assert.ok(e.stored['watch:'+url]);assert.equal(calls,0);e.close();
});
test('missing transcript still records watched title, and manual save can repair it',async()=>{
 const e=setup('<h1>First lesson</h1>');captureScripts(e);await e.w.MedalityAutoCapture(url,.9);
 assert.equal(e.stored['watch:'+url].title,'First lesson');assert.equal(e.stored['watch:'+url].transcriptStatus,'unavailable');assert.equal(e.stored['transcript:'+url],undefined);
 const div=e.w.document.createElement('div');div.innerHTML=rows;e.w.document.body.append(div);
 await e.w.MedalityAutoCapture(url,.95);assert.equal(e.stored['watch:'+url].transcriptStatus,'saved');e.close();
});
test('hidden transcript is captured without opening the panel',async()=>{
 const e=setup('<h1>First</h1><button>Transcript</button><div hidden>'+rows+'</div>');let clicks=0;e.w.document.querySelector('button').addEventListener('click',()=>clicks++);captureScripts(e);
 await e.w.MedalityAutoCapture(url,.9);assert.equal(clicks,0);assert.equal(e.stored['transcript:'+url].text,'Synthetic transcript.');e.close();
});
test('capture opens and restores Cases, and never assigns another lecture transcript to old title',async()=>{
 const e=setup('<h1>First</h1><button id="cases" aria-selected="true">Cases (1)</button><button id="transcript">Transcript</button><section></section>');let restored=0;
 e.w.document.querySelector('#cases').addEventListener('click',()=>restored++);
 e.w.document.querySelector('#transcript').addEventListener('click',()=>{e.w.document.querySelector('section').innerHTML=rows;});captureScripts(e);
 await e.w.MedalityAutoCapture(url,.9);assert.equal(restored,1);assert.equal(e.stored['watch:'+url].transcriptStatus,'saved');e.close();
 const f=setup('<h1>First</h1><button>Transcript</button>');captureScripts(f);
 f.w.document.querySelector('button').addEventListener('click',()=>{f.w.history.pushState({},'',url.replace('first','next'));const div=f.w.document.createElement('div');div.innerHTML=rows;f.w.document.body.append(div);});
 await f.w.MedalityAutoCapture(url,.9);assert.equal(f.stored['transcript:'+url],undefined);assert.equal(f.stored['watch:'+url].transcriptStatus,'unavailable');f.close();
});
test('history shows newest first and copies selected transcripts earliest first, with clear missing count',()=>{
 const e=setup();e.w.eval(read('extension/history-core.js'));const H=e.w.MedalityHistory;
 const first={url,title:'First',text:'First text',watchedAt:'2026-10-19T12:00:00Z'},second={url:url.replace('first','second'),title:'Second',text:'Second text',watchedAt:'2026-10-19T13:00:00Z'},missing={url:url.replace('first','missing'),title:'Missing',watchedAt:'2026-10-19T14:00:00Z'};
 const entries=H.entries({['watch:'+first.url]:first,['transcript:'+first.url]:first,['watch:'+second.url]:second,['watch:'+missing.url]:missing,enabled:true});
 assert.equal(entries.length,3);assert.equal(entries[0].title,'Missing');
 const packet=H.packet(entries);assert.equal(packet.missing,1);assert.ok(packet.text.indexOf('First text')<packet.text.indexOf('Second text'));e.close();
});
test('history page selects one/all/none, previews safely, copies and updates live',async()=>{
 const e=setup(read('extension/history.html'));const first={url,title:'First <img src=x onerror=alert(1)>',text:'One',watchedAt:'2026-10-19T12:00:00Z'};
 e.stored['transcript:'+url]=first;e.stored['watch:'+url]=first;
 const second={url:url.replace('first','second'),title:'Second',text:'Two',watchedAt:'2026-10-19T13:00:00Z'};
 e.stored['transcript:'+second.url]=second;e.stored['watch:'+second.url]=second;
 const copies=[];Object.defineProperty(e.w.navigator,'clipboard',{value:{writeText:async text=>copies.push(text)}});
 e.w.eval(read('extension/history-core.js'));e.w.eval(read('extension/history.js'));await tick();
 const $=id=>e.w.document.getElementById(id);assert.equal($('lectures').querySelectorAll('article').length,2);assert.equal($('lectures').querySelectorAll('img').length,0);
 $('latest').click();assert.match($('selected-count').textContent,/2 selected/);$('copy').click();await tick();assert.ok(copies[0].indexOf('One')<copies[0].indexOf('Two'));
 $('none').click();assert.equal($('copy').disabled,true);const checkbox=$('lectures').querySelector('input');checkbox.click();assert.match($('selected-count').textContent,/1 selected/);
 await e.w.chrome.storage.local.set({['watch:'+url.replace('first','third')]:{url:url.replace('first','third'),title:'Third',watchedAt:'2026-10-19T14:00:00Z'}});await tick();assert.equal($('lectures').querySelectorAll('article').length,3);e.close();
});

test('bridge streams watched entries only after a page request and never exposes helper tokens',async()=>{
 const e=setup('',{});e.w.history.replaceState({},'','/');
 // Bridge path/origin must be the real hosted app.
 const dom=new JSDOM('',{url:'https://starfox1230.github.io/The-Library/apps/medality-study/recent.html',runScripts:'outside-only'}),w=dom.window;
 const handlers=[];let onChange;const messages=[];
 const first={url,title:'First',watchedAt:'2026-10-19T12:00:00Z'};
 const saved={['watch:'+url]:first,['transcript:'+url]:{...first,text:'Text'},helperToken:'secret',enabled:true};
 w.chrome={storage:{local:{get:async()=>saved},onChanged:{addListener:fn=>{onChange=fn;}}}};
 w.addEventListener=(name,fn)=>{if(name==='message')handlers.push(fn);};w.postMessage=data=>messages.push(data);
 w.eval(read('extension/workspace-bridge.js'));
 onChange({},'local');await tick();assert.equal(messages.length,0);
 await handlers[0]({source:w,origin:w.location.origin,data:{channel:'medality-study',type:'request-history',requestId:'request'}});
 assert.equal(messages[0].items.length,2);assert.ok(!JSON.stringify(messages).includes('secret'));
 saved['watch:'+url.replace('first','next')]={...first,url:url.replace('first','next')};onChange({},'local');await tick();assert.equal(messages[1].items.length,3);
 dom.window.close();e.close();
});
test('public history adapter stores incoming extension captures locally and ignores wrong sources',async()=>{
 const dom=new JSDOM(read('recent.html'),{url:'https://starfox1230.github.io/The-Library/apps/medality-study/recent.html',runScripts:'outside-only'}),w=dom.window;
 const handlers=[],requests=[];
 w.addEventListener=(name,fn)=>{if(name==='message')handlers.push(fn);};w.postMessage=data=>requests.push(data);
 w.eval(read('extension/history-core.js'));w.eval(read('history-web.js'));
 const item={url,title:'First',text:'Text',note:'My note',watchedAt:'2026-10-19T12:00:00Z'};
 const message={channel:'medality-study',type:'history',requestId:requests[0].requestId,items:[item]};
 handlers[0]({source:{},origin:w.location.origin,data:message});assert.equal(Object.keys(await w.MedalityStorage.local.get()).length,0);
 handlers[0]({source:w,origin:w.location.origin,data:message});const stored=await w.MedalityStorage.local.get();assert.equal(stored['transcript:'+url].text,'Text');assert.equal(stored['transcript:'+url].note,'My note');assert.ok(stored['watch:'+url]);
 assert.match(w.localStorage.getItem('medality-watched-v1'),/First/);w.close();
});
