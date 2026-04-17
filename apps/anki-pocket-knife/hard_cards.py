from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
import time
from typing import Any, Iterable, Mapping, Sequence

import aqt
from aqt import gui_hooks, mw
from aqt.qt import (
    QAbstractItemView,
    QAction,
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    Qt,
    QVBoxLayout,
)
from aqt.utils import showInfo, showWarning

try:
    from aqt.operations import QueryOp
except Exception:
    QueryOp = None

from .common import note_fields, note_type_name, user_files_dir
from .common import build_shared_deck_action_item, inject_shared_deck_action_html
from .hard_cards_core import (
    HardCardMetrics,
    RankedHardCard,
    build_tutor_clipboard_text,
    compute_failure_cluster_count,
    is_meaningful_candidate,
    merge_hard_cards_config,
    rank_hard_cards,
    select_note_content,
)


WINDOW_TITLE = "Study Repair"
DECK_BROWSER_OPEN_MESSAGE = "anki-pocket-knife:open-hard-cards"
BROWSER_SEARCH_TAG = "anki-pocket-knife:hard-cards"
BROWSER_SEARCH_PROMPT = "rated:1"
CONFIG_PATH = user_files_dir() / "hard_cards_config.json"
_HOOK_REGISTERED = False
_dialog: "StudyRepairDialog | None" = None
_browser_card_ids: list[int] = []


@dataclass(frozen=True)
class HardCardsSnapshot:
    lookback_hours: int
    top_n: int
    reviewed_card_count: int
    candidate_count: int
    generated_at_s: int
    ranked_cards: tuple[RankedHardCard, ...]


def load_hard_cards_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return merge_hard_cards_config({})

    try:
        raw_data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return merge_hard_cards_config({})

    if not isinstance(raw_data, dict):
        return merge_hard_cards_config({})

    return merge_hard_cards_config(raw_data)


