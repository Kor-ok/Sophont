from __future__ import annotations

from nicegui import ui

from gui.tabs.sophont import sophont_tab
from gui.tabs.species import species_tab

# https://quasar.dev/layout/grid/flex-playground

with ui.header().classes('items-center justify-center bg-deep-orange-10 q-ma-none'):
    ui.label('DEV NOTE: GUI State Management and Character Card swapping is currently incomplete').classes('text-sm font-thin q-ma-none')
with ui.tabs().classes('w-full') as tabs:
    zero = ui.tab('Custom Characteristics')
    one = ui.tab('Species')
    two = ui.tab('Sophont')
    three = ui.tab('Package Maker')
with ui.tab_panels(tabs, value=two).classes('w-full'):
    species_tab(one)
    sophont_tab(two)

ui.run(dark=True)