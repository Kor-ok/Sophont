from __future__ import annotations

from collections.abc import Callable
from os import name
from typing import TYPE_CHECKING, TypeVar, Union
from uuid import uuid4

from nicegui import ui

from game.aptitude_package import T as Apt_Types
from game.characteristic_package import T as Char_Types
from game.mappings.characteristics import _NORM_GENE_NAME_TO_CODES, _NORM_PHENE_NAME_TO_CODES
from game.mappings.skills import (
    _NORM_KNOWLEDGE_NAME_TO_CODES,
    _NORM_SKILL_NAME_TO_CODES,
    Table,
    code_to_string,
)
from game.skill import Skill
from gui.initialisation.globals import IS_DEBUG


class TypeSelector(ui.select):
    def __init__(
        self,
        options: list[str] | None = None,
        label: str = "Select Package Type",
        value: str | None = None,
        on_change: Callable[[str | None], None] | None = None,
        **kwargs,
    ) -> None:
        
        super().__init__(
            label=label,
            options=options if options is not None else ["Error"],
            value=value,
            **kwargs,
            on_change=self._handle_selection_change,
        )
        self._external_on_change = on_change

    def _handle_selection_change(self, e) -> None:
        pass

class CharacterAttributeSelector(ui.select):
    def __init__(
            self,
            type: str | None = None,
            on_change: Callable[[int | None], None] | None = None,
    ) -> None:
        super().__init__(
            label=f"Select {type}:",
            options=[f"{type} 1", f"{type} 2"],  # Placeholder options
            on_change=self._handle_selection_change,
        )
        self._external_on_change = on_change

    def _handle_selection_change(self, e) -> None:
        pass

    @staticmethod
    def _compile_attribute_name_options(type: str) -> dict[int, str]:
        # Placeholder implementation
        
        # code: tuple[int, ...] | int
        name_options: dict[int, str]= {}
        # Determine which mapping to use based on type
        for name_normalized, code in {
            "Gene": _NORM_GENE_NAME_TO_CODES,
            "Phene": _NORM_PHENE_NAME_TO_CODES,
            "Skill": _NORM_SKILL_NAME_TO_CODES,
            "Knowledge": _NORM_KNOWLEDGE_NAME_TO_CODES,
        }.items():
            name_options[code] = name_normalized.title()

        return name_options

class PackageBuilder(ui.card):
    def __init__(
        self,
        on_package_built: Callable[[T], None],  # noqa: F821 # type: ignore
    ) -> None:
        super().__init__()
        self.on_package_built = on_package_built
        self.types_list: list[str] = self._get_type_constraints_for_options_select([Apt_Types, Char_Types])
        
        self._build_form()

    def _build_form(self) -> None:    
        with self:
            with ui.row() as attribute_type_selection_row:  # noqa: F841
                TypeSelector(options=self.types_list)

            with ui.row() as attribute_selection_row: # noqa: F841
                CharacterAttributeSelector(type="Attribute")

            with ui.row() as attribute_display_row: # noqa: F841
                ui.label("Attribute Display Placeholder")

            ui.number(label="Level Modifier", value=None, validation={'Cannot be 0': lambda v: v != 0})
            ui.input(label="Context (optional)", placeholder="E.g. Event name or source")

            with ui.row(wrap=False, align_items='end') as action_button_row: # noqa: F841
                ui.button("Save", on_click=lambda: None, color='dark').classes("q-mr-sm")

    @staticmethod
    def _get_type_constraints_for_options_select(types_list: list[T]) -> list[str]: # noqa: F821 # type: ignore
        list_of_types_str = []
        for T in types_list:
            for t in [t.__name__ for t in T.__constraints__]:
                list_of_types_str.append(t)
        
        return list_of_types_str