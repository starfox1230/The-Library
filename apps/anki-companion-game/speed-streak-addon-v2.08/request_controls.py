"""Controls shared by release 2.05 and the experimental 2.06 visual track."""
from __future__ import annotations

from aqt import mw
from aqt.qt import (QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
                    QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget,
                    QTreeWidgetItem, QVBoxLayout, QWidget, Qt, QTimer)


def build_timer_appearance(host, parent, layout):
    for attribute, title, description in [
        ("timer_number_mode_combo", "Circle timer numbers", "Number display in the side-panel timer. Hiding numbers keeps the circular progress indicator."),
        ("card_timer_number_mode_combo", "Horizontal timer numbers", "Number display in the top card timer. Hiding numbers keeps its progress bar.")]:
        combo = QComboBox(parent)
        setattr(host, attribute, combo)
        for text, value in [("Seconds with decimals (default)", "decimal"),
                            ("Whole seconds", "seconds"), ("Hide numbers", "hidden")]:
            combo.addItem(text, value)
        combo.currentIndexChanged.connect(host.persist_settings)
        layout.addWidget(host._build_setting_row(parent, title, description,
            combo, control_width=270))


def build_answer_pause(host, parent, layout):
    host.pause_answer_timer_check = QCheckBox("Pause timer on the answer side", parent)
    host.pause_answer_timer_check.toggled.connect(host.persist_settings)
    host.pause_answer_timer_check.toggled.connect(lambda checked: host.answer_spin.setEnabled(not checked))
    host.pause_answer_timer_check.toggled.connect(lambda checked: host.answer_timeout_breaks_streak_check.setEnabled(not checked))
    layout.addWidget(host._build_toggle_block(parent, host.pause_answer_timer_check,
        "Review revealed answers without a countdown or timeout. Rating stays available, and the next question starts normally. This also applies in No Pause mode."))


def build_timer_visuals_link(host, parent, layout):
    button = QPushButton("Timer appearance…", parent)
    host.timer_visuals_button = button
    def open_appearance():
        host._select_settings_page("visuals")
        section = host.timer_appearance_section
        section.layout().itemAt(0).widget().setChecked(True)
        QTimer.singleShot(0, lambda: host.settings_page_scrolls["visuals"].ensureWidgetVisible(section))
    button.clicked.connect(open_appearance)
    layout.addWidget(host._build_setting_row(parent, "Timer visuals",
        "Show decimals, whole seconds, or only the progress bar in Visuals.", button, control_width=230))


def build_boost_ratings(host, parent, layout):
    row = QWidget(parent)
    horizontal = QHBoxLayout(row)
    horizontal.setContentsMargins(0, 0, 0, 0)
    horizontal.setSpacing(6)
    host.boost_rating_checks = {}
    for rating, name in [(1, "Again"), (2, "Hard"), (3, "Good"), (4, "Easy")]:
        check = QCheckBox(name, row)
        check.setStyleSheet("QCheckBox { border: 1px solid #526176; border-radius: 6px; padding: 6px; spacing: 5px; }"
                           "QCheckBox:checked { background: #263d52; border-color: #6c99be; }"
                           "QCheckBox:disabled { border-color: #38404d; background: transparent; }")
        check.setChecked(True)
        check.toggled.connect(host.persist_settings)
        host.boost_rating_checks[rating] = check
        horizontal.addWidget(check, 1)
    block = host._build_setting_row(parent, "Ratings that earn Boost progress",
        "Each selected rating adds one card toward the next Boost. All are selected by default. Select none to stop earning new Boosts.", row, control_width=370)
    layout.addWidget(block)
    return block


def sync_request_controls(host, state):
    if hasattr(host, "timer_number_mode_combo"):
        host.timer_number_mode_combo.setCurrentIndex(max(0, host.timer_number_mode_combo.findData(state.timer_number_mode)))
    if hasattr(host, "card_timer_number_mode_combo"):
        host.card_timer_number_mode_combo.setCurrentIndex(max(0, host.card_timer_number_mode_combo.findData(state.card_timer_number_mode)))
    if hasattr(host, "pause_answer_timer_check"):
        host.pause_answer_timer_check.setChecked(state.pause_answer_timer)
    for rating, check in getattr(host, "boost_rating_checks", {}).items():
        check.setChecked(rating in state.boost_earning_ratings)
    editor = getattr(host, "deck_timer_editor", None)
    if editor is not None:
        editor.set_rules(host.controller.special_timer_rules)


def deck_options():
    if not mw.col:
        return {}
    return {int(deck.id): str(deck.name) for deck in mw.col.decks.all_names_and_ids()}


def choose_decks(parent, selected):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Choose decks")
    dialog.resize(560, 540)
    layout = QVBoxLayout(dialog)
    help_label = QLabel("Check any number of decks. Subdeck inclusion is controlled by the rule.", dialog)
    help_label.setWordWrap(True)
    layout.addWidget(help_label)
    search = QLineEdit(dialog); search.setPlaceholderText("Find a deck…")
    layout.addWidget(search)
    tree = QTreeWidget(dialog); tree.setHeaderLabels(["Deck"])
    layout.addWidget(tree)
    options = deck_options()
    # Keep unavailable IDs selectable so editing another field cannot erase them.
    for deck_id in selected:
        options.setdefault(deck_id, f"Unavailable deck ({deck_id})")
    items = []
    for deck_id, name in sorted(options.items(), key=lambda item: item[1].casefold()):
        item = QTreeWidgetItem([name])
        item.setData(0, Qt.ItemDataRole.UserRole, deck_id)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if deck_id in selected else Qt.CheckState.Unchecked)
        tree.addTopLevelItem(item); items.append(item)
    search.textChanged.connect(lambda text: [item.setHidden(text.casefold() not in item.text(0).casefold()) for item in items])
    actions = QHBoxLayout()
    for title, checked in [("Select visible", True), ("Clear visible", False)]:
        button = QPushButton(title, dialog)
        button.clicked.connect(lambda _=False, checked=checked: [item.setCheckState(0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked) for item in items if not item.isHidden()])
        actions.addWidget(button)
    layout.addLayout(actions)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, dialog)
    buttons.accepted.connect(dialog.accept); buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() != QDialog.DialogCode.Accepted:
        return None
    return [int(item.data(0, Qt.ItemDataRole.UserRole)) for item in items if item.checkState(0) == Qt.CheckState.Checked]


