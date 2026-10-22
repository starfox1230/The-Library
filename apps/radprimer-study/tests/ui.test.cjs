const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const {boot,record,runtime,fixture}=require('./fixtures.cjs');
const tick=()=>new Promise(r=>setTimeout(r,50));
test('library hides answers/keys, reveals all explanations and annotates the selected image',async()=>{
  const html=fs.readFileSync(path.join(runtime,'library.html'),'utf8');const {w,dom,load}=boot(html,'https://example.test/extension/library.html');
  try{
    const c=await record({notes:'precise note',highlights:['specific fact'],ankiStatus:'queued',tier:'essential'});await w.RadDB.importBackup({format:'radprimer-library',schema:1,cases:[c]});
    await load('library.js');assert.equal(w.document.querySelectorAll('.case-card').length,1);assert.equal(w.document.querySelectorAll('.explanation-pane details').length,0);
    assert.ok(!w.document.querySelector('#case-detail').textContent.includes('Secret explanation'));assert.ok(!w.document.querySelector('#case-detail').textContent.includes('Key g0'));
    const reveal=Array.from(w.document.querySelectorAll('button')).find(b=>b.textContent==='Reveal answer & keys');reveal.click();
    assert.equal(w.document.querySelectorAll('.explanation-pane details').length,3);assert.match(w.document.querySelector('#case-detail').textContent,/Secret explanation/);assert.match(w.document.querySelector('#case-detail').textContent,/Key g0-i0/);
    const toggle=w.document.querySelector('.annotation');toggle.click();assert.equal(toggle.textContent,'Hide annotations');
    assert.equal(w.document.querySelector('#case-notes').value,'precise note');
    w.document.querySelector('#search').value='no match';w.document.querySelector('#search').dispatchEvent(new w.Event('input'));assert.equal(w.document.querySelectorAll('.case-card').length,0);
  }finally{dom.window.close();}
});
test('notes, tiers, review scheduling, archive and restore persist through the UI',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  const click=text=>{const b=Array.from(w.document.querySelectorAll('button')).find(b=>b.textContent===text);assert.ok(b,'button '+text);b.click();};
  try{
    const c=await record();await w.RadDB.saveCapture(c);await load('library.js');w.document.querySelector('#inspector-tab-notes').click();
    const notes=w.document.querySelector('#case-notes');notes.value='new note';notes.dispatchEvent(new w.Event('input'));click('Save note');await tick();assert.equal((await w.RadDB.get(c.id)).notes,'new note');
    const select=w.document.querySelector('#anki-status');select.value='queued';select.dispatchEvent(new w.Event('change'));await tick();assert.equal((await w.RadDB.get(c.id)).ankiStatus,'queued');
    click('Revisit in 1 week');await tick();assert.ok(Date.parse((await w.RadDB.get(c.id)).dueAt)>Date.now());
    click('Archive case');await tick();assert.equal((await w.RadDB.get(c.id)).archived,true);
    w.document.querySelector('[data-view=archive]').click();w.document.querySelector('#inspector-tab-notes').click();click('Restore case');await tick();assert.equal((await w.RadDB.get(c.id)).archived,false);
    w.document.querySelector('[data-view=all]').click();assert.equal(w.document.querySelector('#case-notes').value,'new note');
  }finally{dom.window.close();}
});
test('content panel saves current case with selected facts and Anki intent, then handles SPA navigation',async()=>{
  const {w,dom,load}=fixture();let sent;
  try{
    w.chrome={runtime:{sendMessage:async value=>{sent=value;return{ok:true,answered:true,media:{saved:4,total:4,failed:0}};}}};
    w.RadCapture.fetchImage=async()=>require('./fixtures.cjs').pixel;load('content.js');
    const shadow=w.document.querySelector('#rp-case-library').shadowRoot;shadow.querySelector('textarea').value='Target fact';shadow.querySelector('textarea').dispatchEvent(new w.Event('input'));
    w.getSelection=()=>({toString:()=> 'Selected sentence'});shadow.querySelector('[data-highlight]').click();shadow.querySelector('[data-anki]').click();
    await new Promise(r=>setTimeout(r,600));assert.equal(sent.type,'rp:save');assert.equal(sent.options.anki,true);assert.equal(sent.options.notes,'Target fact');assert.equal(sent.options.highlights[0],'Selected sentence');assert.match(shadow.querySelector('[role=status]').textContent,/Saved \+ queued/);
    w.document.querySelector('#mcq-question-stem').textContent='Another synthetic case';await new Promise(r=>setTimeout(r,300));assert.equal(shadow.querySelector('textarea').value,'');
  }finally{dom.window.close();}
});
test('malicious imported text stays literal and source URLs are sanitized',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try{const c=await record({stem:'<img src=x onerror=alert(1)>',notes:'<script>bad()</script>',sourceUrl:'javascript:bad()'});await w.RadDB.importBackup({format:'radprimer-library',schema:1,cases:[c]});await load('library.js');assert.match(w.document.querySelector('.detail-head .stem').textContent,/<img/);assert.equal(w.document.querySelectorAll('.detail-head img').length,0);assert.equal(w.document.querySelectorAll('.review-topbar a').length,0);}
  finally{dom.window.close();}
});

