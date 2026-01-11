from __future__ import annotations

import datetime

from nicegui import ui

from game.gametime import (
    format_imperial_date,
    gregorian_to_imperial,
)
from gui import styles
from gui.draggable.inheritance import InheritancePopchipDynamicContainer
from gui.forms.character import CharacterCard, CharacterSelector
from gui.initialisation.species import CHARACTER_OPTIONS
from gui.initialisation.state import active_character_card_state
from sophont.character import Sophont

# https://quasar.dev/layout/grid/flex-playground



def sophont_tab(tab):

    def _first_character_or_none() -> Sophont | None:
        try:
            return next(iter(CHARACTER_OPTIONS.keys()))
        except StopIteration:
            return None

    current_card: CharacterCard | None = None

    def render_for(character: Sophont | None) -> None:
        global current_card
        character_card_container.clear()
        if character is None:
            current_card = None
            return

        with character_card_container:
            current_card = CharacterCard(character=character)

        left_scroller.clear()
        with left_scroller:
            inheritance_container = InheritancePopchipDynamicContainer(
                character=character
            )

    def set_active_character(character: Sophont | None) -> None:
        active_character_card_state.set(character)
        render_for(character)

    with ui.tab_panel(tab).classes(styles.TAB_PANEL):
        with ui.row().classes(styles.TAB_ROW):
            left_scroller: ui.column
            character_selector_container: ui.column
            character_card_container: ui.column
            default_character = _first_character_or_none()

            # LEFT COLUMN ===================== DYNAMIC INHERITANCE DRAG & DROP ASSETS
            # inheritance_drop_container should update based on selected sophont
            with ui.column(wrap=False).classes(styles.TAB_COLUMN_LEFT):
                ui.label("Inheritance Drag & Drop")
                left_scroller = ui.column(wrap=False).classes(styles.FIXED_PICKABLES_SCROLLER)

            # CENTER COLUMN ==================== CHARACTER SELECTION DROPDOWN & EDITOR
            # the character selection dropdown should update CHARACTER_CARD which is passed
            # into inheritance_drop_container in the left column and updates the editor below
            with ui.column(wrap=False).classes(styles.TAB_COLUMN_CENTER):
                with ui.column().classes(
                    "w-128 q-pa-md items-center justify-center"
                ) as character_selector_container:
                    card_selector = CharacterSelector(
                        options=CHARACTER_OPTIONS,
                        value=default_character,
                        on_change=set_active_character,
                    ).classes(styles.CHARACTER_SELECTOR)

                with ui.column().classes("w-128 q-pa-md items-center justify-center") as character_card_container:
                    pass

                if default_character is not None:
                    set_active_character(default_character)

            # RIGHT COLUMN =================== TIMELINE DISPLAY
            # TO BE FULLY IMPLEMENTED
            with ui.column(wrap=False).classes(styles.TAB_COLUMN_RIGHT):
                ui.label("Timeline")
                ui_gregorian_date = ui.date_input("Game Date", value="5623-01-01")

                def ui_date_to_imperial(date_str: str) -> str:
                    date_obj = datetime.date.fromisoformat(date_str)
                    imperial_components = gregorian_to_imperial(date_obj)
                    return format_imperial_date(*imperial_components)

                ui.label().bind_text_from(
                    ui_gregorian_date, "value", lambda v: f"Imperial: {ui_date_to_imperial(v)}"
                )
