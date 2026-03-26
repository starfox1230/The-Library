from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
import time
from typing import Any, Dict, Optional


ANSWER_LIMIT_MS = 12_000
REVIEW_LIMIT_MS = 8_000
COLOR_KEYS = ("core", "red", "yellow", "green", "blue")
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def now_epoch_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class CardRuntime:
    question_elapsed_ms: int = 0
    question_free: bool = False
    answer_elapsed_ms: int = 0


@dataclass
class CompanionState:
    enabled: bool = True
    visuals_enabled: bool = True
    show_card_timer: bool = True
    custom_timer_colors: bool = False
    custom_timer_color_level: float = 0.0
    sidebar_collapsed: bool = False
    appearance_mode: str = "midnight"
    custom_colors: dict[str, str] = field(default_factory=dict)
    synced: bool = False
    session_active: bool = False
    first_card_free: bool = False
    phase: str = "idle"
    phase_start_epoch_ms: int = 0
    phase_limit_ms: int = 0
    answer_shown: bool = False
    current_card_index: int = 0
    current_card_id: str = ""
    deck_name: str = ""
    current_card_flag: int = 0
    previous_card_flag: int = 0
    answered_cards: int = 0
    skipped_cards: int = 0
    score: int = 0
    streak: int = 0
    streak_multiplier: float = 1.0
    paused: bool = False
    paused_remaining_ms: int = 0
    failure_visual_active: bool = False
    last_satellite_color: str = "green"
    satellite_colors: list[str] = field(default_factory=list)
    last_event_type: str = ""
    last_event_text: str = ""
    event_nonce: int = 0
    timeout_phase_latch: str = ""
    skip_pending: bool = False
    question_limit_ms: int = ANSWER_LIMIT_MS
    review_limit_ms: int = REVIEW_LIMIT_MS
    total_pause_ms: int = 0
    pause_started_epoch_ms: int = 0
    time_drain_flag: int = 2
    review_later_flag: int = 4


@dataclass
class ReviewUndoSnapshot:
    state: CompanionState
    card: CardRuntime
    last_review_metrics: Optional[Dict[str, Any]]


