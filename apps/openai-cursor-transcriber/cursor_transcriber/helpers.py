from __future__ import annotations

SPECIAL_KEY_LABELS = {
    "ctrl": "Ctrl",
    "shift": "Shift",
    "alt": "Alt",
    "cmd": "Cmd",
    "insert": "Insert",
    "space": "Space",
}


def format_duration(seconds_remaining: float) -> str:
    whole_seconds = max(0, int(round(seconds_remaining)))
    minutes, seconds = divmod(whole_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def hotkey_to_label(hotkey: str) -> str:
    parts: list[str] = []
    for chunk in hotkey.split("+"):
        token = chunk.strip().strip("<>").lower()
        if not token:
            continue
        if token.startswith("f") and token[1:].isdigit():
            parts.append(token.upper())
        else:
            parts.append(SPECIAL_KEY_LABELS.get(token, token.upper()))
    return " + ".join(parts)


def parse_hotkey_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def preview_text(text: str, limit: int = 420) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."
