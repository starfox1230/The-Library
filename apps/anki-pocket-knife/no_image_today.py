from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
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
    QVBoxLayout,
    Qt,
)
from aqt.utils import showInfo, showWarning

from .common import create_or_update_filtered_deck, get_card
from .restore_tracker import register_restore_batch


NO_IMAGE_DECK_NAME_PREFIX = "No image cards "
GEAR_ACTION_LABEL = "Build No-Image Today Deck From This Deck"
_HOOK_REGISTERED = False


@dataclass(frozen=True)
class DeckChoice:
    deck_id: int
    name: str
    is_filtered: bool


@dataclass(frozen=True)
class DeckCounts:
    new_count: int
    learn_count: int
    review_count: int

    @property
    def total(self) -> int:
        return int(self.new_count) + int(self.learn_count) + int(self.review_count)


class _ImageDetector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found_image = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.found_image = True

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() == "img":
            self.found_image = True


def question_has_image(question_html: str) -> bool:
    parser = _ImageDetector()
    parser.feed(question_html or "")
    parser.close()
    return bool(parser.found_image)


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


def _node_attr(node: Any, *names: str, default: int = 0) -> int:
    for name in names:
        if hasattr(node, name):
            try:
                return int(getattr(node, name))
            except Exception:
                continue
    return int(default)


def _deck_due_count_map() -> dict[int, DeckCounts]:
    scheduler = mw.col.sched
    method = getattr(scheduler, "deck_due_tree", None)
    if not callable(method):
        method = getattr(scheduler, "deckDueTree", None)
    if not callable(method):
        return {}

    try:
        root = method()
    except Exception:
        return {}

    counts: dict[int, DeckCounts] = {}

    def walk(node: Any) -> None:
        deck_id = _node_attr(node, "deck_id", "deckId", default=-1)
        if deck_id >= 0:
            counts[int(deck_id)] = DeckCounts(
                new_count=_node_attr(node, "new_count", "newCount"),
                learn_count=_node_attr(node, "learn_count", "learnCount"),
                review_count=_node_attr(node, "review_count", "reviewCount"),
            )
        for child in getattr(node, "children", []) or []:
            walk(child)

    walk(root)
    return counts


def _filtered_deck_live_card_ids(deck_id: int) -> list[int]:
    return _db_list(
        """
        SELECT c.id
        FROM cards AS c
        WHERE c.did = ?
        ORDER BY
          CASE
            WHEN c.queue IN (1, 3) THEN 0
            WHEN c.queue = 2 THEN 1
            WHEN c.queue = 0 THEN 2
            ELSE 3
          END,
          c.due ASC,
          c.id ASC
        """,
        int(deck_id),
    )


def _current_filtered_deck_assignments(card_ids: list[int]) -> dict[int, int]:
    unique_ids = [int(card_id) for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)]
    if not unique_ids:
        return {}
    placeholders = _placeholders(len(unique_ids))
    rows = mw.col.db.all(
        f"""
        SELECT c.id, c.did
        FROM cards AS c
        WHERE c.id IN ({placeholders})
          AND c.odid != 0
        """,
        *unique_ids,
    )
    return {int(card_id): int(deck_id) for card_id, deck_id in rows}


def _group_source_assignments(source_assignments: dict[int, int]) -> dict[int, list[int]]:
    grouped: dict[int, list[int]] = {}
    for raw_card_id, raw_deck_id in source_assignments.items():
        try:
            card_id = int(raw_card_id)
            deck_id = int(raw_deck_id)
        except Exception:
            continue
        if card_id <= 0 or deck_id <= 0:
            continue
        grouped.setdefault(deck_id, []).append(card_id)
    return {deck_id: sorted(card_ids) for deck_id, card_ids in grouped.items()}


def _currently_in_filtered_deck(card_ids: list[int]) -> list[int]:
    unique_ids = [int(card_id) for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)]
    if not unique_ids:
        return []
    placeholders = _placeholders(len(unique_ids))
    return _db_list(
        f"""
        SELECT c.id
        FROM cards AS c
        WHERE c.id IN ({placeholders})
          AND c.odid != 0
        """,
        *unique_ids,
    )


