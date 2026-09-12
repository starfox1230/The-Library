(function () {
  if (window.SpeedStreakAudio) {
    return;
  }

  const state = {
    standbyByUrl: new Map(),
    activeByChannel: new Map(),
  };

  function clamp(value, minimum, maximum) {
    return Math.max(minimum, Math.min(maximum, value));
  }

  function createAudio(url) {
    const audio = new Audio();
    audio.preload = "auto";
    audio.src = url;
    try {
      audio.load();
    } catch (_error) {
      // play() remains the authoritative browser compatibility check.
    }
    return audio;
  }

  function prepare(url) {
    const normalizedUrl = String(url || "");
    if (!normalizedUrl) {
      return false;
    }
    if (!state.standbyByUrl.has(normalizedUrl)) {
      state.standbyByUrl.set(normalizedUrl, createAudio(normalizedUrl));
    }
    return true;
  }

  function takePreparedAudio(url) {
    // Chromium can stutter when a short compressed element is rewound. Each
    // element is therefore played once, while its replacement starts loading
    // immediately for the next cue.
    const audio = state.standbyByUrl.get(url) || createAudio(url);
    state.standbyByUrl.set(url, createAudio(url));
    return audio;
  }

  function silence(audio) {
    if (!audio) {
      return;
    }
    try {
      // Mute before pausing so interrupting a waveform does not create a click.
      audio.volume = 0;
      audio.pause();
    } catch (_error) {
      // A failed or detached element is already effectively silent.
    }
  }

  function stop(channel) {
    const normalizedChannel = String(channel || "feedback");
    const active = state.activeByChannel.get(normalizedChannel);
    silence(active);
    state.activeByChannel.delete(normalizedChannel);
    return true;
  }

  function play(url, options) {
    const normalizedUrl = String(url || "");
    if (!normalizedUrl) {
      return false;
    }

    const settings = options || {};
    const channel = String(settings.channel || "feedback");
    const interrupt = settings.interrupt !== false;
    const requestedVolume = Number(settings.volumePercent);
    const volumePercent = Number.isFinite(requestedVolume) ? requestedVolume : 100;
    const requestedPosition = Number(settings.positionMs);
    const positionMs = Number.isFinite(requestedPosition) ? Math.max(0, requestedPosition) : 0;
    const previous = state.activeByChannel.get(channel);

    if (!interrupt && previous && !previous.paused && !previous.ended) {
      return false;
    }

    try {
      const audio = takePreparedAudio(normalizedUrl);
      if (previous && !previous.paused) {
        silence(previous);
      }
      audio.volume = clamp(volumePercent / 200, 0, 1);
      state.activeByChannel.set(channel, audio);

      let started = false;
      const start = function () {
        if (started || state.activeByChannel.get(channel) !== audio) {
          return;
        }
        started = true;
        if (positionMs > 0) {
          try {
            audio.currentTime = positionMs / 1000;
          } catch (_error) {
            // Some engines only permit seeking after metadata is available.
          }
        }
        const promise = audio.play();
        if (promise && typeof promise.catch === "function") {
          promise.catch(function () {
            if (state.activeByChannel.get(channel) === audio) {
              state.activeByChannel.delete(channel);
            }
          });
        }
      };

      if (positionMs > 0 && audio.readyState < 1) {
        audio.addEventListener("loadedmetadata", start, { once: true });
      } else {
        start();
      }
      return true;
    } catch (_error) {
      return false;
    }
  }

  window.SpeedStreakAudio = {
    prepare: prepare,
    play: play,
    stop: stop,
  };
})();
