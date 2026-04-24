from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, unquote_to_bytes, urlparse
from urllib.request import url2pathname

from aqt import gui_hooks, mw
from aqt.qt import (
    QApplication,
    QByteArray,
    QColor,
    QEvent,
    QImage,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPointF,
    QRectF,
    QShortcut,
    Qt,
    QWidget,
)
from aqt.utils import tooltip

try:
    from aqt.qt import QSvgRenderer
except Exception:  # pragma: no cover - depends on Qt build
    QSvgRenderer = None

from .common import collection_media_dir, note_fields as extract_note_fields
from .review_image_overlay_core import (
    build_image_occlusion_entry,
    build_overlay_entries_from_sources,
    extract_image_sources,
    has_layered_overlay_entries,
    merge_overlay_entries,
    normalize_overlay_entry,
    overlay_entry_layers,
)
from .settings import get_setting, set_setting


SETTING_NAME = "review_image_overlay_shortcuts"
REMEMBER_POSITION_SETTING = "review_image_overlay_remember_position"
NEXT_SHORTCUT = "Ctrl+Shift+5"
PREVIOUS_SHORTCUT = "Ctrl+Shift+4"
EXIT_SHORTCUT = "Ctrl+2"
OVERLAY_ROOT_ID = "pocket-knife-review-image-overlay"
_HOOK_REGISTERED = False
_CONTROLLER: "_ReviewerImageOverlayController | None" = None
_REVIEWER_SHORTCUTS_PATCHED = False


def is_review_image_overlay_enabled() -> bool:
    return bool(get_setting(SETTING_NAME))


def set_review_image_overlay_enabled(enabled: bool) -> bool:
    value = bool(set_setting(SETTING_NAME, bool(enabled)))
    controller = _controller()
    if not value:
        controller.hide_overlay()
    return value


def is_review_image_overlay_remember_position_enabled() -> bool:
    return bool(get_setting(REMEMBER_POSITION_SETTING))


def set_review_image_overlay_remember_position_enabled(enabled: bool) -> bool:
    return bool(set_setting(REMEMBER_POSITION_SETTING, bool(enabled)))


def _reviewer_web():
    if getattr(mw, "state", "") != "review":
        return None
    reviewer = getattr(mw, "reviewer", None)
    return getattr(reviewer, "web", None) if reviewer is not None else None


def _card_id(card: Any) -> int:
    try:
        return int(getattr(card, "id", 0) or 0)
    except Exception:
        return 0


def _scroll_reviewer_to_top() -> None:
    web = _reviewer_web()
    if web is None:
        return

    web.eval(
        """
        (() => {
          const scrollTop = () => {
            try {
              window.scrollTo({ top: 0, left: 0, behavior: "auto" });
            } catch (_error) {
              window.scrollTo(0, 0);
            }
            if (document.documentElement) {
              document.documentElement.scrollTop = 0;
            }
            if (document.body) {
              document.body.scrollTop = 0;
            }
            const scrollers = Array.from(document.querySelectorAll("*")).filter((node) => {
              if (!(node instanceof HTMLElement)) {
                return false;
              }
              return node.scrollHeight > node.clientHeight;
            });
            scrollers.forEach((node) => {
              node.scrollTop = 0;
            });
          };

          scrollTop();
          requestAnimationFrame(scrollTop);
          setTimeout(scrollTop, 0);
        })();
        """
    )


def _card_note_fields(card: Any) -> dict[str, str]:
    note_getter = getattr(card, "note", None)
    if not callable(note_getter):
        return {}

    try:
        note = note_getter()
    except Exception:
        return {}

    try:
        return extract_note_fields(note)
    except Exception:
        return {}


def _entry_sources(entry: dict[str, Any] | None) -> set[str]:
    if not isinstance(entry, dict):
        return set()
    return set(overlay_entry_layers(entry))


def _is_image_occlusion_entry(entry: dict[str, Any] | None, *, answer_side: bool | None = None) -> bool:
    if not isinstance(entry, dict):
        return False
    key = str(entry.get("key", "") or "").strip()
    if answer_side is None:
        return key.startswith("image-occlusion::")
    side_name = "answer" if answer_side else "question"
    return key.startswith(f"image-occlusion::{side_name}::")


