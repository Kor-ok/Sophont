from __future__ import annotations

from textwrap import indent
from typing import ClassVar

from game.characteristic import Characteristic
from game.mappings.data import CanonicalStrKey, StringAliases

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCode = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]

class Phene:
    """
    Immutable package representing a phene.

    Attributes:
        characteristic: Characteristic - The characteristic represented by this phene.
        expression_precedence: int - The value modifying the characteristic.
        contributor_uuid: int - The context or source of the phene.
        is_grafted: bool - Indicates if the phene is grafted which will be used to determine permanence and other effects.
    """
    __slots__ = (
        'characteristic',
        'expression_precedence',
        'contributor_uuid',
        'is_grafted'
    )
    characteristic: Characteristic
    contributor_uuid: int
    
    Key = tuple[Characteristic, int, int, bool]
    _cache: ClassVar[dict[Key, Phene]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        expression_precedence: int = 1,
        contributor_uuid: int = -1,
        is_grafted: bool = False
    ) -> Phene:
        expression_precedence_int = int(expression_precedence)
        contributor_uuid_int = int(contributor_uuid)
        is_grafted_bool = bool(is_grafted) # Python bool/int behaviour enforcement for cache key consistency
        key = (
            characteristic,
            expression_precedence_int,
            contributor_uuid_int,
            is_grafted_bool
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "characteristic", characteristic)
        object.__setattr__(self, "expression_precedence", expression_precedence)
        object.__setattr__(self, "contributor_uuid", contributor_uuid)
        object.__setattr__(self, "is_grafted", is_grafted)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        characteristic: Characteristic,
        expression_precedence: int = 1,
        contributor_uuid: int = -1,
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
        expression_precedence: int = 1, 
        contributor_uuid: int = -1,
        is_grafted: bool = False
    ) -> Phene:
        characteristic = Characteristic.by_name(characteristic_name)
        return cls(
            characteristic=characteristic,
            expression_precedence=expression_precedence,
            contributor_uuid=contributor_uuid,
            is_grafted=is_grafted
        )
    
    @classmethod
    def by_characteristic_code(
        cls,
        characteristic_code: FullCode,
        expression_precedence: int = 1, 
        contributor_uuid: int = -1,
        is_grafted: bool = False
    ) -> Phene:
        characteristic = Characteristic.by_code(characteristic_code)
        return cls(
            characteristic=characteristic,
            expression_precedence=expression_precedence,
            contributor_uuid=contributor_uuid,
            is_grafted=is_grafted
        )
    
    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Get the canonical name and aliases for this phene's characteristic."""
        return self.characteristic.get_name()
    
    def get_code(self) -> FullCode:
        """Get the full code for this phene's characteristic."""
        return self.characteristic.get_code()
    
    def __repr__(self) -> str:
        indentation = "  "
        _blank_uuid = -1
        display = []

        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"memory_pointer={memory_pointer_for_this_immutable_object}:")

        display.append(f"characteristic={self.characteristic!r}")
        display.append(f"expression_precedence={self.expression_precedence}")
        if self.contributor_uuid == _blank_uuid:
            display.append("contributor_uuid=BLANK")
        else:
            display.append(f"contributor_uuid={self.contributor_uuid!r}")
        display.append(f"is_grafted={self.is_grafted}")
        return "Phene(\n" + indent(",\n".join(display), indentation) + "\n)"