@dataclass
class CompanionGameEngine:
    state: CompanionState = field(default_factory=CompanionState)
    card: CardRuntime = field(default_factory=CardRuntime)
    _last_review_metrics: Optional[Dict[str, Any]] = None
    _review_undo_stack: list[ReviewUndoSnapshot] = field(default_factory=list)

    def export(self) -> Dict[str, Any]:
        s = self.state
        return {
            "version": 5,
            "enabled": int(s.enabled),
            "visualsEnabled": int(s.visuals_enabled),
            "showCardTimer": int(s.show_card_timer),
            "customTimerColors": int(s.custom_timer_colors),
            "customTimerColorLevel": round(s.custom_timer_color_level, 3),
            "sidebarCollapsed": int(s.sidebar_collapsed),
            "appearanceMode": s.appearance_mode,
            "customColors": dict(s.custom_colors),
            "synced": int(s.synced),
            "sessionActive": int(s.session_active),
            "firstCardFree": int(s.first_card_free),
            "phase": s.phase,
            "phaseStartEpochMs": s.phase_start_epoch_ms,
            "phaseLimitMs": s.phase_limit_ms,
            "answerShown": int(s.answer_shown),
            "currentCardIndex": s.current_card_index,
            "currentCardId": s.current_card_id,
            "deckName": s.deck_name,
            "currentCardFlag": s.current_card_flag,
            "previousCardFlag": s.previous_card_flag,
            "answeredCards": s.answered_cards,
            "skippedCards": s.skipped_cards,
            "score": s.score,
            "streak": s.streak,
            "streakMultiplier": round(s.streak_multiplier, 2),
            "paused": int(s.paused),
            "pausedRemainingMs": s.paused_remaining_ms,
            "failureVisualActive": int(s.failure_visual_active),
            "lastSatelliteColor": s.last_satellite_color,
            "satelliteColors": s.satellite_colors,
            "lastEventType": s.last_event_type,
            "lastEventText": s.last_event_text,
            "eventNonce": s.event_nonce,
            "questionLimitMs": s.question_limit_ms,
            "reviewLimitMs": s.review_limit_ms,
            "totalPauseMs": self.current_round_pause_ms(),
            "timeDrainFlag": s.time_drain_flag,
            "reviewLaterFlag": s.review_later_flag,
        }

    def hard_reset(self) -> None:
        enabled = self.state.enabled
        visuals_enabled = self.state.visuals_enabled
        show_card_timer = self.state.show_card_timer
        custom_timer_colors = self.state.custom_timer_colors
        custom_timer_color_level = self.state.custom_timer_color_level
        sidebar_collapsed = self.state.sidebar_collapsed
        appearance_mode = self.state.appearance_mode
        custom_colors = dict(self.state.custom_colors)
        question_limit_ms = self.state.question_limit_ms
        review_limit_ms = self.state.review_limit_ms
        time_drain_flag = self.state.time_drain_flag
        review_later_flag = self.state.review_later_flag
        self.state = CompanionState()
        self.card = CardRuntime()
        self.state.enabled = enabled
        self.state.visuals_enabled = visuals_enabled
        self.state.show_card_timer = show_card_timer
        self.state.custom_timer_colors = custom_timer_colors
        self.state.custom_timer_color_level = custom_timer_color_level
        self.state.sidebar_collapsed = sidebar_collapsed
        self.state.appearance_mode = appearance_mode
        self.state.custom_colors = custom_colors
        self.state.question_limit_ms = question_limit_ms
        self.state.review_limit_ms = review_limit_ms
        self.state.time_drain_flag = time_drain_flag
        self.state.review_later_flag = review_later_flag
        self._last_review_metrics = None
        self._publish("reset", "Run reset.")

    def reset_settings_to_defaults(self) -> str:
        s = self.state
        s.question_limit_ms = ANSWER_LIMIT_MS
        s.review_limit_ms = REVIEW_LIMIT_MS
        s.time_drain_flag = 2
        s.review_later_flag = 4
        s.visuals_enabled = True
        s.show_card_timer = True
        s.custom_timer_colors = False
        s.custom_timer_color_level = 0.0
        s.sidebar_collapsed = False
        s.appearance_mode = "midnight"
        s.custom_colors = {}

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = s.question_limit_ms if s.visuals_enabled else 0
        elif s.phase == "answer":
            s.phase_limit_ms = s.review_limit_ms if s.visuals_enabled else 0

        self._publish("settings", "Settings reset to defaults.")
        return "settings"

    def set_enabled(self, enabled: bool) -> Optional[str]:
        s = self.state
        next_enabled = bool(enabled)
        if s.enabled == next_enabled:
            return None
        s.enabled = next_enabled
        self._clear_pause_state(accumulate_active=True)
        s.phase = "idle"
        s.phase_start_epoch_ms = 0
        s.phase_limit_ms = 0
        s.answer_shown = False
        s.timeout_phase_latch = ""
        self.card = CardRuntime()
        if next_enabled:
            self._publish("enabled", "Speed Streak turned on.")
            return "enabled"
        self._publish("disabled", "Speed Streak turned off.")
        return "disabled"

    def sync_on_question(self, *, card_id: str, deck_name: str, card_flag: int = 0) -> None:
        s = self.state
        if s.current_card_index < 1:
            s.current_card_index = 1
        s.previous_card_flag = s.current_card_flag
        s.current_card_id = card_id
        s.deck_name = deck_name
        s.current_card_flag = int(card_flag or 0)
        s.synced = True
        s.session_active = True
        s.answer_shown = False
        s.first_card_free = True
        s.failure_visual_active = False
        self.begin_question_phase(is_free=True)
        self._publish("sync", "Synced on question side. First card is free.")

    def sync_visible_question_surface(self, *, card_id: str, deck_name: str, card_flag: int = 0) -> str:
        s = self.state
        if not s.synced and s.enabled:
            self.sync_on_question(card_id=card_id, deck_name=deck_name, card_flag=card_flag)
            return "sync"

        if not s.synced:
            s.synced = True
            s.session_active = True
            if s.current_card_index < 1:
                s.current_card_index = 1

        previous_card_id = str(s.current_card_id or "")
        s.previous_card_flag = s.current_card_flag
        s.current_card_id = card_id
        s.deck_name = deck_name
        s.current_card_flag = int(card_flag or 0)
        s.synced = True
        s.session_active = True
        s.answer_shown = False
        s.first_card_free = False
        s.failure_visual_active = False
        s.skip_pending = False

        if not s.enabled:
            s.phase = "idle"
            s.phase_start_epoch_ms = 0
            s.phase_limit_ms = 0
            self._clear_pause_state(accumulate_active=True)
            s.timeout_phase_latch = ""
            self.card = CardRuntime()
            self._publish("question-idle", "Question surface synced while off.")
            return "question-idle"

        if s.current_card_index < 1:
            s.current_card_index = 1
        elif previous_card_id and previous_card_id != card_id:
            s.current_card_index += 1

        self.begin_question_phase(is_free=False)
        self._publish("question", "Question surface synced.")
        return "question"

    def sync_visible_answer_surface(self, *, card_id: str, deck_name: str, card_flag: int = 0) -> str:
        s = self.state
        if not s.synced:
            s.synced = True
            s.session_active = True
            if s.current_card_index < 1:
                s.current_card_index = 1

        s.previous_card_flag = s.current_card_flag
        s.current_card_id = card_id
        s.deck_name = deck_name
        s.current_card_flag = int(card_flag or 0)
        s.answer_shown = True
        s.first_card_free = False
        s.failure_visual_active = False
        s.skip_pending = False

        if not s.enabled:
            s.phase = "idle"
            s.phase_start_epoch_ms = 0
            s.phase_limit_ms = 0
            self._clear_pause_state(accumulate_active=True)
            s.timeout_phase_latch = ""
            self.card = CardRuntime()
            self._publish("answer-idle", "Answer surface synced while off.")
            return "answer-idle"

        question_elapsed_ms = 0
        if s.phase == "question" and s.phase_start_epoch_ms > 0:
            question_elapsed_ms = self._phase_elapsed_ms()

        self.card = CardRuntime(question_elapsed_ms=question_elapsed_ms, question_free=False, answer_elapsed_ms=0)
        self.begin_answer_phase()
        self._publish("show-answer", "Answer surface synced.")
        return "reveal"

    def on_question_shown(self, *, card_id: str, deck_name: str, card_flag: int = 0) -> Optional[str]:
        s = self.state
        s.previous_card_flag = s.current_card_flag
        s.current_card_id = card_id
        s.deck_name = deck_name
        s.current_card_flag = int(card_flag or 0)

        if not s.synced:
            self.sync_on_question(card_id=card_id, deck_name=deck_name, card_flag=card_flag)
            return "sync"

        if s.skip_pending:
            s.skip_pending = False
            if s.current_card_index < 1:
                s.current_card_index = 1
            else:
                s.current_card_index += 1
            self.begin_question_phase(is_free=False)
            self._publish("question", "Next question started.")
            return "question"

        if s.phase == "idle":
            self.begin_question_phase(is_free=False)
            self._publish("question", "Question armed.")
            return "question"

        if s.phase != "question" or s.answer_shown:
            self._advance_to_next_question("question", "Next question started.")
            return "question"

        return None

    def on_flag_changed(self, *, card_flag: int) -> Optional[str]:
        s = self.state
        next_flag = int(card_flag or 0)
        if next_flag == s.current_card_flag:
            return None
        previous_flag = s.current_card_flag
        s.previous_card_flag = previous_flag
        s.current_card_flag = next_flag
        if s.review_later_flag > 0 and previous_flag != s.review_later_flag and next_flag == s.review_later_flag:
            self._publish("review-later-added", "Review Later")
            return "review-later-added"
        if s.review_later_flag > 0 and previous_flag == s.review_later_flag and next_flag != s.review_later_flag:
            self._publish("review-later-removed", "Removed from 'Review Later'")
            return "review-later-removed"
        self._publish("flag-change", f"Flag changed to {next_flag}.")
        return "flag-change"

    def on_answer_shown(self) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.synced or s.phase != "question":
            return None

        self.card.question_elapsed_ms = self._phase_elapsed_ms()

        s.answer_shown = True
        s.first_card_free = False
        self.begin_answer_phase()
        text = "Answer revealed on first synced free card." if self.card.question_free else "Answer revealed."
        self._publish("show-answer", text)
        return "reveal"

    def on_skip(self) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.synced:
            return None
        s.skipped_cards += 1
        s.skip_pending = True
        s.phase = "idle"
        s.phase_start_epoch_ms = 0
        s.phase_limit_ms = 0
        s.answer_shown = False
        self._clear_pause_state(accumulate_active=True)
        s.timeout_phase_latch = ""
        self.card = CardRuntime()
        self._publish("skip", "Card buried / skipped.")
        return "skip"

    def on_rate(self, ease: int) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.synced or s.phase != "answer" or s.paused:
            return None

        rating_name = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}.get(ease, "Good")
        answer_elapsed_ms = self._phase_elapsed_ms()
        total_active_ms = max(0, self.card.question_elapsed_ms + answer_elapsed_ms)
        s.answered_cards += 1
        s.failure_visual_active = False

        if ease == 1:
            event_type = "again"
            color = "red"
            base_points = 1
        elif ease == 2:
            event_type = "hard"
            color = "yellow"
            base_points = 2
        elif ease == 3:
            event_type = "good"
            color = "green"
            base_points = 3
        else:
            event_type = "easy"
            color = "blue"
            base_points = 4

        if s.visuals_enabled:
            s.streak += 1
            multiplier = self._multiplier_for_streak(s.streak)
            s.streak_multiplier = multiplier
            s.last_satellite_color = color
            s.satellite_colors.append(color)
            reward = max(1, round(base_points * multiplier))
            s.score += reward
            event_text = f"{rating_name}: +{reward} score | streak {s.streak} | x{multiplier:.2f}"
        else:
            s.streak = 0
            s.streak_multiplier = 1.0
            s.failure_visual_active = False
            s.last_satellite_color = color
            s.satellite_colors = []
            event_text = f"{rating_name}: vibration-only mode"
        self._last_review_metrics = {
            "card_id": int(s.current_card_id or 0),
            "deck_name": s.deck_name,
            "active_ms": total_active_ms,
            "ease": int(ease),
            "correct": int(ease != 1),
        }
        self._advance_to_next_question(event_type, event_text)
        return event_type

    def capture_review_undo_snapshot(self) -> ReviewUndoSnapshot:
        return ReviewUndoSnapshot(
            state=deepcopy(self.state),
            card=deepcopy(self.card),
            last_review_metrics=deepcopy(self._last_review_metrics),
        )

    def commit_review_undo_snapshot(self, snapshot: ReviewUndoSnapshot) -> None:
        self._review_undo_stack.append(snapshot)

    def discard_review_undo_snapshot(self, snapshot: ReviewUndoSnapshot) -> None:
        self.state = deepcopy(snapshot.state)
        self.card = deepcopy(snapshot.card)
        self._last_review_metrics = deepcopy(snapshot.last_review_metrics)

    def undo_last_review(self) -> bool:
        if not self._review_undo_stack:
            return False
        snapshot = self._review_undo_stack.pop()
        self.discard_review_undo_snapshot(snapshot)
        self._publish("undo", "Last review undone.")
        return True

    def begin_question_phase(self, *, is_free: bool) -> None:
        s = self.state
        self._clear_pause_state(accumulate_active=True)
        self.card = CardRuntime(question_elapsed_ms=0, question_free=is_free, answer_elapsed_ms=0)
        s.phase = "question"
        s.phase_start_epoch_ms = now_epoch_ms()
        s.phase_limit_ms = 0 if is_free or not s.visuals_enabled else s.question_limit_ms
        s.answer_shown = False
        s.first_card_free = is_free
        s.session_active = True
        s.skip_pending = False
        s.timeout_phase_latch = ""

    def begin_answer_phase(self) -> None:
        s = self.state
        self._clear_pause_state(accumulate_active=True)
        s.phase = "answer"
        s.phase_start_epoch_ms = now_epoch_ms()
        s.phase_limit_ms = s.review_limit_ms if s.visuals_enabled else 0
        s.timeout_phase_latch = ""

    def toggle_pause(self) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.visuals_enabled or not s.synced or s.phase == "idle":
            return None
        if s.phase_limit_ms <= 0:
            return None

        if s.paused:
            s.paused = False
            if s.paused_remaining_ms > 0:
                s.phase_start_epoch_ms = now_epoch_ms() - (s.phase_limit_ms - s.paused_remaining_ms)
            if s.pause_started_epoch_ms > 0:
                s.total_pause_ms += max(0, now_epoch_ms() - s.pause_started_epoch_ms)
            s.paused_remaining_ms = 0
            s.pause_started_epoch_ms = 0
            self._publish("resume", "Timer resumed.")
            return "resume"

        elapsed = max(0, now_epoch_ms() - s.phase_start_epoch_ms)
        s.paused_remaining_ms = max(0, s.phase_limit_ms - elapsed)
        s.paused = True
        s.pause_started_epoch_ms = now_epoch_ms()
        self._publish("pause", "Timer paused.")
        return "pause"

    def current_round_pause_ms(self) -> int:
        s = self.state
        total = int(s.total_pause_ms)
        if s.paused and s.pause_started_epoch_ms > 0:
            total += max(0, now_epoch_ms() - s.pause_started_epoch_ms)
        return total

    def take_last_review_metrics(self) -> Optional[Dict[str, Any]]:
        metrics = self._last_review_metrics
        self._last_review_metrics = None
        return metrics

    def update_time_limits(
        self,
        *,
        question_seconds: float,
        answer_seconds: float,
        time_drain_flag: int | None = None,
        review_later_flag: int | None = None,
        visuals_enabled: bool | None = None,
        show_card_timer: bool | None = None,
        custom_timer_colors: bool | None = None,
        custom_timer_color_level: float | None = None,
        sidebar_collapsed: bool | None = None,
        appearance_mode: str | None = None,
        custom_colors: dict[str, str] | None = None,
    ) -> Optional[str]:
        s = self.state
        question_ms = int(max(1, round(question_seconds * 1000)))
        answer_ms = int(max(1, round(answer_seconds * 1000)))
        s.question_limit_ms = question_ms
        s.review_limit_ms = answer_ms
        if time_drain_flag is not None:
            s.time_drain_flag = max(0, int(time_drain_flag))
        if review_later_flag is not None:
            s.review_later_flag = max(0, int(review_later_flag))
        if visuals_enabled is not None:
            s.visuals_enabled = bool(visuals_enabled)
        if show_card_timer is not None:
            s.show_card_timer = bool(show_card_timer)
        if custom_timer_colors is not None:
            s.custom_timer_colors = bool(custom_timer_colors)
        if custom_timer_color_level is not None:
            s.custom_timer_color_level = max(-1.0, min(1.0, float(custom_timer_color_level)))
        if sidebar_collapsed is not None:
            s.sidebar_collapsed = bool(sidebar_collapsed)
        if appearance_mode is not None:
            normalized = str(appearance_mode).strip().lower() or "midnight"
            if normalized == "default":
                normalized = "classic"
            s.appearance_mode = normalized
        if custom_colors is not None:
            s.custom_colors = self._normalize_custom_colors(custom_colors)

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = s.question_limit_ms if s.visuals_enabled else 0
        elif s.phase == "answer":
            s.phase_limit_ms = s.review_limit_ms if s.visuals_enabled else 0

        if not s.visuals_enabled:
            self._clear_pause_state(accumulate_active=True)
            s.streak = 0
            s.streak_multiplier = 1.0
            s.failure_visual_active = False
            s.satellite_colors = []

        self._publish(
            "settings",
            f"Timers updated: question {question_seconds:.1f}s, answer {answer_seconds:.1f}s, time drain flag {s.time_drain_flag}, review later flag {s.review_later_flag}, visuals {'on' if s.visuals_enabled else 'off'}, appearance {s.appearance_mode}.",
        )
        return "settings"

    def _normalize_custom_colors(self, custom_colors: dict[str, str]) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for key in COLOR_KEYS:
            value = str(custom_colors.get(key, "") or "").strip()
            if not value:
                continue
            if not HEX_COLOR_RE.match(value):
                continue
            if len(value) == 4:
                value = "#" + "".join(ch * 2 for ch in value[1:])
            normalized[key] = value.lower()
        return normalized

    def check_timeout(self) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.visuals_enabled or not s.synced or s.phase == "idle":
            return None
        if s.phase_limit_ms <= 0 or s.phase_start_epoch_ms <= 0:
            return None
        if s.paused:
            return None

        phase_key = f"{s.phase}:{s.phase_start_epoch_ms}"
        if s.timeout_phase_latch == phase_key:
            return None

        elapsed = max(0, now_epoch_ms() - s.phase_start_epoch_ms)
        if elapsed < s.phase_limit_ms:
            return None

        s.timeout_phase_latch = phase_key
        s.streak = 0
        s.streak_multiplier = 1.0
        s.failure_visual_active = True
        s.satellite_colors = []
        self._publish("timeout", "Timeout: streak lost.")
        return "timeout"

    def _advance_to_next_question(self, event_type: str, event_text: str) -> None:
        s = self.state
        if s.current_card_index < 1:
            s.current_card_index = 1
        else:
            s.current_card_index += 1

        self.begin_question_phase(is_free=False)
        self._publish(event_type, event_text)

    def _publish(self, event_type: str, event_text: str) -> None:
        s = self.state
        s.last_event_type = event_type
        s.last_event_text = event_text
        s.event_nonce += 1

    def _multiplier_for_streak(self, streak: int) -> float:
        return 1.0 + min(4.0, streak * 0.08)

    def _phase_elapsed_ms(self) -> int:
        s = self.state
        if s.phase_start_epoch_ms <= 0:
            return 0
        if s.paused and s.phase_limit_ms > 0:
            return max(0, s.phase_limit_ms - s.paused_remaining_ms)
        return max(0, now_epoch_ms() - s.phase_start_epoch_ms)

    def _clear_pause_state(self, *, accumulate_active: bool) -> None:
        s = self.state
        if accumulate_active and s.paused and s.pause_started_epoch_ms > 0:
            s.total_pause_ms += max(0, now_epoch_ms() - s.pause_started_epoch_ms)
        s.paused = False
        s.paused_remaining_ms = 0
        s.pause_started_epoch_ms = 0
