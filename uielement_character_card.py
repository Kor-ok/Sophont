from __future__ import annotations

from nicegui import ui

from gui.forms.character import CharacterCard, CharacterSelector
from gui.initialisation.species import CHARACTER_OPTIONS
from gui.initialisation.state import active_character_card_state
from sophont.character import Sophont

# https://quasar.dev/layout/grid/flex-playground

"""
NiceGUI Dropdown Selection  dictionary {'value1':'label1', ...} specifying the options
CHARACTER_OPTIONS: dict[Sophont, str]
"""


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


def set_active_character(character: Sophont | None) -> None:
    active_character_card_state.set(character)
    render_for(character)


with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Character Card Development").classes("text-sm font-thin q-ma-none")

default_character = _first_character_or_none()

with ui.column().classes(
    "w-128 q-pa-md items-center justify-center"
) as character_selector_container:
    card_selector = CharacterSelector(
        options=CHARACTER_OPTIONS,
        value=default_character,
        on_change=set_active_character,
    )

with ui.column().classes("w-128 q-pa-md items-center justify-center") as character_card_container:
    pass
if default_character is not None:
    set_active_character(default_character)


ui.run(dark=True)
