from __future__ import annotations

from typing import Any, Optional

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QBrush,
    QColor,
    QColorDialog,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
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

from .display_mode import (
    DISPLAY_MODE_INLINE,
    DISPLAY_MODE_OPTIONS,
    display_mode_label,
)


FLAG_OPTIONS = [
    (0, "0 - Off"),
    (1, "1 - Red"),
    (2, "2 - Orange"),
    (3, "3 - Green"),
    (4, "4 - Blue"),
    (5, "5 - Pink"),
    (6, "6 - Teal"),
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

        self.setModal(False)
        self.setWindowTitle("Speed Streak Settings")
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.setWindowFlag(Qt.WindowType.WindowMinMaxButtonsHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setObjectName("speedStreakSettingsDialog")
        self.setStyleSheet(
            """
            QDialog#speedStreakSettingsDialog {
              background: #0c1018;
            }
            QFrame#speedStreakSettingsCard {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(19, 24, 34, 248),
                stop:0.5 rgba(16, 21, 31, 246),
                stop:1 rgba(12, 16, 24, 244));
              border: 1px solid rgba(141, 154, 182, 0.18);
              border-radius: 24px;
            }
            QFrame#speedStreakSettingsHero {
              background:
                qlineargradient(x1:0, y1:0, x2:1, y2:1,
                  stop:0 rgba(93, 148, 255, 0.18),
                  stop:0.52 rgba(93, 148, 255, 0.06),
                  stop:1 rgba(255,255,255,0.02));
              border: 1px solid rgba(113, 138, 184, 0.18);
              border-radius: 18px;
            }
            QLabel#speedStreakSettingsTitle {
              color: #eef2fb;
              font-size: 28px;
              font-weight: 900;
            }
            QLabel#speedStreakSettingsSub {
              color: #99a6bf;
              font-size: 12px;
            }
            QLabel[class="sectionTitle"] {
              color: #8eb6ff;
              font-size: 11px;
              font-weight: 800;
              letter-spacing: 2px;
              text-transform: uppercase;
            }
            QLabel#speedStreakHeroEyebrow {
              color: #8eb6ff;
              font-size: 11px;
              font-weight: 800;
              letter-spacing: 2px;
              text-transform: uppercase;
            }
            QLabel[class="fieldLabel"] {
              color: #dfe5f3;
              font-size: 12px;
              font-weight: 700;
            }
            QLabel[class="helpText"] {
              color: #98a3b8;
              font-size: 11px;
              line-height: 1.5;
            }
            QLabel#errorLabel {
              color: #f58ea5;
              font-size: 12px;
              font-weight: 700;
            }
            QPushButton[class="primaryAction"], QPushButton[class="secondaryAction"], QPushButton[class="reviewLaterAction"], QPushButton#speedStreakSettingsClose {
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
            QPushButton[class="reviewLaterAction"] {
              color: #f4f8ff;
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #5cc3ff,
                stop:0.5 #3390ff,
                stop:1 #1f62e6);
              border: 1px solid #8fd3ff;
            }
            QPushButton[class="secondaryAction"], QPushButton#speedStreakSettingsClose {
              background: rgba(31, 38, 51, 0.96);
            }
            QPushButton[class="dangerAction"] {
              color: #fff2f4;
              border-radius: 14px;
              padding: 9px 12px;
              font-size: 12px;
              font-weight: 800;
              border: 1px solid rgba(198, 103, 121, 0.28);
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(124, 52, 68, 0.92),
                stop:1 rgba(92, 36, 49, 0.92));
            }
            QPushButton[class="primaryAction"]:hover, QPushButton[class="secondaryAction"]:hover, QPushButton#speedStreakSettingsClose:hover {
              background: rgba(42, 50, 66, 0.98);
            }
            QPushButton[class="reviewLaterAction"]:hover {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #79d0ff,
                stop:0.5 #43a1ff,
                stop:1 #2a71f0);
            }
            QPushButton[class="dangerAction"]:hover {
              background: rgba(143, 58, 77, 0.98);
            }
            QFrame[class="sectionCard"] {
              background: rgba(20, 25, 36, 0.92);
              border: 1px solid rgba(112, 124, 149, 0.16);
              border-radius: 16px;
            }
            QDoubleSpinBox, QComboBox {
              min-height: 34px;
              padding: 3px 9px;
              border-radius: 12px;
              border: 1px solid rgba(116, 128, 153, 0.22);
              background: rgba(10, 14, 22, 0.94);
              color: #edf1fb;
              font-size: 12px;
              font-weight: 700;
            }
            QDoubleSpinBox:hover, QComboBox:hover {
              border-color: rgba(141, 171, 227, 0.34);
            }
            QDoubleSpinBox:focus, QComboBox:focus {
              border-color: rgba(105, 156, 255, 0.62);
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
              border: 1px solid rgba(112, 124, 149, 0.18);
              background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(24, 30, 42, 0.96),
                stop:1 rgba(15, 19, 27, 0.96));
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
        outer.setContentsMargins(16, 16, 16, 16)

        card = QFrame(self)
        card.setObjectName("speedStreakSettingsCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 14)
        card_layout.setSpacing(12)

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
        subtitle = QLabel("Tune timers, flags, modes, and appearance.", hero)
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
        body_layout.setSpacing(10)

        body_layout.addWidget(self._build_actions_section(body))
        body_layout.addWidget(self._build_timers_section(body))
        body_layout.addWidget(self._build_flags_section(body))
        body_layout.addWidget(self._build_modes_section(body))
        body_layout.addWidget(self._build_appearance_section(body))
        body_layout.addStretch(1)

        scroll.setWidget(body)
        card_layout.addWidget(scroll, 1)

        self.error_label = QLabel("", card)
        self.error_label.setObjectName("errorLabel")
        self.error_label.setWordWrap(True)
        card_layout.addWidget(self.error_label)

        outer.addWidget(card, 1)
        self.sync_from_state()

        self.setMinimumSize(900, 760)
        if mw is not None:
            self.resize(min(1120, max(920, int(mw.width() * 0.72))), min(900, max(760, int(mw.height() * 0.86))))
        else:
            self.resize(980, 820)

    def closeEvent(self, event: Any) -> None:
        global _dialog
        if _dialog is self:
            _dialog = None
        super().closeEvent(event)

    def _build_section_card(self, parent: QWidget, title: str, accent: str) -> tuple[QFrame, QVBoxLayout]:
        frame = QFrame(parent)
        frame.setProperty("class", "sectionCard")
        frame.setProperty("accent", accent)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)
        heading = QLabel(title, frame)
        heading.setProperty("class", "sectionTitle")
        layout.addWidget(heading)
        return frame, layout

    def _build_timers_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Timers", "timers")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        q_label = QLabel("Question Time", frame)
        q_label.setProperty("class", "fieldLabel")
        self.question_spin = ScrollSafeDoubleSpinBox(frame)
        self.question_spin.setDecimals(1)
        self.question_spin.setRange(1.0, 999.0)
        self.question_spin.setSingleStep(0.5)
        self.question_spin.setSuffix(" s")
        self.question_spin.valueChanged.connect(self.persist_settings)

        a_label = QLabel("Answer Time", frame)
        a_label.setProperty("class", "fieldLabel")
        self.answer_spin = ScrollSafeDoubleSpinBox(frame)
        self.answer_spin.setDecimals(1)
        self.answer_spin.setRange(1.0, 999.0)
        self.answer_spin.setSingleStep(0.5)
        self.answer_spin.setSuffix(" s")
        self.answer_spin.valueChanged.connect(self.persist_settings)

        grid.addWidget(q_label, 0, 0)
        grid.addWidget(self.question_spin, 0, 1)
        grid.addWidget(a_label, 1, 0)
        grid.addWidget(self.answer_spin, 1, 1)
        layout.addLayout(grid)
        return frame

    def _build_flags_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Flags", "flags")
        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        td_label = QLabel("Time Drain Flag", frame)
        td_label.setProperty("class", "fieldLabel")
        self.time_drain_combo = ScrollSafeComboBox(frame)
        self.time_drain_combo.currentIndexChanged.connect(self.persist_settings)

        rl_label = QLabel("Review Later Flag", frame)
        rl_label.setProperty("class", "fieldLabel")
        self.review_later_combo = ScrollSafeComboBox(frame)
        self.review_later_combo.currentIndexChanged.connect(self.persist_settings)

        grid.addWidget(td_label, 0, 0)
        grid.addWidget(self.time_drain_combo, 0, 1)
        grid.addWidget(rl_label, 1, 0)
        grid.addWidget(self.review_later_combo, 1, 1)
        layout.addLayout(grid)
        return frame

    def _build_modes_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Modes", "modes")
        mode_grid = QGridLayout()
        mode_grid.setHorizontalSpacing(10)
        mode_grid.setVerticalSpacing(8)
        mode_grid.setColumnStretch(1, 1)

        display_mode_label_widget = QLabel("Display Mode", frame)
        display_mode_label_widget.setProperty("class", "fieldLabel")
        self.display_mode_combo = ScrollSafeComboBox(frame)
        for value, label in DISPLAY_MODE_OPTIONS:
            self.display_mode_combo.addItem(label, value)
        self.display_mode_combo.currentIndexChanged.connect(self.persist_settings)

        mode_grid.addWidget(display_mode_label_widget, 0, 0)
        mode_grid.addWidget(self.display_mode_combo, 0, 1)
        layout.addLayout(mode_grid)

        display_mode_help = QLabel(
            "Inline Left Pane keeps the dedicated Speed Streak column. Compatibility Window leaves Anki's "
            "review layout untouched and opens Speed Streak in a floating window, which is recommended for "
            "AMBOSS, AnkiHub, and other reviewer UI add-ons.",
            frame,
        )
        display_mode_help.setWordWrap(True)
        display_mode_help.setProperty("class", "helpText")
        layout.addWidget(display_mode_help)
        layout.addSpacing(4)

        self.show_card_timer_check = QCheckBox("Top Card Timer", frame)
        self.show_card_timer_check.toggled.connect(self.persist_settings)
        self.orbit_animation_check = QCheckBox("Orb Animation", frame)
        self.orbit_animation_check.toggled.connect(self.persist_settings)
        self.vibration_only_check = QCheckBox("Vibration Only Mode", frame)
        self.vibration_only_check.toggled.connect(self.persist_settings)

        top_help = QLabel("Show a horizontal timer bar above the review card.", frame)
        top_help.setProperty("class", "helpText")
        orbit_help = QLabel("Turn off the orb and satellite animation if your computer struggles, and show only the streak number instead.", frame)
        orbit_help.setProperty("class", "helpText")
        vib_help = QLabel("Turns off streak and timer visuals, disables late buzzes, and keeps only haptics.", frame)
        vib_help.setProperty("class", "helpText")

        layout.addWidget(self.show_card_timer_check)
        layout.addWidget(top_help)
        layout.addSpacing(2)
        layout.addWidget(self.orbit_animation_check)
        layout.addWidget(orbit_help)
        layout.addSpacing(2)
        layout.addWidget(self.vibration_only_check)
        layout.addWidget(vib_help)
        return frame

    def _build_appearance_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Appearance", "appearance")
        copy = QLabel("Pick from 8 night-mode color schemes, including one tuned to match your current card style.", frame)
        copy.setProperty("class", "helpText")
        layout.addWidget(copy)
        self.appearance_value = QLabel("", frame)
        self.appearance_value.setProperty("class", "fieldLabel")
        layout.addWidget(self.appearance_value)
        self.color_value = QLabel("", frame)
        self.color_value.setProperty("class", "fieldLabel")
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
        appearance_button = QPushButton("Choose Theme", frame)
        appearance_button.setProperty("class", "primaryAction")
        appearance_button.clicked.connect(self.open_theme_picker)
        layout.addWidget(appearance_button)
        color_button = QPushButton("Customize Orb Colors", frame)
        color_button.setProperty("class", "secondaryAction")
        color_button.clicked.connect(self.open_color_picker)
        layout.addWidget(color_button)
        return frame

    def _build_actions_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Actions", "actions")
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)

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
        layout.addLayout(grid)
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
            self.question_spin.setValue(state.question_limit_ms / 1000)
            self.answer_spin.setValue(state.review_limit_ms / 1000)
            self._populate_flag_combos(state.time_drain_flag, state.review_later_flag)
            self.display_mode_combo.setCurrentIndex(
                max(0, self.display_mode_combo.findData(getattr(self.controller, "display_mode", DISPLAY_MODE_INLINE)))
            )
            self.show_card_timer_check.setChecked(bool(state.show_card_timer))
            self.orbit_animation_check.setChecked(bool(getattr(state, "orbit_animation_enabled", True)))
            self.vibration_only_check.setChecked(not bool(state.visuals_enabled))
            self.current_theme_key = str(state.appearance_mode or "midnight")
            self.custom_colors = normalize_custom_colors(getattr(state, "custom_colors", {}) or {})
            self.use_custom_timer_colors = bool(getattr(state, "custom_timer_colors", False))
            self.timer_color_level = float(getattr(state, "custom_timer_color_level", 0.0) or 0.0)
            self._sync_theme_label()
            self.error_label.setText("")
        finally:
            self._syncing = False

    def _populate_flag_combos(self, time_drain_flag: int, review_later_flag: int) -> None:
        self.time_drain_combo.blockSignals(True)
        self.review_later_combo.blockSignals(True)
        try:
            self.time_drain_combo.clear()
            self.review_later_combo.clear()
            for value, label in FLAG_OPTIONS:
                self.time_drain_combo.addItem(label, value)
                self.review_later_combo.addItem(label, value)
            self.time_drain_combo.setCurrentIndex(max(0, self.time_drain_combo.findData(time_drain_flag)))
            self.review_later_combo.setCurrentIndex(max(0, self.review_later_combo.findData(review_later_flag)))
        finally:
            self.time_drain_combo.blockSignals(False)
            self.review_later_combo.blockSignals(False)

    def persist_settings(self) -> None:
        if self._syncing:
            return
        time_drain_flag = int(self.time_drain_combo.currentData() or 0)
        review_later_flag = int(self.review_later_combo.currentData() or 0)
        if time_drain_flag > 0 and review_later_flag > 0 and time_drain_flag == review_later_flag:
            self.error_label.setText("Time Drain and Review Later cannot use the same flag.")
            return
        self.error_label.setText("")
        self.controller.apply_settings_from_dialog(
            question_seconds=float(self.question_spin.value()),
            answer_seconds=float(self.answer_spin.value()),
            time_drain_flag=time_drain_flag,
            review_later_flag=review_later_flag,
            show_card_timer=bool(self.show_card_timer_check.isChecked()),
            display_mode=str(self.display_mode_combo.currentData() or DISPLAY_MODE_INLINE),
            orbit_animation_enabled=bool(self.orbit_animation_check.isChecked()),
            visuals_enabled=not bool(self.vibration_only_check.isChecked()),
            custom_timer_colors=bool(self.use_custom_timer_colors),
            custom_timer_color_level=float(self.timer_color_level),
            appearance_mode=self.current_theme_key,
            custom_colors=dict(self.custom_colors),
        )

    def _sync_theme_label(self) -> None:
        theme = next(((key, theme_label, top, bottom) for key, theme_label, top, bottom in THEMES if key == self.current_theme_key), None)
        label = theme[1] if theme else "Midnight"
        self.appearance_value.setText(f"Current Theme: {label}")
        resolved_colors = {**theme_default_colors(self.current_theme_key), **normalize_custom_colors(self.custom_colors)}
        display_label = display_mode_label(getattr(self.controller, "display_mode", DISPLAY_MODE_INLINE))
        self.color_value.setText(
            f"Mode: {display_label}   "
            "Orb Colors: "
            f"Orb {resolved_colors['core'].upper()}  "
            f"Again {resolved_colors['red'].upper()}  "
            f"Hard {resolved_colors['yellow'].upper()}  "
            f"Good {resolved_colors['green'].upper()}  "
            f"Easy {resolved_colors['blue'].upper()}  "
            f"Timers {'match' if self.use_custom_timer_colors else 'default'} {self.timer_color_level:+.2f}"
        )
        if theme:
            swatches = [resolved_colors["core"], resolved_colors["red"], resolved_colors["green"], resolved_colors["blue"]]
            for swatch, color in zip(self.preview_swatches, swatches):
                swatch.setStyleSheet(f"background: {color};")

    def set_theme(self, theme_key: str) -> None:
        self.current_theme_key = str(theme_key or "midnight")
        self._sync_theme_label()
        self.persist_settings()

    def open_theme_picker(self) -> None:
        picker = ThemePickerDialog(self)
        picker.exec()

    def open_color_picker(self) -> None:
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
            "Reset all Speed Streak settings, including saved orb colors, back to their defaults?",
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
