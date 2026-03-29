"""
Heat exchanger components.

Hierarchy:
- HeatExchanger (ABC): Base with cold side (1 in / 1 out) and hot side (2 in / 1 out)
  - SteamWaterHeatExchanger (ABC): Steam on hot side condenses
    - Condenser: Main turbine exhaust condenser
    - FeedwaterHeater: Extraction steam heats feedwater
  - WaterWaterHeatExchanger: Liquid on both sides
"""

from __future__ import annotations

from abc import ABC
from typing import ClassVar, Optional

from .base import BalanceComponent, PressureBoundaryComponent


class HeatExchanger(PressureBoundaryComponent, BalanceComponent, ABC):
    """
    Abstract base class for heat exchangers.
    
    Has two isolated flow streams (port groups):
    - Cold side: 1 inlet, 1 outlet
    - Hot side: 2 inlets, 1 outlet
    
    Ports:
        Inputs (3):
            - inputs[0] / "cold_inlet": Cold side inlet
            - inputs[1] / "hot_inlet_1": Hot side primary inlet
            - inputs[2] / "hot_inlet_2": Hot side secondary inlet (optional)
        
        Outputs (2):
            - outputs[0] / "cold_outlet": Cold side outlet
            - outputs[1] / "hot_outlet": Hot side outlet
    
    Port Groups:
        - "cold_side": Cold stream (inputs[0] → outputs[0])
        - "hot_side": Hot stream (inputs[1,2] → outputs[1])
    """
    
    # Class-level registry of HeatExchanger instances
    _hx_instances: ClassVar[list[HeatExchanger]] = []
    
    def __init__(self, name: str = "") -> None:
        """
        Initialize heat exchanger with cold and hot sides.
        
        Args:
            name: Component instance name
        """
        super().__init__(name=name)
        
        # Cold side ports (1 in / 1 out)
        cold_in = self.add_input(name="cold_inlet", is_mandatory=True)
        cold_out = self.add_output(name="cold_outlet", is_mandatory=True)
        
        # Hot side ports (2 in / 1 out)
        hot_in_1 = self.add_input(name="hot_inlet_1", is_mandatory=True)
        hot_in_2 = self.add_input(name="hot_inlet_2", is_mandatory=False)
        hot_out = self.add_output(name="hot_outlet", is_mandatory=True)
        
        # Create isolated port groups for mass balance
        self.add_port_group(
            name="cold_side",
            inputs=[cold_in],
            outputs=[cold_out]
        )
        self.add_port_group(
            name="hot_side",
            inputs=[hot_in_1, hot_in_2],
            outputs=[hot_out]
        )
        
        # Register in HX-specific list
        HeatExchanger._hx_instances.append(self)
    
    @classmethod
    def get_all_heat_exchangers(cls) -> list[HeatExchanger]:
        """Return list of all HeatExchanger instances."""
        return cls._hx_instances.copy()
    
    def calculate_pressure_drop(self) -> Optional[float]:
        """
        Calculate pressure drop on hot side (primary path).
        
        Returns:
            Pressure drop [Pa], or None if pressures not defined
        """
        inlet_p = self.port("hot_inlet_1").pressure
        outlet_p = self.port("hot_outlet").pressure
        
        if inlet_p is None or outlet_p is None:
            return None
        
        return inlet_p - outlet_p
    
    def calculate_cold_side_pressure_drop(self) -> Optional[float]:
        """
        Calculate pressure drop on cold side.
        
        Returns:
            Pressure drop [Pa], or None if pressures not defined
        """
        inlet_p = self.port("cold_inlet").pressure
        outlet_p = self.port("cold_outlet").pressure
        
        if inlet_p is None or outlet_p is None:
            return None
        
        return inlet_p - outlet_p
    
    def solve_energy_balance(self) -> Optional[float]:
        """
        Solve overall energy balance: Q_cold = Q_hot
        
        Energy gained by cold side should equal energy lost by hot side.
        
        Returns:
            Energy balance error [W], or None if cannot be calculated
        """
        # Cold side energy change
        cold_in = self.port("cold_inlet")
        cold_out = self.port("cold_outlet")
        
        if any(x is None for x in [cold_in.mass_flow, cold_in.enthalpy,
                                    cold_out.mass_flow, cold_out.enthalpy]):
            return None
        
        q_cold = cold_out.mass_flow * cold_out.enthalpy - cold_in.mass_flow * cold_in.enthalpy
        
        # Hot side energy change
        hot_in_1 = self.port("hot_inlet_1")
        hot_in_2 = self.port("hot_inlet_2")
        hot_out = self.port("hot_outlet")
        
        if any(x is None for x in [hot_in_1.mass_flow, hot_in_1.enthalpy,
                                    hot_out.mass_flow, hot_out.enthalpy]):
            return None
        
        hot_inlet_energy = hot_in_1.mass_flow * hot_in_1.enthalpy
        
        # Add secondary inlet if connected and has values
        if hot_in_2.is_connected and hot_in_2.mass_flow is not None and hot_in_2.enthalpy is not None:
            hot_inlet_energy += hot_in_2.mass_flow * hot_in_2.enthalpy
        
        q_hot = hot_inlet_energy - hot_out.mass_flow * hot_out.enthalpy
        
        # Energy balance: heat gained by cold = heat lost by hot
        return q_cold - q_hot
    
    @property
    def heat_duty(self) -> Optional[float]:
        """
        Calculate heat transfer rate [W].
        
        Positive value = heat transferred from hot to cold side.
        """
        cold_in = self.port("cold_inlet")
        cold_out = self.port("cold_outlet")
        
        if any(x is None for x in [cold_in.mass_flow, cold_in.enthalpy,
                                    cold_out.mass_flow, cold_out.enthalpy]):
            return None
        
        return cold_out.mass_flow * cold_out.enthalpy - cold_in.mass_flow * cold_in.enthalpy


