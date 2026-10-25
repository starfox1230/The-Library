const LIMIT = 5 * 1024 * 1024;
const SEED = /^[0-9a-f]{32}$/i;

export function makeBackup(state, exportedAtMs = Date.now()) {
  return { app: "Quiet Harbor", format: 1, exportedAtMs, meta: { ...state.meta, resetReceipt: null }, runs: state.runs };
}

export function validateBackup(value) {
  if (!value || typeof value !== "object" || value.app !== "Quiet Harbor") throw new Error("This file is not a Quiet Harbor backup.");
  if (value.format !== 1) throw new Error("This backup version is not supported by this copy of Quiet Harbor.");
  const meta = value.meta, runs = value.runs;
  if (!meta || meta.schemaVersion !== 1 || !Number.isInteger(meta.revision) || !Array.isArray(runs) || runs.length > 10_000) throw new Error("The backup data is incomplete or too large.");
  const ids = new Set();
  for (const run of runs) {
    if (!run || typeof run.id !== "string" || run.id.length > 80 || ids.has(run.id) || !SEED.test(run.seed) || run.generatorVersion !== 1 || run.growthVersion !== 1) throw new Error("The backup contains an unknown or invalid run.");
    ids.add(run.id);
    for (const key of ["startedAtMs", "originalStartedAtMs", "maxObservedElapsedMs"]) if (!Number.isFinite(run[key]) || run[key] < 0) throw new Error("The backup contains invalid times.");
    if (run.endedAtMs !== null && (!Number.isFinite(run.endedAtMs) || run.endedAtMs < run.startedAtMs)) throw new Error("The backup contains an invalid end time.");
    if (run.elapsedAtEndMs !== null && (!Number.isFinite(run.elapsedAtEndMs) || run.elapsedAtEndMs < 0)) throw new Error("The backup contains an invalid duration.");
  }
  if (typeof meta.activeRunId !== "string" || !ids.has(meta.activeRunId)) throw new Error("The backup does not identify its current run.");
  const active = runs.find((run) => run.id === meta.activeRunId);
  if (active.endedAtMs !== null) throw new Error("The active run in the backup has already ended.");
  const settings = meta.settings || {};
  const safeMeta = { ...meta, key: "state", resetReceipt: null, settings: { motion: ["system", "full", "reduced"].includes(settings.motion) ? settings.motion : "system", calmRestart: Boolean(settings.calmRestart) } };
  return { meta: safeMeta, runs };
}

export async function parseBackupFile(file) {
  if (!file || file.size > LIMIT) throw new Error("Choose a backup smaller than 5 MB.");
  let parsed;
  try { parsed = JSON.parse(await file.text()); } catch { throw new Error("This file is not valid JSON."); }
  return validateBackup(parsed);
}
