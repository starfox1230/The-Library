from __future__ import annotations

import shutil
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .anki_export import build_anatomy_apkg
from .annotation import AnatomyAnnotationDialog
from .models import AnatomyCapture, SessionManifest, format_duration
from .review import build_anatomy_review, write_anatomy_manifest


class AnatomyPostEditorDialog(QDialog):
    def __init__(self, session: SessionManifest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._session = session
        self._editor = AnatomyAnnotationDialog(parent=None)
        self.setWindowTitle(f"Edit Anatomy Screenshots — {session.title}")
        self.resize(1040, 700)
        self.setMinimumSize(820, 540)
        self._build_ui()
        self._fill_list()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        title = QLabel("Edit Anatomy Screenshots")
        title.setObjectName("EditorTitle")
        layout.addWidget(title)
        subtitle = QLabel(
            "Rename structures, redraw from the untouched source frame, or change "
            "the crop. All edits remain reversible."
        )
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        body = QHBoxLayout()
        self.capture_list = QListWidget()
        self.capture_list.currentItemChanged.connect(self._on_selection_changed)
        self.capture_list.itemDoubleClicked.connect(lambda *_args: self._edit_selected())
        body.addWidget(self.capture_list, 1)

        preview_column = QVBoxLayout()
        self.preview = QLabel("Select a capture")
        self.preview.setObjectName("Preview")
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumSize(520, 360)
        preview_column.addWidget(self.preview, 1)
        self.detail_label = QLabel("")
        self.detail_label.setObjectName("Muted")
        self.detail_label.setWordWrap(True)
        preview_column.addWidget(self.detail_label)
        self.edit_button = QPushButton("Edit Selected Screenshot")
        self.edit_button.setObjectName("PrimaryButton")
        self.edit_button.clicked.connect(self._edit_selected)
        preview_column.addWidget(self.edit_button)
        body.addLayout(preview_column, 3)
        layout.addLayout(body, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        close_button = QPushButton("Done")
        close_button.clicked.connect(self.accept)
        footer.addWidget(close_button)
        layout.addLayout(footer)

        self.setStyleSheet(
            """
            QDialog, QWidget { background:#09101C; color:#EEF4FC;
                               font-family:"Segoe UI"; font-size:10pt; }
            QLabel#EditorTitle { font-size:21pt; font-weight:700; }
            QLabel#Muted { color:#9EB0C8; }
            QLabel#Preview { background:#05080D; border:1px solid #26364D;
                             border-radius:9px; }
            QListWidget { background:#0B1421; border:1px solid #293A52;
                          border-radius:7px; padding:6px; }
            QListWidget::item { padding:9px; }
            QListWidget::item:selected { background:#216F8B; }
            QPushButton { background:#17273A; border:1px solid #36516F;
                          border-radius:7px; padding:9px 12px; }
            QPushButton#PrimaryButton { background:#1A7390; border-color:#58D7FF;
                                        font-weight:700; }
            """
        )

    def _fill_list(self, selected_index: int | None = None) -> None:
        self.capture_list.clear()
        for capture in self._session.anatomy_captures:
            item = QListWidgetItem(
                f"{format_duration(capture.timestamp_seconds)}  •  "
                f"{capture.label or 'Unlabeled screenshot'}"
            )
            item.setData(Qt.ItemDataRole.UserRole, capture.index)
            self.capture_list.addItem(item)
        if self.capture_list.count():
            row = 0
            if selected_index is not None:
                row = next(
                    (
                        index
                        for index in range(self.capture_list.count())
                        if self.capture_list.item(index).data(
                            Qt.ItemDataRole.UserRole
                        )
                        == selected_index
                    ),
                    0,
                )
            self.capture_list.setCurrentRow(row)
        self.edit_button.setEnabled(bool(self.capture_list.currentItem()))

    def _selected_capture(self) -> AnatomyCapture | None:
        item = self.capture_list.currentItem()
        if item is None:
            return None
        index = int(item.data(Qt.ItemDataRole.UserRole))
        return next(
            (
                capture
                for capture in self._session.anatomy_captures
                if capture.index == index
            ),
            None,
        )

    def _on_selection_changed(
        self,
        _current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        capture = self._selected_capture()
        self.edit_button.setEnabled(capture is not None)
        if capture is None:
            self.preview.clear()
            self.detail_label.clear()
            return
        annotated = self._session.folder / capture.annotated_image
        pixmap = QPixmap(str(annotated))
        if not pixmap.isNull():
            self.preview.setPixmap(
                pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        else:
            self.preview.setText("Preview unavailable")
        edit_status = (
            "Non-destructive edit data is available."
            if capture.edit_file
            else "Legacy capture: its existing drawing will be preserved. "
            "Use Clear Drawing to remove it."
        )
        self.detail_label.setText(
            f"{format_duration(capture.timestamp_seconds)} • "
            f"{'Anki card enabled' if capture.create_anki_card else 'Screenshot only'}\n"
            f"{edit_status}"
        )

    def _edit_selected(self) -> None:
        capture = self._selected_capture()
        if capture is None:
            return
        original_path = self._session.folder / capture.original_image
        annotated_path = self._session.folder / capture.annotated_image
        edit_path = (
            self._session.folder / capture.edit_file
            if capture.edit_file
            else self._session.anatomy_edit_path(capture.index)
        )
        preserved_path: Path | None = None
        if not edit_path.is_file() and annotated_path.is_file():
            preserved_path = self._session.anatomy_preserved_path(capture.index)
            if not preserved_path.is_file():
                shutil.copy2(annotated_path, preserved_path)
        self._editor.prepare(
            original_path,
            format_duration(capture.timestamp_seconds),
            default_card_mode=capture.create_anki_card,
            label=capture.label,
            state_path=edit_path if edit_path.is_file() else None,
            preserved_image_path=preserved_path,
            post_mode=True,
        )
        self._editor.showMaximized()
        if self._editor.exec() != QDialog.DialogCode.Accepted:
            return
        self._editor.save_annotation(annotated_path, edit_path)
        capture.label = self._editor.label
        capture.create_anki_card = self._editor.create_anki_card
        capture.edit_file = str(edit_path.relative_to(self._session.folder))
        self._session.save()
        write_anatomy_manifest(self._session)
        build_anatomy_review(self._session)
        try:
            build_anatomy_apkg(self._session)
        except Exception as exc:
            self._session.warnings.append(f"Post-edit Anki export: {exc}")
            self._session.save()
        self._fill_list(capture.index)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "capture_list"):
            self._on_selection_changed(self.capture_list.currentItem(), None)