class SteamWaterHeatExchanger(HeatExchanger, ABC):
    """
    Abstract base for heat exchangers with steam on the hot side.
    
    Steam enters, condenses, and exits as liquid (condensate).
    Common for condensers and feedwater heaters.
    """
    
    # Class-level registry
    _sw_hx_instances: ClassVar[list[SteamWaterHeatExchanger]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        SteamWaterHeatExchanger._sw_hx_instances.append(self)
    
    @classmethod
    def get_all_steam_water_hx(cls) -> list[SteamWaterHeatExchanger]:
        """Return list of all SteamWaterHeatExchanger instances."""
        return cls._sw_hx_instances.copy()


class Condenser(SteamWaterHeatExchanger):
    """
    Main turbine exhaust condenser.
    
    Condenses turbine exhaust steam using cooling water.
    
    Typical connections:
        - hot_inlet_1: Turbine exhaust steam
        - hot_inlet_2: (optional) Additional steam sources
        - hot_outlet: Condensate to hotwell
        - cold_inlet: Cooling water in
        - cold_outlet: Cooling water out
    """
    
    # Class-level registry
    _condenser_instances: ClassVar[list[Condenser]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        Condenser._condenser_instances.append(self)
    
    @classmethod
    def get_all_condensers(cls) -> list[Condenser]:
        """Return list of all Condenser instances."""
        return cls._condenser_instances.copy()


class FeedwaterHeater(SteamWaterHeatExchanger):
    """
    Feedwater heater (FWT).
    
    Uses extraction steam to preheat feedwater going to boiler.
    
    Typical connections:
        - hot_inlet_1: Extraction steam from turbine
        - hot_inlet_2: (optional) Drains from higher-pressure heater
        - hot_outlet: Drains (to lower-pressure heater or condenser)
        - cold_inlet: Feedwater in (from pump or lower heater)
        - cold_outlet: Feedwater out (to boiler or higher heater)
    """
    
    # Class-level registry
    _fwh_instances: ClassVar[list[FeedwaterHeater]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        FeedwaterHeater._fwh_instances.append(self)
    
    @classmethod
    def get_all_feedwater_heaters(cls) -> list[FeedwaterHeater]:
        """Return list of all FeedwaterHeater instances."""
        return cls._fwh_instances.copy()


class WaterWaterHeatExchanger(HeatExchanger):
    """
    Water-to-water heat exchanger.
    
    Liquid water on both hot and cold sides (no phase change).
    Used for auxiliary cooling, lube oil cooling, etc.
    """
    
    # Class-level registry
    _ww_hx_instances: ClassVar[list[WaterWaterHeatExchanger]] = []
    
    def __init__(self, name: str = "") -> None:
        super().__init__(name=name)
        WaterWaterHeatExchanger._ww_hx_instances.append(self)
    
    @classmethod
    def get_all_water_water_hx(cls) -> list[WaterWaterHeatExchanger]:
        """Return list of all WaterWaterHeatExchanger instances."""
        return cls._ww_hx_instances.copy()
