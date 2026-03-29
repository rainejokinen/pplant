"""
BaseComponentItem - Abstract base class for component graphics items.

All component symbols (Turbine, Valve, HX, etc.) inherit from this.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, List
from PyQt6.QtWidgets import (
    QGraphicsItem, QGraphicsObject, QMenu,
    QStyleOptionGraphicsItem, QWidget
)
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath

if TYPE_CHECKING:
    from ..canvas.flow_scene import FlowScene
    from .port_item import PortItem
    from components.base import Component


class BaseComponentItem(QGraphicsObject):
    """
    Abstract base class for all component graphics items.
    
    Provides:
        - Movable, selectable behavior
        - Selection highlighting (glow effect)
        - Port management
        - Context menu with delete option
        - Link to model Component instance
    
    Subclasses must implement:
        - boundingRect()
        - paint()
        - _create_ports()
    """
    
    # Signals
    position_changed = pyqtSignal(object)  # Emitted when item moves
    
    # Style constants
    SELECTION_COLOR = QColor(255, 200, 50, 180)  # Gold glow
    SELECTION_WIDTH = 4
    
    def __init__(
        self,
        name: str = "",
        model_component: Optional[Component] = None,
        parent: Optional[QGraphicsItem] = None
    ):
        super().__init__(parent)
        
        self._name = name
        self._model = model_component
        
        self._input_ports: List[PortItem] = []
        self._output_ports: List[PortItem] = []
        
        self._setup_item()
        self._create_ports()
    
    def _setup_item(self):
        """Configure item flags and behavior."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
    
    @abstractmethod
    def _create_ports(self):
        """
        Create input/output ports for this component.
        
        Subclasses must implement this to add PortItems.
        Use self.add_input_port() and self.add_output_port() helper methods.
        """
        pass
    
    @abstractmethod
    def boundingRect(self) -> QRectF:
        """Return the bounding rectangle of this item."""
        pass
    
    @abstractmethod
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]):
        """Paint the component symbol."""
        pass
    
    # -------------------------------------------------------------------------
    # Port Management
    # -------------------------------------------------------------------------
    
    def add_input_port(
        self,
        relative_pos: QPointF,
        name: str = "",
        is_mandatory: bool = True
    ) -> PortItem:
        """
        Add an input port at the specified position relative to item center.
        
        Args:
            relative_pos: Position relative to item origin
            name: Optional port name
            is_mandatory: Whether port must be connected
            
        Returns:
            Created PortItem
        """
        from .port_item import PortItem, PortDirection
        
        port = PortItem(
            direction=PortDirection.INPUT,
            name=name,
            is_mandatory=is_mandatory,
            parent=self
        )
        port.setPos(relative_pos)
        self._input_ports.append(port)
        return port
    
    def add_output_port(
        self,
        relative_pos: QPointF,
        name: str = "",
        is_mandatory: bool = True
    ) -> PortItem:
        """
        Add an output port at the specified position relative to item center.
        """
        from .port_item import PortItem, PortDirection
        
        port = PortItem(
            direction=PortDirection.OUTPUT,
            name=name,
            is_mandatory=is_mandatory,
            parent=self
        )
        port.setPos(relative_pos)
        self._output_ports.append(port)
        return port
    
    @property
    def input_ports(self) -> List[PortItem]:
        """List of input ports."""
        return self._input_ports.copy()
    
    @property
    def output_ports(self) -> List[PortItem]:
        """List of output ports."""
        return self._output_ports.copy()
    
    @property
    def all_ports(self) -> List[PortItem]:
        """All ports (inputs + outputs)."""
        return self._input_ports + self._output_ports
    
    def get_port_by_name(self, name: str) -> Optional[PortItem]:
        """Find a port by its name."""
        for port in self.all_ports:
            if port.name == name:
                return port
        return None
    
    # -------------------------------------------------------------------------
    # Selection & Highlighting
    # -------------------------------------------------------------------------
    
    def paint_selection_highlight(self, painter: QPainter, path: QPainterPath):
        """
        Paint selection glow around the component.
        
        Call this from paint() when item is selected.
        """
        if self.isSelected():
            painter.setPen(QPen(self.SELECTION_COLOR, self.SELECTION_WIDTH))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
    
    # -------------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------------
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Handle item changes, particularly position changes."""
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Notify connected flows to update their paths
            self.position_changed.emit(self)
            self._update_connected_flows()
        
        return super().itemChange(change, value)
    
    def _update_connected_flows(self):
        """Tell all connected flows to update their paths."""
        for port in self.all_ports:
            if port.connected_flow:
                port.connected_flow.update_path()
    
    def contextMenuEvent(self, event):
        """Show context menu."""
        menu = QMenu()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self._on_delete)
        
        menu.addSeparator()
        
        props_action = menu.addAction("Properties...")
        props_action.triggered.connect(self._on_properties)
        
        menu.exec(event.screenPos())
    
    def _on_delete(self):
        """Handle delete action."""
        scene = self.scene()
        if scene and hasattr(scene, 'remove_component'):
            scene.remove_component(self)
    
    def _on_properties(self):
        """Handle properties action (can be overridden)."""
        # TODO: Open properties dialog
        pass
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def name(self) -> str:
        return self._name
    
    @name.setter
    def name(self, value: str):
        self._name = value
        self.update()
    
    @property
    def model(self) -> Optional[Component]:
        """The underlying model Component instance."""
        return self._model
    
    @model.setter
    def model(self, component: Component):
        self._model = component
    
    @property
    def component_type(self) -> str:
        """Return the component type name (class name by default)."""
        return self.__class__.__name__.replace("Item", "")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self._name}', pos={self.pos()})"
