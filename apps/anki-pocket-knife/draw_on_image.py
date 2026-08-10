from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    QColor,
    QColorDialog,
    QDialog,
    QFrame,
    QGuiApplication,
    QHBoxLayout,
    QImage,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPointF,
    QPolygonF,
    QPushButton,
    QRectF,
    QSizePolicy,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning

from .common import collection_media_dir
from .settings import load_settings, save_settings


COMMAND_PREFIX = "pocket_knife_draw_on_image:"
DEFAULT_COLOR = "#FFAA00"
DEFAULT_TOOL = "arrow"
DEFAULT_WIDTH = 8
_HOOK_REGISTERED = False
_BRIDGE_PATCHED = False
_dialog: "DrawOnImageDialog | None" = None


def _file_uri_path(source: str) -> Path | None:
    parsed = urlparse(source)
    if parsed.scheme.casefold() != "file":
        return None

    raw_path = url2pathname(f"{parsed.netloc}{parsed.path}")
    if len(raw_path) >= 3 and raw_path[0] == "/" and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return Path(unquote(raw_path)) if raw_path else None


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

    parts = [part for part in relative_path.split("/") if part]
    return collection_media_dir().joinpath(*parts)


def _local_media_path(source: str) -> Path | None:
    trimmed = str(source or "").strip()
    if not trimmed:
        return None

    cleaned = unquote(trimmed.split("#", 1)[0].split("?", 1)[0]).strip()
    if not cleaned:
        return None

    direct = Path(cleaned)
    if direct.is_absolute():
        return direct

    parts = cleaned.lstrip("/\\").replace("\\", "/").split("/")
    return collection_media_dir().joinpath(*[part for part in parts if part])


def _source_image_path(payload: dict) -> Path | None:
    candidates = [
        str(payload.get("src_attr") or ""),
        str(payload.get("src") or ""),
    ]
    for source in candidates:
        if not source:
            continue
        for resolver in (_file_uri_path, _anki_media_url_path, _local_media_path):
            try:
                path = resolver(source)
            except Exception:
                path = None
            if path is not None and path.exists() and path.is_file():
                return path
    return None


@dataclass
class Stroke:
    tool: str
    color: str
    width: float
    points: list[QPointF] = field(default_factory=list)


@dataclass
class AnnotationPreferences:
    color: str = DEFAULT_COLOR
    tool: str = DEFAULT_TOOL
    arrow_width: int = DEFAULT_WIDTH
    pen_width: int = DEFAULT_WIDTH

    def width_for(self, tool: str) -> int:
        return self.pen_width if tool == "pen" else self.arrow_width

    def set_width_for(self, tool: str, width: int) -> None:
        if tool == "pen":
            self.pen_width = width
        else:
            self.arrow_width = width


def _valid_width(value) -> int:
    try:
        return max(2, min(30, int(value)))
    except Exception:
        return DEFAULT_WIDTH


def _load_annotation_preferences() -> AnnotationPreferences:
    settings = load_settings()
    color = QColor(str(settings.get("draw_on_image_color", DEFAULT_COLOR)))
    tool = str(settings.get("draw_on_image_tool", DEFAULT_TOOL))
    return AnnotationPreferences(
        color=color.name().upper() if color.isValid() else DEFAULT_COLOR,
        tool=tool if tool in {"arrow", "pen"} else DEFAULT_TOOL,
        arrow_width=_valid_width(
            settings.get("draw_on_image_arrow_width", DEFAULT_WIDTH)
        ),
        pen_width=_valid_width(settings.get("draw_on_image_pen_width", DEFAULT_WIDTH)),
    )


def _save_annotation_preferences(preferences: AnnotationPreferences) -> None:
    settings = load_settings()
    settings.update(
        {
            "draw_on_image_color": preferences.color,
            "draw_on_image_tool": preferences.tool,
            "draw_on_image_arrow_width": preferences.arrow_width,
            "draw_on_image_pen_width": preferences.pen_width,
        }
    )
    save_settings(settings)


