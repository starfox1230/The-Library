const { test } = require('node:test');
const assert = require('node:assert/strict');
const { JSDOM } = require('jsdom');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const root = resolve(__dirname, '..');
const read = path => readFileSync(resolve(root, path), 'utf8');
const lesson = 'https://medality.com/course/demo/chapter/lesson/sequence/cases/unit/example/';
const rows = '<div><div data-item="0"><p>0:01</p><p>Synthetic opening sentence.</p></div><div data-item="1"><p>0:04</p><p>Synthetic second sentence.</p></div></div>';
const tick = () => new Promise(done => setImmediate(done));
function env(html, url = lesson) {
  const dom = new JSDOM(html, { url, runScripts: 'outside-only' });
  const w = dom.window, observers = [], Original = w.MutationObserver;
  w.MutationObserver = class extends Original { constructor(fn) { super(fn); observers.push(this); } };
  return { w, close() { observers.forEach(o => o.disconnect()); w.close(); } };
}
function workspace(existing) {
  const e = env(read('index.html'), 'https://starfox1230.github.io/The-Library/apps/medality-study/');
  if (existing) e.w.localStorage.setItem('medality-study-v1', JSON.stringify(existing));
  e.w.eval(read('course-data.js')); e.w.eval(read('core.js'));
  e.copied = [];
  Object.defineProperty(e.w.navigator, 'clipboard', { value: { writeText: async text => e.copied.push(text) } });
  e.w.eval(read('app.js'));
  return e;
}

