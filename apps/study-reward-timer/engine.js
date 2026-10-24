/* Pure, clock-injected timer and ledger. Money is always integer cents. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.StudyTimer = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const KEY = 'theLibrary.studyRewardTimer.v1';
  const MAX_TIME = 7 * 24 * 60 * 60 * 1000;
  const id = () => globalThis.crypto?.randomUUID?.() || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  const clone = value => JSON.parse(JSON.stringify(value));
  function hapticDefaults(settings = {}) {
    const option = (pattern, strength = 60) => ({ enabled: true, pattern, strength, engine: 'auto' });
    return { start: option('soft-click'), pause: option('soft-click', 40), resume: option('clean-click', 60), hold: option('hold-rise', 80), complete: { enabled: true, pattern: settings.hapticPattern || 'rise-snap', strength: settings.hapticStrength || 80, engine: settings.hapticEngine || 'auto' } };
  }
  function catalogue() {
    const groups = [
      ['MR', 'Body', ['Body MR', 'Abdomen', 'Liver', 'Pancreas', 'MRCP', 'Abdomen + MRCP', 'MR elastography', 'Abdomen + elastography', 'Renal / adrenal', 'Enterography', 'Pelvis', 'Rectal staging', 'Prostate', 'Female pelvis', 'Perianal fistula', 'Defecography', 'Liver fat / iron quantification']],
      ['MR', 'Neuro', ['Brain', 'Brain + angiography', 'Orbits', 'Pituitary', 'IAC', 'Cervical spine', 'Thoracic spine', 'Lumbar spine', 'Whole spine']],
      ['MR', 'MSK', ['Shoulder', 'Elbow', 'Wrist / hand', 'Hip', 'Knee', 'Ankle / foot', 'Bone / soft tissue lesion']],
      ['MR', 'Other', ['Breast', 'Cardiac', 'Angiography']],
      ['CT', 'Body', ['Abdomen / pelvis', 'Chest', 'Chest / abdomen / pelvis', 'Liver multiphase', 'Pancreas protocol', 'Renal / adrenal protocol', 'Urogram', 'Enterography']],
      ['CT', 'Angiography', ['Pulmonary angiography', 'Aorta', 'Runoff', 'Coronary']],
      ['CT', 'Neuro / MSK', ['Head', 'Head / neck angiography', 'Neck', 'Spine', 'Extremity']],
      ['US', 'General', ['Abdomen', 'RUQ', 'Renal', 'Pelvis', 'Scrotum', 'Thyroid', 'Soft tissue', 'Obstetric', 'Pediatric abdomen']],
      ['US', 'Vascular', ['Venous duplex', 'Arterial duplex', 'Carotid', 'Transplant Doppler']],
      ['XR', 'General', ['Chest', 'Abdomen', 'Spine', 'Extremity']],
      ['Fluoro', 'General', ['Esophagram', 'Upper GI', 'Small bowel', 'Swallow study', 'Enema', 'Other fluoro']],
      ['NM', 'General', ['Bone scan', 'Hepatobiliary', 'Renal', 'Thyroid', 'V/Q', 'Gastric emptying']],
      ['PET', 'General', ['Oncologic PET/CT', 'Brain PET', 'Other PET']],
      ['Breast', 'General', ['Screening mammogram', 'Diagnostic mammogram', 'Breast ultrasound']],
      ['Procedure', 'General', ['Biopsy', 'Drainage', 'Other procedure']]
    ];
    return groups.flatMap(([modality, group, names]) => names.map((name, n) => ({
      id: `${modality}-${group}-${n}`.toLowerCase().replace(/[^a-z0-9-]/g, ''),
      modality, group, name, targetMs: 18 * 60000, rewardCents: modality === 'MR' ? 200 : 0,
      favorite: modality === 'MR' && group === 'Body' && [0, 1, 4, 5, 6, 7].includes(n)
    })));
  }
  function fresh() {
    const types = catalogue();
    return { version: 1, settings: { goalCents: 90000, goalName: 'Steam Deck · 512GB OLED', sound: false, haptics: true, hapticPattern: 'rise-snap', hapticStrength: 80, hapticEngine: 'auto', hapticEvents: hapticDefaults(), holdToComplete: true, holdDefaultVersion: 1, motion: true, keepAwake: true, countUp: false }, customHaptics: [], futureGoals: [], types, selectedTypeId: types[0].id, records: [], active: null };
  }
  function elapsed(active, now = Date.now()) {
    return active ? active.elapsedMs + (active.runningSince === null ? 0 : Math.max(0, now - active.runningSince)) : 0;
  }
  function payout(record) { return record.elapsedMs <= record.targetMs ? record.rewardCents : 0; }
  function total(records) { return records.reduce((sum, record) => sum + payout(record), 0); }
  function start(state, now = Date.now()) {
    if (state.active) throw new Error('A case is already active.');
    const type = state.types.find(type => type.id === state.selectedTypeId);
    if (!type) throw new Error('Choose a study type.');
    state.active = { id: id(), typeId: type.id, typeName: type.name, modality: type.modality, group: type.group, targetMs: type.targetMs, rewardCents: type.rewardCents, startedAt: now, elapsedMs: 0, runningSince: now };
    return state.active;
  }
  function pause(state, now = Date.now()) {
    if (!state.active || state.active.runningSince === null || state.active.holding) return;
    state.active.elapsedMs = elapsed(state.active, now);
    state.active.runningSince = null;
  }
  function resume(state, now = Date.now()) {
    if (state.active && state.active.runningSince === null && !state.active.holding) state.active.runningSince = now;
  }
  function beginHold(state, now = Date.now()) {
    if (!state.active || state.active.runningSince === null) return false;
    state.active.elapsedMs = elapsed(state.active, now);
    state.active.runningSince = null;
    state.active.holding = true;
    return true;
  }
  function cancelHold(state, now = Date.now()) {
    if (!state.active?.holding) return false;
    delete state.active.holding;
    state.active.runningSince = now;
    return true;
  }
  function restartDuration(state, targetMs, now = Date.now()) {
    if (!number(targetMs, 1000, MAX_TIME)) throw new Error('Choose a duration from 1 second to 7 days.');
    const type = state.types.find(t => t.id === (state.active?.typeId || state.selectedTypeId));
    if (!type) throw new Error('Study type is no longer available.');
    type.targetMs = targetMs;
    state.selectedTypeId = type.id;
    state.active = null;
    return start(state, now);
  }
  function finish(state, now = Date.now()) {
    if (!state.active || (state.active.runningSince === null && !state.active.holding)) return null;
    const { runningSince, holding, ...record } = state.active;
    record.elapsedMs = elapsed(state.active, now);
    record.completedAt = now;
    state.records.push(record);
    state.active = null;
    return record;
  }
  function number(value, min, max) { return typeof value === 'number' && Number.isFinite(value) && value >= min && value <= max; }
  function text(value, max = 100) { return typeof value === 'string' && value.length > 0 && value.length <= max; }
  function validateType(t) {
    return t && text(t.id) && text(t.name) && text(t.modality, 30) && text(t.group) && number(t.targetMs, 1000, MAX_TIME) && Number.isInteger(t.rewardCents) && number(t.rewardCents, 0, 1000000) && typeof t.favorite === 'boolean';
  }
  function validateRecord(r) {
    return r && text(r.id) && text(r.typeId) && text(r.typeName) && text(r.modality, 30) && text(r.group) && number(r.elapsedMs, 0, MAX_TIME * 100) && number(r.targetMs, 1000, MAX_TIME) && Number.isInteger(r.rewardCents) && number(r.rewardCents, 0, 1000000) && number(r.startedAt, 0, 8640000000000000) && number(r.completedAt, r.startedAt, 8640000000000000);
  }
  function validate(data) {
    if (!data || data.version !== 1 || !Array.isArray(data.types) || !data.types.length || data.types.length > 2000 || !data.types.every(validateType) || new Set(data.types.map(t => t.id)).size !== data.types.length) throw new Error('Invalid study settings in backup.');
    if (!Array.isArray(data.records) || data.records.length > 100000 || !data.records.every(validateRecord) || new Set(data.records.map(r => r.id)).size !== data.records.length) throw new Error('Invalid case history in backup.');
    if (!data.types.some(t => t.id === data.selectedTypeId)) throw new Error('Invalid selected study.');
    const s = data.settings;
    if (!s || !text(s.goalName) || !Number.isInteger(s.goalCents) || !number(s.goalCents, 100, 100000000) || !['sound', 'haptics', 'motion', 'keepAwake', 'countUp'].every(key => typeof s[key] === 'boolean')) throw new Error('Invalid goal or preferences in backup.');
    const hapticPattern = s.hapticPattern === undefined ? 'rise-snap' : s.hapticPattern;
    const hapticStrength = s.hapticStrength === undefined ? 80 : s.hapticStrength;
    const hapticEngine = s.hapticEngine === undefined ? 'auto' : s.hapticEngine;
    if (!text(hapticPattern,80) || !number(hapticStrength,20,100) || !['auto','standard'].includes(hapticEngine)) throw new Error('Invalid haptic preferences in backup.');
    const hapticEvents = s.hapticEvents === undefined ? hapticDefaults({ hapticPattern, hapticStrength, hapticEngine }) : s.hapticEvents;
    if (!hapticEvents || !['start','pause','resume','hold','complete'].every(key => {
      const e = hapticEvents[key];
      return e && typeof e.enabled === 'boolean' && text(e.pattern,80) && number(e.strength,20,100) && ['auto','standard'].includes(e.engine);
    }) || (s.holdToComplete !== undefined && typeof s.holdToComplete !== 'boolean')) throw new Error('Invalid action haptic preferences in backup.');
    if (s.holdDefaultVersion !== undefined && s.holdDefaultVersion !== 1) throw new Error('Invalid completion preferences in backup.');
    // Apply the new hold default once; later explicit opt-outs survive reload and restore.
    const holdToComplete = s.holdDefaultVersion === 1 ? (s.holdToComplete ?? true) : true;
    const customHaptics = data.customHaptics === undefined ? [] : data.customHaptics;
    if (!Array.isArray(customHaptics) || customHaptics.length > 100 || new Set(customHaptics.map(p => p?.id)).size !== customHaptics.length || !customHaptics.every(validCustomHaptic)) throw new Error('Invalid custom haptic curves in backup.');
    // Older saved data and backups predate the optional future-goals list.
    const goals = data.futureGoals === undefined ? [] : data.futureGoals;
    if (!Array.isArray(goals) || goals.length > 1000 || !goals.every(g => g && text(g.id) && text(g.name) && (g.costCents === null || (Number.isInteger(g.costCents) && number(g.costCents, 100, 100000000)))) || new Set(goals.map(g => g.id)).size !== goals.length) throw new Error('Invalid future goals in backup.');
    if (data.active !== null) {
      const a = data.active;
      if (!a || !validateRecord({ ...a, completedAt: a.startedAt }) || !(a.runningSince === null || number(a.runningSince, a.startedAt, 8640000000000000)) || (a.holding !== undefined && (a.holding !== true || a.runningSince !== null))) throw new Error('Invalid active timer in backup.');
      if (data.records.some(r => r.id === a.id)) throw new Error('Active case is already completed.');
    }
    return { ...clone(data), settings: { ...clone(s), hapticPattern, hapticStrength, hapticEngine, hapticEvents: clone(hapticEvents), holdToComplete, holdDefaultVersion: 1 }, customHaptics: clone(customHaptics), futureGoals: clone(goals) };
  }
  function validCustomHaptic(p) {
    return p && text(p.id,80) && p.id.startsWith('custom-') && text(p.name,60) && number(p.durationMs,200,3000) && typeof p.snap === 'boolean' && Array.isArray(p.points) && p.points.length >= 2 && p.points.length <= 32 && p.points[0]?.at === 0 && p.points.at(-1)?.at === p.durationMs && p.points.every((point,i) => point && number(point.at,0,p.durationMs) && number(point.intensity,0,1) && number(point.sharpness,0,1) && (i === 0 || point.at - p.points[i-1].at >= 10));
  }
  // CSV formula prefixes are escaped for spreadsheet applications, including custom names.
  function csv(records) {
    const cell = value => {
      let str = String(value);
      if (/^[=+@\-\t\r]/.test(str)) str = "'" + str;
      return '"' + str.replace(/"/g, '""') + '"';
    };
    const rows = records.map(r => [r.id, new Date(r.startedAt).toISOString(), new Date(r.completedAt).toISOString(), r.modality, r.group, r.typeName, (r.elapsedMs / 60000).toFixed(3), (r.targetMs / 60000).toFixed(3), (r.rewardCents / 100).toFixed(2), r.elapsedMs <= r.targetMs ? 'yes' : 'no', (payout(r) / 100).toFixed(2)]);
    return [['ID', 'Started (UTC)', 'Completed (UTC)', 'Modality', 'Group', 'Study', 'Active minutes', 'Target minutes', 'Available USD', 'Within target', 'Earned USD'], ...rows].map(row => row.map(cell).join(',')).join('\r\n');
  }
  return { KEY, MAX_TIME, id, clone, catalogue, fresh, elapsed, payout, total, start, pause, resume, beginHold, cancelHold, restartDuration, finish, validate, validCustomHaptic, hapticDefaults, csv };
});
