from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import json
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QTimer

from .common import rebuild_filtered_deck, user_files_dir


RESTORE_BATCHES_PATH = user_files_dir() / "no_image_restore_batches.json"
_HOOK_REGISTERED = False
_restore_timer: QTimer | None = None
_MAX_CARDS_PER_TERM = 250


def _load_batches() -> list[dict[str, Any]]:
    if not RESTORE_BATCHES_PATH.exists():
        return []
    try:
        data = json.loads(RESTORE_BATCHES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _save_batches(batches: list[dict[str, Any]]) -> None:
    RESTORE_BATCHES_PATH.write_text(json.dumps(batches, indent=2, sort_keys=True), encoding="utf-8")


def _deck_exists(deck_id: int) -> bool:
    try:
        deck = mw.col.decks.get(int(deck_id))
    except Exception:
        return False
    return bool(deck)


def _filtered_deck_exists(deck_id: int) -> bool:
    try:
        deck = mw.col.decks.get(int(deck_id))
    except Exception:
        return False
    return bool(deck and deck.get("dyn"))


def _clean_card_ids(raw_ids: Any) -> list[int]:
    if not isinstance(raw_ids, (list, tuple, set)):
        return []
    cleaned: list[int] = []
    seen: set[int] = set()
    for raw_id in raw_ids:
        try:
            card_id = int(raw_id)
        except Exception:
            continue
        if card_id <= 0 or card_id in seen:
            continue
        seen.add(card_id)
        cleaned.append(card_id)
    return cleaned


def _normalize_source_filtered_cards(raw_value: Any) -> dict[int, list[int]]:
    if not isinstance(raw_value, dict):
        return {}
    normalized: dict[int, list[int]] = {}
    for raw_deck_id, raw_card_ids in raw_value.items():
        try:
            deck_id = int(raw_deck_id)
        except Exception:
            continue
        if deck_id <= 0:
            continue
        card_ids = _clean_card_ids(raw_card_ids)
        normalized[deck_id] = card_ids
    return normalized


def _chunked(values: list[int], chunk_size: int) -> list[list[int]]:
    if chunk_size <= 0:
        return [values]
    return [values[index : index + chunk_size] for index in range(0, len(values), chunk_size)]


def _extra_terms_for_card_ids(existing_terms: Any, card_ids: list[int]) -> list[Any]:
    terms = deepcopy(existing_terms)
    if not isinstance(terms, list):
        terms = []

    use_dict_terms = bool(terms and isinstance(terms[0], dict))
    for chunk in _chunked(card_ids, _MAX_CARDS_PER_TERM):
        if not chunk:
            continue
        search = " or ".join(f"cid:{card_id}" for card_id in chunk)
        if use_dict_terms:
            terms.append({"search": search, "limit": len(chunk), "order": 0})
        else:
            terms.append([search, len(chunk), 0])
    return terms


def _restore_cards_to_filtered_deck(deck_id: int, card_ids: list[int]) -> bool:
    deck = mw.col.decks.get(int(deck_id))
    if not deck or not deck.get("dyn"):
        return False

    cleaned_card_ids = _clean_card_ids(card_ids)
    if not cleaned_card_ids:
        rebuild_filtered_deck(int(deck_id))
        return True

    original_terms = deepcopy(deck.get("terms"))
    temporary_terms = _extra_terms_for_card_ids(original_terms, cleaned_card_ids)

    try:
        deck["terms"] = temporary_terms
        mw.col.decks.save(deck)
        rebuild_filtered_deck(int(deck_id))
    finally:
        try:
            current_deck = mw.col.decks.get(int(deck_id)) or deck
            current_deck["terms"] = original_terms
            mw.col.decks.save(current_deck)
        except Exception:
            pass

    return True


def _deck_exists_by_name(deck_name: str) -> bool:
    finder = getattr(mw.col.decks, "id_for_name", None)
    if not callable(finder):
        return False
    try:
        deck_id = finder(str(deck_name))
    except Exception:
        return False
    if deck_id is None:
        return False
    try:
        return int(deck_id) > 0
    except Exception:
        return False


def _target_deck_still_exists(batch: dict[str, Any]) -> bool:
    target_deck_id = int(batch.get("target_deck_id", 0) or 0)
    if target_deck_id > 0 and _deck_exists(target_deck_id):
        return True
    target_deck_name = str(batch.get("target_deck_name", "") or "").strip()
    if target_deck_name and _deck_exists_by_name(target_deck_name):
        return True
    return False


def register_restore_batch(
    *,
    target_deck_id: int,
    target_deck_name: str,
    source_filtered_deck_ids: list[int],
    source_filtered_cards: dict[int, list[int]] | None = None,
) -> None:
    normalized_source_cards = _normalize_source_filtered_cards(source_filtered_cards or {})
    source_ids = [
        int(deck_id)
        for deck_id in dict.fromkeys(int(deck_id) for deck_id in source_filtered_deck_ids if int(deck_id) > 0)
    ]
    for deck_id in source_ids:
        normalized_source_cards.setdefault(int(deck_id), [])
    source_ids = sorted(normalized_source_cards.keys())
    if not source_ids:
        return

    batches = [
        batch
        for batch in _load_batches()
        if int(batch.get("target_deck_id", 0) or 0) != int(target_deck_id)
    ]
    batches.append(
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "source_filtered_cards": {
                str(deck_id): [int(card_id) for card_id in card_ids]
                for deck_id, card_ids in normalized_source_cards.items()
            },
            "source_filtered_deck_ids": source_ids,
            "target_deck_id": int(target_deck_id),
            "target_deck_name": str(target_deck_name),
        }
    )
    _save_batches(batches)
    _ensure_timer_running()


