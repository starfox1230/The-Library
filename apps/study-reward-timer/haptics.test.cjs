const test = require('node:test');
const assert = require('node:assert/strict');
const H = require('./haptics');

function clock() {
  let id=0;
  const queue = new Map();
  return { schedule(fn,at) { queue.set(++id,{fn,at}); return id; }, cancel(id) {queue.delete(id);}, flush() { [...queue].sort((a,b)=>a[1].at-b[1].at).forEach(([id,event])=>{if(queue.delete(id))event.fn();}); }, queue };
}
test('all presets have bounded timing, valid native parameters and vibration fallbacks', () => {
  assert.equal(H.patterns.length,22);
  assert.equal(new Set(H.patterns.map(p=>p.id)).size,22);
  for (const p of H.patterns) {
    assert.ok(H.duration(p)>0 && H.duration(p)<1500,p.id);
    const pattern=H.vibrationFor(p);
    assert.equal(pattern.length%2,1,p.id);
    assert.ok(pattern.length<100 && pattern.every(n=>Number.isInteger(n)&&n>=0&&n<=1500));
    assert.ok(p.events.every(e=>e.intensity>0&&e.intensity<=1&&e.sharpness>=0&&e.sharpness<=1));
    for(let i=1;i<p.events.length;i++) assert.ok(p.events[i].at>=p.events[i-1].at+(p.events[i-1].duration||0));
  }
});
test('HD crescendo increases actual intensity and ends with a sharp transient', () => {
  const c=clock(), calls=[];
  const player=H.createPlayer({haptic:v=>calls.push(v)},c.schedule,c.cancel);
  assert.equal(player.play('rise-snap',{strength:80}).mode,'hd');
  c.flush();
  assert.equal(calls.length,7);
  const events=calls.map(v=>v[0]);
  for(let i=1;i<6;i++) assert.ok(events[i].intensity>events[i-1].intensity);
  assert.equal(events[0].duration,90);
  assert.equal(events[6].duration,undefined);
  assert.equal(events[6].sharpness,.95);
});
test('native system success remains a system success at every strength', () => {
  const calls=[]; const player=H.createPlayer({haptic:v=>calls.push(v)});
  player.play('native-success',{strength:40});
  assert.deepEqual(calls,['success']);
});
test('standard mode uses one complete pattern and never calls native HD', () => {
  const calls=[]; const player=H.createPlayer({haptic:()=>assert.fail('HD should not run'),vibrate:v=>calls.push(v)});
  const result=player.play('classic',{engine:'standard'});
  assert.equal(result.mode,'standard');
  assert.deepEqual(calls,[0,[16,40,24]]);
});
test('Stop and starting another preset cancel the previous pending native events', () => {
  const c=clock(), calls=[];
  const player=H.createPlayer({haptic:v=>calls.push(v)},c.schedule,c.cancel);
  player.play('charge-release');
  assert.ok(c.queue.size>0);
  player.stop(); c.flush(); assert.equal(calls.length,1);
  player.play('charge-release');
  player.play('clean-click'); c.flush();
  assert.equal(calls.length,3);
  assert.equal(calls.at(-1),'rigid');
});
test('throwing or rejected HD bridge falls back without breaking the action', async () => {
  for(const haptic of [()=>{throw new Error('bridge unavailable');},()=>Promise.reject(new Error('rejected'))]) {
    const c=clock(), calls=[];
    const player=H.createPlayer({haptic,vibrate:v=>calls.push(v)},c.schedule,c.cancel);
    assert.doesNotThrow(()=>player.play('rise-snap'));
    await Promise.resolve(); c.flush();
    assert.equal(calls.filter(Array.isArray).length,1);
    assert.deepEqual(calls.at(-1),H.vibrationFor(H.get('rise-snap')));
  }
});
test('unsupported browsers and unknown stored pattern IDs are safe', () => {
  const player=H.createPlayer({});
  assert.equal(player.capability(),'none');
  assert.equal(player.play('unknown-old-id').mode,'none');
  assert.equal(H.get('unknown-old-id').id,H.DEFAULT);
});
