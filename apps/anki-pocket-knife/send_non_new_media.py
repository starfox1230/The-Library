from __future__ import annotations

import re
import time
from typing import Any, Literal

from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu, QMessageBox
from aqt.utils import showInfo, showWarning


AUDIO_DECK_NAME = ".NEW::Audio"
VISUAL_DECK_NAME = ".NEW::Visual"
AUDIO_ACTION_LABEL = "Send Non-New Audio Cards To Main Audio Deck"
VISUAL_ACTION_LABEL = "Send Non-New Visual Cards To Main Visual Deck"
WINDOW_TITLE = "Send Non-New Media Cards"
_IMAGE_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
_HOOK_REGISTERED = False


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(int(count)))


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


def _deck_for_id(deck_id: int) -> dict[str, Any]:
    try:
        deck = mw.col.decks.get(int(deck_id), default=False)
    except TypeError:
        deck = mw.col.decks.get(int(deck_id))
    except Exception:
        deck = None
    return dict(deck or {})


def _deck_name(deck_id: int) -> str:
    deck = _deck_for_id(int(deck_id))
    name = deck.get("name")
    if name:
        return str(name)
    try:
        return str(mw.col.decks.name(int(deck_id)))
    except Exception:
        return f"Deck {int(deck_id)}"


def _deck_and_child_ids(deck_id: int) -> list[int]:
    getter = getattr(mw.col.decks, "deck_and_child_ids", None)
    if callable(getter):
        try:
            return [int(value) for value in getter(int(deck_id))]
        except Exception:
            pass
    return [int(deck_id)]


