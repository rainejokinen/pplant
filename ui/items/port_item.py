"""
PortItem - Connection port for component items.

Small circles on component edges for connecting flows.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Optional
from PyQt6.QtWidgets import QGraphicsEllipseItem, QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush

if TYPE_CHECKING:
    from .base_item import BaseComponentItem
    from .flow_item import FlowItem
    from ..canvas.flow_scene import FlowScene


class PortDirection(Enum):
    """Port direction - input or output."""
    INPUT = auto()
    OUTPUT = auto()


class PortItem(QGraphicsEllipseItem):
    """
    Connection port on a component.
    
    Visual representation of a port where flows connect.
    Handles connection drag initiation.
    
    Attributes:
        direction: INPUT or OUTPUT
        name: Port identifier (e.g., "steam_inlet")
        is_mandatory: Whether connection is required
    """
    
    # Port appearance
    RADIUS = 6
    
    # Colors by state
    COLOR_INPUT = QColor(80, 160, 255)      # Blue
    COLOR_OUTPUT = QColor(255, 100, 100)     # Red
    COLOR_CONNECTED = QColor(100, 220, 100)  # Green
    COLOR_HOVER = QColor(255, 220, 80)       # Gold
    COLOR_INVALID = QColor(150, 150, 150)    # Gray
    
    def __init__(
        self,
        direction: PortDirection,
        name: str = "",
        is_mandatory: bool = True,
        parent: Optional[BaseComponentItem] = None
    ):
        # Create ellipse rect centered at origin
        rect = QRectF(-self.RADIUS, -self.RADIUS, 2 * self.RADIUS, 2 * self.RADIUS)
        super().__init__(rect, parent)
        
        self._direction = direction
        self._name = name
        self._is_mandatory = is_mandatory
        self._connected_flow: Optional[FlowItem] = None
        self._is_hovered = False
        
        self._setup()
    
    def _setup(self):
        """Configure port item."""
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges, True)
        self.setZValue(10)  # Above component body
        self._update_appearance()
    
    def _update_appearance(self):
        """Update pen and brush based on state."""
        if self._connected_flow:
            color = self.COLOR_CONNECTED
        elif self._is_hovered:
            color = self.COLOR_HOVER
        elif self._direction == PortDirection.INPUT:
            color = self.COLOR_INPUT
        else:
            color = self.COLOR_OUTPUT
        
        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(120), 1.5))
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def direction(self) -> PortDirection:
        return self._direction
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def is_mandatory(self) -> bool:
        return self._is_mandatory
    
    @property
    def is_connected(self) -> bool:
        return self._connected_flow is not None
    
    @property
    def connected_flow(self) -> Optional[FlowItem]:
        return self._connected_flow
    
    @connected_flow.setter
    def connected_flow(self, flow: Optional[FlowItem]):
        self._connected_flow = flow
        self._update_appearance()
    
    @property
    def parent_component(self) -> Optional[BaseComponentItem]:
        """The component this port belongs to."""
        parent = self.parentItem()
        from .base_item import BaseComponentItem
        if isinstance(parent, BaseComponentItem):
            return parent
        return None
    
    def get_exit_direction(self) -> QPointF:
        """
        Get the unit vector direction that a flow line should extend when leaving this port.
        
        Based on port's position relative to component center:
        - Left side port → exit left (-1, 0)
        - Right side port → exit right (1, 0)  
        - Top side port → exit up (0, -1)
        - Bottom side port → exit down (0, 1)
        
        Returns:
            QPointF representing the exit direction as a unit vector
        """
        local_pos = self.pos()  # Position relative to parent component
        
        # Determine which edge the port is on based on which coordinate is dominant
        x, y = local_pos.x(), local_pos.y()
        
        # Compare absolute values to determine if port is more horizontal or vertical
        if abs(x) > abs(y):
            # Port is on left or right edge
            return QPointF(1, 0) if x > 0 else QPointF(-1, 0)
        else:
            # Port is on top or bottom edge
            return QPointF(0, 1) if y > 0 else QPointF(0, -1)
    
    # -------------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------------
    
    def hoverEnterEvent(self, event):
        """Highlight on hover."""
        self._is_hovered = True
        self._update_appearance()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Remove highlight."""
        self._is_hovered = False
        self._update_appearance()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Start connection drawing from output ports."""
        if event.button() == Qt.MouseButton.LeftButton:
            if self._direction == PortDirection.OUTPUT and not self.is_connected:
                # Start drawing connection
                scene = self.scene()
                if scene and hasattr(scene, 'start_connection'):
                    scene.start_connection(self)
                    event.accept()
                    return
        
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Complete connection on input ports."""
        if event.button() == Qt.MouseButton.LeftButton:
            scene = self.scene()
            if scene and hasattr(scene, 'is_connecting') and scene.is_connecting:
                if self._direction == PortDirection.INPUT and not self.is_connected:
                    scene.complete_connection(self)
                    event.accept()
                    return
        
        super().mouseReleaseEvent(event)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Notify flow when port position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
            if self._connected_flow:
                self._connected_flow.update_path()
        
        return super().itemChange(change, value)
    
    # -------------------------------------------------------------------------
    # Serialization helpers
    # -------------------------------------------------------------------------
    
    def get_port_id(self) -> tuple[str, str]:
        """
        Get identifier for this port (component_name, port_name).
        
        Used for serialization.
        """
        comp = self.parent_component
        comp_name = comp.name if comp else ""
        return (comp_name, self._name)
