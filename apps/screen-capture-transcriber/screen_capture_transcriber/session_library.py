from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .codex_prompt import build_codex_anki_prompt, save_codex_anki_prompt
from .models import SessionManifest, format_duration
from .post_editor import AnatomyPostEditorDialog
from .review import build_anatomy_review


@dataclass(frozen=True)
class SessionEntry:
    manifest_path: Path
    session: SessionManifest
    modified_at: float


def discover_sessions(roots: list[Path]) -> tuple[list[SessionEntry], list[str]]:
    entries: list[SessionEntry] = []
    errors: list[str] = []
    seen: set[Path] = set()
    for root in roots:
        root = root.resolve()
        if root in seen or not root.is_dir():
            continue
        seen.add(root)
        for manifest_path in root.glob("*/session.json"):
            try:
                session = SessionManifest.load(manifest_path)
                if session.title.casefold().endswith("e2e"):
                    continue
                entries.append(
                    SessionEntry(
                        manifest_path=manifest_path,
                        session=session,
                        modified_at=manifest_path.stat().st_mtime,
                    )
                )
            except Exception as exc:
                errors.append(f"{manifest_path.parent.name}: {exc}")
    entries.sort(key=lambda entry: entry.modified_at, reverse=True)
    return entries, errors


class SessionLibraryDialog(QDialog):
    def __init__(self, roots: list[Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Past Sessions")
        self.resize(1040, 650)
        self.setMinimumSize(850, 520)
        self._entries, self._errors = discover_sessions(roots)
        self._selected: SessionEntry | None = None
        self._items: list[tuple[QTreeWidgetItem, SessionEntry]] = []
        self._build_ui()
        self._populate()

    @property
    def selected_session(self) -> SessionManifest | None:
        return self._selected.session if self._selected else None

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        title = QLabel("Past Sessions")
        title.setObjectName("LibraryTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Search previous recordings, open their study materials directly, "
            "or load one into the main window."
        )
        subtitle.setObjectName("Muted")
        layout.addWidget(subtitle)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search by title, date, state, or transcript status…"
        )
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.textChanged.connect(self._apply_filter)
        layout.addWidget(self.search_edit)

        body = QHBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(
            ["Date", "Title", "Duration", "Anatomy", "Transcript", "State"]
        )
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(lambda *_args: self._load_selected())
        self.tree.setColumnWidth(0, 130)
        self.tree.setColumnWidth(1, 175)
        self.tree.setColumnWidth(2, 72)
        self.tree.setColumnWidth(3, 65)
        self.tree.setColumnWidth(4, 78)
        self.tree.setColumnWidth(5, 88)
        self.tree.setColumnWidth(4, 90)
        body.addWidget(self.tree, 3)

        details = QFrame()
        details.setObjectName("LibraryDetails")
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(16, 16, 16, 16)
        self.detail_title = QLabel("Select a session")
        self.detail_title.setObjectName("DetailTitle")
        self.detail_title.setWordWrap(True)
        details_layout.addWidget(self.detail_title)
        self.detail_meta = QLabel("")
        self.detail_meta.setObjectName("Muted")
        self.detail_meta.setWordWrap(True)
        details_layout.addWidget(self.detail_meta)
        self.detail_summary = QLabel(
            "The direct buttons avoid opening File Explorer."
        )
        self.detail_summary.setWordWrap(True)
        details_layout.addWidget(self.detail_summary)
        details_layout.addStretch()

        self.review_button = QPushButton("Review Anatomy")
        self.edit_anatomy_button = QPushButton("Edit Anatomy Screenshots")
        self.copy_codex_anki_button = QPushButton("Copy Codex Anki Prompt")
        self.play_button = QPushButton("Play Recording")
        self.transcript_button = QPushButton("Open Transcript")
        self.folder_button = QPushButton("Open Folder in Explorer")
        self.load_button = QPushButton("Load in Main Window")
        self.load_button.setObjectName("PrimaryButton")
        self.review_button.clicked.connect(self._open_review)
        self.edit_anatomy_button.clicked.connect(self._edit_anatomy)
        self.copy_codex_anki_button.clicked.connect(self._copy_codex_anki_prompt)
        self.play_button.clicked.connect(self._play_recording)
        self.transcript_button.clicked.connect(self._open_transcript)
        self.folder_button.clicked.connect(self._open_folder)
        self.load_button.clicked.connect(self._load_selected)
        for button in (
            self.review_button,
            self.edit_anatomy_button,
            self.copy_codex_anki_button,
            self.play_button,
            self.transcript_button,
            self.folder_button,
            self.load_button,
        ):
            details_layout.addWidget(button)
        body.addWidget(details, 2)
        layout.addLayout(body, 1)

        footer = QHBoxLayout()
        error_suffix = (
            f" • {len(self._errors)} unreadable session(s)" if self._errors else ""
        )
        self.count_label = QLabel(f"{len(self._entries)} sessions{error_suffix}")
        self.count_label.setObjectName("Muted")
        footer.addWidget(self.count_label)
        footer.addStretch()
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.reject)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        self.setStyleSheet(
            """
            QDialog, QWidget { background:#09101C; color:#EEF4FC;
                               font-family:"Segoe UI"; font-size:10pt; }
            QLabel#LibraryTitle { font-size:22pt; font-weight:700; }
            QLabel#DetailTitle { font-size:15pt; font-weight:700; }
            QLabel#Muted { color:#9EB0C8; }
            QFrame#LibraryDetails { background:#101B2B; border:1px solid #26364D;
                                    border-radius:10px; }
            QLineEdit, QTreeWidget { background:#0B1421; border:1px solid #293A52;
                                     border-radius:7px; padding:7px; }
            QTreeWidget::item { padding:7px 4px; }
            QTreeWidget::item:selected { background:#216F8B; }
            QHeaderView::section { background:#17273A; color:#C8D6E8; padding:7px;
                                   border:0; border-right:1px solid #26364D; }
            QPushButton { background:#17273A; border:1px solid #36516F;
                          border-radius:7px; padding:9px 12px; }
            QPushButton:hover { background:#203551; }
            QPushButton:disabled { color:#65758B; background:#111A27; }
            QPushButton#PrimaryButton { background:#1A7390; border-color:#58D7FF;
                                        font-weight:700; }
            """
        )
        self._sync_buttons()

    def _populate(self) -> None:
        for entry in self._entries:
            session = entry.session
            try:
                created = datetime.fromisoformat(session.created_at).astimezone()
                date_label = created.strftime("%b %d, %Y %I:%M %p")
            except ValueError:
                date_label = session.folder.name[:19].replace("_", " ")
            transcript = "Ready" if session.transcript_markdown_path.is_file() else "—"
            item = QTreeWidgetItem(
                [
                    date_label,
                    session.title,
                    format_duration(session.duration_seconds),
                    str(len(session.anatomy_captures)),
                    transcript,
                    session.state.replace("_", " ").title(),
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, str(entry.manifest_path))
            self.tree.addTopLevelItem(item)
            self._items.append((item, entry))
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _apply_filter(self, text: str) -> None:
        query = text.strip().casefold()
        visible = 0
        for item, entry in self._items:
            session = entry.session
            haystack = " ".join(
                [
                    session.title,
                    session.created_at,
                    session.state,
                    "transcript" if session.transcript_markdown_path.is_file() else "",
                    "anatomy" if session.anatomy_captures else "",
                ]
            ).casefold()
            hidden = bool(query and query not in haystack)
            item.setHidden(hidden)
            visible += not hidden
        self.count_label.setText(
            f"{visible} of {len(self._entries)} sessions"
            + (f" • {len(self._errors)} unreadable" if self._errors else "")
        )

    def _on_selection_changed(
        self,
        current: QTreeWidgetItem | None,
        _previous: QTreeWidgetItem | None,
    ) -> None:
        self._selected = next(
            (entry for item, entry in self._items if item is current),
            None,
        )
        if self._selected is None:
            self.detail_title.setText("Select a session")
            self.detail_meta.clear()
            self._sync_buttons()
            return
        session = self._selected.session
        self.detail_title.setText(session.title)
        self.detail_meta.setText(
            f"{format_duration(session.duration_seconds)} recording\n"
            f"{len(session.chapters)} chapter(s) • "
            f"{len(session.anatomy_captures)} anatomy capture(s)\n"
            f"Status: {session.state.replace('_', ' ')}"
        )
        transcript = (
            "Transcript is ready."
            if session.transcript_markdown_path.is_file()
            else "No completed transcript."
        )
        review = (
            "Anatomy review is ready and remembers playback position."
            if session.review_path.is_file()
            else "No anatomy review is available."
        )
        self.detail_summary.setText(f"{review}\n\n{transcript}")
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        session = self._selected.session if self._selected else None
        self.review_button.setEnabled(bool(session and session.review_path.is_file()))
        self.edit_anatomy_button.setEnabled(
            bool(session and session.anatomy_captures)
        )
        self.copy_codex_anki_button.setEnabled(
            bool(session and session.anatomy_captures)
        )
        self.play_button.setEnabled(
            bool(
                session
                and (
                    session.playback_path.is_file()
                    or session.recording_path.is_file()
                )
            )
        )
        self.transcript_button.setEnabled(
            bool(session and session.transcript_markdown_path.is_file())
        )
        self.folder_button.setEnabled(bool(session and session.folder.is_dir()))
        self.load_button.setEnabled(session is not None)

    def _open_review(self) -> None:
        if self._selected:
            build_anatomy_review(self._selected.session)
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._selected.session.review_path.resolve()))
            )

    def _play_recording(self) -> None:
        if not self._selected:
            return
        session = self._selected.session
        path = (
            session.playback_path
            if session.playback_path.is_file()
            else session.recording_path
        )
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def _edit_anatomy(self) -> None:
        if not self._selected:
            return
        AnatomyPostEditorDialog(self._selected.session, self).exec()
        self._on_selection_changed(self.tree.currentItem(), None)

    def _copy_codex_anki_prompt(self) -> None:
        if not self._selected:
            return
        session = self._selected.session
        prompt = build_codex_anki_prompt(session)
        QApplication.clipboard().setText(prompt)
        prompt_path = save_codex_anki_prompt(session)
        self.detail_summary.setText(
            "Codex Anki prompt copied to the clipboard.\n\n"
            f"A durable copy was saved as {prompt_path.name}."
        )

    def _open_transcript(self) -> None:
        if self._selected:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(
                    str(self._selected.session.transcript_markdown_path.resolve())
                )
            )

    def _open_folder(self) -> None:
        if self._selected:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._selected.session.folder.resolve()))
            )

    def _load_selected(self) -> None:
        if self._selected:
            self.accept()
