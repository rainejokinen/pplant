"""
SplitterItem - Flow splitter (1 input → 2 outputs).
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath,
    QPolygonF
)

from .base_item import BaseComponentItem


class SplitterItem(BaseComponentItem):
    """
    Flow splitter graphics item.
    
    Visual: Y-junction with one inlet diverging to two outlet arrows
    Ports:
        - 1 input: inlet (left)
        - 2 outputs: outlet_1 (top-right), outlet_2 (bottom-right)
    """
    
    # Dimensions
    WIDTH = 50
    HEIGHT = 40
    ARROW_HEAD = 12
    
    # Colors
    COLOR_BODY = QColor(140, 100, 180)
    COLOR_BORDER = QColor(110, 70, 150)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create splitter ports: 1 in, 2 out."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        self.add_input_port(
            QPointF(-half_w, 0),
            name="inlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(half_w, -half_h * 0.6),
            name="outlet_1",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(half_w, half_h * 0.6),
            name="outlet_2",
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
        """Paint splitter symbol - Y junction with diverging arrows."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.setBrush(QBrush(self.COLOR_BODY))
        
        # Draw outlet arrows pointing outward
        path = QPainterPath()
        
        # Top outlet arrow (pointing right/outward)
        arrow_base = half_w - self.ARROW_HEAD
        path.moveTo(arrow_base, -half_h * 0.6 - 5)  # Top of arrow
        path.lineTo(half_w, -half_h * 0.6)  # Arrow tip
        path.lineTo(arrow_base, -half_h * 0.6 + 5)  # Bottom of arrow
        path.lineTo(arrow_base, -half_h * 0.6 - 5)
        
        # Bottom outlet arrow (pointing right/outward)
        path.moveTo(arrow_base, half_h * 0.6 - 5)  # Top of arrow
        path.lineTo(half_w, half_h * 0.6)  # Arrow tip
        path.lineTo(arrow_base, half_h * 0.6 + 5)  # Bottom of arrow
        path.lineTo(arrow_base, half_h * 0.6 - 5)
        
        painter.drawPath(path)
        
        # Draw the lines from inlet to center and out to arrows
        painter.setPen(QPen(self.COLOR_BORDER, 3))
        
        # Inlet to center
        painter.drawLine(QPointF(-half_w, 0), QPointF(0, 0))
        
        # Center to top outlet
        painter.drawLine(
            QPointF(0, 0),
            QPointF(arrow_base, -half_h * 0.6)
        )
        
        # Center to bottom outlet
        painter.drawLine(
            QPointF(0, 0),
            QPointF(arrow_base, half_h * 0.6)
        )
        
        # Draw center junction circle
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.setBrush(QBrush(self.COLOR_BODY.lighter(110)))
        painter.drawEllipse(QPointF(0, 0), 6, 6)
        
        # Selection highlight
        path = QPainterPath()
        path.addRect(self.boundingRect().adjusted(3, 3, -3, -3))
        self.paint_selection_highlight(painter, path)
