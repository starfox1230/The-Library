const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('./engine.js');

test('CT chest / abdomen / pelvis is visible by default with an 18 minute target', () => {
  const s = E.fresh();
  assert.equal(s.settings.studySort, 'recent');
  const cap = E.sortTypes(s).find(t => t.id === 'ct-body-2');
  assert.equal(cap.name, 'Chest / abdomen / pelvis');
  assert.equal(cap.modality, 'CT');
  assert.equal(cap.targetMs, 18 * 60000);
  assert.equal(cap.rewardCents, 0);
});

test('selections reorder immediately, deduplicate and survive backup without starting a timer', () => {
  const s = E.fresh();
  E.selectType(s, 'ct-body-2');
  E.selectType(s, 'mr-body-4');
  E.selectType(s, 'ct-body-2');
  const restored = E.validate(E.clone(s));
  assert.deepEqual(restored.recentTypeIds, ['ct-body-2', 'mr-body-4', 'mr-body-0']);
  assert.deepEqual(E.sortTypes(restored).slice(0, 3).map(t => t.id), restored.recentTypeIds);
  assert.equal(restored.active, null);
  assert.deepEqual(restored.records, []);
  E.start(restored, 1000);
  assert.equal(E.selectType(restored, 'mr-body-4'), false);
  assert.equal(restored.selectedTypeId, 'ct-body-2');
  assert.throws(() => E.selectType(s, 'missing'));
});

test('favorites first retains every study; other orders do not change catalogue or recency', () => {
  const s = E.fresh();
  E.selectType(s, 'ct-body-2');
  const before = E.clone(s);
  s.settings.studySort = 'favorites';
  const ordered = E.sortTypes(s);
  assert.equal(ordered.length, s.types.length);
  const firstNonfavorite = ordered.findIndex(t => !t.favorite);
  assert.ok(firstNonfavorite > 0);
  assert.ok(ordered.slice(firstNonfavorite).every(t => !t.favorite));
  assert.equal(ordered[firstNonfavorite].id, 'ct-body-2');
  assert.ok(E.sortTypes(s, 'favorites-only').every(t => t.favorite));
  const alphabetic = E.sortTypes(s, 'alphabetical');
  assert.ok(alphabetic.every((t, i) => !i || alphabetic[i - 1].name.localeCompare(t.name) <= 0));
  const grouped = E.sortTypes(s, 'modality');
  const headings = grouped.map(t => `${t.modality} · ${t.group}`).filter((h, i, all) => !i || h !== all[i - 1]);
  assert.equal(new Set(headings).size, headings.length);
  assert.deepEqual(s.types, before.types);
  assert.deepEqual(s.recentTypeIds, before.recentTypeIds);
  assert.equal(E.validate(E.clone(s)).settings.studySort, 'favorites');
});

test('older backups migrate order and missing CT CAP without changing active or past cases', () => {
  const s = E.fresh();
  E.selectType(s, 'mr-body-4'); E.start(s, 1000); E.finish(s, 2000);
  E.selectType(s, 'mr-body-1'); E.start(s, 3000);
  delete s.settings.studySort; delete s.recentTypeIds;
  s.types = s.types.filter(t => t.id !== 'ct-body-2');
  const old = E.clone(s);
  const restored = E.validate(s);
  assert.equal(restored.settings.studySort, 'recent');
  assert.deepEqual(restored.recentTypeIds, ['mr-body-1', 'mr-body-4']);
  assert.equal(restored.types.find(t => t.id === 'ct-body-2').targetMs, 1080000);
  assert.deepEqual(restored.active, old.active);
  assert.deepEqual(restored.records, old.records);
  assert.deepEqual(s, old);
  restored.types.find(t => t.id === 'ct-body-2').targetMs = 1200000;
  assert.equal(E.validate(restored).types.find(t => t.id === 'ct-body-2').targetMs, 1200000);
  assert.deepEqual(E.validate(restored), restored);
});

