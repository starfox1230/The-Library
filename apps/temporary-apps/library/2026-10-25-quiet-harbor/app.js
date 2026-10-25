import { formatDuration, longDurationLabel, elapsedForRun } from "./core/time.js";
import { seedHex } from "./core/random-v1.js";
import { GROWTH_VERSION, growthAt } from "./core/growth-v1.js";
import { GENERATOR_VERSION, worldFor } from "./core/world-v1.js";
import { openDatabase, readState, saveInitial, saveSettings, saveCamera, commitReset, undoReset, checkpoint, replaceBackup, rebaseRunClock } from "./core/persistence.js";
import { makeBackup, parseBackupFile } from "./core/backup.js";
import { ClockMonitor } from "./core/clock.js";
import { HoldController } from "./core/reset-controller.js";
import { IslandRenderer } from "./scene/renderer.js";

const $ = (id) => document.getElementById(id);
const els = {
  timer: $("timer"), best: $("bestDuration"), stage: $("worldStage"), summary: $("worldSummary"),
  label: $("holdLabel"), action: $("holdAction"), fill: $("holdFill"), help: $("holdHelp"),
  encouragement: $("encouragement"), storage: $("storageNotice"), status: $("statusMessage"), undo: $("undoReset"),
  sceneMount: $("sceneMount"), fallback: $("sceneFallback"), frame: $("worldFrame"),
  settings: $("settingsDialog"), resetDialog: $("resetDialog"), buildingDialog: $("buildingDialog"),
  history: $("historyList"), historyIntro: $("historyIntro"), motion: $("motionSelect"), calm: $("calmRestart"),
  storagePersistence: $("storagePersistence"), export: $("exportBackup"), importButton: $("importBackupButton"),
  importFile: $("importBackupFile"), backupStatus: $("backupStatus"), wave: $("waveCurtain"),
};

let db = null;
let state = { meta: null, runs: [] };
let ephemeral = false;
let renderer = null;
let hold = null;
let timerHandle = 0;
let sceneReady = false;
let busy = false;
let anomalyElapsed = null;
let lastShownSecond = -1;
let lastWorldKey = "";
let lastCheckpoint = 0;
let cameraSaveHandle = 0;
let undoHandle = 0;
let sceneStartedAt = Date.now();
let clockMonitor;
let channel = null;

function activeRun() { return state.runs.find((run) => run.id === state.meta?.activeRunId) || null; }
function currentElapsed(run = activeRun(), now = Date.now()) { return anomalyElapsed !== null ? anomalyElapsed : elapsedForRun(run, now); }
function newRun(now = Date.now()) {
  return { id: crypto.randomUUID?.() || `run-${seedHex()}`, seed: seedHex(), generatorVersion: GENERATOR_VERSION, growthVersion: GROWTH_VERSION, startedAtMs: now, originalStartedAtMs: now, endedAtMs: null, elapsedAtEndMs: null, maxObservedElapsedMs: 0, lastObservedAtMs: now };
}
function showStatus(message, kind = "good") {
  els.status.textContent = message;
  els.status.classList.toggle("error", kind === "error");
  els.status.hidden = false;
  if (kind === "good") window.setTimeout(() => { if (!busy) els.status.hidden = true; }, 5200);
}
function setStorageNotice(message) {
  els.storage.textContent = message;
  els.storage.hidden = !message;
}

