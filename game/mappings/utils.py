from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache

# from typing import Any, Callable


@lru_cache(maxsize=4096)
def _normalize(name: str | Iterable[str]) -> str:
    """Normalize a skill/aptitude/knowledge name for consistent lookup.
    - case-insensitive + collapses repeated whitespace (e.g. "social   standing")
    - Also works with tuples of strings.
    """
    if isinstance(name, Iterable) and not isinstance(name, str):
        name = " ".join(name)

    return " ".join(name.strip().casefold().split())


class AttributeViewHeader:
    """Header for attribute views, preventing the overhead of
    iterating over mappings when not needed.

    For instance, the starting key for new custom skills will
    be one higher than the highest existing default skill code or custom skill code.

    - Skill code is (master_category, sub_category, base_skill)
    - Knowledge code is (base_knowledge_code, associated_skill_code, focus_code)
    - Characteristic code is (position_code, subtype_code, master_code)
    """

    def __init__(self) -> None:
        self.primary_code: int = -1
        self.secondary_code: int = -1
        self.tertiary_code: int = -1

    @property
    def highest_primary_code(self) -> int:
        return self.primary_code

    @highest_primary_code.setter
    def highest_primary_code(self, value: int) -> None:
        self.primary_code = int(value)

    @property
    def highest_secondary_code(self) -> int:
        return self.secondary_code

    @highest_secondary_code.setter
    def highest_secondary_code(self, value: int) -> None:
        self.secondary_code = int(value)

    @property
    def highest_tertiary_code(self) -> int:
        return self.tertiary_code

    @highest_tertiary_code.setter
    def highest_tertiary_code(self, value: int) -> None:
        self.tertiary_code = int(value)