test('invalid sort and recency backups are rejected without changing input', () => {
  for (const change of [
    s => { s.settings.studySort = 'unknown'; },
    s => { s.recentTypeIds = null; },
    s => { s.recentTypeIds = ['ct-body-2', 'ct-body-2']; },
    s => { s.recentTypeIds = ['missing']; }
  ]) {
    const s = E.fresh(); change(s);
    const before = E.clone(s);
    assert.throws(() => E.validate(s), /study order|recently selected/);
    assert.deepEqual(s, before);
  }
});

test('default MR reward is $2; all other modalities default to $0', () => {
  const s = E.fresh();
  assert.equal(s.settings.goalCents, 90000);
  assert.equal(s.settings.holdToComplete, true);
  assert.ok(s.types.length > 90);
  for (const t of s.types) {
    assert.equal(t.targetMs, 18 * 60000);
    assert.equal(t.rewardCents, t.modality === 'MR' ? 200 : 0);
  }
  assert.deepEqual(E.validate(s), s);
});
test('exact deadline pays; one millisecond beyond earns zero', () => {
  for (const [elapsed, expected] of [[1080000, 200], [1080001, 0]]) {
    const s = E.fresh(); E.start(s, 1000);
    const r = E.finish(s, 1000 + elapsed);
    assert.equal(E.payout(r), expected);
    assert.equal(E.total(s.records), expected);
  }
});
test('pause excludes interruption; serialized running timer includes screen-lock time', () => {
  const s = E.fresh(); E.start(s, 1000); E.pause(s, 61000);
  assert.equal(E.elapsed(s.active, 999999), 60000);
  const reloaded = E.validate(JSON.parse(JSON.stringify(s)));
  E.resume(reloaded, 1000000);
  const locked = E.validate(JSON.parse(JSON.stringify(reloaded)));
  assert.equal(E.elapsed(locked.active, 1060000), 120000);
  assert.equal(E.finish(locked, 1060000).elapsedMs, 120000);
});
test('active target and reward are snapshots, settings never rewrite past earnings', () => {
  const s = E.fresh(); E.start(s, 1000);
  s.types[0].rewardCents = 9999; s.types[0].targetMs = 6000;
  const r = E.finish(s, 61000);
  assert.equal(r.rewardCents, 200); assert.equal(r.targetMs, 1080000);
  assert.equal(E.total(s.records), 200);
});
test('double completion cannot award twice and two active cases are prevented', () => {
  const s = E.fresh(); E.start(s, 1000);
  assert.throws(() => E.start(s, 2000));
  E.finish(s, 3000); assert.equal(E.finish(s, 3000), null);
  assert.equal(s.records.length, 1); assert.equal(E.total(s.records), 200);
});
test('history edits and deletes recalculate fund without cached totals', () => {
  const s = E.fresh(); E.start(s, 1000); E.finish(s, 61000);
  s.records[0].elapsedMs = 1080001; assert.equal(E.total(s.records), 0);
  s.records[0].elapsedMs = 1080000; assert.equal(E.total(s.records), 200);
  s.records.pop(); assert.equal(E.total(s.records), 0);
});
test('restore rejects invalid money, timing, duplicate IDs and active/completed duplicates', () => {
  const s = E.fresh(); E.start(s, 1000); E.finish(s, 61000);
  for (const change of [
    s => { s.records[0].rewardCents = 2.5; },
    s => { s.records[0].elapsedMs = -1; },
    s => { s.records[0].completedAt = 0; },
    s => { s.records.push(s.records[0]); },
    s => { s.settings.goalCents = 0; },
    s => { s.types[0].targetMs = Infinity; },
    s => { s.active = {...s.records[0], runningSince: null}; }
  ]) { const copy = E.clone(s); change(copy); assert.throws(() => E.validate(copy)); }
});
test('CSV includes precise timestamps, outcomes and safe quoted custom names', () => {
  const s = E.fresh(); s.types[0].name = '=formula,"test"';
  E.start(s, 1000); E.finish(s, 61000);
  const csv = E.csv(s.records);
  assert.ok(csv.includes('1970-01-01T00:00:01.000Z'));
  assert.ok(csv.includes('"\'=formula,""test"""'));
  assert.ok(csv.includes('"yes","2.00"'));
});
test('unpaid modalities still save timing and within-target status', () => {
  const s = E.fresh(); s.selectedTypeId = s.types.find(t => t.modality === 'CT').id;
  E.start(s, 1000); const r = E.finish(s, 61000);
  assert.equal(r.modality, 'CT'); assert.equal(E.payout(r), 0);
  assert.equal(s.records.length, 1);
});
test('older backups gain an empty future list without changing earnings or active timer', () => {
  const old = E.fresh();
  E.start(old, 1000); E.finish(old, 61000); E.start(old, 62000);
  delete old.futureGoals;
  const restored = E.validate(old);
  assert.deepEqual(restored.futureGoals, []);
  assert.deepEqual(restored.records, old.records);
  assert.deepEqual(restored.active, old.active);
  assert.equal(E.total(restored.records), 200);
  assert.equal(old.futureGoals, undefined);
});
test('future ideas with or without prices survive a full backup round trip', () => {
  const s = E.fresh(); E.start(s, 1000); E.finish(s, 61000);
  s.futureGoals = [{ id: 'next-1', name: 'Headphones', costCents: 24999 }, { id: 'next-2', name: 'A weekend away', costCents: null }];
  const restored = E.validate(JSON.parse(JSON.stringify(s)));
  assert.deepEqual(restored, s);
  assert.equal(restored.settings.goalCents, 90000);
  assert.equal(E.total(restored.records), 200);
});
test('future list validation rejects bad amounts, duplicate ids and malformed lists', () => {
  for (const goals of [null, {}, [{ id: 'x', name: 'Idea', costCents: -100 }], [{ id: 'x', name: 'Idea', costCents: 1.5 }], [{ id: 'x', name: '', costCents: null }], [{ id: 'x', name: 'One', costCents: null }, { id: 'x', name: 'Two', costCents: null }]]) {
    const s = E.fresh(); s.futureGoals = goals;
    assert.throws(() => E.validate(s), /future goals/);
  }
});
test('legacy haptic settings migrate without changing the ledger; choices survive restore', () => {
  const old=E.fresh(); E.start(old,1000); E.finish(old,61000);
  delete old.settings.hapticPattern; delete old.settings.hapticStrength; delete old.settings.hapticEngine;
  const migrated=E.validate(old);
  assert.equal(migrated.settings.hapticPattern,'rise-snap');
  assert.equal(migrated.settings.hapticStrength,80);
  assert.equal(E.total(migrated.records),200);
  migrated.settings.hapticPattern='coin-drop'; migrated.settings.hapticStrength=40; migrated.settings.hapticEngine='standard';
  assert.deepEqual(E.validate(JSON.parse(JSON.stringify(migrated))),migrated);
  for(const invalid of [{hapticStrength:200},{hapticEngine:'unknown'},{hapticPattern:null}]) {
    const copy=E.clone(migrated); Object.assign(copy.settings,invalid); assert.throws(()=>E.validate(copy),/haptic/);
  }
});

