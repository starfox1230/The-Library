from __future__ import annotations

from typing import Any


AUDIO_DIRECTORY_NAME = "Audio"
AUDIO_TRIMMED_DIRECTORY_NAME = "Audio_trimmed"
AUDIO_UPLOADS_DIRECTORY_NAME = "audio_uploads"
AUDIO_UPLOADS_MANIFEST_NAME = "uploaded_audio_order.json"
DEFAULT_AUDIO_ENABLED = False
DEFAULT_AUDIO_FILE = "kenney_ui-audio/Audio/click1.mp3"

HAPTIC_PATTERN_OFF = "off"
HAPTIC_CONTROLLER_PROFILE_STANDARD = "standard"
HAPTIC_CONTROLLER_PROFILE_STEAM = "steam_controller"

HAPTIC_CONTROLLER_PROFILE_OPTIONS: tuple[tuple[str, str], ...] = (
    (HAPTIC_CONTROLLER_PROFILE_STANDARD, "Standard / Xbox-style controller"),
    (HAPTIC_CONTROLLER_PROFILE_STEAM, "Steam Controller / Steam Input"),
)

HAPTIC_PATTERN_LIBRARY: dict[str, dict[str, Any]] = {
    "reveal": {
        "label": "Reveal Pulse",
        "description": "Short single pulse when the answer side appears.",
        "sequence": [
            {"duration": 90, "weak": 0.64, "strong": 1.0},
        ],
    },
    "again": {
        "label": "Again Double Pulse",
        "description": "Two stronger pulses for Again ratings.",
        "sequence": [
            {"duration": 80, "weak": 0.64, "strong": 0.88},
            {"duration": 55, "weak": 0.0, "strong": 0.0},
            {"duration": 80, "weak": 0.64, "strong": 0.94},
        ],
    },
    "hard": {
        "label": "Hard Tap",
        "description": "Single medium pulse for Hard ratings.",
        "sequence": [
            {"duration": 95, "weak": 0.36, "strong": 0.55},
        ],
    },
    "good": {
        "label": "Good Pulse",
        "description": "Single stronger pulse for Good ratings.",
        "sequence": [
            {"duration": 120, "weak": 0.8, "strong": 1.0},
        ],
    },
    "easy": {
        "label": "Easy Tap",
        "description": "Light single pulse for Easy ratings.",
        "sequence": [
            {"duration": 125, "weak": 0.34, "strong": 0.46},
        ],
    },
    "skip": {
        "label": "Skip Tap",
        "description": "Short light pulse when a card is buried or skipped.",
        "sequence": [
            {"duration": 80, "weak": 0.18, "strong": 0.30},
        ],
    },
    "sync": {
        "label": "Sync Tap",
        "description": "Short pulse when Speed Streak arms itself on a question card.",
        "sequence": [
            {"duration": 95, "weak": 0.20, "strong": 0.28},
        ],
    },
    "reset": {
        "label": "Reset Tap",
        "description": "Brief pulse when the run is reset.",
        "sequence": [
            {"duration": 120, "weak": 0.26, "strong": 0.40},
        ],
    },
    "bossStart": {
        "label": "Boss Start",
        "description": "Unused alternate pattern with a rising double pulse.",
        "sequence": [
            {"duration": 80, "weak": 0.34, "strong": 0.58},
            {"duration": 70, "weak": 0.0, "strong": 0.0},
            {"duration": 110, "weak": 0.40, "strong": 0.66},
        ],
    },
    "bossClear": {
        "label": "Boss Clear",
        "description": "Unused alternate pattern with a longer success pulse.",
        "sequence": [
            {"duration": 180, "weak": 0.49, "strong": 0.79},
        ],
    },
    "timeout": {
        "label": "Timeout Alarm",
        "description": "Long pulse followed by a shorter aftershock when a timer expires.",
        "sequence": [
            {"duration": 420, "weak": 0.80, "strong": 1.0},
            {"duration": 95, "weak": 0.0, "strong": 0.0},
            {"duration": 180, "weak": 0.55, "strong": 0.76},
        ],
    },
    "soft_tap": {
        "label": "Soft Tap",
        "description": "Small low-intensity tap.",
        "sequence": [{"duration": 45, "weak": 0.18, "strong": 0.24}],
    },
    "crisp_tick": {
        "label": "Crisp Tick",
        "description": "Tiny sharp tick for very light feedback.",
        "sequence": [{"duration": 28, "weak": 0.28, "strong": 0.48}],
    },
    "medium_buzz": {
        "label": "Medium Buzz",
        "description": "Plain medium single buzz.",
        "sequence": [{"duration": 115, "weak": 0.45, "strong": 0.62}],
    },
    "heavy_thud": {
        "label": "Heavy Thud",
        "description": "Short heavy thump.",
        "sequence": [{"duration": 140, "weak": 0.72, "strong": 1.0}],
    },
    "long_low": {
        "label": "Long Low Buzz",
        "description": "Longer low-intensity buzz.",
        "sequence": [{"duration": 260, "weak": 0.28, "strong": 0.34}],
    },
    "double_tap_soft": {
        "label": "Soft Double Tap",
        "description": "Two light taps.",
        "sequence": [
            {"duration": 45, "weak": 0.22, "strong": 0.32},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 45, "weak": 0.22, "strong": 0.32},
        ],
    },
    "double_tap_hard": {
        "label": "Hard Double Tap",
        "description": "Two harder taps.",
        "sequence": [
            {"duration": 65, "weak": 0.58, "strong": 0.86},
            {"duration": 45, "weak": 0.0, "strong": 0.0},
            {"duration": 65, "weak": 0.58, "strong": 0.92},
        ],
    },
    "triple_tap": {
        "label": "Triple Tap",
        "description": "Three quick taps.",
        "sequence": [
            {"duration": 42, "weak": 0.42, "strong": 0.68},
            {"duration": 28, "weak": 0.0, "strong": 0.0},
            {"duration": 42, "weak": 0.42, "strong": 0.68},
            {"duration": 28, "weak": 0.0, "strong": 0.0},
            {"duration": 42, "weak": 0.42, "strong": 0.72},
        ],
    },
    "heartbeat_slow": {
        "label": "Slow Heartbeat",
        "description": "Two spaced pulses.",
        "sequence": [
            {"duration": 80, "weak": 0.45, "strong": 0.72},
            {"duration": 130, "weak": 0.0, "strong": 0.0},
            {"duration": 115, "weak": 0.50, "strong": 0.78},
        ],
    },
    "heartbeat_urgent": {
        "label": "Urgent Heartbeat",
        "description": "Quicker heartbeat-like warning.",
        "sequence": [
            {"duration": 55, "weak": 0.52, "strong": 0.82},
            {"duration": 58, "weak": 0.0, "strong": 0.0},
            {"duration": 75, "weak": 0.60, "strong": 0.95},
            {"duration": 70, "weak": 0.0, "strong": 0.0},
            {"duration": 95, "weak": 0.68, "strong": 1.0},
        ],
    },
    "angry_timeout_a": {
        "label": "Angry Timeout A",
        "description": "Rapid warning taps followed by a heavy hit.",
        "sequence": [
            {"duration": 40, "weak": 0.72, "strong": 1.0},
            {"duration": 20, "weak": 0.0, "strong": 0.0},
            {"duration": 40, "weak": 0.72, "strong": 1.0},
            {"duration": 20, "weak": 0.0, "strong": 0.0},
            {"duration": 40, "weak": 0.72, "strong": 1.0},
            {"duration": 60, "weak": 0.0, "strong": 0.0},
            {"duration": 180, "weak": 0.90, "strong": 1.0},
        ],
    },
    "angry_timeout_b": {
        "label": "Angry Timeout B",
        "description": "Six fast hits and a strong final slam.",
        "sequence": [
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 30, "weak": 0.78, "strong": 1.0},
            {"duration": 70, "weak": 0.0, "strong": 0.0},
            {"duration": 220, "weak": 1.0, "strong": 1.0},
        ],
    },
    "buzz_saw": {
        "label": "Buzz Saw",
        "description": "Fast repeated micro-buzzes.",
        "sequence": [
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 20, "weak": 0.72, "strong": 1.0},
        ],
    },
    "panic_chatter": {
        "label": "Panic Chatter",
        "description": "Eight sharp warning bursts.",
        "sequence": [
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
            {"duration": 15, "weak": 0.0, "strong": 0.0},
            {"duration": 25, "weak": 0.65, "strong": 0.95},
        ],
    },
    "heavy_final_slam": {
        "label": "Heavy Final Slam",
        "description": "Medium warning then a long max hit.",
        "sequence": [
            {"duration": 60, "weak": 0.45, "strong": 0.68},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 260, "weak": 1.0, "strong": 1.0},
        ],
    },
    "rising_alarm": {
        "label": "Rising Alarm",
        "description": "Each pulse is stronger than the last, then the same ramp repeats immediately.",
        "sequence": [
            {"duration": 50, "weak": 0.24, "strong": 0.38},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 70, "weak": 0.42, "strong": 0.62},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 120, "weak": 0.68, "strong": 0.92},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 220, "weak": 1.0, "strong": 1.0},
            {"duration": 50, "weak": 0.24, "strong": 0.38},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 70, "weak": 0.42, "strong": 0.62},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 120, "weak": 0.68, "strong": 0.92},
            {"duration": 40, "weak": 0.0, "strong": 0.0},
            {"duration": 220, "weak": 1.0, "strong": 1.0},
        ],
    },
    "falling_alarm": {
        "label": "Falling Alarm",
        "description": "A hard hit decays into smaller pulses.",
        "sequence": [
            {"duration": 180, "weak": 1.0, "strong": 1.0},
            {"duration": 45, "weak": 0.0, "strong": 0.0},
            {"duration": 100, "weak": 0.60, "strong": 0.82},
            {"duration": 35, "weak": 0.0, "strong": 0.0},
            {"duration": 55, "weak": 0.35, "strong": 0.55},
        ],
    },
    "steam_chatter_1": {
        "label": "Steam Chatter 1",
        "description": "Short pulses aimed at Steam Controller haptics.",
        "sequence": [
            {"duration": 18, "weak": 0.75, "strong": 1.0},
            {"duration": 12, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.75, "strong": 1.0},
            {"duration": 12, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.75, "strong": 1.0},
            {"duration": 12, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.75, "strong": 1.0},
        ],
    },
    "steam_chatter_2": {
        "label": "Steam Chatter 2",
        "description": "Denser Steam Controller chatter.",
        "sequence": [
            {"duration": 16, "weak": 0.65, "strong": 0.95},
            {"duration": 8, "weak": 0.0, "strong": 0.0},
            {"duration": 16, "weak": 0.65, "strong": 0.95},
            {"duration": 8, "weak": 0.0, "strong": 0.0},
            {"duration": 16, "weak": 0.65, "strong": 0.95},
            {"duration": 8, "weak": 0.0, "strong": 0.0},
            {"duration": 16, "weak": 0.65, "strong": 0.95},
            {"duration": 8, "weak": 0.0, "strong": 0.0},
            {"duration": 16, "weak": 0.65, "strong": 0.95},
            {"duration": 8, "weak": 0.0, "strong": 0.0},
            {"duration": 16, "weak": 0.65, "strong": 0.95},
        ],
    },
    "steam_harsh_tick": {
        "label": "Steam Harsh Tick",
        "description": "Very short hard tick for Steam Input translation.",
        "sequence": [{"duration": 22, "weak": 1.0, "strong": 1.0}],
    },
    "steam_timeout_burst": {
        "label": "Steam Timeout Burst",
        "description": "Steam-focused timeout burst with a final slam.",
        "sequence": [
            {"duration": 18, "weak": 0.95, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.95, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.95, "strong": 1.0},
            {"duration": 10, "weak": 0.0, "strong": 0.0},
            {"duration": 18, "weak": 0.95, "strong": 1.0},
            {"duration": 65, "weak": 0.0, "strong": 0.0},
            {"duration": 170, "weak": 1.0, "strong": 1.0},
        ],
    },
    "steam_final_slam": {
        "label": "Steam Final Slam",
        "description": "Steam-focused heavy ending pulse.",
        "sequence": [
            {"duration": 35, "weak": 0.65, "strong": 0.85},
            {"duration": 28, "weak": 0.0, "strong": 0.0},
            {"duration": 210, "weak": 1.0, "strong": 1.0},
        ],
    },
}

