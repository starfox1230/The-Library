from __future__ import annotations

from typing import Dict

from aqt.qt import QColor


DEFAULT_FLAG_PALETTE: Dict[int, str] = {
    0: "#8c96ac",
    1: "#ff7b7b",
    2: "#f5aa41",
    3: "#86ce5d",
    4: "#6f9dff",
    5: "#f097e4",
    6: "#5ccfca",
    7: "#9f63d3",
}


def _normalize_color(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    color = QColor(text)
    return color.name() if color.isValid() else text


def get_anki_flag_palette() -> Dict[int, str]:
    palette = dict(DEFAULT_FLAG_PALETTE)
    try:
        from aqt import colors as anki_colors
        from aqt.theme import theme_manager

        for index in range(1, 8):
            raw = getattr(anki_colors, f"FLAG_{index}", None)
            resolved = theme_manager.var(raw) if isinstance(raw, dict) else raw
            normalized = _normalize_color(resolved)
            if normalized:
                palette[index] = normalized
    except Exception:
        pass
    return palette