class DrawingCanvas(QWidget):
    def __init__(self, image: QImage, parent=None) -> None:
        super().__init__(parent)
        self._image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.tool = DEFAULT_TOOL
        self.pen_color = QColor(DEFAULT_COLOR)
        self.pen_size = float(DEFAULT_WIDTH)
        self._strokes: list[Stroke] = []
        self._redo: list[Stroke] = []
        self._active: Stroke | None = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_pen_color(self, color: QColor) -> None:
        if color.isValid():
            self.pen_color = QColor(color)

    def set_pen_size(self, size: int) -> None:
        self.pen_size = float(max(2, min(30, int(size))))

    def set_tool(self, tool: str) -> None:
        if tool not in {"arrow", "pen"}:
            raise ValueError(f"Unknown drawing tool: {tool}")
        self.tool = tool

    def _target_rect(self) -> QRectF:
        available = QRectF(self.rect()).adjusted(8, 8, -8, -8)
        if (
            available.width() <= 0
            or available.height() <= 0
            or self._image.width() <= 0
            or self._image.height() <= 0
        ):
            return QRectF()
        scale = min(
            available.width() / self._image.width(),
            available.height() / self._image.height(),
        )
        width = self._image.width() * scale
        height = self._image.height() * scale
        return QRectF(
            available.center().x() - width / 2,
            available.center().y() - height / 2,
            width,
            height,
        )

    def _image_point(self, pos: QPointF) -> QPointF | None:
        target = self._target_rect()
        if target.isEmpty() or not target.contains(pos):
            return None
        return QPointF(
            (pos.x() - target.left()) * self._image.width() / target.width(),
            (pos.y() - target.top()) * self._image.height() / target.height(),
        )

    def undo(self) -> None:
        if self._strokes:
            self._redo.append(self._strokes.pop())
            self.update()

    def redo(self) -> None:
        if self._redo:
            self._strokes.append(self._redo.pop())
            self.update()

    def clear(self) -> None:
        if not self._strokes:
            return
        self._redo.extend(reversed(self._strokes))
        self._strokes.clear()
        self.update()

    @staticmethod
    def _draw_stroke(painter: QPainter, stroke: Stroke) -> None:
        if len(stroke.points) < 2:
            return

        painter.save()
        pen = QPen(QColor(stroke.color), stroke.width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QColor(stroke.color))

        if stroke.tool == "arrow":
            start, end = stroke.points[0], stroke.points[-1]
            painter.drawLine(start, end)
            angle = math.atan2(end.y() - start.y(), end.x() - start.x())
            head_length = max(18.0, stroke.width * 4.2)
            wing = math.radians(28)
            left = QPointF(
                end.x() - head_length * math.cos(angle - wing),
                end.y() - head_length * math.sin(angle - wing),
            )
            right = QPointF(
                end.x() - head_length * math.cos(angle + wing),
                end.y() - head_length * math.sin(angle + wing),
            )
            painter.drawPolygon(QPolygonF([end, left, right]))
            painter.restore()
            return

        path = QPainterPath(stroke.points[0])
        if len(stroke.points) == 2:
            path.lineTo(stroke.points[1])
        else:
            for index in range(1, len(stroke.points) - 1):
                point = stroke.points[index]
                following = stroke.points[index + 1]
                midpoint = QPointF(
                    (point.x() + following.x()) / 2,
                    (point.y() + following.y()) / 2,
                )
                path.quadTo(point, midpoint)
            path.lineTo(stroke.points[-1])
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        painter.restore()

    def _paint_image_contents(self, painter: QPainter, include_active: bool) -> None:
        painter.drawImage(QPointF(0, 0), self._image)
        for stroke in self._strokes:
            self._draw_stroke(painter, stroke)
        if include_active and self._active is not None:
            self._draw_stroke(painter, self._active)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#05080D"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        target = self._target_rect()
        if target.isEmpty():
            return
        painter.translate(target.left(), target.top())
        painter.scale(
            target.width() / self._image.width(),
            target.height() / self._image.height(),
        )
        self._paint_image_contents(painter, include_active=True)

    def rendered_image(self) -> QImage:
        rendered = self._image.copy()
        painter = QPainter(rendered)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        for stroke in self._strokes:
            self._draw_stroke(painter, stroke)
        painter.end()
        return rendered

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self._image_point(event.position())
        if point is None:
            return
        self._active = Stroke(
            self.tool,
            self.pen_color.name().upper(),
            self.pen_size,
            [point],
        )
        self._redo.clear()
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        point = self._image_point(event.position())
        if point is None or self._active is None:
            return
        if self._active.tool == "arrow":
            if len(self._active.points) == 1:
                self._active.points.append(point)
            else:
                self._active.points[-1] = point
        else:
            self._active.points.append(point)
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton or self._active is None:
            return
        point = self._image_point(event.position())
        if point is not None:
            if self._active.tool == "arrow":
                if len(self._active.points) == 1:
                    self._active.points.append(point)
                else:
                    self._active.points[-1] = point
            elif len(self._active.points) == 1:
                self._active.points.append(point)
        if len(self._active.points) >= 2:
            self._strokes.append(self._active)
        self._active = None
        self.update()


