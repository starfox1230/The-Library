from __future__ import annotations

import logging
import shutil
import threading
from pathlib import Path
from time import perf_counter

import sounddevice
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication
from pynput.keyboard import GlobalHotKeys

from .audio import MicrophoneRecorder
from .config import AppConfig
from .hotkey_polling import (
    PollableHotkey,
    is_pollable_hotkey_down,
    is_windows_hotkey_polling_available,
    parse_pollable_hotkey,
)
from .openai_client import TranscriptionClient, friendly_openai_error
from .overlay import CursorOverlay
from .tray import CursorTray


class CursorTranscriberApp(QObject):
    toggle_requested = Signal()
    paste_requested = Signal()
    exit_requested = Signal()
    transcription_ready = Signal(str)
    transcription_failed = Signal(str)

    def __init__(self, qt_app: QApplication, config: AppConfig) -> None:
        super().__init__()
        self._qt_app = qt_app
        self._config = config
        self._recorder = MicrophoneRecorder(
            runtime_dir=config.runtime_dir,
            sample_rate_hz=config.sample_rate_hz,
            channels=config.channels,
        )
        self._transcriber = TranscriptionClient(api_key=config.api_key, model=config.model)
        self._overlay = CursorOverlay(
            max_width=config.overlay_max_width,
            offset_x=config.overlay_offset_x,
            offset_y=config.overlay_offset_y,
            toggle_hotkey_label=config.toggle_hotkey_label,
            exit_hotkey_label=config.exit_hotkey_label,
        )
        self._tray: CursorTray | None = None
        self._hotkeys: GlobalHotKeys | None = None
        self._pollable_hotkeys: list[tuple[PollableHotkey, Signal]] = []
        self._polling_hotkeys_down: set[str] = set()
        self._last_hotkey_emit_at: dict[str, float] = {}
        self._hotkey_poll_timer = QTimer(self)
        self._hotkey_poll_timer.setInterval(20)
        self._hotkey_poll_timer.timeout.connect(self._poll_windows_hotkeys)
        self._capture_started_at: float | None = None
        self._recording_started_at: float | None = None
        self._is_arming = False
        self._ready_poll_timer = QTimer(self)
        self._ready_poll_timer.setInterval(30)
        self._ready_poll_timer.timeout.connect(self._check_recording_ready)
        self._recording_timer = QTimer(self)
        self._recording_timer.setInterval(100)
        self._recording_timer.timeout.connect(self._tick_recording)
        self._is_transcribing = False
        self._transcript_visible = False
        self._last_transcript_text = ""
        self._shutting_down = False

        self.toggle_requested.connect(self.toggle_recording)
        self.paste_requested.connect(self._handle_paste_shortcut)
        self.exit_requested.connect(self.shutdown_and_exit)
        self.transcription_ready.connect(self._handle_transcription_ready)
        self.transcription_failed.connect(self._handle_transcription_failed)

    def start(self) -> None:
        if CursorTray.is_available():
            self._tray = CursorTray(
                toggle_hotkey_label=self._config.toggle_hotkey_label,
                exit_hotkey_label=self._config.exit_hotkey_label,
            )
            self._tray.toggle_requested.connect(self.toggle_requested.emit)
            self._tray.show_requested.connect(self._show_status_hint)
            self._tray.exit_requested.connect(self.exit_requested.emit)
            self._tray.show()
            self._tray.set_ready()
            logging.info("System tray icon initialized")
        else:
            logging.warning("System tray is not available on this system")

        hotkey_map: dict[str, object] = {
            self._config.toggle_hotkey: lambda: self._emit_hotkey_signal(
                self._config.toggle_hotkey,
                self.toggle_requested,
            ),
            self._config.exit_hotkey: lambda: self._emit_hotkey_signal(
                self._config.exit_hotkey,
                self.exit_requested,
            ),
        }
        for paste_hotkey in self._config.paste_hotkeys:
            hotkey_map[paste_hotkey] = lambda paste_hotkey=paste_hotkey: self._emit_hotkey_signal(
                paste_hotkey,
                self.paste_requested,
            )

        self._hotkeys = GlobalHotKeys(hotkey_map)
        self._hotkeys.start()
        self._start_windows_hotkey_polling()
        logging.info("Cursor transcriber started with hotkey %s", self._config.toggle_hotkey)
        self._set_tray_ready()
        self._overlay.show_ready()
        self._overlay.schedule_hide(2600)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._ready_poll_timer.stop()
        self._is_arming = False
        self._capture_started_at = None
        self._recording_timer.stop()
        self._hotkey_poll_timer.stop()
        self._polling_hotkeys_down.clear()
        self._last_hotkey_emit_at.clear()
        self._last_transcript_text = ""
        try:
            self._recorder.discard()
        except Exception:
            logging.exception("Failed to discard the recorder during shutdown")
        if self._hotkeys is not None:
            try:
                self._hotkeys.stop()
            except Exception:
                logging.exception("Failed to stop global hotkeys")
            self._hotkeys = None
        if self._tray is not None:
            self._tray.hide()
            self._tray.deleteLater()
            self._tray = None
        self._overlay.hide()

    def _start_windows_hotkey_polling(self) -> None:
        if not is_windows_hotkey_polling_available():
            return

        pollable_hotkeys = [
            (self._config.exit_hotkey, self.exit_requested),
            (self._config.toggle_hotkey, self.toggle_requested),
            *[(paste_hotkey, self.paste_requested) for paste_hotkey in self._config.paste_hotkeys],
        ]
        self._pollable_hotkeys = [
            (parsed_hotkey, signal)
            for hotkey, signal in pollable_hotkeys
            if (parsed_hotkey := parse_pollable_hotkey(hotkey)) is not None
        ]
        if not self._pollable_hotkeys:
            logging.warning("No configured hotkeys can be polled with the Windows fallback")
            return

        self._hotkey_poll_timer.start()
        logging.info("Windows hotkey polling fallback enabled for JoyToKey-style injected keys")

    def _poll_windows_hotkeys(self) -> None:
        if self._shutting_down:
            return

        for hotkey, signal in self._pollable_hotkeys:
            is_down = is_pollable_hotkey_down(hotkey)
            was_down = hotkey.source in self._polling_hotkeys_down
            if is_down and not was_down:
                self._polling_hotkeys_down.add(hotkey.source)
                self._emit_hotkey_signal(hotkey.source, signal)
            elif not is_down and was_down:
                self._polling_hotkeys_down.remove(hotkey.source)

    def _emit_hotkey_signal(self, hotkey: str, signal: Signal) -> None:
        now = perf_counter()
        if now - self._last_hotkey_emit_at.get(hotkey, 0.0) < 0.15:
            return
        self._last_hotkey_emit_at[hotkey] = now
        signal.emit()

    def shutdown_and_exit(self) -> None:
        logging.info("Exit hotkey pressed")
        self.shutdown()
        self._qt_app.quit()

    def toggle_recording(self) -> None:
        if self._shutting_down:
            return
        if self._is_transcribing:
            self._overlay.show_error("The previous recording is still transcribing.")
            self._overlay.schedule_hide(2200)
            return
        if self._is_arming:
            self._stop_recording()
            return
        if self._capture_started_at is None:
            self._begin_recording_warmup()
        else:
            self._stop_recording()

    def _begin_recording_warmup(self) -> None:
        self._transcript_visible = False
        try:
            self._recorder.start()
        except sounddevice.PortAudioError:
            logging.exception("Microphone could not start")
            self._overlay.show_error(
                "The microphone could not start. Check your input device and Windows microphone permissions."
            )
            self._overlay.schedule_hide(4200)
            self._set_tray_error()
            return
        except Exception as exc:
            logging.exception("Recording failed to start")
            self._overlay.show_error(str(exc))
            self._overlay.schedule_hide(3200)
            self._set_tray_error()
            return

        self._capture_started_at = perf_counter()
        self._recording_started_at = None
        self._is_arming = True
        self._overlay.show_transcribing()
        self._set_tray_arming()
        self._ready_poll_timer.start()
        logging.info("Recording started, waiting for microphone readiness")

    def _stop_recording(self) -> None:
        self._ready_poll_timer.stop()
        self._is_arming = False
        self._recording_timer.stop()
        self._recording_started_at = None
        try:
            recording_result = self._recorder.stop()
        except Exception as exc:
            logging.exception("Recording failed to stop")
            self._overlay.show_error(f"Could not stop recording: {exc}")
            self._overlay.schedule_hide(3200)
            self._set_tray_error()
            return
        self._capture_started_at = None

        logging.info("Recording stopped: %s", recording_result.path)
        self._save_debug_recording(recording_result.path)
        if recording_result.path.stat().st_size <= 44:
            self._recorder.cleanup(recording_result.path)
            self._overlay.show_error("No microphone audio was captured.")
            self._overlay.schedule_hide(2800)
            self._set_tray_error()
            return

        if recording_result.warnings:
            logging.warning("Recording warnings: %s", "; ".join(recording_result.warnings))

        self._is_transcribing = True
        self._overlay.show_transcribing()
        self._set_tray_transcribing()
        worker = threading.Thread(
            target=self._transcribe_worker,
            args=(recording_result.path,),
            daemon=True,
        )
        worker.start()

    def _tick_recording(self) -> None:
        if self._recording_started_at is None or self._shutting_down:
            return

        elapsed = perf_counter() - self._recording_started_at
        seconds_remaining = max(0.0, self._config.max_recording_seconds - elapsed)
        self._overlay.show_recording(
            seconds_remaining=seconds_remaining,
            max_seconds=self._config.max_recording_seconds,
        )

        if seconds_remaining <= 0:
            self._stop_recording()

    def _check_recording_ready(self) -> None:
        if self._shutting_down or not self._is_arming or self._capture_started_at is None:
            return
        if not self._recorder.has_received_audio():
            return

        elapsed_ms = (perf_counter() - self._capture_started_at) * 1000.0
        if elapsed_ms < self._config.recording_ready_delay_ms:
            return

        self._ready_poll_timer.stop()
        self._is_arming = False
        self._recording_started_at = perf_counter()
        self._recording_timer.start()
        self._set_tray_recording()
        logging.info("Recording ready for speech after %.0f ms", elapsed_ms)
        self._tick_recording()

    def _transcribe_worker(self, audio_path: Path) -> None:
        try:
            transcript = self._transcriber.transcribe(
                audio_path,
                prompt=self._config.transcription_prompt,
            )
        except Exception as exc:
            logging.exception("Transcription failed")
            self.transcription_failed.emit(friendly_openai_error(exc))
        else:
            self.transcription_ready.emit(transcript)
        finally:
            self._recorder.cleanup(audio_path)

    def _handle_transcription_ready(self, transcript: str) -> None:
        self._is_transcribing = False
        if self._shutting_down:
            return
        transcript_text = transcript.strip()
        if not transcript_text:
            self._overlay.show_error("OpenAI returned an empty transcript.")
            self._overlay.schedule_hide(3200)
            return

        self._copy_to_clipboard(transcript_text)
        self._transcript_visible = True
        self._last_transcript_text = transcript_text
        logging.info("Transcript copied to clipboard (%d chars)", len(transcript_text))
        self._overlay.show_transcript(transcript_text)
        self._set_tray_transcript_ready()

    def _handle_transcription_failed(self, error_message: str) -> None:
        self._is_transcribing = False
        if self._shutting_down:
            return
        self._overlay.show_error(error_message)
        self._overlay.schedule_hide(4200)
        self._set_tray_error()

    def _copy_to_clipboard(self, text: str) -> None:
        self._qt_app.clipboard().setText(text)

    def _handle_paste_shortcut(self) -> None:
        if self._transcript_visible and not self._is_transcribing and not self._is_arming and self._capture_started_at is None:
            self._transcript_visible = False
            self._overlay.hide()
            self._set_tray_ready()

    def _save_debug_recording(self, recording_path: Path) -> None:
        debug_path = self._config.runtime_dir / "last-recording.wav"
        try:
            shutil.copyfile(recording_path, debug_path)
            logging.info("Saved debug recording to %s", debug_path)
        except Exception:
            logging.exception("Failed to save debug recording copy")

    def _show_status_hint(self) -> None:
        if self._shutting_down:
            return
        if self._is_transcribing or self._is_arming:
            self._overlay.show_transcribing()
            return
        if self._capture_started_at is not None:
            seconds_remaining = self._config.max_recording_seconds
            if self._recording_started_at is not None:
                elapsed = perf_counter() - self._recording_started_at
                seconds_remaining = max(0.0, self._config.max_recording_seconds - elapsed)
            self._overlay.show_recording(
                seconds_remaining=seconds_remaining,
                max_seconds=self._config.max_recording_seconds,
            )
            return
        if self._transcript_visible:
            self._overlay.show_transcript(self._last_transcript_text or self._qt_app.clipboard().text())
            return

        self._overlay.show_ready()
        self._overlay.schedule_hide(2200)

    def _set_tray_ready(self) -> None:
        if self._tray is not None:
            self._tray.set_ready()

    def _set_tray_arming(self) -> None:
        if self._tray is not None:
            self._tray.set_arming()

    def _set_tray_recording(self) -> None:
        if self._tray is not None:
            self._tray.set_recording()

    def _set_tray_transcribing(self) -> None:
        if self._tray is not None:
            self._tray.set_transcribing()

    def _set_tray_transcript_ready(self) -> None:
        if self._tray is not None:
            self._tray.set_transcript_ready()

    def _set_tray_error(self) -> None:
        if self._tray is not None:
            self._tray.set_error()
