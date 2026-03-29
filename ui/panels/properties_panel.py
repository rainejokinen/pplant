"""
PropertiesPanel - Property editor for selected components.

Shows and edits properties of the currently selected component.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, List
from PyQt6.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QFormLayout, QLabel,
    QLineEdit, QDoubleSpinBox, QGroupBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from ..items.base_item import BaseComponentItem
    from ..items.flow_item import FlowItem


class PropertiesPanel(QDockWidget):
    """
    Dock widget for viewing/editing selected component properties.
    
    Dynamically builds form based on selected item type.
    """
    
    def __init__(self, parent=None):
        super().__init__("Properties", parent)
        
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(250)
        
        self._current_item: Optional[BaseComponentItem] = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Create the UI layout."""
        # Scroll area for long property lists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self._container = QWidget()
        self._layout = QVBoxLayout(self._container)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Placeholder
        self._placeholder = QLabel("Select a component")
        self._placeholder.setStyleSheet("color: #888; padding: 20px;")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(self._placeholder)
        
        scroll.setWidget(self._container)
        self.setWidget(scroll)
        
        # Apply dark styling
        self.setStyleSheet("""
            QDockWidget {
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
            QLineEdit, QDoubleSpinBox {
                background-color: #2d323c;
                color: #e0e0e0;
                border: 1px solid #4a4f5a;
                border-radius: 3px;
                padding: 4px;
            }
            QLabel {
                color: #b0b0b0;
            }
        """)
    
    def set_selection(self, items: List):
        """
        Update panel for selected items.
        
        Args:
            items: List of selected QGraphicsItems
        """
        # Clear current content
        self._clear_content()
        
        if not items:
            self._show_placeholder("Select a component")
            self._current_item = None
            return
        
        if len(items) > 1:
            self._show_placeholder(f"{len(items)} items selected")
            self._current_item = None
            return
        
        item = items[0]
        
        # Check item type
        from ..items.base_item import BaseComponentItem
        from ..items.flow_item import FlowItem
        
        if isinstance(item, BaseComponentItem):
            self._show_component_properties(item)
            self._current_item = item
        elif isinstance(item, FlowItem):
            self._show_flow_properties(item)
            self._current_item = None
        else:
            self._show_placeholder("Unknown item type")
    
    def _clear_content(self):
        """Remove all widgets from layout."""
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _show_placeholder(self, text: str):
        """Show placeholder message."""
        label = QLabel(text)
        label.setStyleSheet("color: #888; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._layout.addWidget(label)
    
    def _show_component_properties(self, item: BaseComponentItem):
        """Build property form for component."""
        # Header with component type
        header = QLabel(f"<b>{item.component_type}</b>")
        header.setStyleSheet("font-size: 14px; color: #4a90d9; padding: 5px;")
        self._layout.addWidget(header)
        
        # General properties group
        general_group = QGroupBox("General")
        general_layout = QFormLayout(general_group)
        
        # Name field
        name_edit = QLineEdit(item.name)
        name_edit.textChanged.connect(lambda text: setattr(item, 'name', text))
        general_layout.addRow("Name:", name_edit)
        
        # Position (read-only for now)
        pos_label = QLabel(f"({item.pos().x():.0f}, {item.pos().y():.0f})")
        general_layout.addRow("Position:", pos_label)
        
        self._layout.addWidget(general_group)
        
        # Ports group
        ports_group = QGroupBox("Ports")
        ports_layout = QFormLayout(ports_group)
        
        # Input ports
        for port in item.input_ports:
            status = "✓ Connected" if port.is_connected else "○ Open"
            color = "#6a6" if port.is_connected else "#888"
            label = QLabel(f'<span style="color: {color}">{status}</span>')
            ports_layout.addRow(f"{port.name}:", label)
        
        # Output ports
        for port in item.output_ports:
            status = "✓ Connected" if port.is_connected else "○ Open"
            color = "#6a6" if port.is_connected else "#888"
            label = QLabel(f'<span style="color: {color}">{status}</span>')
            ports_layout.addRow(f"{port.name}:", label)
        
        self._layout.addWidget(ports_group)
        
        # Add component-specific properties
        self._add_type_specific_properties(item)
        
        # Spacer at bottom
        self._layout.addStretch()
    
    def _add_type_specific_properties(self, item: BaseComponentItem):
        """Add properties specific to component type."""
        from ..items.turbine_item import TurbineItem
        from ..items.valve_item import ValveItem
        from ..items.heat_exchanger_item import HeatExchangerItem
        
        if isinstance(item, TurbineItem):
            self._add_turbine_properties(item)
        elif isinstance(item, ValveItem):
            self._add_valve_properties(item)
        elif isinstance(item, HeatExchangerItem):
            self._add_hx_properties(item)
    
    def _add_turbine_properties(self, item):
        """Add turbine-specific properties."""
        group = QGroupBox("Turbine Parameters")
        layout = QFormLayout(group)
        
        # Efficiency
        efficiency = QDoubleSpinBox()
        efficiency.setRange(0, 100)
        efficiency.setSuffix(" %")
        efficiency.setValue(88.0)
        layout.addRow("Efficiency:", efficiency)
        
        # Power output (read-only, calculated)
        power = QLabel("— MW")
        layout.addRow("Power Output:", power)
        
        self._layout.addWidget(group)
    
    def _add_valve_properties(self, item):
        """Add valve-specific properties."""
        group = QGroupBox("Valve Parameters")
        layout = QFormLayout(group)
        
        # Opening
        opening = QDoubleSpinBox()
        opening.setRange(0, 100)
        opening.setSuffix(" %")
        opening.setValue(100.0)
        layout.addRow("Opening:", opening)
        
        self._layout.addWidget(group)
    
    def _add_hx_properties(self, item):
        """Add heat exchanger properties."""
        group = QGroupBox("Heat Exchanger Parameters")
        layout = QFormLayout(group)
        
        # Heat duty (calculated)
        duty = QLabel("— MW")
        layout.addRow("Heat Duty:", duty)
        
        # TTD
        ttd = QDoubleSpinBox()
        ttd.setRange(0, 50)
        ttd.setSuffix(" °C")
        ttd.setValue(5.0)
        layout.addRow("TTD:", ttd)
        
        self._layout.addWidget(group)
    
    def _show_flow_properties(self, flow: FlowItem):
        """Show properties for a flow connection."""
        header = QLabel("<b>Flow Connection</b>")
        header.setStyleSheet("font-size: 14px; color: #4a90d9; padding: 5px;")
        self._layout.addWidget(header)
        
        group = QGroupBox("Connection")
        layout = QFormLayout(group)
        
        # Source and target
        source = flow.source_component
        target = flow.target_component
        
        source_text = f"{source.name} → {flow.source_port.name}" if source else "—"
        target_text = f"{target.name} → {flow.target_port.name}" if target else "—"
        
        layout.addRow("From:", QLabel(source_text))
        layout.addRow("To:", QLabel(target_text))
        
        self._layout.addWidget(group)
        
        # Flow properties group
        props_group = QGroupBox("Flow Properties")
        props_layout = QFormLayout(props_group)
        
        props_layout.addRow("Pressure:", QLabel("— bar"))
        props_layout.addRow("Temperature:", QLabel("— °C"))
        props_layout.addRow("Enthalpy:", QLabel("— kJ/kg"))
        props_layout.addRow("Mass Flow:", QLabel("— kg/s"))
        
        self._layout.addWidget(props_group)
        self._layout.addStretch()
