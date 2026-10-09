(() => {
  "use strict";
  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};
  const limits = Object.freeze({ question: 12000, answer: 8000 });
  const enabled = { stats: true, timer: true };
  let host = null, ui = null, ticker = null;
  let animationFrame = null;
  let phase = "none", card = null, lastTick = performance.now();
  let phaseMs = 0, cardMs = 0, completedMs = 0, reviews = 0;
  let running = false, waiting = null;

  // Time only visible review phases. Never read or retain card contents/IDs.
  function advance(now = performance.now()) {
    const delta = Math.max(0, now - lastTick);
    if (running && !document.hidden && waiting === null) {
      phaseMs += delta;
      cardMs += delta;
    }
    lastTick = now;
  }

  function snapshot() {
    advance();
    const activeMs = completedMs + cardMs;
    return {
      reviews, completedMs, activeMs,
      reviewsPerMinute: reviews && activeMs > 0 ? reviews * 60000 / activeMs : 0,
      averageSeconds: reviews ? completedMs / reviews / 1000 : null,
      phase, phaseMs, remainingMs: Math.max(0, (limits[phase] || 0) - phaseMs),
      paused: !running || document.hidden || waiting !== null,
      statsShown: enabled.stats, timerShown: enabled.timer,
    };
  }

  function beginReview() {
    advance();
    if (phase === "answer" && waiting === null) waiting = cardMs;
    render();
  }

  function completeReview() {
    advance();
    if (waiting === null) return;
    reviews += 1;
    completedMs += waiting;
    waiting = null;
    cardMs = phaseMs = 0;
    phase = "none";
  }

  function cancelReview() {
    advance();
    waiting = null;
  }

  function setText(node, value) {
    if (node.textContent !== value) node.textContent = value;
  }

  function createUi() {
    if (!document.body) return;
    if (host?.isConnected) return;
    host?.remove();
    host = document.createElement("div");
    host.id = "ankiweb-enhancer-session";
    const shadow = host.attachShadow({ mode: "open" });
    shadow.innerHTML = `
      <style>
        :host { all: initial; position: fixed; top: 0; left: 0; right: 0;
          display: block; z-index: 2147483000; pointer-events: none;
          --surface: #ffffff; --text: #182230; --muted: #526274; --border: #dce3ec;
          --track: #e4eaf2; --fill: #2872d1; --warning: #a45b00; --late: #bf3545;
          color: var(--text); font: 13px/1.4 system-ui, sans-serif; }
        :host([data-dark]) { --surface: #171a20; --text: #e5e7eb; --muted: #aeb9c8;
          --border: #343a46; --track: #303846; --fill: #7fb0ff;
          --warning: #ffb861; --late: #ff8291; color-scheme: dark; }
        :host([hidden]), [hidden] { display: none !important; }
        .wrap { box-sizing: border-box; max-width: 720px; margin: 8px auto;
          padding: 8px 14px; border: 1px solid var(--border); border-radius: 12px;
          background: var(--surface); box-shadow: 0 2px 8px #0000000d; }
        .timer { display: flex; align-items: center; gap: 10px; height: 24px; }
        .phase { font-size: 12px; color: var(--muted); width: 61px; }
        .value { font-weight: 700; font-variant-numeric: tabular-nums; width: 58px;
          text-align: right; white-space: nowrap; }
        .track { height: 5px; border-radius: 999px; overflow: hidden;
          flex: 1; background: var(--track); }
        .fill { width: 100%; height: 100%; transform-origin: left center;
          background: var(--fill); border-radius: inherit; will-change: transform; }
        .timer[data-urgency="warning"] { --fill: var(--warning); }
        .timer[data-urgency="late"] { --fill: var(--late); }
        .timer[data-urgency="late"] .value { color: var(--late); }
        .metrics { display: flex; justify-content: center; align-items: center;
          gap: 22px; min-height: 28px; color: var(--muted); }
        .metrics strong { font-weight: 700; color: var(--text);
          font-variant-numeric: tabular-nums; margin-right: 4px; }
        .metrics span { white-space: nowrap; }
        .hint { color: var(--muted); font-size: 10px; text-align: center; }
        @media (max-width: 760px) { .wrap { margin: 8px 12px; } }
        @media (max-width: 420px) { .metrics { gap: 10px; font-size: 11px; } }
      </style>
      <section class="wrap" aria-label="Review session statistics and pace timer">
        <div class="timer" role="timer" aria-live="off">
          <span class="phase">Question</span>
          <div class="track"><div class="fill"></div></div>
          <span class="value">12.0s</span>
        </div>
        <div class="metrics" aria-live="off">
          <span><strong id="cards">0</strong>cards reviewed</span>
          <span><strong id="rate">0.0</strong>reviews/min</span>
          <span><strong id="average">—</strong>sec/card</span>
        </div>
        <div class="hint">G: stats · T: timer</div>
      </section>`;
    ui = Object.fromEntries(["timer", "phase", "value", "fill", "metrics", "hint"]
      .map(name => [name, shadow.querySelector(`.${name}`)]));
    for (const name of ["cards", "rate", "average"]) ui[name] = shadow.getElementById(name);
    document.body.append(host);
  }

  function renderBar(data) {
    const ratio = data.remainingMs / (limits[phase] || 1);
    ui.fill.style.transform = `scaleX(${ratio})`;
    ui.timer.dataset.urgency = ratio === 0 ? "late" : ratio <= 0.25 ? "warning" : "normal";
  }

  function scheduleBar(data) {
    const animate = host?.isConnected && enabled.timer && !data.paused && data.remainingMs > 0;
    if (!animate) {
      if (animationFrame !== null) cancelAnimationFrame(animationFrame);
      animationFrame = null;
    } else if (animationFrame === null) {
      animationFrame = requestAnimationFrame(() => {
        animationFrame = null;
        const current = snapshot();
        renderBar(current);
        scheduleBar(current);
      });
    }
  }

  function render() {
    if (!host || !ui) return;
    const data = snapshot();
    const reviewing = phase !== "none";
    const shown = reviewing && (enabled.stats || enabled.timer);
    if (host.hidden === shown) host.hidden = !shown;
    host.toggleAttribute("data-dark", document.documentElement.hasAttribute("data-ankiweb-dark"));
    ui.timer.hidden = !enabled.timer;
    ui.metrics.hidden = !enabled.stats;
    setText(ui.cards, String(data.reviews));
    setText(ui.rate, data.reviewsPerMinute.toFixed(1));
    setText(ui.average, data.averageSeconds === null ? "—" : data.averageSeconds.toFixed(1));
    setText(ui.phase, phase === "answer" ? "Answer" : "Question");
    setText(ui.value, `${(data.remainingMs / 1000).toFixed(1)}s`);
    // Animate only the transform at the display's frame rate. Text/statistics
    // retain their slower refresh; no layout measurements or DOM polling per frame.
    renderBar(data);
    scheduleBar(data);
    ui.timer.setAttribute("aria-label", `${phase} pace timer: ${(data.remainingMs / 1000).toFixed(1)} seconds remaining${data.paused ? ", paused" : ""}`);
    const root = document.documentElement;
    root.toggleAttribute("data-ankiweb-session-ui", shown);
    const offset = shown ? `${host.getBoundingClientRect().height}px` : "0px";
    if (root.style.getPropertyValue("--ankiweb-session-offset") !== offset)
      root.style.setProperty("--ankiweb-session-offset", offset);
  }

  function sync() {
    advance();
    const nextPhase = app.dom.getSnapshot().phase;
    const nextCard = app.dom.getCardContent();
    if (nextPhase !== "none" && (nextPhase !== phase || nextCard !== card)) {
      if (nextPhase === "question" || phase === "none" || nextCard !== card) cardMs = 0;
      phaseMs = 0;
    }
    if (nextPhase === "none" && !app.dom.isReviewRoute()) {
      cardMs = phaseMs = 0;
      waiting = null;
    }
    // A modal/loading state pauses time without forgetting the current side.
    if (nextPhase !== "none" || !app.dom.isReviewScreen()) {
      phase = nextPhase;
      card = nextCard;
    }
    running = nextPhase !== "none";
    if (nextPhase !== "none") createUi();
    render();
    if (running && !ticker) ticker = setInterval(render, 100);
    else if (!running && ticker) { clearInterval(ticker); ticker = null; }
  }

  function toggle(kind) {
    if (!Object.hasOwn(enabled, kind)) return;
    enabled[kind] = !enabled[kind];
    render();
  }

  document.addEventListener("visibilitychange", () => {
    // Flush the previous visible interval before using the new visibility state.
    const now = performance.now();
    if (document.hidden && running && waiting === null) {
      const delta = Math.max(0, now - lastTick);
      phaseMs += delta;
      cardMs += delta;
    }
    lastTick = now;
    render();
  });
  app.session = Object.freeze({ sync, toggle, beginReview, completeReview, cancelReview, snapshot });
})();
