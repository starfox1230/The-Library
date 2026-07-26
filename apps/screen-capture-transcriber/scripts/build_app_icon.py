from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"


def rounded_pen(color: str, width: float) -> QPen:
    pen = QPen(QColor(color), width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def build_icon() -> None:
    scale = 4
    size = 256
    canvas = QImage(
        size * scale,
        size * scale,
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(scale, scale)

    background = QPainterPath()
    background.addRoundedRect(QRectF(8, 8, 240, 240), 48, 48)
    gradient_color = QColor("#0A1728")
    painter.fillPath(background, gradient_color)
    painter.setPen(QPen(QColor("#294561"), 4))
    painter.drawPath(background)

    screen = QRectF(42, 45, 172, 126)
    painter.setPen(rounded_pen("#4FDBFF", 9))
    corner = 30
    for start, middle, end in (
        (QPointF(screen.left(), screen.top() + corner), screen.topLeft(), QPointF(screen.left() + corner, screen.top())),
        (QPointF(screen.right() - corner, screen.top()), screen.topRight(), QPointF(screen.right(), screen.top() + corner)),
        (QPointF(screen.right(), screen.bottom() - corner), screen.bottomRight(), QPointF(screen.right() - corner, screen.bottom())),
        (QPointF(screen.left() + corner, screen.bottom()), screen.bottomLeft(), QPointF(screen.left(), screen.bottom() - corner)),
    ):
        path = QPainterPath(start)
        path.lineTo(middle)
        path.lineTo(end)
        painter.drawPath(path)

    waveform = QPainterPath(QPointF(59, 110))
    for point in (
        QPointF(75, 110),
        QPointF(84, 83),
        QPointF(97, 139),
        QPointF(111, 96),
        QPointF(124, 126),
        QPointF(137, 73),
        QPointF(151, 146),
        QPointF(166, 100),
        QPointF(177, 120),
        QPointF(197, 120),
    ):
        waveform.lineTo(point)
    painter.setPen(rounded_pen("#EEF7FF", 8))
    painter.drawPath(waveform)

    painter.setPen(rounded_pen("#FFAA00", 8))
    painter.drawLine(QPointF(66, 207), QPointF(154, 178))
    painter.setBrush(QColor("#FFAA00"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawPolygon(
        [
            QPointF(154, 178),
            QPointF(136, 174),
            QPointF(143, 193),
        ]
    )
    painter.setBrush(QColor("#FF5368"))
    painter.drawEllipse(QPointF(192, 204), 18, 18)
    painter.end()

    rendered = canvas.scaled(
        size,
        size,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    ASSETS.mkdir(parents=True, exist_ok=True)
    if not rendered.save(str(ASSETS / "app-icon.png"), "PNG", 100):
        raise RuntimeError("Could not write app-icon.png")
    if not rendered.save(str(ASSETS / "app-icon.ico"), "ICO", 100):
        raise RuntimeError("Could not write app-icon.ico")


if __name__ == "__main__":
    build_icon()
