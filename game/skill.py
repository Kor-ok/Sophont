from __future__ import annotations

from game.mappings.skills import get_base_skill_code_from_name, get_category_codes_from_skill_code
from game.uid.guid import uuid4


class Skill:
    """Immutable, interned (flyweight) skill descriptor.

    - Instantiate with just `code`: `Skill(38)`
    - The same `code` always returns the same instance (flyweight)
    - `master_category` and `sub_category` are derived once at creation
    """

    __slots__ = ("code", "master_category", "sub_category", "unique_id")

    # Per-process interning cache: code -> Skill singleton
    _cache: dict[tuple[int, int, int], Skill] = {}

    def __new__(cls, code: int = -99) -> Skill:
        code_int = int(code)
        master, sub = get_category_codes_from_skill_code(code_int)
        key = (code_int, master, sub)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)

        # Bypass __setattr__ to initialize immutable slots.
        object.__setattr__(self, "code", code_int)
        object.__setattr__(self, "master_category", master)
        object.__setattr__(self, "sub_category", sub)

        object.__setattr__(self, "unique_id", uuid4().bytes)

        cls._cache[key] = self
        return self

    def __init__(self, code: int = -99) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Skill instances are immutable")

    @classmethod
    def of(cls, code: int) -> Skill:
        """Explicit flyweight constructor (same as `Skill(code)`)."""
        return cls(code)
    
    @classmethod
    def by_skill_name(cls, name: str) -> Skill:
        """Construct Skill flyweight by skill name lookup."""
        code = get_base_skill_code_from_name(name)
        return cls.of(code)

    def __repr__(self) -> str:
        from game.mappings.skills import Table, code_to_string
        return (
            f"Skill(code={self.code}[{code_to_string(self.code, Table.BASE)}], "
            f"master_category={self.master_category}[{code_to_string(self.master_category, Table.MASTER_CATEGORY)}], "
            f"sub_category={self.sub_category}[{code_to_string(self.sub_category, Table.SUB_CATEGORY)}])"
        )
    
    def apply_knowledge(self, knowledge_code: int, focus: str | None = None):
        """Create a Knowledge instance associated with this Skill."""
        from game.knowledge import Knowledge  # Avoid circular import
        return Knowledge.of(knowledge_code, focus=focus, associated_skill=self.code)
        