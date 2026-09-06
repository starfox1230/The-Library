from __future__ import annotations

from typing import Any, Optional

from aqt.qt import (
    QColor,
    QEvent,
    QFontMetrics,
    QFrame,
    QLinearGradient,
    QPainter,
    QPen,
    QPointF,
    QPolygonF,
    QPushButton,
    QRectF,
    QToolButton,
    Qt,
    QWidget,
)


SURFACE_COLORS = {
    "card": ("#0f1722", "#2b394e", 16),
    "hero": ("#162131", "#33465f", 12),
    "row": ("#131d29", "#2b3a50", 10),
    "toggle": ("#131d29", "#2b3a50", 10),
    "button_group": ("#111a25", "#29374b", 10),
    "notice": ("#172b46", "#4979b7", 8),
    "preview": ("#101924", "#2a394e", 10),
    "popup_card": ("#121c29", "#304057", 14),
}

SECTION_COLORS = {
    "actions": ("#141d2a", "#304969", "#b9ccf8"),
    "timers": ("#132126", "#2d5a56", "#a9e1d9"),
    "flags": ("#231e19", "#634f36", "#f0cd93"),
    "feedback": ("#14212d", "#34566e", "#b8def1"),
    "display_style": ("#191d32", "#414d7a", "#c4ccff"),
    "performance": ("#211b21", "#574650", "#e8c7a6"),
    "appearance": ("#142329", "#335d6c", "#b4def0"),
    "help": ("#17221b", "#386047", "#b6dec1"),
    "shortcuts": ("#1e1926", "#58466c", "#d8c2ff"),
}

BUTTON_COLORS = {
    "default": ("#3b4a60", "#61738e", "#f7f9fc"),
    "secondaryAction": ("#3b4a60", "#61738e", "#f7f9fc"),
    "primaryAction": ("#356dcc", "#6a9bea", "#ffffff"),
    "reviewLaterAction": ("#3b5d8d", "#6587b5", "#ffffff"),
    "dangerAction": ("#7f3345", "#b25569", "#fff6f8"),
}


def _mix(color: str, target: str, amount: float) -> QColor:
    source_color = QColor(color)
    target_color = QColor(target)
    amount = max(0.0, min(1.0, float(amount)))
    return QColor(
        round(source_color.red() + ((target_color.red() - source_color.red()) * amount)),
        round(source_color.green() + ((target_color.green() - source_color.green()) * amount)),
        round(source_color.blue() + ((target_color.blue() - source_color.blue()) * amount)),
    )


class ModernSurface(QFrame):
    """A deterministic solid surface that does not depend on Qt stylesheets."""

    def __init__(
        self,
        role: str,
        parent: Optional[QWidget] = None,
        *,
        accent: str = "",
    ) -> None:
        super().__init__(parent)
        self.surface_role = str(role or "row")
        self.surface_accent = str(accent or "")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setAutoFillBackground(False)

    def paintEvent(self, _event: Any) -> None:
        if self.surface_role == "section":
            background, border, _title = SECTION_COLORS.get(
                self.surface_accent,
                SECTION_COLORS["appearance"],
            )
            radius = 16
        else:
            background, border, radius = SURFACE_COLORS.get(
                self.surface_role,
                SURFACE_COLORS["row"],
            )
        if not self.isEnabled() or str(self.property("disabled") or "false") == "true":
            background = "#111923"
            border = "#263243"

        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(bounds, radius, radius)
        painter.end()


