from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDate,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    Qt,
)
from aqt.utils import showInfo, showWarning

from .common import (
    FILTERED_DECK_ORDER_RANDOM,
    build_shared_deck_action_item,
    card_id_search,
    create_or_update_filtered_deck,
    get_card,
    inject_shared_deck_action_html,
)
from .due_today_core import (
    added_card_id_bounds,
    days_ago_for_date,
    deck_date_range_label,
    expand_deck_selection,
    normalize_deck_selection,
    rendered_question_has_image,
    rollover_boundaries,
    selected_scheduler_day,
    target_deck_names_for_range,
)
from .restore_tracker import consume_restore_assignments_for_target_decks, register_restore_batch
from .settings import get_setting, set_setting


AUDIO_DECK_NAME = "..Due Today Audio"
VISUAL_DECK_NAME = "..Due Today Visual"
COMBINED_DECK_NAME = "..Due Today Combined"
OPEN_MESSAGE = "anki_pocket_knife_open_due_today"
SOURCE_DECKS_SETTING = "due_today_source_deck_ids"
INCLUDE_ADDED_CARDS_SETTING = "due_day_include_added_cards"
DATE_PRESET_SETTING = "due_day_date_preset"
AUDIO_DECK_ID_SETTING = "due_day_audio_deck_id"
VISUAL_DECK_ID_SETTING = "due_day_visual_deck_id"
COMBINED_DECK_ID_SETTING = "due_day_combined_deck_id"
_HOOK_REGISTERED = False
_dialog: "DueTodayDialog | None" = None


@dataclass(frozen=True)
class DueTodayResult:
    audio_ids: list[int]
    visual_ids: list[int]
    moved_count: int = 0


def _normal_decks() -> dict[int, str]:
    result: dict[int, str] = {}
    manager = mw.col.decks
    names_method = getattr(manager, "all_names_and_ids", None)
    if callable(names_method):
        try:
            raw_names = names_method()
        except Exception:
            raw_names = []
        for item in raw_names or []:
            raw_id = item.get("id") if isinstance(item, dict) else getattr(item, "id", None)
            raw_name = item.get("name") if isinstance(item, dict) else getattr(item, "name", None)
            if raw_id is None or not raw_name:
                continue
            try:
                deck = manager.get(int(raw_id)) or {}
            except Exception:
                deck = {}
            if not deck.get("dyn"):
                result[int(raw_id)] = str(raw_name)
    if result:
        return result

    all_method = getattr(manager, "all", None)
    try:
        raw_items = all_method() if callable(all_method) else []
    except Exception:
        raw_items = []
    if isinstance(raw_items, dict):
        raw_items = raw_items.values()
    for deck in raw_items or []:
        if not isinstance(deck, dict) or deck.get("dyn"):
            continue
        try:
            result[int(deck["id"])] = str(deck["name"])
        except Exception:
            continue
    return result


def _selected_source_ids(deck_names: dict[int, str]) -> list[int]:
    raw = get_setting(SOURCE_DECKS_SETTING)
    if not isinstance(raw, list):
        raw = []
    selected = [int(value) for value in raw if str(value).isdigit() and int(value) in deck_names]
    return normalize_deck_selection(selected or deck_names.keys(), deck_names)


def _deck_id_for_name(name: str) -> int | None:
    finder = getattr(mw.col.decks, "id_for_name", None)
    if not callable(finder):
        return None
    try:
        value = finder(name)
        return int(value) if value is not None else None
    except Exception:
        return None


def _stored_target_deck_id(kind: str) -> int | None:
    settings = {
        "audio": AUDIO_DECK_ID_SETTING,
        "visual": VISUAL_DECK_ID_SETTING,
        "combined": COMBINED_DECK_ID_SETTING,
    }
    legacy_names = {
        "audio": AUDIO_DECK_NAME,
        "visual": VISUAL_DECK_NAME,
        "combined": COMBINED_DECK_NAME,
    }
    setting = settings[kind]
    try:
        deck_id = int(get_setting(setting) or 0)
        deck = mw.col.decks.get(deck_id) if deck_id > 0 else None
        if deck and deck.get("dyn"):
            return deck_id
    except Exception:
        pass
    return _deck_id_for_name(legacy_names[kind])


