from __future__ import annotations

from collections.abc import Callable

from humanize import time
from nicegui import ui

from game.mappings.gender import _BASE as gender_map
from gui import styles
from gui.computed.upp import UPPDisplay
from gui.initialisation.globals import IS_DEBUG
from gui.initialisation.species import SPECIES_MAP
from sophont.character import Sophont


def format_age(age_seconds: int) -> str:
    result = ""
    if age_seconds < 0:
        result = "Unborn"
    if age_seconds == 0:
        result = "Newborn"
    if age_seconds > 0:
        result = time.naturaldelta(age_seconds, months=True)

    if IS_DEBUG:
        result += f" (value={age_seconds})"
    return result


class CharacterSelector(ui.select):
    def __init__(
        self,
        options: dict[Sophont, str],
        label: str = "Select Character",
        value: Sophont | None = None,
        on_change: Callable[[Sophont | None], None] | None = None,
    ) -> None:
        # NOTE: `ui.select` already uses the attribute name `options` internally
        # (typically a list of strings). Keep our Sophont↔name mapping separate.
        self._character_options: dict[Sophont, str] = options
        self._character_by_name: dict[str, Sophont] = {
            name: character for character, name in options.items()
        }

        str_options = list(options.values())
        super().__init__(
            label=label,
            options=str_options,
            value=options[value] if value is not None else None,
            on_change=self._handle_selection_change,
        )
        self._external_on_change = on_change

    def _handle_selection_change(self, e) -> None:
        # NiceGUI's built-in `on_change` provides `e.value`.
        # (Using low-level `update:model-value` yields GenericEventArguments without `value`.)
        selected_name: str | None = getattr(e, "value", None)
        if selected_name is None:
            args = getattr(e, "args", None)
            if isinstance(args, dict):
                selected_name = args.get("value")
            elif isinstance(args, (list, tuple)) and args:
                # Be permissive: some event shapes pass payloads as a list/tuple.
                selected_name = args[-1]

        selected_character = (
            self._character_by_name.get(selected_name) if selected_name is not None else None
        )
        if self._external_on_change is not None:
            self._external_on_change(selected_character)


class CharacterCard(ui.column):
    def __init__(self, character: Sophont) -> None:
        super().__init__()
        self.character: Sophont = character
        self._build_card()
#region: ================================================== DATA HANDLING ======================
    def _commit_name(self, raw: str) -> None:
        new_name = (raw or "").strip() or "Unnamed"
        if new_name != self.character.name:  # prevents redundant writes
            self.character.name = new_name
            ui.notify(f'Renamed to "{new_name}"', type="positive")

    def _commit_gender(self, new_gender_key: int) -> None:
        original_selected, original_selection_size = self.character.epigenetics.gender
        if new_gender_key != original_selected:  # prevents redundant writes
            self.character.epigenetics.gender = (new_gender_key, original_selection_size)
#endregion
#region: =================================================== UI SECTIONS =======================
    def _build_profile_picture(self) -> None:
        with ui.element("div").classes(styles.CHARACTER_IMAGE_FRAME):
                image_set = "set2"  # 'set2' is alien-themed 'set4' is cats
                # If SPECIES_MAP uuid matches "Human", use 'set5' which is human-themed
                if self.character.epigenetics.species.uuid == SPECIES_MAP["Human"]:
                    image_set = "set5"
                elif (
                    self.character.epigenetics.species.uuid == SPECIES_MAP["Aslan"]
                ):
                    image_set = "set4"
                ui.image(
                    f"https://robohash.org/{self.character.uuid}?set={image_set}"
                ).classes(styles.CHARACTER_IMAGE)

    def _build_debug_info(self) -> None:
        if IS_DEBUG:
                        ui.label("Character UUID:")
                        ui.label(str(self.character.uuid))
                        ui.label("Species UUID:")
                        ui.label(str(self.character.epigenetics.species.uuid))

    def _build_name_input(self) -> None:
        ui.label("Name:")
        name_input = (
            ui.input(value=self.character.name, placeholder=self.character.name)
            .without_auto_validation()
            .classes(styles.CHARACTER_NAME_INPUT_CLASSES)
            .props(styles.CHARACTER_NAME_INPUT_PROPS)
        )
        name_input.on(
            "keydown.enter",
            js_handler="(e) => { e.target.blur(); }",
        )
        name_input.on(
            "blur",
            handler=lambda e: self._commit_name(e.args["value"]),
            js_handler="(e) => emit({value: e.target.value})",
        )

    def _build_age_display(self) -> None:
        ui.label("Age:")
        ui.label(format_age(self.character.age_seconds))

    def _build_parentage_display(self) -> None:
        ui.label("Parents:")
        ui.label(
            str(len(self.character.epigenetics.parent_uuids) - 1) # Exclude 'Self'
        ).tooltip(f"UUIDs: {[pu for pu in self.character.epigenetics.parent_uuids if pu != self.character.uuid]}")

    def _build_gender_display(self) -> None:
        ui.label("Gender:")
        selected_gender, possible_genders = self.character.epigenetics.gender
        gender_map_slice = possible_genders + 2 
        gender_map_options = {k: v[0].capitalize() for k, v in list(gender_map.items())[0:gender_map_slice]}
        gender_select_input = (
             ui.select(value=selected_gender, options=gender_map_options, on_change=lambda e: self._commit_gender(e.value))
             .props('dense rounded outlined')
        )
    
    def _build_genotype_display(self) -> None:
        # Get Species Name by matching species.uuid to SPECIES_MAP
        species_name = "ERROR"
        for name, uuid in SPECIES_MAP.items():
            if uuid == self.character.epigenetics.species.uuid:
                species_name = name
                break
        ui.label(f"Genotype: {species_name}")
        UPPDisplay(character=self.character, display_indices=IS_DEBUG)
#endregion
#region: =================================================== CARD LAYOUT =======================
    def _build_card(self) -> None:
        with ui.card().tight().classes(styles.CHARACTER_CARD):
            self._build_profile_picture()
            
            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                with ui.grid().classes(styles.CHARACTER_GRID):
                    self._build_debug_info()
                    self._build_name_input()
                    self._build_age_display()
                    self._build_parentage_display()
                    self._build_gender_display()

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                self._build_genotype_display()
                # ui.label("PLACEHOLDER: Epigenetic Collation")
                # raw_collation = repr(self.character.epigenetics.characteristics_collation)
                # ui.label(raw_collation).classes()

            # with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
            #     ui.label("PLACEHOLDER: Drop Containers")
#endregion