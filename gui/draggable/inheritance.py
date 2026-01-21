from __future__ import annotations

from random import randint
from typing import Optional

from nicegui import ui

from game.gene import Gene
from game.genotype import Genotype
from gui import styles
from gui.element.popchip import Popchip
from sophont.character import Sophont

T5_STANDARD_DIE_SIDES = 6

dragged: Optional[InheritanceCard] = None

def generate_inheritance_card_popchips(genotype: Genotype, parent_uuids: list[bytes]) -> list[InheritanceCard]:
    """Generates InheritanceCards with Popchips for each gene in the given genotype.

    :param genotype: The Genotype containing Gene/Phene flyweights.
    :param parent_uuids: from character.epigenetic_profile.parent_uuids.
    :type genotype: Genotype
    :type parent_uuids: list[bytes]
    :return: A list of InheritanceCard UI Elements, each containing a Popchip for a Gene without associated Phene.
    :rtype: list[InheritanceCard]
    """
    genes_without_phenes = genotype.get_genes_without_phenes()
    
    cards: list[InheritanceCard] = []
    for upp_index in genes_without_phenes:
        popchip = Popchip(item=genes_without_phenes[upp_index])
        card = InheritanceCard(
            popchip=popchip,
            parent_uuids=parent_uuids,
        )
        cards.append(card)
    return cards

class InheritancePopchipDynamicContainer(ui.column):
    """A container that dynamically generates InheritanceCards derived from the Sophont character currently selected.
    Inheritance Cards contain the Gene as a Popchip Custom FAB ui element, along with controls for selecting parent and inherited value.
    """
    def __init__(
        self,
        character: Sophont,
    ) -> None:
        super().__init__()
        
        inheritance_cards = generate_inheritance_card_popchips(
            genotype=character.epigenetics.species.genotype,
            parent_uuids=character.epigenetics.parent_uuids,
        )
        with self:
            with ui.column(wrap=False, align_items="center").classes("q-py-lg") as card_column:
                for card in inheritance_cards:
                    card.move(card_column)


class InheritanceCard(ui.card):
    def __init__(
        self,
        popchip: Popchip,
        parent_uuids: list[bytes],
        selected_parent_uuid: bytes | None = None,
        chosen_inherited_value: int | None = None,
    ) -> None:

        super().__init__()

        self.popchip: Popchip = popchip
        self.parent_uuids: list[bytes] = parent_uuids
        self._selected_parent_uuid: bytes | None = selected_parent_uuid
        self._chosen_inherited_value: int | None = chosen_inherited_value
        self._is_draggable_active: bool = False

        # Build a dict of parent str to UUID bytes so that the select shows readable options.
        parent_uuid_options_map: dict[str, bytes] = {}
        iteration_size = len(parent_uuids)
        for i in range(iteration_size):
            pu = parent_uuids[i]
            if i == 0:
                parent_uuid_options_map["Self (Clone)"] = pu
            else:
                parent_uuid_options_map[f"Parent {i} - {pu.hex()[:8]}..."] = pu

        self.parent_uuid_options_map = parent_uuid_options_map
        
        self._build_card()
        # Initial state should follow validation; invalid inputs must not be draggable.
        self.validate_and_apply()

    def is_valid(self) -> bool:
        return (
            self._selected_parent_uuid is not None and self._chosen_inherited_value is not None
        )

    def set_draggable(self, active: bool) -> None:
        if active == self._is_draggable_active:
            return
        self._is_draggable_active = active

        self._drag_row.set_visibility(active)
        if active:
            self.props(add="draggable")
            self.classes(replace=styles.DRAGGABLE_CARD_CLASSES)
        else:
            self.props(remove="draggable")
            self.classes(replace=styles.UNDRAGGABLE_CARD_CLASSES)

    def validate_and_apply(self) -> None:
        self.set_draggable(self.is_valid())

    def on_parent_chosen(self, value: str | None) -> None:
        if value is None:
            self._selected_parent_uuid = None
        else:
            self._selected_parent_uuid = self.parent_uuid_options_map[value]
        self.validate_and_apply()

    def on_inherited_value_changed(self, value: int) -> None:
        self._chosen_inherited_value = value
        self.validate_and_apply()

    def on_randomise_inheritance_value_clicked(self) -> None:
        if isinstance(self.popchip.item, Gene):
            if self.popchip.item.die_mult != 0:
                die_mult = self.popchip.item.die_mult
            else:
                die_mult = 1
        else:
            die_mult = 1
        new_value = randint(1, T5_STANDARD_DIE_SIDES * die_mult)
        self.on_inherited_value_changed(new_value)
        self._inherited_value_input.set_value(new_value)

    def on_randomise_parent_clicked(self) -> None:
        if self.parent_uuids is None or len(self.parent_uuids) <= 1:
            return
        index = randint(
            1, len(self.parent_uuids) - 1
        )  # Skip index 0 which is 'Self' intended for cloning scenarios.
        new_parent = self.parent_uuids[index]
        # Get from self.parent_uuid_options_map the str version of the UUID.
        for pu_str, pu_bytes in self.parent_uuid_options_map.items():
            if pu_bytes == new_parent:
                new_parent_str = pu_str
                break
        self.on_parent_chosen(new_parent_str)
        # New Parent str id
        self._parent_select.set_value(new_parent_str)

    def _build_card(self) -> None:
        with self:
            # Showing the characteristic of the gene/phene as a Popchip(custom FAB).
            with ui.row(wrap=False, align_items="center").classes("q-py-lg") as chip_row:
                self.popchip.move(chip_row)
            # Pool of parents passed in from the current Sophont being edited.
            with ui.row(wrap=False, align_items="stretch").classes("q-py-sm"):
                parent_select = ui.select(
                    label="Inherit From Parent:",
                    options=list(self.parent_uuid_options_map.keys()),
                    value=self._selected_parent_uuid,
                    on_change=lambda v: self.on_parent_chosen(v.value),
                ).classes("flex-1")
                self._parent_select = parent_select
                # Randomise Parent Button (exclude 'Self' at index 0)
                random_parent_button = ui.button(icon="casino", on_click=lambda: self.on_randomise_parent_clicked())
                random_parent_button.tooltip("Random excluding 'Self'")
            # Inherited Value Input
            with ui.row(wrap=False, align_items="stretch").classes("q-py-sm"):
                inherited_value_input = ui.number(
                    label="Inherited Value",
                    value=self._chosen_inherited_value,
                    on_change=lambda v: self.on_inherited_value_changed(v.value),
                ).classes("flex-1")
                self._inherited_value_input = inherited_value_input
                # Randomise Inherited Value Button that takes into account the die multiplier value
                # associated with the Gene that has been passed in via the Popchip.
                random_inherited_value_button = ui.button(icon="casino", on_click=lambda: self.on_randomise_inheritance_value_clicked())
                if isinstance(self.popchip.item, Gene) and self.popchip.item.die_mult != 0:
                    random_inherited_value_button.tooltip(f"Randomise Inherited Value ({self.popchip.item.die_mult}d{T5_STANDARD_DIE_SIDES})")
            # On validation success, this user feedback row appears to indicate draggable state.
            with ui.row().classes("q-py-sm w-full justify-end") as drag_row:
                ui.icon("drag_indicator").classes("cursor-grab")
            self._drag_row = drag_row
            self._drag_row.set_visibility(False)

        self.on("dragstart", self.handle_dragstart)
        self.props(add='dense unelevated size=sm padding="xs sm"')
        self.classes(replace=styles.UNDRAGGABLE_CARD_CLASSES)

    def handle_dragstart(self) -> None:
        global dragged
        dragged = self
