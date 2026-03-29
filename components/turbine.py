"""
Turbine component.

A turbine expands steam/gas to produce work. It has 2 inlets and 3 outlets
(main outlet + extraction points).
"""

from __future__ import annotations

from typing import ClassVar, Optional

from .base import BalanceComponent, PressureBoundaryComponent


class Turbine(PressureBoundaryComponent, BalanceComponent):
    """
    Steam/gas turbine with expansion and extraction points.
    
    Ports:
        Inputs (2):
            - inputs[0] / "main_inlet": Main steam inlet
            - inputs[1] / "reheat_inlet": Reheat or secondary inlet
        
        Outputs (3):
            - outputs[0] / "main_outlet": Main exhaust
            - outputs[1] / "extraction_1": First extraction point
            - outputs[2] / "extraction_2": Second extraction point
    
    Port Groups:
        - "main": All ports in single flow stream (steam expands through all)
    """
    
    # Class-level registry of Turbine instances
    _turbine_instances: ClassVar[list[Turbine]] = []
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize turbine with 2 inlets and 3 outlets.
        
        Args:
            name: Component instance name
        """
        super().__init__(name=name)
        
        # Create input ports (2)
        self.add_input(name="main_inlet", is_mandatory=True)
        self.add_input(name="reheat_inlet", is_mandatory=False)
        
        # Create output ports (3)
        self.add_output(name="main_outlet", is_mandatory=True)
        self.add_output(name="extraction_1", is_mandatory=False)
        self.add_output(name="extraction_2", is_mandatory=False)
        
        # Single port group - all ports in same flow stream
        self.add_port_group(
            name="main",
            inputs=self._inputs.copy(),
            outputs=self._outputs.copy()
        )
        
        # Register in turbine-specific list
        Turbine._turbine_instances.append(self)
    
    @classmethod
    def get_all_turbines(cls) -> list[Turbine]:
        """Return list of all Turbine instances."""
        return cls._turbine_instances.copy()
    
    def calculate_pressure_drop(self) -> Optional[float]:
        """
        Calculate pressure drop across turbine (inlet to main outlet).
        
        Returns:
            Pressure drop [Pa], or None if pressures not defined
        """
        inlet_p = self.port("main_inlet").pressure
        outlet_p = self.port("main_outlet").pressure
        
        if inlet_p is None or outlet_p is None:
            return None
        
        return inlet_p - outlet_p
    
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve energy balance: sum(m_in * h_in) - sum(m_out * h_out) - W = 0
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        # Calculate inlet energy
        inlet_energy = 0.0
        for port in self._inputs:
            if port.mass_flow is None or port.enthalpy is None:
                if port.is_mandatory or port.is_connected:
                    return None
            elif port.mass_flow is not None and port.enthalpy is not None:
                inlet_energy += port.mass_flow * port.enthalpy
        
        # Calculate outlet energy
        outlet_energy = 0.0
        for port in self._outputs:
            if port.mass_flow is None or port.enthalpy is None:
                if port.is_mandatory or port.is_connected:
                    return None
            elif port.mass_flow is not None and port.enthalpy is not None:
                outlet_energy += port.mass_flow * port.enthalpy
        
        # Energy balance error (positive = more energy in than out = work produced)
        return inlet_energy - outlet_energy
    
    @property
    def power_output(self) -> Optional[float]:
        """
        Calculate turbine power output [W].
        
        This is the energy extracted from the steam, equal to the
        energy balance (inlet energy - outlet energy).
        """
        return self.solve_energy_balance()
