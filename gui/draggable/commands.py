from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional, Union

from nicegui.element import Element

from game.gene import Gene
from game.phene import Phene

from .fab import draggable

Direction = Literal['up', 'down', 'left', 'right']
Item = Union[Gene, Phene]


@dataclass
class RemoveFabCommand:
    """Undoable command for removing a draggable FAB.

    `execute()` removes the element from the UI.
    `undo()` recreates a new draggable FAB in the original parent container.

    Note: undo restores the item and basic presentation (icon/color/direction),
    but will append it to the container (NiceGUI does not provide a stable
    public API for restoring the exact previous index).
    """

    fab: draggable
    spawn: Callable[[Item, str, str, Direction], draggable]

    _parent: Optional[Element] = None
    _item: Optional[Item] = None
    _icon: Optional[str] = None
    _color: Optional[str] = None
    _direction: Direction = 'right'

    def execute(self) -> None:
        if self._parent is None:
            if self.fab.parent_slot is None or self.fab.parent_slot.parent is None:
                return
            self._parent = self.fab.parent_slot.parent
            self._item = self.fab.item
            self._icon = self.fab.icon
            self._color = self.fab.color
            self._direction = self.fab.direction

        self.fab.remove_now()

    def undo(self) -> None:
        if self._parent is None or self._item is None:
            return
        with self._parent:
            self.spawn(
                self._item,
                self._icon or 'biotech',
                self._color or 'red',
                self._direction,
            )
