from __future__ import annotations

from components.data import CanonicalStrKey, FullCode, StringAliases
from systems.attributes.base import AppliedAttributeBase, AttributeSpecMixin
from systems.attributes.characteristic import Characteristic

# Type alias for the composite cache key
GeneKey = tuple[Characteristic, int, int, int, int, int]


class Gene(AttributeSpecMixin, AppliedAttributeBase[GeneKey]):
    """
    Immutable flyweight representing a gene linked to a Characteristic.

    A Gene extends a Characteristic with genetic modifiers:
    - die_mult: Multiplier for dice rolls related to this gene
    - precedence: Priority when multiple genes affect the same characteristic
    - gender_link: Gender association (-1 = none, else gender code)
    - caste_link: Caste association (-1 = none, else caste code)
    - inheritance_contributors: Number of parents contributing to inheritance

    Implements: 
    - CompositeAttribute protocol (wraps Characteristic)
    - AttributeSpecMixin for standardized attribute specification handling
    """

    ATTRS = {
        "characteristic": Characteristic,
        "die_mult": 1,
        "precedence": 0,
        "gender_link": -1,
        "caste_link": -1,
        "inheritance_contributors": 2,
    }

    __slots__ = tuple(ATTRS.keys())

    characteristic: Characteristic

    die_mult: int
    precedence: int
    gender_link: int
    caste_link: int
    inheritance_contributors: int

    Key = GeneKey

    @classmethod
    def by_characteristic_name(cls, name: str, **kwargs) -> Gene:
        """
        Factory: construct Gene by looking up a Characteristic by name.

        Example:
            str_gene = Gene.by_characteristic_name("Strength", die_mult=2)
        """
        characteristic = Characteristic.by_name(name)
        return cls(characteristic, **kwargs)

    @classmethod
    def by_characteristic_code(cls, code: FullCode, **kwargs) -> Gene:
        """
        Factory: construct Gene by looking up a Characteristic by FullCode.

        Example:
            dex_gene = Gene.by_characteristic_code((2, 0, 0), precedence=1)
        """
        characteristic = Characteristic.by_code(code)
        return cls(characteristic, **kwargs)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        return self.characteristic.get_name()

    def get_code(self) -> FullCode:
        return self.characteristic.get_code()