def _target_names_for_range(start_date: date, end_date: date) -> dict[str, str]:
    return target_deck_names_for_range(start_date, end_date, _today_calendar_date())


def _include_added_cards_enabled() -> bool:
    return bool(get_setting(INCLUDE_ADDED_CARDS_SETTING))


def _rename_target_deck(kind: str, deck_id: int, name: str) -> None:
    deck = mw.col.decks.get(int(deck_id))
    if not deck or not deck.get("dyn"):
        raise RuntimeError(f"Could not load the reusable {kind} filtered deck.")
    existing_id = _deck_id_for_name(name)
    if existing_id is not None and int(existing_id) != int(deck_id):
        raise RuntimeError(f"A different deck already uses the name '{name}'.")
    if str(deck.get("name", "")) == name:
        return
    rename = getattr(mw.col.decks, "rename", None)
    if callable(rename):
        try:
            rename(deck, name)
            return
        except TypeError:
            try:
                rename(int(deck_id), name)
                return
            except Exception:
                pass
        except Exception:
            pass
    deck["name"] = name
    mw.col.decks.save(deck)


def _remove_from_filtered(card_ids: list[int]) -> None:
    if not card_ids:
        return
    scheduler = mw.col.sched
    for method_name in ("remove_from_filtered_deck", "rem_from_dyn", "remFromDyn"):
        method = getattr(scheduler, method_name, None)
        if not callable(method):
            continue
        try:
            method(card_ids)
            return
        except TypeError:
            try:
                method(card_ids=card_ids)
                return
            except Exception:
                continue
        except Exception:
            continue
    raise RuntimeError("This Anki version cannot remove cards from filtered decks.")


def _delete_empty_deck(deck_id: int) -> None:
    rows = mw.col.db.all("SELECT COUNT(*) FROM cards WHERE did = ?", int(deck_id))
    if rows and int(rows[0][0] or 0) != 0:
        raise RuntimeError("Could not delete a non-empty Due-Day deck.")
    manager = mw.col.decks
    remove = getattr(manager, "remove", None)
    if callable(remove):
        for args in (([int(deck_id)],), (int(deck_id),)):
            try:
                remove(*args)
                return
            except TypeError:
                continue
            except Exception:
                break
    rem = getattr(manager, "rem", None)
    if callable(rem):
        for args, kwargs in (
            (([int(deck_id)],), {"cardsToo": False, "childrenToo": False}),
            ((int(deck_id),), {"cardsToo": False, "childrenToo": False}),
            (([int(deck_id)],), {}),
            ((int(deck_id),), {}),
        ):
            try:
                rem(*args, **kwargs)
                return
            except TypeError:
                continue
            except Exception:
                break
    if mw.col.decks.get(int(deck_id)):
        raise RuntimeError("This Anki version could not delete the empty Due-Day deck.")


def _clear_target_setting(kind: str) -> None:
    setting = {
        "audio": AUDIO_DECK_ID_SETTING,
        "visual": VISUAL_DECK_ID_SETTING,
        "combined": COMBINED_DECK_ID_SETTING,
    }[kind]
    set_setting(setting, 0)


