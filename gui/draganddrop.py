from __future__ import annotations

from typing import Callable, Protocol

from nicegui import ui

BG_INACTIVE = 'bg-grey-10'
BG_ACTIVE = 'bg-blue-grey-10'

CARD_BG = 'bg-grey-9'

class Item(Protocol):
    title: str
    value: int


dragged: card | None = None


class column(ui.column):

    def __init__(self, name: str, on_drop: Callable[[Item, str], None] | None = None) -> None:
        super().__init__()
        with self.classes(f'{BG_INACTIVE} w-60 p-4 rounded shadow-2'):
            ui.label(name).classes('text-bold ml-1')
        self.name = name
        self.on('dragover.prevent', self.highlight)
        self.on('dragleave', self.unhighlight)
        self.on('drop', self.move_card)
        self.on_drop = on_drop

    def highlight(self) -> None:
        self.classes(remove=BG_INACTIVE, add=BG_ACTIVE)

    def unhighlight(self) -> None:
        self.classes(remove=BG_ACTIVE, add=BG_INACTIVE)

    def move_card(self) -> None:
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        self.unhighlight()
        if dragged is None or dragged.parent_slot is None or dragged.parent_slot.parent is None:
            return
        dragged.parent_slot.parent.remove(dragged)
        with self:
            card(dragged.item)
        if self.on_drop:
            self.on_drop(dragged.item, self.name)
        dragged = None


class card(ui.card):

    def __init__(self, item: Item) -> None:
        super().__init__()
        self.item = item
        with self.props('draggable').classes(f'w-full cursor-pointer {CARD_BG}'):
            ui.label(item.title)
            ui.label(str(item.value)).classes('text-sm text-grey-5')
        self.on('dragstart', self.handle_dragstart)

    def handle_dragstart(self) -> None:
        global dragged  # pylint: disable=global-statement # noqa: PLW0603
        dragged = self