from __future__ import annotations

from typing import Final, Optional

from game.mappings.characteristics import Characteristics
from game.mappings.knowledges import Knowledges
from game.mappings.skills import Skills


class AttributesSet:
    """App-wide store for RPG skills, knowleges, characteristics and future extensions like certifications.

    This is implemented as a singleton so all callers share the same store:

    ATTRIBUTES = AttributesSet()  # always returns the same instance
    """

    __slots__ = (
        "skills",
        "knowledges",
        "characteristics",
        "_is_initialised",
    )

    # Explicit attribute annotations are important for IDE type inference.
    # Without them, Pylance often treats `ATTRIBUTES.characteristics` as `Any`
    # because it is assigned dynamically via `object.__setattr__` in `__new__`.
    skills: Skills
    knowledges: Knowledges
    characteristics: Characteristics
    """Manages Characteristics data.

    Args:
        default_collection: AliasMappedFullCodeCollection
        custom_collection: AliasMappedFullCodeCollection
        combined_collection: AliasMappedFullCodeCollection

    Functions:
        get_aliases(full_code: FullCode) -> tuple[CanonicalStrKey, StringAliases]
        get_full_code(alias: str) -> FullCode
    """
    _is_initialised: bool

    _instance: Optional[AttributesSet] = None

    def __new__(cls) -> AttributesSet:
        if cls._instance is not None:
            return cls._instance

        self = super().__new__(cls)
        object.__setattr__(self, "skills", Skills())
        object.__setattr__(self, "knowledges", Knowledges())
        object.__setattr__(self, "characteristics", Characteristics())

        object.__setattr__(self, "_is_initialised", False)

        cls._instance = self
        return self

    def __init__(self) -> None:
        if self._is_initialised:
            return
        object.__setattr__(self, "_is_initialised", True)


# Convenience singleton instance for app-wide usage.
ATTRIBUTES: Final[AttributesSet] = AttributesSet()
"""App-wide store for RPG skills, knowleges, characteristics and future extensions like certifications.

Args:
    skills: Skills
    knowledges: Knowledges
    characteristics: Characteristics

"""
