import test from "node:test";
import assert from "node:assert/strict";
import { makeBackup, validateBackup } from "../core/backup.js";

const run = { id: "run-1", seed: "0123456789abcdef0123456789abcdef", generatorVersion: 1, growthVersion: 1, startedAtMs: 100, originalStartedAtMs: 100, endedAtMs: null, elapsedAtEndMs: null, maxObservedElapsedMs: 0 };
const state = { meta: { key: "state", schemaVersion: 1, revision: 1, activeRunId: run.id, settings: { motion: "reduced", calmRestart: true } }, runs: [run] };

test("backup export round-trips valid local state and strips undo receipt", () => {
  const data = makeBackup({ ...state, meta: { ...state.meta, resetReceipt: { oldRun: {} } } }, 500);
  assert.equal(data.exportedAtMs, 500);
  assert.equal(data.meta.resetReceipt, null);
  assert.equal(validateBackup(data).meta.settings.motion, "reduced");
});

test("backup rejects an unknown active run, duplicate ids, and unsupported versions", () => {
  assert.throws(() => validateBackup({ ...makeBackup(state), meta: { ...state.meta, activeRunId: "missing" } }), /current run/);
  assert.throws(() => validateBackup({ ...makeBackup(state), runs: [run, run] }), /invalid run/);
  assert.throws(() => validateBackup({ ...makeBackup(state), format: 99 }), /not supported/);
});
