from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QMenu,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    Qt,
)
from aqt.utils import showInfo, showWarning

from .common import create_or_update_filtered_deck


FILTERED_DECK_NAME_PREFIX = "Recent new cards "
GEAR_ACTION_LABEL = "Build Recent New Cards Deck"
WINDOW_TITLE = "Recent New Cards Deck"
_HOOK_REGISTERED = False
_dialog: "RecentNewCardsDialog | None" = None


@dataclass(frozen=True)
class DeckChoice:
    deck_id: int
    name: str
    is_filtered: bool


def _db_list(sql: str, *args: Any) -> list[int]:
    db = mw.col.db
    list_method = getattr(db, "list", None)
    if callable(list_method):
        try:
            return [int(value) for value in list_method(sql, *args)]
        except Exception:
            pass
    rows = db.all(sql, *args)
    return [int(row[0]) for row in rows]


def _all_deck_choices() -> list[DeckChoice]:
    manager = mw.col.decks
    choices: dict[int, DeckChoice] = {}

    all_names_and_ids = getattr(manager, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        try:
            raw_items = all_names_and_ids()
        except Exception:
            raw_items = []
        for item in raw_items or []:
            deck_id = None
            name = None
            is_filtered = False
            if isinstance(item, dict):
                deck_id = item.get("id")
                name = item.get("name")
                is_filtered = bool(item.get("dyn", False))
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                first, second = item[0], item[1]
                if isinstance(first, int):
                    deck_id, name = first, second
                else:
                    name, deck_id = first, second
            if deck_id is None or not name:
                continue
            try:
                deck = manager.get(int(deck_id)) or {}
                is_filtered = bool(deck.get("dyn", is_filtered))
            except Exception:
                pass
            choices[int(deck_id)] = DeckChoice(int(deck_id), str(name), bool(is_filtered))

    if not choices:
        all_method = getattr(manager, "all", None)
        if callable(all_method):
            try:
                raw_items = all_method()
            except Exception:
                raw_items = []
            if isinstance(raw_items, dict):
                raw_items = list(raw_items.values())
            for item in raw_items or []:
                if not isinstance(item, dict):
                    continue
                deck_id = item.get("id")
                name = item.get("name")
                if deck_id is None or not name:
                    continue
                choices[int(deck_id)] = DeckChoice(
                    int(deck_id),
                    str(name),
                    bool(item.get("dyn", False)),
                )

    return sorted(choices.values(), key=lambda deck: deck.name.casefold())


def _normal_deck_choices() -> list[DeckChoice]:
    return [choice for choice in _all_deck_choices() if not choice.is_filtered]


def _choice_for_deck_id(deck_id: int) -> DeckChoice | None:
    for choice in _all_deck_choices():
        if int(choice.deck_id) == int(deck_id):
            return choice
    return None


def _subtree_deck_ids(choice: DeckChoice, all_choices: list[DeckChoice]) -> list[int]:
    prefix = f"{choice.name}::"
    return [
        int(candidate.deck_id)
        for candidate in all_choices
        if not candidate.is_filtered and (candidate.name == choice.name or candidate.name.startswith(prefix))
    ]


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(int(count)))


def _lower_bound_ms(days: int) -> int:
    safe_days = max(1, min(7, int(days)))
    now = datetime.now().astimezone()
    start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    lower = start_of_today - timedelta(days=safe_days - 1)
    return int(lower.timestamp() * 1000)


def _recent_new_card_ids_for_choice(choice: DeckChoice, days: int) -> list[int]:
    if choice.is_filtered:
        return []

    all_choices = _normal_deck_choices()
    subtree_ids = _subtree_deck_ids(choice, all_choices)
    if not subtree_ids:
        return []

    placeholders = _placeholders(len(subtree_ids))
    lower_bound = _lower_bound_ms(days)
    upper_bound = int(datetime.now().timestamp() * 1000) + 1000
    return _db_list(
        f"""
        SELECT c.id
        FROM cards AS c
        WHERE c.did IN ({placeholders})
          AND c.queue = 0
          AND c.type = 0
          AND c.id >= ?
          AND c.id <= ?
        ORDER BY c.id DESC
        """,
        *[int(deck_id) for deck_id in subtree_ids],
        int(lower_bound),
        int(upper_bound),
    )


