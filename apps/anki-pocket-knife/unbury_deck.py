from __future__ import annotations

from typing import Any

from aqt import gui_hooks, mw
from aqt.operations.scheduling import unbury_cards
from aqt.qt import QAction, QMenu
from aqt.utils import showInfo, showWarning, tooltip


GEAR_ACTION_LABEL = "Unbury Buried Cards In This Deck"
_HOOK_REGISTERED = False


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


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(max(0, int(count))))


def _buried_card_ids_for_deck(deck_id: int) -> list[int]:
    deck_ids = [int(value) for value in _deck_and_child_ids(int(deck_id)) if int(value) > 0]
    if not deck_ids:
        return []

    sql = f"""
        SELECT c.id
        FROM cards AS c
        WHERE c.did IN ({_placeholders(len(deck_ids))})
          AND c.queue IN (-3, -2)
        ORDER BY c.id
    """
    db = mw.col.db
    list_method = getattr(db, "list", None)
    if callable(list_method):
        try:
            return [int(value) for value in list_method(sql, *deck_ids)]
        except Exception:
            pass

    rows = db.all(sql, *deck_ids)
    return [int(row[0]) for row in rows or []]


def unbury_buried_cards_for_deck(deck_id: int) -> bool:
    if getattr(mw, "col", None) is None:
        return False

    safe_deck_id = int(deck_id)
    deck_name = _deck_name(safe_deck_id)
    card_ids = _buried_card_ids_for_deck(safe_deck_id)
    if not card_ids:
        showInfo(f"No buried cards were found in '{deck_name}'.")
        return False

    operation = unbury_cards(parent=mw, card_ids=card_ids)
    operation.success(
        lambda _changes, name=deck_name, count=len(card_ids): tooltip(
            f"Unburied {count} card(s) in '{name}'.",
            parent=mw,
        )
    ).run_in_background()
    return True


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    deck = _deck_for_id(int(deck_id))
    if not deck:
        return

    if menu.actions():
        menu.addSeparator()

    action = QAction(GEAR_ACTION_LABEL, menu)
    action.triggered.connect(
        lambda *_args, did=int(deck_id): unbury_buried_cards_for_deck(did)
    )
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
        showWarning("Could not register the Pocket Knife unbury-deck action.")
        return

    addHook("showDeckOptions", _maybe_add_deck_browser_action)
    _HOOK_REGISTERED = True
