from __future__ import annotations

from typing import Any

from .visual_mode import (
    VISUAL_MODE_CRYSTAL_REACTOR,
    VISUAL_MODE_LIGHTWEIGHT_ROWS,
    VISUAL_MODE_SINGULARITY,
    VISUAL_MODE_SPHERE,
    normalize_visual_mode,
)


COLOR_KEYS = ("core", "crystal", "red", "yellow", "green", "blue")
VISUAL_COLOR_KEYS = {
    VISUAL_MODE_SPHERE: ("core", "red", "yellow", "green", "blue"),
    VISUAL_MODE_CRYSTAL_REACTOR: ("crystal", "red", "yellow", "green", "blue"),
    VISUAL_MODE_LIGHTWEIGHT_ROWS: ("red", "yellow", "green", "blue"),
    VISUAL_MODE_SINGULARITY: ("core", "red", "yellow", "green", "blue"),
}


def normalize_palette_visual(value: Any) -> str:
    raw = str(value or "").strip().lower()
    aliases = {
        "satellite": VISUAL_MODE_SPHERE,
        "satellites": VISUAL_MODE_SPHERE,
        "orbit": VISUAL_MODE_SPHERE,
        "crystal": VISUAL_MODE_CRYSTAL_REACTOR,
        "reactor": VISUAL_MODE_CRYSTAL_REACTOR,
        "brick": VISUAL_MODE_LIGHTWEIGHT_ROWS,
        "bricks": VISUAL_MODE_LIGHTWEIGHT_ROWS,
        "rows": VISUAL_MODE_LIGHTWEIGHT_ROWS,
    }
    return aliases.get(raw, normalize_visual_mode(raw))


def normalize_hex_color(value: Any) -> str:
    color = str(value or "").strip().lower()
    if not color:
        return ""
    if not color.startswith("#"):
        color = f"#{color}"
    if len(color) == 4 and all(ch in "#0123456789abcdef" for ch in color):
        color = "#" + "".join(ch * 2 for ch in color[1:])
    if len(color) == 7 and all(ch in "#0123456789abcdef" for ch in color):
        return color
    return ""


def normalize_color_overrides(colors: Any, *, allowed_keys: tuple[str, ...] = COLOR_KEYS) -> dict[str, str]:
    if not isinstance(colors, dict):
        return {}
    normalized: dict[str, str] = {}
    for key in allowed_keys:
        color = normalize_hex_color(colors.get(key))
        if color:
            normalized[key] = color
    return normalized


def migrate_legacy_visual_palettes(legacy_colors: Any) -> dict[str, dict[str, str]]:
    legacy = normalize_color_overrides(legacy_colors)
    if not legacy:
        return {}
    return {
        visual: {key: legacy[key] for key in keys if key in legacy}
        for visual, keys in VISUAL_COLOR_KEYS.items()
    }


def normalize_visual_color_palettes(
    palettes: Any,
    *,
    legacy_colors: Any = None,
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    if isinstance(palettes, dict):
        for raw_visual, raw_palette in palettes.items():
            visual = normalize_palette_visual(raw_visual)
            # Unknown names normalize to Sphere, so reject them unless they are
            # a documented Sphere alias.
            raw_name = str(raw_visual or "").strip().lower()
            if visual == VISUAL_MODE_SPHERE and raw_name not in {
                "sphere", "satellite", "satellites", "orbit", "sphere_satellites"
            }:
                continue
            normalized = normalize_color_overrides(
                raw_palette,
                allowed_keys=VISUAL_COLOR_KEYS[visual],
            )
            if normalized:
                result[visual] = normalized
    if isinstance(palettes, dict):
        return result
    return migrate_legacy_visual_palettes(legacy_colors)


def palette_for_visual(
    palettes: Any,
    visual: Any,
    *,
    legacy_colors: Any = None,
) -> dict[str, str]:
    normalized = normalize_visual_color_palettes(palettes, legacy_colors=legacy_colors)
    visual_key = normalize_palette_visual(visual)
    if visual_key in normalized:
        return dict(normalized[visual_key])
    if isinstance(palettes, dict):
        return {}
    legacy = normalize_color_overrides(legacy_colors)
    return {
        key: legacy[key]
        for key in VISUAL_COLOR_KEYS[visual_key]
        if key in legacy
    }
