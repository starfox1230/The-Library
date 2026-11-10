const {test}=require('node:test');
const assert=require('node:assert/strict');
const E=require('./engine.js');
const A=require('./alerts.js');
test('legacy backups adopt quiet alert defaults and preserve reward snapshots',()=>{
 const s=E.fresh();E.start(s,100000);delete s.settings.alerts;for(const key of ['minute','warning','alarm'])delete s.settings.hapticEvents[key];
 const restored=E.validate(s);assert.deepEqual(restored.settings.alerts,E.alertDefaults());assert.deepEqual(restored.active,s.active);
 restored.settings.alerts.audioSeconds=0;assert.throws(()=>E.validate(restored),/timer alerts/);
});
test('only fresh running boundaries announce; no backlog on resume, reload or sleep',()=>{
 const before={id:'a',running:true,spent:59900,left:60100,at:1000};
 const after={id:'a',running:true,spent:60100,left:59900};
 assert.deepEqual(A.crossing(before,after,1250),{minute:true,remaining:true,deadline:false});
 assert.deepEqual(A.crossing(before,after,4000),{});
 assert.deepEqual(A.crossing({...before,running:false},after,1250),{});
 assert.deepEqual(A.crossing(null,after,1250),{});
 assert.deepEqual(A.crossing(before,{...after,id:'b'},1250),{});
});
test('deadline rings once and each alarm stops at its independent duration',()=>{
 let now=100000,plays=0,stops=0;const bell={play(){plays++;return Promise.resolve();},pause(){stops++;}};
 const s=E.fresh();s.types[0].targetMs=1000;E.start(s,now);
 Object.assign(s.settings.alerts,{audioAlarm:true,vibrationAlarm:true,audioSeconds:5,vibrationSeconds:30});
 let pulses=0;const h={createPlayer:()=>({play:()=>{pulses++;return {mode:'hd'};},stop(){}}),get:()=>({}),duration:()=>500};
 const a=A.create({haptics:h,navigator:{},getState:()=>s,elapsed:E.elapsed,clock:()=>now,env:{Audio:function(){return bell;}}});
 a.tick();now+=1000;a.tick();assert.equal(plays,1);assert.equal(pulses,1);
 now+=5000;a.tick();assert.ok(stops);const atFive=pulses;
 now+=2000;a.tick();assert.ok(pulses>atFive);
 now=131000;a.tick();const end=pulses;now+=2000;a.tick();assert.equal(pulses,end);assert.equal(plays,1);
});
test('pause and completion cancel active alerts without saving a case',()=>{
 let now=100000,stops=0;const s=E.fresh();s.types[0].targetMs=1000;E.start(s,now);s.settings.alerts.vibrationAlarm=true;
 const a=A.create({haptics:{createPlayer:()=>({play:()=>({}),stop(){stops++;}}),get:()=>({}),duration:()=>500},navigator:{},getState:()=>s,elapsed:E.elapsed,clock:()=>now,env:{}});
 a.tick();now+=1000;a.tick();E.pause(s,now);a.tick();assert.ok(stops);assert.equal(s.records.length,0);
});
