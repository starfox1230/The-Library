from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v2.01"


def load_shortcuts_module():
    spec = importlib.util.spec_from_file_location("speed_streak_v201_shortcuts", ADDON_ROOT / "shortcuts.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v201_package_identity_replaces_v20() -> None:
    manifest = json.loads((ADDON_ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["package"] == "speed_streak_v2_01"
    assert "speed_streak_v2_0" in manifest["conflicts"]
    assert 'speed_streak_v2_01.ankiaddon' in (ADDON_ROOT / "build_ankiaddon.ps1").read_text(encoding="utf-8")
    assert 'speed_streak_v2_01' in (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")


def test_v201_does_not_repeat_the_v20_whats_new_dialog() -> None:
    controller = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
    assert 'WHATS_NEW_VERSION = "2.0"' in controller
    assert 'WHATS_NEW_VERSION = "2.0"' in dialog


def test_every_selectable_vanilla_review_shortcut_reports_its_action() -> None:
    shortcuts = load_shortcuts_module()
    expected = {
        "1": "Answer Again",
        "2": "Answer Hard or Good, depending on the available answer buttons",
        "3": "Answer Good or Easy, depending on the available answer buttons",
        "4": "Answer Easy",
        "5": "Pause or resume audio",
        "6": "Seek audio backward",
        "7": "Seek audio forward",
        "E": "Edit the current card",
        "I": "Show Card Info",
        "M": "Open the More menu",
        "O": "Open Deck Options",
        "R": "Replay Audio",
        "U": "Undo",
        "V": "Replay Recorded Voice",
        "*": "Mark or unmark the current note",
        "=": "Bury the current note",
        "-": "Bury the current card",
        "!": "Suspend the current note",
        "@": "Suspend the current card",
    }
    for key, action in expected.items():
        assert shortcuts.anki_review_shortcut_action(key) == action


def test_safe_keys_and_profile_answer_key_overrides() -> None:
    shortcuts = load_shortcuts_module()
    assert shortcuts.anki_review_shortcut_action("C") == ""
    assert shortcuts.anki_review_shortcut_action("P") == ""
    assert shortcuts.anki_review_shortcut_action("J", {"j": "Answer Good"}) == "Answer Good"


def test_settings_reject_conflict_and_explains_anki_action() -> None:
    source = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
    assert "Shortcut Already Used by Anki" in source
    assert "is already used by Anki during review for {conflict_action}" in source
    assert "field.setText(previous)" in source
    assert "self._anki_answer_key_actions()" in source


def test_horizontal_timer_uses_continuous_webgl_color_and_soft_endpoint() -> None:
    source = (ADDON_ROOT / "web" / "card_timer.js").read_text(encoding="utf-8")
    assert "float edgeWidth = max(0.75 / u_resolution.x, 0.0005);" in source
    assert "1.0 - smoothstep(progress - edgeWidth, progress + edgeWidth, uv.x)" in source
    assert "vec3 rampColor" in source
    assert "gl.uniform1f(renderer.useRampLocation, timer.rampColors ? 1 : 0);" in source
    assert "timerRamp," in source
