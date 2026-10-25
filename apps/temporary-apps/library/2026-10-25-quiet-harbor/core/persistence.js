const DB_NAME = "the-library-quiet-harbor";
const DB_VERSION = 1;

function request(requestObject) {
  return new Promise((resolve, reject) => {
    requestObject.onsuccess = () => resolve(requestObject.result);
    requestObject.onerror = () => reject(requestObject.error || new Error("Storage request failed"));
  });
}

export function openDatabase() {
  return new Promise((resolve, reject) => {
    if (!globalThis.indexedDB) return reject(new Error("Browser storage is unavailable."));
    const opening = indexedDB.open(DB_NAME, DB_VERSION);
    opening.onupgradeneeded = () => {
      const db = opening.result;
      if (!db.objectStoreNames.contains("meta")) db.createObjectStore("meta", { keyPath: "key" });
      if (!db.objectStoreNames.contains("runs")) db.createObjectStore("runs", { keyPath: "id" });
    };
    opening.onsuccess = () => resolve(opening.result);
    opening.onerror = () => reject(opening.error || new Error("Could not open saved progress."));
    opening.onblocked = () => reject(new Error("Another app tab is upgrading saved progress. Close it and retry."));
  });
}

export async function readState(db) {
  const tx = db.transaction(["meta", "runs"], "readonly");
  const done = transactionDone(tx);
  const metaP = request(tx.objectStore("meta").get("state"));
  const runsP = request(tx.objectStore("runs").getAll());
  const [meta, runs] = await Promise.all([metaP, runsP]);
  await done;
  return { meta: meta || null, runs: runs || [] };
}

function transactionDone(tx) {
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error("Could not save progress."));
    tx.onabort = () => reject(tx.error || new Error("Save was cancelled."));
  });
}

export function saveInitial(db, run) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["meta", "runs"], "readwrite");
    const meta = tx.objectStore("meta");
    meta.get("state").onsuccess = (event) => {
      const current = event.target.result;
      if (current?.activeRunId) return tx.abort();
      meta.put({ key: "state", schemaVersion: 1, revision: (current?.revision || 0) + 1, activeRunId: run.id, firstOpenedAtMs: run.startedAtMs, settings: { motion: "system", calmRestart: false }, camera: null, resetReceipt: null });
      tx.objectStore("runs").put(run);
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error("Could not save the new beginning."));
    tx.onabort = () => reject(new Error("A run already exists in another tab."));
  });
}

export function saveSettings(db, settings) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("meta", "readwrite");
    const store = tx.objectStore("meta");
    store.get("state").onsuccess = (event) => {
      const meta = event.target.result;
      if (!meta) return tx.abort();
      store.put({ ...meta, revision: meta.revision + 1, settings: { ...meta.settings, ...settings } });
    };
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error || new Error("Could not save settings."));
    tx.onabort = () => reject(new Error("No saved run is available."));
  });
}

export function saveCamera(db, camera) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("meta", "readwrite");
    const store = tx.objectStore("meta");
    store.get("state").onsuccess = (event) => {
      const meta = event.target.result;
      if (!meta) return tx.abort();
      store.put({ ...meta, camera: { ...camera, runId: meta.activeRunId } });
    };
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error || new Error("Could not save the view."));
    tx.onabort = () => resolve();
  });
}

