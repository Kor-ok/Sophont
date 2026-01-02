from __future__ import annotations

from typing import ClassVar


class Characteristic:

    __slots__ = (
        "upp_index",
        "subtype",
        "category_code",
    )
    Key = tuple[int, int, int]
    _cache: ClassVar[dict[Key, Characteristic]] = {}

    def __new__(cls, upp_index: int = 0, subtype: int = 0, category_code: int = 0) -> Characteristic:
        upp_index_int = int(upp_index)
        subtype_int = int(subtype)
        category_code_int = int(category_code)
        key = (upp_index_int, subtype_int, category_code_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "upp_index", upp_index_int)
        object.__setattr__(self, "subtype", subtype_int)
        object.__setattr__(self, "category_code", category_code_int)

        cls._cache[key] = self
        return self
    
    def __init__(self, upp_index: int = 0, subtype: int = 0, category_code: int = 0) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Characteristic instances are immutable")
    
    @classmethod
    def of(cls, upp_index: int = 0, subtype: int = 0, category_code: int = 0) -> Characteristic:
        """Explicit flyweight constructor (same as `Characteristic(upp_index, subtype, category_code)`)."""
        return cls(upp_index, subtype, category_code)
    
    @classmethod
    def by_name(cls, name: str) -> Characteristic:
        from game.mappings.characteristics import name_to_position_code
        upp_index, subtype = name_to_position_code(name)
        if upp_index == -1 or subtype == -1:
            raise ValueError(f"Could not match characteristic name: {name!r}")
        return cls(upp_index, subtype)
    
    def get_name(self) -> str:
        from game.mappings.characteristics import codes_to_name
        return codes_to_name(self.upp_index, self.subtype)
    
    def __repr__(self) -> str:
        from game.mappings.characteristics import codes_to_name
        display = []
        characteristic_name = codes_to_name(self.upp_index, self.subtype)
        display.append(f"name={characteristic_name!r}")
        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"memory_pointer={memory_pointer_for_this_immutable_object}:")
        display.append(f"upp_index={self.upp_index}, subtype={self.subtype}, category_code={self.category_code}")
        
        return "Characteristic(\n  " + ",\n  ".join(display) + "\n)"