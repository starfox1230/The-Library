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
    lastSettingsSignature: "",
    lastThemeSignature: "",
    lastSidebarBackground: "",
    lastFilterValue: "",
    lastCoreSize: "",
    webgl: null,
    timerWebgl: null,
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
        <button id="acgDisplayModeToggle" class="acg-action acg-foreground-action acg-icon-toggle acg-display-mode-toggle" type="button" title="Switch to external window" aria-label="Switch to external window">↗</button>
      </div>
      <div class="acg-foreground-settings">
        <button id="acgSettingsButton" class="acg-action acg-foreground-action acg-icon-toggle acg-settings-toggle" type="button" title="Settings" aria-label="Settings">⚙</button>
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
          <div id="acgScore" class="acg-score">0</div>
          <div id="acgMultiplier" class="acg-multiplier">x1.00 multiplier</div>
        </div>
        <div class="acg-stage">
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
          </div>
        </div>
        <div class="acg-bottom">
          <div id="acgVisualsDisabledCopy" class="acg-visuals-disabled-copy">Vibration-only mode is active.</div>
          <div id="acgTimer" class="acg-timer">Ready</div>
          <div class="acg-bottom-bar">
            <div class="acg-mode-grid" role="group" aria-label="Layout and resource mode">
              <div class="acg-mode-column acg-mode-column-sphere">
                <button id="acgLayoutSphere" class="acg-action acg-icon-toggle acg-mode-primary" type="button" title="Satellite view" aria-label="Satellite view">◎</button>
                <div class="acg-resource-stack">
                <button id="acgSphereConsolidateToggle" class="acg-action acg-icon-toggle acg-resource-toggle acg-leaf-toggle acg-leaf-toggle-small" type="button" title="Consolidate (low resource)" aria-label="Consolidate (low resource)">
                    <svg class="acg-leaf-icon lucide lucide-leaf-icon lucide-leaf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path>
                      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>
                    </svg>
                  </button>
                  <button id="acgSphereUltraToggle" class="acg-action acg-icon-toggle acg-resource-toggle acg-leaf-toggle" type="button" title="Ultra low resource" aria-label="Ultra low resource">
                    <svg class="acg-leaf-icon lucide lucide-leaf-icon lucide-leaf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                      <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path>
                      <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>
                    </svg>
                  </button>
                </div>
              </div>
              <div class="acg-mode-column acg-mode-column-brick">
                <button id="acgLayoutBrick" class="acg-action acg-icon-toggle acg-mode-primary acg-leaf-toggle" type="button" title="Brick layout (ultra-low resource)" aria-label="Brick layout (ultra-low resource)">
                  <svg class="acg-leaf-icon lucide lucide-leaf-icon lucide-leaf" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
                    <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"></path>
                    <path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"></path>
                  </svg>
                </button>
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
                This sidebar runs a two-phase timer for each card. The question timer runs while you are deciding what the answer is, and the answer timer runs after you reveal the card. The very first synced card is free so the session can start cleanly.
                <br><br>
                Every time you rate a card on time, your streak goes up by one and a new satellite is added to the orbit. Again adds a red satellite, Hard adds yellow, Good adds green, and Easy adds blue. The number in the center orb is your current streak, and the score at the top grows with a streak multiplier so longer runs are worth more.
                <br><br>
                If either timer expires, the streak is lost, the orb flashes into a failed state, and the orbit collapses. If you bury or hide a card, the next card gets a fresh timer without changing the streak or score.
                <br><br>
                Press <strong id="acgHelpPauseShortcut">P</strong> to pause or unpause. Opening Settings also pauses automatically. While paused, the sidebar dims and waits for you to resume. You can change the question and answer timers in Settings, toggle the top-of-card timer, and switch into vibration-only mode. The <strong>Show Stats</strong> screen opens a full-window overlay with your current-round pause time, today's pace, and historical charts.
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

    const layoutSphereButton = document.getElementById("acgLayoutSphere");
    if (layoutSphereButton) {
      layoutSphereButton.addEventListener("click", () => saveSettings({
        visualMode: "sphere",
        sphereMode: "classic",
        renderMode: "webgl",
      }));
    }

    const layoutBrickButton = document.getElementById("acgLayoutBrick");
    if (layoutBrickButton) {
      layoutBrickButton.addEventListener("click", () => saveSettings({
        visualMode: "lightweight_rows",
        renderMode: "ultra_low_resource",
      }));
    }

    const sphereConsolidateToggle = document.getElementById("acgSphereConsolidateToggle");
    if (sphereConsolidateToggle) {
      sphereConsolidateToggle.addEventListener("click", () => {
        const currentVisualMode = getVisualMode(state.data || {});
        const currentSphereMode = getSphereMode(state.data || {});
        const nextSphereMode = currentVisualMode === "sphere" && currentSphereMode === "consolidate"
          ? "classic"
          : "consolidate";
        saveSettings({ visualMode: "sphere", sphereMode: nextSphereMode, renderMode: "webgl" });
      });
    }

    const sphereUltraToggle = document.getElementById("acgSphereUltraToggle");
    if (sphereUltraToggle) {
      sphereUltraToggle.addEventListener("click", () => {
        const currentVisualMode = getVisualMode(state.data || {});
        const currentRenderMode = getRenderMode(state.data || {});
        const nextRenderMode = currentVisualMode === "sphere" && currentRenderMode === "ultra_low_resource"
          ? "webgl"
          : "ultra_low_resource";
        saveSettings({ visualMode: "sphere", renderMode: nextRenderMode, sphereMode: "classic" });
      });
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
        if (typeof pycmd === "function") {
          pycmd("speed-streak:toggle-display-mode");
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

  function syncShortcutCopy(data) {
    const pauseShortcut = getPauseShortcut(data);
    setText("acgPauseShortcutLabel", pauseShortcut);
    setText("acgHelpPauseShortcut", pauseShortcut);
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
    if (Boolean(data.firstCardFree) && phase === "question") {
      return false;
    }
    return Number(data.phaseLimitMs || 0) > 0;
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
    const free = Boolean(data.firstCardFree && phase === "question");
    const paused = Boolean(data.paused);

    if (phase === "idle" || !Number(data.phaseStartEpochMs || 0)) {
      return { phase, free, paused, remaining: 0, total: 0, secondsText: "0.0" };
    }
    if (free || !limit) {
      return { phase, free: true, paused, remaining: 0, total: 0, secondsText: "0.0" };
    }
    const remaining = paused
      ? Math.max(0, Number(data.timerDisplayRemainingMs || 0))
      : computeSharedRemainingMs(data);
    if (paused) {
      return { phase, free: false, paused: true, remaining, total: limit, secondsText: formatTimerSecondsText(remaining) };
    }
    return {
      phase,
      free: false,
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
    const f = Number($("acgTimeDrainFlag")?.value || 0);
    const timeDrainReviewLast = Boolean($("acgTimeDrainReviewLast")?.checked);
    const rl = Number($("acgReviewLaterFlag")?.value || 0);
    const showCardTimer = Boolean($("acgShowCardTimer")?.checked);
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
          timeDrainFlag: f,
          timeDrainReviewLast,
          reviewLaterFlag: rl,
          audioEnabled,
          hapticsEnabled,
          showCardTimer,
          orbitAnimationEnabled,
          visualMode,
          sphereMode,
          renderMode,
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
      showCardTimer: Boolean(data.showCardTimer),
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
    const showCardTimerInput = $("acgShowCardTimer");
    if (showCardTimerInput && document.activeElement !== showCardTimerInput) {
      showCardTimerInput.checked = Boolean(data.showCardTimer);
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

  function syncQuickControls(data) {
    const visualMode = getVisualMode(data);
    const sphereMode = getSphereMode(data);
    const renderMode = getRenderMode(data);
    const audioEnabled = Boolean(data?.audioEnabled ?? false);
    const hapticsEnabled = Boolean(data?.hapticsEnabled ?? true);
    const audioToggle = $("acgAudioToggle");
    const sphereButton = $("acgLayoutSphere");
    const brickButton = $("acgLayoutBrick");
    const sphereConsolidateToggle = $("acgSphereConsolidateToggle");
    const sphereUltraToggle = $("acgSphereUltraToggle");
    const displayModeToggle = $("acgDisplayModeToggle");
    const displayMode = String(data?.displayMode || "inline");
    const sphereConsolidateActive = visualMode === "sphere" && sphereMode === "consolidate" && renderMode !== "ultra_low_resource";
    const sphereUltraActive = visualMode === "sphere" && renderMode === "ultra_low_resource";
    const sphereResourceActive = sphereConsolidateActive || sphereUltraActive;
    const brickResourceActive = visualMode === "lightweight_rows";

    syncQuickControl(sphereButton, visualMode === "sphere", sphereResourceActive ? "Satellite view with reduced resources" : "Satellite view");
    syncQuickControl(brickButton, visualMode === "lightweight_rows", "Brick layout (ultra-low resource)");
    sphereButton?.classList.toggle("is-resource-active", sphereResourceActive);
    brickButton?.classList.toggle("is-resource-active", brickResourceActive);
    syncQuickControl(
      sphereConsolidateToggle,
      sphereConsolidateActive,
      sphereConsolidateActive ? "Consolidate (low resource) on" : "Consolidate (low resource)"
    );
    syncQuickControl(
      sphereUltraToggle,
      sphereUltraActive,
      sphereUltraActive ? "Ultra low resource on" : "Ultra low resource"
    );
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
      displayModeToggle.textContent = compatibility ? "↙" : "↗";
      syncQuickControl(
        displayModeToggle,
        compatibility,
        compatibility ? "Switch to inline side pane" : "Switch to external window"
      );
    }
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
      gl.useProgram(program);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      state.webgl = renderer;
      return renderer;
    } catch (_error) {
      return null;
    }
  }

  function resizeWebglCanvas(renderer) {
    const canvas = renderer.canvas;
    const width = Math.max(1, canvas.offsetWidth || 1);
    const height = Math.max(1, canvas.offsetHeight || 1);
    const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
    const nextWidth = Math.max(1, Math.round(width * dpr));
    const nextHeight = Math.max(1, Math.round(height * dpr));
    if (canvas.width !== nextWidth || canvas.height !== nextHeight) {
      canvas.width = nextWidth;
      canvas.height = nextHeight;
    }
    renderer.gl.viewport(0, 0, nextWidth, nextHeight);
    return { width, height, dpr };
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
        float angle = atan(uv.y, uv.x) + 1.57079632679;
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
      };
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      state.timerWebgl = renderer;
      return renderer;
    } catch (_error) {
      return null;
    }
  }

  function drawTimerRingFrame(renderer) {
    const timer = renderer.timer;
    if (!timer) {
      return;
    }
    const { width, height } = resizeWebglCanvas(renderer);
    const gl = renderer.gl;
    let progress = clamp(Number(timer.progress || 0), 0, 1);
    if (timer.active && timer.total > 0) {
      const elapsed = Math.max(0, Date.now() - timer.startedAt);
      progress = clamp((timer.remaining - elapsed) / timer.total, 0, 1);
    }
    const color = parseTimerColor(timer.color);
    gl.clearColor(0, 0, 0, 0);
    gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(renderer.program);
    gl.bindBuffer(gl.ARRAY_BUFFER, renderer.buffer);
    gl.enableVertexAttribArray(renderer.positionLocation);
    gl.vertexAttribPointer(renderer.positionLocation, 2, gl.FLOAT, false, 0, 0);
    gl.uniform2f(renderer.resolutionLocation, width, height);
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

  function syncTimerRingWebgl(timerHero, timer, color, progress, active) {
    const renderer = ensureTimerRingRenderer();
    if (!renderer) {
      timerHero?.classList.remove("webgl-timer-ready");
      return;
    }
    timerHero?.classList.add("webgl-timer-ready");
    renderer.timer = {
      color,
      progress,
      active: Boolean(active),
      remaining: Number(timer?.remaining || 0),
      total: Number(timer?.total || 0),
      startedAt: Date.now(),
    };
    if (renderer.frameId) {
      window.cancelAnimationFrame(renderer.frameId);
      renderer.frameId = 0;
    }
    renderer.running = true;
    drawTimerRingFrame(renderer);
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
    const sphereMode = getSphereMode(data);
    const ultraLowResource = getRenderMode(data) === "ultra_low_resource";
    if (["again", "hard", "good", "easy"].includes(data.lastEventType)) {
      if (!lightweightRows && !ultraLowResource) {
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
    } else if (data.lastEventType === "review-later-added") {
      showToast("Review Later");
    } else if (data.lastEventType === "review-later-removed") {
      showToast("Removed from 'Review Later'");
    } else if (data.lastEventType === "timeout") {
      if (lightweightRows) {
        spawnRowsTimeoutFlash();
        spawnRowsTimeoutCollapse();
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
    const kind = String(data.lastEventType || "");
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
    if (!timerHero || !timerValue || !phaseLabel) {
      return;
    }

    if (!enabled) {
      setText("acgTimer", "Off");
      setText(phaseLabel, "Off");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", "#8c96ac");
      syncTimerRingWebgl(timerHero, timer, "#8c96ac", 1, false);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (!visualsEnabled) {
      setText("acgTimer", "Vibration only");
      setText(phaseLabel, "Vibration");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", "#8c96ac");
      syncTimerRingWebgl(timerHero, timer, "#8c96ac", 1, false);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.phase === "idle") {
      const timerRamp = getTimerRampColors(data);
      setText("acgTimer", "Ready");
      setText(phaseLabel, "Ready");
      setText(timerValue, "--");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", timerRamp.idle);
      syncTimerRingWebgl(timerHero, timer, timerRamp.idle, 1, false);
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.free) {
      const timerRamp = getTimerRampColors(data);
      setText("acgTimer", "First card free");
      setText(phaseLabel, "Question");
      setText(timerValue, "FREE");
      setStyleProperty(timerHero, "--timer-progress", "1turn");
      setStyleProperty(timerHero, "--timer-color", timerRamp.free);
      syncTimerRingWebgl(timerHero, timer, timerRamp.free, 1, false);
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
      syncTimerRingWebgl(timerHero, timer, color, ratio, !timer.paused && timer.remaining > 0);
      timerHero.classList.toggle("danger", danger);
      timerValue.classList.toggle("danger", danger);
    }

    if (timeDrainOverlay && timeDrainTimer) {
      const activeTimeDrain = enabled
        && visualsEnabled
        && Number(data?.timeDrainFlag || 0) > 0
        && Number(data?.currentCardFlag || 0) === Number(data?.timeDrainFlag || 0)
        && timer.phase === "question";
      timeDrainOverlay.classList.toggle("visible", activeTimeDrain);
      setText(timeDrainTimer, timer.free ? "FREE" : timer.phase === "idle" ? "--" : timer.secondsText);
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
    handleStateEffects(data);
    if (enabled && visualsEnabled && !sidebarCollapsed && lightweightRows) {
      clearOrbitScene();
      renderLightweightRows(data);
    } else if (enabled && visualsEnabled && orbitAnimationEnabled && !sidebarCollapsed) {
      clearRowsScene();
      renderRings(colors, data);
    } else {
      clearOrbitScene();
      clearRowsScene();
    }
    state.prevColors = colors.slice();
    state.prevStreak = streak;
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
