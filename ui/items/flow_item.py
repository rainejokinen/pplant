"""
FlowItem - Bezier curve connection between ports.

Represents a flow connection (pipe) between two components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QGraphicsPathItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPolygonF

if TYPE_CHECKING:
    from .port_item import PortItem
    from .base_item import BaseComponentItem


class FlowItem(QGraphicsPathItem):
    """
    Bezier curve flow connection between two ports.
    
    Draws a smooth curve from source (output) port to target (input) port,
    with an arrow indicating flow direction.
    
    Features:
        - Auto-updates path when connected components move
        - Direction arrow at midpoint
        - Color coding by fluid type/state
        - Selectable for deletion
    """
    
    # Appearance
    LINE_WIDTH = 3
    LINE_WIDTH_SELECTED = 4
    COLOR_DEFAULT = QColor(100, 180, 255)     # Light blue
    COLOR_STEAM = QColor(255, 120, 100)       # Coral red
    COLOR_WATER = QColor(80, 200, 255)        # Cyan
    COLOR_SELECTED = QColor(255, 200, 50)     # Gold
    
    # Arrow size
    ARROW_SIZE = 10
    
    def __init__(
        self,
        source_port: PortItem,
        target_port: PortItem,
        parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        self._source_port = source_port
        self._target_port = target_port
        self._fluid_type = "default"  # "steam", "water", "default"
        
        self._setup()
        self._connect_ports()
        self.update_path()
    
    def _setup(self):
        """Configure item."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)  # Below components
        self.setAcceptHoverEvents(True)
        self._update_pen()
    
    def _connect_ports(self):
        """Register this flow with both ports."""
        self._source_port.connected_flow = self
        self._target_port.connected_flow = self
    
    def disconnect(self):
        """Unregister this flow from ports."""
        if self._source_port:
            self._source_port.connected_flow = None
        if self._target_port:
            self._target_port.connected_flow = None
    
    def _update_pen(self):
        """Update pen based on selection and fluid type."""
        if self.isSelected():
            color = self.COLOR_SELECTED
            width = self.LINE_WIDTH_SELECTED
        else:
            color = self._get_fluid_color()
            width = self.LINE_WIDTH
        
        self.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    
    def _get_fluid_color(self) -> QColor:
        """Get color based on fluid type."""
        if self._fluid_type == "steam":
            return self.COLOR_STEAM
        elif self._fluid_type == "water":
            return self.COLOR_WATER
        return self.COLOR_DEFAULT
    
    def update_path(self):
        """Recalculate Bezier path between ports."""
        if not self._source_port or not self._target_port:
            return
        
        start = self._source_port.scenePos()
        end = self._target_port.scenePos()
        
        # Calculate control points for smooth Bezier curve
        path = self._create_bezier_path(start, end)
        self.setPath(path)
    
    def _create_bezier_path(self, start: QPointF, end: QPointF) -> QPainterPath:
        """
        Create a smooth Bezier curve path.
        
        Uses horizontal-biased control points for clean routing.
        """
        path = QPainterPath()
        path.moveTo(start)
        
        # Calculate distance and control point offset
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # Control point offset (horizontal bias)
        offset = max(abs(dx) * 0.5, 50)
        
        # Control points
        c1 = QPointF(start.x() + offset, start.y())
        c2 = QPointF(end.x() - offset, end.y())
        
        # If going backwards (left), adjust control points
        if dx < 0:
            offset = max(abs(dx) * 0.5, 80)
            # Route around - go down/up first
            mid_y = (start.y() + end.y()) / 2 + (50 if dy >= 0 else -50)
            c1 = QPointF(start.x() + 50, mid_y)
            c2 = QPointF(end.x() - 50, mid_y)
        
        path.cubicTo(c1, c2, end)
        return path
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint the flow line and direction arrow."""
        # Update pen for selection state
        self._update_pen()
        
        # Draw path
        super().paint(painter, option, widget)
        
        # Draw direction arrow at midpoint
        self._draw_arrow(painter)
    
    def _draw_arrow(self, painter: QPainter):
        """Draw flow direction arrow at path midpoint."""
        path = self.path()
        if path.isEmpty():
            return
        
        # Get point and angle at 50% of path
        t = 0.5
        point = path.pointAtPercent(t)
        angle = path.angleAtPercent(t)
        
        # Create arrow polygon
        arrow = QPolygonF()
        arrow.append(QPointF(0, 0))
        arrow.append(QPointF(-self.ARROW_SIZE, -self.ARROW_SIZE / 2))
        arrow.append(QPointF(-self.ARROW_SIZE, self.ARROW_SIZE / 2))
        
        # Transform arrow to position and angle
        painter.save()
        painter.translate(point)
        painter.rotate(-angle)
        
        # Fill arrow
        color = self.COLOR_SELECTED if self.isSelected() else self._get_fluid_color()
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow)
        
        painter.restore()
    
    def shape(self) -> QPainterPath:
        """Return shape for hit testing (wider than visual)."""
        # Create a wider path for easier selection
        stroker = QPainterPath()
        path = self.path()
        
        # Use the path itself with a wide pen
        from PyQt6.QtGui import QPainterPathStroker
        ps = QPainterPathStroker()
        ps.setWidth(15)  # Hit area width
        return ps.createStroke(path)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Handle selection change."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._update_pen()
        return super().itemChange(change, value)
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def source_port(self) -> PortItem:
        return self._source_port
    
    @property
    def target_port(self) -> PortItem:
        return self._target_port
    
    @property
    def fluid_type(self) -> str:
        return self._fluid_type
    
    @fluid_type.setter
    def fluid_type(self, value: str):
        self._fluid_type = value
        self._update_pen()
        self.update()
    
    def is_connected_to(self, component: BaseComponentItem) -> bool:
        """Check if this flow connects to the given component."""
        source_comp = self._source_port.parent_component
        target_comp = self._target_port.parent_component
        return component is source_comp or component is target_comp
    
    @property
    def source_component(self) -> Optional[BaseComponentItem]:
        return self._source_port.parent_component if self._source_port else None
    
    @property
    def target_component(self) -> Optional[BaseComponentItem]:
        return self._target_port.parent_component if self._target_port else None
