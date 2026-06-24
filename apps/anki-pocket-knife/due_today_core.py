from __future__ import annotations

from datetime import date, datetime, timedelta
from html.parser import HTMLParser
import time
from typing import Iterable


class _ImageDetector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.found = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if str(tag).casefold() == "img":
            self.found = True

    def handle_startendtag(self, tag: str, attrs) -> None:
        if str(tag).casefold() == "img":
            self.found = True


def rendered_question_has_image(html: str) -> bool:
    parser = _ImageDetector()
    parser.feed(str(html or ""))
    parser.close()
    return parser.found


def normalize_deck_selection(
    selected_ids: Iterable[int],
    deck_names: dict[int, str],
) -> list[int]:
    selected = {
        int(deck_id)
        for deck_id in selected_ids
        if int(deck_id) in deck_names
    }
    ordered = sorted(selected, key=lambda deck_id: (deck_names[deck_id].count("::"), deck_names[deck_id].casefold()))
    kept: list[int] = []
    for deck_id in ordered:
        name = deck_names[deck_id]
        if any(name.startswith(f"{deck_names[parent_id]}::") for parent_id in kept):
            continue
        kept.append(deck_id)
    return kept


def expand_deck_selection(
    selected_ids: Iterable[int],
    deck_names: dict[int, str],
) -> list[int]:
    normalized = normalize_deck_selection(selected_ids, deck_names)
    result: set[int] = set()
    for selected_id in normalized:
        selected_name = deck_names[selected_id]
        for deck_id, name in deck_names.items():
            if name == selected_name or name.startswith(f"{selected_name}::"):
                result.add(int(deck_id))
    return sorted(result)


def selected_scheduler_day(today: int, days_ago: int) -> int:
    return int(today) - max(0, int(days_ago))


def days_ago_for_date(selected_date: date, today_date: date) -> int:
    return max(0, int((today_date - selected_date).days))


def rollover_boundaries(day_cutoff: int, days_ago: int) -> tuple[int, int]:
    """Return local-time rollover boundaries, preserving DST-short/long days."""
    cutoff_local = datetime.fromtimestamp(int(day_cutoff))
    end_date = cutoff_local.date() - timedelta(days=max(0, int(days_ago)))
    start_date = end_date - timedelta(days=1)
    clock = cutoff_local.time().replace(tzinfo=None)

    def local_timestamp(value: date) -> int:
        local_value = datetime.combine(value, clock)
        return int(time.mktime(local_value.timetuple()))

    return local_timestamp(start_date), local_timestamp(end_date)


def deck_date_label(days_ago: int, selected_date: date) -> str:
    offset = max(0, int(days_ago))
    if offset == 0:
        return f"Today {selected_date.isoformat()}"
    if offset == 1:
        return f"Yesterday {selected_date.isoformat()}"
    return selected_date.isoformat()


def target_deck_names(days_ago: int, selected_date: date) -> dict[str, str]:
    label = deck_date_label(days_ago, selected_date)
    return {
        "audio": f"..Due {label} Audio",
        "visual": f"..Due {label} Visual",
        "combined": f"..Due {label} Combined",
    }
