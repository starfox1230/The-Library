from __future__ import annotations

from html.parser import HTMLParser


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
