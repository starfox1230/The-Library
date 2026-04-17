from __future__ import annotations

from html.parser import HTMLParser
from typing import Any, Iterable, Mapping


def _first_srcset_url(value: str) -> str:
    for item in str(value or "").split(","):
        candidate = item.strip()
        if not candidate:
            continue
        return candidate.split()[0].strip()
    return ""


class _ImageSourceParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.sources: list[str] = []

    def _maybe_add_source(self, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {
            str(name).casefold(): "" if value is None else str(value).strip()
            for name, value in attrs
        }
        source = (
            attr_map.get("src")
            or attr_map.get("data-src")
            or attr_map.get("data-lazy-src")
            or attr_map.get("data-original")
            or _first_srcset_url(attr_map.get("srcset", ""))
        )
        if source:
            self.sources.append(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "img":
            self._maybe_add_source(attrs)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "img":
            self._maybe_add_source(attrs)


def extract_image_sources(html: str) -> list[str]:
    parser = _ImageSourceParser()
    parser.feed(html or "")
    parser.close()
    return list(parser.sources)


def merge_image_sources(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for group in groups:
        for raw_source in group:
            source = str(raw_source or "").strip()
            if not source or source in seen:
                continue
            seen.add(source)
            merged.append(source)

    return merged


def first_image_source(html: str) -> str:
    for source in extract_image_sources(html):
        if source:
            return source
    return ""


def _normalized_field_name(name: str) -> str:
    return "".join(char for char in str(name or "").casefold() if char.isalnum())


def _overlay_entry_key(layers: list[str]) -> str:
    if len(layers) == 1:
        return f"image::{layers[0]}"
    return f"layers::{'|'.join(layers)}"


def normalize_overlay_entry(raw_entry: Any) -> dict[str, Any] | None:
    if isinstance(raw_entry, str):
        layers = merge_image_sources([str(raw_entry).strip()])
        key = ""
    elif isinstance(raw_entry, Mapping):
        raw_layers = raw_entry.get("layers")
        if not isinstance(raw_layers, (list, tuple)):
            return None
        layers = merge_image_sources([str(value or "").strip() for value in raw_layers])
        key = str(raw_entry.get("key") or "").strip()
    else:
        return None

    if not layers:
        return None

    return {
        "key": key or _overlay_entry_key(layers),
        "layers": list(layers),
    }


def build_overlay_entries_from_sources(sources: Iterable[Any]) -> list[dict[str, Any]]:
    return merge_overlay_entries(sources)


def merge_overlay_entries(*groups: Iterable[Any]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()

    for group in groups:
        for raw_entry in group:
            entry = normalize_overlay_entry(raw_entry)
            if entry is None:
                continue
            key = str(entry.get("key") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(entry)

    return merged


def overlay_entry_layers(entry: Mapping[str, Any]) -> list[str]:
    raw_layers = entry.get("layers")
    if not isinstance(raw_layers, (list, tuple)):
        return []
    return merge_image_sources([str(value or "").strip() for value in raw_layers])


def has_layered_overlay_entries(entries: Iterable[Any]) -> bool:
    for raw_entry in entries:
        entry = normalize_overlay_entry(raw_entry)
        if entry is not None and len(overlay_entry_layers(entry)) > 1:
            return True
    return False


def _match_image_field(field_sources: Mapping[str, str]) -> str:
    for candidate in ("image", "img"):
        source = str(field_sources.get(candidate, "") or "").strip()
        if source:
            return source

    for field_name, source in field_sources.items():
        if "image" in field_name and "mask" not in field_name:
            return str(source or "").strip()

    return ""


def _match_mask_field(field_sources: Mapping[str, str], *, answer_side: bool) -> str:
    exact_candidates = ("answermask", "amask") if answer_side else ("questionmask", "qmask")
    word_candidates = ("answer", "mask") if answer_side else ("question", "mask")
    shorthand = "amask" if answer_side else "qmask"

    for candidate in exact_candidates:
        source = str(field_sources.get(candidate, "") or "").strip()
        if source:
            return source

    for field_name, source in field_sources.items():
        normalized_name = str(field_name or "").strip()
        if shorthand in normalized_name:
            return str(source or "").strip()
        if all(word in normalized_name for word in word_candidates):
            return str(source or "").strip()

    return ""


def build_image_occlusion_entry(
    note_fields: Mapping[str, str],
    *,
    answer_side: bool,
) -> dict[str, Any] | None:
    field_sources: dict[str, str] = {}

    for field_name, field_value in note_fields.items():
        source = first_image_source(str(field_value or ""))
        if not source:
            continue
        field_sources[_normalized_field_name(str(field_name or ""))] = source

    base_image = _match_image_field(field_sources)
    mask_image = _match_mask_field(field_sources, answer_side=answer_side)
    if not base_image or not mask_image:
        return None

    side_name = "answer" if answer_side else "question"
    return normalize_overlay_entry(
        {
            "key": f"image-occlusion::{side_name}::{base_image}::{mask_image}",
            "layers": [base_image, mask_image],
        }
    )
