from __future__ import annotations

from nicegui import ui


def phene_form(options: list[str]):
    with ui.row():
        ui.label('Phenes')
        ui.icon('fingerprint')
    with ui.card().classes('w-full'):
        characteristic_select = ui.select(
            options=options,
            with_input=True,
            on_change=lambda e: ui.notify(f'Selected: {e.value}'),
            label='Characteristic'
        ).props('clearable').classes('w-full')
        expression_value_input = ui.number(value=0, label='Expression Value').classes('w-full')
        contributor_uuid_input = ui.input(label='Contributor UUID').classes('w-full')
        is_grafted_checkbox = ui.checkbox(text='Is Grafted').classes('w-full')
        ui.button('Add Phene', on_click=lambda: ui.notify('Phene Added')).classes('w-full mt-2')