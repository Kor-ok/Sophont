from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from typing import Any, Callable


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
    def highest_master_category_code(self) -> int:
        return self.primary_code

    @highest_master_category_code.setter
    def highest_master_category_code(self, value: int) -> None:
        self.primary_code = int(value)

    @property
    def highest_sub_category_code(self) -> int:
        return self.secondary_code

    @highest_sub_category_code.setter
    def highest_sub_category_code(self, value: int) -> None:
        self.secondary_code = int(value)

    @property
    def highest_base_code(self) -> int:
        return self.tertiary_code

    @highest_base_code.setter
    def highest_base_code(self, value: int) -> None:
        self.tertiary_code = int(value)

FullCode = tuple[int, int, int]
NormalizedAlias = str
class DirtyDict(dict[NormalizedAlias, FullCode]):
    __slots__ = ("_mark_dirty",)

    def __init__(
        self,
        *args: object,
        mark_dirty: Callable[[], None],
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._mark_dirty = mark_dirty

    def __setitem__(self, key: NormalizedAlias, value: FullCode) -> None:  # type: ignore[override]
        self._mark_dirty()
        return super().__setitem__(key, value)

    def __delitem__(self, key: NormalizedAlias) -> None:  # type: ignore[override]
        self._mark_dirty()
        return super().__delitem__(key)

    def clear(self) -> None:  # type: ignore[override]
        if self:
            self._mark_dirty()
        return super().clear()

    def pop(self, key: NormalizedAlias, default: object = None):  # type: ignore[override]
        if key in self:
            self._mark_dirty()
        return super().pop(key, default)

    def popitem(self):  # type: ignore[override]
        if self:
            self._mark_dirty()
        return super().popitem()

    def setdefault(self, key: NormalizedAlias, default: FullCode):  # type: ignore[override]
        if key not in self:
            self._mark_dirty()
        return super().setdefault(key, default)

    def update(self, *args: Any, **kwargs: Any) -> None:  # type: ignore[override]
        if args or kwargs:
            self._mark_dirty()
        super().update(*args, **kwargs)