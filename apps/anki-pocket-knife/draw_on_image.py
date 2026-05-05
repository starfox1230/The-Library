from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlparse
from urllib.request import url2pathname

from aqt import gui_hooks, mw
from aqt.editor import Editor
from aqt.qt import (
    QColor,
    QColorDialog,
    QDialog,
    QHBoxLayout,
    QImage,
    QLabel,
    QPainter,
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


def _safe_media_name(source: str) -> str:
    parsed = urlparse(str(source or ""))
    raw_name = unquote(Path(parsed.path or source or "image").name)
    stem = Path(raw_name).stem or "image"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("._") or "image"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{stem}_drawn_{timestamp}.png"


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
        self._last_point = None
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
        painter.fillRect(self.rect(), QColor("#111111"))
        pixmap = QPixmap.fromImage(self.image)
        left, top, width, height = self._image_rect()
        painter.drawPixmap(left, top, width, height, pixmap)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self._last_point = self._image_point(event.position().toPoint())

    def mouseMoveEvent(self, event) -> None:
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        current = self._image_point(event.position().toPoint())
        if current is None or self._last_point is None:
            self._last_point = current
            return

        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(self.pen_color, self.pen_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self._last_point[0], self._last_point[1], current[0], current[1])
        painter.end()
        self._last_point = current
        self.update()

    def mouseReleaseEvent(self, _event) -> None:
        self._last_point = None


class DrawOnImageDialog(QDialog):
    def __init__(self, image_path: Path, parent=None) -> None:
        super().__init__(parent or mw)
        self.setWindowTitle("Draw on Image")
        image = QImage(str(image_path))
        if image.isNull():
            raise RuntimeError("Anki Pocket Knife could not open that image.")
        self.canvas = DrawingCanvas(image, self)
        self._build_ui()
        self.showMaximized()

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

    def save_copy(self, original_source: str) -> str:
        media_dir = collection_media_dir()
        file_name = _safe_media_name(original_source)
        output = media_dir / file_name
        counter = 2
        while output.exists():
            output = media_dir / f"{Path(file_name).stem}_{counter}.png"
            counter += 1
        if not self.canvas.image.save(str(output), "PNG"):
            raise RuntimeError("Anki Pocket Knife could not save the annotated image.")
        return output.name


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
const state = window[globalKey] || (window[globalKey] = { targets: new Map(), nextId: 1 });

function removeMenu() {
  const existing = document.getElementById("pocket-knife-draw-image-menu");
  if (existing) {
    existing.remove();
  }
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
  return null;
}

function editableFor(node) {
  const path = [];
  let current = node;
  while (current) {
    path.push(current);
    current = current.parentNode || current.host;
  }
  for (const item of path) {
    if (item instanceof HTMLElement && item.isContentEditable) {
      return item;
    }
  }
  return null;
}

function markChanged(image) {
  const editable = editableFor(image);
  if (editable) {
    editable.dispatchEvent(new InputEvent("input", {
      bubbles: true,
      inputType: "insertHTML",
      data: ""
    }));
    editable.dispatchEvent(new Event("change", { bubbles: true }));
  }
}

window.__ankiPocketKnifeInsertDrawnImage = function(targetId, fileName) {
  const image = state.targets.get(String(targetId));
  if (!image || !image.isConnected) {
    return false;
  }
  const newImage = document.createElement("img");
  newImage.setAttribute("src", fileName);
  newImage.setAttribute("data-pocket-knife-drawn-image", "true");
  image.insertAdjacentElement("afterend", newImage);
  image.insertAdjacentHTML("afterend", "<br>");
  markChanged(image);
  return true;
};

document.addEventListener("click", removeMenu, true);
document.addEventListener("scroll", removeMenu, true);

document.addEventListener("contextmenu", (event) => {
  const image = imageFromEvent(event);
  if (!image) {
    return;
  }

  event.preventDefault();
  event.stopPropagation();
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
  menu.style.left = `${event.clientX}px`;
  menu.style.top = `${event.clientY}px`;
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
}, true);
"""


def _insert_drawn_image(editor: Editor, target_id: str, file_name: str) -> None:
    target_js = json.dumps(str(target_id))
    file_js = json.dumps(str(file_name))
    _eval_editor_js(
        editor,
        f"""
if (typeof window.__ankiPocketKnifeInsertDrawnImage === "function") {{
  window.__ankiPocketKnifeInsertDrawnImage({target_js}, {file_js});
}}
""",
    )


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
        file_name = _dialog.save_copy(str(payload.get("src_attr") or payload.get("src") or image_path.name))
        _insert_drawn_image(editor, str(payload.get("target_id") or ""), file_name)
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
