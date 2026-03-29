"""
MixerItem - Flow mixer (2 inputs → 1 output).
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath,
    QLinearGradient
)

from .base_item import BaseComponentItem


class MixerItem(BaseComponentItem):
    """
    Flow mixer graphics item.
    
    Visual: Y-junction or circle with converging arrows
    Ports:
        - 2 inputs: inlet_1 (top-left), inlet_2 (bottom-left)
        - 1 output: outlet (right)
    """
    
    # Dimensions
    RADIUS = 20
    
    # Colors
    COLOR_BODY = QColor(100, 140, 180)
    COLOR_BORDER = QColor(140, 180, 220)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create mixer ports: 2 in, 1 out."""
        self.add_input_port(
            QPointF(-self.RADIUS, -self.RADIUS * 0.7),
            name="inlet_1",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(-self.RADIUS, self.RADIUS * 0.7),
            name="inlet_2",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.RADIUS, 0),
            name="outlet",
            is_mandatory=True
        )
    
    def boundingRect(self) -> QRectF:
        margin = 5
        return QRectF(
            -self.RADIUS - margin,
            -self.RADIUS - margin,
            2 * self.RADIUS + 2 * margin,
            2 * self.RADIUS + 2 * margin
        )
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint mixer symbol."""
        # Circle body
        gradient = QLinearGradient(-self.RADIUS, -self.RADIUS, self.RADIUS, self.RADIUS)
        gradient.setColorAt(0, self.COLOR_BODY.lighter(120))
        gradient.setColorAt(1, self.COLOR_BODY)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawEllipse(QPointF(0, 0), self.RADIUS, self.RADIUS)
        
        # Draw converging arrows inside
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        # Top arrow
        painter.drawLine(-8, -8, 0, 0)
        # Bottom arrow
        painter.drawLine(-8, 8, 0, 0)
        # Output arrow
        painter.drawLine(0, 0, 10, 0)
        
        # Arrow head
        painter.drawLine(6, -4, 10, 0)
        painter.drawLine(6, 4, 10, 0)
        
        # Selection highlight
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.RADIUS, self.RADIUS)
        self.paint_selection_highlight(painter, path)
