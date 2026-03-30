"""
FlowScene - Graphics scene for flow diagram components.

Handles drag-and-drop component creation, interactive port connections,
undo/redo, copy/paste, and manages all component and flow items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Type, List, Any
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsLineItem, QGraphicsItem, QMenu, QInputDialog
from PyQt6.QtCore import Qt, QPointF, pyqtSignal, QRectF
from PyQt6.QtGui import QPen, QColor, QTransform, QUndoStack

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
        - Undo/redo support
        - Copy/paste functionality
        - Selection management with signals
        - Component and flow item tracking
    
    Signals:
        component_added(BaseComponentItem): New component added to scene
        component_removed(BaseComponentItem): Component removed from scene
        flow_added(FlowItem): New flow connection created
        flow_removed(FlowItem): Flow connection removed
        selection_changed_items(list): List of currently selected items
        snap_toggled(bool): Snap mode changed
        snap_size_changed(int): Snap grid size changed
    """
    
    component_added = pyqtSignal(object)
    component_removed = pyqtSignal(object)
    flow_added = pyqtSignal(object)
    flow_removed = pyqtSignal(object)
    selection_changed_items = pyqtSignal(list)
    snap_toggled = pyqtSignal(bool)
    snap_size_changed = pyqtSignal(int)
    
    # Snap size presets
    SNAP_SIZES = [5, 10, 20, 50, 100]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scene dimensions (large virtual canvas)
        self.setSceneRect(-5000, -5000, 10000, 10000)
        
        # Item tracking
        self._components: list[BaseComponentItem] = []
        self._flows: list[FlowItem] = []
        
        # Component counters for auto-naming (type_name -> count)
        self._component_counters: Dict[str, int] = {}
        
        # Snap to grid settings
        self.snap_enabled = True
        self.snap_grid_size = 20  # Should match GRID_SIZE_MINOR in FlowView
        
        # Undo/Redo stack
        self._undo_stack = QUndoStack(self)
        
        # Copy/paste clipboard
        self._clipboard: List[Dict[str, Any]] = []
        
        # Connection drawing state
        self._is_connecting = False
        self._connection_source: Optional[PortItem] = None
        self._temp_line: Optional[QGraphicsLineItem] = None
        
        # Component factory registry
        self._component_factories: Dict[str, Type[BaseComponentItem]] = {}
        
        # Connect selection changes
        self.selectionChanged.connect(self._on_selection_changed)
    
    @property
    def undo_stack(self) -> QUndoStack:
        """Get the undo stack."""
        return self._undo_stack
    
    def set_snap_enabled(self, enabled: bool):
        """Enable or disable snap-to-grid."""
        self.snap_enabled = enabled
        self.snap_toggled.emit(enabled)
    
    def toggle_snap(self):
        """Toggle snap-to-grid on/off."""
        self.set_snap_enabled(not self.snap_enabled)
    
    def set_snap_size(self, size: int):
        """Set snap grid size."""
        self.snap_grid_size = max(1, size)
        self.snap_size_changed.emit(self.snap_grid_size)
    
    def increase_snap_size(self):
        """Increase snap size to next preset."""
        for s in self.SNAP_SIZES:
            if s > self.snap_grid_size:
                self.set_snap_size(s)
                return
    
    def decrease_snap_size(self):
        """Decrease snap size to previous preset."""
        for s in reversed(self.SNAP_SIZES):
            if s < self.snap_grid_size:
                self.set_snap_size(s)
                return
    
    def register_component_type(self, type_name: str, factory_class: Type[BaseComponentItem]):
        """
        Register a component type for drag-and-drop creation.
        
        Args:
            type_name: String identifier (e.g., "Turbine")
            factory_class: The item class to instantiate
        """
        self._component_factories[type_name] = factory_class
        if type_name not in self._component_counters:
            self._component_counters[type_name] = 0
    
    def _generate_component_name(self, type_name: str) -> str:
        """
        Generate auto-name for a new component.
        
        Format: TypeName_001, TypeName_002, etc.
        """
        self._component_counters[type_name] = self._component_counters.get(type_name, 0) + 1
        count = self._component_counters[type_name]
        return f"{type_name}_{count:03d}"
    
    def create_component(self, type_name: str, pos: QPointF, name: str = "") -> Optional[BaseComponentItem]:
        """
        Create a component item at the specified position (with undo support).
        
        Args:
            type_name: Registered component type
            pos: Scene position
            name: Optional component name (auto-generated if empty)
            
        Returns:
            Created component item, or None if type not registered
        """
        from .undo_commands import AddComponentCommand
        cmd = AddComponentCommand(self, type_name, pos, name)
        self._undo_stack.push(cmd)
        return cmd._item
    
    def _create_component_internal(self, type_name: str, pos: QPointF, name: str = "") -> Optional[BaseComponentItem]:
        """Internal component creation without undo."""
        if type_name not in self._component_factories:
            print(f"Unknown component type: {type_name}")
            return None
        
        # Auto-generate name if not provided
        if not name:
            name = self._generate_component_name(type_name)
        
        factory = self._component_factories[type_name]
        item = factory(name=name)
        item.setPos(pos)
        self.addItem(item)
        self._components.append(item)
        self.component_added.emit(item)
        
        # Update all flows to check crossings
        self._refresh_all_flow_paths()
        
        return item
    
    def _restore_component(self, item: BaseComponentItem):
        """Restore a component to the scene (for undo)."""
        if item not in self._components:
            self.addItem(item)
            self._components.append(item)
            self.component_added.emit(item)
    
    def remove_component(self, item: BaseComponentItem):
        """Remove a component and its connected flows (with undo support)."""
        from .undo_commands import RemoveComponentCommand
        cmd = RemoveComponentCommand(self, item)
        self._undo_stack.push(cmd)
    
    def _remove_component_internal(self, item: BaseComponentItem):
        """Internal component removal without undo."""
        # Remove connected flows first
        flows_to_remove = [f for f in self._flows if f.is_connected_to(item)]
        for flow in flows_to_remove:
            self._remove_flow_internal(flow)
        
        # Remove the component
        if item in self._components:
            self._components.remove(item)
        self.removeItem(item)
        self.component_removed.emit(item)
    
    def add_flow(self, source_port: PortItem, target_port: PortItem) -> Optional[FlowItem]:
        """
        Create a flow connection between two ports (with undo support).
        
        Args:
            source_port: Output port (source)
            target_port: Input port (destination)
            
        Returns:
            Created FlowItem, or None if connection invalid
        """
        # Validate connection
        if not self._can_connect(source_port, target_port):
            return None
        
        from .undo_commands import AddFlowCommand
        cmd = AddFlowCommand(self, source_port, target_port)
        self._undo_stack.push(cmd)
        return cmd._flow
    
    def _create_flow_internal(self, source_port: PortItem, target_port: PortItem) -> Optional[FlowItem]:
        """Internal flow creation without undo."""
        from ..items.flow_item import FlowItem
        
        flow = FlowItem(source_port, target_port)
        self.addItem(flow)
        self._flows.append(flow)
        self.flow_added.emit(flow)
        
        # Refresh all flow paths for crossing detection
        self._refresh_all_flow_paths()
        
        return flow
    
    def _restore_flow(self, flow: FlowItem):
        """Restore a flow to the scene (for undo)."""
        if flow not in self._flows:
            # Reconnect ports
            flow._source_port.connected_flow = flow
            flow._target_port.connected_flow = flow
            self.addItem(flow)
            self._flows.append(flow)
            flow.update_path()
            self.flow_added.emit(flow)
            self._refresh_all_flow_paths()
    
    def remove_flow(self, flow: FlowItem):
        """Remove a flow connection (with undo support)."""
        from .undo_commands import RemoveFlowCommand
        cmd = RemoveFlowCommand(self, flow)
        self._undo_stack.push(cmd)
    
    def _remove_flow_internal(self, flow: FlowItem):
        """Internal flow removal without undo."""
        flow.disconnect()
        if flow in self._flows:
            self._flows.remove(flow)
        self.removeItem(flow)
        self.flow_removed.emit(flow)
        self._refresh_all_flow_paths()
    
    def _refresh_all_flow_paths(self):
        """Refresh all flow paths (for crossing detection)."""
        for flow in self._flows:
            flow.update_path()
    
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
        elif event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.copy_selected()
        elif event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste()
        elif event.key() == Qt.Key.Key_Z and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self._undo_stack.redo()
            else:
                self._undo_stack.undo()
        elif event.key() == Qt.Key.Key_Y and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self._undo_stack.redo()
        elif event.key() == Qt.Key.Key_G and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.toggle_snap()
        else:
            super().keyPressEvent(event)
    
    # -------------------------------------------------------------------------
    # Copy/Paste
    # -------------------------------------------------------------------------
    
    def copy_selected(self):
        """Copy selected components and their internal flows to clipboard."""
        from ..items.base_item import BaseComponentItem
        from ..items.flow_item import FlowItem
        
        self._clipboard.clear()
        self._clipboard_flows = []
        
        # Collect selected components
        selected_components = []
        for item in self.selectedItems():
            if isinstance(item, BaseComponentItem):
                selected_components.append(item)
                self._clipboard.append({
                    'type': item.component_type,
                    'x': item.pos().x(),
                    'y': item.pos().y(),
                    'name': item.name
                })
        
        # Find flows between selected components
        for flow in self._flows:
            source_comp = flow.source_component
            target_comp = flow.target_component
            
            if source_comp in selected_components and target_comp in selected_components:
                # Both ends are in selection - include this flow
                source_idx = selected_components.index(source_comp)
                target_idx = selected_components.index(target_comp)
                self._clipboard_flows.append({
                    'source_idx': source_idx,
                    'source_port': flow.source_port.name,
                    'target_idx': target_idx,
                    'target_port': flow.target_port.name
                })
    
    def paste(self):
        """Paste components and flows from clipboard."""
        if not self._clipboard:
            return
        
        from .undo_commands import PasteCommand
        offset = QPointF(20, 20)  # Offset pasted items
        
        # Get flow data (may not exist if copied before this feature)
        flows_data = getattr(self, '_clipboard_flows', [])
        
        cmd = PasteCommand(self, self._clipboard, flows_data, offset)
        self._undo_stack.push(cmd)
        
        # Select pasted items
        self.clearSelection()
        for item in cmd._created_items:
            item.setSelected(True)
    
    # -------------------------------------------------------------------------
    # Context Menu
    # -------------------------------------------------------------------------
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click (only for empty canvas)."""
        # Check if clicked on an item - let items handle their own context menus
        item_at_pos = self.itemAt(event.scenePos(), QTransform())
        
        # Skip port items and let parent handle, but otherwise let items handle menus
        if item_at_pos is not None:
            from ..items.port_item import PortItem
            from ..items.flow_item import FlowItem, WaypointHandle
            from ..items.base_item import BaseComponentItem, ResizeHandle
            
            # Let components, flows, and waypoints handle their own menus
            if isinstance(item_at_pos, (BaseComponentItem, FlowItem, WaypointHandle)):
                super().contextMenuEvent(event)
                return
            # For ports and resize handles, check parent
            if isinstance(item_at_pos, (PortItem, ResizeHandle)):
                super().contextMenuEvent(event)
                return
        
        # Canvas (empty space) context menu
        menu = QMenu()
        
        # Edit actions
        undo_action = menu.addAction("Undo")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.setEnabled(self._undo_stack.canUndo())
        undo_action.triggered.connect(self._undo_stack.undo)
        
        redo_action = menu.addAction("Redo")
        redo_action.setShortcut("Ctrl+Y")
        redo_action.setEnabled(self._undo_stack.canRedo())
        redo_action.triggered.connect(self._undo_stack.redo)
        
        menu.addSeparator()
        
        copy_action = menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.setEnabled(len(self.selectedItems()) > 0)
        copy_action.triggered.connect(self.copy_selected)
        
        paste_action = menu.addAction("Paste")
        paste_action.setShortcut("Ctrl+V")
        paste_action.setEnabled(len(self._clipboard) > 0)
        paste_action.triggered.connect(self.paste)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.setShortcut("Del")
        delete_action.setEnabled(len(self.selectedItems()) > 0)
        delete_action.triggered.connect(self.delete_selected)
        
        menu.addSeparator()
        
        # Snap submenu
        snap_menu = menu.addMenu("Snap to Grid")
        
        snap_toggle = snap_menu.addAction("Enabled")
        snap_toggle.setCheckable(True)
        snap_toggle.setChecked(self.snap_enabled)
        snap_toggle.setShortcut("Ctrl+G")
        snap_toggle.triggered.connect(self.toggle_snap)
        
        snap_menu.addSeparator()
        
        # Grid size submenu
        for size in self.SNAP_SIZES:
            size_action = snap_menu.addAction(f"Grid: {size}px")
            size_action.setCheckable(True)
            size_action.setChecked(self.snap_grid_size == size)
            size_action.triggered.connect(lambda checked, s=size: self.set_snap_size(s))
        
        snap_menu.addSeparator()
        
        custom_size = snap_menu.addAction("Custom Size...")
        custom_size.triggered.connect(self._set_custom_snap_size)
        
        menu.addSeparator()
        
        select_all = menu.addAction("Select All")
        select_all.setShortcut("Ctrl+A")
        select_all.triggered.connect(lambda: [item.setSelected(True) for item in self.items()])
        
        menu.exec(event.screenPos())
    
    def _set_custom_snap_size(self):
        """Show dialog to set custom snap grid size."""
        size, ok = QInputDialog.getInt(
            None, "Custom Snap Size",
            "Enter grid size (pixels):",
            self.snap_grid_size, 1, 200
        )
        if ok:
            self.set_snap_size(size)
    
    # -------------------------------------------------------------------------
    # Selection Management
    # -------------------------------------------------------------------------
    
    def _on_selection_changed(self):
        """Emit selection changed signal with selected items."""
        selected = self.selectedItems()
        self.selection_changed_items.emit(selected)
    
    def delete_selected(self):
        """Delete all selected items (with undo support as a group)."""
        from ..items.base_item import BaseComponentItem
        from ..items.flow_item import FlowItem
        
        selected = self.selectedItems()
        if not selected:
            return
        
        # Group deletions in a macro
        self._undo_stack.beginMacro("Delete Selection")
        
        # Delete flows first, then components
        for item in selected:
            if isinstance(item, FlowItem) and item in self._flows:
                self.remove_flow(item)
        
        for item in selected:
            if isinstance(item, BaseComponentItem) and item in self._components:
                self.remove_component(item)
        
        self._undo_stack.endMacro()
    
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