class DeckTimerEditor(QWidget):
    def __init__(self, host, parent):
        super().__init__(parent)
        self.host = host
        self.loading = True
        self.rows = []
        layout = QVBoxLayout(self); layout.setContentsMargins(0, 0, 0, 0)
        self.enabled = QCheckBox("Enable Deck-Specific Timers", self)
        layout.addWidget(host._build_toggle_block(
            self,
            self.enabled,
            "Choose one or more decks per rule. Deck renames are tracked automatically. Filtered cards use their home deck. Matching deck, tag and note-type rules use the longest time for each side; Untimed wins.",
        ))
        self.content = QWidget(self)
        self.content_layout = QVBoxLayout(self.content); self.content_layout.setContentsMargins(24, 0, 0, 0)
        layout.addWidget(self.content)
        self.add_button = QPushButton("Add deck rule", self.content)
        self.add_button.clicked.connect(lambda: self.add_rule({"enabled": True, "include_subdecks": True}))
        self.content_layout.addWidget(self.add_button)
        self.enabled.toggled.connect(self.content.setVisible)
        self.enabled.toggled.connect(self.changed)
        self.set_rules(host.controller.special_timer_rules)
        self.loading = False

    def changed(self, *_):
        if not self.loading:
            self.host.persist_settings()

    def set_rules(self, rules):
        incoming = {"decks_enabled": bool(rules.get("decks_enabled", False)), "decks": rules.get("decks", [])}
        if self.values() == incoming:
            self.content.setVisible(incoming["decks_enabled"])
            return
        self.loading = True
        self.enabled.setChecked(incoming["decks_enabled"])
        self.content.setVisible(incoming["decks_enabled"])
        for row in self.rows:
            self.content_layout.removeWidget(row["panel"]); row["panel"].deleteLater()
        self.rows.clear()
        for rule in incoming["decks"]:
            self.add_rule(rule)
        self.loading = False
        self.update_add_label()

    def update_add_label(self):
        self.add_button.setText("Add another deck rule" if self.rows else "Add deck rule")

    def add_rule(self, rule):
        panel = QWidget(self.content); layout = QVBoxLayout(panel)
        row = {"panel": panel, "deck_ids": list(rule.get("deck_ids", []))}
        row["enabled"] = QCheckBox("Use this deck rule", panel)
        row["enabled"].setChecked(bool(rule.get("enabled", False)))
        layout.addWidget(row["enabled"])
        picker = QPushButton(panel); row["picker"] = picker
        layout.addWidget(picker)
        def update_label():
            names = deck_options()
            labels = [names.get(i, f"Unavailable deck ({i})") for i in row["deck_ids"]]
            picker.setText("Choose decks…" if not labels else f"{len(labels)} selected: " + ", ".join(labels)[:75])
            picker.setToolTip("\n".join(labels))
        def pick():
            selected = choose_decks(self, row["deck_ids"])
            if selected is not None:
                row["deck_ids"] = selected; update_label(); self.changed()
        picker.clicked.connect(pick); update_label()
        row["include_subdecks"] = QCheckBox("Include subdecks", panel)
        row["include_subdecks"].setChecked(bool(rule.get("include_subdecks", True)))
        layout.addWidget(row["include_subdecks"])
        for phase, default in [("question", self.host.question_spin.value()), ("answer", self.host.answer_spin.value())]:
            fields = QHBoxLayout(); fields.addWidget(QLabel(phase.title() + " time", panel))
            spin = type(self.host.question_spin)(panel); spin.setRange(.1, 86400); spin.setDecimals(1); spin.setSuffix(" s")
            spin.setValue(float(rule.get(phase + "_seconds", default))); fields.addWidget(spin)
            untimed = QCheckBox("Untimed", panel); untimed.setChecked(bool(rule.get(phase + "_untimed", False)))
            fields.addWidget(untimed); spin.setEnabled(not untimed.isChecked())
            untimed.toggled.connect(lambda checked, spin=spin: spin.setEnabled(not checked))
            spin.valueChanged.connect(self.changed); untimed.toggled.connect(self.changed)
            row[phase + "_seconds"] = spin; row[phase + "_untimed"] = untimed; layout.addLayout(fields)
        remove = QPushButton("Remove rule", panel)
        def delete():
            self.rows.remove(row); self.content_layout.removeWidget(panel); panel.deleteLater(); self.update_add_label(); self.changed()
        remove.clicked.connect(delete); layout.addWidget(remove)
        self.rows.append(row)
        self.update_add_label()
        self.content_layout.insertWidget(self.content_layout.count() - 1, panel)
        row["enabled"].toggled.connect(self.changed); row["include_subdecks"].toggled.connect(self.changed)

    def values(self):
        result = []
        for row in self.rows:
            if not row["deck_ids"]:
                continue
            result.append({"deck_ids": list(row["deck_ids"]),
                **{key: row[key].isChecked() for key in ("enabled", "include_subdecks", "question_untimed", "answer_untimed")},
                **{phase + "_seconds": row[phase + "_seconds"].value() for phase in ("question", "answer")}})
        return {"decks_enabled": self.enabled.isChecked(), "decks": result}