test('capture extracts ordered cues and excludes unrelated page text or hidden transcripts', () => {
  const e = env(`<h1>Example case</h1><header>Navigation should not be copied</header>${rows}<div aria-hidden="true"><div data-item="0"><p>0:01</p><p>Hidden duplicate</p></div></div>`);
  e.w.eval(read('extension/transcript-core.js'));
  const item = e.w.MedalityTranscript.capture(e.w.document, lesson + '?tracking=1#test');
  assert.equal(item.cues.length, 2); assert.equal(item.text, 'Synthetic opening sentence. Synthetic second sentence.');
  assert.equal(item.url, lesson); assert.ok(!e.w.MedalityTranscript.format(item).includes('Navigation')); e.close();
});
test('absence is explicit and never falls back to copying page body', () => {
  const e = env('<h1>Example</h1><p>Some unrelated content.</p>');
  e.w.eval(read('extension/transcript-core.js'));
  assert.throws(() => e.w.MedalityTranscript.capture(e.w.document, lesson), /No transcript/); e.close();
});
test('copy and save actions work through the content-script message interface', async () => {
  const e = env(`<h1>Example</h1>${rows}`); let listener; const stored = {}, copied = [];
  e.w.chrome = { storage: { local: { set: async obj => Object.assign(stored, obj) } }, runtime: { onMessage: { addListener: fn => { listener = fn; } } } };
  Object.defineProperty(e.w.navigator, 'clipboard', { value: { writeText: async text => copied.push(text) } });
  e.w.eval(read('extension/transcript-core.js')); e.w.eval(read('extension/transcript.js'));
  assert.ok(e.w.document.getElementById('medality-transcript-tools').shadowRoot.querySelector('#copy'));
  const run = action => new Promise(reply => listener({ type: 'medality-transcript-action', action }, {}, reply));
  assert.equal((await run('copy')).ok, true); assert.match(copied[0], /Synthetic opening/);
  assert.equal((await run('save')).ok, true); assert.equal(Object.values(stored)[0].text, 'Synthetic opening sentence. Synthetic second sentence.'); e.close();
});
test('capture can open the existing transcript panel on demand', async () => {
  const e = env('<h1>Example</h1><button>Transcript</button><section id="panel"></section>'); let listener;
  e.w.document.querySelector('button').addEventListener('click', () => { e.w.document.getElementById('panel').innerHTML = rows; });
  e.w.chrome = { storage: { local: { set: async () => {} } }, runtime: { onMessage: { addListener: fn => { listener = fn; } } } };
  e.w.eval(read('extension/transcript-core.js')); e.w.eval(read('extension/transcript.js'));
  const result = await new Promise(reply => listener({ type: 'medality-transcript-action', action: 'save' }, {}, reply));
  assert.equal(result.ok, true); assert.equal(result.cues, 2); e.close();
});
test('packet formatting supports transcripts, notes, timestamps, and missing entries', () => {
  const e = env(''); e.w.eval(read('core.js'));
  const a = { title: 'A', url: lesson, text: 'Synthetic text.', cues: [{time:'0:01',text:'Synthetic text.'}], note:'My note.', focus:'My focus.' };
  const b = { title: 'B', url: lesson.replace('example', 'second'), focus:'Second focus.' };
  assert.match(e.w.MedalityCore.packet([a], { mode:'transcripts', timestamps:true }).text, /0:01  Synthetic text/);
  const notes = e.w.MedalityCore.packet([a], {mode:'notes'}).text;
  assert.match(notes, /My note/); assert.ok(!notes.includes('Synthetic text'));
  const result = e.w.MedalityCore.packet([a,b], {mode:'transcripts'});
  assert.equal(result.included, 1); assert.equal(result.missing.length, 1);
  assert.equal(e.w.MedalityCore.packet([], {prompt:true}).text, ''); e.close();
});
test('imports reject invalid URLs and normalize duplicate lessons', () => {
  const e = env(''); e.w.eval(read('core.js'));
  assert.throws(() => e.w.MedalityCore.imported({items:[{url:'javascript:alert(1)',text:'x'}]}), /Medality/);
  assert.throws(() => e.w.MedalityCore.imported({items:[{url:'https://medality.com.evil.test/unit/x/',text:'x'}]}), /Medality/);
  assert.equal(e.w.MedalityCore.imported({items:[{url:lesson,text:'a'},{url:lesson+'?q=1',text:'b'}]}).length, 1); e.close();
});
test('workspace starts empty, selects any/all/none, and preserves selection across filters', () => {
  const e = workspace(), d = e.w.document;
  assert.equal(d.querySelectorAll('.lesson').length, 38); assert.equal(d.getElementById('copy-packet').disabled, true);
  d.getElementById('select-all').click(); assert.equal(d.getElementById('selection-count').textContent, '38 selected');
  d.getElementById('search').value = 'washout'; d.getElementById('search').dispatchEvent(new e.w.Event('input'));
  assert.ok(d.querySelectorAll('.lesson').length < 38); assert.match(d.getElementById('packet-warning').textContent, /outside/);
  d.getElementById('select-none').click(); assert.equal(d.getElementById('selection-count').textContent, '0 selected');
  d.getElementById('select-first').click(); assert.equal(d.getElementById('selection-count').textContent, '11 selected'); e.close();
});
test('workspace copies only selected transcripts and retains notes on extension import', async () => {
  const boot = workspace(); const url = boot.w.MEDALITY_COURSE[0].url; boot.close();
  const e = workspace({ [url]:{url,title:'Preview',text:'Existing synthetic transcript.',note:'Preserve this note.'} }), d = e.w.document;
  const box = d.querySelector('.lesson input'); box.checked = true; box.dispatchEvent(new e.w.Event('change'));
  assert.match(d.getElementById('preview').value, /Existing synthetic transcript/);
  d.getElementById('copy-packet').click(); await tick(); assert.equal(e.copied.length,1);
  e.w.postMessage = data => {
    if (data.type === 'request-captures') e.w.dispatchEvent(new e.w.MessageEvent('message',{origin:e.w.location.origin,source:e.w,data:{channel:'medality-study',type:'captures',requestId:data.requestId,items:[{url,text:'New synthetic transcript.'}]}}));
  };
  d.getElementById('import-extension').click(); await tick();
  const saved = JSON.parse(e.w.localStorage.getItem('medality-study-v1'));
  assert.equal(saved[url].note,'Preserve this note.'); assert.equal(saved[url].text,'New synthetic transcript.'); e.close();
});
test('bridge exposes only capture entries and ignores wrong-source messages', async () => {
  const e = env('', 'https://starfox1230.github.io/The-Library/apps/medality-study/'); let gets = 0; const output = [];
  e.w.chrome = {storage:{local:{get:async()=>{gets++;return {speed:2,enabled:true,[`transcript:${lesson}`]:{url:lesson,text:'Synthetic.'}};}}}};
  e.w.postMessage = data => output.push(data); e.w.eval(read('extension/workspace-bridge.js'));
  const send = source => e.w.dispatchEvent(new e.w.MessageEvent('message',{origin:e.w.location.origin,source,data:{channel:'medality-study',type:'request-captures',requestId:'test'}}));
  send(null); await tick(); assert.equal(gets,0);
  send(e.w); await tick(); assert.equal(gets,1); assert.equal(output[0].items.length,1); assert.equal(output[0].items[0].text,'Synthetic.'); assert.ok(!JSON.stringify(output).includes('enabled')); e.close();
});
test('imported HTML is displayed as text rather than executed markup', async () => {
  const e = workspace(), d=e.w.document;
  e.w.postMessage = data => { if (data.type === 'request-captures') e.w.dispatchEvent(new e.w.MessageEvent('message',{origin:e.w.location.origin,source:e.w,data:{channel:'medality-study',type:'captures',requestId:data.requestId,items:[{url:lesson,title:'<img src=x onerror=alert(1)>',text:'<script>bad()</script>'}]}})); };
  d.getElementById('import-extension').click(); await tick();
  assert.equal(d.getElementById('lesson-list').querySelectorAll('img').length,0); assert.match(d.getElementById('lesson-list').textContent,/<img/); e.close();
});

