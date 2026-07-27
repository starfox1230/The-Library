from __future__ import annotations

import time
import traceback
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Qt, QUrl, Signal
from PySide6.QtGui import QCloseEvent, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .anki_export import build_anatomy_apkg
from .annotation import AnatomyAnnotationDialog
from .audio import AudioDevice, LoopbackRecorder, list_loopback_devices
from .capture_border import CaptureBorderOverlay
from .codex_prompt import build_codex_anki_prompt, save_codex_anki_prompt
from .config import APP_DIR, AppConfig, ENV_PATH
from .hotkeys import (
    GlobalHotkeys,
    control_key_is_down,
    move_pointer,
    replay_left_click,
)
from .media import (
    MediaError,
    ScreenRecorder,
    concatenate_segments,
    extract_last_frame,
    probe_duration,
    process_recording,
    resolve_ffmpeg,
    resolve_ffprobe,
)
from .models import CaptureRegion, CaptureSegment, SessionManifest, format_duration
from .post_editor import AnatomyPostEditorDialog
from .playback_point_selector import PlaybackPointSelector
from .region_selector import RegionSelector
from .review import build_anatomy_review, write_anatomy_manifest
from .session_library import SessionLibraryDialog
from .transcription import (
    SessionTranscriber,
    estimate_cost,
    friendly_openai_error,
    recover_completed_transcript,
)


MODELS = (
    ("GPT-4o mini — fast, lowest estimated cost", "gpt-4o-mini-transcribe"),
    ("GPT-4o — higher accuracy", "gpt-4o-transcribe"),
    ("GPT-4o diarize — speaker labels", "gpt-4o-transcribe-diarize"),
    ("Whisper — timestamp-friendly legacy model", "whisper-1"),
)


class StopSegmentWorker(QThread):
    progress = Signal(str)
    frame_ready = Signal(object, float)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        session: SessionManifest,
        segment: CaptureSegment | None,
        purpose: str,
        screen_recorder: ScreenRecorder | None,
        audio_recorder: LoopbackRecorder | None,
        ffmpeg_path: Path,
        ffprobe_path: Path,
        bitrate_kbps: int,
    ) -> None:
        super().__init__()
        self._session = session
        self._segment = segment
        self._purpose = purpose
        self._screen_recorder = screen_recorder
        self._audio_recorder = audio_recorder
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._bitrate_kbps = bitrate_kbps

    def run(self) -> None:
        try:
            paused_frame: Path | None = None
            if self._segment is not None:
                if self._screen_recorder is None or self._audio_recorder is None:
                    raise RuntimeError("Active recording devices are unavailable.")
                self.progress.emit("Finalizing screen capture…")
                screen_path = self._screen_recorder.stop()
                self.progress.emit("Finalizing system audio…")
                raw_audio_path = self._audio_recorder.stop()
                self._session.warnings.extend(self._audio_recorder.warnings)

                if self._purpose == "anatomy":
                    capture_index = len(self._session.anatomy_captures) + 1
                    paused_frame = self._session.anatomy_original_path(capture_index)
                    self.progress.emit("Capturing the paused frame…")
                    extract_last_frame(self._ffmpeg_path, screen_path, paused_frame)
                    estimated_timestamp = (
                        self._session.duration_seconds
                        + probe_duration(self._ffprobe_path, screen_path)
                    )
                    self.frame_ready.emit(paused_frame, estimated_timestamp)

                result = process_recording(
                    self._ffmpeg_path,
                    self._ffprobe_path,
                    screen_path,
                    raw_audio_path,
                    self._session.folder / self._segment.recording_file,
                    self._session.folder / self._segment.audio_file,
                    self._segment.video_start_monotonic
                    - self._segment.audio_start_monotonic,
                    self._bitrate_kbps,
                    self.progress.emit,
                )
                self._segment.duration_seconds = result.duration_seconds
                self._segment.state = "ready"
                self._session.duration_seconds = sum(
                    segment.duration_seconds for segment in self._session.segments
                )

            if self._purpose in {"anatomy", "pause"}:
                self._session.state = (
                    "study_paused" if self._purpose == "anatomy" else "paused"
                )
            else:
                recording_segments = [
                    self._session.folder / item.recording_file
                    for item in self._session.segments
                    if item.state == "ready"
                ]
                audio_segments = [
                    self._session.folder / item.audio_file
                    for item in self._session.segments
                    if item.state == "ready"
                ]
                final = concatenate_segments(
                    self._ffmpeg_path,
                    self._ffprobe_path,
                    recording_segments,
                    audio_segments,
                    self._session.recording_path,
                    self._session.audio_path,
                    self._session.playback_path,
                    self.progress.emit,
                )
                self._session.duration_seconds = final.duration_seconds
                self._session.state = "ready"
                write_anatomy_manifest(self._session)
                build_anatomy_review(self._session)
                try:
                    build_anatomy_apkg(self._session)
                except Exception as exc:
                    self._session.warnings.append(f"Anki export: {exc}")
            self._session.save()
            self.completed.emit(
                {
                    "session": self._session,
                    "purpose": self._purpose,
                    "paused_frame": paused_frame,
                }
            )
        except Exception as exc:
            if self._screen_recorder is not None:
                self._screen_recorder.abort()
            if self._audio_recorder is not None:
                self._audio_recorder.abort()
            if self._segment is not None:
                self._segment.state = "processing_failed"
            self._session.state = "processing_failed"
            self._session.warnings.append(str(exc))
            self._session.save()
            self.failed.emit(str(exc))


class TranscriptionWorker(QThread):
    progress = Signal(str, int, int)
    completed = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        session: SessionManifest,
        api_key: str,
        model: str,
        prompt: str | None,
        ffmpeg_path: Path,
        ffprobe_path: Path,
        bitrate_kbps: int,
    ) -> None:
        super().__init__()
        self._session = session
        self._api_key = api_key
        self._model = model
        self._prompt = prompt
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path
        self._bitrate_kbps = bitrate_kbps

    def run(self) -> None:
        try:
            transcriber = SessionTranscriber(
                api_key=self._api_key,
                model=self._model,
                ffmpeg_path=self._ffmpeg_path,
                ffprobe_path=self._ffprobe_path,
                bitrate_kbps=self._bitrate_kbps,
                prompt=self._prompt,
            )
            result = transcriber.transcribe(self._session, self.progress.emit)
            self._session.state = "transcribed"
            self._session.save()
            self.completed.emit(result)
        except Exception as exc:
            error_details = (
                f"Model: {self._model}\n"
                f"Error: {exc.__class__.__name__}: {exc}\n\n"
                f"{traceback.format_exc()}"
            )
            try:
                recovered = recover_completed_transcript(self._session)
            except Exception:
                recovered = None
            if recovered is not None:
                (self._session.folder / "transcription-recovery.txt").write_text(
                    error_details,
                    encoding="utf-8",
                )
                self._session.warnings.append(
                    f"Recovered a complete API transcript after local save error: {exc}"
                )
                self._session.save()
                self.completed.emit(recovered)
                return
            (self._session.folder / "transcription-error.txt").write_text(
                error_details,
                encoding="utf-8",
            )
            self._session.state = "transcription_failed"
            self._session.warnings.append(str(exc))
            self._session.save()
            self.failed.emit(friendly_openai_error(exc))


