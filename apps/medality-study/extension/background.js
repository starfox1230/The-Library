chrome.commands.onCommand.addListener(async (command, tab) => {
  if (command !== 'copy-transcript') return;
  try {
    if (!tab?.id) [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (tab?.id) await chrome.tabs.sendMessage(tab.id, { type: 'medality-transcript-action', action: 'copy' }, { frameId: 0 });
  } catch {
    // The shortcut is intentionally inactive outside a refreshed Medality lesson.
  }
});
