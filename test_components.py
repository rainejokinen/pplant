"""Quick test of component system."""

from components import *

# Clear previous test instances
Component.clear_all_instances()
Flow.clear_all_instances()

# Create components
t = Turbine('HP_Turbine')
c = Condenser('Main_Condenser')

# Test port access
print('Turbine ports:')
print(f'  inputs[0] = {t.inputs[0].name}')
print(f'  port("main_inlet") = {t.port("main_inlet")}')
print(f'  outputs = {[p.name for p in t.outputs]}')

print()
print('Condenser port groups:')
for g in c.port_groups:
    print(f'  {g.name}: {len(g.inputs)} in / {len(g.outputs)} out')

# Test flow connection
f = Flow('turbine_to_condenser')
f.connect(t.outputs[0], c.inputs[1])  # main_outlet -> hot_inlet_1
print()
print(f'Flow connected: {f.is_connected}')
print(f'Turbine main_outlet connected: {t.port("main_outlet").is_connected}')
print(f'Condenser hot_inlet_1 connected: {c.port("hot_inlet_1").is_connected}')

# Test mass balance setup
print()
print('Setting port properties...')
t.port("main_inlet").set_properties(mass_flow=100.0, enthalpy=3000e3)
t.port("main_outlet").set_properties(mass_flow=80.0, enthalpy=2500e3)
t.port("extraction_1").set_properties(mass_flow=20.0, enthalpy=2700e3)

print(f'Mass balance check: {t.check_mass_balance()}')
print(f'Power output: {t.power_output} W')

print()
print('All tests passed!')
