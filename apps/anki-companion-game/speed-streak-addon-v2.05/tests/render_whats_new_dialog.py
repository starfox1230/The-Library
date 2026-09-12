from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6 import QtCore, QtGui, QtWidgets  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]


def _install_aqt_qt_shim() -> None:
    aqt = ModuleType("aqt")
    qt = ModuleType("aqt.qt")
    for module in (QtCore, QtGui, QtWidgets):
        for name in dir(module):
            if not name.startswith("_"):
                setattr(qt, name, getattr(module, name))
    aqt.qt = qt  # type: ignore[attr-defined]
    sys.modules["aqt"] = aqt
    sys.modules["aqt.qt"] = qt


def _load_whats_new_dialog() -> ModuleType:
    package_name = "speed_streak_v2_04_whats_new_render"
    package = ModuleType(package_name)
    package.__path__ = [str(ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for name in ("settings_components", "support_dialog", "whats_new_dialog"):
        qualified = f"{package_name}.{name}"
        spec = importlib.util.spec_from_file_location(qualified, ROOT / f"{name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.whats_new_dialog"]


def main() -> None:
    _install_aqt_qt_shim()
    module = _load_whats_new_dialog()
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    application.setFont(QtGui.QFont("Segoe UI", 10))
    dialog = module.WhatsNewDialog()
    dialog.show()
    application.processEvents()
    if len(sys.argv) > 2:
        scroll = dialog.findChild(QtWidgets.QScrollArea)
        if scroll is None:
            raise SystemExit("Could not find the What’s New scroll area")
        scroll.verticalScrollBar().setValue(int(sys.argv[2]))
        application.processEvents()
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests" / "whats-new-dialog.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not dialog.grab().save(str(output)):
        raise SystemExit("Could not save What’s New dialog render")
    print(output.resolve())
    dialog.close()


if __name__ == "__main__":
    main()
