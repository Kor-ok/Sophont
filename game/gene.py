from __future__ import annotations
from typing import Optional, ClassVar, Dict, Tuple
from uuid import uuid4

from game.characteristic import Characteristic

class Gene:
    """
    Immutable flyweight representing a gene.
    
    """
    __slots__ = (
        "characteristic",
        "die_num",
        "precidence",
        "gender_link",
        "inheritance_contributors"
    )
    Key = Tuple[Characteristic, int, int, int, int]
    _cache: ClassVar[Dict[Key, "Gene"]] = {}

    def __new__(
        cls,
        characteristic: Characteristic,
        die_num: int = 2,
        precidence: int = 0,
        gender_link: int = -1,
        inheritance_contributors: int = 2
    ) -> "Gene":
        # Type Enforcement - Beneficial?
        die_num_int = int(die_num)
        precidence_int = int(precidence)
        gender_link_int = int(gender_link)
        inheritance_contributors_int = int(inheritance_contributors)
        key = (
            characteristic,
            die_num_int,
            precidence_int,
            gender_link_int,
            inheritance_contributors_int
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "characteristic", characteristic)
        object.__setattr__(self, "die_num", die_num_int)
        object.__setattr__(self, "precidence", precidence_int)
        object.__setattr__(self, "gender_link", gender_link_int)
        object.__setattr__(self, "inheritance_contributors", inheritance_contributors_int)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        characteristic: Characteristic,
        die_num: int = 2,
        precidence: int = 0,
        gender_link: int = -1,
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
        die_num: int = 2,
        precidence: int = 0,
        gender_link: int = -1,
        inheritance_contributors: int = 2
    ) -> "Gene":
        
        characteristic = Characteristic.by_name(characteristic_name)

        return cls(
            characteristic,
            die_num,
            precidence,
            gender_link,
            inheritance_contributors
        )
    
    def __repr__(self) -> str:
        return (
            f"Gene(characteristic={repr(self.characteristic)}, die_num={self.die_num}, "
            f"precidence={self.precidence}, gender_link={self.gender_link}, "
            f"inheritance_contributors={self.inheritance_contributors})"
        )
    
class AppliedGene:
    """
    Immutable package representing a gene within a sophont's genetic profile which can be artificial.
    It is immutable and flyweighted because the providor of the gene package should give consistent data
    for many sophonts that gain the package.

    gene: Gene
    expression_value: int
    contributor_uuid: bytes
    is_grafted: bool
    """
    __slots__ = (
        "gene",
        "expression_value",
        "contributor_uuid",
        "is_grafted"
    )
    Key = Tuple[Gene, int, bytes, bool]
    _cache: ClassVar[Dict[Key, "AppliedGene"]] = {}

    def __new__(
        cls,
        gene: Gene,
        expression_value: int,
        contributor_uuid: bytes,
        is_grafted: bool = False
    ) -> "AppliedGene":
        
        if contributor_uuid is None:
            contributor_uuid = bytes(16)  # Default to nil UUID bytes
        
        expression_value_int = int(expression_value)
        is_grafted_bool = bool(is_grafted)

        key = (
            gene,
            expression_value_int,
            contributor_uuid,
            is_grafted_bool
        )
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "gene", gene)
        object.__setattr__(self, "expression_value", expression_value_int)
        object.__setattr__(self, "contributor_uuid", contributor_uuid)
        object.__setattr__(self, "is_grafted", is_grafted_bool)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        gene: Gene,
        expression_value: int,
        contributor_uuid: bytes,
        is_grafted: bool = False
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, key: str, value: object) -> None:  # pragma: no cover
        raise AttributeError("GenePackage instances are immutable")
    
    def __repr__(self) -> str:
        return (
            f"GenePackage(gene={repr(self.gene)}, expression_value={self.expression_value}, "
            f"contributor_uuid={self.contributor_uuid}, "
            f"is_grafted={self.is_grafted})"
        )