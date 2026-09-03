from pathlib import Path
import re


ROOT = Path(__file__).parent


def test_starter_list_has_51_unique_diagnoses_and_three_modalities():
    data = (ROOT / "data.js").read_text(encoding="utf-8")
    ids = re.findall(r'\{id:"([^"]+)"', data)
    assert len(ids) == 51
    assert len(set(ids)) == 51
    app = (ROOT / "app.js").read_text(encoding="utf-8")
    assert app.count('key: "xr"') == 1
    assert app.count('key: "ct"') == 1
    assert app.count('key: "mri"') == 1


def test_native_launcher_and_runtime_are_wired():
    launcher = (ROOT / "run_app.py").read_text(encoding="utf-8")
    native = (ROOT / "native_app.py").read_text(encoding="utf-8")
    browser = (ROOT / "app.js").read_text(encoding="utf-8") + (ROOT / "index.html").read_text(encoding="utf-8")
    assert "from native_app import main" in launcher
    assert "QMainWindow" in native
    assert "open_in_chrome" in native
    assert "dragActive" in native
    assert "ZipFile" in native
    assert "QTabWidget" in native
    assert "def _clear_layout" in native
    assert "ResponsiveImageGrid" in native
    assert "FindingEditor" in native
    assert "AlignTop" in native
    assert "favorite-active" in native
    assert "favorite-active" in browser
    assert "FavoriteListDelegate" in native
