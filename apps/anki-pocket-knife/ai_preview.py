from __future__ import annotations

import difflib
import re
from html import escape

from aqt import mw
from aqt.qt import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .settings import get_setting, set_setting


TEXT_STYLE = """
QTextEdit {
    font-size: 15px;
    line-height: 1.35;
    padding: 10px;
}
QLabel {
    font-size: 14px;
}
QPushButton {
    font-size: 14px;
    padding: 7px 12px;
}
""".strip()


def _heading(text: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setStyleSheet("font-size: 16px; font-weight: 700; margin-top: 4px;")
    return label


def _read_only_text(text: str, parent: QWidget | None = None, *, min_height: int = 170) -> QTextEdit:
    widget = QTextEdit(parent)
    widget.setReadOnly(True)
    widget.setMinimumHeight(min_height)
    widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    widget.setProperty("pocketKnifeRawText", str(text or ""))
    _apply_text_mode(widget)
    return widget


def _apply_text_mode(widget: QTextEdit) -> None:
    text = str(widget.property("pocketKnifeRawText") or "")
    if bool(get_setting("ai_preview_show_html")):
        widget.setPlainText(text)
    else:
        widget.setHtml(text)


def _set_preview_text(widget: QTextEdit, text: str) -> None:
    widget.setProperty("pocketKnifeRawText", str(text or ""))
    _apply_text_mode(widget)


def _html_toggle(widgets: list[QTextEdit], parent: QWidget | None = None) -> QCheckBox:
    checkbox = QCheckBox("Show HTML source", parent)
    checkbox.setChecked(bool(get_setting("ai_preview_show_html")))

    def changed(checked: bool) -> None:
        set_setting("ai_preview_show_html", bool(checked))
        for widget in widgets:
            _apply_text_mode(widget)

    checkbox.toggled.connect(changed)
    return checkbox


class ReplacementPreviewDialog(QDialog):
    def __init__(
        self,
        *,
        title: str,
        original: str,
        suggestion: str,
        parent: QWidget | None = None,
        show_diff: bool = False,
    ) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle(title)
        self.resize(980, 700)
        self.setStyleSheet(TEXT_STYLE)
        self.accepted_replacement = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        text_widgets: list[QTextEdit] = []
        layout.addWidget(_html_toggle(text_widgets, self))
        layout.addWidget(_heading("Original", self))
        original_widget = _read_only_text(original, self, min_height=210)
        text_widgets.append(original_widget)
        layout.addWidget(original_widget)
        layout.addWidget(_heading("AI Suggestion", self))
        suggestion_widget = _read_only_text(suggestion, self, min_height=210)
        text_widgets.append(suggestion_widget)
        layout.addWidget(suggestion_widget)
        if show_diff:
            layout.addWidget(_heading("Changes", self))
            diff = _read_only_text("", self, min_height=170)
            diff.setHtml(_inline_diff_html(original, suggestion))
            layout.addWidget(diff)

        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Cancel", self)
        replace = QPushButton("Replace", self)
        replace.setDefault(True)
        row.addWidget(cancel)
        row.addWidget(replace)
        layout.addLayout(row)

        cancel.clicked.connect(self.reject)
        replace.clicked.connect(self._accept_replacement)

    def _accept_replacement(self) -> None:
        self.accepted_replacement = True
        self.accept()


def _inline_diff_html(original: str, suggestion: str) -> str:
    original_words = str(original or "").split()
    suggestion_words = str(suggestion or "").split()
    parts: list[str] = []
    matcher = difflib.SequenceMatcher(a=original_words, b=suggestion_words)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.extend(escape(word) for word in original_words[i1:i2])
        elif tag == "delete":
            parts.extend(
                f'<span style="background:#7f1d1d;color:#fee2e2;text-decoration:line-through;padding:1px 3px;border-radius:3px;">{escape(word)}</span>'
                for word in original_words[i1:i2]
            )
        elif tag == "insert":
            parts.extend(
                f'<span style="background:#14532d;color:#dcfce7;padding:1px 3px;border-radius:3px;">{escape(word)}</span>'
                for word in suggestion_words[j1:j2]
            )
        elif tag == "replace":
            parts.extend(
                f'<span style="background:#7f1d1d;color:#fee2e2;text-decoration:line-through;padding:1px 3px;border-radius:3px;">{escape(word)}</span>'
                for word in original_words[i1:i2]
            )
            parts.extend(
                f'<span style="background:#14532d;color:#dcfce7;padding:1px 3px;border-radius:3px;">{escape(word)}</span>'
                for word in suggestion_words[j1:j2]
            )
    return '<div style="font-size:15px;line-height:1.6;white-space:normal;">' + " ".join(parts) + "</div>"


def _display_card_label(index: int, card: str) -> str:
    text = str(card or "")
    if not bool(get_setting("ai_preview_show_html")):
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"<[^>]+>", "", text)
    return f"{index}. {text}"