class ModernButton(QPushButton):
    """A filled action button whose pixels are identical across Qt styles."""

    def __init__(self, text: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(text, parent)
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAutoDefault(False)
        self.setDefault(False)

    def _role(self) -> str:
        role = str(self.property("class") or "default")
        return role if role in BUTTON_COLORS else "default"

    def paintEvent(self, _event: Any) -> None:
        role = self._role()
        background, border, foreground = BUTTON_COLORS[role]
        if not self.isEnabled():
            background, border, foreground = "#242e3c", "#39475a", "#7e8b9d"
        elif self.isDown():
            background = _mix(background, "#000000", 0.20).name()
        elif self.underMouse():
            background = _mix(background, "#ffffff", 0.11).name()
            border = _mix(border, "#ffffff", 0.12).name()

        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        theme_top = str(self.property("themeTop") or "")
        theme_bottom = str(self.property("themeBottom") or "")
        if QColor(theme_top).isValid() and QColor(theme_bottom).isValid():
            gradient = QLinearGradient(bounds.topLeft(), bounds.bottomLeft())
            gradient.setColorAt(0.0, QColor(theme_top))
            gradient.setColorAt(1.0, QColor(theme_bottom))
            painter.setBrush(gradient)
            border = "#71819a" if str(self.property("current") or "false") != "true" else "#91b9ff"
            foreground = "#ffffff"
        else:
            painter.setBrush(QColor(background))
        painter.setPen(QPen(QColor(border), 1))
        painter.drawRoundedRect(bounds, 8, 8)

        font = self.font()
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(foreground))
        painter.drawText(bounds.adjusted(10, 0, -10, 0), Qt.AlignmentFlag.AlignCenter, self.text())
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor("#a9c8ff"), 1))
            painter.drawRoundedRect(bounds.adjusted(2, 2, -2, -2), 6, 6)
        painter.end()

    def event(self, event: Any) -> bool:
        result = super().event(event)
        if event.type() in {
            QEvent.Type.Enter,
            QEvent.Type.Leave,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.FocusIn,
            QEvent.Type.FocusOut,
            QEvent.Type.EnabledChange,
        }:
            self.update()
        return result


class ModernToolButton(QToolButton):
    """Filled tool/menu button with deterministic text and menu indicator."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

    def paintEvent(self, _event: Any) -> None:
        background, border, foreground = BUTTON_COLORS["secondaryAction"]
        if not self.isEnabled():
            background, border, foreground = "#242e3c", "#39475a", "#7e8b9d"
        elif self.isDown():
            background = _mix(background, "#000000", 0.20).name()
        elif self.underMouse():
            background = _mix(background, "#ffffff", 0.11).name()
            border = _mix(border, "#ffffff", 0.12).name()

        bounds = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(border), 1))
        painter.setBrush(QColor(background))
        painter.drawRoundedRect(bounds, 8, 8)
        font = self.font()
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(foreground))
        text_rect = bounds.adjusted(12, 0, -28, 0)
        text = QFontMetrics(font).elidedText(self.text(), Qt.TextElideMode.ElideMiddle, max(1, round(text_rect.width())))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        arrow_x = bounds.right() - 14
        arrow_y = bounds.center().y()
        painter.setBrush(QColor(foreground))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(QPolygonF([
            QPointF(arrow_x - 4, arrow_y - 2),
            QPointF(arrow_x + 4, arrow_y - 2),
            QPointF(arrow_x, arrow_y + 3),
        ]))
        painter.end()

    def event(self, event: Any) -> bool:
        result = super().event(event)
        if event.type() in {
            QEvent.Type.Enter,
            QEvent.Type.Leave,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonRelease,
            QEvent.Type.FocusIn,
            QEvent.Type.FocusOut,
            QEvent.Type.EnabledChange,
        }:
            self.update()
        return result


class ModernSectionToggle(QToolButton):
    """Unfilled disclosure heading, visually separate from action buttons."""

    def __init__(self, parent: Optional[QWidget] = None, *, accent: str = "") -> None:
        super().__init__(parent)
        self.section_accent = str(accent or "appearance")
        self.setCheckable(True)
        self.setMinimumHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)

    def paintEvent(self, _event: Any) -> None:
        _background, _border, title_color = SECTION_COLORS.get(
            self.section_accent,
            SECTION_COLORS["appearance"],
        )
        foreground = QColor(title_color)
        if not self.isEnabled():
            foreground = QColor("#6f7c8e")
        elif self.underMouse():
            foreground = _mix(title_color, "#ffffff", 0.28)

        bounds = QRectF(self.rect())
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(foreground)
        center_y = bounds.center().y()
        if self.isChecked():
            points = [QPointF(5, center_y - 3), QPointF(13, center_y - 3), QPointF(9, center_y + 3)]
        else:
            points = [QPointF(6, center_y - 4), QPointF(12, center_y), QPointF(6, center_y + 4)]
        painter.drawPolygon(QPolygonF(points))
        font = self.font()
        font.setBold(True)
        font.setPointSizeF(max(font.pointSizeF(), 12.0))
        painter.setFont(font)
        painter.setPen(foreground)
        painter.drawText(bounds.adjusted(20, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())
        painter.end()

    def event(self, event: Any) -> bool:
        result = super().event(event)
        if event.type() in {QEvent.Type.Enter, QEvent.Type.Leave, QEvent.Type.EnabledChange}:
            self.update()
        return result
