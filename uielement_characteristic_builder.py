from __future__ import annotations

from nicegui import ui

from gui import styles
from gui.element.popchip import Popchip
from gui.forms.characteristic_builder import CharacteristicBuilder

# https://quasar.dev/layout/grid/flex-playground

with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Characteristic Builder UI Element Development").classes("text-sm font-thin q-ma-none")

with ui.row().classes(styles.TAB_ROW):

            # LEFT COLUMN ===================== PACKAGE BUILDER
            with ui.column().classes(styles.TAB_COLUMN_LEFT) as popchip_builder_container:
                builder = CharacteristicBuilder()
            # RIGHT COLUMN ==================== PACKAGE COLLECTION
            with ui.column().classes(styles.TAB_COLUMN_RIGHT) as popchip_collection_area:
                ui.label("Popchip Collection Area")
                # chip = Popchip()

ui.run(dark=True)
