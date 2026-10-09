(() => {
  "use strict";
  const app = globalThis.AnkiWebEnhancer = globalThis.AnkiWebEnhancer || {};
  const enabled = { focus: false, dark: false };

  function sync() {
    const root = document.documentElement;
    if (!root) return;
    const reviewing = app.dom.markModeElements();
    root.toggleAttribute("data-ankiweb-review", reviewing);
    root.toggleAttribute("data-ankiweb-focus", reviewing && enabled.focus);
    root.toggleAttribute("data-ankiweb-dark", reviewing && enabled.dark);
  }

  function toggle(mode) {
    if (!Object.hasOwn(enabled, mode)) return;
    enabled[mode] = !enabled[mode];
    sync();
  }

  app.modes = Object.freeze({ toggle, sync });
})();
