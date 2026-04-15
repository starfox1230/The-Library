from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "pdf_text_compare.py"
LEFT_PDF = (
    REPO_ROOT
    / "apps"
    / "core-studying"
    / "Radioisotope Safety Document"
    / "RISC-Study-Guide-2025-v2 (1).pdf"
)
RIGHT_PDF = (
    REPO_ROOT
    / "apps"
    / "core-studying"
    / "Radioisotope Safety Document"
    / "RISC-Study-Guide-2026.pdf"
)


@unittest.skipUnless(LEFT_PDF.exists() and RIGHT_PDF.exists(), "Sample RISC PDFs are not available.")
class PdfTextCompareCliIntegrationTests(unittest.TestCase):
    def test_cli_generates_comparison_reports_for_risc_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(LEFT_PDF),
                    str(RIGHT_PDF),
                    "--output-dir",
                    str(output_dir),
                    "--left-label",
                    "RISC 2025",
                    "--right-label",
                    "RISC 2026",
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(
                result.returncode,
                0,
                msg=f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}",
            )
            self.assertIn("Change blocks:", result.stdout)

            extracted_files = sorted(output_dir.glob("*.extracted.txt"))
            markdown_files = sorted(output_dir.glob("*.summary.md"))
            json_files = sorted(output_dir.glob("*.changes.json"))
            html_files = sorted(output_dir.glob("*.diff.html"))

            self.assertEqual(2, len(extracted_files))
            self.assertEqual(1, len(markdown_files))
            self.assertEqual(1, len(json_files))
            self.assertEqual(1, len(html_files))

            summary = json.loads(json_files[0].read_text(encoding="utf-8"))
            self.assertGreater(summary["stats"]["change_blocks"], 0)
            self.assertGreater(summary["stats"]["similarity_ratio"], 0.7)

            markdown = markdown_files[0].read_text(encoding="utf-8")
            self.assertIn("2025 cycle", markdown)
            self.assertIn("2026 cycle", markdown)
            self.assertIn("2026 RISC Study Guide Committee", markdown)

            html_report = html_files[0].read_text(encoding="utf-8")
            self.assertIn("Changes Only", html_report)
            self.assertIn("Show nearby context", html_report)
            self.assertIn("Show full document diff", html_report)
            self.assertIn("Jump To Changes", html_report)


if __name__ == "__main__":
    unittest.main()
