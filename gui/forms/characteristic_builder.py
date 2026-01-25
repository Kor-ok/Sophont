from __future__ import annotations

from collections.abc import Callable
from typing import Optional

from nicegui import ui

from game.characteristic import Characteristic
from game.mappings.data import FullCode
from game.mappings.set import ATTRIBUTES
from gui.forms.attribute_builder_base import (
    AttributeBuilderBase,
    AttributeType,
    SelectedAttributeDisplayBase,
)


def _master_category_display_option_builder(code: int) -> str:
    aliases = ATTRIBUTES.characteristics.master_category_name_aliases_dict.get(
        code, ("Unknown",)
    )
    return f"{code} - {aliases[0]}"


def _event_value(e: object) -> Optional[object]:
    """Extract `value` from NiceGUI's event payload in a permissive way."""
    selected = getattr(e, "value", None)
    if selected is not None:
        return selected

    args = getattr(e, "args", None)
    if isinstance(args, dict):
        return args.get("value")
    if isinstance(args, (list, tuple)) and args:
        return args[-1]
    return None


class SelectedCharacteristicDisplay(SelectedAttributeDisplayBase):
    """Display for a selected Characteristic."""

    def __init__(self, full_code: FullCode) -> None:

        canonical, aliases = ATTRIBUTES.characteristics.get_aliases(full_code)
        with ui.column().classes("q-gutter-xs"):
            ui.label("Characteristic Selected:").classes("text-bold")
            ui.label(f"Name: {canonical}")
            if aliases:
                ui.label(f"Aliases: {', '.join(aliases)}").classes("text-grey")

            ui.separator()
            ui.label(f"UPP Index: {full_code[0]}")
            ui.label(f"Subtype: {full_code[1]}")
            ui.label(f"Master Category: {full_code[2]}")


class CharacteristicBuilder(AttributeBuilderBase):
    """Form to build a Characteristic selection."""

    def __init__(
        self,
        *,
        attribute_type: AttributeType = AttributeType.CHARACTERISTIC,
        on_attribute_built: Optional[Callable[[Characteristic], None]] = None,
    ) -> None:
        # super().__init__()
        self.on_attribute_built = on_attribute_built
        self.classes("q-pa-md").props("flat outlined")

        self._attribute_display_row: ui.row | None = None
        self._selected_full_code: FullCode | None = None

        collection = ATTRIBUTES.characteristics.get_all()

        self._valid_codes: set[FullCode] = {code for _, code in collection}
        
        upp_options = sorted({code[0] for _, code in collection})
        sub_options = sorted({code[1] for _, code in collection})
        master_category_codes = sorted({code[2] for _, code in collection})
        master_category_options: dict[int, str] = {
            code: _master_category_display_option_builder(code)
            for code in master_category_codes
        }
        
        with ui.row() as attribute_display_row:
            self._attribute_display_row = attribute_display_row
            ui.label("No Characteristic Selected").classes("text-gray-500 italic")

        self._upp_index_select = (
            ui.select(
                label="UPP Index",
                options=upp_options,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full")
            .props("clearable")
        )

        self._subtype_select = (
            ui.select(
                label="Subtype",
                options=sub_options,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full q-mt-md")
            .props("clearable")
        )

        self._master_category_select = (
            ui.select(
                label="Master Category",
                options=master_category_options,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full q-mt-md")
            .props("clearable")
        )

        ui.button(
            "Save New Characteristic",
            color="dark",
            on_click=self._save_characteristic,
        ).classes("q-mt-md")

        self._render_selected_characteristic()

    def _on_any_select_changed(self, e) -> None:
        # Ensure we always compute from the current widget values.
        _ = _event_value(e)
        self._selected_full_code = self._compute_selected_full_code()
        self._render_selected_characteristic()

    def _compute_selected_full_code(self) -> FullCode | None:
        upp = self._upp_index_select.value
        subtype = self._subtype_select.value
        master_category = self._master_category_select.value

        if upp is None or subtype is None or master_category is None:
            return None

        try:
            full_code: FullCode = (int(upp), int(subtype), int(master_category))
        except (TypeError, ValueError):
            return None

        if full_code not in self._valid_codes:
            return None
        return full_code

    def _render_selected_characteristic(self) -> None:
        if self._attribute_display_row is None:
            return

        self._attribute_display_row.clear()

        full_code = self._selected_full_code
        with self._attribute_display_row:
            if full_code is None:
                ui.label("No Characteristic Selected").classes("text-gray-500 italic")
                ui.label(
                    "Pick UPP Index + Subtype + Master Category (valid combination)."
                ).classes("text-gray-500")
                return

            SelectedCharacteristicDisplay(full_code)

    def _save_characteristic(self) -> None:
        full_code = self._selected_full_code
        if full_code is None:
            ui.notify("Select a valid characteristic first.", type="warning")
            return

        characteristic = Characteristic.by_code(full_code)
        if self.on_attribute_built is not None:
            self.on_attribute_built(characteristic)

        canonical, _aliases = characteristic.get_name()
        ui.notify(f"Saved: {canonical}", type="positive")