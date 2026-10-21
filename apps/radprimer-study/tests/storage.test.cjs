const test=require('node:test');const assert=require('node:assert/strict');
const {boot,record,pixel}=require('./fixtures.cjs');
test('same case deduplicates across assessments; re-save preserves personal edits and complete content',async()=>{
  const {w,dom}=boot();try{
    const c=await record();await w.RadDB.saveCapture(c,{notes:'Only this fact',highlights:['selected fact'],anki:true});
    await w.RadDB.patch(c.id,{ankiStatus:'done',dueAt:'2027-01-01T00:00:00.000Z',tier:'reference'});
    const incoming=JSON.parse(JSON.stringify(c));incoming.answered=false;incoming.teachingPoint='';incoming.answers.forEach(a=>{a.correctness='';a.explanation='';});
    incoming.groups[0].images[0].original='';incoming.groups[0].images[0].annotated='';incoming.groups[0].images[0].caption='';incoming.groups[0].images[0].annotationExpected=false;incoming.groups[0].images[0].annotatedUrl='';incoming.groups[0].images[0].error='Network failed';
    const saved=await w.RadDB.saveCapture(incoming);assert.equal((await w.RadDB.all()).length,1);
    assert.equal(saved.answered,true);assert.equal(saved.notes,'Only this fact');assert.equal(saved.highlights[0],'selected fact');assert.equal(saved.ankiStatus,'done');assert.equal(saved.dueAt,'2027-01-01T00:00:00.000Z');
    assert.equal(saved.groups[0].images[0].original,pixel);assert.equal(saved.groups[0].images[0].error,'');assert.ok(saved.groups[0].images[0].caption);assert.equal(saved.groups[0].images[0].annotationExpected,true);assert.ok(saved.groups[0].images[0].annotatedUrl);
  }finally{dom.window.close();}
});
test('backup round trip includes media; import preserves current notes and queue state',async()=>{
  const {w,dom}=boot();try{
    const c=await record({notes:'imported note',highlights:['old fact'],ankiStatus:'queued',tier:'essential'});
    const data={format:'radprimer-library',schema:1,cases:[c]};await w.RadDB.importBackup(data);
    await w.RadDB.patch(c.id,{notes:'newer local note',ankiStatus:'done',highlights:['new fact']});
    await w.RadDB.importBackup(data);const saved=await w.RadDB.get(c.id);
    assert.equal(saved.notes,'newer local note');assert.equal(saved.ankiStatus,'done');assert.equal(saved.highlights.length,2);assert.equal(saved.groups[0].images[0].original,pixel);
  }finally{dom.window.close();}
});
test('invalid import is atomic, validates schema and rejects duplicate IDs',async()=>{
  const {w,dom}=boot();try{
    const c=await record();assert.throws(()=>w.RadDB.importBackup({format:'radprimer-library',schema:1,cases:[c,{id:'bad'}]}),/invalid case/);assert.equal((await w.RadDB.all()).length,0);
    assert.throws(()=>w.RadCore.parseBackup({format:'radprimer-library',schema:1,cases:[c,c]}),/Duplicate/);
    assert.throws(()=>w.RadCore.parseBackup({schema:999,cases:[c]}),/schema 1/);
  }finally{dom.window.close();}
});
test('imports never render remote/data SVG media or unsafe source links',async()=>{
  const {w,dom}=boot();try{
    const c=await record({sourceUrl:'javascript:alert(1)'});c.groups[0].images[0].original='data:image/svg+xml;base64,PHN2Zz4=';
    const valid=w.RadCore.validateCase(c);assert.equal(valid.sourceUrl,'');assert.equal(valid.groups[0].images[0].original,'');assert.match(valid.groups[0].images[0].error,/not stored/);
    assert.equal(w.RadCore.safeSource('https://app.radprimer.com.evil.test/'),'');
  }finally{dom.window.close();}
});
test('Anki packet includes only active queued cases and leaves queue statuses untouched',async()=>{
  const {w,dom}=boot();try{
    const c=await record({ankiStatus:'queued',notes:'specific fact'}),done={...c,ankiStatus:'done'},archived={...c,archived:true};
    const p=w.RadCore.packet([c,done,archived]);assert.equal(p.cases.length,1);assert.equal(p.cases[0].notes,'specific fact');assert.ok(p.instructions.includes('saCloze++'));assert.equal(c.ankiStatus,'queued');
  }finally{dom.window.close();}
});
test('stable case IDs use answer identity, not assessment or question position',async()=>{
  const {w,dom}=boot();try{
    const a=await w.RadCore.caseId('stem',[{id:'a'},{id:'b'}]),b=await w.RadCore.caseId('stem',[{id:'b'},{id:'a'}]),c=await w.RadCore.caseId('stem',[{id:'c'}]);
    assert.equal(a,b);assert.notEqual(a,c);
  }finally{dom.window.close();}
});