def _empty_target_decks(kind: str) -> dict[int, int]:
    if kind == "combined":
        kinds = ["audio", "visual", "combined"]
        delete_kinds = ["audio", "visual"]
    elif kind == "both":
        kinds = ["audio", "visual", "combined"]
        delete_kinds = ["combined"]
    else:
        kinds = [kind, "combined"]
        delete_kinds = ["combined"]
    target_by_kind = {
        target_kind: deck_id
        for target_kind in kinds
        if (deck_id := _stored_target_deck_id(target_kind))
    }
    target_ids = list(target_by_kind.values())
    if not target_ids:
        return {}
    prior_assignments = consume_restore_assignments_for_target_decks(target_ids)
    placeholders = ", ".join("?" for _ in target_ids)
    card_ids = [
        int(row[0])
        for row in mw.col.db.all(
            f"SELECT id FROM cards WHERE did IN ({placeholders}) AND odid != 0",
            *target_ids,
        )
    ]
    _remove_from_filtered(card_ids)
    for target_kind in delete_kinds:
        deck_id = target_by_kind.get(target_kind)
        if deck_id is None:
            continue
        _delete_empty_deck(deck_id)
        _clear_target_setting(target_kind)
    return prior_assignments


def _scheduler_today() -> int:
    return int(getattr(mw.col.sched, "today"))


def _day_cutoff() -> int:
    cutoff = getattr(mw.col.sched, "day_cutoff", None)
    if callable(cutoff):
        cutoff = cutoff()
    if cutoff is None:
        cutoff = getattr(mw.col.sched, "dayCutoff", None)
        if callable(cutoff):
            cutoff = cutoff()
    if cutoff is None:
        raise RuntimeError("Could not determine Anki's day cutoff.")
    return int(cutoff)


def qualifying_card_ids(
    source_deck_ids: list[int],
    days_ago: int = 0,
    *,
    include_added_cards: bool | None = None,
) -> list[int]:
    selected_date = _today_calendar_date() - timedelta(days=max(0, int(days_ago)))
    return qualifying_card_ids_for_range(
        source_deck_ids,
        selected_date,
        selected_date,
        include_added_cards=include_added_cards,
    )


def qualifying_card_ids_for_range(
    source_deck_ids: list[int],
    start_date: date,
    end_date: date,
    *,
    include_added_cards: bool | None = None,
) -> list[int]:
    if not source_deck_ids:
        return []
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if include_added_cards is None:
        include_added_cards = _include_added_cards_enabled()
    placeholders = ", ".join("?" for _ in source_deck_ids)
    today = _scheduler_today()
    today_date = _today_calendar_date()
    cutoff = _day_cutoff()
    start_days_ago = days_ago_for_date(start_date, today_date)
    end_days_ago = days_ago_for_date(end_date, today_date)
    start_day = selected_scheduler_day(today, start_days_ago)
    end_day = selected_scheduler_day(today, end_days_ago)
    if start_day > end_day:
        start_day, end_day = end_day, start_day
    timestamp_start, _ = rollover_boundaries(cutoff, start_days_ago)
    _, timestamp_end = rollover_boundaries(cutoff, end_days_ago)
    if end_days_ago == 0:
        timestamp_end = min(int(time.time()) + 1, timestamp_end)
    added_start, added_end = added_card_id_bounds(timestamp_start, timestamp_end)
    rows = mw.col.db.all(
        f"""
        SELECT c.id
        FROM cards AS c
        WHERE COALESCE(NULLIF(c.odid, 0), c.did) IN ({placeholders})
          AND (
            (c.queue = 2 AND c.type = 2 AND COALESCE(NULLIF(c.odue, 0), c.due) >= ?
             AND COALESCE(NULLIF(c.odue, 0), c.due) <= ?)
            OR
            (c.queue = 1 AND COALESCE(NULLIF(c.odue, 0), c.due) >= ?
             AND COALESCE(NULLIF(c.odue, 0), c.due) <= ?)
            OR
            (c.queue = 3 AND COALESCE(NULLIF(c.odue, 0), c.due) >= ?
             AND COALESCE(NULLIF(c.odue, 0), c.due) <= ?)
            OR
            (? AND c.type = 0 AND c.queue = 0 AND c.id >= ? AND c.id < ?)
          )
        ORDER BY c.due, c.id
        """,
        *source_deck_ids,
        start_day,
        end_day,
        timestamp_start,
        timestamp_end - 1,
        start_day,
        end_day,
        1 if include_added_cards else 0,
        added_start,
        added_end,
    )
    return [int(row[0]) for row in rows]


