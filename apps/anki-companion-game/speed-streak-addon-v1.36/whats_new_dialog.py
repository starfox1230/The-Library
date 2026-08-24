from __future__ import annotations

from pathlib import Path
from typing import Optional

from aqt.qt import (
    QColor,
    QDialog,
    QFont,
    QHBoxLayout,
    QLabel,
    QPainter,
    QPen,
    QPixmap,
    QRectF,
    QScrollArea,
    QSize,
    QSizePolicy,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .settings_components import ModernButton


WHATS_NEW_VERSION = "1.36"
ANKIWEB_BASELINE_VERSION = "1.21"
ASSET_ROOT = Path(__file__).resolve().parent / "whats_new_assets"


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
    face.setWeight(weight)
    label.setFont(face)
    label.setStyleSheet(f"color: {color}; background: transparent;")
    return label


class ActualUiImage(QWidget):
    """Screenshot produced by the real Speed Streak web interface."""

    def __init__(
        self,
        filename: str,
        accessible_name: str,
        parent: Optional[QWidget] = None,
        *,
        maximum_display_height: int = 300,
    ) -> None:
        super().__init__(parent)
        self._pixmap = QPixmap(str(ASSET_ROOT / filename))
        self._maximum_display_height = max(180, int(maximum_display_height))
        self.setAccessibleName(accessible_name)
        self.setMinimumHeight(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        width = max(560, self.width())
        return QSize(width, self.heightForWidth(width))

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        if self._pixmap.isNull() or self._pixmap.width() < 1:
            return 180
        return min(
            self._maximum_display_height,
            max(180, round(width * self._pixmap.height() / self._pixmap.width())),
        )

    def resizeEvent(self, event: object) -> None:
        self.setFixedHeight(self.heightForWidth(self.width()))
        super().resizeEvent(event)  # type: ignore[arg-type]

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QPen(QColor("#30445f"), 1))
        painter.setBrush(QColor("#08090c"))
        painter.drawRoundedRect(bounds, 10, 10)
        if not self._pixmap.isNull():
            target = bounds.adjusted(1, 1, -1, -1)
            scaled = self._pixmap.scaled(
                round(target.width()),
                round(target.height()),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = round(target.x() + ((target.width() - scaled.width()) / 2))
            y = round(target.y() + ((target.height() - scaled.height()) / 2))
            painter.drawPixmap(x, y, scaled)
        painter.end()


class WhatsNewDialog(QDialog):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.destination = ""
        self.setWindowTitle(f"What’s New in Speed Streak {WHATS_NEW_VERSION}")
        self.setModal(True)
        self.setMinimumSize(700, 600)
        self.resize(780, 720)
        self.setStyleSheet(
            "QDialog { background: #0b111a; }"
            "QScrollArea { border: none; background: #0b111a; }"
            "QScrollArea > QWidget > QWidget { background: #0b111a; }"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget(scroll)
        body.setStyleSheet("background: #0b111a;")
        content = QVBoxLayout(body)
        content.setContentsMargins(32, 26, 32, 24)
        content.setSpacing(12)

        content.addWidget(_label(f"What’s new in {WHATS_NEW_VERSION}", body, size=23, color="#f7f9fc", weight=700))
        content.addWidget(_label("Time Boost", body, size=17, color="#f5f8fc", weight=700))
        content.addWidget(
            _label(
                "Time Boost uses charges instead of points. Answer cards to earn charges. Press R before time "
                "runs out to spend a charge and add time.",
                body,
                size=10,
                color="#c5d0df",
            )
        )
        content.addWidget(
            _label(
                "If you often pause or undo to keep your streak, you can turn on No Pause and No Undo. "
                "Charges give you a limited way to get extra time instead.",
                body,
                size=10,
                color="#c5d0df",
            )
        )
        content.addWidget(
            ActualUiImage(
                "time-boost-actual.png",
                "The real Speed Streak Time Boost view with two charges, No Pause, No Undo, and the R shortcut.",
                body,
            )
        )
        content.addWidget(
            _label(
                "Hover over the charges to show No Pause, No Undo, and R. Click the charges or progress bar "
                "to open their settings. Click the R button to change the shortcut.",
                body,
                size=9,
                color="#9eacc0",
            )
        )
        content.addWidget(
            _label(
                "Change Time Boost: Settings → Gameplay    ·    Change R: Settings → Shortcuts",
                body,
                size=9,
                color="#70dbe1",
                weight=700,
            )
        )

        content.addSpacing(7)
        content.addWidget(_label("Legacy Points", body, size=17, color="#f5f8fc", weight=700))
        content.addWidget(
            _label(
                "The previous point and multiplier system is now called Legacy Points. You can switch between "
                "Legacy Points and Time Boost at any time in Settings → Gameplay.",
                body,
                size=10,
                color="#c5d0df",
            )
        )

        content.addSpacing(7)
        content.addWidget(_label("New visuals", body, size=17, color="#f5f8fc", weight=700))
        content.addWidget(
            _label(
                "Singularity and Crystal Reactor are new visual options. Click the visual button at the "
                "bottom-left of Speed Streak to switch.",
                body,
                size=10,
                color="#c5d0df",
            )
        )
        content.addWidget(
            ActualUiImage(
                "visual-options-actual.png",
                "The real Speed Streak visual selector showing Sphere, Singularity, Crystal Reactor, and Brick.",
                body,
            )
        )
        scroll.setWidget(body)
        root.addWidget(scroll, 1)

        footer = QWidget(self)
        footer.setStyleSheet("background: #0e1621; border-top: 1px solid #26364a;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(24, 13, 24, 13)
        footer_layout.setSpacing(11)
        footer_layout.addWidget(
            _label("You can reopen this from Speed Streak → What’s New.", footer, size=9, color="#8493aa"),
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


def show_whats_new_dialog(parent: Optional[QWidget] = None) -> str:
    dialog = WhatsNewDialog(parent)
    dialog.exec()
    return dialog.destination