def _period_label(days: int) -> str:
    safe_days = max(1, min(7, int(days)))
    if safe_days == 1:
        return "today"
    return f"the past {safe_days} days"


def build_recent_new_filtered_deck_for_choice(choice: DeckChoice, *, days: int, parent=None) -> bool:
    if choice.is_filtered:
        showWarning("Please choose a normal deck for this new-cards builder.")
        return False

    safe_days = max(1, min(7, int(days)))
    card_ids = _recent_new_card_ids_for_choice(choice, safe_days)
    if not card_ids:
        QMessageBox.information(
            parent or mw,
            WINDOW_TITLE,
            f"No still-new cards created in {_period_label(safe_days)} were found in '{choice.name}'.",
        )
        return False

    deck_name = datetime.now().strftime(f"{FILTERED_DECK_NAME_PREFIX}%Y-%m-%d %H-%M-%S")
    search = " or ".join(f"cid:{card_id}" for card_id in card_ids)

    try:
        create_or_update_filtered_deck(
            deck_name,
            search=search,
            limit=len(card_ids),
            resched=True,
        )
    except Exception as exc:
        showWarning(f"Could not create the recent new-cards filtered deck.\n\n{exc}")
        return False

    showInfo(
        f"Created '{deck_name}' with {len(card_ids)} new card(s) from '{choice.name}' "
        f"created in {_period_label(safe_days)}."
    )
    return True