def _remove_cards_from_filtered_decks(card_ids: list[int]) -> list[int]:
    filtered_ids = _currently_in_filtered_deck(card_ids)
    if not filtered_ids:
        return []

    scheduler = mw.col.sched
    method_attempts = [
        ("remove_from_filtered_deck", ((filtered_ids,), {})),
        ("remove_from_filtered_deck", ((), {"card_ids": filtered_ids})),
        ("rem_from_dyn", ((filtered_ids,), {})),
        ("remFromDyn", ((filtered_ids,), {})),
    ]
    for method_name, (args, kwargs) in method_attempts:
        method = getattr(scheduler, method_name, None)
        if not callable(method):
            continue
        try:
            method(*args, **kwargs)
            return filtered_ids
        except TypeError:
            continue
        except Exception:
            continue

    usn_value = 0
    usn = getattr(mw.col, "usn", None)
    if callable(usn):
        try:
            usn_value = int(usn())
        except Exception:
            usn_value = 0

    placeholders = _placeholders(len(filtered_ids))
    _db_execute(
        f"""
        UPDATE cards
        SET did = odid,
            queue = (CASE WHEN type = 1 THEN 0 ELSE type END),
            type = (CASE WHEN type = 1 THEN 0 ELSE type END),
            due = odue,
            odue = 0,
            odid = 0,
            usn = ?
        WHERE id IN ({placeholders})
          AND odid != 0
        """,
        int(usn_value),
        *filtered_ids,
    )
    return filtered_ids


def _filtered_deck_live_counts(deck_id: int) -> DeckCounts:
    rows = mw.col.db.all(
        """
        SELECT c.queue, COUNT(*)
        FROM cards AS c
        WHERE c.did = ?
        GROUP BY c.queue
        """,
        int(deck_id),
    )

    new_count = 0
    learn_count = 0
    review_count = 0
    for queue_value, count_value in rows:
        queue = int(queue_value)
        count = int(count_value)
        if queue == 0:
            new_count += count
        elif queue in (1, 3):
            learn_count += count
        elif queue == 2:
            review_count += count

    return DeckCounts(new_count=new_count, learn_count=learn_count, review_count=review_count)


def _counts_for_choice(choice: DeckChoice, due_counts: dict[int, DeckCounts]) -> DeckCounts:
    if choice.is_filtered:
        return _filtered_deck_live_counts(int(choice.deck_id))
    return due_counts.get(int(choice.deck_id), DeckCounts(0, 0, 0))


def _subtree_deck_ids(choice: DeckChoice, all_choices: list[DeckChoice]) -> list[int]:
    if choice.is_filtered:
        return [int(choice.deck_id)]
    prefix = f"{choice.name}::"
    return [
        int(candidate.deck_id)
        for candidate in all_choices
        if candidate.name == choice.name or candidate.name.startswith(prefix)
    ]


def _normalized_selected_choices(selected: list[DeckChoice]) -> list[DeckChoice]:
    normalized: list[DeckChoice] = []
    selected_sorted = sorted(selected, key=lambda item: (item.name.count("::"), item.name.casefold()))
    for candidate in selected_sorted:
        skip = False
        for kept in normalized:
            if kept.is_filtered:
                continue
            if candidate.name == kept.name or candidate.name.startswith(f"{kept.name}::"):
                skip = True
                break
        if not skip:
            normalized.append(candidate)
    return normalized


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(int(count)))


def _fetch_bucket_card_ids(deck_ids: list[int], *, bucket: str, limit: int) -> list[int]:
    if not deck_ids or limit <= 0:
        return []

    deck_placeholders = _placeholders(len(deck_ids))
    if bucket == "new":
        sql = f"""
            SELECT c.id
            FROM cards AS c
            WHERE c.did IN ({deck_placeholders})
              AND c.queue = 0
            ORDER BY c.due ASC, c.id ASC
            LIMIT ?
        """
    elif bucket == "learn":
        sql = f"""
            SELECT c.id
            FROM cards AS c
            WHERE c.did IN ({deck_placeholders})
              AND c.queue IN (1, 3)
            ORDER BY CASE WHEN c.queue = 1 THEN 0 ELSE 1 END, c.due ASC, c.id ASC
            LIMIT ?
        """
    else:
        sql = f"""
            SELECT c.id
            FROM cards AS c
            WHERE c.did IN ({deck_placeholders})
              AND c.queue = 2
              AND c.type = 2
            ORDER BY c.due ASC, c.id ASC
            LIMIT ?
        """

    return _db_list(sql, *[int(deck_id) for deck_id in deck_ids], int(limit))


