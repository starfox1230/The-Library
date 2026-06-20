(() => {
  "use strict";

  const STORAGE_KEY = "rvu-rush-neon-shift-v1";
  const XP_PER_LEVEL = 600;
  const COMBO_WINDOW_MS = 12 * 60 * 1000;
  const modalityKeys = Object.keys(window.RVU_MODALITIES);
  const studies = window.RVU_STUDIES;
  const studyById = new Map(studies.map((study) => [study.id, study]));
  const studyByCode = new Map();
  studies.forEach((study) => {
    if (!studyByCode.has(study.code)) studyByCode.set(study.code, study);
  });
  const comprehensiveMerges = window.RVU_COMPREHENSIVE_MERGES || {};
  const linkPresets = window.RVU_LINK_PRESETS || [];
  const linkCompanions = window.RVU_LINK_COMPANIONS || {};
  const $ = (id) => document.getElementById(id);

  const els = {
    dateLabel: $("dateLabel"),
    studyCount: $("studyCount"),
    comboCount: $("comboCount"),
    dayStreak: $("dayStreak"),
    undoButton: $("undoButton"),
    mobileRvuTotal: $("mobileRvuTotal"),
    mobileStudyCount: $("mobileStudyCount"),
    mobileUndoButton: $("mobileUndoButton"),
    mobileGoalFill: $("mobileGoalFill"),
    mobileMoreButton: $("mobileMoreButton"),
    shiftRank: $("shiftRank"),
    levelValue: $("levelValue"),
    goalReactor: $("goalReactor"),
    goalProgress: $("goalProgress"),
    goalDesc: $("goalDesc"),
    rvuTotal: $("rvuTotal"),
    goalCurrent: $("goalCurrent"),
    goalTarget: $("goalTarget"),
    xpLabel: $("xpLabel"),
    xpFill: $("xpFill"),
    attributeGrid: $("attributeGrid"),
    runRate: $("runRate"),
    topModality: $("topModality"),
    topModalityDetail: $("topModalityDetail"),
    achievementCount: $("achievementCount"),
    pulseChart: $("pulseChart"),
    recentGrid: $("recentGrid"),
    modalityTabs: $("modalityTabs"),
    studySearch: $("studySearch"),
    studyGrid: $("studyGrid"),
    linkModeButton: $("linkModeButton"),
    linkTray: $("linkTray"),
    linkTrayTotal: $("linkTrayTotal"),
    linkSelection: $("linkSelection"),
    linkSuggestions: $("linkSuggestions"),
    linkPresets: $("linkPresets"),
    clearLinkButton: $("clearLinkButton"),
    logLinkButton: $("logLinkButton"),
    catalogCount: $("catalogCount"),
    toastStack: $("toastStack"),
    drawerButton: $("drawerButton"),
    drawer: $("drawer"),
    drawerBackdrop: $("drawerBackdrop"),
    closeDrawerButton: $("closeDrawerButton"),
    historyList: $("historyList"),
    exportButton: $("exportButton"),
    goalInput: $("goalInput"),
    soundToggle: $("soundToggle"),
    motionToggle: $("motionToggle"),
    customStudyForm: $("customStudyForm"),
    customStudyName: $("customStudyName"),
    customStudyModality: $("customStudyModality"),
    customStudyRvu: $("customStudyRvu"),
    resetButton: $("resetButton"),
  };

  let activeModality = "XR";
  let visibleStudies = [];
  let linkMode = false;
  let linkSelectionIds = [];
  let audioContext = null;
  let favoriteHoldTimer = null;
  let favoriteHoldTarget = null;
  let favoriteHoldStart = null;
  let suppressStudyClickUntil = 0;
  let suppressStudyClickId = null;
  const compactDevice = window.matchMedia("(max-width: 700px), (pointer: coarse)").matches;

  function localDateKey(date = new Date()) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function defaultState() {
    return {
      settings: {
        goal: 40,
        sound: true,
        reducedFx: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      },
      days: {},
      usage: {},
      recentStudyIds: [],
      favoriteStudyIds: [],
    };
  }

  function loadState() {
    try {
      const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
      const fallback = defaultState();
      if (!saved || typeof saved !== "object") return fallback;
      return {
        ...fallback,
        ...saved,
        settings: { ...fallback.settings, ...(saved.settings || {}) },
        days: saved.days || {},
        usage: saved.usage || {},
        recentStudyIds: Array.isArray(saved.recentStudyIds) ? saved.recentStudyIds : [],
        favoriteStudyIds: Array.isArray(saved.favoriteStudyIds) ? saved.favoriteStudyIds : [],
      };
    } catch {
      return defaultState();
    }
  }

  let state = loadState();

  function saveState() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  function getToday() {
    const key = localDateKey();
    if (!state.days[key]) state.days[key] = { entries: [] };
    if (!Array.isArray(state.days[key].entries)) state.days[key].entries = [];
    return state.days[key];
  }

  function modalityMeta(key) {
    return window.RVU_MODALITIES[key] || window.RVU_MODALITIES.XR;
  }

  function esc(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function formatTime(timestamp) {
    return new Intl.DateTimeFormat(undefined, {
      hour: "numeric",
      minute: "2-digit",
    }).format(new Date(timestamp));
  }

  function derived(entries = getToday().entries) {
    const totalWrvu = entries.reduce((sum, entry) => sum + Number(entry.wrvu || 0), 0);
    const xp = entries.reduce((sum, entry) => sum + Number(entry.xp || 0), 0);
    const level = Math.floor(xp / XP_PER_LEVEL) + 1;
    const levelXp = xp % XP_PER_LEVEL;
    const modalityTotals = Object.fromEntries(modalityKeys.map((key) => [
      key,
      { count: 0, wrvu: 0 },
    ]));

    entries.forEach((entry) => {
      if (!modalityTotals[entry.modality]) {
        modalityTotals[entry.modality] = { count: 0, wrvu: 0 };
      }
      modalityTotals[entry.modality].count += 1;
      modalityTotals[entry.modality].wrvu += Number(entry.wrvu || 0);
    });

    const sortedModalities = Object.entries(modalityTotals)
      .sort((a, b) => b[1].wrvu - a[1].wrvu);
    const top = sortedModalities[0];
    const last = entries.at(-1);
    const combo = last && Date.now() - last.timestamp <= COMBO_WINDOW_MS
      ? Number(last.combo || 1)
      : 0;
    const elapsedHours = entries.length > 1
      ? Math.max((entries.at(-1).timestamp - entries[0].timestamp) / 3600000, 0.25)
      : 0;
    const runRate = elapsedHours ? totalWrvu / elapsedHours : totalWrvu;

    return {
      totalWrvu,
      xp,
      level,
      levelXp,
      modalityTotals,
      top,
      combo,
      runRate,
      achievements: achievementList(entries, totalWrvu, modalityTotals),
    };
  }

  function achievementList(entries, totalWrvu, modalityTotals) {
    const unlocked = [];
    if (entries.length >= 1) unlocked.push("FIRST LIGHT");
    if (entries.length >= 10) unlocked.push("DOUBLE DIGITS");
    if (entries.length >= 25) unlocked.push("QUEUE CRUSHER");
    if (entries.length >= 50) unlocked.push("SHIFT OVERDRIVE");
    if (totalWrvu >= 5) unlocked.push("FIVE ALIVE");
    if (totalWrvu >= 10) unlocked.push("TEN-RVU TITAN");
    if (totalWrvu >= 20) unlocked.push("REACTOR HOT");
    if (totalWrvu >= Number(state.settings.goal || 40)) unlocked.push("GOAL SHATTERED");
    Object.entries(modalityTotals).forEach(([key, value]) => {
      if (value.count >= 5) unlocked.push(`${key} SPECIALIST`);
    });
    return unlocked;
  }

  function dayStreak() {
    let streak = 0;
    const cursor = new Date();
    while (true) {
      const key = localDateKey(cursor);
      const entries = state.days[key]?.entries;
      if (!entries?.length) break;
      streak += 1;
      cursor.setDate(cursor.getDate() - 1);
    }
    return streak;
  }

  function rankName(totalWrvu) {
    if (totalWrvu >= 50) return "NEON SHIFT OVERLORD";
    if (totalWrvu >= 35) return "SPECTRAL COMMANDER";
    if (totalWrvu >= 25) return "RECON ACE";
    if (totalWrvu >= 15) return "LASER DIAGNOSTICIAN";
    if (totalWrvu >= 7.5) return "PIXEL READER";
    if (totalWrvu > 0) return "SIGNAL RUNNER";
    return "BOOT SEQUENCE";
  }

  function render() {
    const entries = getToday().entries;
    const stats = derived(entries);
    const goal = Math.max(1, Number(state.settings.goal || 40));
    const progress = Math.min(stats.totalWrvu / goal, 1);
    const circumference = 2 * Math.PI * 98;

    els.dateLabel.textContent = new Intl.DateTimeFormat(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
    }).format(new Date()).toUpperCase();
    els.studyCount.textContent = entries.length;
    els.mobileStudyCount.textContent = entries.length;
    els.comboCount.textContent = `x${stats.combo}`;
    const streak = dayStreak();
    els.dayStreak.textContent = `${streak} DAY${streak === 1 ? "" : "S"}`;
    els.undoButton.disabled = entries.length === 0;
    els.mobileUndoButton.disabled = entries.length === 0;
    els.shiftRank.textContent = rankName(stats.totalWrvu);
    els.levelValue.textContent = stats.level;
    els.rvuTotal.textContent = stats.totalWrvu.toFixed(2);
    els.mobileRvuTotal.textContent = stats.totalWrvu.toFixed(2);
    els.mobileGoalFill.style.width = `${progress * 100}%`;
    els.goalCurrent.textContent = stats.totalWrvu.toFixed(2);
    els.goalTarget.textContent = goal.toFixed(0);
    els.goalProgress.style.strokeDasharray = String(circumference);
    els.goalProgress.style.strokeDashoffset = String(circumference * (1 - progress));
    els.goalProgress.style.stroke = progress >= 1 ? "var(--lime)" : "var(--cyan)";
    els.goalDesc.textContent = `${Math.round(progress * 100)} percent complete`;
    els.xpLabel.textContent = `${stats.levelXp} / ${XP_PER_LEVEL} XP`;
    els.xpFill.style.width = `${(stats.levelXp / XP_PER_LEVEL) * 100}%`;
    els.runRate.textContent = stats.runRate.toFixed(1);
    els.achievementCount.textContent = stats.achievements.length;
    els.goalInput.value = goal;
    els.soundToggle.checked = Boolean(state.settings.sound);
    els.motionToggle.checked = Boolean(state.settings.reducedFx);

    if (stats.top && stats.top[1].count > 0) {
      els.topModality.textContent = modalityMeta(stats.top[0]).short;
      els.topModality.style.color = modalityMeta(stats.top[0]).color;
      els.topModalityDetail.textContent =
        `${stats.top[1].count} STUDIES // ${stats.top[1].wrvu.toFixed(2)} wRVU`;
    } else {
      els.topModality.textContent = "—";
      els.topModality.style.color = "";
      els.topModalityDetail.textContent = "NO DATA";
    }

    renderAttributes(stats.modalityTotals);
    renderPulse(entries);
    renderRecents();
    renderStudies();
    renderHistory();
    window.rvuFx?.setReduced(Boolean(state.settings.reducedFx));
  }

  function renderAttributes(totals) {
    const maxCount = Math.max(5, ...Object.values(totals).map((item) => item.count));
    els.attributeGrid.innerHTML = modalityKeys.map((key) => {
      const meta = modalityMeta(key);
      const value = totals[key] || { count: 0, wrvu: 0 };
      const width = Math.max(2, (value.count / maxCount) * 100);
      return `
        <div class="attribute" style="--attr-color:${meta.color}">
          <div class="attribute-top">
            <span class="attribute-name">${meta.stat}</span>
            <strong>${value.count}</strong>
          </div>
          <div class="attribute-track"><div style="width:${width}%"></div></div>
        </div>`;
    }).join("");
  }

  function renderPulse(entries) {
    const recent = entries.slice(-18);
    if (!recent.length) {
      els.pulseChart.innerHTML = Array.from({ length: 18 }, (_, index) =>
        `<i class="pulse-bar" style="--bar-height:${8 + (index % 4) * 4}px;--bar-color:#362a53"></i>`
      ).join("");
      return;
    }
    const max = Math.max(...recent.map((entry) => Number(entry.wrvu || 0)), 1);
    els.pulseChart.innerHTML = recent.map((entry) => {
      const height = Math.max(10, (Number(entry.wrvu) / max) * 30);
      return `<i class="pulse-bar" title="${esc(entry.label)}: ${Number(entry.wrvu).toFixed(2)} wRVU"
        style="--bar-height:${height}px;--bar-color:${modalityMeta(entry.modality).color}"></i>`;
    }).join("");
  }

  function renderModalityTabs() {
    els.modalityTabs.innerHTML = modalityKeys.map((key, index) => {
      const meta = modalityMeta(key);
      return `
        <button class="modality-button ${activeModality === key ? "active" : ""}"
          type="button" role="tab" aria-selected="${activeModality === key}"
          data-modality="${key}" style="--modality-color:${meta.color}"
          title="Alt+${index + 1}: ${meta.label}">
          <span>${meta.short}</span>${meta.label}
        </button>`;
    }).join("");
  }

  function rankedStudies() {
    const query = els.studySearch.value.trim().toLowerCase();
    const source = query
      ? studies.filter((study) => study.search.includes(query))
      : studies.filter((study) => study.modality === activeModality);
    return source.sort((a, b) =>
      a.label.localeCompare(b.label, undefined, { sensitivity: "base", numeric: true })
      || a.code.localeCompare(b.code)
    );
  }

  function studyCardMarkup(study, index, favoriteCopy = false) {
    const meta = modalityMeta(study.modality);
    const selected = linkSelectionIds.includes(study.id);
    const favorite = state.favoriteStudyIds.includes(study.id);
    const action = linkMode
      ? `${selected ? "Remove from" : "Add to"} linked set`
      : "Log";
    return `
      <button class="study-card ${selected ? "link-selected" : ""} ${favorite ? "favorite" : ""}"
        type="button" data-study-id="${study.id}" data-favorite-copy="${favoriteCopy}"
        style="--card-color:${meta.color}"
        title="${action} ${esc(study.label)}. Press and hold to ${favorite ? "remove from" : "add to"} favorites.">
        ${index < 9 && !favoriteCopy ? `<span class="study-key">${index + 1}</span>` : ""}
        ${favorite ? `<span class="favorite-star" aria-hidden="true">★</span>` : ""}
        <span>
          <span class="study-card-title">${esc(study.label)}</span>
          <small class="study-card-meta">${meta.label.toUpperCase()} // CPT ${study.code}</small>
        </span>
        <strong class="study-card-rvu">+${study.wrvu.toFixed(2)}</strong>
      </button>`;
  }

  function renderStudies() {
    renderModalityTabs();
    renderLinkTray();
    visibleStudies = rankedStudies();
    if (!visibleStudies.length) {
      els.studyGrid.innerHTML = `
        <div class="no-results">NO MATCHING STUDIES.<br>Try a body part, modality, or CPT code.</div>`;
      return;
    }

    const favorites = visibleStudies.filter((study) =>
      state.favoriteStudyIds.includes(study.id)
    );
    const favoriteBlock = favorites.length
      ? `
        <div class="study-section-heading favorite-heading">
          <span>★ FAVORITES</span>
          <small>PRESS + HOLD TO REMOVE</small>
        </div>
        ${favorites.map((study) => studyCardMarkup(study, -1, true)).join("")}
        <div class="study-section-heading">
          <span>ALL ${els.studySearch.value.trim() ? "MATCHES" : modalityMeta(activeModality).label.toUpperCase()}</span>
          <small>ALPHABETICAL</small>
        </div>`
      : "";
    els.studyGrid.innerHTML =
      favoriteBlock + visibleStudies.map((study, index) => studyCardMarkup(study, index)).join("");
  }

  function toggleFavorite(study) {
    const favorite = state.favoriteStudyIds.includes(study.id);
    state.favoriteStudyIds = favorite
      ? state.favoriteStudyIds.filter((id) => id !== study.id)
      : [...state.favoriteStudyIds, study.id];
    saveState();
    renderStudies();
    showToast(
      favorite ? "FAVORITE REMOVED" : "GOLD FAVORITE ADDED",
      study.label,
      favorite ? "☆" : "★",
      "#ffbd2e"
    );
    if (navigator.vibrate) navigator.vibrate(favorite ? 25 : [25, 35, 25]);
  }

  function selectedLinkStudies() {
    return linkSelectionIds.map((id) => studyById.get(id)).filter(Boolean);
  }

  function renderLinkTray() {
    els.linkModeButton.setAttribute("aria-pressed", String(linkMode));
    els.linkTray.hidden = !linkMode;
    if (!linkMode) return;

    const selected = selectedLinkStudies();
    const total = selected.reduce((sum, study) => sum + study.wrvu, 0);
    els.linkTrayTotal.textContent =
      `${selected.length} STUD${selected.length === 1 ? "Y" : "IES"} // ${total.toFixed(2)} wRVU`;
    els.logLinkButton.disabled = selected.length < 2;
    els.linkSelection.innerHTML = selected.length
      ? selected.map((study) => `
          <button class="link-chip" type="button" data-remove-link="${study.id}"
            style="--chip-color:${modalityMeta(study.modality).color}">
            ${modalityMeta(study.modality).short} ${esc(study.label)}
          </button>`).join("")
      : `<span class="link-selection-empty">Choose two or more separately read studies below.</span>`;

    const selectedCodes = new Set(selected.map((study) => study.code));
    const companionCodes = [...new Set(selected.flatMap(
      (study) => linkCompanions[study.code] || []
    ))].filter((code) => !selectedCodes.has(code));
    els.linkSuggestions.innerHTML = companionCodes.map((code) => {
      const study = studyByCode.get(code);
      if (!study) return "";
      return `
        <button class="suggestion-chip" type="button" data-add-link="${study.id}"
          style="--chip-color:${modalityMeta(study.modality).color}">
          + ${esc(study.label)}
        </button>`;
    }).join("");

    els.linkPresets.innerHTML = selected.length ? "" : linkPresets.map((preset) => `
      <button class="preset-chip" type="button" data-link-preset="${preset.id}">
        ${esc(preset.label)}
      </button>`).join("");
  }

  function setLinkMode(enabled) {
    linkMode = enabled;
    if (!enabled) linkSelectionIds = [];
    renderStudies();
  }

  function toggleLinkedStudy(study) {
    const existingIndex = linkSelectionIds.indexOf(study.id);
    if (existingIndex >= 0) {
      linkSelectionIds.splice(existingIndex, 1);
      renderStudies();
      return;
    }

    for (const selectedId of linkSelectionIds) {
      const selectedStudy = studyById.get(selectedId);
      const pair = [selectedStudy.code, study.code].sort().join("+");
      const replacementCode = comprehensiveMerges[pair];
      const replacement = replacementCode ? studyByCode.get(replacementCode) : null;
      if (replacement) {
        linkSelectionIds = linkSelectionIds.filter((id) => id !== selectedId);
        if (!linkSelectionIds.includes(replacement.id)) linkSelectionIds.push(replacement.id);
        activeModality = replacement.modality;
        showToast(
          "SMART MERGE // COMPREHENSIVE CODE",
          `${selectedStudy.label} + ${study.label} → ${replacement.label}`,
          replacement.code,
          "#ffbd2e"
        );
        renderStudies();
        return;
      }
    }

    linkSelectionIds.push(study.id);
    renderStudies();
  }

  function applyLinkPreset(presetId) {
    const preset = linkPresets.find((item) => item.id === presetId);
    if (!preset) return;
    linkSelectionIds = preset.codes
      .map((code) => studyByCode.get(code)?.id)
      .filter(Boolean);
    const first = studyById.get(linkSelectionIds[0]);
    if (first) activeModality = first.modality;
    renderStudies();
  }

  function renderRecents() {
    const recent = state.recentStudyIds
      .map((id) => studyById.get(id))
      .filter(Boolean)
      .slice(0, 3);
    if (!recent.length) {
      els.recentGrid.innerHTML =
        `<div class="empty-recents">YOUR LAST THREE STUDIES WILL APPEAR HERE</div>`;
      return;
    }
    const keys = ["Q", "W", "E"];
    els.recentGrid.innerHTML = recent.map((study, index) => {
      const meta = modalityMeta(study.modality);
      return `
        <button class="recent-button" type="button" data-study-id="${study.id}"
          style="--card-color:${meta.color}">
          <span class="recent-key">${keys[index]}</span>
          <strong>${esc(study.label)}</strong>
          <small>${meta.short} // +${study.wrvu.toFixed(2)}</small>
        </button>`;
    }).join("");
  }

  function renderHistory() {
    const entries = getToday().entries;
    if (!entries.length) {
      els.historyList.innerHTML =
        `<div class="empty-history">NO STUDIES LOGGED YET.<br>THE SHIFT CORE IS WAITING.</div>`;
      return;
    }
    const groups = [];
    const groupIndex = new Map();
    entries.forEach((entry) => {
      const key = entry.groupId || entry.id;
      if (!groupIndex.has(key)) {
        groupIndex.set(key, groups.length);
        groups.push({ key, entries: [] });
      }
      groups[groupIndex.get(key)].entries.push(entry);
    });
    els.historyList.innerHTML = groups.reverse().map((group) => {
      const linked = group.entries.length > 1;
      const first = group.entries[0];
      const total = group.entries.reduce((sum, entry) => sum + Number(entry.wrvu), 0);
      const label = linked
        ? `⛓ ${group.entries.map((entry) => entry.label).join(" + ")}`
        : first.label;
      const deleteAttr = linked
        ? `data-delete-group="${first.groupId}"`
        : `data-delete-entry="${first.id}"`;
      return `
        <div class="history-item" style="--history-color:${modalityMeta(first.modality).color}">
          <span class="history-time">${formatTime(first.timestamp)}</span>
          <span class="history-title" title="${esc(label)}">${esc(label)}</span>
          <strong class="history-rvu">+${total.toFixed(2)}</strong>
          <button class="history-delete" type="button" ${deleteAttr}
            aria-label="Delete ${esc(label)}">×</button>
        </div>`;
    }).join("");
  }

  function logStudy(study, options = {}) {
    const entries = getToday().entries;
    const before = derived(entries);
    const now = Date.now();
    const last = entries.at(-1);
    const combo = last && now - last.timestamp <= COMBO_WINDOW_MS
      ? Number(last.combo || 1) + 1
      : 1;
    const multiplier = 1 + Math.min(combo - 1, 10) * 0.08;
    const xp = Math.round((Number(study.wrvu) * 100 + 25) * multiplier);
    const entry = {
      id: `${now}-${Math.random().toString(16).slice(2)}`,
      studyId: study.id || null,
      label: study.label,
      modality: study.modality,
      code: study.code || "CUSTOM",
      wrvu: Number(study.wrvu),
      timestamp: now,
      combo,
      xp,
    };
    entries.push(entry);

    if (study.id && studyById.has(study.id)) {
      state.usage[study.id] = Number(state.usage[study.id] || 0) + 1;
      state.recentStudyIds = [study.id, ...state.recentStudyIds.filter((id) => id !== study.id)]
        .slice(0, 10);
      activeModality = study.modality;
    }

    saveState();
    render();
    rewardFeedback(entry, before, derived(entries), options.custom);
  }

  function logLinkedSet() {
    const selected = selectedLinkStudies();
    if (selected.length < 2) return;
    const entries = getToday().entries;
    const before = derived(entries);
    const now = Date.now();
    const groupId = `linked-${now}-${Math.random().toString(16).slice(2)}`;
    const previous = entries.at(-1);
    const startingCombo = previous && now - previous.timestamp <= COMBO_WINDOW_MS
      ? Number(previous.combo || 1) + 1
      : 1;
    let totalXp = 0;

    selected.forEach((study, index) => {
      const combo = startingCombo + index;
      const multiplier = 1 + Math.min(combo - 1, 10) * 0.08;
      const xp = Math.round((Number(study.wrvu) * 100 + 25) * multiplier);
      totalXp += xp;
      entries.push({
        id: `${now + index}-${Math.random().toString(16).slice(2)}`,
        studyId: study.id,
        label: study.label,
        modality: study.modality,
        code: study.code,
        wrvu: Number(study.wrvu),
        timestamp: now + index,
        combo,
        xp,
        groupId,
        groupSize: selected.length,
        groupIndex: index,
      });
      state.usage[study.id] = Number(state.usage[study.id] || 0) + 1;
    });

    state.recentStudyIds = [
      ...selected.map((study) => study.id).reverse(),
      ...state.recentStudyIds.filter((id) => !selected.some((study) => study.id === id)),
    ].slice(0, 10);
    const totalWrvu = selected.reduce((sum, study) => sum + study.wrvu, 0);
    const rewardEntry = {
      label: `LINKED SET // ${selected.length} STUDIES`,
      modality: selected[0].modality,
      wrvu: totalWrvu,
      xp: totalXp,
      combo: startingCombo + selected.length - 1,
    };

    linkMode = false;
    linkSelectionIds = [];
    saveState();
    render();
    rewardFeedback(rewardEntry, before, derived(entries));
  }

  function rewardFeedback(entry, before, after, custom = false) {
    const meta = modalityMeta(entry.modality);
    showToast(
      custom ? "CUSTOM SIGNAL LOGGED" : entry.label,
      `+${entry.xp} XP // COMBO x${entry.combo}`,
      `+${entry.wrvu.toFixed(2)}`,
      meta.color
    );

    const newAchievements = after.achievements.filter(
      (achievement) => !before.achievements.includes(achievement)
    );
    if (newAchievements.length) {
      window.setTimeout(() => {
        showToast("ACHIEVEMENT UNLOCKED", newAchievements[0], "◆", "#b6ff35");
      }, 240);
    }

    els.goalReactor.classList.remove("flash-reward");
    void els.goalReactor.offsetWidth;
    els.goalReactor.classList.add("flash-reward");
    window.dispatchEvent(new CustomEvent("rvu:logged", { detail: entry }));
    playRewardSound(entry.wrvu, entry.combo);
  }

  function showToast(title, subtitle, amount, color) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.style.setProperty("--toast-color", color);
    toast.innerHTML = `
      <span class="toast-icon">◆</span>
      <span><strong>${esc(title)}</strong><small>${esc(subtitle)}</small></span>
      <strong class="toast-rvu">${esc(amount)}</strong>`;
    els.toastStack.append(toast);
    window.setTimeout(() => toast.remove(), 2850);
  }

  function playRewardSound(wrvu, combo) {
    if (!state.settings.sound) return;
    try {
      audioContext ||= new (window.AudioContext || window.webkitAudioContext)();
      const now = audioContext.currentTime;
      [0, 0.07, 0.14].forEach((delay, index) => {
        const oscillator = audioContext.createOscillator();
        const gain = audioContext.createGain();
        oscillator.type = index === 2 ? "triangle" : "square";
        oscillator.frequency.setValueAtTime(
          220 + Number(wrvu) * 75 + index * 115 + Math.min(combo, 8) * 9,
          now + delay
        );
        gain.gain.setValueAtTime(0.0001, now + delay);
        gain.gain.exponentialRampToValueAtTime(0.045, now + delay + 0.012);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + delay + 0.11);
        oscillator.connect(gain).connect(audioContext.destination);
        oscillator.start(now + delay);
        oscillator.stop(now + delay + 0.12);
      });
    } catch {
      // Audio is optional; tracking must still work in locked-down browsers.
    }
  }

  function undoLast() {
    const entries = getToday().entries;
    if (!entries.length) return;
    const last = entries.at(-1);
    const removed = last.groupId
      ? entries.splice(entries.findIndex((entry) => entry.groupId === last.groupId))
      : [entries.pop()];
    const total = removed.reduce((sum, entry) => sum + Number(entry.wrvu), 0);
    const label = removed.length > 1 ? `LINKED SET // ${removed.length} STUDIES` : removed[0].label;
    saveState();
    render();
    showToast("LAST LOG UNDONE", label, `-${total.toFixed(2)}`, "#ff426f");
  }

  function deleteEntry(id) {
    const entries = getToday().entries;
    const index = entries.findIndex((entry) => entry.id === id);
    if (index < 0) return;
    const [removed] = entries.splice(index, 1);
    saveState();
    render();
    showToast("ENTRY REMOVED", removed.label, `-${Number(removed.wrvu).toFixed(2)}`, "#ff426f");
  }

  function deleteGroup(groupId) {
    const entries = getToday().entries;
    const removed = entries.filter((entry) => entry.groupId === groupId);
    if (!removed.length) return;
    state.days[localDateKey()].entries = entries.filter((entry) => entry.groupId !== groupId);
    const total = removed.reduce((sum, entry) => sum + Number(entry.wrvu), 0);
    saveState();
    render();
    showToast(
      "LINKED SET REMOVED",
      `${removed.length} studies`,
      `-${total.toFixed(2)}`,
      "#ff426f"
    );
  }

  function openDrawer() {
    els.drawerBackdrop.hidden = false;
    els.drawer.setAttribute("aria-hidden", "false");
    requestAnimationFrame(() => els.drawer.classList.add("open"));
    els.closeDrawerButton.focus();
  }

  function closeDrawer() {
    els.drawer.classList.remove("open");
    els.drawer.setAttribute("aria-hidden", "true");
    window.setTimeout(() => {
      els.drawerBackdrop.hidden = true;
      els.drawerButton.focus();
    }, 220);
  }

  function setMobileView(view) {
    const normalized = view === "stats" ? "stats" : "log";
    document.body.dataset.mobileView = normalized;
    document.querySelectorAll("[data-mobile-view]").forEach((button) => {
      const active = button.dataset.mobileView === normalized;
      button.classList.toggle("active", active);
      button.setAttribute("aria-pressed", String(active));
    });
    if (normalized === "stats") {
      document.querySelector(".arena-panel").scrollTop = 0;
    }
  }

  function exportCsv() {
    const entries = getToday().entries;
    if (!entries.length) {
      showToast("NOTHING TO EXPORT", "Log at least one study first.", "—", "#ffbd2e");
      return;
    }
    const rows = [
      ["date", "time", "modality", "study", "cpt", "work_rvu", "xp", "combo", "linked_group"],
      ...entries.map((entry) => [
        localDateKey(new Date(entry.timestamp)),
        formatTime(entry.timestamp),
        entry.modality,
        entry.label,
        entry.code,
        Number(entry.wrvu).toFixed(2),
        entry.xp,
        entry.combo,
        entry.groupId || "",
      ]),
    ];
    const csv = rows.map((row) =>
      row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")
    ).join("\n");
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `rvu-rush-${localDateKey()}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function resetToday() {
    if (!getToday().entries.length) return;
    if (!window.confirm("Reset every study logged today? This cannot be undone.")) return;
    state.days[localDateKey()] = { entries: [] };
    saveState();
    render();
    showToast("SHIFT RESET", "Today's reactor is back to zero.", "0.00", "#ff426f");
  }

  function bindEvents() {
    els.modalityTabs.addEventListener("click", (event) => {
      const button = event.target.closest("[data-modality]");
      if (!button) return;
      activeModality = button.dataset.modality;
      els.studySearch.value = "";
      renderStudies();
      els.studyGrid.scrollTop = 0;
    });

    const logFromButton = (event) => {
      const button = event.target.closest("[data-study-id]");
      if (!button) return;
      const study = studyById.get(button.dataset.studyId);
      if (!study) return;
      if (study.id === suppressStudyClickId && Date.now() < suppressStudyClickUntil) {
        event.preventDefault();
        suppressStudyClickId = null;
        return;
      }
      if (linkMode) toggleLinkedStudy(study);
      else logStudy(study);
    };
    els.studyGrid.addEventListener("click", logFromButton);
    els.studyGrid.addEventListener("contextmenu", (event) => {
      if (event.target.closest("[data-study-id]")) event.preventDefault();
    });
    els.studyGrid.addEventListener("pointerdown", (event) => {
      if (event.button !== 0) return;
      const button = event.target.closest("[data-study-id]");
      if (!button) return;
      const study = studyById.get(button.dataset.studyId);
      if (!study) return;
      clearTimeout(favoriteHoldTimer);
      favoriteHoldTarget = button;
      favoriteHoldStart = { x: event.clientX, y: event.clientY, id: study.id };
      button.classList.add("holding-favorite");
      favoriteHoldTimer = window.setTimeout(() => {
        suppressStudyClickId = study.id;
        suppressStudyClickUntil = Date.now() + 800;
        toggleFavorite(study);
        favoriteHoldTimer = null;
        favoriteHoldTarget = null;
        favoriteHoldStart = null;
      }, 575);
    });
    const cancelFavoriteHold = () => {
      clearTimeout(favoriteHoldTimer);
      favoriteHoldTimer = null;
      favoriteHoldTarget?.classList.remove("holding-favorite");
      favoriteHoldTarget = null;
      favoriteHoldStart = null;
    };
    els.studyGrid.addEventListener("pointermove", (event) => {
      if (!favoriteHoldStart) return;
      if (
        Math.abs(event.clientX - favoriteHoldStart.x) > 10
        || Math.abs(event.clientY - favoriteHoldStart.y) > 10
      ) {
        cancelFavoriteHold();
      }
    });
    els.studyGrid.addEventListener("pointerup", cancelFavoriteHold);
    els.studyGrid.addEventListener("pointercancel", cancelFavoriteHold);
    els.studyGrid.addEventListener("pointerleave", cancelFavoriteHold);
    els.recentGrid.addEventListener("click", logFromButton);
    els.linkModeButton.addEventListener("click", () => setLinkMode(!linkMode));
    els.clearLinkButton.addEventListener("click", () => {
      linkSelectionIds = [];
      renderStudies();
    });
    els.logLinkButton.addEventListener("click", logLinkedSet);
    els.linkTray.addEventListener("click", (event) => {
      const removeButton = event.target.closest("[data-remove-link]");
      if (removeButton) {
        const study = studyById.get(removeButton.dataset.removeLink);
        if (study) toggleLinkedStudy(study);
        return;
      }
      const addButton = event.target.closest("[data-add-link]");
      if (addButton) {
        const study = studyById.get(addButton.dataset.addLink);
        if (study) toggleLinkedStudy(study);
        return;
      }
      const presetButton = event.target.closest("[data-link-preset]");
      if (presetButton) applyLinkPreset(presetButton.dataset.linkPreset);
    });
    els.studySearch.addEventListener("input", () => {
      renderStudies();
      els.studyGrid.scrollTop = 0;
    });
    els.undoButton.addEventListener("click", undoLast);
    els.mobileUndoButton.addEventListener("click", undoLast);
    els.drawerButton.addEventListener("click", openDrawer);
    els.mobileMoreButton.addEventListener("click", openDrawer);
    document.querySelectorAll("[data-mobile-view]").forEach((button) => {
      button.addEventListener("click", () => setMobileView(button.dataset.mobileView));
    });
    els.closeDrawerButton.addEventListener("click", closeDrawer);
    els.drawerBackdrop.addEventListener("click", closeDrawer);
    els.exportButton.addEventListener("click", exportCsv);
    els.resetButton.addEventListener("click", resetToday);
    els.historyList.addEventListener("click", (event) => {
      const entryButton = event.target.closest("[data-delete-entry]");
      if (entryButton) {
        deleteEntry(entryButton.dataset.deleteEntry);
        return;
      }
      const groupButton = event.target.closest("[data-delete-group]");
      if (groupButton) deleteGroup(groupButton.dataset.deleteGroup);
    });

    els.goalInput.addEventListener("change", () => {
      state.settings.goal = Math.min(250, Math.max(1, Number(els.goalInput.value) || 40));
      saveState();
      render();
    });
    els.soundToggle.addEventListener("change", () => {
      state.settings.sound = els.soundToggle.checked;
      saveState();
    });
    els.motionToggle.addEventListener("change", () => {
      state.settings.reducedFx = els.motionToggle.checked;
      saveState();
      render();
    });

    els.customStudyForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const label = els.customStudyName.value.trim();
      const wrvu = Number(els.customStudyRvu.value);
      if (!label || !Number.isFinite(wrvu) || wrvu <= 0) return;
      logStudy({
        label,
        modality: els.customStudyModality.value,
        code: "CUSTOM",
        wrvu,
      }, { custom: true });
      els.customStudyForm.reset();
      els.customStudyModality.value = activeModality;
    });

    document.addEventListener("keydown", (event) => {
      const isTyping = ["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement?.tagName);
      if (event.key === "Escape" && els.drawer.classList.contains("open")) {
        closeDrawer();
        return;
      }
      if (event.key === "/" && !isTyping) {
        event.preventDefault();
        els.studySearch.focus();
        return;
      }
      if (event.key === "Enter" && document.activeElement === els.studySearch && visibleStudies[0]) {
        event.preventDefault();
        if (linkMode) toggleLinkedStudy(visibleStudies[0]);
        else logStudy(visibleStudies[0]);
        els.studySearch.select();
        return;
      }
      if (isTyping || els.drawer.classList.contains("open")) return;
      if (event.key.toLowerCase() === "l") {
        event.preventDefault();
        setLinkMode(!linkMode);
        return;
      }
      if (event.key === "Enter" && linkMode && linkSelectionIds.length >= 2) {
        event.preventDefault();
        logLinkedSet();
        return;
      }
      if (event.altKey && /^[1-7]$/.test(event.key)) {
        event.preventDefault();
        activeModality = modalityKeys[Number(event.key) - 1];
        els.studySearch.value = "";
        renderStudies();
        return;
      }
      if (!event.altKey && /^[1-9]$/.test(event.key)) {
        const study = visibleStudies[Number(event.key) - 1];
        if (study) {
          event.preventDefault();
          if (linkMode) toggleLinkedStudy(study);
          else logStudy(study);
        }
        return;
      }
      const recentKeyMap = { q: 0, w: 1, e: 2 };
      const recentIndex = recentKeyMap[event.key.toLowerCase()];
      if (recentIndex !== undefined) {
        const study = studyById.get(state.recentStudyIds[recentIndex]);
        if (study) {
          event.preventDefault();
          if (linkMode) toggleLinkedStudy(study);
          else logStudy(study);
        }
      }
    });
  }

  function initControls() {
    els.catalogCount.textContent = `${studies.length} STUDIES LOADED`;
    els.customStudyModality.innerHTML = modalityKeys.map((key) =>
      `<option value="${key}">${modalityMeta(key).label}</option>`
    ).join("");
    els.customStudyModality.value = activeModality;
  }

  class CanvasFallbackFx {
    constructor(parent) {
      this.canvas = document.createElement("canvas");
      this.context = this.canvas.getContext("2d");
      this.parent = parent;
      this.parent.append(this.canvas);
      this.stars = Array.from({ length: compactDevice ? 55 : 110 }, () => this.newStar());
      this.bursts = [];
      this.reduced = false;
      this.resize = this.resize.bind(this);
      this.frame = this.frame.bind(this);
      this.onReward = this.onReward.bind(this);
      window.addEventListener("resize", this.resize);
      window.addEventListener("rvu:logged", this.onReward);
      this.resize();
      requestAnimationFrame(this.frame);
    }

    newStar() {
      return {
        x: Math.random(),
        y: Math.random(),
        speed: 0.00015 + Math.random() * 0.00055,
        size: 0.5 + Math.random() * 1.5,
      };
    }

    resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, compactDevice ? 1.5 : 2);
      this.canvas.width = innerWidth * dpr;
      this.canvas.height = innerHeight * dpr;
      this.canvas.style.width = `${innerWidth}px`;
      this.canvas.style.height = `${innerHeight}px`;
      this.context.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    setReduced(value) {
      this.reduced = value;
    }

    onReward(event) {
      const color = modalityMeta(event.detail.modality).color;
      const count = this.reduced ? 8 : compactDevice ? 18 : 34;
      for (let index = 0; index < count; index += 1) {
        const angle = Math.random() * Math.PI * 2;
        this.bursts.push({
          x: innerWidth * 0.38,
          y: innerHeight * 0.48,
          vx: Math.cos(angle) * (1 + Math.random() * 5),
          vy: Math.sin(angle) * (1 + Math.random() * 5),
          life: 1,
          color,
        });
      }
    }

    frame(time) {
      const ctx = this.context;
      ctx.clearRect(0, 0, innerWidth, innerHeight);
      ctx.globalCompositeOperation = "lighter";
      this.stars.forEach((star) => {
        star.y += this.reduced ? 0 : star.speed * 16;
        if (star.y > 1) Object.assign(star, this.newStar(), { y: 0 });
        ctx.fillStyle = "rgba(118,226,255,.55)";
        ctx.fillRect(star.x * innerWidth, star.y * innerHeight, star.size, star.size * 2.5);
      });

      const horizon = innerHeight * 0.54;
      ctx.strokeStyle = "rgba(108,60,190,.17)";
      ctx.lineWidth = 1;
      for (let index = -12; index <= 12; index += 1) {
        ctx.beginPath();
        ctx.moveTo(innerWidth / 2, horizon);
        ctx.lineTo(innerWidth / 2 + index * innerWidth * 0.12, innerHeight);
        ctx.stroke();
      }
      for (let index = 0; index < 13; index += 1) {
        const p = (index / 13 + (time * 0.00008) % (1 / 13)) ** 2;
        const y = horizon + p * (innerHeight - horizon);
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(innerWidth, y);
        ctx.stroke();
      }

      this.bursts = this.bursts.filter((particle) => particle.life > 0.02);
      this.bursts.forEach((particle) => {
        particle.x += particle.vx;
        particle.y += particle.vy;
        particle.life *= 0.95;
        ctx.globalAlpha = particle.life;
        ctx.fillStyle = particle.color;
        ctx.fillRect(particle.x, particle.y, 3, 3);
      });
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";
      requestAnimationFrame(this.frame);
    }
  }

  function startFx() {
    if (!window.Phaser) {
      window.rvuFx = new CanvasFallbackFx($("fx-layer"));
      window.rvuFx.setReduced(Boolean(state.settings.reducedFx));
      return;
    }

    class NeonScene extends Phaser.Scene {
      constructor() {
        super("NeonScene");
        this.rewardListener = null;
        this.reduced = false;
      }

      create() {
        this.grid = this.add.graphics().setBlendMode(Phaser.BlendModes.ADD);
        this.core = this.add.graphics().setBlendMode(Phaser.BlendModes.ADD);
        this.stars = Array.from({ length: compactDevice ? 70 : 150 }, () => ({
          x: Math.random(),
          y: Math.random(),
          speed: 0.00008 + Math.random() * 0.00028,
          size: 0.6 + Math.random() * 1.8,
          alpha: 0.25 + Math.random() * 0.6,
        }));
        const texture = this.make.graphics({ add: false });
        texture.fillStyle(0xffffff, 1);
        texture.fillCircle(5, 5, 5);
        texture.generateTexture("rvu-spark", 10, 10);
        texture.destroy();
        this.rewardListener = (event) => this.reward(event.detail);
        window.addEventListener("rvu:logged", this.rewardListener);
        this.events.once("shutdown", () => {
          window.removeEventListener("rvu:logged", this.rewardListener);
        });
      }

      setReduced(value) {
        this.reduced = value;
      }

      update(time, delta) {
        const width = this.scale.width;
        const height = this.scale.height;
        const horizon = height * 0.54;
        const cx = width * 0.37;
        const cy = height * 0.48;
        this.grid.clear();
        this.grid.lineStyle(1, 0x6838bc, 0.19);

        for (let index = -14; index <= 14; index += 1) {
          this.grid.beginPath();
          this.grid.moveTo(width / 2, horizon);
          this.grid.lineTo(width / 2 + index * width * 0.11, height);
          this.grid.strokePath();
        }
        for (let index = 0; index < 16; index += 1) {
          const offset = this.reduced ? 0 : (time * 0.00009) % (1 / 16);
          const p = (index / 16 + offset) ** 2;
          const y = horizon + p * (height - horizon);
          this.grid.lineBetween(0, y, width, y);
        }

        this.stars.forEach((star) => {
          star.y += this.reduced ? 0 : star.speed * delta;
          if (star.y > 1) star.y = 0;
          this.grid.fillStyle(0x72e8ff, star.alpha);
          this.grid.fillRect(star.x * width, star.y * height, star.size, star.size * 2.4);
        });

        this.core.clear();
        const pulse = this.reduced ? 0 : Math.sin(time * 0.0025) * 5;
        const rotation = this.reduced ? 0 : time * 0.00035;
        [
          [72 + pulse, 0x28f7ff, 0.17, 0.2],
          [105 - pulse, 0xff2bd6, 0.13, -0.42],
          [138 + pulse * 0.5, 0x8d5cff, 0.1, 0.78],
        ].forEach(([radius, color, alpha, speed], ringIndex) => {
          this.core.lineStyle(ringIndex === 0 ? 2 : 1, color, alpha);
          for (let arc = 0; arc < 4; arc += 1) {
            const start = rotation * speed + arc * Math.PI / 2;
            this.core.beginPath();
            this.core.arc(cx, cy, radius, start, start + 0.9, false);
            this.core.strokePath();
          }
        });
      }

      reward(entry) {
        const width = this.scale.width;
        const height = this.scale.height;
        const x = width * 0.37;
        const y = height * 0.48;
        const color = Phaser.Display.Color.HexStringToColor(
          modalityMeta(entry.modality).color
        ).color;
        if (!this.reduced) {
          this.cameras.main.flash(120, 80, 10, 100, false);
          this.cameras.main.shake(110, 0.0035);
        }
        const count = this.reduced ? 8 : compactDevice ? 22 : 42;
        for (let index = 0; index < count; index += 1) {
          const angle = Math.random() * Math.PI * 2;
          const distance = 45 + Math.random() * 180;
          const spark = this.add.image(x, y, "rvu-spark")
            .setTint(color)
            .setScale(0.25 + Math.random() * 0.6)
            .setBlendMode(Phaser.BlendModes.ADD);
          this.tweens.add({
            targets: spark,
            x: x + Math.cos(angle) * distance,
            y: y + Math.sin(angle) * distance,
            alpha: 0,
            scale: 0,
            duration: 350 + Math.random() * 420,
            ease: "Cubic.Out",
            onComplete: () => spark.destroy(),
          });
        }
        const text = this.add.text(x, y - 45, `+${Number(entry.wrvu).toFixed(2)} wRVU`, {
          fontFamily: "Arial Black, sans-serif",
          fontSize: Math.max(24, Math.min(width / 28, 48)),
          color: modalityMeta(entry.modality).color,
          stroke: "#05030c",
          strokeThickness: 7,
        }).setOrigin(0.5).setBlendMode(Phaser.BlendModes.ADD);
        this.tweens.add({
          targets: text,
          y: y - 130,
          alpha: 0,
          scale: 1.2,
          duration: 900,
          ease: "Cubic.Out",
          onComplete: () => text.destroy(),
        });
      }
    }

    const game = new Phaser.Game({
      type: Phaser.AUTO,
      parent: "fx-layer",
      transparent: true,
      antialias: !compactDevice,
      scale: {
        mode: Phaser.Scale.RESIZE,
        width: window.innerWidth,
        height: window.innerHeight,
      },
      render: {
        antialias: !compactDevice,
        powerPreference: "high-performance",
      },
      scene: NeonScene,
    });

    window.rvuFx = {
      game,
      setReduced(value) {
        game.scene.getScene("NeonScene")?.setReduced(value);
      },
    };
  }

  initControls();
  setMobileView("log");
  bindEvents();
  render();
  startFx();
})();