HAPTIC_PATTERN_ORDER = (
    "reveal",
    "again",
    "hard",
    "good",
    "easy",
    "skip",
    "sync",
    "reset",
    "timeout",
    "bossStart",
    "bossClear",
    "soft_tap",
    "crisp_tick",
    "medium_buzz",
    "heavy_thud",
    "long_low",
    "double_tap_soft",
    "double_tap_hard",
    "triple_tap",
    "heartbeat_slow",
    "heartbeat_urgent",
    "angry_timeout_a",
    "angry_timeout_b",
    "buzz_saw",
    "panic_chatter",
    "heavy_final_slam",
    "rising_alarm",
    "falling_alarm",
    "steam_chatter_1",
    "steam_chatter_2",
    "steam_harsh_tick",
    "steam_timeout_burst",
    "steam_final_slam",
)

HAPTIC_LAB_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Simple", ("soft_tap", "crisp_tick", "medium_buzz", "heavy_thud", "long_low")),
    ("Double / Triple", ("double_tap_soft", "double_tap_hard", "triple_tap", "heartbeat_slow", "heartbeat_urgent")),
    ("Failure / Timeout", ("timeout", "angry_timeout_a", "angry_timeout_b", "buzz_saw", "panic_chatter", "heavy_final_slam", "rising_alarm", "falling_alarm")),
    ("Steam Controller Experiments", ("steam_chatter_1", "steam_chatter_2", "steam_harsh_tick", "steam_timeout_burst", "steam_final_slam")),
    ("Original Event Defaults", ("reveal", "again", "hard", "good", "easy", "skip", "sync", "reset", "bossStart", "bossClear")),
)