def _classify(card_ids: list[int]) -> tuple[list[int], list[int]]:
    audio: list[int] = []
    visual: list[int] = []
    for card_id in card_ids:
        card = get_card(card_id)
        (visual if rendered_question_has_image(str(card.question() or "")) else audio).append(card_id)
    return audio, visual


def _external_filtered_assignments(card_ids: list[int]) -> dict[int, int]:
    if not card_ids:
        return {}
    target_ids = {
        deck_id
        for deck_id in (
            _stored_target_deck_id("audio"),
            _stored_target_deck_id("visual"),
            _stored_target_deck_id("combined"),
        )
        if deck_id
    }
    placeholders = ", ".join("?" for _ in card_ids)
    rows = mw.col.db.all(
        f"SELECT id, did FROM cards WHERE id IN ({placeholders}) AND odid != 0",
        *card_ids,
    )
    return {
        int(card_id): int(deck_id)
        for card_id, deck_id in rows
        if int(deck_id) not in target_ids
    }


def _build_one(kind: str, name: str, card_ids: list[int], assignments: dict[int, int]) -> int:
    deck_id = _stored_target_deck_id(kind)
    if deck_id is None:
        deck_id = create_or_update_filtered_deck(
            name,
            search=card_id_search(card_ids),
            limit=max(1, len(card_ids)),
            resched=True,
            order=FILTERED_DECK_ORDER_RANDOM,
        )
    else:
        _rename_target_deck(kind, deck_id, name)
        deck_id = create_or_update_filtered_deck(
            name,
            search=card_id_search(card_ids),
            limit=max(1, len(card_ids)),
            resched=True,
            order=FILTERED_DECK_ORDER_RANDOM,
        )
    setting = {
        "audio": AUDIO_DECK_ID_SETTING,
        "visual": VISUAL_DECK_ID_SETTING,
        "combined": COMBINED_DECK_ID_SETTING,
    }[kind]
    set_setting(setting, int(deck_id))
    relevant = {card_id: source_id for card_id, source_id in assignments.items() if card_id in set(card_ids)}
    if relevant:
        grouped: dict[int, list[int]] = {}
        for card_id, source_id in relevant.items():
            grouped.setdefault(source_id, []).append(card_id)
        register_restore_batch(
            target_deck_id=deck_id,
            target_deck_name=name,
            source_filtered_deck_ids=sorted(grouped),
            source_filtered_cards=grouped,
        )
    return deck_id


def build_due_day(kind: str, source_ids: list[int], selected_date: date) -> DueTodayResult:
    return build_due_day_range(kind, source_ids, selected_date, selected_date)


def build_due_day_range(
    kind: str,
    source_ids: list[int],
    start_date: date,
    end_date: date,
    *,
    include_added_cards: bool | None = None,
) -> DueTodayResult:
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if include_added_cards is None:
        include_added_cards = _include_added_cards_enabled()
    deck_names = _normal_decks()
    names = _target_names_for_range(start_date, end_date)
    normalized = normalize_deck_selection(source_ids, deck_names)
    set_setting(SOURCE_DECKS_SETTING, normalized)
    expanded = expand_deck_selection(normalized, deck_names)
    prior_assignments = _empty_target_decks(kind)
    card_ids = qualifying_card_ids_for_range(
        expanded,
        start_date,
        end_date,
        include_added_cards=include_added_cards,
    )
    audio_ids, visual_ids = _classify(card_ids)
    selected_ids = (
        audio_ids
        if kind == "audio"
        else visual_ids
        if kind == "visual"
        else audio_ids + visual_ids
    )
    assignments = _external_filtered_assignments(selected_ids)
    assignments.update(
        {
            card_id: source_id
            for card_id, source_id in prior_assignments.items()
            if card_id in set(selected_ids)
        }
    )
    if assignments:
        _remove_from_filtered(sorted(assignments))
    if kind in ("audio", "both"):
        _build_one("audio", names["audio"], audio_ids, assignments)
    if kind in ("visual", "both"):
        _build_one("visual", names["visual"], visual_ids, assignments)
    if kind == "combined":
        _build_one("combined", names["combined"], audio_ids + visual_ids, assignments)
    return DueTodayResult(audio_ids, visual_ids, len(assignments))


