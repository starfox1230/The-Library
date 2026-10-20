chrome.commands.onCommand.addListener(async (command, tab) => {
  if (command !== 'copy-transcript') return;
  try {
    if (!tab?.id) [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) await chrome.tabs.sendMessage(tab.id, { type: 'medality-transcript-action', action: 'copy' }, { frameId: 0 });
  } catch {
    // The shortcut is intentionally inactive outside a refreshed Medality lesson.
  }
});

importScripts('helper-config.js');
async function helperRequest(path, body) {
  if (!self.MEDALITY_HELPER_TOKEN) throw new Error('Double-click helper/Start.cmd in the extension folder, then reload the extension once.');
  let response;
  try { response = await fetch('http://127.0.0.1:18764' + path, {method:body?'POST':'GET',headers:{'Content-Type':'application/json','X-Medality-Token':self.MEDALITY_HELPER_TOKEN},...(body?{body:JSON.stringify(body)}:{})}); }
  catch { throw new Error('Download helper is not running. Double-click helper/Start.cmd, then try again.'); }
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Download failed');
  return result;
}
chrome.runtime.onMessage.addListener((message, sender, reply) => {
  if (!['medality-download','medality-download-status'].includes(message?.type)) return;
  let url;
  try { url = new URL(sender.url); } catch { return; }
  if (url.protocol !== 'https:' || !/(^|\.)(medality\.com|mrionline\.com)$/.test(url.hostname)) return;
  const task = message.type === 'medality-download'
    ? helperRequest('/download', {page:sender.url,video:message.video})
    : /^[a-f0-9]{32}$/.test(message.job || '') ? helperRequest('/jobs/'+message.job) : Promise.reject(new Error('Invalid download'));
  task.then(data=>reply({ok:true,...data})).catch(error=>reply({ok:false,error:error.message}));
  return true;
});
