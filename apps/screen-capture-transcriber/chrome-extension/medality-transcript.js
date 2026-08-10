(() => {
  let sentFingerprint = "";
  let requestInFlight = false;
  let openedByExtension = false;
  let lessonUrl = location.href;
  let appState = {};
  let bridgeInstanceId = "";
  const TEXT_ENTRY_INPUT_TYPES = new Set(
    ["text", "search", "email", "url", "tel", "password", "number"],
  );

  function isTypingTarget(target) {
    if (!(target instanceof Element)) return false;
    if (
      target.closest(
        "textarea, [contenteditable='true'], [contenteditable=''], [role='textbox']",
      )
    ) {
      return true;
    }
    const input = target.closest("input");
    if (!input) return false;
    const inputType = String(input.getAttribute("type") || "text").toLowerCase();
    return TEXT_ENTRY_INPUT_TYPES.has(inputType);
  }

  function onLearningNoteKeydown(event) {
    if (
      event.key !== "Backspace" ||
      event.repeat ||
      event.ctrlKey ||
      event.metaKey ||
      event.altKey ||
      !appState.learning_note_enabled ||
      isTypingTarget(event.target)
    ) {
      return;
    }
    event.preventDefault();
    event.stopImmediatePropagation();
    chrome.runtime.sendMessage({
      type: "sct-learning-note-intent",
    }).catch(() => {});
  }

  function transcriptPaper() {
    const timestampPattern = /^\d+:\d{2}$/;
    const drawers = Array.from(
      document.querySelectorAll(".MuiDrawer-paper, [role='dialog']"),
    );
    const transcriptDrawer = drawers.find((drawer) =>
      Array.from(drawer.querySelectorAll("p")).some((paragraph) =>
        timestampPattern.test((paragraph.textContent || "").trim()),
      ),
    );
    if (transcriptDrawer) return transcriptDrawer;

    const resync = Array.from(document.querySelectorAll("button")).find(
      (button) => (button.textContent || "").trim() === "Re-Sync with Video",
    );
    return resync?.parentElement || null;
  }

  function parseTimestamp(value) {
    const match = String(value || "").trim().match(/^(\d+):(\d{2})$/);
    if (!match) return null;
    return Number(match[1]) * 60 + Number(match[2]);
  }

  function extractTranscript() {
    const paper = transcriptPaper();
    if (!paper) return null;
    const paragraphs = Array.from(paper.querySelectorAll("p"));
    const cues = [];
    for (let index = 0; index < paragraphs.length - 1; index += 1) {
      const timestamp = (paragraphs[index].textContent || "").trim();
      const seconds = parseTimestamp(timestamp);
      if (seconds === null) continue;
      const text = (paragraphs[index + 1].textContent || "").trim();
      if (!text || parseTimestamp(text) !== null) continue;
      cues.push({ timestamp, seconds, text });
      index += 1;
    }
    if (!cues.length) return null;
    const heading = document.querySelector("h1");
    return {
      provider: "Medality built-in transcript",
      title: (heading?.textContent || document.title || "").trim(),
      url: location.href,
      cues,
    };
  }

  async function sendTranscript(transcript) {
    const fingerprint = JSON.stringify(transcript.cues);
    if (fingerprint === sentFingerprint) return true;
    const response = await chrome.runtime.sendMessage({
      type: "sct-source-transcript",
      transcript,
    });
    if (!response?.ok) return false;
    sentFingerprint = fingerprint;
    return true;
  }

  function findTranscriptButton() {
    return Array.from(document.querySelectorAll("button")).find(
      (button) => (button.textContent || "").trim() === "Transcript",
    ) || null;
  }

  function closeExtensionOpenedDrawer() {
    if (!openedByExtension) return;
    const drawer = transcriptPaper();
    const hide = drawer
      ? Array.from(drawer.querySelectorAll("button")).find(
          (button) => (button.textContent || "").trim() === "Hide",
        )
      : null;
    openedByExtension = false;
    if (hide) hide.click();
  }

  async function collectIfRequested() {
    if (requestInFlight) return;
    if (location.href !== lessonUrl) {
      lessonUrl = location.href;
      sentFingerprint = "";
      openedByExtension = false;
    }
    requestInFlight = true;
    try {
      const poll = await chrome.runtime.sendMessage({
        type: "sct-page-poll",
      });
      const nextBridgeInstanceId = String(poll?.bridge_instance_id || "");
      if (
        nextBridgeInstanceId &&
        nextBridgeInstanceId !== bridgeInstanceId
      ) {
        bridgeInstanceId = nextBridgeInstanceId;
        sentFingerprint = "";
      }
      if (poll?.ok) appState = poll.app_state || appState;
      if (
        !poll?.ok ||
        poll.app_state?.source_selected === false ||
        sentFingerprint ||
        !poll.app_state?.request_source_transcript
      ) return;
      let transcript = extractTranscript();
      if (!transcript) {
        const button = findTranscriptButton();
        if (!button) return;
        openedByExtension = true;
        button.click();
        await new Promise((resolve) => setTimeout(resolve, 350));
        transcript = extractTranscript();
      }
      if (transcript) {
        const sent = await sendTranscript(transcript);
        if (sent) closeExtensionOpenedDrawer();
      }
    } catch (_error) {
      // The desktop app may be closed; the next poll will retry.
    } finally {
      requestInFlight = false;
    }
  }

  setInterval(collectIfRequested, 1500);
  // Window capture runs before focused playback controls (including the
  // seek/scrubber slider) can consume Backspace.
  window.addEventListener("keydown", onLearningNoteKeydown, true);
  collectIfRequested();
})();
