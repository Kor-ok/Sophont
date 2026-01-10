from __future__ import annotations

from uuid import uuid4

from humanize import time
from nicegui import ui

from gui import styles
from gui.computed.upp import collation_layer
from sophont.character import Sophont

IS_DEBUG = True


def set_character_name(character: Sophont, new_name: str) -> None:
    if new_name == "":
        new_name = "Unnamed"
    character.name = new_name

def format_age(age_seconds: int) -> str:
    result = ''
    if age_seconds < 0:
        result = "Unborn"
    if age_seconds == 0:
        result = "Newborn"
    if age_seconds > 0:
        result = time.naturaldelta(age_seconds, months=True)
    
    if IS_DEBUG:
        result += f" (value={age_seconds})"
    return result


class CharacterCard(ui.column):
    def __init__(
        self,
        character: Sophont,
        parent_uuids: list[bytes] | None = None
    ) -> None:

        super().__init__()

        self.character: Sophont = character
        self.parent_uuids: list[bytes] | None = parent_uuids

        def _compute_parents_num() -> None:
            # For all Genes in character.epigenetic_profile.genotype.genes:
            # Get the highest inheritance_contributors int value
            value = 0
            for gene in character.epigenetic_profile.genotype.genes:
                inheritance_contributors = gene.inheritance_contributors
                if inheritance_contributors > value:
                    value = inheritance_contributors
                
            set_parent_uuids(num_parents=value)

        def set_parent_uuids(num_parents: int | None = None, uuids: list[bytes] | None = None) -> None:
            if uuids is None and num_parents is None:
                return
            nonlocal parent_uuids
            if uuids is None and num_parents is not None:
                if num_parents < 0:
                    return
                if num_parents == 0:
                    parent_uuids = [character.uuid]
                else:
                    parent_uuids = [uuid4().bytes for _ in range(num_parents)]
            elif uuids is not None:
                parent_uuids = uuids

        _compute_parents_num()

        with ui.card().tight().classes(styles.CHARACTER_CARD):
            with ui.element("div").classes(styles.CHARACTER_IMAGE_FRAME):
                ui.image(f"https://robohash.org/{character.uuid.hex()}?set=set2").classes(styles.CHARACTER_IMAGE)

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                with ui.grid().classes(styles.CHARACTER_GRID):
                    if IS_DEBUG:
                        ui.label("UUID:")
                        ui.label(character.uuid.hex())

                    ui.label("Name:")
                    ui.input(
                        label=character.name,
                        placeholder=character.name,
                        on_change=lambda e: set_character_name(character, e.value),
                        validation={"Input too long": lambda value: len(value) < 20},
                    )

                    ui.label("Age:")
                    ui.label(format_age(character.age_seconds))

                    ui.label("Parents:")
                    ui.label(str(len(parent_uuids) if parent_uuids is not None else "Undefined")).tooltip(
                        "Parent UUIDs: " + ", ".join(
                            pu.hex() for pu in parent_uuids 
                        ) if parent_uuids is not None else "No parent UUIDs defined"
                    )

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                ui.label("Phenotype: <Variable Species Name Placeholder>")
                collation_layer(character.epigenetic_profile.genotype, display_indices=False)
                ui.label("PLACEHOLDER: Epigenetic Collation")
                raw_collation = repr(character.epigenetic_profile.characteristics_collation)
                ui.label(raw_collation).classes()

            with ui.card_section().classes(styles.CHARACTER_CARD_SECTION):
                ui.label("PLACEHOLDER: Drop Containers")