class MainWindow(QMainWindow):
    audio_level_received = Signal(float)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config
        self._region: CaptureRegion | None = None
        self._session: SessionManifest | None = None
        self._audio_devices: list[AudioDevice] = []
        self._audio_recorder: LoopbackRecorder | None = None
        self._screen_recorder: ScreenRecorder | None = None
        self._current_segment: CaptureSegment | None = None
        self._stop_worker: StopSegmentWorker | None = None
        self._transcription_worker: TranscriptionWorker | None = None
        self._recording_started = 0.0
        self._is_recording = False
        self._is_paused = False
        self._is_busy = False
        self._is_transcribing = False
        self._transcription_started = 0.0
        self._transcription_phase = ""
        self._study_paused = False
        self._playback_point: tuple[int, int] | None = None
        self._selecting_playback_point = False
        self._player_transition_pending = False
        self._pending_source_click: tuple[int, int] | None = None
        self._pending_paused_frame: Path | None = None
        self._pending_annotation: dict[str, object] | None = None
        self._anatomy_segment_ready = False
        self._annotation_finished = False
        self._selected_device_index: int | None = None
        self._audio_level = 0.0
        self._ffmpeg_path: Path | None = None
        self._ffprobe_path: Path | None = None
        self._capture_border = CaptureBorderOverlay()
        self._capture_border.screenshot_requested.connect(self._anatomy_pause)
        self._capture_border.pause_requested.connect(self._toggle_pause_recording)
        self._capture_border.stop_requested.connect(self._stop_recording)

        self.setWindowTitle("Screen Capture Transcriber")
        self.resize(1080, 760)
        self.setMinimumSize(900, 650)
        self._build_ui()
        self._apply_styles()
        self._annotation_dialog = AnatomyAnnotationDialog(parent=None)
        self._annotation_dialog.finished.connect(self._on_annotation_finished)

        self._selector = RegionSelector()
        self._selector.selected.connect(self._on_region_selected)
        self._selector.cancelled.connect(
            lambda: self._set_status("Region selection cancelled.", "neutral")
        )
        self._playback_selector = PlaybackPointSelector()
        self._playback_selector.selected.connect(
            self._on_playback_point_selected
        )
        self._playback_selector.cancelled.connect(
            self._on_playback_point_cancelled
        )

        self._hotkeys = GlobalHotkeys(
            config.toggle_recording_hotkey,
            config.add_chapter_hotkey,
            config.anatomy_capture_hotkey,
        )
        self._hotkeys.toggle_recording.connect(self._toggle_recording)
        self._hotkeys.add_chapter.connect(self._add_chapter)
        self._hotkeys.anatomy_capture.connect(self._anatomy_pause)
        self._hotkeys.period_capture.connect(self._anatomy_pause)
        self._hotkeys.ctrl_click.connect(self._on_ctrl_click)
        self._hotkeys.error.connect(
            lambda message: self._set_status(f"Global hotkeys unavailable: {message}", "warning")
        )
        self._hotkeys.start()

        self.audio_level_received.connect(self._on_audio_level)
        self._timer = QTimer(self)
        self._timer.setInterval(200)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

        self._initialize_media()
        self._refresh_audio_devices()
        self._sync_controls()

    def _build_ui(self) -> None:
        root = QWidget()
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        heading_row = QHBoxLayout()
        heading_column = QVBoxLayout()
        title = QLabel("Screen Capture Transcriber")
        title.setObjectName("Title")
        subtitle = QLabel(
            "F8 record / stop  •  F9 chapter  •  F10 anatomy pause  •  "
            "Ctrl+click the player for seamless study capture"
        )
        subtitle.setObjectName("Muted")
        heading_column.addWidget(title)
        heading_column.addWidget(subtitle)
        heading_row.addLayout(heading_column)
        heading_row.addStretch()
        self.past_sessions_button = QPushButton("Past Sessions")
        self.past_sessions_button.clicked.connect(self._show_session_library)
        heading_row.addWidget(
            self.past_sessions_button,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("StatusPill")
        heading_row.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignTop)
        outer.addLayout(heading_row)

        setup_card = QFrame()
        setup_card.setObjectName("Card")
        setup_grid = QGridLayout(setup_card)
        setup_grid.setContentsMargins(18, 16, 18, 16)
        setup_grid.setHorizontalSpacing(12)
        setup_grid.setVerticalSpacing(12)

        setup_grid.addWidget(QLabel("Session name"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Lecture, video, or topic")
        setup_grid.addWidget(self.title_edit, 0, 1, 1, 3)

        setup_grid.addWidget(QLabel("Capture area"), 1, 0)
        self.region_label = QLabel("No area selected")
        self.region_label.setObjectName("Muted")
        setup_grid.addWidget(self.region_label, 1, 1)
        self.select_region_button = QPushButton("Select Area")
        self.select_region_button.clicked.connect(self._select_region)
        setup_grid.addWidget(self.select_region_button, 1, 2)
        self.full_screen_button = QPushButton("Use Primary Screen")
        self.full_screen_button.clicked.connect(self._use_primary_screen)
        setup_grid.addWidget(self.full_screen_button, 1, 3)

        setup_grid.addWidget(QLabel("System audio"), 2, 0)
        self.audio_combo = QComboBox()
        setup_grid.addWidget(self.audio_combo, 2, 1, 1, 2)
        self.refresh_audio_button = QPushButton("Refresh")
        self.refresh_audio_button.clicked.connect(self._refresh_audio_devices)
        setup_grid.addWidget(self.refresh_audio_button, 2, 3)

        setup_grid.addWidget(QLabel("Audio activity"), 3, 0)
        self.audio_meter = QProgressBar()
        self.audio_meter.setRange(0, 100)
        self.audio_meter.setTextVisible(False)
        self.audio_meter.setFixedHeight(10)
        setup_grid.addWidget(self.audio_meter, 3, 1, 1, 3)

        setup_grid.addWidget(QLabel("Anatomy mode"), 4, 0)
        self.anatomy_mode_checkbox = QCheckBox(
            "Ctrl+click anywhere in the capture area uses the chosen player point, "
            "then annotates"
        )
        self.anatomy_mode_checkbox.setChecked(True)
        setup_grid.addWidget(self.anatomy_mode_checkbox, 4, 1, 1, 3)
        outer.addWidget(setup_card)

        control_row = QHBoxLayout()
        self.record_button = QPushButton("●  Start Recording")
        self.record_button.setObjectName("RecordButton")
        self.record_button.clicked.connect(self._toggle_recording)
        control_row.addWidget(self.record_button)
        self.chapter_button = QPushButton("+  Add Chapter")
        self.chapter_button.clicked.connect(self._add_chapter)
        control_row.addWidget(self.chapter_button)
        self.anatomy_button = QPushButton("Anatomy Capture (F10)")
        self.anatomy_button.clicked.connect(lambda: self._anatomy_pause())
        control_row.addWidget(self.anatomy_button)
        self.timer_label = QLabel("00:00")
        self.timer_label.setObjectName("Timer")
        control_row.addWidget(self.timer_label)
        control_row.addStretch()
        self.open_folder_button = QPushButton("Open Session Folder")
        self.open_folder_button.clicked.connect(self._open_session_folder)
        control_row.addWidget(self.open_folder_button)
        self.open_review_button = QPushButton("Open Anatomy Review")
        self.open_review_button.clicked.connect(self._open_anatomy_review)
        control_row.addWidget(self.open_review_button)
        outer.addLayout(control_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        chapters_card = QFrame()
        chapters_card.setObjectName("Card")
        chapters_layout = QVBoxLayout(chapters_card)
        chapters_heading = QLabel("Chapters")
        chapters_heading.setObjectName("SectionTitle")
        chapters_layout.addWidget(chapters_heading)
        chapters_hint = QLabel("Press F9 while recording. Double-click a title to rename it.")
        chapters_hint.setObjectName("Muted")
        chapters_hint.setWordWrap(True)
        chapters_layout.addWidget(chapters_hint)
        self.chapter_list = QListWidget()
        self.chapter_list.itemChanged.connect(self._on_chapter_renamed)
        chapters_layout.addWidget(self.chapter_list)
        anatomy_heading = QLabel("Anatomy captures")
        anatomy_heading.setObjectName("SectionTitle")
        chapters_layout.addWidget(anatomy_heading)
        anatomy_hint = QLabel(
            "Annotated frames are linked to the final video timestamp. "
            "Labeled captures can become saCloze++ cards."
        )
        anatomy_hint.setObjectName("Muted")
        anatomy_hint.setWordWrap(True)
        chapters_layout.addWidget(anatomy_hint)
        self.anatomy_list = QListWidget()
        self.anatomy_list.setMaximumHeight(180)
        chapters_layout.addWidget(self.anatomy_list)
        self.edit_anatomy_button = QPushButton("Edit Anatomy Screenshots")
        self.edit_anatomy_button.clicked.connect(self._edit_anatomy_captures)
        anatomy_actions = QHBoxLayout()
        anatomy_actions.addWidget(self.edit_anatomy_button)
        self.copy_codex_anki_button = QPushButton("Copy Codex Anki Prompt")
        self.copy_codex_anki_button.clicked.connect(self._copy_codex_anki_prompt)
        anatomy_actions.addWidget(self.copy_codex_anki_button)
        chapters_layout.addLayout(anatomy_actions)
        splitter.addWidget(chapters_card)

        transcript_card = QFrame()
        transcript_card.setObjectName("Card")
        transcript_layout = QVBoxLayout(transcript_card)
        transcript_heading_row = QHBoxLayout()
        transcript_heading = QLabel("Transcript")
        transcript_heading.setObjectName("SectionTitle")
        transcript_heading_row.addWidget(transcript_heading)
        transcript_heading_row.addStretch()
        self.copy_button = QPushButton("Copy All")
        self.copy_button.clicked.connect(self._copy_transcript)
        transcript_heading_row.addWidget(self.copy_button)
        transcript_layout.addLayout(transcript_heading_row)
        self.transcript_edit = QPlainTextEdit()
        self.transcript_edit.setPlaceholderText(
            "After recording, choose a model and press Transcribe. "
            "Chapter headings and timestamps will be preserved."
        )
        transcript_layout.addWidget(self.transcript_edit)

        transcribe_row = QHBoxLayout()
        self.model_combo = QComboBox()
        for label, model in MODELS:
            self.model_combo.addItem(label, model)
        selected_index = self.model_combo.findData(self._config.model)
        if selected_index >= 0:
            self.model_combo.setCurrentIndex(selected_index)
        self.model_combo.currentIndexChanged.connect(self._update_cost_label)
        transcribe_row.addWidget(self.model_combo, 2)
        self.cost_label = QLabel("Record something to estimate transcription cost.")
        self.cost_label.setObjectName("Muted")
        transcribe_row.addWidget(self.cost_label, 2)
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.setObjectName("PrimaryButton")
        self.transcribe_button.clicked.connect(self._transcribe)
        transcribe_row.addWidget(self.transcribe_button)
        transcript_layout.addLayout(transcribe_row)

        self.transcription_progress_frame = QFrame()
        self.transcription_progress_frame.setObjectName("ProgressCard")
        progress_layout = QVBoxLayout(self.transcription_progress_frame)
        progress_layout.setContentsMargins(14, 10, 14, 10)
        progress_heading = QHBoxLayout()
        self.transcription_progress_title = QLabel("Transcribing audio…")
        self.transcription_progress_title.setObjectName("ProgressTitle")
        progress_heading.addWidget(self.transcription_progress_title)
        progress_heading.addStretch()
        self.transcription_elapsed_label = QLabel("00:00 elapsed")
        self.transcription_elapsed_label.setObjectName("Muted")
        progress_heading.addWidget(self.transcription_elapsed_label)
        progress_layout.addLayout(progress_heading)
        self.transcription_progress_bar = QProgressBar()
        self.transcription_progress_bar.setRange(0, 0)
        self.transcription_progress_bar.setTextVisible(False)
        self.transcription_progress_bar.setFixedHeight(12)
        progress_layout.addWidget(self.transcription_progress_bar)
        self.transcription_phase_label = QLabel(
            "Preparing transcription request. Long recordings can take several minutes."
        )
        self.transcription_phase_label.setObjectName("Muted")
        self.transcription_phase_label.setWordWrap(True)
        progress_layout.addWidget(self.transcription_phase_label)
        self.transcription_progress_frame.hide()
        transcript_layout.addWidget(self.transcription_progress_frame)

        splitter.addWidget(transcript_card)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        outer.addWidget(splitter, 1)

        self.detail_label = QLabel(
            "Select one screen area, confirm the active system-audio output, then record."
        )
        self.detail_label.setObjectName("Muted")
        self.detail_label.setWordWrap(True)
        outer.addWidget(self.detail_label)

        self.setCentralWidget(root)

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #09101C;
                color: #EEF4FC;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QFrame#Card {
                background: #101B2B;
                border: 1px solid #22324A;
                border-radius: 12px;
            }
            QFrame#ProgressCard {
                background: #12293A;
                border: 1px solid #2B7693;
                border-radius: 9px;
            }
            QLabel#ProgressTitle {
                color: #8DE5FF;
                font-weight: 700;
            }
            QLabel#Title {
                font-size: 22pt;
                font-weight: 700;
            }
            QLabel#SectionTitle {
                font-size: 13pt;
                font-weight: 650;
            }
            QLabel#Muted {
                color: #9EB0C8;
            }
            QLabel#Timer {
                font-family: "Cascadia Mono";
                font-size: 22pt;
                font-weight: 700;
                color: #58D7FF;
                min-width: 120px;
            }
            QLabel#StatusPill {
                background: #17273A;
                border: 1px solid #2D4665;
                border-radius: 11px;
                padding: 6px 12px;
                color: #A9E9FF;
                font-weight: 650;
            }
            QPushButton {
                background: #17273A;
                border: 1px solid #2D4665;
                border-radius: 7px;
                padding: 8px 14px;
                color: #F1F6FD;
            }
            QPushButton:hover { background: #203551; }
            QPushButton:disabled { color: #65758B; background: #111A27; }
            QPushButton#PrimaryButton {
                background: #1A7390;
                border-color: #4AC7EF;
                font-weight: 650;
            }
            QPushButton#RecordButton {
                background: #9C3041;
                border-color: #E56B7B;
                font-weight: 700;
                min-width: 160px;
            }
            QLineEdit, QComboBox, QListWidget, QPlainTextEdit {
                background: #0B1421;
                border: 1px solid #293A52;
                border-radius: 7px;
                padding: 7px;
                selection-background-color: #216F8B;
            }
            QListWidget::item { padding: 7px; }
            QProgressBar {
                background: #0B1421;
                border: none;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background: #58D7FF;
                border-radius: 5px;
            }
            QSplitter::handle { background: #09101C; width: 10px; }
            """
        )

    def _initialize_media(self) -> None:
        try:
            self._ffmpeg_path = resolve_ffmpeg(self._config.ffmpeg_path)
            self._ffprobe_path = resolve_ffprobe(self._ffmpeg_path)
            self._set_status("Ready", "ready")
            self.detail_label.setText(f"Capture engine: {self._ffmpeg_path}")
        except MediaError as exc:
            self._set_status("FFmpeg missing", "error")
            self.detail_label.setText(str(exc))

    def _refresh_audio_devices(self) -> None:
        if self._is_recording or self._is_busy:
            return
        self.audio_combo.clear()
        try:
            self._audio_devices = list_loopback_devices()
        except Exception as exc:
            self._audio_devices = []
            self.audio_combo.addItem("No WASAPI loopback devices found", None)
            self._set_status("Audio unavailable", "error")
            self.detail_label.setText(str(exc))
            return

        default = next((item for item in self._audio_devices if item.is_default), None)
        if default:
            self.audio_combo.addItem(
                f"Follow Windows default — {default.name}",
                None,
            )
        else:
            self.audio_combo.addItem("Follow Windows default", None)
        for device in self._audio_devices:
            suffix = "  [current default]" if device.is_default else ""
            self.audio_combo.addItem(f"{device.name}{suffix}", device.index)
        if default:
            self.detail_label.setText(
                f"Windows default output detected: {default.name}. "
                "The meter will confirm signal after recording starts."
            )

    def _select_region(self) -> None:
        if self._is_recording or self._is_busy:
            return
        self.hide()
        QTimer.singleShot(120, self._selector.begin)

    def _on_region_selected(self, region: CaptureRegion) -> None:
        self._region = region
        self._playback_point = None
        self.region_label.setText(region.label())
        self.show()
        self.raise_()
        self.activateWindow()
        self._set_status("Area selected", "ready")
        self._sync_controls()

    def _use_primary_screen(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        from .region_selector import _physical_region

        self._on_region_selected(_physical_region(screen, screen.geometry()))

    def _toggle_recording(self) -> None:
        if (
            self._is_busy
            or self._selecting_playback_point
            or self._player_transition_pending
        ):
            return
        if self._is_recording:
            self._stop_recording()
        elif self._is_paused:
            self._resume_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        if self._region is None:
            self._set_status("Select an area first", "warning")
            self.detail_label.setText("Use Select Area or Use Primary Screen before recording.")
            return
        if self._ffmpeg_path is None or self._ffprobe_path is None:
            self._initialize_media()
            if self._ffmpeg_path is None:
                return

        self._playback_point = None
        self._selecting_playback_point = True
        self._set_status("Choose player control", "warning")
        self.detail_label.setText(
            "Choose one stable point on the video surface for synchronized "
            "play and pause."
        )
        region = self._region
        self.hide()
        QTimer.singleShot(100, lambda: self._playback_selector.begin(region))

    def _on_playback_point_selected(self, point: object) -> None:
        if (
            not isinstance(point, tuple)
            or len(point) != 2
            or self._region is None
        ):
            self._on_playback_point_cancelled()
            return
        self._selecting_playback_point = False
        self._playback_point = (int(point[0]), int(point[1]))
        self._begin_recording_after_playback_selection()

    def _on_playback_point_cancelled(self) -> None:
        self._selecting_playback_point = False
        self._playback_point = None
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._set_status("Recording start cancelled", "neutral")
        self.detail_label.setText(
            "No play/pause point was selected. Press Start Recording to try again."
        )
        self._sync_controls()

    def _begin_recording_after_playback_selection(self) -> None:
        if self._region is None or self._playback_point is None:
            self._on_playback_point_cancelled()
            return
        title = self.title_edit.text().strip() or "Untitled recording"
        self._selected_device_index = self.audio_combo.currentData()
        session = SessionManifest.create(
            self._config.recordings_dir,
            title,
            self._region,
            "Starting…",
            -1,
            0.0,
            0.0,
        )
        session.playback_toggle_x = self._playback_point[0]
        session.playback_toggle_y = self._playback_point[1]
        session.save()
        self._session = session
        if not self._start_session_segment():
            return
        self._fill_chapter_list()
        self._fill_anatomy_list()
        self._set_status("Recording", "recording")
        self._sync_controls()
        self._schedule_player_toggle()
        if self.anatomy_mode_checkbox.isChecked():
            self.detail_label.setText(
                "Recorder minimized. Ctrl+click anywhere inside the selected area "
                "to pause the player and annotate; press F8 to finish."
            )
            QTimer.singleShot(250, self.showMinimized)

    def _start_session_segment(self) -> bool:
        if (
            self._session is None
            or self._region is None
            or self._ffmpeg_path is None
        ):
            return False
        index = len(self._session.segments) + 1
        audio_recorder = LoopbackRecorder(self.audio_level_received.emit)
        screen_recorder = ScreenRecorder(
            self._ffmpeg_path,
            self._config.frame_rate,
            self._config.video_crf,
        )
        try:
            audio_info = audio_recorder.start(
                self._session.segment_raw_audio_path(index),
                self._selected_device_index,
            )
            video_info = screen_recorder.start(
                self._region,
                self._session.segment_screen_path(index),
            )
        except Exception as exc:
            screen_recorder.abort()
            audio_recorder.abort()
            self._session.state = "capture_failed"
            self._session.warnings.append(str(exc))
            self._session.save()
            self._set_status("Could not start", "error")
            self.detail_label.setText(str(exc))
            self.showNormal()
            self.raise_()
            return False

        self._session.audio_device_name = audio_info.device.name
        self._session.audio_device_index = audio_info.device.index
        self._current_segment = self._session.begin_segment(
            audio_info.started_monotonic,
            video_info.started_monotonic,
        )
        self._session.state = "recording"
        self._session.save()
        self._audio_recorder = audio_recorder
        self._screen_recorder = screen_recorder
        self._recording_started = video_info.started_monotonic
        self._is_recording = True
        self._is_paused = False
        self._capture_border.show(self._region)
        self._sync_ctrl_click_capture()
        self._set_status("Recording", "recording")
        self.detail_label.setText(f"Capturing system audio from {audio_info.device.name}")
        self._sync_controls()
        return True

    def _sync_ctrl_click_capture(self) -> None:
        self._hotkeys.set_period_capture_enabled(
            self._is_recording
            and not self._is_busy
            and not self._player_transition_pending
        )
        region = self._region
        if (
            self._is_recording
            and self.anatomy_mode_checkbox.isChecked()
            and region is not None
        ):
            self._hotkeys.set_ctrl_click_capture_region(
                (region.x, region.y, region.width, region.height)
            )
        else:
            self._hotkeys.set_ctrl_click_capture_region(None)

    def _schedule_player_toggle(
        self,
        after_click: Callable[[], None] | None = None,
    ) -> None:
        point = self._playback_point
        if point is None:
            if callable(after_click):
                after_click()
            return
        self._player_transition_pending = True
        self._sync_ctrl_click_capture()
        self._capture_border.set_busy(True)
        self._sync_controls()
        x, y = point
        QTimer.singleShot(60, lambda: move_pointer(x, y))
        QTimer.singleShot(
            220,
            lambda: self._click_player_and_continue(x, y, after_click),
        )

    def _click_player_and_continue(
        self,
        x: int,
        y: int,
        after_click: Callable[[], None] | None,
    ) -> None:
        if not self._player_transition_pending:
            return
        if control_key_is_down():
            QTimer.singleShot(
                50,
                lambda: self._click_player_and_continue(
                    x,
                    y,
                    after_click,
                ),
            )
            return
        try:
            replay_left_click(x, y)
        except Exception as exc:
            if self._session is not None:
                self._session.warnings.append(f"Player toggle click: {exc}")
                self._session.save()
        QTimer.singleShot(
            90,
            lambda: self._finish_player_toggle(after_click),
        )

    def _finish_player_toggle(
        self,
        after_click: Callable[[], None] | None,
    ) -> None:
        if not self._player_transition_pending:
            return
        self._player_transition_pending = False
        if callable(after_click):
            after_click()
            return
        self._sync_ctrl_click_capture()
        if self._is_recording or self._is_paused:
            self._capture_border.set_busy(False)
        self._sync_controls()

    def _request_segment_stop(self, purpose: str) -> None:
        if (
            not self._is_recording
            or self._is_busy
            or self._player_transition_pending
        ):
            return
        self._hotkeys.set_period_capture_enabled(False)
        self._hotkeys.set_ctrl_click_capture_region(None)
        self._schedule_player_toggle(
            lambda: self._stop_current_segment(purpose)
        )

    def _stop_recording(self) -> None:
        if self._is_paused:
            self._finalize_paused_recording()
        else:
            self._request_segment_stop("final")

    def _toggle_pause_recording(self) -> None:
        if self._is_busy:
            return
        if self._is_recording:
            self._request_segment_stop("pause")
        elif self._is_paused:
            self._resume_recording()

    def _resume_recording(self) -> None:
        if not self._is_paused or self._is_busy:
            return
        if self._start_session_segment():
            self._set_status("Recording", "recording")
            self.detail_label.setText("Recording resumed.")
            self._schedule_player_toggle()
            if self.anatomy_mode_checkbox.isChecked():
                self.showMinimized()

    def _finalize_paused_recording(self) -> None:
        if (
            not self._is_paused
            or self._session is None
            or self._ffmpeg_path is None
            or self._ffprobe_path is None
        ):
            return
        self._is_paused = False
        self._is_busy = True
        self._player_transition_pending = False
        self._hotkeys.set_period_capture_enabled(False)
        self._hotkeys.set_ctrl_click_capture_region(None)
        self._capture_border.hide()
        self._set_status("Finalizing", "busy")
        self._sync_controls()
        worker = StopSegmentWorker(
            self._session,
            None,
            "final",
            None,
            None,
            self._ffmpeg_path,
            self._ffprobe_path,
            self._config.transcription_audio_bitrate_kbps,
        )
        worker.progress.connect(self.detail_label.setText)
        worker.completed.connect(self._on_processing_complete)
        worker.failed.connect(self._on_processing_failed)
        worker.finished.connect(worker.deleteLater)
        self._stop_worker = worker
        worker.start()

    def _stop_current_segment(self, purpose: str) -> None:
        if (
            not self._is_recording
            or self._session is None
            or self._current_segment is None
            or self._screen_recorder is None
            or self._audio_recorder is None
            or self._ffmpeg_path is None
            or self._ffprobe_path is None
        ):
            return
        self._player_transition_pending = False
        self._hotkeys.set_period_capture_enabled(False)
        self._hotkeys.set_ctrl_click_capture_region(None)
        self._is_recording = False
        if purpose == "final":
            self._capture_border.hide()
        else:
            self._capture_border.set_paused(True)
            self._capture_border.set_busy(True)
        self._is_paused = purpose == "pause"
        self._is_busy = True
        self._set_status(
            (
                "Preparing annotation"
                if purpose == "anatomy"
                else ("Pausing" if purpose == "pause" else "Finalizing")
            ),
            "busy",
        )
        self._sync_controls()

        worker = StopSegmentWorker(
            self._session,
            self._current_segment,
            purpose,
            self._screen_recorder,
            self._audio_recorder,
            self._ffmpeg_path,
            self._ffprobe_path,
            self._config.transcription_audio_bitrate_kbps,
        )
        worker.progress.connect(self.detail_label.setText)
        worker.frame_ready.connect(self._on_anatomy_frame_ready)
        worker.completed.connect(self._on_processing_complete)
        worker.failed.connect(self._on_processing_failed)
        worker.finished.connect(worker.deleteLater)
        self._stop_worker = worker
        worker.start()

    def _on_processing_complete(self, payload: object) -> None:
        if not isinstance(payload, dict):
            self._on_processing_failed("Unexpected processing result.")
            return
        session = payload["session"]
        self._session = session
        self.timer_label.setText(format_duration(session.duration_seconds))
        if payload.get("purpose") == "pause":
            self._is_busy = False
            self._is_paused = True
            self._capture_border.set_paused(True)
            self._capture_border.set_busy(False)
            self._set_status("Paused", "warning")
            self.detail_label.setText(
                "Recording is paused. Use ▶ on the boundary to resume or ■ to save."
            )
            self._sync_controls()
            return
        if payload.get("purpose") == "anatomy":
            paused_frame = payload.get("paused_frame")
            if not isinstance(paused_frame, Path):
                self._on_processing_failed("Paused frame was not created.")
                return
            self._pending_paused_frame = paused_frame
            self._anatomy_segment_ready = True
            if self._annotation_finished:
                self._finish_anatomy_pause()
            return

        self._is_busy = False
        self._is_paused = False
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self._set_status("Saved", "ready")
        self.detail_label.setText(
            f"Saved video and audio in {session.folder}. "
            "The anatomy review and any requested Anki package are ready."
        )
        self._fill_anatomy_list()
        self._update_cost_label()
        self._sync_controls()

    def _on_processing_failed(self, message: str) -> None:
        self._is_busy = False
        self._is_paused = False
        self._player_transition_pending = False
        self._hotkeys.set_period_capture_enabled(False)
        self._hotkeys.set_ctrl_click_capture_region(None)
        self._study_paused = False
        self._capture_border.hide()
        if self._annotation_dialog.isVisible():
            self._annotation_dialog.reject()
        self.showNormal()
        self.raise_()
        self._set_status("Processing failed", "error")
        self.detail_label.setText(message)
        self._sync_controls()

    def _on_ctrl_click(self, x: int, y: int) -> None:
        region = self._region
        if (
            not self.anatomy_mode_checkbox.isChecked()
            or not self._is_recording
            or self._is_busy
            or self._player_transition_pending
            or region is None
            or not (
                region.x <= x < region.x + region.width
                and region.y <= y < region.y + region.height
            )
        ):
            return
        self._anatomy_pause((x, y))

    def _anatomy_pause(
        self,
        source_click: tuple[int, int] | None = None,
    ) -> None:
        if (
            not self._is_recording
            or self._is_busy
            or self._player_transition_pending
        ):
            return
        self._pending_source_click = source_click
        self._pending_paused_frame = None
        self._pending_annotation = None
        self._anatomy_segment_ready = False
        self._annotation_finished = False
        self._study_paused = True
        self._request_segment_stop("anatomy")

    def _on_anatomy_frame_ready(
        self,
        paused_frame: object,
        estimated_timestamp: float,
    ) -> None:
        if not isinstance(paused_frame, Path) or self._session is None:
            return
        self._pending_paused_frame = paused_frame
        self._set_status("Study paused", "warning")
        self._annotation_dialog.prepare(
            paused_frame,
            format_duration(estimated_timestamp),
            default_card_mode=True,
            post_mode=False,
        )
        self._annotation_dialog.showMaximized()
        self._annotation_dialog.raise_()
        self._annotation_dialog.activateWindow()

    def _on_annotation_finished(self, result: int) -> None:
        if not self._study_paused or self._session is None:
            return
        paused_frame = self._pending_paused_frame
        accepted = result == int(QDialog.DialogCode.Accepted)
        self._pending_annotation = None
        if accepted:
            index = len(self._session.anatomy_captures) + 1
            annotated_path = self._session.anatomy_annotated_path(index)
            edit_path = self._session.anatomy_edit_path(index)
            try:
                if paused_frame is None:
                    raise RuntimeError("The paused source frame is unavailable.")
                self._annotation_dialog.save_annotation(annotated_path, edit_path)
                self._pending_annotation = {
                    "original_path": paused_frame,
                    "annotated_path": annotated_path,
                    "edit_path": edit_path,
                    "label": self._annotation_dialog.label,
                    "create_anki_card": self._annotation_dialog.create_anki_card,
                }
            except Exception as exc:
                self._session.warnings.append(f"Annotation save: {exc}")
                self._session.save()
        self._annotation_finished = True
        if self._anatomy_segment_ready:
            self._finish_anatomy_pause()
        else:
            self._set_status("Finishing paused segment", "busy")

    def _finish_anatomy_pause(self) -> None:
        if self._session is None:
            return
        pending = self._pending_annotation
        if pending is not None:
            self._session.add_anatomy_capture(
                self._session.duration_seconds,
                pending["original_path"],
                pending["annotated_path"],
                str(pending["label"]),
                bool(pending["create_anki_card"]),
                self._pending_source_click,
                pending["edit_path"],
            )
            self._fill_anatomy_list()
        self._pending_paused_frame = None
        self._pending_annotation = None
        self._anatomy_segment_ready = False
        self._annotation_finished = False
        self._is_busy = False
        self._resume_after_annotation()

    def _resume_after_annotation(self) -> None:
        self._pending_source_click = None
        self._study_paused = False
        if not self._start_session_segment():
            return
        if self.anatomy_mode_checkbox.isChecked():
            self.showMinimized()
        self._schedule_player_toggle()

    def _add_chapter(self) -> None:
        if not self._is_recording or self._session is None:
            return
        elapsed = self._active_timeline_seconds()
        if self._session.chapters and elapsed - self._session.chapters[-1].start_seconds < 1.0:
            return
        chapter = self._session.add_chapter(elapsed)
        item = QListWidgetItem(
            f"{format_duration(chapter.start_seconds)}  •  {chapter.title}"
        )
        item.setData(Qt.ItemDataRole.UserRole, chapter.index)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.chapter_list.addItem(item)
        self.chapter_list.scrollToBottom()
        self._set_status(f"Added {chapter.title}", "recording")

    def _fill_chapter_list(self) -> None:
        self.chapter_list.blockSignals(True)
        self.chapter_list.clear()
        if self._session:
            for chapter in self._session.chapters:
                item = QListWidgetItem(
                    f"{format_duration(chapter.start_seconds)}  •  {chapter.title}"
                )
                item.setData(Qt.ItemDataRole.UserRole, chapter.index)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.chapter_list.addItem(item)
        self.chapter_list.blockSignals(False)

    def _on_chapter_renamed(self, item: QListWidgetItem) -> None:
        if self._session is None:
            return
        chapter_index = int(item.data(Qt.ItemDataRole.UserRole) or 0)
        chapter = next(
            (entry for entry in self._session.chapters if entry.index == chapter_index),
            None,
        )
        if chapter is None:
            return
        raw = item.text()
        title = raw.split("•", 1)[-1].strip() or f"Chapter {chapter.index}"
        chapter.title = title
        canonical = f"{format_duration(chapter.start_seconds)}  •  {chapter.title}"
        if item.text() != canonical:
            self.chapter_list.blockSignals(True)
            item.setText(canonical)
            self.chapter_list.blockSignals(False)
        self._session.save()

    def _fill_anatomy_list(self) -> None:
        self.anatomy_list.clear()
        if self._session is None:
            return
        for capture in self._session.anatomy_captures:
            label = capture.label or "Screenshot"
            suffix = "  •  Anki" if capture.create_anki_card else ""
            self.anatomy_list.addItem(
                f"{format_duration(capture.timestamp_seconds)}  •  {label}{suffix}"
            )

    def _edit_anatomy_captures(self) -> None:
        if (
            self._session is None
            or not self._session.anatomy_captures
            or self._is_recording
            or self._is_busy
        ):
            return
        AnatomyPostEditorDialog(self._session, self).exec()
        self._fill_anatomy_list()
        self._sync_controls()

    def _copy_codex_anki_prompt(self) -> None:
        if self._session is None or not self._session.anatomy_captures:
            return
        prompt = build_codex_anki_prompt(self._session)
        QApplication.clipboard().setText(prompt)
        prompt_path = save_codex_anki_prompt(self._session)
        self._set_status("Codex Anki prompt copied", "ready")
        self.detail_label.setText(
            "Paste the prompt into Codex. A durable copy was also saved at "
            f"{prompt_path.resolve()}."
        )

    def _transcribe(self) -> None:
        if self._is_busy or self._is_recording or self._session is None:
            return
        if not self._session.audio_path.is_file():
            self._set_status("Audio not ready", "warning")
            return
        model = str(self.model_combo.currentData())
        if (
            self._session.state == "transcription_failed"
            and self._session.transcription_model == model
        ):
            recovered = recover_completed_transcript(self._session)
            if recovered is not None:
                self._on_transcription_complete(recovered)
                self.detail_label.setText(
                    "Recovered the complete transcript already returned by the API; "
                    "no second request was sent."
                )
                return
        if not self._config.api_key:
            QMessageBox.information(
                self,
                "OpenAI API key needed",
                f"Recording works without a key.\n\nTo transcribe, add:\n"
                f"OPENAI_API_KEY=your-key\n\nto:\n{ENV_PATH}\n\n"
                "Then restart the app.",
            )
            return
        if self._ffmpeg_path is None or self._ffprobe_path is None:
            return

        self._session.transcription_model = model
        self._session.estimated_cost_usd = estimate_cost(
            model, self._session.duration_seconds
        )
        self._session.state = "transcribing"
        self._session.save()
        self._is_busy = True
        self._is_transcribing = True
        self._transcription_started = time.perf_counter()
        self._transcription_phase = "Preparing and validating the audio file"
        self.transcription_progress_frame.setStyleSheet("")
        self.transcription_progress_title.setText("Transcribing audio…")
        self.transcription_progress_bar.setRange(0, 0)
        self.transcription_progress_bar.show()
        self.transcription_elapsed_label.setText("00:00 elapsed")
        self.transcription_phase_label.setText(
            "Preparing transcription request. Long recordings can take several minutes."
        )
        self.transcription_progress_frame.show()
        self._set_status("Transcribing", "busy")
        self._sync_controls()

        worker = TranscriptionWorker(
            self._session,
            self._config.api_key,
            model,
            self._config.transcription_prompt,
            self._ffmpeg_path,
            self._ffprobe_path,
            self._config.transcription_audio_bitrate_kbps,
        )
        worker.progress.connect(self._on_transcription_progress)
        worker.completed.connect(self._on_transcription_complete)
        worker.failed.connect(self._on_transcription_failed)
        worker.finished.connect(worker.deleteLater)
        self._transcription_worker = worker
        worker.start()

    def _on_transcription_progress(self, message: str, current: int, total: int) -> None:
        self._transcription_phase = f"{message} — request {current} of {total}"
        self.transcription_phase_label.setText(
            f"{self._transcription_phase}. Waiting for OpenAI to return the text…"
        )
        self.detail_label.setText(self._transcription_phase)

    def _on_transcription_complete(self, result: object) -> None:
        self._is_busy = False
        self._is_transcribing = False
        markdown = getattr(result, "markdown", "")
        self.transcript_edit.setPlainText(markdown)
        self.transcription_progress_bar.setRange(0, 1)
        self.transcription_progress_bar.setValue(1)
        self.transcription_progress_title.setText("Transcript ready")
        self.transcription_phase_label.setText(
            "The transcript and its metadata were saved in the session folder."
        )
        self._set_status("Transcript ready", "ready")
        actual = getattr(result, "actual_cost_usd", None)
        if actual is None:
            self.detail_label.setText(
                "Transcript saved. The API response did not include enough usage data "
                "to calculate exact cost."
            )
        else:
            self.detail_label.setText(
                f"Transcript saved. Calculated API cost: ${actual:.4f}."
            )
        self._update_cost_label()
        self._sync_controls()
        QTimer.singleShot(
            2200,
            lambda: (
                self.transcription_progress_frame.hide()
                if not self._is_transcribing
                else None
            ),
        )

    def _on_transcription_failed(self, message: str) -> None:
        self._is_busy = False
        self._is_transcribing = False
        self.transcription_progress_bar.hide()
        self.transcription_progress_title.setText("Transcription failed")
        self.transcription_phase_label.setText(
            f"{message} A detailed report was saved as transcription-error.txt."
        )
        self.transcription_progress_frame.setStyleSheet(
            "QFrame#ProgressCard { background:#351B22; border:1px solid #B94A5C; "
            "border-radius:9px; }"
        )
        self._set_status("Transcription failed", "error")
        self.detail_label.setText(message)
        self._sync_controls()

    def _update_cost_label(self) -> None:
        if self._session is None or self._session.duration_seconds <= 0:
            self.cost_label.setText("Record something to estimate transcription cost.")
            return
        model = str(self.model_combo.currentData())
        estimate = estimate_cost(model, self._session.duration_seconds)
        if self._session.actual_cost_usd is not None and self._session.transcription_model == model:
            self.cost_label.setText(
                f"Actual ${self._session.actual_cost_usd:.4f}  •  "
                f"preflight estimate was ${estimate:.4f}"
            )
        else:
            self.cost_label.setText(
                f"Estimated API cost ≈ ${estimate:.4f} "
                f"for {format_duration(self._session.duration_seconds)}"
            )

    def _copy_transcript(self) -> None:
        text = self.transcript_edit.toPlainText().strip()
        if not text:
            return
        QApplication.clipboard().setText(text)
        self._set_status("Copied transcript", "ready")

    def _open_session_folder(self) -> None:
        folder = self._session.folder if self._session else self._config.recordings_dir
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _show_session_library(self) -> None:
        if self._is_recording or self._is_busy:
            return
        roots = [self._config.recordings_dir, APP_DIR / "recordings"]
        dialog = SessionLibraryDialog(roots, self)
        result = dialog.exec()
        if (
            self._session is not None
            and self._session.folder.resolve() in dialog.deleted_folders
        ):
            self._session = None
            self.chapter_list.clear()
            self.anatomy_list.clear()
            self.transcript_edit.clear()
            self.timer_label.setText("00:00")
            self.detail_label.setText(
                "The loaded past session was permanently deleted."
            )
            self._set_status("Session deleted", "ready")
            self._update_cost_label()
            self._sync_controls()
        if result != QDialog.DialogCode.Accepted:
            return
        session = dialog.selected_session
        if session is not None:
            self._load_past_session(session)

    def _load_past_session(self, session: SessionManifest) -> None:
        self._session = session
        self._region = session.region
        self.title_edit.setText(session.title)
        self.region_label.setText(session.region.label())
        self.timer_label.setText(format_duration(session.duration_seconds))
        self._fill_chapter_list()
        self._fill_anatomy_list()

        if session.transcript_markdown_path.is_file():
            self.transcript_edit.setPlainText(
                session.transcript_markdown_path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )
        else:
            self.transcript_edit.clear()
        if session.transcription_model:
            index = self.model_combo.findData(session.transcription_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)

        self._set_status("Past session loaded", "ready")
        review_text = (
            "Review Anatomy opens the timestamped gallery directly."
            if session.review_path.is_file()
            else "This session does not contain a completed anatomy review."
        )
        self.detail_label.setText(
            f"Loaded {session.folder.name}. {review_text}"
        )
        self._update_cost_label()
        self._sync_controls()

    def _open_anatomy_review(self) -> None:
        if self._session is None or not self._session.review_path.is_file():
            return
        build_anatomy_review(self._session)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._session.review_path.resolve())))

    def _active_timeline_seconds(self) -> float:
        completed = self._session.duration_seconds if self._session else 0.0
        if not self._is_recording:
            return completed
        return completed + max(0.0, time.perf_counter() - self._recording_started)

    def _tick(self) -> None:
        self._audio_level *= 0.72
        self.audio_meter.setValue(round(self._audio_level * 100))
        if self._is_transcribing:
            elapsed = max(0.0, time.perf_counter() - self._transcription_started)
            self.transcription_elapsed_label.setText(
                f"{format_duration(elapsed)} elapsed"
            )
            dots = "." * (int(elapsed * 1.6) % 4)
            self.transcription_progress_title.setText(
                f"Transcribing audio{dots}"
            )
        if not self._is_recording:
            return
        elapsed = self._active_timeline_seconds()
        self.timer_label.setText(format_duration(elapsed))
        if (
            self._audio_recorder is not None
            and time.perf_counter() - self._recording_started > 4
            and self._audio_recorder.seconds_since_audio_callback > 4
        ):
            self.detail_label.setText(
                "No system-audio packets detected recently. If something is playing, "
                "stop and refresh the audio device."
            )

    def _on_audio_level(self, level: float) -> None:
        self._audio_level = max(self._audio_level, min(1.0, level))

    def _set_status(self, text: str, state: str) -> None:
        colors = {
            "ready": ("#17392F", "#7CE5B2"),
            "recording": ("#55202A", "#FF94A4"),
            "busy": ("#17364A", "#70D9FF"),
            "warning": ("#503C18", "#FFD47B"),
            "error": ("#4B2026", "#FF929D"),
            "neutral": ("#17273A", "#A9E9FF"),
        }
        background, foreground = colors.get(state, colors["neutral"])
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            f"background:{background}; color:{foreground}; "
            "border-radius:11px; padding:6px 12px; font-weight:650;"
        )

    def _sync_controls(self) -> None:
        media_available = self._ffmpeg_path is not None
        session_active = self._is_recording or self._is_paused
        interaction_busy = self._is_busy or self._player_transition_pending
        self.select_region_button.setEnabled(not session_active and not interaction_busy)
        self.full_screen_button.setEnabled(not session_active and not interaction_busy)
        self.refresh_audio_button.setEnabled(not session_active and not interaction_busy)
        self.audio_combo.setEnabled(not session_active and not interaction_busy)
        self.title_edit.setEnabled(not session_active and not interaction_busy)
        self.anatomy_mode_checkbox.setEnabled(
            not session_active and not interaction_busy and not self._study_paused
        )
        self.record_button.setEnabled(not interaction_busy and media_available)
        if self._is_recording:
            self.record_button.setText("■  Stop Recording")
        elif self._is_paused:
            self.record_button.setText("▶  Resume Recording")
        else:
            self.record_button.setText("●  Start Recording")
        self.chapter_button.setEnabled(self._is_recording and not interaction_busy)
        self.anatomy_button.setEnabled(self._is_recording and not interaction_busy)
        self.edit_anatomy_button.setEnabled(
            self._session is not None
            and bool(self._session.anatomy_captures)
            and not session_active
            and not self._is_busy
        )
        self.copy_codex_anki_button.setEnabled(
            self._session is not None
            and bool(self._session.anatomy_captures)
            and not session_active
            and not self._is_busy
        )
        transcript_ready = bool(
            self._session
            and self._session.transcript_markdown_path.is_file()
            and self.transcript_edit.toPlainText().strip()
        )
        ready_to_transcribe = (
            self._session is not None
            and self._session.audio_path.is_file()
            and not transcript_ready
            and not session_active
            and not self._is_busy
        )
        self.transcribe_button.setEnabled(ready_to_transcribe)
        self.transcribe_button.setText(
            "Transcribing…"
            if self._is_transcribing
            else ("Transcript Ready" if transcript_ready else "Transcribe")
        )
        self.model_combo.setEnabled(not self._is_busy and not session_active)
        self.copy_button.setEnabled(bool(self.transcript_edit.toPlainText().strip()))
        self.open_folder_button.setEnabled(not session_active)
        self.open_review_button.setEnabled(
            self._session is not None
            and self._session.review_path.is_file()
            and not self._is_busy
        )
        self.past_sessions_button.setEnabled(
            not session_active and not self._is_busy
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._is_recording or self._is_paused:
            QMessageBox.warning(
                self,
                "Recording is active",
                "Stop the recording and wait for it to finish saving before closing.",
            )
            event.ignore()
            return
        if self._is_busy:
            QMessageBox.information(
                self,
                "Work in progress",
                "Please wait for processing or transcription to finish.",
            )
            event.ignore()
            return
        self._hotkeys.stop()
        self._capture_border.hide()
        event.accept()
