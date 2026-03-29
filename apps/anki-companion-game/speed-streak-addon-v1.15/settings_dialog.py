from __future__ import annotations

from typing import Any, Optional

from aqt import mw
from aqt.qt import (
    QButtonGroup,
    QCheckBox,
    QBrush,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
    QPixmap,
    QRectF,
    QRadialGradient,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPalette,
    QPushButton,
    QRadioButton,
    QSlider,
    QScrollArea,
    QSizePolicy,
    Qt,
    QVBoxLayout,
    QWidget,
)

from .anki_flag_colors import get_anki_flag_palette
from .display_mode import (
    DISPLAY_MODE_INLINE,
    DISPLAY_MODE_OPTIONS,
    display_mode_label,
)
from .feedback_catalog import (
    DEFAULT_AUDIO_ENABLED,
    DEFAULT_AUDIO_FILE,
    HAPTIC_EVENT_OPTIONS,
    HAPTIC_PATTERN_OFF,
    HAPTIC_PATTERN_OPTIONS,
    default_haptic_event_patterns,
    haptic_pattern_label,
)
from .render_mode import (
    RENDER_MODE_CLASSIC,
    RENDER_MODE_OPTIONS,
    render_mode_label,
)
from .sphere_mode import (
    SPHERE_MODE_CLASSIC,
    SPHERE_MODE_OPTIONS,
    sphere_mode_label,
)
from .visual_mode import (
    VISUAL_MODE_LIGHTWEIGHT_ROWS,
    VISUAL_MODE_OPTIONS,
    VISUAL_MODE_SPHERE,
    visual_mode_label,
)


FLAG_OPTIONS = [
    (0, "0 - Off"),
    (1, "1 - Red"),
    (2, "2 - Orange"),
    (3, "3 - Green"),
    (4, "4 - Blue"),
    (5, "5 - Pink"),
    (6, "6 - Turquoise"),
    (7, "7 - Purple"),
]

_dialog: Optional["SettingsDialog"] = None

THEMES = [
    ("classic", "Classic", "#071022", "#0b1530"),
    ("cardmatch", "Card Match", "#2F2F31", "#2F2F31"),
    ("graphite", "Graphite", "#1e2126", "#262b33"),
    ("midnight", "Midnight", "#08090c", "#121418"),
    ("forest", "Forest", "#0d1f1a", "#173229"),
    ("ember", "Ember", "#251317", "#341b21"),
    ("violet", "Violet", "#181427", "#251d3a"),
    ("ocean", "Ocean", "#0a1b28", "#113047"),
]

DEFAULT_CUSTOM_COLORS = {
    "core": "#566ed4",
    "red": "#c34f69",
    "yellow": "#c69430",
    "green": "#2b9d73",
    "blue": "#4a74dd",
}

THEME_CUSTOM_COLOR_DEFAULTS = {
    "classic": {
        "core": "#5b6fcf",
        "red": "#c9546d",
        "yellow": "#c89a38",
        "green": "#2ea36f",
        "blue": "#4b7de2",
    },
    "cardmatch": {
        "core": "#84a6c7",
        "red": "#b26a6a",
        "yellow": "#b786ad",
        "green": "#419c5f",
        "blue": "#4d8d8d",
    },
    "graphite": {
        "core": "#6982b8",
        "red": "#b65b70",
        "yellow": "#b48c42",
        "green": "#3d9b79",
        "blue": "#557fd6",
    },
    "midnight": {
        "core": "#566ed4",
        "red": "#c34f69",
        "yellow": "#c69430",
        "green": "#2b9d73",
        "blue": "#4a74dd",
    },
    "forest": {
        "core": "#4f8f9c",
        "red": "#b45a62",
        "yellow": "#b89a43",
        "green": "#2d9a66",
        "blue": "#3d73b8",
    },
    "ember": {
        "core": "#c66a4b",
        "red": "#cf5664",
        "yellow": "#c98a33",
        "green": "#4e9a72",
        "blue": "#4d74c9",
    },
    "violet": {
        "core": "#7761c5",
        "red": "#c15a7f",
        "yellow": "#bc8f3d",
        "green": "#4b9c82",
        "blue": "#5b7ed6",
    },
    "ocean": {
        "core": "#4d8fc2",
        "red": "#bd5c6c",
        "yellow": "#c39932",
        "green": "#2f9a82",
        "blue": "#3e79cc",
    },
}

COLOR_FIELDS = [
    ("core", "Central Orb", "Main color for the center orb."),
    ("red", "Again Satellite", "Used for Again ratings and timeout effects."),
    ("yellow", "Hard Satellite", "Used for Hard ratings."),
    ("green", "Good Satellite", "Used for Good ratings."),
    ("blue", "Easy Satellite", "Used for Easy ratings."),
]

VIBRATION_MODE_DISPLAY_AND_VIBRATION = "display_and_vibration"
VIBRATION_MODE_VIBRATION_ONLY = "vibration_only"