class DrawOnImageDialog(QDialog):
    def __init__(self, image_path: Path, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Annotate Image")
        self.setWindowState(self.windowState() | Qt.WindowState.WindowFullScreen)
        image = QImage(str(image_path))
        if image.isNull():
            raise RuntimeError("Anki Pocket Knife could not open that image.")
        self.canvas = DrawingCanvas(image, self)
        self._preferences = _load_annotation_preferences()
        self._applying_preferences = False
        self._build_ui()
        self._apply_preferences()
        self._fill_available_screen()

    def _fill_available_screen(self) -> None:
        screen = None
        window_handle = self.windowHandle()
        if window_handle is not None:
            screen = window_handle.screen()
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.availableGeometry())

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        toolbar_frame = QFrame()
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(8, 6, 8, 6)

        self.arrow_button = QPushButton("Arrow")
        self.draw_button = QPushButton("Draw")
        self.arrow_button.setCheckable(True)
        self.draw_button.setCheckable(True)
        self.arrow_button.setChecked(True)

        self.color_button = QPushButton(DEFAULT_COLOR)
        self.color_button.setStyleSheet(
            f"background: {DEFAULT_COLOR}; color: #111; font-weight: 600;"
        )
        self.size_label = QLabel("Width: 8")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(2, 30)
        self.size_slider.setValue(8)
        self.size_slider.setFixedWidth(140)

        undo_button = QPushButton("Undo")
        redo_button = QPushButton("Redo")
        clear_button = QPushButton("Clear Drawing")
        reset_defaults_button = QPushButton("Reset Defaults")
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        toolbar.addWidget(self.arrow_button)
        toolbar.addWidget(self.draw_button)
        toolbar.addSpacing(12)
        toolbar.addWidget(QLabel("Color:"))
        toolbar.addWidget(self.color_button)
        toolbar.addSpacing(12)
        toolbar.addWidget(self.size_label)
        toolbar.addWidget(self.size_slider)
        toolbar.addSpacing(12)
        toolbar.addWidget(undo_button)
        toolbar.addWidget(redo_button)
        toolbar.addWidget(clear_button)
        toolbar.addWidget(reset_defaults_button)
        toolbar.addStretch(1)
        toolbar.addWidget(ok_button)
        toolbar.addWidget(cancel_button)
        layout.addWidget(toolbar_frame)
        layout.addWidget(self.canvas, 1)

        self.arrow_button.clicked.connect(lambda: self._set_tool("arrow"))
        self.draw_button.clicked.connect(lambda: self._set_tool("pen"))
        self.color_button.clicked.connect(self._choose_color)
        self.size_slider.valueChanged.connect(self._set_pen_size)
        undo_button.clicked.connect(self.canvas.undo)
        redo_button.clicked.connect(self.canvas.redo)
        clear_button.clicked.connect(self.canvas.clear)
        reset_defaults_button.clicked.connect(self._reset_preferences)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.setStyleSheet(
            """
            QDialog, QWidget {
                background: #09101C;
                color: #EEF4FC;
                font-family: "Segoe UI";
                font-size: 10pt;
            }
            QFrame {
                background: #101B2B;
                border: 1px solid #26364D;
                border-radius: 8px;
            }
            QPushButton {
                background: #17273A;
                border: 1px solid #36516F;
                border-radius: 6px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background: #203752;
                border-color: #4D7097;
            }
            QPushButton:checked {
                background: #9B6800;
                border-color: #FFAA00;
            }
            """
        )

    def _set_tool(self, tool: str) -> None:
        self.canvas.set_tool(tool)
        self._preferences.tool = tool
        self.arrow_button.setChecked(tool == "arrow")
        self.draw_button.setChecked(tool == "pen")
        width = self._preferences.width_for(tool)
        self._applying_preferences = True
        try:
            self.size_slider.setValue(width)
            self.canvas.set_pen_size(width)
            self.size_label.setText(f"Width: {width}")
        finally:
            self._applying_preferences = False
        _save_annotation_preferences(self._preferences)

    def _set_color_button(self, color: QColor) -> None:
        color_name = color.name().upper()
        self.color_button.setText(color_name)
        text_color = "#111" if color.lightness() > 140 else "#fff"
        self.color_button.setStyleSheet(
            f"background: {color_name}; color: {text_color}; font-weight: 600;"
        )

    def _apply_preferences(self) -> None:
        self._applying_preferences = True
        try:
            color = QColor(self._preferences.color)
            self.canvas.set_pen_color(color)
            self._set_color_button(color)
            self.canvas.set_tool(self._preferences.tool)
            self.arrow_button.setChecked(self._preferences.tool == "arrow")
            self.draw_button.setChecked(self._preferences.tool == "pen")
            width = self._preferences.width_for(self._preferences.tool)
            self.size_slider.setValue(width)
            self.canvas.set_pen_size(width)
            self.size_label.setText(f"Width: {width}")
        finally:
            self._applying_preferences = False

    def _reset_preferences(self) -> None:
        self._preferences = AnnotationPreferences()
        self._apply_preferences()
        _save_annotation_preferences(self._preferences)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Choose Pen Color")
        if not color.isValid():
            return
        self.canvas.set_pen_color(color)
        self._set_color_button(color)
        self._preferences.color = color.name().upper()
        _save_annotation_preferences(self._preferences)

    def _set_pen_size(self, value: int) -> None:
        self.canvas.set_pen_size(int(value))
        self.size_label.setText(f"Width: {int(value)}")
        if self._applying_preferences:
            return
        self._preferences.set_width_for(self.canvas.tool, int(value))
        _save_annotation_preferences(self._preferences)

    def copy_to_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("The system clipboard is not available.")
        clipboard.setImage(self.canvas.rendered_image())

    def copy_to_clipboard_and_close(self) -> None:
        self.copy_to_clipboard()
        self.accept()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        modifiers = event.modifiers()
        ctrl = bool(modifiers & Qt.KeyboardModifier.ControlModifier)
        shift = bool(modifiers & Qt.KeyboardModifier.ShiftModifier)
        if ctrl and key == Qt.Key.Key_Z:
            if shift:
                self.canvas.redo()
            else:
                self.canvas.undo()
            event.accept()
            return
        if ctrl and key == Qt.Key.Key_Y:
            self.canvas.redo()
            event.accept()
            return
        if ctrl and key == Qt.Key.Key_C:
            self.copy_to_clipboard_and_close()
            event.accept()
            return
        super().keyPressEvent(event)


