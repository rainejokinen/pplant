"""
Mixer and Splitter components.

- Mixer: Combines 2 inlet streams into 1 outlet stream
- Splitter: Divides 1 inlet stream into 2 outlet streams

Both are balance components only (no pressure boundary behavior).
"""

from __future__ import annotations

from typing import ClassVar, Optional

from .base import BalanceComponent, Component


class Mixer(BalanceComponent):
    """
    Flow mixer - combines 2 inlet streams into 1 outlet.
    
    Performs adiabatic mixing of two streams. Outlet enthalpy is
    determined by mass-weighted average of inlet enthalpies.
    
    Ports:
        Inputs (2):
            - inputs[0] / "inlet_1": First inlet stream
            - inputs[1] / "inlet_2": Second inlet stream
        
        Outputs (1):
            - outputs[0] / "outlet": Mixed outlet stream
    
    Port Groups:
        - "main": All ports in single mixing flow
    """
    
    # Class-level registry of Mixer instances
    _mixer_instances: ClassVar[list[Mixer]] = []
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize mixer with 2 inlets and 1 outlet.
        
        Args:
            name: Component instance name
        """
        # Initialize Component directly (skip PressureBoundary)
        Component.__init__(self, name=name)
        BalanceComponent._balance_instances.append(self)
        
        # Create ports (2 in / 1 out)
        self.add_input(name="inlet_1", is_mandatory=True)
        self.add_input(name="inlet_2", is_mandatory=True)
        self.add_output(name="outlet", is_mandatory=True)
        
        # Single port group - all streams mix
        self.add_port_group(
            name="main",
            inputs=self._inputs.copy(),
            outputs=self._outputs.copy()
        )
        
        # Register in mixer-specific list
        Mixer._mixer_instances.append(self)
    
    @classmethod
    def get_all_mixers(cls) -> list[Mixer]:
        """Return list of all Mixer instances."""
        return cls._mixer_instances.copy()
    
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve energy balance: m1*h1 + m2*h2 = m_out*h_out
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        inlet_1 = self.port("inlet_1")
        inlet_2 = self.port("inlet_2")
        outlet = self.port("outlet")
        
        if any(x is None for x in [inlet_1.mass_flow, inlet_1.enthalpy,
                                    inlet_2.mass_flow, inlet_2.enthalpy,
                                    outlet.mass_flow, outlet.enthalpy]):
            return None
        
        inlet_energy = (inlet_1.mass_flow * inlet_1.enthalpy + 
                       inlet_2.mass_flow * inlet_2.enthalpy)
        outlet_energy = outlet.mass_flow * outlet.enthalpy
        
        return inlet_energy - outlet_energy
    
    def calculate_outlet_enthalpy(self) -> Optional[float]:
        """
        Calculate mixed outlet enthalpy from inlet streams.
        
        Returns:
            Outlet enthalpy [J/kg], or None if cannot be calculated
        """
        inlet_1 = self.port("inlet_1")
        inlet_2 = self.port("inlet_2")
        
        if any(x is None for x in [inlet_1.mass_flow, inlet_1.enthalpy,
                                    inlet_2.mass_flow, inlet_2.enthalpy]):
            return None
        
        total_mass = inlet_1.mass_flow + inlet_2.mass_flow
        if total_mass == 0:
            return None
        
        return (inlet_1.mass_flow * inlet_1.enthalpy + 
                inlet_2.mass_flow * inlet_2.enthalpy) / total_mass


class Splitter(BalanceComponent):
    """
    Flow splitter - divides 1 inlet stream into 2 outlets.
    
    Both outlet streams have the same thermodynamic state (p, T, h)
    as the inlet; only mass flow is divided.
    
    Ports:
        Inputs (1):
            - inputs[0] / "inlet": Inlet stream
        
        Outputs (2):
            - outputs[0] / "outlet_1": First outlet stream
            - outputs[1] / "outlet_2": Second outlet stream
    
    Port Groups:
        - "main": All ports in single splitting flow
    
    Attributes:
        split_fraction: Fraction of flow to outlet_1 (0.0-1.0)
    """
    
    # Class-level registry of Splitter instances
    _splitter_instances: ClassVar[list[Splitter]] = []
    
    def __init__(self, name: str = "", split_fraction: float = 0.5) -> None:
        """
        Initialize splitter with 1 inlet and 2 outlets.
        
        Args:
            name: Component instance name
            split_fraction: Fraction of inlet flow going to outlet_1 (default 0.5)
        """
        # Initialize Component directly (skip PressureBoundary)
        Component.__init__(self, name=name)
        BalanceComponent._balance_instances.append(self)
        
        self.split_fraction = split_fraction
        
        # Create ports (1 in / 2 out)
        self.add_input(name="inlet", is_mandatory=True)
        self.add_output(name="outlet_1", is_mandatory=True)
        self.add_output(name="outlet_2", is_mandatory=True)
        
        # Single port group
        self.add_port_group(
            name="main",
            inputs=self._inputs.copy(),
            outputs=self._outputs.copy()
        )
        
        # Register in splitter-specific list
        Splitter._splitter_instances.append(self)
    
    @classmethod
    def get_all_splitters(cls) -> list[Splitter]:
        """Return list of all Splitter instances."""
        return cls._splitter_instances.copy()
    
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve energy balance: m_in*h_in = m1*h1 + m2*h2
        
        Since h1 = h2 = h_in for ideal splitter, this reduces to mass balance.
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        inlet = self.port("inlet")
        outlet_1 = self.port("outlet_1")
        outlet_2 = self.port("outlet_2")
        
        if any(x is None for x in [inlet.mass_flow, inlet.enthalpy,
                                    outlet_1.mass_flow, outlet_1.enthalpy,
                                    outlet_2.mass_flow, outlet_2.enthalpy]):
            return None
        
        inlet_energy = inlet.mass_flow * inlet.enthalpy
        outlet_energy = (outlet_1.mass_flow * outlet_1.enthalpy + 
                        outlet_2.mass_flow * outlet_2.enthalpy)
        
        return inlet_energy - outlet_energy
    
    def distribute_inlet_properties(self) -> None:
        """
        Copy inlet thermodynamic properties to both outlets.
        
        Splitter outlets have same p, T, h as inlet; only mass flow differs.
        """
        inlet = self.port("inlet")
        
        for outlet in self._outputs:
            outlet.pressure = inlet.pressure
            outlet.temperature = inlet.temperature
            outlet.enthalpy = inlet.enthalpy
    
    def apply_split_fraction(self) -> None:
        """
        Apply split_fraction to calculate outlet mass flows from inlet.
        """
        inlet = self.port("inlet")
        if inlet.mass_flow is None:
            return
        
        self.port("outlet_1").mass_flow = inlet.mass_flow * self.split_fraction
        self.port("outlet_2").mass_flow = inlet.mass_flow * (1.0 - self.split_fraction)
