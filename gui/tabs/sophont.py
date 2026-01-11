from __future__ import annotations

import datetime

from nicegui import ui

from game.gametime import (
    format_imperial_date,
    gregorian_to_imperial,
)
from gui import styles
from gui.draggable.inheritance import inheritance_drop_container
from gui.forms.character import CharacterCard
from gui.initialisation.species import create_human_genotype
from gui.initialisation.state import active_character_card_state
from sophont.character import Sophont

# https://quasar.dev/layout/grid/flex-playground

# THIS ALL NEEDS TO BE REWORKED

example_sophont_1 = Sophont(species_genotype=create_human_genotype())
example_sophont_2 = Sophont(species_genotype=create_human_genotype())

# IMPORTANT: selection state is a CharacterCard, but cards must be created
# inside an active NiceGUI container context (not at import time).
CHARACTER_CARD_SOPHONTS: dict[str, Sophont] = {
    "EXAMPLE Sophont 1": example_sophont_1,
    "EXAMPLE Sophont 2": example_sophont_2,
}

# TODO: Fix the implementation of ActiveCharacterCardState for statemanagement
# TODO: CharacterCard (CENTER COLUMN Editor) isn't swapping out correctly
# TODO: inheritance_drop_container (LEFT COLUMN) isn't updating with parent_uuids correctly

def sophont_tab(tab):
    with ui.tab_panel(tab).classes(styles.TAB_PANEL):
        with ui.row().classes(styles.TAB_ROW):
            left_scroller: ui.column
            editor_container: ui.column
            character_cards: dict[str, CharacterCard] = {}
            current_card: CharacterCard | None = None

            def get_or_create_character_card(option_name: str) -> CharacterCard:
                existing = character_cards.get(option_name)
                if existing is not None:
                    return existing

                sophont = CHARACTER_CARD_SOPHONTS[option_name]
                with editor_container:
                    created = CharacterCard(character=sophont)
                created.set_visibility(False)
                character_cards[option_name] = created
                return created

            def render_for(option_name: str) -> None:
                nonlocal current_card
                next_card = get_or_create_character_card(option_name)
                if current_card is not None and current_card is not next_card:
                    current_card.set_visibility(False)
                next_card.set_visibility(True)
                current_card = next_card

                active_character_card_state.set(next_card)
                left_scroller.clear()
                with left_scroller:
                    inheritance_drop_container(character_card=next_card)

            # LEFT COLUMN ===================== DYNAMIC INHERITANCE DRAG & DROP ASSETS
            # inheritance_drop_container should update based on selected sophont
            with ui.column(wrap=False).classes(styles.TAB_COLUMN_LEFT):
                ui.label("Inheritance Drag & Drop")
                left_scroller = ui.column(wrap=False).classes(styles.FIXED_PICKABLES_SCROLLER)

            # CENTER COLUMN ==================== SOPHONT SELECTION DROPDOWN & EDITOR
            # the sophont selection dropdown should update CHARACTER_CARD which is passed
            # into inheritance_drop_container in the left column and updates the editor below
            with ui.column(wrap=False).classes(styles.TAB_COLUMN_CENTER):
                ui.label("Sophont Editor")
                selector = ui.select(
                    options=list(CHARACTER_CARD_SOPHONTS.keys()),
                    value=list(CHARACTER_CARD_SOPHONTS.keys())[0],
                    with_input=True,
                    on_change=lambda e: render_for(e.value),
                )

                editor_container = ui.column(wrap=False).classes("w-full")
                render_for(selector.value)

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
