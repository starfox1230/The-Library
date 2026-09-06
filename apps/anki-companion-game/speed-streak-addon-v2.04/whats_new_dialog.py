from __future__ import annotations

from pathlib import Path
from typing import Optional

from aqt.qt import (
    QDesktopServices,
    QDialog,
    QFont,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPixmap,
    QRectF,
    QScrollArea,
    QSize,
    QSizePolicy,
    Qt,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from .settings_components import ModernButton
from .support_dialog import (
    ANKIWEB_REVIEW_URL,
    KOFI_URL,
    REDDIT_FEEDBACK_URL,
    SupportIconButton,
)


WHATS_NEW_VERSION = "2.04"
ANKIWEB_BASELINE_VERSION = "1.21"
ASSET_ROOT = Path(__file__).resolve().parent / "whats_new_assets"
REDDIT_URL = "https://www.reddit.com/user/henbitdeadnettle92/"


def _label(
    text: str,
    parent: Optional[QWidget] = None,
    *,
    size: int = 11,
    color: str = "#d6dfeb",
    weight: int = 400,
) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    face = QFont(label.font())
    face.setPointSize(size)
    face.setWeight(QFont.Weight(weight))
    label.setFont(face)
    label.setStyleSheet(f"color: {color}; background: transparent;")
    return label


class ActualUiImage(QWidget):
    """A screenshot rendered from the real Speed Streak interface."""

    def __init__(
        self,
        filename: str,
        accessible_name: str,
        parent: Optional[QWidget] = None,
        *,
        minimum_display_height: int = 110,
        maximum_display_height: int = 320,
    ) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(ASSET_ROOT / filename))
        self._minimum_display_height = max(80, int(minimum_display_height))
        self._maximum_display_height = max(self._minimum_display_height, int(maximum_display_height))
        self.setAccessibleName(accessible_name)
        self.setMinimumHeight(self._minimum_display_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        width = max(180, self.width())
        return QSize(width, self.heightForWidth(width))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if self._pixmap.isNull() or self._pixmap.width() < 1:
            return self._minimum_display_height
        natural_height = round(width * self._pixmap.height() / self._pixmap.width())
        return min(self._maximum_display_height, max(self._minimum_display_height, natural_height))

    def resizeEvent(self, event: object) -> None:
        self.setFixedHeight(self.heightForWidth(self.width()))
        super().resizeEvent(event)  # type: ignore[arg-type]

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), Qt.GlobalColor.black)
        if not self._pixmap.isNull():
            source = QRectF(self._pixmap.rect())
            available = QRectF(self.rect())
            scale = min(
                available.width() / source.width(),
                available.height() / source.height(),
            )
            target_width = source.width() * scale
            target_height = source.height() * scale
            target = QRectF(
                available.x() + ((available.width() - target_width) / 2),
                available.y() + ((available.height() - target_height) / 2),
                target_width,
                target_height,
            )
            # Paint from the full-resolution source in one operation. Creating a
            # logical-pixel-sized intermediate pixmap makes Qt enlarge that copy
            # again on high-DPI Windows displays, which visibly softens the image.
            painter.drawPixmap(target, self._pixmap, source)
        painter.end()


def _instruction(parent: QWidget, number: str, title: str, detail: str) -> QWidget:
    row = QWidget(parent)
    layout = QHBoxLayout(row)
    layout.setContentsMargins(0, 2, 0, 2)
    layout.setSpacing(10)
    badge = QLabel(number, row)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setFixedSize(24, 24)
    badge.setStyleSheet(
        "color: #071018; background: #67dfe7; border-radius: 12px; font-weight: 800;"
    )
    layout.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
    copy = QVBoxLayout()
    copy.setContentsMargins(0, 0, 0, 0)
    copy.setSpacing(1)
    copy.addWidget(_label(title, row, size=10, color="#f5f8fc", weight=700))
    copy.addWidget(_label(detail, row, size=9, color="#aab7c9"))
    layout.addLayout(copy, 1)
    return row


