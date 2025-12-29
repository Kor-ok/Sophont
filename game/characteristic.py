from __future__ import annotations
from typing import Optional, ClassVar, Dict, Tuple

class Characteristic:

    __slots__ = (
        "upp_index",
        "subtype",
    )
    Key = Tuple[int, int]
    _cache: ClassVar[Dict[Key, "Characteristic"]] = {}

    def __new__(cls, upp_index: int = 0, subtype: int = 0) -> "Characteristic":
        # Type Enforcement - Beneficial?
        upp_index_int = int(upp_index)
        subtype_int = int(subtype)
        key = (upp_index_int, subtype_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "upp_index", upp_index_int)
        object.__setattr__(self, "subtype", subtype_int)

        cls._cache[key] = self
        return self
    
    def __init__(self, upp_index: int = 0, subtype: int = 0) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Characteristic instances are immutable")
    
    @classmethod
    def of(cls, upp_index: int = 0, subtype: int = 0) -> "Characteristic":
        """Explicit flyweight constructor (same as `Characteristic(upp_index, subtype)`)."""
        return cls(upp_index, subtype)
    
    @classmethod
    def by_name(cls, name: str) -> "Characteristic":
        from game.mappings.characteristics import name_to_position_code
        upp_index, subtype = name_to_position_code(name)
        if upp_index == -1 or subtype == -1:
            raise ValueError(f"Could not match characteristic name: {name!r}")
        return cls(upp_index, subtype)
    
    def __repr__(self) -> str:
        from game.mappings.characteristics import codes_to_name
        return (
            f"Characteristic(upp_index={self.upp_index}, subtype={self.subtype})"
            f"\n({codes_to_name(self.upp_index, self.subtype)})"
        )