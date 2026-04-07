from __future__ import annotations

import unittest

from cursor_transcriber.helpers import format_duration, hotkey_to_label, parse_hotkey_list, preview_text


class HelpersTests(unittest.TestCase):
    def test_format_duration_rounds_to_nearest_second(self) -> None:
        self.assertEqual(format_duration(59.4), "00:59")
        self.assertEqual(format_duration(59.6), "01:00")

    def test_hotkey_to_label_formats_special_keys(self) -> None:
        self.assertEqual(hotkey_to_label("<shift>+<f3>"), "Shift + F3")
        self.assertEqual(hotkey_to_label("<ctrl>+v"), "Ctrl + V")

    def test_parse_hotkey_list_skips_empty_values(self) -> None:
        self.assertEqual(
            parse_hotkey_list("<ctrl>+v, ,<shift>+<insert>"),
            ("<ctrl>+v", "<shift>+<insert>"),
        )

    def test_preview_text_truncates_long_text(self) -> None:
        long_text = "word " * 200
        self.assertTrue(preview_text(long_text, limit=40).endswith("..."))


if __name__ == "__main__":
    unittest.main()
