"""
Heat exchanger component items (VWO-style with modern touches).

Square/rectangle shapes with diagonal lines indicating heat transfer.
Red outline for steam/condensate, blue for water.

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
    Heat exchanger graphics item (VWO-style square with diagonals).
    
    Visual: Square with X pattern inside (as in VWO image)
    Ports:
        - Cold side: cold_inlet (left), cold_outlet (right)
        - Hot side: hot_inlet_1 (top), hot_inlet_2 (top), hot_outlet (bottom)
    """
    
    # Dimensions
    WIDTH = 50
    HEIGHT = 50
    
    # Colors (VWO-style red outline)
    COLOR_OUTLINE = QColor(255, 0, 0)         # Red outline
    COLOR_FILL = QColor(255, 250, 250)        # Very light pink/white
    COLOR_FILL_ACCENT = QColor(255, 240, 240) # Subtle pink for gradient
    COLOR_SELECTED = QColor(255, 200, 50)     # Gold selection
    
    def __init__(self, name: str = "", parent: Optional[QGraphicsItem] = None):
        super().__init__(name=name, parent=parent)
    
    def _create_ports(self):
        """Create HX ports: 3 in, 2 out."""
        # Cold side (horizontal through)
        self.add_input_port(
            QPointF(-self.WIDTH / 2, 0),
            name="cold_inlet",
            is_mandatory=True
        )
        self.add_output_port(
            QPointF(self.WIDTH / 2, 0),
            name="cold_outlet",
            is_mandatory=True
        )
        
        # Hot side (vertical through)
        self.add_input_port(
            QPointF(0, -self.HEIGHT / 2),
            name="hot_inlet_1",
            is_mandatory=True
        )
        self.add_input_port(
            QPointF(self.WIDTH / 4, -self.HEIGHT / 2),
            name="hot_inlet_2",
            is_mandatory=False
        )
        self.add_output_port(
            QPointF(0, self.HEIGHT / 2),
            name="hot_outlet",
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
        """Paint heat exchanger symbol (VWO-style square with X)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Main body - square
        rect = QRectF(-self.WIDTH / 2, -self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        
        # Subtle gradient fill
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_FILL)
        gradient.setColorAt(1, self.COLOR_FILL_ACCENT)
        
        painter.setBrush(QBrush(gradient))
        pen_width = 2.5 if self.isSelected() else 2
        pen_color = self.COLOR_SELECTED if self.isSelected() else self.COLOR_OUTLINE
        painter.setPen(QPen(pen_color, pen_width))
        painter.drawRect(rect)
        
        # Draw Z-shaped heating pipe inside (VWO-style zigzag)
        painter.setPen(QPen(self.COLOR_OUTLINE, 1.5))
        m = 6  # margin from edge
        hw = self.WIDTH / 2 - m
        hh = self.HEIGHT / 2 - m
        
        # Z-pattern: horizontal at top, diagonal, horizontal at bottom
        # Top horizontal
        painter.drawLine(int(-hw), int(-hh), int(hw), int(-hh))
        # Diagonal from right-top to left-bottom
        painter.drawLine(int(hw), int(-hh), int(-hw), int(hh))
        # Bottom horizontal
        painter.drawLine(int(-hw), int(hh), int(hw), int(hh))
        
        # Draw label if enabled
        self.paint_label(painter)


class CondenserItem(HeatExchangerItem):
    """
    Condenser - larger rectangle (VWO KLV style, yellow/tan).
    """
    
    WIDTH = 80
    HEIGHT = 40
    
    # Condenser colors (tan/yellow like VWO)
    COLOR_FILL = QColor(255, 235, 180)
    COLOR_FILL_ACCENT = QColor(255, 220, 150)
    COLOR_OUTLINE = QColor(0, 0, 0)
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint condenser (larger rectangle, VWO yellow/tan)."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(-self.WIDTH / 2, -self.HEIGHT / 2, self.WIDTH, self.HEIGHT)
        
        # Gradient fill
        gradient = QLinearGradient(0, -self.HEIGHT / 2, 0, self.HEIGHT / 2)
        gradient.setColorAt(0, self.COLOR_FILL)
        gradient.setColorAt(1, self.COLOR_FILL_ACCENT)
        
        painter.setBrush(QBrush(gradient))
        pen_width = 2.5 if self.isSelected() else 2
        pen_color = self.COLOR_SELECTED if self.isSelected() else self.COLOR_OUTLINE
        painter.setPen(QPen(pen_color, pen_width))
        painter.drawRect(rect)
        
        # Internal horizontal lines pattern (tube bundle representation)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        for i in range(1, 4):
            y = -self.HEIGHT/2 + (self.HEIGHT * i / 4)
            painter.drawLine(int(-self.WIDTH/2 + 5), int(y), int(self.WIDTH/2 - 5), int(y))
        
        # Label centered
        if self._name:
            painter.setPen(QColor(0, 0, 0))
            painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._name)


class FeedwaterHeaterItem(HeatExchangerItem):
    """
    Feedwater heater (FWH/FWT) - VWO style square with X, red outline.
    """
    
    COLOR_OUTLINE = QColor(255, 0, 0)         # Red like VWO
    COLOR_FILL = QColor(255, 250, 250)
    COLOR_FILL_ACCENT = QColor(255, 240, 240)


class WaterWaterHXItem(HeatExchangerItem):
    """
    Water-to-water heat exchanger.
    Blue outline version.
    """
    
    COLOR_OUTLINE = QColor(0, 0, 255)         # Blue
    COLOR_FILL = QColor(250, 250, 255)        # Light blue-white
    COLOR_FILL_ACCENT = QColor(240, 245, 255)

