from __future__ import annotations

from textwrap import indent
from typing import ClassVar

from game.characteristic import Characteristic


class Phene:
    """
    Immutable package representing a phene.

    Attributes:
        characteristic: Characteristic - The characteristic represented by this phene.
        expression_precidence: int - The value modifying the characteristic.
        contributor_uuid: bytes - The context or source of the phene.
        is_grafted: bool - Indicates if the phene is grafted which will be used to determine permanence and other effects.
    """
    __slots__ = (
        'characteristic',
        'expression_precidence',
        'contributor_uuid',
        'is_grafted'
    )
    Key = tuple[Characteristic, int, bytes, bool]
    _cache: ClassVar[dict[Key, Phene]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        expression_precidence: int = 1,
        contributor_uuid: bytes = bytes(16),
        is_grafted: bool = False
    ) -> Phene:
        expression_precidence_int = int(expression_precidence)
        contributor_uuid_bytes = bytes(contributor_uuid)
        is_grafted_bool = bool(is_grafted) # Python bool/int behaviour enforcement for cache key consistency
        key = (
            characteristic,
            expression_precidence_int,
            contributor_uuid_bytes,
            is_grafted_bool
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "characteristic", characteristic)
        object.__setattr__(self, "expression_precidence", expression_precidence)
        object.__setattr__(self, "contributor_uuid", contributor_uuid)
        object.__setattr__(self, "is_grafted", is_grafted)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        characteristic: Characteristic,
        expression_precidence: int = 1,
        contributor_uuid: bytes = bytes(16),
        is_grafted: bool = False
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("PhenePackage instances are immutable")
    
    @classmethod
    def by_characteristic_name(
        cls,
        characteristic_name: str,
        expression_precidence: int = 1, 
        contributor_uuid: bytes = bytes(16),
        is_grafted: bool = False
    ) -> Phene:
        characteristic = Characteristic.by_name(characteristic_name)
        return cls(
            characteristic=characteristic,
            expression_precidence=expression_precidence,
            contributor_uuid=contributor_uuid,
            is_grafted=is_grafted
        )
    
    def __repr__(self) -> str:
        indentation = "  "
        _blank_uuid = bytes(16)
        display = []

        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"memory_pointer={memory_pointer_for_this_immutable_object}:")

        display.append(f"characteristic={self.characteristic!r}")
        display.append(f"expression_precidence={self.expression_precidence}")
        if self.contributor_uuid == _blank_uuid:
            display.append("contributor_uuid=BLANK")
        else:
            display.append(f"contributor_uuid={self.contributor_uuid!r}")
        display.append(f"is_grafted={self.is_grafted}")
        return "Phene(\n" + indent(",\n".join(display), indentation) + "\n)"