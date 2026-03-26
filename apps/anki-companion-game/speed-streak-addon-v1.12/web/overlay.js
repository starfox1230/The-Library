(function () {
  const state = {
    mounted: false,
    data: null,
    animationId: 0,
    lastColorsSignature: "",
    lastRingCount: 0,
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
  };

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
    { value: 6, label: "Teal" },
    { value: 7, label: "Purple" },
  ];

  const template = `
    <div id="speed-streak-sidebar" class="speed-streak-sidebar hidden">
      <button id="acgCollapseTab" class="acg-collapse-tab" type="button" title="Hide Speed Streak">
        <span id="acgCollapseTabText" class="acg-collapse-tab-text">Hide</span>
      </button>
      <div class="acg-foreground-controls">
        <button id="acgEnabledToggle" class="acg-enabled-toggle" type="button" aria-pressed="true" title="Toggle Speed Streak">
          <span class="acg-enabled-track">
            <span id="acgEnabledKnob" class="acg-enabled-knob"></span>
          </span>
        </button>
      </div>
      <div class="acg-inner">
        <div class="acg-top">
          <div id="acgTimerHero" class="acg-timer-hero">
            <div class="acg-timer-inner">
              <div id="acgPhaseLabel" class="acg-phase-label">Ready</div>
              <div id="acgTimerValue" class="acg-timer-value">--</div>
            </div>
          </div>
          <div id="acgScore" class="acg-score">0</div>
          <div id="acgMultiplier" class="acg-multiplier">x1.00 multiplier</div>
        </div>
        <div class="acg-stage">
          <div id="acgField" class="acg-field">
            <div id="acgScene" class="acg-scene">
              <div id="acgEnergyDisc" class="acg-energy-disc"></div>
              <div id="acgRings"></div>
              <div id="acgSatellites"></div>
              <div id="acgFx" class="acg-fx"></div>
              <div class="acg-core-wrap">
                <div class="acg-core-halo"></div>
                <div id="acgCore" class="acg-core">
                  <div id="acgStreak" class="acg-streak">0</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="acg-bottom">
          <div id="acgVisualsDisabledCopy" class="acg-visuals-disabled-copy">Vibration-only mode is active.</div>
          <div id="acgTimer" class="acg-timer">Ready</div>
          <button id="acgSettingsButton" class="acg-action acg-foreground-action" type="button">Settings</button>
        </div>
        <div id="acgDim" class="acg-dim"></div>
        <div id="acgPauseOverlay" class="acg-pause-overlay">
          <div class="acg-pause-copy">Press 'P' to Unpause</div>
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
          </div>
        </div>
        <div id="acgToast" class="acg-toast"></div>
        <div id="acgSettingsModal" class="acg-modal">
          <div class="acg-modal-head">
            <div class="acg-modal-title">Settings</div>
            <button id="acgCloseSettings" class="acg-close" type="button">Close</button>
          </div>
          <div class="acg-modal-body">
            <div class="acg-settings-section">
              <div class="acg-section-title">Timers</div>
              <div class="acg-form-row">
                <label class="acg-form-label" for="acgQuestionSeconds">Question Time</label>
                <input id="acgQuestionSeconds" class="acg-input" type="number" min="1" step="0.5" />
              </div>
              <div class="acg-form-row">
                <label class="acg-form-label" for="acgAnswerSeconds">Answer Time</label>
                <input id="acgAnswerSeconds" class="acg-input" type="number" min="1" step="0.5" />
              </div>
            </div>
            <div class="acg-settings-section">
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
            <div class="acg-settings-section">
              <div class="acg-section-title">Modes</div>
              <label class="acg-switch-row" for="acgShowCardTimer">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Top Card Timer</span>
                  <span class="acg-switch-copy">Show a horizontal timer bar at the top of the review card.</span>
                </span>
                <input id="acgShowCardTimer" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgOrbitAnimation">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Orb Animation</span>
                  <span class="acg-switch-copy">Turn off the orb and satellite animation if your computer is slow, and keep only the streak number.</span>
                </span>
                <input id="acgOrbitAnimation" class="acg-switch" type="checkbox" />
              </label>
              <label class="acg-switch-row" for="acgVibrationOnlyMode">
                <span class="acg-switch-copy-wrap">
                  <span class="acg-form-label">Vibration Only Mode</span>
                  <span class="acg-switch-copy">Turns off streak and timer visuals, disables late buzzes, and keeps only haptics.</span>
                </span>
                <input id="acgVibrationOnlyMode" class="acg-switch" type="checkbox" />
              </label>
            </div>
            <div class="acg-settings-section">
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
                This sidebar runs a two-phase timer for each card. The question timer runs while you are deciding what the answer is, and the answer timer runs after you reveal the card. The very first synced card is free so the session can start cleanly.
                <br><br>
                Every time you rate a card on time, your streak goes up by one and a new satellite is added to the orbit. Again adds a red satellite, Hard adds yellow, Good adds green, and Easy adds blue. The number in the center orb is your current streak, and the score at the top grows with a streak multiplier so longer runs are worth more.
                <br><br>
                If either timer expires, the streak is lost, the orb flashes into a failed state, and the orbit collapses. If you bury or hide a card, the next card gets a fresh timer without changing the streak or score.
                <br><br>
                Press <strong>P</strong> to pause or unpause. Opening Settings also pauses automatically. While paused, the sidebar dims and waits for you to resume. You can change the question and answer timers in Settings, toggle the top-of-card timer, and switch into vibration-only mode. The <strong>Show Stats</strong> screen opens a full-window overlay with your current-round pause time, today's pace, and historical charts.
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
      return;
    }
    const host = document.body || document.documentElement;
    if (!host) {
      return;
    }

    host.insertAdjacentHTML("beforeend", template);

    const settingsButton = document.getElementById("acgSettingsButton");
    if (settingsButton) {
      settingsButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:open-settings");
        }
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

    const showCardTimerInput = document.getElementById("acgShowCardTimer");
    if (showCardTimerInput) {
      showCardTimerInput.addEventListener("change", () => saveSettings());
    }

    const orbitAnimationInput = document.getElementById("acgOrbitAnimation");
    if (orbitAnimationInput) {
      orbitAnimationInput.addEventListener("change", () => saveSettings());
    }

    const vibrationOnlyInput = document.getElementById("acgVibrationOnlyMode");
    if (vibrationOnlyInput) {
      vibrationOnlyInput.addEventListener("change", () => saveSettings());
    }

    const statsButton = document.getElementById("acgStatsButton");
    if (statsButton) {
      statsButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:open-stats");
        }
      });
    }

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

    renderFlagSelects(0, 0);

    state.mounted = true;
  }

  function $(id) {
    return document.getElementById(id);
  }

  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }

  function computeTimer(data) {
    const phase = data.phase || "idle";
    const start = Number(data.phaseStartEpochMs || 0);
    const limit = Number(data.phaseLimitMs || 0);
    const free = Boolean(data.firstCardFree && phase === "question");
    const paused = Boolean(data.paused);

    if (phase === "idle" || !start) {
      return { phase, free, paused, remaining: 0, total: 0 };
    }
    if (free || !limit) {
      return { phase, free: true, paused, remaining: 0, total: 0 };
    }
    if (paused) {
      return { phase, free: false, paused: true, remaining: Number(data.pausedRemainingMs || 0), total: limit };
    }

    const elapsed = Math.max(0, Date.now() - start);
    return {
      phase,
      free: false,
      paused: false,
      remaining: Math.max(0, limit - elapsed),
      total: limit,
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
    const f = Number($("acgTimeDrainFlag")?.value || 0);
    const rl = Number($("acgReviewLaterFlag")?.value || 0);
    const showCardTimer = Boolean($("acgShowCardTimer")?.checked);
    const orbitAnimationEnabled = Boolean($("acgOrbitAnimation")?.checked);
    const visualsEnabled = !Boolean($("acgVibrationOnlyMode")?.checked);
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
          timeDrainFlag: f,
          reviewLaterFlag: rl,
          showCardTimer,
          orbitAnimationEnabled,
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
    const questionInput = $("acgQuestionSeconds");
    const answerInput = $("acgAnswerSeconds");
    if (questionInput && document.activeElement !== questionInput) {
      questionInput.value = (Number(data.questionLimitMs || 12000) / 1000).toFixed(1);
    }
    if (answerInput && document.activeElement !== answerInput) {
      answerInput.value = (Number(data.reviewLimitMs || 8000) / 1000).toFixed(1);
    }
    const showCardTimerInput = $("acgShowCardTimer");
    if (showCardTimerInput && document.activeElement !== showCardTimerInput) {
      showCardTimerInput.checked = Boolean(data.showCardTimer);
    }
    const orbitAnimationInput = $("acgOrbitAnimation");
    if (orbitAnimationInput && document.activeElement !== orbitAnimationInput) {
      orbitAnimationInput.checked = Boolean(data.orbitAnimationEnabled ?? true);
    }
    const vibrationOnlyInput = $("acgVibrationOnlyMode");
    if (vibrationOnlyInput && document.activeElement !== vibrationOnlyInput) {
      vibrationOnlyInput.checked = !Boolean(data.visualsEnabled);
    }
    state.appearanceModeDraft = String(data.appearanceMode || "midnight");
    state.colorDrafts = normalizeCustomColors(data.customColors || {});
    state.useCustomTimerColorsDraft = Boolean(data.customTimerColors);
    state.timerColorLevelDraft = Number(data.customTimerColorLevel || 0);
    renderColorInputs(state.colorDrafts);
    renderFlagSelects(Number(data.timeDrainFlag || 0), Number(data.reviewLaterFlag || 0));
    syncAppearanceButtons();
  }

  function syncAppearanceButtons() {
    const mode = state.appearanceModeDraft || "midnight";
    $("acgAppearanceMidnight")?.classList.toggle("active", mode === "midnight");
    $("acgAppearanceCard")?.classList.toggle("active", mode === "card");
  }

  function renderFlagSelects(timeDrainFlag, reviewLaterFlag) {
    renderFlagSelect("acgTimeDrainFlag", timeDrainFlag, reviewLaterFlag);
    renderFlagSelect("acgReviewLaterFlag", reviewLaterFlag, timeDrainFlag);
  }

  function renderFlagSelect(id, selectedValue, blockedValue) {
    const node = $(id);
    if (!node) return;
    node.innerHTML = FLAG_OPTIONS.map((option) => {
      const disabled = option.value !== 0 && option.value === blockedValue ? " disabled" : "";
      const selected = option.value === selectedValue ? " selected" : "";
      const label = option.value === 0 ? "0 - Off" : `${option.value} - ${option.label}`;
      return `<option value="${option.value}"${selected}${disabled}>${label}</option>`;
    }).join("");
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
        swatch.style.background = color;
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

  function renderRings(colors) {
    const ringsNode = $("acgRings");
    const satellitesNode = $("acgSatellites");
    const field = $("acgField");
    const scene = $("acgScene");
    const disc = $("acgEnergyDisc");
    if (!ringsNode || !satellitesNode || !field || !scene) {
      return;
    }

    const ringCount = Math.max(1, Math.ceil(colors.length / 10));
    const signature = colors.join("|");
    if (signature === state.lastColorsSignature && ringCount === state.lastRingCount) {
      if (disc) {
        const discSize = clamp(118 + (colors.length * 5), 118, 280);
        disc.style.setProperty("--disc-size", `${discSize}px`);
        disc.style.setProperty("--disc-speed", `${Math.max(5, 16 - (colors.length * 0.12))}s`);
        disc.style.setProperty("--disc-opacity", `${clamp(0.35 + (colors.length * 0.015), 0.35, 0.92)}`);
      }
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
      const baseOffset = ((ringIndex * 23) + (count % 2 ? 9 : 0)) % 360;
      const orbitDuration = Math.max(4.5, 12 - (ringIndex * 0.8) - (colors.length * 0.04));
      ringColors.forEach((color, slotIndex) => {
        const angle = baseOffset + ((360 / count) * slotIndex);
        satellitesHtml += `<div class="acg-satellite ${color}" style="--angle:${angle}deg;--radius:${radius}px;--orbit-duration:${orbitDuration}s;"></div>`;
      });
    });

    ringsNode.innerHTML = ringsHtml;
    satellitesNode.innerHTML = satellitesHtml;

    const requiredSize = (Math.max(1, ringCount) * 52) + 150;
    const bounds = field.getBoundingClientRect();
    const available = Math.max(180, Math.min(bounds.width || 220, bounds.height || 220) - 10);
    const sceneScale = clamp(available / requiredSize, 0.42, 1);
    scene.style.setProperty("--scene-size", `${requiredSize}px`);
    scene.style.setProperty("--scene-scale", `${sceneScale}`);
    scene.classList.toggle("zooming-out", sceneScale < state.lastSceneScale - 0.015);
    window.clearTimeout(state.zoomTimer);
    state.zoomTimer = window.setTimeout(() => {
      scene.classList.remove("zooming-out");
    }, 560);

    if (disc) {
      const discSize = clamp(118 + (colors.length * 5), 118, 280);
      disc.style.setProperty("--disc-size", `${discSize}px`);
      disc.style.setProperty("--disc-speed", `${Math.max(5, 16 - (colors.length * 0.12))}s`);
      disc.style.setProperty("--disc-opacity", `${clamp(0.35 + (colors.length * 0.015), 0.35, 0.92)}`);
    }

    state.lastColorsSignature = signature;
    state.lastRingCount = ringCount;
    state.lastSceneScale = sceneScale;
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
    if (["again", "hard", "good", "easy"].includes(data.lastEventType)) {
      spawnShockwave(data.lastSatelliteColor || "blue");
      if (milestones.has(streak)) {
        spawnMilestoneFlare();
      }
    } else if (data.lastEventType === "review-later-added") {
      showToast("Review Later");
    } else if (data.lastEventType === "review-later-removed") {
      showToast("Removed from 'Review Later'");
    } else if (data.lastEventType === "timeout") {
      triggerTimeoutCollapse(state.prevColors);
      spawnShockwave("red");
    }

    state.lastNonce = nonce;
  }

  function triggerHaptics(data) {
    if (Number(data.hapticsAvailable || 0) > 0) {
      return;
    }
    const kind = String(data.lastEventType || "");
    const patterns = {
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
      timeout: [
        { duration: 420, weak: 0.8, strong: 1.0 },
        { duration: 95, weak: 0, strong: 0 },
        { duration: 180, weak: 0.55, strong: 0.76 },
      ],
    };
    const sequence = patterns[kind];
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
    const visualsEnabled = Boolean(data.visualsEnabled);
    const orbitAnimationEnabled = Boolean(data.orbitAnimationEnabled ?? true);
    const sidebarCollapsed = displayMode !== "compatibility" && Boolean(data.sidebarCollapsed);
    const appearanceMode = String(data.appearanceMode || "midnight");
    const sidebarBackground = String(data.sidebarBackground || "").trim();

    const colors = Array.isArray(data.satelliteColors) ? data.satelliteColors : [];
    const timer = computeTimer(data);
    const core = $("acgCore");
    const timerHero = $("acgTimerHero");
    const timerValue = $("acgTimerValue");
    const phaseLabel = $("acgPhaseLabel");
    const timeDrainOverlay = $("acgTimeDrainOverlay");
    const timeDrainTimer = $("acgTimeDrainTimer");
    const offOverlay = $("acgOffOverlay");
    const enabledToggle = $("acgEnabledToggle");
    const collapseTab = $("acgCollapseTab");
    const collapseTabText = $("acgCollapseTabText");
    const score = Number(data.score || 0);
    const multiplier = Number(data.streakMultiplier || 1);
    const streak = Number(data.streak || 0);
    const field = $("acgField");
    const coreWrap = document.querySelector(".acg-core-wrap");

    $("acgStreak").textContent = String(streak);
    $("acgScore").textContent = score.toLocaleString();
    $("acgMultiplier").textContent = `x${multiplier.toFixed(2)} multiplier`;
    sidebar.classList.toggle("inline-mode", displayMode !== "compatibility");
    sidebar.classList.toggle("compatibility-mode", displayMode === "compatibility");
    sidebar.classList.toggle("off", !enabled);
    sidebar.classList.toggle("visuals-disabled", enabled && !visualsEnabled);
    sidebar.classList.toggle("orbit-static", enabled && visualsEnabled && !orbitAnimationEnabled);
    sidebar.classList.toggle("collapsed", sidebarCollapsed);
    sidebar.dataset.displayMode = displayMode;
    sidebar.dataset.theme = appearanceMode;
    applyCustomColors(sidebar, data.customColors || {}, appearanceMode);
    if (document.documentElement) {
      document.documentElement.style.background = sidebarBackground || "transparent";
    }
    if (document.body) {
      document.body.style.background = sidebarBackground || "transparent";
    }

    if (enabledToggle) {
      enabledToggle.classList.toggle("off", !enabled);
      enabledToggle.setAttribute("aria-pressed", enabled ? "true" : "false");
    }
    if (collapseTab) {
      collapseTab.setAttribute("title", sidebarCollapsed ? "Show Speed Streak" : "Hide Speed Streak");
    }
    if (collapseTabText) {
      collapseTabText.textContent = sidebarCollapsed ? "Show" : "Hide";
    }

    if (coreWrap && orbitAnimationEnabled) {
      const coreSize = clamp(58 + (streak * 2.8), 58, 142);
      coreWrap.style.setProperty("--core-size", `${coreSize}px`);
    } else if (coreWrap) {
      coreWrap.style.setProperty("--core-size", "auto");
    }
    if (field && orbitAnimationEnabled) {
      field.style.filter = `saturate(${clamp(1 + (streak * 0.04), 1, 2.4)}) brightness(${clamp(1 + (streak * 0.015), 1, 1.45)})`;
    } else if (field) {
      field.style.filter = "none";
    }
    state.appearanceModeDraft = appearanceMode;
    syncAppearanceButtons();

    if (!enabled) {
      $("acgTimer").textContent = "Off";
      phaseLabel.textContent = "Off";
      timerValue.textContent = "--";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", "#8c96ac");
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (!visualsEnabled) {
      $("acgTimer").textContent = "Vibration only";
      phaseLabel.textContent = "Vibration";
      timerValue.textContent = "--";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", "#8c96ac");
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.phase === "idle") {
      const timerRamp = getTimerRampColors(data);
      $("acgTimer").textContent = "Ready";
      phaseLabel.textContent = "Ready";
      timerValue.textContent = "--";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", timerRamp.idle);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.free) {
      const timerRamp = getTimerRampColors(data);
      $("acgTimer").textContent = "First card free";
      phaseLabel.textContent = "Question";
      timerValue.textContent = "FREE";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", timerRamp.free);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else {
      const timerRamp = getTimerRampColors(data);
      const seconds = Math.max(0, timer.remaining / 1000);
      const ratio = timer.total ? clamp(timer.remaining / timer.total, 0, 1) : 0;
      const danger = ratio <= 0.3;
      const blendTarget = ratio > 0.5 ? timerRamp.yellow : timerRamp.red;
      const blendStart = ratio > 0.5 ? timerRamp.green : timerRamp.yellow;
      const localT = ratio > 0.5 ? (1 - ratio) / 0.5 : (0.5 - ratio) / 0.5;
      const color = blendRgb(blendStart, blendTarget, clamp(localT, 0, 1));
      $("acgTimer").textContent = timer.paused ? `Paused ${seconds.toFixed(1)}s` : `${timer.phase} ${seconds.toFixed(1)}s`;
      phaseLabel.textContent = timer.paused ? "Paused" : timer.phase;
      timerValue.textContent = seconds.toFixed(1);
      timerHero.style.setProperty("--timer-progress", `${ratio}turn`);
      timerHero.style.setProperty("--timer-color", color);
      timerHero.classList.toggle("danger", danger);
      timerValue.classList.toggle("danger", danger);
    }

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
    if (offOverlay) {
      offOverlay.classList.toggle("visible", !enabled && !state.settingsOpen);
    }
    if (timeDrainOverlay && timeDrainTimer) {
      const activeTimeDrain = enabled && visualsEnabled && Number(data.timeDrainFlag || 0) > 0
        && Number(data.currentCardFlag || 0) === Number(data.timeDrainFlag || 0)
        && timer.phase === "question";
      timeDrainOverlay.classList.toggle("visible", activeTimeDrain);
      timeDrainTimer.textContent = timer.free ? "FREE" : timer.phase === "idle" ? "--" : Math.max(0, timer.remaining / 1000).toFixed(1);
    }
    handleStateEffects(data);
    if (enabled && visualsEnabled && orbitAnimationEnabled && !sidebarCollapsed) {
      renderRings(colors);
    } else {
      clearOrbitScene();
    }
    state.prevColors = colors.slice();
    state.prevStreak = streak;
  }

  function clearOrbitScene() {
    const ringsNode = $("acgRings");
    const satellitesNode = $("acgSatellites");
    if (ringsNode) {
      ringsNode.innerHTML = "";
    }
    if (satellitesNode) {
      satellitesNode.innerHTML = "";
    }
  }

  function blendRgb(a, b, t) {
    const r = Math.round(a[0] + ((b[0] - a[0]) * t));
    const g = Math.round(a[1] + ((b[1] - a[1]) * t));
    const bl = Math.round(a[2] + ((b[2] - a[2]) * t));
    return `rgb(${r}, ${g}, ${bl})`;
  }

  function animationLoop() {
    if (state.data) {
      render(state.data);
    }
    state.animationId = requestAnimationFrame(animationLoop);
  }

  window.SpeedStreak = {
    receiveState(nextState) {
      ensureMounted();
      render(nextState);
      if (!state.animationId) {
        state.animationId = requestAnimationFrame(animationLoop);
      }
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureMounted, { once: true });
  } else {
    ensureMounted();
  }
})();


