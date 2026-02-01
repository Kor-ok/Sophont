from __future__ import annotations

from textwrap import indent
from typing import ClassVar

from game.characteristic import Characteristic
from game.mappings.data import CanonicalStrKey, FullCode, StringAliases


class Gene:
    """
    Immutable flyweight representing a gene.
    
    """
    __slots__ = (
        "characteristic",
        "die_mult",
        "precidence",
        "gender_link",
        "caste_link", # Added
        "inheritance_contributors"
    )
    characteristic: Characteristic

    Key = tuple[Characteristic, int, int, int, int, int]
    _cache: ClassVar[dict[Key, Gene]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        die_mult: int = 1,
        precidence: int = 0,
        gender_link: int = -1,
        caste_link: int = -1,  # Added
        inheritance_contributors: int = 2
    ) -> Gene:
        die_mult_int = int(die_mult)
        precidence_int = int(precidence)
        gender_link_int = int(gender_link)
        caste_link_int = int(caste_link) # Added
        inheritance_contributors_int = int(inheritance_contributors)
        key = (
            characteristic,
            die_mult_int,
            precidence_int,
            gender_link_int,
            caste_link_int,  # Added
            inheritance_contributors_int
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "characteristic", characteristic)
        object.__setattr__(self, "die_mult", die_mult_int)
        object.__setattr__(self, "precidence", precidence_int)
        object.__setattr__(self, "gender_link", gender_link_int)
        object.__setattr__(self, "caste_link", caste_link_int)  # Added
        object.__setattr__(self, "inheritance_contributors", inheritance_contributors_int)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        characteristic: Characteristic,
        die_mult: int = 1,
        precidence: int = 0,
        gender_link: int = -1,
        caste_link: int = -1,  # Added
        inheritance_contributors: int = 2
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("Gene instances are immutable")
    
    @classmethod
    def by_characteristic_name(
        cls,
        characteristic_name: str,
        die_mult: int = 1,
        precidence: int = 0,
        gender_link: int = -1,
        caste_link: int = -1,  # Added
        inheritance_contributors: int = 2
    ) -> Gene:
        
        characteristic = Characteristic.by_name(characteristic_name)

        return cls(
            characteristic,
            die_mult,
            precidence,
            gender_link,
            caste_link,  # Added
            inheritance_contributors
        )
    
    @classmethod
    def by_characteristic_code(
        cls,
        characteristic_code: FullCode,
        die_mult: int = 1,
        precidence: int = 0,
        gender_link: int = -1,
        caste_link: int = -1,  # Added
        inheritance_contributors: int = 2
    ) -> Gene:
        characteristic = Characteristic.by_code(characteristic_code)
        return cls(
            characteristic,
            die_mult,
            precidence,
            gender_link,
            caste_link,  # Added
            inheritance_contributors
        )

    def get_name(self) -> tuple[CanonicalStrKey, StringAliases]:
        return self.characteristic.get_name()
    
    def get_code(self) -> FullCode:
        return self.characteristic.get_code()
    
    def __repr__(self) -> str:
        indentation = "  "
        display = []

        memory_pointer_for_this_immutable_object = hex(id(self))
        display.append(f"memory_pointer={memory_pointer_for_this_immutable_object}")

        display.append(f"characteristic={repr(self.characteristic)}")
        display.append(f"die_mult={self.die_mult}")
        display.append(f"precidence={self.precidence}")
        display.append(f"gender_link={self.gender_link}")
        display.append(f"caste_link={self.caste_link}")  # Added
        display.append(f"inheritance_contributors={self.inheritance_contributors}")
        return "Gene(\n" + indent(",\n".join(display), indentation) + "\n)"
    
