"""
Heat exchanger component items.

Includes:
- HeatExchangerItem (base)
- CondenserItem
- FeedwaterHeaterItem
- WaterWaterHXItem
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


class HeatExchangerItem(BaseComponentItem):
    """
    Heat exchanger graphics item.
    
    Visual: Rectangle with internal tube pattern
    Ports:
        - Cold side: cold_inlet (bottom-left), cold_outlet (bottom-right)
        - Hot side: hot_inlet_1 (top-left), hot_inlet_2 (top-center), hot_outlet (top-right)
    """
    
    # Dimensions
    WIDTH = 100
    HEIGHT = 60
    
    # Colors
    COLOR_COLD = QColor(80, 180, 255)        # Cyan
    COLOR_HOT = QColor(255, 120, 100)        # Coral
    COLOR_BODY = QColor(60, 65, 75)
    COLOR_BORDER = QColor(120, 130, 150)
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create HX ports: 3 in, 2 out."""
        # Cold side (bottom)
        self.add_input_port(
            QPointF(-self.WIDTH / 3, self.HEIGHT / 2),
            name="cold_inlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.WIDTH / 3, self.HEIGHT / 2),
            name="cold_outlet",
            is_mandatory=True
        )
        
        # Hot side (top)
        self.add_input_port(
            QPointF(-self.WIDTH / 3, -self.HEIGHT / 2),
            name="hot_inlet_1",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(0, -self.HEIGHT / 2),
            name="hot_inlet_2",
            is_mandatory=False
        )
        self.add_output_port(
            QPointF(self.WIDTH / 3, -self.HEIGHT / 2),
            name="hot_outlet",
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
        """Paint heat exchanger symbol."""
        # Main body
        body_rect = QRectF(-self.WIDTH / 2, -self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        
        # Two-tone gradient (hot top, cold bottom)
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_HOT.darker(150))
        gradient.setColorAt(0.5, self.COLOR_BODY)
        gradient.setColorAt(1, self.COLOR_COLD.darker(150))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawRoundedRect(body_rect, 5, 5)
        
        # Draw internal tubes pattern
        self._draw_tubes(painter)
        
        # Selection highlight
        path = QPainterPath()
        path.addRoundedRect(body_rect, 5, 5)
        self.paint_selection_highlight(painter, path)
        
        # Label
        if self._name:
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, self._name)
    
    def _draw_tubes(self, painter: QPainter):
        """Draw internal tube pattern."""
        painter.setPen(QPen(self.COLOR_COLD, 1.5))
        
        # Horizontal tubes
        y_positions = [-self.HEIGHT / 6, self.HEIGHT / 6]
        for y in y_positions:
            painter.drawLine(
                int(-self.WIDTH / 2 + 10), int(y),
                int(self.WIDTH / 2 - 10), int(y)
            )


class CondenserItem(HeatExchangerItem):
    """
    Condenser - steam to condensate heat exchanger.
    
    Visual: Rectangle with rounded bottom (shell shape)
    """
    
    COLOR_BODY = QColor(50, 60, 80)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint condenser with rounded bottom."""
        path = QPainterPath()
        
        # Rounded bottom rectangle
        path.moveTo(-self.WIDTH / 2, -self.HEIGHT / 2)
        path.lineTo(self.WIDTH / 2, -self.HEIGHT / 2)
        path.lineTo(self.WIDTH / 2, self.HEIGHT / 4)
        path.arcTo(
            -self.WIDTH / 2, self.HEIGHT / 4 - self.HEIGHT / 4,
            self.WIDTH, self.HEIGHT / 2,
            0, -180
        )
        path.closeSubpath()
        
        # Gradient
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_HOT.darker(150))
        gradient.setColorAt(1, self.COLOR_COLD.darker(120))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawPath(path)
        
        # Internal pattern
        self._draw_tubes(painter)
        
        # Selection
        self.paint_selection_highlight(painter, path)
        
        # Label
        if self._name:
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self._name)


class FeedwaterHeaterItem(HeatExchangerItem):
    """
    Feedwater heater (FWH/FWT).
    
    Visual: Horizontal cylinder shape
    """
    
    COLOR_BODY = QColor(70, 80, 100)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint FWH as horizontal cylinder."""
        # Main body
        body_rect = QRectF(-self.WIDTH / 2, -self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_BODY.lighter(130))
        gradient.setColorAt(0.5, self.COLOR_BODY)
        gradient.setColorAt(1, self.COLOR_BODY.darker(120))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(self.COLOR_BORDER, 2))
        painter.drawRoundedRect(body_rect, self.HEIGHT / 2, self.HEIGHT / 2)
        
        # Selection
        path = QPainterPath()
        path.addRoundedRect(body_rect, self.HEIGHT / 2, self.HEIGHT / 2)
        self.paint_selection_highlight(painter, path)
        
        # Label
        if self._name:
            painter.setPen(Qt.GlobalColor.white)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(body_rect, Qt.AlignmentFlag.AlignCenter, self._name)


class WaterWaterHXItem(HeatExchangerItem):
    """
    Water-to-water heat exchanger.
    
    Same visual as base HX but with water-only colors.
    """
    
    COLOR_HOT = QColor(255, 160, 120)   # Warm water
    COLOR_COLD = QColor(100, 200, 255)  # Cool water
