(() => {
  "use strict";

  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};
  const actions = Object.freeze({
    " ": "reveal", Enter: "reveal",
    "1": "again", "2": "hard", "3": "good", "4": "easy",
  });
  const editableSelector = 'input, textarea, select, [role="textbox"], [role="searchbox"], [role="combobox"]';
  const interactiveSelector = 'a[href], audio, video, summary, [role="slider"], [role="spinbutton"]';

  function activeElement() {
    let element = document.activeElement;
    while (element?.shadowRoot?.activeElement) element = element.shadowRoot.activeElement;
    return element;
  }

  function isProtected(event) {
    return [...event.composedPath(), activeElement()].some(element =>
      element instanceof Element && (element.isContentEditable ||
        element.closest(editableSelector) || element.closest(interactiveSelector)));
  }

  function install({ dom, perform }) {
    const heldKeys = new Set();
    const ownedReleases = new Set();

    function keydown(event) {
      const action = actions[event.key];
      if (!action || !dom.isReviewScreen()) return;
      ownedReleases.add(event.code || event.key);
      // AnkiWeb grades on document keyup, without checking text fields. Stop
      // propagation even while typing, but preserve normal editing defaults.
      if (isProtected(event) || event.ctrlKey || event.altKey || event.metaKey ||
          event.shiftKey || event.isComposing || event.keyCode === 229) {
        event.stopImmediatePropagation();
        return;
      }
      event.preventDefault();
      event.stopImmediatePropagation();
      const key = event.code || event.key;
      if (event.repeat || heldKeys.has(key)) return;
      heldKeys.add(key);
      perform(action);
    }

    function keyup(event) {
      const key = event.code || event.key;
      const owned = ownedReleases.delete(key);
      heldKeys.delete(key);
      if (!owned && (!actions[event.key] || !dom.isReviewScreen())) return;
      event.stopImmediatePropagation();
      if (!isProtected(event) && !event.ctrlKey && !event.altKey && !event.metaKey &&
          !event.shiftKey && !event.isComposing) event.preventDefault();
    }

    function keypress(event) {
      if (!actions[event.key] || !dom.isReviewScreen()) return;
      event.stopImmediatePropagation();
      if (!isProtected(event) && !event.ctrlKey && !event.altKey && !event.metaKey &&
          !event.shiftKey && !event.isComposing) event.preventDefault();
    }

    // Capture on window runs before AnkiWeb's document-level shortcuts. Both
    // halves of a keypress are owned, including invalid grades on the front.
    window.addEventListener("keydown", keydown, true);
    window.addEventListener("keyup", keyup, true);
    window.addEventListener("keypress", keypress, true);
    window.addEventListener("blur", () => { heldKeys.clear(); ownedReleases.clear(); });
  }

  app.keyboard = Object.freeze({ install });
})();
