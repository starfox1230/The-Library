# PACS Localizer Native

[Download PACSLocalizer.exe](https://github.com/starfox1230/The-Library/raw/refs/heads/main/apps/pacs-localizer-native/dist/PACSLocalizer.exe)

Native C++ / Win32 replacement for Sterling's Ctrl + right-button AutoHotkey localizer. Windows x64, standalone: no installer, AutoHotkey, .NET, or separate runtime DLLs. Close the old AHK executable, download this EXE, and double-click it. A tray icon appears near the clock (possibly under the hidden-icons arrow). It does not start automatically at login.

## Controls

| Gesture | Result |
| --- | --- |
| Hold Ctrl + right mouse button for 140 ms | Sends unmodified F12, waits for the tool, holds left mouse button, and switches system cursors to a crosshair. Move the mouse normally. |
| Release right mouse button or release both Ctrl keys while active | Releases left mouse button, restores cursors, and sends F12 again. |
| Ctrl + right-button double tap within 500 ms of the first release | Sends one F12 on the second release. Holding the second tap never activates a drag. |
| Single short Ctrl + right-button tap | No action. |
| Ctrl + Alt + F12 | Exits, releasing simulated input and restoring cursors. |
| Right-click tray icon | Pause/resume, controls, or exit. |

Other Ctrl shortcuts, ordinary right clicks, mouse movement, and scrolling pass through. Shortcuts are global, as in the supplied AHK script. A press begun with Ctrl remains recognized if Ctrl is released before the 140 ms hold threshold, matching the original `g_ctrlR` behavior. Once a hold activates, releasing Ctrl ends it; its later right-button release cannot become the first tap of a new double tap.

## Changes intended to improve smoothness

- A dedicated input-hook thread only checks button/key state and posts gesture messages. No sleep, input injection, cursor replacement, logging, or file access occurs inside a hook callback.
- One serial state machine controls F12 and the left button, including releases during activation. No overlapping activation/deactivation timers or reentrant cleanup.
- F12 pulses last 25 ms. A separate 75 ms tool-settle interval follows F12-up before left-button-down. All intervals use nonblocking timers; mouse motion is never replayed, throttled, or synthesized.
- Modifier release, injected event, and modifier restoration use one ordered `SendInput` batch. This reproduces non-Blind AHK sending rather than accidentally sending Ctrl+F12 or Ctrl+left-button.
- Crosshair handles are prepared ahead of use. System cursor replacement is done only at mode transitions, on the main thread.
- Duplicate instances are refused. Focus loss cancels a hold and releases simulated buttons. F12 is not sent into another application after focus changes. This can leave the original PACS tool selected; return to PACS and use F12 if needed.

This is a timing/input-handling improvement, not a verified cure for skipped slices. PACS rendering, remote-desktop input handling, and mouse settings can still cause jumps. The app does not modify wheel deltas, PACS settings, or image data. Windows timers may fire later than their nominal intervals under load.

## Optional tuning

The download works alone. To tune it, copy `PACSLocalizer.example.ini` beside the EXE and rename the copy `PACSLocalizer.ini`. Restart the app after editing. For a slow Citrix connection, try `ToolSettleMs=120` or `150`. To isolate cursor overhead, set `Crosshair=0`. The default remains `1` to preserve the supplied crosshair behavior. Set `ToolSettleMs=0` for the original immediate-click timing.

Run at the same Windows permission level as PACS. If Windows blocks an injected event, the app releases its simulated input and pauses, with a tray notification. The executable is unsigned, so Windows or institutional controls may display a warning or block it. Follow your workstation's software policies.

Normal exit restores system cursors. A forced process kill or crash can bypass cleanup, as with the original AHK system-cursor approach. Windows Settings > Mouse > Additional mouse settings > Pointers > OK restores the cursor scheme. The app does not add startup entries or record keyboard/mouse activity.

## Build and validation

- Linux cross-build: install `g++-mingw-w64-x86-64`, then run `bash build-mingw.sh`. The included EXE uses MinGW-w64 GCC 13.2, static runtime linking, and only standard Windows system DLL imports.
- Windows: run `build-windows.cmd` from an x64 Visual Studio Developer Command Prompt. It runs the state-machine tests before building the GUI app with a static C++ runtime.
- Portable tests: `g++ -std=c++17 -Wall -Wextra -Werror tests/engine_test.cpp -o engine-test && ./engine-test`.
- Automated coverage: hold threshold, single/double tap, prolonged second tap, release during F12/setup, Ctrl-first release, cancellation, overlapping presses, and 200,000 randomized state transitions checking balanced key/button events.
- This build was cross-compiled and its portable tests passed with AddressSanitizer and UndefinedBehaviorSanitizer (leak detection disabled due to the build container). Interactive Windows hooks, cursor appearance, and PACS/Citrix behavior have not been tested on Sterling's workstation.

The SHA-256 for the included executable is in `dist/SHA256SUMS.txt`. Source and binary are committed together for inspection and rebuilding.

## Windows API references

- [LowLevelMouseProc](https://learn.microsoft.com/en-us/windows/win32/winmsg/lowlevelmouseproc): callbacks must return quickly.
- [SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput): ordered injection, modifier state, and permission-level restrictions.
- [SetSystemCursor](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setsystemcursor): cursor-handle ownership.
