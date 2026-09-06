from __future__ import annotations

import unittest
from pathlib import Path

from PIL import Image


ADDON_ROOT = Path(__file__).resolve().parents[1]


class WhatsNewReleaseTests(unittest.TestCase):
    def test_v204_release_is_new_and_v20_is_relabelled_as_prior_update(self) -> None:
        dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        self.assertIn('WHATS_NEW_VERSION = "2.04"', dialog)
        self.assertIn('WHATS_NEW_VERSION = "2.04"', reviewer)
        self.assertIn('_label("WHAT’S NEW"', dialog)
        self.assertIn('_label("PRIOR UPDATE"', dialog)
        self.assertLess(dialog.index('_label("WHAT’S NEW"'), dialog.index('_label("PRIOR UPDATE"'))

    def test_release_focuses_on_records_countdown_audio_and_mac_testers(self) -> None:
        dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
        self.assertIn('"Streak records"', dialog)
        self.assertIn('"Best only"', dialog)
        self.assertIn('"Streak strip"', dialog)
        self.assertIn('"Five streaks"', dialog)
        self.assertIn('"“Time’s Running Out” sound"', dialog)
        self.assertIn('"Improved sound timing"', dialog)
        self.assertIn("macOS controller vibration testers wanted", dialog)
        self.assertIn("u/henbitdeadnettle92", dialog)
        self.assertIn('REDDIT_URL = "https://www.reddit.com/user/henbitdeadnettle92/"', dialog)

    def test_release_uses_real_ui_assets_without_double_scaling(self) -> None:
        dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
        expected = {
            "streak-records-display.jpg": (736, 900),
            "countdown-cue-settings.jpg": (782, 786),
        }
        for filename, size in expected.items():
            path = ADDON_ROOT / "whats_new_assets" / filename
            self.assertTrue(path.is_file(), filename)
            with Image.open(path) as image:
                self.assertEqual(image.size, size)
            self.assertIn(f'"{filename}"', dialog)
        paint_event = dialog.split("def paintEvent", 1)[1].split("def _instruction", 1)[0]
        self.assertNotIn("self._pixmap.scaled", paint_event)
        self.assertIn("painter.drawPixmap(target, self._pixmap, source)", paint_event)

    def test_records_capture_carries_the_full_visual_streak(self) -> None:
        harness = (ADDON_ROOT / "tests" / "scoreboard_harness.html").read_text(encoding="utf-8")
        self.assertIn("{ length: celebrateRecord ? 168 : 86 }", harness)
        self.assertNotIn('satelliteColors: ["green", "blue", "yellow", "green"]', harness)

    def test_release_links_open_the_exact_settings_sections_and_support_pages(self) -> None:
        dialog = (ADDON_ROOT / "whats_new_dialog.py").read_text(encoding="utf-8")
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        settings = (ADDON_ROOT / "settings_dialog.py").read_text(encoding="utf-8")
        self.assertIn('SupportIconButton("thumb_up", "Review Speed Streak on AnkiWeb", body)', dialog)
        self.assertIn('SupportIconButton("reddit-logo.png", "Send feedback on Reddit", body)', dialog)
        self.assertIn('SupportIconButton("kofi-logo.png", "Support development on Ko-fi", body)', dialog)
        self.assertIn("QDesktopServices.openUrl(QUrl(ANKIWEB_REVIEW_URL))", dialog)
        self.assertIn("QDesktopServices.openUrl(QUrl(REDDIT_FEEDBACK_URL))", dialog)
        self.assertIn("QDesktopServices.openUrl(QUrl(KOFI_URL))", dialog)
        self.assertIn('self.destination = "records"', dialog)
        self.assertIn('self.destination = "countdown_audio"', dialog)
        self.assertIn('destination == "records"', reviewer)
        self.assertIn('destination == "countdown_audio"', reviewer)
        self.assertIn("def focus_countdown_audio_settings", settings)
        self.assertIn('_select_settings_page("feedback")', settings)

    def test_whats_new_prompt_is_keyed_to_content_version_not_addon_folder_version(self) -> None:
        reviewer = (ADDON_ROOT / "reviewer_overlay.py").read_text(encoding="utf-8")
        installer = (ADDON_ROOT / "install_to_anki.ps1").read_text(encoding="utf-8")
        self.assertIn('WHATS_NEW_VERSION = "2.04"', reviewer)
        self.assertIn("if self._whats_new_seen_version == WHATS_NEW_VERSION", reviewer)
        self.assertIn("self._whats_new_seen_version = WHATS_NEW_VERSION", reviewer)
        self.assertIn('$preserveFiles = @("meta.json")', installer)


if __name__ == "__main__":
    unittest.main()