SECTION_STYLE_TOKENS = {
    "actions": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(29, 37, 54, 0.98),
              stop:1 rgba(20, 26, 38, 0.98))
        """,
        "border_color": "rgba(116, 143, 194, 0.20)",
        "title_color": "#b9ccf8",
    },
    "timers": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(25, 39, 45, 0.98),
              stop:1 rgba(18, 28, 33, 0.98))
        """,
        "border_color": "rgba(96, 179, 171, 0.20)",
        "title_color": "#a9e1d9",
    },
    "flags": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(44, 37, 31, 0.98),
              stop:1 rgba(31, 25, 22, 0.98))
        """,
        "border_color": "rgba(203, 160, 101, 0.20)",
        "title_color": "#f0cd93",
    },
    "feedback": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(26, 38, 52, 0.98),
              stop:1 rgba(18, 27, 37, 0.98))
        """,
        "border_color": "rgba(120, 180, 214, 0.20)",
        "title_color": "#b8def1",
    },
    "display_style": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(31, 36, 59, 0.98),
              stop:1 rgba(21, 26, 42, 0.98))
        """,
        "border_color": "rgba(132, 151, 231, 0.20)",
        "title_color": "#b9c4ff",
    },
    "performance": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(40, 34, 39, 0.98),
              stop:1 rgba(27, 23, 28, 0.98))
        """,
        "border_color": "rgba(195, 153, 119, 0.18)",
        "title_color": "#e8c7a6",
    },
    "appearance": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(24, 39, 47, 0.98),
              stop:1 rgba(17, 28, 35, 0.98))
        """,
        "border_color": "rgba(110, 177, 200, 0.20)",
        "title_color": "#b4def0",
    },
    "help": {
        "frame_background": """
            qlineargradient(x1:0, y1:0, x2:0, y2:1,
              stop:0 rgba(28, 39, 33, 0.98),
              stop:1 rgba(21, 29, 24, 0.98))
        """,
        "border_color": "rgba(111, 171, 135, 0.18)",
        "title_color": "#b6dec1",
    },
}

SECTION_DESCRIPTIONS = {
    "actions": "Quick tools and reset actions for this profile.",
    "timers": "Set how long Speed Streak gives you during the question and answer phases.",
    "flags": "Choose which Anki flags Speed Streak uses for time-drain and review-later cards.",
    "feedback": "Control the audio click and controller haptic feedback that fire during review events.",
    "display_style": "Choose where Speed Streak appears and which visual helpers stay visible while you review.",
    "performance": "Choose which visual renderer to use and reduce motion if the effects feel heavy on your computer.",
    "appearance": "Choose a theme and orb palette without changing how the game behaves.",
    "help": "A few reminders for how the review workflow fits together.",
}


def normalize_custom_colors(colors: Optional[dict[str, str]]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    if not colors:
        return normalized
    for key, _, _ in COLOR_FIELDS:
        value = str(colors.get(key, "") or "").strip().lower()
        if not value:
            continue
        if not value.startswith("#"):
            value = f"#{value}"
        if len(value) == 4 and all(ch in "0123456789abcdef#" for ch in value):
            value = "#" + "".join(ch * 2 for ch in value[1:])
        if len(value) == 7 and all(ch in "0123456789abcdef#" for ch in value):
            normalized[key] = value
    return normalized


def theme_default_colors(theme_key: str) -> dict[str, str]:
    normalized = str(theme_key or "midnight").strip().lower() or "midnight"
    return dict(THEME_CUSTOM_COLOR_DEFAULTS.get(normalized, DEFAULT_CUSTOM_COLORS))


class OrbPreviewButton(QPushButton):
    def __init__(self, kind: str, parent: Optional[QWidget] = None) -> None:
        super().__init__("", parent)
        self.kind = str(kind or "core")
        self.color_hex = "#7fb0ff"
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(58, 58)

    def set_preview(self, color_hex: str) -> None:
        self.color_hex = str(color_hex or "#7fb0ff")
        self.update()

    def _adjust(self, color_hex: str, level: float) -> QColor:
        color = QColor(color_hex)
        if not color.isValid():
            return QColor("#7fb0ff")
        return color.lighter(int(100 + (level * 100))) if level >= 0 else color.darker(int(100 + (abs(level) * 100)))

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)

        side = min(self.width(), self.height()) - 8
        left = (self.width() - side) / 2
        top = (self.height() - side) / 2
        bounds = QRectF(left, top, side, side)
        if self.kind == "core":
            self._paint_core(painter, bounds)
        else:
            self._paint_satellite(painter, bounds)

    def _paint_core(self, painter: QPainter, bounds: QRectF) -> None:
        base = QColor(self.color_hex)
        highlight = self._adjust(self.color_hex, 0.82)
        mid = self._adjust(self.color_hex, 0.24)
        deep = self._adjust(self.color_hex, -0.72)

        halo = QRadialGradient(bounds.center(), bounds.width() * 0.78)
        halo.setColorAt(0.0, QColor(base.red(), base.green(), base.blue(), 56))
        halo.setColorAt(0.46, QColor(base.red(), base.green(), base.blue(), 13))
        halo.setColorAt(1.0, QColor(base.red(), base.green(), base.blue(), 0))
        painter.setBrush(QBrush(halo))
        painter.drawEllipse(bounds.adjusted(-8, -8, 8, 8))

        orb = bounds.adjusted(7, 7, -7, -7)
        shell = QRadialGradient(QPointF(orb.left() + (orb.width() * 0.35), orb.top() + (orb.height() * 0.30)), orb.width() * 0.70)
        shell.setColorAt(0.0, highlight)
        shell.setColorAt(0.20, base)
        shell.setColorAt(0.52, mid)
        shell.setColorAt(0.82, deep)
        painter.setBrush(QBrush(shell))
        painter.drawEllipse(orb)

        inset = QRadialGradient(orb.center(), orb.width() * 0.55)
        inset.setColorAt(0.0, QColor(255, 255, 255, 46))
        inset.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(inset))
        painter.drawEllipse(orb.adjusted(2, 2, -2, -2))

    def _paint_satellite(self, painter: QPainter, bounds: QRectF) -> None:
        base = QColor(self.color_hex)
        soft = self._adjust(self.color_hex, 0.72)
        orb_size = bounds.width() * 0.32
        orb = QRectF(
            bounds.left() + (bounds.width() * 0.34),
            bounds.top() + (bounds.height() * 0.34),
            orb_size,
            orb_size,
        )

        glow = QRadialGradient(orb.center(), orb.width() * 1.3)
        glow.setColorAt(0.0, QColor(255, 255, 255, 28))
        glow.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(glow))
        painter.drawEllipse(orb.adjusted(-6, -6, 6, 6))

        shell = QRadialGradient(QPointF(orb.left() + (orb.width() * 0.35), orb.top() + (orb.height() * 0.30)), orb.width() * 0.78)
        shell.setColorAt(0.0, soft)
        shell.setColorAt(1.0, base)
        painter.setBrush(QBrush(shell))
        painter.drawEllipse(orb)


class _WheelGuardMixin:
    def wheelEvent(self, event: Any) -> None:
        event.ignore()


class ScrollSafeComboBox(_WheelGuardMixin, QComboBox):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        popup = QListView(self)
        popup.setObjectName("speedStreakComboPopup")
        popup.setUniformItemSizes(True)
        popup.setStyleSheet(
            """
            QListView#speedStreakComboPopup {
              background: rgba(17, 22, 31, 0.99);
              color: #edf1fb;
              border: 1px solid rgba(116, 128, 153, 0.22);
              outline: none;
            }
            QListView#speedStreakComboPopup::item {
              min-height: 26px;
              padding: 4px 8px;
            }
            QListView#speedStreakComboPopup::item:selected {
              background: rgba(74, 118, 207, 0.92);
              color: #f7f9ff;
            }
            """
        )
        palette = popup.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor("#11161f"))
        palette.setColor(QPalette.ColorRole.Text, QColor("#edf1fb"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor("#4a76cf"))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#f7f9ff"))
        popup.setPalette(palette)
        self.setView(popup)


class ScrollSafeDoubleSpinBox(_WheelGuardMixin, QDoubleSpinBox):
    pass


class ScrollSafeSlider(_WheelGuardMixin, QSlider):
    pass


class ColorCustomizerDialog(QDialog):
    def __init__(self, owner: "SettingsDialog") -> None:
        super().__init__(owner)
        self.owner = owner
        self.draft_colors = dict(owner.custom_colors)
        self.draft_use_custom_timer_colors = bool(owner.use_custom_timer_colors)
        self.draft_timer_color_level = float(owner.timer_color_level)
        self.rows: dict[str, tuple[OrbPreviewButton, QLineEdit]] = {}
        self._picker_dialog: Optional[QColorDialog] = None
        self._picker_key = ""
        self._picker_original_color = ""
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("speedStreakColorPicker")
        self.setStyleSheet(
            """
            QDialog#speedStreakColorPicker {
              background: rgba(4, 8, 20, 168);
            }
            QFrame#speedStreakColorCard {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(7, 16, 34, 248),
                stop:1 rgba(8, 18, 39, 240));
              border: 1px solid rgba(140, 180, 255, 0.18);
              border-radius: 24px;
            }
            QLabel {
              color: #eef3ff;
            }
            QLabel[class="helpText"] {
              color: #96a7cf;
              font-size: 12px;
            }
            QLabel[class="previewLabel"] {
              color: #c7d3ee;
              font-size: 11px;
              font-weight: 700;
            }
            QFrame[class="colorRow"] {
              border-radius: 16px;
              border: 1px solid rgba(255,255,255,0.08);
              background: rgba(255,255,255,0.04);
            }
            QPushButton[class="colorSwatch"] {
              min-width: 58px;
              max-width: 58px;
              min-height: 58px;
              max-height: 58px;
              border-radius: 29px;
              border: 1px solid rgba(255,255,255,0.14);
              background: transparent;
            }
            QLineEdit {
              min-height: 34px;
              padding: 4px 10px;
              border-radius: 12px;
              border: 1px solid rgba(116, 128, 153, 0.22);
              background: rgba(10, 14, 22, 0.94);
              color: #edf1fb;
              font-size: 12px;
              font-weight: 700;
            }
            QPushButton[class="primaryAction"], QPushButton[class="secondaryAction"] {
              color: #edf1fb;
              border-radius: 14px;
              padding: 9px 12px;
              font-size: 12px;
              font-weight: 800;
              border: 1px solid rgba(125, 137, 161, 0.2);
            }
            QPushButton[class="primaryAction"] {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(87, 146, 255, 0.95),
                stop:1 rgba(57, 112, 214, 0.95));
              border-color: rgba(123, 171, 255, 0.55);
            }
            QPushButton[class="secondaryAction"] {
              background: rgba(31, 38, 51, 0.96);
            }
            QFrame#timerPreviewTrack {
              border-radius: 12px;
              border: 1px solid rgba(255,255,255,0.1);
              background: rgba(9, 13, 21, 0.95);
            }
            QFrame[previewSegment="true"] {
              border-radius: 999px;
              border: 1px solid rgba(255,255,255,0.06);
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(42, 42, 42, 42)
        card = QFrame(self)
        card.setObjectName("speedStreakColorCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Orb Colors", card)
        title.setStyleSheet("font-size: 24px; font-weight: 900;")
        copy = QLabel("Choose the center orb color and the four rating satellite colors. The native color chooser opens when you click a swatch.", card)
        copy.setWordWrap(True)
        copy.setProperty("class", "helpText")
        layout.addWidget(title)
        layout.addWidget(copy)

        for key, label, help_text in COLOR_FIELDS:
            row = QFrame(card)
            row.setProperty("class", "colorRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 10, 12, 10)
            row_layout.setSpacing(10)
            copy_layout = QVBoxLayout()
            copy_layout.setSpacing(2)
            title_label = QLabel(label, row)
            title_label.setStyleSheet("font-size: 12px; font-weight: 800;")
            help_label = QLabel(help_text, row)
            help_label.setWordWrap(True)
            help_label.setProperty("class", "helpText")
            copy_layout.addWidget(title_label)
            copy_layout.addWidget(help_label)
            row_layout.addLayout(copy_layout, 1)

            swatch = OrbPreviewButton(key, row)
            swatch.setProperty("class", "colorSwatch")
            swatch.clicked.connect(lambda _=False, color_key=key: self.pick_color(color_key))
            row_layout.addWidget(swatch)

            field = QLineEdit(row)
            field.setMaxLength(7)
            field.setPlaceholderText(theme_default_colors(self.owner.current_theme_key)[key])
            field.editingFinished.connect(lambda color_key=key: self.commit_hex(color_key))
            row_layout.addWidget(field)

            self.rows[key] = (swatch, field)
            layout.addWidget(row)

        self.timer_colors_check = QCheckBox("Use these theme/custom warning colors for both timers", card)
        self.timer_colors_check.setChecked(self.draft_use_custom_timer_colors)
        self.timer_colors_check.toggled.connect(self._sync_timer_preview)
        layout.addWidget(self.timer_colors_check)

        preview_title = QLabel("Timer Fade Preview", card)
        preview_title.setProperty("class", "previewLabel")
        layout.addWidget(preview_title)

        self.timer_preview_track = QFrame(card)
        self.timer_preview_track.setObjectName("timerPreviewTrack")
        preview_layout = QVBoxLayout(self.timer_preview_track)
        preview_layout.setContentsMargins(10, 10, 10, 10)
        preview_layout.setSpacing(8)

        self.timer_preview_bar = QVBoxLayout()
        self.timer_preview_bar.setSpacing(7)
        self.preview_segments: list[tuple[QFrame, QFrame]] = []
        for width in (1.0, 0.75, 0.5, 0.25, 0.08):
            row = QHBoxLayout()
            row.setSpacing(10)
            segment = QFrame(self.timer_preview_track)
            segment.setProperty("previewSegment", "true")
            segment.setFixedHeight(10)
            segment.setMinimumWidth(180)
            fill = QFrame(segment)
            fill.setProperty("previewSegment", "true")
            fill.setFixedHeight(10)
            fill.setFixedWidth(max(12, int(180 * width)))
            fill.move(0, 0)
            self.preview_segments.append((segment, fill))
            label = QLabel(f"{int(width * 100)}%", self.timer_preview_track)
            label.setProperty("class", "helpText")
            label.setFixedWidth(34)
            row.addWidget(label)
            row.addWidget(segment, 1)
            self.timer_preview_bar.addLayout(row)
        preview_layout.addLayout(self.timer_preview_bar)

        slider_row = QHBoxLayout()
        slider_label = QLabel("Timer Brightness", self.timer_preview_track)
        slider_label.setProperty("class", "previewLabel")
        self.timer_level_value = QLabel("", self.timer_preview_track)
        self.timer_level_value.setProperty("class", "helpText")
        slider_row.addWidget(slider_label)
        slider_row.addStretch(1)
        slider_row.addWidget(self.timer_level_value)
        preview_layout.addLayout(slider_row)

        self.timer_level_slider = ScrollSafeSlider(Qt.Orientation.Horizontal, self.timer_preview_track)
        self.timer_level_slider.setRange(-100, 100)
        self.timer_level_slider.setValue(int(round(self.draft_timer_color_level * 100)))
        self.timer_level_slider.valueChanged.connect(self._on_timer_level_changed)
        preview_layout.addWidget(self.timer_level_slider)
        layout.addWidget(self.timer_preview_track)

        actions = QHBoxLayout()
        actions.addStretch(1)
        reset_button = QPushButton("Reset Colors", card)
        reset_button.setProperty("class", "secondaryAction")
        reset_button.clicked.connect(self.reset_colors)
        save_button = QPushButton("Save Colors", card)
        save_button.setProperty("class", "primaryAction")
        save_button.clicked.connect(self.save_and_close)
        actions.addWidget(reset_button)
        actions.addWidget(save_button)
        layout.addLayout(actions)
        outer.addWidget(card)

        self._sync_rows()
        self._sync_timer_preview()
        self.resize(700, 620)

    def resolved_color(self, key: str) -> str:
        return normalize_custom_colors(self.draft_colors).get(key, theme_default_colors(self.owner.current_theme_key)[key])

    def _sync_rows(self) -> None:
        normalized = normalize_custom_colors(self.draft_colors)
        defaults = theme_default_colors(self.owner.current_theme_key)
        for key, _, _ in COLOR_FIELDS:
            swatch, field = self.rows[key]
            color = normalized.get(key, defaults[key])
            swatch.set_preview(color)
            field.setPlaceholderText(defaults[key])
            if field.text() != color:
                field.setText(color)
        self._sync_timer_preview()

    def _adjust_hex(self, hex_color: str, level: float) -> str:
        color = QColor(hex_color)
        if not color.isValid():
            return hex_color
        if level >= 0:
            return str(color.lighter(int(100 + (level * 100))).name())
        return str(color.darker(int(100 + (abs(level) * 100))).name())

    def _timer_preview_colors(self) -> list[str]:
        palette = {
            **theme_default_colors(self.owner.current_theme_key),
            **normalize_custom_colors(self.draft_colors),
        }
        level = self.draft_timer_color_level
        green = self._adjust_hex(palette["green"], level)
        yellow = self._adjust_hex(palette["yellow"], level)
        red = self._adjust_hex(palette["red"], level)
        return [green, green, yellow, red, red]

    def _sync_timer_preview(self) -> None:
        enabled = bool(self.timer_colors_check.isChecked())
        self.timer_preview_track.setVisible(enabled)
        if not enabled:
            return
        for (track, fill), color in zip(self.preview_segments, self._timer_preview_colors()):
            track.setStyleSheet("background: rgba(255,255,255,0.08); border-radius: 999px; border: 1px solid rgba(255,255,255,0.06);")
            fill.setStyleSheet(f"background: {color}; border-radius: 999px; border: none;")
        value = self.timer_level_slider.value() / 100.0
        self.timer_level_value.setText(f"{value:+.2f}")

    def _on_timer_level_changed(self, value: int) -> None:
        self.draft_timer_color_level = max(-1.0, min(1.0, value / 100.0))
        self._sync_timer_preview()

    def pick_color(self, key: str) -> None:
        current = QColor(self.resolved_color(key))
        self._picker_key = key
        self._picker_original_color = self.draft_colors.get(key, "")
        dialog = QColorDialog(current, self)
        dialog.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
        dialog.setWindowTitle(f"Choose {key.title()} Color")
        dialog.currentColorChanged.connect(self._preview_picker_color)
        dialog.colorSelected.connect(self._accept_picker_color)
        dialog.rejected.connect(self._cancel_picker_color)
        self._picker_dialog = dialog
        dialog.open()

    def _preview_picker_color(self, color: QColor) -> None:
        if not color.isValid() or not self._picker_key:
            return
        self.draft_colors[self._picker_key] = str(color.name())
        self._sync_rows()

    def _accept_picker_color(self, color: QColor) -> None:
        if not self._picker_key or not color.isValid():
            self._clear_picker_state()
            return
        self.draft_colors[self._picker_key] = str(color.name())
        self._sync_rows()
        self._clear_picker_state()

    def _cancel_picker_color(self) -> None:
        if not self._picker_key:
            self._clear_picker_state()
            return
        if self._picker_original_color:
            self.draft_colors[self._picker_key] = self._picker_original_color
        else:
            self.draft_colors.pop(self._picker_key, None)
        self._sync_rows()
        self._clear_picker_state()

    def _clear_picker_state(self) -> None:
        self._picker_dialog = None
        self._picker_key = ""
        self._picker_original_color = ""

    def commit_hex(self, key: str) -> None:
        _, field = self.rows[key]
        text = field.text().strip()
        if not text:
            self.draft_colors.pop(key, None)
        else:
            normalized = normalize_custom_colors({key: text}).get(key)
            if normalized:
                self.draft_colors[key] = normalized
        self._sync_rows()

    def reset_colors(self) -> None:
        self.draft_colors = {}
        self.draft_use_custom_timer_colors = False
        self.timer_colors_check.setChecked(False)
        self.draft_timer_color_level = 0.0
        self.timer_level_slider.setValue(0)
        self._sync_rows()

    def save_and_close(self) -> None:
        self.owner.set_custom_colors(
            normalize_custom_colors(self.draft_colors),
            bool(self.timer_colors_check.isChecked()),
            float(self.draft_timer_color_level),
        )
        self.close()


class SidebarSwitch(QCheckBox):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("", parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(54, 30)

    def paintEvent(self, _event: Any) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        track_rect = QRectF(3, 5, self.width() - 6, self.height() - 10)
        knob_size = track_rect.height() - 4
        knob_x = track_rect.right() - knob_size - 2 if self.isChecked() else track_rect.left() + 2
        knob_rect = QRectF(knob_x, track_rect.top() + 2, knob_size, knob_size)

        track_gradient = QLinearGradient(track_rect.topLeft(), track_rect.topRight())
        if self.isChecked():
            track_gradient.setColorAt(0.0, QColor("#5f9cff"))
            track_gradient.setColorAt(1.0, QColor("#7fb0ff"))
            border_color = QColor(180, 214, 255, 120)
        else:
            track_gradient.setColorAt(0.0, QColor(40, 47, 61, 235))
            track_gradient.setColorAt(1.0, QColor(24, 30, 41, 235))
            border_color = QColor(125, 138, 162, 86)

        if not self.isEnabled():
            painter.setOpacity(0.45)

        painter.setPen(QPen(border_color, 1))
        painter.setBrush(track_gradient)
        painter.drawRoundedRect(track_rect, track_rect.height() / 2, track_rect.height() / 2)

        knob_gradient = QRadialGradient(knob_rect.center(), knob_rect.width() * 0.65)
        knob_gradient.setColorAt(0.0, QColor(255, 255, 255, 250))
        knob_gradient.setColorAt(1.0, QColor(222, 231, 245, 250))
        painter.setPen(QPen(QColor(255, 255, 255, 48), 1))
        painter.setBrush(knob_gradient)
        painter.drawEllipse(knob_rect)

        if self.hasFocus():
            focus_rect = QRectF(1.5, 3.5, self.width() - 3, self.height() - 7)
            painter.setOpacity(1.0)
            painter.setPen(QPen(QColor(132, 181, 255, 170), 1.4))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(focus_rect, focus_rect.height() / 2, focus_rect.height() / 2)

        painter.end()

    def hitButton(self, pos: Any) -> bool:
        return self.rect().contains(pos)


class ThemePickerDialog(QDialog):
    def __init__(self, owner: "SettingsDialog") -> None:
        super().__init__(owner)
        self.owner = owner
        self.setModal(True)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("speedStreakThemePicker")
        self.setStyleSheet(
            """
            QDialog#speedStreakThemePicker {
              background: rgba(4, 8, 20, 168);
            }
            QFrame#themePickerCard {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(7, 16, 34, 248),
                stop:1 rgba(8, 18, 39, 240));
              border: 1px solid rgba(140, 180, 255, 0.18);
              border-radius: 24px;
            }
            QLabel {
              color: #eef3ff;
            }
            QPushButton {
              color: #eef3ff;
              border-radius: 16px;
              padding: 10px 12px;
              font-size: 12px;
              font-weight: 800;
              border: 1px solid rgba(255,255,255,0.12);
              background: rgba(255,255,255,0.06);
            }
            QPushButton:hover {
              background: rgba(255,255,255,0.12);
            }
            QPushButton[current="true"] {
              border-color: rgba(127,176,255,0.36);
              background: rgba(127,176,255,0.18);
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(42, 42, 42, 42)
        card = QFrame(self)
        card.setObjectName("themePickerCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        title = QLabel("Choose A Theme", card)
        title.setStyleSheet("font-size: 24px; font-weight: 900;")
        copy = QLabel("Pick a night-mode palette for the sidebar.", card)
        copy.setStyleSheet("color: #96a7cf; font-size: 13px;")
        layout.addWidget(title)
        layout.addWidget(copy)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)
        current = self.owner.current_theme_key
        for index, (key, label, top, bottom) in enumerate(THEMES):
            button = QPushButton(label, card)
            button.setProperty("current", "true" if key == current else "false")
            button.setMinimumHeight(72)
            button.setStyleSheet(
                button.styleSheet()
                + f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {top}, stop:1 {bottom});"
            )
            button.clicked.connect(lambda _=False, theme_key=key: self._pick(theme_key))
            row, col = divmod(index, 2)
            grid.addWidget(button, row, col)
        layout.addLayout(grid)
        outer.addWidget(card)
        self.resize(620, 520)

    def _pick(self, theme_key: str) -> None:
        self.owner.set_theme(theme_key)
        self.close()


class SettingsDialog(QDialog):
    def __init__(self, controller: Any) -> None:
        super().__init__(mw)
        self.controller = controller
        self._syncing = False
        self.custom_colors: dict[str, str] = {}
        self.use_custom_timer_colors = False
        self.timer_color_level = 0.0
        self.haptic_event_patterns = default_haptic_event_patterns()
        self.haptic_event_combos: dict[str, ScrollSafeComboBox] = {}
        self.haptic_preview_buttons: dict[str, QPushButton] = {}
        self.flag_palette = get_anki_flag_palette()

        self.setModal(False)
        self.setWindowTitle("Speed Streak Settings")
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setObjectName("speedStreakSettingsDialog")
        self.setStyleSheet(
            """
            QDialog#speedStreakSettingsDialog {
              background: #0d1117;
            }
            QFrame#speedStreakSettingsCard {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(18, 24, 35, 250),
                stop:1 rgba(13, 18, 27, 250));
              border: 1px solid rgba(144, 157, 181, 0.14);
              border-radius: 20px;
            }
            QFrame#speedStreakSettingsHero {
              background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(101, 140, 214, 0.10),
                stop:0.58 rgba(255, 255, 255, 0.02),
                stop:1 rgba(255, 255, 255, 0.01));
              border: 1px solid rgba(139, 153, 183, 0.12);
              border-radius: 16px;
            }
            QLabel#speedStreakSettingsTitle {
              color: #f2f5fb;
              font-size: 24px;
              font-weight: 800;
            }
            QLabel#speedStreakSettingsSub {
              color: #9eaabd;
              font-size: 12px;
            }
            QLabel[class="sectionTitle"] {
              color: #eef2fb;
              font-size: 15px;
              font-weight: 750;
            }
            QLabel#speedStreakHeroEyebrow {
              color: #8eb6ff;
              font-size: 11px;
              font-weight: 800;
              letter-spacing: 1px;
            }
            QLabel[class="sectionCopy"] {
              color: #93a1b8;
              font-size: 11px;
            }
            QLabel[class="fieldLabel"] {
              color: #e5eaf5;
              font-size: 12px;
              font-weight: 700;
            }
            QLabel[class="helpText"] {
              color: #95a3ba;
              font-size: 11px;
            }
            QLabel#errorLabel {
              color: #f58ea5;
              font-size: 12px;
              font-weight: 700;
            }
            QPushButton[class="primaryAction"], QPushButton[class="secondaryAction"], QPushButton[class="reviewLaterAction"], QPushButton#speedStreakSettingsClose {
              color: #edf1fb;
              border-radius: 12px;
              padding: 8px 12px;
              font-size: 12px;
              font-weight: 800;
              border: 1px solid rgba(125, 137, 161, 0.18);
            }
            QPushButton[class="primaryAction"] {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(95, 146, 245, 0.94),
                stop:1 rgba(65, 111, 202, 0.94));
              border-color: rgba(127, 169, 245, 0.42);
            }
            QPushButton[class="reviewLaterAction"] {
              background: rgba(44, 57, 81, 0.96);
              border-color: rgba(103, 143, 214, 0.26);
            }
            QPushButton[class="secondaryAction"], QPushButton#speedStreakSettingsClose {
              background: rgba(33, 40, 54, 0.96);
            }
            QPushButton[class="dangerAction"] {
              color: #fff2f4;
              border-radius: 12px;
              padding: 8px 12px;
              font-size: 12px;
              font-weight: 800;
              border: 1px solid rgba(198, 103, 121, 0.24);
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(116, 50, 66, 0.92),
                stop:1 rgba(82, 35, 46, 0.92));
            }
            QPushButton[class="primaryAction"]:hover {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(110, 158, 250, 0.96),
                stop:1 rgba(76, 122, 214, 0.96));
            }
            QPushButton[class="secondaryAction"]:hover, QPushButton[class="reviewLaterAction"]:hover, QPushButton#speedStreakSettingsClose:hover {
              background: rgba(42, 50, 66, 0.98);
            }
            QPushButton[class="dangerAction"]:hover {
              background: rgba(135, 56, 74, 0.96);
            }
            QFrame[class="sectionCard"] {
              border-radius: 16px;
            }
            QFrame[class="settingRow"], QFrame[class="toggleBlock"], QFrame[class="buttonRowGroup"] {
              background: rgba(255, 255, 255, 0.035);
              border: 1px solid rgba(151, 164, 188, 0.10);
              border-radius: 14px;
            }
            QDoubleSpinBox, QComboBox {
              min-height: 34px;
              padding: 4px 10px;
              border-radius: 12px;
              border: 1px solid rgba(127, 142, 169, 0.18);
              background: rgba(12, 17, 26, 0.92);
              color: #edf1fb;
              font-size: 12px;
              font-weight: 700;
            }
            QDoubleSpinBox:hover, QComboBox:hover {
              border-color: rgba(141, 171, 227, 0.28);
            }
            QDoubleSpinBox:focus, QComboBox:focus {
              border-color: rgba(105, 156, 255, 0.54);
            }
            QComboBox::drop-down {
              border: none;
              width: 22px;
              background: transparent;
            }
            QComboBox QAbstractItemView {
              border: 1px solid rgba(116, 128, 153, 0.22);
              background: rgba(17, 22, 31, 0.99);
              color: #edf1fb;
              selection-background-color: rgba(74, 118, 207, 0.92);
              selection-color: #f7f9ff;
              outline: none;
            }
            QCheckBox, QRadioButton {
              color: #edf1fb;
              font-size: 12px;
              font-weight: 700;
              spacing: 8px;
            }
            QCheckBox::indicator, QRadioButton::indicator {
              width: 15px;
              height: 15px;
            }
            QScrollArea {
              border: none;
              background: transparent;
            }
            QScrollArea > QWidget > QWidget {
              background: transparent;
            }
            QScrollBar:vertical {
              background: rgba(255,255,255,0.02);
              width: 8px;
              margin: 4px 0 4px 0;
              border-radius: 4px;
            }
            QScrollBar::handle:vertical {
              background: rgba(117, 140, 184, 0.34);
              min-height: 24px;
              border-radius: 4px;
            }
            QFrame#speedStreakAppearancePreview {
              border-radius: 14px;
              border: 1px solid rgba(112, 124, 149, 0.14);
              background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(25, 32, 44, 0.94),
                stop:1 rgba(16, 21, 30, 0.94));
            }
            QLabel#speedStreakPreviewTitle {
              color: #eef2fb;
              font-size: 12px;
              font-weight: 800;
            }
            QLabel#speedStreakPreviewBody {
              color: #98a3b8;
              font-size: 11px;
            }
            QFrame[swatch="true"] {
              border-radius: 7px;
              border: 1px solid rgba(255,255,255,0.06);
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)

        card = QFrame(self)
        card.setObjectName("speedStreakSettingsCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 16)
        card_layout.setSpacing(14)

        hero = QFrame(card)
        hero.setObjectName("speedStreakSettingsHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(16, 14, 14, 14)
        hero_layout.setSpacing(12)

        header = QVBoxLayout()
        eyebrow = QLabel("Speed Streak", hero)
        eyebrow.setObjectName("speedStreakHeroEyebrow")
        title = QLabel("Settings", hero)
        title.setObjectName("speedStreakSettingsTitle")
        subtitle = QLabel("Tune timers, flags, feedback, modes, and appearance.", hero)
        subtitle.setObjectName("speedStreakSettingsSub")
        header.addWidget(eyebrow)
        header.addWidget(title)
        header.addWidget(subtitle)
        hero_layout.addLayout(header, 1)
        close_button = QPushButton("Close", hero)
        close_button.setObjectName("speedStreakSettingsClose")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.close)
        hero_layout.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        card_layout.addWidget(hero)

        scroll = QScrollArea(card)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setStyleSheet("background: transparent;")

        body = QWidget(scroll)
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(2, 2, 8, 2)
        body_layout.setSpacing(12)

        body_layout.addWidget(self._build_timers_section(body))
        body_layout.addWidget(self._build_flags_section(body))
        body_layout.addWidget(self._build_display_style_section(body))
        body_layout.addWidget(self._build_feedback_section(body))
        body_layout.addWidget(self._build_performance_section(body))
        body_layout.addWidget(self._build_appearance_section(body))
        body_layout.addWidget(self._build_actions_section(body))
        body_layout.addStretch(1)

        scroll.setWidget(body)
        card_layout.addWidget(scroll, 1)

        self.error_label = QLabel("", card)
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        card_layout.addWidget(self.error_label)

        outer.addWidget(card, 1)
        self.sync_from_state()

        self.setMinimumSize(760, 700)
        if mw is not None:
            self.resize(min(860, max(780, int(mw.width() * 0.58))), min(860, max(720, int(mw.height() * 0.82))))
        else:
            self.resize(820, 780)

    def closeEvent(self, event: Any) -> None:
        global _dialog
        if _dialog is self:
            _dialog = None
        super().closeEvent(event)

    def _build_section_card(self, parent: QWidget, title: str, accent: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(parent)
        frame.setProperty("class", "sectionCard")
        frame.setProperty("accent", accent)
        frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        frame.setObjectName(f"speedStreakSectionCard_{accent}")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self._apply_section_card_style(frame, accent)
        heading = QLabel(title, frame)
        heading.setProperty("class", "sectionTitle")
        heading.setStyleSheet(f"color: {SECTION_STYLE_TOKENS.get(accent, SECTION_STYLE_TOKENS['appearance'])['title_color']};")
        layout.addWidget(heading)
        description = SECTION_DESCRIPTIONS.get(accent, "")
        if description:
            copy = QLabel(description, frame)
            copy.setWordWrap(True)
            copy.setProperty("class", "sectionCopy")
            layout.addWidget(copy)
        return frame, layout

    def _apply_section_card_style(self, frame: QFrame, accent: str) -> None:
        tokens = SECTION_STYLE_TOKENS.get(accent, SECTION_STYLE_TOKENS["appearance"])
        frame.setStyleSheet(
            f"""
            QFrame#{frame.objectName()} {{
              background: {tokens["frame_background"].strip()};
              border: 1px solid {tokens["border_color"]};
              border-radius: 18px;
            }}
            """
        )

    def _build_setting_row(
        self,
        parent: QWidget,
        label_text: str,
        help_text: str,
        control: QWidget,
        *,
        control_width: int = 176,
    ) -> QFrame:
        row = QFrame(parent)
        row.setProperty("class", "settingRow")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        copy = QVBoxLayout()
        copy.setSpacing(3)
        label = QLabel(label_text, row)
        label.setProperty("class", "fieldLabel")
        copy.addWidget(label)
        if help_text:
            help_label = QLabel(help_text, row)
            help_label.setWordWrap(True)
            help_label.setProperty("class", "helpText")
            copy.addWidget(help_label)
        layout.addLayout(copy)

        control.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        if control_width > 0:
            control.setMinimumWidth(control_width)
            control.setMaximumWidth(max(control_width, int(control_width * 1.2)))
        layout.addWidget(control, 0, Qt.AlignmentFlag.AlignLeft)
        return row

    def _build_toggle_block(self, parent: QWidget, checkbox: QWidget, help_text: str) -> QFrame:
        block = QFrame(parent)
        block.setProperty("class", "toggleBlock")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        layout.addWidget(checkbox)
        if help_text:
            help_label = QLabel(help_text, block)
            help_label.setWordWrap(True)
            help_label.setProperty("class", "helpText")
            layout.addWidget(help_label)
        return block

    def _build_button_group(self, parent: QWidget) -> tuple[QFrame, QGridLayout]:
        block = QFrame(parent)
        block.setProperty("class", "buttonRowGroup")
        layout = QGridLayout(block)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(8)
        return block, layout

    def _build_inline_controls(self, parent: QWidget, *widgets: QWidget) -> QWidget:
        container = QWidget(parent)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        for index, widget in enumerate(widgets):
            stretch = 1 if index == 0 else 0
            layout.addWidget(widget, stretch)
        return container

    def _build_timers_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Timers", "timers")
        self.question_spin = ScrollSafeDoubleSpinBox(frame)
        self.question_spin.setDecimals(1)
        self.question_spin.setRange(1.0, 999.0)
        self.question_spin.setSingleStep(0.5)
        self.question_spin.setSuffix(" s")
        self.question_spin.valueChanged.connect(self.persist_settings)
        self.answer_spin = ScrollSafeDoubleSpinBox(frame)
        self.answer_spin.setDecimals(1)
        self.answer_spin.setRange(1.0, 999.0)
        self.answer_spin.setSingleStep(0.5)
        self.answer_spin.setSuffix(" s")
        self.answer_spin.valueChanged.connect(self.persist_settings)

        layout.addWidget(
            self._build_setting_row(
                frame,
                "Question time",
                "How long you give yourself before a question is treated as too slow.",
                self.question_spin,
                control_width=148,
            )
        )
        layout.addWidget(
            self._build_setting_row(
                frame,
                "Answer time",
                "How long the answer side stays on its timer once the card is revealed.",
                self.answer_spin,
                control_width=148,
            )
        )
        return frame

    def _build_flags_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Flags", "flags")
        self.time_drain_combo = ScrollSafeComboBox(frame)
        self.time_drain_combo.setObjectName("speedStreakTimeDrainCombo")
        self.time_drain_combo.currentIndexChanged.connect(self._on_flag_combo_changed)
        self.review_later_combo = ScrollSafeComboBox(frame)
        self.review_later_combo.setObjectName("speedStreakReviewLaterCombo")
        self.review_later_combo.currentIndexChanged.connect(self._on_flag_combo_changed)

        layout.addWidget(
            self._build_setting_row(
                frame,
                "Time Drain flag",
                "Used for cards you want to bury quickly and deal with outside the speed-focused session.",
                self.time_drain_combo,
                control_width=210,
            )
        )
        layout.addWidget(
            self._build_setting_row(
                frame,
                "Review Later flag",
                "Used for cards you want to revisit more carefully after you finish the main review flow.",
                self.review_later_combo,
                control_width=210,
            )
        )
        return frame

    def _build_display_style_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Display Style", "display_style")
        self.display_mode_combo = ScrollSafeComboBox(frame)
        for value, label in DISPLAY_MODE_OPTIONS:
            self.display_mode_combo.addItem(label, value)
        self.display_mode_combo.currentIndexChanged.connect(self.persist_settings)
        layout.addWidget(
            self._build_setting_row(
                frame,
                "Display mode",
                "Inline Left Pane keeps the dedicated Speed Streak column. Compatibility Window leaves Anki's "
                "review layout untouched and opens Speed Streak in a floating window, which is recommended for "
                "AMBOSS, AnkiHub, and other reviewer UI add-ons.",
                self.display_mode_combo,
                control_width=240,
            )
        )

        self.show_card_timer_check = QCheckBox("Top Card Timer", frame)
        self.show_card_timer_check.toggled.connect(self.persist_settings)
        layout.addWidget(self._build_toggle_block(frame, self.show_card_timer_check, "Show a horizontal timer bar above the review card."))
        return frame

    def _build_feedback_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Feedback", "feedback")

        audio_group = QFrame(frame)
        audio_group.setProperty("class", "settingRow")
        audio_layout = QVBoxLayout(audio_group)
        audio_layout.setContentsMargins(12, 12, 12, 12)
        audio_layout.setSpacing(8)
        audio_title = QLabel("Audio Feedback", audio_group)
        audio_title.setProperty("class", "fieldLabel")
        audio_copy = QLabel(
            "Audio feedback is off by default. Choose one file from the add-on's Audio folder and preview it here before turning it on.",
            audio_group,
        )
        audio_copy.setWordWrap(True)
        audio_copy.setProperty("class", "helpText")
        audio_layout.addWidget(audio_title)
        audio_layout.addWidget(audio_copy)

        self.audio_enabled_switch = SidebarSwitch(audio_group)
        self.audio_enabled_switch.toggled.connect(self._on_audio_enabled_toggled)
        audio_layout.addWidget(
            self._build_setting_row(
                audio_group,
                "Audio feedback",
                "Default: Off.",
                self.audio_enabled_switch,
                control_width=0,
            )
        )

        self.audio_file_combo = ScrollSafeComboBox(audio_group)
        self.audio_file_combo.currentIndexChanged.connect(self._on_audio_file_changed)
        self.audio_preview_button = QPushButton("Play", audio_group)
        self.audio_preview_button.setProperty("class", "secondaryAction")
        self.audio_preview_button.clicked.connect(self._preview_audio_feedback)
        audio_controls = self._build_inline_controls(audio_group, self.audio_file_combo, self.audio_preview_button)
        audio_layout.addWidget(
            self._build_setting_row(
                audio_group,
                "Audio file",
                f"Choose any clip in the Audio folder. Preview works even while audio feedback is off. Default clip: {DEFAULT_AUDIO_FILE}.",
                audio_controls,
                control_width=340,
            )
        )
        layout.addWidget(audio_group)

        haptics_group = QFrame(frame)
        haptics_group.setProperty("class", "settingRow")
        haptics_layout = QVBoxLayout(haptics_group)
        haptics_layout.setContentsMargins(12, 12, 12, 12)
        haptics_layout.setSpacing(8)
        haptics_title = QLabel("Haptic Feedback", haptics_group)
        haptics_title.setProperty("class", "fieldLabel")
        haptics_copy = QLabel(
            "Haptics stay on by default. Each event below shows when it fires and what the original default pattern was.",
            haptics_group,
        )
        haptics_copy.setWordWrap(True)
        haptics_copy.setProperty("class", "helpText")
        haptics_layout.addWidget(haptics_title)
        haptics_layout.addWidget(haptics_copy)

        self.haptics_enabled_switch = SidebarSwitch(haptics_group)
        self.haptics_enabled_switch.toggled.connect(self._on_vibration_enabled_toggled)
        haptics_layout.addWidget(
            self._build_setting_row(
                haptics_group,
                "Haptic feedback",
                "Default: On.",
                self.haptics_enabled_switch,
                control_width=0,
            )
        )

        self.feedback_mode_group = QFrame(haptics_group)
        self.feedback_mode_group.setProperty("class", "buttonRowGroup")
        feedback_layout = QVBoxLayout(self.feedback_mode_group)
        feedback_layout.setContentsMargins(12, 12, 12, 12)
        feedback_layout.setSpacing(8)
        self.feedback_mode_buttons = QButtonGroup(self.feedback_mode_group)
        self.feedback_mode_buttons.setExclusive(True)
        self.display_and_vibration_radio = QRadioButton("Display + Haptics", self.feedback_mode_group)
        self.feedback_mode_buttons.addButton(self.display_and_vibration_radio)
        self.display_and_vibration_radio.toggled.connect(self._on_feedback_mode_changed)
        feedback_layout.addWidget(
            self._build_toggle_block(
                self.feedback_mode_group,
                self.display_and_vibration_radio,
                "Keep the visual display on and use haptics alongside it.",
            )
        )
        self.vibration_only_radio = QRadioButton("Haptics Only", self.feedback_mode_group)
        self.feedback_mode_buttons.addButton(self.vibration_only_radio)
        self.vibration_only_radio.toggled.connect(self._on_feedback_mode_changed)
        feedback_layout.addWidget(
            self._build_toggle_block(
                self.feedback_mode_group,
                self.vibration_only_radio,
                "Turn off streak and timer visuals, disable appearance editing, and keep only haptics.",
            )
        )
        haptics_layout.addWidget(self.feedback_mode_group)

        for item in HAPTIC_EVENT_OPTIONS:
            event_key = item["event"]
            combo = ScrollSafeComboBox(haptics_group)
            for pattern_key, label in HAPTIC_PATTERN_OPTIONS:
                combo.addItem(label, pattern_key)
            combo.currentIndexChanged.connect(lambda _index=0, key=event_key: self._on_haptic_pattern_changed(key))
            self.haptic_event_combos[event_key] = combo

            preview_button = QPushButton("Test", haptics_group)
            preview_button.setProperty("class", "secondaryAction")
            preview_button.clicked.connect(lambda _=False, key=event_key: self._preview_haptic_feedback(key))
            self.haptic_preview_buttons[event_key] = preview_button

            controls = self._build_inline_controls(haptics_group, combo, preview_button)
            default_label = haptic_pattern_label(item["default_pattern"])
            haptics_layout.addWidget(
                self._build_setting_row(
                    haptics_group,
                    item["label"],
                    f"{item['description']} Default: {default_label}.",
                    controls,
                    control_width=340,
                )
            )

        haptic_note = QLabel(
            "Haptic previews use the currently selected pattern for that event. They need a connected controller with native XInput rumble support.",
            haptics_group,
        )
        haptic_note.setWordWrap(True)
        haptic_note.setProperty("class", "helpText")
        haptics_layout.addWidget(haptic_note)
        layout.addWidget(haptics_group)

        return frame

    def _build_performance_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Performance", "performance")
        self.visual_mode_combo = ScrollSafeComboBox(frame)
        for value, label in VISUAL_MODE_OPTIONS:
            self.visual_mode_combo.addItem(label, value)
        self.visual_mode_combo.currentIndexChanged.connect(self._on_visual_mode_changed)
        layout.addWidget(
            self._build_setting_row(
                frame,
                "Visual mode",
                "Choose between the legacy sphere presentation and the alternate lightweight rows presentation.",
                self.visual_mode_combo,
                control_width=250,
            )
        )

        self.sphere_settings_group = QFrame(frame)
        self.sphere_settings_group.setProperty("class", "settingRow")
        sphere_layout = QVBoxLayout(self.sphere_settings_group)
        sphere_layout.setContentsMargins(12, 12, 12, 12)
        sphere_layout.setSpacing(8)
        sphere_title = QLabel("Sphere/Satellites Settings", self.sphere_settings_group)
        sphere_title.setProperty("class", "fieldLabel")
        sphere_copy = QLabel(
            "These are the sphere controls from v1.14, plus an alternate consolidate renderer that compresses each completed bank of 10 into a static summary ring.",
            self.sphere_settings_group,
        )
        sphere_copy.setWordWrap(True)
        sphere_copy.setProperty("class", "helpText")
        sphere_layout.addWidget(sphere_title)
        sphere_layout.addWidget(sphere_copy)
        self.sphere_mode_combo = ScrollSafeComboBox(frame)
        for value, label in SPHERE_MODE_OPTIONS:
            self.sphere_mode_combo.addItem(label, value)
        self.sphere_mode_combo.currentIndexChanged.connect(self.persist_settings)
        sphere_layout.addWidget(
            self._build_setting_row(
                self.sphere_settings_group,
                "Satellite mode",
                "Classic Orbit keeps the familiar live rings. Consolidate turns every completed bank of 10 into a static donut ring and keeps only the current outer orbit live.",
                self.sphere_mode_combo,
                control_width=230,
            )
        )
        self.render_mode_combo = ScrollSafeComboBox(frame)
        for value, label in RENDER_MODE_OPTIONS:
            self.render_mode_combo.addItem(label, value)
        self.render_mode_combo.currentIndexChanged.connect(self.persist_settings)
        sphere_layout.addWidget(
            self._build_setting_row(
                self.sphere_settings_group,
                "Render mode",
                "Classic keeps the original continuous visual update style. Low Resource keeps smoother timer updates while avoiding the continuous browser animation loop. Ultra Low Resource steps the timers every half second, freezes satellite motion, and skips extra flare effects.",
                self.render_mode_combo,
                control_width=230,
            )
        )
        self.orbit_animation_check = QCheckBox("Orb Animation", frame)
        self.orbit_animation_check.toggled.connect(self.persist_settings)
        sphere_layout.addWidget(
            self._build_toggle_block(
                self.sphere_settings_group,
                self.orbit_animation_check,
                "Turn off the orb and satellite animation if your computer struggles, and show only the streak number instead.",
            )
        )
        layout.addWidget(self.sphere_settings_group)

        self.rows_settings_group = QFrame(frame)
        self.rows_settings_group.setProperty("class", "settingRow")
        rows_layout = QVBoxLayout(self.rows_settings_group)
        rows_layout.setContentsMargins(12, 12, 12, 12)
        rows_layout.setSpacing(8)
        rows_title = QLabel("Lightweight Rows Settings", self.rows_settings_group)
        rows_title.setProperty("class", "fieldLabel")
        rows_copy = QLabel("This is the alternate low-activity view. It keeps motion short and progress chunked.", self.rows_settings_group)
        rows_copy.setWordWrap(True)
        rows_copy.setProperty("class", "helpText")
        rows_layout.addWidget(rows_title)
        rows_layout.addWidget(rows_copy)
        self.reduced_motion_check = QCheckBox("Reduced Motion", frame)
        self.reduced_motion_check.toggled.connect(self.persist_settings)
        rows_layout.addWidget(
            self._build_toggle_block(
                self.rows_settings_group,
                self.reduced_motion_check,
                "Keeps feedback short and subtle so the lightweight view stays calm and battery-friendly.",
            )
        )
        note = QLabel("Lightweight mode minimizes CPU/GPU activity.", self.rows_settings_group)
        note.setWordWrap(True)
        note.setProperty("class", "helpText")
        rows_layout.addWidget(note)
        layout.addWidget(self.rows_settings_group)
        self._sync_feedback_controls()
        self._sync_visual_mode_controls()
        return frame

    def _build_appearance_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Appearance", "appearance")
        self.appearance_section = frame
        self.appearance_value = QLabel("", frame)
        self.appearance_value.setProperty("class", "fieldLabel")
        self.appearance_value.setWordWrap(True)
        layout.addWidget(self.appearance_value)
        self.color_value = QLabel("", frame)
        self.color_value.setProperty("class", "fieldLabel")
        self.color_value.setWordWrap(True)
        layout.addWidget(self.color_value)
        preview = QFrame(frame)
        preview.setObjectName("speedStreakAppearancePreview")
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(12, 10, 12, 10)
        preview_layout.setSpacing(7)
        preview_title = QLabel("Theme Preview", preview)
        preview_title.setObjectName("speedStreakPreviewTitle")
        preview_body = QLabel("Live palette swatches help you preview the sidebar mood before applying it.", preview)
        preview_body.setWordWrap(True)
        preview_body.setObjectName("speedStreakPreviewBody")
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(8)
        self.preview_swatches: list[QFrame] = []
        for _ in range(4):
            swatch = QFrame(preview)
            swatch.setProperty("swatch", "true")
            swatch.setFixedSize(28, 18)
            self.preview_swatches.append(swatch)
            swatch_row.addWidget(swatch)
        swatch_row.addStretch(1)
        preview_layout.addWidget(preview_title)
        preview_layout.addWidget(preview_body)
        preview_layout.addLayout(swatch_row)
        layout.addWidget(preview)
        button_group, button_layout = self._build_button_group(frame)
        appearance_button = QPushButton("Choose Theme", frame)
        appearance_button.setProperty("class", "primaryAction")
        appearance_button.clicked.connect(self.open_theme_picker)
        color_button = QPushButton("Customize Orb Colors", frame)
        color_button.setProperty("class", "secondaryAction")
        color_button.clicked.connect(self.open_color_picker)
        button_layout.addWidget(appearance_button, 0, 0)
        button_layout.addWidget(color_button, 1, 0)
        layout.addWidget(button_group)
        return frame

    def _build_actions_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Actions", "actions")
        button_group, grid = self._build_button_group(frame)

        review_later_button = QPushButton("Review Later Manager", frame)
        review_later_button.setProperty("class", "reviewLaterAction")
        review_later_button.clicked.connect(self.open_review_later_manager)

        stats_button = QPushButton("Show Stats (Work in Progress)", frame)
        stats_button.setProperty("class", "secondaryAction")
        stats_button.clicked.connect(self.open_stats)

        default_button = QPushButton("Default Settings", frame)
        default_button.setProperty("class", "secondaryAction")
        default_button.clicked.connect(self.reset_defaults)

        reset_button = QPushButton("Reset Game", frame)
        reset_button.setProperty("class", "dangerAction")
        reset_button.clicked.connect(self.reset_game)

        grid.addWidget(review_later_button, 0, 0, 1, 2)
        grid.addWidget(stats_button, 1, 0, 1, 2)
        grid.addWidget(default_button, 2, 0)
        grid.addWidget(reset_button, 2, 1)
        layout.addWidget(button_group)
        return frame

    def _build_help_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Help", "help")
        help_text = QLabel(
            "Press P to pause or unpause. Time Drain warns you when a flagged card is consuming time. "
            "Review Later marks cards to revisit later and pairs with the Review Later Manager.",
            frame,
        )
        help_text.setWordWrap(True)
        help_text.setProperty("class", "helpText")
        layout.addWidget(help_text)
        return frame

    def sync_from_state(self) -> None:
        state = self.controller.engine.state
        self._syncing = True
        try:
            self.flag_palette = get_anki_flag_palette()
            self.question_spin.setValue(state.question_limit_ms / 1000)
            self.answer_spin.setValue(state.review_limit_ms / 1000)
            self._populate_flag_combos(state.time_drain_flag, state.review_later_flag)
            self.display_mode_combo.setCurrentIndex(
                max(0, self.display_mode_combo.findData(getattr(self.controller, "display_mode", DISPLAY_MODE_INLINE)))
            )
            self.visual_mode_combo.setCurrentIndex(
                max(0, self.visual_mode_combo.findData(getattr(self.controller, "visual_mode", VISUAL_MODE_LIGHTWEIGHT_ROWS)))
            )
            self.sphere_mode_combo.setCurrentIndex(
                max(0, self.sphere_mode_combo.findData(getattr(self.controller, "sphere_mode", SPHERE_MODE_CLASSIC)))
            )
            self.render_mode_combo.setCurrentIndex(
                max(0, self.render_mode_combo.findData(getattr(self.controller, "render_mode", RENDER_MODE_CLASSIC)))
            )
            self.show_card_timer_check.setChecked(bool(state.show_card_timer))
            self.orbit_animation_check.setChecked(bool(getattr(state, "orbit_animation_enabled", True)))
            self.reduced_motion_check.setChecked(bool(getattr(state, "reduced_motion_enabled", False)))
            self.audio_enabled_switch.setChecked(bool(getattr(state, "audio_enabled", DEFAULT_AUDIO_ENABLED)))
            self._populate_audio_combo(str(getattr(state, "selected_audio_file", DEFAULT_AUDIO_FILE) or DEFAULT_AUDIO_FILE))
            self.haptics_enabled_switch.setChecked(bool(getattr(state, "haptics_enabled", True)))
            self.haptic_event_patterns = dict(getattr(state, "haptic_event_patterns", default_haptic_event_patterns()) or {})
            self._populate_haptic_event_combos(self.haptic_event_patterns)
            if bool(getattr(state, "haptics_enabled", True)) and not bool(state.visuals_enabled):
                self.vibration_only_radio.setChecked(True)
            else:
                self.display_and_vibration_radio.setChecked(True)
            self.current_theme_key = str(state.appearance_mode or "midnight")
            self.custom_colors = normalize_custom_colors(getattr(state, "custom_colors", {}) or {})
            self.use_custom_timer_colors = bool(getattr(state, "custom_timer_colors", False))
            self.timer_color_level = float(getattr(state, "custom_timer_color_level", 0.0) or 0.0)
            self._sync_feedback_controls()
            self._sync_visual_mode_controls()
            self._sync_theme_label()
            self.error_label.setText("")
        finally:
            self._syncing = False

    def _populate_audio_combo(self, selected_audio_file: str) -> None:
        files = list(self.controller.available_audio_feedback_files())
        normalized = self.controller.normalize_audio_feedback_file(selected_audio_file)
        self.audio_file_combo.blockSignals(True)
        try:
            self.audio_file_combo.clear()
            if files:
                for file_name in files:
                    self.audio_file_combo.addItem(file_name, file_name)
                index = self.audio_file_combo.findData(normalized)
                self.audio_file_combo.setCurrentIndex(max(0, index))
            else:
                self.audio_file_combo.addItem("No audio files found", "")
                self.audio_file_combo.setCurrentIndex(0)
        finally:
            self.audio_file_combo.blockSignals(False)
        self.audio_file_combo.setEnabled(bool(files))
        self.audio_preview_button.setEnabled(bool(normalized))

    def _populate_haptic_event_combos(self, patterns: dict[str, str]) -> None:
        for item in HAPTIC_EVENT_OPTIONS:
            event_key = item["event"]
            combo = self.haptic_event_combos.get(event_key)
            if combo is None:
                continue
            combo.blockSignals(True)
            try:
                selected = str(patterns.get(event_key, item["default_pattern"]) or item["default_pattern"])
                index = combo.findData(selected)
                if index < 0:
                    index = combo.findData(item["default_pattern"])
                combo.setCurrentIndex(max(0, index))
            finally:
                combo.blockSignals(False)
            self._update_haptic_preview_button(event_key)

    def _populate_flag_combos(self, time_drain_flag: int, review_later_flag: int) -> None:
        self.time_drain_combo.blockSignals(True)
        self.review_later_combo.blockSignals(True)
        try:
            self.time_drain_combo.clear()
            self.review_later_combo.clear()
            for value, label in FLAG_OPTIONS:
                self.time_drain_combo.addItem(label, value)
                self.review_later_combo.addItem(label, value)
            self._apply_flag_combo_items(self.time_drain_combo)
            self._apply_flag_combo_items(self.review_later_combo)
            self.time_drain_combo.setCurrentIndex(max(0, self.time_drain_combo.findData(time_drain_flag)))
            self.review_later_combo.setCurrentIndex(max(0, self.review_later_combo.findData(review_later_flag)))
            self._update_flag_combo_style(self.time_drain_combo)
            self._update_flag_combo_style(self.review_later_combo)
        finally:
            self.time_drain_combo.blockSignals(False)
            self.review_later_combo.blockSignals(False)

    def _flag_option_color(self, value: int) -> str:
        return self.flag_palette.get(int(value), self.flag_palette[0])

    def _flag_icon(self, color_hex: str) -> QIcon:
        pixmap = QPixmap(14, 14)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(255, 255, 255, 80), 1))
        painter.setBrush(QColor(color_hex))
        painter.drawEllipse(1, 1, 12, 12)
        painter.end()
        return QIcon(pixmap)

    def _apply_flag_combo_items(self, combo: QComboBox) -> None:
        for index in range(combo.count()):
            value = int(combo.itemData(index) or 0)
            color_hex = self._flag_option_color(value)
            combo.setItemData(index, color_hex, Qt.ItemDataRole.UserRole + 1)
            combo.setItemData(index, self._flag_icon(color_hex), Qt.ItemDataRole.DecorationRole)
            combo.setItemData(index, QBrush(QColor(color_hex)), Qt.ItemDataRole.ForegroundRole)
            background = QColor(color_hex)
            background.setAlpha(34 if value > 0 else 18)
            combo.setItemData(index, QBrush(background), Qt.ItemDataRole.BackgroundRole)

    def _flag_combo_stylesheet(self, color_hex: str) -> str:
        tint = QColor(color_hex)
        tint.setAlpha(28)
        tint_str = f"rgba({tint.red()}, {tint.green()}, {tint.blue()}, {tint.alpha()})"
        border = QColor(color_hex)
        border.setAlpha(132)
        border_str = f"rgba({border.red()}, {border.green()}, {border.blue()}, {border.alpha()})"
        return f"""
            QComboBox#{'{name}'} {{
              min-height: 34px;
              padding: 3px 9px;
              border-radius: 12px;
              border: 1px solid {border_str};
              background:
                qlineargradient(x1:0, y1:0, x2:0, y2:1,
                  stop:0 {tint_str},
                  stop:1 rgba(10, 14, 22, 0.94));
              color: #edf1fb;
              font-size: 12px;
              font-weight: 700;
            }}
            QComboBox#{'{name}'}:hover {{
              border-color: {border_str};
            }}
            QComboBox#{'{name}'}:focus {{
              border-color: {border_str};
            }}
            QComboBox#{'{name}'}::drop-down {{
              border: none;
              width: 22px;
              background: transparent;
            }}
        """

    def _update_flag_combo_style(self, combo: QComboBox) -> None:
        color_hex = str(combo.currentData(Qt.ItemDataRole.UserRole + 1) or self._flag_option_color(0))
        combo.setStyleSheet(self._flag_combo_stylesheet(color_hex).replace("{name}", combo.objectName()))

    def _on_flag_combo_changed(self) -> None:
        sender = self.sender()
        if isinstance(sender, QComboBox):
            self._update_flag_combo_style(sender)
        self.persist_settings()

    def _on_audio_enabled_toggled(self, checked: bool) -> None:
        if self._syncing:
            return
        self._sync_theme_label()
        self.persist_settings()

    def _on_audio_file_changed(self) -> None:
        self.audio_preview_button.setEnabled(bool(self.audio_file_combo.currentData()))
        if self._syncing:
            return
        self.persist_settings()

    def _preview_audio_feedback(self) -> None:
        self.error_label.setText("")
        file_name = str(self.audio_file_combo.currentData() or "")
        if not file_name:
            self.error_label.setText("Choose an audio file first.")
            return
        if not self.controller.preview_audio_feedback(file_name):
            self.error_label.setText("Audio preview could not be played from the settings screen.")

    def _is_vibration_only_selected(self) -> bool:
        return bool(getattr(self, "haptics_enabled_switch", None) and self.haptics_enabled_switch.isChecked() and self.vibration_only_radio.isChecked())

    def _update_haptic_preview_button(self, event_key: str) -> None:
        combo = self.haptic_event_combos.get(event_key)
        button = self.haptic_preview_buttons.get(event_key)
        if combo is None or button is None:
            return
        button.setEnabled(str(combo.currentData() or "") != HAPTIC_PATTERN_OFF)

    def _sync_feedback_controls(self) -> None:
        haptics_enabled = bool(getattr(self, "haptics_enabled_switch", None) and self.haptics_enabled_switch.isChecked())
        if getattr(self, "feedback_mode_group", None) is not None:
            self.feedback_mode_group.setEnabled(haptics_enabled)
        if getattr(self, "appearance_section", None) is not None:
            self.appearance_section.setEnabled(not self._is_vibration_only_selected())

    def _on_vibration_enabled_toggled(self, checked: bool) -> None:
        if self._syncing:
            return
        if not checked and self.vibration_only_radio.isChecked():
            self._syncing = True
            try:
                self.display_and_vibration_radio.setChecked(True)
            finally:
                self._syncing = False
        self._sync_feedback_controls()
        self._sync_theme_label()
        self.persist_settings()

    def _on_feedback_mode_changed(self, checked: bool) -> None:
        if self._syncing or not checked:
            return
        self._sync_feedback_controls()
        self._sync_theme_label()
        self.persist_settings()

    def _on_haptic_pattern_changed(self, event_key: str) -> None:
        self._update_haptic_preview_button(event_key)
        if self._syncing:
            return
        self.persist_settings()

    def _preview_haptic_feedback(self, event_key: str) -> None:
        self.error_label.setText("")
        combo = self.haptic_event_combos.get(event_key)
        if combo is None:
            return
        pattern_key = str(combo.currentData() or "")
        if not pattern_key or pattern_key == HAPTIC_PATTERN_OFF:
            self.error_label.setText("This event is set to Off, so there is nothing to preview.")
            return
        if not self.controller.preview_haptic_pattern(pattern_key):
            self.error_label.setText("Haptic preview needs a connected controller with native XInput rumble support.")

    def persist_settings(self) -> None:
        if self._syncing:
            return
        time_drain_flag = int(self.time_drain_combo.currentData() or 0)
        review_later_flag = int(self.review_later_combo.currentData() or 0)
        if time_drain_flag > 0 and review_later_flag > 0 and time_drain_flag == review_later_flag:
            self.error_label.setText("Time Drain and Review Later cannot use the same flag.")
            return
        self.error_label.setText("")
        audio_enabled = bool(self.audio_enabled_switch.isChecked())
        selected_audio_file = str(self.audio_file_combo.currentData() or "")
        haptics_enabled = bool(self.haptics_enabled_switch.isChecked())
        haptic_event_patterns = {
            item["event"]: str(self.haptic_event_combos[item["event"]].currentData() or item["default_pattern"])
            for item in HAPTIC_EVENT_OPTIONS
            if item["event"] in self.haptic_event_combos
        }
        visuals_enabled = not (haptics_enabled and self.vibration_only_radio.isChecked())
        self.controller.apply_settings_from_dialog(
            question_seconds=float(self.question_spin.value()),
            answer_seconds=float(self.answer_spin.value()),
            time_drain_flag=time_drain_flag,
            review_later_flag=review_later_flag,
            audio_enabled=audio_enabled,
            selected_audio_file=selected_audio_file,
            haptics_enabled=haptics_enabled,
            haptic_event_patterns=haptic_event_patterns,
            show_card_timer=bool(self.show_card_timer_check.isChecked()),
            display_mode=str(self.display_mode_combo.currentData() or DISPLAY_MODE_INLINE),
            visual_mode=str(self.visual_mode_combo.currentData() or VISUAL_MODE_SPHERE),
            sphere_mode=str(self.sphere_mode_combo.currentData() or SPHERE_MODE_CLASSIC),
            render_mode=str(self.render_mode_combo.currentData() or RENDER_MODE_CLASSIC),
            orbit_animation_enabled=bool(self.orbit_animation_check.isChecked()),
            reduced_motion_enabled=bool(self.reduced_motion_check.isChecked()),
            visuals_enabled=visuals_enabled,
            custom_timer_colors=bool(self.use_custom_timer_colors),
            custom_timer_color_level=float(self.timer_color_level),
            appearance_mode=self.current_theme_key,
            custom_colors=dict(self.custom_colors),
        )
        self._sync_theme_label()

    def _sync_theme_label(self) -> None:
        theme = next(((key, theme_label, top, bottom) for key, theme_label, top, bottom in THEMES if key == self.current_theme_key), None)
        label = theme[1] if theme else "Midnight"
        state = self.controller.engine.state
        if not bool(getattr(state, "haptics_enabled", True)):
            feedback_label = "Display Only"
        elif bool(state.visuals_enabled):
            feedback_label = "Display + Haptics"
        else:
            feedback_label = "Haptics Only"
        audio_label = "On" if bool(getattr(state, "audio_enabled", False)) else "Off"
        audio_file = str(getattr(state, "selected_audio_file", DEFAULT_AUDIO_FILE) or DEFAULT_AUDIO_FILE)
        self.appearance_value.setText(f"Current Theme: {label}")
        resolved_colors = {**theme_default_colors(self.current_theme_key), **normalize_custom_colors(self.custom_colors)}
        display_label = display_mode_label(getattr(self.controller, "display_mode", DISPLAY_MODE_INLINE))
        visual_mode = getattr(self.controller, "visual_mode", VISUAL_MODE_LIGHTWEIGHT_ROWS)
        if visual_mode == VISUAL_MODE_SPHERE:
            visual_detail = (
                f"Sphere settings: {sphere_mode_label(getattr(self.controller, 'sphere_mode', SPHERE_MODE_CLASSIC))}  |  "
                f"{render_mode_label(getattr(self.controller, 'render_mode', RENDER_MODE_CLASSIC))}  |  "
                f"Orb animation {'on' if getattr(self.controller.engine.state, 'orbit_animation_enabled', True) else 'off'}"
            )
        else:
            visual_detail = (
                "Rows settings: "
                f"Reduced motion {'on' if getattr(self.controller.engine.state, 'reduced_motion_enabled', False) else 'off'}"
            )
        self.color_value.setText(
            f"Display: {display_label}  |  Haptics: {feedback_label}  |  Audio: {audio_label} ({audio_file})  |  Visual: {visual_mode_label(visual_mode)}\n"
            f"{visual_detail}\n"
            "Orb colors: "
            f"Orb {resolved_colors['core'].upper()}  "
            f"Again {resolved_colors['red'].upper()}  "
            f"Hard {resolved_colors['yellow'].upper()}  "
            f"Good {resolved_colors['green'].upper()}  "
            f"Easy {resolved_colors['blue'].upper()}\n"
            f"Timer colors: {'match theme/custom palette' if self.use_custom_timer_colors else 'default ramp'}  ({self.timer_color_level:+.2f})"
        )
        if theme:
            swatches = [resolved_colors["core"], resolved_colors["red"], resolved_colors["green"], resolved_colors["blue"]]
            for swatch, color in zip(self.preview_swatches, swatches):
                swatch.setStyleSheet(f"background: {color};")

    def set_theme(self, theme_key: str) -> None:
        self.current_theme_key = str(theme_key or "midnight")
        self._sync_theme_label()
        self.persist_settings()

    def _on_visual_mode_changed(self) -> None:
        self._sync_visual_mode_controls()
        self.persist_settings()

    def _sync_visual_mode_controls(self) -> None:
        visual_mode = str(getattr(self.visual_mode_combo, "currentData", lambda: VISUAL_MODE_SPHERE)() or VISUAL_MODE_SPHERE)
        sphere_selected = visual_mode == VISUAL_MODE_SPHERE
        rows_selected = visual_mode == VISUAL_MODE_LIGHTWEIGHT_ROWS
        for widget, visible in (
            (getattr(self, "sphere_settings_group", None), sphere_selected),
            (getattr(self, "rows_settings_group", None), rows_selected),
        ):
            if widget is not None:
                widget.setVisible(visible)

    def open_theme_picker(self) -> None:
        if self._is_vibration_only_selected():
            return
        picker = ThemePickerDialog(self)
        picker.exec()

    def open_color_picker(self) -> None:
        if self._is_vibration_only_selected():
            return
        picker = ColorCustomizerDialog(self)
        picker.exec()

    def set_custom_colors(self, custom_colors: dict[str, str], use_custom_timer_colors: bool, timer_color_level: float) -> None:
        self.custom_colors = normalize_custom_colors(custom_colors)
        self.use_custom_timer_colors = bool(use_custom_timer_colors)
        self.timer_color_level = max(-1.0, min(1.0, float(timer_color_level)))
        self._sync_theme_label()
        self.persist_settings()

    def open_review_later_manager(self) -> None:
        self.controller.open_review_later_manager_from_dialog()
        self.close()

    def open_stats(self) -> None:
        self.controller.open_stats_from_dialog()

    def reset_defaults(self) -> None:
        decision = QMessageBox.question(
            self,
            "Confirm Default Settings",
            "Reset all Speed Streak settings, including feedback choices and saved orb colors, back to their defaults?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if decision != QMessageBox.StandardButton.Yes:
            return
        self.controller.reset_defaults_from_dialog()
        self.sync_from_state()

    def reset_game(self) -> None:
        decision = QMessageBox.question(
            self,
            "Confirm Reset Game",
            "Reset the current Speed Streak game state and progress?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if decision != QMessageBox.StandardButton.Yes:
            return
        self.controller.reset_game_from_dialog()


def open_settings_dialog(controller: Any) -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.controller = controller
            _dialog.sync_from_state()
            _dialog.show()
            _dialog.raise_()
            _dialog.activateWindow()
            return
        except Exception:
            try:
                _dialog.close()
            except Exception:
                pass
            _dialog = None
    _dialog = SettingsDialog(controller)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
