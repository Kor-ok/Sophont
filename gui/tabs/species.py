from __future__ import annotations

# from dataclasses import dataclass
from typing import Callable, Literal, Optional, Union  # Protocol

from nicegui import ui

import gui.draggable.fab as d_fab
from game.gene import Gene
from game.phene import Phene
from gui.draggable.commands import RemoveFabCommand
from gui.forms.gene import gene_form
from gui.forms.phene import phene_form


def _spawn_draggable(
    item: Union[Gene, Phene],
    icon: str,
    color: str,
    direction: Literal['up', 'down', 'left', 'right'],
) -> d_fab.draggable:
    return d_fab.draggable(gene=item, icon=icon, color=color, direction=direction, on_remove=_handle_remove_requested)


def _notify_undo(message: str, command: RemoveFabCommand, *, timeout_seconds: float = 60.0) -> None:
    state = {'expired': False}

    def on_dismiss() -> None:
        if state['expired']:
            return
        command.undo()

    notification = ui.notification(
        message,
        close_button='Undo',
        timeout=0,  # we control expiry ourselves to avoid undo-on-timeout
        type='ongoing',
        position='bottom',
        on_dismiss=on_dismiss,
    )

    def expire() -> None:
        state['expired'] = True
        try:
            notification.dismiss()
        except Exception:
            pass

    ui.timer(timeout_seconds, expire, once=True)


def _handle_remove_requested(fab: d_fab.draggable) -> None:
    command = RemoveFabCommand(fab=fab, spawn=_spawn_draggable)
    command.execute()
    _notify_undo(f'Removed {fab.item.characteristic.get_name()}', command)

CHARACTERISTICS = ['Strength', 'Dexterity', 'Intelligence']


class gene_drop_column(ui.column):

    def __init__(
        self,
        name: str,
        on_drop: Optional[Callable[[Union[Gene, Phene], str], None]] = None,
    ) -> None:
        super().__init__()
        with self.classes(f'{d_fab.BG_INACTIVE} w-72 p-4 rounded'):
            ui.label(name).classes('text-bold ml-1')
        self.name = name
        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)
        self.on('drop', self.drop_gene)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove=d_fab.BG_INACTIVE, add=d_fab.BG_ACTIVE)

    def unhighlight(self) -> None:
        self.classes(remove=d_fab.BG_ACTIVE, add=d_fab.BG_INACTIVE)

    def drop_gene(self) -> None:
        dragged = d_fab.dragged
        self.unhighlight()
        if dragged is None or dragged.parent_slot is None or dragged.parent_slot.parent is None:
            return

        gene = dragged.item
        icon = dragged.icon
        color = dragged.color
        direction: Literal['up', 'down', 'left', 'right'] = dragged.direction

        dragged.parent_slot.parent.remove(dragged)
        with self:
            _spawn_draggable(item=gene, icon=icon, color=color, direction=direction)

        if self.on_drop:
            self.on_drop(gene, self.name)

        d_fab.dragged = None

def _pickable_gene_list_section():
    with gene_drop_column('Available Genes'):
        d_fab.draggable(gene=Gene.by_characteristic_name('Strength'), on_remove=_handle_remove_requested)
        d_fab.draggable(gene=Gene.by_characteristic_name('Dexterity'), on_remove=_handle_remove_requested)
        d_fab.draggable(gene=Gene.by_characteristic_name('Intelligence'), on_remove=_handle_remove_requested)
        d_fab.draggable(gene=Phene.by_characteristic_name('Education'), on_remove=_handle_remove_requested)
        d_fab.draggable(gene=Phene.by_characteristic_name('Social Standing'), on_remove=_handle_remove_requested)

def _characteristics_collection_section():
    with gene_drop_column('Genotype (drop genes here)', on_drop=lambda gene, loc: ui.notify(f'Dropped: {gene.characteristic.get_name()}')):
        pass

def _input_form_section():
    gene_form(options=CHARACTERISTICS)
    phene_form(options=CHARACTERISTICS)

def species_tab(tab):
    with ui.tab_panel(tab):
        with ui.row().classes('w-full justify-around'):
            with ui.column(wrap=False, align_items='start'):
                _input_form_section()
            with ui.column(wrap=False, align_items='start'):
                _pickable_gene_list_section()
            with ui.column(wrap=False, align_items='start'):
                _characteristics_collection_section()