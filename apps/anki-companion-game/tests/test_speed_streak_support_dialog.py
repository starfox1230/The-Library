from pathlib import Path


ADDON_ROOT = Path(__file__).resolve().parents[1] / "speed-streak-addon-v2.04"


def test_help_feedback_menu_item_is_below_settings_and_opens_hub() -> None:
    reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
    settings_index = reviewer.index('action = menu.addAction("Settings")')
    help_index = reviewer.index('help_feedback_action = menu.addAction("Help / Feedback")')
    assert help_index > settings_index
    assert 'help_feedback_action.triggered.connect(self._show_help_feedback_from_menu)' in reviewer
    assert 'from .support_dialog import show_help_feedback_dialog' in reviewer


def test_help_feedback_hub_has_review_feedback_and_optional_support_routes() -> None:
    dialog = (ADDON_ROOT / "support_dialog.py").read_text(encoding="utf-8")
    assert 'ANKIWEB_REVIEW_URL = "https://ankiweb.net/shared/info/1237336370"' in dialog
    assert "REDDIT_FEEDBACK_URL" in dialog
    assert "to=henbitdeadnettle92" in dialog
    assert 'KOFI_URL = "https://ko-fi.com/ankispeedstreak"' in dialog
    assert "QDesktopServices.openUrl(QUrl(ANKIWEB_REVIEW_URL))" in dialog
    assert "QDesktopServices.openUrl(QUrl(REDDIT_FEEDBACK_URL))" in dialog
    assert "QDesktopServices.openUrl(QUrl(KOFI_URL))" in dialog
    assert 'button_text="Review on AnkiWeb"' in dialog
    assert 'button_text="Message on Reddit"' in dialog
    assert 'button_text="Open Ko-fi"' in dialog
    assert "optional support is available on Ko-fi" in dialog
    assert 'icon="brand:reddit-logo.png"' in dialog
    assert 'icon="brand:kofi-logo.png"' in dialog
    assert (ADDON_ROOT / "support_assets" / "reddit-logo.png").is_file()
    assert (ADDON_ROOT / "support_assets" / "kofi-logo.png").is_file()
    assert "CoffeeMark" not in dialog
    assert "coffee" not in dialog.lower()