async function initialise() {
  try {
    db = await openDatabase();
    state = await readState(db);
    try {
      const persistent = await navigator.storage?.persist?.();
      const already = await navigator.storage?.persisted?.();
      els.storagePersistence.textContent = (persistent || already)
        ? "This browser has granted persistent storage. Keep a backup for extra peace of mind."
        : "This browser may clear unused local data. Export a backup to keep a copy elsewhere.";
    } catch { els.storagePersistence.textContent = "Progress lives in this browser. Export a backup to keep a copy elsewhere."; }
  } catch (error) {
    ephemeral = true;
    setStorageNotice(`Progress can't be saved in this browser right now. You can use a temporary session, but a refresh will clear it. ${error?.message || ""}`.trim());
    els.storagePersistence.textContent = "Saved progress is unavailable in this browser.";
  }
  if (state.meta?.settings) {
    els.motion.value = state.meta.settings.motion || "system";
    els.calm.checked = Boolean(state.meta.settings.calmRestart);
  }
  attachEvents();
  render();
  void initScene().then(() => render(true));
  hold?.setEnabled(Boolean(activeRun()));
  clockMonitor = new ClockMonitor({ onAnomaly: (elapsed) => showClockAnomaly(elapsed) });
  if (activeRun() && Date.now() - activeRun().startedAtMs < (activeRun().maxObservedElapsedMs || 0) - 5_000) showClockAnomaly(activeRun().maxObservedElapsedMs);
  tick();
  timerHandle = window.setInterval(tick, 250);
  checkpointAtLifecycle();
  registerServiceWorker();
  setupUpdates();
  document.addEventListener("visibilitychange", checkpointAtLifecycle);
  window.addEventListener("pagehide", checkpointAtLifecycle);
  window.addEventListener("pageshow", () => { tick(); refreshFromStorage(); });
  window.addEventListener("focus", () => { tick(); refreshFromStorage(); });
  if ("BroadcastChannel" in window) {
    channel = new BroadcastChannel("quiet-harbor-state-v1");
    channel.onmessage = () => refreshFromStorage();
  }
}

async function initScene() {
  try {
    renderer = new IslandRenderer(els.sceneMount);
    await renderer.init(state.meta?.camera);
    renderer.onCameraChange = (camera) => {
      if (!db || ephemeral) return;
      window.clearTimeout(cameraSaveHandle);
      cameraSaveHandle = window.setTimeout(() => saveCamera(db, camera).catch(() => {}), 700);
    };
    renderer.onSelectBuilding = (building) => {
      const times = Math.max(0, Math.round(building.birthAtSeconds));
      $("buildingTitle").textContent = building.kind === "civic" ? "A shared little place" : "A home by the shore";
      $("buildingDetail").textContent = `${building.kind === "civic" ? "A place for neighbors" : "A cottage for a neighbor"} · appeared after ${formatDuration(times * 1000)}.`;
      if (!els.buildingDialog.open) els.buildingDialog.showModal();
    };
    sceneReady = true;
  } catch (error) {
    console.warn("Quiet Harbor's illustrated scene is unavailable; the timer remains available.", error);
    els.frame.dataset.sceneError = "true";
    els.fallback.hidden = false;
  }
}

function attachEvents() {
  hold = new HoldController(els.action, { onProgress: updateHoldFill, onComplete: () => void recordEpisode() });
  hold.onAccessibleActivation = () => {
    if (activeRun()) els.resetDialog.showModal(); else void startRun();
  };
  els.action.addEventListener("click", (event) => {
    if (!activeRun() && event.detail !== 0) void startRun();
  });
  $("openSettings").addEventListener("click", openSettings);
  $("closeSettings").addEventListener("click", () => els.settings.close());
  $("recenter").addEventListener("click", () => renderer?.recenter());
  $("zoomOut").addEventListener("click", () => renderer?.setZoom((renderer.camera?.zoom || .77) - .14));
  $("zoomIn").addEventListener("click", () => renderer?.setZoom((renderer.camera?.zoom || .77) + .14));
  $("exploreHint").addEventListener("click", () => { showStatus("Drag to wander · use + and − to change your view. The village keeps growing."); els.frame.focus?.(); });
  $("privacyShortcut").addEventListener("click", openSettings);
  $("assistReset").addEventListener("click", () => els.resetDialog.showModal());
  $("cancelReset").addEventListener("click", (event) => { event.preventDefault(); els.resetDialog.close(); });
  $("confirmReset").addEventListener("click", (event) => { event.preventDefault(); els.resetDialog.close(); void recordEpisode(); });
  els.resetDialog.addEventListener("click", (event) => { if (event.target === els.resetDialog) els.resetDialog.close(); });
  els.settings.addEventListener("click", (event) => { if (event.target === els.settings) els.settings.close(); });
  els.undo.addEventListener("click", () => void undoAccidentalReset());
  els.motion.addEventListener("change", () => void updateSetting({ motion: els.motion.value }));
  els.calm.addEventListener("change", () => void updateSetting({ calmRestart: els.calm.checked }));
  els.export.addEventListener("click", () => void exportData());
  els.importButton.addEventListener("click", () => els.importFile.click());
  els.importFile.addEventListener("change", () => void importData(els.importFile.files?.[0]));
  window.matchMedia?.("(prefers-reduced-motion: reduce)").addEventListener?.("change", () => document.body.classList.toggle("reduce-motion", reducedMotion()));
}

