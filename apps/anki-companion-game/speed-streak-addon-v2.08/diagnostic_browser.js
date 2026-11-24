(function () {
  if (window.SpeedStreakDiagnostic) return;
  const page = Math.random().toString(36).slice(2, 10);
  let lastPads = "";
  let windowStart = 0;
  let count = 0;
  function emit(event, detail) {
    try {
      const now = Date.now();
      if (now - windowStart > 1000) { windowStart = now; count = 0; }
      if (++count > 25 || typeof pycmd !== "function") return;
      pycmd("speed-streak:diagnostic:" + JSON.stringify(Object.assign({event, page}, detail || {})));
    } catch (_) { /* Recording must never interrupt review. */ }
  }
  function observeAudio(audio) {
    for (const event of ["playing", "ended", "error"]) {
      audio.addEventListener(event, () => emit("audio_" + event,
        event === "error" ? {error: Number(audio.error && audio.error.code || 0)} : {}));
    }
  }
  window.SpeedStreakDiagnostic = {emit, observeAudio};
  emit("document_loaded", {hidden: document.hidden});
  document.addEventListener("visibilitychange", () => emit("visibility", {hidden: document.hidden}));
  window.addEventListener("pagehide", () => emit("pagehide"));
  window.addEventListener("unhandledrejection", event => {
    emit("unhandled_rejection", {error: event.reason && event.reason.name || "UnknownError"});
  });
  window.addEventListener("error", event => {
    emit("script_error", {error: event.error && event.error.name || "UnknownError"});
  });

  // Observe only calls already made by Speed Streak. Never initiate polling,
  // register gamepad event listeners, reset actuators, or consume their promises.
  try {
    const original = navigator.getGamepads;
    if (typeof original === "function") {
      navigator.getGamepads = function () {
        const pads = original.apply(this, arguments);
        try {
          const live = Array.from(pads || []).filter(Boolean);
          const signature = live.map(pad => pad.index + ":" + Boolean(pad.connected)).join(",");
          if (signature !== lastPads) {
            lastPads = signature;
            emit("controller_snapshot", {count: live.length});
          }
          for (const pad of live) {
            const actuator = pad.vibrationActuator || (pad.hapticActuators || [])[0];
            if (!actuator) continue;
            for (const method of ["playEffect", "pulse"]) {
              const fn = actuator[method];
              if (typeof fn !== "function" || fn.speedStreakObserved) continue;
              const observed = function () {
                emit("haptic_request", {index: pad.index, connected: Boolean(pad.connected),
                  duration: method === "playEffect" ? Number((arguments[1] || {}).duration || 0) : Number(arguments[1] || 0)});
                try { return fn.apply(this, arguments); }
                catch (error) { emit("haptic_exception", {error: error.name}); throw error; }
              };
              observed.speedStreakObserved = true;
              actuator[method] = observed;
            }
          }
        } catch (_) { /* Host objects can prohibit method replacement. */ }
        return pads;
      };
    }
  } catch (_) { emit("controller_observation_unavailable"); }
})();
