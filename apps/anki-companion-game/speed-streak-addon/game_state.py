from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, Optional


ANSWER_LIMIT_MS = 12_000
REVIEW_LIMIT_MS = 8_000


def now_epoch_ms() -> int:
    return int(time.time() * 1000)


@dataclass
class CardRuntime:
    question_free: bool = False
    answer_elapsed_ms: int = 0


@dataclass
class CompanionState:
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
    time_drain_flag: int = 0
    review_later_flag: int = 0


@dataclass
class CompanionGameEngine:
    state: CompanionState = field(default_factory=CompanionState)
    card: CardRuntime = field(default_factory=CardRuntime)

    def export(self) -> Dict[str, Any]:
        s = self.state
        return {
            "version": 3,
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
            "totalPauseMs": s.total_pause_ms,
            "timeDrainFlag": s.time_drain_flag,
            "reviewLaterFlag": s.review_later_flag,
        }

    def hard_reset(self) -> None:
        question_limit_ms = self.state.question_limit_ms
        review_limit_ms = self.state.review_limit_ms
        time_drain_flag = self.state.time_drain_flag
        review_later_flag = self.state.review_later_flag
        self.state = CompanionState()
        self.card = CardRuntime()
        self.state.question_limit_ms = question_limit_ms
        self.state.review_limit_ms = review_limit_ms
        self.state.time_drain_flag = time_drain_flag
        self.state.review_later_flag = review_later_flag
        self._publish("reset", "Run reset.")

    def reset_settings_to_defaults(self) -> str:
        s = self.state
        s.question_limit_ms = ANSWER_LIMIT_MS
        s.review_limit_ms = REVIEW_LIMIT_MS
        s.time_drain_flag = 0
        s.review_later_flag = 0

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = s.question_limit_ms
        elif s.phase == "answer":
            s.phase_limit_ms = s.review_limit_ms

        self._publish("settings", "Settings reset to defaults.")
        return "settings"

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
        if not s.synced:
            self.sync_on_question(card_id=card_id, deck_name=deck_name, card_flag=card_flag)
            return "sync"

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
        self.card = CardRuntime(question_free=False, answer_elapsed_ms=0)
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
        if not s.synced or s.phase != "question":
            return None

        if self.card.question_free:
            self.card.answer_elapsed_ms = 0
        else:
            self.card.answer_elapsed_ms = max(0, now_epoch_ms() - s.phase_start_epoch_ms)

        s.answer_shown = True
        s.first_card_free = False
        self.begin_answer_phase()
        text = "Answer revealed on first synced free card." if self.card.question_free else "Answer revealed."
        self._publish("show-answer", text)
        return "reveal"

    def on_skip(self) -> Optional[str]:
        s = self.state
        if not s.synced:
            return None
        s.skipped_cards += 1
        s.skip_pending = True
        s.phase = "idle"
        s.phase_start_epoch_ms = 0
        s.phase_limit_ms = 0
        s.answer_shown = False
        s.paused = False
        s.paused_remaining_ms = 0
        s.timeout_phase_latch = ""
        self.card = CardRuntime()
        self._publish("skip", "Card buried / skipped.")
        return "skip"

    def on_rate(self, ease: int) -> Optional[str]:
        s = self.state
        if not s.synced or s.phase != "answer":
            return None

        rating_name = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}.get(ease, "Good")
        s.streak += 1
        s.answered_cards += 1
        s.failure_visual_active = False

        multiplier = self._multiplier_for_streak(s.streak)
        s.streak_multiplier = multiplier

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

        s.last_satellite_color = color
        s.satellite_colors.append(color)
        reward = max(1, round(base_points * multiplier))
        s.score += reward
        event_text = f"{rating_name}: +{reward} score | streak {s.streak} | x{multiplier:.2f}"
        self._advance_to_next_question(event_type, event_text)
        return event_type

    def begin_question_phase(self, *, is_free: bool) -> None:
        s = self.state
        self.card = CardRuntime(question_free=is_free, answer_elapsed_ms=0)
        s.phase = "question"
        s.phase_start_epoch_ms = now_epoch_ms()
        s.phase_limit_ms = 0 if is_free else s.question_limit_ms
        s.answer_shown = False
        s.first_card_free = is_free
        s.session_active = True
        s.skip_pending = False
        s.paused = False
        s.paused_remaining_ms = 0
        s.pause_started_epoch_ms = 0
        s.timeout_phase_latch = ""

    def begin_answer_phase(self) -> None:
        s = self.state
        s.phase = "answer"
        s.phase_start_epoch_ms = now_epoch_ms()
        s.phase_limit_ms = s.review_limit_ms
        s.paused = False
        s.paused_remaining_ms = 0
        s.pause_started_epoch_ms = 0
        s.timeout_phase_latch = ""

    def toggle_pause(self) -> Optional[str]:
        s = self.state
        if not s.synced or s.phase == "idle":
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

    def update_time_limits(
        self,
        *,
        question_seconds: float,
        answer_seconds: float,
        time_drain_flag: int | None = None,
        review_later_flag: int | None = None,
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

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = s.question_limit_ms
        elif s.phase == "answer":
            s.phase_limit_ms = s.review_limit_ms

        self._publish(
            "settings",
            f"Timers updated: question {question_seconds:.1f}s, answer {answer_seconds:.1f}s, time drain flag {s.time_drain_flag}, review later flag {s.review_later_flag}.",
        )
        return "settings"

    def check_timeout(self) -> Optional[str]:
        s = self.state
        if not s.synced or s.phase == "idle":
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
