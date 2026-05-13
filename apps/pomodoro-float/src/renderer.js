const STORAGE_KEY = 'pomodoro-float-state-v1';
const CIRCLE_LENGTH = 2 * Math.PI * 104;

const defaultState = {
  mode: 'focus',
  running: false,
  remaining: 25 * 60,
  sessionStartedAt: null,
  completedToday: 0,
  streak: 0,
  round: 1,
  durations: {
    focus: 25,
    short: 5,
    long: 15,
  },
  roundsBeforeLongBreak: 4,
  autoStart: false,
  theme: 'aurora',
  miniMode: false,
  scale: 1,
  alwaysOnTop: true,
  launchAtLogin: true,
  lastStatsDate: todayKey(),
};

let state = loadState();
let tickTimer = null;
let webgl = null;

const $ = (selector) => document.querySelector(selector);
const elements = {
  shell: $('.shell'),
  timeLeft: $('#time-left'),
  sessionTitle: $('#session-title'),
  cycleLabel: $('#cycle-label'),
  ring: $('#ring-progress'),
  tabs: [...document.querySelectorAll('.tab')],
  toggle: $('#toggle-timer'),
  reset: $('#reset-timer'),
  skip: $('#skip-session'),
  mini: $('#mini-toggle'),
  hide: $('#hide-window'),
  quit: $('#quit-app'),
  completed: $('#completed-count'),
  streak: $('#current-streak'),
  next: $('#next-label'),
  focus: $('#focus-minutes'),
  short: $('#short-minutes'),
  long: $('#long-minutes'),
  rounds: $('#rounds'),
  autoStart: $('#auto-start'),
  theme: $('#theme'),
  scale: $('#scale'),
  alwaysOnTop: $('#always-on-top'),
  launchAtLogin: $('#launch-at-login'),
  canvas: $('#ambient-canvas'),
};

initialize();

async function initialize() {
  const nativeSettings = await window.pomodoroNative?.getNativeSettings?.();
  if (nativeSettings) {
    state = { ...state, ...nativeSettings };
  }

  resetDailyStatsIfNeeded();
  setupWebgl();
  bindEvents();
  render();
  persist();
  syncNativeSettings();
  startTicker();
}

function bindEvents() {
  elements.toggle.addEventListener('click', toggleTimer);
  elements.reset.addEventListener('click', resetCurrentSession);
  elements.skip.addEventListener('click', () => completeSession(true));
  elements.mini.addEventListener('click', () => {
    state.miniMode = !state.miniMode;
    render();
    syncNativeSettings();
    persist();
  });
  elements.hide.addEventListener('click', () => window.pomodoroNative?.hide?.());
  elements.quit.addEventListener('click', () => window.pomodoroNative?.quit?.());

  elements.tabs.forEach((tab) => {
    tab.addEventListener('click', () => setMode(tab.dataset.mode, true));
  });

  [
    ['focus', 'focus'],
    ['short', 'short'],
    ['long', 'long'],
  ].forEach(([key, mode]) => {
    elements[key].addEventListener('change', () => {
      state.durations[mode] = clampNumber(elements[key].value, 1, mode === 'focus' ? 180 : 90);
      if (state.mode === mode && !state.running) {
        state.remaining = state.durations[mode] * 60;
      }
      render();
      persist();
    });
  });

  elements.rounds.addEventListener('change', () => {
    state.roundsBeforeLongBreak = clampNumber(elements.rounds.value, 1, 12);
    state.round = Math.min(state.round, state.roundsBeforeLongBreak);
    render();
    persist();
  });

  elements.autoStart.addEventListener('change', () => {
    state.autoStart = elements.autoStart.checked;
    persist();
  });

  elements.theme.addEventListener('change', () => {
    state.theme = elements.theme.value;
    render();
    persist();
  });

  elements.scale.addEventListener('input', () => {
    state.scale = Number(elements.scale.value);
    render();
  });
  elements.scale.addEventListener('change', () => {
    syncNativeSettings();
    persist();
  });

  elements.alwaysOnTop.addEventListener('change', () => {
    state.alwaysOnTop = elements.alwaysOnTop.checked;
    syncNativeSettings();
    persist();
  });

  elements.launchAtLogin.addEventListener('change', () => {
    state.launchAtLogin = elements.launchAtLogin.checked;
    syncNativeSettings();
    persist();
  });

  window.pomodoroNative?.onTimerCommand?.((command) => {
    if (command === 'toggle') toggleTimer();
    if (command === 'reset') resetCurrentSession();
  });

  window.pomodoroNative?.onNativeSettings?.((settings) => {
    state = { ...state, ...settings };
    render();
    persist();
  });

  window.addEventListener('resize', resizeWebgl);
}

function startTicker() {
  if (tickTimer) clearInterval(tickTimer);
  tickTimer = setInterval(() => {
    if (!state.running) return;
    state.remaining -= 1;
    if (state.remaining <= 0) {
      completeSession(false);
    } else {
      renderTimer();
      persist();
    }
  }, 1000);
}

