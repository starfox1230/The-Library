# Native macOS controller haptics: v2.03 validation design

## Decision

Use a small Swift helper app that links Apple's `GameController` and `CoreHaptics` frameworks. The add-on talks to it over newline-delimited JSON on standard input/output. Native output owns a haptic event only when the helper reports at least one haptics-capable controller; otherwise the existing QtWebEngine Gamepad implementation remains the fallback.

The helper may launch with zero controllers so a remote Mac can validate compilation, packaging, process startup, Apple-framework initialization, IPC, status reporting, shutdown, and safe fallback. Native output still remains unavailable until Apple's framework reports a controller with at least one successfully created haptic engine. `POC_VALIDATED.json` records later physical-rumble confirmation for diagnostics; it is evidence, not a launch gate.

Backend selection is automatic. macOS tries the native helper first and uses it only when it reports a haptics-capable controller. Windows retains its existing Steam Input/XInput order. No new backend selector or ordinary reviewer visual is introduced.

## Why this backend

- Apple exposes controller haptics through `GCController.haptics`, `GCDeviceHaptics.supportedLocalities`, and `createEngine(withLocality:)`. Apple's documentation explicitly says to use `supportedLocalities` rather than a generic engine capability flag.
- Chromium's February 2026 macOS implementation uses the same frameworks. It creates left/right handle engines when available, falls back to the default locality for a single-channel controller, maps strong magnitude to the left handle and weak magnitude to the right, and restarts engines after recoverable stops.
- A helper process can be independently signed, notarized, diagnosed, restarted, and disabled without loading native code into Anki. An in-process dylib would be coupled to the host application's hardened-runtime and library-validation policy.
- PyObjC is not part of the add-on or Anki's guaranteed Python surface. Adding it would substantially increase the package and native dependency matrix.
- Swift 5 has a stable ABI on Apple platforms, so a macOS 11+ helper can use the operating system's Swift runtime rather than bundling a private runtime.

## Protocol

Protocol version: `1`.

Commands are one JSON object per line:

- `status`: request controller/backend status.
- `play`: play `steps`, where each step has `duration` in milliseconds and normalized `weak` and `strong` magnitudes.
- `stop`: stop active players.
- `shutdown`: stop haptics and exit cleanly.

The helper emits `ready`, `status`, `playResult`, `stopped`, `shutdown`, and structured `error` events. `ready` identifies the helper version, architecture, macOS version, initialized frameworks, and background-monitoring state. Status includes controller count, haptics-capable controller count, vendor/product names, supported localities, active engine localities, and engine-creation failures.

The Python bridge retains a bounded event tail, stderr tail, handshake payload, latest status, and latest play result. A macOS-only menu command builds a copyable diagnostic report. It performs read-only architecture, signature, Gatekeeper, quarantine, Xcode, and Swift probes only when the user deliberately requests the report.

## Controller lifecycle and pattern mapping

- Existing controllers are enumerated at startup.
- connect/disconnect notifications add and remove sessions automatically.
- background controller monitoring is enabled on macOS 11.3+ because Anki, rather than the accessory helper, is the foreground app.
- wireless discovery is started while the helper is alive.
- every Speed Streak pattern remains sourced from `HAPTIC_PATTERN_LIBRARY`.
- controllers with left/right handle localities receive strong on the left and weak on the right, matching Chromium's implementation.
- single-channel controllers receive `clamp(strong + weak, 0, 1)` through the default locality.
- each pattern is one finite CoreHaptics timeline, preserving pulse lengths and silent gaps without Python sleep timing.

## Controller-free validation and distribution

On any macOS 11+ development machine with Xcode Command Line Tools already installed:

1. Run `sh ./run_controller_free_test.sh` from `mac_haptics`.
2. Confirm the script reports `Controller-free native integration: PASS`. Zero controllers is valid.
3. With Anki closed, run `sh ../install_to_anki.sh`.
4. Restart Anki and choose `Speed Streak > macOS Haptics Diagnostics…`.
5. Copy the report. The first six controller-free integration stages should pass.

These steps require no administrator privileges. An ad-hoc local build is expected to fail Gatekeeper's public-distribution assessment; that does not invalidate local launch/IPC testing.

A publicly distributed helper needs all of the following:

1. Build a universal `arm64` + `x86_64` app bundle with a macOS 11 deployment target.
2. Sign it with Developer ID Application, hardened runtime, secure timestamp, and no debug entitlement.
3. Submit the containing ZIP with `notarytool`, staple the ticket to the app, and verify with `codesign`, `stapler`, and Gatekeeper assessment.
4. Confirm the final `.ankiaddon` extraction path. The Python bridge restores executable mode automatically because ZIP extraction on different platforms does not consistently preserve it; users must never run `chmod`, `xattr`, or `spctl` themselves.
5. Pass the controller-free standalone and in-Anki reports on macOS.
6. Keep physical output described as experimental/unconfirmed until at least one controller test creates `POC_VALIDATED.json`. A stable compatibility claim requires the broader matrix below.

The included `build_release.sh` automates the universal build, signing, notarization, stapling, validation, and staging into the add-on source folder. It requires an Apple Developer ID and a configured notary keychain profile.

## Required physical test matrix

- Apple Silicon Mac, Bluetooth Xbox Series controller.
- Apple Silicon Mac, USB Xbox Series controller.
- Apple Silicon Mac, Bluetooth DualSense or DualShock 4.
- Intel Mac for at least one haptics-capable controller.
- controller connected before Anki starts.
- controller connected after Anki starts.
- disconnect/reconnect during review.
- haptics on/off and preview buttons.
- every existing pattern, especially patterns with silent gaps.
- helper unavailable, unsupported controller, malformed IPC, helper crash, and Anki shutdown.
- Windows XInput and optional Steam Input regression.

Compatibility must be described by capability, not brand: controllers reported by Apple's framework with usable haptic localities are supported. Chromium's original change was manually verified only with an Xbox Series X/S controller over Bluetooth and explicitly reported that its wired test did not work; USB support therefore remains unproven here until the matrix passes.

## Primary references

- Apple `GCDeviceHaptics`: https://developer.apple.com/documentation/gamecontroller/gcdevicehaptics
- Apple `createEngine(withLocality:)`: https://developer.apple.com/documentation/gamecontroller/gcdevicehaptics/createengine(withlocality:)
- Apple `GCController`: https://developer.apple.com/documentation/gamecontroller/gccontroller
- Apple background controller monitoring: https://developer.apple.com/documentation/gamecontroller/gccontroller/shouldmonitorbackgroundevents
- Chromium macOS haptics commit: https://chromium.googlesource.com/chromium/src/+/85f76c3bf99277e2209aceb2fb406398287a3368
- Chromium Sony follow-up: https://chromium.googlesource.com/chromium/src/+/50244958c7839105a42b8e40402aa3826659d219
- Apple notarization requirements: https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
- Swift ABI stability: https://www.swift.org/blog/abi-stability-and-more/