HAPTIC_PATTERN_OPTIONS: tuple[tuple[str, str], ...] = ((HAPTIC_PATTERN_OFF, "Off"),) + tuple(
    (key, str(HAPTIC_PATTERN_LIBRARY[key]["label"])) for key in HAPTIC_PATTERN_ORDER
)

HAPTIC_EVENT_OPTIONS: tuple[dict[str, str], ...] = (
    {
        "event": "sync",
        "label": "Question Sync",
        "description": "When Speed Streak first locks onto a visible question card.",
        "default_pattern": "sync",
    },
    {
        "event": "reveal",
        "label": "Answer Reveal",
        "description": "When you show the answer side of the current card.",
        "default_pattern": "reveal",
    },
    {
        "event": "again",
        "label": "Again Rating",
        "description": "When you rate the card Again.",
        "default_pattern": "again",
    },
    {
        "event": "hard",
        "label": "Hard Rating",
        "description": "When you rate the card Hard.",
        "default_pattern": "hard",
    },
    {
        "event": "good",
        "label": "Good Rating",
        "description": "When you rate the card Good.",
        "default_pattern": "good",
    },
    {
        "event": "easy",
        "label": "Easy Rating",
        "description": "When you rate the card Easy.",
        "default_pattern": "easy",
    },
    {
        "event": "skip",
        "label": "Skip / Bury",
        "description": "When the current card is buried or skipped.",
        "default_pattern": "skip",
    },
    {
        "event": "reset",
        "label": "Run Reset",
        "description": "When you reset the current Speed Streak run.",
        "default_pattern": "reset",
    },
    {
        "event": "timeout",
        "label": "Timeout",
        "description": "When the question or answer timer expires.",
        "default_pattern": "timeout",
    },
)

