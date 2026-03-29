"""
TurbineItem - Steam/gas turbine symbol.

Trapezoid shape representing expansion from high to low pressure.
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath,
    QLinearGradient, QFont
)

from .base_item import BaseComponentItem


class TurbineItem(BaseComponentItem):
    """
    Steam turbine graphics item.
    
    Visual: Trapezoid shape (wide inlet, narrow outlet)
    Ports:
        - 2 inputs: main_inlet (top-left), reheat_inlet (bottom-left)
        - 3 outputs: main_outlet (right), extraction_1 (top-right), extraction_2 (mid-right)
    """
    
    # Dimensions
    WIDTH = 80
    HEIGHT = 60
    INLET_WIDTH = 50
    OUTLET_WIDTH = 25
    
    # Colors
    COLOR_PRIMARY = QColor(74, 144, 217)      # Blue
    COLOR_SECONDARY = QColor(45, 90, 135)     # Dark blue
    COLOR_BORDER = QColor(106, 183, 255)      # Light blue
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create turbine ports: 2 in, 3 out."""
        # Input ports (left side)
        self.add_input_port(
            QPointF(-self.WIDTH / 2, -self.HEIGHT / 4),
            name="main_inlet",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(-self.WIDTH / 2, self.HEIGHT / 4),
            name="reheat_inlet",
            is_mandatory=False
        )
        
        # Output ports (right side)
        self.add_output_port(
            QPointF(self.WIDTH / 2, 0),
            name="main_outlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.WIDTH / 2 - 10, -self.HEIGHT / 3),
            name="extraction_1",
            is_mandatory=False
        )
        self.add_output_port(
            QPointF(self.WIDTH / 2 - 5, self.HEIGHT / 4),
            name="extraction_2",
            is_mandatory=False
        )
    
    def boundingRect(self) -> QRectF:
        margin = 5
        return QRectF(
            -self.WIDTH / 2 - margin,
            -self.HEIGHT / 2 - margin,
            self.WIDTH + 2 * margin,
            self.HEIGHT + 2 * margin
        )
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint turbine symbol."""
        # Create trapezoid path (wide left, narrow right)
        path = QPainterPath()
        
        # Inlet side (left, wider)
        left_top = -self.HEIGHT / 2
        left_bottom = self.HEIGHT / 2
        
        # Outlet side (right, narrower)
        right_top = -self.HEIGHT / 4
        right_bottom = self.HEIGHT / 4
        
        path.moveTo(-self.WIDTH / 2, left_top)
        path.lineTo(self.WIDTH / 2, right_top)
        path.lineTo(self.WIDTH / 2, right_bottom)
        path.lineTo(-self.WIDTH / 2, left_bottom)
        path.closeSubpath()
        
        # Gradient fill
        gradient = QLinearGradient(-self.WIDTH / 2, 0, self.WIDTH / 2, 0)
        gradient.setColorAt(0, self.COLOR_PRIMARY)
        gradient.setColorAt(1, self.COLOR_SECONDARY)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawPath(path)
        
        # Selection highlight
        self.paint_selection_highlight(painter, path)
        
        # Draw label
        if self._name:
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self._name)