def surfaced_today_card_ids_for_choices(selected_choices: list[DeckChoice]) -> tuple[list[int], DeckCounts]:
    all_choices = _all_deck_choices()
    selected_choices = _normalized_selected_choices(selected_choices)
    due_counts = _deck_due_count_map()

    ordered_ids: list[int] = []
    seen: set[int] = set()
    total_counts = DeckCounts(new_count=0, learn_count=0, review_count=0)

    for choice in selected_choices:
        deck_counts = _counts_for_choice(choice, due_counts)
        total_counts = DeckCounts(
            new_count=total_counts.new_count + deck_counts.new_count,
            learn_count=total_counts.learn_count + deck_counts.learn_count,
            review_count=total_counts.review_count + deck_counts.review_count,
        )
        if choice.is_filtered:
            bucket_ids = _filtered_deck_live_card_ids(int(choice.deck_id))
        else:
            subtree_ids = _subtree_deck_ids(choice, all_choices)
            bucket_ids = (
                _fetch_bucket_card_ids(subtree_ids, bucket="learn", limit=deck_counts.learn_count)
                + _fetch_bucket_card_ids(subtree_ids, bucket="review", limit=deck_counts.review_count)
                + _fetch_bucket_card_ids(subtree_ids, bucket="new", limit=deck_counts.new_count)
            )
        for card_id in bucket_ids:
            if card_id in seen:
                continue
            seen.add(card_id)
            ordered_ids.append(int(card_id))

    return ordered_ids, total_counts


def no_image_question_card_ids(card_ids: list[int]) -> list[int]:
    result: list[int] = []
    for card_id in card_ids:
        try:
            card = get_card(int(card_id))
            if not question_has_image(str(card.question() or "")):
                result.append(int(card_id))
        except Exception:
            continue
    return result


def _choice_for_deck_id(deck_id: int) -> DeckChoice | None:
    for choice in _all_deck_choices():
        if int(choice.deck_id) == int(deck_id):
            return choice
    return None


