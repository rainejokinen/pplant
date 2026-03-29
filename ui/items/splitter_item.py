"""
SplitterItem - Flow splitter (1 input → 2 outputs).
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


class SplitterItem(BaseComponentItem):
    """
    Flow splitter graphics item.
    
    Visual: Y-junction or circle with diverging arrows
    Ports:
        - 1 input: inlet (left)
        - 2 outputs: outlet_1 (top-right), outlet_2 (bottom-right)
    """
    
    # Dimensions
    RADIUS = 20
    
    # Colors
    COLOR_BODY = QColor(140, 100, 180)
    COLOR_BORDER = QColor(180, 140, 220)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create splitter ports: 1 in, 2 out."""
        self.add_input_port(
            QPointF(-self.RADIUS, 0),
            name="inlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.RADIUS, -self.RADIUS * 0.7),
            name="outlet_1",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.RADIUS, self.RADIUS * 0.7),
            name="outlet_2",
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
        """Paint splitter symbol."""
        # Circle body
        gradient = QLinearGradient(-self.RADIUS, -self.RADIUS, self.RADIUS, self.RADIUS)
        gradient.setColorAt(0, self.COLOR_BODY.lighter(120))
        gradient.setColorAt(1, self.COLOR_BODY)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawEllipse(QPointF(0, 0), self.RADIUS, self.RADIUS)
        
        # Draw diverging arrows inside
        painter.setPen(QPen(Qt.GlobalColor.white, 2))
        # Input arrow
        painter.drawLine(-10, 0, 0, 0)
        # Top output
        painter.drawLine(0, 0, 8, -8)
        # Bottom output
        painter.drawLine(0, 0, 8, 8)
        
        # Arrow heads
        painter.drawLine(4, -10, 8, -8)
        painter.drawLine(10, -4, 8, -8)
        painter.drawLine(4, 10, 8, 8)
        painter.drawLine(10, 4, 8, 8)
        
        # Selection highlight
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.RADIUS, self.RADIUS)
        self.paint_selection_highlight(painter, path)