function updateHoldFill(progress) {
  els.fill.style.width = `${Math.round(progress * 100)}%`;
  els.label.textContent = progress > 0 && progress < 1 ? "Keep holding…" : activeRun() ? "I picked — begin again" : "Begin growing";
  els.help.textContent = progress > 0 && progress < 1 ? "release to keep your current run" : activeRun() ? "press and hold for one second" : "one tap begins your first little world";
}

async function startRun() {
  if (busy || activeRun()) return;
  const run = newRun();
  try {
    if (db && !ephemeral) await saveInitial(db, run);
    state.meta = { key: "state", schemaVersion: 1, revision: (state.meta?.revision || 0) + 1, activeRunId: run.id, firstOpenedAtMs: state.meta?.firstOpenedAtMs || run.startedAtMs, settings: state.meta?.settings || { motion: "system", calmRestart: false }, camera: null, resetReceipt: null };
    state.runs.push(run);
    if (ephemeral) showStatus("Your temporary run has begun. Keep this page open to keep this session.");
    else showStatus("Your seed has a place to begin.");
    els.encouragement.textContent = "Your next seed is already growing.";
    hold.setEnabled(true); render(true); announceChange();
  } catch (error) {
    await refreshFromStorage();
    showStatus(error.message, "error");
  }
}

async function recordEpisode() {
  if (busy) return;
  const current = activeRun();
  if (!current) { await startRun(); return; }
  busy = true; hold.setEnabled(false); els.action.disabled = true;
  const committedAt = Date.now(), next = newRun(committedAt);
  try {
    if (db && !ephemeral) {
      const receipt = await commitReset(db, current.id, next, committedAt);
      state.runs = state.runs.map((run) => run.id === current.id ? { ...run, endedAtMs: committedAt, elapsedAtEndMs: Math.max(0, committedAt - run.startedAtMs), maxObservedElapsedMs: Math.max(run.maxObservedElapsedMs || 0, committedAt - run.startedAtMs) } : run);
      state.runs.push(next);
      state.meta = { ...state.meta, activeRunId: next.id, revision: state.meta.revision + 1, camera: null, resetReceipt: receipt };
      channel?.postMessage({ revision: state.meta.revision });
    } else {
      const ended = { ...current, endedAtMs: committedAt, elapsedAtEndMs: Math.max(0, committedAt - current.startedAtMs) };
      state.runs = state.runs.map((run) => run.id === current.id ? ended : run).concat(next);
      state.meta = { ...state.meta, activeRunId: next.id, revision: (state.meta.revision || 0) + 1, camera: null, resetReceipt: { oldRunId: ended.id, newRunId: next.id, committedAtMs, undoUntilMs: committedAt + 10_000, oldRun: ended } };
    }
  } catch (error) {
    busy = false; els.action.disabled = false; hold.setEnabled(true);
    await refreshFromStorage(); showStatus(`Couldn't save that restart. Your current run is safe. ${error.message}`, "error"); return;
  }
  anomalyElapsed = null; lastWorldKey = ""; lastShownSecond = -1;
  showStatus("A new beginning. Your past run is saved in History.");
  els.undo.hidden = false;
  window.clearTimeout(undoHandle); undoHandle = window.setTimeout(() => { els.undo.hidden = true; }, Math.max(0, committedAt + 10_000 - Date.now()));
  render(true); announceChange();
  await playWave(reducedMotion());
  busy = false; els.action.disabled = false; hold.setEnabled(Boolean(activeRun()));
  els.encouragement.textContent = "Your next seed is already growing.";
  render(true);
}

