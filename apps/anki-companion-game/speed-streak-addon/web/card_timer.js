(function () {
  if (window.SpeedStreakCardTimer) {
    return;
  }

  const state = {
    mounted: false,
    data: null,
    animationId: 0,
    lastBackground: "",
  };

  function ensureMounted() {
    if (state.mounted) {
      return;
    }
    const host = document.body || document.documentElement;
    if (!host) {
      return;
    }
    host.insertAdjacentHTML(
      "beforeend",
      `
      <div id="speed-streak-card-timer" class="hidden">
        <div class="sst-head">
          <div class="sst-track">
            <div id="sstFill" class="sst-fill"></div>
          </div>
          <div id="sstValue" class="sst-value">--</div>
        </div>
      </div>
      `
    );
    state.mounted = true;
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

    if (!data.enabled || !data.visualsEnabled || !data.showCardTimer || phase === "idle" || !start) {
      return { visible: false };
    }
    if (free || !limit) {
      return { visible: true, free: true, phase, paused: false, remaining: 0, total: 0 };
    }
    if (paused) {
      return {
        visible: true,
        free: false,
        phase,
        paused: true,
        remaining: Number(data.pausedRemainingMs || 0),
        total: limit,
      };
    }
    const elapsed = Math.max(0, Date.now() - start);
    return {
      visible: true,
      free: false,
      phase,
      paused: false,
      remaining: Math.max(0, limit - elapsed),
      total: limit,
    };
  }

  function blendRgb(a, b, t) {
    const r = Math.round(a[0] + ((b[0] - a[0]) * t));
    const g = Math.round(a[1] + ((b[1] - a[1]) * t));
    const bl = Math.round(a[2] + ((b[2] - a[2]) * t));
    return `rgb(${r}, ${g}, ${bl})`;
  }

  function isTransparentColor(value) {
    if (!value) return true;
    const normalized = String(value).trim().toLowerCase();
    return normalized === "transparent" || normalized === "rgba(0, 0, 0, 0)" || normalized === "rgba(0,0,0,0)";
  }

  function detectCardBackground() {
    const selectors = ["#qa", ".card", "body", "html"];
    for (const selector of selectors) {
      const node = document.querySelector(selector);
      if (!node) continue;
      const color = window.getComputedStyle(node).backgroundColor;
      if (!isTransparentColor(color)) {
        return color;
      }
    }
    return "";
  }

  function syncSidebarBackground() {
    const color = detectCardBackground();
    if (!color || color === state.lastBackground) {
      return;
    }
    state.lastBackground = color;
    if (typeof pycmd === "function") {
      pycmd(`speed-streak:card-background:${encodeURIComponent(JSON.stringify({ color }))}`);
    }
  }

  function render(data) {
    ensureMounted();
    const root = document.getElementById("speed-streak-card-timer");
    const value = document.getElementById("sstValue");
    const fill = document.getElementById("sstFill");
    if (!root || !value || !fill) {
      return;
    }

    state.data = data;
    syncSidebarBackground();
    const timer = computeTimer(data);
    if (!timer.visible) {
      root.classList.add("hidden");
      document.documentElement.style.setProperty("--speed-streak-card-offset", "0px");
      return;
    }

    root.classList.remove("hidden");
    root.classList.remove("danger");
    document.documentElement.style.setProperty("--speed-streak-card-offset", "42px");

    if (timer.free) {
      value.textContent = "FREE";
      root.style.setProperty("--sst-progress", "1");
      root.style.setProperty("--sst-color", "#65f0c2");
      return;
    }

    const seconds = Math.max(0, Number(timer.remaining || 0) / 1000);
    const ratio = timer.total ? clamp(timer.remaining / timer.total, 0, 1) : 0;
    const danger = ratio <= 0.3;
    const green = [101, 240, 194];
    const yellow = [255, 217, 120];
    const red = [255, 111, 150];
    const blendTarget = ratio > 0.5 ? yellow : red;
    const blendStart = ratio > 0.5 ? green : yellow;
    const localT = ratio > 0.5 ? (1 - ratio) / 0.5 : (0.5 - ratio) / 0.5;
    const color = blendRgb(blendStart, blendTarget, clamp(localT, 0, 1));

    value.textContent = `${seconds.toFixed(1)}s`;
    root.style.setProperty("--sst-progress", `${ratio}`);
    root.style.setProperty("--sst-color", color);
    root.classList.toggle("danger", danger);
  }

  function animationLoop() {
    if (state.data) {
      render(state.data);
    }
    state.animationId = window.requestAnimationFrame(animationLoop);
  }

  window.SpeedStreakCardTimer = {
    receiveState(nextState) {
      ensureMounted();
      render(nextState);
      if (!state.animationId) {
        state.animationId = window.requestAnimationFrame(animationLoop);
      }
    },
    hide() {
      state.data = null;
      document.documentElement.style.setProperty("--speed-streak-card-offset", "0px");
      const root = document.getElementById("speed-streak-card-timer");
      if (root) {
        root.classList.add("hidden");
      }
    },
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ensureMounted, { once: true });
  } else {
    ensureMounted();
  }
})();
