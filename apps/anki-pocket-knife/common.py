from __future__ import annotations

from pathlib import Path
from typing import Any

from aqt import mw


def addon_root() -> Path:
    return Path(__file__).resolve().parent


def user_files_dir() -> Path:
    path = addon_root() / "user_files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def collection_media_dir() -> Path:
    media = getattr(mw.col, "media", None)
    if media is None:
        raise RuntimeError("Collection media is not available.")

    for method_name in ("dir", "dir_path"):
        method = getattr(media, method_name, None)
        if callable(method):
            path = method()
            if path:
                return Path(str(path))

    path = getattr(media, "dir", None)
    if path:
        return Path(str(path))

    raise RuntimeError("Could not determine the collection media folder.")


def get_card(card_id: int) -> Any:
    getter = getattr(mw.col, "get_card", None)
    if callable(getter):
        return getter(int(card_id))

    getter = getattr(mw.col, "getCard", None)
    if callable(getter):
        return getter(int(card_id))

    raise RuntimeError("Unable to load card from the collection.")


def note_fields(note: Any) -> dict[str, str]:
    try:
        return {str(name): str(value) for name, value in note.items()}
    except Exception:
        fields = getattr(note, "fields", [])
        return {f"Field {index + 1}": str(value) for index, value in enumerate(fields)}


def note_type_name(note: Any) -> str:
    for attr in ("note_type", "notetype", "model"):
        method = getattr(note, attr, None)
        if not callable(method):
            continue
        try:
            info = method()
        except Exception:
            continue
        if isinstance(info, dict):
            return str(info.get("name", "Unknown Note Type"))
    return "Unknown Note Type"


def note_tags(note: Any) -> list[str]:
    return [str(tag) for tag in getattr(note, "tags", [])]


def deck_name(card: Any) -> str:
    did = getattr(card, "odid", 0) or getattr(card, "did", 0)
    try:
        return str(mw.col.decks.name(int(did)))
    except Exception:
        return "Unknown Deck"


def set_filtered_terms(deck: dict[str, Any], search: str, limit: int) -> None:
    terms = deck.get("terms")
    if isinstance(terms, list) and terms and isinstance(terms[0], dict):
        deck["terms"] = [{"search": search, "limit": int(limit), "order": 0}]
        return

    deck["terms"] = [[search, int(limit), 0]]


def rebuild_filtered_deck(deck_id: int) -> None:
    scheduler = mw.col.sched

    rebuild = getattr(scheduler, "rebuild_filtered_deck", None)
    if callable(rebuild):
        rebuild(int(deck_id))
        return

    rebuild = getattr(scheduler, "rebuildDyn", None)
    if callable(rebuild):
        rebuild(int(deck_id))
        return

    raise RuntimeError("This version of Anki cannot rebuild filtered decks.")


def _filtered_deck_id_for_name(deck_name: str) -> int | None:
    finder = getattr(mw.col.decks, "id_for_name", None)
    if callable(finder):
        try:
            deck_id = finder(deck_name)
        except Exception:
            deck_id = None
        if deck_id is not None:
            return int(deck_id)

    return None


def _new_filtered_deck_id(deck_name: str) -> int:
    creator = getattr(mw.col.decks, "new_filtered", None)
    if callable(creator):
        deck_id = creator(deck_name)
        if deck_id is not None:
            return int(deck_id)

    creator = getattr(mw.col.decks, "newDyn", None)
    if callable(creator):
        deck_id = creator(deck_name)
        if deck_id is not None:
            return int(deck_id)

    raise RuntimeError("This version of Anki cannot create filtered decks.")


def create_or_update_filtered_deck(
    deck_name: str,
    *,
    search: str,
    limit: int,
    resched: bool,
) -> int:
    deck_id = _filtered_deck_id_for_name(deck_name)
    if deck_id is None:
        deck_id = _new_filtered_deck_id(deck_name)

    deck = mw.col.decks.get(int(deck_id))
    if not deck:
        raise RuntimeError(f"Could not load filtered deck '{deck_name}'.")

    if not deck.get("dyn"):
        raise RuntimeError(
            f"'{deck_name}' already exists as a normal deck. Rename or remove it, then try again."
        )

    deck["dyn"] = 1
    deck["resched"] = bool(resched)
    deck["delays"] = None
    set_filtered_terms(deck, search, limit)
    mw.col.decks.save(deck)
    rebuild_filtered_deck(int(deck_id))
    mw.reset()
    return int(deck_id)
