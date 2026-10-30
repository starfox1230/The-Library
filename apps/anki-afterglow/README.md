# Afterglow 0.4 — personal Windows preview

A separate Anki desktop add-on: a full-window audio-reactive particle cloud with individual letter halos. The new mode is an original approximation of the principles in Bileam Tschepe's [Audioreactive Particle Cloud (new)](https://www.elekktronaut.com/tutorials/audioreactive-particle-cloud-new): age-colored line particles, audio-driven speed and lagged camera motion. It does not load the creator's project or require TouchDesigner. Plays alongside Speed Streak without importing it, patching its code, or accessing its timers. Works without Speed Streak too. Does not change saved card fields, scheduling, answer keys, or music playback.

## Particle cloud and performance

**Particle cloud** is the default visual for this update. The GPU renders 12,000 seeded particle trails in Smooth and 5,000 in Economy, using two batched drawing calls per pane. No particle positions are copied through Python each frame. Eight smoothed audio bands advance eight forward-only particle clocks; falling amplitude slows the clocks instead of pulling particles back. Detected attacks gently advance a camera target, which is followed with a long lag. Camera motion continues quietly between attacks. Colors follow particle age. **Ember** provides coral/gold/violet coloring. The cloud uses deterministic curved trajectories, rather than the tutorial's full compute-shader physics simulation. Bloom, selective luma blur, mirrors and the creator's exact presets are not reproduced.

On Sterling's Intel Arc graphics, the included isolated three-pane Qt WebEngine test measured approximately **60 FPS per pane at 1920×1080**, with 95th-percentile frame intervals of 16.7–16.8 ms. An Edge test also measured about 60 FPS. These are renderer frame-cadence measurements, not a guarantee of live Anki review performance with other add-ons, large images or the TV's display settings. The review meter now reports actual animation FPS. A simplified 900-point Canvas fallback is used if WebGL cannot initialize; the standalone diagnostics identify that fallback.

