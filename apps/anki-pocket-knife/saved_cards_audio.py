from __future__ import annotations

from datetime import datetime
import time
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu, QMessageBox
from aqt.utils import showInfo, showWarning

from .common import create_or_update_filtered_deck


SOURCE_DECK_NAME = "Saved Cards"
TARGET_DECK_NAME = ".NEW::Audio"
FILTERED_DECK_NAME_TEMPLATE = "New cards from Saved Cards Deck (%Y-%m-%d %H-%M-%S)"
GEAR_ACTION_LABEL = "Send Saved Cards To .NEW::Audio + Build New Deck"
WINDOW_TITLE = "Saved Cards To Audio"
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


def _deck_for_id(deck_id: int) -> dict[str, Any] | None:
    try:
        deck = mw.col.decks.get(int(deck_id)) or {}
    except Exception:
        return None
    return deck if isinstance(deck, dict) and deck else None


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


def _has_child_decks(deck_name: str, *, excluding_deck_id: int) -> bool:
    prefix = f"{deck_name}::"
    manager = mw.col.decks
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
            raw_items = list(fallback.values()) if isinstance(fallback, dict) else list(fallback or [])

    for item in raw_items:
        raw_id = None
        raw_name = None
        if isinstance(item, dict):
            raw_id = item.get("id")
            raw_name = item.get("name")
        elif isinstance(item, (tuple, list)) and len(item) >= 2:
            first, second = item[0], item[1]
            if isinstance(first, int):
                raw_id, raw_name = first, second
            else:
                raw_name, raw_id = first, second
        if raw_id is None or not raw_name:
            continue
        if int(raw_id) == int(excluding_deck_id):
            continue
        if str(raw_name).startswith(prefix):
            return True
    return False


def _cards_in_exact_deck(deck_id: int) -> list[tuple[int, int]]:
    rows = mw.col.db.all(
        """
        SELECT c.id, c.type
        FROM cards AS c
        WHERE c.did = ?
        ORDER BY c.id ASC
        """,
        int(deck_id),
    )
    return [(int(card_id), int(card_type)) for card_id, card_type in rows]


def _deck_card_count(deck_id: int) -> int:
    row = mw.col.db.first(
        """
        SELECT COUNT(*)
        FROM cards AS c
        WHERE c.did = ?
        """,
        int(deck_id),
    )
    if not row:
        return 0
    return int(row[0] or 0)


