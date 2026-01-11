from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from humanize import time
from nicegui import ui

from gui import styles
from gui.computed.upp import UPPDisplay
from gui.initialisation.globals import IS_DEBUG
from gui.initialisation.species import SPECIES_MAP
from sophont.character import Sophont


def set_character_name(character: Sophont, new_name: str) -> None:
    if new_name == "":
        new_name = "Unnamed"
    character.name = new_name


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
    def __init__(self, character: Sophont, parent_uuids: list[bytes] | None = None) -> None:
        super().__init__()

        self.character: Sophont = character
        self.parent_uuids: list[bytes] | None = parent_uuids
        self._compute_parents_num()
        self._build_card()

    def _compute_parents_num(self) -> None:
        # For all Genes in character.epigenetic_profile.genotype.genes:
        # Get the highest inheritance_contributors int value
        value = 0
        for gene in self.character.epigenetic_profile.species_genotype.genotype.genes:
            inheritance_contributors = gene.inheritance_contributors
            if inheritance_contributors > value:
                value = inheritance_contributors

        self.set_parent_uuids(num_parents=value)

    def set_parent_uuids(
        self, num_parents: int | None = None, uuids: list[bytes] | None = None
    ) -> None:
        if uuids is None and num_parents is None:
            return

        if uuids is None and num_parents is not None:
            if num_parents < 0:
                return
            if num_parents == 0:
                self.parent_uuids = [self.character.uuid]
            else:
                self.parent_uuids = [uuid4().bytes for _ in range(num_parents)]
        elif uuids is not None:
            self.parent_uuids = uuids

    def _build_card(self) -> None:
        with ui.card().tight().classes(styles.CHARACTER_CARD):
            with ui.element("div").classes(styles.CHARACTER_IMAGE_FRAME):
                image_set = "set2"  # 'set2' is alien-themed 'set4' is cats
                # If SPECIES_MAP uuid matches "Human", use 'set5' which is human-themed
                if self.character.epigenetic_profile.species_genotype.uuid == SPECIES_MAP["Human"]:
                    image_set = "set5"
                elif (
                    self.character.epigenetic_profile.species_genotype.uuid == SPECIES_MAP["Aslan"]
                ):
                    image_set = "set4"
                ui.image(
                    f"https://robohash.org/{self.character.uuid.hex()}?set={image_set}"
                ).classes(styles.CHARACTER_IMAGE)
            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                with ui.grid().classes(styles.CHARACTER_GRID):
                    if IS_DEBUG:
                        ui.label("Character UUID:")
                        ui.label(self.character.uuid.hex())
                        ui.label("Species UUID:")
                        ui.label(self.character.epigenetic_profile.species_genotype.uuid.hex())

                    ui.label("Name:")
                    ui.input(
                        label=self.character.name,
                        placeholder=self.character.name,
                        on_change=lambda e: set_character_name(self.character, e.value),
                        validation={"Input too long": lambda value: len(value) < 20},
                    )

                    ui.label("Age:")
                    ui.label(format_age(self.character.age_seconds))

                    ui.label("Parents:")
                    ui.label(
                        str(
                            len(self.parent_uuids) if self.parent_uuids is not None else "Undefined"
                        )
                    ).tooltip(
                        "Parent UUIDs: " + ", ".join(pu.hex() for pu in self.parent_uuids)
                        if self.parent_uuids is not None
                        else "No parent UUIDs defined"
                    )

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                # Get Species Name by matching species_genotype.uuid to SPECIES_MAP
                species_name = "ERROR"
                for name, uuid in SPECIES_MAP.items():
                    if uuid == self.character.epigenetic_profile.species_genotype.uuid:
                        species_name = name
                        break
                ui.label(f"Phenotype: {species_name}")
                UPPDisplay(character=self.character, display_indices=False)
                ui.label("PLACEHOLDER: Epigenetic Collation")
                raw_collation = repr(self.character.epigenetic_profile.characteristics_collation)
                ui.label(raw_collation).classes()

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                ui.label("PLACEHOLDER: Drop Containers")
