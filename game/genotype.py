from __future__ import annotations

from collections.abc import Iterable
from textwrap import indent
from typing import Any, ClassVar, Union

from game.gene import Gene
from game.phene import Phene


def _validate_genes(genes: Iterable[Gene]) -> tuple[bool, str]:
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

class Genotype:
    """
    gene.characteristic.upp_index must be unique within a Genotype.
    the of classmethod must provide validation for this constraint.
    The list must be ordered by upp_index.
    """
    __slots__ = ("genes", "phenes")
    GenesCacheKey = tuple[Gene, ...]
    PhenotypesCacheKey = Union[None, tuple[Phene, ...]]
    _cache: ClassVar[dict[tuple[GenesCacheKey, PhenotypesCacheKey], Genotype]] = {}
    def __new__(
        cls,
        genes: Iterable[Gene],
        phenes: None | Iterable[Phene] = None
    ) -> Genotype:
        # Normalize input without mutating caller-owned collections.
        genes_tuple = tuple(genes)
        phenes_tuple = tuple(phenes) if phenes is not None else None

        is_valid, feedback = _validate_genes(genes_tuple)
        if not is_valid:
            raise ValueError(f"Conflicting upp_indices:\n{feedback}")

        # Deterministic order for stable caching.
        sorted_genes = tuple(sorted(genes_tuple, key=lambda g: g.characteristic.upp_index))
        sorted_phenes = tuple(sorted(phenes_tuple, key=lambda p: p.characteristic.upp_index)) if phenes_tuple is not None else None

        key = sorted_genes, sorted_phenes
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        # Store immutably (tuple) to preserve flyweight semantics.
        object.__setattr__(self, "genes", sorted_genes)
        object.__setattr__(self, "phenes", sorted_phenes)
        cls._cache[key] = self
        return self
    
    def __init__(
        self,
        genes: Iterable[Gene],
        phenes: None | Iterable[Phene] = None
    ) -> None:
        # All initialization happens in __new__ (supports flyweight reuse).
        pass

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} instances are immutable")
    
    def _package_key(self) -> tuple[int, ...]:
        gene_key = tuple(gene.characteristic.upp_index for gene in self.genes)
        phene_key = tuple(phene.characteristic.upp_index for phene in self.phenes) if self.phenes is not None else ()
        return gene_key + phene_key

    @classmethod
    def of(cls, genes: Iterable[Gene], phenes: None | Iterable[Phene] = None) -> Genotype:
        # `__new__` performs validation, normalization, and caching.
        return cls(genes, phenes)
    
    @classmethod
    def by_characteristic_names(cls, gene_names: Iterable[str], phene_names: None | Iterable[str] = None) -> Genotype:
        genes = []
        for name in gene_names:
            gene = Gene.by_characteristic_name(name)
            genes.append(gene)
        phenes = []
        if phene_names is not None:
            for name in phene_names:
                phene = Phene.by_characteristic_name(name)
                phenes.append(phene)
        return cls.of(genes, phenes if phene_names is not None else None)
    
    def get_phenotype(self) -> dict[int, tuple[Gene | None, Phene | None]]:
        phenotype: dict[int, tuple[Gene | None, Phene | None]] = {}

        for gene in self.genes:
            upp_index = gene.characteristic.upp_index
            phene_from_gene = Phene(gene.characteristic, 0, bytes(16), False)
            phenotype[upp_index] = (gene, phene_from_gene)

        if self.phenes is not None:
            for phene in self.phenes:
                upp_index = phene.characteristic.upp_index
                existing = phenotype.get(upp_index)
                if existing is None:
                    phenotype[upp_index] = (None, phene)
                else:
                    existing_gene, _existing_phene = existing
                    phenotype[upp_index] = (existing_gene, phene)

        return phenotype
        
    
    def __repr__(self) -> str:
        indentation = "  "
        display = []
        display.append(f"Number of Genes={len(self.genes)}")
        if self.phenes is not None:
            display.append(f"Number of Phenes={len(self.phenes)}")
        display.append(repr(self.genes))
        if self.phenes is not None:
            display.append(repr(self.phenes))
            
        return "Genotype(\n" + indent(",\n".join(display), indentation) + "\n)"
    