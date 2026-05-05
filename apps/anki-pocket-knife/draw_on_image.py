from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    QColor,
    QColorDialog,
    QDialog,
    QGuiApplication,
    QHBoxLayout,
    QImage,
    QLabel,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPushButton,
    QSizePolicy,
    QSlider,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import showWarning

from .common import collection_media_dir


COMMAND_PREFIX = "pocket_knife_draw_on_image:"
DEFAULT_COLOR = "#FFAA00"
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


class DrawingCanvas(QWidget):
    def __init__(self, image: QImage, parent=None) -> None:
        super().__init__(parent)
        self.image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self.pen_color = QColor(DEFAULT_COLOR)
        self.pen_size = 8
        self._current_path: QPainterPath | None = None
        self._current_points: list[tuple[int, int]] = []
        self._undo_stack: list[QImage] = []
        self._redo_stack: list[QImage] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(320, 240)

    def set_pen_color(self, color: QColor) -> None:
        if color.isValid():
            self.pen_color = QColor(color)

    def set_pen_size(self, size: int) -> None:
        self.pen_size = max(1, min(80, int(size)))

    def _image_rect(self):
        pixmap_size = self.image.size()
        pixmap_size.scale(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        left = int((self.width() - pixmap_size.width()) / 2)
        top = int((self.height() - pixmap_size.height()) / 2)
        return left, top, int(pixmap_size.width()), int(pixmap_size.height())

    def _image_point(self, pos):
        left, top, width, height = self._image_rect()
        if width <= 0 or height <= 0:
            return None
        x = pos.x() - left
        y = pos.y() - top
        if x < 0 or y < 0 or x > width or y > height:
            return None
        return (
            int(x * self.image.width() / width),
            int(y * self.image.height() / height),
        )

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#111111"))
        pixmap = QPixmap.fromImage(self.image)
        left, top, width, height = self._image_rect()
        painter.drawPixmap(left, top, width, height, pixmap)
        if self._current_path is not None:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.translate(left, top)
            scale_x = width / max(1, self.image.width())
            scale_y = height / max(1, self.image.height())
            painter.scale(scale_x, scale_y)
            painter.setPen(self._pen())
            painter.drawPath(self._current_path)

    def _pen(self) -> QPen:
        return QPen(
            self.pen_color,
            self.pen_size,
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )

    def _push_undo_snapshot(self) -> None:
        self._undo_stack.append(self.image.copy())
        if len(self._undo_stack) > 80:
            self._undo_stack.pop(0)
        self._redo_stack.clear()

    def undo(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self.image.copy())
        self.image = self._undo_stack.pop()
        self._current_path = None
        self._current_points = []
        self.update()

    def redo(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self.image.copy())
        self.image = self._redo_stack.pop()
        self._current_path = None
        self._current_points = []
        self.update()

    def _smooth_path(self, points: list[tuple[int, int]]) -> QPainterPath:
        path = QPainterPath()
        if not points:
            return path
        path.moveTo(points[0][0], points[0][1])
        if len(points) == 1:
            path.lineTo(points[0][0] + 0.1, points[0][1] + 0.1)
            return path
        for index in range(1, len(points)):
            previous = points[index - 1]
            current = points[index]
            mid_x = (previous[0] + current[0]) / 2
            mid_y = (previous[1] + current[1]) / 2
            path.quadTo(previous[0], previous[1], mid_x, mid_y)
        path.lineTo(points[-1][0], points[-1][1])
        return path

    def _commit_current_path(self) -> None:
        if self._current_path is None:
            return
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.setPen(self._pen())
        painter.drawPath(self._current_path)
        painter.end()
        self._current_path = None
        self._current_points = []
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self._image_point(event.position().toPoint())
        if point is None:
            return
        self._push_undo_snapshot()
        self._current_points = [point]
        self._current_path = self._smooth_path(self._current_points)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        current = self._image_point(event.position().toPoint())
        if current is None or self._current_path is None:
            return
        self._current_points.append(current)
        self._current_path = self._smooth_path(self._current_points)
        self.update()

    def mouseReleaseEvent(self, _event) -> None:
        self._commit_current_path()


class DrawOnImageDialog(QDialog):
    def __init__(self, image_path: Path, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Draw on Image")
        self.setWindowState(self.windowState() | Qt.WindowState.WindowFullScreen)
        image = QImage(str(image_path))
        if image.isNull():
            raise RuntimeError("Anki Pocket Knife could not open that image.")
        self.canvas = DrawingCanvas(image, self)
        self._build_ui()
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

        toolbar = QHBoxLayout()
        self.color_button = QPushButton(DEFAULT_COLOR)
        self.color_button.setStyleSheet(f"background: {DEFAULT_COLOR}; color: #111; font-weight: 600;")
        self.size_label = QLabel("Pen: 8")
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 80)
        self.size_slider.setValue(8)
        self.size_slider.setFixedWidth(220)
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")

        toolbar.addWidget(QLabel("Color:"))
        toolbar.addWidget(self.color_button)
        toolbar.addSpacing(18)
        toolbar.addWidget(self.size_label)
        toolbar.addWidget(self.size_slider)
        toolbar.addStretch(1)
        toolbar.addWidget(ok_button)
        toolbar.addWidget(cancel_button)
        layout.addLayout(toolbar)
        layout.addWidget(self.canvas, 1)

        self.color_button.clicked.connect(self._choose_color)
        self.size_slider.valueChanged.connect(self._set_pen_size)
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

    def _choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Choose Pen Color")
        if not color.isValid():
            return
        self.canvas.set_pen_color(color)
        color_name = color.name().upper()
        self.color_button.setText(color_name)
        text_color = "#111" if color.lightness() > 140 else "#fff"
        self.color_button.setStyleSheet(f"background: {color_name}; color: {text_color}; font-weight: 600;")

    def _set_pen_size(self, value: int) -> None:
        self.canvas.set_pen_size(int(value))
        self.size_label.setText(f"Pen: {int(value)}")

    def copy_to_clipboard(self) -> None:
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            raise RuntimeError("The system clipboard is not available.")
        clipboard.setImage(self.canvas.image)

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
const state = window[globalKey] || (window[globalKey] = { targets: new Map(), nextId: 1, lastImage: null });

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
  const path = typeof event.composedPath === "function" ? event.composedPath() : [];
  for (const node of path) {
    if (node instanceof HTMLImageElement) {
      state.lastImage = node;
      return;
    }
    if (node instanceof Element) {
      const image = node.closest("img");
      if (image) {
        state.lastImage = image;
        return;
      }
    }
  }
}

document.addEventListener("click", removeMenu, true);
document.addEventListener("scroll", removeMenu, true);
document.addEventListener("pointerdown", rememberImage, true);
document.addEventListener("mousedown", rememberImage, true);
document.addEventListener("mouseover", rememberImage, true);

document.addEventListener("contextmenu", (event) => {
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
}, true);
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
