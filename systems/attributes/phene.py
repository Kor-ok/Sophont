from __future__ import annotations

from components.primitives.data import CanonicalStrKey, FullCode, StringAliases
from systems.attributes.base import AppliedAttributeBase, AttributeSpecMixin
from systems.attributes.characteristic import Characteristic

# Type alias for the composite cache key
PheneKey = tuple[Characteristic, int, int, bool]

class Phene(AttributeSpecMixin,AppliedAttributeBase[PheneKey]):
    """
    Immutable flyweight representing a phene (non genetic element) linked to a Characteristic.

    A Phene extends a Characteristic with phenotypic expression modifiers:
        precedence: int - Weight of the phene when multiple same characteristics are present.
        contributor_guid: int - The context_guid or source of the phene.
        is_grafted: bool - Indicates if the phene is grafted which will be used to determine permanence and other effects.
    
    Implements: 
    - CompositeAttribute protocol (wraps Characteristic)
    - AttributeSpecMixin for standardized attribute specification handling
    """
    ATTRS = {
        "characteristic": Characteristic,
        "precedence": 1,
        "contributor_guid": -1,
        "is_grafted": False,
    }
    __slots__ = tuple(ATTRS.keys())

    characteristic: Characteristic
    
    precedence: int
    contributor_guid: int
    is_grafted: bool
    
    Key = PheneKey
    
    @classmethod
    def by_characteristic_name(cls, name: str, **kwargs) -> Phene:
        """
        Factory: construct Phene by looking up a Characteristic by name.

        Example:
            str_phene = Phene.by_characteristic_name("Strength", precedence=2)
        """
        characteristic = Characteristic.by_name(name)
        return cls(characteristic, **kwargs)
    
    @classmethod
    def by_characteristic_code(cls, code: FullCode, **kwargs) -> Phene:
        """
        Factory: construct Phene by looking up a Characteristic by FullCode.

        Example:
            social_phene = Phene.by_characteristic_code((5, 0, 3), precedence=1)
        """
        characteristic = Characteristic.by_code(code)
        return cls(characteristic, **kwargs)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        return self.characteristic.get_name()
    
    def get_code(self) -> FullCode:
        return self.characteristic.get_code()
    
