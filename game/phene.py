from __future__ import annotations

from textwrap import indent
from typing import ClassVar

from game.characteristic import Characteristic


class Phene:
    """
    Immutable package representing a phene.

    Attributes:
        characteristic: Characteristic - The characteristic represented by this phene.
        expression_value: int - The value modifying the characteristic.
        contributor_uuid: bytes - The context or source of the phene.
        is_grafted: bool - Indicates if the phene is grafted which will be used to determine permanence and other effects.
    """
    __slots__ = (
        'characteristic',
        'expression_value',
        'contributor_uuid',
        'is_grafted'
    )
    Key = tuple[Characteristic, int, bytes, bool]
    _cache: ClassVar[dict[Key, Phene]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        expression_value: int,
        contributor_uuid: bytes,
        is_grafted: bool
    ) -> Phene:
        key = (
            characteristic,
            expression_value,
            contributor_uuid,
            is_grafted
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "characteristic", characteristic)
        object.__setattr__(self, "expression_value", expression_value)
        object.__setattr__(self, "contributor_uuid", contributor_uuid)
        object.__setattr__(self, "is_grafted", is_grafted)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        characteristic: Characteristic,
        expression_value: int,
        contributor_uuid: bytes,
        is_grafted: bool
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("PhenePackage instances are immutable")
    
    @classmethod
    def by_characteristic_name(
        cls,
        characteristic_name: str,
        expression_value: int = 0, # 0 For a Phene would act as a way to impliment a "placeholder" for the characteristic akin to a gene 
        contributor_uuid: bytes = bytes(16),
        is_grafted: bool = False
    ) -> Phene:
        characteristic = Characteristic.by_name(characteristic_name)
        return cls(
            characteristic=characteristic,
            expression_value=expression_value,
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
        display.append(f"expression_value={self.expression_value}")
        if self.contributor_uuid == _blank_uuid:
            display.append("contributor_uuid=BLANK")
        else:
            display.append(f"contributor_uuid={self.contributor_uuid!r}")
        display.append(f"is_grafted={self.is_grafted}")
        return "Phene(\n" + indent(",\n".join(display), indentation) + "\n)"