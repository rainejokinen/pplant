"""
Flow connections between component ports.

A Flow connects an OutputPort from one component to an InputPort of another,
enabling property propagation and connection tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, Optional

from .ports import InputPort, OutputPort


@dataclass
class Flow:
    """
    Represents a flow connection between two ports.
    
    Connects an OutputPort (upstream) to an InputPort (downstream).
    Maintains connection state on both ports and can propagate properties.
    
    Attributes:
        name: Optional name for this flow
        outlet_port: The upstream output port (source)
        inlet_port: The downstream input port (destination)
    """
    
    # Class-level registry of all Flow instances
    _instances: ClassVar[list[Flow]] = []
    
    name: Optional[str] = None
    outlet_port: Optional[OutputPort] = None
    inlet_port: Optional[InputPort] = None
    _is_connected: bool = field(default=False, repr=False)
    
    def __post_init__(self) -> None:
        """Register this flow instance."""
        Flow._instances.append(self)
        
        # Auto-connect if both ports provided
        if self.outlet_port is not None and self.inlet_port is not None:
            self.connect(self.outlet_port, self.inlet_port)
    
    @classmethod
    def get_all_flows(cls) -> list[Flow]:
        """Return list of all Flow instances."""
        return cls._instances.copy()
    
    @classmethod
    def clear_all_instances(cls) -> None:
        """Clear all Flow instances. Useful for testing."""
        cls._instances.clear()
    
    @property
    def is_connected(self) -> bool:
        """Return True if this flow is connected to both ports."""
        return self._is_connected
    
    def connect(self, outlet_port: OutputPort, inlet_port: InputPort) -> None:
        """
        Connect this flow between two ports.
        
        Args:
            outlet_port: The upstream output port
            inlet_port: The downstream input port
            
        Raises:
            TypeError: If ports are wrong type
            ValueError: If either port is already connected
        """
        if not isinstance(outlet_port, OutputPort):
            raise TypeError(f"outlet_port must be OutputPort, got {type(outlet_port)}")
        if not isinstance(inlet_port, InputPort):
            raise TypeError(f"inlet_port must be InputPort, got {type(inlet_port)}")
        
        if outlet_port.is_connected:
            raise ValueError(f"OutputPort '{outlet_port.name}' is already connected")
        if inlet_port.is_connected:
            raise ValueError(f"InputPort '{inlet_port.name}' is already connected")
        
        self.outlet_port = outlet_port
        self.inlet_port = inlet_port
        
        # Update port connection state
        outlet_port._connected_flow = self
        inlet_port._connected_flow = self
        
        self._is_connected = True
    
    def disconnect(self) -> None:
        """
        Disconnect this flow from its ports.
        
        Clears connection state on both ports.
        """
        if self.outlet_port is not None:
            self.outlet_port._connected_flow = None
        if self.inlet_port is not None:
            self.inlet_port._connected_flow = None
        
        self.outlet_port = None
        self.inlet_port = None
        self._is_connected = False
    
    def propagate_properties(self, direction: str = "downstream") -> None:
        """
        Copy thermodynamic properties along the flow direction.
        
        Args:
            direction: "downstream" (outlet→inlet) or "upstream" (inlet→outlet)
        """
        if not self._is_connected:
            return
        
        if direction == "downstream":
            source, target = self.outlet_port, self.inlet_port
        elif direction == "upstream":
            source, target = self.inlet_port, self.outlet_port
        else:
            raise ValueError(f"direction must be 'downstream' or 'upstream', got '{direction}'")
        
        target.set_properties(
            pressure=source.pressure,
            temperature=source.temperature,
            enthalpy=source.enthalpy,
            mass_flow=source.mass_flow
        )
    
    def __repr__(self) -> str:
        outlet_name = self.outlet_port.name if self.outlet_port else "None"
        inlet_name = self.inlet_port.name if self.inlet_port else "None"
        return f"Flow(name='{self.name}', {outlet_name} → {inlet_name}, connected={self._is_connected})"