class RecentNewCardsDialog(QDialog):
    def __init__(self, *, preset_deck_id: int | None = None) -> None:
        super().__init__(mw)
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(720, 520)
        self._preset_choice = _choice_for_deck_id(int(preset_deck_id)) if preset_deck_id is not None else None
        self._choices = _normal_deck_choices()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Build a rescheduling filtered deck from cards that are still new and were created recently. "
            "Choose a deck, then decide whether you want only today's new cards or the past few days."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        if self._preset_choice is not None:
            deck_label = QLabel(f"Selected deck: {self._preset_choice.name}")
            deck_label.setWordWrap(True)
            layout.addWidget(deck_label)
        else:
            self.selection_summary = QLabel("No deck selected.")
            self.selection_summary.setWordWrap(True)
            layout.addWidget(self.selection_summary)

            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("Search decks...")
            layout.addWidget(self.search_input)

            self.deck_list = QListWidget()
            self.deck_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            self._populate_deck_list()
            layout.addWidget(self.deck_list, 1)

        period_label = QLabel("Create a filtered deck for:")
        layout.addWidget(period_label)

        today_row = QHBoxLayout()
        self.today_radio = QRadioButton("Today")
        self.past_days_radio = QRadioButton("Past")
        self.today_radio.setChecked(True)
        self.days_spin = QSpinBox()
        self.days_spin.setRange(2, 7)
        self.days_spin.setValue(3)
        self.days_spin.setEnabled(False)
        today_row.addWidget(self.today_radio)
        today_row.addSpacing(8)
        today_row.addWidget(self.past_days_radio)
        today_row.addWidget(self.days_spin)
        today_row.addWidget(QLabel("days"))
        today_row.addStretch(1)
        layout.addLayout(today_row)

        self.result_summary = QLabel("No deck selected.")
        self.result_summary.setWordWrap(True)
        layout.addWidget(self.result_summary)

        button_row = QHBoxLayout()
        self.build_button = QPushButton("Build Recent New Cards Deck")
        self.close_button = QPushButton("Close")
        button_row.addStretch(1)
        button_row.addWidget(self.build_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        if self._preset_choice is None:
            self.deck_list.itemSelectionChanged.connect(self._update_summary)
            self.search_input.textChanged.connect(self._apply_filter)
            self._preselect_current_deck()
        self.today_radio.toggled.connect(self._sync_days_ui)
        self.past_days_radio.toggled.connect(self._sync_days_ui)
        self.days_spin.valueChanged.connect(self._update_summary)
        self.build_button.clicked.connect(self._build)
        self.close_button.clicked.connect(self.close)

        self._sync_days_ui()
        self._update_summary()

    def _populate_deck_list(self, selected_id: int | None = None) -> None:
        if self._preset_choice is not None:
            return
        self.deck_list.clear()
        for choice in self._choices:
            item = QListWidgetItem(choice.name)
            item.setData(Qt.ItemDataRole.UserRole, int(choice.deck_id))
            self.deck_list.addItem(item)
            if selected_id is not None and int(choice.deck_id) == int(selected_id):
                item.setSelected(True)

    def _apply_filter(self, *_args) -> None:
        if self._preset_choice is not None:
            return
        search_text = str(self.search_input.text() or "").strip().casefold()
        terms = [term for term in search_text.split() if term]
        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            name = str(item.text()).casefold()
            visible = all(term in name for term in terms) if terms else True
            item.setHidden(not visible)
        self._update_summary()

    def _preselect_current_deck(self) -> None:
        if self._preset_choice is not None:
            return
        current = getattr(mw.col.decks, "current", None)
        if not callable(current):
            return
        try:
            current_deck = current() or {}
            current_id = int(current_deck.get("id", -1))
        except Exception:
            return
        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            if int(item.data(Qt.ItemDataRole.UserRole)) == current_id:
                item.setSelected(True)
                self.deck_list.scrollToItem(item)
                break

    def _selected_choice(self) -> DeckChoice | None:
        if self._preset_choice is not None:
            return self._preset_choice if not self._preset_choice.is_filtered else None
        items = self.deck_list.selectedItems()
        if not items:
            return None
        selected_id = int(items[0].data(Qt.ItemDataRole.UserRole))
        for choice in self._choices:
            if int(choice.deck_id) == selected_id:
                return choice
        return None

    def _selected_days(self) -> int:
        return int(self.days_spin.value()) if self.past_days_radio.isChecked() else 1

    def _sync_days_ui(self) -> None:
        self.days_spin.setEnabled(self.past_days_radio.isChecked())
        self._update_summary()

    def _update_summary(self) -> None:
        choice = self._selected_choice()
        days = self._selected_days()
        period = _period_label(days)
        if self._preset_choice is None and hasattr(self, "selection_summary"):
            if choice is None:
                self.selection_summary.setText("No deck selected.")
            else:
                self.selection_summary.setText(f"Selected deck tree: {choice.name}")
        if choice is None:
            self.result_summary.setText("Choose a deck to preview the recent new-card count.")
            return
        count = len(_recent_new_card_ids_for_choice(choice, days))
        self.result_summary.setText(
            f"{count} still-new card(s) created in {period} would be gathered from '{choice.name}'."
        )

    def _build(self) -> None:
        choice = self._selected_choice()
        if choice is None:
            QMessageBox.information(self, WINDOW_TITLE, "Select a deck first.")
            return
        if build_recent_new_filtered_deck_for_choice(choice, days=self._selected_days(), parent=self):
            self.close()


def open_recent_new_cards_dialog(*, preset_deck_id: int | None = None) -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.close()
        except Exception:
            pass
    _dialog = RecentNewCardsDialog(preset_deck_id=preset_deck_id)
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    choice = _choice_for_deck_id(int(deck_id))
    if choice is None or choice.is_filtered:
        return
    if menu.actions():
        menu.addSeparator()
    action = QAction(GEAR_ACTION_LABEL, menu)
    action.triggered.connect(lambda *_args, did=int(deck_id): open_recent_new_cards_dialog(preset_deck_id=did))
    menu.addAction(action)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    hook = getattr(gui_hooks, "deck_browser_will_show_options_menu", None)
    if hook is not None:
        hook.append(_maybe_add_deck_browser_action)
        _HOOK_REGISTERED = True
        return

    try:
        from anki.hooks import addHook
    except Exception:
        return

    addHook("showDeckOptions", _maybe_add_deck_browser_action)
    _HOOK_REGISTERED = True
