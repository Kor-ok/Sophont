from __future__ import annotations

from enum import Enum
from textwrap import indent
from typing import ClassVar, Final, Generic, TypeVar

from game.characteristic import Characteristic
from game.gene import Gene
from game.knowledge import Knowledge
from game.phene import Phene
from game.skill import Skill
from game.uid.guid import GUID, NameSpaces

T = TypeVar("T", Skill, Knowledge, Gene, Phene, Characteristic)

class TypeCategory(Enum):
    APTITUDE = "Aptitude"
    GENETIC = "Genetic"
    PERSONAL = "Personal"

_TYPE_CATEGORY_BY_CLASS: Final[dict[type[object], TypeCategory]] = {
    Skill: TypeCategory.APTITUDE,
    Knowledge: TypeCategory.APTITUDE,
    Gene: TypeCategory.GENETIC,
    Phene: TypeCategory.GENETIC,
    Characteristic: TypeCategory.PERSONAL,
}

class AttributePackage(Generic[T]):
    """Constructs reusable and shareable singleton packages that cumulatively modifies character attributes.
    i.e. a "context" such as an event can provide a choice of Skill, Knowledge, Gene, Phene or Characteristic packages
    with a value modifier.

    :param item: The Skill, Knowledge, Gene, Phene or Characteristic flyweight item.
    :param level: The level modifier to apply when this package is used.
    :param context: Storytelling aid to identify the source or reason for this package.
        If omitted/None, a fresh UUID string is generated for each new package.
    :type item: Skill|Knowledge|Gene|Phene|Characteristic
    :type level: int
    :type context: int
    """
    __slots__ = ("item", "level", "context")
    _cache: ClassVar[dict[tuple[object, int, int], AttributePackage]] = {}

    def __new__(cls, item: T, level: int = 0, context_id: int | None = None) -> AttributePackage[T]:
        context_id = GUID.generate(NameSpaces.Entity.PACKAGES, NameSpaces.Owner.PLAYER) if context_id is None else context_id
        key = (item, int(level), int(context_id))  # item is already a flyweight => stable identity
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        object.__setattr__(self, "item", item)
        object.__setattr__(self, "level", int(level))
        object.__setattr__(self, "context", int(context_id))

        cls._cache[key] = self
        return self

    def __init__(self, item: T, level: int = 0, context: int | None = None) -> None:
        pass

    def __setattr__(self, key: str, value: object) -> None:
        raise AttributeError("Package instances are immutable")
    
    def get_type_category(self) -> TypeCategory:
        try:
            return _TYPE_CATEGORY_BY_CLASS[type(self.item)]
        except KeyError as e:
            raise TypeError(f"Unsupported item type for AttributePackage: {type(self.item)!r}") from e

    def __repr__(self) -> str:
        indentation = "  "
        display = []
        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"# Immutable AttributePackage at {memory_pointer_for_this_immutable_object}")
        display.append(f"item={self.item!r}")
        display.append(f"level={self.level!r}")
        display.append(f"context={self.context!r}")
        return "AttributePackage(\n" + indent(",\n".join(display), indentation) + "\n)"