class GeneratedCardsDialog(QDialog):
    def __init__(self, *, title: str, cards: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle(title)
        self.resize(980, 660)
        self.setStyleSheet(TEXT_STYLE)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.selected_action = "dismiss"
        self.cards = list(cards)
        self.action_callback = None

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        toggle = _html_toggle([], self)
        layout.addWidget(toggle)
        layout.addWidget(_heading("Generated Cards", self))
        hint = QLabel("Select a generated card, then copy it, add it now, or load it into the editor.")
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("QListWidget { font-size: 15px; padding: 8px; } QListWidget::item { padding: 10px; }")
        for idx, card in enumerate(self.cards, start=1):
            item = QListWidgetItem(_display_card_label(idx, card))
            item.setData(256, card)
            self.list_widget.addItem(item)
        toggle.toggled.connect(lambda _checked: self._refresh_card_labels())
        if self.cards:
            self.list_widget.setCurrentRow(0)
        layout.addWidget(self.list_widget)

        row = QHBoxLayout()
        row.addStretch(1)
        dismiss = QPushButton("Dismiss", self)
        copy = QPushButton("Copy Selected", self)
        add_now = QPushButton("Add Selected Now", self)
        load = QPushButton("Load Selected Into Editor", self)
        row.addWidget(dismiss)
        row.addWidget(copy)
        row.addWidget(add_now)
        row.addWidget(load)
        layout.addLayout(row)

        dismiss.clicked.connect(self.close)
        copy.clicked.connect(self._copy_selected)
        add_now.clicked.connect(self._add_selected)
        load.clicked.connect(self._load_selected)

    def selected_card(self) -> str:
        item = self.list_widget.currentItem()
        if item is None:
            return self.cards[0] if self.cards else ""
        return str(item.data(256) or "")

    def _copy_selected(self) -> None:
        QApplication.clipboard().setText(self.selected_card())
        self.selected_action = "copy"
        self._mark_current_done()

    def _load_selected(self) -> None:
        self.selected_action = "load"
        if callable(self.action_callback):
            self.action_callback("load", self.selected_card())
            self._mark_current_done("loaded")
        else:
            self.accept()

    def _add_selected(self) -> None:
        self.selected_action = "add"
        if callable(self.action_callback):
            self.action_callback("add", self.selected_card())
            self._mark_current_done("added")
        else:
            self.accept()

    def _mark_current_done(self, label: str = "copied") -> None:
        item = self.list_widget.currentItem()
        if item is not None and not item.text().startswith("["):
            item.setText(f"[{label}] " + item.text())

    def _refresh_card_labels(self) -> None:
        for row, card in enumerate(self.cards):
            item = self.list_widget.item(row)
            if item is None:
                continue
            prefix = ""
            text = item.text()
            if text.startswith("[") and "] " in text:
                prefix = text[: text.index("] ") + 2]
            item.setText(prefix + _display_card_label(row + 1, card))


class BatchPreviewDialog(QDialog):
    def __init__(self, *, title: str, originals: list[str], suggestions: list[str], parent: QWidget | None = None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle(title)
        self.resize(1120, 760)
        self.setStyleSheet(TEXT_STYLE)
        self.apply_changes = False
        self.originals = list(originals)
        self.suggestions = list(suggestions)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        total = min(len(self.originals), len(self.suggestions))
        text_widgets: list[QTextEdit] = []
        layout.addWidget(_html_toggle(text_widgets, self))
        layout.addWidget(_heading(f"Review {total} Uniform Card Changes", self))

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget(scroll)
        stack = QVBoxLayout(content)
        stack.setSpacing(18)

        for idx, (original, suggestion) in enumerate(
            zip(self.originals, self.suggestions),
            start=1,
        ):
            section = QWidget(content)
            section.setObjectName("batchCardSection")
            section.setStyleSheet(
                "#batchCardSection { border: 1px solid rgba(120, 120, 120, 0.35); border-radius: 6px; }"
            )
            section_layout = QVBoxLayout(section)
            section_layout.setSpacing(8)
            section_layout.addWidget(_heading(f"Card {idx}", section))

            compare_row = QHBoxLayout()
            compare_row.setSpacing(14)

            original_col = QVBoxLayout()
            original_col.addWidget(_heading("Original", section))
            original_widget = _read_only_text(original, section, min_height=190)
            text_widgets.append(original_widget)
            original_col.addWidget(original_widget)
            compare_row.addLayout(original_col, 1)

            suggestion_col = QVBoxLayout()
            suggestion_col.addWidget(_heading("Uniform AI Version", section))
            suggestion_widget = _read_only_text(suggestion, section, min_height=190)
            text_widgets.append(suggestion_widget)
            suggestion_col.addWidget(suggestion_widget)
            compare_row.addLayout(suggestion_col, 1)

            section_layout.addLayout(compare_row)
            stack.addWidget(section)

        stack.addStretch(1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        row = QHBoxLayout()
        row.addStretch(1)
        cancel = QPushButton("Cancel", self)
        apply = QPushButton("Apply All", self)
        apply.setDefault(True)
        row.addWidget(cancel)
        row.addWidget(apply)
        layout.addLayout(row)

        cancel.clicked.connect(self.reject)
        apply.clicked.connect(self._accept_apply)

    def _accept_apply(self) -> None:
        self.apply_changes = True
        self.accept()
