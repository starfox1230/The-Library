from __future__ import annotations

import logging
import threading
from pathlib import Path
from time import perf_counter

import sounddevice
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import QApplication
from pynput.keyboard import GlobalHotKeys

from .audio import MicrophoneRecorder
from .config import AppConfig
from .openai_client import TranscriptionClient, friendly_openai_error
from .overlay import CursorOverlay


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
        self._hotkeys: GlobalHotKeys | None = None
        self._recording_started_at: float | None = None
        self._recording_timer = QTimer(self)
        self._recording_timer.setInterval(100)
        self._recording_timer.timeout.connect(self._tick_recording)
        self._is_transcribing = False
        self._transcript_visible = False
        self._shutting_down = False

        self.toggle_requested.connect(self.toggle_recording)
        self.paste_requested.connect(self._handle_paste_shortcut)
        self.exit_requested.connect(self.shutdown_and_exit)
        self.transcription_ready.connect(self._handle_transcription_ready)
        self.transcription_failed.connect(self._handle_transcription_failed)

    def start(self) -> None:
        hotkey_map: dict[str, object] = {
            self._config.toggle_hotkey: lambda: self.toggle_requested.emit(),
            self._config.exit_hotkey: lambda: self.exit_requested.emit(),
        }
        for paste_hotkey in self._config.paste_hotkeys:
            hotkey_map[paste_hotkey] = lambda: self.paste_requested.emit()

        self._hotkeys = GlobalHotKeys(hotkey_map)
        self._hotkeys.start()
        logging.info("Cursor transcriber started with hotkey %s", self._config.toggle_hotkey)
        self._overlay.show_ready()
        self._overlay.schedule_hide(2600)

    def shutdown(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        self._recording_timer.stop()
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
        self._overlay.hide()

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
        if self._recording_started_at is None:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self) -> None:
        self._transcript_visible = False
        try:
            self._recorder.start()
        except sounddevice.PortAudioError:
            logging.exception("Microphone could not start")
            self._overlay.show_error(
                "The microphone could not start. Check your input device and Windows microphone permissions."
            )
            self._overlay.schedule_hide(4200)
            return
        except Exception as exc:
            logging.exception("Recording failed to start")
            self._overlay.show_error(str(exc))
            self._overlay.schedule_hide(3200)
            return

        self._recording_started_at = perf_counter()
        self._recording_timer.start()
        logging.info("Recording started")
        self._tick_recording()

    def _stop_recording(self) -> None:
        self._recording_timer.stop()
        self._recording_started_at = None
        try:
            recording_result = self._recorder.stop()
        except Exception as exc:
            logging.exception("Recording failed to stop")
            self._overlay.show_error(f"Could not stop recording: {exc}")
            self._overlay.schedule_hide(3200)
            return

        logging.info("Recording stopped: %s", recording_result.path)
        if recording_result.path.stat().st_size <= 44:
            self._recorder.cleanup(recording_result.path)
            self._overlay.show_error("No microphone audio was captured.")
            self._overlay.schedule_hide(2800)
            return

        if recording_result.warnings:
            logging.warning("Recording warnings: %s", "; ".join(recording_result.warnings))

        self._is_transcribing = True
        self._overlay.show_transcribing()
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
        logging.info("Transcript copied to clipboard (%d chars)", len(transcript_text))
        self._overlay.show_transcript(transcript_text)

    def _handle_transcription_failed(self, error_message: str) -> None:
        self._is_transcribing = False
        if self._shutting_down:
            return
        self._overlay.show_error(error_message)
        self._overlay.schedule_hide(4200)

    def _copy_to_clipboard(self, text: str) -> None:
        self._qt_app.clipboard().setText(text)

    def _handle_paste_shortcut(self) -> None:
        if self._transcript_visible and not self._is_transcribing and self._recording_started_at is None:
            self._transcript_visible = False
            self._overlay.hide()
