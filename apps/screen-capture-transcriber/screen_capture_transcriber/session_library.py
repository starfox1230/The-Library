from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import shutil

from PySide6.QtCore import Qt, QUrl, QUrlQuery
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .codex_prompt import build_codex_anki_prompt, save_codex_anki_prompt
from .learning_notes import (
    note_display_timestamp,
    read_transcript,
    render_transcript_with_notes,
)
from .models import SessionManifest, format_duration
from .post_editor import AnatomyPostEditorDialog
from .review import build_anatomy_review


@dataclass(frozen=True)
class SessionEntry:
    manifest_path: Path
    session: SessionManifest
    modified_at: float
    total_size_bytes: int


def session_folder_size(folder: Path) -> int:
    """Return the combined size of all regular files below a session folder."""
    total = 0
    pending = [Path(folder)]
    while pending:
        current = pending.pop()
        try:
            with os.scandir(current) as entries:
                for entry in entries:
                    try:
                        if entry.is_file(follow_symlinks=False):
                            total += entry.stat(follow_symlinks=False).st_size
                        elif entry.is_dir(follow_symlinks=False):
                            pending.append(Path(entry.path))
                    except OSError:
                        continue
        except OSError:
            continue
    return total


def format_file_size(size_bytes: int) -> str:
    size = float(max(0, size_bytes))
    if size < 1024:
        return f"{int(size)} B"
    for unit in ("KB", "MB", "GB", "TB"):
        size /= 1024
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
    return f"{size:.1f} TB"


