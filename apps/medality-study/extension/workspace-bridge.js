(() => {
  'use strict';
  const allowedOrigin = 'https://starfox1230.github.io';
  const allowedPath = '/The-Library/apps/medality-study/';
  if (location.origin !== allowedOrigin || !location.pathname.startsWith(allowedPath)) return;
  window.addEventListener('message', async event => {
    if (event.source !== window || event.origin !== allowedOrigin) return;
    const message = event.data;
    if (message?.channel !== 'medality-study' || message.type !== 'request-captures' || typeof message.requestId !== 'string') return;
    try {
      const saved = await chrome.storage.local.get(null);
      const items = Object.entries(saved).filter(([key]) => key.startsWith('transcript:')).map(([, value]) => value);
      window.postMessage({ channel: 'medality-study', type: 'captures', requestId: message.requestId, items }, allowedOrigin);
    } catch {
      window.postMessage({ channel: 'medality-study', type: 'capture-error', requestId: message.requestId }, allowedOrigin);
    }
  });
})();
