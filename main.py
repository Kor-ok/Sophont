from __future__ import annotations

import sys

import uielement_character_card

# from nicegui import ui

# from gui.tabs.package_builder import package_builder_tab

# # https://quasar.dev/layout/grid/flex-playground

# with ui.header().classes('items-center justify-center bg-deep-orange-10 q-ma-none'):
#     ui.label('DEV NOTE: Most GUI Elements are under development but underlying data model is functional').classes('text-sm font-thin q-ma-none')
# with ui.tabs().classes('w-full') as tabs:
#     zero = ui.tab('Custom Characteristics')
#     one = ui.tab('Species')
#     two = ui.tab('Sophont')
#     three = ui.tab('Package Builder')
# with ui.tab_panels(tabs, value=three).classes('w-full'):
#     package_builder_tab(three)

# ui.run(dark=True)


# For now just run uielement_character_card.py
if __name__ == "__main__":
    sys.path.insert(0, ".")
    import uielement_character_card

    uielement_character_card.ui.run(dark=True)