async function playWave(calm = false) {
  if (calm) {
    els.wave.classList.add("calm");
    await wait(360);
    els.wave.classList.remove("calm");
    return;
  }
  els.wave.classList.add("active");
  await wait(4550);
  els.wave.classList.remove("active");
}

async function undoAccidentalReset() {
  if (busy) return;
  const receipt = state.meta?.resetReceipt;
  if (!receipt || Date.now() > receipt.undoUntilMs || receipt.newRunId !== state.meta.activeRunId) { els.undo.hidden = true; return; }
  try {
    let restored;
    if (db && !ephemeral) restored = await undoReset(db, state.meta.activeRunId, Date.now());
    else {
      const elapsedSinceReset = Date.now() - receipt.committedAtMs;
      restored = { ...receipt.oldRun, endedAtMs: null, elapsedAtEndMs: null, maxObservedElapsedMs: Math.max(receipt.oldRun.maxObservedElapsedMs || 0, elapsedSinceReset) };
      state.runs = state.runs.filter((run) => run.id !== receipt.newRunId).map((run) => run.id === restored.id ? restored : run);
      state.meta = { ...state.meta, activeRunId: restored.id, resetReceipt: null, revision: state.meta.revision + 1 };
    }
    state.runs = state.runs.filter((run) => run.id !== receipt.newRunId).map((run) => run.id === restored.id ? restored : run);
    state.meta = { ...state.meta, activeRunId: restored.id, resetReceipt: null, revision: (state.meta.revision || 0) + 1 };
    els.undo.hidden = true; anomalyElapsed = null; lastWorldKey = "";
    showStatus("Your previous island and timer are back."); render(true); channel?.postMessage({ revision: state.meta.revision });
  } catch (error) { showStatus(error.message, "error"); }
}

async function updateSetting(changes) {
  state.meta.settings = { ...state.meta.settings, ...changes };
  document.body.classList.toggle("reduce-motion", reducedMotion());
  try { if (db && !ephemeral) await saveSettings(db, changes); }
  catch (error) { showStatus(error.message, "error"); }
}

function render(forceScene = false) {
  const run = activeRun();
  hold?.setEnabled(Boolean(run));
  els.action.disabled = busy;
  els.label.textContent = run ? "I picked — begin again" : "Begin growing";
  els.help.textContent = run ? "press and hold for one second" : "one tap begins your first little world";
  els.action.setAttribute("aria-describedby", "holdHelp");
  els.encouragement.textContent = run ? "Give your hands a break. Let a little world grow." : "Your island is ready when you are.";
  const elapsed = run ? currentElapsed(run) : 0;
  const text = formatDuration(elapsed);
  if (Math.floor(elapsed / 1000) !== lastShownSecond || forceScene) {
    els.timer.textContent = text;
    els.timer.setAttribute("aria-label", longDurationLabel(elapsed));
    lastShownSecond = Math.floor(elapsed / 1000);
  }
  const historical = state.runs.filter((item) => item.endedAtMs !== null);
  const best = Math.max(0, ...historical.map((item) => elapsedForRun(item)), run ? elapsed : 0);
  els.best.textContent = best ? `Best time · ${formatDuration(best)}` : "Every beginning counts";
  const growth = growthAt(elapsed);
  els.stage.textContent = run ? growth.stage : "A seed finds the shore";
  const person = growth.personPresent ? " · a neighbor is here" : "";
  const buildings = growth.completedBuildings;
  els.summary.textContent = run ? `${buildings ? `${buildings} ${buildings === 1 ? "home" : "homes"}` : (growth.gardenPresent ? "garden and first paths" : growth.personPresent ? "a seed and a neighbor" : "a seed by the shore")}${person}` : "A seed and a quiet shoreline.";
  const visualKey = run ? `${run.id}:${growth.stageId}:${growth.completedBuildings}:${Math.floor(elapsed / 30_000)}` : "empty";
  if (sceneReady && renderer && (forceScene || visualKey !== lastWorldKey)) {
    lastWorldKey = visualKey;
    renderer.renderWorld(worldFor(run?.seed || "quiet-harbor-first-seed", elapsed)).catch(() => {});
  }
  renderHistory();
  updateUndoAvailability();
}

