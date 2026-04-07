from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .app import CursorTranscriberApp
from .config import ConfigError, load_config


def _show_message_box(title: str, message: str) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(f"{title}: {message}", file=sys.stderr)


def _configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def main() -> int:
    try:
        config = load_config()
        _configure_logging(config.runtime_dir / "app.log")
    except ConfigError as exc:
        _show_message_box("Cursor Transcriber", str(exc))
        return 1

    qt_app = QApplication(sys.argv)
    qt_app.setQuitOnLastWindowClosed(False)

    controller = CursorTranscriberApp(qt_app=qt_app, config=config)
    try:
        controller.start()
        return qt_app.exec()
    except Exception as exc:  # pragma: no cover
        logging.exception("Fatal application error")
        _show_message_box(
            "Cursor Transcriber",
            f"The app hit a fatal error:\n\n{exc}\n\nCheck runtime/app.log for details.",
        )
        return 1
    finally:
        controller.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
