(() => {
  const enabled = document.getElementById('enabled');
  const speed = document.getElementById('speed');
  const status = document.getElementById('status');
  let saving = false;
  const transcriptStatus = document.getElementById('transcript-status');
  async function transcriptAction(action) {
    transcriptStatus.textContent = 'Reading transcript…';
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      const result = await chrome.tabs.sendMessage(tab.id, { type: 'medality-transcript-action', action }, { frameId: 0 });
      if (!result.ok) throw new Error(result.error);
      transcriptStatus.textContent = action === 'copy' ? `Copied: ${result.title}` : `Saved: ${result.title}. Open Recently watched to review it.`;
    } catch (error) {
      transcriptStatus.textContent = error?.message?.includes('Receiving end') ? 'Open or refresh a Medality lesson first.' : String(error?.message || error);
    }
  }
  document.getElementById('copy-transcript').addEventListener('click', () => void transcriptAction('copy'));
  document.getElementById('save-transcript').addEventListener('click', () => void transcriptAction('save'));
  document.getElementById('export-transcripts').addEventListener('click', async () => {
    try {
      const saved = await chrome.storage.local.get(null);
      const items = Object.entries(saved).filter(([key]) => key.startsWith('transcript:')).map(([, value]) => value);
      if (!items.length) { transcriptStatus.textContent = 'No saved transcripts yet.'; return; }
      const url = URL.createObjectURL(new Blob([JSON.stringify({ format: 'medality-study-v1', items }, null, 2)], { type: 'application/json' }));
      const link = document.createElement('a'); link.href = url; link.download = 'medality-transcripts.json'; link.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      transcriptStatus.textContent = `Exported ${items.length} saved transcripts.`;
    } catch { transcriptStatus.textContent = 'Could not export saved transcripts.'; }
  });

  const autoCapture = document.getElementById('auto-capture');
  chrome.storage.local.get({autoCapture:true}).then(value=>{autoCapture.checked=value.autoCapture!==false;});
  autoCapture.addEventListener('change',async()=>{
    try { await chrome.storage.local.set({autoCapture:autoCapture.checked}); transcriptStatus.textContent=autoCapture.checked?'Automatic transcript saving on at 90%.':'Automatic transcript saving paused.'; }
    catch { transcriptStatus.textContent='Could not save preference.'; }
  });
  async function refresh() {
    if (saving) return;
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) throw new Error('No active tab.');
      const result = await chrome.tabs.sendMessage(tab.id, { type: 'medality-speed-status' }, { frameId: 0 });
      if (!result.enabled) {
        status.textContent = 'Automatic speed is off. Current playback is left as it is.';
      } else if (!result.players.length) {
        status.textContent = 'No player found on this page. Open a Medality lesson.';
      } else {
        const failures = result.players.filter(player => player.error);
        const confirmed = result.players.filter(player => player.ready && !player.error && Math.abs(player.actual - result.speed) < 0.01);
        status.textContent = failures.length ? `Player: ${failures[0].error}` :
          confirmed.length ? `${result.speed}× confirmed on ${confirmed.length} player${confirmed.length === 1 ? '' : 's'}.` :
          'Waiting for the player to load and confirm its speed…';
      }
    } catch {
      status.textContent = 'Preferences saved. Open or refresh a Medality lesson to use them.';
    }
  }

  async function save() {
    saving = true;
    try {
      await chrome.storage.local.set({ enabled: enabled.checked, speed: Number(speed.value) });
      status.textContent = 'Saved. Applying to your lessons…';
    } catch {
      status.textContent = 'Could not save. Reopen the extension and try again.';
    } finally { saving = false; }
  }

  chrome.storage.local.get({ enabled: true, speed: 2 }).then(value => {
    enabled.checked = value.enabled;
    speed.value = String(value.speed);
    enabled.addEventListener('change', save);
    speed.addEventListener('change', save);
    void refresh();
    setInterval(refresh, 1500);
  }).catch(() => { status.textContent = 'Could not read preferences. Reopen the extension.'; });
})();
