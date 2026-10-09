(() => {
  "use strict";
  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};
  const ratings = Object.freeze({
    again: { label: "Again", color: "#ff6961" },
    hard: { label: "Hard", color: "#ffb861" },
    good: { label: "Good", color: "#61ffb8" },
    easy: { label: "Easy", color: "#61a8ff" },
  });
  let host = null;
  let timer = null;

  function clear() {
    clearTimeout(timer);
    host?.remove();
    host = null;
  }

  function show(grade, anchor) {
    const rating = ratings[grade];
    if (!rating || !document.body) return;
    clear();
    host = document.createElement("div");
    host.id = "ankiweb-enhancer-answer-feedback";
    const width = Math.max(1, Math.min(530, innerWidth - 24));
    const center = anchor ? anchor.left + anchor.width / 2 : innerWidth / 2;
    const left = Math.max(12, Math.min(center - width / 2, innerWidth - width - 12));
    const top = anchor && anchor.top >= 0 && anchor.top < innerHeight - 64
      ? anchor.top : Math.max(12, innerHeight - 80);
    Object.assign(host.style, {
      position: "fixed", left: `${left}px`, top: `${top}px`, width: `${width}px`,
      pointerEvents: "none", zIndex: "2147483647",
    });
    // Keep card/site styles out of the feedback, and never steal keyboard focus.
    const shadow = host.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = `
      :host { pointer-events: none; }
      .rating { box-sizing: border-box; width: 100%; min-height: 60px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 15px; border: 1px solid rgba(0,0,0,.25);
        box-shadow: 0 3px 12px rgba(0,0,0,.25); color: #101010;
        font: 700 26px/1.3 system-ui, sans-serif; padding: 12px 24px;
        pointer-events: none; }
    `;
    const label = document.createElement("div");
    label.className = "rating";
    label.setAttribute("role", "status");
    label.setAttribute("aria-live", "polite");
    label.setAttribute("aria-atomic", "true");
    label.style.backgroundColor = rating.color;
    label.textContent = rating.label;
    shadow.append(style, label);
    document.body.append(host);
    timer = setTimeout(clear, 900);
  }

  app.feedback = Object.freeze({ show, clear });
})();
