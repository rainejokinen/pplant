"""
Base classes for power plant components.

Provides the ABC hierarchy:
- Component: Base class with port management and instance registry
- PressureBoundaryComponent: Components that define pressure boundaries
- BalanceComponent: Components with mass/energy balance equations

Concrete components inherit from both PressureBoundaryComponent and BalanceComponent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Optional

from .ports import InputPort, OutputPort, Port, PortGroup


class Component(ABC):
    """
    Abstract base class for all power plant components.
    
    Manages ports (inputs/outputs), optional port naming, port groups
    for isolated flow streams, and a class-level instance registry.
    
    Attributes:
        name: Component instance name
        _inputs: List of input ports (access via inputs property)
        _outputs: List of output ports (access via outputs property)
        _port_names: Dict mapping names to ports for semantic access
        _port_groups: List of PortGroups for mass/energy balance
    """
    
    # Class-level registry of all Component instances
    _instances: ClassVar[list[Component]] = []
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize component with empty port lists.
        
        Args:
            name: Optional name for this component instance
        """
        self.name = name
        self._inputs: list[InputPort] = []
        self._outputs: list[OutputPort] = []
        self._port_names: dict[str, Port] = {}
        self._port_groups: list[PortGroup] = []
        
        # Register this instance
        Component._instances.append(self)
    
    @classmethod
    def get_all_components(cls) -> list[Component]:
        """Return list of all Component instances."""
        return cls._instances.copy()
    
    @classmethod
    def clear_all_instances(cls) -> None:
        """Clear all instance registries. Useful for testing."""
        Component._instances.clear()
        PressureBoundaryComponent._pb_instances.clear()
        BalanceComponent._balance_instances.clear()
    
    @property
    def inputs(self) -> list[InputPort]:
        """List of input ports. Access by index: component.inputs[0]"""
        return self._inputs
    
    @property
    def outputs(self) -> list[OutputPort]:
        """List of output ports. Access by index: component.outputs[0]"""
        return self._outputs
    
    @property
    def port_groups(self) -> list[PortGroup]:
        """List of port groups for mass/energy balance calculations."""
        return self._port_groups
    
    def add_input(self, name: Optional[str] = None, is_mandatory: bool = True) -> InputPort:
        """
        Add an input port to this component.
        
        Args:
            name: Optional semantic name for the port
            is_mandatory: Whether this port must be connected
            
        Returns:
            The created InputPort
        """
        port = InputPort(name=name, is_mandatory=is_mandatory)
        self._inputs.append(port)
        if name:
            self._port_names[name] = port
        return port
    
    def add_output(self, name: Optional[str] = None, is_mandatory: bool = True) -> OutputPort:
        """
        Add an output port to this component.
        
        Args:
            name: Optional semantic name for the port
            is_mandatory: Whether this port must be connected
            
        Returns:
            The created OutputPort
        """
        port = OutputPort(name=name, is_mandatory=is_mandatory)
        self._outputs.append(port)
        if name:
            self._port_names[name] = port
        return port
    
    def port(self, name: str) -> Port:
        """
        Get a port by its semantic name.
        
        Args:
            name: The port name (e.g., "steam_inlet")
            
        Returns:
            The Port with that name
            
        Raises:
            KeyError: If no port with that name exists
        """
        return self._port_names[name]
    
    def add_port_group(self, name: str, inputs: list[InputPort], outputs: list[OutputPort]) -> PortGroup:
        """
        Create a port group for isolated flow stream calculations.
        
        Args:
            name: Group identifier (e.g., "cold_side")
            inputs: Input ports in this group
            outputs: Output ports in this group
            
        Returns:
            The created PortGroup
        """
        group = PortGroup(name=name, inputs=inputs, outputs=outputs)
        self._port_groups.append(group)
        return group
    
    def validate_connections(self, mandatory_only: bool = True) -> bool:
        """
        Check if all required ports are connected.
        
        Args:
            mandatory_only: If True, only check mandatory ports
            
        Returns:
            True if all required ports are connected
        """
        all_ports = self._inputs + self._outputs
        if mandatory_only:
            all_ports = [p for p in all_ports if p.is_mandatory]
        return all(p.is_connected for p in all_ports)
    
    def get_unconnected_ports(self, mandatory_only: bool = True) -> list[Port]:
        """
        Get list of unconnected ports.
        
        Args:
            mandatory_only: If True, only return unconnected mandatory ports
            
        Returns:
            List of unconnected Port objects
        """
        all_ports = self._inputs + self._outputs
        if mandatory_only:
            all_ports = [p for p in all_ports if p.is_mandatory]
        return [p for p in all_ports if not p.is_connected]
    
    def distribute_properties(
        self,
        direction: str,
        pressure: Optional[float] = None,
        temperature: Optional[float] = None,
        enthalpy: Optional[float] = None,
        mass_flow: Optional[float] = None,
        port_group: Optional[str] = None
    ) -> None:
        """
        Distribute properties to all ports in a direction or group.
        
        Args:
            direction: "input" or "output"
            pressure: Pressure to set [Pa]
            temperature: Temperature to set [K]
            enthalpy: Enthalpy to set [J/kg]
            mass_flow: Mass flow to set [kg/s]
            port_group: If specified, only apply to ports in this group
        """
        if direction == "input":
            ports = self._inputs
        elif direction == "output":
            ports = self._outputs
        else:
            raise ValueError(f"direction must be 'input' or 'output', got '{direction}'")
        
        # Filter by port group if specified
        if port_group:
            group = next((g for g in self._port_groups if g.name == port_group), None)
            if group is None:
                raise ValueError(f"No port group named '{port_group}'")
            group_ports = set(group.inputs + group.outputs)
            ports = [p for p in ports if p in group_ports]
        
        for port in ports:
            port.set_properties(
                pressure=pressure,
                temperature=temperature,
                enthalpy=enthalpy,
                mass_flow=mass_flow
            )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', inputs={len(self._inputs)}, outputs={len(self._outputs)})"


