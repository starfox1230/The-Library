# Speed Streak diagnostic builds

The active tracks are **2.05 (standard visuals)** and **2.07 (Hypernova + Sprint Time)**.
2.06 is the intermediate experimental track and was not updated in this change.
One logger is maintained here and copied into both active tracks by the build tool.

| Audience | Local build after this change | Package |
| --- | --- | --- |
| Standard development | `2.05-user-requests.14+diagnostics.1` | `../speed-streak-addon-v2.05/speed_streak_v2_05.ankiaddon` |
| Experimental development | `2.07-sprint-time.6+diagnostics.1` | `../speed-streak-addon-v2.07/speed_streak_v2_07.ankiaddon` |
| Mac shutdown investigation | `2.05-macos-diagnostic.1` | [Download the diagnostic package](releases/speed_streak_2_05_macos_diagnostic_1.ankiaddon) |

The investigation package starts from the AnkiWeb archive fetched September 30, 2026,
whose internal build is `2.05-user-requests.12`. Its original SHA256 is
`c0e15fc0bfb974706b20ae61c23fc3003a7b0c35971ec9e32a60c7c9636acfbb`.
Only initialization, the build label, the Help dialog, and the two new diagnostic
files differ. Gameplay, visual, audio, and haptic implementation files retain their
original bytes. The sidecar provenance file records the output hash and changed entries.
This is an evidence-gathering build; the unexplained shutdown has not been diagnosed
or reproduced. Nothing has been uploaded to AnkiWeb.

## Asking the tester for one useful report

Suggested message (draft; not sent):

> Hey, sorry for the slow reply. I still don't have enough evidence to tell what's
> closing Anki, and I don't want to keep asking you to try random changes. I made
> a diagnostic copy of the published 2.05 build that records recent technical
> events while you use it normally. It keeps your existing features and visuals.
> If you're willing, install the attached package through Anki's Add-ons window
> and restart Anki. If it closes again, reopen Anki and use Speed Streak → Help /
> Feedback → Copy Support Report, then paste that into your reply. Nothing is sent
> automatically, and the report doesn't include card content. You've already
> given me your versions; this report records the exact build and runtime itself.

The same action is available directly from the Speed Streak menu. Copy soon after
reopening so that the immediately previous session is the failed one. A macOS
crash report from that same occurrence, if macOS created one, can identify the
native crashing thread; the add-on report cannot provide that stack trace.

## What the report records

Build, Anki/Qt/Python/OS versions, a session ID, UTC and elapsed timestamps, import
stages, review/navigation events, a 30-second heartbeat, relevant settings flags,
audio/haptic requests and Python returns, browser media errors, existing gamepad
poll results and haptic calls, and shutdown callbacks. The logger reads SIGPIPE's
disposition without changing it. It does not start native audio, native controller
polls, helper processes, extra browser polling, or new gamepad connection listeners.
Python wrappers preserve original return values and rethrow original exceptions;
browser wrappers preserve the original promise objects.

Events are local under the Anki base directory:
`addons-data/speed_streak/diagnostics`. This is outside `addons21`, so replacing
the add-on preserves the logs. Each session keeps two files capped at 256 KiB
each; four sessions are retained, except another currently live session is never
deleted. Appends close/flush immediately, but a power loss can still lose OS buffers.
The clipboard report contains bounded tails of the preceding and current sessions.
It does not include card text/IDs, deck/profile names, media filenames, full paths,
controller device names, or exception messages. It sends nothing over the network.

An absent shutdown marker does not establish a crash, its category, or its cause.
An observed shutdown callback also does not prove successful process termination.
A haptic/audio request or accepted return does not prove sound/vibration occurred.
The last event is a clue for matching timestamps, not proof of causation.

## Maintain the two tracks

Edit the shared logger here once, then run from the repository root:

```powershell
python -B apps/anki-companion-game/tools/build_diagnostic_packages.py --tracks 2.05 2.07 --package-tracks
```

The tool is idempotent: it does not append another diagnostic suffix or Help card
on subsequent runs. Keep distinct feature build IDs; `+diagnostics.1` identifies
this shared instrumentation revision. When changing instrumentation, update that
revision in the build tool. A diagnostic build label is separate from a claim that
a crash is fixed.

The surrounding feature work in both local tracks predates this task and is left
outside the diagnostic commit. `integration/` stores the exact diagnostic deltas
against those local baselines, including the two corrected 2.07 test fixtures.
The shared build tool applies runtime integration to an existing track. The Git
commit also applies the integration to the already tracked 2.05 source. The
unpublished 2.07 feature baseline is not being introduced as an unrelated source
release. Local packages were rebuilt for both tracks.
The committed 2.05 source/package retain the previously committed feature build
`2.05-macos-browser-audio.2`, with the diagnostic suffix added; your newer local
`2.05-user-requests.14` feature changes remain intact in the working tree. This
keeps the diagnostic commit from silently publishing your unfinished changes.
The integration patches use zero context (apply with `git apply --unidiff-zero`
only against their matching local baselines); the shared runtime files are copied
by the build tool rather than duplicated in the patches.

Reproduce the tester package:

```powershell
python -B apps/anki-companion-game/tools/build_diagnostic_packages.py --frozen apps/anki-companion-game/diagnostics/baselines/speed_streak_2_05_user_requests_12.ankiaddon --output apps/anki-companion-game/diagnostics/releases/speed_streak_2_05_macos_diagnostic_1.ankiaddon --build 2.05-macos-diagnostic.1
```

Verification:

```powershell
python -B -m unittest discover -s apps/anki-companion-game/diagnostics/tests -v
node apps/anki-companion-game/diagnostics/tests/test_diagnostic_browser.cjs
python -B apps/anki-companion-game/diagnostics/verify_packages.py
python -B -m unittest discover -s apps/anki-companion-game/speed-streak-addon-v2.05/tests -p 'test_*.py'
python -B -m unittest discover -s apps/anki-companion-game/speed-streak-addon-v2.07/tests -p 'test_*.py'
```

The diagnostic tests exercise abrupt process termination, recovery on next launch,
rotation, failure containment, concurrent writes, input filtering, and operation
return/exception preservation. The real Qt fixture checks hooks, timer, menu and
clipboard without loading a real Anki profile. The browser fixture checks that
observation does not introduce polling or duplicate actuator calls. Windows test
success does not reproduce or validate the original macOS shutdown.

## Reinstall your experimental track on Windows

Close Anki, then run this from PowerShell:

```powershell
& 'C:\Users\sterl\Documents\GitHub\The-Library\apps\anki-companion-game\speed-streak-addon-v2.07\install_to_anki.ps1'
```

The installer refuses to run while Anki is open, replaces the installed code,
removes prior Speed Streak installations and preserves settings/history. Restart
Anki to load it. This command uses your local 2.07 feature work plus diagnostics.
