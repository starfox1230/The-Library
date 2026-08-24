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
    crystalColorModeDraft: "ice",
    useCustomTimerColorsDraft: false,
    timerColorLevelDraft: 0,
    presetsOpen: false,
    presetMenuOpenId: "",
    presetCloseTimer: 0,
    economyCloseTimer: 0,
    timerContextCloseTimer: 0,
    visualSelectorChoice: "sphere",
    sidebarResizeObserver: null,
    visualFieldResizeObserver: null,
    visualResizeFrame: 0,
    lastVisualFieldWidth: 0,
    lastVisualFieldHeight: 0,
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
    singularityWebgl: null,
    crystalWebgl: null,
    timerWebgl: null,
    fusionDemolitionTimer: 0,
    fusionDemolitionActive: false,
    fusionCenterResetTimer: 0,
  };

  const PAUSE_OVERVIEW_STORAGE_KEY = "speed-streak-pause-overview-v1";

  const DEFAULT_CUSTOM_COLORS = {
    core: "#566ed4",
    crystal: "#566ed4",
    red: "#c34f69",
    yellow: "#c69430",
    green: "#2b9d73",
    blue: "#4a74dd",
  };

  const THEME_CUSTOM_COLOR_DEFAULTS = {
    classic: { core: "#5b6fcf", crystal: "#5b6fcf", red: "#c9546d", yellow: "#c89a38", green: "#2ea36f", blue: "#4b7de2" },
    cardmatch: { core: "#84a6c7", crystal: "#84a6c7", red: "#b26a6a", yellow: "#b786ad", green: "#419c5f", blue: "#4d8d8d" },
    card: { core: "#84a6c7", crystal: "#84a6c7", red: "#b26a6a", yellow: "#b786ad", green: "#419c5f", blue: "#4d8d8d" },
    graphite: { core: "#6982b8", crystal: "#6982b8", red: "#b65b70", yellow: "#b48c42", green: "#3d9b79", blue: "#557fd6" },
    midnight: { core: "#566ed4", crystal: "#566ed4", red: "#c34f69", yellow: "#c69430", green: "#2b9d73", blue: "#4a74dd" },
    forest: { core: "#4f8f9c", crystal: "#4f8f9c", red: "#b45a62", yellow: "#b89a43", green: "#2d9a66", blue: "#3d73b8" },
    ember: { core: "#c66a4b", crystal: "#c66a4b", red: "#cf5664", yellow: "#c98a33", green: "#4e9a72", blue: "#4d74c9" },
    violet: { core: "#7761c5", crystal: "#7761c5", red: "#c15a7f", yellow: "#bc8f3d", green: "#4b9c82", blue: "#5b7ed6" },
    ocean: { core: "#4d8fc2", crystal: "#4d8fc2", red: "#bd5c6c", yellow: "#c39932", green: "#2f9a82", blue: "#3e79cc" },
  };

  const RATING_COLOR_FIELDS = [
    { key: "red", label: "Again", description: "Again satellites plus failure and timeout accents." },
    { key: "yellow", label: "Hard", description: "Hard satellites and Hard crystals in Rating Colors mode." },
    { key: "green", label: "Good", description: "Good satellites and Good crystals in Rating Colors mode." },
    { key: "blue", label: "Easy", description: "Easy satellites and Easy crystals in Rating Colors mode." },
  ];

  const VISUAL_COLOR_FIELDS = [
    { key: "core", label: "Orb / Singularity Core", description: "The Sphere center and Singularity event horizon, corona, grid energy, and sparks." },
    { key: "crystal", label: "Crystal: Single Color", description: "The complete crystal formation in Single Crystal Color mode." },
  ];

  const COLOR_FIELDS = [...RATING_COLOR_FIELDS, ...VISUAL_COLOR_FIELDS];

  function colorRowsMarkup(fields) {
    return fields.map((field) => `
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
    `).join("");
  }

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
    singularity: `
      <svg class="acg-visual-mode-icon acg-singularity-mode-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <g transform="rotate(-11 16 16)">
          <ellipse cx="16" cy="16" rx="12.4" ry="5.1" fill="currentColor" fill-opacity=".10" stroke-opacity=".42" stroke-width="1.05"></ellipse>
          <ellipse cx="16" cy="16" rx="10.3" ry="3.35" stroke-opacity=".68" stroke-width="1.25"></ellipse>
        </g>
        <circle cx="16" cy="16" r="6.15" fill="#03050b" stroke="currentColor" stroke-opacity=".88" stroke-width="1.45"></circle>
        <circle cx="16" cy="16" r="4.75" fill="#010207" stroke="none"></circle>
        <path d="M4.1 18.35c5.15 3.35 18.7 3.12 23.8-1.28" stroke-width="1.75"></path>
        <path d="M7.4 20.15c4.65 1.75 13.2 1.55 17.25-.85" stroke="rgba(255,255,255,.72)" stroke-width=".75"></path>
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
      <svg class="acg-visual-mode-icon acg-brick-mode-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1" aria-hidden="true" focusable="false">
        <g fill="currentColor" fill-opacity=".16">
          <rect x="3.25" y="4.5" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="9.95" y="4.5" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="16.6" y="4.5" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="23.3" y="4.5" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="3.25" y="10.7" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="9.95" y="10.7" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="16.6" y="10.7" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="23.3" y="10.7" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="3.25" y="16.9" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="9.95" y="16.9" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="16.6" y="16.9" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="23.3" y="16.9" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="3.25" y="23.1" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="9.95" y="23.1" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="16.6" y="23.1" width="5.45" height="4.45" rx=".9"></rect>
          <rect x="23.3" y="23.1" width="5.45" height="4.45" rx=".9"></rect>
        </g>
      </svg>
    `,
    number_only: `
      <svg class="acg-visual-mode-icon acg-number-only-icon" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="2.35" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
        <path d="M12.4 5.5 10.2 26.5M21.8 5.5l-2.2 21M6 12.4h20M5.2 20.1h20"></path>
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
          <button id="acgWindowPresetsToggle" class="acg-action acg-foreground-action acg-icon-toggle acg-window-presets-toggle" type="button" title="External window presets" aria-label="External window presets">${WINDOW_PRESET_ICON}</button>
          <div id="acgWindowPresetsPanel" class="acg-window-presets-panel" aria-label="External window presets">
            <div class="acg-window-presets-head">
              <span>External window presets</span>
              <button id="acgWindowPresetSave" class="acg-action acg-icon-toggle acg-window-preset-add" type="button" title="Save current window positions" aria-label="Save current window positions">+</button>
            </div>
            <div class="acg-window-presets-copy">Save and restore the positions of Anki and the external Speed Streak window.</div>
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
          <div id="acgTimerContextZone" class="acg-timer-context-zone">
            <div id="acgTimerHero" class="acg-timer-hero" tabindex="0" role="button" aria-label="Timer options" aria-expanded="false">
              <canvas id="acgTimerCanvas" class="acg-timer-canvas" aria-hidden="true"></canvas>
              <span id="acgBoostOverflowBadge" class="acg-timer-overflow-badge" aria-hidden="true"></span>
              <div class="acg-timer-inner">
                <div id="acgPhaseLabel" class="acg-phase-label">Ready</div>
                <div id="acgTimerValue" class="acg-timer-value">--</div>
              </div>
            </div>
            <div id="acgTimerContext" class="acg-timer-context" role="menu">
              <button id="acgAdjustTimers" type="button" role="menuitem">Adjust timers</button>
            </div>
          </div>
          <div id="acgLegacyEconomy" class="acg-legacy-economy acg-economy-hover-zone" tabindex="0">
            <div id="acgScore" class="acg-score">0</div>
            <div id="acgMultiplier" class="acg-multiplier">x1.00 multiplier</div>
            <div class="acg-legacy-hover-controls">
              <button id="acgSwitchToTimeBoost" class="acg-gameplay-mode-switch" type="button">Switch to Time Boost</button>
            </div>
          </div>
          <div id="acgBoostEconomy" class="acg-boost-economy" aria-live="polite">
            <div id="acgBoostHoverZone" class="acg-boost-hover-zone" tabindex="0" aria-label="Boost bank and controls" title="Click the Boost bank to edit Time Boost settings">
              <div class="acg-boost-bank-row">
                <div id="acgBoostCharges" class="acg-boost-charges" aria-label="1 of 3 Boosts"></div>
              </div>
              <div class="acg-boost-progress" aria-hidden="true"><span id="acgBoostProgressFill"></span></div>
              <div id="acgBoostProgressText" class="acg-boost-progress-text">Next Boost 0 / 5</div>
              <div class="acg-boost-hover-controls">
                <div class="acg-boost-hover-control-row">
                  <div id="acgFocusModeToggles" class="acg-focus-mode-toggles" role="group" aria-label="Focus rules">
                    <button id="acgNoPauseToggle" class="acg-focus-mode-toggle" type="button" aria-pressed="false">NO PAUSE</button>
                    <button id="acgNoUndoToggle" class="acg-focus-mode-toggle" type="button" aria-pressed="false">NO UNDO</button>
                  </div>
                  <button id="acgBoostButton" class="acg-boost-key" type="button" aria-label="Edit Time Boost shortcut">
                    <kbd id="acgBoostShortcutLabel">C</kbd>
                  </button>
                </div>
                <button id="acgSwitchToLegacy" class="acg-gameplay-mode-switch" type="button">Revert to Legacy Points</button>
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
            <div id="acgSingularityScene" class="acg-singularity-scene">
              <canvas id="acgSingularityCanvas" class="acg-singularity-canvas" aria-hidden="true"></canvas>
              <div class="acg-singularity-readout">
                <div id="acgSingularityStreak" class="acg-singularity-streak">0</div>
              </div>
            </div>
          </div>
        </div>
        <div class="acg-bottom">
          <div id="acgVisualsDisabledCopy" class="acg-visuals-disabled-copy">Vibration-only mode is active.</div>
          <div id="acgTimer" class="acg-timer">Ready</div>
          <div class="acg-bottom-bar">
            <div id="acgVisualSelector" class="acg-visual-selector" aria-label="Visual options">
              <button id="acgVisualSelectorToggle" class="acg-action acg-icon-toggle acg-visual-selector-toggle" type="button" aria-expanded="false" title="Visual options">
                <span id="acgVisualSelectorCurrentIcon">${VISUAL_MODE_ICONS.sphere}</span>
              </button>
              <div class="acg-visual-selector-panel">
                <div class="acg-visual-choice-list" role="group" aria-label="Visual style">
                  <button class="acg-visual-choice" type="button" data-visual-choice="sphere" title="Satellite Orbit" aria-label="Satellite Orbit">
                    ${VISUAL_MODE_ICONS.sphere}
                  </button>
                  <button class="acg-visual-choice" type="button" data-visual-choice="singularity" title="Singularity" aria-label="Singularity gravity core">
                    ${VISUAL_MODE_ICONS.singularity}
                  </button>
                  <button class="acg-visual-choice" type="button" data-visual-choice="crystal_reactor" title="Crystal Reactor" aria-label="Crystal Reactor">
                    ${VISUAL_MODE_ICONS.crystal_reactor}
                  </button>
                  <button class="acg-visual-choice" type="button" data-visual-choice="lightweight_rows" title="Brick Streak" aria-label="Brick Streak">
                    ${VISUAL_MODE_ICONS.lightweight_rows}
                  </button>
                  <button class="acg-visual-choice acg-number-only-choice" type="button" data-visual-choice="number_only" title="Number only" aria-label="Number only">
                    ${VISUAL_MODE_ICONS.number_only}
                  </button>
                </div>
                <div id="acgVisualResourcePanel" class="acg-visual-resource-panel">
                  <div class="acg-visual-resource-heading">
                    <span id="acgVisualResourceName">Satellite style</span>
                    <strong id="acgVisualResourceValue">Full</strong>
                  </div>
                  <input id="acgVisualResourceSlider" class="acg-visual-resource-slider" type="range" min="0" max="2" step="1" value="2" aria-label="Visual style" />
                  <div id="acgVisualResourceTicks" class="acg-visual-resource-ticks"></div>
                  <p id="acgVisualResourceDescription" class="acg-visual-resource-description"></p>
                  <button id="acgVisualColorShortcut" class="acg-visual-color-shortcut hidden" type="button">Customize Colors</button>
                </div>
              </div>
            </div>
            <div class="acg-bottom-stack acg-bottom-right">
              <button id="acgHapticsToggle" class="acg-action acg-icon-toggle" type="button" title="Haptics" aria-label="Haptics">
                <!-- Controller geometry: Lucide gamepad-2 (ISC); vibration marks added for this control. -->
                <svg class="acg-haptics-icon" viewBox="-3 0 30 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                  <line x1="6" x2="10" y1="11" y2="11"></line>
                  <line x1="8" x2="8" y1="9" y2="13"></line>
                  <line x1="15" x2="15.01" y1="12" y2="12"></line>
                  <line x1="18" x2="18.01" y1="10" y2="10"></line>
                  <path d="M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z"></path>
                  <path d="M-.3 9.2c-.9 1.45-.9 4.15 0 5.6"></path>
                  <path d="M24.3 9.2c.9 1.45.9 4.15 0 5.6"></path>
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
                <button id="acgColorCustomizerButton" class="acg-action" type="button">Visual Colors</button>
              </div>
            </div>
            <div id="acgColorPanel" class="acg-color-panel hidden">
              <div class="acg-color-panel-head">
                <div>
                  <div class="acg-modal-title">Visual Colors</div>
                  <div class="acg-panel-copy">Rating colors are shared by satellites and Rating Colors crystals. Sphere and Crystal-specific colors are separate.</div>
                </div>
                <button id="acgCloseColorPanel" class="acg-close" type="button">Close</button>
              </div>
              <div class="acg-color-section">
                <div class="acg-color-section-title">Shared Rating Colors</div>
                <div class="acg-panel-copy">Sphere satellites always use these. Crystals use them only in Rating Colors mode.</div>
                <div class="acg-color-grid">${colorRowsMarkup(RATING_COLOR_FIELDS)}</div>
              </div>
              <div class="acg-color-section">
                <div class="acg-color-section-title">Visual-Specific Colors</div>
                <div class="acg-panel-copy">The Sphere center and a single-color Crystal formation have independent controls.</div>
                <div class="acg-color-grid">${colorRowsMarkup([VISUAL_COLOR_FIELDS[0]])}</div>
                <label class="acg-color-mode-row" for="acgCrystalColorMode">
                  <span class="acg-color-copy">
                    <span class="acg-form-label">Crystal Color Source</span>
                    <span class="acg-switch-copy">Ice uses its built-in sheen. Rating Colors uses the shared answer palette. Single Crystal Color uses the Crystal swatch.</span>
                  </span>
                  <select id="acgCrystalColorMode" class="acg-select">
                    <option value="ice">Ice</option>
                    <option value="answer">Rating Colors</option>
                    <option value="core">Single Crystal Color</option>
                  </select>
                </label>
                <div id="acgCrystalSingleColorRow" class="acg-color-grid">${colorRowsMarkup([VISUAL_COLOR_FIELDS[1]])}</div>
              </div>
              <div class="acg-color-section-title">Timer Colors (Optional)</div>
              <label class="acg-switch-row" for="acgTimerColorMode">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Use Shared Rating Colors For Timers</span>
                  <span class="acg-switch-copy">Fade both timers through the shared Good, Hard, and Again colors instead of the default warning ramp.</span>
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
                Every time you rate a card on time, your streak goes up by one and a new satellite is added to the orbit. Again adds a red satellite, Hard adds yellow, Good adds green, and Easy adds blue. Legacy Points grows the score with a streak multiplier. Time Boost replaces those points with a capped Boost bank; complete the configured number of cards to earn a Boost, then press the displayed keyboard shortcut before time expires to add time without losing the streak. Hover over or focus the Boost bank to reveal the directly toggleable No Pause/No Undo pills and the shortcut keycap; clicking the keycap opens its setting.
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
        const choice = String(button.getAttribute("data-visual-choice") || "sphere");
        const level = choice === getVisualMode(state.data || {})
          ? currentVisualResourceLevel(state.data || {}, choice)
          : defaultVisualResourceLevel(choice);
        state.visualSelectorChoice = choice;
        applyVisualResourceLevel(choice, level);
        renderVisualResourceSelector(state.data || {}, level);
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
        scheduleEconomyHoverClose();
        scheduleWindowPresetClose();
        scheduleTimerContextClose();
      });
    }

    const visualField = document.getElementById("acgField");
    state.visualFieldResizeObserver?.disconnect?.();
    if (visualField && typeof ResizeObserver === "function") {
      state.visualFieldResizeObserver = new ResizeObserver((entries) => {
        const rect = entries?.[0]?.contentRect;
        const width = Math.max(0, Number(rect?.width || 0));
        const height = Math.max(0, Number(rect?.height || 0));
        if (
          Math.abs(width - state.lastVisualFieldWidth) < 0.5
          && Math.abs(height - state.lastVisualFieldHeight) < 0.5
        ) {
          return;
        }
        state.lastVisualFieldWidth = width;
        state.lastVisualFieldHeight = height;
        scheduleVisualViewportRedraw();
      });
      state.visualFieldResizeObserver.observe(visualField);
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

    const timerContextZone = document.getElementById("acgTimerContextZone");
    const timerHeroControl = document.getElementById("acgTimerHero");
    const adjustTimers = document.getElementById("acgAdjustTimers");
    if (timerContextZone && timerHeroControl) {
      const showTimerContext = (event) => {
        if (event?.target?.closest?.("#acgAdjustTimers")) return;
        openTimerContext();
      };
      timerHeroControl.addEventListener("click", showTimerContext);
      timerHeroControl.addEventListener("keydown", (event) => {
        if (!["Enter", " "].includes(event.key)) return;
        event.preventDefault();
        showTimerContext(event);
      });
      timerContextZone.addEventListener("pointerenter", cancelTimerContextClose);
      timerContextZone.addEventListener("pointerleave", scheduleTimerContextClose);
      document.addEventListener("pointermove", (event) => {
        if (!timerContextZone.classList.contains("open")) return;
        if (pointerIsNearTimerContext(event.clientX, event.clientY)) {
          cancelTimerContextClose();
        } else if (!state.timerContextCloseTimer) {
          scheduleTimerContextClose();
        }
      });
    }
    if (adjustTimers) {
      adjustTimers.addEventListener("click", (event) => {
        event.stopPropagation();
        closeTimerContext();
        if (typeof pycmd === "function") pycmd("speed-streak:open-settings:timers");
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

    const bindGameplayModeSwitch = (id, mode) => {
      const button = document.getElementById(id);
      if (!button) return;
      button.addEventListener("click", (event) => {
        event.stopPropagation();
        if (typeof pycmd === "function") {
          pycmd(`speed-streak:set-gameplay-mode:${mode}`);
        }
        if (event.detail > 0) button.blur();
        scheduleEconomyHoverClose();
      });
    };
    bindGameplayModeSwitch("acgSwitchToLegacy", "legacy");
    bindGameplayModeSwitch("acgSwitchToTimeBoost", "time_boost");

    const visualColorShortcut = document.getElementById("acgVisualColorShortcut");
    if (visualColorShortcut) {
      visualColorShortcut.addEventListener("click", (event) => {
        event.stopPropagation();
        const visual = state.visualSelectorChoice || getVisualMode(state.data || {});
        if (typeof pycmd === "function") {
          pycmd(`speed-streak:open-settings:visual-colors:${visual}`);
        }
        visualSelector?.classList.remove("open");
        visualSelectorToggle?.setAttribute("aria-expanded", "false");
        if (event.detail > 0) visualColorShortcut.blur();
      });
    }

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
    const legacyHoverZone = document.getElementById("acgLegacyEconomy");
    [boostHoverZone, legacyHoverZone].filter(Boolean).forEach((root) => {
      root.addEventListener("pointerenter", () => openEconomyHover(root));
      root.addEventListener("pointerleave", scheduleEconomyHoverClose);
      root.addEventListener("focusin", () => openEconomyHover(root));
    });
    document.addEventListener("pointermove", (event) => {
      const openRoot = document.querySelector(".acg-economy-hover-zone.hover-open, .acg-boost-hover-zone.hover-open");
      if (!openRoot) return;
      if (distanceFromPointToRect(event.clientX, event.clientY, openRoot.getBoundingClientRect()) <= 42) {
        cancelEconomyHoverClose();
      } else if (!state.economyCloseTimer) {
        scheduleEconomyHoverClose();
      }
    });
    window.addEventListener("resize", () => {
      renderGameplayEconomy(state.data || {});
      scheduleVisualViewportRedraw();
    });

    const windowPresetsRoot = document.getElementById("acgWindowPresets");
    if (windowPresetsRoot) {
      windowPresetsRoot.addEventListener("pointerenter", () => {
        cancelWindowPresetClose();
        openWindowPositionPresets();
      });
      windowPresetsRoot.addEventListener("pointerleave", scheduleWindowPresetClose);
      document.addEventListener("pointermove", (event) => {
        if (!state.presetsOpen) return;
        if (pointerIsNearWindowPresets(event.clientX, event.clientY)) {
          cancelWindowPresetClose();
        } else if (!state.presetCloseTimer) {
          scheduleWindowPresetClose();
        }
      });
    }

    document.documentElement?.addEventListener("mouseleave", () => {
      scheduleEconomyHoverClose();
      scheduleWindowPresetClose();
    });
    window.addEventListener("blur", () => {
      closeEconomyHover();
      closeWindowPositionPresets();
      closeTimerContext();
    });

    const windowPresetsToggle = document.getElementById("acgWindowPresetsToggle");
    if (windowPresetsToggle) {
      windowPresetsToggle.addEventListener("click", (event) => {
        cancelWindowPresetClose();
        state.presetsOpen = !state.presetsOpen;
        state.presetMenuOpenId = "";
        renderWindowPositionPresets(state.data || {});
        if (event.detail > 0) windowPresetsToggle.blur();
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
      colorCustomizerButton.addEventListener("click", () => {
        if (typeof pycmd !== "function") return;
        pycmd(`speed-streak:open-settings:visual-colors:${getVisualMode(state.data || {})}`);
      });
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
          state.data.crystalColorMode = state.crystalColorModeDraft;
        }
        saveSettings({
          customColors: normalized,
          customTimerColors: Boolean(state.useCustomTimerColorsDraft),
          crystalColorMode: state.crystalColorModeDraft,
        });
        closeColorPanel({ preserveDrafts: true });
      });
    }

    const crystalColorMode = document.getElementById("acgCrystalColorMode");
    if (crystalColorMode) {
      crystalColorMode.addEventListener("change", () => {
        state.crystalColorModeDraft = getCrystalColorMode({ crystalColorMode: crystalColorMode.value });
        syncCrystalColorControls();
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
    if (["singularity", "gravity", "gravity_core", "black_hole"].includes(normalized)) {
      return "singularity";
    }
    if (normalized === "crystal_reactor" || normalized === "crystal" || normalized === "reactor") {
      return "crystal_reactor";
    }
    if (normalized === "lightweight_rows" || normalized === "rows") {
      return "lightweight_rows";
    }
    if (["number_only", "number", "number-only", "streak_number"].includes(normalized)) {
      return "number_only";
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
    const normalized = String(data?.sphereMode || "fusion").trim().toLowerCase();
    if (normalized === "classic") return "classic";
    return "fusion";
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

  function isSingularityMode(data) {
    return getVisualMode(data) === "singularity";
  }

  function isCrystalRotationEnabled(data) {
    return Boolean(data?.crystalRotationEnabled ?? true);
  }

  function getCrystalColorMode(data) {
    const normalized = String(data?.crystalColorMode || "ice").trim().toLowerCase();
    if (["answer", "answers", "rating", "ratings"].includes(normalized)) return "answer";
    if (["core", "orb", "single", "monochrome"].includes(normalized)) return "core";
    return "ice";
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
      Number(data?.phaseBaseLimitMs || 0),
      Number(data?.phaseBoostRemainingMs || 0),
      Number(data?.phaseBoostAnchorEpochMs || 0),
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
    const baseLimit = Math.max(0, Number(data.phaseBaseLimitMs || limit));
    const free = Boolean(data.firstCardFree);
    const phasePolicyLimit = phase === "question"
      ? Number(data.timerPolicyQuestionLimitMs ?? -1)
      : Number(data.timerPolicyAnswerLimitMs ?? -1);
    const untimed = String(data.timerPolicyMode || "") === "no_timeout" || phasePolicyLimit === 0;
    const paused = Boolean(data.paused);

    if (phase === "idle" || !Number(data.phaseStartEpochMs || 0)) {
      return { phase, free, untimed: false, paused, remaining: 0, total: 0, baseTotal: 0, secondsText: "0.0" };
    }
    if (free) {
      return { phase, free: true, untimed: false, paused, remaining: 0, total: 0, baseTotal: 0, secondsText: "0.0" };
    }
    if (untimed && !limit) {
      return { phase, free: false, untimed: true, paused: false, remaining: 0, total: 0, baseTotal: 0, secondsText: "0.0" };
    }
    if (!limit) {
      return { phase, free: true, untimed: false, paused, remaining: 0, total: 0, baseTotal: 0, secondsText: "0.0" };
    }
    const remaining = paused
      ? Math.max(0, Number(data.timerDisplayRemainingMs || 0))
      : computeSharedRemainingMs(data);
    const boostAnchor = Math.max(0, Number(data.phaseBoostAnchorEpochMs || 0));
    const storedBoostRemaining = Math.max(0, Number(data.phaseBoostRemainingMs || 0));
    const boostRemaining = paused || !boostAnchor
      ? storedBoostRemaining
      : Math.max(0, storedBoostRemaining - Math.max(0, Date.now() - boostAnchor));
    const baseRemaining = Math.max(0, remaining - boostRemaining);
    const baseProgress = baseLimit > 0 ? clamp(baseRemaining / baseLimit, 0, 1) : 0;
    const boostRatio = baseLimit > 0 ? boostRemaining / baseLimit : 0;
    const boostActive = boostRemaining > 0;
    const totalRatio = baseLimit > 0 ? remaining / baseLimit : 0;
    const overflow = Math.max(0, totalRatio - 1);
    const overflowTurns = Math.floor(overflow);
    const overflowProgress = overflow - overflowTurns;
    if (paused) {
      return { phase, free: false, untimed: false, paused: true, remaining, total: limit, baseTotal: baseLimit, baseRemaining, boostRemaining, boostActive, boostRatio, boostAnchor, storedBoostRemaining, totalRatio, baseProgress, overflowTurns, overflowProgress, secondsText: formatTimerSecondsText(remaining) };
    }
    return {
      phase,
      free: false,
      untimed: false,
      paused: false,
      remaining,
      total: limit,
      baseTotal: baseLimit,
      baseRemaining,
      boostRemaining,
      boostActive,
      boostRatio,
      boostAnchor,
      storedBoostRemaining,
      totalRatio,
      baseProgress,
      overflowTurns,
      overflowProgress,
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
    if (state.data) {
      render(state.data);
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
    const visualsEnabled = !Boolean($("acgVibrationOnlyMode")?.checked || $("acgVibrationOnlyModePerf")?.checked);
    const visualMode = Object.prototype.hasOwnProperty.call(overrides, "visualMode")
      ? String(overrides.visualMode || getVisualMode(state.data || {}))
      : getVisualMode(state.data || {});
    const orbitAnimationEnabled = Object.prototype.hasOwnProperty.call(overrides, "orbitAnimationEnabled")
      ? Boolean(overrides.orbitAnimationEnabled)
      : visualMode !== "number_only";
    const sphereMode = Object.prototype.hasOwnProperty.call(overrides, "sphereMode")
      ? String(overrides.sphereMode || getSphereMode(state.data || {}))
      : getSphereMode(state.data || {});
    const renderMode = Object.prototype.hasOwnProperty.call(overrides, "renderMode")
      ? String(overrides.renderMode || getRenderMode(state.data || {}))
      : getRenderMode(state.data || {});
    const crystalRotationEnabled = Object.prototype.hasOwnProperty.call(overrides, "crystalRotationEnabled")
      ? Boolean(overrides.crystalRotationEnabled)
      : isCrystalRotationEnabled(state.data || {});
    const crystalColorMode = Object.prototype.hasOwnProperty.call(overrides, "crystalColorMode")
      ? getCrystalColorMode({ crystalColorMode: overrides.crystalColorMode })
      : getCrystalColorMode(state.data || {});
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
          crystalColorMode,
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
    if (visualMode === "singularity") {
      return [
        {
          label: "Efficient",
          tick: "Efficient",
          description: "Keeps the gravity core, milestone transformations, and answer reactions at a lower resolution with fewer sparks and a 20 FPS cap.",
        },
        {
          label: "Balanced",
          tick: "Balanced",
          description: "Preserves the warped grid, layered corona, and richer spark streams at 30 FPS. The recommended everyday setting.",
        },
        {
          label: "Full",
          tick: "Full",
          description: "Cinematic gravity well with the densest accretion field, brightest milestone phases, and fluid animation, while retaining strict particle and resolution caps.",
        },
      ];
    }
    if (visualMode === "crystal_reactor") {
      return [
        {
          label: "Still",
          tick: "Still",
          description: "Stops continuous crystal rotation. Idle GPU use is near zero, while answer reactions and milestones still animate.",
        },
        {
          label: "Animated",
          tick: "Animated",
          description: "Continuously rotates the full Crystal Reactor and keeps all live reactions and milestone effects.",
        },
      ];
    }
    if (visualMode === "lightweight_rows") {
      return [
        {
          label: "Ultra light",
          tick: "Fixed",
          description: "Static brick layout with essentially no continuous GPU use while nothing is changing.",
        },
      ];
    }
    if (visualMode === "number_only") {
      return [
        {
          label: "# only",
          tick: "Fixed",
          description: "Shows the streak number without a continuous visual animation.",
        },
      ];
    }
    return [
      {
        label: "Classic",
        tick: "Classic",
        description: "The original Speed Streak satellite layout and sizing.",
      },
      {
        label: "Fusion",
        tick: "Fusion",
        description: "Every 50 cards fuses into a permanent rating-color ring while the current group builds in rows. This is the default.",
      },
    ];
  }

  function highestVisualResourceLevel(visualMode) {
    return visualResourceLevels(visualMode).length - 1;
  }

  function defaultVisualResourceLevel(visualMode) {
    if (visualMode === "singularity") return 1;
    if (visualMode === "sphere") return 1;
    return highestVisualResourceLevel(visualMode);
  }

  function currentVisualResourceLevel(data, visualMode) {
    if (visualMode !== getVisualMode(data)) return highestVisualResourceLevel(visualMode);
    if (visualMode === "crystal_reactor") return isCrystalRotationEnabled(data) ? 1 : 0;
    if (visualMode === "lightweight_rows") return 0;
    if (visualMode === "number_only") return 0;
    if (visualMode === "singularity") {
      if (getRenderMode(data) === "ultra_low_resource") return 0;
      return getRenderMode(data) === "low_resource" ? 1 : 2;
    }
    return getSphereMode(data) === "classic" ? 0 : 1;
  }

  function applyVisualResourceLevel(visualMode, rawLevel) {
    const level = Math.max(0, Math.min(highestVisualResourceLevel(visualMode), Math.round(Number(rawLevel) || 0)));
    if (visualMode === "crystal_reactor") {
      saveSettings({
        visualMode: "crystal_reactor",
        sphereMode: "classic",
        renderMode: "webgl",
        crystalRotationEnabled: level > 0,
        orbitAnimationEnabled: true,
      });
      return;
    }
    if (visualMode === "lightweight_rows") {
      saveSettings({ visualMode: "lightweight_rows", renderMode: "ultra_low_resource", orbitAnimationEnabled: true });
      return;
    }
    if (visualMode === "number_only") {
      saveSettings({ visualMode: "number_only", renderMode: "ultra_low_resource", orbitAnimationEnabled: false });
      return;
    }
    if (visualMode === "singularity") {
      saveSettings({
        visualMode: "singularity",
        sphereMode: "classic",
        renderMode: level === 0 ? "ultra_low_resource" : level === 1 ? "low_resource" : "webgl",
        orbitAnimationEnabled: true,
      });
      return;
    }
    saveSettings({
      visualMode: "sphere",
      sphereMode: level === 0 ? "classic" : "fusion",
      renderMode: "webgl",
      orbitAnimationEnabled: true,
    });
  }

  function renderVisualResourceSelector(data, requestedLevel = null) {
    const actualVisualMode = getVisualMode(data);
    const choice = ["sphere", "singularity", "crystal_reactor", "lightweight_rows", "number_only"].includes(state.visualSelectorChoice)
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
    const colorShortcut = $("acgVisualColorShortcut");
    if (currentIcon) currentIcon.innerHTML = VISUAL_MODE_ICONS[actualVisualMode] || VISUAL_MODE_ICONS.sphere;
    document.querySelectorAll("[data-visual-choice]").forEach((button) => {
      const selected = button.getAttribute("data-visual-choice") === choice;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", selected ? "true" : "false");
    });
    if (name) {
      name.textContent = choice === "sphere"
        ? "Satellite style"
        : choice === "singularity"
          ? "Singularity detail"
          : choice === "crystal_reactor"
            ? "Crystal motion"
            : choice === "lightweight_rows"
              ? "Brick style"
              : "Number display";
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
    if (colorShortcut) {
      const names = {
        sphere: "Satellite",
        crystal_reactor: "Crystal",
        lightweight_rows: "Brick",
        singularity: "Singularity",
      };
      colorShortcut.classList.toggle("hidden", choice === "number_only");
      if (choice !== "number_only") {
        colorShortcut.setAttribute("title", `Customize ${names[choice] || "visual"} colors`);
      }
    }
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
    const crystalMode = $("acgCrystalColorMode");
    if (crystalMode && crystalMode.value !== state.crystalColorModeDraft) {
      crystalMode.value = state.crystalColorModeDraft;
    }
    syncCrystalColorControls();
  }

  function syncCrystalColorControls() {
    const singleColor = $("acgCrystalSingleColorRow");
    const active = state.crystalColorModeDraft === "core";
    singleColor?.classList.toggle("inactive", !active);
    singleColor?.querySelectorAll("input").forEach((input) => {
      input.disabled = !active;
    });
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
    state.crystalColorModeDraft = getCrystalColorMode(state.data || {});
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
      state.crystalColorModeDraft = getCrystalColorMode(state.data || {});
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

  const MILESTONE_RING_CARDS = 50;

  function milestoneRingSpacing(totalRingCount) {
    return clamp(17 - (Math.max(0, totalRingCount - 10) * 0.15), 12, 17);
  }

  function milestoneRingRadius(ringIndex, totalRingCount) {
    const spacing = milestoneRingSpacing(totalRingCount);
    const groupGap = Math.floor(Math.max(0, ringIndex) / 5) * 9;
    return 104 + (Math.max(0, ringIndex) * spacing) + groupGap;
  }

  function milestoneLiveRadius(completedRingCount) {
    if (completedRingCount <= 0) return 96;
    const spacing = milestoneRingSpacing(completedRingCount);
    return milestoneRingRadius(completedRingCount - 1, completedRingCount) + spacing + 18;
  }

  function milestoneOuterRadius(completedRingCount, liveCount) {
    if (liveCount > 0) return milestoneLiveRadius(completedRingCount);
    if (completedRingCount > 0) {
      return milestoneRingRadius(completedRingCount - 1, completedRingCount);
    }
    return 96;
  }

  function isMilestoneRingMode(sphereMode) {
    return sphereMode === "milestone" || sphereMode === "fusion";
  }

  function fusionLiveRowRadius(completedRingCount, rowIndex) {
    const completedOuterRadius = completedRingCount > 0
      ? milestoneRingRadius(completedRingCount - 1, completedRingCount)
      : 72;
    return completedOuterRadius + 34 + (Math.max(0, rowIndex) * 25);
  }

  function fusionOuterRadius(completedRingCount, liveCount) {
    if (liveCount <= 0) return milestoneOuterRadius(completedRingCount, 0);
    const liveRowCount = Math.ceil(liveCount / 10);
    return fusionLiveRowRadius(completedRingCount, liveRowCount - 1);
  }

  function buildFusionLiveSatellites(liveColors, completedRingCount) {
    const satellites = [];
    const liveRowCount = Math.ceil(liveColors.length / 10);
    for (let rowIndex = 0; rowIndex < liveRowCount; rowIndex += 1) {
      const rowColors = liveColors.slice(rowIndex * 10, (rowIndex + 1) * 10);
      const count = rowColors.length;
      const radius = fusionLiveRowRadius(completedRingCount, rowIndex);
      const baseOffset = orbitBaseOffset(completedRingCount + rowIndex, count);
      const duration = Math.max(6.2, 12 - (rowIndex * 0.72) - (completedRingCount * 0.1));
      rowColors.forEach((color, slotIndex) => {
        satellites.push({
          angle: baseOffset + ((360 / count) * slotIndex),
          radius,
          duration,
          color,
          rowIndex,
        });
      });
    }
    return satellites;
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
      precision highp float;
      attribute vec3 a_orbit;
      attribute vec3 a_previous_orbit;
      attribute vec4 a_color;
      attribute float a_size;
      attribute float a_previous_size;
      attribute float a_demolition_delay;
      uniform vec2 u_resolution;
      uniform float u_pixel_ratio;
      uniform float u_time;
      uniform float u_layout_transition;
      uniform float u_demolition_elapsed;
      varying vec4 v_color;
      varying float v_visibility;
      void main() {
        float theta = a_orbit.x + (u_time * a_orbit.z);
        float previousTheta = a_previous_orbit.x + (u_time * a_previous_orbit.z);
        vec2 targetPosition = vec2(cos(theta), sin(theta)) * a_orbit.y;
        vec2 previousPosition = vec2(cos(previousTheta), sin(previousTheta)) * a_previous_orbit.y;
        float transition = u_layout_transition * u_layout_transition * (3.0 - (2.0 * u_layout_transition));
        vec2 position = mix(previousPosition, targetPosition, transition);
        vec2 clip = position / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
        gl_PointSize = mix(a_previous_size, a_size, transition) * u_pixel_ratio;
        v_color = a_color;
        float demolitionActive = step(0.0, u_demolition_elapsed);
        v_visibility = 1.0 - (demolitionActive * step(a_demolition_delay, u_demolition_elapsed));
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      varying float v_visibility;
      void main() {
        vec2 centered = gl_PointCoord - vec2(0.5);
        float dist = length(centered);
        float core = smoothstep(0.5, 0.39, dist);
        float highlight = smoothstep(0.42, 0.0, length(centered - vec2(-0.13, 0.14)));
        vec3 color = mix(v_color.rgb, vec3(1.0), highlight * 0.28);
        gl_FragColor = vec4(color, core * v_color.a * v_visibility);
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

  function createFusionDebrisProgram(gl) {
    const vertex = createShader(gl, gl.VERTEX_SHADER, `
      precision highp float;
      attribute vec2 a_origin;
      attribute vec2 a_travel;
      attribute vec4 a_color;
      attribute float a_size;
      attribute float a_delay;
      attribute float a_lifetime;
      attribute float a_seed;
      attribute float a_kind;
      uniform vec2 u_resolution;
      uniform float u_pixel_ratio;
      uniform float u_elapsed;
      varying vec4 v_color;
      varying float v_life;
      varying float v_seed;
      varying float v_kind;
      varying float v_active;

      void main() {
        float age = u_elapsed - a_delay;
        float life = clamp(age / a_lifetime, 0.0, 1.0);
        float launched = step(0.0, age) * (1.0 - step(a_lifetime, age));
        float easedTravel = (1.0 - exp(-4.0 * life)) / 0.981684;
        vec2 travelDirection = normalize(a_travel + vec2(0.0001));
        vec2 perpendicular = vec2(-travelDirection.y, travelDirection.x);
        float curve = sin((life * 3.1415926) + (a_seed * 2.3))
          * (0.055 + a_seed * 0.045) * length(a_travel) * life;
        float gravity = length(a_travel) * mix(0.035, 0.11, a_seed) * life * life;
        vec2 position = a_origin + (a_travel * easedTravel)
          + (perpendicular * curve) + vec2(0.0, gravity);
        vec2 clip = position / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
        float sizeFalloff = a_kind < 0.5
          ? mix(1.08, 0.58, life)
          : mix(1.0, 0.28, life);
        gl_PointSize = max(0.0, a_size * u_pixel_ratio * sizeFalloff * launched);
        v_color = a_color;
        v_life = life;
        v_seed = a_seed;
        v_kind = a_kind;
        v_active = launched;
      }
    `);
    const fragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      varying float v_life;
      varying float v_seed;
      varying float v_kind;
      varying float v_active;

      void main() {
        vec2 point = gl_PointCoord - vec2(0.5);
        float rotation = (v_seed * 6.2831853) + (v_life * (2.4 + v_seed * 5.2));
        mat2 spin = mat2(cos(rotation), -sin(rotation), sin(rotation), cos(rotation));
        vec2 local = spin * point;
        float alpha;
        vec3 color;
        if (v_kind < 0.5) {
          float skew = mix(-0.22, 0.20, v_seed);
          local.x += local.y * skew;
          float along = clamp(local.x + 0.50, 0.0, 1.0);
          float halfWidth = mix(0.42, 0.08, along)
            * mix(0.78, 1.08, fract(v_seed * 7.13));
          float wedge = max(abs(local.y) - halfWidth, abs(local.x) - 0.48);
          float chippedCorner = dot(local, normalize(vec2(-0.72, 0.64)))
            - mix(0.28, 0.42, fract(v_seed * 11.7));
          float polygon = max(wedge, chippedCorner);
          float chunk = 1.0 - smoothstep(-0.025, 0.035, polygon);
          float edge = smoothstep(-0.12, -0.015, polygon) * chunk;
          float heat = (1.0 - smoothstep(0.0, 0.34, v_life));
          color = mix(v_color.rgb, vec3(1.0, 0.60, 0.12), heat * edge * 0.82);
          color = mix(color, vec3(0.10, 0.055, 0.035), smoothstep(0.54, 1.0, v_life) * 0.55);
          alpha = chunk * (1.0 - smoothstep(0.66, 1.0, v_life));
        } else {
          float distanceFromCenter = length(point);
          float ember = 1.0 - smoothstep(0.22, 0.50, distanceFromCenter);
          float heat = 1.0 - smoothstep(0.18, 0.82, v_life);
          color = mix(vec3(1.0, 0.31, 0.045), vec3(1.0, 0.93, 0.50), heat);
          alpha = ember * (1.0 - smoothstep(0.42, 1.0, v_life));
        }
        gl_FragColor = vec4(color, alpha * v_color.a * v_active);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "Fusion debris program link failed.");
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
      const debrisProgram = createFusionDebrisProgram(gl);
      const buffer = gl.createBuffer();
      const renderer = {
        canvas,
        gl,
        program,
        buffer,
        orbitLocation: gl.getAttribLocation(program, "a_orbit"),
        previousOrbitLocation: gl.getAttribLocation(program, "a_previous_orbit"),
        colorLocation: gl.getAttribLocation(program, "a_color"),
        sizeLocation: gl.getAttribLocation(program, "a_size"),
        previousSizeLocation: gl.getAttribLocation(program, "a_previous_size"),
        demolitionDelayLocation: gl.getAttribLocation(program, "a_demolition_delay"),
        resolutionLocation: gl.getUniformLocation(program, "u_resolution"),
        pixelRatioLocation: gl.getUniformLocation(program, "u_pixel_ratio"),
        timeLocation: gl.getUniformLocation(program, "u_time"),
        layoutTransitionLocation: gl.getUniformLocation(program, "u_layout_transition"),
        demolitionElapsedLocation: gl.getUniformLocation(program, "u_demolition_elapsed"),
        debrisProgram,
        debrisBuffer: gl.createBuffer(),
        debrisOriginLocation: gl.getAttribLocation(debrisProgram, "a_origin"),
        debrisTravelLocation: gl.getAttribLocation(debrisProgram, "a_travel"),
        debrisColorLocation: gl.getAttribLocation(debrisProgram, "a_color"),
        debrisSizeLocation: gl.getAttribLocation(debrisProgram, "a_size"),
        debrisDelayLocation: gl.getAttribLocation(debrisProgram, "a_delay"),
        debrisLifetimeLocation: gl.getAttribLocation(debrisProgram, "a_lifetime"),
        debrisSeedLocation: gl.getAttribLocation(debrisProgram, "a_seed"),
        debrisKindLocation: gl.getAttribLocation(debrisProgram, "a_kind"),
        debrisResolutionLocation: gl.getUniformLocation(debrisProgram, "u_resolution"),
        debrisPixelRatioLocation: gl.getUniformLocation(debrisProgram, "u_pixel_ratio"),
        debrisElapsedLocation: gl.getUniformLocation(debrisProgram, "u_elapsed"),
        debrisCount: 0,
        debrisDuration: 0,
        satelliteCount: 0,
        satellites: [],
        orbitSignature: "",
        bufferScale: 1,
        lastBufferScale: 0,
        visualTime: performance.now() / 1000,
        lastFrameAt: 0,
        frameId: 0,
        running: false,
        layoutTransitionStartedAt: 0,
        layoutTransitionDuration: 640,
        demolitionStartedAt: 0,
        demolitionComplete: false,
      };
      initializeWebglCanvasSizing(renderer, () => {
        if (!renderer.running && getVisualMode(state.data || {}) === "sphere") {
          renderer.running = true;
          drawWebglFrame(renderer);
        }
      });
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

  function cancelEconomyHoverClose() {
    if (!state.economyCloseTimer) return;
    window.clearTimeout(state.economyCloseTimer);
    state.economyCloseTimer = 0;
  }

  function cancelTimerContextClose() {
    if (!state.timerContextCloseTimer) return;
    window.clearTimeout(state.timerContextCloseTimer);
    state.timerContextCloseTimer = 0;
  }

  function openTimerContext() {
    const zone = $("acgTimerContextZone");
    const hero = $("acgTimerHero");
    if (!zone || !hero) return;
    cancelTimerContextClose();
    zone.classList.add("open");
    hero.setAttribute("aria-expanded", "true");
  }

  function closeTimerContext() {
    cancelTimerContextClose();
    $("acgTimerContextZone")?.classList.remove("open");
    $("acgTimerHero")?.setAttribute("aria-expanded", "false");
  }

  function scheduleTimerContextClose() {
    cancelTimerContextClose();
    state.timerContextCloseTimer = window.setTimeout(() => {
      state.timerContextCloseTimer = 0;
      closeTimerContext();
    }, 520);
  }

  function pointerIsNearTimerContext(x, y) {
    const zone = $("acgTimerContextZone");
    const menu = $("acgTimerContext");
    if (!zone || !menu) return false;
    return Math.min(
      distanceFromPointToRect(x, y, zone.getBoundingClientRect()),
      distanceFromPointToRect(x, y, menu.getBoundingClientRect()),
    ) <= 42;
  }

  function openEconomyHover(root) {
    if (!root) return;
    cancelEconomyHoverClose();
    document.querySelectorAll(".acg-economy-hover-zone.hover-open, .acg-boost-hover-zone.hover-open")
      .forEach((node) => {
        if (node !== root) node.classList.remove("hover-open");
      });
    root.classList.add("hover-open");
  }

  function closeEconomyHover() {
    cancelEconomyHoverClose();
    document.querySelectorAll(".acg-economy-hover-zone.hover-open, .acg-boost-hover-zone.hover-open")
      .forEach((node) => node.classList.remove("hover-open"));
  }

  function scheduleEconomyHoverClose() {
    cancelEconomyHoverClose();
    state.economyCloseTimer = window.setTimeout(() => {
      state.economyCloseTimer = 0;
      closeEconomyHover();
    }, 520);
  }

  function cancelWindowPresetClose() {
    if (!state.presetCloseTimer) return;
    window.clearTimeout(state.presetCloseTimer);
    state.presetCloseTimer = 0;
  }

  function closeWindowPositionPresets() {
    cancelWindowPresetClose();
    if (!state.presetsOpen && !state.presetMenuOpenId) return;
    state.presetsOpen = false;
    state.presetMenuOpenId = "";
    renderWindowPositionPresets(state.data || {});
  }

  function openWindowPositionPresets() {
    if (String(state.data?.displayMode || "inline") !== "compatibility") return;
    if (state.presetsOpen) return;
    state.presetsOpen = true;
    state.presetMenuOpenId = "";
    renderWindowPositionPresets(state.data || {});
  }

  function scheduleWindowPresetClose() {
    cancelWindowPresetClose();
    state.presetCloseTimer = window.setTimeout(() => {
      state.presetCloseTimer = 0;
      closeWindowPositionPresets();
    }, 420);
  }

  function distanceFromPointToRect(x, y, rect) {
    const dx = Math.max(rect.left - x, 0, x - rect.right);
    const dy = Math.max(rect.top - y, 0, y - rect.bottom);
    return Math.hypot(dx, dy);
  }

  function pointerIsNearWindowPresets(x, y) {
    const root = $("acgWindowPresets");
    const panel = $("acgWindowPresetsPanel");
    if (!root || !panel) return false;
    const proximity = 34;
    return Math.min(
      distanceFromPointToRect(x, y, root.getBoundingClientRect()),
      distanceFromPointToRect(x, y, panel.getBoundingClientRect()),
    ) <= proximity;
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
      cancelWindowPresetClose();
      state.presetsOpen = false;
      state.presetMenuOpenId = "";
    }
    root.classList.toggle("open", compatibility && state.presetsOpen);
    root.classList.toggle("disabled", !compatibility);
    toggle.disabled = !compatibility;
    syncQuickControl(
      toggle,
      compatibility && state.presetsOpen,
      compatibility ? "External window presets" : "Window presets are available in external window mode"
    );
    const rows = [
      `
        <div class="acg-window-preset-row acg-window-preset-row-default">
          <button class="acg-window-preset-apply" type="button" data-preset-action="apply" data-preset-id="default" title="Restore the original Anki and Speed Streak external-window positions">Default setup</button>
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
    const bufferScale = clamp(Number(renderer.bufferScale || 1), 0.02, 1);
    if (!renderer.needsResize && renderer.dpr === dpr && renderer.lastBufferScale === bufferScale) {
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
    const nextWidth = Math.max(1, Math.round(width * dpr * bufferScale));
    const nextHeight = Math.max(1, Math.round(height * dpr * bufferScale));
    if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
      canvas.width = nextWidth;
      canvas.height = nextHeight;
    }
    renderer.cssWidth = width;
    renderer.cssHeight = height;
    renderer.bufferWidth = nextWidth;
    renderer.bufferHeight = nextHeight;
    renderer.dpr = dpr;
    renderer.lastBufferScale = bufferScale;
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
      uniform float u_base_progress;
      uniform float u_overflow_progress;
      uniform float u_overflow_turns;
      uniform float u_time;
      uniform vec4 u_color;
      void main() {
        vec2 uv = (gl_FragCoord.xy / u_resolution) - vec2(0.5);
        uv.x *= u_resolution.x / u_resolution.y;
        float radius = length(uv);
        float ring = smoothstep(0.492, 0.472, radius) * smoothstep(0.365, 0.385, radius);
        float overflowRing = smoothstep(0.352, 0.34, radius) * smoothstep(0.302, 0.316, radius);
        float track = ring * 0.18;
        float angle = atan(uv.x, uv.y);
        if (angle < 0.0) angle += 6.28318530718;
        float active = step(angle, clamp(u_progress, 0.0, 1.0) * 6.28318530718);
        float baseActive = step(angle, clamp(u_base_progress, 0.0, 1.0) * 6.28318530718);
        float boostedMain = active * (1.0 - baseActive);
        float electric = 0.72 + (0.18 * sin((angle * 31.0) - (u_time * 15.0)));
        vec3 electricColor = mix(vec3(1.0, 0.52, 0.035), vec3(1.0, 0.86, 0.16), 0.5 + 0.5 * sin(angle * 4.0));
        vec3 activeRgb = mix(u_color.rgb, electricColor * electric, boostedMain);
        vec4 activeColor = vec4(activeRgb, ring * u_color.a);
        vec4 trackColor = vec4(1.0, 1.0, 1.0, track);
        vec4 mainColor = mix(trackColor, activeColor, active);
        float overflowArc = clamp(u_overflow_progress, 0.0, 1.0);
        float overflowActive = step(angle, overflowArc * 6.28318530718);
        float overflowHead = exp(-18.0 * abs(angle - (u_overflow_progress * 6.28318530718)));
        vec4 overflowColor = vec4(electricColor * (0.76 + 0.16 * sin(angle * 37.0 - u_time * 18.0)), overflowRing * (0.68 + 0.24 * overflowHead) * overflowActive);
        float combinedAlpha = overflowColor.a + (mainColor.a * (1.0 - overflowColor.a));
        vec3 combinedRgb = (
          (overflowColor.rgb * overflowColor.a)
          + (mainColor.rgb * mainColor.a * (1.0 - overflowColor.a))
        ) / max(combinedAlpha, 0.0001);
        gl_FragColor = vec4(combinedRgb, combinedAlpha);
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
        baseProgressLocation: gl.getUniformLocation(program, "u_base_progress"),
        overflowProgressLocation: gl.getUniformLocation(program, "u_overflow_progress"),
        overflowTurnsLocation: gl.getUniformLocation(program, "u_overflow_turns"),
        timeLocation: gl.getUniformLocation(program, "u_time"),
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
    let baseProgress = clamp(Number(timer.baseProgress || progress), 0, 1);
    let overflowProgress = Math.max(0, Number(timer.overflowProgress || 0));
    let overflowTurns = Math.max(0, Number(timer.overflowTurns || 0));
    if (timer.active && timer.total > 0) {
      const remaining = Math.max(0, timer.deadlineEpochMs - Date.now());
      const boostRemaining = timer.boostAnchorEpochMs > 0
        ? Math.max(0, timer.storedBoostRemainingMs - Math.max(0, Date.now() - timer.boostAnchorEpochMs))
        : Math.max(0, timer.storedBoostRemainingMs);
      const normalRemaining = Math.max(0, remaining - boostRemaining);
      const boostRatio = timer.baseTotal > 0 ? boostRemaining / timer.baseTotal : 0;
      const normalRatio = timer.baseTotal > 0 ? normalRemaining / timer.baseTotal : 0;
      const totalRatio = timer.baseTotal > 0 ? remaining / timer.baseTotal : 0;
      progress = clamp(totalRatio, 0, 1);
      baseProgress = clamp(normalRatio, 0, 1);
      const overflow = Math.max(0, totalRatio - 1);
      overflowTurns = Math.floor(overflow);
      overflowProgress = overflow - overflowTurns;
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
    gl.uniform1f(renderer.baseProgressLocation, baseProgress);
    gl.uniform1f(renderer.overflowProgressLocation, overflowProgress);
    gl.uniform1f(renderer.overflowTurnsLocation, overflowTurns);
    gl.uniform1f(renderer.timeLocation, performance.now() / 1000);
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
      baseProgress: Number(timer?.baseProgress ?? progress),
      overflowProgress: Number(timer?.overflowProgress || 0),
      overflowTurns: Number(timer?.overflowTurns || 0),
      active: Boolean(active),
      total: Number(timer?.total || 0),
      baseTotal: Number(timer?.baseTotal || timer?.total || 0),
      storedBoostRemainingMs: Number(timer?.storedBoostRemaining || 0),
      boostAnchorEpochMs: Number(timer?.boostAnchor || 0),
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
    if (isMilestoneRingMode(sphereMode)) {
      const completedRingCount = Math.floor(colors.length / MILESTONE_RING_CARDS);
      const liveColors = colors.slice(completedRingCount * MILESTONE_RING_CARDS);
      if (!liveColors.length) return [];
      if (sphereMode === "fusion") {
        return buildFusionLiveSatellites(liveColors, completedRingCount);
      }
      const radius = milestoneLiveRadius(completedRingCount);
      const baseOffset = orbitBaseOffset(completedRingCount, liveColors.length);
      const duration = Math.max(5.8, 12 - (completedRingCount * 0.12) - (liveColors.length * 0.045));
      return liveColors.map((color, slotIndex) => ({
        angle: baseOffset + ((360 / liveColors.length) * slotIndex),
        radius,
        duration,
        color,
      }));
    }
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

  function uploadWebglSatellites(renderer, satellites, signature) {
    if (renderer.orbitSignature === signature) {
      return;
    }
    const previousSatellites = Array.isArray(renderer.satellites) ? renderer.satellites : [];
    const animateFusionAddition = getSphereMode(state.data || {}) === "fusion"
      && satellites.length > 0
      && satellites.length === previousSatellites.length + 1
      && !visualMotionSuspended()
      && !window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    const values = new Float32Array(satellites.length * 13);
    const outerRowIndex = satellites.reduce(
      (maximum, candidate) => Math.max(maximum, Number(candidate.rowIndex || 0)),
      0,
    );
    satellites.forEach((satellite, index) => {
      const offset = index * 13;
      const rgb = satelliteRgb(satellite.color);
      const previous = animateFusionAddition && index < previousSatellites.length
        ? previousSatellites[index]
        : satellite;
      values[offset] = (satellite.angle * Math.PI) / 180;
      values[offset + 1] = satellite.radius;
      values[offset + 2] = (Math.PI * 2) / satellite.duration;
      values[offset + 3] = (previous.angle * Math.PI) / 180;
      values[offset + 4] = previous.radius;
      values[offset + 5] = (Math.PI * 2) / previous.duration;
      values[offset + 6] = 16;
      values[offset + 7] = animateFusionAddition && index >= previousSatellites.length ? 0 : 16;
      values[offset + 8] = rgb[0];
      values[offset + 9] = rgb[1];
      values[offset + 10] = rgb[2];
      values[offset + 11] = rgb[3];
      const rowIndex = Math.max(0, Number(satellite.rowIndex || 0));
      values[offset + 12] = Math.max(0, outerRowIndex - rowIndex) * 0.05;
    });
    const gl = renderer.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
    gl.bufferData(gl.ARRAY_BUFFER, values, gl.STATIC_DRAW);
    renderer.satelliteCount = satellites.length;
    renderer.satellites = satellites.map((satellite) => ({ ...satellite }));
    renderer.orbitSignature = signature;
    renderer.layoutTransitionStartedAt = animateFusionAddition ? performance.now() : 0;
  }

  function buildFusionDebris(renderer) {
    const satellites = Array.isArray(renderer?.satellites) ? renderer.satellites : [];
    if (!satellites.length) return { values: new Float32Array(0), count: 0, duration: 0 };
    const particlesPerSatellite = 9;
    const stride = 13;
    const values = new Float32Array(satellites.length * particlesPerSatellite * stride);
    const outerRowIndex = satellites.reduce(
      (maximum, satellite) => Math.max(maximum, Number(satellite.rowIndex || 0)),
      0,
    );
    let cursor = 0;
    let duration = 0;
    const sceneScale = clamp(Number(renderer.bufferScale || 1), 0.10, 1);
    satellites.forEach((satellite, satelliteIndex) => {
      const theta = ((Number(satellite.angle || 0) * Math.PI) / 180)
        + (renderer.visualTime * ((Math.PI * 2) / Math.max(0.1, Number(satellite.duration || 10))));
      const rowIndex = Math.max(0, Number(satellite.rowIndex || 0));
      const rowDelay = Math.max(0, outerRowIndex - rowIndex) * 0.05;
      const angularSpeed = (Math.PI * 2) / Math.max(0.1, Number(satellite.duration || 10));
      const explosionTheta = theta + (rowDelay * angularSpeed);
      const explosionOriginX = Math.cos(explosionTheta) * Number(satellite.radius || 0);
      const explosionOriginY = Math.sin(explosionTheta) * Number(satellite.radius || 0);
      const rgb = satelliteRgb(satellite.color);
      for (let particleIndex = 0; particleIndex < particlesPerSatellite; particleIndex += 1) {
        const particleSeed = singularityHash(
          ((satelliteIndex + 1) * 91.17) + ((particleIndex + 1) * 37.41),
        );
        const angleSeed = singularityHash((particleSeed * 217.7) + 13.9);
        const speedSeed = singularityHash((particleSeed * 311.3) + 29.1);
        const sizeSeed = singularityHash((particleSeed * 419.9) + 47.3);
        const lifetimeSeed = singularityHash((particleSeed * 523.1) + 71.7);
        const angle = angleSeed * Math.PI * 2;
        const ember = particleIndex >= 6;
        const screenDistance = ember
          ? 28 + (speedSeed * 25)
          : 18 + (speedSeed * 24);
        const distance = screenDistance / sceneScale;
        const size = ember
          ? 2.4 + (sizeSeed * 2.8)
          : 10 + (sizeSeed * 8);
        const lifetime = ember
          ? 0.34 + (lifetimeSeed * 0.22)
          : 0.48 + (lifetimeSeed * 0.22);
        const delay = rowDelay + (particleIndex === 0 ? 0 : particleSeed * 0.018);
        values[cursor] = explosionOriginX;
        values[cursor + 1] = explosionOriginY;
        values[cursor + 2] = Math.cos(angle) * distance;
        values[cursor + 3] = Math.sin(angle) * distance;
        values[cursor + 4] = rgb[0];
        values[cursor + 5] = rgb[1];
        values[cursor + 6] = rgb[2];
        values[cursor + 7] = rgb[3];
        values[cursor + 8] = size;
        values[cursor + 9] = delay;
        values[cursor + 10] = lifetime;
        values[cursor + 11] = particleSeed;
        values[cursor + 12] = ember ? 1 : 0;
        cursor += stride;
        duration = Math.max(duration, delay + lifetime);
      }
    });
    return { values, count: satellites.length * particlesPerSatellite, duration };
  }

  function uploadFusionDebris(renderer) {
    const debris = buildFusionDebris(renderer);
    const gl = renderer.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER, renderer.debrisBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, debris.values, gl.STATIC_DRAW);
    renderer.debrisCount = debris.count;
    renderer.debrisDuration = debris.duration;
  }

  function visualMotionSuspended() {
    return Boolean(document.hidden || state.settingsOpen || state.data?.paused);
  }

  function shouldAnimateWebglOrbit(renderer) {
    return Boolean(
      renderer?.satelliteCount > 0
      && (!visualMotionSuspended() || Boolean(renderer?.demolitionStartedAt))
      && state.data?.enabled
      && state.data?.visualsEnabled
      && !state.data?.sidebarCollapsed
      && getVisualMode(state.data) === "sphere"
      && getRenderMode(state.data) === "webgl"
      && Boolean(state.data?.orbitAnimationEnabled ?? true)
    );
  }

  function drawWebglFrame(renderer, timestamp = performance.now()) {
    if (!renderer.running) {
      return;
    }
    renderer.frameId = 0;
    const now = Number(timestamp || performance.now()) / 1000;
    const animate = shouldAnimateWebglOrbit(renderer);
    if (animate && renderer.lastFrameAt > 0) {
      renderer.visualTime += clamp(now - renderer.lastFrameAt, 0, 0.08);
    }
    renderer.lastFrameAt = now;
    const { width, height, dpr } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);

    if (renderer.satelliteCount > 0) {
      gl.useProgram(renderer.program);
      gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
      const stride = 13 * 4;
      gl.enableVertexAttribArray(renderer.orbitLocation);
      gl.vertexAttribPointer(renderer.orbitLocation, 3, gl.FLOAT, false, stride, 0);
      gl.enableVertexAttribArray(renderer.previousOrbitLocation);
      gl.vertexAttribPointer(renderer.previousOrbitLocation, 3, gl.FLOAT, false, stride, 3 * 4);
      gl.enableVertexAttribArray(renderer.sizeLocation);
      gl.vertexAttribPointer(renderer.sizeLocation, 1, gl.FLOAT, false, stride, 6 * 4);
      gl.enableVertexAttribArray(renderer.previousSizeLocation);
      gl.vertexAttribPointer(renderer.previousSizeLocation, 1, gl.FLOAT, false, stride, 7 * 4);
      gl.enableVertexAttribArray(renderer.colorLocation);
      gl.vertexAttribPointer(renderer.colorLocation, 4, gl.FLOAT, false, stride, 8 * 4);
      gl.enableVertexAttribArray(renderer.demolitionDelayLocation);
      gl.vertexAttribPointer(renderer.demolitionDelayLocation, 1, gl.FLOAT, false, stride, 12 * 4);
      gl.uniform2f(renderer.resolutionLocation, width, height);
      const sceneScale = clamp(Number(renderer.bufferScale || 1), 0.02, 1);
      gl.uniform1f(renderer.pixelRatioLocation, dpr * sceneScale);
      gl.uniform1f(renderer.timeLocation, renderer.visualTime);
      const layoutTransition = renderer.layoutTransitionStartedAt
        ? clamp((performance.now() - renderer.layoutTransitionStartedAt) / renderer.layoutTransitionDuration, 0, 1)
        : 1;
      gl.uniform1f(renderer.layoutTransitionLocation, layoutTransition);
      const demolitionElapsed = renderer.demolitionStartedAt
        ? Math.max(0, (performance.now() - renderer.demolitionStartedAt) / 1000)
        : renderer.demolitionComplete ? Math.max(1, renderer.debrisDuration + 1) : -1;
      gl.uniform1f(renderer.demolitionElapsedLocation, demolitionElapsed);
      gl.drawArrays(gl.POINTS, 0, renderer.satelliteCount);
      if (layoutTransition >= 1) renderer.layoutTransitionStartedAt = 0;
      if (renderer.demolitionStartedAt && renderer.debrisCount > 0) {
        gl.useProgram(renderer.debrisProgram);
        gl.bindBuffer(gl.ARRAY_BUFFER, renderer.debrisBuffer);
        const debrisStride = 13 * 4;
        gl.enableVertexAttribArray(renderer.debrisOriginLocation);
        gl.vertexAttribPointer(renderer.debrisOriginLocation, 2, gl.FLOAT, false, debrisStride, 0);
        gl.enableVertexAttribArray(renderer.debrisTravelLocation);
        gl.vertexAttribPointer(renderer.debrisTravelLocation, 2, gl.FLOAT, false, debrisStride, 2 * 4);
        gl.enableVertexAttribArray(renderer.debrisColorLocation);
        gl.vertexAttribPointer(renderer.debrisColorLocation, 4, gl.FLOAT, false, debrisStride, 4 * 4);
        gl.enableVertexAttribArray(renderer.debrisSizeLocation);
        gl.vertexAttribPointer(renderer.debrisSizeLocation, 1, gl.FLOAT, false, debrisStride, 8 * 4);
        gl.enableVertexAttribArray(renderer.debrisDelayLocation);
        gl.vertexAttribPointer(renderer.debrisDelayLocation, 1, gl.FLOAT, false, debrisStride, 9 * 4);
        gl.enableVertexAttribArray(renderer.debrisLifetimeLocation);
        gl.vertexAttribPointer(renderer.debrisLifetimeLocation, 1, gl.FLOAT, false, debrisStride, 10 * 4);
        gl.enableVertexAttribArray(renderer.debrisSeedLocation);
        gl.vertexAttribPointer(renderer.debrisSeedLocation, 1, gl.FLOAT, false, debrisStride, 11 * 4);
        gl.enableVertexAttribArray(renderer.debrisKindLocation);
        gl.vertexAttribPointer(renderer.debrisKindLocation, 1, gl.FLOAT, false, debrisStride, 12 * 4);
        gl.uniform2f(renderer.debrisResolutionLocation, width, height);
        gl.uniform1f(renderer.debrisPixelRatioLocation, dpr);
        gl.uniform1f(renderer.debrisElapsedLocation, demolitionElapsed);
        gl.drawArrays(gl.POINTS, 0, renderer.debrisCount);
      }
      if (renderer.demolitionStartedAt && demolitionElapsed >= renderer.debrisDuration) {
        renderer.demolitionStartedAt = 0;
        renderer.demolitionComplete = true;
        renderer.debrisCount = 0;
      }
    }

    if (animate) {
      renderer.frameId = window.requestAnimationFrame((nextTimestamp) => drawWebglFrame(renderer, nextTimestamp));
    } else {
      renderer.running = false;
      renderer.lastFrameAt = 0;
    }
  }

  function stopWebglOrbit() {
    const renderer = state.webgl;
    if (!renderer) {
      return;
    }
    renderer.running = false;
    renderer.lastFrameAt = 0;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    try {
      renderer.gl.clearColor(0, 0, 0, 0);
      renderer.gl.clear(renderer.gl.COLOR_BUFFER_BIT);
    } catch (_error) {}
  }

  function singularityHash(value) {
    const raw = Math.sin((Number(value || 0) + 1.371) * 91.729) * 43758.5453123;
    return raw - Math.floor(raw);
  }

  function singularityQuality(data) {
    const renderMode = getRenderMode(data);
    if (renderMode === "ultra_low_resource") return 0;
    if (renderMode === "low_resource") return 1;
    return 2;
  }

  function singularityRgbFromHex(hex) {
    const rgb = hexToRgb(hex);
    return [rgb[0] / 255, rgb[1] / 255, rgb[2] / 255];
  }

  function mixSingularityRgb(a, b, amount) {
    const t = clamp(Number(amount || 0), 0, 1);
    return [
      a[0] + ((b[0] - a[0]) * t),
      a[1] + ((b[1] - a[1]) * t),
      a[2] + ((b[2] - a[2]) * t),
    ];
  }

  function singularityNeonPalette(data) {
    const palette = resolveCustomColors(data?.customColors || {}, data?.appearanceMode || "midnight");
    return {
      core: singularityRgbFromHex(palette.core),
      red: singularityRgbFromHex(palette.red),
      yellow: singularityRgbFromHex(palette.yellow),
      green: singularityRgbFromHex(palette.green),
      blue: singularityRgbFromHex(palette.blue),
    };
  }

  function singularityCoreColor(data) {
    return singularityNeonPalette(data).core;
  }

  function singularityEventColor(data) {
    const palette = singularityNeonPalette(data);
    const key = ["red", "yellow", "green", "blue"].includes(String(data?.lastSatelliteColor || ""))
      ? String(data.lastSatelliteColor)
      : "blue";
    return palette[key];
  }

  function createSingularityPrograms(gl) {
    const backgroundVertex = createShader(gl, gl.VERTEX_SHADER, `
      attribute vec2 a_position;
      void main() {
        gl_Position = vec4(a_position, 0.0, 1.0);
      }
    `);
    const backgroundFragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      uniform vec2 u_resolution;
      uniform float u_time;
      uniform float u_intensity;
      uniform float u_decade;
      uniform float u_fifty;
      uniform float u_century;
      uniform float u_event_age;
      uniform float u_event_strength;
      uniform float u_failure;
      uniform float u_quality;
      uniform float u_paused;
      uniform vec3 u_core_color;
      uniform vec3 u_event_color;
      uniform vec3 u_palette_red;
      uniform vec3 u_palette_yellow;
      uniform vec3 u_palette_green;
      uniform vec3 u_palette_blue;

      mat2 rotate2d(float angle) {
        float s = sin(angle);
        float c = cos(angle);
        return mat2(c, -s, s, c);
      }

      float thinRing(float radius, float target, float width) {
        return exp(-abs(radius - target) * width);
      }

      void main() {
        vec2 uv = gl_FragCoord.xy / u_resolution;
        vec2 p = uv - vec2(0.5);
        p.x *= u_resolution.x / max(1.0, u_resolution.y);
        float radius = length(p);
        float angle = atan(p.y, p.x);
        float motion = mix(1.0, 0.05, u_paused);
        float coreRadius = 0.075
          + min(u_decade, 12.0) * 0.0017
          + min(u_fifty, 5.0) * 0.0035
          + min(u_century, 4.0) * 0.0045;
        float breathing = 1.0 + sin(u_time * 1.75 * motion + u_decade * 0.27) * (0.018 + u_intensity * 0.012);
        coreRadius *= breathing;

        float eventVisible = 1.0 - smoothstep(0.0, 1.18, u_event_age);
        float eventFlash = eventVisible * u_event_strength;
        float fieldFalloff = exp(-radius * (3.6 - min(u_intensity, 1.2) * 0.44));
        float twist = fieldFalloff
          * (0.035 + u_intensity * 0.095 + min(u_fifty, 4.0) * 0.012)
          * sin(u_time * 0.72 * motion + radius * 10.0 + u_century * 0.7);
        vec2 warped = rotate2d(twist) * p;
        warped *= 1.0 + fieldFalloff * (0.07 + u_intensity * 0.11 + eventVisible * 0.055);

        float gridScale = 13.0 + min(u_decade, 10.0) * 0.22 + min(u_century, 3.0) * 1.2;
        vec2 gridCell = abs(fract(warped * gridScale + 0.5) - 0.5);
        float grid = max(smoothstep(0.462, 0.495, gridCell.x), smoothstep(0.462, 0.495, gridCell.y));
        float gridWindow = smoothstep(0.075, 0.18, radius) * (1.0 - smoothstep(0.62, 0.92, radius));
        float gridLevel = 0.008
          + step(1.0, u_decade) * 0.028
          + min(u_fifty, 4.0) * 0.008
          + min(u_century, 3.0) * 0.012;
        gridLevel *= mix(0.58, 1.0, u_quality * 0.5);

        float neonShift = 0.5 + 0.5 * sin(angle * 3.0 - u_time * 0.34 * motion + radius * 8.0);
        vec3 neonCool = mix(u_palette_blue, u_palette_green, neonShift);
        vec3 neonWarm = mix(u_palette_red, u_palette_yellow, 0.5 + 0.5 * sin(angle * 2.0 + u_time * 0.27 * motion));
        vec3 base = vec3(0.0025, 0.0045, 0.014);
        base += u_core_color * exp(-radius * 8.5) * (0.032 + u_intensity * 0.075);
        base += mix(u_core_color, neonCool, 0.44) * grid * gridWindow * gridLevel;

        float deepHalo = exp(-radius * (10.8 - u_intensity * 1.1));
        float nearHalo = exp(-radius * 23.0);
        base += u_core_color * deepHalo * (0.10 + u_intensity * 0.17);
        base += mix(u_core_color, vec3(1.0), 0.42) * nearHalo * (0.10 + u_intensity * 0.15);

        float horizonOuter = thinRing(radius, coreRadius, 128.0);
        float horizonHot = thinRing(radius, coreRadius * 0.93, 210.0);
        vec3 horizonColor = mix(u_core_color, vec3(1.0), 0.62 + min(u_intensity, 1.0) * 0.18);
        base += horizonColor * horizonOuter * (0.58 + u_intensity * 0.62 + eventFlash * 0.46);
        base += vec3(1.0) * horizonHot * (0.16 + eventFlash * 0.34);

        float coronaOne = thinRing(radius, coreRadius + 0.028, 96.0);
        float coronaOneSegments = pow(max(0.0, 0.5 + 0.5 * sin(angle * 3.0 - u_time * 1.7 * motion + radius * 14.0)), 3.0);
        base += mix(u_core_color, neonCool, 0.58)
          * coronaOne * coronaOneSegments * (0.18 + u_intensity * 0.42);

        float secondEnabled = step(2.0, u_decade);
        float coronaTwo = thinRing(radius, coreRadius + 0.054, 82.0);
        float coronaTwoSegments = pow(max(0.0, 0.5 + 0.5 * sin(angle * 5.0 + u_time * 1.12 * motion - radius * 17.0)), 4.0);
        base += mix(u_core_color, mix(u_palette_red, u_palette_blue, neonShift), 0.64)
          * coronaTwo * coronaTwoSegments * secondEnabled * (0.10 + u_intensity * 0.26);

        float decadeStep = mod(u_decade, 5.0);
        float decadeBand = thinRing(radius, coreRadius + 0.066 + decadeStep * 0.009, 76.0);
        float decadeSegments = pow(
          max(0.0, 0.5 + 0.5 * sin(angle * (4.0 + decadeStep) - u_time * (0.58 + decadeStep * 0.08) * motion)),
          5.0
        );
        base += mix(u_core_color, mix(u_palette_yellow, u_palette_green, neonShift), 0.58)
          * decadeBand * decadeSegments * step(1.0, u_decade) * (0.075 + decadeStep * 0.026);

        float phaseEnabled = step(1.0, u_fifty);
        float phaseRing = thinRing(radius, coreRadius + 0.088 + min(u_fifty, 4.0) * 0.008, 68.0);
        float phaseSegments = pow(max(0.0, 0.5 + 0.5 * sin(angle * 7.0 - u_time * 0.76 * motion)), 6.0);
        base += mix(u_core_color, neonWarm, 0.66)
          * phaseRing * (0.18 + phaseSegments * 0.52) * phaseEnabled * min(1.0, 0.48 + u_fifty * 0.18);

        float apexEnabled = step(1.0, u_century);
        float apexRadius = 0.245 + min(u_century, 4.0) * 0.016;
        float apexRing = thinRing(radius, apexRadius, 72.0);
        float apexSegments = 0.3 + 0.7 * pow(max(0.0, 0.5 + 0.5 * sin(angle * 8.0 + u_time * 0.41 * motion)), 4.0);
        base += mix(neonCool, neonWarm, 0.48 + 0.22 * sin(angle * 4.0))
          * apexRing * apexSegments * apexEnabled * (0.17 + min(u_century, 3.0) * 0.07);
        float spokes = pow(abs(cos(angle * (4.0 + min(u_century, 3.0)))), 34.0)
          * smoothstep(coreRadius + 0.02, coreRadius + 0.09, radius)
          * (1.0 - smoothstep(0.28, 0.54, radius));
        base += mix(u_core_color, vec3(1.0), 0.62) * spokes * apexEnabled * (0.018 + min(u_century, 4.0) * 0.014);

        float waveRadius = 0.055 + u_event_age * (0.24 + min(u_event_strength, 4.0) * 0.028);
        float shockwave = thinRing(radius, waveRadius, 88.0) * eventVisible;
        base += mix(u_event_color, vec3(1.0), 0.44) * shockwave * (0.20 + u_event_strength * 0.20);
        base += u_event_color * exp(-radius * 7.5) * eventVisible * (0.025 + u_event_strength * 0.025);

        float failureFlash = u_failure * eventVisible;
        base += vec3(1.0, 0.08, 0.18) * exp(-radius * 5.6) * failureFlash * 0.34;
        base += vec3(1.0) * horizonOuter * failureFlash * 0.76;

        float disk = 1.0 - smoothstep(coreRadius * 0.70, coreRadius * 0.965, radius);
        vec3 voidColor = vec3(0.0005, 0.0008, 0.0035) + u_core_color * 0.006;
        base = mix(base, voidColor, disk * (0.94 - failureFlash * 0.17));
        float pin = exp(-radius * 82.0);
        base += vec3(1.0) * pin * (0.04 + eventVisible * 0.21);

        float vignette = 1.0 - smoothstep(0.38, 0.92, radius);
        base *= 0.58 + 0.42 * vignette;
        gl_FragColor = vec4(base, 1.0);
      }
    `);
    const backgroundProgram = gl.createProgram();
    gl.attachShader(backgroundProgram, backgroundVertex);
    gl.attachShader(backgroundProgram, backgroundFragment);
    gl.linkProgram(backgroundProgram);
    if (!gl.getProgramParameter(backgroundProgram, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(backgroundProgram) || "WebGL Singularity background program link failed.");
    }

    const particleVertex = createShader(gl, gl.VERTEX_SHADER, `
      precision mediump float;
      attribute vec2 a_position;
      attribute float a_size;
      attribute float a_angle;
      attribute float a_stretch;
      attribute vec4 a_color;
      uniform vec2 u_resolution;
      uniform float u_pixel_ratio;
      varying vec4 v_color;
      varying float v_angle;
      varying float v_stretch;
      void main() {
        vec2 clip = a_position / (u_resolution * 0.5);
        gl_Position = vec4(clip.x, -clip.y, 0.0, 1.0);
        gl_PointSize = a_size * a_stretch * u_pixel_ratio;
        v_color = a_color;
        v_angle = a_angle;
        v_stretch = a_stretch;
      }
    `);
    const particleFragment = createShader(gl, gl.FRAGMENT_SHADER, `
      precision mediump float;
      varying vec4 v_color;
      varying float v_angle;
      varying float v_stretch;
      void main() {
        vec2 point = gl_PointCoord - vec2(0.5);
        float s = sin(v_angle);
        float c = cos(v_angle);
        vec2 local = mat2(c, -s, s, c) * point;
        float distanceToTrail = length(vec2(local.x, local.y * v_stretch)) * 2.0;
        float soft = 1.0 - smoothstep(0.08, 1.0, distanceToTrail);
        float hot = exp(-distanceToTrail * distanceToTrail * 14.0);
        float needle = exp(-abs(local.y) * v_stretch * 24.0) * (1.0 - smoothstep(0.10, 0.50, abs(local.x)));
        vec3 color = mix(v_color.rgb, vec3(1.0), clamp(hot * 0.78 + needle * 0.34, 0.0, 0.9));
        gl_FragColor = vec4(color, soft * v_color.a);
      }
    `);
    const particleProgram = gl.createProgram();
    gl.attachShader(particleProgram, particleVertex);
    gl.attachShader(particleProgram, particleFragment);
    gl.linkProgram(particleProgram);
    if (!gl.getProgramParameter(particleProgram, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(particleProgram) || "WebGL Singularity particle program link failed.");
    }
    for (const [program, shaders] of [
      [backgroundProgram, [backgroundVertex, backgroundFragment]],
      [particleProgram, [particleVertex, particleFragment]],
    ]) {
      for (const shader of shaders) {
        gl.detachShader(program, shader);
        gl.deleteShader(shader);
      }
    }
    return { backgroundProgram, particleProgram };
  }

  function ensureSingularityRenderer() {
    const canvas = $("acgSingularityCanvas");
    if (!canvas) return null;
    if (state.singularityWebgl?.canvas === canvas && state.singularityWebgl.gl) {
      return state.singularityWebgl.contextLost ? null : state.singularityWebgl;
    }
    if (state.singularityWebgl) {
      disposeSingularityRenderer(state.singularityWebgl);
    }
    try {
      const gl = canvas.getContext("webgl", {
        alpha: false,
        antialias: false,
        depth: false,
        stencil: false,
        premultipliedAlpha: false,
        powerPreference: "high-performance",
      });
      if (!gl) return null;
      const programs = createSingularityPrograms(gl);
      const quadBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, quadBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
      const particleBuffer = gl.createBuffer();
      const initialParticleCapacity = 4096;
      gl.bindBuffer(gl.ARRAY_BUFFER, particleBuffer);
      gl.bufferData(gl.ARRAY_BUFFER, initialParticleCapacity * 4, gl.DYNAMIC_DRAW);
      const renderer = {
        canvas,
        gl,
        ...programs,
        quadBuffer,
        particleBuffer,
        background: {
          position: gl.getAttribLocation(programs.backgroundProgram, "a_position"),
          resolution: gl.getUniformLocation(programs.backgroundProgram, "u_resolution"),
          time: gl.getUniformLocation(programs.backgroundProgram, "u_time"),
          intensity: gl.getUniformLocation(programs.backgroundProgram, "u_intensity"),
          decade: gl.getUniformLocation(programs.backgroundProgram, "u_decade"),
          fifty: gl.getUniformLocation(programs.backgroundProgram, "u_fifty"),
          century: gl.getUniformLocation(programs.backgroundProgram, "u_century"),
          eventAge: gl.getUniformLocation(programs.backgroundProgram, "u_event_age"),
          eventStrength: gl.getUniformLocation(programs.backgroundProgram, "u_event_strength"),
          failure: gl.getUniformLocation(programs.backgroundProgram, "u_failure"),
          quality: gl.getUniformLocation(programs.backgroundProgram, "u_quality"),
          paused: gl.getUniformLocation(programs.backgroundProgram, "u_paused"),
          coreColor: gl.getUniformLocation(programs.backgroundProgram, "u_core_color"),
          eventColor: gl.getUniformLocation(programs.backgroundProgram, "u_event_color"),
          paletteRed: gl.getUniformLocation(programs.backgroundProgram, "u_palette_red"),
          paletteYellow: gl.getUniformLocation(programs.backgroundProgram, "u_palette_yellow"),
          paletteGreen: gl.getUniformLocation(programs.backgroundProgram, "u_palette_green"),
          paletteBlue: gl.getUniformLocation(programs.backgroundProgram, "u_palette_blue"),
        },
        particles: {
          position: gl.getAttribLocation(programs.particleProgram, "a_position"),
          size: gl.getAttribLocation(programs.particleProgram, "a_size"),
          angle: gl.getAttribLocation(programs.particleProgram, "a_angle"),
          stretch: gl.getAttribLocation(programs.particleProgram, "a_stretch"),
          color: gl.getAttribLocation(programs.particleProgram, "a_color"),
          resolution: gl.getUniformLocation(programs.particleProgram, "u_resolution"),
          pixelRatio: gl.getUniformLocation(programs.particleProgram, "u_pixel_ratio"),
        },
        cssWidth: 0,
        cssHeight: 0,
        pixelRatio: 1,
        quality: 2,
        needsResize: true,
        resizeObserver: null,
        contextLost: false,
        contextLostHandler: null,
        contextRestoredHandler: null,
        frameId: 0,
        running: false,
        lastFrameAt: 0,
        lastDrawAt: 0,
        visualTime: 0,
        data: null,
        lastEventNonce: null,
        eventStartAt: -100,
        eventType: "",
        eventColor: [0.5, 0.69, 1.0],
        eventStrength: 0,
        eventSourceStreak: 0,
        particleValues: [],
        particleUpload: new Float32Array(initialParticleCapacity),
        particleBufferCapacity: initialParticleCapacity,
      };
      renderer.contextLostHandler = (event) => {
        event.preventDefault();
        if (state.singularityWebgl !== renderer) return;
        renderer.contextLost = true;
        renderer.running = false;
        if (renderer.frameId) {
          window.cancelAnimationFrame(renderer.frameId);
          renderer.frameId = 0;
        }
      };
      renderer.contextRestoredHandler = () => {
        if (state.singularityWebgl !== renderer) return;
        const shouldResume = Boolean(state.data) && isSingularityMode(state.data);
        disposeSingularityRenderer(renderer, false);
        if (shouldResume && !document.hidden && state.data) {
          window.requestAnimationFrame(() => renderSingularity(state.data));
        }
      };
      canvas.addEventListener("webglcontextlost", renderer.contextLostHandler, false);
      canvas.addEventListener("webglcontextrestored", renderer.contextRestoredHandler, false);
      if (typeof ResizeObserver === "function") {
        renderer.resizeObserver = new ResizeObserver(() => {
          renderer.needsResize = true;
          if (renderer.data && !renderer.running && !renderer.contextLost && !document.hidden) {
            renderer.running = true;
            renderer.frameId = window.requestAnimationFrame((timestamp) => drawSingularityFrame(renderer, timestamp));
          }
        });
        renderer.resizeObserver.observe(canvas);
      }
      state.singularityWebgl = renderer;
      return renderer;
    } catch (error) {
      console.error("Speed Streak Singularity WebGL initialization failed:", error);
      return null;
    }
  }

  function resizeSingularityCanvas(renderer) {
    const rect = renderer.canvas.getBoundingClientRect();
    const width = Math.max(1, Number(rect.width || renderer.cssWidth || 1));
    const height = Math.max(1, Number(rect.height || renderer.cssHeight || 1));
    const deviceRatio = clamp(window.devicePixelRatio || 1, 1, 2);
    const pixelRatio = renderer.quality === 0
      ? Math.min(deviceRatio, 0.78)
      : renderer.quality === 1
        ? Math.min(deviceRatio, 1.05)
        : Math.min(deviceRatio, 1.45);
    const bufferWidth = Math.max(1, Math.round(width * pixelRatio));
    const bufferHeight = Math.max(1, Math.round(height * pixelRatio));
    if (renderer.canvas.width !== bufferWidth || renderer.canvas.height !== bufferHeight) {
      renderer.canvas.width = bufferWidth;
      renderer.canvas.height = bufferHeight;
    }
    renderer.cssWidth = width;
    renderer.cssHeight = height;
    renderer.pixelRatio = pixelRatio;
    renderer.needsResize = false;
    renderer.gl.viewport(0, 0, bufferWidth, bufferHeight);
    return { width, height, bufferWidth, bufferHeight, pixelRatio };
  }

  function appendSingularityPoint(values, x, y, size, angle, stretch, color, alpha) {
    values.push(
      x,
      y,
      size,
      angle,
      stretch,
      clamp(color[0], 0, 1),
      clamp(color[1], 0, 1),
      clamp(color[2], 0, 1),
      clamp(alpha, 0, 1),
    );
  }

  function singularityEaseOut(value) {
    const t = clamp(value, 0, 1);
    return 1 - Math.pow(1 - t, 3);
  }

  function appendSingularityDecadeRing(values, renderer, eventAge, minSize, coreRadius, palette) {
    const streak = Math.max(0, Number(renderer.data?.streak || 0));
    if (!["hard", "good", "easy"].includes(renderer.eventType) || streak <= 0 || streak % 10 !== 0 || streak % 50 === 0 || eventAge > 1.9) {
      return;
    }
    const quality = renderer.quality;
    const decadeWithinPhase = Math.max(1, Math.floor((streak % 50 || 50) / 10));
    const count = (quality === 0 ? 16 : quality === 1 ? 26 : 38) + (decadeWithinPhase * 2);
    const expand = singularityEaseOut(eventAge / 0.42);
    const capture = singularityEaseOut((eventAge - 0.42) / 1.25);
    const expandedRadius = coreRadius * 1.18 + minSize * (0.27 + decadeWithinPhase * 0.018) * expand;
    const radius = expandedRadius + ((coreRadius * 1.28 - expandedRadius) * capture);
    const fade = 1 - smoothstepNumber(1.48, 1.9, eventAge);
    const colors = [palette.blue, palette.green, palette.yellow, palette.red];
    for (let index = 0; index < count; index += 1) {
      const seed = singularityHash(index * 17.31 + streak * 0.19);
      const angle = (index / count) * Math.PI * 2 + capture * Math.PI * (2.4 + decadeWithinPhase * 0.18);
      const jitter = (seed - 0.5) * minSize * 0.009 * (1 - capture);
      const color = mixSingularityRgb(colors[(index + decadeWithinPhase) % colors.length], palette.core, capture * 0.5);
      appendSingularityPoint(
        values,
        Math.cos(angle) * (radius + jitter),
        Math.sin(angle) * (radius + jitter) * (0.9 + seed * 0.08),
        3.1 + seed * 3.4 + decadeWithinPhase * 0.18,
        angle + Math.PI * 0.5,
        1.25 + capture * 2.4,
        color,
        fade * (0.5 + quality * 0.14),
      );
    }
  }

  function singularityStarPoint(progress, outerRadius, innerRadius) {
    const segmentProgress = ((progress % 1) + 1) % 1 * 10;
    const segment = Math.floor(segmentProgress);
    const local = segmentProgress - segment;
    const angleA = -Math.PI / 2 + (segment / 10) * Math.PI * 2;
    const angleB = -Math.PI / 2 + ((segment + 1) / 10) * Math.PI * 2;
    const radiusA = segment % 2 === 0 ? outerRadius : innerRadius;
    const radiusB = segment % 2 === 0 ? innerRadius : outerRadius;
    return {
      x: Math.cos(angleA) * radiusA + (Math.cos(angleB) * radiusB - Math.cos(angleA) * radiusA) * local,
      y: Math.sin(angleA) * radiusA + (Math.sin(angleB) * radiusB - Math.sin(angleA) * radiusA) * local,
    };
  }

  function appendSingularityFiftyStar(values, renderer, eventAge, minSize, coreRadius, palette) {
    const streak = Math.max(0, Number(renderer.data?.streak || 0));
    if (!["hard", "good", "easy"].includes(renderer.eventType) || streak <= 0 || streak % 50 !== 0 || eventAge > 2.15) {
      return;
    }
    const quality = renderer.quality;
    const count = quality === 0 ? 28 : quality === 1 ? 46 : 68;
    const expand = singularityEaseOut(eventAge / 0.5);
    const capture = singularityEaseOut((eventAge - 0.5) / 1.38);
    const outerExpanded = coreRadius * 1.26 + minSize * 0.34 * expand;
    const innerExpanded = coreRadius * 1.08 + minSize * 0.15 * expand;
    const outerRadius = outerExpanded + ((coreRadius * 1.4 - outerExpanded) * capture);
    const innerRadius = innerExpanded + ((coreRadius * 1.18 - innerExpanded) * capture);
    const rotation = capture * Math.PI * 3.7 + renderer.visualTime * 0.08;
    const cosRotation = Math.cos(rotation);
    const sinRotation = Math.sin(rotation);
    const fade = 1 - smoothstepNumber(1.72, 2.15, eventAge);
    const colors = [palette.yellow, palette.red, palette.blue, palette.green];
    for (let index = 0; index < count; index += 1) {
      const seed = singularityHash(index * 23.93 + streak * 0.37);
      const point = singularityStarPoint((index + seed * 0.18) / count, outerRadius, innerRadius);
      const x = point.x * cosRotation - point.y * sinRotation;
      const y = point.x * sinRotation + point.y * cosRotation;
      const direction = Math.atan2(y, x) + Math.PI * 0.5;
      const color = mixSingularityRgb(colors[index % colors.length], palette.core, capture * 0.42);
      appendSingularityPoint(
        values,
        x,
        y * 0.94,
        3.6 + seed * 4.1,
        direction,
        1.45 + capture * 2.9,
        color,
        fade * (0.58 + quality * 0.15),
      );
    }
  }

  function appendSingularityIntakeBurst(values, renderer, eventAge, minSize, coreRadius, palette) {
    if (!["hard", "good", "easy"].includes(renderer.eventType) || eventAge < 0 || eventAge > 1.95) {
      return;
    }
    const quality = renderer.quality;
    const count = quality === 0 ? 9 : quality === 1 ? 15 : 22;
    const burstSeed = singularityHash(renderer.lastEventNonce * 5.37 + 0.91);
    const burstAngle = burstSeed * Math.PI * 2;
    const burstRadius = minSize * (0.36 + singularityHash(renderer.lastEventNonce * 9.17) * 0.18);
    const burstX = Math.cos(burstAngle) * burstRadius;
    const burstY = Math.sin(burstAngle) * burstRadius * 0.9;
    const explosion = singularityEaseOut(eventAge / 0.18);
    const capture = singularityEaseOut((eventAge - 0.12) / 1.08);
    const settle = smoothstepNumber(0.72, 1.0, capture);
    const fade = 1 - smoothstepNumber(1.48, 1.95, eventAge);
    const eventColor = renderer.eventColor;
    const neighborColors = [eventColor, palette.yellow, palette.green, palette.blue, palette.red];
    for (let index = 0; index < count; index += 1) {
      const seedA = singularityHash(index * 13.73 + renderer.lastEventNonce * 0.23);
      const seedB = singularityHash(index * 29.11 + renderer.lastEventNonce * 0.41);
      const sprayAngle = burstAngle + (seedA - 0.5) * Math.PI * 1.35;
      const sprayDistance = minSize * (0.012 + seedB * 0.075) * explosion;
      const startX = burstX + Math.cos(sprayAngle) * sprayDistance;
      const startY = burstY + Math.sin(sprayAngle) * sprayDistance;
      const startRadius = Math.max(coreRadius * 1.5, Math.hypot(startX, startY));
      const startAngle = Math.atan2(startY, startX);
      const captureRadius = coreRadius * (1.15 + seedB * 0.52);
      const radius = startRadius + ((captureRadius - startRadius) * capture);
      const turns = 1.75 + seedA * 1.35 + renderer.eventStrength * 0.18;
      const angle = startAngle + capture * Math.PI * 2 * turns + settle * Math.PI * 1.5;
      const nextCapture = clamp(capture + 0.014, 0, 1);
      const nextRadius = startRadius + ((captureRadius - startRadius) * nextCapture);
      const nextAngle = startAngle + nextCapture * Math.PI * 2 * turns + smoothstepNumber(0.72, 1.0, nextCapture) * Math.PI * 1.5;
      const x = Math.cos(angle) * radius;
      const y = Math.sin(angle) * radius * 0.91;
      const velocityAngle = Math.atan2(Math.sin(nextAngle) * nextRadius * 0.91 - y, Math.cos(nextAngle) * nextRadius - x);
      const selectedColor = neighborColors[(index + Math.floor(burstSeed * 4)) % neighborColors.length];
      const color = mixSingularityRgb(selectedColor, palette.core, settle * 0.48);
      const pop = 0.38 + 0.62 * smoothstepNumber(0.0, 0.08, eventAge);
      appendSingularityPoint(
        values,
        x,
        y,
        3.8 + seedA * 4.6 + (1 - capture) * 1.8,
        velocityAngle,
        1.6 + capture * 4.0 + seedB,
        color,
        fade * pop * (0.55 + quality * 0.16),
      );
    }
  }

  function buildSingularityParticles(renderer, eventAge, width, height) {
    const data = renderer.data || {};
    const streak = Math.max(0, Number(data.streak || 0));
    const decade = Math.floor(streak / 10);
    const fifty = Math.floor(streak / 50);
    const century = Math.floor(streak / 100);
    const quality = renderer.quality;
    const intensity = clamp(Math.log2(streak + 1) / 6.65, 0, 1.34);
    const minSize = Math.min(width, height);
    const coreRadius = minSize * (0.075 + Math.min(decade, 12) * 0.0017 + Math.min(fifty, 5) * 0.0035 + Math.min(century, 4) * 0.0045);
    const palette = singularityNeonPalette(data);
    const coreColor = palette.core;
    const neonColors = [palette.blue, palette.green, palette.yellow, palette.red];
    const values = renderer.particleValues;
    values.length = 0;
    const particleCount = quality === 0
      ? Math.min(28, 4 + (decade * 2) + fifty + (century * 2))
      : quality === 1
        ? Math.min(48, 6 + (decade * 3) + (fifty * 2) + (century * 3))
        : Math.min(72, 8 + (decade * 3) + (fifty * 3) + (century * 4));
    const time = renderer.visualTime;
    for (let index = 0; index < particleCount; index += 1) {
      const group = Math.floor(index / 3);
      const groupSlot = index % 3;
      const seedA = singularityHash(group * 7.13 + 0.7);
      const seedB = singularityHash(group * 11.71 + 2.9);
      const seedC = singularityHash(index * 17.17 + 5.1);
      const life = 1.85 + seedB * 2.75 - Math.min(intensity, 1.0) * 0.34;
      const cycle = ((time / life) + seedA + groupSlot * 0.018) % 1;
      const previousCycle = Math.max(0, cycle - 0.0075);
      const outerRadius = minSize * (0.36 + seedB * 0.23);
      const inward = Math.pow(1 - cycle, 0.58 + seedC * 0.08);
      const previousInward = Math.pow(1 - previousCycle, 0.58 + seedC * 0.08);
      const radius = coreRadius * 0.88 + (outerRadius - coreRadius * 0.88) * inward;
      const previousRadius = coreRadius * 0.88 + (outerRadius - coreRadius * 0.88) * previousInward;
      const direction = index % 3 === 0 ? -1 : 1;
      const turns = 2.45 + seedC * 1.75 + Math.min(decade, 10) * 0.035;
      const phase = cycle + cycle * cycle * 0.62;
      const previousPhase = previousCycle + previousCycle * previousCycle * 0.62;
      const baseAngle = seedA * Math.PI * 2 + (groupSlot - 1) * (0.045 + seedC * 0.035);
      const theta = baseAngle + direction * turns * Math.PI * 2 * phase + time * 0.055 * direction;
      const previousTheta = baseAngle + direction * turns * Math.PI * 2 * previousPhase + time * 0.055 * direction;
      const ellipse = 0.84 + seedC * 0.12;
      const x = Math.cos(theta) * radius;
      const y = Math.sin(theta) * radius * ellipse;
      const previousX = Math.cos(previousTheta) * previousRadius;
      const previousY = Math.sin(previousTheta) * previousRadius * ellipse;
      const velocityAngle = Math.atan2(y - previousY, x - previousX);
      const nearCore = 1 - clamp((radius - coreRadius) / Math.max(1, outerRadius - coreRadius), 0, 1);
      const sourceColor = neonColors[(group + decade) % neonColors.length];
      const energizedColor = mixSingularityRgb(sourceColor, coreColor, 0.12 + nearCore * 0.34);
      const whiteMix = 0.08 + nearCore * 0.68;
      const color = [
        energizedColor[0] + (1 - energizedColor[0]) * whiteMix,
        energizedColor[1] + (1 - energizedColor[1]) * whiteMix,
        energizedColor[2] + (1 - energizedColor[2]) * whiteMix,
      ];
      const fade = Math.pow(Math.sin(Math.PI * clamp(cycle, 0.001, 0.999)), 0.34);
      const ignition = smoothstepNumber(0.0, 0.055, cycle);
      const flicker = 0.78 + 0.22 * Math.sin(time * (8.0 + seedC * 9.0) + index * 2.3);
      const size = 4.1 + seedB * 3.1 + intensity * 1.8 + nearCore * 2.2;
      const stretch = 2.3 + nearCore * 3.4 + seedC * 1.1;
      appendSingularityPoint(values, x, y, size, velocityAngle, stretch, color, fade * ignition * flicker * (0.34 + quality * 0.17));
    }

    const failureEvent = renderer.eventType === "again" || renderer.eventType === "timeout" || renderer.eventType === "reset";
    if (failureEvent && eventAge >= 0 && eventAge < 1.08) {
      const explosionProgress = clamp((eventAge - 0.06) / 0.9, 0, 1);
      const explosionCount = quality === 0 ? 18 : quality === 1 ? 30 : 48;
      for (let index = 0; index < explosionCount; index += 1) {
        const seedA = singularityHash(index * 19.31 + renderer.lastEventNonce * 0.17);
        const seedB = singularityHash(index * 31.77 + renderer.lastEventNonce * 0.31);
        const angle = seedA * Math.PI * 2 + explosionProgress * (seedB - 0.5) * 0.65;
        const distance = coreRadius * 0.72 + Math.pow(explosionProgress, 0.68) * minSize * (0.27 + seedB * 0.34);
        const color = [1.0, 0.16 + seedB * 0.34, 0.26 + seedA * 0.3];
        appendSingularityPoint(
          values,
          Math.cos(angle) * distance,
          Math.sin(angle) * distance,
          4.8 + seedB * 4.4,
          angle,
          2.8 + seedA * 3.2,
          color,
          (1 - explosionProgress) * 0.86,
        );
      }
    }
    appendSingularityIntakeBurst(values, renderer, eventAge, minSize, coreRadius, palette);
    appendSingularityDecadeRing(values, renderer, eventAge, minSize, coreRadius, palette);
    appendSingularityFiftyStar(values, renderer, eventAge, minSize, coreRadius, palette);
    return values;
  }

  function smoothstepNumber(edge0, edge1, value) {
    const local = clamp((value - edge0) / Math.max(0.0001, edge1 - edge0), 0, 1);
    return local * local * (3 - 2 * local);
  }

  function drawSingularityFrame(renderer, timestamp) {
    renderer.frameId = 0;
    if (!renderer.running || !renderer.data || renderer.contextLost || document.hidden) {
      renderer.running = false;
      return;
    }
    const now = Number(timestamp || performance.now()) / 1000;
    const frameInterval = renderer.quality === 0 ? 1 / 20 : renderer.quality === 1 ? 1 / 30 : 1 / 60;
    if (renderer.lastDrawAt && now - renderer.lastDrawAt < frameInterval * 0.92) {
      renderer.frameId = window.requestAnimationFrame((nextTimestamp) => drawSingularityFrame(renderer, nextTimestamp));
      return;
    }
    const data = renderer.data;
    const paused = Boolean(data.paused);
    const elapsed = renderer.lastFrameAt ? clamp(now - renderer.lastFrameAt, 0, 0.08) : 0;
    renderer.lastFrameAt = now;
    renderer.lastDrawAt = now;
    if (!paused) renderer.visualTime += elapsed;
    const size = resizeSingularityCanvas(renderer);
    const gl = renderer.gl;
    const streak = Math.max(0, Number(data.streak || 0));
    const decade = Math.floor(streak / 10);
    const fifty = Math.floor(streak / 50);
    const century = Math.floor(streak / 100);
    const intensity = clamp(Math.log2(streak + 1) / 6.65, 0, 1.34);
    const eventAge = renderer.eventStartAt > -10 ? Math.max(0, now - renderer.eventStartAt) : 10;
    const failureEvent = renderer.eventType === "again" || renderer.eventType === "timeout" || renderer.eventType === "reset";
    const failure = failureEvent && eventAge < 1.18 ? 1 : Boolean(data.failureVisualActive) ? 1 : 0;
    const palette = singularityNeonPalette(data);
    const coreColor = palette.core;
    const eventColor = renderer.eventColor;

    gl.disable(gl.BLEND);
    gl.useProgram(renderer.backgroundProgram);
    gl.bindBuffer(gl.ARRAY_BUFFER, renderer.quadBuffer);
    gl.enableVertexAttribArray(renderer.background.position);
    gl.vertexAttribPointer(renderer.background.position, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(renderer.background.resolution, size.bufferWidth, size.bufferHeight);
    gl.uniform1f(renderer.background.time, renderer.visualTime);
    gl.uniform1f(renderer.background.intensity, intensity);
    gl.uniform1f(renderer.background.decade, decade);
    gl.uniform1f(renderer.background.fifty, fifty);
    gl.uniform1f(renderer.background.century, century);
    gl.uniform1f(renderer.background.eventAge, eventAge);
    gl.uniform1f(renderer.background.eventStrength, renderer.eventStrength);
    gl.uniform1f(renderer.background.failure, failure);
    gl.uniform1f(renderer.background.quality, renderer.quality);
    gl.uniform1f(renderer.background.paused, paused ? 1 : 0);
    gl.uniform3f(renderer.background.coreColor, coreColor[0], coreColor[1], coreColor[2]);
    gl.uniform3f(renderer.background.eventColor, eventColor[0], eventColor[1], eventColor[2]);
    gl.uniform3f(renderer.background.paletteRed, palette.red[0], palette.red[1], palette.red[2]);
    gl.uniform3f(renderer.background.paletteYellow, palette.yellow[0], palette.yellow[1], palette.yellow[2]);
    gl.uniform3f(renderer.background.paletteGreen, palette.green[0], palette.green[1], palette.green[2]);
    gl.uniform3f(renderer.background.paletteBlue, palette.blue[0], palette.blue[1], palette.blue[2]);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

    const particleValues = buildSingularityParticles(renderer, eventAge, size.width, size.height);
    if (particleValues.length) {
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE);
      gl.useProgram(renderer.particleProgram);
      gl.bindBuffer(gl.ARRAY_BUFFER, renderer.particleBuffer);
      if (particleValues.length > renderer.particleBufferCapacity) {
        let nextCapacity = renderer.particleBufferCapacity;
        while (nextCapacity < particleValues.length) nextCapacity *= 2;
        renderer.particleBufferCapacity = nextCapacity;
        renderer.particleUpload = new Float32Array(nextCapacity);
        gl.bufferData(gl.ARRAY_BUFFER, nextCapacity * 4, gl.DYNAMIC_DRAW);
      }
      renderer.particleUpload.set(particleValues, 0);
      gl.bufferSubData(
        gl.ARRAY_BUFFER,
        0,
        renderer.particleUpload.subarray(0, particleValues.length),
      );
      const stride = 9 * 4;
      gl.enableVertexAttribArray(renderer.particles.position);
      gl.vertexAttribPointer(renderer.particles.position, 2, gl.FLOAT, false, stride, 0);
      gl.enableVertexAttribArray(renderer.particles.size);
      gl.vertexAttribPointer(renderer.particles.size, 1, gl.FLOAT, false, stride, 2 * 4);
      gl.enableVertexAttribArray(renderer.particles.angle);
      gl.vertexAttribPointer(renderer.particles.angle, 1, gl.FLOAT, false, stride, 3 * 4);
      gl.enableVertexAttribArray(renderer.particles.stretch);
      gl.vertexAttribPointer(renderer.particles.stretch, 1, gl.FLOAT, false, stride, 4 * 4);
      gl.enableVertexAttribArray(renderer.particles.color);
      gl.vertexAttribPointer(renderer.particles.color, 4, gl.FLOAT, false, stride, 5 * 4);
      gl.uniform2f(renderer.particles.resolution, size.width, size.height);
      gl.uniform1f(renderer.particles.pixelRatio, size.pixelRatio);
      gl.drawArrays(gl.POINTS, 0, particleValues.length / 9);
    }

    if (renderer.running && !paused) {
      renderer.frameId = window.requestAnimationFrame((nextTimestamp) => drawSingularityFrame(renderer, nextTimestamp));
    } else {
      renderer.running = false;
    }
  }

  function syncSingularityEvent(renderer, data) {
    const nonce = Number(data?.eventNonce || 0);
    if (renderer.lastEventNonce === null) {
      renderer.lastEventNonce = nonce;
      return;
    }
    if (nonce === renderer.lastEventNonce) return;
    renderer.lastEventNonce = nonce;
    renderer.eventStartAt = performance.now() / 1000;
    renderer.eventType = String(data?.lastEventType || "");
    renderer.eventColor = singularityEventColor(data);
    renderer.eventSourceStreak = Math.max(Number(data?.streak || 0), Number(state.prevStreak || 0));
    const streak = Math.max(0, Number(data?.streak || 0));
    renderer.eventStrength = streak > 0 && streak % 50 === 0
      ? 3
      : streak > 0 && streak % 10 === 0
        ? 2
        : 1;
    if (["again", "timeout", "reset"].includes(renderer.eventType)) {
      renderer.eventStrength = Math.max(2, Math.min(4, 1 + Math.floor(renderer.eventSourceStreak / 50)));
      renderer.eventColor = [1.0, 0.12, 0.24];
    }
  }

  function renderSingularity(data) {
    if (document.hidden) {
      stopSingularityRenderer();
      return;
    }
    const renderer = ensureSingularityRenderer();
    if (!renderer) return;
    const streak = Math.max(0, Number(data?.streak || 0));
    const quality = singularityQuality(data);
    if (renderer.quality !== quality) {
      renderer.quality = quality;
      renderer.needsResize = true;
    }
    renderer.data = data;
    syncSingularityEvent(renderer, data);
    setText("acgSingularityStreak", String(streak));
    const sidebar = $("speed-streak-sidebar");
    if (sidebar) sidebar.dataset.singularityCentury = String(Math.floor(streak / 100));
    if (!renderer.running) {
      renderer.running = true;
      renderer.lastFrameAt = 0;
      renderer.frameId = window.requestAnimationFrame((timestamp) => drawSingularityFrame(renderer, timestamp));
    }
  }

  function stopSingularityRenderer() {
    const renderer = state.singularityWebgl;
    if (!renderer) return;
    renderer.running = false;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    renderer.lastFrameAt = 0;
  }

  function disposeSingularityRenderer(renderer = state.singularityWebgl, deleteResources = true) {
    if (!renderer) return;
    renderer.running = false;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    renderer.resizeObserver?.disconnect?.();
    renderer.resizeObserver = null;
    if (renderer.contextLostHandler) {
      renderer.canvas.removeEventListener("webglcontextlost", renderer.contextLostHandler, false);
    }
    if (renderer.contextRestoredHandler) {
      renderer.canvas.removeEventListener("webglcontextrestored", renderer.contextRestoredHandler, false);
    }
    if (deleteResources && !renderer.contextLost) {
      try {
        renderer.gl.deleteBuffer(renderer.quadBuffer);
        renderer.gl.deleteBuffer(renderer.particleBuffer);
        renderer.gl.deleteProgram(renderer.backgroundProgram);
        renderer.gl.deleteProgram(renderer.particleProgram);
      } catch (_error) {}
    }
    renderer.data = null;
    renderer.particleValues.length = 0;
    renderer.particleUpload = null;
    if (state.singularityWebgl === renderer) {
      state.singularityWebgl = null;
    }
  }

  function syncSingularityDocumentVisibility() {
    if (document.hidden) {
      stopSingularityRenderer();
      return;
    }
    if (state.data && isSingularityMode(state.data)) {
      renderSingularity(state.data);
    }
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
      crystal: crystalRgb(palette.crystal),
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
    if (canvas && mode === "crystal") {
      canvas.style.inset = "";
      canvas.style.left = "";
      canvas.style.top = "";
      canvas.style.width = "";
      canvas.style.height = "";
      canvas.style.transform = "";
    }
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
        visualTime: performance.now() / 1000,
        lastFrameAt: 0,
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

  function fixedCrystalSheenPalette(_data) {
    const iceBase = crystalRgb("#566ed4");
    return [
      mixCrystalRgb(iceBase, [0.94, 0.99, 1.0, 1], 0.78),
      mixCrystalRgb(iceBase, [0.57, 0.88, 0.96, 1], 0.72),
      mixCrystalRgb(iceBase, [0.67, 0.61, 1.0, 1], 0.76),
      mixCrystalRgb(iceBase, [0.38, 0.30, 0.78, 1], 0.72),
      mixCrystalRgb(iceBase, [0.16, 0.12, 0.39, 1], 0.66),
    ];
  }

  function coloredCrystalFacetPalette(baseColor) {
    return [
      mixCrystalRgb(baseColor, [1.0, 1.0, 1.0, 1], 0.76),
      mixCrystalRgb(baseColor, [1.0, 1.0, 1.0, 1], 0.38),
      mixCrystalRgb(baseColor, [0.72, 0.82, 0.94, 1], 0.12),
      mixCrystalRgb(baseColor, [0.0, 0.0, 0.0, 1], 0.28),
      mixCrystalRgb(baseColor, [0.0, 0.0, 0.0, 1], 0.56),
    ];
  }

  function usesDefaultCrystalAppearance(data) {
    const colorMode = getCrystalColorMode(data);
    if (colorMode === "ice") return true;
    return colorMode === "core" && !normalizeCustomColors(data?.customColors || {}).crystal;
  }

  function crystalFacetPaletteForComponent(index, colors, data, icePalette) {
    const colorMode = getCrystalColorMode(data);
    if (usesDefaultCrystalAppearance(data)) return icePalette;
    const theme = crystalPalette(data);
    const baseColor = colorMode === "answer"
      ? crystalRatingRgb(colors[index] || data?.lastSatelliteColor || "blue", theme)
      : theme.crystal;
    return coloredCrystalFacetPalette(baseColor);
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

  function buildCrystalClusterVertices(count, colors, data) {
    const value = Math.max(0, Math.floor(Number(count || 0)));
    const camera = crystalCameraForCount(value);
    const icePalette = fixedCrystalSheenPalette(data);
    const colorMode = getCrystalColorMode(data);
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
      const palette = crystalFacetPaletteForComponent(index, colors, data, icePalette);
      const paletteOffset = (ordinal + (ringIndex * 2)) % palette.length;
      const fresh = index === value - 1 ? 1 : 0;

      if (newestBeyondBaseline) {
        const glowScale = 1.62;
        const glowPoint = (point) => [
          center[0] + ((point[0] - center[0]) * glowScale),
          center[1] + ((point[1] - center[1]) * glowScale),
        ];
        const glowColor = usesDefaultCrystalAppearance(data)
          ? [0.55, 0.78, 1, 0.16]
          : [palette[0][0], palette[0][1], palette[0][2], 0.16];
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
    const colorMode = getCrystalColorMode(data);
    const icePalette = fixedCrystalSheenPalette(data);
    const coreBase = colorMode === "core"
      ? palette.crystal
      : colorMode === "ice" ? crystalRgb("#566ed4") : palette.core;
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
      const ratingA = colorMode === "core"
        ? palette.crystal
        : colorMode === "ice"
          ? icePalette[(side + 1) % icePalette.length]
          : colors.length ? crystalRatingRgb(colors[(side * 17) % colors.length], palette) : palette.blue;
      const ratingB = colorMode === "core"
        ? palette.crystal
        : colorMode === "ice"
          ? icePalette[(side + 3) % icePalette.length]
          : colors.length ? crystalRatingRgb(colors[((side * 17) + 7) % colors.length], palette) : palette.green;
      const topColor = mixCrystalRgb(coreBase, ratingA, 0.42);
      const bottomColor = mixCrystalRgb(coreBase, ratingB, 0.58);
      const seed = crystalHash(side * 7.13 + streak);
      appendCrystalTriangle(values, top, waistA, waistB, topColor, seed);
      appendCrystalTriangle(values, bottom, waistB, waistA, bottomColor, seed);
    }
    return new Float32Array(values);
  }

  function uploadCrystalScene(renderer, colors, data, signature) {
    const componentCount = Math.max(0, Number(data?.streak || colors.length));
    const cluster = buildCrystalClusterVertices(componentCount, colors, data);
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
    const colorMode = getCrystalColorMode(data);
    setText("acgCrystalStreak", String(streak));
    if (scene) {
      scene.dataset.motion = rotationEnabled ? "rotating" : "still";
      scene.dataset.colorMode = colorMode;
      scene.dataset.growthEra = String(streak > 50 ? Math.floor((streak - 1) / 50) : 0);
      scene.dataset.eraProgress = String(streak > 50 ? ((streak - 1) % 50) + 1 : streak);
    }

    const renderer = ensureCrystalRenderer();
    scene?.classList.toggle("no-webgl", !renderer);
    scene?.classList.toggle("webgl-ready", Boolean(renderer));
    if (!renderer) return;
    const answerColorSignature = colorMode === "answer" ? colors.join(",") : "";
    const signature = `${streak}|${colorMode}|${answerColorSignature}|${data?.appearanceMode || "midnight"}|${JSON.stringify(data?.customColors || {})}`;
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
    const motionSuspended = visualMotionSuspended();
    const nowSeconds = Number(timestamp || performance.now()) / 1000;
    if (!motionSuspended && renderer.lastFrameAt > 0) {
      renderer.visualTime += clamp(nowSeconds - renderer.lastFrameAt, 0, 0.08);
    }
    renderer.lastFrameAt = nowSeconds;
    const { width, height, bufferWidth, bufferHeight } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    const pulse = clamp(1 - ((timestamp - renderer.pulseStartedAt) / 700), 0, 1);
    const decadeLock = clamp(1 - ((timestamp - renderer.decadeLockStartedAt) / 760), 0, 1);
    const eraIgnition = clamp(1 - ((timestamp - renderer.eraIgnitionStartedAt) / 1260), 0, 1);
    const milestone = clamp(1 - ((timestamp - renderer.milestoneStartedAt) / 1480), 0, 1);
    const growthProgress = clamp((timestamp - renderer.growthStartedAt) / 520, 0, 1);
    const growth = 1 - Math.pow(1 - growthProgress, 3);
    const visualPulse = clamp(pulse + (decadeLock * 0.18) + (eraIgnition * 0.3) + (milestone * 0.46), 0, 1);
    const rotationEnabled = isCrystalRotationEnabled(state.data) && !motionSuspended;
    const rotation = isCrystalRotationEnabled(state.data) ? renderer.visualTime * 0.16 : 0;
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
      gl.uniform1f(renderer.timeLocation, isCrystalRotationEnabled(state.data) ? renderer.visualTime : 0);
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
    if (rotationEnabled || (!motionSuspended && reactionActive) || renderer.needsDraw) {
      renderer.frameId = window.requestAnimationFrame((nextTimestamp) => drawCrystalFrame(renderer, nextTimestamp));
    } else {
      renderer.running = false;
      renderer.frameId = 0;
      renderer.lastFrameAt = 0;
    }
  }

  function stopCrystalReactor() {
    const renderer = state.crystalWebgl;
    if (!renderer) return;
    renderer.running = false;
    renderer.lastFrameAt = 0;
    renderer.needsDraw = true;
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    try {
      renderer.gl.clearColor(0, 0, 0, 0);
      renderer.gl.clear(renderer.gl.COLOR_BUFFER_BIT | renderer.gl.DEPTH_BUFFER_BIT);
    } catch (_error) {}
  }

  function scheduleVisualViewportRedraw() {
    if (state.visualResizeFrame) return;
    state.visualResizeFrame = window.requestAnimationFrame(() => {
      state.visualResizeFrame = 0;
      const data = state.data || {};
      if (
        !data.enabled
        || !data.visualsEnabled
        || data.sidebarCollapsed
        || !Boolean(data.orbitAnimationEnabled ?? true)
        || getVisualMode(data) !== "sphere"
      ) {
        return;
      }
      const colors = Array.isArray(data.satelliteColors) ? data.satelliteColors : [];
      renderRings(colors, data);
    });
  }

  function updateSceneMetrics({ field, scene, disc, colorsLength, ringCount, requiredSize, minScale = 0.42, classicSizing = false }) {
    const bounds = field.getBoundingClientRect();
    const available = Math.max(classicSizing ? 180 : 80, Math.min(bounds.width || 220, bounds.height || 220) - 10);
    const sceneScale = clamp(available / requiredSize, minScale, 1);
    scene.style.setProperty("--scene-size", `${requiredSize}px`);
    scene.style.setProperty("--scene-scale", `${sceneScale}`);
    const coreBasePixels = clamp(58 + (colorsLength * 2.8), 58, 142);
    const minimumReadableCorePixels = 68;
    const projectedCorePixels = coreBasePixels * sceneScale;
    const coreReadableScale = classicSizing
      ? 1
      : projectedCorePixels > 0
        ? Math.max(1, minimumReadableCorePixels / projectedCorePixels)
        : 1;
    scene.style.setProperty("--core-readable-scale", `${coreReadableScale}`);
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
    return { bounds, sceneScale };
  }

  function configureWebglOrbitViewport(renderer, canvas, bounds, sceneScale) {
    if (!renderer || !canvas) return;
    const scale = clamp(Number(sceneScale || 1), 0.02, 1);
    const cssWidth = Math.max(1, Number(bounds?.width || 1) / scale);
    const cssHeight = Math.max(1, Number(bounds?.height || 1) / scale);
    const nextWidth = `${cssWidth}px`;
    const nextHeight = `${cssHeight}px`;
    const layoutChanged = canvas.style.width !== nextWidth
      || canvas.style.height !== nextHeight
      || renderer.bufferScale !== scale;
    canvas.style.inset = "auto";
    canvas.style.left = "50%";
    canvas.style.top = "50%";
    canvas.style.width = nextWidth;
    canvas.style.height = nextHeight;
    canvas.style.transform = "translate(-50%, -50%)";
    renderer.bufferScale = scale;
    if (layoutChanged) renderer.needsResize = true;
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
        minScale: 0.42,
        classicSizing: true,
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
      minScale: 0.42,
      classicSizing: true,
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

  function buildMilestoneRingsMarkup(colors, completedRingCount, previousRingCount) {
    let html = "";
    for (let ringIndex = 0; ringIndex < completedRingCount; ringIndex += 1) {
      const ringColors = colors.slice(
        ringIndex * MILESTONE_RING_CARDS,
        (ringIndex + 1) * MILESTONE_RING_CARDS,
      );
      const radius = milestoneRingRadius(ringIndex, completedRingCount);
      const size = radius * 2;
      const newest = ringIndex === completedRingCount - 1 && completedRingCount > previousRingCount;
      const major = (ringIndex + 1) % 5 === 0;
      const apex = (ringIndex + 1) % 10 === 0;
      const direction = ringIndex % 2 === 0 ? " clockwise" : " counterclockwise";
      const classes = `${direction}${newest ? " unlocking" : ""}${major ? " major" : ""}${apex ? " apex" : ""}`;
      const gradient = buildBankGradient(ringColors);
      const spinDuration = Math.min(48, 31 + (ringIndex * 1.7));
      html += `<div class="acg-milestone-ring-glow${classes}" data-milestone-ring="${ringIndex}" style="width:${size}px;height:${size}px;--milestone-gradient:${gradient};--milestone-spin-duration:${spinDuration}s;"></div>`;
      html += `<div class="acg-milestone-ring${classes}" data-milestone-ring="${ringIndex}" style="width:${size}px;height:${size}px;--milestone-gradient:${gradient};--milestone-number:${ringIndex + 1};--milestone-spin-duration:${spinDuration}s;"></div>`;
    }
    return html;
  }

  function syncMilestoneLiveTrack(ringsNode, completedRingCount, liveCount) {
    ringsNode.querySelectorAll(".acg-fusion-live-ring").forEach((node) => node.remove());
    let track = ringsNode.querySelector(".acg-milestone-live-track");
    if (liveCount <= 0) {
      track?.remove();
      return;
    }
    if (!track) {
      track = document.createElement("div");
      track.className = "acg-milestone-live-track";
      ringsNode.appendChild(track);
    }
    const liveRadius = milestoneLiveRadius(completedRingCount);
    const liveSize = liveRadius * 2;
    track.style.width = `${liveSize}px`;
    track.style.height = `${liveSize}px`;
    track.style.setProperty("--milestone-progress", String(liveCount / MILESTONE_RING_CARDS));
  }

  function syncFusionLiveRows(ringsNode, completedRingCount, liveCount) {
    ringsNode.querySelector(".acg-milestone-live-track")?.remove();
    ringsNode.querySelectorAll(".acg-fusion-live-ring").forEach((node) => node.remove());
    const liveRowCount = Math.ceil(liveCount / 10);
    for (let rowIndex = 0; rowIndex < liveRowCount; rowIndex += 1) {
      const radius = fusionLiveRowRadius(completedRingCount, rowIndex);
      const row = document.createElement("div");
      row.className = "acg-fusion-live-ring";
      row.style.width = `${radius * 2}px`;
      row.style.height = `${radius * 2}px`;
      ringsNode.appendChild(row);
    }
  }

  function syncMilestoneLiveGuides(ringsNode, sphereMode, completedRingCount, liveCount) {
    if (sphereMode === "fusion") {
      syncFusionLiveRows(ringsNode, completedRingCount, liveCount);
    } else {
      syncMilestoneLiveTrack(ringsNode, completedRingCount, liveCount);
    }
  }

  function renderMilestoneOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature, sphereMode) {
    const completedRingCount = Math.floor(colors.length / MILESTONE_RING_CARDS);
    const liveColors = colors.slice(completedRingCount * MILESTONE_RING_CARDS);
    const outerRadius = sphereMode === "fusion"
      ? fusionOuterRadius(completedRingCount, liveColors.length)
      : milestoneOuterRadius(completedRingCount, liveColors.length);
    const requiredSize = (outerRadius * 2) + 104;
    const sameCompletedRings = state.lastColorsSignature.includes(`|${sphereMode}|`)
      && completedRingCount === state.lastRingCount;
    if (!sameCompletedRings) {
      const previousRingCount = state.lastColorsSignature.includes(`|${sphereMode}|`) ? state.lastRingCount : 0;
      ringsNode.innerHTML = buildMilestoneRingsMarkup(colors, completedRingCount, previousRingCount);
    }
    syncMilestoneLiveGuides(ringsNode, sphereMode, completedRingCount, liveColors.length);

    let satellitesHtml = "";
    if (liveColors.length) {
      const satellites = sphereMode === "fusion"
        ? buildFusionLiveSatellites(liveColors, completedRingCount)
        : buildWebglSatellites(colors, { ...state.data, sphereMode: "milestone" });
      satellites.forEach((satellite) => {
        satellitesHtml += `<div class="acg-satellite ${satellite.color}" style="--angle:${satellite.angle}deg;--radius:${satellite.radius}px;--orbit-duration:${satellite.duration}s;"></div>`;
      });
    }
    satellitesNode.innerHTML = satellitesHtml;
    updateSceneMetrics({
      field,
      scene,
      disc,
      colorsLength: colors.length,
      ringCount: completedRingCount,
      requiredSize,
      minScale: 0.10,
    });
    state.lastColorsSignature = signature;
    state.lastRingCount = completedRingCount;
  }

  function renderWebglOrbit(colors, ringsNode, satellitesNode, field, scene, disc, data, signature) {
    const renderer = ensureWebglRenderer();
    if (!renderer) {
      $("speed-streak-sidebar")?.classList.remove("webgl-orbit");
      if (isMilestoneRingMode(getSphereMode(data))) {
        renderMilestoneOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature, getSphereMode(data));
      } else if (getSphereMode(data) === "consolidate") {
        renderConsolidatedOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature);
      } else {
        renderClassicOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature);
      }
      return;
    }

    const sphereMode = getSphereMode(data);
    const ringCount = isMilestoneRingMode(sphereMode)
      ? Math.floor(colors.length / MILESTONE_RING_CARDS)
      : sphereMode === "consolidate"
        ? Math.floor(colors.length / 10)
        : Math.max(1, Math.ceil(colors.length / 10));

    const satellites = buildWebglSatellites(colors, data);
    uploadWebglSatellites(renderer, satellites, signature);
    satellitesNode.innerHTML = "";

    if (isMilestoneRingMode(sphereMode)) {
      const sameCompletedRings = state.lastColorsSignature.includes(`|${sphereMode}|`)
        && ringCount === state.lastRingCount;
      const liveCount = colors.length - (ringCount * MILESTONE_RING_CARDS);
      if (!sameCompletedRings) {
        const previousRingCount = state.lastColorsSignature.includes(`|${sphereMode}|`) ? state.lastRingCount : 0;
        ringsNode.innerHTML = buildMilestoneRingsMarkup(colors, ringCount, previousRingCount);
      }
      syncMilestoneLiveGuides(ringsNode, sphereMode, ringCount, liveCount);
      state.lastColorsSignature = signature;
      state.lastRingCount = ringCount;
    } else if (signature !== state.lastColorsSignature || ringCount !== state.lastRingCount) {
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

    const liveCount = colors.length - (ringCount * MILESTONE_RING_CARDS);
    const outerRadius = sphereMode === "fusion"
      ? fusionOuterRadius(ringCount, liveCount)
      : sphereMode === "milestone"
        ? milestoneOuterRadius(ringCount, liveCount)
      : sphereMode === "consolidate"
        ? (renderer.satelliteCount
          ? consolidatedLiveRadius(ringCount)
          : (ringCount > 0 ? consolidatedBankRadius(ringCount - 1, ringCount) : 92))
        : (78 + (Math.max(0, ringCount - 1) * 26));
    const requiredSize = isMilestoneRingMode(sphereMode)
      ? (outerRadius * 2) + 104
      : sphereMode === "consolidate"
        ? (outerRadius * 2) + 88
        : (Math.max(1, ringCount) * 52) + 150;
    const sceneMetrics = updateSceneMetrics({
      field,
      scene,
      disc,
      colorsLength: colors.length,
      ringCount,
      requiredSize,
      minScale: sphereMode === "classic" ? 0.42 : sphereMode === "consolidate" ? 0.14 : 0.10,
      classicSizing: sphereMode === "classic",
    });
    configureWebglOrbitViewport(renderer, renderer.canvas, sceneMetrics.bounds, sceneMetrics.sceneScale);

    const shouldAnimate = shouldAnimateWebglOrbit(renderer);
    if (!shouldAnimate && renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    if (!renderer.running || !shouldAnimate) {
      renderer.running = true;
      drawWebglFrame(renderer);
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
    if (isMilestoneRingMode(sphereMode)) {
      renderMilestoneOrbit(colors, ringsNode, satellitesNode, field, scene, disc, signature, sphereMode);
      return;
    }
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

  function spawnFusionSatelliteArrival(color) {
    window.requestAnimationFrame(() => {
      const renderer = state.webgl;
      const fx = $("acgFx");
      const satellite = renderer?.satellites?.at(-1);
      if (!renderer || !fx || !satellite) return;
      const theta = ((satellite.angle * Math.PI) / 180)
        + (renderer.visualTime * ((Math.PI * 2) / satellite.duration));
      const wave = document.createElement("div");
      wave.className = `acg-shockwave acg-satellite-arrival-wave ${color || "blue"}`;
      wave.style.left = `calc(50% + ${Math.cos(theta) * satellite.radius}px)`;
      wave.style.top = `calc(50% + ${Math.sin(theta) * satellite.radius}px)`;
      fx.appendChild(wave);
      window.setTimeout(() => wave.remove(), 760);
    });
  }

  function cssRotationDegrees(node) {
    if (!node) return 0;
    try {
      const transform = window.getComputedStyle(node).transform;
      if (!transform || transform === "none") return 0;
      const matrix = new DOMMatrixReadOnly(transform);
      return Math.atan2(matrix.b, matrix.a) * 180 / Math.PI;
    } catch (_error) {
      return 0;
    }
  }

  function triggerFusionDemolition(colors) {
    const fx = $("acgFx");
    const sidebar = $("speed-streak-sidebar");
    if (!fx || !sidebar || !colors.length) return;
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (reducedMotion || document.hidden || state.settingsOpen) {
      return;
    }
    const completedRingCount = Math.floor(colors.length / MILESTONE_RING_CARDS);
    const liveColors = colors.slice(completedRingCount * MILESTONE_RING_CARDS);
    const liveSatellites = buildFusionLiveSatellites(liveColors, completedRingCount);
    const liveRowCount = Math.ceil(liveSatellites.length / 10);
    const satelliteWaveDuration = Math.max(0, liveRowCount - 1) * 50;
    const ringStep = completedRingCount > 1
      ? Math.max(6, Math.min(62, 720 / (completedRingCount - 1)))
      : 62;
    const ringCollapseBase = liveSatellites.length ? satelliteWaveDuration + 760 : 240;
    const cleanupDelay = ringCollapseBase + (Math.max(0, completedRingCount - 1) * ringStep) + 680;
    const originalRings = $("acgRings");
    const ringTrajectories = Array.from({ length: completedRingCount }, (_, ringIndex) => {
      const original = originalRings?.querySelector(`.acg-milestone-ring[data-milestone-ring="${ringIndex}"]`);
      const direction = original?.classList.contains("counterclockwise") ? -1 : 1;
      const spinDurationSeconds = Math.min(48, 31 + (ringIndex * 1.7));
      return {
        startAngle: cssRotationDegrees(original),
        turn: direction * 360 * (cleanupDelay / 1000) / spinDurationSeconds,
      };
    });

    window.clearTimeout(state.fusionDemolitionTimer);
    window.clearTimeout(state.fusionCenterResetTimer);
    fx.querySelectorAll(".acg-fusion-demolition").forEach((node) => node.remove());
    state.fusionDemolitionActive = true;
    sidebar.classList.remove("fusion-demolition-active");
    sidebar.classList.remove("fusion-center-resetting");
    void sidebar.offsetWidth;
    sidebar.classList.add("fusion-demolition-active");
    if (state.webgl && liveSatellites.length) {
      uploadFusionDebris(state.webgl);
      state.webgl.demolitionStartedAt = performance.now();
      state.webgl.demolitionComplete = false;
      state.webgl.running = true;
      if (!state.webgl.frameId) {
        state.webgl.frameId = window.requestAnimationFrame((timestamp) => drawWebglFrame(state.webgl, timestamp));
      }
    }

    for (let ringIndex = completedRingCount - 1; ringIndex >= 0; ringIndex -= 1) {
      const ringColors = colors.slice(
        ringIndex * MILESTONE_RING_CARDS,
        (ringIndex + 1) * MILESTONE_RING_CARDS,
      );
      const radius = milestoneRingRadius(ringIndex, completedRingCount);
      const delay = ringCollapseBase + ((completedRingCount - 1 - ringIndex) * ringStep);
      const ringTrack = document.createElement("span");
      const ring = document.createElement("span");
      const trajectory = ringTrajectories[ringIndex] || { startAngle: 0, turn: 0 };
      ringTrack.className = "acg-fusion-demolition acg-fusion-demolition-ring-track";
      ringTrack.style.width = `${radius * 2}px`;
      ringTrack.style.height = `${radius * 2}px`;
      ringTrack.style.setProperty("--ring-start-angle", `${trajectory.startAngle}deg`);
      ringTrack.style.setProperty("--ring-end-angle", `${trajectory.startAngle + trajectory.turn}deg`);
      ringTrack.style.setProperty("--ring-trajectory-duration", `${cleanupDelay}ms`);
      ring.className = "acg-fusion-demolition-ring";
      ring.style.setProperty("--milestone-gradient", buildBankGradient(ringColors));
      ring.style.setProperty("--demolition-delay", `${delay}ms`);
      ringTrack.appendChild(ring);
      fx.appendChild(ringTrack);
      for (let trailIndex = 0; trailIndex < 3; trailIndex += 1) {
        const trail = document.createElement("span");
        trail.className = "acg-fusion-demolition acg-fusion-collapse-trail";
        trail.style.setProperty("--collapse-angle", `${(trailIndex * 120) + ((ringIndex * 29) % 47)}deg`);
        trail.style.setProperty("--collapse-radius", `${radius}px`);
        trail.style.setProperty("--demolition-delay", `${delay + 70 + (trailIndex * 22)}ms`);
        fx.appendChild(trail);
      }
    }

    state.fusionDemolitionTimer = window.setTimeout(() => {
      fx.querySelectorAll(".acg-fusion-demolition").forEach((node) => node.remove());
      sidebar.classList.remove("fusion-demolition-active");
      sidebar.classList.add("fusion-center-resetting");
      state.fusionDemolitionActive = false;
      if (state.webgl) state.webgl.demolitionComplete = false;
      state.fusionDemolitionTimer = 0;
      if (state.data) render(state.data);
      state.fusionCenterResetTimer = window.setTimeout(() => {
        sidebar.classList.remove("fusion-center-resetting");
        state.fusionCenterResetTimer = 0;
      }, 360);
    }, cleanupDelay);
  }

  function spawnMilestoneFlare(emphasis = "") {
    const fx = $("acgFx");
    if (!fx) return;
    const flare = document.createElement("div");
    flare.className = `acg-milestone-flare${emphasis ? ` ${emphasis}` : ""}`;
    fx.appendChild(flare);
    setTimeout(() => flare.remove(), emphasis ? 1650 : 1200);
  }

  function chargeTransferScene(data) {
    if (isSingularityMode(data)) {
      return $("acgSingularityScene");
    }
    if (isCrystalReactorMode(data)) {
      return $("acgCrystalScene");
    }
    if (isLightweightRowsMode(data)) {
      return $("acgRowsScene");
    }
    return $("acgScene");
  }

  function chargeTransferVisualAnchor(data) {
    if (isSingularityMode(data)) {
      return $("acgSingularityScene");
    }
    if (isCrystalReactorMode(data)) {
      return $("acgCrystalScene");
    }
    if (isLightweightRowsMode(data)) {
      return $("acgRowsStreakValue") || $("acgRowsScene");
    }
    return $("acgCore") || $("acgScene");
  }

  function chargeTransferBankTarget(direction) {
    const bank = $("acgBoostCharges");
    if (!bank) return null;
    const slots = Array.from(bank.querySelectorAll(".acg-boost-charge-slot"));
    const matchingSlots = slots.filter((slot) => (
      direction === "earned" ? slot.classList.contains("filled") : slot.classList.contains("empty")
    ));
    return (direction === "earned" ? matchingSlots.at(-1) : matchingSlots[0]) || bank;
  }

  function chargeTransferOcclusionRadius(data, fieldRect) {
    const minSize = Math.min(fieldRect.width, fieldRect.height);
    if (isSingularityMode(data)) {
      const streak = Math.max(0, Number(data?.streak || 0));
      const decade = Math.floor(streak / 10);
      const fifty = Math.floor(streak / 50);
      const century = Math.floor(streak / 100);
      const coreRadius = minSize * (
        0.075
        + Math.min(decade, 12) * 0.0017
        + Math.min(fifty, 5) * 0.0035
        + Math.min(century, 4) * 0.0045
      );
      return clamp(coreRadius + (minSize * 0.045) + 5, 40, 64);
    }
    if (isCrystalReactorMode(data)) {
      const streak = Math.max(0, Number(data?.streak || 0));
      return clamp(50 + (Math.log2(streak + 1) * 3.8), 52, 84);
    }
    return 0;
  }

  function spawnChargeTransfer(data, direction) {
    const sidebar = $("speed-streak-sidebar");
    const timerBound = direction === "spent";
    const scene = timerBound ? sidebar : chargeTransferScene(data);
    const visualAnchor = timerBound ? $("acgTimerHero") : chargeTransferVisualAnchor(data);
    const bankTarget = chargeTransferBankTarget(direction);
    if (!sidebar || !scene || !visualAnchor || !bankTarget || !Boolean(data?.visualsEnabled)) return;

    sidebar.querySelector(".acg-charge-transfer")?.remove();
    const sceneRect = scene.getBoundingClientRect();
    const anchorRect = visualAnchor.getBoundingClientRect();
    const bankRect = bankTarget.getBoundingClientRect();
    if (!sceneRect.width || !sceneRect.height || !anchorRect.width || !bankRect.width) return;

    const scaleX = sceneRect.width / Math.max(1, scene.offsetWidth || sceneRect.width);
    const scaleY = sceneRect.height / Math.max(1, scene.offsetHeight || sceneRect.height);
    const toScenePoint = (rect) => ({
      x: ((rect.left + rect.width / 2) - sceneRect.left) / Math.max(0.01, scaleX),
      y: ((rect.top + rect.height / 2) - sceneRect.top) / Math.max(0.01, scaleY),
    });
    const visualPoint = toScenePoint(anchorRect);
    const bankPoint = toScenePoint(bankRect);
    const source = direction === "earned" ? visualPoint : bankPoint;
    const destination = direction === "earned" ? bankPoint : visualPoint;
    const fieldRect = $("acgField")?.getBoundingClientRect() || sceneRect;
    const visualDiameter = clamp(Math.min(fieldRect.width, fieldRect.height) * 0.82, 116, 238);
    const startDiameter = direction === "earned" ? visualDiameter : 54;
    const endDiameter = direction === "earned" ? 15 : 78;
    const averageScale = Math.max(0.01, (scaleX + scaleY) / 2);
    const startSize = startDiameter / averageScale;
    const routePadding = Math.max((startSize / 2) + (34 / averageScale), 72 / averageScale);
    const sceneWidth = Math.max(1, scene.offsetWidth || (sceneRect.width / Math.max(0.01, scaleX)));
    const sceneHeight = Math.max(1, scene.offsetHeight || (sceneRect.height / Math.max(0.01, scaleY)));
    const transferLeft = Math.min(0, source.x - routePadding, destination.x - routePadding);
    const transferTop = Math.min(0, source.y - routePadding, destination.y - routePadding);
    const transferRight = Math.max(sceneWidth, source.x + routePadding, destination.x + routePadding);
    const transferBottom = Math.max(sceneHeight, source.y + routePadding, destination.y + routePadding);
    const transferSource = { x: source.x - transferLeft, y: source.y - transferTop };
    const transferVisual = { x: visualPoint.x - transferLeft, y: visualPoint.y - transferTop };

    const transfer = document.createElement("div");
    transfer.className = `acg-charge-transfer ${direction}${timerBound ? " timer-bound" : ""}`;
    transfer.setAttribute("aria-hidden", "true");
    transfer.style.inset = "auto";
    transfer.style.left = `${transferLeft}px`;
    transfer.style.top = `${transferTop}px`;
    transfer.style.width = `${transferRight - transferLeft}px`;
    transfer.style.height = `${transferBottom - transferTop}px`;
    transfer.style.setProperty("--charge-start-x", `${transferSource.x}px`);
    transfer.style.setProperty("--charge-start-y", `${transferSource.y}px`);
    transfer.style.setProperty("--charge-dx", `${destination.x - source.x}px`);
    transfer.style.setProperty("--charge-dy", `${destination.y - source.y}px`);
    transfer.style.setProperty("--charge-start-size", `${startSize}px`);
    transfer.style.setProperty("--charge-end-scale", `${endDiameter / startDiameter}`);

    const occlusionRadius = chargeTransferOcclusionRadius(data, fieldRect) / averageScale;
    if (!timerBound && occlusionRadius > 0) {
      transfer.classList.add("center-occluded");
      transfer.style.setProperty("--charge-visual-x", `${transferVisual.x}px`);
      transfer.style.setProperty("--charge-visual-y", `${transferVisual.y}px`);
      transfer.style.setProperty("--charge-occlusion-inner", `${occlusionRadius * 0.76}px`);
      transfer.style.setProperty("--charge-occlusion-middle", `${occlusionRadius * 0.9}px`);
      transfer.style.setProperty("--charge-occlusion-outer", `${occlusionRadius}px`);
    }

    for (const ringClass of ["primary", "echo"]) {
      const ring = document.createElement("span");
      ring.className = `acg-charge-transfer-ring ${ringClass}`;
      transfer.appendChild(ring);
    }

    const quality = singularityQuality(data);
    const sparkCount = quality === 0 ? 7 : quality === 1 ? 10 : 13;
    const nonce = Number(data?.eventNonce || 0);
    for (let index = 0; index < sparkCount; index += 1) {
      const spark = document.createElement("span");
      const seed = singularityHash(nonce * 3.17 + index * 11.73);
      const angle = ((Math.PI * 2) / sparkCount) * index + ((seed - 0.5) * 0.42);
      const radius = direction === "earned" ? startDiameter * (0.34 + seed * 0.12) : 20 + seed * 12;
      spark.className = "acg-charge-transfer-spark";
      spark.style.setProperty("--spark-x", `${Math.cos(angle) * radius}px`);
      spark.style.setProperty("--spark-y", `${Math.sin(angle) * radius}px`);
      spark.style.setProperty("--spark-angle", `${Math.round(angle * 180 / Math.PI)}deg`);
      spark.style.setProperty("--spark-delay", `${Math.round(index * 13 + seed * 34)}ms`);
      transfer.appendChild(spark);
    }

    const arrival = document.createElement("span");
    arrival.className = "acg-charge-transfer-arrival";
    transfer.appendChild(arrival);
    scene.appendChild(transfer);
    sidebar.classList.add("charge-transfer-active");
    if (timerBound) {
      window.setTimeout(() => {
        const timerHero = $("acgTimerHero");
        if (!timerHero) return;
        timerHero.classList.remove("boost-impact");
        void timerHero.offsetWidth;
        timerHero.classList.add("boost-impact");
        window.setTimeout(() => timerHero.classList.remove("boost-impact"), 760);
      }, 720);
    }
    window.setTimeout(() => {
      transfer.remove();
      sidebar.classList.remove("charge-transfer-active");
    }, 1280);
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

  function spawnMilestoneRingConsolidation(ringColors, completedRingCount, sphereMode = "milestone") {
    const fx = $("acgFx");
    const sidebar = $("speed-streak-sidebar");
    if (!fx || !sidebar || ringColors.length !== MILESTONE_RING_CARDS || completedRingCount <= 0) {
      return;
    }

    const previousRingCount = completedRingCount - 1;
    const endRadius = milestoneRingRadius(completedRingCount - 1, completedRingCount);
    const fusionLayout = sphereMode === "fusion";
    const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (!reducedMotion) {
      ringColors.forEach((color, slotIndex) => {
        const rowIndex = fusionLayout ? Math.floor(slotIndex / 10) : 0;
        const rowStart = rowIndex * 10;
        const rowCount = fusionLayout ? Math.min(10, ringColors.length - rowStart) : ringColors.length;
        const rowSlotIndex = slotIndex - rowStart;
        const startRadius = fusionLayout
          ? fusionLiveRowRadius(previousRingCount, rowIndex)
          : milestoneLiveRadius(previousRingCount);
        const baseOffset = orbitBaseOffset(previousRingCount + rowIndex, rowCount);
        const angle = baseOffset + ((360 / rowCount) * rowSlotIndex);
        const node = document.createElement("div");
        node.className = `acg-satellite ${color} ${fusionLayout ? "fusion-consolidating" : "milestone-consolidating"}`;
        node.style.setProperty("--angle", `${angle}deg`);
        node.style.setProperty("--start-radius", `${startRadius}px`);
        node.style.setProperty("--mid-radius", `${Math.round(endRadius + ((startRadius - endRadius) * 0.48))}px`);
        node.style.setProperty("--end-radius", `${endRadius}px`);
        node.style.animationDelay = fusionLayout
          ? `${rowIndex * 56 + rowSlotIndex * 11}ms`
          : `${slotIndex * 8}ms`;
        fx.appendChild(node);
        window.setTimeout(() => node.remove(), fusionLayout ? 1550 : 1300 + (slotIndex * 8));
      });
    }

    const lock = document.createElement("div");
    const apex = completedRingCount % 10 === 0;
    const major = !apex && completedRingCount % 5 === 0;
    lock.className = `acg-milestone-lock-effect${major ? " major" : ""}${apex ? " apex" : ""}`;
    lock.style.width = `${endRadius * 2}px`;
    lock.style.height = `${endRadius * 2}px`;
    lock.style.setProperty("--milestone-gradient", buildBankGradient(ringColors));
    fx.appendChild(lock);

    sidebar.classList.remove("milestone-lock-active");
    void sidebar.offsetWidth;
    sidebar.classList.add("milestone-lock-active");
    window.setTimeout(() => {
      lock.remove();
      sidebar.classList.remove("milestone-lock-active");
    }, apex ? 1700 : 1350);
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
    const singularity = isSingularityMode(data);
    const sphereMode = getSphereMode(data);
    const ultraLowResource = getRenderMode(data) === "ultra_low_resource";
    if (["again", "hard", "good", "easy"].includes(data.lastEventType)) {
      if (String(data.lastEventText || "").includes("Boost earned")) {
        spawnChargeTransfer(data, "earned");
      }
      if (!lightweightRows && !crystalReactor && !singularity && !ultraLowResource) {
        if (sphereMode === "fusion" && streak > state.prevStreak && streak % MILESTONE_RING_CARDS !== 0) {
          spawnFusionSatelliteArrival(data.lastSatelliteColor || "blue");
        } else {
          spawnShockwave(data.lastSatelliteColor || "blue");
        }
        if (sphereMode === "consolidate" && streak > 0 && streak % 10 === 0) {
          spawnConsolidationSatellites(
            (Array.isArray(data.satelliteColors) ? data.satelliteColors : []).slice(-10),
            Math.floor(streak / 10),
          );
        }
        if (isMilestoneRingMode(sphereMode) && streak > 0 && streak % MILESTONE_RING_CARDS === 0) {
          spawnMilestoneRingConsolidation(
            (Array.isArray(data.satelliteColors) ? data.satelliteColors : []).slice(-MILESTONE_RING_CARDS),
            Math.floor(streak / MILESTONE_RING_CARDS),
            sphereMode,
          );
        }
        if (isMilestoneRingMode(sphereMode) && streak > 0 && streak % 500 === 0) {
          spawnMilestoneFlare("apex");
        } else if (isMilestoneRingMode(sphereMode) && streak > 0 && streak % 250 === 0) {
          spawnMilestoneFlare("major");
        } else if (milestones.has(streak)) {
          spawnMilestoneFlare();
        }
      }
    } else if (data.lastEventType === "time-boost") {
      spawnChargeTransfer(data, "spent");
    } else if (data.lastEventType === "time-boost-blocked") {
      showToast(String(data.lastEventText || "Time Boost is unavailable"));
      const economy = $("acgBoostEconomy");
      economy?.classList.remove("charge-rejected");
      if (economy) {
        void economy.offsetWidth;
        economy.classList.add("charge-rejected");
        window.setTimeout(() => economy.classList.remove("charge-rejected"), 620);
      }
    } else if (data.lastEventType === "pause-blocked") {
      showToast("No Pause mode is active");
    } else if (data.lastEventType === "undo-blocked") {
      showToast("No Undo mode is active");
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
      } else if (singularity) {
        // Singularity owns its implosion, flare, and debris animation in WebGL.
      } else if (!ultraLowResource && sphereMode === "fusion") {
        triggerFusionDemolition(state.prevColors);
      } else if (!ultraLowResource && sphereMode === "classic") {
        triggerTimeoutCollapse(state.prevColors);
        spawnShockwave("red");
      } else if (!ultraLowResource) {
        spawnShockwave("red");
      }
    } else if (
      data.lastEventType === "reset"
      && !lightweightRows
      && !crystalReactor
      && !singularity
      && !ultraLowResource
      && sphereMode === "fusion"
      && state.prevStreak > 0
    ) {
      triggerFusionDemolition(state.prevColors);
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
    const overflowBadge = $("acgBoostOverflowBadge");
    const timeDrainOverlay = $("acgTimeDrainOverlay");
    const timeDrainTimer = $("acgTimeDrainTimer");
    const animationSignature = [
      String(timer.phase || "idle"),
      Number(data?.phaseStartEpochMs || 0),
      Number(data?.phaseLimitMs || 0),
      Number(data?.phaseBaseLimitMs || 0),
      Number(data?.phaseBoostRemainingMs || 0),
      Number(data?.phaseBoostAnchorEpochMs || 0),
      Number(Boolean(timer.paused)),
      Number(Boolean(timer.free)),
      Number(Boolean(timer.untimed)),
    ].join("|");
    const deadlineEpochMs = Number(data?.phaseStartEpochMs || 0) + Number(data?.phaseLimitMs || 0);
    if (!timerHero || !timerValue || !phaseLabel) {
      return;
    }
    timerHero.classList.toggle("untimed", Boolean(timer.untimed));
    timerHero.classList.toggle("boosted", Number(timer.boostRemaining || 0) > 0);
    if (overflowBadge) {
      const fullTurns = Math.max(0, Number(timer.overflowTurns || 0));
      overflowBadge.textContent = fullTurns > 0 ? `+${fullTurns}×` : "";
      overflowBadge.classList.toggle("visible", fullTurns > 0);
    }

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
      const ratio = clamp(Number(timer.totalRatio || 0), 0, 1);
      const normalRatio = clamp(Number(timer.baseProgress || 0), 0, 1);
      const displayBaseProgress = normalRatio;
      const danger = !timer.boostActive && normalRatio <= 0.3;
      const blendTarget = normalRatio > 0.5 ? timerRamp.yellow : timerRamp.red;
      const blendStart = normalRatio > 0.5 ? timerRamp.green : timerRamp.yellow;
      const localT = normalRatio > 0.5 ? (1 - normalRatio) / 0.5 : (0.5 - normalRatio) / 0.5;
      const color = blendRgb(blendStart, blendTarget, clamp(localT, 0, 1));
      setText("acgTimer", timer.paused ? `Paused ${timer.secondsText}s` : `${timer.phase} ${timer.secondsText}s`);
      setText(phaseLabel, timer.paused ? "Paused" : timer.phase);
      setText(timerValue, timer.secondsText);
      setStyleProperty(timerHero, "--timer-progress", `${ratio}turn`);
      setStyleProperty(timerHero, "--timer-base-progress", `${displayBaseProgress}turn`);
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
    const numberOnly = visualMode === "number_only";
    const crystalReactor = visualMode === "crystal_reactor";
    const singularity = visualMode === "singularity";
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

    // A Fusion loss must start before the zero-streak render changes the
    // center and scene scale. Other effects retain their normal later timing
    // because some of them depend on freshly rendered controls.
    const eventNonceChanged = Number(data.eventNonce || 0) !== state.lastNonce;
    const fusionLossIncoming = eventNonceChanged
      && visualMode === "sphere"
      && sphereMode === "fusion"
      && state.prevStreak > 0
      && ["timeout", "reset"].includes(String(data.lastEventType || ""));
    if (fusionLossIncoming) handleStateEffects(data);
    const holdFusionScene = state.fusionDemolitionActive
      && visualMode === "sphere"
      && sphereMode === "fusion";
    const visualStreak = holdFusionScene ? state.prevStreak : streak;
    const visualColors = holdFusionScene ? state.prevColors : colors;

    setText("acgStreak", String(visualStreak));
    setText("acgScore", score.toLocaleString());
    setText("acgMultiplier", `x${multiplier.toFixed(2)} multiplier`);
    sidebar.classList.toggle("inline-mode", displayMode !== "compatibility");
    sidebar.classList.toggle("compatibility-mode", displayMode === "compatibility");
    sidebar.classList.toggle("off", !enabled);
    sidebar.classList.toggle("visuals-disabled", enabled && !visualsEnabled);
    sidebar.classList.toggle("orbit-static", enabled && visualsEnabled && numberOnly);
    sidebar.classList.toggle("lightweight-rows", enabled && visualsEnabled && lightweightRows);
    sidebar.classList.toggle("crystal-reactor", enabled && visualsEnabled && crystalReactor);
    sidebar.classList.toggle("singularity-mode", enabled && visualsEnabled && singularity);
    sidebar.classList.toggle("sphere-consolidate", enabled && visualsEnabled && visualMode === "sphere" && sphereMode === "consolidate");
    sidebar.classList.toggle("sphere-milestone", enabled && visualsEnabled && visualMode === "sphere" && isMilestoneRingMode(sphereMode));
    sidebar.classList.toggle("sphere-fusion", enabled && visualsEnabled && visualMode === "sphere" && sphereMode === "fusion");
    sidebar.classList.toggle("ultra-low-resource", enabled && visualsEnabled && visualMode === "sphere" && renderMode === "ultra_low_resource");
    sidebar.classList.toggle("webgl-orbit", enabled && visualsEnabled && visualMode === "sphere" && renderMode === "webgl");
    sidebar.classList.toggle("collapsed", sidebarCollapsed);
    sidebar.classList.toggle("motion-suspended", visualMotionSuspended());
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

    if (coreWrap && visualMode === "sphere") {
      const coreSize = clamp(58 + (visualStreak * 2.8), 58, 142);
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
    if (field && visualMode === "sphere") {
      const nextFilter = `saturate(${clamp(1 + (visualStreak * 0.04), 1, 2.4)}) brightness(${clamp(1 + (visualStreak * 0.015), 1, 1.45)})`;
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
    core.classList.toggle("failed", !holdFusionScene && Boolean(data.failureVisualActive));
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
    if (!fusionLossIncoming) handleStateEffects(data);
    if (enabled && visualsEnabled && !sidebarCollapsed && lightweightRows) {
      stopSingularityRenderer();
      stopCrystalReactor();
      clearOrbitScene();
      renderLightweightRows(data);
    } else if (enabled && visualsEnabled && !sidebarCollapsed && singularity) {
      stopCrystalReactor();
      clearOrbitScene();
      clearRowsScene();
      renderSingularity(data);
    } else if (enabled && visualsEnabled && !sidebarCollapsed && crystalReactor) {
      stopSingularityRenderer();
      clearOrbitScene();
      clearRowsScene();
      renderCrystalReactor(data);
    } else if (enabled && visualsEnabled && !sidebarCollapsed && visualMode === "sphere") {
      stopSingularityRenderer();
      stopCrystalReactor();
      clearRowsScene();
      moveSharedWebglCanvas("sphere");
      renderRings(visualColors, data);
    } else {
      stopSingularityRenderer();
      stopCrystalReactor();
      clearOrbitScene();
      clearRowsScene();
    }
    if (!holdFusionScene) {
      state.prevColors = colors.slice();
      state.prevStreak = streak;
    }
  }

  function renderGameplayEconomy(data) {
    const timeBoostMode = String(data?.gameplayMode || "time_boost") === "time_boost";
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

    const canUseBoost = Boolean(data?.canUseTimeBoost);
    const unavailableReason = String(data?.timeBoostUnavailableReason || "");
    boost?.classList.toggle("charge-unavailable", !canUseBoost);
    const boostZone = $("acgBoostHoverZone");
    if (boostZone) {
      boostZone.setAttribute("title", canUseBoost ? "Click the Boost bank to edit Time Boost settings" : unavailableReason);
    }

    const charges = Math.max(0, Number(data?.boostCharges || 0));
    const maxCharges = Math.max(1, Number(data?.maxBoostCharges || 1));
    const progress = Math.max(0, Number(data?.boostChargeProgress || 0));
    const required = Math.max(1, Number(data?.cardsPerBoostCharge || 1));
    const boostSeconds = Math.max(0.5, Number(data?.boostSeconds || 10));
    renderBoostChargeBank(charges, maxCharges);
    setText("acgBoostProgressText", charges >= maxCharges ? "" : `Next Boost ${progress} / ${required}`);
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
    bank.setAttribute("aria-label", `${charges} of ${maxCharges} Boosts available`);
    bank.setAttribute("title", `${charges} / ${maxCharges} Boosts`);
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

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      syncSingularityDocumentVisibility();
      stopWebglOrbit();
      stopCrystalReactor();
      $("speed-streak-sidebar")?.classList.add("motion-suspended");
      return;
    }
    if (state.data) render(state.data);
  });
  window.addEventListener("pagehide", () => disposeSingularityRenderer());

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureMounted, { once: true });
  } else {
    ensureMounted();
  }
})();
