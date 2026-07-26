from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QCloseEvent,
    QCursor,
    QImage,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPen,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


DEFAULT_ANNOTATION_COLOR = "#FFAA00"
MIN_CROP_SIZE = 32.0


@dataclass
class Stroke:
    tool: str
    color: str
    width: float
    points: list[QPointF] = field(default_factory=list)

    def to_payload(self) -> dict[str, object]:
        return {
            "tool": self.tool,
            "color": self.color,
            "width": self.width,
            "points": [[point.x(), point.y()] for point in self.points],
        }

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "Stroke":
        return cls(
            tool=str(payload.get("tool", "arrow")),
            color=str(payload.get("color", DEFAULT_ANNOTATION_COLOR)),
            width=float(payload.get("width", 8.0)),
            points=[
                QPointF(float(point[0]), float(point[1]))
                for point in payload.get("points", [])
            ],
        )


class AnnotationCanvas(QWidget):
    changed = Signal()
    crop_mode_changed = Signal(bool, str)

    def __init__(self, image_path: Path | None = None) -> None:
        super().__init__()
        self._image = QImage(1280, 720, QImage.Format.Format_ARGB32)
        self._image.fill(QColor("#172536"))
        self._image_path: Path | None = None
        self._preserved_image: QImage | None = None
        self._preserved_image_path: Path | None = None
        self._redo_preserved_image: QImage | None = None
        self._redo_preserved_image_path: Path | None = None
        self._strokes: list[Stroke] = []
        self._redo: list[Stroke] = []
        self._active: Stroke | None = None
        self._crop_rect: QRectF | None = None
        self._crop_before_edit: QRectF | None = None
        self._crop_mode = ""
        self._crop_drag = ""
        self._crop_drag_origin: QPointF | None = None
        self._crop_drag_rect: QRectF | None = None
        self._motion_last_point: QPointF | None = None
        self._motion_pointer_origin: QPoint | None = None
        self.tool = "arrow"
        self.color = DEFAULT_ANNOTATION_COLOR
        self.width = 8.0
        self.setMinimumSize(640, 360)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        if image_path is not None:
            self.load_image(image_path)

    @property
    def image_size(self):
        return self._image.size()

    @property
    def crop_mode(self) -> str:
        return self._crop_mode

    @property
    def crop_rect(self) -> QRectF | None:
        return QRectF(self._crop_rect) if self._crop_rect else None

    def load_image(
        self,
        image_path: Path,
        state_path: Path | None = None,
        preserved_image_path: Path | None = None,
    ) -> None:
        self.release_motion_pointer()
        image = QImage(str(image_path))
        if image.isNull():
            raise RuntimeError(f"Could not open paused frame: {image_path}")
        self._image = image.convertToFormat(QImage.Format.Format_ARGB32)
        self._image_path = image_path
        self._preserved_image = None
        self._preserved_image_path = None
        self._redo_preserved_image = None
        self._redo_preserved_image_path = None
        self._strokes.clear()
        self._redo.clear()
        self._active = None
        self._crop_rect = None
        self._crop_mode = ""
        if state_path and state_path.is_file():
            payload = json.loads(state_path.read_text(encoding="utf-8"))
            self._strokes = [
                Stroke.from_payload(item)
                for item in payload.get("strokes", [])
                if isinstance(item, dict)
            ]
            crop = payload.get("crop")
            if isinstance(crop, list) and len(crop) == 4:
                self._crop_rect = self._clamp_rect(
                    QRectF(*(float(value) for value in crop))
                )
            saved_preserved = str(payload.get("preserved_image", "")).strip()
            if saved_preserved:
                saved_path = Path(saved_preserved)
                preserved_image_path = (
                    saved_path
                    if saved_path.is_absolute()
                    else state_path.parent / saved_path
                )
        if preserved_image_path and preserved_image_path.is_file():
            preserved = QImage(str(preserved_image_path))
            if not preserved.isNull():
                preserved = preserved.convertToFormat(QImage.Format.Format_ARGB32)
                if preserved.size() != self._image.size():
                    preserved = preserved.scaled(
                        self._image.size(),
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                self._preserved_image = preserved
                self._preserved_image_path = preserved_image_path
        self.crop_mode_changed.emit(False, "")
        self.changed.emit()
        self.update()

    def _base_image(self) -> QImage:
        return self._preserved_image or self._image

    def _target_rect(self) -> QRectF:
        available = QRectF(self.rect()).adjusted(8, 8, -8, -8)
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

    def _to_image(self, point: QPointF, clamp: bool = False) -> QPointF | None:
        target = self._target_rect()
        if not target.contains(point) and not clamp:
            return None
        x = (point.x() - target.left()) * self._image.width() / target.width()
        y = (point.y() - target.top()) * self._image.height() / target.height()
        return QPointF(
            min(float(self._image.width()), max(0.0, x)),
            min(float(self._image.height()), max(0.0, y)),
        )

    def _scale_to_image(self) -> float:
        return self._image.width() / max(1.0, self._target_rect().width())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self._to_image(event.position())
        if point is None:
            return
        if self._crop_mode == "standard":
            self._crop_drag = self._crop_hit_test(point)
            if not self._crop_drag:
                return
            self._crop_drag_origin = point
            self._crop_drag_rect = QRectF(self._crop_rect) if self._crop_rect else None
            return
        if self._crop_mode:
            return
        if self._crop_rect is not None and not self._crop_rect.contains(point):
            return
        self._active = Stroke(self.tool, self.color, self.width, [point])
        self._redo.clear()
        self._redo_preserved_image = None
        self._redo_preserved_image_path = None
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._crop_mode == "motion":
            self._motion_crop_from_pointer(event.position(), event.modifiers())
            return
        point = self._to_image(event.position(), clamp=bool(self._crop_mode))
        if point is None:
            return
        if (
            self._crop_mode == "standard"
            and self._crop_drag
            and self._crop_drag_origin is not None
            and self._crop_drag_rect is not None
        ):
            self._drag_standard_crop(point)
            return
        if self._crop_mode == "standard":
            self._set_crop_cursor(self._crop_hit_test(point))
            return
        if self._active is None:
            return
        if self._active.tool == "arrow":
            if len(self._active.points) == 1:
                self._active.points.append(point)
            else:
                self._active.points[-1] = point
        else:
            self._active.points.append(point)
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if self._crop_mode == "standard":
            self._crop_drag = ""
            self._crop_drag_origin = None
            self._crop_drag_rect = None
            self.changed.emit()
            return
        if self._active is None:
            return
        point = self._to_image(event.position())
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
            self.changed.emit()
        self._active = None
        self.update()

    def undo(self) -> None:
        if self._strokes:
            self._redo.append(self._strokes.pop())
            self.changed.emit()
            self.update()

    def redo(self) -> None:
        if self._redo_preserved_image is not None:
            self._preserved_image = self._redo_preserved_image
            self._preserved_image_path = self._redo_preserved_image_path
            self._redo_preserved_image = None
            self._redo_preserved_image_path = None
            self.changed.emit()
            self.update()
            return
        if self._redo:
            self._strokes.append(self._redo.pop())
            self.changed.emit()
            self.update()

    def clear(self) -> None:
        if self._strokes or self._preserved_image is not None:
            self._redo.extend(reversed(self._strokes))
            self._strokes.clear()
            self._redo_preserved_image = self._preserved_image
            self._redo_preserved_image_path = self._preserved_image_path
            self._preserved_image = None
            self._preserved_image_path = None
            self.changed.emit()
            self.update()

    def begin_crop(self, mode: str) -> None:
        if mode not in {"standard", "motion"}:
            raise ValueError(f"Unknown crop mode: {mode}")
        self._crop_before_edit = QRectF(self._crop_rect) if self._crop_rect else None
        if self._crop_rect is None:
            margin_x = self._image.width() * 0.08
            margin_y = self._image.height() * 0.08
            self._crop_rect = QRectF(
                margin_x,
                margin_y,
                self._image.width() - 2 * margin_x,
                self._image.height() - 2 * margin_y,
            )
        self._crop_mode = mode
        self._motion_last_point = None
        if mode == "motion":
            self._activate_motion_pointer()
        else:
            self.release_motion_pointer()
        self.crop_mode_changed.emit(True, mode)
        self.update()

    def commit_crop(self) -> None:
        if not self._crop_mode:
            return
        self._crop_mode = ""
        self._crop_before_edit = None
        self._motion_last_point = None
        self.release_motion_pointer()
        self.crop_mode_changed.emit(False, "")
        self.changed.emit()
        self.update()

    def cancel_crop(self) -> None:
        if not self._crop_mode:
            return
        self._crop_rect = (
            QRectF(self._crop_before_edit) if self._crop_before_edit else None
        )
        self._crop_mode = ""
        self._crop_before_edit = None
        self._motion_last_point = None
        self.release_motion_pointer()
        self.crop_mode_changed.emit(False, "")
        self.update()

    def reset_crop(self) -> None:
        self._crop_rect = None
        self._crop_mode = ""
        self._crop_before_edit = None
        self._motion_last_point = None
        self.release_motion_pointer()
        self.crop_mode_changed.emit(False, "")
        self.changed.emit()
        self.update()

    def _motion_crop(
        self,
        point: QPointF,
        modifiers: Qt.KeyboardModifier,
    ) -> None:
        if self._crop_rect is None:
            return
        if self._motion_last_point is None:
            self._motion_last_point = point
            return
        delta = point - self._motion_last_point
        self._motion_last_point = point
        self._apply_motion_crop_delta(delta, modifiers)

    def _motion_crop_from_pointer(
        self,
        position: QPointF,
        modifiers: Qt.KeyboardModifier,
    ) -> None:
        """Apply relative motion and recenter the hidden pointer for endless travel."""
        anchor = QPointF(self.rect().center())
        widget_delta = position - anchor
        if abs(widget_delta.x()) < 0.01 and abs(widget_delta.y()) < 0.01:
            return
        image_scale = self._scale_to_image()
        self._apply_motion_crop_delta(
            QPointF(
                widget_delta.x() * image_scale,
                widget_delta.y() * image_scale,
            ),
            modifiers,
        )
        self._recenter_motion_pointer()

    def _apply_motion_crop_delta(
        self,
        delta: QPointF,
        modifiers: Qt.KeyboardModifier,
    ) -> None:
        if self._crop_rect is None:
            return
        rect = QRectF(self._crop_rect)
        if modifiers & Qt.KeyboardModifier.ControlModifier:
            rect.translate(delta.x(), delta.y())
        else:
            center = rect.center()
            width = max(MIN_CROP_SIZE, rect.width() + 2 * delta.x())
            height = max(MIN_CROP_SIZE, rect.height() - 2 * delta.y())
            width = min(float(self._image.width()), width)
            height = min(float(self._image.height()), height)
            rect = QRectF(
                center.x() - width / 2,
                center.y() - height / 2,
                width,
                height,
            )
        self._crop_rect = self._clamp_rect(rect)
        self.update()

    def _activate_motion_pointer(self) -> None:
        if self._motion_pointer_origin is None:
            self._motion_pointer_origin = QCursor.pos()
        self.setCursor(Qt.CursorShape.BlankCursor)
        self._recenter_motion_pointer()

    def _recenter_motion_pointer(self) -> None:
        if self._crop_mode != "motion" or not self.isVisible():
            return
        QCursor.setPos(self.mapToGlobal(self.rect().center()))

    def release_motion_pointer(self) -> None:
        origin = self._motion_pointer_origin
        self._motion_pointer_origin = None
        self.setCursor(Qt.CursorShape.CrossCursor)
        if origin is not None:
            QCursor.setPos(origin)

    def _crop_hit_test(self, point: QPointF) -> str:
        rect = self._crop_rect
        if rect is None:
            return ""
        margin = 12.0 * self._scale_to_image()
        near_left = abs(point.x() - rect.left()) <= margin
        near_right = abs(point.x() - rect.right()) <= margin
        near_top = abs(point.y() - rect.top()) <= margin
        near_bottom = abs(point.y() - rect.bottom()) <= margin
        within_x = rect.left() - margin <= point.x() <= rect.right() + margin
        within_y = rect.top() - margin <= point.y() <= rect.bottom() + margin
        horizontal = "l" if near_left else ("r" if near_right else "")
        vertical = "t" if near_top else ("b" if near_bottom else "")
        if horizontal and vertical:
            return vertical + horizontal
        if horizontal and within_y:
            return horizontal
        if vertical and within_x:
            return vertical
        return "move" if rect.contains(point) else ""

    def _drag_standard_crop(self, point: QPointF) -> None:
        if (
            self._crop_drag_rect is None
            or self._crop_drag_origin is None
            or not self._crop_drag
        ):
            return
        original = QRectF(self._crop_drag_rect)
        delta = point - self._crop_drag_origin
        if self._crop_drag == "move":
            original.translate(delta.x(), delta.y())
            self._crop_rect = self._clamp_rect(original)
            self.update()
            return
        left, top, right, bottom = (
            original.left(),
            original.top(),
            original.right(),
            original.bottom(),
        )
        if "l" in self._crop_drag:
            left = min(point.x(), right - MIN_CROP_SIZE)
        if "r" in self._crop_drag:
            right = max(point.x(), left + MIN_CROP_SIZE)
        if "t" in self._crop_drag:
            top = min(point.y(), bottom - MIN_CROP_SIZE)
        if "b" in self._crop_drag:
            bottom = max(point.y(), top + MIN_CROP_SIZE)
        self._crop_rect = self._clamp_rect(
            QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()
        )
        self.update()

    def _clamp_rect(self, rect: QRectF) -> QRectF:
        width = min(float(self._image.width()), max(MIN_CROP_SIZE, rect.width()))
        height = min(float(self._image.height()), max(MIN_CROP_SIZE, rect.height()))
        left = min(
            float(self._image.width()) - width,
            max(0.0, rect.left()),
        )
        top = min(
            float(self._image.height()) - height,
            max(0.0, rect.top()),
        )
        return QRectF(left, top, width, height)

    def _set_crop_cursor(self, hit: str) -> None:
        cursors = {
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor,
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "move": Qt.CursorShape.SizeAllCursor,
        }
        self.setCursor(cursors.get(hit, Qt.CursorShape.ArrowCursor))

    @staticmethod
    def _draw_stroke(painter: QPainter, stroke: Stroke) -> None:
        if len(stroke.points) < 2:
            return
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

    def _paint_image_contents(self, painter: QPainter) -> None:
        painter.drawImage(QPointF(0, 0), self._base_image())
        for stroke in self._strokes:
            self._draw_stroke(painter, stroke)
        if self._active:
            self._draw_stroke(painter, self._active)

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#05080D"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        target = self._target_rect()
        painter.save()
        painter.translate(target.left(), target.top())
        painter.scale(
            target.width() / self._image.width(),
            target.height() / self._image.height(),
        )
        self._paint_image_contents(painter)
        if self._crop_rect is not None:
            crop = self._crop_rect
            shade = QColor(0, 0, 0, 145)
            painter.fillRect(QRectF(0, 0, self._image.width(), crop.top()), shade)
            painter.fillRect(
                QRectF(0, crop.bottom(), self._image.width(), self._image.height()),
                shade,
            )
            painter.fillRect(QRectF(0, crop.top(), crop.left(), crop.height()), shade)
            painter.fillRect(
                QRectF(crop.right(), crop.top(), self._image.width(), crop.height()),
                shade,
            )
            crop_pen = QPen(QColor("#FFCC4D"), 2.0 * self._scale_to_image())
            crop_pen.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(crop_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(crop)
            if self._crop_mode:
                handle = 6.0 * self._scale_to_image()
                painter.setBrush(QColor("#FFCC4D"))
                for point in (
                    crop.topLeft(),
                    crop.topRight(),
                    crop.bottomLeft(),
                    crop.bottomRight(),
                    QPointF(crop.center().x(), crop.top()),
                    QPointF(crop.center().x(), crop.bottom()),
                    QPointF(crop.left(), crop.center().y()),
                    QPointF(crop.right(), crop.center().y()),
                ):
                    painter.drawRect(
                        QRectF(
                            point.x() - handle,
                            point.y() - handle,
                            2 * handle,
                            2 * handle,
                        )
                    )
        painter.restore()

    def save(self, output_path: Path) -> Path:
        rendered = self._base_image().copy()
        painter = QPainter(rendered)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        for stroke in self._strokes:
            self._draw_stroke(painter, stroke)
        painter.end()
        if self._crop_rect is not None:
            rendered = rendered.copy(self._crop_rect.toAlignedRect())
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not rendered.save(str(output_path), "PNG", 100):
            raise RuntimeError(f"Could not save annotation: {output_path}")
        return output_path

    def save_state(self, output_path: Path) -> Path:
        crop = (
            [
                self._crop_rect.x(),
                self._crop_rect.y(),
                self._crop_rect.width(),
                self._crop_rect.height(),
            ]
            if self._crop_rect is not None
            else None
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "version": 2,
                    "source": str(self._image_path) if self._image_path else "",
                    "source_width": self._image.width(),
                    "source_height": self._image.height(),
                    "preserved_image": (
                        self._preserved_image_path.name
                        if self._preserved_image_path is not None
                        else ""
                    ),
                    "crop": crop,
                    "strokes": [stroke.to_payload() for stroke in self._strokes],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return output_path


class AnatomyAnnotationDialog(QDialog):
    def __init__(
        self,
        image_path: Path | None = None,
        timestamp_label: str = "00:00",
        default_card_mode: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.resize(1280, 820)
        self._post_mode = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        toolbar = QFrame()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)

        self.arrow_button = QPushButton("Arrow")
        self.pen_button = QPushButton("Pen")
        self.crop_button = QPushButton("Crop")
        self.reset_crop_button = QPushButton("Reset Crop")
        self.arrow_button.setCheckable(True)
        self.pen_button.setCheckable(True)
        self.crop_button.setCheckable(True)
        self.arrow_button.setChecked(True)
        self.arrow_button.clicked.connect(lambda: self._set_tool("arrow"))
        self.pen_button.clicked.connect(lambda: self._set_tool("pen"))
        self.crop_button.clicked.connect(self._toggle_standard_crop)
        self.reset_crop_button.clicked.connect(self.canvas_reset_crop)
        toolbar_layout.addWidget(self.arrow_button)
        toolbar_layout.addWidget(self.pen_button)
        toolbar_layout.addWidget(self.crop_button)
        toolbar_layout.addWidget(self.reset_crop_button)

        toolbar_layout.addWidget(QLabel("Width"))
        self.width_slider = QSlider(Qt.Orientation.Horizontal)
        self.width_slider.setRange(2, 30)
        self.width_slider.setValue(8)
        self.width_slider.setFixedWidth(120)
        toolbar_layout.addWidget(self.width_slider)

        undo_button = QPushButton("Undo")
        redo_button = QPushButton("Redo")
        clear_button = QPushButton("Clear Drawing")
        toolbar_layout.addWidget(undo_button)
        toolbar_layout.addWidget(redo_button)
        toolbar_layout.addWidget(clear_button)
        toolbar_layout.addStretch()
        self.timestamp_label = QLabel("")
        toolbar_layout.addWidget(self.timestamp_label)
        layout.addWidget(toolbar)

        self.canvas = AnnotationCanvas(image_path)
        self.width_slider.valueChanged.connect(
            lambda value: setattr(self.canvas, "width", float(value))
        )
        undo_button.clicked.connect(self.canvas.undo)
        redo_button.clicked.connect(self.canvas.redo)
        clear_button.clicked.connect(self.canvas.clear)
        self.canvas.crop_mode_changed.connect(self._on_crop_mode_changed)
        layout.addWidget(self.canvas, 1)

        self.crop_hint = QLabel("")
        self.crop_hint.setObjectName("CropHint")
        self.crop_hint.setWordWrap(True)
        layout.addWidget(self.crop_hint)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("Capture name / structure"))
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText(
            "e.g. posterior cerebral artery (optional for screenshot-only captures)"
        )
        footer.addWidget(self.label_edit, 1)
        self.anki_checkbox = QCheckBox(
            "Create “What is indicated by the arrow?” Anki card"
        )
        footer.addWidget(self.anki_checkbox)
        self.discard_button = QPushButton("Discard & Resume")
        self.save_button = QPushButton("Save & Resume")
        self.save_button.setDefault(True)
        self.discard_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)
        footer.addWidget(self.discard_button)
        footer.addWidget(self.save_button)
        layout.addLayout(footer)

        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

        self.setStyleSheet(
            """
            QDialog, QWidget { background:#09101C; color:#EEF4FC;
                               font-family:"Segoe UI"; font-size:10pt; }
            QFrame { background:#101B2B; border:1px solid #26364D; border-radius:8px; }
            QPushButton, QLineEdit { background:#17273A; border:1px solid #36516F;
                                    border-radius:6px; padding:8px 12px; }
            QPushButton:checked { background:#9B6800; border-color:#FFAA00; }
            QLineEdit { background:#0B1421; }
            QLabel#CropHint { color:#FFD47B; padding:3px 8px; }
            """
        )
        if image_path is not None:
            self.prepare(
                image_path,
                timestamp_label,
                default_card_mode=default_card_mode,
            )
        else:
            self.timestamp_label.setText(
                f"{timestamp_label}  •  {DEFAULT_ANNOTATION_COLOR}"
            )

    def prepare(
        self,
        image_path: Path,
        timestamp_label: str,
        *,
        default_card_mode: bool = True,
        label: str = "",
        state_path: Path | None = None,
        preserved_image_path: Path | None = None,
        post_mode: bool = False,
    ) -> None:
        self._post_mode = post_mode
        self.setWindowTitle(
            f"{'Edit anatomy capture' if post_mode else 'Anatomy capture'} "
            f"— {timestamp_label}"
        )
        self.canvas.load_image(image_path, state_path, preserved_image_path)
        self.label_edit.setText(label)
        self.anki_checkbox.setChecked(default_card_mode)
        self.timestamp_label.setText(
            f"{timestamp_label}  •  {DEFAULT_ANNOTATION_COLOR}"
        )
        self.save_button.setText("Save Changes" if post_mode else "Save & Resume")
        self.discard_button.setText("Cancel" if post_mode else "Discard & Resume")
        self.crop_hint.setText(
            "Enter saves. Ctrl+Backspace discards and resumes. "
            "Press . for motion crop."
            if not post_mode
            else "Enter saves changes. Ctrl+Backspace cancels. "
            "Press . for motion crop."
        )
        self._set_tool("arrow")
        self.label_edit.setFocus()

    @property
    def label(self) -> str:
        return self.label_edit.text().strip()

    @property
    def create_anki_card(self) -> bool:
        return self.anki_checkbox.isChecked() and bool(self.label)

    def save_annotation(
        self,
        output_path: Path,
        state_path: Path | None = None,
    ) -> Path:
        result = self.canvas.save(output_path)
        if state_path is not None:
            self.canvas.save_state(state_path)
        return result

    def canvas_reset_crop(self) -> None:
        self.canvas.reset_crop()

    def _set_tool(self, tool: str) -> None:
        if self.canvas.crop_mode:
            self.canvas.commit_crop()
        self.canvas.tool = tool
        self.arrow_button.setChecked(tool == "arrow")
        self.pen_button.setChecked(tool == "pen")
        self.crop_button.setChecked(False)

    def _toggle_standard_crop(self) -> None:
        if self.canvas.crop_mode:
            self.canvas.commit_crop()
        else:
            self.canvas.begin_crop("standard")

    def _toggle_motion_crop(self) -> None:
        if self.canvas.crop_mode:
            self.canvas.commit_crop()
        else:
            self.canvas.begin_crop("motion")

    def _on_crop_mode_changed(self, active: bool, mode: str) -> None:
        self.crop_button.setChecked(active and mode == "standard")
        if active and mode == "motion":
            self.crop_hint.setText(
                "Motion crop: mouse ↑ expands height, ↓ shrinks height, "
                "→ expands width, ← shrinks width. Hold Ctrl to move the crop. "
                "The hidden pointer recenters for unlimited movement. "
                "Press . to apply or Backspace to cancel."
            )
        elif active:
            self.crop_hint.setText(
                "Standard crop: drag an edge or corner; drag inside to move. "
                "Click Crop or press . to apply; Backspace cancels."
            )
        else:
            self.crop_hint.setText(
                "Enter saves. Ctrl+Backspace "
                f"{'cancels' if self._post_mode else 'discards and resumes'}. "
                "Press . for motion crop."
            )

    def eventFilter(self, watched, event) -> bool:
        if event.type() == QEvent.Type.KeyPress and self.isVisible():
            key = event.key()
            modifiers = event.modifiers()
            if (
                key == Qt.Key.Key_Backspace
                and modifiers & Qt.KeyboardModifier.ControlModifier
            ):
                self.reject()
                return True
            if key == Qt.Key.Key_Period and not (
                modifiers & Qt.KeyboardModifier.ControlModifier
            ):
                self._toggle_motion_crop()
                return True
            if key == Qt.Key.Key_Backspace and self.canvas.crop_mode:
                self.canvas.cancel_crop()
                return True
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.accept()
                return True
        return super().eventFilter(watched, event)

    def done(self, result: int) -> None:
        self.canvas.release_motion_pointer()
        super().done(result)

    def closeEvent(self, event: QCloseEvent) -> None:
        self.reject()
        event.accept()
