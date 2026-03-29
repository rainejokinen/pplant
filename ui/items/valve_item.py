"""
ValveItem - Control valve symbol.

Bowtie/hourglass shape representing flow restriction.
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


class ValveItem(BaseComponentItem):
    """
    Control valve graphics item.
    
    Visual: Bowtie/hourglass shape
    Ports:
        - 1 input: inlet (left)
        - 1 output: outlet (right)
    """
    
    # Dimensions
    WIDTH = 40
    HEIGHT = 30
    
    # Colors
    COLOR_BODY = QColor(120, 120, 140)
    COLOR_BORDER = QColor(180, 180, 200)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create valve ports: 1 in, 1 out."""
        self.add_input_port(
            QPointF(-self.WIDTH / 2, 0),
            name="inlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.WIDTH / 2, 0),
            name="outlet",
            is_mandatory=True
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
        """Paint valve symbol (bowtie shape)."""
        path = QPainterPath()
        
        # Left triangle (pointing right)
        path.moveTo(-self.WIDTH / 2, -self.HEIGHT / 2)
        path.lineTo(0, 0)
        path.lineTo(-self.WIDTH / 2, self.HEIGHT / 2)
        path.closeSubpath()
        
        # Right triangle (pointing left)
        path.moveTo(self.WIDTH / 2, -self.HEIGHT / 2)
        path.lineTo(0, 0)
        path.lineTo(self.WIDTH / 2, self.HEIGHT / 2)
        path.closeSubpath()
        
        # Gradient fill
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_BODY.lighter(120))
        gradient.setColorAt(1, self.COLOR_BODY)
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawPath(path)
        
        # Selection highlight
        self.paint_selection_highlight(painter, path)
