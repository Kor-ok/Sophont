from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from typing import Optional

from nicegui import ui

from game.mappings.data import FullCode
from game.mappings.set import ATTRIBUTES
from game.skill import Skill
from gui.forms.attribute_builder_base import (
    AttributeBuilderBase,
    AttributeType,
    SelectedAttributeDisplayBase,
)


class DisplayOptionType(Enum):
    MASTER = ATTRIBUTES.skills.master_category_name_aliases_dict.get
    SUB = ATTRIBUTES.skills.master_sub_category_name_aliases_dict.get
    BASE = ATTRIBUTES.skills.master_skill_code_name_aliases_dict.get


def _display_options_builder(code: int, option_type: DisplayOptionType) -> str:
    aliases = option_type.value(code, ("Unknown",))
    return f"{code} - {aliases[0]}"


class SelectedSkillDisplay(SelectedAttributeDisplayBase):
    """Display for a selected Skill."""

    def __init__(self, full_code: FullCode) -> None:
        super().__init__(full_code)

        canonical, aliases = ATTRIBUTES.skills.get_aliases(full_code)
        with ui.column().classes("q-gutter-xs"):
            ui.label("Skill Selected:").classes("text-bold")
            ui.label(f"Name: {canonical}")
            if aliases:
                ui.label(f"Aliases: {', '.join(aliases)}").classes("text-grey")

            ui.separator()
            ui.label(f"Base Skill ID: {full_code[2]}")
            ui.label(f"Master Category: {full_code[0]}")
            ui.label(f"Sub Category: {full_code[1]}")


class SkillBuilder(AttributeBuilderBase):
    """Form to build a Skill selection."""

    def __init__(
        self,
        *,
        on_skill_built: Optional[Callable[[Skill], None]] = None,
    ) -> None:
        super().__init__(
            attribute_type=AttributeType.SKILL,
            on_attribute_built=on_skill_built,
        )

        with ui.row() as attribute_display_row:
            self._attribute_display_row = attribute_display_row
            self._render_no_selection()

        self._build_selects()

        ui.button(
            "Save New Skill",
            color="dark",
            on_click=self._save_attribute,
        ).classes("q-mt-md")

        self._render_selected_attribute()

    def _build_selects(self) -> None:
        """Build the skill-specific select widgets."""
        collection = self._collection

        master_options = sorted({code[0] for _, code in collection})
        master_options_display: dict[int, str] = {
            code: _display_options_builder(code, DisplayOptionType.MASTER)
            for code in master_options
        }
        sub_options = sorted({code[1] for _, code in collection})
        sub_options_display: dict[int, str] = {
            code: _display_options_builder(code, DisplayOptionType.SUB) for code in sub_options
        }
        base_skill_codes = sorted({code[2] for _, code in collection})
        base_skill_codes_display: dict[int, str] = {
            code: _display_options_builder(code, DisplayOptionType.BASE)
            for code in base_skill_codes
        }

        self._base_skill_id_select = (
            ui.select(
                label="Base Skill ID",
                options=base_skill_codes_display,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full q-mt-md")
            .props("clearable")
        )

        self._master_category_select = (
            ui.select(
                label="Master Category",
                options=master_options_display,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full")
            .props("clearable")
        )

        self._sub_category_select = (
            ui.select(
                label="Sub Category",
                options=sub_options_display,
                value=None,
                on_change=self._on_any_select_changed,
            )
            .classes("w-full q-mt-md")
            .props("clearable")
        )

    def _compute_selected_full_code(self) -> FullCode | None:
        master = self._master_category_select.value
        sub_category = self._sub_category_select.value
        base_skill_id = self._base_skill_id_select.value

        if master is None or sub_category is None or base_skill_id is None:
            return None

        try:
            full_code: FullCode = (int(master), int(sub_category), int(base_skill_id))
        except (TypeError, ValueError):
            return None

        if full_code not in self._valid_codes:
            return None
        return full_code

    def _get_no_selection_label(self) -> str:
        return "No Skill Selected"

    def _get_no_selection_hint(self) -> str:
        return "Pick Master Category + Sub Category + Base Skill ID (valid combination)."

    def _render_selected_attribute(self) -> None:
        if self._attribute_display_row is None:
            return

        self._attribute_display_row.clear()

        full_code = self._selected_full_code
        with self._attribute_display_row:
            if full_code is None:
                self._render_no_selection()
                return

            SelectedSkillDisplay(full_code)

    def _save_attribute(self) -> None:
        full_code = self._selected_full_code
        if full_code is None:
            ui.notify("Select a valid skill first.", type="warning")
            return

        skill = Skill.by_code(full_code)
        if self._on_attribute_built is not None:
            self._on_attribute_built(skill)

        canonical, _aliases = skill.get_name()
        ui.notify(f"Saved: {canonical}", type="positive")
