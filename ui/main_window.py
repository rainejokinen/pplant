"""
MainWindow - Main application window for power plant simulator.

Assembles canvas, panels, menus, and toolbars.
"""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QKeySequence, QIcon

from .canvas.flow_view import FlowView
from .canvas.flow_scene import FlowScene
from .panels.component_library import ComponentLibrary
from .panels.properties_panel import PropertiesPanel

# Import component items for registration
from .items.turbine_item import TurbineItem
from .items.valve_item import ValveItem
from .items.heat_exchanger_item import (
    HeatExchangerItem, CondenserItem, FeedwaterHeaterItem, WaterWaterHXItem
)
from .items.mixer_item import MixerItem
from .items.splitter_item import SplitterItem


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Layout:
        - Left dock: Component Library
        - Center: Flow diagram canvas
        - Right dock: Properties panel
        - Top: Menu bar and toolbar
        - Bottom: Status bar
    """
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Power Plant Simulator")
        self.setMinimumSize(1200, 800)
        
        self._setup_scene()
        self._setup_canvas()
        self._setup_panels()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._apply_theme()
        self._connect_signals()
    
    def _setup_scene(self):
        """Create and configure the graphics scene."""
        self._scene = FlowScene()
        
        # Register component types for drag-drop
        self._scene.register_component_type("Turbine", TurbineItem)
        self._scene.register_component_type("Valve", ValveItem)
        self._scene.register_component_type("HeatExchanger", HeatExchangerItem)
        self._scene.register_component_type("Condenser", CondenserItem)
        self._scene.register_component_type("FeedwaterHeater", FeedwaterHeaterItem)
        self._scene.register_component_type("WaterWaterHX", WaterWaterHXItem)
        self._scene.register_component_type("Mixer", MixerItem)
        self._scene.register_component_type("Splitter", SplitterItem)
    
    def _setup_canvas(self):
        """Create the central canvas widget."""
        self._view = FlowView(self._scene)
        self.setCentralWidget(self._view)
    
    def _setup_panels(self):
        """Create dock panels."""
        # Component library (left)
        self._library = ComponentLibrary(self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self._library)
        
        # Properties panel (right)
        self._properties = PropertiesPanel(self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._properties)
    
    def _setup_menus(self):
        """Create menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        delete_action = QAction("&Delete", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.triggered.connect(self._on_delete)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        select_all_action = QAction("Select &All", self)
        select_all_action.setShortcut(QKeySequence.StandardKey.SelectAll)
        select_all_action.triggered.connect(self._on_select_all)
        edit_menu.addAction(select_all_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        zoom_in_action.triggered.connect(self._view.zoom_in)
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        zoom_out_action.triggered.connect(self._view.zoom_out)
        view_menu.addAction(zoom_out_action)
        
        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self._view.reset_zoom)
        view_menu.addAction(zoom_reset_action)
        
        fit_action = QAction("&Fit to Contents", self)
        fit_action.setShortcut("Ctrl+F")
        fit_action.triggered.connect(self._view.fit_to_contents)
        view_menu.addAction(fit_action)
        
        view_menu.addSeparator()
        
        # Snap to grid toggle
        self._snap_action = QAction("&Snap to Grid", self)
        self._snap_action.setShortcut("Ctrl+G")
        self._snap_action.setCheckable(True)
        self._snap_action.setChecked(True)  # Default enabled
        self._snap_action.triggered.connect(self._on_toggle_snap)
        view_menu.addAction(self._snap_action)
        
        view_menu.addSeparator()
        
        # Toggle panels
        view_menu.addAction(self._library.toggleViewAction())
        view_menu.addAction(self._properties.toggleViewAction())
        
        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")
        
        run_action = QAction("&Run", self)
        run_action.setShortcut("F5")
        run_action.triggered.connect(self._on_run_simulation)
        sim_menu.addAction(run_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Create main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # File actions
        toolbar.addAction("New").triggered.connect(self._on_new)
        toolbar.addAction("Open").triggered.connect(self._on_open)
        toolbar.addAction("Save").triggered.connect(self._on_save)
        
        toolbar.addSeparator()
        
        # Edit actions
        toolbar.addAction("Delete").triggered.connect(self._on_delete)
        
        toolbar.addSeparator()
        
        # View actions
        toolbar.addAction("Zoom In").triggered.connect(self._view.zoom_in)
        toolbar.addAction("Zoom Out").triggered.connect(self._view.zoom_out)
        toolbar.addAction("Fit").triggered.connect(self._view.fit_to_contents)
        
        toolbar.addSeparator()
        
        # Snap toggle button
        snap_btn = toolbar.addAction("⊞ Snap")
        snap_btn.setCheckable(True)
        snap_btn.setChecked(True)
        snap_btn.setToolTip("Snap to Grid (Ctrl+G)")
        snap_btn.triggered.connect(self._on_toggle_snap)
        self._snap_toolbar_action = snap_btn
        
        toolbar.addSeparator()
        
        # Simulation
        toolbar.addAction("▶ Run").triggered.connect(self._on_run_simulation)
    
    def _setup_statusbar(self):
        """Create status bar."""
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        
        # Permanent widgets
        self._zoom_label = QLabel("Zoom: 100%")
        self._statusbar.addPermanentWidget(self._zoom_label)
        
        self._selection_label = QLabel("Ready")
        self._statusbar.addWidget(self._selection_label)
    
    def _apply_theme(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e2228;
            }
            QMenuBar {
                background-color: #2d323c;
                color: #e0e0e0;
            }
            QMenuBar::item:selected {
                background-color: #4a90d9;
            }
            QMenu {
                background-color: #2d323c;
                color: #e0e0e0;
                border: 1px solid #4a4f5a;
            }
            QMenu::item:selected {
                background-color: #4a90d9;
            }
            QToolBar {
                background-color: #2d323c;
                border: none;
                spacing: 5px;
                padding: 5px;
            }
            QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #4a4f5a;
            }
            QToolButton:pressed {
                background-color: #4a90d9;
            }
            QStatusBar {
                background-color: #2d323c;
                color: #b0b0b0;
            }
            QDockWidget {
                color: #e0e0e0;
                titlebar-close-icon: none;
            }
            QDockWidget::title {
                background-color: #3d424c;
                padding: 5px;
            }
        """)
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Selection changes
        self._scene.selection_changed_items.connect(self._on_selection_changed)
        
        # Zoom changes
        self._view.zoom_changed.connect(self._on_zoom_changed)
        
        # Component added/removed
        self._scene.component_added.connect(
            lambda c: self._statusbar.showMessage(f"Added {c.component_type}", 2000)
        )
    
    # -------------------------------------------------------------------------
    # Event Handlers
    # -------------------------------------------------------------------------
    
    def _on_selection_changed(self, items):
        """Handle selection change."""
        self._properties.set_selection(items)
        
        if not items:
            self._selection_label.setText("Ready")
        elif len(items) == 1:
            item = items[0]
            if hasattr(item, 'component_type'):
                self._selection_label.setText(f"Selected: {item.component_type}")
            else:
                self._selection_label.setText("Selected: Flow")
        else:
            self._selection_label.setText(f"Selected: {len(items)} items")
    
    def _on_zoom_changed(self, zoom: float):
        """Handle zoom level change."""
        self._zoom_label.setText(f"Zoom: {int(zoom * 100)}%")
    
    def _on_new(self):
        """Create new diagram."""
        reply = QMessageBox.question(
            self, "New Diagram",
            "Clear current diagram?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._scene.clear_all()
    
    def _on_open(self):
        """Open diagram file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Diagram", "",
            "Power Plant Files (*.pplant);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            # TODO: Implement load
            self._statusbar.showMessage(f"Opened: {filename}", 3000)
    
    def _on_save(self):
        """Save current diagram."""
        # TODO: Implement save
        self._statusbar.showMessage("Save not implemented yet", 3000)
    
    def _on_save_as(self):
        """Save diagram as new file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Diagram", "",
            "Power Plant Files (*.pplant);;JSON Files (*.json);;All Files (*)"
        )
        if filename:
            # TODO: Implement save
            self._statusbar.showMessage(f"Saved: {filename}", 3000)
    
    def _on_delete(self):
        """Delete selected items."""
        self._scene.delete_selected()
    
    def _on_select_all(self):
        """Select all items."""
        for item in self._scene.items():
            item.setSelected(True)
    
    def _on_toggle_snap(self, checked: bool):
        """Toggle snap-to-grid."""
        self._scene.set_snap_enabled(checked)
        # Keep menu and toolbar in sync
        self._snap_action.setChecked(checked)
        self._snap_toolbar_action.setChecked(checked)
        status = "enabled" if checked else "disabled"
        self._statusbar.showMessage(f"Snap to grid {status}", 2000)
    
    def _on_run_simulation(self):
        """Run simulation."""
        components = self._scene.components
        flows = self._scene.flows
        
        self._statusbar.showMessage(
            f"Simulation: {len(components)} components, {len(flows)} flows",
            3000
        )
        # TODO: Implement actual simulation
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self, "About Power Plant Simulator",
            "Power Plant Simulator\n\n"
            "A graphical simulation tool for power plant processes.\n\n"
            "Built with PyQt6"
        )


def run_app():
    """Launch the application."""
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("Power Plant Simulator")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_app()
