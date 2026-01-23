from __future__ import annotations

from typing import ClassVar

from typing_extensions import TypeAlias

from game.mappings.set import ATTRIBUTES

CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCode = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
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
        upp_index, subtype, category_code = ATTRIBUTES.characteristics.get_full_code(name)
        return cls(upp_index, subtype, category_code)
    
    @classmethod
    def by_code(cls, code: FullCode) -> Characteristic:
        upp_index, subtype, category_code = code
        return cls(upp_index, subtype, category_code)

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        """Get the canonical name and aliases for this characteristic."""
        canonical_str_key, string_aliases = ATTRIBUTES.characteristics.get_aliases(
            (self.upp_index, self.subtype, self.category_code)
        )
        return canonical_str_key, string_aliases
    
    def __repr__(self) -> str:
        display = []
        characteristic_name = ATTRIBUTES.characteristics.get_aliases(
            (self.upp_index, self.subtype, self.category_code)
            )
        display.append(f"name={characteristic_name!r}")
        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"memory_pointer={memory_pointer_for_this_immutable_object}:")
        display.append(f"upp_index={self.upp_index}, subtype={self.subtype}, category_code={self.category_code}")
        
        return "Characteristic(\n  " + ",\n  ".join(display) + "\n)"