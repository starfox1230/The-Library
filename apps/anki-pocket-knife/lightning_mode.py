from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
import sys
import time
from typing import Any

from aqt import gui_hooks, mw
from aqt.qt import QAction, QMenu, QTimer
from aqt.utils import showInfo, showWarning

from .common import create_or_update_filtered_deck, get_card, rebuild_filtered_deck
from .settings import get_setting, set_setting


LIGHTNING_MODE_DECK_NAME_PREFIX = "Lightning mode "
GEAR_ACTION_LABEL = "Build Lightning Mode Deck"
LIGHTNING_MODE_CARD_LIMIT_SETTING = "lightning_mode_card_limit"
LIGHTNING_MODE_QUESTION_SECONDS_SETTING = "lightning_mode_question_seconds"
LIGHTNING_MODE_ANSWER_SECONDS_SETTING = "lightning_mode_answer_seconds"
FILTERED_LIGHTNING_SESSIONS_CONFIG_KEY = "anki_pocket_knife_lightning_sessions"
QUESTION_ACTION_SHOW_ANSWER = 0
ANSWER_ACTION_BURY_CARD = 0
LIGHTNING_MODE_PAUSE_SHORTCUT = "P"
_HOOK_REGISTERED = False
_MAX_CARDS_PER_TERM = 250
_SESSION_TIMER_INTERVAL_MS = 2500


@dataclass(frozen=True)
class CardCandidate:
    card_id: int
    current_deck_id: int
    original_deck_id: int

    @property
    def in_filtered_deck(self) -> bool:
        return int(self.original_deck_id) > 0


@dataclass(frozen=True)
class SpeedStreakTimerOverride:
    module_name: str
    question_seconds: float
    answer_seconds: float


@dataclass(frozen=True)
class LightningTimerPauseState:
    card_id: int
    reviewer_state: str
    remaining_ms: int


_speed_streak_override: SpeedStreakTimerOverride | None = None
_original_config_dict_for_deck_id: Any = None
_deck_config_patch_installed = False
_reviewer_timeout_patch_installed = False
_filtered_lightning_session_timer: QTimer | None = None
_pending_lightning_answer_targets: dict[int, int] = {}
_lightning_timer_pause_state: LightningTimerPauseState | None = None


def lightning_card_limit() -> int:
    try:
        raw_value = int(get_setting(LIGHTNING_MODE_CARD_LIMIT_SETTING))
    except Exception:
        raw_value = 100
    return max(1, min(1000, raw_value))


def set_lightning_card_limit(value: int) -> int:
    safe_value = max(1, min(1000, int(value)))
    set_setting(LIGHTNING_MODE_CARD_LIMIT_SETTING, safe_value)
    return safe_value


def lightning_question_seconds() -> int:
    try:
        raw_value = int(get_setting(LIGHTNING_MODE_QUESTION_SECONDS_SETTING))
    except Exception:
        raw_value = 10
    return max(1, min(60, raw_value))


def set_lightning_question_seconds(value: int) -> int:
    safe_value = max(1, min(60, int(value)))
    set_setting(LIGHTNING_MODE_QUESTION_SECONDS_SETTING, safe_value)
    return safe_value


def lightning_answer_seconds() -> int:
    try:
        raw_value = int(get_setting(LIGHTNING_MODE_ANSWER_SECONDS_SETTING))
    except Exception:
        raw_value = 5
    return max(1, min(60, raw_value))


def set_lightning_answer_seconds(value: int) -> int:
    safe_value = max(1, min(60, int(value)))
    set_setting(LIGHTNING_MODE_ANSWER_SECONDS_SETTING, safe_value)
    return safe_value


def _db_rows(sql: str, *args: Any) -> list[tuple[Any, ...]]:
    rows = mw.col.db.all(sql, *args)
    return [tuple(row) for row in rows or []]


def _db_list(sql: str, *args: Any) -> list[int]:
    db = mw.col.db
    list_method = getattr(db, "list", None)
    if callable(list_method):
        try:
            return [int(value) for value in list_method(sql, *args)]
        except Exception:
            pass
    rows = db.all(sql, *args)
    return [int(row[0]) for row in rows or []]


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


def _placeholders(count: int) -> str:
    return ", ".join("?" for _ in range(max(0, int(count))))


def _usn_value() -> int:
    usn = getattr(mw.col, "usn", None)
    if callable(usn):
        try:
            return int(usn())
        except Exception:
            return 0
    return 0


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


def _deck_id_for_name(deck_name: str) -> int | None:
    finder = getattr(mw.col.decks, "id_for_name", None)
    if not callable(finder):
        return None
    try:
        deck_id = finder(str(deck_name))
    except Exception:
        return None
    if deck_id is None:
        return None
    try:
        safe_id = int(deck_id)
    except Exception:
        return None
    return safe_id if safe_id > 0 else None


def _is_filtered_deck(deck_id: int) -> bool:
    return bool(_deck_for_id(int(deck_id)).get("dyn"))


def _is_lightning_deck_id(deck_id: int) -> bool:
    deck = _deck_for_id(int(deck_id))
    if not deck.get("dyn"):
        return False
    return str(deck.get("name", "")).startswith(LIGHTNING_MODE_DECK_NAME_PREFIX)


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


def _chunked(values: list[int], chunk_size: int) -> list[list[int]]:
    if chunk_size <= 0:
        return [values]
    return [values[index : index + chunk_size] for index in range(0, len(values), chunk_size)]


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


def _recent_new_card_ids_from_filtered_deck(deck_id: int, *, limit: int) -> list[int]:
    safe_limit = max(1, min(1000, int(limit)))
    return _db_list(
        """
        SELECT c.id
        FROM cards AS c
        WHERE c.did = ?
          AND c.type = 0
          AND c.queue >= 0
        ORDER BY c.id DESC
        LIMIT ?
        """,
        int(deck_id),
        int(safe_limit),
    )


def _current_cards_still_in_filtered_decks(card_ids: list[int]) -> list[int]:
    unique_ids = _clean_card_ids(card_ids)
    if not unique_ids:
        return []
    found: list[int] = []
    for chunk in _chunked(unique_ids, _MAX_CARDS_PER_TERM):
        rows = _db_list(
            f"""
            SELECT c.id
            FROM cards AS c
            WHERE c.id IN ({_placeholders(len(chunk))})
              AND c.odid != 0
            """,
            *chunk,
        )
        found.extend(rows)
    return _clean_card_ids(found)


