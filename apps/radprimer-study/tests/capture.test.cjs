const test = require('node:test');
const assert = require('node:assert/strict');
const { fixture, pixel } = require('./fixtures.cjs');

test('captures every group/image with its exact key and both variants, then restores selections', async()=>{
  const {w,dom}=fixture(); const urls=[];
  try {
    const c=await w.RadCapture.capture(w.document,async url=>{urls.push(url);return pixel;});
    assert.equal(c.groups.length,2);assert.equal(c.groups.flatMap(g=>g.images).length,4);assert.equal(urls.length,8);
    for(const g of c.groups) for(const i of g.images){
      assert.ok(i.caption.includes(i.id));assert.ok(i.caption.includes('[White solid arrow]'));
      assert.equal(i.original,pixel);assert.equal(i.annotated,pixel);
      assert.ok(i.originalUrl.endsWith('?style=xlarge'));assert.ok(i.annotatedUrl.endsWith('?style=xlarge&annotated=true'));
    }
    assert.equal(c.answers[1].correctness,'correct');assert.equal(c.answers[1].text,'Square');assert.equal(c.teachingPoint,'Secret teaching point');
    assert.equal(w.document.querySelector('.image-group:not(.hidden)').dataset.imageGroupId,'group-1');
    assert.ok(Array.from(w.document.querySelectorAll('.image-slider-button.selected')).every(b=>b.dataset.imageId.endsWith('i1')));
  }finally{dom.window.close();}
});
test('unanswered captures do not include hidden correctness, explanations, teaching points or keys',async()=>{
  const {w,dom}=fixture(false);let requests=0;
  try{
    const c=await w.RadCapture.capture(w.document,async()=>{requests++;return pixel;});
    assert.equal(c.answered,false);assert.equal(requests,4);assert.equal(c.teachingPoint,'');
    assert.ok(c.answers.every(a=>!a.correctness&&!a.explanation));
    assert.ok(c.groups.every(g=>g.images.every(i=>!i.caption&&!i.annotated&&!i.annotationExpected)));
  }finally{dom.window.close();}
});
test('failed image responses remain visible while other media and the question are saved',async()=>{
  const {w,dom}=fixture();
  try{
    const c=await w.RadCapture.capture(w.document,async url=>{if(url.includes('g0-i0'))throw Error('401');return pixel;});
    const counts=w.RadCore.mediaCount(c);assert.equal(counts.total,4);assert.equal(counts.saved,3);assert.equal(counts.failed,1);
    assert.match(c.groups[0].images[0].error,/Original: 401; Annotated: 401/);
  }finally{dom.window.close();}
});
test('navigation during image capture aborts instead of mixing two questions',async()=>{
  const {w,dom}=fixture();
  try{await assert.rejects(w.RadCapture.capture(w.document,async()=>{w.document.querySelector('#mcq-question-stem').textContent='Different question';return pixel;}),/question changed/);}
  finally{dom.window.close();}
});
test('unsupported question layout fails explicitly',()=>{
  const {w,dom}=fixture();try{w.document.querySelector('#mcq-question-stem').remove();assert.throws(()=>w.RadCapture.snapshot(),/layout is not recognized/);}finally{dom.window.close();}
});
