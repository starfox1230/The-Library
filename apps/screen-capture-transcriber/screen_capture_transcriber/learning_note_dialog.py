from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .learning_note_preferences import (
    MAX_TEXT_SIZE_POINTS,
    MIN_TEXT_SIZE_POINTS,
    TEXT_SIZE_STEP_POINTS,
    load_learning_note_preferences,
    normalize_text_size,
    save_learning_note_preferences,
)
from .models import format_duration


class LearningNoteDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
        preferences_path: Path | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Timestamped Learning Note")
        self.resize(980, 560)
        self.setMinimumSize(720, 420)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._timestamp_seconds = 0.0
        self._preferences_path = preferences_path
        self._preferences = load_learning_note_preferences(preferences_path)
        self._build_ui()
        self._apply_text_size(self._preferences.text_size_points, persist=False)

    @property
    def note_text(self) -> str:
        return self.note_edit.toPlainText().strip()

    @property
    def timestamp_seconds(self) -> float:
        return self._timestamp_seconds

    def prepare(
        self,
        timestamp_seconds: float,
        transcript_context: str,
    ) -> None:
        self._timestamp_seconds = max(0.0, float(timestamp_seconds))
        self.timestamp_label.setText(
            f"Learning note at {format_duration(self._timestamp_seconds)}"
        )
        self.note_edit.clear()
        self.context_edit.setPlainText(
            transcript_context.strip()
            or "No timestamped transcript context is available for this video."
        )
        self.save_button.setEnabled(False)
        QTimer.singleShot(0, self._focus_note)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        self.timestamp_label = QLabel("Learning note")
        self.timestamp_label.setObjectName("Title")
        layout.addWidget(self.timestamp_label)

        text_size_row = QHBoxLayout()
        text_size_row.addStretch()
        text_size_row.addWidget(QLabel("Editor text size"))
        self.decrease_text_size_button = QPushButton("-")
        self.decrease_text_size_button.setAccessibleName("Decrease editor text size")
        self.decrease_text_size_button.setFixedWidth(38)
        self.decrease_text_size_button.clicked.connect(
            lambda: self._change_text_size(-TEXT_SIZE_STEP_POINTS)
        )
        self.text_size_label = QLabel("")
        self.text_size_label.setObjectName("TextSize")
        self.text_size_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_size_label.setMinimumWidth(46)
        self.increase_text_size_button = QPushButton("+")
        self.increase_text_size_button.setAccessibleName("Increase editor text size")
        self.increase_text_size_button.setFixedWidth(38)
        self.increase_text_size_button.clicked.connect(
            lambda: self._change_text_size(TEXT_SIZE_STEP_POINTS)
        )
        text_size_row.addWidget(self.decrease_text_size_button)
        text_size_row.addWidget(self.text_size_label)
        text_size_row.addWidget(self.increase_text_size_button)
        layout.addLayout(text_size_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        note_frame = QFrame()
        note_frame.setObjectName("Card")
        note_layout = QVBoxLayout(note_frame)
        note_layout.setContentsMargins(12, 12, 12, 12)
        note_layout.addWidget(QLabel("What do you want to remember?"))
        self.note_edit = QPlainTextEdit()
        self.note_edit.installEventFilter(self)
        self.note_edit.setPlaceholderText(
            "Write the principle, relationship, fact, or distinction in your own words…"
        )
        self.note_edit.textChanged.connect(
            lambda: self.save_button.setEnabled(bool(self.note_text))
        )
        note_layout.addWidget(self.note_edit, 1)
        splitter.addWidget(note_frame)

        context_frame = QFrame()
        context_frame.setObjectName("Card")
        context_layout = QVBoxLayout(context_frame)
        context_layout.setContentsMargins(12, 12, 12, 12)
        context_layout.addWidget(QLabel("Nearby transcript"))
        self.context_edit = QPlainTextEdit()
        self.context_edit.setReadOnly(True)
        context_layout.addWidget(self.context_edit, 1)
        splitter.addWidget(context_frame)
        splitter.setSizes([560, 400])
        layout.addWidget(splitter, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        self.save_button = QPushButton("Save Note")
        self.save_button.setObjectName("PrimaryButton")
        self.save_button.clicked.connect(self.accept)
        actions.addWidget(cancel_button)
        actions.addWidget(self.save_button)
        layout.addLayout(actions)

        self.setStyleSheet(
            """
            QDialog, QWidget {
                background:#09101C; color:#EEF4FC;
                font-family:"Segoe UI"; font-size:10pt;
            }
            QLabel#Title { font-size:18pt; font-weight:700; }
            QLabel#TextSize { color:#9EB0C8; font-weight:700; }
            QFrame#Card {
                background:#101B2B; border:1px solid #26364D;
                border-radius:9px;
            }
            QPlainTextEdit {
                background:#07101B; border:1px solid #2B405A;
                border-radius:7px; padding:9px; selection-background-color:#1A7390;
            }
            QPushButton {
                background:#17273A; border:1px solid #36516F;
                border-radius:7px; padding:9px 15px;
            }
            QPushButton:hover { background:#203551; }
            QPushButton:disabled { color:#65758B; background:#111A27; }
            QPushButton#PrimaryButton {
                background:#1A7390; border-color:#58D7FF; font-weight:700;
            }
            """
        )

    @property
    def text_size_points(self) -> int:
        return self._preferences.text_size_points

    def _change_text_size(self, delta: int) -> None:
        self._apply_text_size(self.text_size_points + delta, persist=True)

    def _apply_text_size(self, value: int, *, persist: bool) -> None:
        size = normalize_text_size(value)
        self._preferences.text_size_points = size
        editor_style = f"font-size:{size}pt;"
        self.note_edit.setStyleSheet(editor_style)
        self.context_edit.setStyleSheet(editor_style)
        self.text_size_label.setText(f"{size} pt")
        self.decrease_text_size_button.setEnabled(size > MIN_TEXT_SIZE_POINTS)
        self.increase_text_size_button.setEnabled(size < MAX_TEXT_SIZE_POINTS)
        if persist:
            try:
                save_learning_note_preferences(
                    self._preferences,
                    self._preferences_path,
                )
            except OSError:
                pass

    def _focus_note(self) -> None:
        self.note_edit.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
        self.note_edit.moveCursor(QTextCursor.MoveOperation.End)

    def eventFilter(self, watched: object, event: QEvent) -> bool:
        if (
            watched is self.note_edit
            and event.type() == QEvent.Type.KeyPress
            and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.accept()
            return True
        return super().eventFilter(watched, event)

    def accept(self) -> None:
        if not self.note_text:
            self.note_edit.setFocus(Qt.FocusReason.ActiveWindowFocusReason)
            return
        super().accept()
