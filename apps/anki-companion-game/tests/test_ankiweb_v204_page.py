from __future__ import annotations

import re
import unittest
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PAGE_ROOT = ROOT / "ankiweb-v2.04"


class AnkiWebV204PageTests(unittest.TestCase):
    def test_all_hosted_images_have_matching_local_assets(self) -> None:
        description = (PAGE_ROOT / "ankiweb-description.html").read_text(encoding="utf-8")
        sources = re.findall(r'<img[^>]+src="([^"]+)"', description)
        self.assertEqual(len(sources), 8)
        for source in sources:
            self.assertIn("henbitdeathmetal/anki-speed-streak", source)
            self.assertIn("/ankiweb/v2.04/assets/", source)
            asset = PAGE_ROOT / "assets" / source.rsplit("/", 1)[-1]
            self.assertTrue(asset.is_file(), asset.name)
            with Image.open(asset) as image:
                self.assertGreater(image.width, 0)
                self.assertGreater(image.height, 0)

    def test_public_links_and_current_release_language_are_present(self) -> None:
        description = (PAGE_ROOT / "ankiweb-description.html").read_text(encoding="utf-8")
        self.assertIn("henbitdeadnettle92", description)
        self.assertIn("https://ko-fi.com/ankispeedstreak", description)
        self.assertIn("https://github.com/henbitdeathmetal/anki-speed-streak", description)
        self.assertIn("New in 2.04", description)
        self.assertIn("Streak records", description)
        self.assertIn("Time’s Running Out", description)
        self.assertNotIn("Historical stats tracking is a work in progress", description)

    def test_markup_uses_only_ankiweb_preserved_layout_elements(self) -> None:
        description = (PAGE_ROOT / "ankiweb-description.html").read_text(encoding="utf-8")
        self.assertNotRegex(description, r"<\/?(?:table|tr|td|small|span|div)\b")
        self.assertNotIn("style=", description)
        self.assertIn('width="48%"', description)
        self.assertIn('width="32%"', description)


if __name__ == "__main__":
    unittest.main()
