from __future__ import annotations

from html import escape
from pathlib import Path
import re
from typing import Any

from aqt import mw


def addon_root() -> Path:
    return Path(__file__).resolve().parent


SHARED_DECK_ACTIONS_STYLE_ID = "anki-shared-deck-actions-style"
SHARED_DECK_ACTIONS_CONTAINER_START = "<!--anki-shared-deck-actions:start-->"
SHARED_DECK_ACTIONS_CONTAINER_END = "<!--anki-shared-deck-actions:end-->"
SHARED_DECK_ACTIONS_CONTAINER_OPEN = '<div id="anki-shared-deck-actions-row" class="anki-shared-deck-actions-row">'
SHARED_DECK_ACTIONS_CONTAINER_CLOSE = "</div>"
SHARED_DECK_ACTIONS_STYLE = f"""
<style id="{SHARED_DECK_ACTIONS_STYLE_ID}">
  #anki-shared-deck-actions-row {{
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    align-items: center;
    gap: 10px;
    margin: 0 0 14px 0;
  }}

  .anki-shared-deck-action-slot {{
    display: flex;
    align-items: center;
    justify-content: center;
  }}

  .anki-shared-deck-action-button {{
    appearance: none;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    min-height: 38px;
    padding: 8px 14px;
    border-radius: 999px;
    border: 1px solid rgba(0, 0, 0, 0.14);
    background: var(--canvas, #ffffff);
    color: inherit;
    font: 600 13px/1.2 "Segoe UI", system-ui, sans-serif;
    text-align: center;
    white-space: nowrap;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  }}

  .anki-shared-deck-action-button:hover {{
    background: rgba(127, 127, 127, 0.08);
  }}
</style>
""".strip()
_SHARED_DECK_ACTION_BLOCK_RE = re.compile(
    r"<!--anki-shared-deck-action:(?P<key>.+?):start-->(?P<block>.*?)<!--anki-shared-deck-action:(?P=key):end-->",
    re.DOTALL,
)
_SHARED_DECK_ACTION_CONTAINER_RE = re.compile(
    re.escape(SHARED_DECK_ACTIONS_CONTAINER_START)
    + r"(?P<body>.*?)"
    + re.escape(SHARED_DECK_ACTIONS_CONTAINER_END),
    re.DOTALL,
)
_SHARED_DECK_ACTION_ORDER_RE = re.compile(r'data-anki-deck-action-order="(?P<order>-?\d+)"')


def user_files_dir() -> Path:
    path = addon_root() / "user_files"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_shared_deck_action_item(*, key: str, order: int, message: str, label: str) -> str:
    safe_message = str(message).replace("\\", "\\\\").replace("'", "\\'")
    return (
        f"<!--anki-shared-deck-action:{key}:start-->"
        f'<div class="anki-shared-deck-action-slot" data-anki-deck-action-order="{int(order)}" '
        f'data-anki-deck-action-key="{escape(str(key), quote=True)}">'
        f'<button type="button" class="anki-shared-deck-action-button" '
        f'onclick="pycmd(\'{safe_message}\'); return false;">{escape(str(label))}</button>'
        f"</div>"
        f"<!--anki-shared-deck-action:{key}:end-->"
    )


def _shared_deck_action_order(item_html: str) -> int:
    match = _SHARED_DECK_ACTION_ORDER_RE.search(str(item_html))
    if match is None:
        return 0
    try:
        return int(match.group("order"))
    except Exception:
        return 0


def inject_shared_deck_action_html(content_html: str, item_html: str) -> str:
    html = str(content_html or "")
    prefix = "" if SHARED_DECK_ACTIONS_STYLE_ID in html else f"{SHARED_DECK_ACTIONS_STYLE}\n"
    match = _SHARED_DECK_ACTION_CONTAINER_RE.search(html)
    if match is None:
        container_html = (
            f"{SHARED_DECK_ACTIONS_CONTAINER_START}"
            f"{SHARED_DECK_ACTIONS_CONTAINER_OPEN}{item_html}{SHARED_DECK_ACTIONS_CONTAINER_CLOSE}"
            f"{SHARED_DECK_ACTIONS_CONTAINER_END}"
        )
        return f"{prefix}{container_html}{html}"

    existing_items = [entry.group(0) for entry in _SHARED_DECK_ACTION_BLOCK_RE.finditer(match.group("body"))]
    existing_items.append(str(item_html))
    existing_items.sort(key=_shared_deck_action_order)
    container_html = (
        f"{SHARED_DECK_ACTIONS_CONTAINER_START}"
        f"{SHARED_DECK_ACTIONS_CONTAINER_OPEN}{''.join(existing_items)}{SHARED_DECK_ACTIONS_CONTAINER_CLOSE}"
        f"{SHARED_DECK_ACTIONS_CONTAINER_END}"
    )
    return f"{prefix}{html[:match.start()]}{container_html}{html[match.end():]}"


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


def card_id_search(card_ids: list[int], *, exclude_suspended: bool = True) -> str:
    cleaned_ids: list[int] = []
    seen: set[int] = set()
    for raw_card_id in card_ids:
        try:
            card_id = int(raw_card_id)
        except Exception:
            continue
        if card_id <= 0 or card_id in seen:
            continue
        seen.add(card_id)
        cleaned_ids.append(card_id)

    if not cleaned_ids:
        search = "cid:0"
    else:
        search = " or ".join(f"cid:{card_id}" for card_id in cleaned_ids)

    if exclude_suspended:
        return f"({search}) -is:suspended"
    return search


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
