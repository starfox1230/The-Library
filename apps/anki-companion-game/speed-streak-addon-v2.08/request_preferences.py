"""Shared, UI-independent user-request settings for the 2.05/2.06 tracks."""
from __future__ import annotations


def timer_number_mode(value):
    return value if value in ("decimal", "seconds", "hidden") else "decimal"


def boost_ratings(value):
    if not isinstance(value, (list, tuple)):
        return [1, 2, 3, 4]
    return [rating for rating in (1, 2, 3, 4) if rating in value]


def deck_rules(value, normalize_rule, question_seconds, answer_seconds):
    result = []
    for item in value if isinstance(value, list) else []:
        if not isinstance(item, dict):
            continue
        ids = []
        for raw in item.get("deck_ids", []) if isinstance(item.get("deck_ids"), list) else []:
            try:
                deck_id = int(raw)
            except (ValueError, TypeError):
                continue
            if deck_id > 0 and deck_id not in ids:
                ids.append(deck_id)
        if ids:
            result.append({"deck_ids": ids, "include_subdecks": bool(item.get("include_subdecks", True)),
                           **normalize_rule(item, default_question_seconds=question_seconds,
                                            default_answer_seconds=answer_seconds)})
    return result


def matches_deck(rule, card, decks):
    """Use the home deck for filtered cards; IDs survive deck renames."""
    card_id = int(getattr(card, "odid", 0) or getattr(card, "did", 0) or 0)
    selected = set(rule.get("deck_ids", []))
    if card_id in selected:
        return True
    if not rule.get("include_subdecks", True) or not card_id:
        return False
    current = decks.get(card_id, default=False)
    if not current:
        return False
    name = str(current.get("name", ""))
    for deck_id in selected:
        parent = decks.get(deck_id, default=False)
        if parent and name.startswith(str(parent.get("name", "")) + "::"):
            return True
    return False
