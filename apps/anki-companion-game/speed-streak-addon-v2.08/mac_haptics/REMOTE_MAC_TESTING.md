# Remote Mac test: no controller and no administrator access

This test validates the native helper without changing Speed Streak's normal visuals or selecting a backend manually. A controller is not required. Xcode Command Line Tools must already be present; the scripts do not install software or request administrator access.

## 1. Open Terminal in this folder

The folder is `speed-streak-addon-v2.04/mac_haptics` inside the repository.

## 2. Build and run the standalone check

```sh
sh ./run_controller_free_test.sh
```

Expected result:

```text
Controller-free native integration: PASS
Controllers: 0
Haptics-capable controllers: 0
```

The exact controller counts may be higher if the remote Mac exposes a controller. The script writes `SpeedStreakHaptics-diagnostic.json`; send that file back for investigation if any stage fails.

If the build says Xcode Command Line Tools are missing and the machine does not permit installing them, stop there. The helper can instead be built by a macOS GitHub Actions runner and brought back to this Mac for the remaining checks.

## 3. Install the development copy into Anki

Quit Anki completely, then run from the `mac_haptics` folder:

```sh
sh ../install_to_anki.sh
```

Restart Anki. This uses the current macOS user's Anki add-on folder and does not require administrator privileges.

## 4. Run the in-Anki check

Choose:

```text
Speed Streak > macOS Haptics Diagnostics…
```

Open the details and click **Copy Report**. The desired controller-free result is:

- helper bundle and executable found;
- launch attempted and helper running;
- protocol handshake passed;
- GameController status received;
- zero controllers accepted as a valid result;
- ordinary output still reports browser fallback while no native haptics-capable controller exists.

An ad-hoc development build may show that Gatekeeper distribution assessment did not pass. That is expected. The public package will need the separate Developer ID signing and notarization build.

## What this does not prove

This test cannot confirm physical vibration, motor strength, left/right mapping, Bluetooth behavior, USB behavior, or disconnect/reconnect behavior with real hardware. Those remain explicitly unconfirmed until a controller test is available.
