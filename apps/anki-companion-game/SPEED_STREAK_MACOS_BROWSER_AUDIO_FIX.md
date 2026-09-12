# macOS browser audio fix 2

Build: `2.04-macos-browser-audio.2`

Installable file: `speed-streak-addon-v2.04/speed_streak_v2_04_macos_browser_audio_fix2.ankiaddon`

This supersedes `speed_streak_v2_04_audio_lifetime_hotfix.ankiaddon`. The first
hotfix still used QtMultimedia and displayed version 2.04. Its archive filename
was not an installed-build indicator. The user reported the same native crash
again about 35 minutes after launch, with Anki in the background. That disproves
the adequacy of the lifetime-only mitigation; it does not identify the precise
Qt object behind the unsymbolicated stack offsets.

## What changed

- Speed Streak does not import or construct QtMultimedia audio classes on macOS.
  This applies to all four creation helpers, the defensive object factory,
  startup/profile preloading, warm-ups, event playback, countdowns, alignment
  previews and native diagnostics.
- Removed the QMediaDevices monitor introduced by the first hotfix.
- All macOS clips, including WAV, use the existing embedded-browser audio player.
  Volume and alignment position are passed through; countdown and alignment keep
  separate channels. If the browser is unavailable, the cue fails without using
  Anki's shared AV player or a native fallback.
- The native diagnostic button is disabled on macOS. Diagnostic reports identify
  the exact build and `browser-only (macOS)` policy without creating audio devices.
- Settings and Help / Feedback window titles display the build ID. The package
  identity remains `speed_streak_v2_04` so this replaces the existing release.
- Windows/Linux retain their existing native/browser routing and lifetime fixes.
  Haptics is unchanged. The same fix is included in the v2.05 source and rebuilt
  package as `2.05-macos-browser-audio.2`.

This controls Speed Streak's audio code. It cannot prevent Anki or another add-on
from independently loading QtMultimedia. A full restart is required to remove
objects loaded by the old build from the process.

## Verify the installed build

1. Install the new archive using Anki's Add-ons > Install from file.
2. Fully quit Anki and reopen it.
3. Open Speed Streak Settings or Help / Feedback. Its window title must include
   `2.04-macos-browser-audio.2`.
4. An Audio Check report also includes `Build: 2.04-macos-browser-audio.2` and, on
   macOS, `Audio policy: browser-only (macOS)`.

Test review sounds, countdowns and alignment previews, then leave Anki in the
background substantially longer than the previously reported 35 minutes. Confirm
the build label before reporting whether the crash recurs. Native crash resolution
has not yet been verified on the affected Mac. Browser timing/codec support can
differ from native Qt playback; countdown alignment remains available.

## Automated validation

- v2.04: 98 unittest tests passed.
- v2.05: 101 unittest tests passed.
- Shared companion-game suite: 204 pytest tests passed.
- Existing browser-audio JavaScript checks passed.
- macOS simulation intercepts imports across public audio operations and confirms
  zero attempts to import QtMultimedia classes or Anki's shared AV player.
- Behavioral routing checks exercise disabled-audio startup normalization, WAV
  and MP3 previews, seek position, volume, countdown channels, all tested review
  events, native diagnostics and unavailable-browser fallback.
- Real Windows QtWebEngine played a muted countdown WAV successfully without a
  Python QtMultimedia module loaded. This is not a native macOS crash reproduction.
- Both archives were checked for ZIP integrity, exact source contents and build ID.

Windows reinstall from this checkout, with Anki closed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-companion-game\speed-streak-addon-v2.04\install_to_anki.ps1"
```
