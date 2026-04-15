from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from html.parser import HTMLParser
import math
import re
from typing import Any, Mapping


DEFAULT_HARD_CARDS_CONFIG: dict[str, Any] = {
    "default_lookback_hours": 24,
    "default_top_n": 20,
    "preview_max_chars": 160,
    "recent_introduction_window_hours": 72,
    "cluster_window_minutes": 30,
    "weights": {
        "again": 12.0,
        "hard": 4.0,
        "recent_success_penalty": 8.0,
        "learning_bonus": 4.5,
        "relearning_bonus": 7.0,
        "recent_introduction_bonus": 6.5,
        "cluster_failure_bonus": 3.5,
        "lifetime_lapse_bonus": 1.4,
        "last_again_bonus": 3.0,
        "fsrs_difficulty_bonus": 0.0,
    },
    "preferred_field_names_by_note_type": {
        "__cloze__": ["Text"],
        "Visual_Card_Multitude": ["Question", "English"],
        "__default__": ["Text", "Front", "Main", "Stem", "Prompt", "Question", "English"],
    },
    "auxiliary_field_names": [
        "Back",
        "Answer",
        "Extra",
        "More Info",
        "Hint",
        "Hints",
        "ID",
        "Ids",
        "Guid",
        "UUID",
        "Tags",
        "Tag",
        "Source",
        "Sources",
        "Reference",
        "References",
        "Citation",
        "Citations",
        "Css",
        "Style",
        "Script",
        "Header",
        "Footer",
    ],
    "include_deck_name_in_copy": True,
    "include_note_type_in_copy": True,
    "preserve_raw_cloze_syntax": True,
}

_CLOZE_RE = re.compile(r"\{\{c\d+::(.*?)(?:::(.*?))?\}\}", re.IGNORECASE | re.DOTALL)
_BLANK_LINE_RE = re.compile(r"\n{3,}")
_WHITESPACE_RE = re.compile(r"[ \t\r\f\v]+")


