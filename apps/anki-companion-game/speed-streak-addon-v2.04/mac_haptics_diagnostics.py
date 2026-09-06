from __future__ import annotations

import json
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple


def _redact(value: Any) -> str:
    text = str(value or "")
    try:
        home = str(Path.home())
        if home:
            text = text.replace(home, "<HOME>")
    except Exception:
        pass
    return text


def _probe(command: Sequence[str], timeout: float = 4.0) -> Dict[str, Any]:
    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = "\n".join(
            part.strip() for part in (completed.stdout, completed.stderr) if part.strip()
        )
        return {
            "command": " ".join(command),
            "returnCode": int(completed.returncode),
            "output": _redact(output[:6000]),
        }
    except FileNotFoundError:
        return {
            "command": " ".join(command),
            "returnCode": 127,
            "output": "Command is not installed.",
        }
    except subprocess.TimeoutExpired:
        return {
            "command": " ".join(command),
            "returnCode": 124,
            "output": "Command timed out.",
        }
    except Exception as exc:
        return {
            "command": " ".join(command),
            "returnCode": 1,
            "output": f"{type(exc).__name__}: {_redact(exc)}",
        }


def _anki_runtime() -> Dict[str, str]:
    runtime = {
        "python": platform.python_version(),
        "anki": "unknown",
        "qt": "unknown",
    }
    try:
        import aqt

        runtime["anki"] = str(getattr(aqt, "appVersion", "unknown"))
    except Exception:
        pass
    try:
        from aqt.qt import qVersion

        runtime["qt"] = str(qVersion())
    except Exception:
        pass
    return runtime


def _addon_version(root: Path) -> str:
    candidates = [root.name]
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        if isinstance(manifest, dict):
            candidates.insert(0, str(manifest.get("package") or ""))
    except Exception:
        pass
    for candidate in candidates:
        match = re.search(r"(?:^|_)v(\d+)_(\d+)(?:$|_)", candidate)
        if match:
            return f"{int(match.group(1))}.{match.group(2)}"
    return "unknown"


def _stage(label: str, passed: bool, detail: str) -> str:
    return f"[{'PASS' if passed else 'FAIL'}] {label}: {detail}"


def _probe_line(label: str, result: Mapping[str, Any]) -> str:
    code = int(result.get("returnCode", 1) or 0)
    output = str(result.get("output") or "No output.")
    status = "PASS" if code == 0 else "INFO"
    return f"[{status}] {label} (exit {code})\n{output}"


def collect_mac_haptics_report(
    addon_root: Path,
    diagnostics: Mapping[str, Any],
) -> Dict[str, Any]:
    root = Path(addon_root)
    bundle = Path(str(diagnostics.get("helperBundlePath") or root / "mac_haptics" / "SpeedStreakHaptics.app"))
    executable = Path(
        str(
            diagnostics.get("helperPath")
            or bundle / "Contents" / "MacOS" / "SpeedStreakHaptics"
        )
    )

    probes: Dict[str, Dict[str, Any]] = {}
    if sys.platform.startswith("darwin"):
        probes["xcodePath"] = _probe(("xcode-select", "-p"))
        probes["swiftCompiler"] = _probe(("xcrun", "swiftc", "--version"))
        if executable.is_file():
            probes["architectures"] = _probe(("lipo", "-archs", str(executable)))
        if bundle.is_dir():
            probes["codeSignature"] = _probe(
                ("codesign", "--verify", "--deep", "--strict", "--verbose=2", str(bundle))
            )
            probes["signatureDetails"] = _probe(
                ("codesign", "-dv", "--verbose=4", str(bundle))
            )
            probes["gatekeeper"] = _probe(
                ("spctl", "--assess", "--type", "execute", "--verbose=2", str(bundle))
            )
            probes["quarantine"] = _probe(
                ("xattr", "-p", "com.apple.quarantine", str(bundle))
            )

    direct_pyobjc = bool(diagnostics.get("directPyObjC"))
    browser_fallback_selected = bool(diagnostics.get("browserFallbackSelected"))
    direct_passed = bool(
        diagnostics.get("pyobjcFrameworksLoaded")
        and diagnostics.get("notificationsRegistered")
    )
    helper_transport_passed = all(
        bool(diagnostics.get(key))
        for key in (
            "helperExists",
            "launchAttempted",
            "helperRunning",
            "protocolReady",
            "statusReceived",
        )
    )
    signing_passed = int(probes.get("codeSignature", {}).get("returnCode", 1) or 0) == 0
    gatekeeper_passed = int(probes.get("gatekeeper", {}).get("returnCode", 1) or 0) == 0

    transport_passed = (
        True
        if browser_fallback_selected
        else direct_passed if direct_pyobjc else helper_transport_passed
    )
    addon_version = _addon_version(root)
    return {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat(),
        "addonVersion": addon_version,
        "platform": {
            "system": platform.system(),
            "macOS": platform.mac_ver()[0] or "unknown",
            "machine": platform.machine() or "unknown",
            "runtime": _anki_runtime(),
        },
        "selection": {
            "mode": "automatic capability detection",
            "nativeOutputActive": bool(diagnostics.get("nativeOutputActive")),
            "backend": str(diagnostics.get("backend") or "unknown"),
        },
        "controllerFreeIntegrationPassed": transport_passed,
        "distributionChecksPassed": bool(
            browser_fallback_selected or direct_passed or (signing_passed and gatekeeper_passed)
        ),
        "physicalHapticsConfirmed": bool(diagnostics.get("hardwareValidated")),
        "diagnostics": dict(diagnostics),
        "probes": probes,
    }