DEFAULT_AUDIO_EVENT_FILES = {
    "sync": "kenney_impact-sounds/Audio/footstep_grass_004.mp3",
    "reveal": "kenney_rpg-audio/Audio/drawKnife2.mp3",
    "again": "kenney_impact-sounds/Audio/impactSoft_heavy_000.mp3",
    "hard": "kenney_impact-sounds/Audio/impactPlank_medium_002.mp3",
    "good": "kenney_casino-audio/Audio/chips-handle-3.mp3",
    "easy": "kenney_impact-sounds/Audio/impactMining_002.mp3",
    "skip": "kenney_rpg-audio/Audio/bookFlip2.mp3",
    "reset": "kenney_ui-audio/Audio/switch9.mp3",
    "timeout": "kenney_impact-sounds/Audio/impactBell_heavy_000.mp3",
}

DEFAULT_HAPTIC_EVENT_PATTERNS = {
    item["event"]: item["default_pattern"] for item in HAPTIC_EVENT_OPTIONS
}

STEAM_CONTROLLER_HAPTIC_EVENT_PATTERNS = {
    **DEFAULT_HAPTIC_EVENT_PATTERNS,
    "again": "sync",
    "timeout": "rising_alarm",
}


def default_audio_event_files() -> dict[str, str]:
    normalized: dict[str, str] = {}
    for item in HAPTIC_EVENT_OPTIONS:
        event_key = item["event"]
        normalized[event_key] = str(DEFAULT_AUDIO_EVENT_FILES.get(event_key, DEFAULT_AUDIO_FILE) or DEFAULT_AUDIO_FILE)
    return normalized


