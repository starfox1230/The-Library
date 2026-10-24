const test = require('node:test');
const assert = require('node:assert/strict');
const E = require('./engine.js');

test('default MR reward is $2; all other modalities default to $0', () => {
  const s = E.fresh();
  assert.equal(s.settings.goalCents, 90000);
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
