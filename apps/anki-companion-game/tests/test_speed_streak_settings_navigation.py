from __future__ import annotations

import ast
import json
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v1.35"
SETTINGS_PATH = ADDON_ROOT / "settings_dialog.py"


def settings_source() -> str:
    return SETTINGS_PATH.read_text(encoding="utf-8")


def test_v1_35_is_a_separate_upgrade_from_v1_34() -> None:
    manifest = json.loads((ADDON_ROOT / "manifest.json").read_text(encoding="utf-8"))
    readme = (ADDON_ROOT / "README.md").read_text(encoding="utf-8")
    frozen_v134 = ADDON_ROOT.parent / "speed-streak-addon-v1.34"

    assert manifest["name"] == "Speed Streak v1.35"
    assert manifest["package"] == "speed_streak_v1_35"
    assert "v1.35 (from v1.34)" in readme
    assert json.loads((frozen_v134 / "manifest.json").read_text(encoding="utf-8"))["package"] == "speed_streak_v1_34"
    assert "SETTINGS_PAGES" not in (frozen_v134 / "settings_dialog.py").read_text(encoding="utf-8")


def test_settings_have_six_focused_pages_and_one_visible_stack() -> None:
    source = settings_source()

    assert "QStackedWidget" in source
    for key, title in (
        ("gameplay", "Gameplay"),
        ("timers", "Timers"),
        ("visuals", "Visuals"),
        ("feedback", "Audio/Haptics"),
        ("shortcuts", "Shortcuts"),
        ("tools", "Tools"),
    ):
        assert f'("{key}", "{title}"' in source
    assert "self.settings_stack.setCurrentIndex(self.settings_page_indices[normalized])" in source
    assert 'self._select_settings_page("gameplay")' in source


def test_contextual_entry_points_select_the_correct_page_before_focus() -> None:
    source = settings_source()
    tree = ast.parse(source)
    methods = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }

    assert 'self._select_settings_page("shortcuts")' in methods["focus_shortcut_setting"]
    assert 'self._select_settings_page("gameplay")' in methods["focus_time_boost_settings"]
    assert "self.settings_scroll.ensureWidgetVisible(field, 32, 80)" in methods["focus_shortcut_setting"]
    assert "self.settings_scroll.ensureWidgetVisible(field, 32, 80)" in methods["focus_time_boost_settings"]


def test_fast_open_contract_is_preserved() -> None:
    source = settings_source()
    tree = ast.parse(source)
    settings_class = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SettingsDialog"
    )
    initializer = next(
        node for node in settings_class.body if isinstance(node, ast.FunctionDef) and node.name == "__init__"
    )
    called_methods = {
        call.func.attr
        for call in ast.walk(initializer)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    }

    # These editors create large numbers of controls and must remain behind
    # _build_lazy_settings_panel rather than running during dialog creation.
    for forbidden_eager_call in (
        "_build_absolute_special_timers",
        "_build_audio_event_editor",
        "_build_haptic_event_editor",
        "open_stats",
    ):
        assert forbidden_eager_call not in called_methods

    assert "self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)" in source
    assert "if _dialog is not None:" in source
    assert "_dialog.sync_from_state()" in source
    assert source.count("self._build_lazy_settings_panel(") >= 6


def test_settings_pages_keep_heavy_panels_lazy_and_live_controls_intact() -> None:
    source = settings_source()

    assert '"Special Timers",\n                self._build_absolute_special_timers' in source
    assert "self._build_gameplay_section(gameplay_body)" in source
    assert "self._build_timers_section(timers_body)" in source
    assert "self._build_feedback_section(feedback_body)" in source
    assert "self._build_shortcuts_section(shortcuts_body)" in source
    assert "valueChanged.connect(self.persist_settings)" in source
    assert "toggled.connect(self.persist_settings)" in source


def test_v1_35_keeps_every_v1_34_settings_field() -> None:
    def assigned_self_attributes(path: Path) -> set[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names: set[str] = set()
        for node in ast.walk(tree):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
            for target in targets:
                if (
                    isinstance(target, ast.Attribute)
                    and isinstance(target.value, ast.Name)
                    and target.value.id == "self"
                ):
                    names.add(target.attr)
        return names

    v134_settings = ADDON_ROOT.parent / "speed-streak-addon-v1.34" / "settings_dialog.py"
    assert assigned_self_attributes(v134_settings) <= assigned_self_attributes(SETTINGS_PATH)


def test_developer_preferences_shortcut_is_window_wide_and_reveals_its_page() -> None:
    source = settings_source()
    tree = ast.parse(source)
    methods = {
        node.name: ast.get_source_segment(source, node) or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
    }

    assert 'QKeySequence("Ctrl+Shift+W")' in source
    assert "Qt.ShortcutContext.WindowShortcut" in source
    assert "developer_toggle_shortcut.setAutoRepeat(False)" in source
    assert "developer_toggle_shortcut.activatedAmbiguously.connect" in source
    assert 'self._select_settings_page("gameplay")' in methods["_toggle_developer_preferences"]
    assert "self.settings_scroll.ensureWidgetVisible(self.developer_testing_section, 32, 24)" in methods["_toggle_developer_preferences"]
