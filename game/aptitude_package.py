from __future__ import annotations

from textwrap import indent
from typing import ClassVar, Generic, TypeVar
from uuid import uuid4

from game.knowledge import Knowledge
from game.skill import Skill

T = TypeVar("T", Skill, Knowledge)  # Skill or Knowledge (or anything else immutable)

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
    _cache: ClassVar[dict[tuple[object, int, str], AptitudePackage]] = {}

    def __new__(cls, item: T, level: int = 0, context: str | None = None) -> AptitudePackage[T]:
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
        indentation = "  "
        display = []
        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"# Immutable AptitudePackage at {memory_pointer_for_this_immutable_object}")
        display.append(f"item={self.item!r}")
        display.append(f"level={self.level!r}")
        display.append(f"context={self.context!r}")
        return "AptitudePackage(\n" + indent(",\n".join(display), indentation) + "\n)"