def _move_cards_to_deck(card_ids: list[int], *, source_deck_id: int, target_deck_id: int) -> int:
    unique_card_ids = [int(card_id) for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)]
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
              AND did = ?
            """,
            int(target_deck_id),
            int(mod_value),
            int(usn_value),
            *chunk,
            int(source_deck_id),
        )

    return len(unique_card_ids)


def _delete_empty_deck(deck_id: int) -> None:
    if _deck_card_count(int(deck_id)) != 0:
        raise RuntimeError("The Saved Cards deck is not empty, so it could not be deleted.")

    manager = mw.col.decks
    remove = getattr(manager, "remove", None)
    removal_errors: list[str] = []

    if callable(remove):
        for args in (([int(deck_id)],), (int(deck_id),)):
            try:
                remove(*args)
                return
            except TypeError:
                continue
            except Exception as exc:
                removal_errors.append(str(exc))

    rem = getattr(manager, "rem", None)
    if callable(rem):
        attempts = [
            (([int(deck_id)],), {"cardsToo": False, "childrenToo": False}),
            ((int(deck_id),), {"cardsToo": False, "childrenToo": False}),
            (([int(deck_id)],), {}),
            ((int(deck_id),), {}),
        ]
        for args, kwargs in attempts:
            try:
                rem(*args, **kwargs)
                return
            except TypeError:
                continue
            except Exception as exc:
                removal_errors.append(str(exc))

    deck = _deck_for_id(int(deck_id))
    if deck is None:
        return

    details = "\n".join(error for error in removal_errors if error)
    raise RuntimeError(details or "This version of Anki could not delete the empty Saved Cards deck.")


def _build_confirmation_message(*, total_count: int, new_count: int, source_name: str, target_name: str) -> str:
    other_count = int(total_count) - int(new_count)
    if new_count:
        filtered_note = (
            f"A new filtered deck will then be created from the {new_count} still-new card(s) that were moved."
        )
    else:
        filtered_note = "No still-new cards were found, so no filtered deck will be created."
    return (
        f"Move all {total_count} card(s) from '{source_name}' to '{target_name}'?\n\n"
        f"Still-new cards: {new_count}\n"
        f"Already reviewed or in learning: {other_count}\n\n"
        f"{filtered_note}\n"
        f"After that, Pocket Knife will delete the now-empty '{source_name}' deck."
    )


def send_saved_cards_to_audio(deck_id: int, *, parent=None) -> bool:
    source_deck = _deck_for_id(int(deck_id))
    if not source_deck:
        showWarning("Could not load that deck.")
        return False
    if source_deck.get("dyn"):
        showWarning("This Saved Cards action only works on a normal deck.")
        return False

    source_name = str(source_deck.get("name", ""))
    if source_name != SOURCE_DECK_NAME:
        showWarning(f"This action only appears for the exact '{SOURCE_DECK_NAME}' deck.")
        return False

    if _has_child_decks(source_name, excluding_deck_id=int(deck_id)):
        showWarning(
            f"'{SOURCE_DECK_NAME}' currently has subdecks.\n\n"
            "This action is limited to the exact Saved Cards deck so it does not accidentally delete child decks."
        )
        return False

    target_deck_id = _deck_id_for_exact_name(TARGET_DECK_NAME)
    if target_deck_id is None:
        showWarning(f"Could not find the target deck '{TARGET_DECK_NAME}'.")
        return False

    target_deck = _deck_for_id(int(target_deck_id))
    if not target_deck or target_deck.get("dyn"):
        showWarning(f"'{TARGET_DECK_NAME}' is not available as a normal deck.")
        return False

    card_rows = _cards_in_exact_deck(int(deck_id))
    if not card_rows:
        QMessageBox.information(
            parent or mw,
            WINDOW_TITLE,
            f"'{SOURCE_DECK_NAME}' is already empty, so there is nothing to move.",
        )
        return False

    all_card_ids = [int(card_id) for card_id, _card_type in card_rows]
    new_card_ids = [int(card_id) for card_id, card_type in card_rows if int(card_type) == 0]

    decision = QMessageBox.question(
        parent or mw,
        WINDOW_TITLE,
        _build_confirmation_message(
            total_count=len(all_card_ids),
            new_count=len(new_card_ids),
            source_name=SOURCE_DECK_NAME,
            target_name=TARGET_DECK_NAME,
        ),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.Yes,
    )
    if decision != QMessageBox.StandardButton.Yes:
        return False

    try:
        _move_cards_to_deck(
            all_card_ids,
            source_deck_id=int(deck_id),
            target_deck_id=int(target_deck_id),
        )
    except Exception as exc:
        showWarning(f"Could not move cards from '{SOURCE_DECK_NAME}' to '{TARGET_DECK_NAME}'.\n\n{exc}")
        return False

    filtered_deck_name: str | None = None
    filtered_error: Exception | None = None
    if new_card_ids:
        filtered_deck_name = datetime.now().strftime(FILTERED_DECK_NAME_TEMPLATE)
        search = " or ".join(f"cid:{card_id}" for card_id in new_card_ids)
        try:
            create_or_update_filtered_deck(
                filtered_deck_name,
                search=search,
                limit=len(new_card_ids),
                resched=True,
            )
        except Exception as exc:
            filtered_error = exc
            filtered_deck_name = None

    delete_error: Exception | None = None
    try:
        _delete_empty_deck(int(deck_id))
    except Exception as exc:
        delete_error = exc

    mw.reset()

    if filtered_error or delete_error:
        parts = [
            f"Moved {len(all_card_ids)} card(s) from '{SOURCE_DECK_NAME}' to '{TARGET_DECK_NAME}'.",
        ]
        if new_card_ids:
            if filtered_error is None and filtered_deck_name is not None:
                parts.append(
                    f"Created '{filtered_deck_name}' with {len(new_card_ids)} still-new card(s)."
                )
            else:
                parts.append(
                    "The cards were moved, but Pocket Knife could not create the new filtered deck "
                    f"for the {len(new_card_ids)} still-new card(s):\n{filtered_error}"
                )
        else:
            parts.append("There were no still-new cards to place into a filtered deck.")
        if delete_error is None:
            parts.append(f"Deleted the now-empty '{SOURCE_DECK_NAME}' deck.")
        else:
            parts.append(
                f"Pocket Knife could not delete the now-empty '{SOURCE_DECK_NAME}' deck:\n{delete_error}"
            )
        showWarning("\n\n".join(parts))
        return False

    if filtered_deck_name is not None:
        showInfo(
            f"Moved {len(all_card_ids)} card(s) from '{SOURCE_DECK_NAME}' to '{TARGET_DECK_NAME}', "
            f"created '{filtered_deck_name}' with {len(new_card_ids)} still-new card(s), "
            f"and deleted the empty '{SOURCE_DECK_NAME}' deck."
        )
    else:
        showInfo(
            f"Moved {len(all_card_ids)} card(s) from '{SOURCE_DECK_NAME}' to '{TARGET_DECK_NAME}'. "
            f"There were no still-new cards to place into a filtered deck, and the empty '{SOURCE_DECK_NAME}' deck was deleted."
        )
    return True


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    deck = _deck_for_id(int(deck_id))
    if not deck or deck.get("dyn") or str(deck.get("name", "")) != SOURCE_DECK_NAME:
        return

    if menu.actions():
        menu.addSeparator()

    action = QAction(GEAR_ACTION_LABEL, menu)
    action.triggered.connect(lambda *_args, did=int(deck_id): send_saved_cards_to_audio(did))
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
