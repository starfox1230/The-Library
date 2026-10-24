import {WATCHLIST_URL} from './core.js';
const form = document.querySelector('#connect');
const token = document.querySelector('#token');
const autoOpen = document.querySelector('#auto-open');
const submit = document.querySelector('#submit');
const disconnect = document.querySelector('#disconnect');
const status = document.querySelector('#status');
document.querySelector('#watchlist').href = WATCHLIST_URL;
async function send(message) {
  const result = await chrome.runtime.sendMessage(message);
  if (!result?.ok) throw new Error(result?.error || 'The extension did not respond. Reload this page.');
  return result;
}
function show(text, error = false) { status.textContent = text; status.dataset.error = String(error); }
async function load() {
  try {
    const result = await send({type: 'CONFIG_STATUS'});
    autoOpen.checked = result.openAfterSave;
    disconnect.hidden = !result.connected;
    show(result.connected ? 'Connected. You’re ready to save from Rotten Tomatoes.' : 'Not connected yet. Complete the steps above.');
  } catch (error) { show(error.message, true); }
}
form.addEventListener('submit', async event => {
  event.preventDefault();
  submit.disabled = true; disconnect.disabled = true;
  show('Checking your Watchlist and its fields…');
  try {
    await send({type: 'CONNECT', token: token.value, openAfterSave: autoOpen.checked});
    token.value = ''; disconnect.hidden = false;
    show('Connected. Refresh your Rotten Tomatoes page and click Add to Watchlist.');
  } catch (error) { show(error.message, true); }
  finally { submit.disabled = false; disconnect.disabled = false; }
});
disconnect.addEventListener('click', async () => {
  try {
    await send({type: 'DISCONNECT'});
    token.value = ''; disconnect.hidden = true;
    show('Disconnected. The saved token has been removed from this Chrome profile.');
  } catch (error) { show(error.message, true); }
});
autoOpen.addEventListener('change', async () => {
  try {
    await send({type: 'SAVE_PREFERENCES', openAfterSave: autoOpen.checked});
    show('Opening preference saved.');
  } catch (error) { show(error.message, true); }
});
load();
