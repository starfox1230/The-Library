/* No network data, accounts, analytics, or patient fields. */
(() => {
  'use strict';
  const E = StudyTimer;
  const H = AfterglowHaptics;
  const hapticPlayer = H.createPlayer(navigator);
  const $ = id => document.getElementById(id);
  const money = cents => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: cents % 100 ? 2 : 0 }).format(cents / 100);
  const minutes = ms => Number((ms / 60000).toFixed(2)).toString();
  const duration = (ms, ceil = false) => {
    const seconds = Math.max(0, (ceil ? Math.ceil : Math.floor)(Math.abs(ms) / 1000));
    return `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  };
  const localDate = time => new Date(time).toLocaleDateString();
  const localInput = time => {
    const date = new Date(time);
    return new Date(time - date.getTimezoneOffset() * 60000).toISOString().slice(0, 19);
  };
  const node = (tag, className, text) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  };
  let corrupt = false;
  let unsaved = false;
  let state = E.fresh();
  let pickerFavorites = true;
  let settingsFavorites = true;
  let undoAction = null;
  let toastTimeout, celebrationTimeout;
  let wakeLock = null;
  let wakePending = false;
  let audio = null;
  let confirmAction = null;
  let hapticTestTimer = null;
  function storageWarning(message) {
    $('storageAlert').textContent = message;
    $('storageAlert').hidden = !message;
  }
  function readStored() {
    // Never replace newer in-memory work with an older disk copy after a quota failure.
    if (unsaved) return state;
    let raw;
    try { raw = localStorage.getItem(E.KEY); }
    catch { storageWarning('Local saving is unavailable. Keep this page open and export a backup before leaving.'); return state; }
    if (!raw) return state;
    try { const result = E.validate(JSON.parse(raw)); corrupt = false; return result; }
    catch { corrupt = true; storageWarning('Saved data could not be read. Export the original backup in Settings → Data, then restore a valid backup. Existing data has not been overwritten.'); return state; }
  }
  state = readStored();
  function mutate(fn) {
    const latest = readStored();
    if (corrupt) { toast('Restore a valid backup before changing data.'); return null; }
    const next = E.clone(latest);
    const result = fn(next);
    try { localStorage.setItem(E.KEY, JSON.stringify(next)); unsaved = false; storageWarning(''); }
    catch { unsaved = true; storageWarning('Changes are in memory only: device storage is unavailable or full. Export a backup before leaving this page.'); }
    state = next;
    render();
    return result;
  }
  function toast(message, undo = null) {
    clearTimeout(toastTimeout);
    undoAction = undo;
    $('toast').querySelector('span').textContent = message;
    const dialogs = [...document.querySelectorAll('dialog[open]')];
    (dialogs.at(-1) || document.body).append($('toast'));
    $('undoButton').hidden = !undo;
    $('toast').hidden = false;
    toastTimeout = setTimeout(() => { $('toast').hidden = true; undoAction = null; }, undo ? 10000 : 4500);
  }
  $('undoButton').onclick = () => { const action = undoAction; undoAction = null; $('toast').hidden = true; action?.(); };
  function open(dialog) { if (!dialog.open) dialog.showModal(); }
  document.querySelectorAll('[data-close]').forEach(button => { button.onclick = () => button.closest('dialog').close(); });
  document.querySelectorAll('dialog').forEach(dialog => {
    dialog.addEventListener('close', () => {
      if ($('toast').closest('dialog') === dialog) {
        const openDialogs = [...document.querySelectorAll('dialog[open]')];
        (openDialogs.at(-1) || document.body).append($('toast'));
      }
    });
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    });
  });
  function confirm(title, text, action) {
    $('confirmTitle').textContent = title;
    $('confirmText').textContent = text;
    confirmAction = action;
    open($('confirmDialog'));
  }
  $('confirmCancel').onclick = () => $('confirmDialog').close();
  $('confirmOk').onclick = () => { const action = confirmAction; $('confirmDialog').close(); confirmAction = null; action?.(); };
  function selected() { return state.types.find(t => t.id === state.selectedTypeId) || state.types[0]; }
  function renderTimer() {
    const a = state.active;
    const type = a || selected();
    const target = type.targetMs;
    const spent = E.elapsed(a);
    const over = !!a && spent > target;
    const paused = a && a.runningSince === null;
    document.body.dataset.state = paused ? 'paused' : over ? 'over' : a ? 'running' : 'idle';
    document.body.dataset.active = !!a;
    $('studyName').textContent = a ? a.typeName : type.name;
    $('modality').textContent = type.modality;
    $('studyPicker').disabled = !!a;
    $('studyPicker').setAttribute('aria-label', a ? `Active study: ${a.typeName}. Finish or discard to change.` : 'Choose study type');
    $('time').textContent = state.settings.countUp && a ? duration(spent) : `${over ? '+' : ''}${duration(a ? target - spent : target, !over)}`;
    $('timerStatus').textContent = paused ? 'PAUSED' : over ? 'OVER TARGET' : a ? (state.settings.countUp ? 'ELAPSED' : 'REMAINING') : 'READY';
    $('timerDetail').textContent = a ? `${duration(state.settings.countUp ? Math.abs(target - spent) : spent, state.settings.countUp && !over)} ${state.settings.countUp ? (over ? 'over target' : 'remaining') : 'elapsed'}` : `${minutes(target)} min target`;
    $('dialProgress').style.strokeDashoffset = a ? Math.min(100, spent / target * 100) : 0;
    $('targetMeta').textContent = `${minutes(target)} min target`;
    $('rewardMeta').textContent = over ? '$0 · over target' : type.rewardCents ? `${money(type.rewardCents)} on target` : '$0 · tracking only';
    $('completeButton').hidden = !a;
    $('discardButton').hidden = !a;
    $('toggleButton').querySelector('span').textContent = !a ? 'Start' : paused ? 'Resume' : 'Pause';
    $('toggleButton').setAttribute('aria-label', !a ? 'Start timer' : paused ? 'Resume timer' : 'Pause timer');
    $('toggleButton').querySelector('use').setAttribute('href', a && !paused ? '#i-pause' : '#i-play');
  }
  function render() {
    document.body.classList.toggle('reduce-motion', !state.settings.motion);
    renderTimer();
    const earned = E.total(state.records);
    const percent = Math.min(100, earned / state.settings.goalCents * 100);
    $('goalName').textContent = state.settings.goalName;
    $('earned').textContent = money(earned);
    $('goalTotal').textContent = `/ ${money(state.settings.goalCents)}`;
    $('fundProgress').style.width = `${percent}%`;
    $('fundSpark').style.left = `${percent}%`;
    $('fundPercent').textContent = `${Number(percent.toFixed(1))}%`;
    document.querySelector('.progress-track').setAttribute('aria-valuenow', percent.toFixed(1));
    document.querySelector('.progress-track').setAttribute('aria-valuetext', `${money(earned)} of ${money(state.settings.goalCents)}`);
    const today = state.records.filter(r => localDate(r.completedAt) === localDate(Date.now()));
    $('todayStats').textContent = `${today.length} today · ${money(E.total(today))}`;
    if ($('historyDialog').open) renderHistory();
    if ($('settingsDialog').open) renderFutureGoals();
    updateWakeLock();
  }
  async function updateWakeLock() {
    const wanted = state.settings.keepAwake && state.active?.runningSince != null && document.visibilityState === 'visible';
    if (!wanted && wakeLock) { const old = wakeLock; wakeLock = null; await old.release().catch(() => {}); }
    else if (wanted && !wakeLock && !wakePending && navigator.wakeLock) {
      wakePending = true;
      try { const lock = await navigator.wakeLock.request('screen'); if (!state.active || state.active.runningSince === null || !state.settings.keepAwake || document.visibilityState !== 'visible') await lock.release(); else { wakeLock = lock; lock.addEventListener('release', () => { if (wakeLock === lock) wakeLock = null; }); } } catch { /* Optional capability. */ }
      finally { wakePending = false; }
    }
  }
  function clearCelebration() {
    stopHapticTest();
    clearTimeout(celebrationTimeout);
    $('timerFace').classList.remove('celebrating');
    document.querySelector('.fund').classList.remove('receiving');
    $('particles').replaceChildren();
  }
  function chime() {
    if (!state.settings.sound) return;
    try {
      audio ||= new (window.AudioContext || window.webkitAudioContext)();
      audio.resume().catch(() => {});
      [659.25, 830.61, 987.77].forEach((frequency, i) => {
        const oscillator = audio.createOscillator(), gain = audio.createGain();
        const at = audio.currentTime + i * .075;
        oscillator.type = 'sine'; oscillator.frequency.value = frequency;
        gain.gain.setValueAtTime(0, at); gain.gain.linearRampToValueAtTime(.045, at + .012); gain.gain.exponentialRampToValueAtTime(.001, at + .48);
        oscillator.connect(gain).connect(audio.destination); oscillator.start(at); oscillator.stop(at + .5);
      });
    } catch { /* Sound must never block completing a case. */ }
  }
  function celebrate(cents, preview = false) {
    clearCelebration();
    $('flashAmount').textContent = `+${money(cents)}`;
    $('rewardFlash').querySelector('span').textContent = preview ? 'PREVIEW' : 'IN THE FUND';
    // Restart a short, nonblocking success sequence.
    void $('timerFace').offsetWidth;
    $('timerFace').classList.add('celebrating');
    document.querySelector('.fund').classList.add('receiving');
    chime();
    if (state.settings.haptics) hapticPlayer.play(state.settings.hapticPattern, { engine: state.settings.hapticEngine, strength: state.settings.hapticStrength });
    if (state.settings.motion && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const face = $('timerFace').getBoundingClientRect();
      for (let i = 0; i < 26; i++) {
        const particle = node('i', 'particle');
        const angle = Math.PI * 2 * i / 26;
        const radius = 90 + Math.random() * 110;
        particle.style.left = `${face.left + face.width / 2}px`;
        particle.style.top = `${face.top + face.height / 2}px`;
        particle.style.setProperty('--dx', `${Math.cos(angle) * radius}px`);
        particle.style.setProperty('--dy', `${Math.sin(angle) * radius}px`);
        particle.style.setProperty('--rot', `${Math.random() * 200}deg`);
        particle.style.background = i % 3 ? '#91ffe0' : '#a69aff';
        particle.style.animationDelay = `${Math.random() * 80}ms`;
        $('particles').append(particle);
      }
      const flight = node('div', 'coin-flight', '+');
      const fund = $('earned').getBoundingClientRect();
      flight.style.left = `${face.left + face.width / 2}px`; flight.style.top = `${face.top + face.height / 2}px`;
      flight.style.setProperty('--dx', `${fund.left + fund.width / 2 - face.left - face.width / 2}px`);
      flight.style.setProperty('--dy', `${fund.top - face.top - face.height / 2}px`);
      flight.style.animationDelay = '.45s';
      $('particles').append(flight);
    }
    celebrationTimeout = setTimeout(clearCelebration, 1700);
  }
  $('toggleButton').onclick = () => {
    clearCelebration();
    mutate(s => { if (!s.active) E.start(s); else if (s.active.runningSince === null) E.resume(s); else E.pause(s); });
  };
  $('completeButton').onclick = () => {
    const before = E.total(state.records);
    const record = mutate(s => E.finish(s));
    if (!record) return;
    const earned = E.payout(record);
    if (earned > 0) celebrate(earned);
    else { clearCelebration(); toast(record.elapsedMs <= record.targetMs ? 'On target · saved · $0 reward configured' : 'Saved · over target · $0'); }
    $('liveStatus').textContent = `Case saved. ${money(earned)} earned. Total ${money(E.total(state.records))}.`;
    if (before < state.settings.goalCents && E.total(state.records) >= state.settings.goalCents) toast('Steam Deck goal reached.');
  };
  $('discardButton').onclick = () => confirm('Discard this timer?', 'This case won’t be saved or earn money.', () => mutate(s => { s.active = null; }));
  function star(type) {
    const button = node('button', 'star-button', type.favorite ? '★' : '☆');
    button.setAttribute('aria-label', `${type.favorite ? 'Unfavorite' : 'Favorite'} ${type.name}`);
    button.setAttribute('aria-pressed', type.favorite);
    button.onclick = () => { mutate(s => { const t = s.types.find(t => t.id === type.id); if (t) t.favorite = !t.favorite; }); renderPicker(); renderStudySettings(); };
    return button;
  }
  function typeList(container, types, action) {
    container.replaceChildren();
    if (!types.length) { container.append(node('p', 'empty', 'No studies here. Turn off Favorites or change your search.')); return; }
    let group = '';
    const fragment = document.createDocumentFragment();
    types.forEach(type => {
      const heading = `${type.modality} · ${type.group}`;
      if (heading !== group) { fragment.append(node('h3', '', heading)); group = heading; }
      const row = node('div', `type-row${type.id === state.selectedTypeId ? ' selected' : ''}`);
      const button = node('button', 'type-select');
      button.append(node('strong', '', type.name), node('small', '', `${minutes(type.targetMs)} min · ${money(type.rewardCents)}`));
      button.onclick = () => action(type);
      row.append(button, star(type)); fragment.append(row);
    });
    container.append(fragment);
  }
  function filteredTypes(search, favorites) {
    return state.types.filter(t => (!favorites || t.favorite) && `${t.modality} ${t.group} ${t.name}`.toLowerCase().includes(search.toLowerCase().trim()));
  }
  function renderPicker() {
    typeList($('pickerList'), filteredTypes($('pickerSearch').value, pickerFavorites), type => {
      mutate(s => { if (!s.active) s.selectedTypeId = type.id; }); $('pickerDialog').close();
    });
  }
  $('studyPicker').onclick = () => { state = readStored(); renderPicker(); open($('pickerDialog')); };
  $('pickerSearch').oninput = renderPicker;
  $('pickerFavorites').onclick = () => { pickerFavorites = !pickerFavorites; $('pickerFavorites').setAttribute('aria-pressed', pickerFavorites); renderPicker(); };
  function renderHistory() {
    const search = $('historySearch').value.toLowerCase().trim();
    const period = $('historyRange').value;
    const cutoff = Date.now() - 7 * 86400000;
    const records = state.records.filter(r => `${r.modality} ${r.group} ${r.typeName}`.toLowerCase().includes(search) && (period === 'all' || (period === 'today' ? localDate(r.completedAt) === localDate(Date.now()) : r.completedAt >= cutoff))).sort((a, b) => b.completedAt - a.completedAt);
    const stats = $('historyStats'); stats.replaceChildren();
    [[records.length, 'cases'], [records.filter(r => r.elapsedMs <= r.targetMs).length, 'on target'], [money(E.total(records)), 'earned']].forEach(([value, label]) => { const stat = node('div', 'stat'); stat.append(node('strong', '', value), node('span', '', label)); stats.append(stat); });
    const list = $('historyList'); list.replaceChildren();
    if (!records.length) { list.append(node('p', 'empty', 'Completed cases appear here. Tap a case to edit it.')); return; }
    let date = '';
    const fragment = document.createDocumentFragment();
    records.forEach(record => {
      const day = new Date(record.completedAt).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
      if (day !== date) { fragment.append(node('h3', '', day)); date = day; }
      const button = node('button', 'history-row');
      button.setAttribute('aria-label', `Edit ${record.typeName}, ${duration(record.elapsedMs)}, ${money(E.payout(record))} earned`);
      button.append(node('span', `history-mark${record.elapsedMs > record.targetMs ? ' missed' : ''}`, record.elapsedMs <= record.targetMs ? '✓' : '—'));
      const info = node('span', 'history-info');
      info.append(node('strong', '', `${record.modality} · ${record.typeName}`), node('span', '', `${new Date(record.completedAt).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })} · ${duration(record.elapsedMs)} / ${minutes(record.targetMs)} min`));
      button.append(info, node('span', `history-money${E.payout(record) ? '' : ' zero'}`, `+${money(E.payout(record))}`));
      button.onclick = () => editRecord(record.id); fragment.append(button);
    });
    list.append(fragment);
  }
  $('historyButton').onclick = () => { state = readStored(); renderHistory(); open($('historyDialog')); };
  $('historySearch').oninput = renderHistory; $('historyRange').onchange = renderHistory;
  function editRecord(id) {
    const record = state.records.find(r => r.id === id); if (!record) return;
    const f = $('editForm').elements;
    $('editType').replaceChildren(...state.types.map(t => new Option(`${t.modality} · ${t.name}`, t.id)));
    if (!state.types.some(t => t.id === record.typeId)) $('editType').add(new Option(`${record.modality} · ${record.typeName}`, record.typeId));
    f.id.value = id; f.typeId.value = record.typeId; f.completedAt.value = localInput(record.completedAt);
    f.elapsed.value = duration(record.elapsedMs); f.minutes.value = minutes(record.targetMs); f.dollars.value = (record.rewardCents / 100).toFixed(2);
    open($('editDialog'));
  }
  $('editForm').onsubmit = event => {
    event.preventDefault(); const f = event.currentTarget.elements;
    const [m, sec] = f.elapsed.value.split(':').map(Number);
    const completedAt = new Date(f.completedAt.value).getTime();
    const elapsedMs = (m * 60 + sec) * 1000;
    if (!Number.isFinite(completedAt) || !Number.isFinite(elapsedMs) || elapsedMs < 0 || elapsedMs > E.MAX_TIME * 100) return toast('Check the date and active time.');
    const changed = mutate(s => {
      const r = s.records.find(r => r.id === f.id.value); if (!r) return false;
      const type = s.types.find(t => t.id === f.typeId.value);
      if (type && type.id !== r.typeId) Object.assign(r, { typeId: type.id, typeName: type.name, modality: type.modality, group: type.group });
      // Preserve exact milliseconds if the displayed time was not edited.
      if (duration(r.elapsedMs) !== f.elapsed.value) r.elapsedMs = elapsedMs;
      if (localInput(r.completedAt) !== f.completedAt.value) r.completedAt = completedAt;
      if (r.completedAt < r.startedAt) r.startedAt = Math.max(0, r.completedAt - r.elapsedMs);
      r.targetMs = Math.round(Number(f.minutes.value) * 60000); r.rewardCents = Math.round(Number(f.dollars.value) * 100);
      return true;
    });
    if (changed) { $('editDialog').close(); toast('Case updated · earnings recalculated'); }
  };
  $('deleteRecord').onclick = () => {
    const id = $('editForm').elements.id.value;
    const record = state.records.find(r => r.id === id); if (!record) return;
    const deleted = mutate(s => { const index = s.records.findIndex(r => r.id === id); if (index < 0) return false; s.records.splice(index, 1); return true; });
    if (!deleted) return;
    $('editDialog').close();
    toast('Case deleted · earnings updated', () => mutate(s => { if (!s.records.some(r => r.id === id)) s.records.push(record); }));
  };
  function setTab(name) {
    if (name !== 'feel') stopHapticTest();
    document.querySelectorAll('[data-tab]').forEach(b => b.setAttribute('aria-pressed', b.dataset.tab === name));
    document.querySelectorAll('[data-panel]').forEach(p => { p.hidden = p.dataset.panel !== name; });
  }
  document.querySelectorAll('[data-tab]').forEach(button => { button.onclick = () => { setTab(button.dataset.tab); if (button.dataset.tab === 'studies') renderStudySettings(); if (button.dataset.tab === 'feel') renderHapticSettings(); }; });
  function hapticMode() {
    return state.settings.hapticEngine === 'standard' ? (typeof navigator.vibrate === 'function' ? 'standard' : 'none') : hapticPlayer.capability();
  }
  function stopHapticTest() {
    clearTimeout(hapticTestTimer); hapticTestTimer = null;
    hapticPlayer.stop();
    $('hapticTimeline').classList.remove('playing');
    $('stopHaptic').hidden = true;
    $('testHaptic').textContent = 'Test pattern';
  }
  function renderHapticSettings() {
    const pattern = H.get(state.settings.hapticPattern);
    if (!$('hapticPattern').children.length) {
      let group;
      H.patterns.forEach(p => {
        if (!group || group.label !== p.group) { group = node('optgroup'); group.label = p.group; $('hapticPattern').append(group); }
        group.append(new Option(`${p.name} · ${(H.duration(p)/1000).toFixed(2)}s`, p.id));
      });
    }
    $('hapticPattern').value = pattern.id;
    $('hapticEngine').value = state.settings.hapticEngine;
    // Imported values in the supported range still get a selectable strength.
    if (![...$('hapticStrength').options].some(o => Number(o.value) === state.settings.hapticStrength)) $('hapticStrength').add(new Option(`${state.settings.hapticStrength}%`, state.settings.hapticStrength));
    $('hapticStrength').value = String(state.settings.hapticStrength);
    $('hapticDescription').textContent = pattern.description;
    const mode = hapticMode();
    $('hapticStrength').disabled = mode !== 'hd' || pattern.events.every(e => e.preset);
    $('testHaptic').disabled = !state.settings.haptics || mode === 'none';
    $('hapticStatus').textContent = !state.settings.haptics ? 'Turn on Haptics to test.' : mode === 'hd' ? 'HD haptics available · test on your phone to compare.' : mode === 'standard' ? 'Standard vibration · pulse timing approximates the HD feel.' : 'No haptic API here. Open in Brrrowser on your iPhone to feel these.';
    const bars = $('hapticBars'); bars.replaceChildren();
    const length = H.duration(pattern);
    $('hapticTimeline').style.setProperty('--haptic-duration', `${length}ms`);
    pattern.events.forEach(e => {
      const bar = node('i', e.duration ? 'haptic-buzz' : 'haptic-tap');
      bar.style.left = `${e.at/length*100}%`;
      bar.style.width = `${Math.max(1,(e.duration || 20)/length*100)}%`;
      bar.style.height = `${9+e.intensity*24}px`;
      bar.style.opacity = String(.35+e.intensity*.65);
      bars.append(bar);
    });
  }
  function selectHaptic(id) {
    stopHapticTest();
    mutate(s => { s.settings.hapticPattern = id; });
    renderHapticSettings();
  }
  $('hapticPattern').onchange = event => selectHaptic(event.target.value);
  function stepHaptic(direction) {
    const index = H.patterns.indexOf(H.get(state.settings.hapticPattern));
    selectHaptic(H.patterns[(index + direction + H.patterns.length) % H.patterns.length].id);
  }
  $('previousHaptic').onclick = () => stepHaptic(-1);
  $('nextHaptic').onclick = () => stepHaptic(1);
  $('testHaptic').onclick = () => {
    clearCelebration();
    if (!state.settings.haptics) return;
    const result = hapticPlayer.play(state.settings.hapticPattern, { engine: state.settings.hapticEngine, strength: state.settings.hapticStrength });
    if (result.mode === 'none') { renderHapticSettings(); return; }
    $('stopHaptic').hidden = false;
    $('testHaptic').textContent = 'Test again';
    $('hapticStatus').textContent = `Testing ${result.pattern.name} · ${result.mode === 'hd' ? 'HD haptics' : 'standard vibration'}`;
    void $('hapticTimeline').offsetWidth;
    $('hapticTimeline').classList.add('playing');
    hapticTestTimer = setTimeout(() => { stopHapticTest(); renderHapticSettings(); }, result.duration + 80);
  };
  $('stopHaptic').onclick = () => { stopHapticTest(); renderHapticSettings(); };
  ['Engine','Strength'].forEach(key => {
    $('haptic'+key).onchange = event => {
      stopHapticTest();
      const value = key === 'Strength' ? Number(event.target.value) : event.target.value;
      mutate(s => { s.settings['haptic'+key] = value; });
      renderHapticSettings();
    };
  });
  $('settingsDialog').addEventListener('close', () => { if (hapticTestTimer !== null) stopHapticTest(); });
  function updateGroupOptions() {
    const modality = $('bulkModality').value;
    $('bulkGroup').replaceChildren(new Option('All categories', '*'), ...[...new Set(state.types.filter(t => t.modality === modality).map(t => t.group))].map(g => new Option(g, g)));
  }
  function renderStudySettings() { typeList($('settingsTypes'), filteredTypes($('settingsSearch').value, settingsFavorites), editType); }
  function resetFutureGoalForm() {
    $('futureGoalForm').reset();
    $('futureGoalForm').elements.id.value = '';
    $('saveFutureGoal').textContent = 'Add future goal';
    $('cancelFutureGoal').hidden = true;
  }
  function renderFutureGoals() {
    const list = $('futureGoalList');
    list.replaceChildren();
    if (!state.futureGoals.length) { list.append(node('p', 'empty', 'No future goals yet.')); return; }
    state.futureGoals.forEach(goal => {
      const card = node('div', 'future-goal');
      const info = node('div', 'future-goal-info');
      info.append(node('strong', '', goal.name), node('span', '', goal.costCents === null ? 'Cost not set' : money(goal.costCents)));
      const actions = node('div', 'future-goal-actions');
      const use = node('button', '', 'Use goal');
      use.setAttribute('aria-label', `Use goal: ${goal.name}`);
      use.onclick = () => {
        const fields = $('goalForm').elements;
        fields.goalName.value = goal.name;
        fields.goalAmount.value = goal.costCents === null ? '' : (goal.costCents / 100).toFixed(2);
        $('goalForm').scrollIntoView({ block: 'start', behavior: 'instant' });
        (goal.costCents === null ? fields.goalAmount : fields.goalName).focus({ preventScroll: true });
        toast('Ready above · Save goal to activate');
      };
      const edit = node('button', '', 'Edit');
      edit.setAttribute('aria-label', `Edit future goal: ${goal.name}`);
      edit.onclick = () => {
        const f = $('futureGoalForm').elements;
        f.id.value = goal.id; f.name.value = goal.name; f.cost.value = goal.costCents === null ? '' : (goal.costCents / 100).toFixed(2);
        $('saveFutureGoal').textContent = 'Save idea'; $('cancelFutureGoal').hidden = false;
        f.name.focus();
      };
      const remove = node('button', 'remove-goal', 'Delete');
      remove.setAttribute('aria-label', `Delete future goal: ${goal.name}`);
      remove.onclick = () => {
        const removed = mutate(s => {
          const index = s.futureGoals.findIndex(g => g.id === goal.id);
          if (index < 0) return null;
          return { index, goal: s.futureGoals.splice(index, 1)[0] };
        });
        if (!removed) return;
        if ($('futureGoalForm').elements.id.value === goal.id) resetFutureGoalForm();
        toast('Future goal deleted', () => mutate(s => { if (!s.futureGoals.some(g => g.id === removed.goal.id)) s.futureGoals.splice(Math.min(removed.index, s.futureGoals.length), 0, removed.goal); }));
      };
      actions.append(use, edit, remove); card.append(info, actions); list.append(card);
    });
  }
  $('futureGoalForm').onsubmit = event => {
    event.preventDefault();
    const f = event.currentTarget.elements;
    const name = f.name.value.trim();
    if (!name) return toast('Enter a future goal name.');
    const goal = { id: f.id.value || E.id(), name, costCents: f.cost.value === '' ? null : Math.round(Number(f.cost.value) * 100) };
    const saved = mutate(s => {
      const index = s.futureGoals.findIndex(g => g.id === goal.id);
      if (index < 0) { if (s.futureGoals.length >= 1000) return false; s.futureGoals.push(goal); }
      else s.futureGoals[index] = goal;
      return true;
    });
    if (saved) { resetFutureGoalForm(); toast('Future goal saved'); }
    else if (saved === false) toast('Future goals list is full. Remove an idea first.');
  };
  $('cancelFutureGoal').onclick = resetFutureGoalForm;
  function populateSettings() {
    const f = $('goalForm').elements;
    f.goalName.value = state.settings.goalName; f.goalAmount.value = (state.settings.goalCents / 100).toFixed(2);
    ['sound', 'haptics', 'motion', 'keepAwake', 'countUp'].forEach(key => { $(key + 'Setting').checked = state.settings[key]; });
    const modalities = [...new Set(state.types.map(t => t.modality))];
    $('bulkModality').replaceChildren(...modalities.map(m => new Option(m, m)));
    $('modalities').replaceChildren(...modalities.map(m => new Option(m, m)));
    updateGroupOptions(); renderStudySettings(); renderFutureGoals(); renderHapticSettings();
  }
  $('settingsButton').onclick = () => { state = readStored(); populateSettings(); open($('settingsDialog')); };
  $('goalForm').onsubmit = event => { event.preventDefault(); const f = event.currentTarget.elements; const name = f.goalName.value.trim(); if (!name) return toast('Enter a goal name.'); mutate(s => { s.settings.goalName = name; s.settings.goalCents = Math.round(Number(f.goalAmount.value) * 100); }); toast('Goal saved'); };
  $('settingsSearch').oninput = renderStudySettings;
  $('settingsFavorites').onclick = () => { settingsFavorites = !settingsFavorites; $('settingsFavorites').setAttribute('aria-pressed', settingsFavorites); renderStudySettings(); };
  $('bulkModality').onchange = updateGroupOptions;
  $('bulkForm').onsubmit = event => {
    event.preventDefault(); const f = event.currentTarget.elements;
    const modality = f.modality.value, group = f.group.value;
    const targetMs = Math.round(Number(f.minutes.value) * 60000), rewardCents = Math.round(Number(f.dollars.value) * 100);
    const count = state.types.filter(t => t.modality === modality && (group === '*' || t.group === group)).length;
    confirm(`Update ${count} study types?`, `${modality}${group === '*' ? '' : ' · ' + group}: ${minutes(targetMs)} minutes and ${money(rewardCents)} per success. Past and active cases stay unchanged.`, () => {
      mutate(s => s.types.forEach(t => { if (t.modality === modality && (group === '*' || t.group === group)) Object.assign(t, { targetMs, rewardCents }); }));
      renderStudySettings(); toast(`${count} study types updated`);
    });
  };
  function editType(type = null) {
    const f = $('typeForm').elements;
    f.id.value = type?.id || ''; f.name.value = type?.name || ''; f.modality.value = type?.modality || 'MR'; f.group.value = type?.group || 'Custom';
    f.minutes.value = type ? minutes(type.targetMs) : 18; f.dollars.value = type ? (type.rewardCents / 100).toFixed(2) : '0.00'; f.favorite.checked = type?.favorite ?? true;
    $('typeDialogTitle').textContent = type ? 'Study settings' : 'Custom study'; open($('typeDialog'));
  }
  $('addType').onclick = () => editType();
  $('typeForm').onsubmit = event => {
    event.preventDefault(); const f = event.currentTarget.elements;
    const type = { id: f.id.value || E.id(), name: f.name.value.trim(), modality: f.modality.value.trim(), group: f.group.value.trim(), targetMs: Math.round(Number(f.minutes.value) * 60000), rewardCents: Math.round(Number(f.dollars.value) * 100), favorite: f.favorite.checked };
    if (!type.name || !type.modality || !type.group) return toast('Complete the study, modality, and category.');
    const saved = mutate(s => { const index = s.types.findIndex(t => t.id === type.id); if (index < 0) s.types.push(type); else s.types[index] = type; return true; });
    if (saved) { $('typeDialog').close(); renderStudySettings(); renderPicker(); toast('Study saved'); }
  };
  ['sound', 'haptics', 'motion', 'keepAwake', 'countUp'].forEach(key => { $(key + 'Setting').onchange = event => { const checked = event.target.checked; if (key === 'haptics') stopHapticTest(); mutate(s => { s.settings[key] = checked; }); if (key === 'haptics') renderHapticSettings(); }; });
  $('previewReward').onclick = () => { $('settingsDialog').close(); celebrate(selected().rewardCents || 200, true); };
  function backupText() {
    if (corrupt) { try { return localStorage.getItem(E.KEY) || JSON.stringify(state); } catch { /* Memory fallback. */ } }
    return JSON.stringify({ ...state, exportedAt: new Date().toISOString() }, null, 2);
  }
  const fileDate = () => new Date().toISOString().slice(0, 10);
  function download(text, type, filename) {
    const url = URL.createObjectURL(new Blob([text], { type }));
    const anchor = node('a'); anchor.href = url; anchor.download = filename; document.body.append(anchor); anchor.click(); anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }
  async function shareBackup() {
    const file = new File([backupText()], `afterglow-${fileDate()}.json`, { type: 'application/json' });
    try {
      if (navigator.canShare?.({ files: [file] })) await navigator.share({ title: 'Afterglow backup', files: [file] });
      else { download(backupText(), 'application/json', file.name); toast('Backup downloaded'); }
    } catch (error) { if (error.name !== 'AbortError') { download(backupText(), 'application/json', file.name); toast('Share unavailable · backup downloaded'); } }
  }
  $('shareBackup').onclick = shareBackup; $('quickShare').onclick = shareBackup;
  $('downloadBackup').onclick = () => download(backupText(), 'application/json', `afterglow-${fileDate()}.json`);
  $('downloadCsv').onclick = () => download('\uFEFF' + E.csv(state.records), 'text/csv;charset=utf-8', `afterglow-history-${fileDate()}.csv`);
  $('emailSummary').onclick = () => {
    const records = [...state.records].sort((a, b) => b.completedAt - a.completedAt);
    const lines = [`${state.settings.goalName}: ${money(E.total(records))} / ${money(state.settings.goalCents)}`, `${records.length} cases; ${records.filter(r => r.elapsedMs <= r.targetMs).length} within target.`, '', 'Recent cases (up to 12):', ...records.slice(0, 12).map(r => `${new Date(r.completedAt).toLocaleString()} | ${r.modality} ${r.typeName} | ${duration(r.elapsedMs)} / ${minutes(r.targetMs)}m | ${money(E.payout(r))}`), '', 'Full history and restore data are available through Share backup.'];
    window.location.href = `mailto:?subject=${encodeURIComponent('Afterglow · study summary')}&body=${encodeURIComponent(lines.join('\n'))}`;
  };
  $('importButton').onclick = () => $('importFile').click();
  $('importFile').onchange = async event => {
    const file = event.target.files[0]; event.target.value = ''; if (!file) return;
    if (file.size > 30 * 1024 * 1024) return toast('Backup is too large (30 MB maximum).');
    let imported;
    try { imported = E.validate(JSON.parse(await file.text())); }
    catch (error) { toast(error.message || 'This is not a valid backup.'); return; }
    confirm('Replace local data?', `${imported.records.length} cases and ${money(E.total(imported.records))} earned. This replaces this device’s history, settings, and active timer. Export first if you need the current data.`, () => {
      try { localStorage.setItem(E.KEY, JSON.stringify(imported)); }
      catch { toast('Could not restore: device storage is unavailable or full. Current data was kept.'); return; }
      corrupt = false; unsaved = false; state = imported; storageWarning(''); clearCelebration(); populateSettings(); render(); toast('Backup restored');
    });
  };
  window.addEventListener('storage', event => { if (event.key === E.KEY || event.key === null) { state = readStored(); render(); if ($('pickerDialog').open) renderPicker(); if ($('settingsDialog').open) renderStudySettings(); } });
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') { state = readStored(); render(); } else { stopHapticTest(); updateWakeLock(); } });
  window.addEventListener('pageshow', () => { state = readStored(); render(); });
  setInterval(() => { if (document.visibilityState === 'visible') renderTimer(); }, 250);
  // Keyboard shortcuts never intercept inputs or open sheets.
  document.addEventListener('keydown', event => {
    if (event.repeat || document.querySelector('dialog[open]') || event.target.closest('button,a,input,select,textarea')) return;
    if (event.code === 'Space') { event.preventDefault(); $('toggleButton').click(); }
  });
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js', { scope: './' }).catch(() => {});
  render();
})();
