(() => {
  const PROVIDER = location.hostname.includes("vimeo")
    ? "Medality / Vimeo"
    : (location.hostname.includes("youtube") ? "YouTube" : location.hostname);
  let activeVideo = null;
  let appState = { linked_session_active: false, recorder_state: "idle" };
  let allowPlayUntil = 0;
  let suppressPauseReason = "";
  let lastStableTime = 0;
  let seekFromTime = null;
  let pollInFlight = false;
  let lastPollError = "";
  let priorSample = null;
  const TEXT_ENTRY_INPUT_TYPES = new Set(
    ["text", "search", "email", "url", "tel", "password", "number"],
  );

  function visibleArea(video) {
    const rect = video.getBoundingClientRect();
    if (rect.width < 80 || rect.height < 45) return 0;
    return rect.width * rect.height;
  }

  function findActiveVideo() {
    const videos = Array.from(document.querySelectorAll("video"));
    videos.sort((left, right) => visibleArea(right) - visibleArea(left));
    return videos[0] || null;
  }

  function snapshot(video = activeVideo) {
    if (!video) return null;
    const now = Date.now();
    let observedRate = null;
    if (
      priorSample &&
      !video.paused &&
      !video.seeking &&
      now - priorSample.wallMs >= 200
    ) {
      const wallDelta = (now - priorSample.wallMs) / 1000;
      observedRate = wallDelta > 0
        ? (video.currentTime - priorSample.mediaTime) / wallDelta
        : null;
    }
    priorSample = { wallMs: now, mediaTime: video.currentTime };
    return {
      provider: PROVIDER,
      frame_url: location.href,
      frame_title: document.title,
      current_time: Number(video.currentTime || 0),
      duration: Number.isFinite(video.duration) ? Number(video.duration) : 0,
      paused: Boolean(video.paused),
      ended: Boolean(video.ended),
      seeking: Boolean(video.seeking),
      playback_rate: Number(video.playbackRate || 1),
      default_playback_rate: Number(video.defaultPlaybackRate || 1),
      observed_rate: Number.isFinite(observedRate) ? observedRate : null,
      ready_state: Number(video.readyState || 0),
      wall_time_ms: now,
    };
  }

  function sendEvent(event, reason = "", extra = {}) {
    const player = snapshot();
    if (!player) return;
    try {
      chrome.runtime.sendMessage({
        type: "sct-event",
        event,
        reason,
        player: { ...player, ...extra },
      }).catch(() => {});
    } catch (_error) {
      // An already-open page can briefly retain this script after the
      // unpacked extension is reloaded. Reloading the page reconnects it.
    }
  }

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
    sendEvent("learning_note_intent", "backspace");
  }

  function onPlay() {
    const mustIntercept =
      appState.linked_session_active &&
      appState.source_selected !== false &&
      appState.recorder_state !== "recording" &&
      Date.now() > allowPlayUntil;
    if (mustIntercept) {
      suppressPauseReason = "intercepted_play_intent";
      activeVideo.pause();
      sendEvent("play_intent");
      return;
    }
    sendEvent("play");
  }

  function onPause() {
    const reason = suppressPauseReason;
    suppressPauseReason = "";
    sendEvent("pause", reason);
  }

  function onSeeking() {
    seekFromTime = lastStableTime;
    sendEvent("seeking", "", {
      seek_from_time: Number(seekFromTime || 0),
    });
  }

  function onSeeked() {
    lastStableTime = activeVideo.currentTime;
    sendEvent("seeked", "", {
      seek_from_time: Number(seekFromTime || 0),
    });
    seekFromTime = null;
  }

  function onTimeUpdate() {
    if (!activeVideo.seeking) lastStableTime = activeVideo.currentTime;
  }

  function bindVideo(video) {
    if (activeVideo === video) return;
    if (activeVideo) {
      activeVideo.removeEventListener("play", onPlay);
      activeVideo.removeEventListener("pause", onPause);
      activeVideo.removeEventListener("seeking", onSeeking);
      activeVideo.removeEventListener("seeked", onSeeked);
      activeVideo.removeEventListener("timeupdate", onTimeUpdate);
      activeVideo.removeEventListener("ratechange", onRateChange);
      activeVideo.removeEventListener("ended", onEnded);
      activeVideo.removeEventListener("loadedmetadata", onMetadata);
      activeVideo.removeEventListener("durationchange", onMetadata);
    }
    activeVideo = video;
    if (!video) return;
    lastStableTime = video.currentTime;
    video.addEventListener("play", onPlay);
    video.addEventListener("pause", onPause);
    video.addEventListener("seeking", onSeeking);
    video.addEventListener("seeked", onSeeked);
    video.addEventListener("timeupdate", onTimeUpdate);
    video.addEventListener("ratechange", onRateChange);
    video.addEventListener("ended", onEnded);
    video.addEventListener("loadedmetadata", onMetadata);
    video.addEventListener("durationchange", onMetadata);
    sendEvent("player_detected");
  }

  function onRateChange() {
    sendEvent("ratechange");
  }

  function onEnded() {
    sendEvent("ended");
  }

  function onMetadata() {
    sendEvent("metadata");
  }

  async function executeCommand(command) {
    const video = activeVideo;
    if (!video) return;
    try {
      if (command.action === "pause") {
        if (video.paused) {
          sendEvent("command_pause_ack", "already_paused");
        } else {
          video.pause();
        }
      } else if (command.action === "play") {
        allowPlayUntil = Date.now() + 2500;
        await video.play();
      } else if (command.action === "set_rate") {
        const rate = Number(command.rate);
        if (Number.isFinite(rate) && rate >= 0.25 && rate <= 4) {
          video.playbackRate = rate;
          video.defaultPlaybackRate = rate;
          sendEvent("rate_applied");
        }
      } else if (command.action === "status") {
        sendEvent("status");
      }
    } catch (error) {
      sendEvent("command_error", String(error?.message || error), {
        command_id: command.id,
        command_action: command.action,
      });
    }
  }

  async function poll() {
    if (pollInFlight) return;
    const candidate = findActiveVideo();
    if (candidate !== activeVideo) bindVideo(candidate);
    if (!activeVideo) return;
    pollInFlight = true;
    try {
      const response = await chrome.runtime.sendMessage({
        type: "sct-poll",
        event: "heartbeat",
        player: snapshot(),
      });
      if (response?.ok) {
        appState = response.app_state || appState;
        lastPollError = "";
        for (const command of response.commands || []) {
          await executeCommand(command);
        }
      } else {
        lastPollError = response?.error || "Recorder bridge unavailable";
      }
    } catch (error) {
      lastPollError = String(error?.message || error);
    } finally {
      pollInFlight = false;
    }
  }

  new MutationObserver(() => {
    const candidate = findActiveVideo();
    if (candidate !== activeVideo) bindVideo(candidate);
  }).observe(document.documentElement, { childList: true, subtree: true });

  bindVideo(findActiveVideo());
  // Window capture runs before focused playback controls (including the
  // seek/scrubber slider) can consume Backspace.
  window.addEventListener("keydown", onLearningNoteKeydown, true);
  setInterval(poll, 350);
  poll();

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "sct-content-status") {
      sendResponse({
        ok: Boolean(activeVideo),
        provider: PROVIDER,
        player: snapshot(),
        bridge_error: lastPollError,
      });
    }
  });
})();
