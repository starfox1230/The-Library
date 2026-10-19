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
  assert.equal(d.querySelectorAll('img').length,0); assert.match(d.getElementById('lesson-list').textContent,/<img/); e.close();
});