def default_haptic_event_patterns() -> dict[str, str]:
    return dict(DEFAULT_HAPTIC_EVENT_PATTERNS)


def default_haptic_event_patterns_for_profile(profile: Any) -> dict[str, str]:
    normalized = normalize_haptic_controller_profile(profile)
    if normalized == HAPTIC_CONTROLLER_PROFILE_STEAM:
        return dict(STEAM_CONTROLLER_HAPTIC_EVENT_PATTERNS)
    return default_haptic_event_patterns()


def normalize_haptic_controller_profile(value: Any) -> str:
    profile = str(value or "").strip()
    valid_profiles = {key for key, _label in HAPTIC_CONTROLLER_PROFILE_OPTIONS}
    if profile in valid_profiles:
        return profile
    return HAPTIC_CONTROLLER_PROFILE_STANDARD


def normalize_audio_event_files(value: Any, *, fallback_file: str | None = None) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    fallback = str(fallback_file or DEFAULT_AUDIO_FILE or "").strip()
    normalized: dict[str, str] = {}
    defaults = default_audio_event_files()
    for item in HAPTIC_EVENT_OPTIONS:
        event_key = item["event"]
        selected = str(source.get(event_key, defaults.get(event_key, fallback)) or "").strip()
        normalized[event_key] = selected or defaults.get(event_key, fallback)
    return normalized


def normalize_haptic_pattern_key(value: Any) -> str:
    key = str(value or "").strip()
    if key == HAPTIC_PATTERN_OFF:
        return HAPTIC_PATTERN_OFF
    if key in HAPTIC_PATTERN_LIBRARY:
        return key
    return ""


def normalize_haptic_event_patterns(value: Any) -> dict[str, str]:
    source = value if isinstance(value, dict) else {}
    normalized: dict[str, str] = {}
    for item in HAPTIC_EVENT_OPTIONS:
        event_key = item["event"]
        default_pattern = item["default_pattern"]
        selected = normalize_haptic_pattern_key(source.get(event_key, default_pattern))
        normalized[event_key] = selected or default_pattern
    return normalized


def haptic_pattern_label(pattern_key: str) -> str:
    if pattern_key == HAPTIC_PATTERN_OFF:
        return "Off"
    return str(HAPTIC_PATTERN_LIBRARY.get(pattern_key, {}).get("label", pattern_key or "Unknown"))


def haptic_pattern_sequences() -> dict[str, list[dict[str, float]]]:
    return {
        key: [dict(step) for step in meta["sequence"]]
        for key, meta in HAPTIC_PATTERN_LIBRARY.items()
    }