def delete_session_folder(session_folder: Path, allowed_roots: list[Path]) -> None:
    """Permanently remove one validated session folder and all of its contents."""
    candidate = Path(session_folder)
    if candidate.is_symlink():
        raise ValueError("Refusing to delete a session through a symbolic link.")

    folder = candidate.resolve(strict=True)
    roots = {Path(root).resolve() for root in allowed_roots}
    if folder.parent not in roots:
        raise ValueError(
            "The selected folder is not a direct child of a configured recordings folder."
        )
    if not folder.is_dir():
        raise ValueError("The selected session folder is not a directory.")
    if not (folder / "session.json").is_file():
        raise ValueError("The selected folder does not contain a session manifest.")

    shutil.rmtree(folder)


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
                        total_size_bytes=session_folder_size(manifest_path.parent),
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
        self.resize(1260, 820)
        self.setMinimumSize(1000, 680)
        self._roots = list(dict.fromkeys(Path(root).resolve() for root in roots))
        self._deleted_folders: set[Path] = set()
        self._entries, self._errors = discover_sessions(roots)
        self._selected: SessionEntry | None = None
        self._items: list[tuple[QTreeWidgetItem, SessionEntry]] = []
        self._build_ui()
        self._populate()

    @property
    def selected_session(self) -> SessionManifest | None:
        return self._selected.session if self._selected else None

    @property
    def deleted_folders(self) -> frozenset[Path]:
        return frozenset(self._deleted_folders)

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
        self.tree.setColumnCount(8)
        self.tree.setHeaderLabels(
            [
                "Date",
                "Title",
                "Duration",
                "Size",
                "Anatomy",
                "Notes",
                "Transcript",
                "State",
            ]
        )
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.currentItemChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(lambda *_args: self._load_selected())
        self.tree.setColumnWidth(0, 130)
        self.tree.setColumnWidth(1, 175)
        self.tree.setColumnWidth(2, 72)
        self.tree.setColumnWidth(3, 76)
        self.tree.setColumnWidth(4, 65)
        self.tree.setColumnWidth(5, 60)
        self.tree.setColumnWidth(6, 90)
        self.tree.setColumnWidth(7, 88)
        body.addWidget(self.tree, 4)

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

        self.review_button = QPushButton("Review Session")
        self.edit_anatomy_button = QPushButton("Edit Anatomy Screenshots")
        self.copy_codex_anki_button = QPushButton("Copy Codex Anki Prompt")
        self.play_button = QPushButton("Play Recording")
        self.transcript_button = QPushButton("Open Transcript")
        self.folder_button = QPushButton("Open Folder in Explorer")
        self.delete_button = QPushButton("Delete Session…")
        self.delete_button.setObjectName("DangerButton")
        self.load_button = QPushButton("Load in Main Window")
        self.load_button.setObjectName("PrimaryButton")
        self.review_button.clicked.connect(self._open_review)
        self.edit_anatomy_button.clicked.connect(self._edit_anatomy)
        self.copy_codex_anki_button.clicked.connect(self._copy_codex_anki_prompt)
        self.play_button.clicked.connect(self._play_recording)
        self.transcript_button.clicked.connect(self._open_transcript)
        self.folder_button.clicked.connect(self._open_folder)
        self.delete_button.clicked.connect(self._delete_selected)
        self.load_button.clicked.connect(self._load_selected)
        for button in (
            self.review_button,
            self.edit_anatomy_button,
            self.copy_codex_anki_button,
            self.play_button,
            self.transcript_button,
            self.folder_button,
            self.delete_button,
            self.load_button,
        ):
            details_layout.addWidget(button)
        body.addWidget(details, 2)
        layout.addLayout(body, 1)

        notes_frame = QFrame()
        notes_frame.setObjectName("LibraryDetails")
        notes_layout = QHBoxLayout(notes_frame)
        notes_layout.setContentsMargins(14, 12, 14, 12)
        notes_layout.setSpacing(12)

        notes_list_column = QVBoxLayout()
        notes_list_column.addWidget(QLabel("Timestamped Learning Notes"))
        self.notes_list = QListWidget()
        self.notes_list.currentItemChanged.connect(self._on_note_selected)
        notes_list_column.addWidget(self.notes_list, 1)
        notes_layout.addLayout(notes_list_column, 2)

        note_editor_column = QVBoxLayout()
        self.note_edit = QPlainTextEdit()
        self.note_edit.setPlaceholderText("Select a learning note to edit it.")
        note_editor_column.addWidget(self.note_edit, 1)
        note_actions = QHBoxLayout()
        self.save_note_button = QPushButton("Save Edit")
        self.delete_note_button = QPushButton("Delete Note…")
        self.copy_note_button = QPushButton("Copy Note")
        self.open_note_button = QPushButton("Open at Timestamp")
        self.save_note_button.clicked.connect(self._save_note_edit)
        self.delete_note_button.clicked.connect(self._delete_note)
        self.copy_note_button.clicked.connect(self._copy_note)
        self.open_note_button.clicked.connect(self._open_note_timestamp)
        for button in (
            self.save_note_button,
            self.delete_note_button,
            self.copy_note_button,
            self.open_note_button,
        ):
            note_actions.addWidget(button)
        note_editor_column.addLayout(note_actions)
        copy_actions = QHBoxLayout()
        self.copy_transcript_button = QPushButton("Copy Transcript")
        self.copy_transcript_notes_button = QPushButton(
            "Copy Transcript + Notes"
        )
        self.copy_transcript_button.clicked.connect(self._copy_transcript)
        self.copy_transcript_notes_button.clicked.connect(
            self._copy_transcript_and_notes
        )
        copy_actions.addWidget(self.copy_transcript_button)
        copy_actions.addWidget(self.copy_transcript_notes_button)
        copy_actions.addStretch()
        note_editor_column.addLayout(copy_actions)
        notes_layout.addLayout(note_editor_column, 3)
        layout.addWidget(notes_frame)

        footer = QHBoxLayout()
        error_suffix = (
            f" • {len(self._errors)} unreadable session(s)" if self._errors else ""
        )
        total_size = sum(entry.total_size_bytes for entry in self._entries)
        self.count_label = QLabel(
            f"{len(self._entries)} sessions • {format_file_size(total_size)} total"
            f"{error_suffix}"
        )
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
            QLineEdit, QPlainTextEdit, QListWidget, QTreeWidget {
                                     background:#0B1421; border:1px solid #293A52;
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
            QPushButton#DangerButton { background:#3A1B24; border-color:#9D4255;
                                       color:#FFD8DF; }
            QPushButton#DangerButton:hover { background:#542431;
                                             border-color:#E0667E; }
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
                    format_file_size(entry.total_size_bytes),
                    str(len(session.anatomy_captures)),
                    str(len(session.learning_notes)),
                    transcript,
                    session.state.replace("_", " ").title(),
                ]
            )
            item.setData(0, Qt.ItemDataRole.UserRole, str(entry.manifest_path))
            item.setData(3, Qt.ItemDataRole.UserRole, entry.total_size_bytes)
            self.tree.addTopLevelItem(item)
            self._items.append((item, entry))
        if self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))

    def _apply_filter(self, text: str) -> None:
        query = text.strip().casefold()
        visible = 0
        visible_size = 0
        for item, entry in self._items:
            session = entry.session
            haystack = " ".join(
                [
                    session.title,
                    session.created_at,
                    session.state,
                    "transcript" if session.transcript_markdown_path.is_file() else "",
                    "anatomy" if session.anatomy_captures else "",
                    " ".join(note.text for note in session.learning_notes),
                ]
            ).casefold()
            hidden = bool(query and query not in haystack)
            item.setHidden(hidden)
            visible += not hidden
            if not hidden:
                visible_size += entry.total_size_bytes
        self.count_label.setText(
            f"{visible} of {len(self._entries)} sessions • "
            f"{format_file_size(visible_size)} shown"
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
            self._populate_notes()
            self._sync_buttons()
            return
        session = self._selected.session
        self.detail_title.setText(session.title)
        self.detail_meta.setText(
            f"{format_duration(session.duration_seconds)} recording • "
            f"{format_file_size(self._selected.total_size_bytes)} total size\n"
            f"{len(session.anatomy_captures)} anatomy capture(s) • "
            f"{len(session.learning_notes)} learning note(s)\n"
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
        notes = (
            f"{len(session.learning_notes)} timestamped learning note(s) are ready "
            "for review and non-visual card export."
            if session.learning_notes
            else "No timestamped learning notes were saved."
        )
        self.detail_summary.setText(f"{review}\n\n{transcript}\n\n{notes}")
        self._populate_notes()
        self._sync_buttons()

    def _sync_buttons(self) -> None:
        session = self._selected.session if self._selected else None
        self.review_button.setEnabled(
            bool(
                session
                and (
                    session.review_path.is_file()
                    or session.playback_path.is_file()
                    or session.recording_path.is_file()
                    or session.anatomy_captures
                    or session.learning_notes
                    or session.transcript_markdown_path.is_file()
                )
            )
        )
        self.edit_anatomy_button.setEnabled(
            bool(session and session.anatomy_captures)
        )
        self.copy_codex_anki_button.setEnabled(
            bool(
                session
                and (session.anatomy_captures or session.learning_notes)
            )
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
        note = self._selected_note()
        has_note = note is not None
        self.note_edit.setEnabled(has_note)
        self.save_note_button.setEnabled(has_note)
        self.delete_note_button.setEnabled(has_note)
        self.copy_note_button.setEnabled(has_note)
        self.open_note_button.setEnabled(
            bool(
                has_note
                and session
                and (
                    session.playback_path.is_file()
                    or session.recording_path.is_file()
                )
            )
        )
        self.copy_transcript_button.setEnabled(
            bool(session and session.transcript_markdown_path.is_file())
        )
        self.copy_transcript_notes_button.setEnabled(
            bool(
                session
                and (
                    session.transcript_markdown_path.is_file()
                    or session.learning_notes
                )
            )
        )
        self.folder_button.setEnabled(bool(session and session.folder.is_dir()))
        self.delete_button.setEnabled(bool(session and session.folder.is_dir()))
        self.load_button.setEnabled(session is not None)

    def _populate_notes(self) -> None:
        self.notes_list.blockSignals(True)
        self.notes_list.clear()
        session = self._selected.session if self._selected else None
        if session is not None:
            for note in sorted(
                session.learning_notes,
                key=lambda item: (
                    item.timestamp_seconds,
                    item.created_at,
                    item.id,
                ),
            ):
                summary = " ".join(note.text.split())
                if len(summary) > 105:
                    summary = summary[:102].rstrip() + "…"
                item = QListWidgetItem(
                    f"{format_duration(note_display_timestamp(note))}  •  {summary}"
                )
                item.setData(Qt.ItemDataRole.UserRole, note.id)
                self.notes_list.addItem(item)
        self.notes_list.blockSignals(False)
        if self.notes_list.count():
            self.notes_list.setCurrentRow(0)
        else:
            self.note_edit.clear()

    def _selected_note(self):
        session = self._selected.session if self._selected else None
        item = self.notes_list.currentItem()
        if session is None or item is None:
            return None
        note_id = str(item.data(Qt.ItemDataRole.UserRole) or "")
        return next(
            (note for note in session.learning_notes if note.id == note_id),
            None,
        )

    def _on_note_selected(
        self,
        _current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        note = self._selected_note()
        self.note_edit.setPlainText(note.text if note is not None else "")
        self._sync_buttons()

    def _save_note_edit(self) -> None:
        if self._selected is None:
            return
        note = self._selected_note()
        text = self.note_edit.toPlainText().strip()
        if note is None or not text:
            return
        self._selected.session.update_learning_note(note.id, text)
        self._refresh_notes_after_change(note.id)
        self.detail_summary.setText("Learning note updated.")

    def _delete_note(self) -> None:
        if self._selected is None:
            return
        note = self._selected_note()
        if note is None:
            return
        result = QMessageBox.question(
            self,
            "Delete learning note?",
            (
                f"Delete the learning note at "
                f"{format_duration(note_display_timestamp(note))}?\n\n"
                "The recording and transcript will not be changed."
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if result != QMessageBox.StandardButton.Yes:
            return
        self._selected.session.delete_learning_note(note.id)
        self._refresh_notes_after_change()
        self.detail_summary.setText("Learning note deleted.")

    def _copy_note(self) -> None:
        note = self._selected_note()
        if note is None:
            return
        QApplication.clipboard().setText(
            f"[USER LEARNING NOTE — "
            f"{format_duration(note_display_timestamp(note))}] "
            f"{note.text.strip()}"
        )
        self.detail_summary.setText("Learning note copied to the clipboard.")

    def _copy_transcript(self) -> None:
        if self._selected is None:
            return
        transcript = read_transcript(self._selected.session)
        if not transcript:
            return
        QApplication.clipboard().setText(transcript)
        self.detail_summary.setText(
            "Transcript copied without user learning notes."
        )

    def _copy_transcript_and_notes(self) -> None:
        if self._selected is None:
            return
        QApplication.clipboard().setText(
            render_transcript_with_notes(self._selected.session)
        )
        self.detail_summary.setText(
            "Transcript and clearly labeled learning notes copied."
        )

    def _open_note_timestamp(self) -> None:
        if self._selected is None:
            return
        note = self._selected_note()
        if note is None:
            return
        session = self._selected.session
        build_anatomy_review(session)
        url = QUrl.fromLocalFile(str(session.review_path.resolve()))
        query = QUrlQuery()
        query.addQueryItem("t", f"{note.timestamp_seconds:.3f}")
        url.setQuery(query)
        url.setFragment(note.id)
        QDesktopServices.openUrl(url)

    def _refresh_notes_after_change(self, selected_note_id: str = "") -> None:
        if self._selected is None:
            return
        session = self._selected.session
        build_anatomy_review(session)
        current_item = self.tree.currentItem()
        if current_item is not None:
            current_item.setText(5, str(len(session.learning_notes)))
        self.detail_meta.setText(
            f"{format_duration(session.duration_seconds)} recording • "
            f"{format_file_size(self._selected.total_size_bytes)} total size\n"
            f"{len(session.anatomy_captures)} anatomy capture(s) • "
            f"{len(session.learning_notes)} learning note(s)\n"
            f"Status: {session.state.replace('_', ' ')}"
        )
        self._populate_notes()
        if selected_note_id:
            for index in range(self.notes_list.count()):
                item = self.notes_list.item(index)
                if (
                    str(item.data(Qt.ItemDataRole.UserRole) or "")
                    == selected_note_id
                ):
                    self.notes_list.setCurrentItem(item)
                    break
        self._sync_buttons()

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

    def _confirm_delete(self, session: SessionManifest) -> bool:
        message = QMessageBox(self)
        message.setWindowTitle("Delete past session?")
        message.setIcon(QMessageBox.Icon.Critical)
        message.setText(f'Permanently delete “{session.title}”?')
        message.setInformativeText(
            "This deletes the entire session folder, including every video, audio "
            "file, transcript, screenshot, anatomy edit, review page, and metadata "
            "file. This action cannot be undone.\n\n"
            "Cards already imported into Anki are stored separately in Anki and "
            "will not be deleted. The local .apkg source file will be deleted."
        )
        message.setDetailedText(str(session.folder))
        delete_button = message.addButton(
            "Delete Permanently",
            QMessageBox.ButtonRole.DestructiveRole,
        )
        message.addButton(QMessageBox.StandardButton.Cancel)
        message.setDefaultButton(QMessageBox.StandardButton.Cancel)
        message.exec()
        return message.clickedButton() is delete_button

    def _delete_selected(self) -> None:
        if self._selected is None:
            return
        entry = self._selected
        session = entry.session
        if not self._confirm_delete(session):
            return

        try:
            folder = session.folder.resolve(strict=True)
            delete_session_folder(folder, self._roots)
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Could not delete session",
                f"The session was not deleted.\n\n{exc}",
            )
            return

        current_item = self.tree.currentItem()
        current_index = self.tree.indexOfTopLevelItem(current_item)
        self._items = [
            (item, candidate)
            for item, candidate in self._items
            if candidate is not entry
        ]
        self._entries = [candidate for candidate in self._entries if candidate is not entry]
        self._deleted_folders.add(folder)
        self._selected = None
        if current_index >= 0:
            self.tree.takeTopLevelItem(current_index)

        self.detail_title.setText("Select a session")
        self.detail_meta.clear()
        self.detail_summary.setText(
            "Session deleted. Its videos and all associated files were removed."
        )
        self._apply_filter(self.search_edit.text())
        next_item = next(
            (
                self.tree.topLevelItem(index)
                for index in range(self.tree.topLevelItemCount())
                if not self.tree.topLevelItem(index).isHidden()
            ),
            None,
        )
        if next_item is not None:
            self.tree.setCurrentItem(next_item)
        else:
            self.tree.setCurrentItem(None)
            self._selected = None
            self._sync_buttons()

    def _load_selected(self) -> None:
        if self._selected:
            self.accept()
