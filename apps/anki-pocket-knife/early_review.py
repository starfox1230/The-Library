from __future__ import annotations

from datetime import datetime, timedelta

from aqt import mw
from aqt.utils import getText, showInfo, showWarning

from .common import card_id_search, create_or_update_filtered_deck


EARLY_REVIEW_SHORTCUT = "Ctrl+Alt+F"
EARLY_REVIEW_DEFAULT_COUNT = 50
EARLY_REVIEW_DECK_NAME_PREFIX = "............... Early Preview Deck for "


def prompt_early_review_count(default_count: int = EARLY_REVIEW_DEFAULT_COUNT) -> int | None:
    response, accepted = getText(
        "How many cards due tomorrow should be pulled?",
        default=str(int(default_count)),
        title="Build Early Review Deck",
    )
    if not accepted:
        return None

    value = (response or "").strip()
    if not value:
        return int(default_count)

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


def fetch_due_tomorrow_card_ids(limit: int) -> list[int]:
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
        _tomorrow_due_number(),
        int(limit),
    )
    return [int(row[0]) for row in rows]


def build_early_review_filtered_deck(
    limit: int | None = None,
    *,
    prompt_if_missing: bool = True,
) -> bool:
    if mw.col is None:
        return False

    if limit is None:
        if not prompt_if_missing:
            limit = int(EARLY_REVIEW_DEFAULT_COUNT)
        else:
            limit = prompt_early_review_count()
            if limit is None:
                return False

    card_ids = fetch_due_tomorrow_card_ids(int(limit))
    if not card_ids:
        showInfo("No review cards are due tomorrow.")
        return False

    deck_name = f"{EARLY_REVIEW_DECK_NAME_PREFIX}{_tomorrow_iso_date()}"
    search = card_id_search(card_ids)

    try:
        create_or_update_filtered_deck(
            deck_name,
            search=search,
            limit=len(card_ids),
            resched=True,
        )
    except Exception as exc:
        showWarning(f"Could not build the early review deck.\n\n{exc}")
        return False

    showInfo(f"Built '{deck_name}' with {len(card_ids)} cards.")
    return True
