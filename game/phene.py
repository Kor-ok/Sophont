from __future__ import annotations
from typing import Any, Optional, ClassVar, Dict, Tuple
from uuid import uuid4

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
    Key = Tuple[Characteristic, int, bytes, bool]
    _cache: ClassVar[Dict[Key, "Phene"]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        expression_value: int,
        contributor_uuid: bytes,
        is_grafted: bool
    ) -> "Phene":
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

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("PhenePackage instances are immutable")
    
    def __repr__(self) -> str:
        return (
            f"PhenePackage(characteristic={repr(self.characteristic)}, "
            f"expression_value={self.expression_value}, "
            f"contributor_uuid={repr(self.contributor_uuid)}, "
            f"is_grafted={self.is_grafted})"
        )