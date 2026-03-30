"""
Undo/Redo commands for the flow scene.

Implements QUndoCommand subclasses for all undoable operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List, Dict, Any
from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import QPointF

if TYPE_CHECKING:
    from .flow_scene import FlowScene
    from ..items.base_item import BaseComponentItem
    from ..items.flow_item import FlowItem
    from ..items.port_item import PortItem


class AddComponentCommand(QUndoCommand):
    """Command to add a component to the scene."""
    
    def __init__(self, scene: FlowScene, type_name: str, pos: QPointF, name: str = ""):
        super().__init__(f"Add {type_name}")
        self._scene = scene
        self._type_name = type_name
        self._pos = pos
        self._name = name
        self._item: Optional[BaseComponentItem] = None
    
    def redo(self):
        if self._item is None:
            self._item = self._scene._create_component_internal(
                self._type_name, self._pos, self._name
            )
            if self._item and not self._name:
                self._name = self._item.name  # Save generated name
        else:
            self._scene._restore_component(self._item)
    
    def undo(self):
        if self._item:
            self._scene._remove_component_internal(self._item)


class RemoveComponentCommand(QUndoCommand):
    """Command to remove a component from the scene."""
    
    def __init__(self, scene: FlowScene, item: BaseComponentItem):
        super().__init__(f"Remove {item.component_type}")
        self._scene = scene
        self._item = item
        self._pos = item.pos()
        
        # Store connected flows info for restoration
        self._connected_flows_data: List[Dict[str, Any]] = []
    
    def redo(self):
        # Store flow connection data before removal
        self._connected_flows_data.clear()
        from ..items.flow_item import FlowItem
        for flow in list(self._scene._flows):
            if flow.is_connected_to(self._item):
                self._connected_flows_data.append({
                    'flow': flow,
                    'source_port': flow.source_port,
                    'target_port': flow.target_port
                })
        
        self._scene._remove_component_internal(self._item)
    
    def undo(self):
        self._scene._restore_component(self._item)
        self._item.setPos(self._pos)
        
        # Restore flows
        for flow_data in self._connected_flows_data:
            self._scene._restore_flow(flow_data['flow'])


class MoveComponentCommand(QUndoCommand):
    """Command for component movement."""
    
    def __init__(self, item: BaseComponentItem, old_pos: QPointF, new_pos: QPointF):
        super().__init__(f"Move {item.component_type}")
        self._item = item
        self._old_pos = old_pos
        self._new_pos = new_pos
    
    def redo(self):
        self._item.setPos(self._new_pos)
    
    def undo(self):
        self._item.setPos(self._old_pos)
    
    def mergeWith(self, other: QUndoCommand) -> bool:
        if not isinstance(other, MoveComponentCommand):
            return False
        if other._item is not self._item:
            return False
        self._new_pos = other._new_pos
        return True
    
    def id(self) -> int:
        return 1001  # Unique ID for merging


class AddFlowCommand(QUndoCommand):
    """Command to add a flow connection."""
    
    def __init__(self, scene: FlowScene, source_port: PortItem, target_port: PortItem):
        super().__init__("Add Flow")
        self._scene = scene
        self._source_port = source_port
        self._target_port = target_port
        self._flow: Optional[FlowItem] = None
    
    def redo(self):
        if self._flow is None:
            self._flow = self._scene._create_flow_internal(self._source_port, self._target_port)
        else:
            self._scene._restore_flow(self._flow)
    
    def undo(self):
        if self._flow:
            self._scene._remove_flow_internal(self._flow)


class RemoveFlowCommand(QUndoCommand):
    """Command to remove a flow connection."""
    
    def __init__(self, scene: FlowScene, flow: FlowItem):
        super().__init__("Remove Flow")
        self._scene = scene
        self._flow = flow
        self._source_port = flow.source_port
        self._target_port = flow.target_port
    
    def redo(self):
        self._scene._remove_flow_internal(self._flow)
    
    def undo(self):
        self._scene._restore_flow(self._flow)


class PasteCommand(QUndoCommand):
    """Command to paste components."""
    
    def __init__(self, scene: FlowScene, items_data: List[Dict[str, Any]], offset: QPointF):
        super().__init__("Paste")
        self._scene = scene
        self._items_data = items_data
        self._offset = offset
        self._created_items: List[BaseComponentItem] = []
    
    def redo(self):
        if not self._created_items:
            for data in self._items_data:
                pos = QPointF(data['x'] + self._offset.x(), data['y'] + self._offset.y())
                item = self._scene._create_component_internal(data['type'], pos, "")
                if item:
                    self._created_items.append(item)
        else:
            for item in self._created_items:
                self._scene._restore_component(item)
    
    def undo(self):
        for item in self._created_items:
            self._scene._remove_component_internal(item)