function tick() {
  const run = activeRun();
  if (run && clockMonitor && anomalyElapsed === null) {
    const elapsed = clockMonitor.observe(run);
    if (Math.floor(elapsed / 1000) !== lastShownSecond) render();
  } else render();
  if (run && !document.hidden && Date.now() - lastCheckpoint >= 60_000 && db && !ephemeral) {
    lastCheckpoint = Date.now();
    checkpoint(db, run.id).catch(() => setStorageNotice("A time checkpoint could not be saved. Your timer is still visible; try exporting a backup."));
  }
}

function showClockAnomaly(elapsed) {
  if (anomalyElapsed !== null) return;
  anomalyElapsed = Math.max(0, elapsed || 0);
  els.status.replaceChildren(document.createTextNode("Your device time changed. Keep your saved duration and continue with the current time? "));
  const button = document.createElement("button");
  button.type = "button"; button.className = "inline-action"; button.textContent = "Keep this duration and continue";
  button.addEventListener("click", () => void rebaseClock());
  els.status.append(button); els.status.classList.remove("error"); els.status.hidden = false;
  render(true);
}

async function rebaseClock() {
  const run = activeRun(); if (!run) return;
  const now = Date.now(), elapsed = anomalyElapsed;
  try {
    if (db && !ephemeral) await rebaseRunClock(db, run.id, now, elapsed);
    const rebased = { ...run, startedAtMs: now - elapsed, originalStartedAtMs: run.originalStartedAtMs || run.startedAtMs, maxObservedElapsedMs: elapsed };
    state.runs = state.runs.map((item) => item.id === run.id ? rebased : item);
    anomalyElapsed = null; clockMonitor.acceptRebased(); showStatus("Your saved duration is kept. The timer is continuing."); render(true);
  } catch (error) { showStatus(error.message, "error"); }
}

function checkpointAtLifecycle() {
  const run = activeRun();
  if (!run || !db || ephemeral) return;
  checkpoint(db, run.id).catch(() => {});
}

function renderHistory() {
  const runs = [...state.runs].sort((a, b) => (b.endedAtMs || Date.now()) - (a.endedAtMs || Date.now()));
  const finished = runs.filter((run) => run.endedAtMs !== null);
  els.historyIntro.textContent = finished.length ? `${finished.length} previous ${finished.length === 1 ? "run" : "runs"}. Your best time is based on the saved history.` : "Your first run is ready to begin. Completed runs will appear here.";
  els.history.replaceChildren();
  if (!runs.length) {
    const empty = document.createElement("div"); empty.className = "empty-history"; empty.textContent = "Your island will be here when you're ready."; els.history.append(empty); return;
  }
  for (const run of runs.slice(0, 80)) {
    const row = document.createElement("div"); row.className = "history-row";
    const name = document.createElement("span"); name.textContent = run.id === state.meta?.activeRunId ? "Current island" : "A previous beginning";
    const date = document.createElement("span"); date.className = "history-date"; date.textContent = new Date(run.originalStartedAtMs || run.startedAtMs).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
    const duration = document.createElement("span"); duration.className = "history-time"; duration.textContent = formatDuration(elapsedForRun(run));
    row.append(name, date, duration); els.history.append(row);
  }
}

function updateUndoAvailability() {
  const receipt = state.meta?.resetReceipt;
  if (receipt && receipt.newRunId === state.meta.activeRunId) {
    const remaining = receipt.undoUntilMs - Date.now();
    if (remaining > 0) {
      els.undo.hidden = false;
      if (!undoHandle) undoHandle = window.setTimeout(() => { els.undo.hidden = true; state.meta.resetReceipt = null; undoHandle = 0; }, remaining);
    } else { els.undo.hidden = true; state.meta.resetReceipt = null; }
  } else els.undo.hidden = true;
}

