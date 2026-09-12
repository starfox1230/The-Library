import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]


class PrismReleaseTests(unittest.TestCase):
    def test_visual_and_independent_palette_round_trip(self):
        package = ModuleType("prism_release_test")
        package.__path__ = [str(ROOT)]
        sys.modules[package.__name__] = package
        modes = importlib.import_module(package.__name__ + ".visual_mode")
        colors = importlib.import_module(package.__name__ + ".visual_colors")
        self.assertEqual(modes.normalize_visual_mode("Prism"), "prism_gate")
        self.assertEqual(modes.normalize_visual_mode("Hypernova"), "prism_gate")
        self.assertEqual(modes.visual_mode_label("prism_gate"), "Hypernova")
        palettes = colors.normalize_visual_color_palettes({
            "prism_gate": {"core": "#abcdef", "green": "#123456"},
            "sphere": {"core": "#fedcba"},
        })
        restored = colors.normalize_visual_color_palettes(json.loads(json.dumps(palettes)))
        self.assertEqual(restored["prism_gate"]["core"], "#abcdef")
        self.assertEqual(restored["sphere"]["core"], "#fedcba")

    @unittest.skipUnless(sys.platform == "win32", "PowerShell upgrade integration test")
    def test_upgrade_and_reinstall_preserve_settings_and_data(self):
        running = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             "[bool](Get-Process -Name anki -ErrorAction SilentlyContinue)"],
            capture_output=True, text=True, timeout=15,
        )
        if running.stdout.strip().lower() == "true":
            self.skipTest("Anki is open; the production installer intentionally refuses replacement")
        # Never use the real Anki profile: all recursive writes stay in this fixture.
        with tempfile.TemporaryDirectory(prefix="prism-install-", dir=REPO / "tmp") as temp:
            fixture = Path(temp).resolve()
            addons = fixture / "Anki2" / "addons21"
            old = addons / "speed_streak_v2_04"
            (old / "user_files").mkdir(parents=True)
            (old / "user_files" / "history-sentinel.txt").write_text("keep my records")
            (old / "meta.json").write_text(json.dumps({"config": {
                "visual_mode": "singularity", "custom_setting": 47,
            }}))
            new = addons / "speed_streak_v2_05"
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
                       "-File", str(ROOT / "install_to_anki.ps1")]
            for _ in range(2):
                result = subprocess.run(command, env={**os.environ, "APPDATA": str(fixture)},
                                        capture_output=True, text=True, timeout=90)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(old.exists())
                self.assertEqual((new / "user_files" / "history-sentinel.txt").read_text(), "keep my records")
                config = json.loads((new / "meta.json").read_text())["config"]
                self.assertEqual(config["custom_setting"], 47)
                self.assertEqual(config["visual_mode"], "singularity")
                self.assertFalse((new / "web" / "web").exists())
                self.assertEqual((new / "web" / "overlay.js").read_bytes(), (ROOT / "web" / "overlay.js").read_bytes())

    def test_package_assets_match_sources(self):
        with zipfile.ZipFile(ROOT / "speed_streak_v2_05.ankiaddon") as archive:
            manifest = json.loads(archive.read("manifest.json"))
            self.assertEqual(manifest["package"], "speed_streak_v2_05")
            self.assertIn("speed_streak_v2_04", manifest["conflicts"])
            for name in ("web/overlay.js", "web/overlay.css", "visual_mode.py", "settings_dialog.py"):
                self.assertEqual(archive.read(name), (ROOT / name).read_bytes())
            self.assertFalse(any("\\" in name or "__pycache__" in name or name.startswith(("tests/", "user_files/")) for name in archive.namelist()))
            fallback = {}
            exec(archive.read("web_assets.py"), fallback)
            self.assertEqual(fallback["WEB_ASSETS"]["overlay.js"], (ROOT / "web" / "overlay.js").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