def _has_answer_image_occlusion_entry(entries: list[dict[str, Any]]) -> bool:
    return any(_is_image_occlusion_entry(entry, answer_side=True) for entry in entries)


def _question_overlay_entries(card: Any) -> list[dict[str, Any]]:
    question_html = str(card.question() or "")
    question_entries = build_overlay_entries_from_sources(extract_image_sources(question_html))
    occlusion_entry = build_image_occlusion_entry(_card_note_fields(card), answer_side=False)
    if occlusion_entry is None:
        return question_entries

    used_sources = _entry_sources(occlusion_entry)
    extra_entries = build_overlay_entries_from_sources(
        [source for source in extract_image_sources(question_html) if source not in used_sources]
    )
    return merge_overlay_entries([occlusion_entry], extra_entries)


def _answer_overlay_entries(card: Any, question_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    answer_html = str(card.answer() or "")
    occlusion_entry = build_image_occlusion_entry(_card_note_fields(card), answer_side=True)
    if occlusion_entry is not None:
        used_sources = _entry_sources(occlusion_entry)
        extra_entries = build_overlay_entries_from_sources(
            [source for source in extract_image_sources(answer_html) if source not in used_sources]
        )
        return merge_overlay_entries([occlusion_entry], extra_entries)

    answer_entries = build_overlay_entries_from_sources(extract_image_sources(answer_html))
    return merge_overlay_entries(question_entries, answer_entries)


def _normalize_overlay_entries(raw_value: Any) -> list[dict[str, Any]]:
    parsed = raw_value
    if isinstance(raw_value, str):
        text = raw_value.strip()
        if not text:
            return []
        try:
            parsed = json.loads(text)
        except Exception:
            parsed = [text]

    if not isinstance(parsed, list):
        return []

    return merge_overlay_entries(parsed)


def _visible_images_query_script() -> str:
    return f"""
    (() => {{
      const overlayRootId = {json.dumps(OVERLAY_ROOT_ID)};
      const unique = [];
      const seen = new Set();
      const isHidden = (node) => {{
        if (!(node instanceof Element)) {{
          return false;
        }}
        const style = window.getComputedStyle(node);
        if (
          style.display === "none"
          || style.visibility === "hidden"
          || Number(style.opacity || "1") === 0
        ) {{
          return true;
        }}
        return false;
      }};
      const isVisibleImage = (img) => {{
        if (!(img instanceof HTMLImageElement)) {{
          return false;
        }}
        if (img.closest(`#${{overlayRootId}}`)) {{
          return false;
        }}
        const rect = img.getBoundingClientRect();
        if (rect.width <= 1 || rect.height <= 1) {{
          return false;
        }}
        let current = img;
        while (current instanceof Element) {{
          if (isHidden(current)) {{
            return false;
          }}
          current = current.parentElement;
        }}
        return true;
      }};

      for (const img of Array.from(document.querySelectorAll("img"))) {{
        if (!isVisibleImage(img)) {{
          continue;
        }}
        const source = String(
          img.getAttribute("src")
          || img.getAttribute("data-src")
          || img.getAttribute("data-lazy-src")
          || img.getAttribute("data-original")
          || img.currentSrc
          || img.src
          || ""
        ).trim();
        if (!source || seen.has(source)) {{
          continue;
        }}
        seen.add(source);
        unique.push(source);
      }}

      return JSON.stringify(unique);
    }})();
    """


def _data_uri_bytes(source: str) -> bytes | None:
    header, separator, payload = str(source or "").partition(",")
    if not separator:
        return None

    if ";base64" in header.casefold():
        try:
            return base64.b64decode(payload, validate=False)
        except Exception:
            return None

    try:
        return unquote_to_bytes(payload)
    except Exception:
        return None


def _file_uri_path(source: str) -> Path | None:
    parsed = urlparse(source)
    if parsed.scheme.casefold() != "file":
        return None

    raw_path = url2pathname(f"{parsed.netloc}{parsed.path}")
    if len(raw_path) >= 3 and raw_path[0] == "/" and raw_path[2] == ":":
        raw_path = raw_path[1:]

    if not raw_path:
        return None

    return Path(unquote(raw_path))


def _local_media_path(source: str) -> Path | None:
    trimmed = str(source or "").strip()
    if not trimmed:
        return None

    cleaned = unquote(trimmed.split("#", 1)[0].split("?", 1)[0]).strip()
    if not cleaned:
        return None

    direct_path = Path(cleaned)
    if direct_path.is_absolute():
        return direct_path

    try:
        media_root = collection_media_dir()
    except Exception:
        return None

    relative_parts = cleaned.lstrip("/\\").replace("\\", "/").split("/")
    return media_root.joinpath(*[part for part in relative_parts if part])


def _anki_media_url_path(source: str) -> Path | None:
    parsed = urlparse(str(source or "").strip())
    if parsed.scheme.casefold() not in {"http", "https"}:
        return None

    request_path = unquote(parsed.path or "").replace("\\", "/")
    marker = "/_anki/media/"
    if marker not in request_path:
        return None

    relative_path = request_path.split(marker, 1)[1].lstrip("/")
    if not relative_path:
        return None

    try:
        media_root = collection_media_dir()
    except Exception:
        return None

    relative_parts = [part for part in relative_path.split("/") if part]
    if not relative_parts:
        return None

    return media_root.joinpath(*relative_parts)


def _source_bytes(source: str) -> bytes | None:
    trimmed = str(source or "").strip()
    if not trimmed:
        return None

    if trimmed.casefold().startswith("data:"):
        return _data_uri_bytes(trimmed)

    path = _file_uri_path(trimmed)
    if path is None:
        path = _anki_media_url_path(trimmed)
    if path is None:
        path = _local_media_path(trimmed)
    if path is None or not path.exists() or not path.is_file():
        return None

    try:
        return path.read_bytes()
    except Exception:
        return None


def _looks_like_svg(source: str, payload: bytes) -> bool:
    lowered = str(source or "").casefold()
    if lowered.endswith(".svg") or lowered.startswith("data:image/svg"):
        return True

    prefix = payload.lstrip()[:256].casefold()
    return b"<svg" in prefix


class _OverlayLayerAsset:
    def __init__(self, source: str) -> None:
        self.source = str(source or "").strip()
        self.image: QImage | None = None
        self.svg_renderer: Any = None
        self.width = 0
        self.height = 0
        self.error = ""
        self._load()

    @property
    def is_valid(self) -> bool:
        return self.width > 0 and self.height > 0 and (self.image is not None or self.svg_renderer is not None)

    def _load(self) -> None:
        payload = _source_bytes(self.source)
        if not payload:
            self.error = "Image source could not be resolved."
            return

        if QSvgRenderer is not None and _looks_like_svg(self.source, payload):
            try:
                renderer = QSvgRenderer(QByteArray(payload))
                if renderer.isValid():
                    size = renderer.defaultSize()
                    width = max(1, int(size.width()))
                    height = max(1, int(size.height()))
                    self.svg_renderer = renderer
                    self.width = width
                    self.height = height
                    return
            except Exception:
                pass

        image = QImage()
        if image.loadFromData(payload):
            self.image = image
            self.width = max(1, int(image.width()))
            self.height = max(1, int(image.height()))
            return

        self.error = "Image data could not be decoded."

    def paint(self, painter: QPainter, target_rect: QRectF) -> None:
        if not self.is_valid:
            return
        if self.svg_renderer is not None:
            self.svg_renderer.render(painter, target_rect)
            return
        if self.image is not None:
            painter.drawImage(
                target_rect,
                self.image,
                QRectF(0, 0, float(self.image.width()), float(self.image.height())),
            )


def _contained_rect(bounds: QRectF, *, width: int, height: int) -> QRectF:
    if width <= 0 or height <= 0 or bounds.width() <= 0 or bounds.height() <= 0:
        return QRectF(bounds)

    scale = min(bounds.width() / float(width), bounds.height() / float(height))
    target_width = width * scale
    target_height = height * scale
    offset_x = bounds.x() + ((bounds.width() - target_width) / 2.0)
    offset_y = bounds.y() + ((bounds.height() - target_height) / 2.0)
    return QRectF(offset_x, offset_y, target_width, target_height)


def _shortcut_text(value: Any) -> str:
    if isinstance(value, QKeySequence):
        try:
            text = value.toString(QKeySequence.SequenceFormat.PortableText)
        except Exception:
            text = value.toString()
        return str(text or "").strip()
    return str(value or "").strip()


def _shortcut_definition_matches(value: Any, shortcut_text: str) -> bool:
    left = _shortcut_text(value)
    right = _shortcut_text(shortcut_text)
    return bool(left and right and left.casefold() == right.casefold())


def _patch_reviewer_shortcuts() -> None:
    global _REVIEWER_SHORTCUTS_PATCHED

    if _REVIEWER_SHORTCUTS_PATCHED:
        return

    try:
        from aqt.reviewer import Reviewer
    except Exception:
        return

    if getattr(Reviewer, "_anki_pocket_knife_review_image_overlay_shortcuts_patched", False):
        _REVIEWER_SHORTCUTS_PATCHED = True
        return

    original = getattr(Reviewer, "_shortcutKeys", None)
    if not callable(original):
        return

    def wrapped(reviewer: Any):
        shortcuts = list(original(reviewer))
        patched: list[Any] = []
        replaced_exit_shortcut = False

        for shortcut in shortcuts:
            if not isinstance(shortcut, tuple) or len(shortcut) < 2:
                patched.append(shortcut)
                continue

            shortcut_key = shortcut[0]
            callback = shortcut[1]
            if not _shortcut_definition_matches(shortcut_key, EXIT_SHORTCUT):
                patched.append(shortcut)
                continue

            def overlay_aware_exit(_callback: Any = callback) -> None:
                if _controller().close_overlay_if_visible():
                    return
                if callable(_callback):
                    _callback()

            patched.append((shortcut_key, overlay_aware_exit, *shortcut[2:]))
            replaced_exit_shortcut = True

        if not replaced_exit_shortcut:
            return shortcuts

        return patched

    Reviewer._shortcutKeys = wrapped
    setattr(Reviewer, "_anki_pocket_knife_review_image_overlay_shortcuts_patched", True)
    _REVIEWER_SHORTCUTS_PATCHED = True


class _ReviewerImageOverlayWidget(QWidget):
    _PADDING = 20.0
    _PILL_MARGIN = 16.0
    _PILL_HEIGHT = 34.0
    _PILL_HORIZONTAL_PADDING = 14.0
    _DEFAULT_BACKGROUND = (0, 0, 0, 251)
    _LAST_IMAGE_BACKGROUND = (128, 0, 128, 251)

    def __init__(self) -> None:
        super().__init__(mw)
        self._entries: list[dict[str, Any]] = []
        self._index = 0
        self._asset_cache: dict[str, _OverlayLayerAsset] = {}
        self._app = QApplication.instance()
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        mw.installEventFilter(self)
        if self._app is not None:
            self._app.installEventFilter(self)
        self.hide()

    def eventFilter(self, watched: Any, event: Any) -> bool:
        if self.isVisible() and event is not None:
            event_type = event.type()
            action = self._shortcut_action_for_event(event)
            if event_type == QEvent.Type.ShortcutOverride and action is not None:
                if action == "close":
                    self.hide_overlay()
                    event.accept()
                    return True
                event.accept()
                return False
            if event_type == QEvent.Type.KeyPress and self._handle_shortcut_action(action):
                event.accept()
                return True

        if watched is mw and event is not None:
            event_type = event.type()
            if event_type in (
                QEvent.Type.Resize,
                QEvent.Type.Move,
                QEvent.Type.Show,
                QEvent.Type.WindowStateChange,
            ):
                self._sync_geometry()
            elif event_type == QEvent.Type.Hide:
                self.hide_overlay()
        return False

    def current_key(self) -> str:
        entry = self.current_entry()
        return str(entry.get("key", "") or "").strip() if entry is not None else ""

    def current_entry(self) -> dict[str, Any] | None:
        if not self._entries:
            return None
        return self._entries[self._index] if 0 <= self._index < len(self._entries) else None

    def set_entries(
        self,
        entries: list[dict[str, Any]],
        *,
        reset: bool = False,
        close: bool = False,
        preserve_current: bool = False,
    ) -> None:
        normalized_entries = [
            entry for entry in (normalize_overlay_entry(raw_entry) for raw_entry in entries) if entry is not None
        ]
        previous_key = self.current_key()
        self._entries = list(normalized_entries)

        if not self._entries:
            self._index = 0
            self.hide_overlay()
            self.update()
            return

        if reset:
            self._index = 0
        elif preserve_current and previous_key:
            preserved_index = next(
                (
                    index
                    for index, entry in enumerate(self._entries)
                    if str(entry.get("key", "") or "").strip() == previous_key
                ),
                -1,
            )
            self._index = preserved_index if preserved_index >= 0 else min(self._index, len(self._entries) - 1)
        else:
            self._index = min(self._index, len(self._entries) - 1)

        if close:
            self.hide_overlay()

        self.update()

    def show_next(self) -> bool:
        if not self._entries:
            self.hide_overlay()
            self.update()
            return False

        if not self.isVisible():
            self._sync_geometry()
            self.show()
            self.raise_()
            self.setFocus(Qt.FocusReason.ShortcutFocusReason)
            self.update()
            return True

        self._index = (self._index + 1) % len(self._entries)
        self.raise_()
        self.update()
        return True

    def show_previous(self) -> bool:
        if not self._entries or not self.isVisible():
            return False

        self._index = (self._index - 1) % len(self._entries)
        self.raise_()
        self.update()
        return True

    def hide_overlay(self) -> None:
        if self.isVisible():
            self.hide()

    def mousePressEvent(self, event: Any) -> None:
        if event is None:
            return
        point = self._event_point(event)
        if point is not None and self._close_button_rect().contains(point):
            self.hide_overlay()
        event.accept()

    def mouseDoubleClickEvent(self, event: Any) -> None:
        if event is not None:
            event.accept()

    def mouseReleaseEvent(self, event: Any) -> None:
        if event is not None:
            event.accept()

    def wheelEvent(self, event: Any) -> None:
        if event is not None:
            event.accept()

    def keyPressEvent(self, event: Any) -> None:
        if event is None:
            return
        if self._handle_shortcut_action(self._shortcut_action_for_event(event)):
            event.accept()
            return
        if getattr(event, "key", lambda: None)() == Qt.Key.Key_Escape:
            self.hide_overlay()
        event.accept()

    def keyReleaseEvent(self, event: Any) -> None:
        if event is not None:
            event.accept()

    def paintEvent(self, event: Any) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.fillRect(self.rect(), self._background_color())

        entry = self.current_entry()
        if entry is None:
            return

        assets = self._assets_for_entry(entry)
        if not assets:
            self._draw_center_message(painter, "Image could not be loaded.")
            self._draw_close_button(painter)
            self._draw_counter(painter)
            return

        reference_asset = assets[0]
        available = QRectF(
            self._PADDING,
            self._PADDING,
            max(0.0, float(self.width()) - (self._PADDING * 2.0)),
            max(0.0, float(self.height()) - (self._PADDING * 2.0)),
        )
        target = _contained_rect(
            available,
            width=reference_asset.width,
            height=reference_asset.height,
        )
        for asset in assets:
            asset.paint(painter, target)

        self._draw_close_button(painter)
        self._draw_counter(painter)

    def _sync_geometry(self) -> None:
        self.setGeometry(mw.rect())
        if self.isVisible():
            self.raise_()

    def _assets_for_entry(self, entry: dict[str, Any]) -> list[_OverlayLayerAsset]:
        assets: list[_OverlayLayerAsset] = []
        for source in overlay_entry_layers(entry):
            cached = self._asset_cache.get(source)
            if cached is None:
                cached = _OverlayLayerAsset(source)
                self._asset_cache[source] = cached
            if cached.is_valid:
                assets.append(cached)
        return assets

    def _background_color(self) -> QColor:
        rgba = self._DEFAULT_BACKGROUND
        if self._entries and self._index == len(self._entries) - 1:
            rgba = self._LAST_IMAGE_BACKGROUND
        return QColor(*rgba)

    def _draw_center_message(self, painter: QPainter, message: str) -> None:
        painter.save()
        painter.setPen(QColor(255, 255, 255, 220))
        text_rect = QRectF(40, 40, max(0.0, float(self.width() - 80)), max(0.0, float(self.height() - 80)))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(message or ""))
        painter.restore()

    def _draw_counter(self, painter: QPainter) -> None:
        if not self._entries:
            return

        counter_text = f"{self._index + 1} / {len(self._entries)}"
        self._draw_pill(
            painter,
            self._counter_rect(counter_text),
            counter_text,
            background=QColor(255, 255, 255, 20),
            foreground=QColor(255, 255, 255, 235),
        )

    def _draw_close_button(self, painter: QPainter) -> None:
        self._draw_pill(
            painter,
            self._close_button_rect(),
            "X Close",
            background=QColor(255, 255, 255, 28),
            foreground=QColor(255, 255, 255, 245),
        )

    def _shortcut_action_for_event(self, event: Any) -> str | None:
        if event is None:
            return None

        if getattr(event, "key", lambda: None)() == Qt.Key.Key_Escape:
            return "close"
        if self._event_matches_shortcut(event, EXIT_SHORTCUT):
            return "close"
        if self._event_matches_shortcut(event, PREVIOUS_SHORTCUT):
            return "previous"
        if self._event_matches_shortcut(event, NEXT_SHORTCUT):
            return "next"
        return None

    def _handle_shortcut_action(self, action: str | None) -> bool:
        if action == "close":
            self.hide_overlay()
            return True
        if action == "previous":
            return self.show_previous()
        if action == "next":
            return self.show_next()
        return False

    def _event_matches_shortcut(self, event: Any, shortcut_text: str) -> bool:
        key_getter = getattr(event, "key", None)
        modifiers_getter = getattr(event, "modifiers", None)
        if not callable(key_getter) or not callable(modifiers_getter):
            return False

        try:
            sequence = QKeySequence(int(modifiers_getter()) | int(key_getter()))
            target = QKeySequence(str(shortcut_text or ""))
            return sequence.matches(target) == QKeySequence.SequenceMatch.ExactMatch
        except Exception:
            return False

    def _counter_rect(self, counter_text: str) -> QRectF:
        return self._pill_rect(
            counter_text,
            align_right=True,
        )

    def _close_button_rect(self) -> QRectF:
        return self._pill_rect(
            "X Close",
            align_right=False,
        )

    def _pill_rect(self, text: str, *, align_right: bool) -> QRectF:
        metrics = self.fontMetrics()
        text_rect = metrics.boundingRect(str(text or ""))
        pill_width = float(text_rect.width() + (self._PILL_HORIZONTAL_PADDING * 2.0))
        pill_height = self._PILL_HEIGHT
        pill_left = (
            float(self.width()) - pill_width - self._PILL_MARGIN
            if align_right
            else self._PILL_MARGIN
        )
        return QRectF(pill_left, self._PILL_MARGIN, pill_width, pill_height)

    def _draw_pill(
        self,
        painter: QPainter,
        rect: QRectF,
        text: str,
        *,
        background: QColor,
        foreground: QColor,
    ) -> None:
        painter.save()
        path = QPainterPath()
        path.addRoundedRect(rect, rect.height() / 2.0, rect.height() / 2.0)
        painter.fillPath(path, background)
        painter.setPen(foreground)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, str(text or ""))
        painter.restore()

    def _event_point(self, event: Any) -> QPointF | None:
        position_getter = getattr(event, "position", None)
        if callable(position_getter):
            try:
                return position_getter()
            except Exception:
                pass
        pos_getter = getattr(event, "pos", None)
        if callable(pos_getter):
            try:
                pos = pos_getter()
                return QPointF(float(pos.x()), float(pos.y()))
            except Exception:
                return None
        return None


