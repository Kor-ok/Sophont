from __future__ import annotations
from typing import Optional, ClassVar, Dict, Tuple
from uuid import uuid4

class Knowledge:

    __slots__ = ("code", "focus", "associated_skill", "unique_id")

    _cache: ClassVar[Dict[Tuple[int, str, int], "Knowledge"]] = {}

    def __new__(cls, code: int = -99, focus: Optional[str] = None, associated_skill: Optional[int] = -99) -> "Knowledge":
        code_int = int(code)
        focus_str = "" if focus is None else str(focus)
        associated_skill_int = int(associated_skill) if associated_skill is not None else -99
        
        key = (code_int, focus_str, associated_skill_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached

        self = super().__new__(cls)

        object.__setattr__(self, "code", code_int)
        object.__setattr__(self, "focus", focus_str)
        object.__setattr__(self, "associated_skill", associated_skill_int)
        
        object.__setattr__(self, "unique_id", uuid4().bytes)

        cls._cache[key] = self
        return self
    
    def __init__(self, code: int = -99, focus: Optional[str] = None, associated_skill: Optional[int] = -99) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Knowledge instances are immutable")
    
    @classmethod
    def of(cls, code: int, focus: Optional[str] = None, associated_skill: Optional[int] = -99) -> "Knowledge":
        """Explicit flyweight constructor (same as `Knowledge(code)`)."""
        return cls(code, focus, associated_skill)
    
    def __repr__(self) -> str:
        from game.mappings.skills import Table, code_to_string
        return (
            f"Knowledge(code={self.code}[{code_to_string(self.code, Table.KNOWLEDGES)}]," 
            f' focus="{self.focus}", '
            f"associated_skill={self.associated_skill}[{code_to_string(self.associated_skill, Table.BASE)}],"
            f' unique_id="{self.unique_id}")'
        )

