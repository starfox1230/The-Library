from __future__ import annotations

import ctypes
import logging
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .app import CursorTranscriberApp
from .config import ConfigError, load_config
from .single_instance import acquire_single_instance


def _show_message_box(title: str, message: str, flags: int = 0x10) -> None:
    try:
        ctypes.windll.user32.MessageBoxW(0, message, title, flags)
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
    controller: CursorTranscriberApp | None = None
    instance_lock = None
    try:
        config = load_config()
        _configure_logging(config.runtime_dir / "app.log")
        instance_lock = acquire_single_instance("Local\\OpenAICursorTranscriber")
        if instance_lock is None:
            logging.info("Skipped launch because another Cursor Transcriber instance is already running")
            _show_message_box(
                "Cursor Transcriber",
                "Cursor Transcriber is already running.",
                flags=0x40,
            )
            return 0
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
        if controller is not None:
            controller.shutdown()
        if instance_lock is not None:
            instance_lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
