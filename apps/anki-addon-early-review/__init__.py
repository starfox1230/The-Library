from __future__ import annotations

from datetime import datetime, timedelta

from aqt import gui_hooks, mw
from aqt.qt import QAction
from aqt.utils import getText, showInfo, showWarning

ADDON_NAME = "Early Review Deck"
SHORTCUT = "Ctrl+Alt+F"
DEFAULT_COUNT = 50
DECK_NAME_PREFIX = "............... Early Preview Deck for "
_ACTION_FLAG = "_early_review_deck_action_registered"


def _prompt_count(default_count: int = DEFAULT_COUNT) -> int | None:
    response, accepted = getText(
        "How many cards due tomorrow should be pulled?",
        default=str(default_count),
        title=ADDON_NAME,
    )
    if not accepted:
        return None

    value = (response or "").strip()
    if not value:
        return default_count

    try:
        parsed = int(value)
    except ValueError:
        showWarning("Please enter a whole number.")
        return None

    if parsed <= 0:
        showWarning("Please enter a number greater than 0.")
        return None

    return parsed


def _tomorrow_due_number() -> int:
    return int(mw.col.sched.today) + 1


def _tomorrow_iso_date() -> str:
    return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")


def _fetch_due_tomorrow_card_ids(limit: int) -> list[int]:
    due_tomorrow = _tomorrow_due_number()
    rows = mw.col.db.all(
        """
        SELECT c.id
        FROM cards AS c
        WHERE c.queue IN (2, 3)
          AND c.type = 2
          AND c.due = ?
        ORDER BY c.ivl DESC, c.id ASC
        LIMIT ?
        """,
        due_tomorrow,
        limit,
    )
    return [int(row[0]) for row in rows]


def _set_filtered_terms(deck: dict, search: str, limit: int) -> None:
    terms = deck.get("terms")
    if isinstance(terms, list) and terms and isinstance(terms[0], dict):
        deck["terms"] = [{"search": search, "limit": limit, "order": 0}]
        return

    deck["terms"] = [[search, limit, 0]]


def _rebuild_filtered_deck(deck_id: int) -> None:
    scheduler = mw.col.sched

    if hasattr(scheduler, "rebuild_filtered_deck"):
        scheduler.rebuild_filtered_deck(deck_id)
        return

    if hasattr(scheduler, "rebuildDyn"):
        scheduler.rebuildDyn(deck_id)


def build_early_review_filtered_deck() -> None:
    if mw.col is None:
        return

    limit = _prompt_count()
    if limit is None:
        return

    card_ids = _fetch_due_tomorrow_card_ids(limit)
    if not card_ids:
        showInfo("No review cards are due tomorrow.")
        return

    deck_name = f"{DECK_NAME_PREFIX}{_tomorrow_iso_date()}"
    deck_id = mw.col.decks.id_for_name(deck_name)

    if deck_id is None:
        deck_id = mw.col.decks.new_filtered(deck_name)

    deck = mw.col.decks.get(deck_id)
    if not deck:
        showWarning(f"Could not create or load '{deck_name}'.")
        return

    if not deck.get("dyn"):
        showWarning(
            f"'{deck_name}' already exists as a normal deck. Rename or remove it, then try again."
        )
        return

    cid_search = " or ".join(f"cid:{card_id}" for card_id in card_ids)
    _set_filtered_terms(deck, cid_search, len(card_ids))
    deck["resched"] = True
    mw.col.decks.save(deck)

    _rebuild_filtered_deck(deck_id)
    mw.col.reset()

    showInfo(f"Built '{deck_name}' with {len(card_ids)} cards.")


def _register_menu_action() -> None:
    if getattr(mw, _ACTION_FLAG, False):
        return

    action = QAction("Build Early Review Deck", mw)
    action.setShortcut(SHORTCUT)
    action.triggered.connect(build_early_review_filtered_deck)
    mw.form.menuTools.addAction(action)

    setattr(mw, _ACTION_FLAG, True)


gui_hooks.main_window_did_init.append(_register_menu_action)
