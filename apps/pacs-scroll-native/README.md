# PACS Precision Scroll Native

[Download PACSScroll.exe](https://github.com/starfox1230/The-Library/raw/refs/heads/main/apps/pacs-scroll-native/dist/PACSScroll.exe)

Standalone native C++ / Win32 scrolling tool for Windows x64. Close the old scrolling AHK EXE, download this file, and double-click it. No installation, AutoHotkey, .NET, or extra runtime downloads. Its tray icon is near the clock, possibly under the hidden-icons arrow. Nothing is added to startup. This is the replacement for `original.ahk`, **not** the Ctrl-right-button F12 localizer built earlier.

## Feature mapping to the supplied scrolling script

| Original feature | Native behavior |
| --- | --- |
| Hold middle button for 300 ms | Starts precision scrolling. Releasing before 300 ms cancels; releasing after activation leaves it on. |
| Hold progress ring | 56px ring, 6px stroke, dark base, top-start arc progressing red to green, follows cursor. Transparent, antialiased, click-through, no focus capture. |
| Middle click during either scroll mode | Stops that mode immediately; a held stop click does not start another mode. |
| Precision mouse movement | Vertical displacement produces full wheel ticks. First movement emits one tick. Later movement uses accumulated distance and threshold `51 - sensitivity`. |
| Sensitivity | 1–50, default 43 (8px threshold). Shift increases it, Ctrl decreases it, both left and right keys. Values stay selected until exit. |
| Direction halt | Reversal clears pending movement and pauses 50 ms; motion during the pause is ignored. |
| Infinite vertical wrapping | 100px edge margin, preserves X, returns Y to screen center. Uses the current monitor, including negative desktop coordinates. |
| Ctrl + middle button | Toggles auto-scroll; switching from precision cancels it and the hold ring. |
| Auto-scroll defaults | Starts in the last wheel direction, initially Down, at 25 ticks/second. Remembers selected speed until exit. |
| All 23 auto-scroll speeds | 7, 12.5, 19, 25, 31, 37.5, 50, 62.5, 75, 87.5, 100, 112.5, 125, 137.5, 150, 162.5, 175, 187.5, 200, 212.5, 225, 237.5, 250 ticks/second. |
| Auto speed keys | Shift increases speed one step; Ctrl decreases it, bounded to the original list. Keyboard repeat remains supported. |
| Auto direction | Up/Down keys change direction without a tooltip. Physical wheel changes direction and is swallowed, so it does not add wheel events on top of auto-scroll. |
| Ordinary physical wheel | Passes through outside auto mode and updates the last wheel direction. |
| No auto cursor restrictions | No locking, recentering, or synthetic motion in auto mode. Cursor wrapping applies only in precision mode. |
| Optional VirtualMonitor | Tries to activate a visible window whose title contains `VirtualMonitor` at hold/scroll startup; works without one. Activation is asynchronous, so it never blocks the scrolling scheduler. |
| Tooltips | Scroll ON/OFF, Auto-Scroll ON/OFF, sensitivity with default indicator, and rate-only speed updates with the original 900/700/650 ms durations. |
| Ctrl + Alt + 3 | Shows active executable filename and window title. |
| High hotkey-rate handling | Native hooks have no AutoHotkey hotkey-rate popup. |
| Cleanup | Hides overlays, stops the scheduler, unhooks input and frees graphics resources. No persistent system-cursor replacement. |

Added conveniences: right-click tray icon to pause/resume, view controls, or exit; double-click for controls; Ctrl+Alt+F12 pauses/resumes even when modifiers are being used as speed keys. Duplicate instances are refused. Suspend pauses the tool. Restart or Resume after suspension as appropriate.

## What changes for smoothness

The AHK precision loop emits all accumulated clicks in a single `Send` and its auto-scroll loop uses a `while` to replay overdue ticks. Both can produce bursts. This native version uses:

- A dedicated hook thread that never sleeps, renders, injects input, or performs file access in callbacks.
- A separate serial scrolling thread, performance-counter deadlines, and a Windows high-resolution waitable timer (with ordinary waitable-timer fallback).
- One full wheel event per scheduled output. The original precision samples remain 10 ms; clicks from each sample are distributed over time rather than sent in one burst.
- No replay of overdue auto-scroll ticks after a stall. Normal cadence preserves the selected rate; a delayed scheduler resumes without a catch-up flood.
- A bounded precision queue (64 ticks), at least 1 ms between precision events, and expiry after 100 ms without vertical motion. Stop/reversal discards pending work. Under overload, stale distance can be dropped instead of producing delayed jumps. This is an intentional scheduling difference, not a claim that every original wheel-event timestamp/count is reproduced under load.
- A separate UI thread for the ring/tooltips, reusing one bitmap and drawing surface instead of allocating a new bitmap/DC on every frame.
- Temporary modifier release/restoration around injected wheel events, matching the intent of non-Blind AHK `Send`. Captured speed keys do not leak to PACS, while unrelated keys pass through.

The original high process priority is not retained: the app uses normal priority and efficient waits so it does not compete unnecessarily with PACS. VirtualMonitor activation does not wait up to 0.5 seconds. Multi-monitor wrapping uses the current monitor rather than the original primary-screen-height assumption. These are internal reliability improvements; controls and available settings are retained.

## Validation and practical limits

The included Windows GUI EXE was cross-compiled with MinGW-w64 GCC 13.2, strict warnings, and static C++ runtime linking. Imports are Windows system DLLs only. Portable logic tests passed with AddressSanitizer and UndefinedBehaviorSanitizer (leak detection disabled in the build container). They cover hold/cancel, persistent precision mode, thresholds, reversal pause, both mode toggles, speed bounds, all 23 rates with 23,000 cadence checks, delayed scheduling, queue expiry, and stop behavior.

Interactive Windows hooks, overlay rendering and PACS/Citrix behavior require workstation testing; they were not exercised here. This cannot guarantee that PACS will display every image at 250 ticks/second. A viewer can skip rendered frames or handle wheel events differently even with evenly timed input. Compare at 7 or 12.5/s first if testing whether the underlying skips remain.

Windows/institutional software controls may flag the unsigned EXE. Run it at the same permission level as PACS. If input injection fails, scrolling pauses and displays a notice. Shortcuts are global, like the original. No keystrokes or mouse activity are saved; no network access, startup entry, or PACS configuration changes are performed.

## Build

- Linux: install MinGW-w64, then `bash build-mingw.sh` (`CXX` can override the compiler path).
- Windows: run `build-windows.cmd` from an x64 Visual Studio Developer Command Prompt; it runs the engine tests, then builds the standalone GUI EXE with `/MT`.
- Portable tests: `g++ -std=c++17 -Wall -Wextra -Werror tests/engine_test.cpp -o engine-test && ./engine-test`.
- Executable checksum: `dist/SHA256SUMS.txt`.

References: [high-resolution waitable timers](https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createwaitabletimerexw), [SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput), [wheel input units](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-mouseinput).
