from __future__ import annotations

import ctypes
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QLockFile, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .config import load_config
from .main_window import MainWindow


APP_ICON_PATH = Path(__file__).resolve().parents[1] / "assets" / "app-icon.ico"


def _enable_per_monitor_dpi_awareness() -> None:
    if not hasattr(ctypes, "windll"):
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass


def main() -> int:
    _enable_per_monitor_dpi_awareness()
    app = QApplication(sys.argv)
    app.setApplicationName("Screen Capture Transcriber")
    app.setOrganizationName("The Library")
    if APP_ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(APP_ICON_PATH)))

    lock_dir = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.TempLocation
    )
    lock = QLockFile(os.path.join(lock_dir, "screen-capture-transcriber.lock"))
    lock.setStaleLockTime(0)
    if not lock.tryLock(100):
        QMessageBox.information(
            None,
            "Screen Capture Transcriber",
            "Screen Capture Transcriber is already running.",
        )
        return 0

    try:
        config = load_config()
    except Exception as exc:
        QMessageBox.critical(None, "Configuration error", str(exc))
        return 1

    logging.basicConfig(level=logging.INFO)
    window = MainWindow(config)
    window.show()
    return app.exec()