test('image-first review switches groups in place and compares them without stacking every group', async () => {
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try {
    const c=await record();await w.RadDB.saveCapture(c);await load('library.js');
    const visible=()=>Array.from(w.document.querySelectorAll('.image-grid > .group')).filter(g=>!g.hidden);
    assert.equal(visible().length,1);assert.equal(visible()[0].id,'image-group-panel-0');
    assert.ok(w.document.querySelector('.review-layout').firstElementChild.classList.contains('case-inspector'));
    assert.ok(w.document.querySelector('.work').classList.contains('single-case'));
    assert.equal(w.document.querySelector('#inspector-panel-question').hidden,false);
    assert.equal(w.document.querySelector('#inspector-panel-notes').hidden,true);
    w.document.querySelector('#image-group-tab-1').click();assert.equal(visible()[0].id,'image-group-panel-1');
    w.document.querySelector('.compare-groups').click();assert.equal(visible().length,2);assert.ok(w.document.querySelector('.image-grid').classList.contains('comparing'));
    w.document.querySelector('.compare-groups').click();assert.equal(visible().length,1);
    // Select image 2, then change information panels and groups: the selected image is retained.
    visible()[0].querySelector('[data-image-next]').click();
    w.document.querySelector('#inspector-tab-notes').click();assert.equal(visible()[0].querySelector('.thumbs [aria-pressed=true]').getAttribute('aria-label'),'Group 2, image 2');
    w.document.querySelector('#image-group-tab-0').click();w.document.querySelector('#image-group-tab-1').click();
    assert.equal(visible()[0].querySelector('.thumbs [aria-pressed=true]').getAttribute('aria-label'),'Group 2, image 2');
    w.document.querySelector('#focus-images').click();assert.ok(w.document.body.classList.contains('images-focus'));
    w.document.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Escape',bubbles:true}));assert.equal(w.document.body.classList.contains('images-focus'),false);
  } finally {dom.window.close();}
});

test('tab and image keyboard navigation work without revealing answers',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try{
    await w.RadDB.saveCapture(await record());await load('library.js');
    w.document.querySelector('#image-group-tab-0').dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,cancelable:true}));
    assert.equal(w.document.querySelector('#image-group-tab-1').getAttribute('aria-selected'),'true');
    w.document.querySelector('#image-group-panel-1 [data-image-next]').dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowRight',bubbles:true,cancelable:true}));
    assert.equal(w.document.querySelector('#image-group-panel-1 .thumbs [aria-pressed=true]').getAttribute('aria-label'),'Group 2, image 2');
    assert.equal(w.document.querySelectorAll('.explanation-pane details').length,0);
    assert.ok(!w.document.querySelector('.caption').textContent.includes('Key g'));
    w.document.querySelector('#inspector-tab-question').dispatchEvent(new w.KeyboardEvent('keydown',{key:'End',bubbles:true,cancelable:true}));
    assert.equal(w.document.querySelector('#inspector-panel-notes').hidden,false);
  }finally{dom.window.close();}
});

test('two single-image groups open side by side on desktop and multiple cases have a collapsible list',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try{
    const c=await record();c.groups.forEach(g=>{g.images=g.images.slice(0,1);});
    await w.RadDB.saveCapture(c);
    const other=await record({id:'rp-'+'a'.repeat(64),stem:'Another independent synthetic case'});await w.RadDB.saveCapture(other);
    await load('library.js');
    // Select the two-image case regardless of saved-time ordering.
    Array.from(w.document.querySelectorAll('.case-card')).find(b=>b.textContent.includes(c.stem)).click();
    assert.equal(Array.from(w.document.querySelectorAll('.image-grid>.group')).filter(g=>!g.hidden).length,2);
    assert.equal(w.document.querySelector('.work').classList.contains('single-case'),false);
    w.document.querySelector('#toggle-cases').click();assert.equal(w.document.querySelector('.work').classList.contains('cases-collapsed'),true);
    assert.equal(w.document.querySelector('#toggle-cases').getAttribute('aria-expanded'),'false');
  }finally{dom.window.close();}
});

test('opening an image key reveals the saved answer and keeps the selected image and key open',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try{
    await w.RadDB.saveCapture(await record());await load('library.js');
    w.document.querySelector('#image-group-tab-1').click();w.document.querySelector('#image-group-panel-1 [data-image-next]').click();
    w.document.querySelector('#image-group-panel-1 .image-key').open=true;await tick();
    assert.equal(w.document.querySelector('#image-group-panel-1 .image-key').open,true);
    assert.match(w.document.querySelector('#image-group-panel-1 .caption').textContent,/Key g1-i1/);
    assert.equal(w.document.querySelector('#image-group-tab-1').getAttribute('aria-selected'),'true');
    assert.equal(w.document.querySelector('#image-group-panel-1 .thumbs [aria-pressed=true]').getAttribute('aria-label'),'Group 2, image 2');
    assert.ok(w.document.querySelector('.choice.correct'));assert.equal(w.document.querySelectorAll('.explanation-pane details').length,3);
    Array.from(w.document.querySelectorAll('button')).find(b=>b.textContent==='Hide answer & keys').click();await tick();
    assert.equal(w.document.querySelectorAll('.image-key[open]').length,0);assert.equal(w.document.querySelectorAll('.explanation-pane details').length,0);
  }finally{dom.window.close();}
});

test('opening a question-only image key does not invent an unavailable answer',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  try{
    const c=await record({answered:false,teachingPoint:''});c.answers.forEach(a=>{a.explanation='';a.correctness='';});c.groups.forEach(g=>g.images.forEach(i=>{i.caption='';}));
    await w.RadDB.saveCapture(c);await load('library.js');
    w.document.querySelector('.image-key').open=true;await tick();
    assert.match(w.document.querySelector('.caption').textContent,/No image key was saved/);assert.equal(w.document.querySelector('.choice.correct'),null);
    assert.equal(w.document.querySelectorAll('.explanation-pane details').length,0);
  }finally{dom.window.close();}
});
