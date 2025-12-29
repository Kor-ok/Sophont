from __future__ import annotations
from typing import ClassVar, Dict, Generic, Tuple, TypeVar, Union
from uuid import uuid4

T = TypeVar("T") 

class CharacteristicPackage(Generic[T]):
    """Constructs reusable and shareable singleton packages that cumulatively modifies character characteristics.
    i.e. a "context" such as an event can provide a choice of Gene or Phene packages with a genetic value modifier.

    :param item: The Gene, Phene or other immutable flyweight item.
    :param level: The level modifier to apply when this package is used.
    :param context: Storytelling aid to identify the source or reason for this package.
        If omitted/None, a fresh UUID string is generated for each new package.
    :type item: T|AppliedGene|AppliedPhene
    :type level: int
    :type context: str
    """
    __slots__ = ("item", "level", "context")
    _cache: ClassVar[Dict[Tuple[object, int, str], "CharacteristicPackage"]] = {}

    def __new__(cls, item: T, level: int = 0, context: str | None = None) -> "CharacteristicPackage[T]":
        context_str = str(uuid4()) if context is None else str(context)
        key = (item, int(level), context_str)  # item is already a flyweight => stable identity
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)
        object.__setattr__(self, "item", item)
        object.__setattr__(self, "level", int(level))
        object.__setattr__(self, "context", context_str)

        cls._cache[key] = self
        return self

    def __init__(self, item: T, level: int = 0, context: str | None = None) -> None:
        pass

    def __setattr__(self, key: str, value: object) -> None:
        raise AttributeError("Package instances are immutable")

    def __repr__(self) -> str:
        return (
            f"Package(item={self.item!r}, level={self.level}, context={self.context!r})"
            f"\nitem_type={type(self.item).__name__}:"
            f"\n  {self.item.__str__()}"
            )