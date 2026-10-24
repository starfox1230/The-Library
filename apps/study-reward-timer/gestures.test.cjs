const test=require('node:test');
const assert=require('node:assert/strict');
const G=require('./gestures');
const E=require('./engine');
function setup() {
  let time=1000,id=0;
  const tasks=new Map(),s=E.fresh();E.start(s,time);
  const feedback=[],progress=[];
  const hold=G.createHold({
    begin:()=>{feedback.push('hold');return E.beginHold(s,time);},
    cancel:()=>{feedback.push('cancel');E.cancelHold(s,time);},
    complete:()=>{feedback.push('complete');E.finish(s,time);},
    progress:(...p)=>progress.push(p),now:()=>time,
    schedule:(fn,delay)=>{tasks.set(++id,{fn,at:time+delay});return id;},clear:id=>tasks.delete(id),
    frame:()=>1,cancelFrame:()=>{}
  });
  return {s,hold,feedback,progress,tasks,setTime:t=>time=t,flush:()=>{for(const [id,t] of tasks)if(t.at<=time){tasks.delete(id);t.fn();}}};
}
test('hold freezes at contact, completes only after a second, and never pays twice',()=>{
  const x=setup();x.setTime(1080999);assert.equal(x.hold.start(),true);
  assert.equal(E.elapsed(x.s.active,2000000),1079999);assert.equal(x.s.active.holding,true);
  x.setTime(1081998);x.flush();assert.equal(x.s.records.length,0);
  x.setTime(1081999);x.flush();x.hold.release();x.hold.cancel();
  assert.equal(x.s.records.length,1);assert.equal(x.s.records[0].elapsedMs,1079999);assert.equal(E.total(x.s.records),200);
  assert.deepEqual(x.feedback,['hold','complete']);assert.deepEqual(x.progress[0],[0,true]);assert.deepEqual(x.progress.at(-1),[0,false]);
});
test('early release resumes exactly and cancels every pending completion callback',()=>{
  const x=setup();x.setTime(2000);x.hold.start();x.setTime(2700);x.hold.release();
  assert.equal(x.s.active.holding,undefined);assert.equal(x.s.active.runningSince,2700);assert.equal(x.tasks.size,0);
  x.setTime(10000);x.flush();assert.equal(x.s.records.length,0);assert.equal(E.elapsed(x.s.active,2800),1100);
});
test('release at the deadline succeeds even if the browser has not dispatched its timeout yet',()=>{
  const x=setup();x.hold.start();x.setTime(2000);x.hold.release();x.flush();
  assert.equal(x.s.records.length,1);assert.equal(x.s.records[0].elapsedMs,0);
});
test('cancellation by blur, navigation or pointer interruption never completes a case',()=>{
  const x=setup();x.hold.start();assert.equal(x.hold.start(),false);
  x.setTime(3000);x.hold.cancel();x.flush();assert.equal(x.s.records.length,0);assert.equal(x.tasks.size,0);
  E.pause(x.s,3100);assert.equal(x.hold.start(),false);assert.equal(x.hold.isActive(),false);
});

test('main taps exclude interactive controls; moving and long presses do not toggle pause',()=>{
  const saved={document:global.document,window:global.window,setTimeout:global.setTimeout,clearTimeout:global.clearTimeout,performance:global.performance};
  class Surface {
    listeners={};
    addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
    emit(name,event){for(const fn of this.listeners[name]||[])fn(event);}
  }
  const doc=new Surface(),win=new Surface(),main=new Surface(),face=new Surface(),button=new Surface();
  let time=0,timeout,toggles=0,durations=0,cancelled=0,dialog=false;
  global.document=doc;global.window=win;global.performance={now:()=>time};
  global.setTimeout=fn=>(timeout=fn,1);global.clearTimeout=()=>{timeout=null;};
  const target={closest:()=>null};face.contains=t=>t===target;
  const event=(extra={})=>({target,pointerId:1,isPrimary:true,button:0,clientX:100,clientY:100,preventDefault(){},stopPropagation(){},...extra});
  try {
    G.bind({face,completeButton:button,main,toggle:()=>toggles++,openDuration:()=>{durations++;dialog=true;},canInteract:()=>!dialog,holdEnabled:()=>false,hold:{cancel:()=>cancelled++,release(){}}});
    main.emit('pointerdown',event());time=100;doc.emit('pointerup',event());assert.equal(toggles,1);
    main.emit('pointerdown',event({target:{closest:()=>({})}}));doc.emit('pointerup',event());assert.equal(toggles,1);
    main.emit('pointerdown',event());doc.emit('pointermove',event({clientX:120}));doc.emit('pointerup',event());assert.equal(toggles,1);
    main.emit('pointerdown',event());timeout();time=800;doc.emit('pointerup',event());assert.equal(durations,1);assert.equal(toggles,1);
    dialog=false;main.emit('pointerdown',event());doc.emit('pointercancel',event());doc.emit('pointerup',event());assert.equal(toggles,1);assert.equal(cancelled,1);
    // Switching apps can lose the old touch's pointerup entirely.
    doc.emit('pointerdown',event({pointerId:10}));main.emit('pointerdown',event({pointerId:10}));win.emit('blur',{});
    doc.emit('pointerdown',event({pointerId:11}));main.emit('pointerdown',event({pointerId:11}));
    doc.emit('pointerup',event({pointerId:11}));assert.equal(toggles,2);
  } finally {for(const [key,value] of Object.entries(saved))global[key]=value;}
});
