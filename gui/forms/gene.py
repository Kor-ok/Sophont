from __future__ import annotations

from nicegui import ui


def gene_form(options: list[str]):
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
        ui.button('Add Gene', on_click=lambda: ui.notify('Gene Added')).classes('w-full mt-2')