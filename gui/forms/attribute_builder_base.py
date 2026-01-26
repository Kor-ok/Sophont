from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import Any, Optional, TypeVar

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
        self._full_code = full_code


# TypeVar for the attribute type built by subclasses (Skill, Characteristic, etc.)
T = TypeVar("T")


class AttributeBuilderBase(ui.card):
    """Form to build an Attribute selection.

    Subclasses must implement:
        - _build_selects(): Create the UI select widgets.
        - _compute_selected_full_code(): Compute FullCode from widget values.
        - _render_selected_attribute(): Update the display row.
        - _save_attribute(): Handle the save action.
        - _get_no_selection_label(): Return the "nothing selected" label text.
        - _get_no_selection_hint(): Return the hint text for selection.
    """

    def __init__(
        self,
        *,
        attribute_type: AttributeType,
        on_attribute_built: Optional[Callable[[Any], None]] = None,
    ) -> None:
        super().__init__()
        self.classes("q-pa-md").props("flat outlined")

        self._attribute_type = attribute_type
        self._on_attribute_built = on_attribute_built

        self._attribute_display_row: ui.row | None = None
        self._selected_full_code: FullCode | None = None

        collection = attribute_type.value.get_all()
        self._collection = collection
        self._valid_codes: set[FullCode] = {code for _, code in collection}

    def _on_any_select_changed(self, e) -> None:
        """Handle change events from any select widget."""
        _ = _event_value(e)
        self._selected_full_code = self._compute_selected_full_code()
        self._render_selected_attribute()

    @abstractmethod
    def _build_selects(self) -> None:
        """Build the select widgets for this attribute type."""
        ...

    @abstractmethod
    def _compute_selected_full_code(self) -> FullCode | None:
        """Compute the FullCode from the current select widget values."""
        ...

    @abstractmethod
    def _render_selected_attribute(self) -> None:
        """Render the selected attribute display."""
        ...

    @abstractmethod
    def _save_attribute(self) -> None:
        """Handle saving the selected attribute."""
        ...

    @abstractmethod
    def _get_no_selection_label(self) -> str:
        """Return the label text when no attribute is selected."""
        ...

    @abstractmethod
    def _get_no_selection_hint(self) -> str:
        """Return the hint text describing how to select an attribute."""
        ...

    def _render_no_selection(self) -> None:
        """Render the 'no selection' state in the display row."""
        ui.label(self._get_no_selection_label()).classes("text-gray-500 italic")
        ui.label(self._get_no_selection_hint()).classes("text-gray-500")