def _remove_cards_from_filtered_decks(card_ids: list[int]) -> list[int]:
    filtered_ids = _current_cards_still_in_filtered_decks(card_ids)
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

    usn_value = _usn_value()
    for chunk in _chunked(filtered_ids, _MAX_CARDS_PER_TERM):
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
            WHERE id IN ({_placeholders(len(chunk))})
              AND odid != 0
            """,
            int(usn_value),
            *chunk,
        )
    return filtered_ids


def _terms_for_exact_card_ids(existing_terms: Any, card_ids: list[int]) -> list[Any]:
    cleaned_card_ids = _clean_card_ids(card_ids)
    use_dict_terms = bool(
        isinstance(existing_terms, list) and existing_terms and isinstance(existing_terms[0], dict)
    )
    chunks = _chunked(cleaned_card_ids, _MAX_CARDS_PER_TERM)
    if not chunks:
        chunks = [[]]

    terms: list[Any] = []
    for chunk in chunks:
        if chunk:
            search = " or ".join(f"cid:{card_id}" for card_id in chunk)
            limit = len(chunk)
        else:
            search = "cid:0"
            limit = 1
        if use_dict_terms:
            terms.append({"search": search, "limit": limit, "order": 0})
        else:
            terms.append([search, limit, 0])
    return terms


def _rebuild_filtered_deck_with_exact_card_ids(
    deck_id: int,
    *,
    card_ids: list[int],
    original_terms: Any | None = None,
) -> bool:
    deck = mw.col.decks.get(int(deck_id))
    if not deck or not deck.get("dyn"):
        return False

    preserved_terms = deepcopy(deck.get("terms") if original_terms is None else original_terms)
    temporary_terms = _terms_for_exact_card_ids(preserved_terms, card_ids)

    try:
        deck["terms"] = temporary_terms
        mw.col.decks.save(deck)
        rebuild_filtered_deck(int(deck_id))
    finally:
        try:
            current_deck = mw.col.decks.get(int(deck_id)) or deck
            current_deck["terms"] = deepcopy(preserved_terms)
            mw.col.decks.save(current_deck)
        except Exception:
            pass
    return True


def _subtree_deck_ids(deck_id: int) -> list[int]:
    manager = mw.col.decks
    direct = getattr(manager, "deck_and_child_ids", None)
    if callable(direct):
        try:
            ids = [int(value) for value in direct(int(deck_id))]
        except Exception:
            ids = []
        if ids:
            return ids

    base_deck = _deck_for_id(int(deck_id))
    base_name = str(base_deck.get("name", "")).strip()
    if not base_name:
        return [int(deck_id)]

    prefix = f"{base_name}::"
    ids: list[int] = []
    all_names_and_ids = getattr(manager, "all_names_and_ids", None)
    if callable(all_names_and_ids):
        try:
            raw_items = list(all_names_and_ids() or [])
        except Exception:
            raw_items = []
        for item in raw_items:
            if isinstance(item, dict):
                candidate_id = item.get("id")
                candidate_name = item.get("name")
            elif isinstance(item, (tuple, list)) and len(item) >= 2:
                first, second = item[0], item[1]
                if isinstance(first, int):
                    candidate_id, candidate_name = first, second
                else:
                    candidate_name, candidate_id = first, second
            else:
                continue
            if candidate_id is None or not candidate_name:
                continue
            candidate_name = str(candidate_name)
            if candidate_name == base_name or candidate_name.startswith(prefix):
                ids.append(int(candidate_id))
    return ids or [int(deck_id)]


def _recent_new_card_candidates(deck_id: int, *, limit: int) -> list[CardCandidate]:
    subtree_ids = _subtree_deck_ids(int(deck_id))
    if not subtree_ids:
        return []

    placeholders = _placeholders(len(subtree_ids))
    safe_limit = max(1, min(1000, int(limit)))
    rows = _db_rows(
        f"""
        SELECT c.id, c.did, c.odid
        FROM cards AS c
        WHERE c.type = 0
          AND c.queue >= 0
          AND (
            (c.odid = 0 AND c.did IN ({placeholders}))
            OR c.odid IN ({placeholders})
          )
        ORDER BY c.id DESC
        LIMIT ?
        """,
        *[int(value) for value in subtree_ids],
        *[int(value) for value in subtree_ids],
        int(safe_limit),
    )
    return [
        CardCandidate(
            card_id=int(row[0]),
            current_deck_id=int(row[1] or 0),
            original_deck_id=int(row[2] or 0),
        )
        for row in rows
        if row and int(row[0] or 0) > 0
    ]


def _lightning_deck_name() -> str:
    return datetime.now().strftime(f"{LIGHTNING_MODE_DECK_NAME_PREFIX}%Y-%m-%d %H-%M-%S")


def _search_for_card_ids(card_ids: list[int]) -> str:
    cleaned_card_ids = _clean_card_ids(card_ids)
    if not cleaned_card_ids:
        return "cid:0"
    return " or ".join(f"cid:{card_id}" for card_id in cleaned_card_ids)


def _collection_get_config(key: str, default: Any) -> Any:
    getter = getattr(mw.col, "get_config", None)
    if callable(getter):
        try:
            return getter(str(key), default)
        except TypeError:
            return getter(str(key))
    legacy_getter = getattr(mw.col, "getConfig", None)
    if callable(legacy_getter):
        return legacy_getter(str(key), default=default)
    return deepcopy(default)


def _collection_set_config(key: str, value: Any) -> None:
    setter = getattr(mw.col, "set_config", None)
    if callable(setter):
        setter(str(key), value)
        return
    legacy_setter = getattr(mw.col, "setConfig", None)
    if callable(legacy_setter):
        legacy_setter(str(key), value)
        return
    raise RuntimeError("Collection config API is not available.")


def _normalize_lightning_session(raw_value: Any) -> dict[str, Any] | None:
    if not isinstance(raw_value, dict):
        return None

    try:
        source_deck_id = int(raw_value.get("source_filtered_deck_id", 0) or 0)
    except Exception:
        source_deck_id = 0
    try:
        target_deck_id = int(raw_value.get("target_deck_id", 0) or 0)
    except Exception:
        target_deck_id = 0

    source_deck_name = str(raw_value.get("source_filtered_deck_name", "") or "").strip()
    target_deck_name = str(raw_value.get("target_deck_name", "") or "").strip()
    if source_deck_id <= 0 and not source_deck_name:
        return None
    if target_deck_id <= 0 and not target_deck_name:
        return None

    selected_lightning_card_ids = _clean_card_ids(raw_value.get("selected_lightning_card_ids"))
    pending_lightning_card_ids = _clean_card_ids(raw_value.get("pending_lightning_card_ids"))
    if selected_lightning_card_ids:
        selected_set = set(selected_lightning_card_ids)
        pending_lightning_card_ids = [
            card_id for card_id in pending_lightning_card_ids if card_id in selected_set
        ]
    if not pending_lightning_card_ids and selected_lightning_card_ids:
        pending_lightning_card_ids = list(selected_lightning_card_ids)

    return {
        "created_at": str(raw_value.get("created_at", "") or ""),
        "leftover_source_card_ids": _clean_card_ids(raw_value.get("leftover_source_card_ids")),
        "pending_lightning_card_ids": pending_lightning_card_ids,
        "selected_lightning_card_ids": selected_lightning_card_ids,
        "source_filtered_deck_id": int(source_deck_id),
        "source_filtered_deck_name": source_deck_name,
        "source_filtered_deck_original_terms": deepcopy(
            raw_value.get("source_filtered_deck_original_terms")
        ),
        "source_snapshot_card_ids": _clean_card_ids(raw_value.get("source_snapshot_card_ids")),
        "target_deck_id": int(target_deck_id),
        "target_deck_name": target_deck_name,
    }


def _load_filtered_lightning_sessions() -> list[dict[str, Any]]:
    raw_sessions = _collection_get_config(FILTERED_LIGHTNING_SESSIONS_CONFIG_KEY, [])
    if not isinstance(raw_sessions, list):
        return []
    sessions: list[dict[str, Any]] = []
    seen_target_deck_ids: set[int] = set()
    for raw_session in raw_sessions:
        session = _normalize_lightning_session(raw_session)
        if session is None:
            continue
        target_deck_id = int(session.get("target_deck_id", 0) or 0)
        if target_deck_id > 0 and target_deck_id in seen_target_deck_ids:
            continue
        if target_deck_id > 0:
            seen_target_deck_ids.add(target_deck_id)
        sessions.append(session)
    return sessions


def _save_filtered_lightning_sessions(sessions: list[dict[str, Any]]) -> None:
    serialized_sessions = [
        session
        for session in (_normalize_lightning_session(item) for item in sessions)
        if session is not None
    ]
    _collection_set_config(FILTERED_LIGHTNING_SESSIONS_CONFIG_KEY, serialized_sessions)


def _resolved_filtered_deck(deck_id: int, deck_name: str) -> dict[str, Any] | None:
    candidates: list[int] = []
    if int(deck_id) > 0:
        candidates.append(int(deck_id))
    name_match_id = _deck_id_for_name(deck_name)
    if name_match_id is not None and name_match_id not in candidates:
        candidates.append(int(name_match_id))

    for candidate_id in candidates:
        deck = _deck_for_id(int(candidate_id))
        if deck and deck.get("dyn"):
            return deck
    return None


def _target_lightning_deck_for_session(session: dict[str, Any]) -> dict[str, Any] | None:
    deck = _resolved_filtered_deck(
        int(session.get("target_deck_id", 0) or 0),
        str(session.get("target_deck_name", "") or ""),
    )
    if not deck:
        return None
    if not str(deck.get("name", "")).startswith(LIGHTNING_MODE_DECK_NAME_PREFIX):
        return None
    return deck


def _source_filtered_deck_for_session(session: dict[str, Any]) -> dict[str, Any] | None:
    return _resolved_filtered_deck(
        int(session.get("source_filtered_deck_id", 0) or 0),
        str(session.get("source_filtered_deck_name", "") or ""),
    )


def _upsert_filtered_lightning_session(session: dict[str, Any]) -> None:
    normalized_session = _normalize_lightning_session(session)
    if normalized_session is None:
        return

    target_deck_id = int(normalized_session.get("target_deck_id", 0) or 0)
    sessions = [
        existing_session
        for existing_session in _load_filtered_lightning_sessions()
        if int(existing_session.get("target_deck_id", 0) or 0) != target_deck_id
    ]
    sessions.append(normalized_session)
    _save_filtered_lightning_sessions(sessions)
    _ensure_filtered_lightning_session_timer_running()


def _register_filtered_lightning_session(
    *,
    source_filtered_deck_id: int,
    source_filtered_deck_name: str,
    source_filtered_deck_original_terms: Any,
    source_snapshot_card_ids: list[int],
    selected_lightning_card_ids: list[int],
    leftover_source_card_ids: list[int],
    target_deck_id: int,
    target_deck_name: str,
) -> None:
    _upsert_filtered_lightning_session(
        {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "leftover_source_card_ids": _clean_card_ids(leftover_source_card_ids),
            "pending_lightning_card_ids": _clean_card_ids(selected_lightning_card_ids),
            "selected_lightning_card_ids": _clean_card_ids(selected_lightning_card_ids),
            "source_filtered_deck_id": int(source_filtered_deck_id),
            "source_filtered_deck_name": str(source_filtered_deck_name or ""),
            "source_filtered_deck_original_terms": deepcopy(source_filtered_deck_original_terms),
            "source_snapshot_card_ids": _clean_card_ids(source_snapshot_card_ids),
            "target_deck_id": int(target_deck_id),
            "target_deck_name": str(target_deck_name or ""),
        }
    )


def _exclude_pending_lightning_cards(*, target_deck_id: int, card_ids: list[int]) -> None:
    excluded_ids = set(_clean_card_ids(card_ids))
    if int(target_deck_id) <= 0 or not excluded_ids:
        return

    changed = False
    updated_sessions: list[dict[str, Any]] = []
    for session in _load_filtered_lightning_sessions():
        if int(session.get("target_deck_id", 0) or 0) != int(target_deck_id):
            updated_sessions.append(session)
            continue

        pending_ids = _clean_card_ids(session.get("pending_lightning_card_ids"))
        kept_ids = [card_id for card_id in pending_ids if card_id not in excluded_ids]
        if kept_ids != pending_ids:
            changed = True

        updated_session = dict(session)
        updated_session["pending_lightning_card_ids"] = kept_ids
        updated_sessions.append(updated_session)

    if not changed:
        return

    _save_filtered_lightning_sessions(updated_sessions)
    if updated_sessions:
        _ensure_filtered_lightning_session_timer_running()
    else:
        _stop_filtered_lightning_session_timer()


def _refresh_session_target_metadata(session: dict[str, Any]) -> dict[str, Any]:
    target_deck = _target_lightning_deck_for_session(session)
    if not target_deck:
        return dict(session)

    updated_session = dict(session)
    updated_session["target_deck_id"] = int(target_deck.get("id", 0) or 0)
    updated_session["target_deck_name"] = str(target_deck.get("name", "") or "")
    return updated_session


def _buried_card_ids_by_type(card_ids: list[int]) -> tuple[list[int], list[int]]:
    unique_ids = _clean_card_ids(card_ids)
    if not unique_ids:
        return [], []

    user_buried_ids: list[int] = []
    sched_buried_ids: list[int] = []
    for chunk in _chunked(unique_ids, _MAX_CARDS_PER_TERM):
        rows = _db_rows(
            f"""
            SELECT c.id, c.queue
            FROM cards AS c
            WHERE c.id IN ({_placeholders(len(chunk))})
              AND c.queue IN (-3, -2)
            """,
            *chunk,
        )
        for raw_card_id, raw_queue in rows:
            try:
                safe_card_id = int(raw_card_id or 0)
                safe_queue = int(raw_queue or 0)
            except Exception:
                continue
            if safe_card_id <= 0:
                continue
            if safe_queue == -3:
                user_buried_ids.append(safe_card_id)
            elif safe_queue == -2:
                sched_buried_ids.append(safe_card_id)

    return _clean_card_ids(user_buried_ids), _clean_card_ids(sched_buried_ids)


def _move_cards_to_filtered_deck_preserving_schedule(
    *,
    deck_id: int,
    card_ids: list[int],
) -> int:
    unique_ids = _clean_card_ids(card_ids)
    if int(deck_id) <= 0 or not unique_ids:
        return 0

    moved_count = 0
    mod_value = int(time.time())
    usn_value = _usn_value()
    for chunk in _chunked(unique_ids, _MAX_CARDS_PER_TERM):
        before_rows = _db_rows(
            f"""
            SELECT COUNT(*)
            FROM cards AS c
            WHERE c.id IN ({_placeholders(len(chunk))})
              AND c.did != ?
            """,
            *chunk,
            int(deck_id),
        )
        before_count = int(before_rows[0][0] or 0) if before_rows else 0
        if before_count <= 0:
            continue

        _db_execute(
            f"""
            UPDATE cards
            SET did = ?,
                odid = CASE
                    WHEN odid != 0 THEN odid
                    WHEN did != ? THEN did
                    ELSE odid
                END,
                odue = CASE
                    WHEN odid != 0 THEN odue
                    WHEN did != ? THEN due
                    ELSE odue
                END,
                mod = ?,
                usn = ?
            WHERE id IN ({_placeholders(len(chunk))})
              AND did != ?
            """,
            int(deck_id),
            int(deck_id),
            int(deck_id),
            int(mod_value),
            int(usn_value),
            *chunk,
            int(deck_id),
        )
        moved_count += before_count

    return moved_count


def _unbury_card_ids(card_ids: list[int]) -> bool:
    unique_ids = _clean_card_ids(card_ids)
    if not unique_ids:
        return True

    unbury = getattr(mw.col.sched, "unbury_cards", None)
    if callable(unbury):
        try:
            unbury(unique_ids)
            return True
        except Exception:
            pass

    unsuspend = getattr(mw.col.sched, "unsuspend_cards", None)
    if callable(unsuspend):
        try:
            unsuspend(unique_ids)
            return True
        except Exception:
            pass

    return False


def _rebury_card_ids(*, user_buried_ids: list[int], sched_buried_ids: list[int]) -> bool:
    bury = getattr(mw.col.sched, "bury_cards", None)
    if not callable(bury):
        return not _clean_card_ids(user_buried_ids + sched_buried_ids)

    user_ids = _clean_card_ids(user_buried_ids)
    sched_ids = _clean_card_ids(sched_buried_ids)

    try:
        if user_ids:
            bury(user_ids, manual=True)
        if sched_ids:
            bury(sched_ids, manual=False)
    except TypeError:
        try:
            if user_ids:
                bury(user_ids)
            if sched_ids:
                bury(sched_ids)
        except Exception:
            return False
    except Exception:
        return False

    return True


def _restore_filtered_lightning_session(session: dict[str, Any]) -> bool:
    source_deck = _source_filtered_deck_for_session(session)
    if not source_deck:
        return False

    source_deck_id = int(source_deck.get("id", 0) or 0)
    if source_deck_id <= 0:
        return False

    leftover_ids = _clean_card_ids(session.get("leftover_source_card_ids"))
    pending_ids = _clean_card_ids(session.get("pending_lightning_card_ids"))
    restore_ids = _clean_card_ids(leftover_ids + pending_ids)
    user_buried_ids, sched_buried_ids = _buried_card_ids_by_type(restore_ids)
    buried_restore_ids = _clean_card_ids(user_buried_ids + sched_buried_ids)
    unburied_for_restore = False

    if buried_restore_ids:
        if not _unbury_card_ids(buried_restore_ids):
            return False
        unburied_for_restore = True

    try:
        _move_cards_to_filtered_deck_preserving_schedule(
            deck_id=int(source_deck_id),
            card_ids=restore_ids,
        )
        restored = True
    except Exception:
        if unburied_for_restore:
            _rebury_card_ids(
                user_buried_ids=user_buried_ids,
                sched_buried_ids=sched_buried_ids,
            )
        return False

    if restored and unburied_for_restore:
        if not _rebury_card_ids(
            user_buried_ids=user_buried_ids,
            sched_buried_ids=sched_buried_ids,
        ):
            return False

    return bool(restored)


def check_pending_filtered_lightning_sessions() -> None:
    sessions = _load_filtered_lightning_sessions()
    if not sessions:
        _stop_filtered_lightning_session_timer()
        return

    changed = False
    restored_any = False
    remaining_sessions: list[dict[str, Any]] = []
    for session in sessions:
        target_deck = _target_lightning_deck_for_session(session)
        if target_deck is not None:
            updated_session = _refresh_session_target_metadata(session)
            if updated_session != session:
                changed = True
            remaining_sessions.append(updated_session)
            continue

        source_deck = _source_filtered_deck_for_session(session)
        if source_deck is None:
            changed = True
            continue

        if _restore_filtered_lightning_session(session):
            restored_any = True
            changed = True
            continue

        remaining_sessions.append(session)

    if changed:
        _save_filtered_lightning_sessions(remaining_sessions)

    if restored_any:
        mw.reset()

    if remaining_sessions:
        _ensure_filtered_lightning_session_timer_running()
    else:
        _stop_filtered_lightning_session_timer()


def _ensure_filtered_lightning_session_timer_running() -> None:
    global _filtered_lightning_session_timer
    if _filtered_lightning_session_timer is None:
        return
    if not _filtered_lightning_session_timer.isActive():
        _filtered_lightning_session_timer.start(_SESSION_TIMER_INTERVAL_MS)


def _stop_filtered_lightning_session_timer() -> None:
    if _filtered_lightning_session_timer is not None and _filtered_lightning_session_timer.isActive():
        _filtered_lightning_session_timer.stop()


def _on_main_window_init() -> None:
    global _filtered_lightning_session_timer
    if _filtered_lightning_session_timer is None:
        _filtered_lightning_session_timer = QTimer(mw)
        _filtered_lightning_session_timer.setInterval(_SESSION_TIMER_INTERVAL_MS)
        _filtered_lightning_session_timer.timeout.connect(check_pending_filtered_lightning_sessions)
    check_pending_filtered_lightning_sessions()
    if _load_filtered_lightning_sessions():
        _ensure_filtered_lightning_session_timer_running()


def _configure_lightning_filtered_deck(deck_id: int) -> None:
    deck = _deck_for_id(int(deck_id))
    if not deck:
        raise RuntimeError(f"Could not load filtered deck {int(deck_id)}.")

    desired_values = {
        "dyn": 1,
        "resched": True,
        "secondsToShowQuestion": float(lightning_question_seconds()),
        "secondsToShowAnswer": float(lightning_answer_seconds()),
        "questionAction": QUESTION_ACTION_SHOW_ANSWER,
        "answerAction": ANSWER_ACTION_BURY_CARD,
        "waitForAudio": False,
    }
    changed = False
    for key, value in desired_values.items():
        if deck.get(key) != value:
            deck[key] = value
            changed = True
    if changed:
        mw.col.decks.save(deck)


def _move_existing_filtered_cards_into_lightning(target_deck_id: int, card_ids: list[int]) -> int:
    unique_card_ids = [
        int(card_id)
        for card_id in dict.fromkeys(int(card_id) for card_id in card_ids if int(card_id) > 0)
    ]
    if not unique_card_ids:
        return 0

    moved_count = 0
    mod_value = int(time.time())
    usn_value = _usn_value()
    for chunk in _chunked(unique_card_ids, _MAX_CARDS_PER_TERM):
        before_rows = _db_rows(
            f"""
            SELECT COUNT(*)
            FROM cards
            WHERE id IN ({_placeholders(len(chunk))})
              AND odid != 0
              AND did != ?
            """,
            *chunk,
            int(target_deck_id),
        )
        before_count = int(before_rows[0][0] or 0) if before_rows else 0
        if before_count <= 0:
            continue
        _db_execute(
            f"""
            UPDATE cards
            SET did = ?,
                mod = ?,
                usn = ?
            WHERE id IN ({_placeholders(len(chunk))})
              AND odid != 0
              AND did != ?
            """,
            int(target_deck_id),
            int(mod_value),
            int(usn_value),
            *chunk,
            int(target_deck_id),
        )
        moved_count += before_count
    return moved_count


def _build_lightning_mode_for_normal_deck(source_deck: dict[str, Any]) -> bool:
    source_deck_id = int(source_deck.get("id", 0) or 0)
    candidates = _recent_new_card_candidates(source_deck_id, limit=lightning_card_limit())
    if not candidates:
        showInfo(
            f"No eligible new cards were found in '{_deck_name(source_deck_id)}'. "
            "Lightning Mode only gathers still-new, unburied, unsuspended cards."
        )
        return False

    deck_name = _lightning_deck_name()
    search = _search_for_card_ids([candidate.card_id for candidate in candidates])
    filtered_card_ids = [candidate.card_id for candidate in candidates if candidate.in_filtered_deck]

    try:
        lightning_deck_id = create_or_update_filtered_deck(
            deck_name,
            search=search,
            limit=len(candidates),
            resched=True,
        )
        _configure_lightning_filtered_deck(int(lightning_deck_id))
        transplanted_count = _move_existing_filtered_cards_into_lightning(
            int(lightning_deck_id),
            filtered_card_ids,
        )
        mw.reset()
    except Exception as exc:
        showWarning(f"Could not create the Lightning Mode deck.\n\n{exc}")
        return False

    selected_count = len(candidates)
    source_name = str(source_deck.get("name", _deck_name(source_deck_id)))
    extra = ""
    if transplanted_count:
        extra = f"\n\nPocket Knife also transplanted {transplanted_count} card(s) out of other filtered deck(s)."
    showInfo(
        f"Created '{deck_name}' with {selected_count} recent new card(s) from '{source_name}'.\n\n"
        f"Auto-advance is configured for {lightning_question_seconds()}s on the question side and "
        f"{lightning_answer_seconds()}s on the answer side. Unanswered answer-side timeouts will bury the card."
        f"{extra}"
    )
    return True


def _build_lightning_mode_for_filtered_deck(source_deck: dict[str, Any]) -> bool:
    source_deck_id = int(source_deck.get("id", 0) or 0)
    source_name = str(source_deck.get("name", _deck_name(source_deck_id)))
    source_snapshot_card_ids = _filtered_deck_live_card_ids(source_deck_id)
    if not source_snapshot_card_ids:
        showInfo(
            f"'{source_name}' is currently empty. Rebuild or open that filtered deck first, then try Lightning Mode again."
        )
        return False

    selected_lightning_card_ids = _recent_new_card_ids_from_filtered_deck(
        source_deck_id,
        limit=lightning_card_limit(),
    )
    if not selected_lightning_card_ids:
        showInfo(
            f"No eligible new cards were found in the current gathered contents of '{source_name}'. "
            "Lightning Mode only gathers still-new, unburied, unsuspended cards."
        )
        return False

    selected_set = set(selected_lightning_card_ids)
    leftover_source_card_ids = [
        int(card_id)
        for card_id in source_snapshot_card_ids
        if int(card_id) not in selected_set
    ]
    original_terms = deepcopy(source_deck.get("terms"))
    lightning_deck_name = _lightning_deck_name()
    search = _search_for_card_ids(selected_lightning_card_ids)
    removed_card_ids: list[int] = []

    try:
        removed_card_ids = _remove_cards_from_filtered_decks(selected_lightning_card_ids)
        if len(removed_card_ids) != len(selected_lightning_card_ids):
            raise RuntimeError(
                "Pocket Knife could not remove every selected card from the source filtered deck first."
            )
        lingering_filtered_ids = _current_cards_still_in_filtered_decks(selected_lightning_card_ids)
        if lingering_filtered_ids:
            raise RuntimeError(
                "Some selected cards were still inside a filtered deck after Pocket Knife tried to move them home."
            )

        if not _rebuild_filtered_deck_with_exact_card_ids(
            int(source_deck_id),
            card_ids=leftover_source_card_ids,
            original_terms=original_terms,
        ):
            raise RuntimeError("Could not rebuild the source filtered deck with its leftover cards.")

        lightning_deck_id = create_or_update_filtered_deck(
            lightning_deck_name,
            search=search,
            limit=len(selected_lightning_card_ids),
            resched=True,
        )
        _configure_lightning_filtered_deck(int(lightning_deck_id))
    except Exception as exc:
        if removed_card_ids:
            try:
                _rebuild_filtered_deck_with_exact_card_ids(
                    int(source_deck_id),
                    card_ids=source_snapshot_card_ids,
                    original_terms=original_terms,
                )
                mw.reset()
            except Exception:
                pass
        showWarning(f"Could not create the Lightning Mode deck from that filtered deck.\n\n{exc}")
        return False

    try:
        _register_filtered_lightning_session(
            source_filtered_deck_id=int(source_deck_id),
            source_filtered_deck_name=source_name,
            source_filtered_deck_original_terms=original_terms,
            source_snapshot_card_ids=source_snapshot_card_ids,
            selected_lightning_card_ids=selected_lightning_card_ids,
            leftover_source_card_ids=leftover_source_card_ids,
            target_deck_id=int(lightning_deck_id),
            target_deck_name=lightning_deck_name,
        )
    except Exception as exc:
        showWarning(
            "Lightning Mode created the filtered deck, but Pocket Knife could not save its restore session.\n\n"
            f"{exc}"
        )
        return False

    mw.reset()
    showInfo(
        f"Created '{lightning_deck_name}' with {len(selected_lightning_card_ids)} recent new card(s) from the current "
        f"gathered contents of '{source_name}'.\n\n"
        f"'{source_name}' was rebuilt immediately with its remaining {len(leftover_source_card_ids)} card(s), and "
        "Pocket Knife will restore any remaining Lightning cards, including buried ones, back into that filtered deck "
        "if you later delete the Lightning deck.\n\n"
        f"Auto-advance is configured for {lightning_question_seconds()}s on the question side and "
        f"{lightning_answer_seconds()}s on the answer side. Unanswered answer-side timeouts will bury the card."
    )
    return True


def build_lightning_mode_filtered_deck_for_deck_id(deck_id: int, *, parent=None) -> bool:
    del parent
    source_deck = _deck_for_id(int(deck_id))
    if not source_deck:
        showWarning("Could not find that deck.")
        return False
    if _is_lightning_deck_id(int(deck_id)):
        showWarning("Lightning Mode decks cannot be used to create another Lightning Mode deck.")
        return False
    if source_deck.get("dyn"):
        return _build_lightning_mode_for_filtered_deck(source_deck)
    return _build_lightning_mode_for_normal_deck(source_deck)


def build_lightning_mode_filtered_deck_for_current_deck(*, parent=None) -> bool:
    del parent
    current = getattr(mw.col.decks, "current", None)
    if not callable(current):
        showWarning("Could not determine the current deck.")
        return False

    try:
        current_deck = current() or {}
        deck_id = int(current_deck.get("id", 0) or 0)
    except Exception:
        deck_id = 0

    if deck_id <= 0:
        showWarning("Select a deck first.")
        return False

    return build_lightning_mode_filtered_deck_for_deck_id(deck_id)


def _maybe_add_deck_browser_action(menu: QMenu, deck_id: int) -> None:
    if _is_lightning_deck_id(int(deck_id)):
        return
    if menu.actions():
        menu.addSeparator()
    action = QAction(GEAR_ACTION_LABEL, menu)
    action.triggered.connect(
        lambda *_args, did=int(deck_id): build_lightning_mode_filtered_deck_for_deck_id(did)
    )
    menu.addAction(action)


def _displayed_deck_id_for_card(card: Any) -> int:
    did = getattr(card, "did", 0)
    try:
        return int(did or 0)
    except Exception:
        return 0


def _home_deck_id_for_card(card: Any) -> int:
    odid = getattr(card, "odid", 0)
    try:
        safe_odid = int(odid or 0)
    except Exception:
        safe_odid = 0
    if safe_odid > 0:
        return safe_odid
    return _displayed_deck_id_for_card(card)


def _current_lightning_review_card() -> Any | None:
    if getattr(mw, "state", "") != "review":
        return None
    reviewer = getattr(mw, "reviewer", None)
    if reviewer is None:
        return None
    card = getattr(reviewer, "card", None)
    if card is None:
        return None
    if not _is_lightning_deck_id(_displayed_deck_id_for_card(card)):
        return None
    return card


def _mark_lightning_card_handled(card: Any) -> None:
    if card is None:
        return
    target_deck_id = _displayed_deck_id_for_card(card)
    card_id = getattr(card, "id", 0)
    try:
        safe_card_id = int(card_id or 0)
    except Exception:
        safe_card_id = 0
    if safe_card_id <= 0 or not _is_lightning_deck_id(target_deck_id):
        return
    _exclude_pending_lightning_cards(target_deck_id=int(target_deck_id), card_ids=[safe_card_id])


def _remember_lightning_card_answer_target(card: Any) -> None:
    if card is None:
        return
    target_deck_id = _displayed_deck_id_for_card(card)
    card_id = getattr(card, "id", 0)
    try:
        safe_card_id = int(card_id or 0)
    except Exception:
        safe_card_id = 0
    if safe_card_id <= 0 or not _is_lightning_deck_id(target_deck_id):
        return
    _pending_lightning_answer_targets[int(safe_card_id)] = int(target_deck_id)


def _mark_lightning_card_id_handled(card_id: int) -> None:
    try:
        card = get_card(int(card_id))
    except Exception:
        return
    _mark_lightning_card_handled(card)


def _lightning_auto_advance_overrides(deck_id: int) -> dict[str, Any]:
    deck = _deck_for_id(int(deck_id))
    return {
        "secondsToShowQuestion": float(deck.get("secondsToShowQuestion", lightning_question_seconds())),
        "secondsToShowAnswer": float(deck.get("secondsToShowAnswer", lightning_answer_seconds())),
        "questionAction": int(deck.get("questionAction", QUESTION_ACTION_SHOW_ANSWER)),
        "answerAction": int(deck.get("answerAction", ANSWER_ACTION_BURY_CARD)),
        "waitForAudio": bool(deck.get("waitForAudio", False)),
    }


def _patch_deck_config_lookup() -> None:
    global _original_config_dict_for_deck_id
    global _deck_config_patch_installed

    if _deck_config_patch_installed:
        return

    try:
        from anki.decks import DeckManager
    except Exception:
        return

    original = getattr(DeckManager, "config_dict_for_deck_id", None)
    if not callable(original):
        return

    _original_config_dict_for_deck_id = original

    def wrapped(self: Any, did: Any) -> Any:
        conf = original(self, did)
        card = _current_lightning_review_card()
        if card is None:
            return conf

        displayed_deck_id = _displayed_deck_id_for_card(card)
        home_deck_id = _home_deck_id_for_card(card)
        try:
            requested_deck_id = int(did)
        except Exception:
            return conf

        if requested_deck_id not in {displayed_deck_id, home_deck_id}:
            return conf

        base_conf = conf
        if requested_deck_id == displayed_deck_id:
            try:
                base_conf = original(self, home_deck_id)
            except Exception:
                base_conf = conf

        merged_conf = dict(base_conf or {})
        merged_conf.update(_lightning_auto_advance_overrides(displayed_deck_id))
        return merged_conf

    DeckManager.config_dict_for_deck_id = wrapped
    _deck_config_patch_installed = True


def _set_reviewer_auto_advance_enabled(enabled: bool) -> None:
    reviewer = getattr(mw, "reviewer", None)
    if reviewer is None:
        return
    try:
        reviewer.auto_advance_enabled = bool(enabled)
    except Exception:
        return
    auto_advance_if_enabled = getattr(reviewer, "auto_advance_if_enabled", None)
    if callable(auto_advance_if_enabled):
        try:
            auto_advance_if_enabled()
        except Exception:
            pass


def _refresh_review_state_shortcuts() -> bool:
    if str(getattr(mw, "state", "") or "") != "review":
        return False

    reviewer = getattr(mw, "reviewer", None)
    clear_shortcuts = getattr(mw, "clearStateShortcuts", None)
    set_shortcuts = getattr(mw, "setStateShortcuts", None)
    shortcut_keys = getattr(reviewer, "_shortcutKeys", None) if reviewer is not None else None
    if not callable(clear_shortcuts) or not callable(set_shortcuts) or not callable(shortcut_keys):
        return False

    try:
        shortcuts = list(shortcut_keys())
    except Exception:
        return False

    try:
        clear_shortcuts()
        set_shortcuts(shortcuts)
    except Exception:
        return False

    return True


def _speed_streak_is_paused() -> bool:
    found = _find_speed_streak_controller()
    if found is None:
        return False

    _module_name, controller = found
    state = getattr(getattr(controller, "engine", None), "state", None)
    if state is None:
        return False

    try:
        return bool(getattr(state, "paused", False))
    except Exception:
        return False


def _should_block_lightning_auto_advance(reviewer: Any) -> bool:
    if not _speed_streak_is_paused():
        return False
    if str(getattr(mw, "state", "") or "") != "review":
        return False

    active_reviewer = getattr(mw, "reviewer", None)
    if reviewer is None or active_reviewer is None or reviewer is not active_reviewer:
        return False

    card = getattr(reviewer, "card", None)
    if card is None:
        return False

    return _is_lightning_deck_id(_displayed_deck_id_for_card(card))


def _patch_reviewer_auto_advance_timeouts() -> None:
    global _reviewer_timeout_patch_installed

    if _reviewer_timeout_patch_installed:
        return

    try:
        from aqt.reviewer import Reviewer
    except Exception:
        return

    original_show_answer_timeout = getattr(Reviewer, "_on_show_answer_timeout", None)
    original_show_question_timeout = getattr(Reviewer, "_on_show_question_timeout", None)
    if not callable(original_show_answer_timeout) or not callable(original_show_question_timeout):
        return

    def wrapped_show_answer_timeout(self: Any, *args: Any, **kwargs: Any) -> Any:
        if _should_block_lightning_auto_advance(self):
            return None
        return original_show_answer_timeout(self, *args, **kwargs)

    def wrapped_show_question_timeout(self: Any, *args: Any, **kwargs: Any) -> Any:
        if _should_block_lightning_auto_advance(self):
            return None
        return original_show_question_timeout(self, *args, **kwargs)

    Reviewer._on_show_answer_timeout = wrapped_show_answer_timeout
    Reviewer._on_show_question_timeout = wrapped_show_question_timeout
    _reviewer_timeout_patch_installed = True


def _clear_lightning_timer_pause_state() -> None:
    global _lightning_timer_pause_state
    _lightning_timer_pause_state = None


def _active_lightning_timer_slot() -> tuple[Any, str, QTimer | None, int] | None:
    reviewer = getattr(mw, "reviewer", None)
    card = _current_lightning_review_card()
    if reviewer is None or card is None:
        return None

    reviewer_state = str(getattr(reviewer, "state", "") or "")
    timer_attr_name = ""
    if reviewer_state == "question":
        timer_attr_name = "_show_answer_timer"
    elif reviewer_state == "answer":
        timer_attr_name = "_show_question_timer"
    else:
        return None

    timer = getattr(reviewer, timer_attr_name, None)
    card_id = getattr(card, "id", 0)
    try:
        safe_card_id = int(card_id or 0)
    except Exception:
        safe_card_id = 0
    if safe_card_id <= 0:
        return None
    return reviewer, reviewer_state, timer, safe_card_id


def _sync_lightning_timer_pause_state() -> None:
    global _lightning_timer_pause_state

    paused = _lightning_timer_pause_state
    if paused is None:
        return

    slot = _active_lightning_timer_slot()
    if slot is None:
        _lightning_timer_pause_state = None
        return

    _reviewer, reviewer_state, _timer, card_id = slot
    if int(paused.card_id) != int(card_id) or str(paused.reviewer_state) != str(reviewer_state):
        _lightning_timer_pause_state = None


def _resume_lightning_timer_if_paused() -> bool:
    paused = _lightning_timer_pause_state
    if paused is None:
        return False

    slot = _active_lightning_timer_slot()
    if slot is None:
        _clear_lightning_timer_pause_state()
        return False

    _reviewer, reviewer_state, timer, card_id = slot
    if int(paused.card_id) != int(card_id) or str(paused.reviewer_state) != str(reviewer_state):
        _clear_lightning_timer_pause_state()
        return False
    if timer is None:
        _clear_lightning_timer_pause_state()
        return False

    try:
        timer.start(max(1, int(paused.remaining_ms)))
    except Exception:
        _clear_lightning_timer_pause_state()
        return False

    _clear_lightning_timer_pause_state()
    return True


def _pause_active_lightning_timer() -> bool:
    global _lightning_timer_pause_state

    slot = _active_lightning_timer_slot()
    if slot is None:
        _clear_lightning_timer_pause_state()
        return False

    _reviewer, reviewer_state, timer, card_id = slot
    if timer is None:
        return False

    remaining_getter = getattr(timer, "remainingTime", None)
    is_active_getter = getattr(timer, "isActive", None)
    try:
        remaining_ms = int(remaining_getter()) if callable(remaining_getter) else 0
    except Exception:
        remaining_ms = 0
    try:
        is_active = bool(is_active_getter()) if callable(is_active_getter) else remaining_ms > 0
    except Exception:
        is_active = remaining_ms > 0

    if not is_active and remaining_ms <= 0:
        return False

    try:
        timer.stop()
    except Exception:
        return False

    _lightning_timer_pause_state = LightningTimerPauseState(
        card_id=int(card_id),
        reviewer_state=str(reviewer_state),
        remaining_ms=max(1, int(remaining_ms or 1)),
    )
    return True


def _toggle_lightning_timer_pause() -> bool:
    _sync_lightning_timer_pause_state()
    if _resume_lightning_timer_if_paused():
        return True
    return _pause_active_lightning_timer()


def _ensure_speed_streak_pause_bridge() -> Any | None:
    found = _find_speed_streak_controller()
    if found is None:
        return None

    _module_name, controller = found
    original = getattr(controller, "_on_pause_shortcut", None)
    if not callable(original):
        return controller

    if getattr(controller, "_anki_pocket_knife_lightning_pause_bridge_installed", False):
        return controller

    def wrapped_pause_shortcut(*args: Any, **kwargs: Any) -> None:
        original(*args, **kwargs)
        _toggle_lightning_timer_pause()

    setattr(controller, "_anki_pocket_knife_original_pause_shortcut", original)
    setattr(controller, "_on_pause_shortcut", wrapped_pause_shortcut)
    setattr(controller, "_anki_pocket_knife_lightning_pause_bridge_installed", True)
    return controller


def _on_lightning_pause_shortcut() -> None:
    controller = _ensure_speed_streak_pause_bridge()
    if controller is not None:
        pause_shortcut = getattr(controller, "_on_pause_shortcut", None)
        if callable(pause_shortcut):
            try:
                pause_shortcut()
                return
            except Exception:
                pass
    _toggle_lightning_timer_pause()


def _find_speed_streak_controller() -> tuple[str, Any] | None:
    for module_name, module in list(sys.modules.items()):
        if not module_name or not module_name.endswith("reviewer_overlay"):
            continue
        if module is None:
            continue
        package_name = str(getattr(module, "ADDON_PACKAGE", "") or "")
        display_name = str(getattr(module, "ADDON_DISPLAY_NAME", "") or "")
        haystack = f"{module_name} {package_name} {display_name}".casefold()
        if "speed_streak" not in haystack and "speed streak" not in haystack:
            continue
        controller = getattr(module, "controller", None)
        if controller is None or not hasattr(controller, "engine"):
            continue
        return module_name, controller
    return None


def _push_speed_streak_state(controller: Any) -> None:
    push_state = getattr(controller, "_push_state", None)
    if callable(push_state):
        try:
            push_state(only_if_changed=False)
        except TypeError:
            try:
                push_state()
            except Exception:
                pass
        except Exception:
            pass


def _apply_speed_streak_override() -> None:
    global _speed_streak_override

    found = _find_speed_streak_controller()
    if found is None:
        return

    module_name, controller = found
    pause_bridge_installed = bool(
        getattr(controller, "_anki_pocket_knife_lightning_pause_bridge_installed", False)
    )
    _ensure_speed_streak_pause_bridge()
    if not pause_bridge_installed:
        _refresh_review_state_shortcuts()
    state = getattr(getattr(controller, "engine", None), "state", None)
    if state is None:
        return

    if _speed_streak_override is None or _speed_streak_override.module_name != module_name:
        _speed_streak_override = SpeedStreakTimerOverride(
            module_name=module_name,
            question_seconds=max(0.1, float(getattr(state, "question_limit_ms", 5000)) / 1000.0),
            answer_seconds=max(0.1, float(getattr(state, "review_limit_ms", 5000)) / 1000.0),
        )

    try:
        controller.engine.update_time_limits(
            question_seconds=float(lightning_question_seconds()),
            answer_seconds=float(lightning_answer_seconds()),
        )
        _push_speed_streak_state(controller)
    except Exception:
        pass


def _restore_speed_streak_override() -> None:
    global _speed_streak_override

    override = _speed_streak_override
    if override is None:
        return
    _speed_streak_override = None

    found = _find_speed_streak_controller()
    if found is None:
        return

    module_name, controller = found
    if module_name != override.module_name:
        return

    try:
        controller.engine.update_time_limits(
            question_seconds=float(override.question_seconds),
            answer_seconds=float(override.answer_seconds),
        )
        _push_speed_streak_state(controller)
    except Exception:
        pass


def _sync_lightning_reviewer_runtime(card: Any) -> None:
    _sync_lightning_timer_pause_state()
    deck_id = _displayed_deck_id_for_card(card)
    if _is_lightning_deck_id(deck_id):
        try:
            _configure_lightning_filtered_deck(int(deck_id))
        except Exception:
            pass
        _set_reviewer_auto_advance_enabled(True)
        _apply_speed_streak_override()
        return

    _clear_lightning_timer_pause_state()
    _set_reviewer_auto_advance_enabled(False)
    _restore_speed_streak_override()


def _on_reviewer_did_show_question(card: Any) -> None:
    _sync_lightning_reviewer_runtime(card)


def _on_reviewer_did_show_answer(card: Any) -> None:
    _sync_lightning_reviewer_runtime(card)


def _on_reviewer_will_answer_card(answer_context: tuple[bool, int], reviewer: Any, card: Any) -> tuple[bool, int]:
    del reviewer
    try:
        proceed, _ease = answer_context
    except Exception:
        return answer_context
    if proceed:
        _remember_lightning_card_answer_target(card)
    return answer_context


def _on_reviewer_did_answer_card(reviewer: Any, card: Any, ease: int) -> None:
    del reviewer
    del ease
    _clear_lightning_timer_pause_state()
    card_id = getattr(card, "id", 0)
    try:
        safe_card_id = int(card_id or 0)
    except Exception:
        safe_card_id = 0
    if safe_card_id <= 0:
        return

    remembered_target = _pending_lightning_answer_targets.pop(int(safe_card_id), None)
    if remembered_target is not None:
        _exclude_pending_lightning_cards(
            target_deck_id=int(remembered_target),
            card_ids=[int(safe_card_id)],
        )
        return

    _mark_lightning_card_handled(card)


def _on_reviewer_will_bury_card(card_id: int) -> None:
    _clear_lightning_timer_pause_state()


def _on_reviewer_will_suspend_card(card_id: int) -> None:
    _clear_lightning_timer_pause_state()
    _mark_lightning_card_id_handled(int(card_id))


def _on_reviewer_will_end() -> None:
    _pending_lightning_answer_targets.clear()
    _clear_lightning_timer_pause_state()
    _set_reviewer_auto_advance_enabled(False)
    _restore_speed_streak_override()


def _on_state_did_change(new_state: str, old_state: str) -> None:
    del old_state
    if str(new_state or "") == "review":
        reviewer = getattr(mw, "reviewer", None)
        card = getattr(reviewer, "card", None) if reviewer is not None else None
        if card is not None:
            _sync_lightning_reviewer_runtime(card)
        return

    _pending_lightning_answer_targets.clear()
    _clear_lightning_timer_pause_state()
    _set_reviewer_auto_advance_enabled(False)
    _restore_speed_streak_override()


def _on_state_shortcuts_will_change(state: Any, shortcuts: list[tuple[str, Any]]) -> None:
    if str(state or "") != "review":
        return
    shortcuts.append((LIGHTNING_MODE_PAUSE_SHORTCUT, _on_lightning_pause_shortcut))


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    _patch_deck_config_lookup()
    _patch_reviewer_auto_advance_timeouts()

    deck_options_hook = getattr(gui_hooks, "deck_browser_will_show_options_menu", None)
    if deck_options_hook is not None:
        deck_options_hook.append(_maybe_add_deck_browser_action)
    else:
        try:
            from anki.hooks import addHook
        except Exception:
            addHook = None
        if callable(addHook):
            addHook("showDeckOptions", _maybe_add_deck_browser_action)

    reviewer_show_question = getattr(gui_hooks, "reviewer_did_show_question", None)
    if reviewer_show_question is not None:
        reviewer_show_question.append(_on_reviewer_did_show_question)

    reviewer_show_answer = getattr(gui_hooks, "reviewer_did_show_answer", None)
    if reviewer_show_answer is not None:
        reviewer_show_answer.append(_on_reviewer_did_show_answer)

    reviewer_will_answer = getattr(gui_hooks, "reviewer_will_answer_card", None)
    if reviewer_will_answer is not None:
        reviewer_will_answer.append(_on_reviewer_will_answer_card)

    reviewer_did_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_did_answer is not None:
        reviewer_did_answer.append(_on_reviewer_did_answer_card)

    reviewer_will_bury = getattr(gui_hooks, "reviewer_will_bury_card", None)
    if reviewer_will_bury is not None:
        reviewer_will_bury.append(_on_reviewer_will_bury_card)

    reviewer_will_suspend = getattr(gui_hooks, "reviewer_will_suspend_card", None)
    if reviewer_will_suspend is not None:
        reviewer_will_suspend.append(_on_reviewer_will_suspend_card)

    reviewer_will_end = getattr(gui_hooks, "reviewer_will_end", None)
    if reviewer_will_end is not None:
        reviewer_will_end.append(_on_reviewer_will_end)

    state_did_change = getattr(gui_hooks, "state_did_change", None)
    if state_did_change is not None:
        state_did_change.append(_on_state_did_change)

    state_shortcuts_will_change = getattr(gui_hooks, "state_shortcuts_will_change", None)
    if state_shortcuts_will_change is not None:
        state_shortcuts_will_change.append(_on_state_shortcuts_will_change)

    main_window_did_init = getattr(gui_hooks, "main_window_did_init", None)
    if main_window_did_init is not None:
        main_window_did_init.append(_on_main_window_init)

    _HOOK_REGISTERED = True
