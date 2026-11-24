from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path
from types import ModuleType, SimpleNamespace


ADDON_ROOT = Path(__file__).resolve().parents[1]


def _load_stats_dialog() -> ModuleType:
    package_name = "speed_streak_v2_04_stats_records_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package

    class Dummy:
        pass

    aqt_module = ModuleType("aqt")
    aqt_module.mw = None
    qt_module = ModuleType("aqt.qt")
    for name in (
        "QDialog",
        "QFrame",
        "QHBoxLayout",
        "QPushButton",
        "QSizePolicy",
        "QVBoxLayout",
    ):
        setattr(qt_module, name, Dummy)
    qt_module.Qt = SimpleNamespace()
    webview_module = ModuleType("aqt.webview")
    webview_module.AnkiWebView = Dummy
    sys.modules["aqt"] = aqt_module
    sys.modules["aqt.qt"] = qt_module
    sys.modules["aqt.webview"] = webview_module

    game_state_module = ModuleType(f"{package_name}.game_state")
    game_state_module.CompanionGameEngine = Dummy
    stats_store_module = ModuleType(f"{package_name}.stats_store")
    stats_store_module.StatsStore = Dummy
    sys.modules[game_state_module.__name__] = game_state_module
    sys.modules[stats_store_module.__name__] = stats_store_module

    qualified = f"{package_name}.stats_dialog"
    spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / "stats_dialog.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    return module


class StatsRecordViewTests(unittest.TestCase):
    def test_record_view_contains_rank_and_comparison_fields(self) -> None:
        module = _load_stats_dialog()
        record = {
            "id": 7,
            "allTimeRank": 2,
            "endedAt": "2026-08-30T12:00:00",
            "endReason": "timeout",
            "streak": 18,
            "runSpanMs": 90_000,
            "activeMs": 55_000,
            "pausedMs": 10_000,
            "pauseCount": 1,
            "reviewExitMs": 20_000,
            "reviewExitCount": 1,
            "resumedAfterRestart": False,
            "usedUndo": False,
            "boostsUsed": 2,
            "cardsAnswered": 18,
        }
        html = module.StatsDialog._html(
            None,
            {
                "generatedAt": "2026-08-30T12:00:00",
                "currentRoundPauseMs": 0,
                "pauseActive": False,
                "today": {},
                "overall": {},
                "history": [],
                "records": [record],
                "selectedRunId": 7,
                "selectedRecord": record,
            },
        )

        self.assertIn("All-Time Records", html)
        self.assertIn("First → last streak number", html)
        self.assertIn("Total time (in-game)", html)
        self.assertIn("A Pure run has no manual pauses", html)
        script_match = re.search(r"<script>([\s\S]*?)</script>", html)
        self.assertIsNotNone(script_match)
        result = subprocess.run(
            ["node", "--check", "-"],
            input=script_match.group(1),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