def _today_calendar_date() -> date:
    cutoff_date = datetime.fromtimestamp(_day_cutoff()).date()
    return cutoff_date - timedelta(days=1)


def _is_deck_browser_context(context: Any) -> bool:
    return context is getattr(mw, "deckBrowser", None) or getattr(context.__class__, "__name__", "") == "DeckBrowser"


def _button_html() -> str:
    return build_shared_deck_action_item(
        key="anki-pocket-knife:due-today",
        order=0,
        message=OPEN_MESSAGE,
        label="Create Due-Day Decks",
    )


def _on_deck_browser_will_render_content(deck_browser: Any, content: Any) -> None:
    del deck_browser
    button = _button_html()
    if isinstance(getattr(content, "tree", None), str):
        content.tree = inject_shared_deck_action_html(content.tree, button)
    elif isinstance(getattr(content, "stats", None), str):
        content.stats = inject_shared_deck_action_html(content.stats, button)


def _on_js_message(handled: tuple[bool, Any], message: str, context: Any) -> tuple[bool, Any]:
    if handled[0] or message != OPEN_MESSAGE or not _is_deck_browser_context(context):
        return handled
    open_due_today_dialog()
    return (True, None)


class DueTodayDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle("Create Due-Day Decks")
        self.resize(760, 650)
        self.deck_names = _normal_decks()
        self.today_date = _today_calendar_date()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        intro = QLabel(
            "Choose scheduling dates and source decks. Cards are included only in their exact stored due-day "
            "bucket, with still-new added cards optionally included by creation date. Suspended, buried, "
            "and already-reviewed added cards are excluded. Parent decks include their subdecks."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)
        date_row = QHBoxLayout()
        self.date_preset_buttons: dict[str, QPushButton] = {}
        for preset, label, days, end_days_ago in (
            ("today", "Today", 1, 0),
            ("yesterday", "Yesterday", 1, 1),
            ("last_3_days", "Last 3 Days", 3, 0),
            ("last_7_days", "Last 7 Days", 7, 0),
        ):
            button = QPushButton(label)
            button.setCheckable(True)
            button.clicked.connect(
                lambda _checked=False, preset=preset, day_count=days, end_offset=end_days_ago:
                self._select_preset(preset, day_count, end_offset)
            )
            self.date_preset_buttons[preset] = button
            date_row.addWidget(button)
        today_qdate = QDate(self.today_date.year, self.today_date.month, self.today_date.day)
        date_row.addWidget(QLabel("From"))
        self.start_picker = QDateEdit()
        self.start_picker.setCalendarPopup(True)
        self.start_picker.setMaximumDate(today_qdate)
        self.start_picker.setDate(today_qdate)
        date_row.addWidget(self.start_picker)
        date_row.addWidget(QLabel("To"))
        self.end_picker = QDateEdit()
        self.end_picker.setCalendarPopup(True)
        self.end_picker.setMaximumDate(today_qdate)
        self.end_picker.setDate(today_qdate)
        date_row.addWidget(self.end_picker)
        saved_preset = str(get_setting(DATE_PRESET_SETTING) or "today")
        if saved_preset not in self.date_preset_buttons:
            saved_preset = "today"
        self._select_preset(saved_preset, *(dict(
            today=(1, 0), yesterday=(1, 1), last_3_days=(3, 0), last_7_days=(7, 0)
        )[saved_preset]))
        layout.addLayout(date_row)
        self.summary = QLabel()
        layout.addWidget(self.summary)
        self.include_added_checkbox = QCheckBox("Include added cards")
        self.include_added_checkbox.setToolTip(
            "Include only still-new cards created during the selected date range, even if they are not due yet."
        )
        self.include_added_checkbox.setChecked(_include_added_cards_enabled())
        layout.addWidget(self.include_added_checkbox)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search decks...")
        layout.addWidget(self.search)
        self.deck_list = QListWidget()
        self.deck_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        selected = set(_selected_source_ids(self.deck_names))
        for deck_id, name in sorted(self.deck_names.items(), key=lambda item: item[1].casefold()):
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, deck_id)
            self.deck_list.addItem(item)
            item.setSelected(deck_id in selected)
        layout.addWidget(self.deck_list, 1)
        row = QHBoxLayout()
        self.audio_button = QPushButton("Build Audio")
        self.visual_button = QPushButton("Build Visual")
        self.both_button = QPushButton("Build Both")
        self.combined_button = QPushButton("Build Combined")
        self.combined_button.setDefault(True)
        self.previous_button = QPushButton("Previous Range")
        close_button = QPushButton("Close")
        for button in (self.audio_button, self.visual_button, self.both_button, self.combined_button):
            row.addWidget(button)
        row.addWidget(self.previous_button)
        row.addStretch(1)
        row.addWidget(close_button)
        layout.addLayout(row)
        self.search.textChanged.connect(self._filter)
        self.start_picker.dateChanged.connect(self._refresh_summary)
        self.end_picker.dateChanged.connect(self._refresh_summary)
        self.start_picker.dateChanged.connect(lambda *_args: self._clear_preset())
        self.end_picker.dateChanged.connect(lambda *_args: self._clear_preset())
        self.include_added_checkbox.stateChanged.connect(self._include_added_cards_changed)
        self.deck_list.itemSelectionChanged.connect(self._refresh_summary)
        self.audio_button.clicked.connect(lambda: self._build("audio"))
        self.visual_button.clicked.connect(lambda: self._build("visual"))
        self.both_button.clicked.connect(lambda: self._build("both"))
        self.combined_button.clicked.connect(lambda: self._build("combined"))
        self.previous_button.clicked.connect(self._previous_day)
        close_button.clicked.connect(self.close)
        self._refresh_summary()
        self._focus_selected_preset()

    def _selected_ids(self) -> list[int]:
        return [int(item.data(Qt.ItemDataRole.UserRole)) for item in self.deck_list.selectedItems()]

    def _qdate_to_date(self, value: QDate) -> date:
        return date(value.year(), value.month(), value.day())

    def _selected_start_date(self) -> date:
        return self._qdate_to_date(self.start_picker.date())

    def _selected_end_date(self) -> date:
        return self._qdate_to_date(self.end_picker.date())

    def _selected_range(self) -> tuple[date, date]:
        start_date = self._selected_start_date()
        end_date = self._selected_end_date()
        if start_date > end_date:
            return end_date, start_date
        return start_date, end_date

    def _set_days_ago(self, days_ago: int) -> None:
        selected = self.today_date - timedelta(days=max(0, int(days_ago)))
        selected_qdate = QDate(selected.year, selected.month, selected.day)
        self.start_picker.setDate(selected_qdate)
        self.end_picker.setDate(selected_qdate)

    def _set_recent_range(self, days: int, end_days_ago: int = 0) -> None:
        end_date = self.today_date - timedelta(days=max(0, int(end_days_ago)))
        start_date = end_date - timedelta(days=max(1, int(days)) - 1)
        self.start_picker.setDate(QDate(start_date.year, start_date.month, start_date.day))
        self.end_picker.setDate(QDate(end_date.year, end_date.month, end_date.day))

    def _clear_preset(self) -> None:
        if getattr(self, "_applying_preset", False) or not hasattr(self, "date_preset_buttons"):
            return
        if any(button.isChecked() for button in self.date_preset_buttons.values()):
            for button in self.date_preset_buttons.values():
                button.setChecked(False)
            set_setting(DATE_PRESET_SETTING, "today")

    def _select_preset(self, preset: str, days: int, end_days_ago: int = 0) -> None:
        self._applying_preset = True
        try:
            for name, button in self.date_preset_buttons.items():
                button.setChecked(name == preset)
            set_setting(DATE_PRESET_SETTING, preset)
            self._set_recent_range(days, end_days_ago)
        finally:
            self._applying_preset = False
        self._focus_selected_preset()

    def _focus_selected_preset(self) -> None:
        for button in self.date_preset_buttons.values():
            if button.isChecked():
                button.setFocus()
                return

    def _previous_day(self) -> None:
        start_date, end_date = self._selected_range()
        start_date -= timedelta(days=1)
        end_date -= timedelta(days=1)
        self.start_picker.setDate(QDate(start_date.year, start_date.month, start_date.day))
        self.end_picker.setDate(QDate(end_date.year, end_date.month, end_date.day))

    def _filter(self, text: str) -> None:
        terms = str(text or "").casefold().split()
        for row in range(self.deck_list.count()):
            item = self.deck_list.item(row)
            item.setHidden(not all(term in item.text().casefold() for term in terms))

    def _include_added_cards_changed(self, *_args: Any) -> None:
        set_setting(INCLUDE_ADDED_CARDS_SETTING, self.include_added_checkbox.isChecked())
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        normalized = normalize_deck_selection(self._selected_ids(), self.deck_names)
        expanded = expand_deck_selection(normalized, self.deck_names)
        start_date, end_date = self._selected_range()
        start_days_ago = days_ago_for_date(start_date, self.today_date)
        end_days_ago = days_ago_for_date(end_date, self.today_date)
        try:
            card_ids = qualifying_card_ids_for_range(
                expanded,
                start_date,
                end_date,
                include_added_cards=self.include_added_checkbox.isChecked(),
            )
            audio_ids, visual_ids = _classify(card_ids)
            label = deck_date_range_label(start_date, end_date, self.today_date)
            if start_date == end_date:
                age_label = f"{start_days_ago} day(s) ago"
            else:
                age_label = f"{min(start_days_ago, end_days_ago)}-{max(start_days_ago, end_days_ago)} day(s) ago"
            self.summary.setText(
                f"{label} ({age_label}): "
                f"{len(audio_ids)} audio, {len(visual_ids)} visual; "
                f"{len(normalized)} source selection(s); "
                f"added cards {'included' if self.include_added_checkbox.isChecked() else 'excluded'}."
            )
        except Exception:
            self.summary.setText(f"{len(normalized)} source selection(s).")
        enabled = bool(normalized)
        for button in (self.audio_button, self.visual_button, self.both_button, self.combined_button):
            button.setEnabled(enabled)

    def _build(self, kind: str) -> None:
        start_date, end_date = self._selected_range()
        include_added = self.include_added_checkbox.isChecked()
        set_setting(INCLUDE_ADDED_CARDS_SETTING, include_added)
        try:
            result = build_due_day_range(
                kind,
                self._selected_ids(),
                start_date,
                end_date,
                include_added_cards=include_added,
            )
        except Exception as exc:
            showWarning(f"Could not build Due Today decks.\n\n{exc}")
            return
        label = deck_date_range_label(start_date, end_date, self.today_date)
        showInfo(
            f"Due {label}: "
            f"{len(result.audio_ids)} audio and {len(result.visual_ids)} visual card(s)."
            + (f"\nMoved {result.moved_count} card(s) from other filtered decks." if result.moved_count else "")
        )
        self.close()


def open_due_today_dialog() -> None:
    global _dialog
    if _dialog is not None:
        _dialog.close()
    _dialog = DueTodayDialog()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    render_hook = getattr(gui_hooks, "deck_browser_will_render_content", None)
    message_hook = getattr(gui_hooks, "webview_did_receive_js_message", None)
    if render_hook is None or message_hook is None:
        return
    render_hook.append(_on_deck_browser_will_render_content)
    message_hook.append(_on_js_message)
    _HOOK_REGISTERED = True
