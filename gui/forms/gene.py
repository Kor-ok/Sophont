from __future__ import annotations

from typing import Callable, Optional

from nicegui import ui

from game.gene import Gene


def gene_form(options: list[str], on_add: Optional[Callable[[Gene], None]] = None):
    with ui.row():
        ui.label('Genes')
        ui.icon('biotech')
    with ui.card().classes('w-full'):
        characteristic_select = ui.select(
            options=options,
            with_input=True,
            on_change=lambda e: ui.notify(f'Selected: {e.value}'),
            label='Characteristic'
        ).props('clearable').classes('w-full')
        die_mult_input = ui.number(value=1, label='Die Multiplier').classes('w-full')
        precidence_input = ui.number(value=0, label='Precidence').classes('w-full')
        gender_link_input = ui.number(value=-1, label='Gender Link').classes('w-full')
        caste_link_input = ui.number(value=-1, label='Caste Link').classes('w-full')
        inheritance_contributors_input = ui.number(value=2, label='Inheritance Contributors').classes('w-full')

        def _add_gene() -> None:
            characteristic_name = characteristic_select.value
            if not characteristic_name:
                ui.notify('Pick a characteristic first')
                return
            try:
                gene = Gene.by_characteristic_name(
                    characteristic_name=str(characteristic_name),
                    die_mult=int(die_mult_input.value or 0),
                    precidence=int(precidence_input.value or 0),
                    gender_link=int(gender_link_input.value or 0),
                    caste_link=int(caste_link_input.value or 0),
                    inheritance_contributors=int(inheritance_contributors_input.value or 0),
                )
            except Exception as exc:  # NiceGUI callback boundary
                ui.notify(f'Failed to create Gene: {exc}')
                return

            if on_add is not None:
                on_add(gene)
            else:
                ui.notify('Gene Added')

        ui.button('Add Gene', on_click=_add_gene).classes('w-full mt-2')