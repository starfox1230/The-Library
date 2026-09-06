from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Optional

from aqt.qt import (
    QColor,
    QDesktopServices,
    QDialog,
    QFont,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPushButton,
    QRectF,
    Qt,
    QUrl,
    QVBoxLayout,
    QWidget,
)

from .settings_components import ModernButton, ModernSurface


ANKIWEB_REVIEW_URL = "https://ankiweb.net/shared/info/1237336370"
REDDIT_FEEDBACK_URL = (
    "https://www.reddit.com/message/compose/"
    "?to=henbitdeadnettle92&subject=Speed%20Streak%20feedback"
)
KOFI_URL = "https://ko-fi.com/ankispeedstreak"
SUPPORT_ASSET_DIR = Path(__file__).resolve().parent / "support_assets"


class ThumbUpIcon(QWidget):
    """Small deterministic thumb icon that follows the green accent on every OS."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(32, 32)

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor("#a4ebc6"), 1))
        painter.setBrush(QColor("#52c98c"))

        hand = QPainterPath()
        hand.moveTo(10, 13)
        hand.lineTo(14, 13)
        hand.cubicTo(15.8, 11.4, 16.8, 8.6, 17.2, 6.2)
        hand.cubicTo(17.5, 4.5, 19.7, 4.7, 20.2, 6.4)
        hand.cubicTo(20.8, 8.3, 20.5, 10.4, 20.1, 12.2)
        hand.lineTo(24.5, 12.2)
        hand.cubicTo(26.4, 12.2, 27.3, 13.5, 26.7, 15.2)
        hand.lineTo(23.6, 23.4)
        hand.cubicTo(23.1, 24.7, 22.1, 25.3, 20.7, 25.3)
        hand.lineTo(14, 25.3)
        hand.cubicTo(12.4, 25.3, 11.1, 24.5, 10, 23.5)
        hand.closeSubpath()
        painter.drawPath(hand)
        painter.drawRoundedRect(5, 13, 5, 13, 1.5, 1.5)
        painter.end()


class BrandIcon(QLabel):
    """Display an official brand icon without changing its proportions or colors."""

    def __init__(self, filename: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        source = QPixmap(str(SUPPORT_ASSET_DIR / filename))
        if not source.isNull():
            self.setPixmap(
                source.scaled(
                    32,
                    32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )


class SupportIconButton(QPushButton):
    """Compact icon-only link button shared with the What’s New header."""

    def __init__(
        self,
        icon: str,
        tooltip: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.icon_kind = str(icon)
        self.setFixedSize(38, 36)
        self.setToolTip(tooltip)
        self.setAccessibleName(tooltip)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if self.icon_kind == "thumb_up":
            self.icon_pixmap = QPixmap()
        else:
            self.icon_pixmap = QPixmap(str(SUPPORT_ASSET_DIR / self.icon_kind)).scaled(
                24,
                24,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        background = "#1a2736"
        border = "#3d516b"
        if self.isDown():
            background = "#101a26"
        elif self.underMouse():
            background = "#26384c"
            border = "#617b9c"
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(bounds, 8, 8)
        if self.icon_kind == "thumb_up":
            painter.save()
            painter.translate(3, 2)
            self._paint_thumb(painter)
            painter.restore()
        elif not self.icon_pixmap.isNull():
            x = round((self.width() - self.icon_pixmap.width()) / 2)
            y = round((self.height() - self.icon_pixmap.height()) / 2)
            painter.drawPixmap(x, y, self.icon_pixmap)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#a9c8ff"), 1))
            painter.drawRoundedRect(bounds.adjusted(2, 2, -2, -2), 6, 6)
        painter.end()

    @staticmethod
    def _paint_thumb(painter: QPainter) -> None:
        painter.setPen(QPen(QColor("#a4ebc6"), 1))
        painter.setBrush(QColor("#52c98c"))
        hand = QPainterPath()
        hand.moveTo(10, 13)
        hand.lineTo(14, 13)
        hand.cubicTo(15.8, 11.4, 16.8, 8.6, 17.2, 6.2)
        hand.cubicTo(17.5, 4.5, 19.7, 4.7, 20.2, 6.4)
        hand.cubicTo(20.8, 8.3, 20.5, 10.4, 20.1, 12.2)
        hand.lineTo(24.5, 12.2)
        hand.cubicTo(26.4, 12.2, 27.3, 13.5, 26.7, 15.2)
        hand.lineTo(23.6, 23.4)
        hand.cubicTo(23.1, 24.7, 22.1, 25.3, 20.7, 25.3)
        hand.lineTo(14, 25.3)
        hand.cubicTo(12.4, 25.3, 11.1, 24.5, 10, 23.5)
        hand.closeSubpath()
        painter.drawPath(hand)
        painter.drawRoundedRect(5, 13, 5, 13, 1.5, 1.5)


def _label(
    text: str,
    parent: Optional[QWidget] = None,
    *,
    size: int = 11,
    color: str = "#c7d1df",
    weight: int = 400,
) -> QLabel:
    label = QLabel(text, parent)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
    font = QFont(label.font())
    font.setPointSize(size)
    font.setWeight(QFont.Weight(weight))
    label.setFont(font)
    label.setStyleSheet(f"color: {color}; background: transparent;")
    return label


def _action_card(
    parent: QWidget,
    *,
    icon: str,
    icon_color: str,
    title: str,
    detail: str,
    button_text: str,
    callback: Callable[[], None],
    primary: bool = False,
) -> ModernSurface:
    card = ModernSurface("row", parent)
    row = QHBoxLayout(card)
    row.setContentsMargins(15, 13, 14, 13)
    row.setSpacing(13)

    if icon == "thumb_up":
        icon_widget = ThumbUpIcon(card)
    elif icon.startswith("brand:"):
        icon_widget = BrandIcon(icon.removeprefix("brand:"), card)
    else:
        icon_widget = _label(icon, card, size=18, color=icon_color, weight=700)
        icon_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_widget.setFixedWidth(32)
    row.addWidget(icon_widget, 0, Qt.AlignmentFlag.AlignTop)

    copy = QVBoxLayout()
    copy.setContentsMargins(0, 0, 0, 0)
    copy.setSpacing(4)
    copy.addWidget(_label(title, card, size=11, color="#f4f7fb", weight=700))
    copy.addWidget(_label(detail, card, size=9, color="#9eacbf"))
    row.addLayout(copy, 1)

    button = ModernButton(button_text, card)
    button.setProperty("class", "primaryAction" if primary else "secondaryAction")
    button.setMinimumWidth(148)
    button.clicked.connect(callback)
    row.addWidget(button, 0, Qt.AlignmentFlag.AlignVCenter)
    return card


class SupportDialog(QDialog):
    """A compact hub for reviews, feedback, and optional support."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Speed Streak Help / Feedback")
        self.setModal(True)
        self.setMinimumWidth(610)
        self.resize(650, 400)
        self.setStyleSheet(
            "QDialog { background: #0a1018; }"
            "QLabel { background: transparent; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 25, 28, 22)
        root.setSpacing(11)

        root.addWidget(_label("Help / Feedback", self, size=20, color="#f4f7fb", weight=700))
        root.addWidget(
            _label(
                "Reviews, bug reports, and feature ideas all help improve Speed Streak.",
                self,
                size=10,
                color="#aebacc",
            )
        )

        root.addSpacing(4)
        root.addWidget(
            _action_card(
                self,
                icon="thumb_up",
                icon_color="#65d79e",
                title="Enjoying Speed Streak?",
                detail="A positive AnkiWeb review helps other Anki users find the add-on.",
                button_text="Review on AnkiWeb",
                callback=self._open_ankiweb_review,
                primary=True,
            )
        )
        root.addWidget(
            _action_card(
                self,
                icon="brand:reddit-logo.png",
                icon_color="#7fb0ff",
                title="Found a problem or have an idea?",
                detail="Send bugs, glitches, or feature requests to u/henbitdeadnettle92 on Reddit.",
                button_text="Message on Reddit",
                callback=self._open_reddit_feedback,
            )
        )
        root.addWidget(
            _action_card(
                self,
                icon="brand:kofi-logo.png",
                icon_color="#d7bd79",
                title="Support development",
                detail="If you feel inclined, optional support is available on Ko-fi.",
                button_text="Open Ko-fi",
                callback=self._open_kofi,
            )
        )
        root.addStretch(1)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 4, 0, 0)
        footer.setSpacing(10)
        footer.addStretch(1)

        close_button = ModernButton("Close", self)
        close_button.setProperty("class", "secondaryAction")
        close_button.setMinimumWidth(96)
        close_button.clicked.connect(self.reject)
        footer.addWidget(close_button)

        root.addLayout(footer)

    def _open_ankiweb_review(self) -> None:
        QDesktopServices.openUrl(QUrl(ANKIWEB_REVIEW_URL))

    def _open_reddit_feedback(self) -> None:
        QDesktopServices.openUrl(QUrl(REDDIT_FEEDBACK_URL))

    def _open_kofi(self) -> None:
        QDesktopServices.openUrl(QUrl(KOFI_URL))


def show_help_feedback_dialog(parent: Optional[QWidget] = None) -> None:
    dialog = SupportDialog(parent)
    dialog.exec()