def _focus_mode_explanation(parent: QWidget) -> QWidget:
    block = QWidget(parent)
    layout = QVBoxLayout(block)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(
        _label(
            "I added this because I found myself cheating by using Pause and Undo to protect a streak.",
            block,
            size=10,
            color="#aab7c9",
        )
    )

    controls = QHBoxLayout()
    controls.setContentsMargins(0, 0, 0, 0)
    controls.setSpacing(7)
    for text, foreground, border, background in (
        ("•  NO PAUSE", "#ef7f9d", "rgba(239, 127, 157, 0.72)", "rgba(101, 24, 48, 0.32)"),
        ("•  NO UNDO", "#e8bd55", "rgba(232, 189, 85, 0.72)", "rgba(91, 61, 13, 0.32)"),
    ):
        pill = QLabel(text, block)
        pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pill.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        pill.setStyleSheet(
            "QLabel {"
            f"color: {foreground}; border: 1px solid {border}; background: {background};"
            "border-radius: 10px; padding: 3px 9px; font-size: 9px; font-weight: 800;"
            "}"
        )
        pill.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        controls.addWidget(pill, 0, Qt.AlignmentFlag.AlignTop)
    controls.addWidget(
        _label(
            "are off by default, but can be turned on to counteract the urge to cheat. Hover over the Boost bank to reveal them and toggle them on or off.",
            block,
            size=9,
            color="#aab7c9",
        ),
        1,
    )
    layout.addLayout(controls)
    layout.addWidget(
        _label(
            "Boosts ⚡ give you a limited way to add time when you get distracted or cannot answer quickly enough, without pausing or undoing the review.",
            block,
            size=10,
            color="#d4deea",
        )
    )
    return block


def _visual_preview(parent: QWidget, filename: str, title: str, count: int) -> QWidget:
    item = QWidget(parent)
    layout = QVBoxLayout(item)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    layout.addWidget(
        ActualUiImage(
            filename,
            f"{title} at a {count}-card streak",
            item,
            minimum_display_height=105,
            maximum_display_height=150,
        )
    )
    layout.addWidget(_label(title, item, size=9, color="#dce5f0", weight=700))
    return item


def _summary_card(parent: QWidget, title: str, detail: str) -> QWidget:
    card = QWidget(parent)
    card.setStyleSheet(
        "QWidget { background: #111b28; border: 1px solid #2c3d54; border-radius: 10px; }"
        "QLabel { background: transparent; border: none; }"
    )
    layout = QVBoxLayout(card)
    layout.setContentsMargins(13, 10, 13, 10)
    layout.setSpacing(3)
    layout.addWidget(_label(title, card, size=10, color="#f3f7fc", weight=700))
    layout.addWidget(_label(detail, card, size=9, color="#9eacc0"))
    return card


def _section_action(text: str, parent: QWidget, callback: object) -> ModernButton:
    button = ModernButton(text, parent)
    button.setProperty("class", "secondaryAction")
    button.setMinimumWidth(190)
    button.clicked.connect(callback)  # type: ignore[arg-type]
    return button


class WhatsNewDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.destination = ""
        self.setWindowTitle("What’s New in Speed Streak")
        self.setModal(True)
        self.setMinimumSize(720, 620)
        self.resize(860, 760)
        self.setStyleSheet(
            "QDialog { background: #0a1018; }"
            "QScrollArea { border: none; background: #0a1018; }"
            "QScrollArea > QWidget > QWidget { background: #0a1018; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget(scroll)
        body.setStyleSheet("background: #0a1018;")
        content = QVBoxLayout(body)
        content.setContentsMargins(38, 30, 38, 28)
        content.setSpacing(11)

        release_header = QHBoxLayout()
        release_header.setContentsMargins(0, 0, 0, 0)
        release_header.setSpacing(6)
        release_header.addWidget(_label("WHAT’S NEW", body, size=9, color="#67dfe7", weight=700), 1)
        review_button = SupportIconButton("thumb_up", "Review Speed Streak on AnkiWeb", body)
        review_button.clicked.connect(self._open_ankiweb_review)
        release_header.addWidget(review_button, 0, Qt.AlignmentFlag.AlignRight)
        feedback_button = SupportIconButton("reddit-logo.png", "Send feedback on Reddit", body)
        feedback_button.clicked.connect(self._open_reddit_feedback)
        release_header.addWidget(feedback_button, 0, Qt.AlignmentFlag.AlignRight)
        support_button = SupportIconButton("kofi-logo.png", "Support development on Ko-fi", body)
        support_button.clicked.connect(self._open_kofi)
        release_header.addWidget(support_button, 0, Qt.AlignmentFlag.AlignRight)
        content.addLayout(release_header)

        content.addWidget(_label("Streak records", body, size=25, color="#f7f9fc", weight=700))
        content.addWidget(
            _label(
                "Keep a record to beat in view while you review. Choose the minimal default, a live comparison, or a five-streak list.",
                body,
                size=11,
                color="#d4deea",
            )
        )

        record_preview_row = QHBoxLayout()
        record_preview_row.setContentsMargins(0, 4, 0, 0)
        record_preview_row.setSpacing(14)
        record_preview_row.addWidget(
            ActualUiImage(
                "streak-records-display.jpg",
                "The actual Streak Strip and Five Streaks review display with synthetic record data",
                body,
                minimum_display_height=390,
                maximum_display_height=470,
            ),
            1,
        )
        record_choices = QVBoxLayout()
        record_choices.setContentsMargins(0, 0, 0, 0)
        record_choices.setSpacing(8)
        record_choices.addWidget(_summary_card(body, "Best only", "The default: one all-time or today target."))
        record_choices.addWidget(_summary_card(body, "Streak strip", "Adds the live streak and distance to the record."))
        record_choices.addWidget(_summary_card(body, "Five streaks", "Adds five ranked or recent completed streaks."))
        record_choices.addWidget(
            _summary_card(
                body,
                "Open any record for details",
                "Compare active time, pauses, Review departures, restarts, undo use, and Pure status.",
            )
        )
        record_choices.addStretch(1)
        record_choices.addWidget(_section_action("Edit streak record display", body, self._open_record_settings))
        record_preview_row.addLayout(record_choices, 1)
        content.addLayout(record_preview_row)

        content.addSpacing(14)
        content.addWidget(_label("“Time’s Running Out” sound", body, size=20, color="#f7f9fc", weight=700))
        content.addWidget(
            _label(
                "Add an optional cue on each whole-second mark near the end of the timer.",
                body,
                size=10,
                color="#b8c4d3",
            )
        )
        countdown_row = QHBoxLayout()
        countdown_row.setContentsMargins(0, 3, 0, 0)
        countdown_row.setSpacing(14)
        countdown_row.addWidget(
            ActualUiImage(
                "countdown-cue-settings.jpg",
                "The actual Countdown Cue controls in Audio and Haptics settings",
                body,
                minimum_display_height=330,
                maximum_display_height=410,
            ),
            1,
        )
        countdown_choices = QVBoxLayout()
        countdown_choices.setContentsMargins(0, 0, 0, 0)
        countdown_choices.setSpacing(8)
        countdown_choices.addWidget(_summary_card(body, "Choose when it starts", "The same threshold turns the timer red."))
        countdown_choices.addWidget(_summary_card(body, "Choose the sound", "Use a built-in cue or upload your own file."))
        countdown_choices.addWidget(_summary_card(body, "Tune it", "Set volume, preview it, and align the exact sync point."))
        countdown_choices.addWidget(
            _summary_card(
                body,
                "Improved sound timing",
                "Default review cues now preload on dedicated low-latency channels.",
            )
        )
        countdown_choices.addStretch(1)
        countdown_choices.addWidget(_section_action("Edit countdown sound", body, self._open_countdown_settings))
        countdown_row.addLayout(countdown_choices, 1)
        content.addLayout(countdown_row)

        content.addSpacing(12)
        mac_note = QWidget(body)
        mac_note.setStyleSheet(
            "QWidget { background: #102033; border: 1px solid #315174; border-radius: 10px; }"
            "QLabel { background: transparent; border: none; }"
        )
        mac_layout = QHBoxLayout(mac_note)
        mac_layout.setContentsMargins(14, 11, 14, 11)
        mac_layout.setSpacing(12)
        mac_copy = QVBoxLayout()
        mac_copy.setContentsMargins(0, 0, 0, 0)
        mac_copy.setSpacing(3)
        mac_copy.addWidget(_label("macOS controller vibration testers wanted", mac_note, size=10, color="#e9f3ff", weight=700))
        mac_copy.addWidget(
            _label(
                "Native macOS support is included, but I do not have the hardware to verify it. If you can test controller vibration, please contact u/henbitdeadnettle92 on Reddit.",
                mac_note,
                size=9,
                color="#a9bdd4",
            )
        )
        mac_layout.addLayout(mac_copy, 1)
        reddit_button = ModernButton("Reddit profile", mac_note)
        reddit_button.setProperty("class", "secondaryAction")
        reddit_button.setMinimumWidth(126)
        reddit_button.clicked.connect(self._open_reddit)
        mac_layout.addWidget(reddit_button, 0, Qt.AlignmentFlag.AlignVCenter)
        content.addWidget(mac_note)

        content.addSpacing(22)
        divider = QWidget(body)
        divider.setFixedHeight(1)
        divider.setStyleSheet("background: #2b3b50;")
        content.addWidget(divider)
        content.addSpacing(14)
        content.addWidget(_label("PRIOR UPDATE", body, size=9, color="#8493aa", weight=700))
        content.addWidget(_label("Boosts ⚡", body, size=25, color="#f7f9fc", weight=700))
        content.addWidget(
            _label(
                "Time Boost is now the default. Complete cards to earn Boosts. Press C before the timer "
                "expires to use one and add time.",
                body,
                size=11,
                color="#d4deea",
            )
        )
        content.addWidget(_focus_mode_explanation(body))
        content.addSpacing(3)
        content.addWidget(
            ActualUiImage(
                "boosts.png",
                "The Speed Streak timer, three-slot Boost bank, Next Boost meter, No Pause, No Undo, and C shortcut",
                body,
                minimum_display_height=250,
                maximum_display_height=380,
            )
        )
        content.addSpacing(4)
        content.addWidget(
            _instruction(body, "1", "Earn", "Every card you complete advances the Next Boost meter. A full meter adds one Boost to the bank.")
        )
        content.addWidget(
            _instruction(body, "2", "Use", "Press the shortcut shown under the bank before time expires. The default shortcut is C.")
        )
        content.addWidget(
            _instruction(
                body,
                "3",
                "Adjust",
                "Click the Boost bank for its gameplay settings. Click the shortcut key to change the key.",
            )
        )
        content.addWidget(
            _label(
                "New runs start with 3 of 5 Boosts. Both values are configurable in Gameplay settings.",
                body,
                size=9,
                color="#8fe1e6",
                weight=700,
            )
        )
        content.addWidget(
            _label(
                "Prefer the old score and multiplier? Legacy Points is still available in Settings → Gameplay.",
                body,
                size=9,
                color="#8fe1e6",
                weight=700,
            )
        )

        content.addSpacing(14)
        content.addWidget(_label("New visual options", body, size=18, color="#f7f9fc", weight=700))
        content.addWidget(
            _label(
                "Fusion is the new default satellite style. Singularity and Crystal Reactor are also available. "
                "Click the visual button at the bottom-left during review to switch.",
                body,
                size=10,
                color="#b8c4d3",
            )
        )
        previews = QHBoxLayout()
        previews.setContentsMargins(0, 3, 0, 0)
        previews.setSpacing(10)
        previews.addWidget(_visual_preview(body, "fusion-248.png", "Fusion", 248), 1)
        previews.addWidget(_visual_preview(body, "singularity-248.png", "Singularity", 248), 1)
        previews.addWidget(_visual_preview(body, "crystal-53.png", "Crystal Reactor", 53), 1)
        content.addLayout(previews)
        content.addStretch(1)

        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        footer = QWidget(self)
        footer.setStyleSheet("background: #0d151f; border-top: 1px solid #223246;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(26, 13, 26, 13)
        footer_layout.setSpacing(11)
        footer_layout.addWidget(
            _label("Reopen this from Speed Streak → What’s New.", footer, size=9, color="#8493aa"),
            1,
        )
        settings_button = ModernButton("Open Gameplay Settings", footer)
        settings_button.setProperty("class", "secondaryAction")
        settings_button.setMinimumWidth(174)
        settings_button.clicked.connect(self._open_settings)
        footer_layout.addWidget(settings_button)
        done_button = ModernButton("Done", footer)
        done_button.setProperty("class", "primaryAction")
        done_button.setMinimumWidth(100)
        done_button.clicked.connect(self.accept)
        footer_layout.addWidget(done_button)
        root.addWidget(footer)

    def _open_settings(self) -> None:
        self.destination = "settings"
        self.accept()

    def _open_record_settings(self) -> None:
        self.destination = "records"
        self.accept()

    def _open_countdown_settings(self) -> None:
        self.destination = "countdown_audio"
        self.accept()

    def _open_kofi(self) -> None:
        QDesktopServices.openUrl(QUrl(KOFI_URL))

    def _open_ankiweb_review(self) -> None:
        QDesktopServices.openUrl(QUrl(ANKIWEB_REVIEW_URL))

    def _open_reddit_feedback(self) -> None:
        QDesktopServices.openUrl(QUrl(REDDIT_FEEDBACK_URL))

    def _open_reddit(self) -> None:
        QDesktopServices.openUrl(QUrl(REDDIT_URL))


def show_whats_new_dialog(parent: Optional[QWidget] = None) -> str:
    dialog = WhatsNewDialog(parent)
    dialog.exec()
    return dialog.destination
