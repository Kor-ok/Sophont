from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Optional

from nicegui import ui

from game.mappings.data import FullCode
from game.mappings.set import ATTRIBUTES


class AttributeType(Enum):
    CHARACTERISTIC = ATTRIBUTES.characteristics
    SKILL = ATTRIBUTES.skills

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

class SelectedAttributeDisplayBase(ui.card):
    """Display for a selected Attribute."""

    def __init__(self, full_code: FullCode) -> None:
        super().__init__()
        self.classes("q-pa-md").props("flat outlined")

class AttributeBuilderBase(ui.card):
    """Form to build an Attribute selection."""

    def __init__(
        self,
        *,
        attribute_type: AttributeType,
        on_attribute_built: Optional[Callable[[object], None]] = None,
    ) -> None:
        super().__init__()
        self.classes("q-pa-md").props("flat outlined")

        self._on_attribute_built = on_attribute_built

        self._attribute_display_row: ui.row | None = None
        self._selected_full_code: FullCode | None = None

        collection = attribute_type.value.get_all()

        self._valid_codes: set[FullCode] = {code for _, code in collection}