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


def _load_addon_modules() -> ModuleType:
    package_name = "speed_streak_v2_04_sync_render"
    package = ModuleType(package_name)
    package.__path__ = [str(ROOT)]  # type: ignore[attr-defined]
    sys.modules[package_name] = package
    for name in ("audio_waveform", "countdown_audio", "countdown_sync_dialog"):
        qualified = f"{package_name}.{name}"
        spec = importlib.util.spec_from_file_location(qualified, ROOT / f"{name}.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified] = module
        spec.loader.exec_module(module)
    return sys.modules[f"{package_name}.countdown_sync_dialog"]


class FakeController:
    def preview_audio_feedback(self, _audio_key: str) -> bool:
        return True

    def preview_countdown_audio(self, _audio_key: str) -> bool:
        return True


def main() -> None:
    _install_aqt_qt_shim()
    module = _load_addon_modules()
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    application.setFont(QtGui.QFont("Segoe UI", 10))
    cue = ROOT / "Audio_trimmed" / "countdown-cues" / "clock-tick-soft.wav"
    dialog = module.CountdownSyncPointDialog(
        FakeController(),
        audio_key="countdown-cues/clock-tick-soft.wav",
        audio_label="Countdown Cues / Clock Tick Soft",
        audio_path=str(cue),
        warning_seconds=3,
        alignment_ms=180,
        timer_colors={"red": "#c34f69"},
    )
    if len(sys.argv) >= 4:
        dialog.resize(int(sys.argv[2]), int(sys.argv[3]))
    dialog.show()
    application.processEvents()
    print(
        "waveform=",
        dialog.waveform_widget.geometry().getRect(),
        "summary=",
        dialog.sync_summary.geometry().getRect(),
        "spin=",
        dialog.sync_spin.geometry().getRect(),
        "timer=",
        dialog.timer_preview.geometry().getRect(),
        "actions=",
        dialog.action_bar.geometry().getRect(),
        "cancel=",
        dialog.cancel_button.geometry().getRect(),
        "use=",
        dialog.use_button.geometry().getRect(),
    )
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests" / "countdown-sync-dialog.png"
    output.parent.mkdir(parents=True, exist_ok=True)
    if not dialog.grab().save(str(output)):
        raise SystemExit("Could not save dialog render")
    print(output.resolve())
    dialog.close()


if __name__ == "__main__":
    main()