Open **Tools → Afterglow — Standalone performance preview** to render the same cloud in a separate Edge window, while Anki can remain open. This reads real local system audio and displays the graphics device, frame rate and frame intervals. It is a comparison window; it does not make the Anki window transparent. Qt supports transparent [web pages](https://doc.qt.io/qt-6/qwebenginepage.html#backgroundColor-prop), but full native-window transparency introduces additional composition and focus handling. The tested integrated GPU path gives us a useful first option without requiring that window-management change.

You can also run `start_preview.ps1` directly from the source folder, including before reinstalling Anki. It uses Python available on the machine or bundled with Anki. The preview's HTTP service binds only to 127.0.0.1, serves only its preview assets and numeric audio state, and stops immediately with **Stop**, or about 90 seconds after the last browser poll. No microphone, audio files or internet service is used. Closing the comparison window leaves a short idle timeout before its listener shuts down.

The previous **Liquid wall** remains available in the **Visual** selector. There are no mouse-movement handlers in either visual. For the cloud, **Motion** controls overall speed and **Light intensity** controls brightness. The liquid mode retains its **Music / beat impact** setting for fold deformation. Letter halos and independent card zoom apply to both.

Both visuals use bounded resolution (1024×720 at Smooth, 720×480 at Economy) and require no external graphics engine or downloaded assets. The liquid mode uses a three-octave warped color field with a cached Canvas ribbon fallback. The fallback and GPU versions share music inputs and layout but have different detail. GPU availability and other active add-ons still affect frame rate.

## Install or replace

Close Anki, then run from any PowerShell location:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-afterglow\install_to_anki.ps1"
```

Restart Anki and review a card. Open **Tools → Afterglow — Music background** for the enable switch, audio response, intensity, motion, letter halos, palette, quality, and timing advance. When Speed Streak's top-level menu is present, the same action also appears there after the profile opens. This uses Qt's public menu interface and never changes Speed Streak's files. Settings apply immediately. The installer refuses to run while Anki is open, replaces files in the stable `anki_afterglow` folder, and preserves `meta.json` settings. Disable or remove Afterglow through Anki's add-on manager to restore normal review backgrounds.

Windows .NET Framework's C# compiler builds the small audio helper during installation. No pip, Python wheels, Spotify account, audio driver, or microphone permission is required. `build.ps1` also generates a local `afterglow.ankiaddon` for Tools → Add-ons → Install from file. The generated binary/package are local build outputs, not committed source.

## Sound and timing

The hidden helper uses Windows WASAPI shared-mode loopback on connected playback devices, including HDMI/TV, USB and Bluetooth outputs. It calculates 20 ms loudness, bass and eight broad frequency-band RMS windows per output. The bands are an IIR filter bank, not the tutorial's full FFT spectrum resampled to 100 values. Automatic selection follows the output carrying the strongest sustained signal, with a hold period to prevent flapping; it does not rely on the default-device setting. New outputs are checked every two seconds. Switching outputs resets beat tracking to avoid carrying the old rhythm across. Only numeric features and output names reach Anki, not the sound samples. No files are recorded and no microphone is used. The add-on's listener is local; the optional standalone comparison uses a loopback-only HTTP connection. Listening in Anki runs only during reviews with the feature enabled; its helper exits when leaving reviews or closing the profile. The system mix includes other sounds such as Anki's own audio. Exclusive-mode/protected audio may not be available.

The review-screen meter identifies the selected device, signal activity and animation FPS. It says **Hearing music** while sound is detected and shows BPM once the predictor locks. Settings also show raw signal strength and a meter. Detected attacks advance the cloud camera target, even before tempo lock; silence produces gentle drift. Stale input settles. Motion 0 or OS reduced motion freezes the light show and is identified by the meter.

An independent streaming detector finds attacks, estimates a 75–180 BPM tempo, and aligns a predictive clock to recent beats. It needs several clear beats to lock, can choose half/double tempo, and may lose lock during breakdowns or changes. It falls back to smooth loudness response when confidence or recent sound drops. This is an initial heuristic tracker, not a promise of perfect synchronization. Adjust **Timing advance (ms)** upward if the lights feel late and downward if early; negative values delay the light. Device and rendering delays vary.

## Visual integration

**Extend behind toolbars, answer buttons and side panes** is on by default. The review view, top toolbar, answer bar and embedded review panes draw aligned slices of one scene, using the same clock and window coordinates. Buttons retain their handlers and colors with translucent surfaces; toolbar and Speed Streak pane backgrounds become transparent. Floating Speed Streak windows outside the main review window are independent. Native Windows title/menu bars retain their normal appearance in windowed mode. **Speed Streak / Tools → Afterglow — Toggle immersive fullscreen**, or **Ctrl+Alt+F11**, uses Anki's own fullscreen mode; press the same shortcut to leave fullscreen. Switching immersive coverage off restores other panes immediately.

Images stay opaque and unmodified. Card container backgrounds can be replaced; switch that setting off for notes whose backgrounds carry meaning. Computed text color selects a dark or pale per-letter halo without recoloring the letters. No text is wrapped or changed. Scrollbar tracks are transparent with a thin visible thumb. Custom card CSS using aggressive stacking contexts or opaque tables may need adjustment.

Frame rate is bounded to 30/60 FPS; backing resolution is capped according to quality with at most 1.25× device density. Rendering stops in hidden documents; Motion 0 and OS reduced-motion preferences produce a still scene. Lights use soft pulses rather than abrupt full-screen flashes. Disabling the feature removes its styling immediately.

Card zoom scales the card's content while the background stays anchored to native window coordinates. Main and toolbar views can use different zoom factors. Each pane's native width/height and display density are supplied explicitly; CSS viewport pixels and browser DPR are not used to size the Anki scene. A Qt WebEngine regression test covers 75–250% zoom. Transparent buttons do not apply a blur filter, and renderer health checks send a small existence probe instead of repeatedly sending the renderer's full source.

The browser [preview](index.html) uses the same renderer and a clearly labeled simulated rhythm. It does not capture audio. Live HDMI system capture was confirmed with Sterling's TOSHIBA-TV output. Perceived synchronization and live card-template appearance still need hands-on confirmation after installing the update.

## Sources and portability

Audio capture: [Microsoft WASAPI loopback](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording). The COM bridge and beat tracker are implemented here without third-party runtime code. All analysis/rendering could be reused with future capture backends. This initial package supports system capture only on Windows; other platforms retain ambient visuals and report that limitation.

Validation is recorded in `VALIDATION.md`.
