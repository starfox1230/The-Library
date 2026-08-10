const BRIDGE_URL = "http://127.0.0.1:43129";
const BRIDGE_TOKEN = "sct-medality-local-v1-9f63d2c7";

async function bridgeRequest(path, payload) {
  const response = await fetch(`${BRIDGE_URL}${path}`, {
    method: "POST",
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-SCT-Bridge-Token": BRIDGE_TOKEN,
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`Recorder bridge returned ${response.status}`);
  }
  return response.json();
}

function enrichedPayload(message, sender) {
  return {
    ...message,
    top_url: sender.tab?.url || "",
    top_title: sender.tab?.title || "",
    tab_id: sender.tab?.id ?? null,
    tab_active: Boolean(sender.tab?.active),
    window_id: sender.tab?.windowId ?? null,
    frame_id: sender.frameId ?? null,
  };
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "sct-event") {
    bridgeRequest("/v1/event", enrichedPayload(message, sender))
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message?.type === "sct-poll") {
    bridgeRequest("/v1/poll", enrichedPayload(message, sender))
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message?.type === "sct-page-poll") {
    bridgeRequest("/v1/page-poll", enrichedPayload(message, sender))
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message?.type === "sct-source-transcript") {
    bridgeRequest(
      "/v1/event",
      enrichedPayload(
        {
          type: "sct-event",
          event: "source_transcript",
          transcript: message.transcript,
        },
        sender,
      ),
    )
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message?.type === "sct-learning-note-intent") {
    bridgeRequest(
      "/v1/event",
      enrichedPayload(
        {
          type: "sct-event",
          event: "learning_note_intent",
          reason: "backspace",
        },
        sender,
      ),
    )
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  if (message?.type === "sct-popup-status") {
    fetch(`${BRIDGE_URL}/v1/health`, { cache: "no-store" })
      .then(async (response) => ({
        ok: response.ok,
        health: response.ok ? await response.json() : null,
      }))
      .then(sendResponse)
      .catch((error) => sendResponse({ ok: false, error: String(error.message || error) }));
    return true;
  }
  return false;
});
