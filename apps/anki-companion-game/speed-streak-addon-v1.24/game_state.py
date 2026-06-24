from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
import re
import time
from typing import Any, Dict, Optional

from .feedback_catalog import (
    DEFAULT_AUDIO_ENABLED,
    DEFAULT_AUDIO_FILE,
    default_audio_event_files,
    default_haptic_event_patterns,
    normalize_audio_event_files,
    normalize_haptic_controller_profile,
    normalize_haptic_event_patterns,
)


ANSWER_LIMIT_MS = 12_000
REVIEW_LIMIT_MS = 8_000
COLOR_KEYS = ("core", "red", "yellow", "green", "blue")
HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
TIMER_POLICY_NORMAL = "normal"
TIMER_POLICY_EXTRA_TIME = "extra_time"
TIMER_POLICY_NO_TIMEOUT = "no_timeout"


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
    audio_enabled: bool = DEFAULT_AUDIO_ENABLED
    selected_audio_file: str = DEFAULT_AUDIO_FILE
    audio_event_files: dict[str, str] = field(default_factory=default_audio_event_files)
    haptics_enabled: bool = True
    haptic_controller_profile: str = "standard"
    haptic_event_patterns: dict[str, str] = field(default_factory=default_haptic_event_patterns)
    visuals_enabled: bool = True
    show_card_timer: bool = True
    orbit_animation_enabled: bool = True
    reduced_motion_enabled: bool = False
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
    pause_count_started_epoch_ms: int = 0
    pause_origin: str = ""
    time_drain_flag: int = 2
    time_drain_review_last: bool = False
    review_later_flag: int = 4
    current_timer_policy_source: str = ""
    current_timer_policy_mode: str = TIMER_POLICY_NORMAL
    current_timer_policy_question_extra_ms: int = 0
    current_timer_policy_answer_extra_ms: int = 0
    current_timer_policy_question_limit_ms: int = -1
    current_timer_policy_answer_limit_ms: int = -1


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

    def _capture_user_preferences(self) -> Dict[str, Any]:
        s = self.state
        return {
            "enabled": bool(s.enabled),
            "audio_enabled": bool(s.audio_enabled),
            "selected_audio_file": str(s.selected_audio_file),
            "audio_event_files": dict(s.audio_event_files),
            "haptics_enabled": bool(s.haptics_enabled),
            "haptic_controller_profile": str(s.haptic_controller_profile),
            "haptic_event_patterns": dict(s.haptic_event_patterns),
            "visuals_enabled": bool(s.visuals_enabled),
            "show_card_timer": bool(s.show_card_timer),
            "orbit_animation_enabled": bool(s.orbit_animation_enabled),
            "reduced_motion_enabled": bool(s.reduced_motion_enabled),
            "custom_timer_colors": bool(s.custom_timer_colors),
            "custom_timer_color_level": float(s.custom_timer_color_level),
            "sidebar_collapsed": bool(s.sidebar_collapsed),
            "appearance_mode": str(s.appearance_mode),
            "custom_colors": dict(s.custom_colors),
            "question_limit_ms": int(s.question_limit_ms),
            "review_limit_ms": int(s.review_limit_ms),
            "time_drain_flag": int(s.time_drain_flag),
            "time_drain_review_last": bool(s.time_drain_review_last),
            "review_later_flag": int(s.review_later_flag),
            "current_timer_policy_source": str(s.current_timer_policy_source),
            "current_timer_policy_mode": str(s.current_timer_policy_mode),
            "current_timer_policy_question_extra_ms": int(s.current_timer_policy_question_extra_ms),
            "current_timer_policy_answer_extra_ms": int(s.current_timer_policy_answer_extra_ms),
            "current_timer_policy_question_limit_ms": int(s.current_timer_policy_question_limit_ms),
            "current_timer_policy_answer_limit_ms": int(s.current_timer_policy_answer_limit_ms),
        }

    def _restore_user_preferences(self, preferences: Dict[str, Any]) -> None:
        s = self.state
        s.enabled = bool(preferences.get("enabled", s.enabled))
        s.audio_enabled = bool(preferences.get("audio_enabled", s.audio_enabled))
        s.selected_audio_file = str(preferences.get("selected_audio_file", s.selected_audio_file))
        s.audio_event_files = normalize_audio_event_files(
            preferences.get("audio_event_files", s.audio_event_files),
            fallback_file=s.selected_audio_file,
        )
        s.haptics_enabled = bool(preferences.get("haptics_enabled", s.haptics_enabled))
        s.haptic_controller_profile = normalize_haptic_controller_profile(
            preferences.get("haptic_controller_profile", s.haptic_controller_profile)
        )
        s.haptic_event_patterns = normalize_haptic_event_patterns(
            preferences.get("haptic_event_patterns", s.haptic_event_patterns)
        )
        s.visuals_enabled = bool(preferences.get("visuals_enabled", s.visuals_enabled))
        s.show_card_timer = bool(preferences.get("show_card_timer", s.show_card_timer))
        s.orbit_animation_enabled = bool(preferences.get("orbit_animation_enabled", s.orbit_animation_enabled))
        s.reduced_motion_enabled = bool(preferences.get("reduced_motion_enabled", s.reduced_motion_enabled))
        s.custom_timer_colors = bool(preferences.get("custom_timer_colors", s.custom_timer_colors))
        s.custom_timer_color_level = max(
            -1.0,
            min(1.0, float(preferences.get("custom_timer_color_level", s.custom_timer_color_level))),
        )
        s.sidebar_collapsed = bool(preferences.get("sidebar_collapsed", s.sidebar_collapsed))
        s.appearance_mode = str(preferences.get("appearance_mode", s.appearance_mode) or "midnight")
        s.custom_colors = self._normalize_custom_colors(preferences.get("custom_colors", s.custom_colors))
        s.question_limit_ms = int(max(1, preferences.get("question_limit_ms", s.question_limit_ms)))
        s.review_limit_ms = int(max(1, preferences.get("review_limit_ms", s.review_limit_ms)))
        s.time_drain_flag = max(0, int(preferences.get("time_drain_flag", s.time_drain_flag)))
        s.time_drain_review_last = bool(preferences.get("time_drain_review_last", s.time_drain_review_last))
        s.review_later_flag = max(0, int(preferences.get("review_later_flag", s.review_later_flag)))
        s.current_timer_policy_source = str(preferences.get("current_timer_policy_source", s.current_timer_policy_source) or "")
        s.current_timer_policy_mode = self._normalize_timer_policy_mode(
            preferences.get("current_timer_policy_mode", s.current_timer_policy_mode)
        )
        s.current_timer_policy_question_extra_ms = max(
            0,
            int(preferences.get("current_timer_policy_question_extra_ms", s.current_timer_policy_question_extra_ms) or 0),
        )
        s.current_timer_policy_answer_extra_ms = max(
            0,
            int(preferences.get("current_timer_policy_answer_extra_ms", s.current_timer_policy_answer_extra_ms) or 0),
        )

        if not s.haptics_enabled and not s.visuals_enabled:
            s.visuals_enabled = True

        if s.phase == "question":
            s.phase_limit_ms = self._question_phase_limit_ms(is_free=s.first_card_free)
        elif s.phase == "answer":
            s.phase_limit_ms = self._answer_phase_limit_ms()
        else:
            s.phase_limit_ms = 0

        if not s.visuals_enabled:
            self._clear_pause_state(accumulate_active=True)
            s.streak = 0
            s.streak_multiplier = 1.0
            s.failure_visual_active = False
            s.satellite_colors = []
        elif s.paused and s.phase_limit_ms > 0:
            s.paused_remaining_ms = min(max(0, s.paused_remaining_ms), s.phase_limit_ms)
        else:
            s.paused_remaining_ms = max(0, s.paused_remaining_ms)

    def export(self) -> Dict[str, Any]:
        s = self.state
        return {
            "version": 8,
            "enabled": int(s.enabled),
            "audioEnabled": int(s.audio_enabled),
            "selectedAudioFile": s.selected_audio_file,
            "audioEventFiles": dict(s.audio_event_files),
            "hapticsEnabled": int(s.haptics_enabled),
            "hapticControllerProfile": str(s.haptic_controller_profile),
            "hapticEventPatterns": dict(s.haptic_event_patterns),
            "visualsEnabled": int(s.visuals_enabled),
            "showCardTimer": int(s.show_card_timer),
            "orbitAnimationEnabled": int(s.orbit_animation_enabled),
            "reducedMotion": int(s.reduced_motion_enabled),
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
            "timeDrainReviewLast": int(s.time_drain_review_last),
            "reviewLaterFlag": s.review_later_flag,
            "timerPolicySource": s.current_timer_policy_source,
            "timerPolicyMode": s.current_timer_policy_mode,
            "timerPolicyQuestionExtraMs": s.current_timer_policy_question_extra_ms,
            "timerPolicyAnswerExtraMs": s.current_timer_policy_answer_extra_ms,
            "timerPolicyQuestionLimitMs": s.current_timer_policy_question_limit_ms,
            "timerPolicyAnswerLimitMs": s.current_timer_policy_answer_limit_ms,
        }

    def export_runtime(self) -> Dict[str, Any]:
        s = self.state
        return {
            "synced": bool(s.synced),
            "session_active": bool(s.session_active),
            "first_card_free": bool(s.first_card_free),
            "phase": str(s.phase),
            "phase_start_epoch_ms": int(s.phase_start_epoch_ms),
            "phase_limit_ms": int(s.phase_limit_ms),
            "answer_shown": bool(s.answer_shown),
            "current_card_index": int(s.current_card_index),
            "current_card_id": str(s.current_card_id),
            "deck_name": str(s.deck_name),
            "current_card_flag": int(s.current_card_flag),
            "previous_card_flag": int(s.previous_card_flag),
            "answered_cards": int(s.answered_cards),
            "skipped_cards": int(s.skipped_cards),
            "score": int(s.score),
            "streak": int(s.streak),
            "streak_multiplier": float(s.streak_multiplier),
            "paused": bool(s.paused),
            "paused_remaining_ms": int(s.paused_remaining_ms),
            "failure_visual_active": bool(s.failure_visual_active),
            "last_satellite_color": str(s.last_satellite_color),
            "satellite_colors": list(s.satellite_colors),
            "timeout_phase_latch": str(s.timeout_phase_latch),
            "skip_pending": bool(s.skip_pending),
            "total_pause_ms": int(s.total_pause_ms),
            "pause_started_epoch_ms": int(s.pause_started_epoch_ms),
            "pause_count_started_epoch_ms": int(s.pause_count_started_epoch_ms),
            "pause_origin": str(s.pause_origin),
            "current_timer_policy_source": str(s.current_timer_policy_source),
            "current_timer_policy_mode": str(s.current_timer_policy_mode),
            "current_timer_policy_question_extra_ms": int(s.current_timer_policy_question_extra_ms),
            "current_timer_policy_answer_extra_ms": int(s.current_timer_policy_answer_extra_ms),
            "card": {
                "question_elapsed_ms": int(self.card.question_elapsed_ms),
                "question_free": bool(self.card.question_free),
                "answer_elapsed_ms": int(self.card.answer_elapsed_ms),
            },
        }

    def restore_runtime(self, runtime: Dict[str, Any]) -> None:
        if not isinstance(runtime, dict):
            return
        s = self.state
        phase = str(runtime.get("phase", "idle") or "idle")
        if phase not in {"idle", "question", "answer"}:
            phase = "idle"
        s.synced = bool(runtime.get("synced", False))
        s.session_active = bool(runtime.get("session_active", False))
        s.first_card_free = bool(runtime.get("first_card_free", False))
        s.phase = phase
        s.phase_start_epoch_ms = max(0, int(runtime.get("phase_start_epoch_ms", 0) or 0))
        s.phase_limit_ms = max(0, int(runtime.get("phase_limit_ms", 0) or 0))
        s.answer_shown = bool(runtime.get("answer_shown", False))
        s.current_card_index = max(0, int(runtime.get("current_card_index", 0) or 0))
        s.current_card_id = str(runtime.get("current_card_id", "") or "")
        s.deck_name = str(runtime.get("deck_name", "") or "")
        s.current_card_flag = max(0, int(runtime.get("current_card_flag", 0) or 0))
        s.previous_card_flag = max(0, int(runtime.get("previous_card_flag", 0) or 0))
        s.answered_cards = max(0, int(runtime.get("answered_cards", 0) or 0))
        s.skipped_cards = max(0, int(runtime.get("skipped_cards", 0) or 0))
        s.score = max(0, int(runtime.get("score", 0) or 0))
        s.streak = max(0, int(runtime.get("streak", 0) or 0))
        s.streak_multiplier = max(1.0, float(runtime.get("streak_multiplier", 1.0) or 1.0))
        s.paused = bool(runtime.get("paused", False))
        s.paused_remaining_ms = max(0, int(runtime.get("paused_remaining_ms", 0) or 0))
        s.failure_visual_active = bool(runtime.get("failure_visual_active", False))
        s.last_satellite_color = str(runtime.get("last_satellite_color", "green") or "green")
        raw_colors = runtime.get("satellite_colors", [])
        s.satellite_colors = [str(color) for color in raw_colors] if isinstance(raw_colors, list) else []
        s.timeout_phase_latch = str(runtime.get("timeout_phase_latch", "") or "")
        s.skip_pending = bool(runtime.get("skip_pending", False))
        s.total_pause_ms = max(0, int(runtime.get("total_pause_ms", 0) or 0))
        s.pause_started_epoch_ms = max(0, int(runtime.get("pause_started_epoch_ms", 0) or 0))
        s.pause_count_started_epoch_ms = max(0, int(runtime.get("pause_count_started_epoch_ms", 0) or 0))
        s.pause_origin = str(runtime.get("pause_origin", "") or "")
        s.current_timer_policy_source = str(runtime.get("current_timer_policy_source", "") or "")
        s.current_timer_policy_mode = self._normalize_timer_policy_mode(runtime.get("current_timer_policy_mode", TIMER_POLICY_NORMAL))
        s.current_timer_policy_question_extra_ms = max(0, int(runtime.get("current_timer_policy_question_extra_ms", 0) or 0))
        s.current_timer_policy_answer_extra_ms = max(0, int(runtime.get("current_timer_policy_answer_extra_ms", 0) or 0))
        s.current_timer_policy_question_limit_ms = int(runtime.get("current_timer_policy_question_limit_ms", -1))
        s.current_timer_policy_answer_limit_ms = int(runtime.get("current_timer_policy_answer_limit_ms", -1))
        raw_card = runtime.get("card", {})
        if isinstance(raw_card, dict):
            self.card = CardRuntime(
                question_elapsed_ms=max(0, int(raw_card.get("question_elapsed_ms", 0) or 0)),
                question_free=bool(raw_card.get("question_free", False)),
                answer_elapsed_ms=max(0, int(raw_card.get("answer_elapsed_ms", 0) or 0)),
            )
        if s.phase == "idle" or not s.current_card_id:
            s.phase = "idle"
            s.phase_start_epoch_ms = 0
            s.phase_limit_ms = 0
            s.paused = False
            s.paused_remaining_ms = 0

    def hard_reset(self) -> None:
        preferences = self._capture_user_preferences()
        self.state = CompanionState()
        self.card = CardRuntime()
        self._restore_user_preferences(preferences)
        self._last_review_metrics = None
        self._publish("reset", "Run reset.")

    def reset_settings_to_defaults(self) -> str:
        s = self.state
        s.question_limit_ms = ANSWER_LIMIT_MS
        s.review_limit_ms = REVIEW_LIMIT_MS
        s.time_drain_flag = 2
        s.time_drain_review_last = False
        s.review_later_flag = 4
        s.audio_enabled = DEFAULT_AUDIO_ENABLED
        s.selected_audio_file = DEFAULT_AUDIO_FILE
        s.audio_event_files = default_audio_event_files()
        s.haptics_enabled = True
        s.haptic_controller_profile = "standard"
        s.haptic_event_patterns = default_haptic_event_patterns()
        s.visuals_enabled = True
        s.show_card_timer = True
        s.orbit_animation_enabled = True
        s.reduced_motion_enabled = False
        s.custom_timer_colors = False
        s.custom_timer_color_level = 0.0
        s.sidebar_collapsed = False
        s.appearance_mode = "midnight"
        s.custom_colors = {}
        self.set_current_timer_policy()

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = self._question_phase_limit_ms(is_free=False)
        elif s.phase == "answer":
            s.phase_limit_ms = self._answer_phase_limit_ms()

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

    def sync_on_question(
        self,
        *,
        card_id: str,
        deck_name: str,
        card_flag: int = 0,
        timer_policy: dict[str, Any] | None = None,
    ) -> None:
        s = self.state
        self.set_current_timer_policy(**(timer_policy or {}))
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

    def sync_visible_question_surface(
        self,
        *,
        card_id: str,
        deck_name: str,
        card_flag: int = 0,
        timer_policy: dict[str, Any] | None = None,
    ) -> str:
        s = self.state
        self.set_current_timer_policy(**(timer_policy or {}))
        if not s.synced and s.enabled:
            self.sync_on_question(card_id=card_id, deck_name=deck_name, card_flag=card_flag, timer_policy=timer_policy)
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

        if previous_card_id == card_id and s.phase == "question" and not s.answer_shown:
            self._publish("question", "Question surface re-synced.")
            return "question"

        self.begin_question_phase(is_free=False)
        self._publish("question", "Question surface synced.")
        return "question"

    def sync_visible_answer_surface(
        self,
        *,
        card_id: str,
        deck_name: str,
        card_flag: int = 0,
        timer_policy: dict[str, Any] | None = None,
    ) -> str:
        s = self.state
        if timer_policy is not None:
            self.set_current_timer_policy(**timer_policy)
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

        if previous_card_id == str(card_id) and s.phase == "answer":
            self._publish("show-answer", "Answer surface re-synced.")
            return "reveal"

        question_elapsed_ms = 0
        if s.phase == "question" and s.phase_start_epoch_ms > 0:
            question_elapsed_ms = self._phase_elapsed_ms()

        self.card = CardRuntime(question_elapsed_ms=question_elapsed_ms, question_free=False, answer_elapsed_ms=0)
        self.begin_answer_phase()
        self._publish("show-answer", "Answer surface synced.")
        return "reveal"

    def on_question_shown(
        self,
        *,
        card_id: str,
        deck_name: str,
        card_flag: int = 0,
        timer_policy: dict[str, Any] | None = None,
    ) -> Optional[str]:
        s = self.state
        self.set_current_timer_policy(**(timer_policy or {}))
        s.previous_card_flag = s.current_card_flag
        s.current_card_id = card_id
        s.deck_name = deck_name
        s.current_card_flag = int(card_flag or 0)

        if not s.synced:
            self.sync_on_question(card_id=card_id, deck_name=deck_name, card_flag=card_flag, timer_policy=timer_policy)
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
        preferences = self._capture_user_preferences()
        self.state = deepcopy(snapshot.state)
        self.card = deepcopy(snapshot.card)
        self._last_review_metrics = deepcopy(snapshot.last_review_metrics)
        self._restore_user_preferences(preferences)

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
        s.phase_limit_ms = self._question_phase_limit_ms(is_free=is_free)
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
        s.phase_limit_ms = self._answer_phase_limit_ms()
        s.timeout_phase_latch = ""

    def toggle_pause(self, *, count_in_stats: bool = True) -> Optional[str]:
        s = self.state
        if not s.enabled or not s.visuals_enabled or not s.synced or s.phase == "idle":
            return None
        if s.phase_limit_ms <= 0:
            return None

        if s.paused:
            s.paused = False
            if s.paused_remaining_ms > 0:
                s.phase_start_epoch_ms = now_epoch_ms() - (s.phase_limit_ms - s.paused_remaining_ms)
            self._accumulate_counted_pause_time()
            s.paused_remaining_ms = 0
            s.pause_started_epoch_ms = 0
            s.pause_count_started_epoch_ms = 0
            s.pause_origin = ""
            self._publish("resume", "Timer resumed.")
            return "resume"

        now_ms = now_epoch_ms()
        elapsed = max(0, now_ms - s.phase_start_epoch_ms)
        s.paused_remaining_ms = max(0, s.phase_limit_ms - elapsed)
        s.paused = True
        s.pause_started_epoch_ms = now_ms
        s.pause_count_started_epoch_ms = now_ms if count_in_stats else 0
        s.pause_origin = "manual" if count_in_stats else "non-review"
        self._publish("pause", "Timer paused.")
        return "pause"

    def current_round_pause_ms(self) -> int:
        s = self.state
        total = int(s.total_pause_ms)
        if s.paused and s.pause_count_started_epoch_ms > 0:
            total += max(0, now_epoch_ms() - s.pause_count_started_epoch_ms)
        return total

    def pause_counts_toward_stats(self) -> bool:
        s = self.state
        return bool(s.paused and s.pause_count_started_epoch_ms > 0)

    def set_pause_stat_tracking_active(self, active: bool) -> bool:
        s = self.state
        if not s.paused or s.pause_origin != "manual":
            return False
        if active:
            if s.pause_count_started_epoch_ms > 0:
                return False
            s.pause_count_started_epoch_ms = now_epoch_ms()
            return True
        if s.pause_count_started_epoch_ms <= 0:
            return False
        self._accumulate_counted_pause_time()
        return True

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
        time_drain_review_last: bool | None = None,
        review_later_flag: int | None = None,
        audio_enabled: bool | None = None,
        selected_audio_file: str | None = None,
        audio_event_files: dict[str, str] | None = None,
        visuals_enabled: bool | None = None,
        haptics_enabled: bool | None = None,
        haptic_controller_profile: str | None = None,
        haptic_event_patterns: dict[str, str] | None = None,
        show_card_timer: bool | None = None,
        orbit_animation_enabled: bool | None = None,
        reduced_motion_enabled: bool | None = None,
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
        if time_drain_review_last is not None:
            s.time_drain_review_last = bool(time_drain_review_last)
        if review_later_flag is not None:
            s.review_later_flag = max(0, int(review_later_flag))
        if audio_enabled is not None:
            s.audio_enabled = bool(audio_enabled)
        if selected_audio_file is not None:
            s.selected_audio_file = str(selected_audio_file or DEFAULT_AUDIO_FILE).strip()
        if audio_event_files is not None:
            s.audio_event_files = normalize_audio_event_files(audio_event_files, fallback_file=s.selected_audio_file)
        if visuals_enabled is not None:
            s.visuals_enabled = bool(visuals_enabled)
        if haptics_enabled is not None:
            s.haptics_enabled = bool(haptics_enabled)
        if haptic_controller_profile is not None:
            s.haptic_controller_profile = normalize_haptic_controller_profile(haptic_controller_profile)
        if haptic_event_patterns is not None:
            s.haptic_event_patterns = normalize_haptic_event_patterns(haptic_event_patterns)
        if show_card_timer is not None:
            s.show_card_timer = bool(show_card_timer)
        if orbit_animation_enabled is not None:
            s.orbit_animation_enabled = bool(orbit_animation_enabled)
        if reduced_motion_enabled is not None:
            s.reduced_motion_enabled = bool(reduced_motion_enabled)
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

        if not s.haptics_enabled and not s.visuals_enabled:
            s.visuals_enabled = True

        if s.phase == "question" and not s.first_card_free:
            s.phase_limit_ms = self._question_phase_limit_ms(is_free=False)
        elif s.phase == "answer":
            s.phase_limit_ms = self._answer_phase_limit_ms()

        if not s.visuals_enabled:
            self._clear_pause_state(accumulate_active=True)
            s.streak = 0
            s.streak_multiplier = 1.0
            s.failure_visual_active = False
            s.satellite_colors = []

        self._publish(
            "settings",
            f"Timers updated: question {question_seconds:.1f}s, answer {answer_seconds:.1f}s, time drain flag {s.time_drain_flag}, time drain review last {'on' if s.time_drain_review_last else 'off'}, review later flag {s.review_later_flag}, audio {'on' if s.audio_enabled else 'off'}, haptics {'on' if s.haptics_enabled else 'off'}, visuals {'on' if s.visuals_enabled else 'off'}, orbit animation {'on' if s.orbit_animation_enabled else 'off'}, reduced motion {'on' if s.reduced_motion_enabled else 'off'}, appearance {s.appearance_mode}.",
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
        if s.current_timer_policy_mode == TIMER_POLICY_NO_TIMEOUT:
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

    def set_current_timer_policy(
        self,
        *,
        source: str = "",
        mode: str = TIMER_POLICY_NORMAL,
        question_extra_ms: int = 0,
        answer_extra_ms: int = 0,
        question_limit_ms: int = -1,
        answer_limit_ms: int = -1,
    ) -> None:
        s = self.state
        s.current_timer_policy_source = str(source or "")[:80]
        s.current_timer_policy_mode = self._normalize_timer_policy_mode(mode)
        s.current_timer_policy_question_extra_ms = max(0, int(question_extra_ms or 0))
        s.current_timer_policy_answer_extra_ms = max(0, int(answer_extra_ms or 0))
        s.current_timer_policy_question_limit_ms = int(question_limit_ms)
        s.current_timer_policy_answer_limit_ms = int(answer_limit_ms)
        if s.phase == "question":
            s.phase_limit_ms = self._question_phase_limit_ms(is_free=s.first_card_free)
        elif s.phase == "answer":
            s.phase_limit_ms = self._answer_phase_limit_ms()

    def restart_current_phase_timer(self) -> None:
        s = self.state
        if s.phase not in {"question", "answer"}:
            return
        self._clear_pause_state(accumulate_active=True)
        s.phase_start_epoch_ms = now_epoch_ms()
        s.phase_limit_ms = (
            self._question_phase_limit_ms(is_free=s.first_card_free)
            if s.phase == "question"
            else self._answer_phase_limit_ms()
        )
        s.timeout_phase_latch = ""

    def _normalize_timer_policy_mode(self, value: object) -> str:
        normalized = str(value or TIMER_POLICY_NORMAL).strip().lower()
        if normalized in {TIMER_POLICY_EXTRA_TIME, TIMER_POLICY_NO_TIMEOUT}:
            return normalized
        return TIMER_POLICY_NORMAL

    def _question_phase_limit_ms(self, *, is_free: bool) -> int:
        s = self.state
        if is_free or not s.visuals_enabled:
            return 0
        if s.current_timer_policy_mode == TIMER_POLICY_NO_TIMEOUT:
            return 0
        if s.current_timer_policy_question_limit_ms >= 0:
            return int(s.current_timer_policy_question_limit_ms)
        return max(1, int(s.question_limit_ms) + int(s.current_timer_policy_question_extra_ms))

    def _answer_phase_limit_ms(self) -> int:
        s = self.state
        if not s.visuals_enabled:
            return 0
        if s.current_timer_policy_mode == TIMER_POLICY_NO_TIMEOUT:
            return 0
        if s.current_timer_policy_answer_limit_ms >= 0:
            return int(s.current_timer_policy_answer_limit_ms)
        return max(1, int(s.review_limit_ms) + int(s.current_timer_policy_answer_extra_ms))

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
        if accumulate_active:
            self._accumulate_counted_pause_time()
        s.paused = False
        s.paused_remaining_ms = 0
        s.pause_started_epoch_ms = 0
        s.pause_count_started_epoch_ms = 0
        s.pause_origin = ""

    def _accumulate_counted_pause_time(self) -> None:
        s = self.state
        if s.pause_count_started_epoch_ms <= 0:
            return
        s.total_pause_ms += max(0, now_epoch_ms() - s.pause_count_started_epoch_ms)
        s.pause_count_started_epoch_ms = 0
