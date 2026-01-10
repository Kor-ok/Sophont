from __future__ import annotations

# from dataclasses import dataclass
from collections.abc import Mapping
from typing import Callable, Literal, Optional, Union  # Protocol

from nicegui import ui

import gui.draggable.fab as d_fab
from game.gene import Gene
from game.genotype import Genotype
from game.mappings.characteristics import char_name_to_category_code
from game.phene import Phene
from gui.computed.upp import collation_layer
from gui.draggable.commands import RemoveFabCommand
from gui.history.undo import notify_undo


def _spawn_draggable(
    item: Union[Gene, Phene],
    icon: str,
    color: str,
    direction: Literal['up', 'down', 'left', 'right'],
) -> d_fab.draggable:
    return d_fab.draggable(gene=item, icon=icon, color=color, direction=direction, on_remove=handle_remove_requested)

def handle_remove_requested(fab: d_fab.draggable) -> None:
    command = RemoveFabCommand(fab=fab, spawn=_spawn_draggable)
    command.execute()
    notify_undo(f'Removed {fab.item.characteristic.get_name()}', command)

class species_genotype_widget(ui.column):

    def __init__(
        self,
        name: str,
        placeholder: str = 'Homo Sapiens',
        genotype: Genotype | None = None,
        is_instantiated: bool = False,
        on_drop: Optional[Callable[[Union[Gene, Phene], str], None]] = None,
    ) -> None:
        super().__init__()

        # Public child containers for later wiring:
        # - `collation_layer`: placeholder where you can render computed/collated output
        # - `collection`: the actual list of dropped Genes/Phenes
        self.collation_layer: ui.element
        self.collection: ui.element
        self.save_button: ui.element

        with self.classes(f'{d_fab.BG_INACTIVE} w-96 p-4 rounded'):
            if is_instantiated:
                name_label = ''
            else:
                name_label = 'Enter Species Name:'
            self.name_input = ui.input(label=name_label, placeholder=placeholder, value=name).props('').classes('w-full text-xs')

            # Collation layer placeholder section.
            with ui.label('UPP:').classes('w-full'):
                self.collation_layer = collation_layer(genotype=genotype)

            # Collection section: dropped items are appended here.
            with ui.expansion('Collection (drag & drop items here)', value=True).classes('w-full'):
                self.collection = ui.row().classes('')

            if not is_instantiated:
                ui.button('Save Species Genotype', on_click=lambda: ui.notify(message='Not Yet Implemented', color='orange')) \
                    .classes('w-full mt-2 text-xs')

        self.name = name
        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)
        self.on('drop', self.drop_item)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove=d_fab.BG_INACTIVE, add=d_fab.BG_ACTIVE)

    def unhighlight(self) -> None:
        self.classes(remove=d_fab.BG_ACTIVE, add=d_fab.BG_INACTIVE)

    def drop_item(self) -> None:
        dragged = d_fab.dragged
        self.unhighlight()
        if dragged is None or dragged.parent_slot is None or dragged.parent_slot.parent is None:
            return

        item = dragged.item
        icon = dragged.icon
        color = dragged.color
        direction: Literal['up', 'down', 'left', 'right'] = dragged.direction

        dragged.parent_slot.parent.remove(dragged)
        with self.collection:
            _spawn_draggable(item=item, icon=icon, color=color, direction=direction)

        if self.on_drop:
            self.on_drop(item, self.name)

        d_fab.dragged = None


class categorised_drop_column(ui.column):

    def __init__(
        self,
        name: str,
        category_targets: Mapping[int, ui.element],
        default_target: ui.element | None = None,
        on_drop: Optional[Callable[[Union[Gene, Phene], str], None]] = None,
    ) -> None:
        super().__init__()
        with self.classes(f'{d_fab.BG_INACTIVE} w-72 p-4 rounded'):
            ui.label(name).classes('text-bold ml-1')

        self.name = name
        self._category_targets = dict(category_targets)
        self._default_target: ui.element = default_target if default_target is not None else self

        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)
        self.on('drop', self.drop_item)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove=d_fab.BG_INACTIVE, add=d_fab.BG_ACTIVE)

    def unhighlight(self) -> None:
        self.classes(remove=d_fab.BG_ACTIVE, add=d_fab.BG_INACTIVE)

    def _target_for(self, item: Union[Gene, Phene]) -> ui.element:
        try:
            cat_code = char_name_to_category_code(item.characteristic.get_name())
        except Exception:
            cat_code = 0
        return self._category_targets.get(cat_code, self._default_target)

    def drop_item(self) -> None:
        dragged = d_fab.dragged
        self.unhighlight()
        if dragged is None or dragged.parent_slot is None or dragged.parent_slot.parent is None:
            return

        item = dragged.item
        icon = dragged.icon
        color = dragged.color
        direction: Literal['up', 'down', 'left', 'right'] = dragged.direction

        dragged.parent_slot.parent.remove(dragged)

        target = self._target_for(item)
        with target:
            _spawn_draggable(item=item, icon=icon, color=color, direction=direction)

        if self.on_drop:
            self.on_drop(item, self.name)

        d_fab.dragged = None