def exclude_restored_cards_for_target_deck(*, target_deck_id: int, card_ids: list[int]) -> None:
    excluded_ids = set(_clean_card_ids(card_ids))
    if not excluded_ids:
        return

    changed = False
    remaining_batches: list[dict[str, Any]] = []
    for batch in _load_batches():
        if int(batch.get("target_deck_id", 0) or 0) != int(target_deck_id):
            remaining_batches.append(batch)
            continue

        source_filtered_cards = _normalize_source_filtered_cards(batch.get("source_filtered_cards"))
        if not source_filtered_cards:
            remaining_batches.append(batch)
            continue

        pruned_cards: dict[int, list[int]] = {}
        for source_deck_id, source_card_ids in source_filtered_cards.items():
            kept_ids = [card_id for card_id in source_card_ids if card_id not in excluded_ids]
            if len(kept_ids) != len(source_card_ids):
                changed = True
            if kept_ids:
                pruned_cards[source_deck_id] = kept_ids

        if not pruned_cards:
            changed = True
            continue

        updated_batch = dict(batch)
        updated_batch["source_filtered_cards"] = {
            str(deck_id): [int(card_id) for card_id in card_ids]
            for deck_id, card_ids in pruned_cards.items()
        }
        updated_batch["source_filtered_deck_ids"] = sorted(pruned_cards.keys())
        remaining_batches.append(updated_batch)

    if not changed:
        return

    _save_batches(remaining_batches)
    if remaining_batches:
        _ensure_timer_running()
    else:
        _stop_timer()


def _restore_batch(batch: dict[str, Any]) -> None:
    restored_any = False
    source_filtered_cards = _normalize_source_filtered_cards(batch.get("source_filtered_cards"))
    if source_filtered_cards:
        for source_deck_id, card_ids in source_filtered_cards.items():
            if not _filtered_deck_exists(source_deck_id):
                continue
            try:
                if _restore_cards_to_filtered_deck(source_deck_id, card_ids):
                    restored_any = True
            except Exception:
                continue

    for deck_id in batch.get("source_filtered_deck_ids", []) or []:
        try:
            source_deck_id = int(deck_id)
        except Exception:
            continue
        if source_deck_id in source_filtered_cards:
            continue
        if not _filtered_deck_exists(source_deck_id):
            continue
        try:
            rebuild_filtered_deck(source_deck_id)
            restored_any = True
        except Exception:
            continue
    if restored_any:
        mw.reset()


def check_pending_restores() -> None:
    batches = _load_batches()
    if not batches:
        _stop_timer()
        return

    remaining: list[dict[str, Any]] = []
    for batch in batches:
        if _target_deck_still_exists(batch):
            remaining.append(batch)
            continue
        _restore_batch(batch)

    if remaining != batches:
        _save_batches(remaining)

    if not remaining:
        _stop_timer()


def _ensure_timer_running() -> None:
    global _restore_timer
    if _restore_timer is None:
        return
    if not _restore_timer.isActive():
        _restore_timer.start(2500)


def _stop_timer() -> None:
    if _restore_timer is not None and _restore_timer.isActive():
        _restore_timer.stop()


def _on_main_window_init() -> None:
    global _restore_timer
    if _restore_timer is None:
        _restore_timer = QTimer(mw)
        _restore_timer.setInterval(2500)
        _restore_timer.timeout.connect(check_pending_restores)
    check_pending_restores()
    if _load_batches():
        _ensure_timer_running()


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return
    gui_hooks.main_window_did_init.append(_on_main_window_init)
    _HOOK_REGISTERED = True
