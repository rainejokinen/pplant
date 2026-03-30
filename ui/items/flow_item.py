"""
FlowItem - Orthogonal line connection between ports.

Represents a flow connection (pipe) between two components with
right-angle routing, support for manual waypoints, and line jump-overs
at crossings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from PyQt6.QtWidgets import (
    QGraphicsPathItem, QGraphicsItem, QGraphicsEllipseItem,
    QStyleOptionGraphicsItem, QWidget, QMenu
)
from PyQt6.QtCore import Qt, QPointF, QRectF, QLineF
from PyQt6.QtGui import QPainter, QPen, QColor, QPainterPath, QPolygonF

if TYPE_CHECKING:
    from .port_item import PortItem
    from .base_item import BaseComponentItem


class WaypointHandle(QGraphicsEllipseItem):
    """Small handle for adjusting/deleting flow waypoints."""
    
    RADIUS = 5
    
    def __init__(self, flow_item: FlowItem, index: int, parent=None):
        rect = QRectF(-self.RADIUS, -self.RADIUS, 2 * self.RADIUS, 2 * self.RADIUS)
        super().__init__(rect, parent)
        
        self._flow_item = flow_item
        self._index = index
        
        self.setBrush(QColor(100, 150, 255))
        self.setPen(QPen(QColor(50, 100, 200), 1))
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setZValue(100)
        self.setVisible(False)  # Only show when flow is selected
        self.setAcceptHoverEvents(True)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            self._flow_item.update_waypoint(self._index, self.scenePos())
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Right-click to delete waypoint."""
        menu = QMenu()
        delete_action = menu.addAction("Delete Waypoint")
        delete_action.triggered.connect(lambda: self._flow_item.remove_waypoint(self._index))
        menu.exec(event.screenPos())
    
    def mouseDoubleClickEvent(self, event):
        """Double-click to delete waypoint."""
        self._flow_item.remove_waypoint(self._index)
        event.accept()


