"""
MixerItem - Flow mixer (2 inputs → 1 output).
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath
)

from .base_item import BaseComponentItem


class MixerItem(BaseComponentItem):
    """
    Flow mixer graphics item.
    
    Visual: T-junction - horizontal main line with vertical inlet from top
    Ports:
        - 2 inputs: inlet_1 (top), inlet_2 (left) 
        - 1 output: outlet (right)
    """
    
    # Dimensions  
    WIDTH = 40
    HEIGHT = 30
    LINE_WIDTH = 3
    
    # Colors (modern dark theme)
    COLOR_LINE = QColor(0, 150, 255)  # Bright blue
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create mixer ports: 2 in, 1 out."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        # Vertical inlet from top
        self.add_input_port(
            QPointF(0, -half_h),
            name="inlet_1",
            is_mandatory=True
        )
        # Horizontal inlet from left
        self.add_input_port(
            QPointF(-half_w, 0),
            name="inlet_2",
            is_mandatory=True
        )
        # Output to right
        self.add_output_port(
            QPointF(half_w, 0),
            name="outlet",
            is_mandatory=True
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
        """Paint mixer symbol - T junction with perpendicular inlet."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        # Line color - selection adjusts brightness
        color = self.COLOR_LINE.lighter(130) if self.isSelected() else self.COLOR_LINE
        pen = QPen(color, self.LINE_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw T-junction: horizontal line with vertical inlet
        # Horizontal line (left to right through center)
        painter.drawLine(QPointF(-half_w, 0), QPointF(half_w, 0))
        
        # Vertical line (top to center)
        painter.drawLine(QPointF(0, -half_h), QPointF(0, 0))
        
        # Small junction dot
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(0, 0), 3, 3)
        
        # Selection highlight
        if self.isSelected():
            path = QPainterPath()
            path.addRect(self.boundingRect().adjusted(5, 5, -5, -5))
            self.paint_selection_highlight(painter, path)
        
        # Draw label if enabled
        self.paint_label(painter)
