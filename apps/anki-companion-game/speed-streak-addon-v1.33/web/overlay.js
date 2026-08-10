(function () {
  const state = {
    mounted: false,
    data: null,
    timerLoopId: 0,
    timerLoopSignature: "",
    lastColorsSignature: "",
    lastRingCount: 0,
    lastRowsSignature: "",
    lastNonce: -1,
    prevColors: [],
    prevStreak: 0,
    lastSceneScale: 1,
    zoomTimer: 0,
    settingsOpen: false,
    toastTimer: 0,
    hapticTimer: 0,
    appearanceModeDraft: "midnight",
    colorDrafts: {},
    useCustomTimerColorsDraft: false,
    timerColorLevelDraft: 0,
    presetsOpen: false,
    presetMenuOpenId: "",
    visualSelectorChoice: "sphere",
    sidebarResizeObserver: null,
    boostBankResizeObserver: null,
    lastBoostBankSignature: "",
    lastSettingsSignature: "",
    lastThemeSignature: "",
    lastSidebarBackground: "",
    lastFilterValue: "",
    lastCoreSize: "",
    pauseOverview: null,
    lastPauseOverviewStartSent: -1,
    webgl: null,
    crystalWebgl: null,
    timerWebgl: null,
  };

  const PAUSE_OVERVIEW_STORAGE_KEY = "speed-streak-pause-overview-v1";

  const DEFAULT_CUSTOM_COLORS = {
    core: "#566ed4",
    red: "#c34f69",
    yellow: "#c69430",
    green: "#2b9d73",
    blue: "#4a74dd",
  };

  const THEME_CUSTOM_COLOR_DEFAULTS = {
    classic: { core: "#5b6fcf", red: "#c9546d", yellow: "#c89a38", green: "#2ea36f", blue: "#4b7de2" },
    cardmatch: { core: "#84a6c7", red: "#b26a6a", yellow: "#b786ad", green: "#419c5f", blue: "#4d8d8d" },
    card: { core: "#84a6c7", red: "#b26a6a", yellow: "#b786ad", green: "#419c5f", blue: "#4d8d8d" },
    graphite: { core: "#6982b8", red: "#b65b70", yellow: "#b48c42", green: "#3d9b79", blue: "#557fd6" },
    midnight: { core: "#566ed4", red: "#c34f69", yellow: "#c69430", green: "#2b9d73", blue: "#4a74dd" },
    forest: { core: "#4f8f9c", red: "#b45a62", yellow: "#b89a43", green: "#2d9a66", blue: "#3d73b8" },
    ember: { core: "#c66a4b", red: "#cf5664", yellow: "#c98a33", green: "#4e9a72", blue: "#4d74c9" },
    violet: { core: "#7761c5", red: "#c15a7f", yellow: "#bc8f3d", green: "#4b9c82", blue: "#5b7ed6" },
    ocean: { core: "#4d8fc2", red: "#bd5c6c", yellow: "#c39932", green: "#2f9a82", blue: "#3e79cc" },
  };

  const COLOR_FIELDS = [
    { key: "core", label: "Central Orb", description: "Main color for the center orb and its glow." },
    { key: "red", label: "Again Satellite", description: "Used for Again ratings and timeout accents." },
    { key: "yellow", label: "Hard Satellite", description: "Used for Hard ratings." },
    { key: "green", label: "Good Satellite", description: "Used for Good ratings." },
    { key: "blue", label: "Easy Satellite", description: "Used for Easy ratings." },
  ];

  const FLAG_OPTIONS = [
    { value: 0, label: "Off" },
    { value: 1, label: "Red" },
    { value: 2, label: "Orange" },
    { value: 3, label: "Green" },
    { value: 4, label: "Blue" },
    { value: 5, label: "Pink" },
    { value: 6, label: "Turquoise" },
    { value: 7, label: "Purple" },
  ];

  const DEFAULT_FLAG_PALETTE = {
    0: "#8c96ac",
    1: "#ff7b7b",
    2: "#f5aa41",
    3: "#86ce5d",
    4: "#6f9dff",
    5: "#f097e4",
    6: "#5ccfca",
    7: "#9f63d3",
  };

  const DISPLAY_MODE_ICONS = {
    external: `
      <svg class="acg-display-mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="M7 17 17 7"></path>
        <path d="M9 7h8v8"></path>
      </svg>
    `,
    inline: `
      <svg class="acg-display-mode-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="M17 7 7 17"></path>
        <path d="M15 17H7V9"></path>
      </svg>
    `,
  };

  const WINDOW_PRESET_ICON = `
    <svg class="acg-window-preset-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
      <rect x="3" y="4" width="18" height="16" rx="2.2"></rect>
      <path d="M3 8h18M13.5 8v12"></path>
      <path d="m7 13 2-2m-2 2 2 2M18 13l-2-2m2 2-2 2"></path>
    </svg>
  `;

  const VISUAL_MODE_ICONS = {
    sphere: `
      <svg class="acg-visual-mode-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <ellipse cx="16" cy="16" rx="12" ry="6.5" stroke-width="1.35" transform="rotate(-18 16 16)"></ellipse>
        <circle cx="16" cy="16" r="4.1" fill="currentColor" fill-opacity=".22" stroke-width="1.6"></circle>
        <circle cx="5.7" cy="18.4" r="2.05" fill="currentColor" stroke="none"></circle>
        <circle cx="25.8" cy="12.2" r="1.8" fill="currentColor" stroke="none"></circle>
        <circle cx="20.5" cy="21.5" r="1.45" fill="currentColor" stroke="none"></circle>
      </svg>
    `,
    crystal_reactor: `
      <svg class="acg-visual-mode-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="M16 3.5 25.5 10 22 25 16 29 10 25 6.5 10Z" fill="currentColor" fill-opacity=".13" stroke-width="1.45"></path>
        <path d="M16 3.5 18.5 11 16 29 10.5 12Z" fill="currentColor" fill-opacity=".22" stroke-width="1.1"></path>
        <path d="m6.5 10 4 2 8-1 7-1M10 25l6-4 6 4" stroke-width="1.05"></path>
      </svg>
    `,
    lightweight_rows: `
      <svg class="acg-visual-mode-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="M4 7h11v7H4zM17 7h11v7H17zM8 16h11v7H8zM21 16h7v7h-7zM4 25h11v4H4zM17 25h11v4H17z" fill="currentColor" fill-opacity=".14"></path>
        <path d="M4 14h24M8 23h20M15 7v7M19 16v7M15 25v4"></path>
      </svg>
    `,
  };

  function timeDrainToggleMarkup() {
    return `
      <label class="acg-time-drain-toggle" for="acgTimeDrainReviewLast">
        <span class="acg-time-drain-toggle-copy">
          <span class="acg-time-drain-toggle-label">Review Time Drains Last</span>
          <span class="acg-time-drain-toggle-subcopy">Future repeats move behind the rest of this session.</span>
        </span>
        <span class="acg-time-drain-toggle-control">
          <input id="acgTimeDrainReviewLast" class="acg-time-drain-toggle-input" type="checkbox" />
          <span class="acg-time-drain-toggle-track" aria-hidden="true">
            <span class="acg-time-drain-toggle-knob"></span>
          </span>
        </span>
      </label>
    `;
  }

  function defaultPauseOverview(data = {}) {
    const now = Date.now();
    return {
      visible: false,
      startMs: now,
      baseAnsweredCards: Number(data.answeredCards || 0),
      lastEventNonce: Number(data.eventNonce || -1),
      again: 0,
      hard: 0,
      good: 0,
      easy: 0,
    };
  }

  function normalizePauseOverview(raw, data = {}) {
    const fallback = defaultPauseOverview(data);
    if (!raw || typeof raw !== "object") {
      return fallback;
    }
    return {
      visible: Boolean(raw.visible),
      startMs: Math.max(1, Number(raw.startMs || fallback.startMs)),
      baseAnsweredCards: Math.max(0, Number(raw.baseAnsweredCards || 0)),
      lastEventNonce: Number(raw.lastEventNonce ?? fallback.lastEventNonce),
      again: Math.max(0, Number(raw.again || 0)),
      hard: Math.max(0, Number(raw.hard || 0)),
      good: Math.max(0, Number(raw.good || 0)),
      easy: Math.max(0, Number(raw.easy || 0)),
    };
  }

  function loadPauseOverview(data = {}) {
    if (state.pauseOverview) {
      return state.pauseOverview;
    }
    if (data.pauseOverviewState && typeof data.pauseOverviewState === "object") {
      state.pauseOverview = normalizePauseOverview(data.pauseOverviewState, data);
      savePauseOverview({ syncBackend: false });
      return state.pauseOverview;
    }
    try {
      state.pauseOverview = normalizePauseOverview(JSON.parse(window.localStorage.getItem(PAUSE_OVERVIEW_STORAGE_KEY) || "null"), data);
    } catch (_error) {
      state.pauseOverview = defaultPauseOverview(data);
    }
    return state.pauseOverview;
  }

  function savePauseOverview(options = {}) {
    if (!state.pauseOverview) {
      return;
    }
    try {
      window.localStorage.setItem(PAUSE_OVERVIEW_STORAGE_KEY, JSON.stringify(state.pauseOverview));
    } catch (_error) {
      // Ignore storage failures; the overview still works for the current page.
    }
    if (options.syncBackend !== false) {
      syncPauseOverviewToBackend();
    }
  }

  function syncPauseOverviewToBackend() {
    const overview = loadPauseOverview(state.data || {});
    const payload = {
      visible: Boolean(overview.visible),
      startMs: Math.max(0, Math.round(Number(overview.startMs || 0))),
    };
    const signature = JSON.stringify(payload);
    if (signature === state.lastPauseOverviewStartSent) {
      return;
    }
    state.lastPauseOverviewStartSent = signature;
    if (typeof pycmd === "function") {
      pycmd(`speed-streak:pause-overview:${encodeURIComponent(signature)}`);
    }
  }

  function syncPauseOverviewStartToBackend() {
    syncPauseOverviewToBackend();
  }

  function resetPauseOverview(data = {}) {
    state.pauseOverview = defaultPauseOverview(data);
    state.pauseOverview.visible = true;
    savePauseOverview();
  }

  function formatOverviewStart(ms) {
    try {
      return new Date(ms).toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
    } catch (_error) {
      return "--";
    }
  }

  function formatOverviewDuration(totalSeconds) {
    const seconds = Math.max(0, Math.floor(Number(totalSeconds || 0)));
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remSeconds = seconds % 60;
    if (hours > 0) {
      return `${hours}h ${minutes}m ${remSeconds}s`;
    }
    if (minutes > 0) {
      return `${minutes}m ${remSeconds}s`;
    }
    return `${remSeconds}s`;
  }

  function renderPauseOverview(data) {
    const overview = loadPauseOverview(data);
    const node = $("acgPauseOverview");
    if (!node) {
      return;
    }
    node.classList.toggle("hidden", !overview.visible);
    if (!overview.visible) {
      return;
    }
    syncPauseOverviewStartToBackend();
    const stats = data && typeof data.pauseOverviewStats === "object" && data.pauseOverviewStats
      ? data.pauseOverviewStats
      : {};
    const statsStartMs = Number(stats.startMs || 0);
    const useBackendStats = statsStartMs > 0 && Math.abs(statsStartMs - Number(overview.startMs || 0)) < 1000;
    const cards = Math.max(0, Number(useBackendStats ? stats.total : 0) || 0);
    const again = Math.max(0, Number(useBackendStats ? stats.again : 0) || 0);
    const hard = Math.max(0, Number(useBackendStats ? stats.hard : 0) || 0);
    const good = Math.max(0, Number(useBackendStats ? stats.good : 0) || 0);
    const easy = Math.max(0, Number(useBackendStats ? stats.easy : 0) || 0);
    const elapsedSeconds = Math.max(1, Number(useBackendStats ? stats.elapsedSeconds : 0) || ((Date.now() - Number(overview.startMs || Date.now())) / 1000));
    const cardsPerMinute = cards ? (cards / (elapsedSeconds / 60)) : 0;
    const secondsPerCard = cards ? (elapsedSeconds / cards) : 0;
    const right = Math.max(0, hard + good + easy);
    const wrong = Math.max(0, again);

    setText("acgPauseOverviewSince", `Since ${formatOverviewStart(overview.startMs)}`);
    setText("acgPauseOverviewElapsed", formatOverviewDuration(elapsedSeconds));
    setText("acgPauseOverviewTotal", String(Math.round(cards)));
    const rateNode = $("acgPauseOverviewRate");
    const secondsNode = $("acgPauseOverviewSeconds");
    if (rateNode) {
      rateNode.innerHTML = `<strong>${cardsPerMinute.toFixed(1)}</strong> / min`;
    }
    if (secondsNode) {
      secondsNode.innerHTML = `<strong>${Math.round(secondsPerCard)}</strong> sec / card`;
    }
    setText("acgPauseOverviewAgain", String(Math.round(again)));
    setText("acgPauseOverviewHard", String(Math.round(hard)));
    setText("acgPauseOverviewGood", String(Math.round(good)));
    setText("acgPauseOverviewEasy", String(Math.round(easy)));
    setText("acgPauseOverviewAccuracy", `${right} right / ${wrong} wrong`);
  }

  function hidePauseOverviewMenu() {
    const menu = $("acgPauseOverviewMenu");
    if (menu) {
      menu.classList.add("hidden");
    }
  }

  function showPauseOverviewMenu(event) {
    event.preventDefault();
    event.stopPropagation();
    const overview = loadPauseOverview(state.data || {});
    const menu = $("acgPauseOverviewMenu");
    const overlay = $("acgPauseOverlay");
    if (!menu || !overlay) {
      return;
    }
    const toggle = $("acgPauseOverviewToggle");
    if (toggle) {
      setText(toggle, overview.visible ? "Hide Timer" : "Show Timer");
      toggle.setAttribute("data-pause-overview-action", overview.visible ? "hide" : "show");
    }
    const reset = $("acgPauseOverviewReset");
    const edit = $("acgPauseOverviewEdit");
    if (reset) {
      reset.hidden = !overview.visible;
    }
    if (edit) {
      edit.hidden = !overview.visible;
    }
    const bounds = overlay.getBoundingClientRect();
    const x = clamp(Number(event.clientX || bounds.left + bounds.width - 10) - bounds.left, 8, Math.max(8, bounds.width - 118));
    const y = clamp(Number(event.clientY || bounds.top + 10) - bounds.top, 8, Math.max(8, bounds.height - 96));
    menu.style.left = `${x}px`;
    menu.style.top = `${y}px`;
    menu.classList.remove("hidden");
  }

  function applyPauseOverviewAction(action) {
    const overview = loadPauseOverview(state.data || {});
    if (action === "hide") {
      overview.visible = false;
      savePauseOverview();
    } else if (action === "show") {
      resetPauseOverview(state.data || {});
    } else if (action === "edit") {
      const current = new Date(overview.startMs).toLocaleString();
      const value = window.prompt("Start date/time", current);
      if (value) {
        const parsed = Date.parse(value);
        if (Number.isFinite(parsed)) {
          overview.startMs = parsed;
          savePauseOverview();
        }
      }
    } else {
      resetPauseOverview(state.data || {});
    }
    hidePauseOverviewMenu();
    renderPauseOverview(state.data || {});
  }

  const template = `
    <div id="speed-streak-sidebar" class="speed-streak-sidebar hidden">
      <button id="acgCollapseTab" class="acg-collapse-tab" type="button" title="Hide Speed Streak" aria-label="Hide Speed Streak">
        <span id="acgCollapseTabText" class="acg-collapse-tab-text">‹</span>
      </button>
      <div class="acg-foreground-controls">
        <button id="acgEnabledToggle" class="acg-enabled-toggle" type="button" aria-pressed="true" title="Toggle Speed Streak">
          <span class="acg-enabled-track">
            <span id="acgEnabledKnob" class="acg-enabled-knob"></span>
          </span>
        </button>
        <button id="acgDisplayModeToggle" class="acg-action acg-foreground-action acg-icon-toggle acg-display-mode-toggle" type="button" title="Switch to external window" aria-label="Switch to external window">${DISPLAY_MODE_ICONS.external}</button>
        <div id="acgWindowPresets" class="acg-window-presets">
          <button id="acgWindowPresetsToggle" class="acg-action acg-foreground-action acg-icon-toggle acg-window-presets-toggle" type="button" title="Window position presets" aria-label="Window position presets">${WINDOW_PRESET_ICON}</button>
          <div id="acgWindowPresetsPanel" class="acg-window-presets-panel" aria-label="Window position presets">
            <div class="acg-window-presets-head">
              <span>Window presets</span>
              <button id="acgWindowPresetSave" class="acg-action acg-icon-toggle acg-window-preset-add" type="button" title="Save current window positions" aria-label="Save current window positions">+</button>
            </div>
            <div id="acgWindowPresetList" class="acg-window-preset-list"></div>
          </div>
        </div>
      </div>
      <div class="acg-foreground-settings">
        <button id="acgSettingsButton" class="acg-action acg-foreground-action acg-icon-toggle acg-settings-toggle" type="button" title="Settings" aria-label="Settings">⚙</button>
        <button id="acgInlineSideToggle" class="acg-action acg-foreground-action acg-icon-toggle acg-inline-side-toggle" type="button" title="Move inline pane to the right" aria-label="Move inline pane to the right">→</button>
      </div>
      <div class="acg-inner">
        <div class="acg-top">
          <div id="acgTimerHero" class="acg-timer-hero">
            <canvas id="acgTimerCanvas" class="acg-timer-canvas" aria-hidden="true"></canvas>
            <div class="acg-timer-inner">
              <div id="acgPhaseLabel" class="acg-phase-label">Ready</div>
              <div id="acgTimerValue" class="acg-timer-value">--</div>
            </div>
          </div>
          <div id="acgLegacyEconomy" class="acg-legacy-economy">
            <div id="acgScore" class="acg-score">0</div>
            <div id="acgMultiplier" class="acg-multiplier">x1.00 multiplier</div>
          </div>
          <div id="acgBoostEconomy" class="acg-boost-economy" aria-live="polite">
            <div id="acgBoostHoverZone" class="acg-boost-hover-zone" tabindex="0" aria-label="Time Boost charges and controls" title="Click the charge bank to edit Time Boost settings">
              <div class="acg-boost-bank-row">
                <div id="acgBoostCharges" class="acg-boost-charges" aria-label="1 of 3 Time Boost charges"></div>
              </div>
              <div class="acg-boost-progress" aria-hidden="true"><span id="acgBoostProgressFill"></span></div>
              <div id="acgBoostProgressText" class="acg-boost-progress-text">Next charge 0 / 5</div>
              <div class="acg-boost-hover-controls">
                <div id="acgFocusModeToggles" class="acg-focus-mode-toggles" role="group" aria-label="Focus rules">
                  <button id="acgNoPauseToggle" class="acg-focus-mode-toggle" type="button" aria-pressed="false">NO PAUSE</button>
                  <button id="acgNoUndoToggle" class="acg-focus-mode-toggle" type="button" aria-pressed="false">NO UNDO</button>
                </div>
                <button id="acgBoostButton" class="acg-boost-key" type="button" aria-label="Edit Time Boost shortcut">
                  <kbd id="acgBoostShortcutLabel">R</kbd>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div id="acgStage" class="acg-stage" title="Click to open visual and resource options">
          <div id="acgField" class="acg-field">
            <div id="acgScene" class="acg-scene">
              <div id="acgEnergyDisc" class="acg-energy-disc"></div>
              <div id="acgRings"></div>
              <canvas id="acgWebglOrbit" class="acg-webgl-orbit" aria-hidden="true"></canvas>
              <div id="acgSatellites"></div>
              <div id="acgFx" class="acg-fx"></div>
              <div class="acg-core-wrap">
                <div class="acg-core-halo"></div>
                <div id="acgCore" class="acg-core">
                  <div id="acgStreak" class="acg-streak">0</div>
                </div>
              </div>
            </div>
            <div id="acgRowsScene" class="acg-rows-scene">
              <div class="acg-rows-milestones-wrap">
                <div class="acg-rows-milestones-bar">
                  <div id="acgRowsMilestones" class="acg-rows-milestones"></div>
                  <div id="acgRowsOverflow" class="acg-rows-overflow hidden"></div>
                </div>
              </div>
              <div id="acgRowsGrid" class="acg-rows-grid"></div>
              <div id="acgRowsFx" class="acg-rows-fx"></div>
              <div class="acg-rows-footer">
                <div id="acgRowsStreakValue" class="acg-rows-streak-value">0</div>
              </div>
            </div>
            <div id="acgCrystalScene" class="acg-crystal-scene">
              <div class="acg-crystal-grid"></div>
              <div id="acgCrystalFlash" class="acg-crystal-flash"></div>
              <div class="acg-crystal-milestone-rings" aria-hidden="true">
                <span class="acg-crystal-milestone-ring ring-inner"></span>
                <span class="acg-crystal-milestone-ring ring-outer"></span>
              </div>
              <div class="acg-crystal-readout">
                <div id="acgCrystalStreak" class="acg-crystal-streak">0</div>
              </div>
            </div>
          </div>
        </div>
        <div class="acg-bottom">
          <div id="acgVisualsDisabledCopy" class="acg-visuals-disabled-copy">Vibration-only mode is active.</div>
          <div id="acgTimer" class="acg-timer">Ready</div>
          <div class="acg-bottom-bar">
            <div id="acgVisualSelector" class="acg-visual-selector" aria-label="Visual and resource options">
              <button id="acgVisualSelectorToggle" class="acg-action acg-icon-toggle acg-visual-selector-toggle" type="button" aria-expanded="false" title="Visual and resource options">
                <span id="acgVisualSelectorCurrentIcon">${VISUAL_MODE_ICONS.sphere}</span>
              </button>
              <div class="acg-visual-selector-panel">
                <div class="acg-visual-choice-list" role="group" aria-label="Visual style">
                  <button class="acg-visual-choice" type="button" data-visual-choice="sphere" title="Satellite Orbit" aria-label="Satellite Orbit">
                    ${VISUAL_MODE_ICONS.sphere}
                  </button>
                  <button class="acg-visual-choice" type="button" data-visual-choice="crystal_reactor" title="Crystal Reactor" aria-label="Crystal Reactor">
                    ${VISUAL_MODE_ICONS.crystal_reactor}
                  </button>
                  <button class="acg-visual-choice" type="button" data-visual-choice="lightweight_rows" title="Brick Streak" aria-label="Brick Streak">
                    ${VISUAL_MODE_ICONS.lightweight_rows}
                  </button>
                </div>
                <div id="acgVisualResourcePanel" class="acg-visual-resource-panel">
                  <div class="acg-visual-resource-heading">
                    <span id="acgVisualResourceName">Resource usage</span>
                    <strong id="acgVisualResourceValue">Full</strong>
                  </div>
                  <input id="acgVisualResourceSlider" class="acg-visual-resource-slider" type="range" min="0" max="2" step="1" value="2" aria-label="Visual resource usage" />
                  <div id="acgVisualResourceTicks" class="acg-visual-resource-ticks"></div>
                  <p id="acgVisualResourceDescription" class="acg-visual-resource-description"></p>
                </div>
              </div>
            </div>
            <div class="acg-bottom-stack acg-bottom-right">
              <button id="acgHapticsToggle" class="acg-action acg-icon-toggle" type="button" title="Haptics" aria-label="Haptics">
                <svg class="acg-haptics-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.15" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                  <rect x="10" y="8" width="4" height="8" rx="2"></rect>
                  <path d="M6.75 9c-1.45 1.55-1.45 4.45 0 6"></path>
                  <path d="M17.25 9c1.45 1.55 1.45 4.45 0 6"></path>
                  <path d="M3.75 6.5c-2.3 2.35-2.3 8.65 0 11"></path>
                  <path d="M20.25 6.5c2.3 2.35 2.3 8.65 0 11"></path>
                </svg>
              </button>
              <button id="acgAudioToggle" class="acg-action acg-icon-toggle" type="button" title="Sound off" aria-label="Sound off">🔇</button>
            </div>
          </div>
        </div>
        <div id="acgDim" class="acg-dim"></div>
        <div id="acgPauseOverlay" class="acg-pause-overlay">
          <div class="acg-pause-copy">Press <span id="acgPauseShortcutLabel">P</span> to Unpause</div>
          <div id="acgPauseOverview" class="acg-pause-overview hidden">
            <div class="acg-pause-overview-head">
              <span id="acgPauseOverviewSince">Since --</span>
              <span id="acgPauseOverviewElapsed">--</span>
            </div>
            <div class="acg-pause-overview-total-row">
              <div class="acg-pause-overview-total">
                <span id="acgPauseOverviewTotal">0</span>
                <span>cards seen</span>
              </div>
              <div class="acg-pause-overview-rate-stack">
                <span id="acgPauseOverviewRate">0.0 per minute</span>
                <span id="acgPauseOverviewSeconds">0 seconds per card</span>
              </div>
            </div>
            <div class="acg-pause-overview-grid">
              <div class="acg-pause-overview-chip acg-pause-overview-again"><span id="acgPauseOverviewAgain">0</span></div>
              <div class="acg-pause-overview-chip acg-pause-overview-hard"><span id="acgPauseOverviewHard">0</span></div>
              <div class="acg-pause-overview-chip acg-pause-overview-good"><span id="acgPauseOverviewGood">0</span></div>
              <div class="acg-pause-overview-chip acg-pause-overview-easy"><span id="acgPauseOverviewEasy">0</span></div>
            </div>
            <div id="acgPauseOverviewAccuracy" class="acg-pause-overview-foot">0 right / 0 wrong</div>
          </div>
          <div id="acgPauseOverviewMenu" class="acg-pause-overview-menu hidden">
            <button id="acgPauseOverviewToggle" type="button" data-pause-overview-action="show">Show Timer</button>
            <button id="acgPauseOverviewReset" type="button" data-pause-overview-action="reset">Reset from now</button>
            <button id="acgPauseOverviewEdit" type="button" data-pause-overview-action="edit">Edit start time</button>
          </div>
        </div>
        <div id="acgOffOverlay" class="acg-off-overlay">
          <div class="acg-off-copy">Speed Streak is Off</div>
          <div class="acg-off-subcopy">This can be toggled in the top left of the screen.</div>
        </div>
        <div id="acgTimeDrainOverlay" class="acg-time-drain">
          <div class="acg-time-drain-copy">
            <div class="acg-time-drain-title">Time Drain</div>
            <div id="acgTimeDrainTimer" class="acg-time-drain-timer">--</div>
            <div class="acg-time-drain-body">This card is a time drain, press '-' to bury! Quick!</div>
            ${timeDrainToggleMarkup()}
          </div>
        </div>
        <div id="acgToast" class="acg-toast"></div>
        <div id="acgSettingsModal" class="acg-modal">
          <div class="acg-modal-head">
            <div class="acg-modal-title">Settings</div>
            <button id="acgCloseSettings" class="acg-close" type="button">Close</button>
          </div>
          <div class="acg-modal-body">
            <div class="acg-settings-section" data-section="timers">
              <div class="acg-section-title">Timers</div>
              <div class="acg-form-row">
                <label class="acg-form-label" for="acgQuestionSeconds">Question Time</label>
                <input id="acgQuestionSeconds" class="acg-input" type="number" min="1" step="0.5" />
              </div>
              <div class="acg-form-row">
                <label class="acg-form-label" for="acgAnswerSeconds">Answer Time</label>
                <input id="acgAnswerSeconds" class="acg-input" type="number" min="1" step="0.5" />
              </div>
              <label class="acg-switch-row" for="acgFreeFirstCardOnReviewEntry">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Free First Card When Entering Review</span>
                  <span class="acg-switch-copy">Makes both sides of the first card untimed.</span>
                </span>
                <input id="acgFreeFirstCardOnReviewEntry" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgAnswerTimeoutBreaksStreak">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Answer Timer Can End Streak</span>
                  <span class="acg-switch-copy">When off, answer timeout preserves the streak.</span>
                </span>
                <input id="acgAnswerTimeoutBreaksStreak" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgResumeRunAfterRestart">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Resume Run After Restart</span>
                  <span class="acg-switch-copy">Restore the active run, streak, score, and timer after closing and reopening Anki.</span>
                </span>
                <input id="acgResumeRunAfterRestart" class="acg-switch" type="checkbox" />
              </label>
            </div>
            <div class="acg-settings-section" data-section="flags">
              <div class="acg-section-title">Flags</div>
              <div class="acg-form-row">
                <label class="acg-form-label">Time Drain Flag</label>
                <select id="acgTimeDrainFlag" class="acg-select"></select>
              </div>
              <div class="acg-form-row">
                <label class="acg-form-label">Review Later Flag</label>
                <select id="acgReviewLaterFlag" class="acg-select"></select>
              </div>
            </div>
            <div class="acg-settings-section" data-section="display-style">
              <div class="acg-section-title">Display Style</div>
              <label class="acg-switch-row" for="acgSidePanelEnabled">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Side Panel</span>
                  <span class="acg-switch-copy">Turn off to keep the top timer and haptics without reserving the inline left panel.</span>
                </span>
                <input id="acgSidePanelEnabled" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgShowCardTimer">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Top Card Timer</span>
                  <span class="acg-switch-copy">Show a horizontal timer bar at the top of the review card.</span>
                </span>
                <input id="acgShowCardTimer" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgVibrationOnlyMode">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Vibration Only Mode</span>
                  <span class="acg-switch-copy">Turns off streak and timer visuals, disables late buzzes, and keeps only haptics.</span>
                </span>
                <input id="acgVibrationOnlyMode" class="acg-switch" type="checkbox" />
              </label>
            </div>
            <div class="acg-settings-section" data-section="performance">
              <div class="acg-section-title">Performance</div>
              <label class="acg-switch-row" for="acgOrbitAnimation">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Orb Animation</span>
                  <span class="acg-switch-copy">Turn off the orb and satellite animation if your computer is slow, and keep only the streak number.</span>
                </span>
                <input id="acgOrbitAnimation" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgVibrationOnlyModePerf">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Vibration Only Mode</span>
                  <span class="acg-switch-copy">Linked with the Display Style toggle above. This also reduces visual load by disabling streak and timer visuals.</span>
                </span>
                <input id="acgVibrationOnlyModePerf" class="acg-switch" type="checkbox" />
              </label>
            </div>
            <div class="acg-settings-section" data-section="actions">
              <div class="acg-section-title">Actions</div>
              <div class="acg-button-stack">
                <button id="acgReviewLaterManagerButton" class="acg-action acg-action-primary" type="button">Review Later Manager</button>
                <button id="acgStatsButton" class="acg-action" type="button">Show Stats (Work in Progress)</button>
                <button id="acgAppearanceButton" class="acg-action" type="button">Appearance</button>
                <button id="acgHelpButton" class="acg-action" type="button">How It Works</button>
                <button id="acgDefaultSettingsButton" class="acg-action" type="button">Default Settings</button>
                <button id="acgResetGameButton" class="acg-action" type="button">Reset Game</button>
              </div>
            </div>
            <div id="acgAppearancePanel" class="acg-panel hidden">
              <div class="acg-panel-copy">Choose how Speed Streak is drawn in the sidebar.</div>
              <div class="acg-appearance-options">
                <button id="acgAppearanceMidnight" class="acg-action" type="button">Midnight Appearance</button>
                <button id="acgAppearanceCard" class="acg-action" type="button">Card Background Mode</button>
                <button id="acgColorCustomizerButton" class="acg-action" type="button">Orb Colors</button>
              </div>
            </div>
            <div id="acgColorPanel" class="acg-color-panel hidden">
              <div class="acg-color-panel-head">
                <div>
                  <div class="acg-modal-title">Orb Colors</div>
                  <div class="acg-panel-copy">Pick the center orb color and each satellite rating color. Changes preview immediately and save when you hit Save Colors.</div>
                </div>
                <button id="acgCloseColorPanel" class="acg-close" type="button">Close</button>
              </div>
              <div class="acg-color-grid">
                ${COLOR_FIELDS.map((field) => `
                  <label class="acg-color-row" for="acgColorHex-${field.key}">
                    <span class="acg-color-copy">
                      <span class="acg-form-label">${field.label}</span>
                      <span class="acg-switch-copy">${field.description}</span>
                    </span>
                    <span class="acg-color-controls">
                      <span id="acgColorSwatch-${field.key}" class="acg-color-swatch"></span>
                      <input id="acgColorPicker-${field.key}" class="acg-color-picker" type="color" />
                      <input id="acgColorHex-${field.key}" class="acg-input acg-color-hex" type="text" inputmode="text" spellcheck="false" maxlength="7" />
                    </span>
                  </label>
                `).join("")}
              </div>
              <label class="acg-switch-row" for="acgTimerColorMode">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Use Orb Colors For Timers</span>
                  <span class="acg-switch-copy">Fade both timers through this theme/custom green, yellow, and red palette instead of the default warning colors.</span>
                </span>
                <input id="acgTimerColorMode" class="acg-switch" type="checkbox" />
              </label>
              <div class="acg-color-actions">
                <button id="acgColorResetButton" class="acg-action" type="button">Reset Colors</button>
                <button id="acgColorSaveButton" class="acg-action acg-action-primary" type="button">Save Colors</button>
              </div>
            </div>
            <div id="acgHelpPanel" class="acg-panel hidden">
              <div class="acg-panel-copy">
                This sidebar runs a two-phase timer for each card. The question timer runs while you are deciding what the answer is, and the answer timer runs after you reveal the card. By default, both sides of the first card are untimed each time you enter Review.
                <br><br>
                Every time you rate a card on time, your streak goes up by one and a new satellite is added to the orbit. Again adds a red satellite, Hard adds yellow, Good adds green, and Easy adds blue. Legacy Points grows the score with a streak multiplier. Time Boost replaces those points with a capped charge bank; complete the configured number of timed cards to earn a charge, then press the displayed keyboard shortcut before time expires to add time without losing the streak. Hover over or focus the charge bank to reveal the directly toggleable No Pause/No Undo pills and the shortcut keycap; clicking the keycap opens its setting.
                <br><br>
                By default, if either timer expires, the streak is lost, the orb flashes into a failed state, and the orbit collapses. If you bury or hide a card, the next card gets a fresh timer without changing the streak or score.
                <br><br>
                <span id="acgHelpShortcutCopy">Press <strong id="acgHelpPauseShortcut">P</strong> to pause or unpause.</span> No Pause mode rejects deliberate pause commands, while navigation and Settings retain safety pauses. While paused, the sidebar dims and waits for you to resume. You can change the question and answer timers in Settings, toggle the top-of-card timer, and switch into vibration-only mode. The <strong>Show Stats</strong> screen opens a full-window overlay with your current-round pause time, today's pace, and historical charts.
                <br><br>
                The <strong>Time Drain Flag</strong> is a watched flag you choose in Settings. When the current review card has that same flag on its question side, the normal orbit view is temporarily replaced with a warning screen. That warning shows the live countdown in large text and says to press <strong>-</strong> to bury the card if it is becoming a time sink. This is meant for cards you still want to keep, but want the add-on to call out when they are slowing your session down.
                <br><br>
                The <strong>Review Later Flag</strong> is a separate watched flag, and it cannot be the same color as Time Drain. When you add that flag to the current card, the sidebar shows a rising <strong>Review Later</strong> message. When you remove it, the sidebar shows <strong>Removed from 'Review Later'</strong>. The add-on also keeps track of when each card entered the Review Later group, so the manager can work by cohort instead of just by card age.
                <br><br>
                <strong>Review Later Manager</strong> shows all cards that currently have the Review Later flag. You can filter them by when they were added to Review Later, such as today, yesterday, or the past X days. <strong>Copy All</strong> copies only the text from each field for the visible cards. <strong>Open in Browser</strong> opens the current visible set in Anki Browser. <strong>Make Filtered Deck</strong> creates a dated filtered deck from the currently visible Review Later cohort so you can work through that batch directly inside Anki.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  function ensureMounted() {
    if (state.mounted) {
      ensureTimeDrainToggleControl();
      bindTimeDrainToggleInput();
      return;
    }
    const host = document.body || document.documentElement;
    if (!host) {
      return;
    }

    if (!document.getElementById("speed-streak-sidebar")) {
      host.insertAdjacentHTML("beforeend", template);
    }
    ensureTimeDrainToggleControl();

    const settingsButton = document.getElementById("acgSettingsButton");
    if (settingsButton) {
      settingsButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:open-settings");
        }
      });
    }

    const visualSelector = document.getElementById("acgVisualSelector");
    const visualSelectorToggle = document.getElementById("acgVisualSelectorToggle");
    const visualResourceSlider = document.getElementById("acgVisualResourceSlider");
    if (visualSelectorToggle && visualSelector) {
      visualSelectorToggle.addEventListener("click", () => {
        visualSelector.classList.toggle("open");
        visualSelectorToggle.setAttribute("aria-expanded", visualSelector.classList.contains("open") ? "true" : "false");
      });
    }

    const inlineSideToggle = document.getElementById("acgInlineSideToggle");
    if (inlineSideToggle) {
      inlineSideToggle.addEventListener("click", () => {
        if (typeof pycmd === "function") pycmd("speed-streak:toggle-inline-side");
      });
    }
    document.querySelectorAll("[data-visual-choice]").forEach((button) => {
      button.addEventListener("click", () => {
        state.visualSelectorChoice = String(button.getAttribute("data-visual-choice") || "sphere");
        applyVisualResourceLevel(state.visualSelectorChoice, highestVisualResourceLevel(state.visualSelectorChoice));
        renderVisualResourceSelector(state.data || {});
      });
    });
    if (visualResourceSlider) {
      visualResourceSlider.addEventListener("input", () => {
        renderVisualResourceSelector(state.data || {}, Number(visualResourceSlider.value));
      });
      visualResourceSlider.addEventListener("change", () => {
        applyVisualResourceLevel(state.visualSelectorChoice, Number(visualResourceSlider.value));
      });
    }
    const stage = document.getElementById("acgStage");
    if (stage && visualSelector && visualSelectorToggle) {
      const openVisualSelector = () => {
        state.visualSelectorChoice = getVisualMode(state.data || {});
        visualSelector.classList.add("open");
        visualSelectorToggle.setAttribute("aria-expanded", "true");
        renderVisualResourceSelector(state.data || {});
      };
      stage.addEventListener("pointerup", openVisualSelector, true);
      stage.addEventListener("click", openVisualSelector);
    }
    const sidebarRoot = document.getElementById("speed-streak-sidebar");
    if (sidebarRoot && visualSelector && visualSelectorToggle) {
      const syncSidebarWidth = () => {
        const width = Math.floor(sidebarRoot.getBoundingClientRect().width || 0);
        if (width <= 0) return;
        sidebarRoot.style.setProperty("--acg-sidebar-width", `${width}px`);
        sidebarRoot.classList.toggle("narrow-pane", width < 230);
      };
      syncSidebarWidth();
      state.sidebarResizeObserver?.disconnect?.();
      if (typeof ResizeObserver === "function") {
        state.sidebarResizeObserver = new ResizeObserver(syncSidebarWidth);
        state.sidebarResizeObserver.observe(sidebarRoot);
      }
      sidebarRoot.addEventListener("mouseleave", () => {
        visualSelector.classList.remove("open");
        visualSelectorToggle.setAttribute("aria-expanded", "false");
        if (visualSelector.contains(document.activeElement)) document.activeElement?.blur?.();
      });
    }

    const boostBank = document.getElementById("acgBoostCharges");
    const boostBankHost = boostBank?.parentElement;
    state.boostBankResizeObserver?.disconnect?.();
    if (boostBankHost && typeof ResizeObserver === "function") {
      state.boostBankResizeObserver = new ResizeObserver(() => {
        if (state.data) renderGameplayEconomy(state.data);
      });
      state.boostBankResizeObserver.observe(boostBankHost);
    }

    const hapticsToggle = document.getElementById("acgHapticsToggle");
    if (hapticsToggle) {
      hapticsToggle.addEventListener("click", () => {
        saveSettings({ hapticsEnabled: !Boolean(state.data?.hapticsEnabled ?? true) });
      });
    }

    const audioToggle = document.getElementById("acgAudioToggle");
    if (audioToggle) {
      audioToggle.addEventListener("click", () => {
        saveSettings({ audioEnabled: !Boolean(state.data?.audioEnabled ?? false) });
      });
    }

    const enabledToggle = document.getElementById("acgEnabledToggle");
    if (enabledToggle) {
      enabledToggle.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:toggle-enabled");
        }
      });
    }

    const displayModeToggle = document.getElementById("acgDisplayModeToggle");
    if (displayModeToggle) {
      displayModeToggle.addEventListener("click", () => {
        if (!Boolean(state.data?.sidePanelEnabled ?? true)) {
          return;
        }
        if (typeof pycmd === "function") {
          pycmd("speed-streak:toggle-display-mode");
        }
      });
    }

    const boostButton = document.getElementById("acgBoostButton");
    if (boostButton) {
      boostButton.addEventListener("click", (event) => {
        if (typeof pycmd !== "function") return;
        pycmd("speed-streak:open-settings:shortcut:boost");
        if (event.detail > 0) boostButton.blur();
      });
    }

    const bindFocusRuleToggle = (id, rule, dataKey) => {
      const button = document.getElementById(id);
      if (!button) return;
      button.addEventListener("click", (event) => {
        if (typeof pycmd !== "function") return;
        const enabled = !Boolean(state.data?.[dataKey]);
        pycmd(`speed-streak:set-focus-rule:${rule}:${enabled ? 1 : 0}`);
        if (event.detail > 0) button.blur();
      });
    };
    bindFocusRuleToggle("acgNoPauseToggle", "no-pause", "noPauseMode");
    bindFocusRuleToggle("acgNoUndoToggle", "no-undo", "noUndoMode");

    const boostHoverZone = document.getElementById("acgBoostHoverZone");
    if (boostHoverZone) {
      const openTimeBoostSettings = (event) => {
        const target = event.target;
        if (target?.closest?.(".acg-boost-hover-controls")) return;
        const setting = target?.closest?.(".acg-boost-progress, #acgBoostProgressText")
          ? "cards"
          : "capacity";
        if (event.detail > 0) {
          const focused = document.activeElement;
          if (focused && boostHoverZone.contains(focused) && typeof focused.blur === "function") {
            focused.blur();
          }
          boostHoverZone.blur();
        }
        if (typeof pycmd === "function") {
          pycmd(`speed-streak:open-settings:gameplay:time-boost:${setting}`);
        }
      };
      boostHoverZone.addEventListener("click", openTimeBoostSettings);
      boostHoverZone.addEventListener("keydown", (event) => {
        if (event.target !== boostHoverZone || !["Enter", " "].includes(event.key)) return;
        event.preventDefault();
        openTimeBoostSettings(event);
      });
    }
    window.addEventListener("resize", () => renderGameplayEconomy(state.data || {}));

    const windowPresetsToggle = document.getElementById("acgWindowPresetsToggle");
    if (windowPresetsToggle) {
      windowPresetsToggle.addEventListener("click", () => {
        state.presetsOpen = !state.presetsOpen;
        state.presetMenuOpenId = "";
        renderWindowPositionPresets(state.data || {});
      });
    }

    const windowPresetSave = document.getElementById("acgWindowPresetSave");
    if (windowPresetSave) {
      windowPresetSave.addEventListener("click", () => {
        sendWindowPresetCommand("save");
      });
    }

    const windowPresetList = document.getElementById("acgWindowPresetList");
    if (windowPresetList) {
      windowPresetList.addEventListener("click", (event) => {
        const button = event.target?.closest?.("[data-preset-action]");
        if (!button) {
          return;
        }
        const action = button.getAttribute("data-preset-action") || "";
        const presetId = button.getAttribute("data-preset-id") || "";
        if (action === "menu") {
          state.presetMenuOpenId = state.presetMenuOpenId === presetId ? "" : presetId;
          renderWindowPositionPresets(state.data || {});
          return;
        }
        if (action === "apply") {
          state.presetsOpen = false;
          state.presetMenuOpenId = "";
        }
        if (action === "rename" || action === "delete") {
          state.presetMenuOpenId = "";
        }
        sendWindowPresetCommand(action, presetId);
        renderWindowPositionPresets(state.data || {});
      });
    }

    const collapseTab = document.getElementById("acgCollapseTab");
    if (collapseTab) {
      collapseTab.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:toggle-collapsed");
        }
      });
    }

    const resetButton = document.getElementById("acgResetGameButton");
    if (resetButton) {
      resetButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:reset");
        }
      });
    }

    const closeButton = document.getElementById("acgCloseSettings");
    if (closeButton) {
      closeButton.addEventListener("click", () => setSettingsOpen(false));
    }

    const questionInput = document.getElementById("acgQuestionSeconds");
    if (questionInput) {
      questionInput.addEventListener("change", () => saveSettings());
      questionInput.addEventListener("blur", () => saveSettings());
    }

    const answerInput = document.getElementById("acgAnswerSeconds");
    if (answerInput) {
      answerInput.addEventListener("change", () => saveSettings());
      answerInput.addEventListener("blur", () => saveSettings());
    }

    const freeFirstCardInput = document.getElementById("acgFreeFirstCardOnReviewEntry");
    if (freeFirstCardInput) {
      freeFirstCardInput.addEventListener("change", () => saveSettings());
    }

    const answerTimeoutBreaksStreakInput = document.getElementById("acgAnswerTimeoutBreaksStreak");
    if (answerTimeoutBreaksStreakInput) {
      answerTimeoutBreaksStreakInput.addEventListener("change", () => saveSettings());
    }

    const resumeRunInput = document.getElementById("acgResumeRunAfterRestart");
    if (resumeRunInput) {
      resumeRunInput.addEventListener("change", () => saveSettings());
    }

    const showCardTimerInput = document.getElementById("acgShowCardTimer");
    if (showCardTimerInput) {
      showCardTimerInput.addEventListener("change", () => saveSettings());
    }

    const sidePanelEnabledInput = document.getElementById("acgSidePanelEnabled");
    if (sidePanelEnabledInput) {
      sidePanelEnabledInput.addEventListener("change", () => saveSettings());
    }

    const orbitAnimationInput = document.getElementById("acgOrbitAnimation");
    if (orbitAnimationInput) {
      orbitAnimationInput.addEventListener("change", () => saveSettings());
    }

    const bindVibrationOnlyInput = (id) => {
      const input = document.getElementById(id);
      if (!input) {
        return;
      }
      input.addEventListener("change", () => {
        syncVibrationOnlyInputs(Boolean(input.checked), id);
        saveSettings();
      });
    };
    bindVibrationOnlyInput("acgVibrationOnlyMode");
    bindVibrationOnlyInput("acgVibrationOnlyModePerf");

    const statsButton = document.getElementById("acgStatsButton");
    if (statsButton) {
      statsButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:open-stats");
        }
      });
    }

    const pauseOverlay = document.getElementById("acgPauseOverlay");
    if (pauseOverlay) {
      pauseOverlay.addEventListener("contextmenu", (event) => {
        event.preventDefault();
        event.stopPropagation();
      });
      pauseOverlay.addEventListener("pointerup", (event) => {
        if (event.button === 2) {
          showPauseOverviewMenu(event);
        }
      });
    }

    const pauseOverviewMenu = document.getElementById("acgPauseOverviewMenu");
    if (pauseOverviewMenu) {
      pauseOverviewMenu.addEventListener("click", (event) => {
        const button = event.target?.closest?.("[data-pause-overview-action]");
        if (!button) {
          return;
        }
        event.preventDefault();
        event.stopPropagation();
        applyPauseOverviewAction(String(button.getAttribute("data-pause-overview-action") || "reset"));
      });
    }

    document.addEventListener("click", hidePauseOverviewMenu);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        hidePauseOverviewMenu();
      }
    });

    const appearanceButton = document.getElementById("acgAppearanceButton");
    if (appearanceButton) {
      appearanceButton.addEventListener("click", () => togglePanel("acgAppearancePanel"));
    }

    const colorCustomizerButton = document.getElementById("acgColorCustomizerButton");
    if (colorCustomizerButton) {
      colorCustomizerButton.addEventListener("click", openColorPanel);
    }

    const closeColorPanelButton = document.getElementById("acgCloseColorPanel");
    if (closeColorPanelButton) {
      closeColorPanelButton.addEventListener("click", closeColorPanel);
    }

    const colorResetButton = document.getElementById("acgColorResetButton");
    if (colorResetButton) {
      colorResetButton.addEventListener("click", () => {
        state.colorDrafts = {};
        state.useCustomTimerColorsDraft = false;
        renderColorInputs(state.colorDrafts);
        applyCustomColors($("speed-streak-sidebar"), state.colorDrafts, state.appearanceModeDraft || state.data?.appearanceMode || "midnight");
      });
    }

    const colorSaveButton = document.getElementById("acgColorSaveButton");
    if (colorSaveButton) {
      colorSaveButton.addEventListener("click", () => {
        const normalized = normalizeCustomColors(state.colorDrafts);
        if (state.data) {
          state.data.customColors = normalized;
          state.data.customTimerColors = Boolean(state.useCustomTimerColorsDraft);
        }
        saveSettings({ customColors: normalized, customTimerColors: Boolean(state.useCustomTimerColorsDraft) });
        closeColorPanel({ preserveDrafts: true });
      });
    }

    const timerColorMode = document.getElementById("acgTimerColorMode");
    if (timerColorMode) {
      timerColorMode.addEventListener("change", () => {
        state.useCustomTimerColorsDraft = Boolean(timerColorMode.checked);
      });
    }

    COLOR_FIELDS.forEach((field) => {
      const picker = document.getElementById(`acgColorPicker-${field.key}`);
      const hexInput = document.getElementById(`acgColorHex-${field.key}`);
      if (picker) {
        picker.addEventListener("input", () => updateDraftColor(field.key, picker.value));
      }
      if (hexInput) {
        hexInput.addEventListener("input", () => updateDraftColor(field.key, hexInput.value, { allowPartial: true }));
        hexInput.addEventListener("blur", () => updateDraftColor(field.key, hexInput.value));
      }
    });

    const appearanceMidnightButton = document.getElementById("acgAppearanceMidnight");
    if (appearanceMidnightButton) {
      appearanceMidnightButton.addEventListener("click", () => {
        state.appearanceModeDraft = "midnight";
        saveSettings();
      });
    }

    const appearanceCardButton = document.getElementById("acgAppearanceCard");
    if (appearanceCardButton) {
      appearanceCardButton.addEventListener("click", () => {
        state.appearanceModeDraft = "card";
        saveSettings();
      });
    }

    const helpButton = document.getElementById("acgHelpButton");
    if (helpButton) {
      helpButton.addEventListener("click", () => togglePanel("acgHelpPanel"));
    }

    const reviewLaterManagerButton = document.getElementById("acgReviewLaterManagerButton");
    if (reviewLaterManagerButton) {
      reviewLaterManagerButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:open-review-later-manager");
        }
      });
    }

    const defaultSettingsButton = document.getElementById("acgDefaultSettingsButton");
    if (defaultSettingsButton) {
      defaultSettingsButton.addEventListener("click", () => {
        const ok = window.confirm("Reset Speed Streak settings, watched flags, and saved orb colors to defaults?");
        if (!ok) return;
        if (typeof pycmd === "function") {
          pycmd("speed-streak:default-settings");
        }
      });
    }

    const timeDrainSelect = document.getElementById("acgTimeDrainFlag");
    if (timeDrainSelect) {
      timeDrainSelect.addEventListener("change", () => saveSettings());
    }

    const reviewLaterSelect = document.getElementById("acgReviewLaterFlag");
    if (reviewLaterSelect) {
      reviewLaterSelect.addEventListener("change", () => saveSettings());
    }

    bindTimeDrainToggleInput();

    renderFlagSelects(0, 0);

    state.mounted = true;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function ensureTimeDrainToggleControl() {
    if ($("acgTimeDrainReviewLast")) {
      return;
    }
    const body = document.querySelector("#acgTimeDrainOverlay .acg-time-drain-body");
    if (!body) {
      return;
    }
    body.insertAdjacentHTML("afterend", timeDrainToggleMarkup());
  }

  function bindTimeDrainToggleInput() {
    const input = $("acgTimeDrainReviewLast");
    if (!input || input.dataset.bound === "1") {
      return;
    }
    input.dataset.bound = "1";
    input.addEventListener("change", () => saveSettings());
  }

  function getFlagPalette(data = state.data) {
    return { ...DEFAULT_FLAG_PALETTE, ...(data?.flagPalette || {}) };
  }

  function rgbaFromColor(color, alpha) {
    const rgb = hexToRgb(color);
    if (!rgb) {
      return color;
    }
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`;
  }

  function applyFlagSelectTint(node, value, palette) {
    if (!node) {
      return;
    }
    const selectedValue = Number(value || 0);
    const color = palette[selectedValue] || palette[0] || DEFAULT_FLAG_PALETTE[0];
    if (selectedValue > 0) {
      node.style.borderColor = rgbaFromColor(color, 0.5);
      node.style.background = [
        "linear-gradient(45deg, transparent 50%, rgba(255,255,255,0.75) 50%)",
        "linear-gradient(135deg, rgba(255,255,255,0.75) 50%, transparent 50%)",
        `linear-gradient(180deg, ${rgbaFromColor(color, 0.24)}, rgba(255,255,255,0.04))`,
        "linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.92))",
      ].join(", ");
      node.style.boxShadow = `inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 24px ${rgbaFromColor(color, 0.12)}`;
    } else {
      node.style.borderColor = "rgba(255,255,255,0.12)";
      node.style.background = [
        "linear-gradient(45deg, transparent 50%, rgba(255,255,255,0.75) 50%)",
        "linear-gradient(135deg, rgba(255,255,255,0.75) 50%, transparent 50%)",
        "linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04))",
        "linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.92))",
      ].join(", ");
      node.style.boxShadow = "inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 24px rgba(0,0,0,0.12)";
    }
  }

  function syncVibrationOnlyInputs(checked, sourceId = "") {
    ["acgVibrationOnlyMode", "acgVibrationOnlyModePerf"].forEach((id) => {
      const input = $(id);
      if (!input) {
        return;
      }
      if (id === sourceId && input.checked === Boolean(checked)) {
        return;
      }
      input.checked = Boolean(checked);
    });
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function setText(nodeOrId, value) {
    const node = typeof nodeOrId === "string" ? $(nodeOrId) : nodeOrId;
    if (!node) {
      return;
    }
    const next = String(value ?? "");
    if (node.textContent !== next) {
      node.textContent = next;
    }
  }

  function getPauseShortcut(data) {
    const rawBindings = data && typeof data.shortcutBindings === "object" && data.shortcutBindings
      ? data.shortcutBindings
      : {};
    const rawValue = String((data && data.pauseShortcut) || rawBindings.pause || "P").trim();
    return rawValue || "P";
  }

  function getUnpauseShortcut(data) {
    const mode = String(data?.pauseShortcutMode || "combined").trim().toLowerCase();
    if (mode !== "split") {
      return getPauseShortcut(data);
    }
    const rawBindings = data && typeof data.shortcutBindings === "object" && data.shortcutBindings
      ? data.shortcutBindings
      : {};
    const rawValue = String(rawBindings.unpause || (data && data.unpauseShortcut) || "U").trim();
    return rawValue || "U";
  }

  function getBoostShortcut(data) {
    const rawBindings = data && typeof data.shortcutBindings === "object" && data.shortcutBindings
      ? data.shortcutBindings
      : {};
    const rawValue = String(rawBindings.boost || "B").trim();
    return rawValue || "B";
  }

  function syncShortcutCopy(data) {
    const pauseShortcut = getPauseShortcut(data);
    const unpauseShortcut = getUnpauseShortcut(data);
    const split = String(data?.pauseShortcutMode || "combined").trim().toLowerCase() === "split";
    setText("acgPauseShortcutLabel", unpauseShortcut);
    setText("acgHelpPauseShortcut", pauseShortcut);
    setText("acgBoostShortcutLabel", getBoostShortcut(data));
    const helpCopy = $("acgHelpShortcutCopy");
    if (helpCopy) {
      if (split) {
        helpCopy.innerHTML = `Press <strong id="acgHelpPauseShortcut">${escapeHtml(pauseShortcut)}</strong> to pause and <strong>${escapeHtml(unpauseShortcut)}</strong> to unpause.`;
      } else {
        helpCopy.innerHTML = `Press <strong id="acgHelpPauseShortcut">${escapeHtml(pauseShortcut)}</strong> to pause or unpause.`;
      }
    }
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setStyleProperty(node, property, value) {
    if (!node) {
      return;
    }
    const next = String(value ?? "");
    if (node.style.getPropertyValue(property) !== next) {
      node.style.setProperty(property, next);
    }
  }

  function setBackgroundStyle(node, value) {
    if (!node) {
      return;
    }
    const next = String(value ?? "");
    if (node.style.background !== next) {
      node.style.background = next;
    }
  }

  function getVisualMode(data) {
    const normalized = String(data?.visualMode || "").trim().toLowerCase();
    if (normalized === "crystal_reactor" || normalized === "crystal" || normalized === "reactor") {
      return "crystal_reactor";
    }
    if (normalized === "lightweight_rows" || normalized === "rows") {
      return "lightweight_rows";
    }
    const legacy = String(data?.renderMode || "").trim().toLowerCase();
    if (legacy === "lightweight_rows" || legacy === "rows") {
      return "lightweight_rows";
    }
    return "sphere";
  }

  function getRenderMode(data) {
    const normalized = String(data?.renderMode || "webgl").trim().toLowerCase();
    if (normalized === "webgl") {
      return "webgl";
    }
    if (normalized === "ultra_low_resource") {
      return "ultra_low_resource";
    }
    if (normalized === "low_resource") {
      return "low_resource";
    }
    return normalized === "classic" ? "classic" : "webgl";
  }

  function getSphereMode(data) {
    const normalized = String(data?.sphereMode || "classic").trim().toLowerCase();
    return normalized === "consolidate" ? "consolidate" : "classic";
  }

  function isReducedRenderMode(data) {
    return isLightweightRowsMode(data) || getRenderMode(data) !== "classic";
  }

  function isLightweightRowsMode(data) {
    return getVisualMode(data) === "lightweight_rows";
  }

  function isCrystalReactorMode(data) {
    return getVisualMode(data) === "crystal_reactor";
  }

  function isCrystalRotationEnabled(data) {
    return Boolean(data?.crystalRotationEnabled ?? true);
  }

  function getTimerStepMs(data) {
    const explicit = Math.max(0, Number(data?.timerDisplayStepMs || 0));
    if (explicit) {
      return explicit;
    }
    if (isLightweightRowsMode(data)) {
      return 100;
    }
    return getRenderMode(data) === "ultra_low_resource" ? 500 : 100;
  }

  function stopTimerLoop() {
    if (state.timerLoopId) {
      clearTimeout(state.timerLoopId);
      state.timerLoopId = 0;
    }
  }

  function timerLoopSignature(data) {
    const phase = String(data?.phase || "idle");
    return [
      getTimerStepMs(data),
      phase,
      Number(data?.phaseStartEpochMs || 0),
      Number(data?.phaseLimitMs || 0),
      Number(data?.paused || 0),
      Number(data?.firstCardFree || 0),
      Number(data?.enabled || 0),
      Number(data?.visualsEnabled || 0),
    ].join("|");
  }

  function needsLiveTimerLoop(data) {
    if (!data || !Number(data.enabled || 0) || !Number(data.visualsEnabled || 0)) {
      return false;
    }
    const phase = String(data.phase || "idle");
    if (phase !== "question" && phase !== "answer") {
      return false;
    }
    if (Boolean(data.paused)) {
      return false;
    }
    if (Boolean(data.firstCardFree)) {
      return false;
    }
    return Number(data.phaseLimitMs || 0) > 0 && computeSharedRemainingMs(data) > 0;
  }

  function nextTimerLoopDelayMs(data) {
    const stepMs = Math.max(1, getTimerStepMs(data));
    const anchorMs = Number(data?.timerDisplayNowEpochMs || 0);
    if (!anchorMs) {
      return stepMs;
    }
    const elapsed = Math.max(0, Date.now() - anchorMs);
    const remainder = elapsed % stepMs;
    const delay = remainder === 0 ? stepMs : stepMs - remainder;
    return Math.max(16, delay);
  }

  function scheduleTimerLoop() {
    if (!state.data || state.timerLoopId) {
      return;
    }
    state.timerLoopId = window.setTimeout(() => {
      state.timerLoopId = 0;
      if (!state.data) {
        return;
      }
      renderLiveTimerState(state.data);
      if (needsLiveTimerLoop(state.data)) {
        scheduleTimerLoop();
      }
    }, nextTimerLoopDelayMs(state.data));
  }

  function syncTimerLoop() {
    if (!state.data || !needsLiveTimerLoop(state.data)) {
      state.timerLoopSignature = "";
      stopTimerLoop();
      return;
    }
    const signature = timerLoopSignature(state.data);
    if (signature !== state.timerLoopSignature) {
      state.timerLoopSignature = signature;
      stopTimerLoop();
    }
    scheduleTimerLoop();
  }

  function computeSharedRemainingMs(data) {
    const baseRemaining = Math.max(0, Number(data?.timerDisplayRemainingMs || 0));
    const anchorMs = Number(data?.timerDisplayNowEpochMs || 0);
    const stepMs = Math.max(1, getTimerStepMs(data));
    if (!anchorMs || baseRemaining <= 0) {
      return baseRemaining;
    }
    const elapsed = Math.max(0, Date.now() - anchorMs);
    const elapsedSteps = Math.floor(elapsed / stepMs);
    return Math.max(0, baseRemaining - (elapsedSteps * stepMs));
  }

  function formatTimerSecondsText(remainingMs) {
    return `${(Math.max(0, Number(remainingMs || 0)) / 1000).toFixed(1)}`;
  }

  function computeTimer(data) {
    const phase = data.phase || "idle";
    const limit = Number(data.phaseLimitMs || 0);
    const free = Boolean(data.firstCardFree);
    const phasePolicyLimit = phase === "question"
      ? Number(data.timerPolicyQuestionLimitMs ?? -1)
      : Number(data.timerPolicyAnswerLimitMs ?? -1);
    const untimed = String(data.timerPolicyMode || "") === "no_timeout" || phasePolicyLimit === 0;
    const paused = Boolean(data.paused);

    if (phase === "idle" || !Number(data.phaseStartEpochMs || 0)) {
      return { phase, free, untimed: false, paused, remaining: 0, total: 0, secondsText: "0.0" };
    }
    if (free) {
      return { phase, free: true, untimed: false, paused, remaining: 0, total: 0, secondsText: "0.0" };
    }
    if (untimed && !limit) {
      return { phase, free: false, untimed: true, paused: false, remaining: 0, total: 0, secondsText: "0.0" };
    }
    if (!limit) {
      return { phase, free: true, untimed: false, paused, remaining: 0, total: 0, secondsText: "0.0" };
    }
    const remaining = paused
      ? Math.max(0, Number(data.timerDisplayRemainingMs || 0))
      : computeSharedRemainingMs(data);
    if (paused) {
      return { phase, free: false, untimed: false, paused: true, remaining, total: limit, secondsText: formatTimerSecondsText(remaining) };
    }
    return {
      phase,
      free: false,
      untimed: false,
      paused: false,
      remaining,
      total: limit,
      secondsText: formatTimerSecondsText(remaining),
    };
  }

  function setSettingsOpen(open) {
    state.settingsOpen = open;
    const sidebar = $("speed-streak-sidebar");
    const modal = $("acgSettingsModal");
    const dim = $("acgDim");
    const pauseOverlay = $("acgPauseOverlay");
    if (sidebar) {
      sidebar.classList.toggle("settings-open", open);
    }
    if (modal) {
      modal.classList.toggle("visible", open);
    }
    if (dim) {
      dim.classList.toggle("visible", open || Boolean(state.data?.paused));
    }
    if (pauseOverlay) {
      pauseOverlay.classList.toggle("visible", Boolean(state.data?.paused) && !open);
    }
    if (!open) {
      closeColorPanel();
    }
    if (open && state.data) {
      syncSettingsFields(state.data);
    }
  }

  function togglePanel(id) {
    const panel = $(id);
    if (!panel) return;
    panel.classList.toggle("hidden");
  }

  function saveSettings(overrides = {}) {
    const q = Number($("acgQuestionSeconds")?.value || 12);
    const a = Number($("acgAnswerSeconds")?.value || 8);
    const freeFirstCardOnReviewEntry = Boolean(
      $("acgFreeFirstCardOnReviewEntry")?.checked ?? state.data?.freeFirstCardOnReviewEntry ?? true
    );
    const answerTimeoutBreaksStreak = Boolean(
      $("acgAnswerTimeoutBreaksStreak")?.checked ?? state.data?.answerTimeoutBreaksStreak ?? true
    );
    const f = Number($("acgTimeDrainFlag")?.value || 0);
    const timeDrainReviewLast = Boolean($("acgTimeDrainReviewLast")?.checked);
    const rl = Number($("acgReviewLaterFlag")?.value || 0);
    const sidePanelEnabled = Object.prototype.hasOwnProperty.call(overrides, "sidePanelEnabled")
      ? Boolean(overrides.sidePanelEnabled)
      : Boolean($("acgSidePanelEnabled")?.checked ?? state.data?.sidePanelEnabled ?? true);
    const showCardTimer = Boolean($("acgShowCardTimer")?.checked);
    const resumeRunAfterRestart = Boolean($("acgResumeRunAfterRestart")?.checked);
    const orbitAnimationEnabled = Boolean($("acgOrbitAnimation")?.checked);
    const visualsEnabled = !Boolean($("acgVibrationOnlyMode")?.checked || $("acgVibrationOnlyModePerf")?.checked);
    const visualMode = Object.prototype.hasOwnProperty.call(overrides, "visualMode")
      ? String(overrides.visualMode || getVisualMode(state.data || {}))
      : getVisualMode(state.data || {});
    const sphereMode = Object.prototype.hasOwnProperty.call(overrides, "sphereMode")
      ? String(overrides.sphereMode || getSphereMode(state.data || {}))
      : getSphereMode(state.data || {});
    const renderMode = Object.prototype.hasOwnProperty.call(overrides, "renderMode")
      ? String(overrides.renderMode || getRenderMode(state.data || {}))
      : getRenderMode(state.data || {});
    const crystalRotationEnabled = Object.prototype.hasOwnProperty.call(overrides, "crystalRotationEnabled")
      ? Boolean(overrides.crystalRotationEnabled)
      : isCrystalRotationEnabled(state.data || {});
    const reducedMotion = Boolean(state.data?.reducedMotion);
    const audioEnabled = Object.prototype.hasOwnProperty.call(overrides, "audioEnabled")
      ? Boolean(overrides.audioEnabled)
      : Boolean(state.data?.audioEnabled ?? false);
    const hapticsEnabled = Object.prototype.hasOwnProperty.call(overrides, "hapticsEnabled")
      ? Boolean(overrides.hapticsEnabled)
      : Boolean(state.data?.hapticsEnabled ?? true);
    const appearanceMode = state.appearanceModeDraft || state.data?.appearanceMode || "midnight";
    const customTimerColors = Object.prototype.hasOwnProperty.call(overrides, "customTimerColors")
      ? Boolean(overrides.customTimerColors)
      : Boolean(state.data?.customTimerColors);
    const customTimerColorLevel = Object.prototype.hasOwnProperty.call(overrides, "customTimerColorLevel")
      ? Number(overrides.customTimerColorLevel || 0)
      : Number(state.data?.customTimerColorLevel || 0);
    const customColors = Object.prototype.hasOwnProperty.call(overrides, "customColors")
      ? normalizeCustomColors(overrides.customColors)
      : normalizeCustomColors(state.data?.customColors || {});
    if (f > 0 && rl > 0 && f === rl) {
      return;
    }
    if (typeof pycmd === "function") {
      pycmd(
        `speed-streak:update-settings:${JSON.stringify({
          questionSeconds: q,
          answerSeconds: a,
          freeFirstCardOnReviewEntry,
          answerTimeoutBreaksStreak,
          timeDrainFlag: f,
          timeDrainReviewLast,
          reviewLaterFlag: rl,
          audioEnabled,
          hapticsEnabled,
          sidePanelEnabled,
          showCardTimer,
          resumeRunAfterRestart,
          orbitAnimationEnabled,
          visualMode,
          sphereMode,
          renderMode,
          crystalRotationEnabled,
          reducedMotion,
          customTimerColors,
          customTimerColorLevel,
          visualsEnabled,
          appearanceMode,
          customColors,
        })}`
      );
    }
  }

  function syncSettingsFields(data) {
    const normalizedColors = normalizeCustomColors(data.customColors || {});
    state.appearanceModeDraft = String(data.appearanceMode || "midnight");
    state.colorDrafts = normalizedColors;
    state.useCustomTimerColorsDraft = Boolean(data.customTimerColors);
    state.timerColorLevelDraft = Number(data.customTimerColorLevel || 0);

    const signature = JSON.stringify({
      question: Number(data.questionLimitMs || 12000),
      answer: Number(data.reviewLimitMs || 8000),
      freeFirstCardOnReviewEntry: Boolean(data.freeFirstCardOnReviewEntry ?? true),
      answerTimeoutBreaksStreak: Boolean(data.answerTimeoutBreaksStreak ?? true),
      sidePanelEnabled: Boolean(data.sidePanelEnabled ?? true),
      showCardTimer: Boolean(data.showCardTimer),
      resumeRunAfterRestart: Boolean(data.resumeRunAfterRestart),
      orbitAnimationEnabled: Boolean(data.orbitAnimationEnabled ?? true),
      visualsEnabled: Boolean(data.visualsEnabled),
      appearanceMode: state.appearanceModeDraft,
      customColors: normalizedColors,
      customTimerColors: state.useCustomTimerColorsDraft,
      customTimerColorLevel: state.timerColorLevelDraft,
      timeDrainFlag: Number(data.timeDrainFlag || 0),
      timeDrainReviewLast: Boolean(data.timeDrainReviewLast),
      reviewLaterFlag: Number(data.reviewLaterFlag || 0),
      flagPalette: data.flagPalette || {},
    });
    if (signature === state.lastSettingsSignature) {
      return;
    }
    state.lastSettingsSignature = signature;

    const questionInput = $("acgQuestionSeconds");
    const answerInput = $("acgAnswerSeconds");
    if (questionInput && document.activeElement !== questionInput) {
      questionInput.value = (Number(data.questionLimitMs || 12000) / 1000).toFixed(1);
    }
    if (answerInput && document.activeElement !== answerInput) {
      answerInput.value = (Number(data.reviewLimitMs || 8000) / 1000).toFixed(1);
    }
    const freeFirstCardInput = $("acgFreeFirstCardOnReviewEntry");
    if (freeFirstCardInput && document.activeElement !== freeFirstCardInput) {
      freeFirstCardInput.checked = Boolean(data.freeFirstCardOnReviewEntry ?? true);
    }
    const answerTimeoutBreaksStreakInput = $("acgAnswerTimeoutBreaksStreak");
    if (
      answerTimeoutBreaksStreakInput
      && document.activeElement !== answerTimeoutBreaksStreakInput
    ) {
      answerTimeoutBreaksStreakInput.checked = Boolean(data.answerTimeoutBreaksStreak ?? true);
    }
    const showCardTimerInput = $("acgShowCardTimer");
    if (showCardTimerInput && document.activeElement !== showCardTimerInput) {
      showCardTimerInput.checked = Boolean(data.showCardTimer);
    }
    const sidePanelEnabledInput = $("acgSidePanelEnabled");
    if (sidePanelEnabledInput && document.activeElement !== sidePanelEnabledInput) {
      sidePanelEnabledInput.checked = Boolean(data.sidePanelEnabled ?? true);
    }
    const resumeRunInput = $("acgResumeRunAfterRestart");
    if (resumeRunInput && document.activeElement !== resumeRunInput) {
      resumeRunInput.checked = Boolean(data.resumeRunAfterRestart);
    }
    const orbitAnimationInput = $("acgOrbitAnimation");
    if (orbitAnimationInput && document.activeElement !== orbitAnimationInput) {
      orbitAnimationInput.checked = Boolean(data.orbitAnimationEnabled ?? true);
    }
    const timeDrainReviewLastInput = $("acgTimeDrainReviewLast");
    if (timeDrainReviewLastInput && document.activeElement !== timeDrainReviewLastInput) {
      timeDrainReviewLastInput.checked = Boolean(data.timeDrainReviewLast);
    }
    syncVibrationOnlyInputs(!Boolean(data.visualsEnabled), document.activeElement?.id || "");
    renderColorInputs(state.colorDrafts);
    renderFlagSelects(Number(data.timeDrainFlag || 0), Number(data.reviewLaterFlag || 0));
    syncAppearanceButtons();
  }

  function syncAppearanceButtons() {
    const mode = state.appearanceModeDraft || "midnight";
    $("acgAppearanceMidnight")?.classList.toggle("active", mode === "midnight");
    $("acgAppearanceCard")?.classList.toggle("active", mode === "card");
  }

  function syncQuickControl(button, active, title) {
    if (!button) {
      return;
    }
    button.classList.toggle("is-on", Boolean(active));
    button.classList.toggle("is-selected", Boolean(active));
    button.setAttribute("aria-pressed", active ? "true" : "false");
    if (title) {
      button.setAttribute("title", title);
      button.setAttribute("aria-label", title);
    }
  }

  function visualResourceLevels(visualMode) {
    if (visualMode === "crystal_reactor") {
      return [
        {
          label: "Still",
          tick: "Still",
          description: "Stops continuous crystal rotation while keeping reactions and milestones. Estimated at roughly 70–85% of Animated load.",
        },
        {
          label: "Animated",
          tick: "Animated",
          description: "Full rotating Crystal Reactor with live reactions. Highest-quality crystal mode and the 100% comparison baseline.",
        },
      ];
    }
    if (visualMode === "lightweight_rows") {
      return [
        {
          label: "Ultra light",
          tick: "Fixed",
          description: "Brick Streak has one intentionally minimal mode. Estimated at roughly 20–35% of Full Orbit load.",
        },
      ];
    }
    return [
      {
        label: "Ultra light",
        tick: "Ultra",
        description: "Simplifies the orbit renderer for the lowest satellite cost. Estimated at roughly 35–55% of Full Orbit load.",
      },
      {
        label: "Balanced",
        tick: "Balanced",
        description: "Consolidates satellite motion while preserving the orbit identity. Estimated at roughly 65–80% of Full Orbit load.",
      },
      {
        label: "Full",
        tick: "Full",
        description: "Full WebGL orbit and independent satellite motion. Best visual fidelity and the 100% comparison baseline.",
      },
    ];
  }

  function highestVisualResourceLevel(visualMode) {
    return visualResourceLevels(visualMode).length - 1;
  }

  function currentVisualResourceLevel(data, visualMode) {
    if (visualMode !== getVisualMode(data)) return highestVisualResourceLevel(visualMode);
    if (visualMode === "crystal_reactor") return isCrystalRotationEnabled(data) ? 1 : 0;
    if (visualMode === "lightweight_rows") return 0;
    if (getRenderMode(data) === "ultra_low_resource") return 0;
    return getSphereMode(data) === "consolidate" ? 1 : 2;
  }

  function applyVisualResourceLevel(visualMode, rawLevel) {
    const level = Math.max(0, Math.min(highestVisualResourceLevel(visualMode), Math.round(Number(rawLevel) || 0)));
    if (visualMode === "crystal_reactor") {
      saveSettings({
        visualMode: "crystal_reactor",
        sphereMode: "classic",
        renderMode: "webgl",
        crystalRotationEnabled: level > 0,
      });
      return;
    }
    if (visualMode === "lightweight_rows") {
      saveSettings({ visualMode: "lightweight_rows", renderMode: "ultra_low_resource" });
      return;
    }
    saveSettings({
      visualMode: "sphere",
      sphereMode: level === 1 ? "consolidate" : "classic",
      renderMode: level === 0 ? "ultra_low_resource" : "webgl",
    });
  }

  function renderVisualResourceSelector(data, requestedLevel = null) {
    const actualVisualMode = getVisualMode(data);
    const choice = ["sphere", "crystal_reactor", "lightweight_rows"].includes(state.visualSelectorChoice)
      ? state.visualSelectorChoice
      : actualVisualMode;
    const levels = visualResourceLevels(choice);
    const level = requestedLevel === null
      ? currentVisualResourceLevel(data, choice)
      : Math.max(0, Math.min(levels.length - 1, Math.round(Number(requestedLevel) || 0)));
    const slider = $("acgVisualResourceSlider");
    const value = $("acgVisualResourceValue");
    const name = $("acgVisualResourceName");
    const ticks = $("acgVisualResourceTicks");
    const description = $("acgVisualResourceDescription");
    const panel = $("acgVisualResourcePanel");
    const currentIcon = $("acgVisualSelectorCurrentIcon");
    if (currentIcon) currentIcon.innerHTML = VISUAL_MODE_ICONS[actualVisualMode] || VISUAL_MODE_ICONS.sphere;
    document.querySelectorAll("[data-visual-choice]").forEach((button) => {
      const selected = button.getAttribute("data-visual-choice") === choice;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    if (name) {
      name.textContent = choice === "sphere" ? "Orbit resources" : choice === "crystal_reactor" ? "Crystal resources" : "Brick resources";
    }
    if (value) value.textContent = levels[level].label;
    if (description) description.textContent = levels[level].description;
    if (ticks) ticks.innerHTML = levels.map((item, index) => `<span class="${index === level ? "active" : ""}">${escapeHtml(item.tick)}</span>`).join("");
    if (slider) {
      slider.min = "0";
      slider.max = String(Math.max(0, levels.length - 1));
      slider.step = "1";
      slider.value = String(level);
      slider.disabled = levels.length === 1;
    }
    panel?.classList.toggle("fixed", levels.length === 1);
  }

  function syncQuickControls(data) {
    const audioEnabled = Boolean(data?.audioEnabled ?? false);
    const hapticsEnabled = Boolean(data?.hapticsEnabled ?? true);
    const audioToggle = $("acgAudioToggle");
    const displayModeToggle = $("acgDisplayModeToggle");
    const inlineSideToggle = $("acgInlineSideToggle");
    const displayMode = String(data?.displayMode || "inline");
    const sidePanelEnabled = Boolean(data?.sidePanelEnabled ?? true);
    state.visualSelectorChoice = document.getElementById("acgVisualSelector")?.classList.contains("open")
      ? state.visualSelectorChoice
      : getVisualMode(data);
    renderVisualResourceSelector(data);
    syncQuickControl(
      $("acgHapticsToggle"),
      hapticsEnabled,
      hapticsEnabled ? "Haptics on" : "Haptics off"
    );
    syncQuickControl(
      audioToggle,
      audioEnabled,
      audioEnabled ? "Sound on" : "Sound off"
    );
    if (audioToggle) {
      audioToggle.textContent = audioEnabled ? "🔊" : "🔇";
      audioToggle.setAttribute("aria-label", audioEnabled ? "Sound on" : "Sound off");
    }
    if (displayModeToggle) {
      const compatibility = displayMode === "compatibility";
      displayModeToggle.innerHTML = compatibility ? DISPLAY_MODE_ICONS.inline : DISPLAY_MODE_ICONS.external;
      displayModeToggle.disabled = !sidePanelEnabled;
      displayModeToggle.classList.toggle("disabled", !sidePanelEnabled);
      syncQuickControl(
        displayModeToggle,
        sidePanelEnabled && compatibility,
        sidePanelEnabled
          ? compatibility ? "Switch to inline side pane" : "Switch to external window"
          : "Turn Side Panel on to choose inline or external display"
      );
    }
    if (inlineSideToggle) {
      const inline = displayMode === "inline" && sidePanelEnabled;
      const side = String(data?.inlineSide || "left") === "right" ? "right" : "left";
      inlineSideToggle.classList.toggle("hidden", !inline);
      inlineSideToggle.textContent = side === "left" ? "→" : "←";
      inlineSideToggle.setAttribute("title", side === "left" ? "Move inline pane to the right" : "Move inline pane to the left");
      inlineSideToggle.setAttribute("aria-label", inlineSideToggle.getAttribute("title") || "Move inline pane");
    }
    renderWindowPositionPresets(data);
  }

  function renderFlagSelects(timeDrainFlag, reviewLaterFlag) {
    renderFlagSelect("acgTimeDrainFlag", timeDrainFlag, reviewLaterFlag);
    renderFlagSelect("acgReviewLaterFlag", reviewLaterFlag, timeDrainFlag);
  }

  function renderFlagSelect(id, selectedValue, blockedValue) {
    const node = $(id);
    if (!node) return;
    const palette = getFlagPalette();
    const signature = `${selectedValue}|${blockedValue}|${JSON.stringify(palette)}`;
    if (node.dataset.optionsSignature === signature) {
      applyFlagSelectTint(node, selectedValue, palette);
      return;
    }
    node.dataset.optionsSignature = signature;
    node.innerHTML = FLAG_OPTIONS.map((option) => {
      const disabled = option.value !== 0 && option.value === blockedValue ? " disabled" : "";
      const selected = option.value === selectedValue ? " selected" : "";
      const label = option.value === 0 ? "0 - Off" : `${option.value} - ${option.label}`;
      const color = palette[option.value] || palette[0];
      const style = option.value > 0
        ? ` style="color:${color}; background:${rgbaFromColor(color, 0.18)};"`
        : "";
      return `<option value="${option.value}"${selected}${disabled}${style}>${label}</option>`;
    }).join("");
    applyFlagSelectTint(node, selectedValue, palette);
  }

  function normalizeThemeKey(themeKey) {
    const normalized = String(themeKey || "midnight").trim().toLowerCase() || "midnight";
    return normalized === "card" ? "cardmatch" : normalized;
  }

  function themeDefaultColors(themeKey) {
    return { ...DEFAULT_CUSTOM_COLORS, ...(THEME_CUSTOM_COLOR_DEFAULTS[normalizeThemeKey(themeKey)] || {}) };
  }

  function resolveCustomColors(customColors, themeKey) {
    return { ...themeDefaultColors(themeKey), ...normalizeCustomColors(customColors || {}) };
  }

  function normalizeCustomColors(customColors) {
    const normalized = {};
    if (!customColors || typeof customColors !== "object") {
      return normalized;
    }
    COLOR_FIELDS.forEach((field) => {
      const value = normalizeHexColor(customColors[field.key]);
      if (value) {
        normalized[field.key] = value;
      }
    });
    return normalized;
  }

  function normalizeHexColor(value) {
    const raw = String(value || "").trim();
    if (!raw) {
      return "";
    }
    const withHash = raw.startsWith("#") ? raw : `#${raw}`;
    if (!/^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(withHash)) {
      return "";
    }
    if (withHash.length === 4) {
      return `#${withHash[1]}${withHash[1]}${withHash[2]}${withHash[2]}${withHash[3]}${withHash[3]}`.toLowerCase();
    }
    return withHash.toLowerCase();
  }

  function hexToRgb(hex) {
    const normalized = normalizeHexColor(hex);
    if (!normalized) {
      return [127, 176, 255];
    }
    return [
      Number.parseInt(normalized.slice(1, 3), 16),
      Number.parseInt(normalized.slice(3, 5), 16),
      Number.parseInt(normalized.slice(5, 7), 16),
    ];
  }

  function rgbToHex(rgb) {
    return `#${rgb.map((value) => clamp(Math.round(value), 0, 255).toString(16).padStart(2, "0")).join("")}`;
  }

  function mixHex(a, b, t) {
    const mix = [
      hexToRgb(a)[0] + ((hexToRgb(b)[0] - hexToRgb(a)[0]) * t),
      hexToRgb(a)[1] + ((hexToRgb(b)[1] - hexToRgb(a)[1]) * t),
      hexToRgb(a)[2] + ((hexToRgb(b)[2] - hexToRgb(a)[2]) * t),
    ];
    return rgbToHex(mix);
  }

  function rgba(hex, alpha) {
    const [r, g, b] = hexToRgb(hex);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }

  function adjustHex(hex, level) {
    const [r, g, b] = hexToRgb(hex);
    const amount = clamp(Number(level || 0), -1, 1);
    if (amount === 0) {
      return hex;
    }
    const target = amount > 0 ? 255 : 0;
    const mix = Math.abs(amount);
    return rgbToHex([
      r + ((target - r) * mix),
      g + ((target - g) * mix),
      b + ((target - b) * mix),
    ]);
  }

  function applyCustomColors(sidebar, customColors, themeKey = "midnight") {
    if (!sidebar) {
      return;
    }
    const palette = resolveCustomColors(customColors, themeKey);
    const signature = JSON.stringify({ themeKey, palette });
    if (signature === state.lastThemeSignature) {
      return;
    }
    state.lastThemeSignature = signature;
    const coreHighlight = mixHex(palette.core, "#ffffff", 0.82);
    const coreMid = mixHex(palette.core, "#5dd3c4", 0.24);
    const coreDeep = mixHex(palette.core, "#120b2c", 0.82);
    const redDeep = mixHex(palette.red, "#2b0812", 0.72);

    sidebar.style.setProperty("--acg-core-base", palette.core);
    sidebar.style.setProperty("--acg-core-highlight", coreHighlight);
    sidebar.style.setProperty("--acg-core-mid", coreMid);
    sidebar.style.setProperty("--acg-core-deep", coreDeep);
    sidebar.style.setProperty("--acg-core-glow", rgba(palette.core, 0.42));
    sidebar.style.setProperty("--acg-core-halo-strong", rgba(palette.core, 0.22));
    sidebar.style.setProperty("--acg-core-halo-soft", rgba(palette.core, 0.05));
    sidebar.style.setProperty("--acg-ring-color", rgba(palette.core, 0.15));
    sidebar.style.setProperty("--acg-ring-glow", rgba(palette.core, 0.08));
    sidebar.style.setProperty("--acg-disc-a", rgba(palette.core, 0.05));
    sidebar.style.setProperty("--acg-disc-b", rgba(palette.green, 0.32));
    sidebar.style.setProperty("--acg-disc-c", rgba(palette.yellow, 0.18));
    sidebar.style.setProperty("--acg-failed-highlight", mixHex(palette.red, "#ffffff", 0.74));
    sidebar.style.setProperty("--acg-failed-mid", mixHex(palette.red, "#ff9fb6", 0.24));
    sidebar.style.setProperty("--acg-failed-deep", redDeep);
    sidebar.style.setProperty("--acg-failed-glow", rgba(palette.red, 0.44));

    ["red", "yellow", "green", "blue"].forEach((key) => {
      const color = palette[key];
      sidebar.style.setProperty(`--acg-${key}`, color);
      sidebar.style.setProperty(`--acg-${key}-soft`, mixHex(color, "#ffffff", 0.72));
      sidebar.style.setProperty(`--acg-${key}-wave-border`, rgba(color, 0.62));
      sidebar.style.setProperty(`--acg-${key}-wave-glow`, rgba(color, 0.22));
    });
  }

  function renderColorInputs(customColors) {
    const palette = resolveCustomColors(customColors, state.appearanceModeDraft || state.data?.appearanceMode || "midnight");
    COLOR_FIELDS.forEach((field) => {
      const color = palette[field.key];
      const picker = $(`acgColorPicker-${field.key}`);
      const hexInput = $(`acgColorHex-${field.key}`);
      const swatch = $(`acgColorSwatch-${field.key}`);
      if (picker && picker.value !== color) {
        picker.value = color;
      }
      if (hexInput && document.activeElement !== hexInput) {
        hexInput.value = color;
      }
      if (swatch) {
        setBackgroundStyle(swatch, color);
      }
    });
    const timerCheckbox = $("acgTimerColorMode");
    if (timerCheckbox) {
      timerCheckbox.checked = Boolean(state.useCustomTimerColorsDraft);
    }
  }

  function updateDraftColor(key, value, options = {}) {
    const { allowPartial = false } = options;
    const raw = String(value || "").trim();
    const normalized = normalizeHexColor(raw);
    if (normalized) {
      state.colorDrafts = { ...normalizeCustomColors(state.colorDrafts), [key]: normalized };
      renderColorInputs(state.colorDrafts);
      applyCustomColors($("speed-streak-sidebar"), state.colorDrafts, state.appearanceModeDraft || state.data?.appearanceMode || "midnight");
      return;
    }
    if (allowPartial) {
      const hexInput = $(`acgColorHex-${key}`);
      if (hexInput) {
        hexInput.value = raw;
      }
      return;
    }
    const nextDrafts = normalizeCustomColors(state.colorDrafts);
    delete nextDrafts[key];
    state.colorDrafts = nextDrafts;
    renderColorInputs(state.colorDrafts);
    applyCustomColors($("speed-streak-sidebar"), state.colorDrafts, state.appearanceModeDraft || state.data?.appearanceMode || "midnight");
  }

  function openColorPanel() {
    const panel = $("acgColorPanel");
    if (!panel) {
      return;
    }
    state.colorDrafts = normalizeCustomColors(state.data?.customColors || {});
    state.useCustomTimerColorsDraft = Boolean(state.data?.customTimerColors);
    renderColorInputs(state.colorDrafts);
    applyCustomColors($("speed-streak-sidebar"), state.colorDrafts, state.appearanceModeDraft || state.data?.appearanceMode || "midnight");
    panel.classList.remove("hidden");
    panel.classList.add("visible");
  }

  function closeColorPanel(options = {}) {
    const { preserveDrafts = false } = options;
    const panel = $("acgColorPanel");
    if (!panel) {
      return;
    }
    panel.classList.remove("visible");
    panel.classList.add("hidden");
    if (!preserveDrafts) {
      state.colorDrafts = normalizeCustomColors(state.data?.customColors || {});
      state.useCustomTimerColorsDraft = Boolean(state.data?.customTimerColors);
      renderColorInputs(state.colorDrafts);
      applyCustomColors($("speed-streak-sidebar"), state.data?.customColors || {}, state.data?.appearanceMode || "midnight");
    }
  }

  function getTimerRampColors(data) {
    if (Boolean(data?.customTimerColors)) {
      const palette = resolveCustomColors(data?.customColors || {}, data?.appearanceMode || "midnight");
      const level = Number(data?.customTimerColorLevel || 0);
      return {
        idle: adjustHex(palette.blue, level),
        free: adjustHex(palette.green, level),
        green: hexToRgb(adjustHex(palette.green, level)),
        yellow: hexToRgb(adjustHex(palette.yellow, level)),
        red: hexToRgb(adjustHex(palette.red, level)),
      };
    }
    return {
      idle: "#7fb0ff",
      free: "#65f0c2",
      green: [101, 240, 194],
      yellow: [255, 217, 120],
      red: [255, 111, 150],
    };
  }

  function colorCssVariable(color) {
    switch (String(color || "")) {
      case "red":
        return "var(--acg-red)";
      case "yellow":
        return "var(--acg-yellow)";
      case "green":
        return "var(--acg-green)";
      case "blue":
      default:
        return "var(--acg-blue)";
    }
  }

  function orbitBaseOffset(ringIndex, count) {
    return ((ringIndex * 23) + (count % 2 ? 9 : 0)) % 360;
  }

  function consolidatedRingSpacing(bankCount) {
    return clamp(18 - (Math.max(0, bankCount - 10) * 0.14), 11, 18);
  }

  function consolidatedBankRadius(bankIndex, totalBankCount) {
    const spacing = consolidatedRingSpacing(totalBankCount);
    return 72 + (bankIndex * spacing);
  }

  function consolidatedLiveRadius(completedBankCount) {
    if (completedBankCount <= 0) {
      return 92;
    }
    const spacing = consolidatedRingSpacing(completedBankCount);
    return consolidatedBankRadius(completedBankCount - 1, completedBankCount) + spacing + 10;
  }

  function buildBankCounts(bankColors) {
    const counts = {
      red: 0,
      yellow: 0,
      green: 0,
      blue: 0,
    };
    bankColors.forEach((color) => {
      if (Object.prototype.hasOwnProperty.call(counts, color)) {
        counts[color] += 1;
      }
    });
    return counts;
  }

  function buildBankGradient(bankColors) {
    const counts = buildBankCounts(bankColors);
    const total = counts.red + counts.yellow + counts.green + counts.blue;
    if (!total) {
      return "conic-gradient(from -90deg, rgba(255,255,255,0.14) 0deg 360deg)";
    }
    let cursor = 0;
    const segments = [];
    ["red", "yellow", "green", "blue"].forEach((color) => {
      const count = counts[color];
      if (!count) {
        return;
      }
      const start = cursor;
      cursor += (count / total) * 360;
      segments.push(`${colorCssVariable(color)} ${start}deg ${cursor}deg`);
    });
    if (cursor < 360 && segments.length) {
      segments.push(`${segments[segments.length - 1].split(" ")[0]} ${cursor}deg 360deg`);
    }
    return `conic-gradient(from -90deg, ${segments.join(", ")})`;
  }

  function satelliteRgb(color) {
    const css = colorCssVariable(color);
    if (css === "var(--acg-red)") return [1.0, 0.44, 0.59, 1.0];
    if (css === "var(--acg-yellow)") return [1.0, 0.85, 0.47, 1.0];
    if (css === "var(--acg-green)") return [0.40, 0.94, 0.76, 1.0];
    return [0.50, 0.69, 1.0, 1.0];
  }

  function createShader(gl, type, source) {
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(shader) || "WebGL shader compile failed.");
    }
    return shader;
  }

  function createWebglProgram(gl) {
    const vertex = createShader(gl, gl.VERTEX_SHADER, `
      precision mediump float;
      attribute vec2 a_position;
      attribute vec4 a_color;
      attribute float a_size;
      uniform vec2 u_resolution;
      uniform float u_pixel_ratio;
      varying vec4 v_color;
      void main() {
        vec2 clip = a_position / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
        gl_PointSize = a_size * u_pixel_ratio;
        v_color = a_color;
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      void main() {
        vec2 centered = gl_PointCoord - vec2(0.5);
        float dist = length(centered);
        float alpha = smoothstep(0.5, 0.36, dist);
        float highlight = smoothstep(0.42, 0.0, length(gl_PointCoord - vec2(0.34, 0.30)));
        vec3 color = mix(v_color.rgb, vec3(1.0), highlight * 0.42);
        gl_FragColor = vec4(color, alpha * v_color.a);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "WebGL program link failed.");
    }
    return program;
  }

  function ensureWebglRenderer() {
    const canvas = $("acgWebglOrbit");
    if (!canvas) {
      return null;
    }
    if (state.webgl?.canvas === canvas && state.webgl.gl) {
      return state.webgl;
    }
    try {
      const gl = canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
      if (!gl) {
        return null;
      }
      const program = createWebglProgram(gl);
      const buffer = gl.createBuffer();
      const renderer = {
        canvas,
        gl,
        program,
        buffer,
        positionLocation: gl.getAttribLocation(program, "a_position"),
        colorLocation: gl.getAttribLocation(program, "a_color"),
        sizeLocation: gl.getAttribLocation(program, "a_size"),
        resolutionLocation: gl.getUniformLocation(program, "u_resolution"),
        pixelRatioLocation: gl.getUniformLocation(program, "u_pixel_ratio"),
        satellites: [],
        frameId: 0,
        running: false,
      };
      initializeWebglCanvasSizing(renderer);
      gl.useProgram(program);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      state.webgl = renderer;
      return renderer;
    } catch (_error) {
      return null;
    }
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[char]));
  }

  function sendWindowPresetCommand(action, id = "") {
    if (typeof pycmd !== "function") {
      return;
    }
    if (action === "save") {
      pycmd("speed-streak:window-preset-save");
      return;
    }
    pycmd(`speed-streak:window-preset:${action}:${encodeURIComponent(String(id || ""))}`);
  }

  function renderWindowPositionPresets(data) {
    const root = $("acgWindowPresets");
    const panel = $("acgWindowPresetsPanel");
    const list = $("acgWindowPresetList");
    const toggle = $("acgWindowPresetsToggle");
    if (!root || !panel || !list || !toggle) {
      return;
    }
    const compatibility = String(data?.displayMode || "inline") === "compatibility";
    const presets = Array.isArray(data?.windowPositionPresets) ? data.windowPositionPresets : [];
    const defaultPresetId = String(data?.windowPositionDefaultPresetId || "");
    if (!compatibility) {
      state.presetsOpen = false;
      state.presetMenuOpenId = "";
    }
    root.classList.toggle("open", compatibility && state.presetsOpen);
    root.classList.toggle("disabled", !compatibility);
    toggle.disabled = !compatibility;
    syncQuickControl(
      toggle,
      compatibility && state.presetsOpen,
      compatibility ? "Window position presets" : "Window presets available in external window mode"
    );
    const rows = [
      `
        <div class="acg-window-preset-row acg-window-preset-row-default">
          <button class="acg-window-preset-apply" type="button" data-preset-action="apply" data-preset-id="default">Default setup</button>
          <button class="acg-window-preset-default${defaultPresetId === "default" ? " active" : ""}" type="button" data-preset-action="set-default" data-preset-id="default" title="${defaultPresetId === "default" ? "Stop always using this setup" : "Always use this setup when external mode opens"}" aria-label="Always use Default setup">${defaultPresetId === "default" ? "✓" : "○"}</button>
        </div>
      `,
      ...presets.map((preset) => {
        const id = escapeHtml(preset.id || "");
        const name = escapeHtml(preset.name || "Saved setup");
        const menuOpen = state.presetMenuOpenId === String(preset.id || "");
        return `
          <div class="acg-window-preset-row${menuOpen ? " menu-open" : ""}">
            <button class="acg-window-preset-apply" type="button" data-preset-action="apply" data-preset-id="${id}">${name}</button>
            <button class="acg-window-preset-default${defaultPresetId === String(preset.id || "") ? " active" : ""}" type="button" data-preset-action="set-default" data-preset-id="${id}" title="${defaultPresetId === String(preset.id || "") ? "Stop always using this setup" : "Always use this setup when external mode opens"}" aria-label="Always use ${name}">${defaultPresetId === String(preset.id || "") ? "✓" : "○"}</button>
            <button class="acg-window-preset-menu-button" type="button" data-preset-action="menu" data-preset-id="${id}" aria-label="Edit ${name}">⋯</button>
            <div class="acg-window-preset-menu">
              <button type="button" data-preset-action="rename" data-preset-id="${id}">Rename</button>
              <button type="button" data-preset-action="delete" data-preset-id="${id}">Delete</button>
            </div>
          </div>
        `;
      }),
    ];
    list.innerHTML = rows.join("");
  }

  function initializeWebglCanvasSizing(renderer, onResize = null) {
    renderer.cssWidth = 0;
    renderer.cssHeight = 0;
    renderer.bufferWidth = 1;
    renderer.bufferHeight = 1;
    renderer.dpr = 0;
    renderer.needsResize = true;
    renderer.resizeObserver = null;
    if (typeof ResizeObserver !== "function") return;
    renderer.resizeObserver = new ResizeObserver((entries) => {
      const rect = entries?.[0]?.contentRect;
      if (rect) {
        renderer.cssWidth = Math.max(0, Number(rect.width || 0));
        renderer.cssHeight = Math.max(0, Number(rect.height || 0));
      }
      renderer.needsResize = true;
      if (typeof onResize === "function") onResize();
    });
    renderer.resizeObserver.observe(renderer.canvas);
  }

  function resizeWebglCanvas(renderer) {
    const canvas = renderer.canvas;
    const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
    if (!renderer.needsResize && renderer.dpr === dpr) {
      return {
        width: renderer.cssWidth,
        height: renderer.cssHeight,
        dpr: renderer.dpr,
        bufferWidth: renderer.bufferWidth,
        bufferHeight: renderer.bufferHeight,
      };
    }
    let width = Number(renderer.cssWidth || 0);
    let height = Number(renderer.cssHeight || 0);
    if (width <= 0 || height <= 0) {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, Number(rect.width || 0));
      height = Math.max(1, Number(rect.height || 0));
    }
    const nextWidth = Math.max(1, Math.round(width * dpr));
    const nextHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
      canvas.width = nextWidth;
      canvas.height = nextHeight;
    }
    renderer.cssWidth = width;
    renderer.cssHeight = height;
    renderer.bufferWidth = nextWidth;
    renderer.bufferHeight = nextHeight;
    renderer.dpr = dpr;
    renderer.needsResize = false;
    renderer.gl.viewport(0, 0, nextWidth, nextHeight);
    return { width, height, dpr, bufferWidth: nextWidth, bufferHeight: nextHeight };
  }

  function parseTimerColor(color) {
    const text = String(color || "").trim();
    const rgbMatch = text.match(/^rgba?\(([^)]+)\)$/i);
    if (rgbMatch) {
      const parts = rgbMatch[1].split(",").map((part) => Number(part.trim()));
      return [clamp(parts[0] || 0, 0, 255) / 255, clamp(parts[1] || 0, 0, 255) / 255, clamp(parts[2] || 0, 0, 255) / 255, 1];
    }
    const hex = normalizeHexColor(text) || "#7fb0ff";
    return [
      Number.parseInt(hex.slice(1, 3), 16) / 255,
      Number.parseInt(hex.slice(3, 5), 16) / 255,
      Number.parseInt(hex.slice(5, 7), 16) / 255,
      1,
    ];
  }

  function createTimerRingProgram(gl) {
    const vertex = createShader(gl, gl.VERTEX_SHADER, `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      uniform vec2 u_resolution;
      uniform float u_progress;
      uniform vec4 u_color;
      void main() {
        vec2 uv = (gl_FragCoord.xy / u_resolution) - vec2(0.5);
        uv.x *= u_resolution.x / u_resolution.y;
        float radius = length(uv);
        float ring = smoothstep(0.492, 0.472, radius) * smoothstep(0.365, 0.385, radius);
        float track = ring * 0.18;
        float angle = atan(uv.x, uv.y);
        if (angle < 0.0) angle += 6.28318530718;
        float active = step(angle, clamp(u_progress, 0.0, 1.0) * 6.28318530718);
        vec4 activeColor = vec4(u_color.rgb, ring * u_color.a);
        vec4 trackColor = vec4(1.0, 1.0, 1.0, track);
        gl_FragColor = mix(trackColor, activeColor, active);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "WebGL timer program link failed.");
    }
    return program;
  }

  function ensureTimerRingRenderer() {
    const canvas = $("acgTimerCanvas");
    if (!canvas) {
      return null;
    }
    if (state.timerWebgl?.canvas === canvas && state.timerWebgl.gl) {
      return state.timerWebgl;
    }
    try {
      const gl = canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
      if (!gl) {
        return null;
      }
      const program = createTimerRingProgram(gl);
      const buffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      const renderer = {
        canvas,
        gl,
        program,
        buffer,
        positionLocation: gl.getAttribLocation(program, "a_position"),
        resolutionLocation: gl.getUniformLocation(program, "u_resolution"),
        progressLocation: gl.getUniformLocation(program, "u_progress"),
        colorLocation: gl.getUniformLocation(program, "u_color"),
        frameId: 0,
        running: false,
        timer: null,
        animationSignature: "",
        drawStateSignature: "",
      };
      initializeWebglCanvasSizing(renderer, () => {
        if (renderer.timer && !renderer.frameId) {
          renderer.running = true;
          renderer.frameId = window.requestAnimationFrame(() => drawTimerRingFrame(renderer));
        }
      });
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      state.timerWebgl = renderer;
      return renderer;
    } catch (_error) {
      return null;
    }
  }

  function drawTimerRingFrame(renderer) {
    renderer.frameId = 0;
    const timer = renderer.timer;
    if (!timer) {
      return;
    }
    const { bufferWidth, bufferHeight } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    let progress = clamp(Number(timer.progress || 0), 0, 1);
    if (timer.active && timer.total > 0) {
      progress = clamp((timer.deadlineEpochMs - Date.now()) / timer.total, 0, 1);
    }
    const color = timer.color;
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(renderer.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
    gl.enableVertexAttribArray(renderer.positionLocation);
    gl.vertexAttribPointer(renderer.positionLocation, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(renderer.resolutionLocation, bufferWidth, bufferHeight);
    gl.uniform1f(renderer.progressLocation, progress);
    gl.uniform4f(renderer.colorLocation, color[0], color[1], color[2], color[3]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    if (timer.active && progress > 0) {
      renderer.frameId = window.requestAnimationFrame(() => drawTimerRingFrame(renderer));
    } else {
      renderer.running = false;
      renderer.frameId = 0;
    }
  }

  function syncTimerRingWebgl(timerHero, timer, color, progress, active, animationSignature, deadlineEpochMs) {
    const renderer = ensureTimerRingRenderer();
    if (!renderer) {
      timerHero?.classList.remove("webgl-timer-ready");
      return;
    }
    timerHero?.classList.add("webgl-timer-ready");
    const nextSignature = String(animationSignature || "");
    const signatureChanged = nextSignature !== renderer.animationSignature;
    const nextDrawStateSignature = `${nextSignature}|${Number(Boolean(active))}|${Number(progress || 0)}|${String(color || "")}`;
    const drawStateChanged = nextDrawStateSignature !== renderer.drawStateSignature;
    renderer.timer = {
      color: parseTimerColor(color),
      progress,
      active: Boolean(active),
      total: Number(timer?.total || 0),
      deadlineEpochMs: Number(deadlineEpochMs || 0),
    };
    if (signatureChanged && renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    renderer.animationSignature = nextSignature;
    renderer.drawStateSignature = nextDrawStateSignature;
    if (!active && renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    if ((active && (signatureChanged || !renderer.frameId)) || (!active && drawStateChanged)) {
      renderer.running = true;
      drawTimerRingFrame(renderer);
    }
  }

  function buildWebglSatellites(colors, data) {
    const sphereMode = getSphereMode(data);
    if (sphereMode === "consolidate") {
      const completedBankCount = Math.floor(colors.length / 10);
      const liveColors = colors.slice(completedBankCount * 10);
      if (!liveColors.length) {
        return [];
      }
      const radius = consolidatedLiveRadius(completedBankCount);
      const baseOffset = orbitBaseOffset(completedBankCount, liveColors.length);
      const duration = Math.max(4.2, 10.6 - (completedBankCount * 0.18) - (liveColors.length * 0.08));
      return liveColors.map((color, slotIndex) => ({
        angle: baseOffset + ((360 / liveColors.length) * slotIndex),
        radius,
        duration,
        color,
      }));
    }

    const ringCount = Math.max(1, Math.ceil(colors.length / 10));
    const satellites = [];
    for (let ringIndex = 0; ringIndex < ringCount; ringIndex += 1) {
      const ringColors = colors.slice(ringIndex * 10, (ringIndex + 1) * 10);
      const radius = 78 + (ringIndex * 26);
      const count = Math.max(1, ringColors.length);
      const baseOffset = orbitBaseOffset(ringIndex, count);
      const duration = Math.max(4.5, 12 - (ringIndex * 0.8) - (colors.length * 0.04));
      ringColors.forEach((color, slotIndex) => {
        satellites.push({
          angle: baseOffset + ((360 / count) * slotIndex),
          radius,
          duration,
          color,
        });
      });
    }
    return satellites;
  }

  function drawWebglFrame(renderer) {
    if (!renderer.running) {
      return;
    }
    const { width, height, dpr } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    const satellites = renderer.satellites || [];
    if (satellites.length) {
      const now = performance.now() / 1000;
      const values = new Float32Array(satellites.length * 7);
      satellites.forEach((sat, index) => {
        const theta = ((sat.angle + ((now / sat.duration) * 360)) * Math.PI) / 180;
        const offset = index * 7;
        const rgb = satelliteRgb(sat.color);
        values[offset] = Math.cos(theta) * sat.radius;
        values[offset + 1] = Math.sin(theta) * sat.radius;
        values[offset + 2] = 16;
        values[offset + 3] = rgb[0];
        values[offset + 4] = rgb[1];
        values[offset + 5] = rgb[2];
        values[offset + 6] = rgb[3];
      });

      gl.useProgram(renderer.program);
      gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
      gl.bufferData(gl.ARRAY_BUFFER, values, gl.DYNAMIC_DRAW);
      const stride = 7 * 4;
      gl.enableVertexAttribArray(renderer.positionLocation);
      gl.vertexAttribPointer(renderer.positionLocation, 2, gl.FLOAT, false, stride, 0);
      gl.enableVertexAttribArray(renderer.sizeLocation);
      gl.vertexAttribPointer(renderer.sizeLocation, 1, gl.FLOAT, false, stride, 2 * 4);
      gl.enableVertexAttribArray(renderer.colorLocation);
      gl.vertexAttribPointer(renderer.colorLocation, 4, gl.FLOAT, false, stride, 3 * 4);
      gl.uniform2f(renderer.resolutionLocation, width, height);
      gl.uniform1f(renderer.pixelRatioLocation, dpr);
      gl.drawArrays(gl.POINTS, 0, satellites.length);
    }

    renderer.frameId = window.requestAnimationFrame(() => drawWebglFrame(renderer));
  }

  function stopWebglOrbit() {
    const renderer = state.webgl;
    if (!renderer) {
      return;
    }
    renderer.running = false;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    try {
      renderer.gl.clearColor(0, 0, 0, 0);
      renderer.gl.clear(renderer.gl.COLOR_BUFFER_BIT);
    } catch (_error) {}
  }

  function crystalTierForStreak(streak) {
    const value = Math.max(0, Number(streak || 0));
    if (value >= 1000) return { index: 7, label: "TRANSCENDENT" };
    if (value >= 500) return { index: 6, label: "SINGULARITY" };
    if (value >= 250) return { index: 5, label: "ASCENDANT" };
    if (value >= 100) return { index: 4, label: "REACTOR" };
    if (value >= 50) return { index: 3, label: "CROWN" };
    if (value >= 25) return { index: 2, label: "PRISM" };
    if (value >= 10) return { index: 1, label: "IGNITION" };
    return { index: 0, label: "SEED" };
  }

  function crystalHash(value) {
    const raw = Math.sin((Number(value || 0) + 1) * 12.9898) * 43758.5453123;
    return raw - Math.floor(raw);
  }

  function crystalRgb(hex) {
    const rgb = hexToRgb(hex);
    return [rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, 1];
  }

  function crystalPalette(data) {
    const palette = resolveCustomColors(data?.customColors || {}, data?.appearanceMode || "midnight");
    return {
      core: crystalRgb(palette.core),
      red: crystalRgb(palette.red),
      yellow: crystalRgb(palette.yellow),
      green: crystalRgb(palette.green),
      blue: crystalRgb(palette.blue),
    };
  }

  function crystalRatingRgb(color, palette) {
    return palette[String(color || "")] || palette.blue;
  }

  function mixCrystalRgb(a, b, amount) {
    const t = clamp(Number(amount || 0), 0, 1);
    return [
      a[0] + ((b[0] - a[0]) * t),
      a[1] + ((b[1] - a[1]) * t),
      a[2] + ((b[2] - a[2]) * t),
      1,
    ];
  }

  function createCrystalShardProgram(gl) {
    const vertex = createShader(gl, gl.VERTEX_SHADER, `
      precision mediump float;
      attribute vec2 a_position;
      attribute vec2 a_center;
      attribute vec4 a_color;
      attribute float a_seed;
      attribute float a_fresh;
      uniform vec2 u_resolution;
      uniform float u_time;
      uniform float u_rotation;
      uniform float u_pulse;
      uniform float u_decade_lock;
      uniform float u_era_ignition;
      uniform float u_growth;
      uniform float u_failure;
      varying vec4 v_color;
      varying float v_sheen;
      void main() {
        float localGrowth = mix(1.0, u_growth, a_fresh);
        vec2 position = a_center + ((a_position - a_center) * localGrowth);
        position *= 1.0 + (u_pulse * 0.025) + (u_decade_lock * 0.018) + (u_era_ignition * 0.055);
        float rotationCos = cos(u_rotation);
        float rotationSin = sin(u_rotation);
        mat2 sceneRotation = mat2(rotationCos, -rotationSin, rotationSin, rotationCos);
        position = sceneRotation * position;
        vec2 rotatedCenter = sceneRotation * a_center;
        vec2 escape = normalize(rotatedCenter + vec2((a_seed - 0.5) * 24.0, (0.5 - a_seed) * 18.0));
        position += escape * u_failure * (28.0 + (a_seed * 92.0));
        position.y += u_failure * u_failure * ((a_seed - 0.34) * 110.0);
        vec2 clip = position / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
        v_color = a_color;
        v_sheen = 0.5 + (0.5 * sin((u_time * 0.72) + (a_seed * 19.0)));
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      varying float v_sheen;
      uniform float u_pulse;
      uniform float u_decade_lock;
      uniform float u_era_ignition;
      uniform float u_failure;
      void main() {
        float shimmer = 0.88 + (v_sheen * 0.16);
        vec3 color = v_color.rgb * shimmer;
        float celebration = (u_pulse * 0.16) + (u_decade_lock * 0.18) + (u_era_ignition * 0.32);
        color = mix(color, vec3(0.96, 0.99, 1.0), (v_sheen * 0.11) + celebration);
        gl_FragColor = vec4(color, v_color.a * (1.0 - u_failure));
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "Crystal shard program link failed.");
    }
    return program;
  }

  function createCrystalCoreProgram(gl) {
    const vertex = createShader(gl, gl.VERTEX_SHADER, `
      attribute vec3 a_position;
      attribute vec3 a_normal;
      attribute vec4 a_color;
      attribute float a_seed;
      uniform vec2 u_resolution;
      uniform float u_time;
      uniform float u_pulse;
      uniform float u_milestone;
      uniform float u_failure;
      varying vec4 v_color;
      varying float v_light;
      varying float v_alpha;
      void main() {
        float spin = -(u_time * 0.34);
        float c = cos(spin);
        float s = sin(spin);
        mat2 rotation = mat2(c, -s, s, c);
        vec3 position = a_position;
        vec3 normal = a_normal;
        position.xz = rotation * position.xz;
        normal.xz = rotation * normal.xz;
        float tilt = 0.16 + (sin(u_time * 0.44) * 0.05);
        float tc = cos(tilt);
        float ts = sin(tilt);
        position.yz = mat2(tc, -ts, ts, tc) * position.yz;
        normal.yz = mat2(tc, -ts, ts, tc) * normal.yz;
        float reactionScale = 1.0 + (u_pulse * 0.11) + (u_milestone * 0.19);
        position *= reactionScale;
        vec3 escapeDirection = normalize(position + vec3((a_seed - 0.5) * 26.0, (a_seed - 0.45) * 18.0, 7.0));
        position += escapeDirection * u_failure * (44.0 + (a_seed * 70.0));
        position.y += u_failure * u_failure * ((a_seed - 0.35) * 96.0);
        float perspective = 340.0 / max(190.0, 340.0 + position.z);
        vec2 screen = position.xy * perspective;
        vec2 clip = screen / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, clamp(position.z / 300.0, -0.9, 0.9), 1.0);
        vec3 lightDirection = normalize(vec3(-0.38, -0.7, 0.62));
        v_light = clamp(0.34 + (dot(normalize(normal), lightDirection) * 0.66), 0.22, 1.0);
        v_color = a_color;
        v_alpha = 1.0 - u_failure;
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      varying float v_light;
      varying float v_alpha;
      uniform float u_pulse;
      uniform float u_milestone;
      void main() {
        vec3 color = v_color.rgb * v_light;
        float ignition = (u_pulse * 0.22) + (u_milestone * 0.38);
        color = mix(color, vec3(1.0), ignition);
        color += v_color.rgb * 0.16;
        gl_FragColor = vec4(color, v_color.a * v_alpha);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "Crystal core program link failed.");
    }
    return program;
  }

  function moveSharedWebglCanvas(mode) {
    const canvas = $("acgWebglOrbit");
    const target = mode === "crystal" ? $("acgCrystalScene") : $("acgScene");
    if (canvas && target && canvas.parentElement !== target) {
      target.appendChild(canvas);
    }
    return canvas;
  }

  function ensureCrystalRenderer() {
    const canvas = moveSharedWebglCanvas("crystal");
    if (!canvas) return null;
    if (state.crystalWebgl?.canvas === canvas && state.crystalWebgl.gl && !state.crystalWebgl.gl.isContextLost()) {
      return state.crystalWebgl;
    }
    try {
      const existingGl = state.webgl?.canvas === canvas ? state.webgl.gl : null;
      const gl = existingGl && !existingGl.isContextLost()
        ? existingGl
        : canvas.getContext("webgl", { alpha: true, antialias: true, premultipliedAlpha: false });
      if (!gl) {
        console.warn("Speed Streak Crystal Reactor: the shared satellite WebGL canvas did not provide a context.");
        return null;
      }
      const program = createCrystalShardProgram(gl);
      const renderer = {
        canvas,
        gl,
        program,
        buffer: gl.createBuffer(),
        positionLocation: gl.getAttribLocation(program, "a_position"),
        centerLocation: gl.getAttribLocation(program, "a_center"),
        colorLocation: gl.getAttribLocation(program, "a_color"),
        seedLocation: gl.getAttribLocation(program, "a_seed"),
        freshLocation: gl.getAttribLocation(program, "a_fresh"),
        resolutionLocation: gl.getUniformLocation(program, "u_resolution"),
        timeLocation: gl.getUniformLocation(program, "u_time"),
        rotationLocation: gl.getUniformLocation(program, "u_rotation"),
        pulseLocation: gl.getUniformLocation(program, "u_pulse"),
        decadeLockLocation: gl.getUniformLocation(program, "u_decade_lock"),
        eraIgnitionLocation: gl.getUniformLocation(program, "u_era_ignition"),
        growthLocation: gl.getUniformLocation(program, "u_growth"),
        failureLocation: gl.getUniformLocation(program, "u_failure"),
        vertexCount: 0,
        componentCount: 0,
        sceneSignature: "",
        lastEventNonce: -1,
        lastStreak: 0,
        pulseStartedAt: 0,
        growthStartedAt: 0,
        decadeLockStartedAt: 0,
        eraIgnitionStartedAt: 0,
        milestoneStartedAt: 0,
        failureStartedAt: 0,
        pendingScene: null,
        frameId: 0,
        running: false,
        needsDraw: true,
      };
      initializeWebglCanvasSizing(renderer, () => {
        renderer.needsDraw = true;
        if (!renderer.running && isCrystalReactorMode(state.data)) {
          renderer.running = true;
          renderer.frameId = window.requestAnimationFrame((timestamp) => drawCrystalFrame(renderer, timestamp));
        }
      });
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      state.crystalWebgl = renderer;
      return renderer;
    } catch (error) {
      console.error("Speed Streak Crystal Reactor WebGL initialization failed:", error);
      return null;
    }
  }

  function crystalCameraForCount(count) {
    const value = Math.max(0, Number(count || 0));
    const ringIndex = value > 50 ? Math.floor((value - 1) / 50) : 0;
    const naturalRadius = value <= 50
      ? 50 + (5.8 * Math.sqrt(value))
      : 126 + (ringIndex * 23);
    const targetRadius = 91 + (42 * (1 - Math.exp(-value / 260)));
    return {
      scale: clamp(targetRadius / Math.max(targetRadius, naturalRadius), 0.22, 1),
      naturalRadius,
      targetRadius,
    };
  }

  function crystalRosetteBaselineGeometry(ordinal) {
    const value = Math.max(1, Math.floor(Number(ordinal || 1)));
    const seed = crystalHash((value * 13.71) + 2.4);
    const goldenAngle = Math.PI * (3 - Math.sqrt(5));
    return {
      seed,
      angle: (value * goldenAngle) - (Math.PI / 2) + ((seed - 0.5) * 0.16),
      radialDistance: 20 + (5.8 * Math.sqrt(value)),
      length: 30 + (seed * 17),
      width: 11 + (crystalHash(value * 7.31) * 8),
    };
  }

  function crystalMandalaRadius(ordinal, baseline) {
    const value = Math.max(1, Math.floor(Number(ordinal || 1)));
    if (value <= 50) {
      return baseline.radialDistance;
    }
    const ringIndex = Math.floor((value - 1) / 50);
    const ringTexture = (crystalHash((value * 3.17) + 8.2) - 0.5) * 6;
    return 74 + (ringIndex * 23) + ringTexture;
  }

  function fixedCrystalSheenPalette(data) {
    const theme = crystalPalette(data);
    return [
      mixCrystalRgb(theme.core, [0.94, 0.99, 1.0, 1], 0.78),
      mixCrystalRgb(theme.core, [0.57, 0.88, 0.96, 1], 0.72),
      mixCrystalRgb(theme.core, [0.67, 0.61, 1.0, 1], 0.76),
      mixCrystalRgb(theme.core, [0.38, 0.30, 0.78, 1], 0.72),
      mixCrystalRgb(theme.core, [0.16, 0.12, 0.39, 1], 0.66),
    ];
  }

  function appendCrystalMeshTriangle(values, points, center, color, seed, fresh) {
    points.forEach((point) => {
      values.push(
        point[0], point[1],
        center[0], center[1],
        color[0], color[1], color[2], color[3],
        seed,
        fresh,
      );
    });
  }

  function buildCrystalClusterVertices(count, data) {
    const value = Math.max(0, Math.floor(Number(count || 0)));
    const camera = crystalCameraForCount(value);
    const palette = fixedCrystalSheenPalette(data);
    const values = [];

    for (let index = 0; index < value; index += 1) {
      const ordinal = index + 1;
      const baseline = crystalRosetteBaselineGeometry(ordinal);
      const seed = baseline.seed;
      const angle = baseline.angle;
      const radialDistance = crystalMandalaRadius(ordinal, baseline);
      const radialX = Math.cos(angle);
      const radialY = Math.sin(angle);
      const tangentX = -radialY;
      const tangentY = radialX;
      const newestBeyondBaseline = value > 50 && index === value - 1;
      const emphasisScale = newestBeyondBaseline ? 1.22 : 1;
      const center = [
        radialX * radialDistance * camera.scale,
        radialY * radialDistance * 0.88 * camera.scale,
      ];
      const length = baseline.length * emphasisScale * camera.scale;
      const width = baseline.width * emphasisScale * camera.scale;
      const root = [center[0] - (radialX * length * 0.48), center[1] - (radialY * length * 0.48)];
      const tip = [center[0] + (radialX * length * 0.52), center[1] + (radialY * length * 0.52)];
      const left = [center[0] + (tangentX * width * 0.5), center[1] + (tangentY * width * 0.5)];
      const right = [center[0] - (tangentX * width * 0.5), center[1] - (tangentY * width * 0.5)];
      const ridge = [center[0] + (radialX * length * 0.07), center[1] + (radialY * length * 0.07)];
      const ringIndex = ordinal > 50 ? Math.floor((ordinal - 1) / 50) : 0;
      const paletteOffset = (ordinal + (ringIndex * 2)) % palette.length;
      const fresh = index === value - 1 ? 1 : 0;

      if (newestBeyondBaseline) {
        const glowScale = 1.62;
        const glowPoint = (point) => [
          center[0] + ((point[0] - center[0]) * glowScale),
          center[1] + ((point[1] - center[1]) * glowScale),
        ];
        const glowColor = [0.55, 0.78, 1, 0.16];
        const glowRoot = glowPoint(root);
        const glowTip = glowPoint(tip);
        const glowLeft = glowPoint(left);
        const glowRight = glowPoint(right);
        const glowRidge = glowPoint(ridge);
        appendCrystalMeshTriangle(values, [glowRoot, glowLeft, glowRidge], center, glowColor, seed, fresh);
        appendCrystalMeshTriangle(values, [glowRoot, glowRidge, glowRight], center, glowColor, seed + 0.07, fresh);
        appendCrystalMeshTriangle(values, [glowLeft, glowTip, glowRidge], center, glowColor, seed + 0.13, fresh);
        appendCrystalMeshTriangle(values, [glowRidge, glowTip, glowRight], center, glowColor, seed + 0.19, fresh);
      }

      appendCrystalMeshTriangle(values, [root, left, ridge], center, palette[(paletteOffset + 4) % palette.length], seed, fresh);
      appendCrystalMeshTriangle(values, [root, ridge, right], center, palette[(paletteOffset + 3) % palette.length], seed + 0.07, fresh);
      appendCrystalMeshTriangle(values, [left, tip, ridge], center, palette[paletteOffset], seed + 0.13, fresh);
      appendCrystalMeshTriangle(values, [ridge, tip, right], center, palette[(paletteOffset + 1) % palette.length], seed + 0.19, fresh);
    }

    return {
      values: new Float32Array(values),
      vertexCount: values.length / 10,
      camera,
      ringCount: value > 50 ? Math.floor((value - 1) / 50) + 1 : 1,
    };
  }

  function crystalTriangleNormal(a, b, c) {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const ac = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const normal = [
      (ab[1] * ac[2]) - (ab[2] * ac[1]),
      (ab[2] * ac[0]) - (ab[0] * ac[2]),
      (ab[0] * ac[1]) - (ab[1] * ac[0]),
    ];
    const length = Math.hypot(normal[0], normal[1], normal[2]) || 1;
    return [normal[0] / length, normal[1] / length, normal[2] / length];
  }

  function appendCrystalTriangle(values, a, b, c, color, seed) {
    const normal = crystalTriangleNormal(a, b, c);
    [a, b, c].forEach((point) => {
      values.push(
        point[0], point[1], point[2],
        normal[0], normal[1], normal[2],
        color[0], color[1], color[2], color[3],
        seed,
      );
    });
  }

  function buildCrystalCoreVertices(colors, data) {
    const streak = colors.length;
    const tier = crystalTierForStreak(streak);
    const palette = crystalPalette(data);
    const logarithmicGrowth = Math.log2(streak + 1);
    const sides = Math.min(18, 6 + (tier.index * 2));
    const radius = clamp(29 + (logarithmicGrowth * 2.7), 29, 49);
    const halfHeight = clamp(45 + (logarithmicGrowth * 3.8), 45, 76);
    const top = [0, -halfHeight, 0];
    const bottom = [0, halfHeight, 0];
    const values = [];
    for (let side = 0; side < sides; side += 1) {
      const angleA = ((side / sides) * Math.PI * 2) - (Math.PI / 2);
      const angleB = (((side + 1) / sides) * Math.PI * 2) - (Math.PI / 2);
      const waistA = [Math.cos(angleA) * radius, 1.5, Math.sin(angleA) * radius];
      const waistB = [Math.cos(angleB) * radius, 1.5, Math.sin(angleB) * radius];
      const ratingA = colors.length ? crystalRatingRgb(colors[(side * 17) % colors.length], palette) : palette.blue;
      const ratingB = colors.length ? crystalRatingRgb(colors[((side * 17) + 7) % colors.length], palette) : palette.green;
      const topColor = mixCrystalRgb(palette.core, ratingA, 0.42);
      const bottomColor = mixCrystalRgb(palette.core, ratingB, 0.58);
      const seed = crystalHash(side * 7.13 + streak);
      appendCrystalTriangle(values, top, waistA, waistB, topColor, seed);
      appendCrystalTriangle(values, bottom, waistB, waistA, bottomColor, seed);
    }
    return new Float32Array(values);
  }

  function uploadCrystalScene(renderer, colors, data, signature) {
    const componentCount = Math.max(0, Number(data?.streak || colors.length));
    const cluster = buildCrystalClusterVertices(componentCount, data);
    renderer.gl.bindBuffer(renderer.gl.ARRAY_BUFFER, renderer.buffer);
    renderer.gl.bufferData(renderer.gl.ARRAY_BUFFER, cluster.values, renderer.gl.STATIC_DRAW);
    renderer.vertexCount = cluster.vertexCount;
    renderer.componentCount = componentCount;
    renderer.camera = cluster.camera;
    renderer.ringCount = cluster.ringCount;
    renderer.sceneSignature = signature;
    renderer.lastStreak = componentCount;
    renderer.needsDraw = true;
  }

  function restartCrystalSceneClass(className, duration) {
    const scene = $("acgCrystalScene");
    if (!scene) return;
    scene.classList.remove(className);
    void scene.offsetWidth;
    scene.classList.add(className);
    window.setTimeout(() => scene.classList.remove(className), duration);
  }

  function renderCrystalReactor(data) {
    const scene = $("acgCrystalScene");
    const colors = Array.isArray(data?.satelliteColors) ? data.satelliteColors : [];
    const streak = Math.max(0, Number(data?.streak || colors.length));
    const rotationEnabled = isCrystalRotationEnabled(data);
    setText("acgCrystalStreak", String(streak));
    if (scene) {
      scene.dataset.motion = rotationEnabled ? "rotating" : "still";
      scene.dataset.growthEra = String(streak > 50 ? Math.floor((streak - 1) / 50) : 0);
      scene.dataset.eraProgress = String(streak > 50 ? ((streak - 1) % 50) + 1 : streak);
    }

    const renderer = ensureCrystalRenderer();
    scene?.classList.toggle("no-webgl", !renderer);
    scene?.classList.toggle("webgl-ready", Boolean(renderer));
    if (!renderer) return;
    const signature = `${streak}|${data?.appearanceMode || "midnight"}|${JSON.stringify(data?.customColors || {})}`;
    const nonce = Number(data?.eventNonce ?? -1);
    const newEvent = nonce !== renderer.lastEventNonce;
    const eventType = String(data?.lastEventType || "");
    const now = performance.now();

    if (newEvent && eventType === "timeout" && renderer.componentCount > 0) {
      renderer.failureStartedAt = now;
      renderer.needsDraw = true;
      renderer.pendingScene = { colors: colors.slice(), data, signature };
      restartCrystalSceneClass("fracturing", 860);
    } else if (!renderer.failureStartedAt && signature !== renderer.sceneSignature) {
      uploadCrystalScene(renderer, colors, data, signature);
    }

    if (newEvent && ["again", "hard", "good", "easy"].includes(eventType)) {
      renderer.pulseStartedAt = now;
      renderer.growthStartedAt = now;
      renderer.needsDraw = true;
      restartCrystalSceneClass("reacting", 700);
      if (streak > 0 && streak % 10 === 0) {
        renderer.decadeLockStartedAt = now;
        restartCrystalSceneClass("decade-complete", 820);
      }
      if (streak > 0 && streak % 50 === 0) {
        renderer.eraIgnitionStartedAt = now;
        restartCrystalSceneClass("era-complete", 1320);
      }
      if ([100, 250, 500, 1000].includes(streak)) {
        renderer.milestoneStartedAt = now;
        restartCrystalSceneClass("milestone", 1540);
      }
    }
    renderer.lastEventNonce = nonce;

    if (renderer.needsResize) renderer.needsDraw = true;

    if (!renderer.running && (rotationEnabled || renderer.needsDraw)) {
      renderer.running = true;
      renderer.frameId = window.requestAnimationFrame((timestamp) => drawCrystalFrame(renderer, timestamp));
    }
  }

  function drawCrystalFrame(renderer, timestamp = performance.now()) {
    if (!renderer.running || !isCrystalReactorMode(state.data)) {
      renderer.running = false;
      renderer.frameId = 0;
      return;
    }
    const { width, height, bufferWidth, bufferHeight } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    const pulse = clamp(1 - ((timestamp - renderer.pulseStartedAt) / 700), 0, 1);
    const decadeLock = clamp(1 - ((timestamp - renderer.decadeLockStartedAt) / 760), 0, 1);
    const eraIgnition = clamp(1 - ((timestamp - renderer.eraIgnitionStartedAt) / 1260), 0, 1);
    const milestone = clamp(1 - ((timestamp - renderer.milestoneStartedAt) / 1480), 0, 1);
    const growthProgress = clamp((timestamp - renderer.growthStartedAt) / 520, 0, 1);
    const growth = 1 - Math.pow(1 - growthProgress, 3);
    const visualPulse = clamp(pulse + (decadeLock * 0.18) + (eraIgnition * 0.3) + (milestone * 0.46), 0, 1);
    const rotationEnabled = isCrystalRotationEnabled(state.data);
    const rotation = rotationEnabled ? (timestamp / 1000) * 0.16 : 0;
    let failure = renderer.failureStartedAt
      ? clamp((timestamp - renderer.failureStartedAt) / 820, 0, 1)
      : 0;

    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    if (renderer.vertexCount > 0) {
      gl.useProgram(renderer.program);
      gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
      const stride = 10 * 4;
      gl.enableVertexAttribArray(renderer.positionLocation);
      gl.vertexAttribPointer(renderer.positionLocation, 2, gl.FLOAT, false, stride, 0);
      gl.enableVertexAttribArray(renderer.centerLocation);
      gl.vertexAttribPointer(renderer.centerLocation, 2, gl.FLOAT, false, stride, 2 * 4);
      gl.enableVertexAttribArray(renderer.colorLocation);
      gl.vertexAttribPointer(renderer.colorLocation, 4, gl.FLOAT, false, stride, 4 * 4);
      gl.enableVertexAttribArray(renderer.seedLocation);
      gl.vertexAttribPointer(renderer.seedLocation, 1, gl.FLOAT, false, stride, 8 * 4);
      gl.enableVertexAttribArray(renderer.freshLocation);
      gl.vertexAttribPointer(renderer.freshLocation, 1, gl.FLOAT, false, stride, 9 * 4);
      gl.uniform2f(renderer.resolutionLocation, width, height);
      gl.uniform1f(renderer.timeLocation, rotationEnabled ? timestamp / 1000 : 0);
      gl.uniform1f(renderer.rotationLocation, rotation);
      gl.uniform1f(renderer.pulseLocation, visualPulse);
      gl.uniform1f(renderer.decadeLockLocation, decadeLock);
      gl.uniform1f(renderer.eraIgnitionLocation, eraIgnition);
      gl.uniform1f(renderer.growthLocation, growth);
      gl.uniform1f(renderer.failureLocation, failure);
      gl.drawArrays(gl.TRIANGLES, 0, renderer.vertexCount);
    }
    renderer.needsDraw = false;

    if (renderer.failureStartedAt && failure >= 1) {
      const pending = renderer.pendingScene;
      renderer.failureStartedAt = 0;
      renderer.pendingScene = null;
      failure = 0;
      if (pending) {
        uploadCrystalScene(renderer, pending.colors, pending.data, pending.signature);
      }
    }
    const reactionActive = pulse > 0 || decadeLock > 0 || eraIgnition > 0 || milestone > 0 || growthProgress < 1 || failure > 0 || Boolean(renderer.failureStartedAt);
    if (rotationEnabled || reactionActive || renderer.needsDraw) {
      renderer.frameId = window.requestAnimationFrame((nextTimestamp) => drawCrystalFrame(renderer, nextTimestamp));
    } else {
      renderer.running = false;
      renderer.frameId = 0;
    }
  }

  function stopCrystalReactor() {
    const renderer = state.crystalWebgl;
    if (!renderer) return;
    renderer.running = false;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    try {
      renderer.gl.clearColor(0, 0, 0, 0);
      renderer.gl.clear(renderer.gl.COLOR_BUFFER_BIT | renderer.gl.DEPTH_BUFFER_BIT);
    } catch (_error) {}
  }

  function updateSceneMetrics({ field, scene, disc, colorsLength, ringCount, requiredSize, minScale = 0.42 }) {
    const bounds = field.getBoundingClientRect();
    const available = Math.max(180, Math.min(bounds.width || 220, bounds.height || 220) - 10);
    const sceneScale = clamp(available / requiredSize, minScale, 1);
    scene.style.setProperty("--scene-size", `${requiredSize}px`);
    scene.style.setProperty("--scene-scale", `${sceneScale}`);
    scene.classList.toggle("zooming-out", sceneScale < state.lastSceneScale - 0.015);
    window.clearTimeout(state.zoomTimer);
    state.zoomTimer = window.setTimeout(() => {
      scene.classList.remove("zooming-out");
    }, 560);

    if (disc) {
      const discSize = clamp(118 + (colorsLength * 5), 118, 280);
      disc.style.setProperty("--disc-size", `${discSize}px`);
      disc.style.setProperty("--disc-speed", `${Math.max(5, 16 - (colorsLength * 0.12))}s`);
      disc.style.setProperty("--disc-opacity", `${clamp(0.35 + (colorsLength * 0.015), 0.35, 0.92)}`);
      disc.style.setProperty("--disc-ring-count", `${Math.max(1, ringCount)}`);
    }

    state.lastSceneScale = sceneScale;
  }

  function renderClassicOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature) {
    const ringCount = Math.max(1, Math.ceil(colors.length / 10));
    if (signature === state.lastColorsSignature && ringCount === state.lastRingCount) {
      updateSceneMetrics({
        field,
        scene,
        disc,
        colorsLength: colors.length,
        ringCount,
        requiredSize: (Math.max(1, ringCount) * 52) + 150,
      });
      return;
    }

    const grouped = [];
    for (let i = 0; i < ringCount; i += 1) {
      grouped.push(colors.slice(i * 10, (i + 1) * 10));
    }

    let ringsHtml = "";
    let satellitesHtml = "";

    for (let ringIndex = 0; ringIndex < ringCount; ringIndex += 1) {
      const radius = 78 + (ringIndex * 26);
      const size = radius * 2;
      const unlocking = ringIndex >= state.lastRingCount ? " unlocking" : "";
      ringsHtml += `<div class="acg-ring${unlocking}" style="width:${size}px;height:${size}px;"></div>`;
    }

    grouped.forEach((ringColors, ringIndex) => {
      const radius = 78 + (ringIndex * 26);
      const count = Math.max(1, ringColors.length);
      const baseOffset = orbitBaseOffset(ringIndex, count);
      const orbitDuration = Math.max(4.5, 12 - (ringIndex * 0.8) - (colors.length * 0.04));
      ringColors.forEach((color, slotIndex) => {
        const angle = baseOffset + ((360 / count) * slotIndex);
        satellitesHtml += `<div class="acg-satellite ${color}" style="--angle:${angle}deg;--radius:${radius}px;--orbit-duration:${orbitDuration}s;"></div>`;
      });
    });

    ringsNode.innerHTML = ringsHtml;
    satellitesNode.innerHTML = satellitesHtml;

    updateSceneMetrics({
      field,
      scene,
      disc,
      colorsLength: colors.length,
      ringCount,
      requiredSize: (Math.max(1, ringCount) * 52) + 150,
    });

    state.lastColorsSignature = signature;
    state.lastRingCount = ringCount;
  }

  function renderConsolidatedOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature) {
    const completedBankCount = Math.floor(colors.length / 10);
    const liveColors = colors.slice(completedBankCount * 10);
    const ringCount = completedBankCount;
    if (signature === state.lastColorsSignature && ringCount === state.lastRingCount) {
      updateSceneMetrics({
        field,
        scene,
        disc,
        colorsLength: colors.length,
        ringCount,
        requiredSize: (() => {
          const outerRadius = liveColors.length
            ? consolidatedLiveRadius(completedBankCount)
            : (completedBankCount > 0 ? consolidatedBankRadius(completedBankCount - 1, completedBankCount) : 92);
          return (outerRadius * 2) + 88;
        })(),
        minScale: 0.14,
      });
      return;
    }

    let ringsHtml = "";
    for (let bankIndex = 0; bankIndex < completedBankCount; bankIndex += 1) {
      const bankColors = colors.slice(bankIndex * 10, (bankIndex + 1) * 10);
      const radius = consolidatedBankRadius(bankIndex, completedBankCount);
      const size = radius * 2;
      const unlocking = bankIndex >= state.lastRingCount ? " unlocking" : "";
      const emphasis = (bankIndex + 1) % 5 === 0 ? " emphasis" : "";
      const gradient = buildBankGradient(bankColors);
      ringsHtml += `<div class="acg-bank-ring-glow${emphasis}" style="width:${size}px;height:${size}px;--bank-gradient:${gradient};"></div>`;
      ringsHtml += `<div class="acg-bank-ring${unlocking}${emphasis}" style="width:${size}px;height:${size}px;--bank-gradient:${gradient};"></div>`;
    }

    let satellitesHtml = "";
    if (liveColors.length) {
      const radius = consolidatedLiveRadius(completedBankCount);
      const count = liveColors.length;
      const baseOffset = orbitBaseOffset(completedBankCount, count);
      const orbitDuration = Math.max(4.2, 10.6 - (completedBankCount * 0.18) - (liveColors.length * 0.08));
      liveColors.forEach((color, slotIndex) => {
        const angle = baseOffset + ((360 / count) * slotIndex);
        satellitesHtml += `<div class="acg-satellite ${color}" style="--angle:${angle}deg;--radius:${radius}px;--orbit-duration:${orbitDuration}s;"></div>`;
      });
    }

    ringsNode.innerHTML = ringsHtml;
    satellitesNode.innerHTML = satellitesHtml;

    const outerRadius = liveColors.length
      ? consolidatedLiveRadius(completedBankCount)
      : (completedBankCount > 0 ? consolidatedBankRadius(completedBankCount - 1, completedBankCount) : 92);
    updateSceneMetrics({
      field,
      scene,
      disc,
      colorsLength: colors.length,
      ringCount,
      requiredSize: (outerRadius * 2) + 88,
      minScale: 0.14,
    });

    state.lastColorsSignature = signature;
    state.lastRingCount = ringCount;
  }

  function renderWebglOrbit(colors, ringsNode, satellitesNode, field, scene, disc, data, signature) {
    const renderer = ensureWebglRenderer();
    if (!renderer) {
      $("speed-streak-sidebar")?.classList.remove("webgl-orbit");
      renderClassicOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature);
      return;
    }

    const sphereMode = getSphereMode(data);
    const ringCount = sphereMode === "consolidate"
      ? Math.floor(colors.length / 10)
      : Math.max(1, Math.ceil(colors.length / 10));

    renderer.satellites = buildWebglSatellites(colors, data);
    satellitesNode.innerHTML = "";

    if (signature !== state.lastColorsSignature || ringCount !== state.lastRingCount) {
      let ringsHtml = "";
      if (sphereMode === "consolidate") {
        for (let bankIndex = 0; bankIndex < ringCount; bankIndex += 1) {
          const bankColors = colors.slice(bankIndex * 10, (bankIndex + 1) * 10);
          const radius = consolidatedBankRadius(bankIndex, ringCount);
          const size = radius * 2;
          const unlocking = bankIndex >= state.lastRingCount ? " unlocking" : "";
          const emphasis = (bankIndex + 1) % 5 === 0 ? " emphasis" : "";
          const gradient = buildBankGradient(bankColors);
          ringsHtml += `<div class="acg-bank-ring-glow${emphasis}" style="width:${size}px;height:${size}px;--bank-gradient:${gradient};"></div>`;
          ringsHtml += `<div class="acg-bank-ring${unlocking}${emphasis}" style="width:${size}px;height:${size}px;--bank-gradient:${gradient};"></div>`;
        }
      } else {
        for (let ringIndex = 0; ringIndex < ringCount; ringIndex += 1) {
          const radius = 78 + (ringIndex * 26);
          const size = radius * 2;
          const unlocking = ringIndex >= state.lastRingCount ? " unlocking" : "";
          ringsHtml += `<div class="acg-ring${unlocking}" style="width:${size}px;height:${size}px;"></div>`;
        }
      }
      ringsNode.innerHTML = ringsHtml;
      state.lastColorsSignature = signature;
      state.lastRingCount = ringCount;
    }

    const outerRadius = sphereMode === "consolidate"
      ? (renderer.satellites.length
        ? consolidatedLiveRadius(ringCount)
        : (ringCount > 0 ? consolidatedBankRadius(ringCount - 1, ringCount) : 92))
      : (78 + (Math.max(0, ringCount - 1) * 26));
    updateSceneMetrics({
      field,
      scene,
      disc,
      colorsLength: colors.length,
      ringCount,
      requiredSize: sphereMode === "consolidate" ? (outerRadius * 2) + 88 : (Math.max(1, ringCount) * 52) + 150,
      minScale: sphereMode === "consolidate" ? 0.14 : 0.42,
    });

    if (!renderer.running) {
      renderer.running = true;
      renderer.frameId = window.requestAnimationFrame(() => drawWebglFrame(renderer));
    }
  }

  function renderRings(colors, data) {
    const ringsNode = $("acgRings");
    const satellitesNode = $("acgSatellites");
    const field = $("acgField");
    const scene = $("acgScene");
    const disc = $("acgEnergyDisc");
    if (!ringsNode || !satellitesNode || !field || !scene) {
      return;
    }
    const renderMode = getRenderMode(data);
    const sphereMode = getSphereMode(data);
    const signature = `${renderMode}|${sphereMode}|${colors.join("|")}`;
    if (renderMode === "webgl") {
      renderWebglOrbit(colors, ringsNode, satellitesNode, field, scene, disc, data, signature);
      return;
    }
    stopWebglOrbit();
    if (sphereMode === "consolidate") {
      renderConsolidatedOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature);
      return;
    }
    renderClassicOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature);
  }

  function renderLightweightRows(data) {
    const gridNode = $("acgRowsGrid");
    const milestonesNode = $("acgRowsMilestones");
    const overflowNode = $("acgRowsOverflow");
    const streakValueNode = $("acgRowsStreakValue");
    if (!gridNode || !milestonesNode || !overflowNode || !streakValueNode) {
      return;
    }

    const streak = Math.max(0, Number(data?.streak || 0));
    const colors = Array.isArray(data?.satelliteColors) ? data.satelliteColors : [];
    const reducedMotion = Boolean(data?.reducedMotion);
    const milestoneCount = Math.floor(streak / 100);
    const remainder = streak % 100;
    const visibleMilestoneCount = Math.min(8, milestoneCount);
    const milestoneStart = Math.max(0, milestoneCount - visibleMilestoneCount);
    const visibleMilestoneColors = milestoneCount > 0
      ? colors.slice(milestoneStart * 100, milestoneCount * 100)
      : [];
    const currentBlockColors = remainder > 0 ? colors.slice(Math.max(0, colors.length - remainder)) : [];
    const signature = [
      streak,
      milestoneCount,
      remainder,
      reducedMotion ? 1 : 0,
      visibleMilestoneColors.join("|"),
      currentBlockColors.join("|"),
      String(data?.lastEventType || ""),
    ].join("|");
    if (signature === state.lastRowsSignature) {
      return;
    }

    const milestoneAnimationEnabled = !reducedMotion
      && ["again", "hard", "good", "easy"].includes(String(data?.lastEventType || ""))
      && streak > 0
      && remainder === 0;
    let milestonesHtml = "";
    for (let index = 0; index < visibleMilestoneCount; index += 1) {
      const milestoneNumber = milestoneStart + index + 1;
      const milestoneColors = colors.slice((milestoneNumber - 1) * 100, milestoneNumber * 100);
      const newest = milestoneNumber === milestoneCount;
      const consolidated = newest && milestoneAnimationEnabled ? " consolidated" : "";
      milestonesHtml += `
        <div class="acg-row-milestone${newest ? " newest" : ""}${consolidated}">
          <div class="acg-row-milestone-fill">${buildMilestoneFill(milestoneColors)}</div>
          <span class="acg-row-milestone-label">100</span>
        </div>
      `;
    }
    milestonesNode.innerHTML = milestonesHtml;

    if (milestoneCount > visibleMilestoneCount) {
      overflowNode.classList.remove("hidden");
      setText(overflowNode, `+${milestoneCount - visibleMilestoneCount}`);
    } else {
      overflowNode.classList.add("hidden");
      setText(overflowNode, "");
    }

    const lastEventType = String(data?.lastEventType || "");
    const ratingEvent = ["again", "hard", "good", "easy"].includes(lastEventType);
    const newestIndex = !reducedMotion && ratingEvent && remainder > 0 ? remainder - 1 : -1;
    const completedRowIndex = !reducedMotion && ratingEvent && remainder > 0 && remainder % 10 === 0
      ? 9 - Math.floor((remainder - 1) / 10)
      : -1;

    let gridHtml = "";
    for (let rowIndex = 0; rowIndex < 10; rowIndex += 1) {
      const rowClasses = ["acg-rows-grid-row"];
      if (rowIndex === completedRowIndex) {
        rowClasses.push("row-complete");
      }
      gridHtml += `<div class="${rowClasses.join(" ")}">`;
      for (let colIndex = 0; colIndex < 10; colIndex += 1) {
        const cellIndex = ((9 - rowIndex) * 10) + colIndex;
        const cellClasses = ["acg-rows-cell"];
        if (cellIndex < remainder) {
          const color = String(currentBlockColors[cellIndex] || data?.lastSatelliteColor || "green");
          cellClasses.push("filled", color);
          if (cellIndex === newestIndex) {
            cellClasses.push("fresh");
          }
        } else {
          cellClasses.push("empty");
        }
        gridHtml += `<div class="${cellClasses.join(" ")}" data-cell-index="${cellIndex}"></div>`;
      }
      gridHtml += "</div>";
    }
    gridNode.innerHTML = gridHtml;

    setText(streakValueNode, String(streak));
    streakValueNode.className = "acg-rows-streak-value";
    streakValueNode.style.removeProperty("--streak-pulse-color");
    streakValueNode.style.removeProperty("color");
    if (ratingEvent) {
      const pulseColor = rowsPulseColor(String(data?.lastSatelliteColor || ""));
      streakValueNode.style.setProperty("--streak-pulse-color", pulseColor);
      void streakValueNode.offsetWidth;
      streakValueNode.classList.add("pulse");
    }
    state.lastRowsSignature = signature;
  }

  function clearRowsScene() {
    const gridNode = $("acgRowsGrid");
    const milestonesNode = $("acgRowsMilestones");
    const overflowNode = $("acgRowsOverflow");
    const fxNode = $("acgRowsFx");
    const streakValueNode = $("acgRowsStreakValue");
    if (!state.lastRowsSignature && !gridNode?.innerHTML && !milestonesNode?.innerHTML) {
      return;
    }
    if (gridNode) {
      gridNode.innerHTML = "";
    }
    if (milestonesNode) {
      milestonesNode.innerHTML = "";
    }
    if (overflowNode) {
      overflowNode.classList.add("hidden");
      setText(overflowNode, "");
    }
    if (fxNode) {
      fxNode.innerHTML = "";
    }
    if (streakValueNode) {
      setText(streakValueNode, "0");
      streakValueNode.className = "acg-rows-streak-value";
      streakValueNode.style.removeProperty("--streak-pulse-color");
      streakValueNode.style.removeProperty("color");
    }
    state.lastRowsSignature = "";
  }

  function buildMilestoneFill(blockColors) {
    const counts = {
      blue: 0,
      green: 0,
      yellow: 0,
      red: 0,
    };
    blockColors.forEach((color) => {
      if (Object.prototype.hasOwnProperty.call(counts, color)) {
        counts[color] += 1;
      }
    });
    const total = counts.blue + counts.green + counts.yellow + counts.red;
    if (!total) {
      return '<span class="acg-row-milestone-segment neutral" style="flex:1"></span>';
    }
    return ["blue", "green", "yellow", "red"]
      .map((color) => `<span class="acg-row-milestone-segment ${color}" style="flex:${counts[color]}"></span>`)
      .join("");
  }

  function rowsPulseColor(color) {
    switch (String(color || "")) {
      case "blue":
        return "var(--acg-blue)";
      case "green":
        return "var(--acg-green)";
      case "yellow":
        return "var(--acg-yellow)";
      case "red":
        return "var(--acg-red)";
      default:
        return "var(--acg-text)";
    }
  }

  function spawnRowsTimeoutCollapse() {
    const gridNode = $("acgRowsGrid");
    const fxNode = $("acgRowsFx");
    if (!gridNode || !fxNode) {
      return;
    }
    const gridRect = gridNode.getBoundingClientRect();
    const fxRect = fxNode.getBoundingClientRect();
    const filledCells = Array.from(gridNode.querySelectorAll(".acg-rows-cell.filled"))
      .sort((a, b) => Number(b.dataset.cellIndex || -1) - Number(a.dataset.cellIndex || -1));
    filledCells.forEach((cell, index) => {
      const rect = cell.getBoundingClientRect();
      const clone = document.createElement("div");
      const colorClass = ["red", "yellow", "green", "blue"].find((name) => cell.classList.contains(name)) || "blue";
      clone.className = `acg-rows-collapse-cell ${colorClass}`;
      clone.style.left = `${rect.left - fxRect.left}px`;
      clone.style.top = `${rect.top - fxRect.top}px`;
      clone.style.width = `${rect.width}px`;
      clone.style.height = `${rect.height}px`;
      clone.style.animationDelay = `${index * 50}ms`;
      fxNode.appendChild(clone);
      setTimeout(() => clone.remove(), 760 + (index * 50));
    });
  }

  function spawnRowsTimeoutFlash() {
    const fx = $("acgRowsFx");
    if (!fx) {
      return;
    }
    const flash = document.createElement("div");
    flash.className = "acg-rows-timeout-flash";
    fx.appendChild(flash);
    setTimeout(() => flash.remove(), 760);
  }

  function spawnShockwave(color) {
    const fx = $("acgFx");
    if (!fx) return;
    const wave = document.createElement("div");
    wave.className = `acg-shockwave ${color || "blue"}`;
    fx.appendChild(wave);
    setTimeout(() => wave.remove(), 700);
  }

  function spawnMilestoneFlare() {
    const fx = $("acgFx");
    if (!fx) return;
    const flare = document.createElement("div");
    flare.className = "acg-milestone-flare";
    fx.appendChild(flare);
    setTimeout(() => flare.remove(), 1200);
  }

  function spawnConsolidationSatellites(bankColors, completedBankCount) {
    const fx = $("acgFx");
    if (!fx || !bankColors.length || completedBankCount <= 0) {
      return;
    }
    const previousCompletedBankCount = Math.max(0, completedBankCount - 1);
    const startRadius = consolidatedLiveRadius(previousCompletedBankCount);
    const endRadius = consolidatedBankRadius(completedBankCount - 1, completedBankCount);
    const baseOffset = orbitBaseOffset(previousCompletedBankCount, bankColors.length);
    bankColors.forEach((color, slotIndex) => {
      const angle = baseOffset + ((360 / bankColors.length) * slotIndex);
      const node = document.createElement("div");
      node.className = `acg-satellite ${color} consolidating`;
      node.style.setProperty("--angle", `${angle}deg`);
      node.style.setProperty("--start-radius", `${startRadius}px`);
      node.style.setProperty("--mid-radius", `${Math.round((startRadius + endRadius) / 2)}px`);
      node.style.setProperty("--end-radius", `${endRadius}px`);
      node.style.animationDelay = `${slotIndex * 22}ms`;
      fx.appendChild(node);
      setTimeout(() => node.remove(), 820 + (slotIndex * 22));
    });
  }

  function triggerTimeoutCollapse(colors) {
    const fx = $("acgFx");
    if (!fx || !colors.length) return;
    const ringCount = Math.max(1, Math.ceil(colors.length / 10));
    for (let ringIndex = 0; ringIndex < ringCount; ringIndex += 1) {
      const ringColors = colors.slice(ringIndex * 10, (ringIndex + 1) * 10);
      const radius = 78 + (ringIndex * 26);
      const count = Math.max(1, ringColors.length);
      const baseOffset = ((ringIndex * 23) + (count % 2 ? 9 : 0)) % 360;
      ringColors.forEach((color, slotIndex) => {
        const angle = baseOffset + ((360 / count) * slotIndex);
        const node = document.createElement("div");
        node.className = `acg-satellite ${color} collapse`;
        node.style.setProperty("--angle", `${angle}deg`);
        node.style.setProperty("--radius", `${radius}px`);
        fx.appendChild(node);
        setTimeout(() => node.remove(), 600);
      });
    }
  }

  function handleStateEffects(data) {
    const nonce = Number(data.eventNonce || 0);
    if (nonce === state.lastNonce) {
      return;
    }

    triggerHaptics(data);

    const streak = Number(data.streak || 0);
    const milestones = new Set([10, 25, 50, 100]);
    const lightweightRows = isLightweightRowsMode(data);
    const crystalReactor = isCrystalReactorMode(data);
    const sphereMode = getSphereMode(data);
    const ultraLowResource = getRenderMode(data) === "ultra_low_resource";
    if (["again", "hard", "good", "easy"].includes(data.lastEventType)) {
      if (String(data.lastEventText || "").includes("charge earned")) {
        showToast("⚡ Time Boost charge earned");
      }
      if (!lightweightRows && !crystalReactor && !ultraLowResource) {
        spawnShockwave(data.lastSatelliteColor || "blue");
        if (sphereMode === "consolidate" && streak > 0 && streak % 10 === 0) {
          spawnConsolidationSatellites(
            (Array.isArray(data.satelliteColors) ? data.satelliteColors : []).slice(-10),
            Math.floor(streak / 10),
          );
        }
        if (milestones.has(streak)) {
          spawnMilestoneFlare();
        }
      }
    } else if (data.lastEventType === "time-boost") {
      showToast(String(data.lastEventText || "Time Boost activated"));
    } else if (data.lastEventType === "pause-blocked") {
      showToast("No Pause mode is active");
    } else if (data.lastEventType === "undo-blocked") {
      showToast("No Undo mode is active");
    } else if (data.lastEventType === "focus-rule") {
      showToast(String(data.lastEventText || "Focus rule updated"));
    } else if (data.lastEventType === "review-later-added") {
      showToast("Review Later");
    } else if (data.lastEventType === "review-later-removed") {
      showToast("Removed from 'Review Later'");
    } else if (data.lastEventType === "timeout") {
      if (lightweightRows) {
        spawnRowsTimeoutFlash();
        spawnRowsTimeoutCollapse();
      } else if (crystalReactor) {
        // The Crystal Reactor owns its fracture animation in the WebGL scene.
      } else if (!ultraLowResource && sphereMode !== "consolidate") {
        triggerTimeoutCollapse(state.prevColors);
        spawnShockwave("red");
      } else if (!ultraLowResource) {
        spawnShockwave("red");
      }
    }

    state.lastNonce = nonce;
  }

  function triggerHaptics(data) {
    if (!Number(data?.hapticsEnabled ?? 1)) {
      return;
    }
    if (Number(data.hapticsAvailable || 0) > 0) {
      return;
    }
    const rawKind = String(data.lastEventType || "");
    const kind = rawKind === "answer-timeout" ? "timeout" : rawKind;
    const fallbackPatterns = {
      reveal: [{ duration: 90, weak: 0.64, strong: 1.0 }],
      again: [
        { duration: 80, weak: 0.64, strong: 0.88 },
        { duration: 55, weak: 0, strong: 0 },
        { duration: 80, weak: 0.64, strong: 0.94 },
      ],
      hard: [{ duration: 95, weak: 0.36, strong: 0.55 }],
      good: [{ duration: 120, weak: 0.8, strong: 1.0 }],
      easy: [{ duration: 125, weak: 0.34, strong: 0.46 }],
      skip: [{ duration: 80, weak: 0.18, strong: 0.3 }],
      sync: [{ duration: 95, weak: 0.2, strong: 0.28 }],
      reset: [{ duration: 120, weak: 0.26, strong: 0.4 }],
      bossStart: [
        { duration: 80, weak: 0.34, strong: 0.58 },
        { duration: 70, weak: 0, strong: 0 },
        { duration: 110, weak: 0.4, strong: 0.66 },
      ],
      bossClear: [{ duration: 180, weak: 0.49, strong: 0.79 }],
      timeout: [
        { duration: 420, weak: 0.8, strong: 1.0 },
        { duration: 95, weak: 0, strong: 0 },
        { duration: 180, weak: 0.55, strong: 0.76 },
      ],
    };
    const fallbackEventPatterns = {
      sync: "sync",
      reveal: "reveal",
      again: "again",
      hard: "hard",
      good: "good",
      easy: "easy",
      skip: "skip",
      reset: "reset",
      timeout: "timeout",
    };
    const eventPatterns = data && typeof data.hapticEventPatterns === "object" && data.hapticEventPatterns
      ? data.hapticEventPatterns
      : fallbackEventPatterns;
    const patterns = data && typeof data.hapticPatternSequences === "object" && data.hapticPatternSequences
      ? data.hapticPatternSequences
      : fallbackPatterns;
    const patternKey = String(eventPatterns[kind] || fallbackEventPatterns[kind] || "");
    if (!patternKey || patternKey === "off") {
      return;
    }
    const sequence = Array.isArray(patterns[patternKey]) ? patterns[patternKey] : fallbackPatterns[patternKey];
    if (!sequence) {
      return;
    }
    playBrowserHaptics(sequence);
  }

  function playBrowserHaptics(sequence) {
    const actuator = getGamepadActuator();
    if (!actuator) {
      return;
    }
    window.clearTimeout(state.hapticTimer);
    runBrowserHapticStep(actuator, sequence.slice(), 0);
  }

  function runBrowserHapticStep(actuator, sequence, index) {
    if (index >= sequence.length) {
      stopBrowserHaptics(actuator);
      return;
    }

    const step = sequence[index];
    const duration = Math.max(0, Number(step.duration || 0));
    const weak = clamp(Number(step.weak || 0), 0, 1);
    const strong = clamp(Number(step.strong || 0), 0, 1);

    try {
      if (typeof actuator.playEffect === "function") {
        actuator.playEffect("dual-rumble", {
          duration,
          startDelay: 0,
          weakMagnitude: weak,
          strongMagnitude: strong,
        });
      } else if (typeof actuator.pulse === "function") {
        actuator.pulse(Math.max(weak, strong), duration);
      }
    } catch (error) {
      return;
    }

    state.hapticTimer = window.setTimeout(() => {
      runBrowserHapticStep(actuator, sequence, index + 1);
    }, duration);
  }

  function stopBrowserHaptics(actuator) {
    try {
      if (typeof actuator.playEffect === "function") {
        actuator.playEffect("dual-rumble", {
          duration: 0,
          startDelay: 0,
          weakMagnitude: 0,
          strongMagnitude: 0,
        });
      } else if (typeof actuator.pulse === "function") {
        actuator.pulse(0, 0);
      }
    } catch (error) {
      // Ignore unsupported stop calls.
    }
  }

  function getGamepadActuator() {
    const gamepads = typeof navigator.getGamepads === "function" ? navigator.getGamepads() : [];
    for (const gamepad of gamepads || []) {
      if (!gamepad) {
        continue;
      }
      if (gamepad.vibrationActuator) {
        return gamepad.vibrationActuator;
      }
      if (Array.isArray(gamepad.hapticActuators) && gamepad.hapticActuators.length > 0) {
        return gamepad.hapticActuators[0];
      }
    }
    return null;
  }

  function showToast(text) {
    const toast = $("acgToast");
    if (!toast) return;
    toast.textContent = text;
    toast.classList.remove("visible");
    void toast.offsetWidth;
    toast.classList.add("visible");
    window.clearTimeout(state.toastTimer);
    state.toastTimer = window.setTimeout(() => {
      toast.classList.remove("visible");
    }, 1500);
  }

  function renderLiveTimerState(data) {
    const enabled = Boolean(data?.enabled);
    const visualsEnabled = Boolean(data?.visualsEnabled);
    const timer = computeTimer(data || {});
    const timerHero = $("acgTimerHero");
    const timerValue = $("acgTimerValue");
    const phaseLabel = $("acgPhaseLabel");
    const timeDrainOverlay = $("acgTimeDrainOverlay");
    const timeDrainTimer = $("acgTimeDrainTimer");
    const animationSignature = [
      String(timer.phase || "idle"),
      Number(data?.phaseStartEpochMs || 0),
      Number(data?.phaseLimitMs || 0),
      Number(Boolean(timer.paused)),
      Number(Boolean(timer.free)),
      Number(Boolean(timer.untimed)),
    ].join("|");
    const deadlineEpochMs = Number(data?.phaseStartEpochMs || 0) + Number(data?.phaseLimitMs || 0);
    if (!timerHero || !timerValue || !phaseLabel) {
      return;
    }
    timerHero.classList.toggle("untimed", Boolean(timer.untimed));

    if (!enabled) {
      setText("acgTimer", "Off");
      setText(phaseLabel, "Off");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", "#8c96ac");
      syncTimerRingWebgl(timerHero, timer, "#8c96ac", 1, false, animationSignature, deadlineEpochMs);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (!visualsEnabled) {
      setText("acgTimer", "Vibration only");
      setText(phaseLabel, "Vibration");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", "#8c96ac");
      syncTimerRingWebgl(timerHero, timer, "#8c96ac", 1, false, animationSignature, deadlineEpochMs);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.phase === "idle") {
      const timerRamp = getTimerRampColors(data);
      setText("acgTimer", "Ready");
      setText(phaseLabel, "Ready");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", timerRamp.idle);
      syncTimerRingWebgl(timerHero, timer, timerRamp.idle, 1, false, animationSignature, deadlineEpochMs);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.untimed) {
      const timerRamp = getTimerRampColors(data);
      setText("acgTimer", "Untimed");
      setText(phaseLabel, timer.phase === "answer" ? "Answer" : "Question");
      setText(timerValue, "UNTIMED");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", timerRamp.idle);
      syncTimerRingWebgl(timerHero, timer, timerRamp.idle, 1, false, animationSignature, deadlineEpochMs);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.free) {
      const timerRamp = getTimerRampColors(data);
      setText("acgTimer", "First card free");
      setText(phaseLabel, timer.phase === "answer" ? "Answer" : "Question");
      setText(timerValue, "FREE");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", timerRamp.free);
      syncTimerRingWebgl(timerHero, timer, timerRamp.free, 1, false, animationSignature, deadlineEpochMs);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else {
      const timerRamp = getTimerRampColors(data);
      const ratio = timer.total ? clamp(timer.remaining / timer.total, 0, 1) : 0;
      const danger = ratio <= 0.3;
      const blendTarget = ratio > 0.5 ? timerRamp.yellow : timerRamp.red;
      const blendStart = ratio > 0.5 ? timerRamp.green : timerRamp.yellow;
      const localT = ratio > 0.5 ? (1 - ratio) / 0.5 : (0.5 - ratio) / 0.5;
      const color = blendRgb(blendStart, blendTarget, clamp(localT, 0, 1));
      setText("acgTimer", timer.paused ? `Paused ${timer.secondsText}s` : `${timer.phase} ${timer.secondsText}s`);
      setText(phaseLabel, timer.paused ? "Paused" : timer.phase);
      setText(timerValue, timer.secondsText);
      setStyleProperty(timerHero, "--timer-progress", `${ratio}turn`);
      setStyleProperty(timerHero, "--timer-color", color);
      syncTimerRingWebgl(
        timerHero,
        timer,
        color,
        ratio,
        !timer.paused && timer.remaining > 0,
        animationSignature,
        deadlineEpochMs,
      );
      timerHero.classList.toggle("danger", danger);
      timerValue.classList.toggle("danger", danger);
    }

    if (timeDrainOverlay && timeDrainTimer) {
      const activeTimeDrain = enabled
        && visualsEnabled
        && !Boolean(data?.timeDrainTimerOverrideEnabled)
        && Number(data?.timeDrainFlag || 0) > 0
        && Number(data?.currentCardFlag || 0) === Number(data?.timeDrainFlag || 0)
        && timer.phase === "question";
      timeDrainOverlay.classList.toggle("visible", activeTimeDrain);
      setText(timeDrainTimer, timer.untimed ? "UNTIMED" : timer.free ? "FREE" : timer.phase === "idle" ? "--" : timer.secondsText);
    }
  }

  function render(data) {
    ensureMounted();
    const sidebar = $("speed-streak-sidebar");
    if (!sidebar) {
      return;
    }
    sidebar.classList.remove("hidden");
    state.data = data;
    const enabled = Boolean(data.enabled);
    const displayMode = String(data.displayMode || "inline");
    const visualMode = getVisualMode(data);
    const sphereMode = getSphereMode(data);
    const renderMode = getRenderMode(data);
    const lightweightRows = visualMode === "lightweight_rows";
    const crystalReactor = visualMode === "crystal_reactor";
    const visualsEnabled = Boolean(data.visualsEnabled);
    const orbitAnimationEnabled = Boolean(data.orbitAnimationEnabled ?? true);
    const sidebarCollapsed = displayMode !== "compatibility" && Boolean(data.sidebarCollapsed);
    const appearanceMode = String(data.appearanceMode || "midnight");
    const sidebarBackground = String(data.sidebarBackground || "").trim();

    const colors = Array.isArray(data.satelliteColors) ? data.satelliteColors : [];
    const core = $("acgCore");
    const offOverlay = $("acgOffOverlay");
    const enabledToggle = $("acgEnabledToggle");
    const collapseTab = $("acgCollapseTab");
    const collapseTabText = $("acgCollapseTabText");
    const score = Number(data.score || 0);
    const multiplier = Number(data.streakMultiplier || 1);
    const streak = Number(data.streak || 0);
    const field = $("acgField");
    const coreWrap = document.querySelector(".acg-core-wrap");

    setText("acgStreak", String(streak));
    setText("acgScore", score.toLocaleString());
    setText("acgMultiplier", `x${multiplier.toFixed(2)} multiplier`);
    sidebar.classList.toggle("inline-mode", displayMode !== "compatibility");
    sidebar.classList.toggle("compatibility-mode", displayMode === "compatibility");
    sidebar.classList.toggle("off", !enabled);
    sidebar.classList.toggle("visuals-disabled", enabled && !visualsEnabled);
    sidebar.classList.toggle("orbit-static", enabled && visualsEnabled && visualMode === "sphere" && !orbitAnimationEnabled);
    sidebar.classList.toggle("lightweight-rows", enabled && visualsEnabled && lightweightRows);
    sidebar.classList.toggle("crystal-reactor", enabled && visualsEnabled && crystalReactor);
    sidebar.classList.toggle("sphere-consolidate", enabled && visualsEnabled && visualMode === "sphere" && sphereMode === "consolidate");
    sidebar.classList.toggle("ultra-low-resource", enabled && visualsEnabled && visualMode === "sphere" && renderMode === "ultra_low_resource");
    sidebar.classList.toggle("webgl-orbit", enabled && visualsEnabled && visualMode === "sphere" && renderMode === "webgl");
    sidebar.classList.toggle("collapsed", sidebarCollapsed);
    sidebar.dataset.displayMode = displayMode;
    sidebar.dataset.visualMode = visualMode;
    sidebar.dataset.sphereMode = sphereMode;
    sidebar.dataset.renderMode = renderMode;
    sidebar.dataset.theme = appearanceMode;
    applyCustomColors(sidebar, data.customColors || {}, appearanceMode);
    if (sidebarBackground !== state.lastSidebarBackground) {
      state.lastSidebarBackground = sidebarBackground;
      if (document.documentElement) {
        setBackgroundStyle(document.documentElement, sidebarBackground || "transparent");
      }
      if (document.body) {
        setBackgroundStyle(document.body, sidebarBackground || "transparent");
      }
    }

    if (enabledToggle) {
      enabledToggle.classList.toggle("off", !enabled);
      enabledToggle.setAttribute("aria-pressed", enabled ? "true" : "false");
    }
    syncQuickControls(data);
    if (collapseTab) {
      const collapseLabel = sidebarCollapsed ? "Show Speed Streak" : "Hide Speed Streak";
      collapseTab.setAttribute("title", collapseLabel);
      collapseTab.setAttribute("aria-label", collapseLabel);
    }
    if (collapseTabText) {
      setText(collapseTabText, sidebarCollapsed ? "›" : "‹");
    }

    if (coreWrap && orbitAnimationEnabled && visualMode === "sphere") {
      const coreSize = clamp(58 + (streak * 2.8), 58, 142);
      const nextCoreSize = `${coreSize}px`;
      if (nextCoreSize !== state.lastCoreSize) {
        state.lastCoreSize = nextCoreSize;
        setStyleProperty(coreWrap, "--core-size", nextCoreSize);
      }
    } else if (coreWrap) {
      if (state.lastCoreSize !== "auto") {
        state.lastCoreSize = "auto";
        setStyleProperty(coreWrap, "--core-size", "auto");
      }
    }
    if (field && orbitAnimationEnabled && visualMode === "sphere") {
      const nextFilter = `saturate(${clamp(1 + (streak * 0.04), 1, 2.4)}) brightness(${clamp(1 + (streak * 0.015), 1, 1.45)})`;
      if (nextFilter !== state.lastFilterValue) {
        state.lastFilterValue = nextFilter;
        field.style.filter = nextFilter;
      }
    } else if (field) {
      if (state.lastFilterValue !== "none") {
        state.lastFilterValue = "none";
        field.style.filter = "none";
      }
    }
    state.appearanceModeDraft = appearanceMode;
    syncAppearanceButtons();
    syncShortcutCopy(data);
    renderLiveTimerState(data);
    renderGameplayEconomy(data);

    core.classList.toggle("paused", Boolean(data.paused));
    core.classList.toggle("failed", Boolean(data.failureVisualActive));
    if (!state.settingsOpen) {
      syncSettingsFields(data);
    }
    const dim = $("acgDim");
    const pauseOverlay = $("acgPauseOverlay");
    if (dim) {
      dim.classList.toggle("visible", Boolean(data.paused) || state.settingsOpen || !enabled);
    }
    if (pauseOverlay) {
      pauseOverlay.classList.toggle("visible", Boolean(data.paused) && !state.settingsOpen);
    }
    renderPauseOverview(data);
    if (offOverlay) {
      offOverlay.classList.toggle("visible", !enabled && !state.settingsOpen);
    }
    handleStateEffects(data);
    if (enabled && visualsEnabled && !sidebarCollapsed && lightweightRows) {
      stopCrystalReactor();
      clearOrbitScene();
      renderLightweightRows(data);
    } else if (enabled && visualsEnabled && !sidebarCollapsed && crystalReactor) {
      clearOrbitScene();
      clearRowsScene();
      renderCrystalReactor(data);
    } else if (enabled && visualsEnabled && orbitAnimationEnabled && !sidebarCollapsed && visualMode === "sphere") {
      stopCrystalReactor();
      clearRowsScene();
      moveSharedWebglCanvas("sphere");
      renderRings(colors, data);
    } else {
      stopCrystalReactor();
      clearOrbitScene();
      clearRowsScene();
    }
    state.prevColors = colors.slice();
    state.prevStreak = streak;
  }

  function renderGameplayEconomy(data) {
    const timeBoostMode = String(data?.gameplayMode || "legacy") === "time_boost";
    const legacy = $("acgLegacyEconomy");
    const boost = $("acgBoostEconomy");
    const button = $("acgBoostButton");
    const progressFill = $("acgBoostProgressFill");
    const focusToggles = $("acgFocusModeToggles");
    const noPauseToggle = $("acgNoPauseToggle");
    const noUndoToggle = $("acgNoUndoToggle");
    if (legacy) legacy.classList.toggle("hidden", timeBoostMode);
    if (boost) boost.classList.toggle("visible", timeBoostMode);
    if (!timeBoostMode) return;

    const charges = Math.max(0, Number(data?.boostCharges || 0));
    const maxCharges = Math.max(1, Number(data?.maxBoostCharges || 1));
    const progress = Math.max(0, Number(data?.boostChargeProgress || 0));
    const required = Math.max(1, Number(data?.cardsPerBoostCharge || 1));
    const boostSeconds = Math.max(0.5, Number(data?.boostSeconds || 5));
    renderBoostChargeBank(charges, maxCharges);
    setText("acgBoostProgressText", charges >= maxCharges ? "Charge bank full" : `Next charge ${progress} / ${required}`);
    if (progressFill) {
      setStyleProperty(progressFill, "width", `${charges >= maxCharges ? 100 : clamp((progress / required) * 100, 0, 100)}%`);
    }
    if (button) {
      const shortcut = getBoostShortcut(data);
      button.setAttribute("title", `Edit Time Boost shortcut (currently ${shortcut}); keyboard Boost adds ${boostSeconds}s`);
      button.setAttribute("aria-label", `Edit Time Boost shortcut. Current key ${shortcut}`);
    }
    const showInactive = Boolean(data?.showFocusModeToggles ?? true);
    syncFocusRuleToggle(noPauseToggle, Boolean(data?.noPauseMode), showInactive, "No Pause mode");
    syncFocusRuleToggle(noUndoToggle, Boolean(data?.noUndoMode), showInactive, "No Undo mode");
    focusToggles?.classList.toggle(
      "hidden",
      Boolean(noPauseToggle?.classList.contains("hidden")) && Boolean(noUndoToggle?.classList.contains("hidden")),
    );
  }

  function syncFocusRuleToggle(button, active, showInactive, label) {
    if (!button) return;
    button.classList.toggle("active", active);
    button.classList.toggle("hidden", !active && !showInactive);
    button.setAttribute("aria-pressed", active ? "true" : "false");
    button.setAttribute("title", `${label} is ${active ? "on" : "off"}. Click to turn it ${active ? "off" : "on"}.`);
  }

  function renderBoostChargeBank(charges, maxCharges) {
    const bank = $("acgBoostCharges");
    if (!bank) return;
    const availableWidth = Math.max(0, bank.parentElement?.clientWidth || bank.clientWidth || 0);
    const slotsThatFit = Math.max(1, Math.floor(availableWidth / 24));
    const useFraction = maxCharges > slotsThatFit;
    const nextSignature = `${charges}|${maxCharges}|${Number(useFraction)}`;
    if (nextSignature === state.lastBoostBankSignature) return;
    state.lastBoostBankSignature = nextSignature;
    bank.replaceChildren();
    bank.setAttribute("aria-label", `${charges} of ${maxCharges} Time Boost charges available`);
    bank.setAttribute("title", `${charges} / ${maxCharges} Time Boost charges`);
    if (useFraction) {
      bank.classList.add("fraction");
      bank.textContent = `⚡ ${charges} / ${maxCharges}`;
      return;
    }
    bank.classList.remove("fraction");
    for (let index = 0; index < maxCharges; index += 1) {
      const slot = document.createElement("span");
      slot.className = `acg-boost-charge-slot ${index < charges ? "filled" : "empty"}`;
      slot.textContent = "⚡";
      slot.setAttribute("aria-hidden", "true");
      bank.appendChild(slot);
    }
  }

  function clearOrbitScene() {
    const ringsNode = $("acgRings");
    const satellitesNode = $("acgSatellites");
    if (!state.lastColorsSignature && state.lastRingCount === 0) {
      return;
    }
    if (ringsNode) {
      ringsNode.innerHTML = "";
    }
    if (satellitesNode) {
      satellitesNode.innerHTML = "";
    }
    stopWebglOrbit();
    state.lastColorsSignature = "";
    state.lastRingCount = 0;
    state.lastSceneScale = 1;
  }

  function blendRgb(a, b, t) {
    const r = Math.round(a[0] + ((b[0] - a[0]) * t));
    const g = Math.round(a[1] + ((b[1] - a[1]) * t));
    const bl = Math.round(a[2] + ((b[2] - a[2]) * t));
    return `rgb(${r}, ${g}, ${bl})`;
  }

  function animationLoop() {
    stopTimerLoop();
  }

  window.SpeedStreak = {
    receiveState(nextState) {
      ensureMounted();
      render(nextState);
      syncTimerLoop();
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureMounted, { once: true });
  } else {
    ensureMounted();
  }
})();