class FlowItem(QGraphicsPathItem):
    """
    Orthogonal flow connection between two ports.
    
    Draws right-angle lines from source (output) port to target (input) port.
    Supports manual waypoints added by double-clicking.
    
    Features:
        - Orthogonal (right-angle) routing
        - Auto-updates path when connected components move
        - Manual waypoints (double-click to add, right-click/double-click to delete)
        - Jump-over gaps at line crossings
        - Direction arrow at midpoint
        - Color coding by fluid type/state
        - Selectable for deletion
    """
    
    # Appearance
    LINE_WIDTH = 2
    LINE_WIDTH_SELECTED = 3
    COLOR_DEFAULT = QColor(0, 0, 255)         # Blue (VWO style)
    COLOR_STEAM = QColor(255, 0, 0)           # Red
    COLOR_WATER = QColor(0, 0, 255)           # Blue
    COLOR_SELECTED = QColor(255, 200, 50)     # Gold
    LABEL_COLOR = QColor(200, 200, 200)
    
    # Arrow size
    ARROW_SIZE = 8
    
    # Jump-over size (arc radius at crossing)
    JUMP_RADIUS = 6
    
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
        self._label = ""  # Custom label text
        self._show_label = False
        
        # Manual waypoints (scene coordinates)
        self._waypoints: List[QPointF] = []
        self._waypoint_handles: List[WaypointHandle] = []
        
        # Cached segments for crossing detection
        self._segments: List[QLineF] = []
        
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
        
        # Remove waypoint handles
        for handle in self._waypoint_handles:
            if handle.scene():
                handle.scene().removeItem(handle)
        self._waypoint_handles.clear()
    
    def _update_pen(self):
        """Update pen based on selection and fluid type."""
        if self.isSelected():
            color = self.COLOR_SELECTED
            width = self.LINE_WIDTH_SELECTED
        else:
            color = self._get_fluid_color()
            width = self.LINE_WIDTH
        
        self.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.SquareCap, Qt.PenJoinStyle.MiterJoin))
    
    def _get_fluid_color(self) -> QColor:
        """Get color based on fluid type."""
        if self._fluid_type == "steam":
            return self.COLOR_STEAM
        elif self._fluid_type == "water":
            return self.COLOR_WATER
        return self.COLOR_DEFAULT
    
    def get_segments(self) -> List[QLineF]:
        """Return line segments for crossing detection."""
        return self._segments.copy()
    
    def update_path(self):
        """Recalculate orthogonal path between ports."""
        if not self._source_port or not self._target_port:
            return
        
        start = self._source_port.scenePos()
        end = self._target_port.scenePos()
        
        # Build list of points
        if self._waypoints:
            points = self._create_waypoint_points(start, end)
        else:
            points = self._create_auto_orthogonal_points(start, end)
        
        # Store segments for crossing detection
        self._segments = []
        for i in range(len(points) - 1):
            self._segments.append(QLineF(points[i], points[i + 1]))
        
        # Build path with jump-overs at crossings
        path = self._build_path_with_jumps(points)
        self.setPath(path)
        self._update_waypoint_handles()
    
    def _create_auto_orthogonal_points(self, start: QPointF, end: QPointF) -> List[QPointF]:
        """
        Create automatic orthogonal routing points.
        
        Forces lines to exit ports straight outward (perpendicular to component edge),
        then routes orthogonally to destination.
        """
        points = [start]
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        if abs(dx) < 1 and abs(dy) < 1:
            points.append(end)
            return points
        
        # Minimum distance to go straight out of the port before turning
        MIN_EXTEND = 30
        
        # Get actual port exit directions
        source_dir = self._source_port.get_exit_direction()
        target_dir = self._target_port.get_exit_direction()
        
        # Calculate the extension points based on port directions
        source_extend = QPointF(
            start.x() + source_dir.x() * MIN_EXTEND,
            start.y() + source_dir.y() * MIN_EXTEND
        )
        target_extend = QPointF(
            end.x() + target_dir.x() * MIN_EXTEND,
            end.y() + target_dir.y() * MIN_EXTEND
        )
        
        # Route based on source and target directions
        src_horizontal = abs(source_dir.x()) > 0.5
        tgt_horizontal = abs(target_dir.x()) > 0.5
        
        if src_horizontal and tgt_horizontal:
            # Both horizontal ports (most common case)
            return self._route_horizontal_to_horizontal(start, end, source_extend, target_extend, MIN_EXTEND)
        elif not src_horizontal and not tgt_horizontal:
            # Both vertical ports
            return self._route_vertical_to_vertical(start, end, source_extend, target_extend, MIN_EXTEND)
        else:
            # Mixed: one horizontal, one vertical
            return self._route_mixed_directions(start, end, source_extend, target_extend, src_horizontal)
    
    def _route_horizontal_to_horizontal(self, start: QPointF, end: QPointF, 
                                         source_extend: QPointF, target_extend: QPointF,
                                         min_extend: float) -> List[QPointF]:
        """Route from horizontal port to horizontal port."""
        points = [start]
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        # Determine if we need complex routing
        source_going_right = source_extend.x() > start.x()
        target_coming_from_left = target_extend.x() < end.x()
        
        if source_going_right and target_coming_from_left:
            if dx >= min_extend * 2:
                # Direct routing with single bend
                mid_x = (start.x() + end.x()) / 2
                mid_x = max(mid_x, source_extend.x())
                mid_x = min(mid_x, target_extend.x())
                points.append(QPointF(mid_x, start.y()))
                points.append(QPointF(mid_x, end.y()))
            else:
                # Need to route around
                mid_y = (start.y() + end.y()) / 2
                if abs(dy) < min_extend:
                    mid_y = start.y() + (60 if dy >= 0 else -60)
                points.append(source_extend)
                points.append(QPointF(source_extend.x(), mid_y))
                points.append(QPointF(target_extend.x(), mid_y))
                points.append(target_extend)
        else:
            # Complex case: ports facing away or towards each other
            mid_y = (start.y() + end.y()) / 2
            if abs(dy) < min_extend:
                mid_y = start.y() + (60 if dy >= 0 else -60)
            points.append(source_extend)
            points.append(QPointF(source_extend.x(), mid_y))
            points.append(QPointF(target_extend.x(), mid_y))
            points.append(target_extend)
        
        points.append(end)
        return points
    
    def _route_vertical_to_vertical(self, start: QPointF, end: QPointF,
                                     source_extend: QPointF, target_extend: QPointF,
                                     min_extend: float) -> List[QPointF]:
        """Route from vertical port to vertical port."""
        points = [start]
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        
        source_going_down = source_extend.y() > start.y()
        target_coming_from_top = target_extend.y() < end.y()
        
        if source_going_down and target_coming_from_top:
            if dy >= min_extend * 2:
                # Direct vertical routing
                mid_y = (start.y() + end.y()) / 2
                mid_y = max(mid_y, source_extend.y())
                mid_y = min(mid_y, target_extend.y())
                points.append(QPointF(start.x(), mid_y))
                points.append(QPointF(end.x(), mid_y))
            else:
                # Need to route around
                mid_x = (start.x() + end.x()) / 2
                if abs(dx) < min_extend:
                    mid_x = start.x() + (60 if dx >= 0 else -60)
                points.append(source_extend)
                points.append(QPointF(mid_x, source_extend.y()))
                points.append(QPointF(mid_x, target_extend.y()))
                points.append(target_extend)
        else:
            # Complex case
            mid_x = (start.x() + end.x()) / 2
            if abs(dx) < min_extend:
                mid_x = start.x() + (60 if dx >= 0 else -60)
            points.append(source_extend)
            points.append(QPointF(mid_x, source_extend.y()))
            points.append(QPointF(mid_x, target_extend.y()))
            points.append(target_extend)
        
        points.append(end)
        return points
    
    def _route_mixed_directions(self, start: QPointF, end: QPointF,
                                 source_extend: QPointF, target_extend: QPointF,
                                 src_horizontal: bool) -> List[QPointF]:
        """Route from horizontal port to vertical port or vice versa."""
        points = [start]
        
        if src_horizontal:
            # Source is horizontal, target is vertical
            # Go out horizontally from source, then connect to target's vertical extension
            points.append(source_extend)
            # Route to align with target
            points.append(QPointF(target_extend.x(), source_extend.y()))
            points.append(target_extend)
        else:
            # Source is vertical, target is horizontal
            # Go out vertically from source, then connect to target's horizontal extension
            points.append(source_extend)
            # Route to align with target
            points.append(QPointF(source_extend.x(), target_extend.y()))
            points.append(target_extend)
        
        points.append(end)
        return points
    
    def _create_waypoint_points(self, start: QPointF, end: QPointF) -> List[QPointF]:
        """Create path points through manual waypoints with orthogonal segments."""
        all_points = [start]
        
        points = [start] + self._waypoints + [end]
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            
            # Make each segment orthogonal (horizontal then vertical)
            intermediate = QPointF(p2.x(), p1.y())
            if intermediate != p1:
                all_points.append(intermediate)
            if p2 != intermediate:
                all_points.append(p2)
        
        return all_points
    
    def _build_path_with_jumps(self, points: List[QPointF]) -> QPainterPath:
        """Build path with jump-over arcs where this flow crosses others."""
        path = QPainterPath()
        if not points:
            return path
        
        path.moveTo(points[0])
        
        # Get all other flows in scene
        scene = self.scene()
        other_segments: List[QLineF] = []
        if scene:
            from .flow_item import FlowItem
            for item in scene.items():
                if isinstance(item, FlowItem) and item is not self:
                    other_segments.extend(item.get_segments())
        
        for i in range(len(points) - 1):
            segment = QLineF(points[i], points[i + 1])
            
            # Find all crossings with other flows on this segment
            crossings = []
            for other_seg in other_segments:
                intersection_type, intersection_point = segment.intersects(other_seg)
                if intersection_type == QLineF.IntersectionType.BoundedIntersection:
                    # Calculate distance from segment start
                    dist = QLineF(points[i], intersection_point).length()
                    crossings.append((dist, intersection_point))
            
            # Sort crossings by distance
            crossings.sort(key=lambda x: x[0])
            
            # Draw segment with jumps
            current_pos = points[i]
            for dist, cross_pt in crossings:
                # Is this segment horizontal or vertical?
                is_horizontal = abs(segment.dy()) < 0.1
                
                # Draw line to just before crossing
                if is_horizontal:
                    before_pt = QPointF(cross_pt.x() - self.JUMP_RADIUS, cross_pt.y())
                    after_pt = QPointF(cross_pt.x() + self.JUMP_RADIUS, cross_pt.y())
                else:
                    before_pt = QPointF(cross_pt.x(), cross_pt.y() - self.JUMP_RADIUS)
                    after_pt = QPointF(cross_pt.x(), cross_pt.y() + self.JUMP_RADIUS)
                
                # Only draw jump if we haven't passed it
                if QLineF(current_pos, before_pt).length() > 0.5:
                    path.lineTo(before_pt)
                
                # Draw arc (jump over) - simplified as a gap
                # We use arcTo for a semi-circle jump
                if is_horizontal:
                    arc_rect = QRectF(
                        cross_pt.x() - self.JUMP_RADIUS,
                        cross_pt.y() - self.JUMP_RADIUS,
                        2 * self.JUMP_RADIUS,
                        2 * self.JUMP_RADIUS
                    )
                    # Arc from 180° to 0° (top semi-circle)
                    path.arcTo(arc_rect, 180, -180)
                else:
                    arc_rect = QRectF(
                        cross_pt.x() - self.JUMP_RADIUS,
                        cross_pt.y() - self.JUMP_RADIUS,
                        2 * self.JUMP_RADIUS,
                        2 * self.JUMP_RADIUS
                    )
                    # Arc from 90° to 270° (left semi-circle)
                    path.arcTo(arc_rect, 90, -180)
                
                current_pos = after_pt
            
            # Finish segment
            path.lineTo(points[i + 1])
        
        return path
    
    def add_waypoint(self, scene_pos: QPointF):
        """Add a manual waypoint at the given scene position."""
        self._waypoints.append(scene_pos)
        self.update_path()
    
    def update_waypoint(self, index: int, new_pos: QPointF):
        """Update a waypoint position."""
        if 0 <= index < len(self._waypoints):
            self._waypoints[index] = new_pos
            self.update_path()
    
    def remove_waypoint(self, index: int):
        """Remove a waypoint."""
        if 0 <= index < len(self._waypoints):
            self._waypoints.pop(index)
            self.update_path()
    
    def _update_waypoint_handles(self):
        """Update or create waypoint handles."""
        scene = self.scene()
        if not scene:
            return
        
        # Remove extra handles
        while len(self._waypoint_handles) > len(self._waypoints):
            handle = self._waypoint_handles.pop()
            scene.removeItem(handle)
        
        # Add missing handles
        while len(self._waypoint_handles) < len(self._waypoints):
            idx = len(self._waypoint_handles)
            handle = WaypointHandle(self, idx)
            scene.addItem(handle)
            self._waypoint_handles.append(handle)
        
        # Update positions and visibility
        for i, (handle, wp) in enumerate(zip(self._waypoint_handles, self._waypoints)):
            handle._index = i
            handle.setPos(wp)
            handle.setVisible(self.isSelected())
    
    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None):
        """Paint the flow line and direction arrow."""
        self._update_pen()
        super().paint(painter, option, widget)
        self._draw_arrow(painter)
        self._draw_label(painter)
    
    def _draw_label(self, painter: QPainter):
        """Draw flow label at path midpoint."""
        if not self._show_label or not self._label:
            return
        
        from PyQt6.QtGui import QFont, QFontMetrics
        
        path = self.path()
        if path.isEmpty():
            return
        
        # Position at 50% along path
        point = path.pointAtPercent(0.5)
        
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        painter.setPen(self.LABEL_COLOR)
        
        fm = QFontMetrics(font)
        text_width = fm.horizontalAdvance(self._label)
        
        # Draw label offset above the line
        x = int(point.x() - text_width / 2)
        y = int(point.y() - 10)
        
        painter.drawText(x, y, self._label)
    
    def _draw_arrow(self, painter: QPainter):
        """Draw flow direction arrow at path midpoint."""
        path = self.path()
        if path.isEmpty():
            return
        
        t = 0.5
        point = path.pointAtPercent(t)
        angle = path.angleAtPercent(t)
        
        arrow = QPolygonF()
        arrow.append(QPointF(0, 0))
        arrow.append(QPointF(-self.ARROW_SIZE, -self.ARROW_SIZE / 2))
        arrow.append(QPointF(-self.ARROW_SIZE, self.ARROW_SIZE / 2))
        
        painter.save()
        painter.translate(point)
        painter.rotate(-angle)
        
        color = self.COLOR_SELECTED if self.isSelected() else self._get_fluid_color()
        painter.setBrush(color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(arrow)
        painter.restore()
    
    def shape(self) -> QPainterPath:
        """Return shape for hit testing (wider than visual)."""
        from PyQt6.QtGui import QPainterPathStroker
        ps = QPainterPathStroker()
        ps.setWidth(12)
        return ps.createStroke(self.path())
    
    def mouseDoubleClickEvent(self, event):
        """Add waypoint on double-click."""
        if self.isSelected():
            self.add_waypoint(event.scenePos())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
    
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Handle selection change."""
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            self._update_pen()
            for handle in self._waypoint_handles:
                handle.setVisible(value)
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Show context menu for flow line."""
        from PyQt6.QtWidgets import QInputDialog
        
        menu = QMenu()
        
        # Waypoint actions
        add_waypoint = menu.addAction("Add Waypoint Here")
        add_waypoint.triggered.connect(lambda: self.add_waypoint(event.scenePos()))
        
        if self._waypoints:
            clear_waypoints = menu.addAction("Clear All Waypoints")
            clear_waypoints.triggered.connect(self._clear_all_waypoints)
        
        menu.addSeparator()
        
        # Label options
        label_menu = menu.addMenu("Label")
        
        show_label = label_menu.addAction("Show Label")
        show_label.setCheckable(True)
        show_label.setChecked(self._show_label)
        show_label.triggered.connect(self._toggle_label)
        
        set_label = label_menu.addAction("Set Label Text...")
        set_label.triggered.connect(self._prompt_set_label)
        
        menu.addSeparator()
        
        # Fluid type submenu
        fluid_menu = menu.addMenu("Fluid Type")
        
        fluid_default = fluid_menu.addAction("Default (Blue)")
        fluid_default.setCheckable(True)
        fluid_default.setChecked(self._fluid_type == "default")
        fluid_default.triggered.connect(lambda: self._set_fluid_type("default"))
        
        fluid_water = fluid_menu.addAction("Water (Blue)")
        fluid_water.setCheckable(True)
        fluid_water.setChecked(self._fluid_type == "water")
        fluid_water.triggered.connect(lambda: self._set_fluid_type("water"))
        
        fluid_steam = fluid_menu.addAction("Steam (Red)")
        fluid_steam.setCheckable(True)
        fluid_steam.setChecked(self._fluid_type == "steam")
        fluid_steam.triggered.connect(lambda: self._set_fluid_type("steam"))
        
        menu.addSeparator()
        
        # Delete action
        delete_action = menu.addAction("Delete Flow")
        delete_action.triggered.connect(self._on_delete)
        
        menu.exec(event.screenPos())
    
    def _toggle_label(self):
        """Toggle label visibility."""
        self._show_label = not self._show_label
        self.update()
    
    def _prompt_set_label(self):
        """Prompt user to set label text."""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(None, "Flow Label", "Label text:", text=self._label)
        if ok:
            self._label = text
            if text:
                self._show_label = True
            self.update()
    
    def _clear_all_waypoints(self):
        """Remove all waypoints."""
        self._waypoints.clear()
        self.update_path()
    
    def _set_fluid_type(self, fluid_type: str):
        """Set the fluid type."""
        self._fluid_type = fluid_type
        self._update_pen()
        self.update()
    
    def _on_delete(self):
        """Delete this flow."""
        scene = self.scene()
        if scene and hasattr(scene, 'remove_flow'):
            scene.remove_flow(self)
    
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
    
    @property
    def label(self) -> str:
        return self._label
    
    @label.setter
    def label(self, value: str):
        self._label = value
        self.update()
    
    @property
    def show_label(self) -> bool:
        return self._show_label
    
    @show_label.setter
    def show_label(self, value: bool):
        self._show_label = value
        self.update()
    
    @property
    def waypoints(self) -> List[QPointF]:
        return self._waypoints.copy()
    
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
