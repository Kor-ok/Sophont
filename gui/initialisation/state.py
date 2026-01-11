from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from gui.forms.character import CharacterCard

CharacterCardListener = Callable[[Optional[CharacterCard]], None]


@dataclass()
class ActiveCharacterCardState:
    """Simple in-process state for tracking the currently active CharacterCard.

    This is the primary shared state for UI modules: downstream logic often
    needs data cached on the card (e.g. derived parent UUIDs), not just the
    underlying Sophont.
    """

    value: Optional[CharacterCard] = None
    _listeners: list[CharacterCardListener] = field(default_factory=list, init=False, repr=False)

    def set(self, character_card: Optional[CharacterCard]) -> None:
        if character_card is self.value:
            return
        self.value = character_card
        for listener in list(self._listeners):
            listener(self.value)

    def subscribe(self, listener: CharacterCardListener) -> Callable[[], None]:
        self._listeners.append(listener)

        def unsubscribe() -> None:
            try:
                self._listeners.remove(listener)
            except ValueError:
                return

        return unsubscribe


active_character_card_state = ActiveCharacterCardState()


__all__ = [
    "ActiveCharacterCardState",
    "active_character_card_state",
]
