"""
TurbineItem - Steam/gas turbine symbol.

Trapezoid shape representing expansion from high to low pressure.
VWO-style: narrow inlet (left), wide outlet (right).
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath,
    QLinearGradient, QFont, QTransform
)

from .base_item import BaseComponentItem


class TurbineItem(BaseComponentItem):
    """
    Steam turbine graphics item (VWO-style).
    
    Visual: Trapezoid shape (narrow inlet on left, wide outlet on right)
    - Steam expands as it flows through, so outlet is larger
    Ports:
        - 2 inputs: main_inlet (left-center), reheat_inlet (top)
        - 3 outputs: main_outlet (right), extraction_1 (bottom), extraction_2 (bottom)
    """
    
    # Dimensions (shorter for single stage)
    WIDTH = 45
    HEIGHT = 40
    
    # VWO style: narrow inlet, wide outlet
    INLET_HEIGHT_RATIO = 0.4   # Narrow on left
    OUTLET_HEIGHT_RATIO = 1.0  # Full height on right
    
    # Colors (modern but outlined like VWO)
    COLOR_OUTLINE = QColor(0, 0, 0)           # Black outline
    COLOR_FILL = QColor(245, 248, 255)        # Light blue-white
    COLOR_ACCENT = QColor(200, 210, 230)      # Light blue accent
    COLOR_SELECTED = QColor(255, 200, 50)     # Gold selection
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create turbine ports: 2 in, 3 out."""
        # Input ports (left side - narrow end)
        self.add_input_port(
            QPointF(-self.WIDTH / 2, 0),
            name="main_inlet",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(0, -self.HEIGHT / 2),
            name="reheat_inlet",
            is_mandatory=False
        )
        
        # Output ports (right side - wide end, and bottom for extractions)
        self.add_output_port(
            QPointF(self.WIDTH / 2, 0),
            name="main_outlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(-self.WIDTH / 6, self.HEIGHT / 2),
            name="extraction_1",
            is_mandatory=False
        )
        self.add_output_port(
            QPointF(self.WIDTH / 6, self.HEIGHT / 2),
            name="extraction_2",
            is_mandatory=False
        )
    
    def boundingRect(self) -> QRectF:
        margin = 8
        return QRectF(
            -self.WIDTH / 2 - margin,
            -self.HEIGHT / 2 - margin,
            self.WIDTH + 2 * margin,
            self.HEIGHT + 2 * margin
        )
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint turbine symbol (VWO-style: narrow left, wide right)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Calculate dimensions
        inlet_half = self.HEIGHT * self.INLET_HEIGHT_RATIO / 2
        outlet_half = self.HEIGHT * self.OUTLET_HEIGHT_RATIO / 2
        
        # Create trapezoid path (narrow inlet left, wide outlet right)
        path = QPainterPath()
        path.moveTo(-self.WIDTH / 2, -inlet_half)   # Top-left (narrow)
        path.lineTo(self.WIDTH / 2, -outlet_half)   # Top-right (wide)
        path.lineTo(self.WIDTH / 2, outlet_half)    # Bottom-right (wide)
        path.lineTo(-self.WIDTH / 2, inlet_half)    # Bottom-left (narrow)
        path.closeSubpath()
        
        # Gradient fill (subtle modern look)
        gradient = QLinearGradient(-self.WIDTH / 2, 0, self.WIDTH / 2, 0)
        gradient.setColorAt(0, self.COLOR_FILL)
        gradient.setColorAt(1, self.COLOR_ACCENT)
        
        painter.setBrush(QBrush(gradient))
        pen_width = 2.5 if self.isSelected() else 2
        pen_color = self.COLOR_SELECTED if self.isSelected() else self.COLOR_OUTLINE
        painter.setPen(QPen(pen_color, pen_width))
        painter.drawPath(path)
        
        # Draw internal stage lines (VWO-style) - fewer lines for shorter turbine
        painter.setPen(QPen(self.COLOR_OUTLINE, 1))
        for i in range(1, 3):  # Fewer stage lines
            x = -self.WIDTH / 2 + (self.WIDTH * i / 3)
            # Linear interpolation of y limits
            t = i / 3
            y_top = -inlet_half + t * (-outlet_half - (-inlet_half))
            y_bottom = inlet_half + t * (outlet_half - inlet_half)
            painter.drawLine(int(x), int(y_top), int(x), int(y_bottom))
        
        # Draw label if enabled
        self.paint_label(painter)