def save_hard_cards_config(config: Mapping[str, Any]) -> dict[str, Any]:
    normalized = merge_hard_cards_config(config)
    CONFIG_PATH.write_text(
        json.dumps(normalized, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return normalized


def _persist_default_controls(lookback_hours: int, top_n: int) -> dict[str, Any]:
    config = load_hard_cards_config()
    config["default_lookback_hours"] = max(1, int(lookback_hours))
    config["default_top_n"] = max(1, int(top_n))
    return save_hard_cards_config(config)


def _safe_int(raw_value: Any, default: int = 0) -> int:
    try:
        return int(raw_value)
    except Exception:
        return int(default)


def _chunked(values: Sequence[int], size: int) -> Iterable[list[int]]:
    safe_size = max(1, int(size))
    for index in range(0, len(values), safe_size):
        yield [int(value) for value in values[index : index + safe_size]]


def _get_card_from_collection(collection: Any, card_id: int) -> Any | None:
    for method_name in ("get_card", "getCard"):
        method = getattr(collection, method_name, None)
        if not callable(method):
            continue
        try:
            return method(int(card_id))
        except Exception:
            continue
    return None


def _note_type_info(note: Any) -> Mapping[str, Any] | None:
    for attr in ("note_type", "notetype", "model"):
        method = getattr(note, attr, None)
        if not callable(method):
            continue
        try:
            info = method()
        except Exception:
            continue
        if isinstance(info, Mapping):
            return info
    return None


def _is_cloze_note(note: Any, resolved_note_type_name: str) -> bool:
    info = _note_type_info(note) or {}
    model_type = info.get("type")
    try:
        if model_type is not None and int(model_type) == 1:
            return True
    except Exception:
        pass

    name = str(info.get("name", resolved_note_type_name or "")).casefold()
    return "cloze" in name


def _deck_name_for_card(collection: Any, card: Any) -> str:
    deck_id = _safe_int(getattr(card, "odid", 0)) or _safe_int(getattr(card, "did", 0))
    decks = getattr(collection, "decks", None)
    if decks is None:
        return "Unknown Deck"

    name_method = getattr(decks, "name", None)
    if callable(name_method):
        try:
            return str(name_method(int(deck_id)))
        except Exception:
            pass

    get_method = getattr(decks, "get", None)
    if callable(get_method):
        try:
            info = get_method(int(deck_id)) or {}
        except Exception:
            info = {}
        if isinstance(info, Mapping):
            return str(info.get("name", "Unknown Deck"))

    return "Unknown Deck"


def _card_state(card: Any) -> str:
    queue = _safe_int(getattr(card, "queue", 0))
    card_type = _safe_int(getattr(card, "type", 0))
    lapses = _safe_int(getattr(card, "lapses", 0))

    if queue == -1:
        return "suspended"
    if queue in {-2, -3}:
        return "buried"
    if card_type == 3 or queue == 3:
        return "relearning"
    if card_type == 1 or queue == 1:
        return "relearning" if lapses > 0 else "learning"
    if card_type == 0 or queue == 0:
        return "new"
    return "review"


def _fsrs_difficulty(card: Any) -> float | None:
    for attr in ("memory_state", "memoryState"):
        raw_value = getattr(card, attr, None)
        if callable(raw_value):
            try:
                raw_value = raw_value()
            except Exception:
                raw_value = None
        if raw_value is None:
            continue

        if isinstance(raw_value, Mapping):
            difficulty = raw_value.get("difficulty")
        else:
            difficulty = getattr(raw_value, "difficulty", None)
        if difficulty is None:
            continue
        try:
            return float(difficulty)
        except Exception:
            continue
    return None


def _first_review_timestamp_s_by_card(collection: Any, card_ids: Sequence[int]) -> dict[int, int]:
    if not card_ids:
        return {}

    result: dict[int, int] = {}
    for chunk in _chunked([int(card_id) for card_id in card_ids if int(card_id) > 0], 400):
        if not chunk:
            continue
        placeholders = ", ".join("?" for _ in chunk)
        rows = collection.db.all(
            f"""
            SELECT cid, MIN(id)
            FROM revlog
            WHERE cid IN ({placeholders})
              AND ease BETWEEN 1 AND 4
            GROUP BY cid
            """,
            *chunk,
        )
        for raw_card_id, raw_first_review in rows:
            card_id = _safe_int(raw_card_id)
            first_review_ms = _safe_int(raw_first_review)
            if card_id <= 0 or first_review_ms <= 0:
                continue
            result[card_id] = int(first_review_ms / 1000)
    return result


def _introduced_age_hours(now_s: int, card_id: int, first_review_at_s: int | None) -> float:
    introduced_at_s = _safe_int(first_review_at_s)
    if introduced_at_s <= 0:
        introduced_at_s = max(1, int(int(card_id) / 1000))
    return max(0.0, (float(now_s) - float(introduced_at_s)) / 3600.0)


def _build_metrics_for_card(
    collection: Any,
    *,
    card_id: int,
    events: list[tuple[int, int]],
    now_s: int,
    first_review_at_s: int | None,
    config: Mapping[str, Any],
) -> HardCardMetrics | None:
    card = _get_card_from_collection(collection, card_id)
    if card is None:
        return None

    try:
        note = card.note()
    except Exception:
        return None
    if note is None:
        return None

    resolved_note_type_name = note_type_name(note)
    is_cloze = _is_cloze_note(note, resolved_note_type_name)
    selected_content = select_note_content(
        note_type_name=resolved_note_type_name,
        fields=note_fields(note),
        is_cloze=is_cloze,
        config=config,
    )

    again_count = sum(1 for _timestamp_s, ease in events if int(ease) == 1)
    hard_count = sum(1 for _timestamp_s, ease in events if int(ease) == 2)
    good_count = sum(1 for _timestamp_s, ease in events if int(ease) == 3)
    easy_count = sum(1 for _timestamp_s, ease in events if int(ease) == 4)

    return HardCardMetrics(
        card_id=int(card_id),
        note_id=_safe_int(getattr(note, "id", getattr(card, "nid", 0))),
        deck_name=_deck_name_for_card(collection, card),
        note_type_name=resolved_note_type_name,
        is_cloze=is_cloze,
        current_state=_card_state(card),
        created_age_hours=_introduced_age_hours(now_s, card_id, first_review_at_s),
        total_reps=_safe_int(getattr(card, "reps", 0)),
        total_lapses=_safe_int(getattr(card, "lapses", 0)),
        again_count=again_count,
        hard_count=hard_count,
        good_count=good_count,
        easy_count=easy_count,
        total_answers=len(events),
        most_recent_ease=int(events[-1][1]) if events else None,
        last_review_at_s=int(events[-1][0]) if events else None,
        failure_cluster_count=compute_failure_cluster_count(
            events,
            cluster_window_minutes=float(config.get("cluster_window_minutes", 30)),
        ),
        content=selected_content,
        fsrs_difficulty=_fsrs_difficulty(card),
    )


def compute_hard_cards_snapshot(
    collection: Any,
    *,
    lookback_hours: int,
    top_n: int,
    config: Mapping[str, Any],
) -> HardCardsSnapshot:
    safe_lookback_hours = max(1, int(lookback_hours))
    safe_top_n = max(1, int(top_n))
    now_s = int(time.time())
    cutoff_ms = int((now_s - (safe_lookback_hours * 60 * 60)) * 1000)

    rows = collection.db.all(
        """
        SELECT id, cid, ease
        FROM revlog
        WHERE id >= ?
          AND ease BETWEEN 1 AND 4
        ORDER BY cid, id
        """,
        int(cutoff_ms),
    )

    events_by_card: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for raw_timestamp_ms, raw_card_id, raw_ease in rows:
        card_id = _safe_int(raw_card_id)
        ease = _safe_int(raw_ease)
        timestamp_ms = _safe_int(raw_timestamp_ms)
        if card_id <= 0 or ease not in {1, 2, 3, 4} or timestamp_ms <= 0:
            continue
        events_by_card[card_id].append((int(timestamp_ms / 1000), ease))

    if not events_by_card:
        return HardCardsSnapshot(
            lookback_hours=safe_lookback_hours,
            top_n=safe_top_n,
            reviewed_card_count=0,
            candidate_count=0,
            generated_at_s=now_s,
            ranked_cards=(),
        )

    first_review_at_s_by_card = _first_review_timestamp_s_by_card(
        collection,
        list(events_by_card.keys()),
    )

    metrics_list: list[HardCardMetrics] = []
    for card_id, events in events_by_card.items():
        metrics = _build_metrics_for_card(
            collection,
            card_id=int(card_id),
            events=events,
            now_s=now_s,
            first_review_at_s=first_review_at_s_by_card.get(int(card_id)),
            config=config,
        )
        if metrics is not None:
            metrics_list.append(metrics)

    candidate_count = sum(1 for metrics in metrics_list if is_meaningful_candidate(metrics))
    ranked_cards = tuple(rank_hard_cards(metrics_list, config=config, top_n=safe_top_n))

    return HardCardsSnapshot(
        lookback_hours=safe_lookback_hours,
        top_n=safe_top_n,
        reviewed_card_count=len(events_by_card),
        candidate_count=candidate_count,
        generated_at_s=now_s,
        ranked_cards=ranked_cards,
    )


def _ordered_unique_card_ids(card_ids: Sequence[int]) -> list[int]:
    ordered: list[int] = []
    seen: set[int] = set()
    for raw_card_id in card_ids:
        card_id = _safe_int(raw_card_id)
        if card_id <= 0 or card_id in seen:
            continue
        seen.add(card_id)
        ordered.append(card_id)
    return ordered


def _existing_card_ids(card_ids: Sequence[int]) -> set[int]:
    safe_ids = _ordered_unique_card_ids(card_ids)
    if not safe_ids:
        return set()

    placeholders = ", ".join("?" for _ in safe_ids)
    rows = mw.col.db.all(
        f"SELECT id FROM cards WHERE id IN ({placeholders})",
        *safe_ids,
    )
    return {int(row[0]) for row in rows}


def _browser_cards_mode(browser: Any) -> None:
    table = getattr(browser, "table", None)
    if table is None:
        return
    is_notes_mode = getattr(table, "is_notes_mode", None)
    if not callable(is_notes_mode):
        return
    try:
        currently_notes_mode = bool(is_notes_mode())
    except Exception:
        return
    if not currently_notes_mode:
        return

    toggle = getattr(browser, "on_table_state_changed", None)
    if callable(toggle):
        try:
            toggle(False)
        except Exception:
            pass


def open_hard_cards_browser(card_ids: Sequence[int]) -> None:
    global _browser_card_ids

    wanted_ids = _ordered_unique_card_ids(card_ids)
    if not wanted_ids:
        showInfo("No recent hard cards are available to show in Browser.")
        return

    existing_ids = _existing_card_ids(wanted_ids)
    browser_card_ids = [card_id for card_id in wanted_ids if card_id in existing_ids]
    if not browser_card_ids:
        showInfo("Those recent hard cards no longer exist in the collection.")
        return

    _browser_card_ids = browser_card_ids
    browser = None
    dialogs = getattr(aqt, "dialogs", None)
    opener = getattr(dialogs, "open", None) if dialogs is not None else None
    if callable(opener):
        browser = opener("Browser", mw)

    if browser is None:
        showInfo("Could not open Anki's Browser window.")
        return

    _browser_cards_mode(browser)
    browser.activateWindow()
    browser.raise_()
    browser.search_for(BROWSER_SEARCH_TAG, BROWSER_SEARCH_PROMPT)


def _snapshot_card_ids(snapshot: HardCardsSnapshot | None) -> list[int]:
    if snapshot is None:
        return []
    return [ranked.metrics.card_id for ranked in snapshot.ranked_cards]


def _is_deck_browser_context(context: Any) -> bool:
    if context is getattr(mw, "deckBrowser", None):
        return True
    return getattr(getattr(context, "__class__", None), "__name__", "") == "DeckBrowser"


def _study_repair_button_html() -> str:
    return build_shared_deck_action_item(
        key="anki-pocket-knife:study-repair",
        order=20,
        message=DECK_BROWSER_OPEN_MESSAGE,
        label="Study Repair",
    )


def _on_deck_browser_will_render_content(deck_browser: Any, content: Any) -> None:
    del deck_browser
    banner_html = _study_repair_button_html()
    current_tree = getattr(content, "tree", None)
    if isinstance(current_tree, str):
        content.tree = inject_shared_deck_action_html(current_tree, banner_html)
        return

    current_stats = getattr(content, "stats", None)
    if isinstance(current_stats, str):
        content.stats = inject_shared_deck_action_html(current_stats, banner_html)


def _on_webview_did_receive_js_message(
    handled: tuple[bool, Any],
    message: str,
    context: Any,
) -> tuple[bool, Any]:
    if handled[0]:
        return handled
    if message != DECK_BROWSER_OPEN_MESSAGE:
        return handled
    if not _is_deck_browser_context(context):
        return handled

    open_hard_cards_dialog()
    return (True, None)


def _apply_hard_cards_browser_search(search_context: Any) -> None:
    if getattr(search_context, "search", "") != BROWSER_SEARCH_TAG:
        return

    search_context.search = BROWSER_SEARCH_PROMPT
    search_context.ids = list(_browser_card_ids)


def build_open_hard_cards_action(parent) -> QAction:
    action = QAction("Open Study Repair", parent)
    action.triggered.connect(lambda *_args: open_hard_cards_dialog())
    return action


def _pluralize(value: int, singular: str, plural: str | None = None) -> str:
    safe_value = int(value)
    if safe_value == 1:
        return f"1 {singular}"
    return f"{safe_value} {plural or singular + 's'}"


def _snapshot_summary(snapshot: HardCardsSnapshot, *, stale: bool) -> str:
    lookback_text = _pluralize(snapshot.lookback_hours, "hour")
    if snapshot.reviewed_card_count <= 0:
        summary = f"No review answers were found in the last {lookback_text}."
    elif snapshot.candidate_count <= 0:
        summary = (
            f"Reviewed {_pluralize(snapshot.reviewed_card_count, 'card')} in the last {lookback_text}. "
            "Nothing currently looks unstable enough to rank."
        )
    else:
        summary = (
            f"Showing {_pluralize(len(snapshot.ranked_cards), 'card')} from "
            f"{_pluralize(snapshot.candidate_count, 'unstable candidate')} across "
            f"{_pluralize(snapshot.reviewed_card_count, 'reviewed card')} in the last {lookback_text}."
        )

    if stale:
        return f"{summary} Press Refresh / Recompute to apply the updated controls."
    return summary


def _item_text(index: int, ranked: RankedHardCard) -> str:
    why = ", ".join(ranked.explanation)
    headline = f"#{index}  Score {ranked.score:.1f}  {ranked.preview_text or '(blank)'}"
    detail = (
        f"{ranked.metrics.deck_name} | {ranked.metrics.note_type_name} | "
        f"{why or 'recent instability'}"
    )
    return f"{headline}\n{detail}"


def _item_tooltip(index: int, ranked: RankedHardCard) -> str:
    field_source = ", ".join(ranked.metrics.content.field_names) or "Unknown"
    reasons = ", ".join(ranked.explanation) or "recent instability"
    return "\n".join(
        [
            f"Rank #{index}",
            f"Score: {ranked.score:.2f}",
            f"Deck: {ranked.metrics.deck_name}",
            f"Note type: {ranked.metrics.note_type_name}",
            f"Field source: {field_source}",
            f"Why: {reasons}",
            "",
            ranked.metrics.content.content_text or "(blank)",
        ]
    )


class StudyRepairDialog(QDialog):
    def __init__(self) -> None:
        super().__init__(mw)
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(880, 620)
        self._config = load_hard_cards_config()
        self._snapshot: HardCardsSnapshot | None = None
        self._active_snapshot_config = dict(self._config)
        self._loading = False
        self._params_stale = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Rank cards from the recent review window that look genuinely unstable or not truly learned yet. "
            "This is read-only: it analyzes your existing history, then lets you open the exact cards in Browser "
            "or copy clean note content for a tutor workflow."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        controls_row = QHBoxLayout()
        controls_row.addWidget(QLabel("Look back:"))
        self.lookback_hours_spin = QSpinBox()
        self.lookback_hours_spin.setRange(1, 24 * 30)
        self.lookback_hours_spin.setValue(int(self._config.get("default_lookback_hours", 24)))
        controls_row.addWidget(self.lookback_hours_spin)
        controls_row.addWidget(QLabel("hours"))
        controls_row.addSpacing(18)
        controls_row.addWidget(QLabel("Top cards:"))
        self.top_n_spin = QSpinBox()
        self.top_n_spin.setRange(1, 500)
        self.top_n_spin.setSingleStep(5)
        self.top_n_spin.setValue(int(self._config.get("default_top_n", 20)))
        controls_row.addWidget(self.top_n_spin)
        controls_row.addStretch(1)
        layout.addLayout(controls_row)

        self.summary_label = QLabel("Press Refresh / Recompute to load recent hard cards.")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.results_list = QListWidget()
        self.results_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.results_list.setAlternatingRowColors(True)
        layout.addWidget(self.results_list, 1)

        advanced = QLabel(
            "Advanced weights, field preferences, and copy options live in "
            f"{CONFIG_PATH.name} inside Pocket Knife's user_files folder."
        )
        advanced.setWordWrap(True)
        layout.addWidget(advanced)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.view_browser_button = QPushButton("View In Browser")
        self.copy_all_button = QPushButton("Copy All For Tutor")
        self.refresh_button = QPushButton("Refresh / Recompute")
        self.close_button = QPushButton("Close")
        button_row.addWidget(self.view_browser_button)
        button_row.addWidget(self.copy_all_button)
        button_row.addWidget(self.refresh_button)
        button_row.addWidget(self.close_button)
        layout.addLayout(button_row)

        self.lookback_hours_spin.valueChanged.connect(self._on_controls_changed)
        self.top_n_spin.valueChanged.connect(self._on_controls_changed)
        self.view_browser_button.clicked.connect(self._view_in_browser)
        self.copy_all_button.clicked.connect(self._copy_all_for_tutor)
        self.refresh_button.clicked.connect(lambda *_args: self.refresh_snapshot(force=True))
        self.close_button.clicked.connect(self.close)

        self._update_action_states()

    def reload_controls_from_config(self) -> None:
        self._config = load_hard_cards_config()
        self.lookback_hours_spin.blockSignals(True)
        self.top_n_spin.blockSignals(True)
        self.lookback_hours_spin.setValue(int(self._config.get("default_lookback_hours", 24)))
        self.top_n_spin.setValue(int(self._config.get("default_top_n", 20)))
        self.lookback_hours_spin.blockSignals(False)
        self.top_n_spin.blockSignals(False)
        self._params_stale = False
        self._update_summary()
        self._update_action_states()

    def _on_controls_changed(self, *_args: Any) -> None:
        self._config = _persist_default_controls(
            int(self.lookback_hours_spin.value()),
            int(self.top_n_spin.value()),
        )
        self._params_stale = True
        self._update_summary()
        self._update_action_states()

    def _set_loading(self, loading: bool) -> None:
        self._loading = bool(loading)
        self.refresh_button.setEnabled(not self._loading)
        self.lookback_hours_spin.setEnabled(not self._loading)
        self.top_n_spin.setEnabled(not self._loading)
        self._update_action_states()

    def _update_summary(self) -> None:
        if self._loading:
            self.summary_label.setText("Computing recent hard cards...")
            return
        if self._snapshot is None:
            if self._params_stale:
                self.summary_label.setText(
                    "Controls changed. Press Refresh / Recompute to load recent hard cards."
                )
            else:
                self.summary_label.setText(
                    "Press Refresh / Recompute to load recent hard cards."
                )
            return
        self.summary_label.setText(_snapshot_summary(self._snapshot, stale=self._params_stale))

    def _update_action_states(self) -> None:
        has_results = bool(self._snapshot and self._snapshot.ranked_cards)
        actions_enabled = has_results and not self._loading and not self._params_stale
        self.view_browser_button.setEnabled(actions_enabled)
        self.copy_all_button.setEnabled(actions_enabled)

    def _render_snapshot(self) -> None:
        self.results_list.clear()
        if self._snapshot is None:
            return

        for index, ranked in enumerate(self._snapshot.ranked_cards, start=1):
            item = QListWidgetItem(_item_text(index, ranked))
            item.setToolTip(_item_tooltip(index, ranked))
            item.setData(Qt.ItemDataRole.UserRole, int(ranked.metrics.card_id))
            self.results_list.addItem(item)

    def refresh_snapshot(self, *, force: bool = False) -> None:
        if self._loading:
            return
        if not force and not self._params_stale and self._snapshot is not None:
            return

        lookback_hours = int(self.lookback_hours_spin.value())
        top_n = int(self.top_n_spin.value())
        self._active_snapshot_config = _persist_default_controls(lookback_hours, top_n)
        self._params_stale = False
        self._set_loading(True)
        self._update_summary()

        if QueryOp is None:
            try:
                snapshot = compute_hard_cards_snapshot(
                    mw.col,
                    lookback_hours=lookback_hours,
                    top_n=top_n,
                    config=self._active_snapshot_config,
                )
            except Exception as exc:
                self._on_query_failed(exc)
            else:
                self._on_snapshot_ready(snapshot)
            return

        try:
            op = QueryOp(
                parent=self,
                op=lambda collection: compute_hard_cards_snapshot(
                    collection,
                    lookback_hours=lookback_hours,
                    top_n=top_n,
                    config=self._active_snapshot_config,
                ),
                success=self._on_snapshot_ready,
            )
            failure_method = getattr(op, "failure", None)
            if callable(failure_method):
                configured = failure_method(self._on_query_failed)
                if configured is not None:
                    op = configured
            progress_method = getattr(op, "with_progress", None)
            if callable(progress_method):
                try:
                    configured = progress_method(label="Computing recent hard cards...")
                except TypeError:
                    configured = progress_method("Computing recent hard cards...")
                if configured is not None:
                    op = configured
            op.run_in_background()
        except Exception as exc:
            self._on_query_failed(exc)

    def _on_snapshot_ready(self, snapshot: HardCardsSnapshot) -> None:
        self._snapshot = snapshot
        self._set_loading(False)
        self._render_snapshot()
        self._update_summary()

    def _on_query_failed(self, exc: Any) -> None:
        self._snapshot = None
        self.results_list.clear()
        self._set_loading(False)
        self._update_summary()
        showWarning(f"Could not compute recent hard cards.\n\n{exc}")

    def _view_in_browser(self) -> None:
        if self._snapshot is None or self._params_stale:
            return
        open_hard_cards_browser(_snapshot_card_ids(self._snapshot))

    def _copy_all_for_tutor(self) -> None:
        if self._snapshot is None or self._params_stale:
            return
        ranked_cards = list(self._snapshot.ranked_cards)
        if not ranked_cards:
            showInfo("No recent hard cards are available to copy.")
            return

        text = build_tutor_clipboard_text(
            ranked_cards,
            config=self._active_snapshot_config,
        )
        QApplication.clipboard().setText(text)
        showInfo(
            f"Copied {_pluralize(len(ranked_cards), 'card')} for your tutor workflow."
        )


def open_hard_cards_dialog() -> None:
    global _dialog

    if _dialog is None:
        _dialog = StudyRepairDialog()

    _dialog.reload_controls_from_config()
    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
    _dialog.refresh_snapshot(force=True)


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    deck_browser_hook = getattr(gui_hooks, "deck_browser_will_render_content", None)
    if deck_browser_hook is not None:
        deck_browser_hook.append(_on_deck_browser_will_render_content)

    browser_will_search = getattr(gui_hooks, "browser_will_search", None)
    if browser_will_search is not None:
        browser_will_search.append(_apply_hard_cards_browser_search)

    webview_hook = getattr(gui_hooks, "webview_did_receive_js_message", None)
    if webview_hook is not None:
        webview_hook.append(_on_webview_did_receive_js_message)

    _HOOK_REGISTERED = True