test('normal pause cannot complete, but holding freezes without being a normal pause',()=>{
  const s=E.fresh();E.start(s,1000);E.pause(s,2000);
  assert.equal(E.beginHold(s,3000),false);assert.equal(E.finish(s,4000),null);assert.equal(s.records.length,0);
  E.resume(s,5000);assert.equal(E.beginHold(s,6000),true);assert.equal(s.active.holding,true);
  E.pause(s,7000);E.resume(s,8000);assert.equal(s.active.runningSince,null);
  assert.equal(E.elapsed(s.active,9000),2000);
  const r=E.finish(s,9000);assert.equal(r.elapsedMs,2000);assert.equal(r.holding,undefined);
});
test('completion hold protects the exact deadline, but never rescues an already late case',()=>{
  for(const [offset,reward] of [[-1,200],[0,200],[1,0]]) {
    const s=E.fresh();E.start(s,1000);const contact=1000+s.active.targetMs+offset;
    assert.equal(E.beginHold(s,contact),true);
    const restored=E.validate(JSON.parse(JSON.stringify(s)));
    const r=E.finish(restored,contact+1500);assert.equal(E.payout(r),reward);assert.equal(r.elapsedMs,r.targetMs+offset);
    assert.equal(E.finish(restored,contact+2000),null);
  }
});
test('releasing holds repeatedly excludes only hold intervals and resumes exactly',()=>{
  const s=E.fresh();E.start(s,1000);E.beginHold(s,1500);E.cancelHold(s,1900);
  assert.equal(E.elapsed(s.active,2000),600);E.beginHold(s,2100);E.cancelHold(s,2900);
  assert.equal(E.finish(s,3000).elapsedMs,800);
});
test('reload or transfer recovery resumes an orphaned hold at its frozen time',()=>{
  const s=E.fresh();E.start(s,1000);E.beginHold(s,2000);
  const restored=E.validate(JSON.parse(JSON.stringify(s)));E.cancelHold(restored,500000);
  assert.equal(E.elapsed(restored.active,501000),2000);assert.equal(restored.active.holding,undefined);
});
test('changing duration discards the session and updates only that study type default',()=>{
  const s=E.fresh();E.start(s,1000);E.beginHold(s,2000);const oldId=s.active.id;
  E.restartDuration(s,25*60000,3000);
  assert.equal(s.records.length,0);assert.notEqual(s.active.id,oldId);assert.equal(E.elapsed(s.active,3000),0);
  assert.equal(s.active.holding,undefined);assert.equal(s.types[0].targetMs,25*60000);assert.equal(s.types[1].targetMs,18*60000);
  E.pause(s,4000);E.restartDuration(s,5*60000,5000);assert.equal(s.active.runningSince,5000);
  assert.throws(()=>E.restartDuration(s,0));
});
test('old backups migrate all action controls without changing their previous success choice',()=>{
  const old=E.fresh();delete old.settings.hapticEvents;delete old.settings.holdToComplete;delete old.settings.holdDefaultVersion;delete old.customHaptics;
  old.settings.hapticPattern='coin-drop';old.settings.hapticStrength=40;old.settings.haptics=false;
  const s=E.validate(old);assert.equal(s.settings.hapticEvents.complete.pattern,'coin-drop');assert.equal(s.settings.hapticEvents.complete.strength,40);
  assert.equal(s.settings.haptics,false);assert.equal(s.settings.holdToComplete,true);assert.deepEqual(s.customHaptics,[]);
});
test('action choices and custom curves round trip with the ledger and reject malformed data',()=>{
  const s=E.fresh();E.start(s,1000);E.finish(s,2000);
  const p={id:'custom-one',name:'My lift',durationMs:1000,snap:true,points:[{at:0,intensity:.1,sharpness:0},{at:1000,intensity:1,sharpness:1}]};
  s.customHaptics=[p];s.settings.hapticEvents.hold.pattern=p.id;s.settings.hapticEvents.pause.enabled=false;s.settings.holdToComplete=true;
  assert.deepEqual(E.validate(JSON.parse(JSON.stringify(s))),s);
  for(const change of [s=>s.customHaptics[0].points[1].intensity=1.5,s=>s.customHaptics[0].points[1].at=200,s=>s.customHaptics.push(p),s=>s.settings.hapticEvents.start.strength=500,s=>s.settings.holdToComplete='yes',s=>s.active={...s.records[0],id:'new',runningSince:3000,holding:true}]) {
    const copy=E.clone(s);change(copy);assert.throws(()=>E.validate(copy));
  }
});

test('the hold default applies once to existing timers without changing their data',()=>{
  const old=E.fresh();E.start(old,1000);E.finish(old,2000);E.start(old,3000);
  old.settings.holdToComplete=false;delete old.settings.holdDefaultVersion;
  const before=E.clone(old), migrated=E.validate(old);
  assert.equal(migrated.settings.holdToComplete,true);assert.equal(migrated.settings.holdDefaultVersion,1);
  assert.deepEqual(migrated.records,before.records);assert.deepEqual(migrated.active,before.active);
  assert.deepEqual(migrated.types,before.types);assert.deepEqual(migrated.settings.hapticEvents,before.settings.hapticEvents);
  assert.deepEqual(old,before);
  migrated.settings.holdToComplete=false;
  const restored=E.validate(JSON.parse(JSON.stringify(migrated)));
  assert.equal(restored.settings.holdToComplete,false);assert.deepEqual(restored,migrated);
  restored.settings.holdDefaultVersion=2;assert.throws(()=>E.validate(restored),/completion preferences/);
});