class PressureBoundaryComponent(Component, ABC):
    """
    Abstract base for components that define pressure boundaries.
    
    Pressure boundary components set/modify pressure in the system
    (e.g., turbines, valves, pumps).
    """
    
    # Class-level registry of PressureBoundaryComponent instances
    _pb_instances: ClassVar[list[PressureBoundaryComponent]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        PressureBoundaryComponent._pb_instances.append(self)
    
    @classmethod
    def get_all_pressure_boundary(cls) -> list[PressureBoundaryComponent]:
        """Return list of all PressureBoundaryComponent instances."""
        return cls._pb_instances.copy()
    
    @abstractmethod
    def calculate_pressure_drop(self) -> Optional[float]:
        """
        Calculate pressure drop across this component.
        
        Returns:
            Pressure drop [Pa], or None if cannot be calculated
        """
        pass


class BalanceComponent(Component, ABC):
    """
    Abstract base for components with mass/energy balance equations.
    
    Balance components conserve mass and energy across their port groups.
    """
    
    # Class-level registry of BalanceComponent instances
    _balance_instances: ClassVar[list[BalanceComponent]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        BalanceComponent._balance_instances.append(self)
    
    @classmethod
    def get_all_balance(cls) -> list[BalanceComponent]:
        """Return list of all BalanceComponent instances."""
        return cls._balance_instances.copy()
    
    def solve_mass_balance(self) -> dict[str, Optional[float]]:
        """
        Solve mass balance for each port group.
        
        Returns:
            Dict mapping group name to mass balance error (None if undefined)
        """
        results = {}
        for group in self._port_groups:
            results[group.name] = group.get_mass_balance_error()
        return results
    
    def check_mass_balance(self, tolerance: float = 1e-6) -> dict[str, Optional[bool]]:
        """
        Check if mass balance is satisfied for each port group.
        
        Args:
            tolerance: Acceptable error [kg/s]
            
        Returns:
            Dict mapping group name to balance status (True/False/None)
        """
        results = {}
        for group in self._port_groups:
            results[group.name] = group.is_balanced(tolerance)
        return results
    
    @abstractmethod
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve energy balance for this component.
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        pass
