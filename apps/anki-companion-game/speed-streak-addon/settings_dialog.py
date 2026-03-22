from __future__ import annotations

from typing import Any, Optional

from aqt import mw
from aqt.qt import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    Qt,
    QVBoxLayout,
    QWidget,
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

        self.setModal(True)
        self.setWindowTitle("Speed Streak Settings")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("speedStreakSettingsDialog")
        self.setStyleSheet(
            """
            QDialog#speedStreakSettingsDialog {
              background: rgba(5, 8, 14, 172);
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
        outer.setContentsMargins(30, 30, 30, 30)

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
        close_button = QPushButton("×", hero)
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

        if mw is not None:
            self.resize(min(760, max(660, int(mw.width() * 0.56))), min(820, max(660, int(mw.height() * 0.82))))

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
        self.question_spin = QDoubleSpinBox(frame)
        self.question_spin.setDecimals(1)
        self.question_spin.setRange(1.0, 999.0)
        self.question_spin.setSingleStep(0.5)
        self.question_spin.setSuffix(" s")
        self.question_spin.valueChanged.connect(self.persist_settings)

        a_label = QLabel("Answer Time", frame)
        a_label.setProperty("class", "fieldLabel")
        self.answer_spin = QDoubleSpinBox(frame)
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
        self.time_drain_combo = QComboBox(frame)
        self.time_drain_combo.currentIndexChanged.connect(self.persist_settings)

        rl_label = QLabel("Review Later Flag", frame)
        rl_label.setProperty("class", "fieldLabel")
        self.review_later_combo = QComboBox(frame)
        self.review_later_combo.currentIndexChanged.connect(self.persist_settings)

        grid.addWidget(td_label, 0, 0)
        grid.addWidget(self.time_drain_combo, 0, 1)
        grid.addWidget(rl_label, 1, 0)
        grid.addWidget(self.review_later_combo, 1, 1)
        layout.addLayout(grid)
        return frame

    def _build_modes_section(self, parent: QWidget) -> QWidget:
        frame, layout = self._build_section_card(parent, "Modes", "modes")
        self.show_card_timer_check = QCheckBox("Top Card Timer", frame)
        self.show_card_timer_check.toggled.connect(self.persist_settings)
        self.vibration_only_check = QCheckBox("Vibration Only Mode", frame)
        self.vibration_only_check.toggled.connect(self.persist_settings)

        top_help = QLabel("Show a horizontal timer bar above the review card.", frame)
        top_help.setProperty("class", "helpText")
        vib_help = QLabel("Turns off streak and timer visuals, disables late buzzes, and keeps only haptics.", frame)
        vib_help.setProperty("class", "helpText")

        layout.addWidget(self.show_card_timer_check)
        layout.addWidget(top_help)
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
            self.show_card_timer_check.setChecked(bool(state.show_card_timer))
            self.vibration_only_check.setChecked(not bool(state.visuals_enabled))
            self.current_theme_key = str(state.appearance_mode or "midnight")
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
            visuals_enabled=not bool(self.vibration_only_check.isChecked()),
            appearance_mode=self.current_theme_key,
        )

    def _sync_theme_label(self) -> None:
        theme = next(((key, theme_label, top, bottom) for key, theme_label, top, bottom in THEMES if key == self.current_theme_key), None)
        label = theme[1] if theme else "Midnight"
        self.appearance_value.setText(f"Current Theme: {label}")
        if theme:
            swatches = [theme[2], theme[3], "#7fb0ff", "#65f0c2"]
            for swatch, color in zip(self.preview_swatches, swatches):
                swatch.setStyleSheet(f"background: {color};")

    def set_theme(self, theme_key: str) -> None:
        self.current_theme_key = str(theme_key or "midnight")
        self._sync_theme_label()
        self.persist_settings()

    def open_theme_picker(self) -> None:
        picker = ThemePickerDialog(self)
        picker.exec()

    def open_review_later_manager(self) -> None:
        self.controller.open_review_later_manager_from_dialog()
        self.close()

    def open_stats(self) -> None:
        self.controller.open_stats_from_dialog()

    def reset_defaults(self) -> None:
        decision = QMessageBox.question(
            self,
            "Confirm Default Settings",
            "Reset all Speed Streak settings back to their defaults?",
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
            _dialog.close()
        except Exception:
            pass
    _dialog = SettingsDialog(controller)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
