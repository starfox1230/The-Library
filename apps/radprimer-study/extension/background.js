importScripts('core.js', 'db.js');
'use strict';
chrome.action.onClicked.addListener(() => chrome.tabs.create({ url: chrome.runtime.getURL('library.html') }));
chrome.runtime.onMessage.addListener((message, sender, respond) => {
  // MessageSender.url identifies the actual document without requesting tabs permission.
  if (sender.id !== chrome.runtime.id || !sender.tab || sender.frameId !== 0 || !RadCore.safeSource(sender.url)) return;
  if (message?.type === 'rp:open') {
    chrome.tabs.create({ url: chrome.runtime.getURL('library.html') }); respond({ ok: true }); return;
  }
  if (message?.type !== 'rp:save') return;
  (async () => {
    const capture = RadCore.validateCase(message.capture);
    const c = await RadDB.saveCapture(capture, {
      notes: String(message.options?.notes || ''),
      highlights: Array.isArray(message.options?.highlights) ? message.options.highlights.map(String) : [],
      anki: !!message.options?.anki
    });
    return { ok: true, id: c.id, answered: c.answered, media: RadCore.mediaCount(c) };
  })().then(respond, error => respond({ ok: false, error: error.message }));
  return true;
});
