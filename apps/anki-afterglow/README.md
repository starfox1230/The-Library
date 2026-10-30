# Afterglow 0.2 — personal Windows preview

A separate Anki desktop add-on: full-review-window cyan/violet/rose light, flowing filaments, a distant neon floor, and individual letter halos. Plays alongside Speed Streak without importing it, patching its code, or accessing its timers. Works without Speed Streak too. Does not change saved card fields, scheduling, answer keys, or music playback.

## Install or replace

Close Anki, then run from any PowerShell location:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-afterglow\install_to_anki.ps1"
```

Restart Anki and review a card. Open **Tools → Afterglow — Music background** for the enable switch, audio response, intensity, motion, letter halos, palette, quality, and timing advance. When Speed Streak's top-level menu is present, the same action also appears there after the profile opens. This uses Qt's public menu interface and never changes Speed Streak's files. Settings apply immediately. The installer refuses to run while Anki is open, replaces files in the stable `anki_afterglow` folder, and preserves `meta.json` settings. Disable or remove Afterglow through Anki's add-on manager to restore normal review backgrounds.

Windows .NET Framework's C# compiler builds the small audio helper during installation. No pip, Python wheels, Spotify account, audio driver, or microphone permission is required. `build.ps1` also generates a local `afterglow.ankiaddon` for Tools → Add-ons → Install from file. The generated binary/package are local build outputs, not committed source.

## Sound and timing

The hidden helper uses Windows WASAPI shared-mode loopback on connected playback devices, including HDMI/TV, USB and Bluetooth outputs. It calculates 20 ms loudness and low-frequency energy windows per output. Automatic selection follows the output carrying the strongest sustained signal, with a hold period to prevent flapping; it does not rely on the default-device setting. New outputs are checked every two seconds. Switching outputs resets beat tracking to avoid carrying the old rhythm across. Only numeric features and output names reach Anki, not the sound samples. No files are recorded, no microphone is used, and no network requests are made. Listening runs only during reviews with the feature enabled; the helper exits when leaving reviews or closing the profile. The system mix includes other sounds such as Anki's own audio. Exclusive-mode/protected audio may not be available.

The review-screen meter identifies the selected device and shows signal activity. It says **Hearing music** while sound is detected and shows BPM once the predictor locks. Settings also show raw signal strength and a meter. **Music / beat impact** controls how strongly the lights react. The light fans and edge arcs respond to detected attacks immediately, even before tempo lock; silence produces only the slow ambient backdrop. Stale input fades out. Motion 0 or OS reduced motion freezes the light show and is identified by the meter.

An independent streaming detector finds attacks, estimates a 75–180 BPM tempo, and aligns a predictive clock to recent beats. It needs several clear beats to lock, can choose half/double tempo, and may lose lock during breakdowns or changes. It falls back to smooth loudness response when confidence or recent sound drops. This is an initial heuristic tracker, not a promise of perfect synchronization. Adjust **Timing advance (ms)** upward if the lights feel late and downward if early; negative values delay the light. Device and rendering delays vary.

## Visual integration

**Extend behind toolbars, answer buttons and side panes** is on by default. The review view, top toolbar, answer bar and embedded review panes draw aligned slices of one scene, using the same clock and window coordinates. Buttons retain their handlers and colors with translucent surfaces; toolbar and Speed Streak pane backgrounds become transparent. Floating Speed Streak windows outside the main review window are independent. Native Windows title/menu bars retain their normal appearance in windowed mode. **Speed Streak / Tools → Afterglow — Toggle immersive fullscreen**, or **Ctrl+Alt+F11**, uses Anki's own fullscreen mode; press the same shortcut to leave fullscreen. Switching immersive coverage off restores other panes immediately.

Images stay opaque and unmodified. Card container backgrounds can be replaced; switch that setting off for notes whose backgrounds carry meaning. Computed text color selects a dark or pale per-letter halo without recoloring the letters. No text is wrapped or changed. Scrollbar tracks are transparent with a thin visible thumb. Custom card CSS using aggressive stacking contexts or opaque tables may need adjustment.

Frame rate is bounded to 30/60 FPS; backing resolution is capped at 1440×1000 with at most 1.25× device density. Rendering stops in hidden documents; Motion 0 and OS reduced-motion preferences produce a still scene. Lights use soft pulses rather than abrupt full-screen flashes. Disabling the feature removes its styling immediately.

The browser [preview](index.html) uses the same renderer and a clearly labeled simulated rhythm. It does not capture audio. Live HDMI system capture was confirmed with Sterling's TOSHIBA-TV output. Perceived synchronization and live card-template appearance still need hands-on confirmation after installing the update.

## Sources and portability

Audio capture: [Microsoft WASAPI loopback](https://learn.microsoft.com/en-us/windows/win32/coreaudio/loopback-recording). The COM bridge and beat tracker are implemented here without third-party runtime code. All analysis/rendering could be reused with future capture backends. This initial package supports system capture only on Windows; other platforms retain ambient visuals and report that limitation.

Validation is recorded in `VALIDATION.md`.
