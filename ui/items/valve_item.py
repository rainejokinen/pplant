"""
ValveItem - Control valve symbol (VWO-style with modern touches).

Bowtie/hourglass shape representing flow restriction.
"""

from __future__ import annotations

from typing import Optional
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QBrush, QPainterPath,
    QFont, QLinearGradient
)

from .base_item import BaseComponentItem


class ValveItem(BaseComponentItem):
    """
    Control valve graphics item (VWO-style bowtie).
    
    Visual: Two triangles meeting at a point
    Ports:
        - 1 input: inlet (left)
        - 1 output: outlet (right)
    """
    
    # Dimensions
    WIDTH = 30
    HEIGHT = 20
    
    # Colors (modern with VWO outline style)
    COLOR_OUTLINE = QColor(0, 0, 0)
    COLOR_FILL = QColor(248, 250, 255)        # Light blue-white
    COLOR_FILL_ACCENT = QColor(230, 240, 255) # Subtle blue accent
    COLOR_SELECTED = QColor(255, 200, 50)
    
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
        margin = 8
        return QRectF(
            -self.WIDTH / 2 - margin,
            -self.HEIGHT / 2 - margin,
            self.WIDTH + 2 * margin,
            self.HEIGHT + 2 * margin
        )
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint valve symbol (VWO-style bowtie with modern gradient)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Left triangle path
        left_path = QPainterPath()
        left_path.moveTo(-self.WIDTH / 2, -self.HEIGHT / 2)
        left_path.lineTo(0, 0)
        left_path.lineTo(-self.WIDTH / 2, self.HEIGHT / 2)
        left_path.closeSubpath()
        
        # Right triangle path
        right_path = QPainterPath()
        right_path.moveTo(self.WIDTH / 2, -self.HEIGHT / 2)
        right_path.lineTo(0, 0)
        right_path.lineTo(self.WIDTH / 2, self.HEIGHT / 2)
        right_path.closeSubpath()
        
        # Gradient for subtle modern look
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_FILL)
        gradient.setColorAt(1, self.COLOR_FILL_ACCENT)
        
        pen_width = 2.5 if self.isSelected() else 2
        pen_color = self.COLOR_SELECTED if self.isSelected() else self.COLOR_OUTLINE
        
        # Draw both triangles
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(pen_color, pen_width))
        painter.drawPath(left_path)
        painter.drawPath(right_path)
        
        # Label above
        if self._name:
            painter.setPen(self.COLOR_OUTLINE)
            painter.setFont(QFont("Segoe UI", 7))
            painter.drawText(
                QRectF(-self.WIDTH, -self.HEIGHT/2 - 14, self.WIDTH * 2, 12),
                Qt.AlignmentFlag.AlignCenter, 
                self._name
            )

