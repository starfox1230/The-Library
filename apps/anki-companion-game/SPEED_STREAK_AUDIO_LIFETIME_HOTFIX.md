# Speed Streak 2.04 audio lifetime hotfix

**Superseded:** The same native crash recurred after this patch. Use the
[macOS browser audio fix 2](SPEED_STREAK_MACOS_BROWSER_AUDIO_FIX.md) instead.
The original archive below remains available only as a historical build.

The reported macOS arm64 crash (Anki 26.08.1 / Qt 6.11.0) enters
`AudioObjectRemovePropertyListenerBlock` from QtMultimedia while another
CoreAudio thread is handling hardware changes. This is consistent with a native
listener lifetime race, but the abbreviated stack does not identify the exact
Qt object or prove that Speed Streak initiated its destruction.

## Verified risks and changes

- `on_profile_did_open()` replaced `AudioFeedbackController` when the data root
  changed. Its parentless audio objects could then be collected. It now rebinds
  profile upload paths and refreshes the catalog on the same controller.
- All six audio construction sites now give objects QApplication ownership and
  retain their Python wrappers before further setup. This includes players and
  outputs whose setup subsequently fails. Dialog close, profile change and
  playback stop do not delete these objects.
- macOS retains one application-owned `QMediaDevices` monitor when the API is
  available. Older Qt bindings without that API retain the prior playback path.
- Profile close stops audio even when no run is active. Generation checks cancel
  pending warm-up callbacks without deleting their native objects.
- Countdown stop now stops compressed media as well as WAV effects, and cancels
  pending countdown warm-ups independently of event-audio warm-ups.
- The same focused changes are present in the existing v2.05 source. Haptics,
  browser fallback selection, volume scaling and review sound overlap are unchanged.

Objects are retained until QApplication teardown. Memory therefore reflects the
distinct audio files prepared during the Anki session; revisiting the same file
or profile reuses its cached objects. This does not claim to repair a race wholly
inside Qt during hardware changes or final application shutdown.

Qt ownership reference: https://doc.qt.io/qt-6/objecttrees.html
Device monitor reference: https://doc.qt.io/qt-6.10/qmediadevices.html

## Validation

- v2.04 unittest suite: 96 passed, including 41 audio tests.
- v2.05 unittest suite: 99 passed.
- Repository companion-game pytest suite: 204 passed.
- Browser audio JavaScript checks passed.
- Real Windows PySide6 / Qt 6.11.0 smoke check passed for effect/player/output
  ownership, profile rebinding and stop. This is not a macOS/PyQt6 crash reproduction.

On the affected Mac, verify repeated countdown preview open/close, WAV and
compressed cues, output-device switching/disconnection, profile switching, and
Anki exit. Confirm review-event sounds, countdown timing and card audio remain
functional. Native crash resolution requires that confirmation.

## Install

The hotfix archive is
`speed-streak-addon-v2.04/speed_streak_v2_04_audio_lifetime_hotfix.ankiaddon`.
It preserves the v2.04 package identity and contains the complete add-on. Install
it through Anki's Add-ons > Install from file and restart Anki.

For this Windows checkout, close Anki and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-companion-game\speed-streak-addon-v2.04\install_to_anki.ps1"
```

The existing installer replaces the installed v2.04/older versions and preserves
legacy user data for migration. The original v2.04 archive is retained; use the
explicitly named hotfix archive for this build.