def _deck_id_for_exact_name(deck_name: str) -> int | None:
    manager = mw.col.decks

    by_name = getattr(manager, "by_name", None)
    if callable(by_name):
        try:
            deck = by_name(deck_name)
        except Exception:
            deck = None
        if isinstance(deck, dict) and deck.get("id") is not None and str(deck.get("name", "")) == deck_name:
            return int(deck["id"])

    finder = getattr(manager, "id_for_name", None)
    if callable(finder):
        try:
            deck_id = finder(deck_name)
        except Exception:
            deck_id = None
        if deck_id is not None:
            deck = _deck_for_id(int(deck_id))
            if deck and str(deck.get("name", "")) == deck_name:
                return int(deck_id)

    all_names_and_ids = getattr(manager, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        try:
            raw_items = list(all_names_and_ids() or [])
        except Exception:
            raw_items = []
        for item in raw_items:
            if isinstance(item, dict):
                raw_name = item.get("name")
                raw_id = item.get("id")
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                first, second = item[0], item[1]
                if isinstance(first, int):
                    raw_id, raw_name = first, second
                else:
                    raw_name, raw_id = first, second
            else:
                continue
            if raw_name == deck_name and raw_id is not None:
                return int(raw_id)

    return None


def _field_ord_for_model(model_id: int, field_name: str) -> int | None:
    try:
        model = mw.col.models.get(int(model_id)) or {}
    except Exception:
        model = {}

    wanted = field_name.casefold()
    for index, field in enumerate(model.get("flds", []) or []):
        if str(field.get("name", "")).casefold() == wanted:
            return int(field.get("ord", index))
    return None


def _text_field_html_for_note(model_id: int, fields: str) -> str:
    text_ord = _field_ord_for_model(int(model_id), "Text")
    if text_ord is None:
        return ""
    split_fields = str(fields or "").split("\x1f")
    if text_ord < 0 or text_ord >= len(split_fields):
        return ""
    return split_fields[text_ord]


def _candidate_rows(deck_id: int) -> list[tuple[int, int, int, int, int, str]]:
    deck_ids = [int(value) for value in _deck_and_child_ids(int(deck_id)) if int(value) > 0]
    if not deck_ids:
        return []
    sql = f"""
        SELECT c.id, c.did, c.type, c.queue, n.mid, n.flds
        FROM cards AS c
        JOIN notes AS n ON n.id = c.nid
        WHERE c.did IN ({_placeholders(len(deck_ids))})
          AND c.type != 0
        ORDER BY c.id ASC
    """
    rows = mw.col.db.all(sql, *deck_ids)
    return [
        (
            int(card_id),
            int(current_deck_id),
            int(card_type),
            int(card_queue),
            int(model_id),
            str(fields or ""),
        )
        for card_id, current_deck_id, card_type, card_queue, model_id, fields in rows
    ]


def _matching_card_ids(deck_id: int, kind: Literal["audio", "visual"], target_deck_id: int) -> tuple[list[int], int]:
    card_ids: list[int] = []
    candidate_count = 0
    for card_id, current_deck_id, _card_type, _card_queue, model_id, fields in _candidate_rows(int(deck_id)):
        text_html = _text_field_html_for_note(model_id=int(model_id), fields=fields)
        has_image = bool(_IMAGE_RE.search(text_html))
        if (kind == "visual" and has_image) or (kind == "audio" and not has_image):
            candidate_count += 1
            if int(current_deck_id) != int(target_deck_id):
                card_ids.append(int(card_id))
    return card_ids, candidate_count


def _move_cards_to_deck(card_ids: list[int], target_deck_id: int) -> int:
    unique_card_ids = [int(card_id) for card_id in dict.fromkeys(card_ids) if int(card_id) > 0]
    if not unique_card_ids:
        return 0

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
            SET did = ?,
                mod = ?,
                usn = ?
            WHERE id IN ({placeholders})
              AND type != 0
            """,
            int(target_deck_id),
            int(mod_value),
            int(usn_value),
            *chunk,
        )

    return len(unique_card_ids)


def send_non_new_media_cards(deck_id: int, kind: Literal["audio", "visual"], *, parent=None) -> bool:
    source_deck = _deck_for_id(int(deck_id))
    if not source_deck:
        showWarning("Could not load that deck.")
        return False
    if source_deck.get("dyn"):
        showWarning("This action only works from a normal deck.")
        return False

    target_name = AUDIO_DECK_NAME if kind == "audio" else VISUAL_DECK_NAME
    target_deck_id = _deck_id_for_exact_name(target_name)
    if target_deck_id is None:
        showWarning(f"Could not find the target deck '{target_name}'.")
        return False

    target_deck = _deck_for_id(int(target_deck_id))
    if not target_deck or target_deck.get("dyn"):
        showWarning(f"'{target_name}' is not available as a normal deck.")
        return False

    source_name = _deck_name(int(deck_id))
    card_ids, matching_count = _matching_card_ids(int(deck_id), kind, int(target_deck_id))
    label = "audio" if kind == "audio" else "visual"
    if not matching_count:
        QMessageBox.information(
            parent or mw,
            WINDOW_TITLE,
            f"No non-new {label} cards were found in '{source_name}' or its subdecks.",
        )
        return False

    if not card_ids:
        QMessageBox.information(
            parent or mw,
            WINDOW_TITLE,
            f"All {matching_count} non-new {label} card(s) from '{source_name}' are already in '{target_name}'.",
        )
        return False

    decision = QMessageBox.question(
        parent or mw,
        WINDOW_TITLE,
        (
            f"Move {len(card_ids)} non-new {label} card(s) from '{source_name}' and its subdecks "
            f"to '{target_name}'?\n\n"
            "New cards will be left where they are."
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if decision != QMessageBox.StandardButton.Yes:
        return False

    try:
        moved_count = _move_cards_to_deck(card_ids, int(target_deck_id))
    except Exception as exc:
        showWarning(f"Could not move non-new {label} cards to '{target_name}'.\n\n{exc}")
        return False

    mw.reset()
    showInfo(f"Moved {moved_count} non-new {label} card(s) from '{source_name}' to '{target_name}'.")
    return True


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    deck = _deck_for_id(int(deck_id))
    if not deck or deck.get("dyn"):
        return

    if menu.actions():
        menu.addSeparator()

    audio_action = QAction(AUDIO_ACTION_LABEL, menu)
    audio_action.triggered.connect(
        lambda *_args, did=int(deck_id): send_non_new_media_cards(did, "audio")
    )
    menu.addAction(audio_action)

    visual_action = QAction(VISUAL_ACTION_LABEL, menu)
    visual_action.triggered.connect(
        lambda *_args, did=int(deck_id): send_non_new_media_cards(did, "visual")
    )
    menu.addAction(visual_action)


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
