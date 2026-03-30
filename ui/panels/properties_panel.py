"""
PropertiesPanel - Tabbed property editor for selected components.

Shows and edits properties of the currently selected component
with multiple tabs for different property categories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QGroupBox, QScrollArea, QFrame,
    QTabWidget, QSpinBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..items.base_item import BaseComponentItem
    from ..items.flow_item import FlowItem


class PropertiesPanel(QDockWidget):
    """
    Tabbed dock widget for viewing/editing selected component properties.
    
    Tabs:
        - General: Name, position, ports
        - Parameters: Component-specific parameters (properties)
        - Flows: Input/output flow states (p, t, h, m)
        - Balance: Combined mass and energy balance
        - Iteration: Solver status
    """
    
    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(280)
        
        self._current_item: Optional[BaseComponentItem] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the tabbed UI layout."""
        self._main_widget = QWidget()
        self._main_layout = QVBoxLayout(self._main_widget)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Header label (component type)
        self._header = QLabel("No Selection")
        self._header.setStyleSheet("font-size: 14px; font-weight: bold; color: #4a90d9; padding: 8px;")
        self._main_layout.addWidget(self._header)
        
        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._main_layout.addWidget(self._tabs)
        
        # Create tabs
        self._general_tab = self._create_scroll_tab()
        self._params_tab = self._create_scroll_tab()
        self._flows_tab = self._create_scroll_tab()
        self._balance_tab = self._create_scroll_tab()
        self._iteration_tab = self._create_scroll_tab()
        
        self._tabs.addTab(self._general_tab, "General")
        self._tabs.addTab(self._params_tab, "Parameters")
        self._tabs.addTab(self._flows_tab, "Flows")
        self._tabs.addTab(self._balance_tab, "Balance")
        self._tabs.addTab(self._iteration_tab, "Iteration")
        
        self.setWidget(self._main_widget)
        
        # Apply dark styling
        self.setStyleSheet("""
            QDockWidget {
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #4a4f5a;
                background: #1e222a;
            }
            QTabBar::tab {
                background: #2d323c;
                color: #b0b0b0;
                padding: 6px 10px;
                border: 1px solid #4a4f5a;
                border-bottom: none;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #1e222a;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #4a4f5a;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QDoubleSpinBox, QSpinBox {
                background-color: #2d323c;
                color: #e0e0e0;
                border: 1px solid #4a4f5a;
                border-radius: 3px;
                padding: 4px;
                min-height: 20px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button,
            QSpinBox::up-button, QSpinBox::down-button {
                width: 20px;
                background: #3d424c;
                border: 1px solid #4a4f5a;
            }
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover,
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background: #4d525c;
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 6px solid #b0b0b0;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #b0b0b0;
            }
            QLabel {
                color: #b0b0b0;
            }
            QTableWidget {
                background-color: #2d323c;
                color: #e0e0e0;
                border: 1px solid #4a4f5a;
                gridline-color: #4a4f5a;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #3d424c;
                color: #e0e0e0;
                padding: 4px;
                border: 1px solid #4a4f5a;
            }
        """)
        
        self._show_no_selection()
    
    def _create_scroll_tab(self) -> QScrollArea:
        """Create a scrollable tab content area."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        container = QWidget()
        container.setObjectName("tab_container")
        layout = QVBoxLayout(container)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(5, 5, 5, 5)
        
        scroll.setWidget(container)
        return scroll
    
    def _get_tab_layout(self, tab: QScrollArea) -> QVBoxLayout:
        """Get the layout of a tab's container widget."""
        return tab.widget().layout()
    
    def _clear_tab(self, tab: QScrollArea):
        """Clear all widgets from a tab."""
        layout = self._get_tab_layout(tab)
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _clear_all_tabs(self):
        """Clear all tab contents."""
        self._clear_tab(self._general_tab)
        self._clear_tab(self._params_tab)
        self._clear_tab(self._flows_tab)
        self._clear_tab(self._balance_tab)
        self._clear_tab(self._iteration_tab)
    
    def _show_no_selection(self):
        """Show empty state."""
        self._header.setText("No Selection")
        self._clear_all_tabs()
        
        for tab in [self._general_tab, self._params_tab, self._flows_tab,
                    self._balance_tab, self._iteration_tab]:
            layout = self._get_tab_layout(tab)
            label = QLabel("Select a component to view properties")
            label.setStyleSheet("color: #666; padding: 20px;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            layout.addWidget(label)
    
    def set_selection(self, items: List):
        """
        Update panel for selected items.
        
        Args:
            items: List of selected QGraphicsItems
        """
        self._clear_all_tabs()
        
        if not items:
            self._show_no_selection()
            self._current_item = None
            return
        
        if len(items) > 1:
            self._header.setText(f"{len(items)} Items Selected")
            self._current_item = None
            for tab in [self._general_tab, self._params_tab]:
                layout = self._get_tab_layout(tab)
                label = QLabel("Multiple items selected.\nEdit is not available.")
                label.setStyleSheet("color: #888; padding: 20px;")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
            return
        
        item = items[0]
        
        from ..items.base_item import BaseComponentItem
        from ..items.flow_item import FlowItem
        
        if isinstance(item, BaseComponentItem):
            self._show_component_properties(item)
            self._current_item = item
        elif isinstance(item, FlowItem):
            self._show_flow_properties(item)
            self._current_item = None
        else:
            self._header.setText("Unknown Item")
    
    def _show_component_properties(self, item: BaseComponentItem):
        """Build property form for component across tabs."""
        self._header.setText(item.component_type)
        
        # === General Tab ===
        general_layout = self._get_tab_layout(self._general_tab)
        
        # Identity group
        id_group = QGroupBox("Identity")
        id_layout = QFormLayout(id_group)
        
        name_edit = QLineEdit(item.name)
        name_edit.textChanged.connect(lambda text: setattr(item, 'name', text))
        id_layout.addRow("Name:", name_edit)
        
        type_label = QLabel(item.component_type)
        id_layout.addRow("Type:", type_label)
        
        general_layout.addWidget(id_group)
        
        # Position group
        pos_group = QGroupBox("Position && Transform")
        pos_layout = QFormLayout(pos_group)
        
        pos_label = QLabel(f"({item.pos().x():.0f}, {item.pos().y():.0f})")
        pos_layout.addRow("Position:", pos_label)
        
        rot_label = QLabel(f"{item.rotation_angle}°")
        pos_layout.addRow("Rotation:", rot_label)
        
        flip_text = []
        if item.is_flipped_h:
            flip_text.append("H")
        if item.is_flipped_v:
            flip_text.append("V")
        flip_label = QLabel(" + ".join(flip_text) if flip_text else "None")
        pos_layout.addRow("Flip:", flip_label)
        
        # Scale display (show X and Y separately if different)
        if hasattr(item, '_scale_x') and hasattr(item, '_scale_y'):
            if abs(item._scale_x - item._scale_y) < 0.01:
                scale_text = f"{item._scale_x:.1f}x"
            else:
                scale_text = f"X:{item._scale_x:.1f} Y:{item._scale_y:.1f}"
        else:
            scale_text = f"{item.scale_factor:.1f}x"
        scale_label = QLabel(scale_text)
        pos_layout.addRow("Scale:", scale_label)
        
        general_layout.addWidget(pos_group)
        
        # Label group - expanded settings
        label_group = QGroupBox("Labels")
        label_layout = QFormLayout(label_group)
        
        from PyQt6.QtWidgets import QCheckBox, QComboBox, QPushButton, QColorDialog, QHBoxLayout
        
        # Master show/hide
        show_label_cb = QCheckBox()
        show_label_cb.setChecked(item.show_label)
        show_label_cb.stateChanged.connect(lambda state: setattr(item, 'show_label', state == Qt.CheckState.Checked.value))
        label_layout.addRow("Show Labels:", show_label_cb)
        
        # Get the name label for settings (if exists)
        name_label = item.get_label("name") if hasattr(item, 'get_label') else None
        
        if name_label:
            # Font size
            font_size_spin = QSpinBox()
            font_size_spin.setRange(6, 24)
            font_size_spin.setValue(name_label.font_size)
            font_size_spin.valueChanged.connect(lambda v: setattr(name_label, 'font_size', v))
            label_layout.addRow("Font Size:", font_size_spin)
            
            # Bold toggle
            bold_cb = QCheckBox()
            bold_cb.setChecked(name_label.bold)
            bold_cb.stateChanged.connect(lambda state: setattr(name_label, 'bold', state == Qt.CheckState.Checked.value))
            label_layout.addRow("Bold:", bold_cb)
            
            # Color picker
            color_btn = QPushButton()
            color_btn.setFixedSize(60, 24)
            color_btn.setStyleSheet(f"background-color: {name_label.color.name()}; border: 1px solid #666;")
            
            def pick_color():
                color = QColorDialog.getColor(name_label.color, None, "Label Color")
                if color.isValid():
                    name_label.color = color
                    color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
            
            color_btn.clicked.connect(pick_color)
            label_layout.addRow("Color:", color_btn)
            
            # Reset position button
            reset_btn = QPushButton("Reset Position")
            reset_btn.clicked.connect(name_label.reset_position)
            label_layout.addRow("", reset_btn)
        
        general_layout.addWidget(label_group)
        
        # Ports group - show what each port is connected to
        ports_group = QGroupBox("Ports")
        ports_layout = QFormLayout(ports_group)
        
        for port in item.input_ports:
            if port.is_connected and port.connected_flow:
                flow = port.connected_flow
                source_comp = flow.source_component
                conn_name = source_comp.name if source_comp else "Unknown"
                conn_port = flow.source_port.name if flow.source_port else ""
                status = f'<span style="color: #6a6">→ {conn_name}.{conn_port}</span>'
            else:
                status = '<span style="color: #888">○ Not connected</span>'
            label = QLabel(status)
            ports_layout.addRow(f"⬤ {port.name}:", label)
        
        for port in item.output_ports:
            if port.is_connected and port.connected_flow:
                flow = port.connected_flow
                target_comp = flow.target_component
                conn_name = target_comp.name if target_comp else "Unknown"
                conn_port = flow.target_port.name if flow.target_port else ""
                status = f'<span style="color: #6a6">→ {conn_name}.{conn_port}</span>'
            else:
                status = '<span style="color: #888">○ Not connected</span>'
            label = QLabel(status)
            ports_layout.addRow(f"◯ {port.name}:", label)
        
        general_layout.addWidget(ports_group)
        general_layout.addStretch()
        
        # === Parameters Tab ===
        self._add_type_specific_properties(item)
        
        # === Flows Tab ===
        self._add_flows_tab(item)
        
        # === Balance Tab (Combined Mass & Energy) ===
        balance_layout = self._get_tab_layout(self._balance_tab)
        
        mass_group = QGroupBox("Mass Balance")
        mass_form = QFormLayout(mass_group)
        mass_form.addRow("Status:", QLabel("Not calculated"))
        mass_form.addRow("Inlet Mass:", QLabel("— kg/s"))
        mass_form.addRow("Outlet Mass:", QLabel("— kg/s"))
        mass_form.addRow("Imbalance:", QLabel("— kg/s"))
        balance_layout.addWidget(mass_group)
        
        energy_group = QGroupBox("Energy Balance")
        energy_form = QFormLayout(energy_group)
        energy_form.addRow("Status:", QLabel("Not calculated"))
        energy_form.addRow("Inlet Energy:", QLabel("— MW"))
        energy_form.addRow("Outlet Energy:", QLabel("— MW"))
        energy_form.addRow("Heat Transfer:", QLabel("— MW"))
        energy_form.addRow("Work:", QLabel("— MW"))
        energy_form.addRow("Imbalance:", QLabel("— MW"))
        balance_layout.addWidget(energy_group)
        balance_layout.addStretch()
        
        # === Iteration Tab ===
        iter_layout = self._get_tab_layout(self._iteration_tab)
        iter_group = QGroupBox("Iteration Status")
        iter_form = QFormLayout(iter_group)
        iter_form.addRow("Converged:", QLabel("—"))
        iter_form.addRow("Iterations:", QLabel("—"))
        iter_form.addRow("Residual:", QLabel("—"))
        iter_form.addRow("Last Update:", QLabel("—"))
        iter_layout.addWidget(iter_group)
        iter_layout.addStretch()
    
    def _add_flows_tab(self, item: BaseComponentItem):
        """Add flow parameters tab with tables for inlet/outlet flows."""
        flows_layout = self._get_tab_layout(self._flows_tab)
        
        # Inlet flows table
        inlet_group = QGroupBox("Inlet Flows")
        inlet_layout = QVBoxLayout(inlet_group)
        
        inlet_table = QTableWidget()
        inlet_table.setColumnCount(5)
        inlet_table.setHorizontalHeaderLabels(["Port", "p (bar)", "t (°C)", "h (kJ/kg)", "m (kg/s)"])
        inlet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        inlet_table.verticalHeader().setVisible(False)
        
        # Add rows for each input port
        inlet_table.setRowCount(len(item.input_ports))
        for row, port in enumerate(item.input_ports):
            inlet_table.setItem(row, 0, QTableWidgetItem(port.name))
            inlet_table.setItem(row, 1, QTableWidgetItem("—"))
            inlet_table.setItem(row, 2, QTableWidgetItem("—"))
            inlet_table.setItem(row, 3, QTableWidgetItem("—"))
            inlet_table.setItem(row, 4, QTableWidgetItem("—"))
        
        inlet_layout.addWidget(inlet_table)
        flows_layout.addWidget(inlet_group)
        
        # Outlet flows table
        outlet_group = QGroupBox("Outlet Flows")
        outlet_layout = QVBoxLayout(outlet_group)
        
        outlet_table = QTableWidget()
        outlet_table.setColumnCount(5)
        outlet_table.setHorizontalHeaderLabels(["Port", "p (bar)", "t (°C)", "h (kJ/kg)", "m (kg/s)"])
        outlet_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        outlet_table.verticalHeader().setVisible(False)
        
        # Add rows for each output port
        outlet_table.setRowCount(len(item.output_ports))
        for row, port in enumerate(item.output_ports):
            outlet_table.setItem(row, 0, QTableWidgetItem(port.name))
            outlet_table.setItem(row, 1, QTableWidgetItem("—"))
            outlet_table.setItem(row, 2, QTableWidgetItem("—"))
            outlet_table.setItem(row, 3, QTableWidgetItem("—"))
            outlet_table.setItem(row, 4, QTableWidgetItem("—"))
        
        outlet_layout.addWidget(outlet_table)
        flows_layout.addWidget(outlet_group)
        flows_layout.addStretch()
    
    def _add_type_specific_properties(self, item: BaseComponentItem):
        """Add properties specific to component type to Parameters tab."""
        from ..items.turbine_item import TurbineItem
        from ..items.valve_item import ValveItem
        from ..items.heat_exchanger_item import HeatExchangerItem
        
        params_layout = self._get_tab_layout(self._params_tab)
        
        if isinstance(item, TurbineItem):
            self._add_turbine_properties(params_layout, item)
        elif isinstance(item, ValveItem):
            self._add_valve_properties(params_layout, item)
        elif isinstance(item, HeatExchangerItem):
            self._add_hx_properties(params_layout, item)
        else:
            label = QLabel("No specific parameters for this component type")
            label.setStyleSheet("color: #888; padding: 20px;")
            params_layout.addWidget(label)
        
        params_layout.addStretch()
    
    def _add_turbine_properties(self, layout, item):
        """Add turbine-specific properties."""
        group = QGroupBox("Turbine Parameters")
        form = QFormLayout(group)
        
        efficiency = QDoubleSpinBox()
        efficiency.setRange(0.0, 100.0)
        efficiency.setSingleStep(0.5)
        efficiency.setDecimals(1)
        efficiency.setSuffix(" %")
        efficiency.setValue(88.0)
        form.addRow("Efficiency:", efficiency)
        
        stages = QSpinBox()
        stages.setRange(1, 20)
        stages.setValue(5)
        form.addRow("Stages:", stages)
        
        layout.addWidget(group)
        
        results_group = QGroupBox("Calculated Results")
        results_form = QFormLayout(results_group)
        results_form.addRow("Power Output:", QLabel("— MW"))
        results_form.addRow("Exhaust Pressure:", QLabel("— bar"))
        results_form.addRow("Exhaust Quality:", QLabel("— %"))
        layout.addWidget(results_group)
    
    def _add_valve_properties(self, layout, item):
        """Add valve-specific properties."""
        group = QGroupBox("Valve Parameters")
        form = QFormLayout(group)
        
        opening = QDoubleSpinBox()
        opening.setRange(0.0, 100.0)
        opening.setSingleStep(1.0)
        opening.setDecimals(1)
        opening.setSuffix(" %")
        opening.setValue(100.0)
        form.addRow("Opening:", opening)
        
        cv = QDoubleSpinBox()
        cv.setRange(0.0, 10000.0)
        cv.setSingleStep(10.0)
        cv.setDecimals(1)
        cv.setValue(100.0)
        form.addRow("Cv:", cv)
        
        layout.addWidget(group)
        
        results_group = QGroupBox("Calculated Results")
        results_form = QFormLayout(results_group)
        results_form.addRow("Pressure Drop:", QLabel("— bar"))
        results_form.addRow("Flow Rate:", QLabel("— kg/s"))
        layout.addWidget(results_group)
    
    def _add_hx_properties(self, layout, item):
        """Add heat exchanger properties."""
        group = QGroupBox("Heat Exchanger Parameters")
        form = QFormLayout(group)
        
        ttd = QDoubleSpinBox()
        ttd.setRange(0.0, 50.0)
        ttd.setSingleStep(0.5)
        ttd.setDecimals(1)
        ttd.setSuffix(" °C")
        ttd.setValue(5.0)
        form.addRow("TTD:", ttd)
        
        dca = QDoubleSpinBox()
        dca.setRange(0.0, 50.0)
        dca.setSingleStep(0.5)
        dca.setDecimals(1)
        dca.setSuffix(" °C")
        dca.setValue(5.0)
        form.addRow("DCA:", dca)
        
        layout.addWidget(group)
        
        results_group = QGroupBox("Calculated Results")
        results_form = QFormLayout(results_group)
        results_form.addRow("Heat Duty:", QLabel("— MW"))
        results_form.addRow("LMTD:", QLabel("— °C"))
        results_form.addRow("UA:", QLabel("— kW/°C"))
        layout.addWidget(results_group)
    
    def _show_flow_properties(self, flow: FlowItem):
        """Show properties for a flow connection."""
        self._header.setText("Flow Connection")
        
        # === General Tab ===
        general_layout = self._get_tab_layout(self._general_tab)
        
        conn_group = QGroupBox("Connection")
        conn_layout = QFormLayout(conn_group)
        
        source = flow.source_component
        target = flow.target_component
        
        source_text = f"{source.name}.{flow.source_port.name}" if source else "—"
        target_text = f"{target.name}.{flow.target_port.name}" if target else "—"
        
        conn_layout.addRow("From:", QLabel(source_text))
        conn_layout.addRow("To:", QLabel(target_text))
        
        waypoints = len(flow.waypoints)
        conn_layout.addRow("Waypoints:", QLabel(str(waypoints)))
        
        general_layout.addWidget(conn_group)
        
        # Display settings group
        from PyQt6.QtWidgets import QCheckBox
        
        display_group = QGroupBox("Display")
        display_layout = QFormLayout(display_group)
        
        # Show label toggle
        show_label_cb = QCheckBox()
        show_label_cb.setChecked(flow.show_label)
        show_label_cb.stateChanged.connect(lambda state: setattr(flow, 'show_label', state == Qt.CheckState.Checked.value))
        display_layout.addRow("Show Label:", show_label_cb)
        
        # Show property cross toggle
        show_cross_cb = QCheckBox()
        show_cross_cb.setChecked(flow.show_property_cross)
        show_cross_cb.stateChanged.connect(lambda state: setattr(flow, 'show_property_cross', state == Qt.CheckState.Checked.value))
        display_layout.addRow("Show Property Cross:", show_cross_cb)
        
        general_layout.addWidget(display_group)
        general_layout.addStretch()
        
        # === Parameters Tab ===
        params_layout = self._get_tab_layout(self._params_tab)
        
        props_group = QGroupBox("Flow State")
        props_layout = QFormLayout(props_group)
        props_layout.addRow("Pressure:", QLabel("— bar"))
        props_layout.addRow("Temperature:", QLabel("— °C"))
        props_layout.addRow("Enthalpy:", QLabel("— kJ/kg"))
        props_layout.addRow("Mass Flow:", QLabel("— kg/s"))
        props_layout.addRow("Quality:", QLabel("— %"))
        params_layout.addWidget(props_group)
        params_layout.addStretch()
