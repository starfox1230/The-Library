from __future__ import annotations

from dataclasses import dataclass
import time
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
    QVBoxLayout,
    Qt,
    QMenu,
)
from aqt.utils import showInfo, showWarning

from .restore_tracker import exclude_restored_cards_for_target_deck


ACTION_LABEL = "Send Non-New Cards Back To Original Decks"
_HOOK_REGISTERED = False
_dialog: "ReturnNonNewDialog | None" = None


@dataclass(frozen=True)
class FilteredDeckChoice:
    deck_id: int
    name: str
    total_count: int
    new_count: int
    non_new_count: int


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(int(count)))


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


def _db_execute(sql: str, *args: Any) -> None:
    db = mw.col.db
    execute = getattr(db, "execute", None)
    if callable(execute):
        execute(sql, *args)
        return
    executemany = getattr(db, "executemany", None)
    if callable(executemany):
        executemany(sql, [args])
        return
    raise RuntimeError("Database execute API not available.")


def _all_filtered_deck_choices() -> list[FilteredDeckChoice]:
    manager = mw.col.decks
    seen_ids: set[int] = set()
    choices: list[FilteredDeckChoice] = []

    all_names_and_ids = getattr(manager, "all_names_and_ids", None)
    raw_items: list[Any] = []
    if callable(all_names_and_ids):
        try:
            raw_items = list(all_names_and_ids() or [])
        except Exception:
            raw_items = []

    if not raw_items:
        all_method = getattr(manager, "all", None)
        if callable(all_method):
            try:
                fallback = all_method()
            except Exception:
                fallback = []
            if isinstance(fallback, dict):
                raw_items = list(fallback.values())
            else:
                raw_items = list(fallback or [])

    for item in raw_items:
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
            deck_id = int(deck_id)
        except Exception:
            continue
        if deck_id <= 0 or deck_id in seen_ids:
            continue

        try:
            deck = manager.get(deck_id) or {}
        except Exception:
            deck = {}
        is_filtered = bool(deck.get("dyn", is_filtered))
        if not is_filtered:
            continue

        total_count, new_count, non_new_count = _filtered_deck_counts(deck_id)
        choices.append(
            FilteredDeckChoice(
                deck_id=deck_id,
                name=str(name),
                total_count=total_count,
                new_count=new_count,
                non_new_count=non_new_count,
            )
        )
        seen_ids.add(deck_id)

    return sorted(choices, key=lambda choice: choice.name.casefold())


def _filtered_deck_counts(deck_id: int) -> tuple[int, int, int]:
    row = mw.col.db.first(
        """
        SELECT
          COUNT(*),
          SUM(CASE WHEN c.type = 0 THEN 1 ELSE 0 END),
          SUM(CASE WHEN c.type != 0 THEN 1 ELSE 0 END)
        FROM cards AS c
        WHERE c.did = ?
          AND c.odid != 0
        """,
        int(deck_id),
    )
    if not row:
        return (0, 0, 0)
    total_count = int(row[0] or 0)
    new_count = int(row[1] or 0)
    non_new_count = int(row[2] or 0)
    return (total_count, new_count, non_new_count)


def _non_new_card_ids_in_filtered_deck(deck_id: int) -> list[int]:
    return _db_list(
        """
        SELECT c.id
        FROM cards AS c
        WHERE c.did = ?
          AND c.odid != 0
          AND c.type != 0
        ORDER BY c.id ASC
        """,
        int(deck_id),
    )


def _current_deck_name(deck_id: int) -> str:
    try:
        deck = mw.col.decks.get(int(deck_id)) or {}
    except Exception:
        deck = {}
    name = deck.get("name")
    if name:
        return str(name)
    try:
        return str(mw.col.decks.name(int(deck_id)))
    except Exception:
        return f"Filtered deck {int(deck_id)}"


def _move_cards_home_preserving_schedule(deck_id: int, card_ids: list[int]) -> int:
    unique_card_ids = [int(card_id) for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)]
    if not unique_card_ids:
        return 0

    exclude_restored_cards_for_target_deck(target_deck_id=int(deck_id), card_ids=unique_card_ids)

    usn_value = 0
    usn = getattr(mw.col, "usn", None)
    if callable(usn):
        try:
            usn_value = int(usn())
        except Exception:
            usn_value = 0
    mod_value = int(time.time())

    chunk_size = 250
    for start in range(0, len(unique_card_ids), chunk_size):
        chunk = unique_card_ids[start : start + chunk_size]
        placeholders = _placeholders(len(chunk))
        _db_execute(
            f"""
            UPDATE cards
            SET did = odid,
                odid = 0,
                odue = 0,
                mod = ?,
                usn = ?
            WHERE id IN ({placeholders})
              AND did = ?
              AND odid != 0
              AND type != 0
            """,
            int(mod_value),
            int(usn_value),
            *chunk,
            int(deck_id),
        )

    mw.reset()
    return len(unique_card_ids)


def send_non_new_cards_back_to_original_decks(deck_id: int, *, parent=None) -> bool:
    try:
        deck = mw.col.decks.get(int(deck_id)) or {}
    except Exception:
        deck = {}
    if not deck or not deck.get("dyn"):
        showWarning("That deck is not a filtered deck.")
        return False

    deck_name = _current_deck_name(int(deck_id))
    candidate_ids = _non_new_card_ids_in_filtered_deck(int(deck_id))
    if not candidate_ids:
        total_count, new_count, _non_new_count = _filtered_deck_counts(int(deck_id))
        QMessageBox.information(
            parent or mw,
            ACTION_LABEL,
            (
                f"'{deck_name}' does not currently contain any non-new cards to send home.\n\n"
                f"Current filtered-deck contents: {total_count} total card(s), {new_count} new card(s)."
            ),
        )
        return False

    moved_count = _move_cards_home_preserving_schedule(int(deck_id), candidate_ids)
    total_count, new_count, non_new_count = _filtered_deck_counts(int(deck_id))
    showInfo(
        f"Sent {moved_count} non-new card(s) from '{deck_name}' back to their original deck(s).\n\n"
        f"Their current schedule was kept.\n"
        f"Still in the filtered deck: {total_count} total card(s), {new_count} new card(s), {non_new_count} non-new card(s)."
    )
    return True


class ReturnNonNewDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle(ACTION_LABEL)
        self.resize(760, 500)
        self._choices = _all_filtered_deck_choices()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Pick a filtered deck and send only its current non-new cards back to their original deck. "
            "Pocket Knife keeps those cards' current schedule, and any cards that are still new stay in the filtered deck."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.selection_summary = QLabel("No filtered deck selected.")
        self.selection_summary.setWordWrap(True)
        layout.addWidget(self.selection_summary)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search filtered decks...")
        layout.addWidget(self.search_input)

        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._populate_deck_list()
        layout.addWidget(self.deck_list, 1)

        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Filtered Decks")
        self.run_button = QPushButton("Send Non-New Cards Home")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.refresh_button)
        button_row.addStretch(1)
        button_row.addWidget(self.run_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.deck_list.itemSelectionChanged.connect(self._update_selection_summary)
        self.deck_list.itemDoubleClicked.connect(lambda *_args: self._run())
        self.search_input.textChanged.connect(self._apply_filter)
        self.refresh_button.clicked.connect(self._refresh)
        self.run_button.clicked.connect(self._run)
        self.close_button.clicked.connect(self.close)

        self._preselect_current_deck()
        self._update_selection_summary()

    def _choice_label(self, choice: FilteredDeckChoice) -> str:
        return (
            f"{choice.name}  |  current: {choice.total_count} "
            f"(new {choice.new_count}, non-new {choice.non_new_count})"
        )

    def _populate_deck_list(self, selected_id: int | None = None) -> None:
        self.deck_list.clear()
        for choice in self._choices:
            item = QListWidgetItem(self._choice_label(choice))
            item.setData(Qt.ItemDataRole.UserRole, int(choice.deck_id))
            self.deck_list.addItem(item)
            if selected_id is not None and int(choice.deck_id) == int(selected_id):
                item.setSelected(True)

    def _selected_choice(self) -> FilteredDeckChoice | None:
        items = self.deck_list.selectedItems()
        if not items:
            return None
        deck_id = int(items[0].data(Qt.ItemDataRole.UserRole))
        for choice in self._choices:
            if int(choice.deck_id) == deck_id:
                return choice
        return None

    def _matches_search(self, choice: FilteredDeckChoice, search_text: str) -> bool:
        search_text = str(search_text or "").strip().casefold()
        if not search_text:
            return True
        haystack = choice.name.casefold()
        terms = [term for term in search_text.split() if term]
        return all(term in haystack for term in terms)

    def _apply_filter(self, *_args) -> None:
        search_text = self.search_input.text()
        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            deck_id = int(item.data(Qt.ItemDataRole.UserRole))
            choice = next((choice for choice in self._choices if int(choice.deck_id) == deck_id), None)
            visible = True if choice is None else self._matches_search(choice, search_text)
            item.setHidden(not visible)
        self._update_selection_summary()

    def _preselect_current_deck(self) -> None:
        current = getattr(mw.col.decks, "current", None)
        current_id = None
        if callable(current):
            try:
                current_deck = current() or {}
                current_id = int(current_deck.get("id", -1))
            except Exception:
                current_id = None

        if current_id is None or not any(int(choice.deck_id) == current_id for choice in self._choices):
            if self.deck_list.count():
                self.deck_list.item(0).setSelected(True)
            return

        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            if int(item.data(Qt.ItemDataRole.UserRole)) == current_id:
                item.setSelected(True)
                self.deck_list.scrollToItem(item)
                return

    def _refresh(self) -> None:
        selected = self._selected_choice()
        selected_id = int(selected.deck_id) if selected is not None else None
        self._choices = _all_filtered_deck_choices()
        self._populate_deck_list(selected_id=selected_id)
        if selected_id is None:
            self._preselect_current_deck()
        self._apply_filter()
        self._update_selection_summary()

    def _update_selection_summary(self) -> None:
        choice = self._selected_choice()
        if choice is None:
            self.selection_summary.setText("No filtered deck selected.")
            self.run_button.setEnabled(False)
            return

        self.selection_summary.setText(
            f"Selected: {choice.name}. "
            f"Sending now would move {choice.non_new_count} non-new card(s) home and leave {choice.new_count} new card(s) behind."
        )
        self.run_button.setEnabled(True)

    def _run(self) -> None:
        choice = self._selected_choice()
        if choice is None:
            QMessageBox.information(self, ACTION_LABEL, "Select a filtered deck first.")
            return

        completed = send_non_new_cards_back_to_original_decks(int(choice.deck_id), parent=self)
        if completed:
            self._refresh()


def open_return_non_new_dialog() -> None:
    global _dialog
    if not _all_filtered_deck_choices():
        showInfo("There are no filtered decks available right now.")
        return
    if _dialog is not None:
        try:
            _dialog.close()
        except Exception:
            pass
    _dialog = ReturnNonNewDialog()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    try:
        deck = mw.col.decks.get(int(deck_id)) or {}
    except Exception:
        return
    if not deck or not deck.get("dyn"):
        return

    if menu.actions():
        menu.addSeparator()

    action = QAction(ACTION_LABEL, menu)
    action.triggered.connect(lambda *_args, did=int(deck_id): send_non_new_cards_back_to_original_decks(did))
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
