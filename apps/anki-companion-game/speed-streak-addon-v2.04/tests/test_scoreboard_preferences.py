from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path
from types import ModuleType


ADDON_ROOT = Path(__file__).resolve().parents[1]


def _load_modules() -> tuple[ModuleType, ModuleType]:
    package_name = "speed_streak_v2_04_scoreboard_preferences_test"
    package = ModuleType(package_name)
    package.__path__ = [str(ADDON_ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    loaded: dict[str, ModuleType] = {}
    for name in ("stats_store", "run_history", "scoreboard_colors"):
        qualified = f"{package_name}.{name}"
        spec = importlib.util.spec_from_file_location(qualified, ADDON_ROOT / f"{name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
        loaded[name] = module
    return loaded["run_history"], loaded["scoreboard_colors"]


RUN_HISTORY, SCOREBOARD_COLORS = _load_modules()


class ScoreboardPreferenceTests(unittest.TestCase):
    def test_best_only_is_the_default_layout(self) -> None:
        self.assertEqual(
            RUN_HISTORY.normalize_scoreboard_layout(None),
            RUN_HISTORY.SCOREBOARD_LAYOUT_BEST_ONLY,
        )
        self.assertEqual(
            RUN_HISTORY.normalize_scoreboard_layout("not-a-layout"),
            RUN_HISTORY.SCOREBOARD_LAYOUT_BEST_ONLY,
        )
        defaults = json.loads((ADDON_ROOT / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(defaults["scoreboard_layout"], RUN_HISTORY.SCOREBOARD_LAYOUT_BEST_ONLY)
        self.assertEqual(defaults["scoreboard_list_mode"], RUN_HISTORY.SCOREBOARD_LIST_BEST)

    def test_record_colors_normalize_and_resolve_defaults(self) -> None:
        self.assertEqual(
            SCOREBOARD_COLORS.normalize_scoreboard_colors(
                {
                    "label": "ABC",
                    "value": "#123456",
                    "new_record": "f5aa41",
                    "ignored": "#ffffff",
                }
            ),
            {"label": "#aabbcc", "value": "#123456", "new_record": "#f5aa41"},
        )
        self.assertEqual(
            SCOREBOARD_COLORS.resolved_scoreboard_colors({"value": "#010203"}),
            {"label": "#8ea0cc", "value": "#010203", "new_record": "#f5aa41"},
        )

    def test_new_record_celebration_is_number_focused_and_colorful(self) -> None:
        script = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        self.assertIn('bestLabel.textContent = recordBreaking', script)
        self.assertIn('"NEW RECORD"', script)
        self.assertIn("burstScoreboardConfetti", script)
        self.assertIn('const palette = ["#ff6f96", "#ffd978", "#65f0c2"', script)
        self.assertIn("transform: scale(1.36)", stylesheet)
        self.assertIn("var(--acg-record-new)", stylesheet)

    def test_five_streak_markup_omits_completion_reason_line(self) -> None:
        script = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        row_template = script.split('class="acg-scoreboard-row"', 1)[1].split("</button>", 1)[0]
        self.assertNotIn("formatRunEndReason", row_template)
        self.assertNotIn("<small>", row_template)

    def test_record_panel_disables_internal_scrolling(self) -> None:
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        panel_rules = stylesheet.split(".speed-streak-sidebar .acg-scoreboard-panel {", 1)[1].split("}", 1)[0]
        self.assertIn("overflow-x: hidden", panel_rules)
        self.assertIn("overflow-y: hidden", panel_rules)
        self.assertIn("max-height: none", panel_rules)

    def test_pause_overlay_moves_below_every_five_streak_scoreboard(self) -> None:
        script = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        placement = script.split("function syncPauseOverlayPlacement", 1)[1].split("function ", 1)[0]
        self.assertIn('layout === "ladder"', placement)
        self.assertNotIn("listMode", placement)
        self.assertIn("pause-below-scoreboard", stylesheet)
        self.assertIn("z-index: 14", stylesheet)

    def test_record_surfaces_share_stats_or_settings_chooser(self) -> None:
        script = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        self.assertIn('class="acg-scoreboard-actions-title">Streak Records', script)
        self.assertIn('data-scoreboard-action="stats"', script)
        self.assertIn('data-scoreboard-action="settings"', script)
        self.assertIn("openScoreboardActions(row, runId)", script)
        self.assertIn("openScoreboardActions(scoreboardTarget)", script)
        self.assertIn("speed-streak:open-stats-run:", script)
        self.assertIn('"speed-streak:open-stats"', script)
        self.assertIn("speed-streak:open-settings:gameplay:run-scores", script)
        self.assertIn("<= 42", script)
        self.assertIn("}, 520)", script)
        self.assertIn(".acg-scoreboard-actions.open", stylesheet)

    def test_recent_five_is_valid_only_for_five_streaks_layout(self) -> None:
        self.assertEqual(
            RUN_HISTORY.scoreboard_list_mode_for_layout(
                RUN_HISTORY.SCOREBOARD_LAYOUT_LADDER,
                RUN_HISTORY.SCOREBOARD_LIST_RECENT,
            ),
            RUN_HISTORY.SCOREBOARD_LIST_RECENT,
        )
        for layout in (
            RUN_HISTORY.SCOREBOARD_LAYOUT_OFF,
            RUN_HISTORY.SCOREBOARD_LAYOUT_BEST_ONLY,
            RUN_HISTORY.SCOREBOARD_LAYOUT_COMPACT,
        ):
            self.assertEqual(
                RUN_HISTORY.scoreboard_list_mode_for_layout(
                    layout,
                    RUN_HISTORY.SCOREBOARD_LIST_RECENT,
                ),
                RUN_HISTORY.SCOREBOARD_LIST_BEST,
            )

    def test_settings_hides_recent_five_outside_five_streaks(self) -> None:
        settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        controller = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        self.assertIn(
            "self.scoreboard_list_row.setEnabled(layout_mode != SCOREBOARD_LAYOUT_OFF)",
            settings,
        )
        self.assertIn(
            "self.scoreboard_order_row.setEnabled(layout_mode == SCOREBOARD_LAYOUT_LADDER)",
            settings,
        )
        self.assertIn(
            "set_row_hidden(recent_index, not recent_available)",
            settings,
        )
        self.assertIn(
            "effective_scoreboard_list_mode = scoreboard_list_mode_for_layout(",
            controller,
        )

    def test_time_drain_hides_only_the_five_record_panel(self) -> None:
        script = (ADDON_ROOT / "web" / "overlay.js").read_text(encoding="utf-8")
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        self.assertIn('sidebar.classList.toggle("time-drain-active", activeTimeDrain)', script)
        self.assertIn("scoreboardPanel.hidden = activeTimeDrain", script)
        self.assertIn("syncTimeDrainOverlayLayout()", script)
        self.assertIn(".time-drain-active .acg-scoreboard-panel", stylesheet)
        self.assertNotIn(".time-drain-active .acg-scoreboard-target", stylesheet)

    def test_time_drain_surface_is_flush_with_the_panel(self) -> None:
        stylesheet = (ADDON_ROOT / "web" / "overlay.css").read_text(encoding="utf-8")
        time_drain_rules = stylesheet.split(
            ".speed-streak-sidebar .acg-time-drain {", 1
        )[1].split("}", 1)[0]
        self.assertIn("inset: 0", time_drain_rules)
        self.assertIn("border: 0", time_drain_rules)
        self.assertNotIn("inset: 26px", time_drain_rules)


if __name__ == "__main__":
    unittest.main()
