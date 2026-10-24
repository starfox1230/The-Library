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

function withStartButton(run) {
  const saved={document:global.document,window:global.window};
  class Surface {
    listeners={};
    addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
    emit(name,event){for(const fn of this.listeners[name]||[])fn(event);}
  }
  const doc=new Surface(),win=new Surface(),button=new Surface();
  const startTarget={},completeTarget={},otherTarget={};
  button.contains=target=>target===startTarget;
  button.hidden=true;button.disabled=false;
  global.document=doc;global.window=win;
  const x=setup();let starts=0;
  const event=(extra={})=>({target:startTarget,pointerId:1,pointerType:'touch',detail:1,isPrimary:true,button:0,clientX:100,clientY:100,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},...extra});
  G.bindStartButton({button,canStart:()=>!x.s.active,start:()=>{starts++;E.start(x.s,10000);button.hidden=true;}});
  const tap=()=>{doc.emit('pointerdown',event());doc.emit('pointerup',event());button.emit('click',event());};
  try {run({...x,doc,win,button,event,tap,startTarget,completeTarget,otherTarget,starts:()=>starts});}
  finally {global.document=saved.document;global.window=saved.window;}
}

test('hold boundary releases cannot click through to the newly visible Start button',()=>{
  for(const [releaseAt,timeoutFirst] of [[1999,false],[2000,false],[2000,true],[2001,true],[2300,true]]) {
    for(const clickShape of [{pointerType:'touch',detail:1},{pointerType:'touch',detail:0},{pointerId:undefined,pointerType:undefined,detail:1}]) {
      withStartButton(x=>{
        x.doc.emit('pointerdown',x.event({target:x.completeTarget}));x.hold.start();
        x.setTime(releaseAt);if(timeoutFirst)x.flush();
        // Model the browser retargeting release/click onto the replacement button.
        x.doc.emit('pointerup',x.event());x.hold.release();x.button.hidden=!!x.s.active;
        const click=x.event(clickShape);x.button.emit('click',click);
        assert.equal(x.starts(),0,`${releaseAt}/${timeoutFirst}`);assert.equal(click.prevented,true);
        assert.equal(x.s.records.length,releaseAt>=2000?1:0);
        if(releaseAt>=2000) {
          assert.equal(x.s.active,null);
          // A real new tap is accepted immediately; no arbitrary cooldown.
          x.tap();assert.equal(x.starts(),1);assert.ok(x.s.active);assert.equal(x.s.records.length,1);
        } else assert.ok(x.s.active);
      });
    }
  }
});

test('delayed release clicks, cancelled presses, and presses elsewhere cannot start a timer',()=>{
  withStartButton(x=>{
    x.hold.start();x.setTime(2000);x.flush();x.button.hidden=false;
    x.setTime(5000);x.button.emit('click',x.event());assert.equal(x.starts(),0);
    x.doc.emit('pointerdown',x.event({target:x.otherTarget}));x.doc.emit('pointerup',x.event());x.button.emit('click',x.event());assert.equal(x.starts(),0);
    x.doc.emit('pointerdown',x.event());x.doc.emit('pointercancel',x.event());x.button.emit('click',x.event());assert.equal(x.starts(),0);
    x.doc.emit('pointerdown',x.event());x.doc.emit('pointermove',x.event({clientX:130}));x.doc.emit('pointerup',x.event());x.button.emit('click',x.event());assert.equal(x.starts(),0);
    x.doc.emit('pointerdown',x.event());x.doc.emit('pointerup',x.event({pointerId:2}));x.button.emit('click',x.event());assert.equal(x.starts(),0);
    x.tap();assert.equal(x.starts(),1);
  });
});

test('Start retains keyboard and assistive activation while refusing duplicate starts',()=>{
  withStartButton(x=>{
    x.hold.start();x.setTime(2000);x.flush();x.button.hidden=false;
    x.button.emit('click',x.event({detail:0,pointerType:'',pointerId:-1}));assert.equal(x.starts(),1);
    x.button.emit('click',x.event({detail:0,pointerType:undefined,pointerId:undefined}));assert.equal(x.starts(),1);
  });
});
