from __future__ import annotations

from nicegui import ui

from gui.tabs.species import species_tab

# https://quasar.dev/layout/grid/flex-playground

with ui.tabs().classes('w-full') as tabs:
    zero = ui.tab('Custom Characteristics')
    one = ui.tab('Species')
    two = ui.tab('Sophont')
    three = ui.tab('Package Maker')
with ui.tab_panels(tabs, value=one).classes('w-full'):
    species_tab(one)

    with ui.tab_panel(three):
        ui.label('Package Maker')

ui.run(dark=True)