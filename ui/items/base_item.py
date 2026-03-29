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
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath, QTransform

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
        - Rotate/Flip/Scale transformations
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
    
    # Transform defaults
    DEFAULT_SCALE = 1.0
    MIN_SCALE = 0.5
    MAX_SCALE = 2.0
    SCALE_STEP = 0.1
    
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
        
        # Transform state
        self._rotation_angle = 0  # degrees (0, 90, 180, 270)
        self._flip_h = False       # horizontal flip
        self._flip_v = False       # vertical flip
        self._scale_factor = self.DEFAULT_SCALE
        
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
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            # Snap to grid if enabled
            new_pos = value
            scene = self.scene()
            if scene and hasattr(scene, 'snap_enabled') and scene.snap_enabled:
                grid_size = getattr(scene, 'snap_grid_size', 20)
                new_pos = QPointF(
                    round(new_pos.x() / grid_size) * grid_size,
                    round(new_pos.y() / grid_size) * grid_size
                )
            return new_pos
        
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
        
        # Transform submenu
        transform_menu = menu.addMenu("Transform")
        
        rotate_cw = transform_menu.addAction("Rotate 90° CW (R)")
        rotate_cw.triggered.connect(self.rotate_cw)
        
        rotate_ccw = transform_menu.addAction("Rotate 90° CCW (Shift+R)")
        rotate_ccw.triggered.connect(self.rotate_ccw)
        
        transform_menu.addSeparator()
        
        flip_h = transform_menu.addAction("Flip Horizontal (H)")
        flip_h.triggered.connect(self.flip_horizontal)
        flip_h.setCheckable(True)
        flip_h.setChecked(self._flip_h)
        
        flip_v = transform_menu.addAction("Flip Vertical (V)")
        flip_v.triggered.connect(self.flip_vertical)
        flip_v.setCheckable(True)
        flip_v.setChecked(self._flip_v)
        
        transform_menu.addSeparator()
        
        scale_up = transform_menu.addAction("Scale Up (+)")
        scale_up.triggered.connect(self.scale_up)
        scale_up.setEnabled(self._scale_factor < self.MAX_SCALE)
        
        scale_down = transform_menu.addAction("Scale Down (-)")
        scale_down.triggered.connect(self.scale_down)
        scale_down.setEnabled(self._scale_factor > self.MIN_SCALE)
        
        reset_transform = transform_menu.addAction("Reset Transform")
        reset_transform.triggered.connect(self.reset_transform)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(self._on_delete)
        
        menu.addSeparator()
        
        props_action = menu.addAction("Properties...")
        props_action.triggered.connect(self._on_properties)
        
        menu.exec(event.screenPos())
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for transforms."""
        if event.key() == Qt.Key.Key_R:
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                self.rotate_ccw()
            else:
                self.rotate_cw()
            event.accept()
        elif event.key() == Qt.Key.Key_H:
            self.flip_horizontal()
            event.accept()
        elif event.key() == Qt.Key.Key_V:
            self.flip_vertical()
            event.accept()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.scale_up()
            event.accept()
        elif event.key() == Qt.Key.Key_Minus:
            self.scale_down()
            event.accept()
        elif event.key() == Qt.Key.Key_Delete:
            self._on_delete()
            event.accept()
        else:
            super().keyPressEvent(event)
    
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
    # Transform Methods
    # -------------------------------------------------------------------------
    
    def _apply_transform(self):
        """Apply current rotation, flip, and scale to the item."""
        transform = QTransform()
        
        # Apply scale
        transform.scale(self._scale_factor, self._scale_factor)
        
        # Apply flip
        flip_x = -1 if self._flip_h else 1
        flip_y = -1 if self._flip_v else 1
        transform.scale(flip_x, flip_y)
        
        # Apply rotation
        transform.rotate(self._rotation_angle)
        
        self.setTransform(transform)
        self._update_connected_flows()
        self.update()
    
    def rotate_cw(self):
        """Rotate 90 degrees clockwise."""
        self._rotation_angle = (self._rotation_angle + 90) % 360
        self._apply_transform()
    
    def rotate_ccw(self):
        """Rotate 90 degrees counter-clockwise."""
        self._rotation_angle = (self._rotation_angle - 90) % 360
        self._apply_transform()
    
    def flip_horizontal(self):
        """Toggle horizontal flip."""
        self._flip_h = not self._flip_h
        self._apply_transform()
    
    def flip_vertical(self):
        """Toggle vertical flip."""
        self._flip_v = not self._flip_v
        self._apply_transform()
    
    def scale_up(self):
        """Increase scale by one step."""
        if self._scale_factor < self.MAX_SCALE:
            self._scale_factor = min(self._scale_factor + self.SCALE_STEP, self.MAX_SCALE)
            self._apply_transform()
    
    def scale_down(self):
        """Decrease scale by one step."""
        if self._scale_factor > self.MIN_SCALE:
            self._scale_factor = max(self._scale_factor - self.SCALE_STEP, self.MIN_SCALE)
            self._apply_transform()
    
    def reset_transform(self):
        """Reset all transforms to defaults."""
        self._rotation_angle = 0
        self._flip_h = False
        self._flip_v = False
        self._scale_factor = self.DEFAULT_SCALE
        self._apply_transform()
    
    @property
    def rotation_angle(self) -> int:
        """Current rotation in degrees (0, 90, 180, 270)."""
        return self._rotation_angle
    
    @property
    def is_flipped_h(self) -> bool:
        """Whether item is flipped horizontally."""
        return self._flip_h
    
    @property
    def is_flipped_v(self) -> bool:
        """Whether item is flipped vertically."""
        return self._flip_v
    
    @property
    def scale_factor(self) -> float:
        """Current scale factor."""
        return self._scale_factor
    
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
