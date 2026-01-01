from __future__ import annotations

from typing import ClassVar

from game.characteristic import Characteristic


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
        # Type Enforcement - Beneficial?
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
    
    def __repr__(self) -> str:
        return (
            f"\nGene(characteristic={repr(self.characteristic)}, die_mult={self.die_mult}, "
            f"precidence={self.precidence}, gender_link={self.gender_link}, "
            f"caste_link={self.caste_link}, "
            f"inheritance_contributors={self.inheritance_contributors}\n)"
        )
    
# class AppliedGene:
#     """
#     Immutable package representing a gene within a sophont's genetic profile which can be artificial.
#     It is immutable and flyweighted because the providor of the gene package should give consistent data
#     for many sophonts that gain the package.

#     gene: Gene
#     expression_value: int
#     contributor_uuid: bytes
#     is_grafted: bool
#     """
#     __slots__ = (
#         "gene",
#         "expression_value",
#         "contributor_uuid",
#         "is_grafted"
#     )
#     Key = Tuple[Gene, int, bytes, bool]
#     _cache: ClassVar[Dict[Key, "AppliedGene"]] = {}

#     def __new__(
#         cls,
#         gene: Gene,
#         expression_value: int,
#         contributor_uuid: bytes,
#         is_grafted: bool = False
#     ) -> "AppliedGene":
        
#         if contributor_uuid is None:
#             contributor_uuid = bytes(16)  # Default to nil UUID bytes
        
#         expression_value_int = int(expression_value)
#         is_grafted_bool = bool(is_grafted)

#         key = (
#             gene,
#             expression_value_int,
#             contributor_uuid,
#             is_grafted_bool
#         )
#         cached = cls._cache.get(key)
#         if cached is not None:
#             return cached
        
#         self = super().__new__(cls)

#         object.__setattr__(self, "gene", gene)
#         object.__setattr__(self, "expression_value", expression_value_int)
#         object.__setattr__(self, "contributor_uuid", contributor_uuid)
#         object.__setattr__(self, "is_grafted", is_grafted_bool)
#         cls._cache[key] = self
#         return self
    
#     def __init__(
#         self,
#         gene: Gene,
#         expression_value: int,
#         contributor_uuid: bytes,
#         is_grafted: bool = False
#     ) -> None:
#         # All initialization happens in __new__ (supports flyweight reuse).
#         pass

#     def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
#         raise AttributeError("GenePackage instances are immutable")
    
#     def __repr__(self) -> str:
#         return (
#             f"GenePackage(gene={repr(self.gene)}, expression_value={self.expression_value}, "
#             f"contributor_uuid={self.contributor_uuid}, "
#             f"is_grafted={self.is_grafted})"
#         )