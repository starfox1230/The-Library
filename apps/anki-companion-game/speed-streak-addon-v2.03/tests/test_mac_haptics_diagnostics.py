from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "speed_streak_mac_haptics_diagnostics_test",
        ADDON_ROOT / "mac_haptics_diagnostics.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacHapticsDiagnosticsTests(unittest.TestCase):
    def test_controller_free_pass_is_not_physical_confirmation(self) -> None:
        module = _load_module()
        payload = {
            "generatedAtUtc": "2026-08-29T00:00:00+00:00",
            "addonVersion": "2.03",
            "platform": {
                "macOS": "15.6",
                "machine": "arm64",
                "runtime": {"anki": "26.08", "qt": "6.11", "python": "3.13"},
            },
            "controllerFreeIntegrationPassed": True,
            "distributionChecksPassed": False,
            "physicalHapticsConfirmed": False,
            "diagnostics": {
                "helperBundleExists": True,
                "helperExists": True,
                "launchAttempted": True,
                "helperRunning": True,
                "protocolReady": True,
                "statusReceived": True,
                "controllerCount": 0,
                "hapticControllerCount": 0,
                "backend": "browser-fallback-native-monitoring",
            },
            "probes": {},
        }

        summary, report = module.render_mac_haptics_report(payload)
        self.assertIn("passed", summary.lower())
        self.assertIn("No controller was detected", summary)
        self.assertIn("Physical vibration confirmed: no", report)
        self.assertIn("cannot prove", report)

    def test_report_redacts_home_directory(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as temporary:
            diagnostics = {
                "helperBundlePath": str(Path.home() / "secret" / "SpeedStreakHaptics.app"),
                "helperPath": str(Path.home() / "secret" / "SpeedStreakHaptics"),
                "helperBundleExists": False,
                "helperExists": False,
                "launchAttempted": False,
                "helperRunning": False,
                "protocolReady": False,
                "statusReceived": False,
            }
            payload = module.collect_mac_haptics_report(Path(temporary), diagnostics)
            _, report = module.render_mac_haptics_report(payload)
        self.assertNotIn(str(Path.home()), report)
        self.assertIn("<HOME>", report)

    def test_browser_fallback_is_healthy_and_manifest_reports_v203(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "1237336370"
            root.mkdir()
            (root / "manifest.json").write_text(
                json.dumps({"package": "speed_streak_v2_03"}),
                encoding="utf-8",
            )
            payload = module.collect_mac_haptics_report(
                root,
                {
                    "backend": "browser-fallback",
                    "browserFallbackSelected": True,
                    "directPyObjC": False,
                    "controllerCount": 0,
                    "hapticControllerCount": 0,
                },
            )
        summary, report = module.render_mac_haptics_report(payload)
        self.assertEqual(payload["addonVersion"], "2.03")
        self.assertIn("browser haptics fallback is active", summary.lower())
        self.assertIn("[PASS] Startup safety", report)
        self.assertNotIn("[FAIL]", report)

    def test_startup_timers_do_not_use_progress_manager(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        self.assertNotIn("mw.progress.timer(100, self._on_tick", reviewer)
        self.assertNotIn("mw.progress.timer(1, self._prompt_for_display_mode", reviewer)
        self.assertIn("self._timer = QTimer(mw)", reviewer)
        self.assertIn("QTimer.singleShot(1, self._prompt_for_display_mode)", reviewer)

    def test_settings_preview_keeps_browser_haptics_fallback(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        overlay = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        self.assertIn("if self.haptics.preview_pattern(pattern_key):", reviewer)
        self.assertIn("window.SpeedStreak.previewHaptics", reviewer)
        self.assertIn("previewHaptics(sequence)", overlay)
        self.assertIn("playBrowserHaptics(sequence)", overlay)


if __name__ == "__main__":
    unittest.main()
