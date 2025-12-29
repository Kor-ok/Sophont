from __future__ import annotations
from typing import Any, ClassVar, Dict, Iterable, Tuple

from game.gene import Gene


def _validate_genes(genes: Iterable[Gene]) -> Tuple[bool, str]:
    feedback = ""
    is_valid = True
    seen_upp_indexes = set()
    for gene in genes:
        upp_index = gene.characteristic.upp_index
        if upp_index in seen_upp_indexes:
            is_valid = False
            feedback += f"{upp_index}\n"
        seen_upp_indexes.add(upp_index)
    return is_valid, feedback

class SpeciesGenotype:
    """
    gene.characteristic.upp_index must be unique within a Genotype.
    the of classmethod must provide validation for this constraint.
    The list must be ordered by upp_index.
    """
    __slots__ = (
        "genes",
    )
    _cache: ClassVar[Dict[Tuple[Gene, ...], "SpeciesGenotype"]] = {}
    def __new__(
        cls,
        genes: Iterable[Gene],
    ) -> "SpeciesGenotype":
        # Normalize input without mutating caller-owned collections.
        genes_tuple = tuple(genes)

        is_valid, feedback = _validate_genes(genes_tuple)
        if not is_valid:
            raise ValueError(f"Conflicting upp_indices:\n{feedback}")

        # Deterministic order for stable caching.
        sorted_genes = tuple(sorted(genes_tuple, key=lambda g: g.characteristic.upp_index))

        key = sorted_genes
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        # Store immutably (tuple) to preserve flyweight semantics.
        object.__setattr__(self, "genes", sorted_genes)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        genes: Iterable[Gene]
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} instances are immutable")
    
    def _package_key(self) -> Tuple[int, ...]:
        return tuple(gene.characteristic.upp_index for gene in self.genes)

    @classmethod
    def of(cls, genes: Iterable[Gene]) -> "SpeciesGenotype":
        # `__new__` performs validation, normalization, and caching.
        return cls(genes)
    
    def get_all_genes(self) -> Dict[int, Gene]:
        return {gene.characteristic.upp_index: gene for gene in self.genes}
    
    def __repr__(self) -> str:
        return (
            f"Number of Genes={len(self.genes)}"
            f"\nGenotype(genes={repr(self.genes)})"
            )