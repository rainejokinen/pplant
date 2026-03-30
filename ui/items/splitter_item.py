"""
SplitterItem - Flow splitter (1 input → 2 outputs).
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath
)

from .base_item import BaseComponentItem


class SplitterItem(BaseComponentItem):
    """
    Flow splitter graphics item.
    
    Visual: T-junction - horizontal main line with vertical outlet going down
    Ports:
        - 1 input: inlet (left)
        - 2 outputs: outlet_1 (right), outlet_2 (bottom)
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
        """Create splitter ports: 1 in, 2 out."""
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        # Inlet from left
        self.add_input_port(
            QPointF(-half_w, 0),
            name="inlet",
            is_mandatory=True
        )
        # Outlet to right (main flow)
        self.add_output_port(
            QPointF(half_w, 0),
            name="outlet_1",
            is_mandatory=True
        )
        # Outlet to bottom (perpendicular extraction)
        self.add_output_port(
            QPointF(0, half_h),
            name="outlet_2",
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
        """Paint splitter symbol - T junction with perpendicular outlet."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        half_w = self.WIDTH / 2
        half_h = self.HEIGHT / 2
        
        # Line color - selection adjusts brightness
        color = self.COLOR_LINE.lighter(130) if self.isSelected() else self.COLOR_LINE
        pen = QPen(color, self.LINE_WIDTH, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Draw T-junction: horizontal line with vertical outlet
        # Horizontal line (left to right through center)
        painter.drawLine(QPointF(-half_w, 0), QPointF(half_w, 0))
        
        # Vertical line (center to bottom)
        painter.drawLine(QPointF(0, 0), QPointF(0, half_h))
        
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