export async function commitReset(db, expectedRunId, nextRun, committedAtMs) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["meta", "runs"], "readwrite");
    const metaStore = tx.objectStore("meta"), runStore = tx.objectStore("runs");
    let receipt;
    metaStore.get("state").onsuccess = (event) => {
      const meta = event.target.result;
      if (!meta || meta.activeRunId !== expectedRunId) return tx.abort();
      const oldRequest = runStore.get(expectedRunId);
      oldRequest.onsuccess = () => {
        const oldRun = oldRequest.result;
        if (!oldRun || oldRun.endedAtMs !== null) return tx.abort();
        const elapsed = Math.max(0, committedAtMs - oldRun.startedAtMs);
        runStore.put({ ...oldRun, endedAtMs: committedAtMs, elapsedAtEndMs: elapsed, maxObservedElapsedMs: Math.max(oldRun.maxObservedElapsedMs || 0, elapsed) });
        runStore.add(nextRun);
        receipt = { oldRunId: oldRun.id, newRunId: nextRun.id, committedAtMs, undoUntilMs: committedAtMs + 10_000, oldRun };
        metaStore.put({ ...meta, revision: meta.revision + 1, activeRunId: nextRun.id, camera: null, resetReceipt: receipt });
      };
    };
    tx.oncomplete = () => resolve(receipt);
    tx.onerror = () => reject(tx.error || new Error("Could not save the new beginning."));
    tx.onabort = () => reject(new Error("Saved progress changed in another tab. It has been refreshed."));
  });
}

export function undoReset(db, expectedRunId, now = Date.now()) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["meta", "runs"], "readwrite");
    const metaStore = tx.objectStore("meta"), runStore = tx.objectStore("runs");
    let restored;
    metaStore.get("state").onsuccess = (event) => {
      const meta = event.target.result, receipt = meta?.resetReceipt;
      if (!receipt || meta.activeRunId !== expectedRunId || receipt.newRunId !== expectedRunId || now > receipt.undoUntilMs) return tx.abort();
      const oldRun = receipt.oldRun || runStore.get(receipt.oldRunId).result;
      const activeRequest = runStore.get(expectedRunId);
      activeRequest.onsuccess = () => {
        const active = activeRequest.result;
        if (!oldRun || !active) return tx.abort();
        restored = { ...oldRun, endedAtMs: null, elapsedAtEndMs: null, startedAtMs: oldRun.startedAtMs, maxObservedElapsedMs: Math.max(oldRun.maxObservedElapsedMs || 0, now - oldRun.startedAtMs) };
        runStore.put(restored);
        runStore.delete(expectedRunId);
        metaStore.put({ ...meta, revision: meta.revision + 1, activeRunId: restored.id, resetReceipt: null, camera: null });
      };
    };
    tx.oncomplete = () => resolve(restored);
    tx.onerror = () => reject(tx.error || new Error("Could not undo this restart."));
    tx.onabort = () => reject(new Error("Undo has expired or progress changed in another tab."));
  });
}

export function checkpoint(db, runId, now = Date.now()) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("runs", "readwrite");
    const store = tx.objectStore("runs");
    store.get(runId).onsuccess = (event) => {
      const run = event.target.result;
      if (!run || run.endedAtMs !== null) return;
      store.put({ ...run, lastObservedAtMs: now, maxObservedElapsedMs: Math.max(run.maxObservedElapsedMs || 0, now - run.startedAtMs) });
    };
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error || new Error("Could not save the time checkpoint."));
  });
}

export function rebaseRunClock(db, runId, now, preservedElapsedMs) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction("runs", "readwrite");
    const store = tx.objectStore("runs");
    store.get(runId).onsuccess = (event) => {
      const run = event.target.result;
      if (!run || run.endedAtMs !== null) return tx.abort();
      store.put({ ...run, originalStartedAtMs: run.originalStartedAtMs || run.startedAtMs, startedAtMs: now - preservedElapsedMs, maxObservedElapsedMs: preservedElapsedMs, lastObservedAtMs: now });
    };
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error || new Error("Could not update the device time."));
    tx.onabort = () => reject(new Error("The saved run changed before the device time could be updated."));
  });
}

export function replaceBackup(db, records) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(["meta", "runs"], "readwrite");
    const metaStore = tx.objectStore("meta"), runStore = tx.objectStore("runs");
    runStore.clear();
    for (const run of records.runs) runStore.put(run);
    metaStore.put({ ...records.meta, key: "state", revision: (records.meta.revision || 0) + 1, schemaVersion: 1 });
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error || new Error("Could not import this backup."));
  });
}
