"""
Port system for power plant components.

Provides Port, InputPort, OutputPort classes for component connections,
and PortGroup for defining isolated flow streams in mass/energy balances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .flow import Flow


@dataclass
class Port:
    """
    Base class for component ports.
    
    Ports hold thermodynamic state (p, T, h) and mass flow,
    and track connections to Flow objects.
    
    Attributes:
        name: Optional semantic name (e.g., "steam_inlet")
        is_mandatory: Whether this port must be connected for valid simulation
        pressure: Pressure [Pa]
        temperature: Temperature [K]
        enthalpy: Specific enthalpy [J/kg]
        mass_flow: Mass flow rate [kg/s]
    """
    name: Optional[str] = None
    is_mandatory: bool = True
    
    # Thermodynamic state
    pressure: Optional[float] = None
    temperature: Optional[float] = None
    enthalpy: Optional[float] = None
    mass_flow: Optional[float] = None
    
    # Connection state (set by Flow)
    _connected_flow: Optional[Flow] = field(default=None, repr=False)
    
    @property
    def is_connected(self) -> bool:
        """Return True if this port is connected to a Flow."""
        return self._connected_flow is not None
    
    @property
    def connected_flow(self) -> Optional[Flow]:
        """Return the Flow connected to this port, or None."""
        return self._connected_flow
    
    def set_properties(
        self,
        pressure: Optional[float] = None,
        temperature: Optional[float] = None,
        enthalpy: Optional[float] = None,
        mass_flow: Optional[float] = None
    ) -> None:
        """Set multiple thermodynamic properties at once."""
        if pressure is not None:
            self.pressure = pressure
        if temperature is not None:
            self.temperature = temperature
        if enthalpy is not None:
            self.enthalpy = enthalpy
        if mass_flow is not None:
            self.mass_flow = mass_flow
    
    def clear_properties(self) -> None:
        """Reset all thermodynamic properties to None."""
        self.pressure = None
        self.temperature = None
        self.enthalpy = None
        self.mass_flow = None


@dataclass
class InputPort(Port):
    """
    Input port - receives flow from an upstream component.
    
    Connected to the inlet_port side of a Flow object.
    """
    pass


@dataclass
class OutputPort(Port):
    """
    Output port - sends flow to a downstream component.
    
    Connected to the outlet_port side of a Flow object.
    """
    pass


@dataclass
class PortGroup:
    """
    A group of ports that form an isolated flow stream.
    
    Used for mass/energy balance calculations where flows don't mix
    (e.g., cold side vs hot side of a heat exchanger).
    
    Attributes:
        name: Identifier for this group (e.g., "cold_side", "hot_side")
        inputs: List of input ports in this group
        outputs: List of output ports in this group
    """
    name: str
    inputs: list[InputPort] = field(default_factory=list)
    outputs: list[OutputPort] = field(default_factory=list)
    
    def get_mass_balance_error(self) -> Optional[float]:
        """
        Calculate mass balance error for this port group.
        
        Returns:
            Error = sum(inlet mass flows) - sum(outlet mass flows)
            Returns None if any port has undefined mass flow.
        """
        inlet_flows = [p.mass_flow for p in self.inputs]
        outlet_flows = [p.mass_flow for p in self.outputs]
        
        if None in inlet_flows or None in outlet_flows:
            return None
        
        return sum(inlet_flows) - sum(outlet_flows)
    
    def is_balanced(self, tolerance: float = 1e-6) -> Optional[bool]:
        """
        Check if mass balance is satisfied within tolerance.
        
        Returns:
            True if balanced, False if not, None if cannot determine.
        """
        error = self.get_mass_balance_error()
        if error is None:
            return None
        return abs(error) <= tolerance
    
    def all_connected(self, mandatory_only: bool = True) -> bool:
        """
        Check if all ports in this group are connected.
        
        Args:
            mandatory_only: If True, only check mandatory ports.
        """
        ports = self.inputs + self.outputs
        if mandatory_only:
            ports = [p for p in ports if p.is_mandatory]
        return all(p.is_connected for p in ports)
