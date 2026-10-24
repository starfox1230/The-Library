import {DATA_SOURCE_ID, createNotionClient, validateSchema, validateMedia, saveMedia} from './core.js';

// Secrets stay in trusted extension contexts, never the Rotten Tomatoes content script.
const storageReady = chrome.storage.local.setAccessLevel({accessLevel: 'TRUSTED_CONTEXTS'});
const pending = new Map();
let saveQueue = Promise.resolve();
const trusted = sender => sender.id === chrome.runtime.id && sender.url === chrome.runtime.getURL('options.html');

async function handle(message, sender) {
  await storageReady;
  if (message?.type === 'OPEN_SETTINGS') {
    if (sender.id !== chrome.runtime.id) throw new Error('Invalid sender.');
    await chrome.runtime.openOptionsPage();
    return {};
  }
  if (['CONFIG_STATUS', 'CONNECT', 'DISCONNECT', 'SAVE_PREFERENCES'].includes(message?.type)) {
    if (!trusted(sender)) throw new Error('Open extension settings to manage the connection.');
    if (message.type === 'CONFIG_STATUS') {
      const {token, openAfterSave = false} = await chrome.storage.local.get(['token', 'openAfterSave']);
      return {connected: Boolean(token), openAfterSave};
    }
    if (message.type === 'DISCONNECT') {
      await chrome.storage.local.remove(['token', 'openAfterSave']);
      return {};
    }
    if (message.type === 'SAVE_PREFERENCES') {
      await chrome.storage.local.set({openAfterSave: Boolean(message.openAfterSave)});
      return {};
    }
    const token = typeof message.token === 'string' ? message.token.trim() : '';
    if (!token || token.length > 1000 || /\s/.test(token)) throw new Error('Paste your Notion connection secret.');
    const api = createNotionClient(token);
    validateSchema(await api(`data_sources/${DATA_SOURCE_ID}`));
    // A read-only query also verifies query capability. No test entries are created.
    await api(`data_sources/${DATA_SOURCE_ID}/query`, {page_size: 1});
    await chrome.storage.local.set({token, openAfterSave: Boolean(message.openAfterSave)});
    return {connected: true};
  }
  if (message?.type !== 'SAVE_MEDIA' || sender.id !== chrome.runtime.id || !sender.tab || sender.frameId !== 0) throw new Error('Unsupported request.');
  const media = validateMedia(message.media, sender.url);
  const key = media.url;
  if (pending.has(key)) return pending.get(key);
  const job = saveQueue.then(async () => {
    const {token, openAfterSave} = await chrome.storage.local.get(['token', 'openAfterSave']);
    if (!token) return {state: 'setup'};
    const api = createNotionClient(token);
    validateSchema(await api(`data_sources/${DATA_SOURCE_ID}`));
    const result = await saveMedia(api, media, message.allowSeparate === true);
    if (openAfterSave && result.state === 'created') {
      // A successful save remains successful if Chrome cannot open a tab.
      try { await chrome.tabs.create({url: result.url}); } catch { /* Use the on-page link. */ }
    }
    return result;
  });
  pending.set(key, job);
  saveQueue = job.catch(() => {});
  try { return await job; } finally { pending.delete(key); }
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
  handle(message, sender).then(data => respond({ok: true, ...data}), error => respond({ok: false, error: error.message || 'Something went wrong. Try again.'}));
  return true;
});
chrome.action.onClicked.addListener(() => chrome.runtime.openOptionsPage());
chrome.runtime.onInstalled.addListener(({reason}) => {
  if (reason === 'install') chrome.runtime.openOptionsPage();
});
