from __future__ import annotations

from random import randint
from typing import Optional, Union

from nicegui import ui

from game.gene import Gene
from game.genotype import Genotype
from game.phene import Phene
from gui import styles
from gui.element.popchip import Popchip
from gui.forms.character import CharacterCard

T5_STANDARD_DIE_SIDES = 6

dragged: Optional[inheritance_card] = None

Phenotype = dict[int, tuple[Union[Gene, None], Union[Phene, None]]]


def _derive_genes_without_phenes(genotype: Genotype) -> list[Gene]:
    """Return all Genes that have no matching Phene in this genotype.

    Note: `Genotype.get_phenotype()` always returns a Phene entry for every Gene
    (it synthesizes a default Phene when none exists). So we must compare
    indices against `genotype.phenes` rather than look for `phene is None`.
    """

    phene_indices = (
        {phene.characteristic.upp_index for phene in genotype.phenes}
        if genotype.phenes is not None
        else set()
    )
    return [
        gene
        for gene in genotype.genes
        if gene.characteristic.upp_index not in phene_indices
    ]

def _generate_inheritance_card_popchips(genotype: Genotype, parent_uuids: list[bytes]) -> list[inheritance_card]:
    genes_without_phenes = _derive_genes_without_phenes(genotype)
    
    cards: list[inheritance_card] = []
    for gene in genes_without_phenes:
        popchip = Popchip(item=gene)
        card = inheritance_card(
            popchip=popchip,
            parent_uuids=parent_uuids,
        )
        cards.append(card)
    return cards

class inheritance_drop_container(ui.column):
    def __init__(
        self,
        character_card: CharacterCard,
    ) -> None:

        super().__init__()

        inheritance_cards = _generate_inheritance_card_popchips(
            genotype=character_card.character.epigenetic_profile.genotype,
            parent_uuids=character_card.parent_uuids if character_card.parent_uuids is not None else [],
        )
        with self:
            with ui.column(wrap=False, align_items="center").classes("q-py-lg") as card_column:
                for card in inheritance_cards:
                    card.move(card_column)


class inheritance_card(ui.card):
    def __init__(
        self,
        popchip: Popchip,
        parent_uuids: list[bytes] | list[str] | None = None,
        selected_parent_uuid: bytes | str | None = None,
        chosen_inherited_value: int | None = None,
        is_draggable_active: bool = False,
    ) -> None:

        super().__init__()

        self._selected_parent_uuid: bytes | str | None = selected_parent_uuid
        self._chosen_inherited_value: int | None = chosen_inherited_value
        self.is_draggable_active: bool = False

        def is_valid() -> bool:
            return (
                self._selected_parent_uuid is not None and self._chosen_inherited_value is not None
            )

        def set_draggable(active: bool) -> None:
            if active == self.is_draggable_active:
                return
            self.is_draggable_active = active

            self._drag_row.set_visibility(active)
            if active:
                self.props(add="draggable")
                self.classes(replace=styles.DRAGGABLE_CARD_CLASSES)
            else:
                self.props(remove="draggable")
                self.classes(replace=styles.UNDRAGGABLE_CARD_CLASSES)

        def validate_and_apply() -> None:
            set_draggable(is_valid())

        def on_parent_chosen(value: bytes | str | None) -> None:
            self._selected_parent_uuid = value
            validate_and_apply()

        def on_inherited_value_changed(value: int) -> None:
            self._chosen_inherited_value = value
            validate_and_apply()

        def on_randomise_inheritance_value_clicked() -> None:
            if isinstance(popchip.item, Gene):
                if popchip.item.die_mult != 0:
                    die_mult = popchip.item.die_mult
                else:
                    die_mult = 1
            else:
                die_mult = 1
            new_value = randint(1, T5_STANDARD_DIE_SIDES * die_mult)
            on_inherited_value_changed(new_value)
            self._inherited_value_input.set_value(new_value)

        def on_randomise_parent_clicked() -> None:
            if parent_uuids is None or len(parent_uuids) <= 1:
                return
            index = randint(
                1, len(parent_uuids) - 1
            )  # Skip index 0 which is 'Self' intended for cloning scenarios.
            new_parent = parent_uuids[index]
            on_parent_chosen(new_parent)
            self._parent_select.set_value(new_parent)

        with self:
            # Showing the characteristic of the gene/phene as a Popchip(custom FAB).
            with ui.row(wrap=False, align_items="center").classes("q-py-lg") as chip_row:
                popchip.move(chip_row)
            # Pool of parents passed in from the current Sophont being edited.
            with ui.row(wrap=False, align_items="stretch").classes("q-py-sm"):
                parent_select = ui.select(
                    label="Inherit From Parent:",
                    options=parent_uuids if parent_uuids else [],
                    value=self._selected_parent_uuid,
                    on_change=lambda v: on_parent_chosen(v.value),
                ).classes("flex-1")
                self._parent_select = parent_select
                # Randomise Parent Button (exclude 'Self' at index 0).
                ui.button(icon="casino", on_click=lambda: on_randomise_parent_clicked())
            # Inherited Value Input
            with ui.row(wrap=False, align_items="stretch").classes("q-py-sm"):
                inherited_value_input = ui.number(
                    label="Inherited Value",
                    value=self._chosen_inherited_value,
                    on_change=lambda v: on_inherited_value_changed(v.value),
                ).classes("flex-1")
                self._inherited_value_input = inherited_value_input
                # Randomise Inherited Value Button that takes into account the die multiplier value
                # associated with the Gene that has been passed in via the Popchip.
                ui.button(icon="casino", on_click=lambda: on_randomise_inheritance_value_clicked())
            # On validation success, this user feedback row appears to indicate draggable state.
            with ui.row().classes("q-py-sm w-full justify-end") as drag_row:
                ui.icon("drag_indicator").classes("cursor-grab")
            self._drag_row = drag_row
            self._drag_row.set_visibility(False)

        self.on("dragstart", self.handle_dragstart)
        self.props(add='dense unelevated size=sm padding="xs sm"')
        self.classes(replace=styles.UNDRAGGABLE_CARD_CLASSES)

        # Initial state should follow validation; invalid inputs must not be draggable.
        validate_and_apply()

    def handle_dragstart(self) -> None:
        global dragged
        dragged = self