test('new device can start with useful study notes without importing a file', () => {
  const e=workspace(), d=e.w.document;
  assert.equal(d.getElementById('empty-state').hidden,false);
  d.getElementById('start-notes').click();
  assert.equal(d.getElementById('mode').value,'notes');
  assert.equal(d.getElementById('selection-count').textContent,'11 selected');
  assert.ok(d.getElementById('preview').value.length>100);
  e.close();
});
test('empty device does not create an empty phone-transfer file', () => {
  const e=workspace(), d=e.w.document;
  d.getElementById('send-library').click();
  assert.match(d.getElementById('transfer-status').textContent,/no saved transcripts/);
  e.close();
});
test('phone file sharing carries saved transcripts and notes, and leaves source intact', async () => {
  const boot=workspace(), url=boot.w.MEDALITY_COURSE[0].url;boot.close();
  const entry={url,title:'Synthetic case',text:'Synthetic transcript.',note:'Personal note.'};
  const e=workspace({[url]:entry});let shared;
  e.w.navigator.canShare=()=>true;
  e.w.navigator.share=async data=>{shared=data;};
  e.w.document.getElementById('send-library').click();await tick();
  assert.equal(shared.files[0].name,'liver-mri-saved-library.json');
  const reader=new e.w.FileReader();
  const content=await new Promise(resolve=>{reader.onload=()=>resolve(reader.result);reader.readAsText(shared.files[0]);});
  const data=JSON.parse(content);
  assert.equal(data.items[0].note,'Personal note.');
  assert.equal(e.w.MedalityCore.imported(data)[0].text,'Synthetic transcript.');
  assert.equal(JSON.parse(e.w.localStorage.getItem('medality-study-v1'))[url].note,'Personal note.');
  e.close();
});
test('connected extension with zero captures explains the required first save', async () => {
  const e=workspace(), d=e.w.document;
  e.w.postMessage=data=>{if(data.type==='request-captures')e.w.dispatchEvent(new e.w.MessageEvent('message',{origin:e.w.location.origin,source:e.w,data:{channel:'medality-study',type:'captures',requestId:data.requestId,items:[]}}));};
  d.getElementById('import-extension').click();await tick();
  assert.match(d.getElementById('message').textContent,/Save transcript first/);
  e.close();
});

test('download button sends the current lecture to helper and shows completion', async () => {
  const e = env('<h1>Example</h1><iframe src="https://player.vimeo.com/video/123?autoplay=1&h=abc"></iframe>');
  const sent = [];
  e.w.setTimeout = fn => { fn(); return 0; };
  e.w.chrome = { runtime: { onMessage: { addListener() {} }, sendMessage: async message => {
    sent.push(message);
    return message.type === 'medality-download' ? {ok:true,job:'abc'} : {ok:true,state:'complete',message:'Saved in Downloads / Medality'};
  } } };
  e.w.eval(read('extension/transcript-core.js')); e.w.eval(read('extension/transcript.js'));
  const root = e.w.document.getElementById('medality-transcript-tools').shadowRoot;
  root.querySelector('#download').click(); await tick();
  assert.equal(sent[0].video, 'https://player.vimeo.com/video/123?h=abc');
  assert.equal(sent[1].job, 'abc');
  assert.match(root.querySelector('[role="status"]').textContent, /Saved/);
  assert.equal(root.querySelector('#download').disabled, false);
  e.close();
});

test('download button explains missing player and helper errors', async () => {
  const e = env('<h1>Example</h1>');
  e.w.chrome = {runtime:{onMessage:{addListener(){}},sendMessage:async()=>({ok:false,error:'Start helper first'})}};
  e.w.eval(read('extension/transcript-core.js')); e.w.eval(read('extension/transcript.js'));
  const root = e.w.document.getElementById('medality-transcript-tools').shadowRoot;
  root.querySelector('#download').click(); await tick();
  assert.match(root.querySelector('[role="status"]').textContent, /No supported video/);
  const frame = e.w.document.createElement('iframe');frame.src='https://player.vimeo.com/video/123';e.w.document.body.append(frame);
  root.querySelector('#download').click(); await tick();
  assert.match(root.querySelector('[role="status"]').textContent, /Start helper first/);
  assert.equal(root.querySelector('#download').disabled,false);e.close();
});

test('background download bridge rejects unrelated sites and passes only lesson URL and video', async () => {
  const vm = require('node:vm'); const listeners = [], requests = [];
  const context = { self:{MEDALITY_HELPER_TOKEN:'synthetic'}, importScripts(){}, URL,
    chrome:{commands:{onCommand:{addListener(){}}},runtime:{onMessage:{addListener:fn=>listeners.push(fn)}}},
    fetch:async (url,options)=>{requests.push({url,options});return {ok:true,json:async()=>({job:'a'.repeat(32)})};} };
  vm.runInNewContext(read('extension/background.js'),context);
  const listener = listeners[0];
  assert.equal(listener({type:'medality-download',video:'https://player.vimeo.com/video/123'},{url:'https://medality.com.evil.test/'},()=>{}),undefined);
  assert.equal(requests.length,0);
  const reply = await new Promise(resolve=>listener({type:'medality-download',video:'https://player.vimeo.com/video/123',page:'https://evil.test/'},{url:lesson},resolve));
  assert.equal(reply.ok,true);
  assert.equal(JSON.parse(requests[0].options.body).page,lesson);
  assert.equal(requests[0].options.headers['X-Medality-Token'],'synthetic');
});
