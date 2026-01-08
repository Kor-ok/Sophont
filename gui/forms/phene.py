from __future__ import annotations

from typing import Callable, Optional
from uuid import UUID

from nicegui import ui

from game.phene import Phene


def phene_form(options: list[str], on_add: Optional[Callable[[Phene], None]] = None):
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

        def _add_phene() -> None:
            characteristic_name = characteristic_select.value
            if not characteristic_name:
                ui.notify('Pick a characteristic first')
                return

            uuid_text = (contributor_uuid_input.value or '').strip()
            contributor_uuid = bytes(16)
            if uuid_text:
                try:
                    contributor_uuid = UUID(uuid_text).bytes
                except Exception:
                    ui.notify('Contributor UUID must be a valid UUID')
                    return

            try:
                phene = Phene.by_characteristic_name(
                    characteristic_name=str(characteristic_name),
                    expression_value=int(expression_value_input.value or 0),
                    contributor_uuid=contributor_uuid,
                    is_grafted=bool(is_grafted_checkbox.value),
                )
            except Exception as exc:  # NiceGUI callback boundary
                ui.notify(f'Failed to create Phene: {exc}')
                return

            if on_add is not None:
                on_add(phene)
            else:
                ui.notify('Phene Added')

        ui.button('Add Phene', on_click=_add_phene).classes('w-full mt-2')