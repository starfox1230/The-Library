/* Apply before styles load to avoid a bright flash when opening the reader. */
(() => {
  'use strict';
  const key = 'library-bone-tumor-theme-v1';
  let theme = 'dark';
  try {
    const saved = localStorage.getItem(key);
    if (saved === 'light' || saved === 'dark') theme = saved;
  } catch { /* The toggle still works when persistent storage is unavailable. */ }

  function apply(value) {
    theme = value;
    document.documentElement.dataset.theme = value;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = value === 'dark' ? '#101b20' : '#f7f6f0';
    const button = document.getElementById('theme-toggle');
    if (button) {
      button.textContent = value === 'dark' ? '☀ Day mode' : '☾ Night mode';
      button.setAttribute('aria-label', value === 'dark' ? 'Switch to day mode' : 'Switch to night mode');
      button.setAttribute('aria-pressed', String(value === 'dark'));
    }
  }
  apply(theme);
  document.addEventListener('DOMContentLoaded', () => {
    apply(theme);
    document.getElementById('theme-toggle').addEventListener('click', () => {
      apply(theme === 'dark' ? 'light' : 'dark');
      try { localStorage.setItem(key, theme); } catch { /* Session-only preference. */ }
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === key && (event.newValue === 'dark' || event.newValue === 'light')) apply(event.newValue);
  });
})();
