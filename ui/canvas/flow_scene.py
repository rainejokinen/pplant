"""
FlowScene - Graphics scene for flow diagram components.

Handles drag-and-drop component creation, interactive port connections,
and manages all component and flow items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Type
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsItem
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QColor, QTransform

if TYPE_CHECKING:
    from .flow_view import FlowView
    from ..items.port_item import PortItem
    from ..items.base_item import BaseComponentItem
    from ..items.flow_item import FlowItem


# MIME type for component drag-drop
COMPONENT_MIME_TYPE = "application/x-pplant-component"


class FlowScene(QGraphicsScene):
    """
    Custom QGraphicsScene for power plant flow diagrams.
    
    Features:
        - Drag-and-drop component creation from library
        - Interactive port-to-port connection drawing
        - Selection management with signals
        - Component and flow item tracking
    
    Signals:
        component_added(BaseComponentItem): New component added to scene
        component_removed(BaseComponentItem): Component removed from scene
        flow_added(FlowItem): New flow connection created
        flow_removed(FlowItem): Flow connection removed
        selection_changed_items(list): List of currently selected items
    """
    
    component_added = pyqtSignal(object)
    component_removed = pyqtSignal(object)
    flow_added = pyqtSignal(object)
    flow_removed = pyqtSignal(object)
    selection_changed_items = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scene dimensions (large virtual canvas)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        
        # Item tracking
        self._components: list[BaseComponentItem] = []
        self._flows: list[FlowItem] = []
        
        # Connection drawing state
        self._is_connecting = False
        self._connection_source: Optional[PortItem] = None
        self._temp_line: Optional[QGraphicsLineItem] = None
        
        # Component factory registry
        self._component_factories: Dict[str, Type[BaseComponentItem]] = {}
        
        # Connect selection changes
        self.selectionChanged.connect(self._on_selection_changed)
    
    def register_component_type(self, type_name: str, factory_class: Type[BaseComponentItem]):
        """
        Register a component type for drag-and-drop creation.
        
        Args:
            type_name: String identifier (e.g., "Turbine")
            factory_class: The item class to instantiate
        """
        self._component_factories[type_name] = factory_class
    
    def create_component(self, type_name: str, pos: QPointF, name: str = "") -> Optional[BaseComponentItem]:
        """
        Create a component item at the specified position.
        
        Args:
            type_name: Registered component type
            pos: Scene position
            name: Optional component name
            
        Returns:
            Created component item, or None if type not registered
        """
        if type_name not in self._component_factories:
            print(f"Unknown component type: {type_name}")
            return None
        
        factory = self._component_factories[type_name]
        item = factory(name=name)
        item.setPos(pos)
        self.addItem(item)
        self._components.append(item)
        self.component_added.emit(item)
        return item
    
    def remove_component(self, item: BaseComponentItem):
        """Remove a component and its connected flows."""
        # Remove connected flows first
        flows_to_remove = [f for f in self._flows if f.is_connected_to(item)]
        for flow in flows_to_remove:
            self.remove_flow(flow)
        
        # Remove the component
        if item in self._components:
            self._components.remove(item)
        self.removeItem(item)
        self.component_removed.emit(item)
    
    def add_flow(self, source_port: PortItem, target_port: PortItem) -> Optional[FlowItem]:
        """
        Create a flow connection between two ports.
        
        Args:
            source_port: Output port (source)
            target_port: Input port (destination)
            
        Returns:
            Created FlowItem, or None if connection invalid
        """
        # Import here to avoid circular imports
        from ..items.flow_item import FlowItem
        
        # Validate connection
        if not self._can_connect(source_port, target_port):
            return None
        
        flow = FlowItem(source_port, target_port)
        self.addItem(flow)
        self._flows.append(flow)
        self.flow_added.emit(flow)
        return flow
    
    def remove_flow(self, flow: FlowItem):
        """Remove a flow connection."""
        flow.disconnect()
        if flow in self._flows:
            self._flows.remove(flow)
        self.removeItem(flow)
        self.flow_removed.emit(flow)
    
    def _can_connect(self, source: PortItem, target: PortItem) -> bool:
        """Check if two ports can be connected."""
        from ..items.port_item import PortItem, PortDirection
        
        # Must be different ports
        if source is target:
            return False
        
        # Must be on different components
        if source.parent_component is target.parent_component:
            return False
        
        # Source must be output, target must be input
        if source.direction != PortDirection.OUTPUT:
            return False
        if target.direction != PortDirection.INPUT:
            return False
        
        # Neither port should already be connected
        if source.is_connected or target.is_connected:
            return False
        
        return True
    
    # -------------------------------------------------------------------------
    # Interactive Connection Drawing
    # -------------------------------------------------------------------------
    
    def start_connection(self, port: PortItem):
        """
        Begin drawing a connection from a port.
        
        Called by PortItem when user starts dragging from it.
        """
        from ..items.port_item import PortDirection
        
        # Only start from output ports
        if port.direction != PortDirection.OUTPUT:
            return
        
        if port.is_connected:
            return
        
        self._is_connecting = True
        self._connection_source = port
        
        # Create temporary line for visual feedback
        self._temp_line = QGraphicsLineItem()
        self._temp_line.setPen(QPen(QColor(100, 180, 255), 2, Qt.PenStyle.DashLine))
        self._temp_line.setZValue(1000)
        self.addItem(self._temp_line)
        
        # Position at source port
        start_pos = port.scenePos()
        self._temp_line.setLine(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
    
    def update_connection_line(self, end_pos: QPointF):
        """Update temporary connection line endpoint during drag."""
        if self._temp_line and self._connection_source:
            start_pos = self._connection_source.scenePos()
            self._temp_line.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
    
    def complete_connection(self, target_port: PortItem) -> bool:
        """
        Complete a connection to a target port.
        
        Returns:
            True if connection was created successfully
        """
        success = False
        
        if self._connection_source and target_port:
            if self._can_connect(self._connection_source, target_port):
                self.add_flow(self._connection_source, target_port)
                success = True
        
        self._cancel_connection()
        return success
    
    def _cancel_connection(self):
        """Cancel current connection drawing."""
        self._is_connecting = False
        self._connection_source = None
        
        if self._temp_line:
            self.removeItem(self._temp_line)
            self._temp_line = None
    
    @property
    def is_connecting(self) -> bool:
        """True if currently drawing a connection."""
        return self._is_connecting
    
    # -------------------------------------------------------------------------
    # Drag and Drop Handling
    # -------------------------------------------------------------------------
    
    def dragEnterEvent(self, event):
        """Accept component drag-drop."""
        if event.mimeData().hasFormat(COMPONENT_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)
    
    def dragMoveEvent(self, event):
        """Track drag position."""
        if event.mimeData().hasFormat(COMPONENT_MIME_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)
    
    def dropEvent(self, event):
        """Create component on drop."""
        if event.mimeData().hasFormat(COMPONENT_MIME_TYPE):
            # Decode component type from MIME data
            data = event.mimeData().data(COMPONENT_MIME_TYPE)
            type_name = bytes(data).decode('utf-8')
            
            # Create component at drop position
            pos = event.scenePos()
            self.create_component(type_name, pos)
            
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
    
    # -------------------------------------------------------------------------
    # Mouse Events for Connection Drawing
    # -------------------------------------------------------------------------
    
    def mouseMoveEvent(self, event):
        """Update connection line during drag."""
        if self._is_connecting:
            self.update_connection_line(event.scenePos())
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Cancel connection if released in empty space."""
        if self._is_connecting and event.button() == Qt.MouseButton.LeftButton:
            # Check if released on a valid port
            items = self.items(event.scenePos())
            from ..items.port_item import PortItem
            
            target_port = None
            for item in items:
                if isinstance(item, PortItem):
                    target_port = item
                    break
            
            if target_port:
                self.complete_connection(target_port)
            else:
                self._cancel_connection()
        
        super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_Escape:
            if self._is_connecting:
                self._cancel_connection()
            else:
                self.clearSelection()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        else:
            super().keyPressEvent(event)
    
    # -------------------------------------------------------------------------
    # Selection Management
    # -------------------------------------------------------------------------
    
    def _on_selection_changed(self):
        """Emit selection changed signal with selected items."""
        selected = self.selectedItems()
        self.selection_changed_items.emit(selected)
    
    def delete_selected(self):
        """Delete all selected items."""
        from ..items.base_item import BaseComponentItem
        from ..items.flow_item import FlowItem
        
        selected = self.selectedItems()
        
        # Delete flows first, then components
        for item in selected:
            if isinstance(item, FlowItem):
                self.remove_flow(item)
        
        for item in selected:
            if isinstance(item, BaseComponentItem):
                self.remove_component(item)
    
    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    
    @property
    def components(self) -> list[BaseComponentItem]:
        """List of all component items in the scene."""
        return self._components.copy()
    
    @property
    def flows(self) -> list[FlowItem]:
        """List of all flow items in the scene."""
        return self._flows.copy()
    
    def clear_all(self):
        """Remove all items from the scene."""
        for flow in self._flows.copy():
            self.remove_flow(flow)
        for comp in self._components.copy():
            self.remove_component(comp)
        self.clear()
