from __future__ import annotations

from aqt.qt import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog,
                    QDialogButtonBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                    QPushButton, QSpinBox, Qt, QVBoxLayout, QWidget)
from .suggestion_lab import IDEAS, VERDICTS


class SuggestionDialog(QDialog):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.lab = controller.lab
        self.setWindowTitle("Speed Streak · Suggestion Lab")
        self.resize(840, 530)
        outer = QVBoxLayout(self)
        outer.addWidget(QLabel("Try ideas during review. Your Keep and Skip choices are saved independently."))
        columns = QHBoxLayout()
        outer.addLayout(columns, 1)
        self.list = QListWidget()
        self.list.setMinimumWidth(250)
        columns.addWidget(self.list)
        right = QVBoxLayout()
        columns.addLayout(right, 1)
        self.source = QLabel()
        right.addWidget(self.source)
        self.title = QLabel()
        font = self.title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 3)
        self.title.setFont(font)
        right.addWidget(self.title)
        self.labels = []
        for heading in ("Already available", "What to try", "Quick test"):
            label = QLabel(heading)
            font = label.font()
            font.setBold(True)
            label.setFont(font)
            right.addWidget(label)
            label = QLabel()
            label.setWordWrap(True)
            right.addWidget(label)
            self.labels.append(label)
        self.options = QWidget()
        self.option_layout = QHBoxLayout(self.options)
        self.option_layout.setContentsMargins(0, 0, 0, 0)
        right.addWidget(self.options)
        self.try_box = QCheckBox("Try in reviewer")
        self.try_box.toggled.connect(self.toggle_trial)
        right.addWidget(self.try_box)
        verdict_row = QHBoxLayout()
        verdict_row.addWidget(QLabel("Next build"))
        self.verdict = QComboBox()
        self.verdict.addItems(VERDICTS)
        self.verdict.currentTextChanged.connect(self.set_verdict)
        verdict_row.addWidget(self.verdict, 1)
        right.addLayout(verdict_row)
        right.addStretch()
        footer = QHBoxLayout()
        copy = QPushButton("Copy build choices")
        copy.clicked.connect(self.copy_choices)
        footer.addWidget(copy)
        stop = QPushButton("Turn off all trials")
        stop.clicked.connect(self.stop_trials)
        footer.addWidget(stop)
        footer.addStretch()
        close = QPushButton("Done")
        close.clicked.connect(self.accept)
        footer.addWidget(close)
        outer.addLayout(footer)
        self.list.addItems([idea.title for idea in IDEAS])
        self.list.currentRowChanged.connect(self.select)
        self.refresh_list()
        self.list.setCurrentRow(0)

    def refresh_list(self):
        for i, idea in enumerate(IDEAS):
            verdict = self.lab.verdict(idea.key)
            suffix = {"Keep": "  ✓", "Skip": "  ×"}.get(verdict, "")
            if self.lab.active(idea.key):
                suffix += "  ●"
            self.list.item(i).setText(idea.title + suffix)

    def select(self, row):
        idea = IDEAS[row]
        self.idea = idea
        self.source.setText(idea.source)
        self.title.setText(idea.title)
        for label, value in zip(self.labels, (idea.current, idea.behavior, idea.test)):
            label.setText(value)
        while self.option_layout.count():
            widget = self.option_layout.takeAt(0).widget()
            widget.hide()
            widget.deleteLater()
        can_try = True
        if idea.key == "width":
            size = QSpinBox()
            size.setRange(200, 480)
            size.setSuffix(" px")
            size.setValue(self.lab.data.get("width_px", 250))
            size.valueChanged.connect(lambda value: self.option("width_px", value))
            self.option_layout.addWidget(size)
        elif idea.key == "move_flag":
            picker = QComboBox()
            picker.addItem("Choose a destination deck…", 0)
            from aqt import mw
            if mw.col:
                for deck in mw.col.decks.all_names_and_ids():
                    record = mw.col.decks.get(deck.id, default=False)
                    if record and not record.get("dyn"):
                        picker.addItem(deck.name, int(deck.id))
            picker.setCurrentIndex(max(0, picker.findData(self.lab.data.get("deck_id", 0))))
            can_try = bool(picker.currentData())
            def choose_deck():
                self.option("deck_id", picker.currentData())
                self.try_box.setEnabled(bool(picker.currentData()))
                if not picker.currentData():
                    self.try_box.setChecked(False)
            picker.currentIndexChanged.connect(choose_deck)
            self.option_layout.addWidget(picker)
        elif idea.key == "shuffle":
            rating = QComboBox()
            rating.addItems(["Again", "Hard", "Good", "Easy"])
            self.option_layout.addWidget(rating)
            sounds = QPushButton("Choose clips…")
            sounds.clicked.connect(lambda: self.choose_clips(rating.currentText().lower()))
            self.option_layout.addWidget(sounds)
        self.options.setVisible(bool(self.option_layout.count()))
        self.try_box.blockSignals(True)
        self.try_box.setChecked(self.lab.active(idea.key))
        self.try_box.setVisible(idea.live)
        self.try_box.setEnabled(can_try)
        self.try_box.blockSignals(False)
        self.verdict.blockSignals(True)
        self.verdict.setCurrentText(self.lab.verdict(idea.key))
        self.verdict.blockSignals(False)

    def choose_clips(self, event):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Choose sounds for {event.title()}")
        dlg.resize(580, 440)
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Select clips for this rating. An empty selection uses the suggested pool."))
        choices = QListWidget()
        layout.addWidget(choices)
        choices.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        selected = self.controller.trial_sound_pool(event)
        for label, key in self.controller.available_audio_feedback_options():
            item = QListWidgetItem(label, choices)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setSelected(key in selected)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec():
            pools = dict(self.lab.data.get("pools", {}))
            pools[event] = [item.data(Qt.ItemDataRole.UserRole) for item in choices.selectedItems()]
            self.option("pools", pools)

    def option(self, key, value):
        self.lab.data[key] = value
        self.lab.save()
        self.controller.apply_suggestion_trials()

    def toggle_trial(self, checked):
        active = set(self.lab.data.get("trying", []))
        if checked:
            active.add(self.idea.key)
        else:
            active.discard(self.idea.key)
        self.option("trying", sorted(active))
        self.refresh_list()

    def set_verdict(self, text):
        self.lab.data.setdefault("decisions", {})[self.idea.key] = text
        self.lab.save()
        self.refresh_list()

    def stop_trials(self):
        self.option("trying", [])
        self.select(self.list.currentRow())
        self.refresh_list()

    def copy_choices(self):
        QApplication.clipboard().setText(self.lab.summary())
        from aqt.utils import tooltip
        tooltip("Build choices copied", parent=self)

