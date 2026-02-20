from __future__ import annotations

from enum import Enum
from typing import Final, Generic, TypeVar

from systems.attributes.base import AppliedAttributeBase
from systems.attributes.characteristic import Characteristic
from systems.attributes.gene import Gene
from systems.attributes.knowledge import Knowledge
from systems.attributes.phene import Phene
from systems.attributes.skill import Skill

from utils.guid import GUID

T = TypeVar("T", Skill, Knowledge, Gene, Phene, Characteristic)
"""
Type variable constraining the wrapped attribute type.

AttributePackage[T] is parameterized by this, allowing type-safe access
to the wrapped item while sharing a single flyweight cache.
"""
PackageKey = tuple[object, int, int, int]


class TypeCategory(Enum):
    """
    Semantic category for attribute types.

    Used by AttributePackage.get_type_category() to classify the wrapped item
    without requiring isinstance() checks in downstream code.
    """

    APTITUDE = "Aptitude"
    """Skills and Knowledges: training/experience-based attributes."""

    GENETIC = "Genetic"
    """Genes and Phenes: inherited/biological attributes."""

    PERSONAL = "Personal"
    """Characteristics, Locations, Activity etc: current state modifiers."""


_TYPE_CATEGORY_BY_CLASS: Final[dict[type[object], TypeCategory]] = {
    Skill: TypeCategory.APTITUDE,
    Knowledge: TypeCategory.APTITUDE,
    Gene: TypeCategory.GENETIC,
    Phene: TypeCategory.GENETIC,
    Characteristic: TypeCategory.PERSONAL,
}
"""
Mapping from attribute class to its semantic category.

Used by get_type_category() for O(1) lookup instead of isinstance() chains.
"""


class AttributePackage(AppliedAttributeBase[PackageKey], Generic[T]):
    """
    Immutable flyweight that wraps any attribute with level and duration modifiers.

    A package represents a "buff" or "debuff" applied to a character:
    - The wrapped `item` is any attribute flyweight (Skill, Knowledge, Gene, etc.)
    - `level` is the modifier value (+2 Strength, -1 Pilot, etc.)
    - `duration_seconds` controls how long the effect lasts (-1 = permanent)
    - `context_guid` tracks the source/reason for this package

    Each unique combination of (item, level, duration, guid) maps to exactly one
    AttributePackage instance in memory (flyweight identity guarantee).

    Hierarchy: AttributePackage is a PolymorphicComposite that can wrap any attribute.
    """

    __slots__ = ("item", "level", "duration_seconds", "context_guid")
   
    item: T
    """The wrapped attribute flyweight (Skill, Knowledge, Gene, Phene, or Characteristic)."""
    level: int
    duration_seconds: int
    context_guid: int

    Key = PackageKey

    def __new__(
        cls,
        item: T,
        level: int = 0,
        duration_seconds: int = -1,
        context_guid: int | None = None,
    ) -> AttributePackage[T]:
        
        resolved_guid = (
            GUID.generate(GUID.NameSpaces.Entity.PACKAGES, GUID.NameSpaces.Owner.PLAYER)
            if context_guid is None
            else context_guid
        )

        key: PackageKey = (item, int(level), int(duration_seconds), int(resolved_guid))

        cached, found = cls._cache_get_or_create(key)
        if found:
            return cached  # type: ignore[return-value]

        self = super().__new__(cls)

        self._set_attr("item", item)
        self._set_attr("level", int(level))
        self._set_attr("duration_seconds", int(duration_seconds))
        self._set_attr("context_guid", int(resolved_guid))

        cls._cache_set(key, self)
        return self


    def get_type_category(self) -> TypeCategory:
        item_type = type(self.item)
        try:
            return _TYPE_CATEGORY_BY_CLASS[item_type]
        except KeyError as e:
            raise TypeError(f"Unsupported item type for AttributePackage: {item_type!r}") from e
