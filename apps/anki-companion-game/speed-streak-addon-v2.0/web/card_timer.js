(function () {
  if (window.SpeedStreakCardTimer) {
    return;
  }

  const state = {
    mounted: false,
    data: null,
    timerLoopId: 0,
    timerLoopSignature: "",
    timerVisualSignature: "",
    timerWebgl: null,
    lastBackground: "",
    lastBackgroundProbeAt: 0,
    lastBackgroundProbeKey: "",
    feedbackAudio: null,
    feedbackAudioSrc: "",
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
            <canvas id="sstCanvas" class="sst-canvas" aria-hidden="true"></canvas>
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

  function setText(node, value) {
    if (!node) {
      return;
    }
    const next = String(value ?? "");
    if (node.textContent !== next) {
      node.textContent = next;
    }
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

  function setSmoothTimerProgress(root, ratio, remainingMs, signature, active) {
    if (!root) {
      return;
    }
    const progress = clamp(Number(ratio || 0), 0, 1);
    if (!active || remainingMs <= 0) {
      state.timerVisualSignature = "";
      setStyleProperty(root, "--sst-transition-ms", "0ms");
      setStyleProperty(root, "--sst-progress", `${progress}`);
      return;
    }
    if (signature === state.timerVisualSignature) {
      return;
    }
    state.timerVisualSignature = signature;
    setStyleProperty(root, "--sst-transition-ms", "0ms");
    setStyleProperty(root, "--sst-progress", `${progress}`);
    window.requestAnimationFrame(() => {
      if (signature !== state.timerVisualSignature) {
        return;
      }
      setStyleProperty(root, "--sst-transition-ms", `${Math.max(0, Math.round(remainingMs))}ms`);
      setStyleProperty(root, "--sst-progress", "0");
    });
  }

  function parseTimerColor(color) {
    const text = String(color || "").trim();
    const rgbMatch = text.match(/^rgba?\(([^)]+)\)$/i);
    if (rgbMatch) {
      const parts = rgbMatch[1].split(",").map((part) => Number(part.trim()));
      return [clamp(parts[0] || 0, 0, 255) / 255, clamp(parts[1] || 0, 0, 255) / 255, clamp(parts[2] || 0, 0, 255) / 255, 1];
    }
    const normalized = normalizeHexColor(text) || "#7fb0ff";
    return [
      Number.parseInt(normalized.slice(1, 3), 16) / 255,
      Number.parseInt(normalized.slice(3, 5), 16) / 255,
      Number.parseInt(normalized.slice(5, 7), 16) / 255,
      1,
    ];
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

  function createTimerBarProgram(gl) {
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
        vec2 uv = gl_FragCoord.xy / u_resolution;
        float fill = step(uv.x, clamp(u_progress, 0.0, 1.0));
        gl_FragColor = vec4(u_color.rgb, u_color.a * fill);
      }
    `);
    const program = gl.createProgram();
    gl.attachShader(program, vertex);
    gl.attachShader(program, fragment);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      throw new Error(gl.getProgramInfoLog(program) || "WebGL timer bar link failed.");
    }
    return program;
  }

  function ensureTimerBarRenderer() {
    const canvas = document.getElementById("sstCanvas");
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
      const program = createTimerBarProgram(gl);
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

  function resizeTimerBarCanvas(renderer) {
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
    return { width, height, bufferWidth: nextWidth, bufferHeight: nextHeight };
  }

  function drawTimerBarFrame(renderer) {
    const timer = renderer.timer;
    if (!timer) {
      return;
    }
    const { bufferWidth, bufferHeight } = resizeTimerBarCanvas(renderer);
    let progress = clamp(Number(timer.progress || 0), 0, 1);
    if (timer.active && timer.total > 0) {
      progress = clamp((timer.remaining - Math.max(0, Date.now() - timer.startedAt)) / timer.total, 0, 1);
    }
    const color = parseTimerColor(timer.color);
    const gl = renderer.gl;
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
      renderer.frameId = window.requestAnimationFrame(() => drawTimerBarFrame(renderer));
    } else {
      renderer.frameId = 0;
    }
  }

  function syncTimerBarWebgl(root, timer, color, progress, active) {
    const renderer = ensureTimerBarRenderer();
    if (!renderer) {
      root?.classList.remove("webgl-timer-ready");
      return;
    }
    root?.classList.add("webgl-timer-ready");
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
    drawTimerBarFrame(renderer);
  }

  function getRenderMode(data) {
    const normalized = String(data?.renderMode || "classic").trim().toLowerCase();
    if (normalized === "ultra_low_resource") {
      return "ultra_low_resource";
    }
    return normalized === "low_resource" ? "low_resource" : "classic";
  }

  function getTimerStepMs(data) {
    const explicit = Math.max(0, Number(data?.timerDisplayStepMs || 0));
    if (explicit) {
      return explicit;
    }
    if (getVisualMode(data) === "lightweight_rows") {
      return 100;
    }
    return getRenderMode(data) === "ultra_low_resource" ? 500 : 100;
  }

  function stopTimerLoop() {
    if (state.timerLoopId) {
      window.clearTimeout(state.timerLoopId);
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
      Number(data?.showCardTimer || 0),
    ].join("|");
  }

  function needsLiveTimerLoop(data) {
    if (!data || !Number(data.enabled || 0) || !Number(data.visualsEnabled || 0) || !Number(data.showCardTimer || 0)) {
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
      renderTimerState(state.data);
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

    if (!data.enabled || !data.visualsEnabled || !data.showCardTimer || phase === "idle" || !Number(data.phaseStartEpochMs || 0)) {
      return { visible: false };
    }
    if (free || !limit) {
      return { visible: true, free: true, phase, paused: false, remaining: 0, total: 0, secondsText: "0.0" };
    }
    const remaining = paused
      ? Math.max(0, Number(data.timerDisplayRemainingMs || 0))
      : computeSharedRemainingMs(data);
    if (paused) {
      return {
        visible: true,
        free: false,
        phase,
        paused: true,
        remaining,
        total: limit,
        secondsText: formatTimerSecondsText(remaining),
      };
    }
    return {
      visible: true,
      free: false,
      phase,
      paused: false,
      remaining,
      total: limit,
      secondsText: formatTimerSecondsText(remaining),
    };
  }

  function blendRgb(a, b, t) {
    const r = Math.round(a[0] + ((b[0] - a[0]) * t));
    const g = Math.round(a[1] + ((b[1] - a[1]) * t));
    const bl = Math.round(a[2] + ((b[2] - a[2]) * t));
    return `rgb(${r}, ${g}, ${bl})`;
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

  function normalizeThemeKey(themeKey) {
    const normalized = String(themeKey || "midnight").trim().toLowerCase() || "midnight";
    return normalized === "card" ? "cardmatch" : normalized;
  }

  function themeDefaultColors(themeKey) {
    return { ...DEFAULT_CUSTOM_COLORS, ...(THEME_CUSTOM_COLOR_DEFAULTS[normalizeThemeKey(themeKey)] || {}) };
  }

  function normalizeCustomColors(customColors) {
    const normalized = {};
    if (!customColors || typeof customColors !== "object") {
      return normalized;
    }
    Object.keys(DEFAULT_CUSTOM_COLORS).forEach((key) => {
      const value = normalizeHexColor(customColors[key]);
      if (value) {
        normalized[key] = value;
      }
    });
    return normalized;
  }

  function resolveCustomColors(data) {
    return {
      ...themeDefaultColors(data?.appearanceMode || "midnight"),
      ...normalizeCustomColors(data?.customColors || {}),
    };
  }

  function getTimerRampColors(data) {
    if (Boolean(data?.customTimerColors)) {
      const palette = resolveCustomColors(data);
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

  function syncSidebarBackground(data) {
    const probeKey = `${Number(data?.phaseStartEpochMs || 0)}|${String(data?.phase || "idle")}`;
    const now = Date.now();
    if (probeKey === state.lastBackgroundProbeKey && (now - state.lastBackgroundProbeAt) < 1000) {
      return;
    }
    state.lastBackgroundProbeKey = probeKey;
    state.lastBackgroundProbeAt = now;
    const color = detectCardBackground();
    if (!color || color === state.lastBackground) {
      return;
    }
    state.lastBackground = color;
    if (typeof pycmd === "function") {
      pycmd(`speed-streak:card-background:${encodeURIComponent(JSON.stringify({ color }))}`);
    }
  }

  function renderTimerState(data) {
    const root = document.getElementById("speed-streak-card-timer");
    const value = document.getElementById("sstValue");
    const fill = document.getElementById("sstFill");
    if (!root || !value || !fill) {
      return;
    }

    const timer = computeTimer(data);
    if (!timer.visible) {
      state.timerVisualSignature = "";
      root.classList.remove("webgl-timer-ready");
      root.classList.add("hidden");
      setStyleProperty(document.documentElement, "--speed-streak-card-offset", "0px");
      return;
    }

    root.classList.remove("hidden");
    root.classList.remove("danger");
    setStyleProperty(document.documentElement, "--speed-streak-card-offset", "42px");

    if (timer.free) {
      const timerRamp = getTimerRampColors(data);
      setText(value, "FREE");
      setSmoothTimerProgress(root, 1, 0, "", false);
      setStyleProperty(root, "--sst-color", timerRamp.free);
      syncTimerBarWebgl(root, timer, timerRamp.free, 1, false);
      return;
    }

    const timerRamp = getTimerRampColors(data);
    const ratio = timer.total ? clamp(timer.remaining / timer.total, 0, 1) : 0;
    const maxLabelSeconds = Math.max(Number(timer.total || 0) / 1000, Number(timer.secondsText || 0));
    const labelWidth = Math.max(4, `${maxLabelSeconds.toFixed(1)}s`.length);
    const danger = ratio <= 0.3;
    const blendTarget = ratio > 0.5 ? timerRamp.yellow : timerRamp.red;
    const blendStart = ratio > 0.5 ? timerRamp.green : timerRamp.yellow;
    const localT = ratio > 0.5 ? (1 - ratio) / 0.5 : (0.5 - ratio) / 0.5;
    const color = blendRgb(blendStart, blendTarget, clamp(localT, 0, 1));

    setStyleProperty(root, "--sst-value-width", `${labelWidth}ch`);
    setText(value, `${timer.secondsText}s`);
    setStyleProperty(root, "--sst-color", color);
    syncTimerBarWebgl(root, timer, color, ratio, !timer.paused && timer.remaining > 0);
    setSmoothTimerProgress(
      root,
      ratio,
      timer.remaining,
      `${String(data.phase || "")}|${Number(data.phaseStartEpochMs || 0)}|${Number(data.phaseLimitMs || 0)}|${Number(data.paused || 0)}`,
      !timer.paused && timer.remaining > 0
    );
    root.classList.toggle("danger", danger);
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
    syncSidebarBackground(data);
    renderTimerState(data);
  }

  function ensureFeedbackAudio() {
    if (state.feedbackAudio) {
      return state.feedbackAudio;
    }
    const audio = new Audio();
    audio.preload = "auto";
    state.feedbackAudio = audio;
    return audio;
  }

  function playFeedbackAudio(url, interrupt) {
    if (!url) {
      return false;
    }
    const audio = ensureFeedbackAudio();
    if (!interrupt && !audio.paused && !audio.ended) {
      return false;
    }
    try {
      if (state.feedbackAudioSrc !== url) {
        audio.src = url;
        state.feedbackAudioSrc = url;
      }
      audio.currentTime = 0;
      const playPromise = audio.play();
      if (playPromise && typeof playPromise.catch === "function") {
        playPromise.catch(() => {});
      }
      return true;
    } catch (_error) {
      return false;
    }
  }

  window.SpeedStreakCardTimer = {
    receiveState(nextState) {
      ensureMounted();
      render(nextState);
      syncTimerLoop();
    },
    playFeedbackAudio(url, interrupt = true) {
      ensureMounted();
      return playFeedbackAudio(String(url || ""), Boolean(interrupt));
    },
    hide() {
      state.data = null;
      state.timerLoopSignature = "";
      state.timerVisualSignature = "";
      stopTimerLoop();
      setStyleProperty(document.documentElement, "--speed-streak-card-offset", "0px");
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
