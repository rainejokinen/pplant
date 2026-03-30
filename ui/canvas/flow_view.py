"""
FlowView - Zoomable, pannable canvas for flow diagrams.

Provides mouse wheel zoom, middle-click pan, and grid background.
"""

from PyQt6.QtWidgets import QGraphicsView, QApplication
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QWheelEvent, QMouseEvent


class FlowView(QGraphicsView):
    """
    Custom QGraphicsView with zoom, pan, and grid background.
    
    Controls:
        - Mouse wheel: Zoom in/out (centered on cursor)
        - Middle mouse drag: Pan view
        - Ctrl+0: Reset zoom to 100%
        - Ctrl++/-: Zoom in/out
    
    Signals:
        zoom_changed(float): Emitted when zoom level changes
    """
    
    zoom_changed = pyqtSignal(float)
    
    # Zoom configuration
    ZOOM_MIN = 0.1
    ZOOM_MAX = 5.0
    ZOOM_STEP = 1.15  # 15% per wheel notch
    
    # Grid configuration (defaults, can be overridden by scene.snap_grid_size)
    GRID_SIZE_MINOR_DEFAULT = 20
    GRID_SIZE_MAJOR_DEFAULT = 100
    GRID_COLOR_MINOR = QColor(50, 55, 65)
    GRID_COLOR_MAJOR = QColor(60, 65, 75)
    BACKGROUND_COLOR = QColor(30, 35, 45)
    
    def __init__(self, scene=None, parent=None):
        super().__init__(scene, parent)
        
        self._zoom_level = 1.0
        self._is_panning = False
        self._pan_start = QPointF()
        
        self._setup_view()
        
        # Connect to scene's snap size changes
        if scene and hasattr(scene, 'snap_size_changed'):
            scene.snap_size_changed.connect(self._on_snap_size_changed)
    
    def _on_snap_size_changed(self, size: int):
        """Handle snap size change from scene."""
        self.resetCachedContent()
        self.viewport().update()
    
    @property
    def grid_size_minor(self) -> int:
        """Get minor grid size (from scene or default)."""
        scene = self.scene()
        if scene and hasattr(scene, 'snap_grid_size'):
            return scene.snap_grid_size
        return self.GRID_SIZE_MINOR_DEFAULT
    
    @property
    def grid_size_major(self) -> int:
        """Get major grid size (5x minor)."""
        return self.grid_size_minor * 5
    
    def _setup_view(self):
        """Configure view settings."""
        # Rendering quality
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        
        # Interaction
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        
        # Scrollbars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Background
        self.setBackgroundBrush(self.BACKGROUND_COLOR)
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        
        # Viewport updates
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
    
    def drawBackground(self, painter: QPainter, rect):
        """Draw grid background."""
        super().drawBackground(painter, rect)
        
        minor = self.grid_size_minor
        major = self.grid_size_major
        
        # Calculate visible grid area
        left = int(rect.left()) - (int(rect.left()) % minor)
        top = int(rect.top()) - (int(rect.top()) % minor)
        
        # Draw minor grid lines
        painter.setPen(QPen(self.GRID_COLOR_MINOR, 0.5))
        
        x = left
        while x < rect.right():
            if x % major != 0:  # Skip major lines
                painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += minor
        
        y = top
        while y < rect.bottom():
            if y % major != 0:
                painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += minor
        
        # Draw major grid lines
        painter.setPen(QPen(self.GRID_COLOR_MAJOR, 1.0))
        
        left_major = int(rect.left()) - (int(rect.left()) % major)
        top_major = int(rect.top()) - (int(rect.top()) % major)
        
        x = left_major
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += major
        
        y = top_major
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += major
    
    def wheelEvent(self, event: QWheelEvent):
        """Handle mouse wheel zoom."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+wheel: horizontal scroll (let default handle)
            super().wheelEvent(event)
            return
        
        # Zoom
        angle = event.angleDelta().y()
        if angle > 0:
            factor = self.ZOOM_STEP
        elif angle < 0:
            factor = 1.0 / self.ZOOM_STEP
        else:
            return
        
        self._apply_zoom(factor)
    
    def _apply_zoom(self, factor: float):
        """Apply zoom factor with limits."""
        new_zoom = self._zoom_level * factor
        
        # Clamp to limits
        if new_zoom < self.ZOOM_MIN:
            factor = self.ZOOM_MIN / self._zoom_level
            new_zoom = self.ZOOM_MIN
        elif new_zoom > self.ZOOM_MAX:
            factor = self.ZOOM_MAX / self._zoom_level
            new_zoom = self.ZOOM_MAX
        
        if factor == 1.0:
            return
        
        self._zoom_level = new_zoom
        self.scale(factor, factor)
        self.zoom_changed.emit(self._zoom_level)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle middle mouse button for panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle pan dragging."""
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            
            # Scroll the view
            self.horizontalScrollBar().setValue(
                int(self.horizontalScrollBar().value() - delta.x())
            )
            self.verticalScrollBar().setValue(
                int(self.verticalScrollBar().value() - delta.y())
            )
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle end of panning."""
        if event.button() == Qt.MouseButton.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def reset_zoom(self):
        """Reset zoom to 100%."""
        self.resetTransform()
        self._zoom_level = 1.0
        self.zoom_changed.emit(self._zoom_level)
    
    def zoom_in(self):
        """Zoom in by one step."""
        self._apply_zoom(self.ZOOM_STEP)
    
    def zoom_out(self):
        """Zoom out by one step."""
        self._apply_zoom(1.0 / self.ZOOM_STEP)
    
    def fit_to_contents(self):
        """Fit view to show all scene contents."""
        self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        # Update zoom level from transform
        self._zoom_level = self.transform().m11()
        self.zoom_changed.emit(self._zoom_level)
    
    @property
    def zoom_level(self) -> float:
        """Current zoom level (1.0 = 100%)."""
        return self._zoom_level
    
    @property
    def zoom_percent(self) -> int:
        """Current zoom as percentage."""
        return int(self._zoom_level * 100)
