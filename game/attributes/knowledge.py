from __future__ import annotations

from typing import ClassVar

from typing_extensions import TypeAlias

from game.mappings.set import ATTRIBUTES

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]

class Knowledge:

    __slots__ = ("base_code", "associated_skill", "focus")

    _cache: ClassVar[dict[tuple[int, int, int], Knowledge]] = {}

    def __new__(cls, base_code: int = -99, associated_skill: int = -99, focus: int = -99) -> Knowledge:
        base_code_int = int(base_code)
        associated_skill_int = int(associated_skill)
        focus_int = int(focus)
        
        key = (base_code_int, associated_skill_int, focus_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)

        object.__setattr__(self, "base_code", base_code_int)
        object.__setattr__(self, "associated_skill", associated_skill_int)
        object.__setattr__(self, "focus", focus_int)

        cls._cache[key] = self
        return self
    
    def __init__(self, base_code: int = -99, associated_skill: int = -99, focus: int = -99) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Knowledge instances are immutable")
    
    @classmethod
    def of(cls, base_code: int, associated_skill: int = -99, focus: int = -99) -> Knowledge:
        """Explicit flyweight constructor (same as `Knowledge(base_code)`)."""
        return cls(base_code, associated_skill, focus)
    
    @classmethod
    def by_name(cls, name: str) -> Knowledge:
        """Construct Knowledge flyweight by knowledge name lookup."""
        base_knowledge_code, associated_skill_code, focus_code = ATTRIBUTES.knowledges.get_full_code(name)
        return cls(base_knowledge_code, associated_skill_code, focus_code)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Get the (canonical name, aliases) for this Knowledge."""
        return ATTRIBUTES.knowledges.get_aliases(
            (self.base_code, self.associated_skill, self.focus)
        )
    
    def __repr__(self) -> str:
        display = []
        knowledge_name = ATTRIBUTES.knowledges.get_aliases(
            (self.base_code, self.associated_skill, self.focus)
        )
        display.append(f"Knowledge(name={knowledge_name}, code=({self.base_code}, {self.associated_skill}, {self.focus}))")
        return "<" + " ".join(display) + ">"
