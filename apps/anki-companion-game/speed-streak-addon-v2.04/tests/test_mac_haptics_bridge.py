from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import patch


ADDON_ROOT = Path(__file__).resolve().parents[1]


class _Stream:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self._iter_lines: list[str] = []

    def write(self, text: str) -> None:
        self.lines.append(text)

    def flush(self) -> None:
        return

    def __iter__(self):
        return iter(self._iter_lines)


class _FakeProcess:
    def __init__(self, stdout_lines: list[str] | None = None) -> None:
        self.stdin = _Stream()
        self.stdout = _Stream()
        self.stderr = _Stream()
        self.stdout._iter_lines = list(stdout_lines or [])
        self._returncode: int | None = None

    def poll(self) -> int | None:
        return self._returncode

    def wait(self, timeout: float | None = None) -> int:
        self._returncode = 0
        return 0

    def terminate(self) -> None:
        self._returncode = -15


def _load_bridge_module() -> ModuleType:
    package_name = "speed_streak_v2_03_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for module_name in ("feedback_catalog", "mac_haptics_bridge"):
        qualified = f"{package_name}.{module_name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{module_name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.mac_haptics_bridge"]


class MacHapticsBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = _load_bridge_module()
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _stage_helper(self, *, validated: bool = False) -> None:
        helper = (
            self.root
            / "mac_haptics"
            / "SpeedStreakHaptics.app"
            / "Contents"
            / "MacOS"
            / "SpeedStreakHaptics"
        )
        helper.parent.mkdir(parents=True)
        helper.write_bytes(b"poc")
        if validated:
            (self.root / "mac_haptics" / "POC_VALIDATED.json").write_text(
                json.dumps({"validated": True, "protocolVersion": 1}),
                encoding="utf-8",
            )

    def test_bridge_is_inert_outside_macos(self) -> None:
        with patch.object(self.module.sys, "platform", "win32"):
            bridge = self.module.MacHapticsBridge(self.root)
        self.assertFalse(bridge.available)
        self.assertEqual(bridge.backend_name, "not-macos")

    def test_controller_free_helper_launches_without_physical_marker(self) -> None:
        self._stage_helper()
        process = _FakeProcess()
        with patch.object(self.module.sys, "platform", "darwin"):
            bridge = self.module.MacHapticsBridge(
                self.root,
                process_factory=lambda *args, **kwargs: process,
            )
            time.sleep(0.05)
            bridge._handle_message(
                {
                    "event": "ready",
                    "protocolVersion": 1,
                    "frameworksInitialized": ["GameController", "CoreHaptics"],
                }
            )
            bridge._handle_message(
                {
                    "event": "status",
                    "controllerCount": 0,
                    "hapticControllerCount": 0,
                    "controllers": [],
                }
            )

        self.assertTrue(bridge.transport_ready)
        self.assertFalse(bridge.available)
        with patch.object(self.module.sys, "platform", "darwin"):
            self.assertEqual(bridge.backend_name, "browser-fallback-native-monitoring")
        self.assertFalse(bridge.diagnostics["hardwareValidated"])
        self.assertTrue(bridge.diagnostics["statusReceived"])

    def test_validated_helper_routes_sanitized_pattern(self) -> None:
        self._stage_helper(validated=True)
        process = _FakeProcess()
        with patch.object(self.module.sys, "platform", "darwin"):
            bridge = self.module.MacHapticsBridge(
                self.root,
                process_factory=lambda *args, **kwargs: process,
            )
            time.sleep(0.05)
            bridge._handle_message({"event": "ready", "protocolVersion": 1})
            bridge._handle_message(
                {
                    "event": "status",
                    "controllerCount": 1,
                    "hapticControllerCount": 1,
                    "controllers": [],
                }
            )

        self.assertTrue(bridge.available)
        self.assertTrue(bridge.play_sequence([{"duration": 120, "weak": -4, "strong": 8}]))
        command = json.loads(process.stdin.lines[-1])
        self.assertEqual(command["command"], "play")
        self.assertEqual(
            command["steps"],
            [{"duration": 120.0, "weak": 0.0, "strong": 1.0}],
        )

    def test_protocol_mismatch_never_claims_native_output(self) -> None:
        self._stage_helper(validated=True)
        process = _FakeProcess()
        with patch.object(self.module.sys, "platform", "darwin"):
            bridge = self.module.MacHapticsBridge(
                self.root,
                process_factory=lambda *args, **kwargs: process,
            )
            time.sleep(0.05)
            bridge._handle_message({"event": "ready", "protocolVersion": 99})

        self.assertFalse(bridge.available)
        self.assertIn("protocol mismatch", bridge.diagnostics["lastError"].lower())

    def test_missing_helper_falls_back_without_launch_attempt(self) -> None:
        with patch.object(self.module.sys, "platform", "darwin"):
            bridge = self.module.MacHapticsBridge(self.root)
        diagnostics = bridge.diagnostics
        self.assertFalse(diagnostics["helperExists"])
        self.assertFalse(diagnostics["launchAttempted"])
        with patch.object(self.module.sys, "platform", "darwin"):
            self.assertEqual(bridge.backend_name, "browser-fallback-native-unavailable")


if __name__ == "__main__":
    unittest.main()
