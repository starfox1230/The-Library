from pathlib import Path
import re


ROOT = Path(__file__).parent


def test_starter_list_has_50_unique_diagnoses_and_three_modalities():
    data = (ROOT / "data.js").read_text(encoding="utf-8")
    ids = re.findall(r'\{id:"([^"]+)"', data)
    assert len(ids) == 50
    assert len(set(ids)) == 50
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    assert app.count('key: "xr"') == 1
    assert app.count('key: "ct"') == 1
    assert app.count('key: "mri"') == 1


def test_local_launcher_uses_standard_library_only():
    launcher = (ROOT / "run_app.py").read_text(encoding="utf-8")
    assert "http.server.ThreadingHTTPServer" in launcher
    assert "127.0.0.1" in launcher