def render_mac_haptics_report(payload: Mapping[str, Any]) -> Tuple[str, str]:
    diagnostics = payload.get("diagnostics", {})
    if not isinstance(diagnostics, Mapping):
        diagnostics = {}
    platform_info = payload.get("platform", {})
    if not isinstance(platform_info, Mapping):
        platform_info = {}
    probes = payload.get("probes", {})
    if not isinstance(probes, Mapping):
        probes = {}

    transport_passed = bool(payload.get("controllerFreeIntegrationPassed"))
    browser_fallback_selected = bool(diagnostics.get("browserFallbackSelected"))
    controller_count = int(diagnostics.get("controllerCount", 0) or 0)
    haptic_count = int(diagnostics.get("hapticControllerCount", 0) or 0)
    if browser_fallback_selected:
        summary = (
            "Stable embedded-browser haptics fallback is active. "
            "No native dependency installation is attempted."
        )
    elif transport_passed:
        summary = "Controller-free native integration passed."
        if haptic_count:
            summary += f" Apple reports {haptic_count} haptics-capable controller(s)."
        elif controller_count:
            summary += " A controller is visible, but Apple did not expose haptics for it."
        else:
            summary += " No controller was detected, which is valid for this test."
    else:
        summary = "Controller-free native integration did not complete. Open the report for the failing stage."

    if browser_fallback_selected:
        stages = [
            _stage("Startup safety", True, "automatic dependency installation is disabled"),
            _stage("Haptics route", True, "embedded-browser gamepad fallback selected"),
        ]
    elif diagnostics.get("directPyObjC"):
        install_state = str(diagnostics.get("dependencyInstallState") or "unknown")
        stages = [
            _stage("User-writable dependency area", bool(diagnostics.get("dependencyTargetExists")), "ready" if diagnostics.get("dependencyTargetExists") else "will be created automatically"),
            _stage("PyObjC dependencies", install_state in {"ready", "installed-awaiting-load"}, install_state),
            _stage("Apple frameworks loaded", bool(diagnostics.get("pyobjcFrameworksLoaded")), "GameController and CoreHaptics imported" if diagnostics.get("pyobjcFrameworksLoaded") else "framework bindings are unavailable"),
            _stage("Controller monitoring", bool(diagnostics.get("notificationsRegistered")), "connect/disconnect monitoring is active" if diagnostics.get("notificationsRegistered") else "monitoring is not active"),
        ]
    else:
        stages = [
            _stage("Helper bundle packaged", bool(diagnostics.get("helperBundleExists")), "app bundle found" if diagnostics.get("helperBundleExists") else "app bundle is absent"),
            _stage("Helper executable packaged", bool(diagnostics.get("helperExists")), "executable found" if diagnostics.get("helperExists") else "build the helper on macOS first"),
            _stage("Launch attempted", bool(diagnostics.get("launchAttempted")), "Anki attempted automatic startup" if diagnostics.get("launchAttempted") else "startup was skipped because no executable was found"),
            _stage("Helper running", bool(diagnostics.get("helperRunning")), "process is alive" if diagnostics.get("helperRunning") else "process is not running"),
            _stage("Protocol handshake", bool(diagnostics.get("protocolReady")), "protocol versions match" if diagnostics.get("protocolReady") else "ready event was not accepted"),
            _stage("GameController status", bool(diagnostics.get("statusReceived")), "status response received" if diagnostics.get("statusReceived") else "no status response received"),
        ]

    runtime = platform_info.get("runtime", {})
    if not isinstance(runtime, Mapping):
        runtime = {}
    lines = [
        "Speed Streak macOS Haptics Diagnostic Report",
        "==============================================",
        f"Generated: {payload.get('generatedAtUtc', 'unknown')}",
        f"Speed Streak: {payload.get('addonVersion', 'unknown')}",
        f"macOS: {platform_info.get('macOS', 'unknown')}",
        f"Architecture: {platform_info.get('machine', 'unknown')}",
        f"Anki: {runtime.get('anki', 'unknown')}",
        f"Qt: {runtime.get('qt', 'unknown')}",
        f"Python: {runtime.get('python', 'unknown')}",
        "Backend selection: automatic; there is no user-facing Mac/Steam/XInput selector.",
        "",
        "Native backend",
        "--------------",
        *stages,
        f"[INFO] Connected controllers: {controller_count}",
        f"[INFO] Haptics-capable controllers: {haptic_count}",
        f"[INFO] Physical vibration confirmed: {'yes' if payload.get('physicalHapticsConfirmed') else 'no'}",
    ]

    last_error = str(diagnostics.get("lastError") or "")
    if last_error:
        lines.append(f"[INFO] Last backend error: {_redact(last_error)}")

    lines.extend(["", "Build and distribution probes", "-----------------------------"])
    if probes:
        for key, label in (
            ("xcodePath", "Xcode Command Line Tools"),
            ("swiftCompiler", "Swift compiler"),
            ("architectures", "Packaged architectures"),
            ("codeSignature", "Code-signature verification"),
            ("signatureDetails", "Code-signature details"),
            ("gatekeeper", "Gatekeeper assessment"),
            ("quarantine", "Quarantine attribute (absence is normal for a local build)"),
        ):
            result = probes.get(key)
            if isinstance(result, Mapping):
                lines.append(_probe_line(label, result))
    else:
        lines.append("[INFO] Native macOS command probes were not run on this platform.")

    sanitized_diagnostics = json.loads(json.dumps(diagnostics, default=str))
    for key in ("helperBundlePath", "helperPath"):
        if key in sanitized_diagnostics:
            sanitized_diagnostics[key] = _redact(sanitized_diagnostics[key])
    lines.extend(
        [
            "",
            "Structured backend snapshot",
            "---------------------------",
            json.dumps(sanitized_diagnostics, indent=2, sort_keys=True),
            "",
            "Interpretation",
            "--------------",
            (
                "A browser-fallback PASS confirms that Speed Streak avoided native dependency setup and selected its stable embedded-browser haptics path."
                if browser_fallback_selected
                else "A controller-free PASS validates dependency loading, Apple-framework initialization, controller monitoring, and safe no-controller fallback."
            ),
            "It cannot prove that a physical controller vibrates or that left/right motor mapping feels correct.",
            (
                "No native helper or Python dependency is required for the selected browser fallback."
                if browser_fallback_selected
                else "The direct PyObjC backend does not require a separately signed helper; Gatekeeper results apply only to the retained Swift fallback."
            ),
            "No administrator privileges are required to run this diagnostic.",
        ]
    )
    return summary, "\n".join(lines)


def build_mac_haptics_report(
    addon_root: Path,
    diagnostics: Mapping[str, Any],
) -> Tuple[str, str]:
    return render_mac_haptics_report(collect_mac_haptics_report(addon_root, diagnostics))
