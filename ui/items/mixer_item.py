"""
MixerItem - Flow mixer (2 inputs → 1 output).
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


class MixerItem(BaseComponentItem):
    """
    Flow mixer graphics item.
    
    Visual: Y-junction with two inlet arrows converging into one outlet
    Ports:
        - 2 inputs: inlet_1 (top-left), inlet_2 (bottom-left)
        - 1 output: outlet (right)
    """
    
    # Dimensions
    WIDTH = 50
    HEIGHT = 40
    ARROW_HEAD = 12
    
    # Colors
    COLOR_BODY = QColor(100, 140, 180)
    COLOR_BORDER = QColor(70, 110, 150)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create mixer ports: 2 in, 1 out."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        self.add_input_port(
            QPointF(-half_w, -half_h * 0.6),
            name="inlet_1",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(-half_w, half_h * 0.6),
            name="inlet_2",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(half_w, 0),
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
        """Paint mixer symbol - Y junction with converging arrows."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.setBrush(QBrush(self.COLOR_BODY))
        
        # Draw Y-junction shape as polygon
        # Two inlet arrows on left converging to a single outlet on right
        path = QPainterPath()
        
        # Top inlet branch (arrow shape)
        path.moveTo(-half_w, -half_h * 0.6 - 5)  # Top of top arrow
        path.lineTo(-half_w + self.ARROW_HEAD, -half_h * 0.6)  # Arrow tip
        path.lineTo(-half_w, -half_h * 0.6 + 5)  # Bottom of top arrow
        path.lineTo(-half_w, -half_h * 0.6 - 5)
        
        # Bottom inlet branch (arrow shape)
        path.moveTo(-half_w, half_h * 0.6 - 5)  # Top of bottom arrow
        path.lineTo(-half_w + self.ARROW_HEAD, half_h * 0.6)  # Arrow tip
        path.lineTo(-half_w, half_h * 0.6 + 5)  # Bottom of bottom arrow
        path.lineTo(-half_w, half_h * 0.6 - 5)
        
        painter.drawPath(path)
        
        # Draw the joining lines from arrow tips to center and out
        painter.setPen(QPen(self.COLOR_BORDER, 3))
        
        # Top inlet line to center
        painter.drawLine(
            QPointF(-half_w + self.ARROW_HEAD, -half_h * 0.6),
            QPointF(0, 0)
        )
        
        # Bottom inlet line to center
        painter.drawLine(
            QPointF(-half_w + self.ARROW_HEAD, half_h * 0.6),
            QPointF(0, 0)
        )
        
        # Center to outlet
        painter.drawLine(QPointF(0, 0), QPointF(half_w, 0))
        
        # Draw center junction circle
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.setBrush(QBrush(self.COLOR_BODY.lighter(110)))
        painter.drawEllipse(QPointF(0, 0), 6, 6)
        
        # Selection highlight
        path = QPainterPath()
        path.addRect(self.boundingRect().adjusted(3, 3, -3, -3))
        self.paint_selection_highlight(painter, path)
