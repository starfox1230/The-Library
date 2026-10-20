(() => {
  'use strict';
  const allowedOrigin = 'https://starfox1230.github.io';
  const allowedPath = '/The-Library/apps/medality-study/';
  if (location.origin !== allowedOrigin || !location.pathname.startsWith(allowedPath)) return;
  let historyRequest = null;
  async function publishHistory() {
    if (!historyRequest) return;
    try {
      const saved = await chrome.storage.local.get(null);
      const items = Object.entries(saved).filter(([key]) => key.startsWith('transcript:') || key.startsWith('watch:')).map(([,value])=>value);
      window.postMessage({channel:'medality-study',type:'history',requestId:historyRequest,items},allowedOrigin);
    } catch {}
  }
  chrome.storage.onChanged?.addListener((_changes,area)=>{if(area==='local')void publishHistory();});
  window.addEventListener('message', async event => {
    if (event.source !== window || event.origin !== allowedOrigin) return;
    const message = event.data;
    if (message?.channel !== 'medality-study' || typeof message.requestId !== 'string' || message.requestId.length > 100) return;
    if (message.type === 'request-history') { historyRequest = message.requestId; await publishHistory(); return; }
    if (message.type !== 'request-captures') return;
    try {
      const saved = await chrome.storage.local.get(null);
      const items = Object.entries(saved).filter(([key]) => key.startsWith('transcript:')).map(([, value]) => value);
      window.postMessage({ channel: 'medality-study', type: 'captures', requestId: message.requestId, items }, allowedOrigin);
    } catch {
      window.postMessage({ channel: 'medality-study', type: 'capture-error', requestId: message.requestId }, allowedOrigin);
    }
  });
})();