function toggleTimer() {
  state.running = !state.running;
  state.sessionStartedAt = state.running ? Date.now() : null;
  render();
  persist();
}

function resetCurrentSession() {
  state.running = false;
  state.remaining = state.durations[state.mode] * 60;
  state.sessionStartedAt = null;
  render();
  persist();
}

function completeSession(skipped) {
  const completedMode = state.mode;
  const wasFocus = completedMode === 'focus';

  if (!skipped && wasFocus) {
    state.completedToday += 1;
    state.streak += 1;
  }

  const nextMode = getNextMode(completedMode);
  const notificationTitle = skipped ? 'Session skipped' : `${labelForMode(completedMode)} complete`;
  const notificationBody = nextMode === 'focus' ? 'Time to focus again.' : `Take a ${labelForMode(nextMode).toLowerCase()}.`;
  window.pomodoroNative?.notify?.({ title: notificationTitle, body: notificationBody });

  setMode(nextMode, false);
  state.running = state.autoStart;
  state.sessionStartedAt = state.running ? Date.now() : null;
  render();
  persist();
}

function getNextMode(completedMode) {
  if (completedMode !== 'focus') return 'focus';
  if (state.round >= state.roundsBeforeLongBreak) {
    state.round = 1;
    return 'long';
  }
  state.round += 1;
  return 'short';
}

function setMode(mode, manual) {
  state.mode = mode;
  state.running = false;
  state.remaining = state.durations[mode] * 60;
  state.sessionStartedAt = null;
  if (manual && mode === 'focus') {
    state.round = Math.min(state.round, state.roundsBeforeLongBreak);
  }
  render();
  persist();
}

function render() {
  resetDailyStatsIfNeeded();
  document.body.className = `theme-${state.theme}`;
  elements.shell.classList.toggle('mini', state.miniMode);
  elements.shell.dataset.mode = state.mode;
  document.documentElement.style.setProperty('--scale', state.scale);

  elements.sessionTitle.textContent = labelForMode(state.mode);
  elements.tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.mode === state.mode));
  elements.toggle.textContent = state.running ? 'Pause' : 'Start';
  elements.mini.textContent = state.miniMode ? '▣' : '□';
  elements.completed.textContent = state.completedToday;
  elements.streak.textContent = state.streak;
  elements.next.textContent = labelForMode(peekNextMode());

  elements.focus.value = state.durations.focus;
  elements.short.value = state.durations.short;
  elements.long.value = state.durations.long;
  elements.rounds.value = state.roundsBeforeLongBreak;
  elements.autoStart.checked = state.autoStart;
  elements.theme.value = state.theme;
  elements.scale.value = state.scale;
  elements.alwaysOnTop.checked = state.alwaysOnTop;
  elements.launchAtLogin.checked = state.launchAtLogin;

  renderTimer();
  updateWebglTheme();
}

function renderTimer() {
  elements.timeLeft.textContent = formatTime(state.remaining);
  const durationSeconds = state.durations[state.mode] * 60;
  const elapsed = Math.max(0, durationSeconds - state.remaining);
  const progress = durationSeconds > 0 ? elapsed / durationSeconds : 0;
  elements.ring.style.strokeDasharray = CIRCLE_LENGTH;
  elements.ring.style.strokeDashoffset = CIRCLE_LENGTH * (1 - progress);
  elements.cycleLabel.textContent = state.mode === 'focus'
    ? `Round ${state.round} of ${state.roundsBeforeLongBreak}`
    : `${labelForMode(state.mode)} session`;
}

function peekNextMode() {
  if (state.mode !== 'focus') return 'focus';
  return state.round >= state.roundsBeforeLongBreak ? 'long' : 'short';
}

function labelForMode(mode) {
  return {
    focus: 'Focus',
    short: 'Short break',
    long: 'Long break',
  }[mode] || 'Focus';
}

