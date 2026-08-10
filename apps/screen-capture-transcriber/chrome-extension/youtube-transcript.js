(() => {
  let sentFingerprint = "";
  let requestInFlight = false;
  let openedByExtension = false;
  let videoUrl = location.href;
  let bridgeInstanceId = "";

  function parseTimestamp(value) {
    const parts = String(value || "")
      .trim()
      .split(":")
      .map((part) => Number(part));
    if (
      parts.length < 2 ||
      parts.length > 3 ||
      parts.some((part) => !Number.isFinite(part) || part < 0)
    ) {
      return null;
    }
    return parts.reduce((total, part) => total * 60 + part, 0);
  }

  function videoTitle() {
    const heading = document.querySelector(
      "ytd-watch-metadata h1 yt-formatted-string, "
      + "ytd-watch-metadata h1, h1.ytd-watch-metadata",
    );
    return (heading?.textContent || document.title || "")
      .replace(/^\(\d+\)\s*/, "")
      .replace(/\s*-\s*YouTube\s*$/, "")
      .trim();
  }

  function extractTranscript() {
    const segments = Array.from(
      document.querySelectorAll("ytd-transcript-segment-renderer"),
    );
    const cues = [];
    for (const segment of segments) {
      const lines = (segment.innerText || "")
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean);
      if (lines.length < 2) continue;
      const timestamp = lines[0];
      const seconds = parseTimestamp(timestamp);
      const text = lines.slice(1).join(" ").trim();
      if (seconds === null || !text) continue;
      cues.push({ timestamp, seconds, text });
    }
    if (!cues.length) return null;
    return {
      provider: "YouTube built-in transcript",
      title: videoTitle(),
      url: location.href,
      cues,
    };
  }

  function buttonWithText(text) {
    const expected = text.toLowerCase();
    return Array.from(document.querySelectorAll("button")).find(
      (button) => (button.textContent || "").trim().toLowerCase() === expected,
    ) || null;
  }

  function expandDescription() {
    const expand = document.querySelector(
      "ytd-text-inline-expander #expand, #description-inline-expander #expand",
    ) || buttonWithText("...more");
    if (expand) expand.click();
  }

  async function openTranscript() {
    let show = buttonWithText("Show transcript");
    if (!show) {
      expandDescription();
      await new Promise((resolve) => setTimeout(resolve, 250));
      show = buttonWithText("Show transcript");
    }
    if (!show) return false;
    openedByExtension = true;
    show.click();
    await new Promise((resolve) => setTimeout(resolve, 550));
    return true;
  }

  function closeExtensionOpenedTranscript() {
    if (!openedByExtension) return;
    const close = Array.from(document.querySelectorAll("button")).find(
      (button) =>
        String(button.getAttribute("aria-label") || "")
          .trim()
          .toLowerCase() === "close transcript",
    );
    openedByExtension = false;
    if (close) close.click();
  }

  async function sendTranscript(transcript) {
    const fingerprint = `${location.href}\n${JSON.stringify(transcript.cues)}`;
    if (fingerprint === sentFingerprint) return true;
    const response = await chrome.runtime.sendMessage({
      type: "sct-source-transcript",
      transcript,
    });
    if (!response?.ok) return false;
    sentFingerprint = fingerprint;
    return true;
  }

  async function collectIfRequested() {
    if (requestInFlight) return;
    if (location.href !== videoUrl) {
      videoUrl = location.href;
      sentFingerprint = "";
      openedByExtension = false;
    }
    requestInFlight = true;
    try {
      const poll = await chrome.runtime.sendMessage({
        type: "sct-page-poll",
      });
      const nextBridgeInstanceId = String(poll?.bridge_instance_id || "");
      if (nextBridgeInstanceId && nextBridgeInstanceId !== bridgeInstanceId) {
        bridgeInstanceId = nextBridgeInstanceId;
        sentFingerprint = "";
      }
      if (
        !poll?.ok ||
        poll.app_state?.source_selected === false ||
        !poll.app_state?.request_source_transcript ||
        sentFingerprint
      ) {
        return;
      }
      let transcript = extractTranscript();
      if (!transcript && await openTranscript()) {
        transcript = extractTranscript();
      }
      if (transcript && await sendTranscript(transcript)) {
        closeExtensionOpenedTranscript();
      }
    } catch (_error) {
      // The desktop app may be closed or the unpacked extension may have just
      // been reloaded. The next page/app refresh will reconnect.
    } finally {
      requestInFlight = false;
    }
  }

  setInterval(collectIfRequested, 1500);
  collectIfRequested();
})();
