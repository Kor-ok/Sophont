from __future__ import annotations

from nicegui import ui

from gui import styles
from gui.forms.package_builder import PackageBuilder

# https://quasar.dev/layout/grid/flex-playground

with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Package Builder UI Element Development").classes("text-sm font-thin q-ma-none")

with ui.row().classes(styles.TAB_ROW):
            builder: ui.column
            collection: ui.column

            # LEFT COLUMN ===================== PACKAGE BUILDER
            with ui.column().classes(styles.TAB_COLUMN_LEFT) as package_builder_container:
                package_builder = PackageBuilder(
                    on_package_built=lambda pkg: None,)
            # RIGHT COLUMN ==================== PACKAGE COLLECTION
            with ui.column().classes(styles.TAB_COLUMN_RIGHT) as packages_collection_container:
                ui.label("Package Collection Area")

ui.run(dark=True)