function openSettings() {
  if (!els.settings.open) els.settings.showModal();
  renderHistory();
  $("installHelp").hidden = window.matchMedia?.("(display-mode: standalone)").matches || navigator.standalone === true;
}

async function exportData() {
  const status = (message, error = false) => { els.backupStatus.textContent = message; els.backupStatus.hidden = false; els.backupStatus.style.color = error ? "#934d3c" : ""; };
  try {
    if (!state.meta) throw new Error("Begin a run before making a backup.");
    const data = makeBackup(state);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const file = new File([blob], "quiet-harbor-backup.json", { type: "application/json" });
    if (navigator.canShare?.({ files: [file] }) && navigator.share) await navigator.share({ files: [file], title: "Quiet Harbor backup", text: "My Quiet Harbor progress" });
    else { const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = file.name; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000); }
    status("Your backup file is ready.");
  } catch (error) { if (error.name !== "AbortError") status(error.message || "Could not make a backup.", true); }
}

async function importData(file) {
  if (!file) return;
  const status = (message, error = false) => { els.backupStatus.textContent = message; els.backupStatus.hidden = false; els.backupStatus.style.color = error ? "#934d3c" : ""; };
  try {
    const restored = await parseBackupFile(file);
    const active = restored.runs.find((run) => run.id === restored.meta.activeRunId);
    const duration = formatDuration(elapsedForRun(active));
    if (!confirm(`Replace this browser's saved progress with ${restored.runs.length} run(s)?\n\nThe active timer in the file reads ${duration}.`)) return;
    if (!db || ephemeral) throw new Error("This browser can't safely replace saved progress. Exported backup is unchanged.");
    await replaceBackup(db, restored);
    state = restored; anomalyElapsed = null; lastWorldKey = ""; els.motion.value = state.meta.settings.motion; els.calm.checked = state.meta.settings.calmRestart;
    hold.setEnabled(true); status("Your saved island and run history have been restored."); render(true); channel?.postMessage({ revision: state.meta.revision });
  } catch (error) { status(error.message, true); }
  finally { els.importFile.value = ""; }
}

async function refreshFromStorage() {
  if (!db || ephemeral) return;
  try {
    const fresh = await readState(db);
    if (fresh.meta?.revision !== state.meta?.revision || fresh.meta?.activeRunId !== state.meta?.activeRunId) {
      state = fresh; anomalyElapsed = null; lastWorldKey = "";
      els.undo.hidden = true; hold?.setEnabled(Boolean(activeRun())); render(true);
    }
  } catch (error) { showStatus(`Saved progress couldn't be refreshed. ${error.message}`, "error"); }
}

function announceChange() { channel?.postMessage({ revision: state.meta?.revision }); }
function reducedMotion() { return Boolean(state.meta?.settings?.motion === "reduced" || (state.meta?.settings?.motion === "system" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches)); }
function wait(ms) { return new Promise((resolve) => window.setTimeout(resolve, ms)); }

async function registerServiceWorker() {
  if (!("serviceWorker" in navigator) || !location.protocol.startsWith("http")) return;
  try { await navigator.serviceWorker.register("./sw.js", { scope: "./" }); }
  catch (error) { console.info("Offline app caching is unavailable in this browser.", error); }
}

function setupUpdates() {
  if (!("serviceWorker" in navigator)) return;
  navigator.serviceWorker.ready.then((registration) => {
    const check = () => { if (registration.waiting && navigator.serviceWorker.controller) $("applyUpdate").hidden = false; };
    check(); registration.addEventListener("updatefound", () => registration.installing?.addEventListener("statechange", check));
    $("applyUpdate").addEventListener("click", () => {
      if (busy || hold?.pointerId !== null || hold?.key) { showStatus("Finish the current gesture before installing the update."); return; }
      registration.waiting?.postMessage({ type: "SKIP_WAITING" });
    });
    navigator.serviceWorker.addEventListener("controllerchange", () => { if (!busy) location.reload(); });
  });
}

initialise().catch((error) => {
  setStorageNotice(`The app could not load its saved state. ${error.message}`);
  els.fallback.hidden = false;
  attachEvents(); render();
});
