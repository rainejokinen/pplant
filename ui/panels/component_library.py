"""
ComponentLibrary - Drag source panel for adding components.

Tree widget with categorized components that can be dragged onto the canvas.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QDockWidget, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
    QLineEdit, QLabel
)
from PyQt6.QtCore import Qt, QMimeData, QByteArray
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor, QFont

from ..canvas.flow_scene import COMPONENT_MIME_TYPE


# Component definitions: (display_name, internal_type, tooltip)
COMPONENT_CATEGORIES = {
    "Turbomachinery": [
        ("Turbine", "Turbine", "Steam/gas turbine with 2 inlets and 3 outlets"),
    ],
    "Valves": [
        ("Control Valve", "Valve", "Flow control valve with pressure drop"),
    ],
    "Heat Exchangers": [
        ("Heat Exchanger", "HeatExchanger", "Generic heat exchanger"),
        ("Condenser", "Condenser", "Steam condenser with cooling water"),
        ("Feedwater Heater", "FeedwaterHeater", "Feedwater heater using extraction steam"),
        ("Water-Water HX", "WaterWaterHX", "Water to water heat exchanger"),
    ],
    "Junctions": [
        ("Mixer", "Mixer", "Combines 2 streams into 1"),
        ("Splitter", "Splitter", "Splits 1 stream into 2"),
    ],
}


class ComponentLibrary(QDockWidget):
    """
    Dock widget containing draggable component library.
    
    Features:
        - Categorized tree of available components
        - Search/filter functionality
        - Drag-and-drop to canvas
    """
    
    def __init__(self, parent=None):
        super().__init__("Component Library", parent)
        
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(200)
        
        self._setup_ui()
        self._populate_tree()
    
    def _setup_ui(self):
        """Create the UI layout."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search components...")
        self._search_box.textChanged.connect(self._filter_tree)
        layout.addWidget(self._search_box)
        
        # Component tree
        self._tree = ComponentTree()
        layout.addWidget(self._tree)
        
        # Instructions
        hint = QLabel("Drag components to canvas")
        hint.setStyleSheet("color: #888; font-size: 10px;")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint)
        
        self.setWidget(container)
    
    def _populate_tree(self):
        """Add components to the tree."""
        for category_name, components in COMPONENT_CATEGORIES.items():
            category_item = QTreeWidgetItem([category_name])
            category_item.setFlags(category_item.flags() & ~Qt.ItemFlag.ItemIsDragEnabled)
            category_item.setExpanded(True)
            
            # Style category header
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            for display_name, type_name, tooltip in components:
                comp_item = QTreeWidgetItem([display_name])
                comp_item.setData(0, Qt.ItemDataRole.UserRole, type_name)
                comp_item.setToolTip(0, tooltip)
                category_item.addChild(comp_item)
            
            self._tree.addTopLevelItem(category_item)
    
    def _filter_tree(self, text: str):
        """Filter components by search text."""
        search = text.lower()
        
        for i in range(self._tree.topLevelItemCount()):
            category = self._tree.topLevelItem(i)
            category_visible = False
            
            for j in range(category.childCount()):
                item = category.child(j)
                name = item.text(0).lower()
                tooltip = (item.toolTip(0) or "").lower()
                
                visible = search in name or search in tooltip
                item.setHidden(not visible)
                
                if visible:
                    category_visible = True
            
            category.setHidden(not category_visible)


class ComponentTree(QTreeWidget):
    """
    Tree widget with drag support for components.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setHeaderHidden(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        
        # Styling
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #2d323c;
                color: #e0e0e0;
                border: none;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:hover {
                background-color: #3d424c;
            }
            QTreeWidget::item:selected {
                background-color: #4a90d9;
            }
        """)
    
    def startDrag(self, supportedActions):
        """Start drag operation with component data."""
        item = self.currentItem()
        if not item:
            return
        
        # Get component type from item data
        type_name = item.data(0, Qt.ItemDataRole.UserRole)
        if not type_name:
            return  # Category item, not draggable
        
        # Create MIME data
        mime = QMimeData()
        data = QByteArray(type_name.encode('utf-8'))
        mime.setData(COMPONENT_MIME_TYPE, data)
        
        # Create drag with preview pixmap
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # Create ghost image
        pixmap = self._create_drag_pixmap(item.text(0))
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        drag.exec(Qt.DropAction.CopyAction)
    
    def _create_drag_pixmap(self, text: str) -> QPixmap:
        """Create a preview pixmap for dragging."""
        pixmap = QPixmap(120, 40)
        pixmap.fill(QColor(74, 144, 217, 200))
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, text)
        painter.end()
        
        return pixmap
