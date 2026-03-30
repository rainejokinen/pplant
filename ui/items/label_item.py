"""
LabelItem and PropertyCrossItem - Independent moveable label graphics items.

Labels are decoupled from parent transforms and can be freely positioned.
PropertyCrossItem displays 2x2 grid of flow properties (p|t / h|m) for VWO style.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import (
    QGraphicsTextItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget, QMenu
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QFont, QColor, QPen, QBrush, QFontMetrics
)

if TYPE_CHECKING:
    from .base_item import BaseComponentItem
    from .flow_item import FlowItem


class LabelItem(QGraphicsTextItem):
    """
    Independent moveable label item.
    
    Features:
        - Not affected by parent component's transforms
        - Freely moveable via drag
        - Configurable font, color, bold
        - Can show label text, value, or both
        - Optional units display
    """
    
    # Default styling
    DEFAULT_FONT_SIZE = 9
    DEFAULT_COLOR = QColor(200, 200, 200)
    DEFAULT_BOLD = False
    
    def __init__(
        self,
        label_key: str,
        label_text: str = "",
        value_text: str = "",
        units_text: str = "",
        parent_component: Optional[BaseComponentItem] = None,
        parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        self._label_key = label_key  # Unique identifier (e.g., "name", "efficiency", "p_in")
        self._label_text = label_text
        self._value_text = value_text
        self._units_text = units_text
        self._parent_component = parent_component
        
        # Display flags
        self._show_label = True
        self._show_value = True
        self._show_units = True
        self._visible = True
        
        # Style settings
        self._font_size = self.DEFAULT_FONT_SIZE
        self._bold = self.DEFAULT_BOLD
        self._color = QColor(self.DEFAULT_COLOR)
        
        # Offset from default position (for user repositioning)
        self._offset = QPointF(0, 0)
        self._default_pos = QPointF(0, 0)
        
        self._setup()
        self._update_display()
    
    def _setup(self):
        """Configure item flags."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        # Labels are added to scene (not as children of components)
        # so they don't inherit component transforms but DO scale with view zoom
        self.setAcceptHoverEvents(True)
        self.setZValue(50)  # Above components, below handles
    
    def _update_display(self):
        """Update displayed text based on settings."""
        if not self._visible:
            self.setVisible(False)
            return
        
        self.setVisible(True)
        
        parts = []
        if self._show_label and self._label_text:
            parts.append(self._label_text)
        if self._show_value and self._value_text:
            value_str = self._value_text
            if self._show_units and self._units_text:
                value_str += f" {self._units_text}"
            parts.append(value_str)
        
        if not parts:
            self.setPlainText("")
            return
        
        # Format: "Label: Value Units" or just "Value Units" or just "Label"
        if self._show_label and self._label_text and (self._show_value and self._value_text):
            display = f"{self._label_text}: {self._value_text}"
            if self._show_units and self._units_text:
                display += f" {self._units_text}"
        elif self._show_label and self._label_text:
            display = self._label_text
        else:
            display = self._value_text
            if self._show_units and self._units_text:
                display += f" {self._units_text}"
        
        self.setPlainText(display)
        
        # Apply font
        font = QFont()
        font.setPointSize(self._font_size)
        font.setBold(self._bold)
        self.setFont(font)
        self.setDefaultTextColor(self._color)
    
    def set_default_position(self, pos: QPointF):
        """Set the default/anchor position (without user offset)."""
        self._default_pos = pos
        self._apply_position()
    
    def _apply_position(self):
        """Apply default position plus user offset."""
        self.setPos(self._default_pos + self._offset)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Track user-dragged offset."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update offset based on where user dragged
            new_pos = value
            self._offset = new_pos - self._default_pos
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Right-click context menu."""
        menu = QMenu()
        
        # Reset position
        reset_action = menu.addAction("Reset Position")
        reset_action.triggered.connect(self.reset_position)
        
        menu.addSeparator()
        
        # Show/hide toggles
        show_label_action = menu.addAction("Show Label")
        show_label_action.setCheckable(True)
        show_label_action.setChecked(self._show_label)
        show_label_action.triggered.connect(self._toggle_show_label)
        
        show_value_action = menu.addAction("Show Value")
        show_value_action.setCheckable(True)
        show_value_action.setChecked(self._show_value)
        show_value_action.triggered.connect(self._toggle_show_value)
        
        show_units_action = menu.addAction("Show Units")
        show_units_action.setCheckable(True)
        show_units_action.setChecked(self._show_units)
        show_units_action.triggered.connect(self._toggle_show_units)
        
        menu.addSeparator()
        
        # Hide completely
        hide_action = menu.addAction("Hide")
        hide_action.triggered.connect(lambda: self.set_visible(False))
        
        menu.exec(event.screenPos())
    
    def reset_position(self):
        """Reset to default position (clear user offset)."""
        self._offset = QPointF(0, 0)
        self._apply_position()
    
    def _toggle_show_label(self):
        self._show_label = not self._show_label
        self._update_display()
    
    def _toggle_show_value(self):
        self._show_value = not self._show_value
        self._update_display()
    
    def _toggle_show_units(self):
        self._show_units = not self._show_units
        self._update_display()
    
    # --- Properties for external control ---
    
    @property
    def label_key(self) -> str:
        return self._label_key
    
    @property
    def label_text(self) -> str:
        return self._label_text
    
    @label_text.setter
    def label_text(self, value: str):
        self._label_text = value
        self._update_display()
    
    @property
    def value_text(self) -> str:
        return self._value_text
    
    @value_text.setter
    def value_text(self, value: str):
        self._value_text = value
        self._update_display()
    
    @property
    def units_text(self) -> str:
        return self._units_text
    
    @units_text.setter
    def units_text(self, value: str):
        self._units_text = value
        self._update_display()
    
    @property
    def font_size(self) -> int:
        return self._font_size
    
    @font_size.setter
    def font_size(self, value: int):
        self._font_size = max(6, min(24, value))
        self._update_display()
    
    @property
    def bold(self) -> bool:
        return self._bold
    
    @bold.setter
    def bold(self, value: bool):
        self._bold = value
        self._update_display()
    
    @property
    def color(self) -> QColor:
        return self._color
    
    @color.setter
    def color(self, value: QColor):
        self._color = value
        self._update_display()
    
    def set_visible(self, visible: bool):
        """Set overall visibility."""
        self._visible = visible
        self._update_display()
    
    @property
    def show_label_text(self) -> bool:
        return self._show_label
    
    @show_label_text.setter
    def show_label_text(self, value: bool):
        self._show_label = value
        self._update_display()
    
    @property
    def show_value_text(self) -> bool:
        return self._show_value
    
    @show_value_text.setter
    def show_value_text(self, value: bool):
        self._show_value = value
        self._update_display()
    
    @property
    def show_units_text(self) -> bool:
        return self._show_units
    
    @show_units_text.setter
    def show_units_text(self, value: bool):
        self._show_units = value
        self._update_display()
    
    @property
    def offset(self) -> QPointF:
        return QPointF(self._offset)
    
    @offset.setter
    def offset(self, value: QPointF):
        self._offset = value
        self._apply_position()


class PropertyCrossItem(QGraphicsItem):
    """
    2x2 grid display of flow properties in VWO style.
    
    Layout:
        p  | t
        ---|---
        h  | m
    
    Where:
        p = pressure (bar)
        t = temperature (°C)  
        h = enthalpy (kJ/kg)
        m = mass flow (kg/s)
    
    Features:
        - Independent moveable (not affected by parent transform)
        - Compact grid display
        - Color-coded by property type
        - Optional quality (x) display as 5th value
    """
    
    # Layout
    CELL_WIDTH = 45
    CELL_HEIGHT = 14
    PADDING = 2
    SEPARATOR_COLOR = QColor(100, 100, 100)
    
    # Property colors
    COLOR_P = QColor(200, 200, 200)  # Pressure - white/gray
    COLOR_T = QColor(255, 180, 180)  # Temperature - light red
    COLOR_H = QColor(180, 220, 255)  # Enthalpy - light blue
    COLOR_M = QColor(180, 255, 180)  # Mass flow - light green
    COLOR_X = QColor(255, 255, 180)  # Quality - light yellow
    
    FONT_SIZE = 8
    
    def __init__(
        self,
        parent_flow: Optional[FlowItem] = None,
        parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        self._parent_flow = parent_flow
        
        # Property values
        self._p_value: Optional[float] = None  # bar
        self._t_value: Optional[float] = None  # °C
        self._h_value: Optional[float] = None  # kJ/kg
        self._m_value: Optional[float] = None  # kg/s
        self._x_value: Optional[float] = None  # quality (0-1)
        
        self._show_x = False  # Show quality (makes it 2x3 or special layout)
        
        # Offset from default position
        self._offset = QPointF(0, 0)
        self._default_pos = QPointF(0, 0)
        
        self._visible = True
        
        self._setup()
    
    def _setup(self):
        """Configure item flags."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        # Added to scene (not as child) so doesn't inherit component transforms
        # but DOES scale with view zoom
        self.setAcceptHoverEvents(True)
        self.setZValue(50)
    
    def boundingRect(self) -> QRectF:
        """Return bounding rectangle."""
        width = self.CELL_WIDTH * 2 + self.PADDING * 2
        height = self.CELL_HEIGHT * 2 + self.PADDING * 2
        if self._show_x:
            height += self.CELL_HEIGHT  # Extra row for quality
        return QRectF(0, 0, width, height)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint the property cross grid."""
        if not self._visible:
            return
        
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        font = QFont()
        font.setPointSize(self.FONT_SIZE)
        painter.setFont(font)
        
        # Background
        bg_rect = self.boundingRect()
        painter.fillRect(bg_rect, QBrush(QColor(30, 35, 45, 200)))
        
        # Grid lines
        pen = QPen(self.SEPARATOR_COLOR, 1)
        painter.setPen(pen)
        
        # Vertical center line
        cx = self.PADDING + self.CELL_WIDTH
        painter.drawLine(int(cx), int(self.PADDING), int(cx), int(bg_rect.height() - self.PADDING))
        
        # Horizontal center line
        cy = self.PADDING + self.CELL_HEIGHT
        painter.drawLine(int(self.PADDING), int(cy), int(bg_rect.width() - self.PADDING), int(cy))
        
        if self._show_x:
            cy2 = self.PADDING + self.CELL_HEIGHT * 2
            painter.drawLine(int(self.PADDING), int(cy2), int(bg_rect.width() - self.PADDING), int(cy2))
        
        # Draw values
        def draw_value(value: Optional[float], x: int, y: int, color: QColor, decimals: int = 2):
            painter.setPen(color)
            if value is not None:
                text = f"{value:.{decimals}f}"
            else:
                text = "—"
            painter.drawText(x, y, self.CELL_WIDTH - 2, self.CELL_HEIGHT, 
                           Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)
        
        # Top-left: p (pressure)
        draw_value(self._p_value, self.PADDING, self.PADDING, self.COLOR_P, 2)
        
        # Top-right: t (temperature)
        draw_value(self._t_value, self.PADDING + self.CELL_WIDTH, self.PADDING, self.COLOR_T, 1)
        
        # Bottom-left: h (enthalpy)
        draw_value(self._h_value, self.PADDING, self.PADDING + self.CELL_HEIGHT, self.COLOR_H, 1)
        
        # Bottom-right: m (mass flow)
        draw_value(self._m_value, self.PADDING + self.CELL_WIDTH, self.PADDING + self.CELL_HEIGHT, self.COLOR_M, 2)
        
        # Quality row if shown
        if self._show_x:
            # Center the x value
            painter.setPen(self.COLOR_X)
            if self._x_value is not None:
                text = f"x={self._x_value:.3f}"
            else:
                text = "x=—"
            painter.drawText(int(self.PADDING), int(self.PADDING + self.CELL_HEIGHT * 2),
                           int(self.CELL_WIDTH * 2), int(self.CELL_HEIGHT),
                           Qt.AlignmentFlag.AlignCenter, text)
        
        # Selection highlight
        if self.isSelected():
            painter.setPen(QPen(QColor(255, 200, 50), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(bg_rect)
    
    def set_default_position(self, pos: QPointF):
        """Set the default/anchor position."""
        self._default_pos = pos
        self._apply_position()
    
    def _apply_position(self):
        """Apply default position plus user offset."""
        self.setPos(self._default_pos + self._offset)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Track user-dragged offset."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            new_pos = value
            self._offset = new_pos - self._default_pos
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Right-click context menu."""
        menu = QMenu()
        
        reset_action = menu.addAction("Reset Position")
        reset_action.triggered.connect(self.reset_position)
        
        menu.addSeparator()
        
        show_x_action = menu.addAction("Show Quality (x)")
        show_x_action.setCheckable(True)
        show_x_action.setChecked(self._show_x)
        show_x_action.triggered.connect(self._toggle_show_x)
        
        menu.addSeparator()
        
        hide_action = menu.addAction("Hide")
        hide_action.triggered.connect(lambda: self.set_visible(False))
        
        menu.exec(event.screenPos())
    
    def reset_position(self):
        """Reset to default position."""
        self._offset = QPointF(0, 0)
        self._apply_position()
    
    def _toggle_show_x(self):
        self._show_x = not self._show_x
        self.prepareGeometryChange()
        self.update()
    
    # --- Property setters ---
    
    def set_values(self, p: Optional[float] = None, t: Optional[float] = None,
                   h: Optional[float] = None, m: Optional[float] = None,
                   x: Optional[float] = None):
        """Set all flow property values at once."""
        self._p_value = p
        self._t_value = t
        self._h_value = h
        self._m_value = m
        self._x_value = x
        self.update()
    
    @property
    def pressure(self) -> Optional[float]:
        return self._p_value
    
    @pressure.setter
    def pressure(self, value: Optional[float]):
        self._p_value = value
        self.update()
    
    @property
    def temperature(self) -> Optional[float]:
        return self._t_value
    
    @temperature.setter
    def temperature(self, value: Optional[float]):
        self._t_value = value
        self.update()
    
    @property
    def enthalpy(self) -> Optional[float]:
        return self._h_value
    
    @enthalpy.setter
    def enthalpy(self, value: Optional[float]):
        self._h_value = value
        self.update()
    
    @property
    def mass_flow(self) -> Optional[float]:
        return self._m_value
    
    @mass_flow.setter
    def mass_flow(self, value: Optional[float]):
        self._m_value = value
        self.update()
    
    @property
    def quality(self) -> Optional[float]:
        return self._x_value
    
    @quality.setter
    def quality(self, value: Optional[float]):
        self._x_value = value
        self.update()
    
    @property
    def show_quality(self) -> bool:
        return self._show_x
    
    @show_quality.setter
    def show_quality(self, value: bool):
        if self._show_x != value:
            self._show_x = value
            self.prepareGeometryChange()
            self.update()
    
    def set_visible(self, visible: bool):
        """Set overall visibility."""
        self._visible = visible
        self.setVisible(visible)
        self.update()
    
    @property
    def offset(self) -> QPointF:
        return QPointF(self._offset)
    
    @offset.setter
    def offset(self, value: QPointF):
        self._offset = value
        self._apply_position()
