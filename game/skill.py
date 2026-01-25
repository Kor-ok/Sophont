from __future__ import annotations

from typing_extensions import TypeAlias

from game.mappings.set import ATTRIBUTES

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]


class Skill:
    """Immutable, interned (flyweight) skill descriptor.

    """

    __slots__ = ("master_category", "sub_category", "base_code")

    # Per-process interning cache: code -> Skill singleton
    _cache: dict[tuple[int, int, int], Skill] = {}

    def __new__(cls, master_category: int = -99, sub_category: int = -99, base_code: int = -99) -> Skill:
        master_int = int(master_category)
        sub_int = int(sub_category)
        code_int = int(base_code)
        key = (master_int, sub_int, code_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)

        # Bypass __setattr__ to initialize immutable slots.
        object.__setattr__(self, "master_category", master_int)
        object.__setattr__(self, "sub_category", sub_int)
        object.__setattr__(self, "base_code", code_int)

        cls._cache[key] = self
        return self

    def __init__(self, master_category: int = -99, sub_category: int = -99, base_code: int = -99) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Skill instances are immutable")

    @classmethod
    def of(cls, master_category: int = -99, sub_category: int = -99, base_code: int = -99) -> Skill:
        return cls(master_category, sub_category, base_code)
    
    @classmethod
    def by_name(cls, name: str) -> Skill:
        """Construct Skill flyweight by skill name lookup."""
        master_category, sub_category, base_code = ATTRIBUTES.skills.get_full_code(name)
        return cls(master_category, sub_category, base_code)
    
    @classmethod
    def by_code(cls, code: tuple[int, int, int]) -> Skill:
        master_category, sub_category, base_code = code
        return cls(master_category, sub_category, base_code)
    
    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Get the (canonical name, aliases) for this Skill."""
        return ATTRIBUTES.skills.get_aliases(
            (self.master_category, self.sub_category, self.base_code)
        )

    def __repr__(self) -> str:
        display = []
        skill_name = ATTRIBUTES.skills.get_aliases(
            (self.master_category, self.sub_category, self.base_code)
        )
        display.append(f"Skill(name={skill_name}, code=({self.master_category}, {self.sub_category}, {self.base_code}))")
        return f"Skill({', '.join(display)})"
        