"""
Valve component.

A valve controls flow and creates a pressure drop. It has 1 inlet and 1 outlet.
"""

from __future__ import annotations

from typing import ClassVar, Optional

from .base import BalanceComponent, PressureBoundaryComponent


class Valve(PressureBoundaryComponent, BalanceComponent):
    """
    Flow control valve with pressure drop.
    
    Ports:
        Inputs (1):
            - inputs[0] / "inlet": Upstream connection
        
        Outputs (1):
            - outputs[0] / "outlet": Downstream connection
    
    Port Groups:
        - "main": Single flow stream through valve
    
    Attributes:
        opening: Valve opening fraction (0.0 = closed, 1.0 = fully open)
    """
    
    # Class-level registry of Valve instances
    _valve_instances: ClassVar[list[Valve]] = []
    
    def __init__(self, name: str = "", opening: float = 1.0) -> None:
        """
        Initialize valve with 1 inlet and 1 outlet.
        
        Args:
            name: Component instance name
            opening: Initial valve opening (0.0-1.0)
        """
        super().__init__(name=name)
        
        self.opening = opening
        
        # Create ports (1 in / 1 out)
        self.add_input(name="inlet", is_mandatory=True)
        self.add_output(name="outlet", is_mandatory=True)
        
        # Single port group
        self.add_port_group(
            name="main",
            inputs=self._inputs.copy(),
            outputs=self._outputs.copy()
        )
        
        # Register in valve-specific list
        Valve._valve_instances.append(self)
    
    @classmethod
    def get_all_valves(cls) -> list[Valve]:
        """Return list of all Valve instances."""
        return cls._valve_instances.copy()
    
    def calculate_pressure_drop(self) -> Optional[float]:
        """
        Calculate pressure drop across valve.
        
        Returns:
            Pressure drop [Pa], or None if pressures not defined
        """
        inlet_p = self.port("inlet").pressure
        outlet_p = self.port("outlet").pressure
        
        if inlet_p is None or outlet_p is None:
            return None
        
        return inlet_p - outlet_p
    
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve energy balance: m_in * h_in - m_out * h_out = 0 (isenthalpic)
        
        For an ideal valve, enthalpy is conserved (no work, adiabatic).
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        inlet = self.port("inlet")
        outlet = self.port("outlet")
        
        if any(x is None for x in [inlet.mass_flow, inlet.enthalpy, 
                                    outlet.mass_flow, outlet.enthalpy]):
            return None
        
        return inlet.mass_flow * inlet.enthalpy - outlet.mass_flow * outlet.enthalpy
    
    @property
    def is_closed(self) -> bool:
        """Return True if valve is fully closed."""
        return self.opening <= 0.0
    
    @property
    def is_fully_open(self) -> bool:
        """Return True if valve is fully open."""
        return self.opening >= 1.0
