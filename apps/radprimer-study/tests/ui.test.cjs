const test=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const path=require('node:path');
const {boot,record,runtime,fixture}=require('./fixtures.cjs');
const tick=()=>new Promise(r=>setTimeout(r,50));
test('library hides answers/keys, reveals all explanations and annotates the selected image',async()=>{
  const html=fs.readFileSync(path.join(runtime,'library.html'),'utf8');const {w,dom,load}=boot(html,'https://example.test/extension/library.html');
  try{
    const c=await record({notes:'precise note',highlights:['specific fact'],ankiStatus:'queued',tier:'essential'});await w.RadDB.importBackup({format:'radprimer-library',schema:1,cases:[c]});
    await load('library.js');assert.equal(w.document.querySelectorAll('.case-card').length,1);assert.equal(w.document.querySelectorAll('#case-detail details').length,0);
    assert.ok(!w.document.querySelector('#case-detail').textContent.includes('Secret explanation'));assert.ok(!w.document.querySelector('#case-detail').textContent.includes('Key g0'));
    const reveal=Array.from(w.document.querySelectorAll('button')).find(b=>b.textContent==='Reveal answer & keys');reveal.click();
    assert.equal(w.document.querySelectorAll('#case-detail details').length,3);assert.match(w.document.querySelector('#case-detail').textContent,/Secret explanation/);assert.match(w.document.querySelector('#case-detail').textContent,/Key g0-i0/);
    const toggle=w.document.querySelector('.annotation');toggle.click();assert.equal(toggle.textContent,'Hide annotations');
    assert.equal(w.document.querySelector('#case-notes').value,'precise note');
    w.document.querySelector('#search').value='no match';w.document.querySelector('#search').dispatchEvent(new w.Event('input'));assert.equal(w.document.querySelectorAll('.case-card').length,0);
  }finally{dom.window.close();}
});
test('notes, tiers, review scheduling, archive and restore persist through the UI',async()=>{
  const {w,dom,load}=boot(fs.readFileSync(path.join(runtime,'library.html'),'utf8'),'https://example.test/extension/library.html');
  const click=text=>{const b=Array.from(w.document.querySelectorAll('button')).find(b=>b.textContent===text);assert.ok(b,'button '+text);b.click();};
  try{
    const c=await record();await w.RadDB.saveCapture(c);await load('library.js');
    const notes=w.document.querySelector('#case-notes');notes.value='new note';notes.dispatchEvent(new w.Event('input'));click('Save note');await tick();assert.equal((await w.RadDB.get(c.id)).notes,'new note');
    const select=w.document.querySelector('#anki-status');select.value='queued';select.dispatchEvent(new w.Event('change'));await tick();assert.equal((await w.RadDB.get(c.id)).ankiStatus,'queued');
    click('Revisit in 1 week');await tick();assert.ok(Date.parse((await w.RadDB.get(c.id)).dueAt)>Date.now());
    click('Archive case');await tick();assert.equal((await w.RadDB.get(c.id)).archived,true);
    w.document.querySelector('[data-view=archive]').click();click('Restore case');await tick();assert.equal((await w.RadDB.get(c.id)).archived,false);
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
  try{const c=await record({stem:'<img src=x onerror=alert(1)>',notes:'<script>bad()</script>',sourceUrl:'javascript:bad()'});await w.RadDB.importBackup({format:'radprimer-library',schema:1,cases:[c]});await load('library.js');assert.match(w.document.querySelector('.detail-head .stem').textContent,/<img/);assert.equal(w.document.querySelectorAll('.detail-head img').length,0);assert.equal(w.document.querySelectorAll('.detail-head a').length,0);}
  finally{dom.window.close();}
});
