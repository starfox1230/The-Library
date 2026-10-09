(() => {
  "use strict";

  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};

  // All assumptions about AnkiWeb's markup live here. Verified against the
  // public /study JavaScript on 2026-10-09; authenticated review still needs QA.
  const selectors = Object.freeze({
    quiz: "#quiz",
    card: "#qa",
    controls: "#ansarea",
    button: 'button, input[type="button"], input[type="submit"], [role="button"]',
    cardContent: "#qa, #qa_box",
    blocked: '[hidden], [inert], [aria-hidden="true"]',
    dialog: 'dialog[open], [aria-modal="true"], [role="dialog"], .modal.show',
    cardSurface: "#qa_box",
    navigation: "nav, .navbar, header, footer",
    reviewToolbar: ":scope > .float-start",
    counts: ":scope > .float-end .count",
    main: "main",
  });
  const grades = ["again", "hard", "good", "easy"];

  function isAllowedOrigin() {
    return location.origin === "https://ankiweb.net" || location.origin === "https://ankiuser.net";
  }

  function isReviewRoute() {
    return isAllowedOrigin() && /^\/study\/?$/.test(location.pathname);
  }

  function isVisible(element) {
    if (!element?.isConnected || element.closest(selectors.blocked)) return false;
    if (!element.getClientRects().length) return false;
    for (let node = element; node instanceof Element; node = node.parentElement) {
      const style = getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden" || style.visibility === "collapse") return false;
    }
    return true;
  }

  function isUsable(button) {
    return isVisible(button) && !button.matches(":disabled") &&
      button.getAttribute("aria-disabled") !== "true";
  }

  function getReviewElements() {
    if (!isReviewRoute()) return null;
    const quiz = document.querySelector(selectors.quiz);
    const card = quiz?.querySelector(selectors.card);
    const controls = quiz?.querySelector(selectors.controls);
    if (!card || !controls || card.contains(controls) || !isVisible(quiz) || !isVisible(card)) return null;
    return { quiz, card, controls };
  }

  function isReviewScreen() {
    return Boolean(getReviewElements());
  }

  function buttonLabel(button) {
    return (button.getAttribute("aria-label") || button.value || button.textContent || "")
      .replace(/\s+/g, " ").trim().toLowerCase();
  }

  function getSnapshot() {
    const elements = getReviewElements();
    const empty = { phase: "none", reveal: null, grades: {} };
    if (!elements || [...document.querySelectorAll(selectors.dialog)].some(isVisible)) return empty;
    const found = { reveal: [], again: [], hard: [], good: [], easy: [] };
    for (const button of elements.controls.querySelectorAll(selectors.button)) {
      if (!isUsable(button) || button.closest(selectors.cardContent)) continue;
      const label = buttonLabel(button);
      if (label === "show answer") found.reveal.push(button);
      else if (grades.includes(label)) found[label].push(button);
    }
    // Ambiguous or mixed controls fail closed instead of guessing a card side.
    if (Object.values(found).some(buttons => buttons.length > 1)) return empty;
    const answerButtons = Object.fromEntries(grades.filter(grade => found[grade].length)
      .map(grade => [grade, found[grade][0]]));
    if (found.reveal.length && Object.keys(answerButtons).length) return empty;
    if (found.reveal.length) return { phase: "question", reveal: found.reveal[0], grades: {} };
    if (Object.keys(answerButtons).length) return { phase: "answer", reveal: null, grades: answerButtons };
    return empty;
  }

  function showAnswer() {
    const snapshot = getSnapshot();
    if (snapshot.phase !== "question") return false;
    snapshot.reveal.click();
    return true;
  }

  function markModeElements() {
    const elements = getReviewElements();
    if (!elements) return false;
    // Keep site selectors in the adapter. CSS only uses extension-owned markers.
    elements.quiz.setAttribute("data-ankiweb-quiz", "");
    elements.controls.setAttribute("data-ankiweb-controls", "");
    elements.card.setAttribute("data-ankiweb-card-text", "");
    elements.quiz.querySelector(selectors.cardSurface)?.setAttribute("data-ankiweb-card-surface", "");
    elements.quiz.closest(selectors.main)?.setAttribute("data-ankiweb-review-main", "");
    for (const node of document.querySelectorAll(selectors.navigation)) {
      if (!elements.quiz.contains(node) && !node.contains(elements.quiz))
        node.setAttribute("data-ankiweb-chrome", "");
    }
    for (const node of elements.quiz.querySelectorAll(selectors.reviewToolbar))
      node.setAttribute("data-ankiweb-chrome", "");
    for (const node of elements.quiz.querySelectorAll(selectors.counts)) {
      const kind = ["new", "learn", "review"].find(name => node.classList.contains(name));
      if (kind) node.setAttribute("data-ankiweb-count", kind);
    }
    return true;
  }

  function answer(grade) {
    const snapshot = getSnapshot();
    const button = snapshot.grades[grade];
    if (snapshot.phase !== "answer" || !button) return false;
    button.click();
    return true;
  }

  app.dom = Object.freeze({
    isAllowedOrigin, isReviewRoute, isReviewScreen, getSnapshot, showAnswer, markModeElements,
    getCardContent: () => getReviewElements()?.card ?? null,
    getFeedbackAnchor: () => getReviewElements()?.controls.getBoundingClientRect() ?? null,
    isAnswerVisible: () => getSnapshot().phase === "answer",
    getAnswerButtons: () => getSnapshot().grades,
    answerAgain: () => answer("again"),
    answerHard: () => answer("hard"),
    answerGood: () => answer("good"),
    answerEasy: () => answer("easy"),
  });
})();