def _eval_editor_js(editor: Editor, body: str) -> None:
    web = getattr(editor, "web", None)
    if web is None:
        return
    web.eval(
        """
(() => {
  const run = () => {
%s
  };
  if (typeof require === "function") {
    try {
      require("anki/ui").loaded.then(run);
      return;
    } catch (_error) {}
  }
  run();
})();
"""
        % body
    )


def _sync_editor_js(editor: Editor) -> None:
    _eval_editor_js(editor, _build_editor_script())


def _build_editor_script() -> str:
    return r"""
const globalKey = "__ankiPocketKnifeDrawOnImage";
const state = window[globalKey] || (window[globalKey] = { targets: new Map(), nextId: 1, lastImage: null, installed: false });

function removeMenu() {
  const existing = document.getElementById("pocket-knife-draw-image-menu");
  if (existing) {
    existing.remove();
  }
}

function scheduleRemoveMenu() {
  window.setTimeout(removeMenu, 5000);
}

function imageFromEvent(event) {
  const path = typeof event.composedPath === "function" ? event.composedPath() : [];
  for (const node of path) {
    if (node instanceof HTMLImageElement) {
      return node;
    }
    if (node instanceof Element) {
      const image = node.closest("img");
      if (image) {
        return image;
      }
    }
  }
  if (state.lastImage && state.lastImage.isConnected) {
    return state.lastImage;
  }
  return null;
}

function rememberImage(event) {
  state.lastImage = imageFromEvent(event);
}

function showDrawMenu(event) {
  const image = imageFromEvent(event);
  if (!image) {
    return;
  }

  removeMenu();

  let targetId = image.getAttribute("data-pocket-knife-draw-target");
  if (!targetId) {
    targetId = String(state.nextId++);
    image.setAttribute("data-pocket-knife-draw-target", targetId);
  }
  state.targets.set(targetId, image);

  const menu = document.createElement("div");
  menu.id = "pocket-knife-draw-image-menu";
  menu.textContent = "Draw on Image";
  menu.style.position = "fixed";
  const menuWidth = 160;
  const menuHeight = 38;
  menu.style.left = `${Math.max(0, Math.min(event.clientX, window.innerWidth - menuWidth))}px`;
  menu.style.top = `${Math.max(0, event.clientY - menuHeight - 8)}px`;
  menu.style.zIndex = "2147483647";
  menu.style.padding = "8px 12px";
  menu.style.border = "1px solid rgba(0,0,0,.22)";
  menu.style.borderRadius = "6px";
  menu.style.background = "var(--canvas, #fff)";
  menu.style.color = "var(--fg, #111)";
  menu.style.boxShadow = "0 4px 18px rgba(0,0,0,.22)";
  menu.style.font = "13px system-ui, sans-serif";
  menu.style.cursor = "default";
  menu.addEventListener("pointerdown", (pointerEvent) => {
    pointerEvent.preventDefault();
    pointerEvent.stopPropagation();
  }, true);
  menu.addEventListener("mousedown", (mouseEvent) => {
    mouseEvent.preventDefault();
    mouseEvent.stopPropagation();
  }, true);
  menu.addEventListener("click", (clickEvent) => {
    clickEvent.preventDefault();
    clickEvent.stopPropagation();
    const payload = {
      target_id: targetId,
      src: image.src || "",
      src_attr: image.getAttribute("src") || ""
    };
    removeMenu();
    pycmd("pocket_knife_draw_on_image:" + encodeURIComponent(JSON.stringify(payload)));
  });
  document.body.appendChild(menu);
  scheduleRemoveMenu();
}

if (!state.installed) {
  document.addEventListener("click", removeMenu, true);
  document.addEventListener("scroll", removeMenu, true);
  document.addEventListener("pointerdown", rememberImage, true);
  document.addEventListener("mousedown", rememberImage, true);
  document.addEventListener("mouseover", rememberImage, true);
  document.addEventListener("contextmenu", showDrawMenu, true);
  state.installed = true;
}
"""

