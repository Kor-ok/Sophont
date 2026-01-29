from __future__ import annotations

from nicegui import ui

from game.uid.guid import GUID
from gui import styles
from gui.forms.character import CharacterCard, CharacterSelector
from gui.initialisation.character import initialise_example_data
from gui.initialisation.species import CHARACTER_OPTIONS, SPECIES_MAP
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
debug_data_container: ui.column | None = None


def render_for(character: Sophont | None) -> None:
    global current_card
    character_card_container.clear()
    if character is None:
        current_card = None
        return

    with character_card_container:
        current_card = CharacterCard(character=character)


def _get_species_name(species_uuid: int) -> str:
    """Look up species name from UUID via SPECIES_MAP."""
    for name, uuid in SPECIES_MAP.items():
        if uuid == species_uuid:
            return name
    return f"Unknown ({species_uuid})"


def render_debug_view(character: Sophont | None) -> None:
    """Render the debug/data view for the selected character."""
    if debug_data_container is None:
        return

    debug_data_container.clear()
    with debug_data_container:
        if character is None:
            ui.label("No Character Selected").classes("text-gray-500 italic")
            return

        # ===== DEBUG DATA FIELDS =====

        epigenetics_collation_data: str = ""
        for entry in character.epigenetics.characteristics_collation or []:
            name, aliases = entry.item.get_name()
            epigenetics_collation_data += f"\n- {name} (Level: {entry.computed_level})"

        epigenetics_packages_data: str = ""
        for acquired in character.epigenetics.acquired_packages_collection:
            item_name, _ = acquired.package.item.get_name()
            type_name = type(acquired.package.item).__name__
            epigenetics_packages_data += f"\n- {item_name} ({type_name}): {acquired.package.level} (Acquired Age: {acquired.age_acquired_seconds}, Inherited From: {GUID.uid_to_string(acquired.context)})"

        aptitudes_collation_data: str = ""
        for entry in character.aptitudes.aptitude_collation or []:
            name, aliases = entry.item.get_name()
            aptitudes_collation_data += f"\n- {name} (Level: {entry.computed_level}, Training Progress: {entry.training_progress:.2f})"

        aptitudes_packages_data: str = ""
        for acquired in character.aptitudes.acquired_packages_collection:
            item_name, _ = acquired.package.item.get_name()
            type_name = type(acquired.package.item).__name__
            aptitudes_packages_data += f"\n- {item_name} ({type_name}): {acquired.package.level} (Acquired Age: {acquired.age_acquired_seconds}, Context: {GUID.uid_to_string(acquired.context)})"

        debug_fields: list[tuple[str, object]] = [
            ("Epigenetics Collation", epigenetics_collation_data),
            ("Epigenetics Packages", epigenetics_packages_data),
            ("Aptitudes Collation", aptitudes_collation_data),
            ("Aptitudes Packages", aptitudes_packages_data)
        ]

        for label, value in debug_fields:
            ui.label(f"{label}:").classes("text-bold text-sm")
            ui.restructured_text(str(value)).classes("text-sm font-mono text-left")


def set_active_character(character: Sophont | None) -> None:
    active_character_card_state.set(character)
    render_for(character)
    render_debug_view(character)


with ui.header().classes("items-center justify-center bg-deep-orange-10 q-ma-none"):
    ui.label("NOTE: Isolated Character Card Development").classes("text-sm font-thin q-ma-none")

default_character = _first_character_or_none()

with ui.row().classes(styles.TAB_ROW):
    # LEFT COLUMN ===================== CHARACTER SELECTION & DISPLAY
    with ui.column().classes(styles.TAB_COLUMN_LEFT) as character_container:
        with ui.column().classes(
            "w-128 q-pa-md items-center justify-center"
        ) as character_selector_container:
            card_selector = CharacterSelector(
                options=CHARACTER_OPTIONS,
                value=default_character,
                on_change=set_active_character,
            ).classes(styles.CHARACTER_SELECTOR)

        with ui.column().classes(
            "w-128 q-pa-md items-center justify-center"
        ) as character_card_container:
            pass

    # RIGHT COLUMN ==================== CHARACTER DEBUG / DATA VIEW
    with ui.column().classes(styles.TAB_COLUMN_RIGHT) as right_column:
        with ui.card().classes("w-128 q-pa-md"):
            ui.label("Debug / Data View").classes("text-lg font-medium q-mb-md")
            debug_data_container = ui.column().classes("q-pa-none gap-1")

# Initialize with default character after UI is built
if default_character is not None:
    set_active_character(default_character)

INITIALISED = False

def run_once_initialisation() -> None:
    global INITIALISED
    if not INITIALISED:
        initialise_example_data()
        INITIALISED = True

run_once_initialisation()

ui.run(dark=True)