function formatTime(seconds) {
  const safeSeconds = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(safeSeconds / 60).toString().padStart(2, '0');
  const remainder = (safeSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${remainder}`;
}

function clampNumber(value, min, max) {
  const parsed = Number.parseInt(value, 10);
  if (Number.isNaN(parsed)) return min;
  return Math.max(min, Math.min(max, parsed));
}

function syncNativeSettings() {
  window.pomodoroNative?.updateNativeSettings?.({
    alwaysOnTop: state.alwaysOnTop,
    launchAtLogin: state.launchAtLogin,
    miniMode: state.miniMode,
    scale: state.scale,
  });
}

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return {
      ...defaultState,
      ...saved,
      durations: { ...defaultState.durations, ...(saved?.durations || {}) },
      running: false,
      remaining: saved?.remaining || defaultState.remaining,
    };
  } catch {
    return { ...defaultState };
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function todayKey() {
  return new Date().toISOString().slice(0, 10);
}

function resetDailyStatsIfNeeded() {
  const key = todayKey();
  if (state.lastStatsDate === key) return;
  state.completedToday = 0;
  state.streak = 0;
  state.lastStatsDate = key;
}

function setupWebgl() {
  const gl = elements.canvas.getContext('webgl', { antialias: false, alpha: true, powerPreference: 'low-power' });
  if (!gl) return;

  const vertex = `
    attribute vec2 position;
    void main() {
      gl_Position = vec4(position, 0.0, 1.0);
    }
  `;
  const fragment = `
    precision mediump float;
    uniform vec2 u_resolution;
    uniform float u_time;
    uniform vec3 u_accent;
    uniform vec3 u_accent2;
    uniform vec3 u_bg;

    float softCircle(vec2 uv, vec2 center, float radius, float blur) {
      float d = distance(uv, center);
      return smoothstep(radius + blur, radius - blur, d);
    }

    void main() {
      vec2 uv = gl_FragCoord.xy / u_resolution.xy;
      vec2 p = uv - 0.5;
      p.x *= u_resolution.x / u_resolution.y;
      float t = u_time * 0.08;
      float wave = sin((p.x * 4.0) + t) * cos((p.y * 5.0) - t * 1.4);
      vec3 color = u_bg;
      color += u_accent * softCircle(p, vec2(sin(t) * 0.22, cos(t * 1.3) * 0.18), 0.34 + wave * 0.03, 0.22) * 0.38;
      color += u_accent2 * softCircle(p, vec2(cos(t * 0.7) * -0.24, sin(t * 0.9) * 0.2), 0.29, 0.2) * 0.32;
      color += vec3(1.0) * pow(max(0.0, 1.0 - length(p) * 1.35), 3.0) * 0.05;
      gl_FragColor = vec4(color, 0.95);
    }
  `;

  const program = createProgram(gl, vertex, fragment);
  if (!program) return;

  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, -1, 1, 1, -1, 1, 1]), gl.STATIC_DRAW);

  webgl = {
    gl,
    program,
    position: gl.getAttribLocation(program, 'position'),
    resolution: gl.getUniformLocation(program, 'u_resolution'),
    time: gl.getUniformLocation(program, 'u_time'),
    accent: gl.getUniformLocation(program, 'u_accent'),
    accent2: gl.getUniformLocation(program, 'u_accent2'),
    bg: gl.getUniformLocation(program, 'u_bg'),
    colors: themeColors(state.theme),
    started: performance.now(),
  };

  resizeWebgl();
  requestAnimationFrame(drawWebgl);
}

function createProgram(gl, vertexSource, fragmentSource) {
  const vertex = compileShader(gl, gl.VERTEX_SHADER, vertexSource);
  const fragment = compileShader(gl, gl.FRAGMENT_SHADER, fragmentSource);
  if (!vertex || !fragment) return null;
  const program = gl.createProgram();
  gl.attachShader(program, vertex);
  gl.attachShader(program, fragment);
  gl.linkProgram(program);
  return gl.getProgramParameter(program, gl.LINK_STATUS) ? program : null;
}

function compileShader(gl, type, source) {
  const shader = gl.createShader(type);
  gl.shaderSource(shader, source);
  gl.compileShader(shader);
  return gl.getShaderParameter(shader, gl.COMPILE_STATUS) ? shader : null;
}

function resizeWebgl() {
  if (!webgl) return;
  const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
  const width = Math.floor(elements.canvas.clientWidth * ratio);
  const height = Math.floor(elements.canvas.clientHeight * ratio);
  if (elements.canvas.width !== width || elements.canvas.height !== height) {
    elements.canvas.width = width;
    elements.canvas.height = height;
    webgl.gl.viewport(0, 0, width, height);
  }
}

function drawWebgl(now) {
  if (!webgl) return;
  const { gl, program } = webgl;
  resizeWebgl();
  gl.useProgram(program);
  gl.enableVertexAttribArray(webgl.position);
  gl.vertexAttribPointer(webgl.position, 2, gl.FLOAT, false, 0, 0);
  gl.uniform2f(webgl.resolution, elements.canvas.width, elements.canvas.height);
  gl.uniform1f(webgl.time, (now - webgl.started) / 1000);
  gl.uniform3fv(webgl.accent, webgl.colors.accent);
  gl.uniform3fv(webgl.accent2, webgl.colors.accent2);
  gl.uniform3fv(webgl.bg, webgl.colors.bg);
  gl.drawArrays(gl.TRIANGLES, 0, 6);
  requestAnimationFrame(drawWebgl);
}

function updateWebglTheme() {
  if (!webgl) return;
  webgl.colors = themeColors(state.theme);
}

function themeColors(theme) {
  const palettes = {
    aurora: { bg: [0.035, 0.052, 0.09], accent: [0.49, 0.95, 0.83], accent2: [0.54, 0.65, 1.0] },
    midnight: { bg: [0.025, 0.04, 0.075], accent: [0.6, 0.84, 1.0], accent2: [0.49, 0.94, 0.74] },
    ember: { bg: [0.065, 0.05, 0.075], accent: [1.0, 0.82, 0.54], accent2: [1.0, 0.5, 0.66] },
    violet: { bg: [0.045, 0.043, 0.095], accent: [0.78, 0.65, 1.0], accent2: [0.45, 0.92, 1.0] },
  };
  return palettes[theme] || palettes.aurora;
}
