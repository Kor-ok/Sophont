from __future__ import annotations
from typing import ClassVar, Dict, Generic, Tuple, TypeVar
from uuid import uuid4

T = TypeVar("T")  # Skill or Knowledge (or anything else immutable)

class AptitudePackage(Generic[T]):
    """Constructs reusable and shareable singleton packages that cumulatively modifies character aptitudes.
    i.e. a "context" such as an event can provide a choice of Skill, Knowledge or other (like Certifications)
    packages with a delta level modifier.

    :param item: The Skill, Knowledge or other immutable flyweight item.
    :param level: The level modifier to apply when this package is used.
    :param context: Storytelling aid to identify the source or reason for this package.
        If omitted/None, a fresh UUID string is generated for each new package.
    :type item: T|Skill|Knowledge
    :type level: int
    :type context: str
    """
    __slots__ = ("item", "level", "context")
    _cache: ClassVar[Dict[Tuple[object, int, str], "AptitudePackage"]] = {}

    def __new__(cls, item: T, level: int = 0, context: str | None = None) -> "AptitudePackage[T]":
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