def _handle_draw_command(editor: Editor, cmd: str) -> bool:
    if not cmd.startswith(COMMAND_PREFIX):
        return False

    raw_payload = unquote(cmd[len(COMMAND_PREFIX) :])
    try:
        payload = json.loads(raw_payload)
    except Exception as exc:
        showWarning(f"Could not read the selected image information.\n\n{exc}")
        return True

    image_path = _source_image_path(payload if isinstance(payload, dict) else {})
    if image_path is None:
        showWarning("Could not find that image in the Anki media folder.")
        return True

    global _dialog
    try:
        _dialog = DrawOnImageDialog(image_path, getattr(editor, "parentWindow", None) or mw)
        accepted = _dialog.exec()
        if not accepted:
            return True
        _dialog.copy_to_clipboard()
    except Exception as exc:
        showWarning(f"Could not draw on that image.\n\n{exc}")
    finally:
        _dialog = None
    return True


def _patch_editor_bridge() -> None:
    global _BRIDGE_PATCHED
    if _BRIDGE_PATCHED:
        return

    original = getattr(Editor, "onBridgeCmd", None)
    if not callable(original):
        return

    def wrapped(editor: Editor, cmd: str):
        if _handle_draw_command(editor, cmd):
            return None
        return original(editor, cmd)

    Editor.onBridgeCmd = wrapped
    _BRIDGE_PATCHED = True


def install() -> None:
    global _HOOK_REGISTERED
    if _HOOK_REGISTERED:
        return

    gui_hooks.editor_did_init.append(_sync_editor_js)
    gui_hooks.editor_did_load_note.append(_sync_editor_js)
    _patch_editor_bridge()
    _HOOK_REGISTERED = True