def build_no_image_today_deck_for_choices(selected_choices: list[DeckChoice], *, parent=None) -> bool:
    selected = _normalized_selected_choices(selected_choices)
    if not selected:
        QMessageBox.information(parent or mw, "No-Image Cards For Today", "Select at least one deck first.")
        return False

    surfaced_ids, counts = surfaced_today_card_ids_for_choices(selected)
    if not surfaced_ids:
        QMessageBox.information(
            parent or mw,
            "No-Image Cards For Today",
            "Anki is not surfacing any cards today for the selected deck level(s).",
        )
        return False

    no_image_ids = no_image_question_card_ids(surfaced_ids)
    if not no_image_ids:
        QMessageBox.information(
            parent or mw,
            "No-Image Cards For Today",
            "All surfaced cards for the selected deck level(s) already have an image on the question side.",
        )
        return False

    source_assignments = _current_filtered_deck_assignments(no_image_ids)
    source_filtered_cards = _group_source_assignments(source_assignments)
    source_filtered_card_ids = sorted(source_assignments.keys())
    if source_filtered_card_ids:
        decision = QMessageBox.question(
            parent or mw,
            "No-Image Cards For Today",
            (
                f"{len(source_filtered_card_ids)} matching card(s) are currently inside another filtered deck.\n\n"
                "To move them into the new no-image deck, Anki Pocket Knife needs to remove those cards from "
                "their current filtered deck first and return them to their original deck.\n\n"
                "Continue?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if decision != QMessageBox.StandardButton.Yes:
            return False
        try:
            _remove_cards_from_filtered_decks(source_filtered_card_ids)
        except Exception as exc:
            showWarning(
                "Could not move cards out of their current filtered deck before building the new one.\n\n"
                f"{exc}"
            )
            return False

    deck_name = datetime.now().strftime(f"{NO_IMAGE_DECK_NAME_PREFIX}%Y-%m-%d %H-%M-%S")
    search = " or ".join(f"cid:{card_id}" for card_id in no_image_ids)

    try:
        target_deck_id = create_or_update_filtered_deck(
            deck_name,
            search=search,
            limit=len(no_image_ids),
            resched=True,
        )
    except Exception as exc:
        showWarning(f"Could not create the no-image filtered deck.\n\n{exc}")
        return False

    if source_assignments:
        register_restore_batch(
            target_deck_id=int(target_deck_id),
            target_deck_name=deck_name,
            source_filtered_deck_ids=sorted({int(deck_id) for deck_id in source_assignments.values()}),
            source_filtered_cards=source_filtered_cards,
        )

    showInfo(
        f"Created '{deck_name}' with {len(no_image_ids)} no-image cards "
        f"from {len(surfaced_ids)} surfaced cards "
        f"(new {counts.new_count}, learn {counts.learn_count}, review {counts.review_count})."
        + (
            f"\n\nMoved {len(source_filtered_card_ids)} card(s) out of an existing filtered deck first."
            if source_filtered_card_ids
            else ""
        )
    )
    return True


def build_no_image_today_deck_for_deck_id(deck_id: int, *, parent=None) -> bool:
    choice = _choice_for_deck_id(int(deck_id))
    if choice is None:
        showWarning("Could not find that deck in Anki's current deck list.")
        return False
    return build_no_image_today_deck_for_choices([choice], parent=parent)


class NoImageTodayDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("No-Image Cards For Today")
        self.resize(760, 520)
        self._choices = _all_deck_choices()
        self._counts = _deck_due_count_map()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Select one or more decks. Parent deck selections win over their subdecks to avoid duplicates. "
            "Filtered decks are included in the list when Anki is surfacing them, and selected filtered decks use "
            "their current gathered contents directly. If matching cards are already inside another filtered deck, "
            "Pocket Knife can move them out first so they can be gathered into the new no-image deck, then rebuild "
            "their prior filtered deck automatically after the no-image deck is deleted."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.selection_summary = QLabel("No decks selected.")
        self.selection_summary.setWordWrap(True)
        layout.addWidget(self.selection_summary)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search decks...")
        layout.addWidget(self.search_input)

        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self._populate_deck_list()
        layout.addWidget(self.deck_list, 1)

        button_row = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Counts")
        self.build_button = QPushButton("Build No-Image Deck")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.refresh_button)
        button_row.addStretch(1)
        button_row.addWidget(self.build_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.deck_list.itemSelectionChanged.connect(self._update_selection_summary)
        self.search_input.textChanged.connect(self._apply_filter)
        self.refresh_button.clicked.connect(self._refresh)
        self.build_button.clicked.connect(self._build)
        self.close_button.clicked.connect(self.close)

        self._preselect_current_deck()
        self._update_selection_summary()

    def _current_selected_choices(self) -> list[DeckChoice]:
        selected_ids = {
            int(item.data(Qt.ItemDataRole.UserRole))
            for item in self.deck_list.selectedItems()
        }
        return [choice for choice in self._choices if int(choice.deck_id) in selected_ids]

    def _choice_label(self, choice: DeckChoice) -> str:
        counts = _counts_for_choice(choice, self._counts)
        label = f"{choice.name}"
        if choice.is_filtered:
            label += " [filtered, current contents]"
        label += f"  |  today: {counts.total} (new {counts.new_count}, learn {counts.learn_count}, review {counts.review_count})"
        return label

    def _populate_deck_list(self, selected_ids: set[int] | None = None) -> None:
        selected_ids = set(selected_ids or set())
        self.deck_list.clear()
        for choice in self._choices:
            item = QListWidgetItem(self._choice_label(choice))
            item.setData(Qt.ItemDataRole.UserRole, int(choice.deck_id))
            self.deck_list.addItem(item)
            if int(choice.deck_id) in selected_ids:
                item.setSelected(True)

    def _matches_search(self, choice: DeckChoice, search_text: str) -> bool:
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

    def _refresh(self) -> None:
        selected_ids = {int(choice.deck_id) for choice in self._current_selected_choices()}
        self._choices = _all_deck_choices()
        self._counts = _deck_due_count_map()
        self._populate_deck_list(selected_ids=selected_ids)
        self._preselect_current_deck()
        self._apply_filter()
        self._update_selection_summary()

    def _update_selection_summary(self) -> None:
        selected = _normalized_selected_choices(self._current_selected_choices())
        if not selected:
            self.selection_summary.setText("No decks selected.")
            return
        surfaced_ids, counts = surfaced_today_card_ids_for_choices(selected)
        self.selection_summary.setText(
            f"{len(selected)} effective deck selection(s). "
            f"Surfaced today: {len(surfaced_ids)} cards "
            f"(new {counts.new_count}, learn {counts.learn_count}, review {counts.review_count})."
        )

    def _build(self) -> None:
        completed = build_no_image_today_deck_for_choices(self._current_selected_choices(), parent=self)
        if completed:
            self.close()


_dialog: NoImageTodayDialog | None = None


def open_no_image_today_dialog() -> None:
    global _dialog
    if _dialog is not None:
        try:
            _dialog.close()
        except Exception:
            pass
    _dialog = NoImageTodayDialog()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    if menu.actions():
        menu.addSeparator()

    action = QAction(GEAR_ACTION_LABEL, menu)
    action.triggered.connect(lambda *_args, did=int(deck_id): build_no_image_today_deck_for_deck_id(did))
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
