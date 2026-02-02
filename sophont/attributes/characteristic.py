from __future__ import annotations

from game.primitives.data import CanonicalStrKey, FullCode, StringAliases
from game.primitives.set import ATTRIBUTES
from sophont.attributes.base import AppliedAttributeBase


class Characteristic(AppliedAttributeBase[FullCode]):
    """
    Immutable flyweight representing a character characteristic (e.g., Strength, Dexterity).

    Implements: FullCodeAttribute protocol (position_code, subtype_code, master_code)
    where position_code is the T5 UPP index, subtype is the characteristic variant (e.g. Agility),
    and master (e.g. Physical, Social) is used downstream for genetics and other systems.
    """
    __slots__ = ("code",)
    code: FullCode
    Key = FullCode

    def __new__(cls, code: FullCode = (-99, -99, -99)) -> Characteristic:

        cached, found = cls._cache_get_or_create(code)
        if found:
            return cached  # type: ignore[return-value]

        self = super().__new__(cls)
        self._set_attr("code", code)
        cls._cache_set(code, self)
        return self


    @classmethod
    def by_name(cls, name: str) -> Characteristic:
        """
        Factory: construct Characteristic flyweight by name lookup.

        Uses the ATTRIBUTES registry to resolve human-readable names/aliases
        to their corresponding FullCode, then returns the cached flyweight.

        Example:
            strength = Characteristic.by_name("Strength")
            str_alias = Characteristic.by_name("Str")  # Same object
        """
        full_code = ATTRIBUTES.characteristics.get_full_code(name)
        return cls(full_code)

    @classmethod
    def by_code(cls, code: FullCode) -> Characteristic:
        """
        Factory: construct Characteristic flyweight by FullCode tuple.

        (position_code, subtype_code, master_code)

        Example:
            dex = Characteristic.by_code((1, 0, 0))
        """
        return cls(code)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """
        Get the canonical name and aliases for this characteristic.

        Returns:
            (canonical_name, (alias1, alias2, ...))

        Example:
            name, aliases = Characteristic.by_name("Str").get_name()
            # name = "Strength", aliases = ("Str", "STR", ...)
        """
        return ATTRIBUTES.characteristics.get_aliases(self.code)

    def get_code(self) -> FullCode:
        """
        Get the FullCode tuple for this characteristic.

        Returns:
            (position_code, subtype_code, master_code)
        """
        return self.code