class _HtmlToTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._skip_depth += 1
            return
        if self._skip_depth:
            return
        if tag == "img":
            self.parts.append("[Image]")
            return
        if tag in {"br", "p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"} or self._skip_depth:
            return
        if tag == "img":
            self.parts.append("[Image]")
            return
        if tag in {"br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth:
            return
        if tag in {"p", "div", "li", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self.parts.append(data)

    def get_text(self) -> str:
        text = "".join(self.parts).replace("\xa0", " ")
        lines = [_WHITESPACE_RE.sub(" ", line).strip() for line in text.splitlines()]
        collapsed = "\n".join(line for line in lines if line)
        return _BLANK_LINE_RE.sub("\n\n", collapsed).strip()


@dataclass(frozen=True)
class SelectedContent:
    field_names: tuple[str, ...]
    content_text: str


@dataclass(frozen=True)
class HardCardMetrics:
    card_id: int
    note_id: int
    deck_name: str
    note_type_name: str
    is_cloze: bool
    current_state: str
    created_age_hours: float
    total_reps: int
    total_lapses: int
    again_count: int
    hard_count: int
    good_count: int
    easy_count: int
    total_answers: int
    most_recent_ease: int | None
    last_review_at_s: int | None
    failure_cluster_count: int
    content: SelectedContent
    fsrs_difficulty: float | None = None


@dataclass(frozen=True)
class RankedHardCard:
    metrics: HardCardMetrics
    score: float
    explanation: tuple[str, ...]
    preview_text: str
    score_components: dict[str, float]


def merge_hard_cards_config(raw_config: Mapping[str, Any] | None) -> dict[str, Any]:
    merged = deepcopy(DEFAULT_HARD_CARDS_CONFIG)
    if not isinstance(raw_config, Mapping):
        return merged

    merged["default_lookback_hours"] = _positive_int(
        raw_config.get("default_lookback_hours"),
        merged["default_lookback_hours"],
    )
    merged["default_top_n"] = _positive_int(
        raw_config.get("default_top_n"),
        merged["default_top_n"],
    )
    merged["preview_max_chars"] = _positive_int(
        raw_config.get("preview_max_chars"),
        merged["preview_max_chars"],
    )
    merged["recent_introduction_window_hours"] = _positive_float(
        raw_config.get("recent_introduction_window_hours"),
        merged["recent_introduction_window_hours"],
    )
    merged["cluster_window_minutes"] = _positive_float(
        raw_config.get("cluster_window_minutes"),
        merged["cluster_window_minutes"],
    )
    merged["include_deck_name_in_copy"] = bool(
        raw_config.get("include_deck_name_in_copy", merged["include_deck_name_in_copy"])
    )
    merged["include_note_type_in_copy"] = bool(
        raw_config.get("include_note_type_in_copy", merged["include_note_type_in_copy"])
    )
    merged["preserve_raw_cloze_syntax"] = bool(
        raw_config.get("preserve_raw_cloze_syntax", merged["preserve_raw_cloze_syntax"])
    )

    raw_weights = raw_config.get("weights")
    if isinstance(raw_weights, Mapping):
        for key, default_value in merged["weights"].items():
            merged["weights"][key] = _float(raw_weights.get(key), default_value)

    raw_field_map = raw_config.get("preferred_field_names_by_note_type")
    if isinstance(raw_field_map, Mapping):
        merged_field_map = deepcopy(DEFAULT_HARD_CARDS_CONFIG["preferred_field_names_by_note_type"])
        for key, value in raw_field_map.items():
            normalized = _string_list(value)
            if normalized:
                merged_field_map[str(key)] = normalized
        merged["preferred_field_names_by_note_type"] = merged_field_map

    raw_auxiliary = raw_config.get("auxiliary_field_names")
    auxiliary = _string_list(raw_auxiliary)
    if auxiliary:
        merged["auxiliary_field_names"] = auxiliary

    return merged


def html_to_text(html: str) -> str:
    parser = _HtmlToTextParser()
    parser.feed(html or "")
    parser.close()
    return parser.get_text()


def strip_cloze_markup(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        answer = str(match.group(1) or "").strip()
        hint = str(match.group(2) or "").strip()
        if answer:
            return answer
        if hint:
            return hint
        return ""

    return _CLOZE_RE.sub(replace, text or "")


def select_note_content(
    *,
    note_type_name: str,
    fields: Mapping[str, str],
    is_cloze: bool,
    config: Mapping[str, Any],
) -> SelectedContent:
    preferred = config.get("preferred_field_names_by_note_type", {})
    auxiliary_fields = {
        str(name).casefold() for name in config.get("auxiliary_field_names", [])
    }
    normalized_fields = {
        str(name).casefold(): str(name) for name in fields.keys()
    }
    exact_key = _matching_mapping_key(preferred, note_type_name)
    selected_names: list[str] = []

    if exact_key is not None:
        selected_names = _matching_field_names(
            preferred.get(exact_key, []),
            normalized_fields,
            fields,
            is_cloze=is_cloze,
            preserve_raw_cloze_syntax=bool(config.get("preserve_raw_cloze_syntax", True)),
            keep_all_matches=True,
        )
    else:
        mapping_key = "__cloze__" if is_cloze else "__default__"
        selected_names = _matching_field_names(
            preferred.get(mapping_key, []),
            normalized_fields,
            fields,
            is_cloze=is_cloze,
            preserve_raw_cloze_syntax=bool(config.get("preserve_raw_cloze_syntax", True)),
            keep_all_matches=False,
        )

    if not selected_names:
        selected_names = _fallback_field_names(
            fields,
            auxiliary_fields=auxiliary_fields,
            is_cloze=is_cloze,
            preserve_raw_cloze_syntax=bool(config.get("preserve_raw_cloze_syntax", True)),
        )

    sections: list[str] = []
    for name in selected_names:
        cleaned = clean_field_text(
            str(fields.get(name, "") or ""),
            preserve_raw_cloze_syntax=bool(config.get("preserve_raw_cloze_syntax", True)),
        )
        if not cleaned:
            continue
        if len(selected_names) > 1:
            sections.append(f"{name}:\n{cleaned}")
        else:
            sections.append(cleaned)

    content_text = "\n\n".join(sections).strip() or "(blank)"
    return SelectedContent(tuple(selected_names), content_text)


def clean_field_text(raw_value: str, *, preserve_raw_cloze_syntax: bool) -> str:
    cleaned = html_to_text(str(raw_value or ""))
    if not preserve_raw_cloze_syntax:
        cleaned = strip_cloze_markup(cleaned)
    cleaned = _BLANK_LINE_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def compute_failure_cluster_count(
    events: list[tuple[int, int]],
    *,
    cluster_window_minutes: float,
) -> int:
    if not events:
        return 0

    gap_seconds = max(60.0, float(cluster_window_minutes) * 60.0)
    failures = [(timestamp_s, ease) for timestamp_s, ease in events if int(ease) in (1, 2)]
    if len(failures) < 2:
        return 0

    clusters = 0
    for previous, current in zip(failures, failures[1:]):
        if (int(current[0]) - int(previous[0])) <= gap_seconds:
            clusters += 1
    return clusters


def is_meaningful_candidate(metrics: HardCardMetrics) -> bool:
    return bool(
        metrics.again_count > 0
        or metrics.hard_count > 0
        or metrics.current_state in {"learning", "relearning"}
        or metrics.most_recent_ease == 1
    )


def compute_hard_card_score(
    metrics: HardCardMetrics,
    *,
    config: Mapping[str, Any],
) -> tuple[float, dict[str, float]]:
    weights = config.get("weights", {})
    success_rate = recent_success_rate(metrics)
    recent_pressure = min(2.0, float(metrics.again_count) + (float(metrics.hard_count) * 0.5))
    intro_factor = recent_introduction_factor(
        metrics.created_age_hours,
        float(config.get("recent_introduction_window_hours", 72)),
    )

    components = {
        "again": float(metrics.again_count) * _float(weights.get("again"), 0.0),
        "hard": float(metrics.hard_count) * _float(weights.get("hard"), 0.0),
        "recent_success_penalty": (1.0 - success_rate)
        * _float(weights.get("recent_success_penalty"), 0.0),
        "learning_bonus": (
            _float(weights.get("learning_bonus"), 0.0)
            if metrics.current_state == "learning"
            else 0.0
        ),
        "relearning_bonus": (
            _float(weights.get("relearning_bonus"), 0.0)
            if metrics.current_state == "relearning"
            else 0.0
        ),
        "recent_introduction_bonus": (
            _float(weights.get("recent_introduction_bonus"), 0.0)
            * intro_factor
            * min(1.5, recent_pressure)
        ),
        "cluster_failure_bonus": (
            float(metrics.failure_cluster_count)
            * _float(weights.get("cluster_failure_bonus"), 0.0)
        ),
        "lifetime_lapse_bonus": (
            math.log1p(max(0, metrics.total_lapses))
            * _float(weights.get("lifetime_lapse_bonus"), 0.0)
        ),
        "last_again_bonus": (
            _float(weights.get("last_again_bonus"), 0.0)
            if metrics.most_recent_ease == 1
            else 0.0
        ),
        "fsrs_difficulty_bonus": (
            max(0.0, min(1.0, float(metrics.fsrs_difficulty or 0.0) / 10.0))
            * _float(weights.get("fsrs_difficulty_bonus"), 0.0)
        ),
    }

    total = sum(components.values())
    return total, components


def recent_success_rate(metrics: HardCardMetrics) -> float:
    total_answers = max(1, int(metrics.total_answers))
    weighted_successes = (
        float(metrics.good_count)
        + float(metrics.easy_count)
        + (float(metrics.hard_count) * 0.5)
    )
    return max(0.0, min(1.0, weighted_successes / float(total_answers)))


def recent_introduction_factor(created_age_hours: float, intro_window_hours: float) -> float:
    safe_window = max(1.0, float(intro_window_hours))
    safe_age = max(0.0, float(created_age_hours))
    return max(0.0, 1.0 - (safe_age / safe_window))


def build_explanation(metrics: HardCardMetrics, *, config: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    if metrics.again_count > 0:
        reasons.append(f"{metrics.again_count} Again")
    if metrics.hard_count > 0:
        reasons.append(f"{metrics.hard_count} Hard")
    if metrics.current_state == "relearning":
        reasons.append("currently relearning")
    elif metrics.current_state == "learning":
        reasons.append("currently learning")
    if metrics.failure_cluster_count > 0:
        reasons.append("clustered misses")
    if metrics.most_recent_ease == 1:
        reasons.append("last review Again")
    if recent_introduction_factor(
        metrics.created_age_hours,
        float(config.get("recent_introduction_window_hours", 72)),
    ) > 0 and (metrics.again_count > 0 or metrics.hard_count > 0):
        reasons.append(f"introduced {format_age_brief(metrics.created_age_hours)} ago")
    if metrics.total_lapses >= 3:
        reasons.append(f"{metrics.total_lapses} lifetime lapses")
    if not reasons:
        reasons.append("recent instability")
    return tuple(reasons[:5])


def rank_hard_cards(
    metrics_list: list[HardCardMetrics],
    *,
    config: Mapping[str, Any],
    top_n: int,
) -> list[RankedHardCard]:
    ranked: list[RankedHardCard] = []
    preview_chars = _positive_int(
        config.get("preview_max_chars"),
        DEFAULT_HARD_CARDS_CONFIG["preview_max_chars"],
    )

    for metrics in metrics_list:
        if not is_meaningful_candidate(metrics):
            continue
        score, components = compute_hard_card_score(metrics, config=config)
        ranked.append(
            RankedHardCard(
                metrics=metrics,
                score=score,
                explanation=build_explanation(metrics, config=config),
                preview_text=build_preview_text(metrics.content.content_text, preview_chars),
                score_components=components,
            )
        )

    ranked.sort(
        key=lambda result: (
            -result.score,
            -result.metrics.again_count,
            -result.metrics.hard_count,
            -result.metrics.failure_cluster_count,
            -(result.metrics.last_review_at_s or 0),
            result.metrics.deck_name.casefold(),
            result.metrics.note_type_name.casefold(),
            result.metrics.card_id,
        )
    )
    return ranked[: max(1, int(top_n))]


def build_tutor_clipboard_text(
    ranked_cards: list[RankedHardCard],
    *,
    config: Mapping[str, Any],
) -> str:
    blocks: list[str] = []
    include_deck = bool(config.get("include_deck_name_in_copy", True))
    include_note_type = bool(config.get("include_note_type_in_copy", True))

    for index, ranked in enumerate(ranked_cards, start=1):
        lines = [f"Card {index}"]
        if include_deck:
            lines.append(f"Deck: {ranked.metrics.deck_name}")
        if include_note_type:
            lines.append(f"Note type: {ranked.metrics.note_type_name}")
        field_source = ", ".join(ranked.metrics.content.field_names) or "Unknown"
        lines.append(f"Field source: {field_source}")
        lines.append("Content:")
        lines.append(ranked.metrics.content.content_text or "(blank)")
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks).strip()


def build_preview_text(text: str, max_chars: int) -> str:
    single_line = " ".join(str(text or "").split())
    limit = max(24, int(max_chars))
    if len(single_line) <= limit:
        return single_line
    truncated = single_line[: max(1, limit - 3)].rstrip()
    return truncated + "..."
    return single_line[: limit - 1].rstrip() + "…"


def format_age_brief(age_hours: float) -> str:
    safe_hours = max(0.0, float(age_hours))
    if safe_hours < 1:
        minutes = max(1, int(round(safe_hours * 60.0)))
        return f"{minutes}m"
    if safe_hours < 24:
        return f"{int(round(safe_hours))}h"
    days = max(1, int(round(safe_hours / 24.0)))
    return f"{days}d"


def _matching_mapping_key(
    preferred: Any,
    note_type_name: str,
) -> str | None:
    if not isinstance(preferred, Mapping):
        return None
    wanted = str(note_type_name or "").casefold()
    for raw_key in preferred.keys():
        key = str(raw_key or "")
        if key.startswith("__"):
            continue
        if key.casefold() == wanted:
            return key
    return None


def _matching_field_names(
    wanted_names: Any,
    normalized_fields: Mapping[str, str],
    fields: Mapping[str, str],
    *,
    is_cloze: bool,
    preserve_raw_cloze_syntax: bool,
    keep_all_matches: bool,
) -> list[str]:
    selected: list[str] = []
    for wanted_name in _string_list(wanted_names):
        actual_name = normalized_fields.get(wanted_name.casefold())
        if not actual_name:
            continue
        cleaned = clean_field_text(
            str(fields.get(actual_name, "") or ""),
            preserve_raw_cloze_syntax=preserve_raw_cloze_syntax,
        )
        if not cleaned:
            continue
        selected.append(actual_name)
        if not keep_all_matches:
            break
    return selected


def _fallback_field_names(
    fields: Mapping[str, str],
    *,
    auxiliary_fields: set[str],
    is_cloze: bool,
    preserve_raw_cloze_syntax: bool,
) -> list[str]:
    for name, value in fields.items():
        if str(name).casefold() in auxiliary_fields:
            continue
        cleaned = clean_field_text(
            str(value or ""),
            preserve_raw_cloze_syntax=preserve_raw_cloze_syntax,
        )
        if cleaned:
            return [str(name)]
    for name, value in fields.items():
        cleaned = clean_field_text(
            str(value or ""),
            preserve_raw_cloze_syntax=preserve_raw_cloze_syntax,
        )
        if cleaned:
            return [str(name)]
    return [next(iter(fields.keys()), "Unknown")]


def _positive_int(raw_value: Any, default_value: int) -> int:
    try:
        value = int(raw_value)
    except Exception:
        return int(default_value)
    return value if value > 0 else int(default_value)


def _positive_float(raw_value: Any, default_value: float) -> float:
    try:
        value = float(raw_value)
    except Exception:
        return float(default_value)
    return value if value > 0 else float(default_value)


def _float(raw_value: Any, default_value: float) -> float:
    try:
        return float(raw_value)
    except Exception:
        return float(default_value)


def _string_list(raw_value: Any) -> list[str]:
    if not isinstance(raw_value, (list, tuple)):
        return []
    cleaned: list[str] = []
    for value in raw_value:
        text = str(value or "").strip()
        if text:
            cleaned.append(text)
    return cleaned
