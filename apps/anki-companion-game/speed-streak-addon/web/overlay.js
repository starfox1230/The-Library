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
  };

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
          <div id="acgTimer" class="acg-timer">Ready</div>
          <button id="acgSettingsButton" class="acg-action" type="button">Settings</button>
        </div>
        <div id="acgDim" class="acg-dim"></div>
        <div id="acgPauseOverlay" class="acg-pause-overlay">
          <div class="acg-pause-copy">Press 'P' to Unpause</div>
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
            <div class="acg-form-row">
              <label class="acg-form-label" for="acgQuestionSeconds">Question Time</label>
              <input id="acgQuestionSeconds" class="acg-input" type="number" min="1" step="0.5" />
            </div>
            <div class="acg-form-row">
              <label class="acg-form-label" for="acgAnswerSeconds">Answer Time</label>
              <input id="acgAnswerSeconds" class="acg-input" type="number" min="1" step="0.5" />
            </div>
            <div class="acg-form-row">
              <label class="acg-form-label">Time Drain Flag</label>
              <select id="acgTimeDrainFlag" class="acg-select"></select>
            </div>
            <div class="acg-form-row">
              <label class="acg-form-label">Review Later Flag</label>
              <select id="acgReviewLaterFlag" class="acg-select"></select>
            </div>
            <div class="acg-button-stack">
              <button id="acgReviewLaterManagerButton" class="acg-action acg-action-primary" type="button">Review Later Manager</button>
              <button id="acgPauseStatsButton" class="acg-action" type="button">Show Total Pause Time</button>
              <button id="acgShortcutsButton" class="acg-action" type="button">Shortcuts</button>
              <button id="acgHelpButton" class="acg-action" type="button">How It Works</button>
              <button id="acgDefaultSettingsButton" class="acg-action" type="button">Default Settings</button>
              <button id="acgResetGameButton" class="acg-action" type="button">Reset Game</button>
            </div>
            <div id="acgPauseStatsPanel" class="acg-panel hidden">
              <div id="acgPauseStatsCopy" class="acg-panel-copy">Total pause time: 0.0s</div>
            </div>
            <div id="acgShortcutsPanel" class="acg-panel hidden">
              <div class="acg-panel-copy"><strong>P</strong> pauses or unpauses the timer.</div>
            </div>
            <div id="acgHelpPanel" class="acg-panel hidden">
              <div class="acg-panel-copy">
                This sidebar runs a two-phase timer for each card. The question timer runs while you are deciding what the answer is, and the answer timer runs after you reveal the card. The very first synced card is free so the session can start cleanly.
                <br><br>
                Every time you rate a card on time, your streak goes up by one and a new satellite is added to the orbit. Again adds a red satellite, Hard adds yellow, Good adds green, and Easy adds blue. The number in the center orb is your current streak, and the score at the top grows with a streak multiplier so longer runs are worth more.
                <br><br>
                If either timer expires, the streak is lost, the orb flashes into a failed state, and the orbit collapses. If you bury or hide a card, the next card gets a fresh timer without changing the streak or score.
                <br><br>
                Press <strong>P</strong> to pause or unpause. Opening Settings also pauses automatically. While paused, the sidebar dims and waits for you to resume. You can change the question and answer timers in Settings, and those settings persist across Anki restarts.
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
        if (!state.data?.paused && typeof pycmd === "function") {
          pycmd("speed-streak:toggle-pause");
        }
        setSettingsOpen(true);
      });
    }

    const resetButton = document.getElementById("acgResetGameButton");
    if (resetButton) {
      resetButton.addEventListener("click", () => {
        if (typeof pycmd === "function") {
          pycmd("speed-streak:reset");
        }
        setSettingsOpen(false);
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

    const pauseStatsButton = document.getElementById("acgPauseStatsButton");
    if (pauseStatsButton) {
      pauseStatsButton.addEventListener("click", () => togglePanel("acgPauseStatsPanel"));
    }

    const shortcutsButton = document.getElementById("acgShortcutsButton");
    if (shortcutsButton) {
      shortcutsButton.addEventListener("click", () => togglePanel("acgShortcutsPanel"));
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
        const ok = window.confirm("Reset timer settings and both watched flags to defaults?");
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
    const modal = $("acgSettingsModal");
    const dim = $("acgDim");
    const pauseOverlay = $("acgPauseOverlay");
    if (modal) {
      modal.classList.toggle("visible", open);
    }
    if (dim) {
      dim.classList.toggle("visible", open || Boolean(state.data?.paused));
    }
    if (pauseOverlay) {
      pauseOverlay.classList.toggle("visible", Boolean(state.data?.paused) && !open);
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

  function saveSettings() {
    const q = Number($("acgQuestionSeconds")?.value || 12);
    const a = Number($("acgAnswerSeconds")?.value || 8);
    const f = Number($("acgTimeDrainFlag")?.value || 0);
    const rl = Number($("acgReviewLaterFlag")?.value || 0);
    if (f > 0 && rl > 0 && f === rl) {
      return;
    }
    if (typeof pycmd === "function") {
      pycmd(
        `speed-streak:update-settings:${JSON.stringify({ questionSeconds: q, answerSeconds: a, timeDrainFlag: f, reviewLaterFlag: rl })}`
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
    renderFlagSelects(Number(data.timeDrainFlag || 0), Number(data.reviewLaterFlag || 0));
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

    const colors = Array.isArray(data.satelliteColors) ? data.satelliteColors : [];
    const timer = computeTimer(data);
    const core = $("acgCore");
    const timerHero = $("acgTimerHero");
    const timerValue = $("acgTimerValue");
    const phaseLabel = $("acgPhaseLabel");
    const timeDrainOverlay = $("acgTimeDrainOverlay");
    const timeDrainTimer = $("acgTimeDrainTimer");
    const score = Number(data.score || 0);
    const multiplier = Number(data.streakMultiplier || 1);
    const streak = Number(data.streak || 0);
    const field = $("acgField");
    const coreWrap = document.querySelector(".acg-core-wrap");

    $("acgStreak").textContent = String(streak);
    $("acgScore").textContent = score.toLocaleString();
    $("acgMultiplier").textContent = `x${multiplier.toFixed(2)} multiplier`;

    if (coreWrap) {
      const coreSize = clamp(58 + (streak * 2.8), 58, 142);
      coreWrap.style.setProperty("--core-size", `${coreSize}px`);
    }
    if (field) {
      field.style.filter = `saturate(${clamp(1 + (streak * 0.04), 1, 2.4)}) brightness(${clamp(1 + (streak * 0.015), 1, 1.45)})`;
    }

    if (timer.phase === "idle") {
      $("acgTimer").textContent = "Ready";
      phaseLabel.textContent = "Ready";
      timerValue.textContent = "--";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", "#7fb0ff");
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else if (timer.free) {
      $("acgTimer").textContent = "First card free";
      phaseLabel.textContent = "Question";
      timerValue.textContent = "FREE";
      timerHero.style.setProperty("--timer-progress", "1turn");
      timerHero.style.setProperty("--timer-color", "#65f0c2");
      timerHero.classList.remove("danger");
      timerValue.classList.remove("danger");
    } else {
      const seconds = Math.max(0, timer.remaining / 1000);
      const ratio = timer.total ? clamp(timer.remaining / timer.total, 0, 1) : 0;
      const danger = ratio <= 0.3;
      const green = [101, 240, 194];
      const yellow = [255, 217, 120];
      const red = [255, 111, 150];
      const blendTarget = ratio > 0.5 ? yellow : red;
      const blendStart = ratio > 0.5 ? green : yellow;
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
    $("acgPauseStatsCopy").textContent = `Total pause time: ${(Number(data.totalPauseMs || 0) / 1000).toFixed(1)}s`;
    const dim = $("acgDim");
    const pauseOverlay = $("acgPauseOverlay");
    if (dim) {
      dim.classList.toggle("visible", Boolean(data.paused) || state.settingsOpen);
    }
    if (pauseOverlay) {
      pauseOverlay.classList.toggle("visible", Boolean(data.paused) && !state.settingsOpen);
    }
    if (timeDrainOverlay && timeDrainTimer) {
      const activeTimeDrain = Number(data.timeDrainFlag || 0) > 0
        && Number(data.currentCardFlag || 0) === Number(data.timeDrainFlag || 0)
        && timer.phase === "question";
      timeDrainOverlay.classList.toggle("visible", activeTimeDrain);
      timeDrainTimer.textContent = timer.free ? "FREE" : timer.phase === "idle" ? "--" : Math.max(0, timer.remaining / 1000).toFixed(1);
    }
    handleStateEffects(data);
    renderRings(colors);
    state.prevColors = colors.slice();
    state.prevStreak = streak;
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
