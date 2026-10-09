(() => {
  "use strict";
  if (location.origin !== "https://ankiweb.net" || window !== window.top) return;
  const app = globalThis.AnkiWebEnhancer;
  if (app.started) return;
  app.started = true;
  const dom = app.dom;
  const debounceMs = 350;
  let lastActionAt = -Infinity;
  let pending = null;
  let dispatching = false;

  function observeTransition() {
    if (!pending) return;
    if (!dom.isReviewRoute()) { pending = null; return; }
    const phase = dom.getSnapshot().phase;
    // A removed/disabled button or unrelated DOM mutation is NOT confirmation.
    // A grade remains locked until AnkiWeb actually renders the next question.
    if ((pending === "reveal" && phase === "answer") ||
        (pending !== "reveal" && phase === "question")) pending = null;
  }

  function perform(action) {
    observeTransition();
    const snapshot = dom.getSnapshot();
    if (action === "reveal" ? snapshot.phase !== "question" :
      snapshot.phase !== "answer" || !snapshot.grades[action]) return;
    const now = performance.now();
    if (pending || now - lastActionAt < debounceMs) return;
    // Lock before dispatch: synchronous page updates cannot allow a second click.
    pending = action;
    lastActionAt = now;
    dispatching = true;
    try {
      const clicked = action === "reveal" ? dom.showAnswer() :
        ({ again: dom.answerAgain, hard: dom.answerHard, good: dom.answerGood, easy: dom.answerEasy })[action]();
      if (!clicked) pending = null;
    } finally {
      dispatching = false;
    }
  }

  // Track ordinary mouse clicks too, so immediately following keyboard input
  // cannot accidentally submit a second rating while the same answer is shown.
  window.addEventListener("click", event => {
    if (dispatching) return;
    const snapshot = dom.getSnapshot();
    const path = event.composedPath();
    const action = snapshot.reveal && path.includes(snapshot.reveal) ? "reveal" :
      Object.entries(snapshot.grades).find(([, button]) => path.includes(button))?.[0];
    if (action) { pending = action; lastActionAt = performance.now(); }
  }, true);

  app.keyboard.install({ dom, perform });
  // No polling. Observe the document because AnkiWeb can replace the entire
  // review view during client-side navigation. No card text is read or stored.
  const observer = new MutationObserver(observeTransition);
  observer.observe(document, {
    childList: true, subtree: true, characterData: true, attributes: true,
    attributeFilter: ["disabled", "aria-disabled", "hidden", "inert", "aria-hidden", "class", "style", "aria-label", "open"],
  });
  window.addEventListener("popstate", observeTransition);
})();
