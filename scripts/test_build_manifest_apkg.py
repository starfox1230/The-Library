from __future__ import annotations

import unittest

from scripts import build_manifest_apkg as builder


class CanonicalVisualModelTests(unittest.TestCase):
    def test_visual_style_uses_the_canonical_sacloze_model(self) -> None:
        model = builder.model_for_style("saCloze++")

        self.assertEqual(model.name, "saCloze++")
        self.assertEqual(model.model_id, 1761198205290)
        self.assertEqual([field["name"] for field in model.fields], ["Text", "Extra"])
        self.assertEqual(model.templates[0]["name"], "Card 1")
        self.assertIn("{{edit:tts", model.templates[0]["qfmt"])
        self.assertIn("{{edit:tts", model.templates[0]["afmt"])
        self.assertIn("data-seconds=\"12\"", model.templates[0]["qfmt"])
        self.assertIn(".iphone .tbar", model.css)


if __name__ == "__main__":
    unittest.main()