class _ReviewerImageOverlayController:
    def __init__(self) -> None:
        self._cycle_shortcut: QShortcut | None = None
        self._previous_shortcut: QShortcut | None = None
        self._question_entries: list[dict[str, Any]] = []
        self._active_entries: list[dict[str, Any]] = []
        self._current_card_id = 0
        self._overlay_widget: _ReviewerImageOverlayWidget | None = None

    def install(self) -> None:
        if self._cycle_shortcut is None:
            self._cycle_shortcut = QShortcut(QKeySequence(NEXT_SHORTCUT), mw)
            self._cycle_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._cycle_shortcut.activated.connect(self.on_cycle_shortcut)

        if self._previous_shortcut is None:
            self._previous_shortcut = QShortcut(QKeySequence(PREVIOUS_SHORTCUT), mw)
            self._previous_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
            self._previous_shortcut.activated.connect(self.on_previous_shortcut)

        self._overlay()

    def on_reviewer_did_show_question(self, card: Any) -> None:
        self._current_card_id = _card_id(card)
        self._question_entries = _question_overlay_entries(card)
        self._active_entries = list(self._question_entries)
        self._sync_overlay(reset=True, close=True, preserve_current=False)

    def on_reviewer_did_show_answer(self, card: Any) -> None:
        card_id = _card_id(card)
        if card_id != self._current_card_id:
            self._current_card_id = card_id
            self._question_entries = _question_overlay_entries(card)
        overlay = self._overlay()
        keep_visible_for_occlusion_answer = bool(overlay.isVisible())
        self._active_entries = _answer_overlay_entries(card, self._question_entries)
        keep_visible_for_occlusion_answer = (
            keep_visible_for_occlusion_answer
            and _has_answer_image_occlusion_entry(self._active_entries)
        )
        self._sync_overlay(
            reset=True,
            close=not keep_visible_for_occlusion_answer,
            preserve_current=False,
        )

    def on_reviewer_did_answer_card(self, reviewer: Any, card: Any, ease: int) -> None:
        del reviewer
        del card
        del ease
        self.hide_overlay()

    def on_cycle_shortcut(self) -> None:
        if not is_review_image_overlay_enabled():
            return
        if _reviewer_web() is None:
            return
        if not has_layered_overlay_entries(self._active_entries) and self._refresh_active_images_from_dom(
            self._show_next_entry
        ):
            return
        self._show_next_entry(list(self._active_entries))

    def on_previous_shortcut(self) -> None:
        if not is_review_image_overlay_enabled():
            return
        if _reviewer_web() is None:
            return
        self._overlay().show_previous()

    def close_overlay_if_visible(self) -> bool:
        overlay = self._overlay()
        if not overlay.isVisible():
            return False
        overlay.hide_overlay()
        return True

    def hide_overlay(self, *, scroll_to_top: bool = False) -> None:
        overlay = self._overlay()
        if self._active_entries and not is_review_image_overlay_remember_position_enabled():
            overlay.set_entries(
                self._active_entries,
                reset=True,
                close=True,
                preserve_current=False,
            )
        else:
            overlay.hide_overlay()
        if scroll_to_top:
            _scroll_reviewer_to_top()

    def _show_next_entry(self, entries: list[dict[str, Any]]) -> None:
        self._active_entries = [
            entry for entry in (normalize_overlay_entry(raw_entry) for raw_entry in entries) if entry is not None
        ]
        if not self._active_entries:
            tooltip("No images found on the current card.")
            self.hide_overlay()
            return

        overlay = self._overlay()
        overlay.set_entries(
            self._active_entries,
            preserve_current=True,
        )
        overlay.show_next()

    def _refresh_active_images_from_dom(
        self,
        callback: Callable[[list[dict[str, Any]]], None],
    ) -> bool:
        web = _reviewer_web()
        if web is None:
            return False

        eval_with_callback = getattr(web, "evalWithCallback", None)
        if not callable(eval_with_callback):
            return False

        def on_result(value: Any) -> None:
            callback(_normalize_overlay_entries(value))

        eval_with_callback(_visible_images_query_script(), on_result)
        return True

    def _sync_overlay(self, *, reset: bool, close: bool, preserve_current: bool) -> None:
        if not is_review_image_overlay_enabled():
            self.hide_overlay()
            return
        self._overlay().set_entries(
            self._active_entries,
            reset=reset,
            close=close,
            preserve_current=preserve_current,
        )

    def _overlay(self) -> _ReviewerImageOverlayWidget:
        if self._overlay_widget is None:
            self._overlay_widget = _ReviewerImageOverlayWidget()
        return self._overlay_widget


def _controller() -> _ReviewerImageOverlayController:
    global _CONTROLLER
    if _CONTROLLER is None:
        _CONTROLLER = _ReviewerImageOverlayController()
    return _CONTROLLER


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    _patch_reviewer_shortcuts()
    controller = _controller()
    controller.install()

    reviewer_show_question = getattr(gui_hooks, "reviewer_did_show_question", None)
    if reviewer_show_question is not None:
        reviewer_show_question.append(controller.on_reviewer_did_show_question)

    reviewer_show_answer = getattr(gui_hooks, "reviewer_did_show_answer", None)
    if reviewer_show_answer is not None:
        reviewer_show_answer.append(controller.on_reviewer_did_show_answer)

    reviewer_answer = getattr(gui_hooks, "reviewer_did_answer_card", None)
    if reviewer_answer is not None:
        reviewer_answer.append(controller.on_reviewer_did_answer_card)

    _HOOK_REGISTERED = True
