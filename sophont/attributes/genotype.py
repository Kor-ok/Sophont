from __future__ import annotations

from collections.abc import Iterable
from typing import Union

from sophont.attributes.base import AppliedAttributeBase
from sophont.attributes.gene import Gene
from sophont.attributes.phene import Phene

GenesTuple = tuple[Gene, ...]
PhenesTuple = Union[None, tuple[Phene, ...]]
GenotypeKey = tuple[GenesTuple, PhenesTuple]


def _validate_genes(genes: Iterable[Gene]) -> tuple[bool, str]:
    """
    Validate that all genes have unique upp_index values.

    Args:
        genes: Iterable of Gene flyweights to validate

    Returns:
        (is_valid, feedback) where feedback lists any duplicate upp_indices
    """
    feedback = ""
    is_valid = True
    seen_upp_indexes: set[int] = set()
    for gene in genes:
        upp_index = gene.characteristic.code[0]
        if upp_index in seen_upp_indexes:
            is_valid = False
            feedback += f"Duplicate upp_index: {upp_index}\n"
        seen_upp_indexes.add(upp_index)
    return is_valid, feedback


class Genotype(AppliedAttributeBase[GenotypeKey]):
    """
    Immutable flyweight representing a genetic profile: a set of Genes and optional Phenes.

    Constraints:
    - Each gene.characteristic.code[0] (upp_index) must be unique within the Genotype
    - Genes and phenes are stored sorted by upp_index for deterministic caching

    Each unique combination of (genes, phenes) maps to exactly one Genotype instance
    in memory (flyweight identity guarantee).

    Hierarchy: Genotype aggregates Gene/Phene flyweights (CollectionComposite pattern)
    """

    # -------------------------------------------------------------------------
    # Flyweight Configuration
    # -------------------------------------------------------------------------

    __slots__ = ("genes", "phenes")
  
    genes: tuple[Gene, ...]
    """Ordered by upp_index."""
    phenes: tuple[Phene, ...] | None
    """Ordered by upp_index, or None if no phenes defined."""

    Key = GenotypeKey

    def __new__(
        cls,
        genes: Iterable[Gene],
        phenes: Iterable[Phene] | None = None,
    ) -> Genotype:
        
        genes_tuple = tuple(genes)
        phenes_tuple = tuple(phenes) if phenes is not None else None

        is_valid, feedback = _validate_genes(genes_tuple)
        if not is_valid:
            raise ValueError(f"Conflicting upp_indices in genes:\n{feedback}")

        sorted_genes: tuple[Gene, ...] = tuple(
            sorted(genes_tuple, key=lambda g: g.characteristic.code[0])
        )
        sorted_phenes: tuple[Phene, ...] | None = (
            tuple(sorted(phenes_tuple, key=lambda p: p.characteristic.code[0]))
            if phenes_tuple is not None
            else None
        )

        key: GenotypeKey = (sorted_genes, sorted_phenes)

        cached, found = cls._cache_get_or_create(key)
        if found:
            return cached  # type: ignore[return-value]

        self = super().__new__(cls)

        self._set_attr("genes", sorted_genes)
        self._set_attr("phenes", sorted_phenes)

        cls._cache_set(key, self)
        return self
    

    @classmethod
    def by_characteristic_names(
        cls,
        gene_names: Iterable[str],
        phene_names: Iterable[str] | None = None,
        custom_genes: Iterable[Gene] | None = None,
        custom_phenes: Iterable[Phene] | None = None,
    ) -> Genotype:
        """
        Factory: construct Genotype by looking up Genes/Phenes by name.

        This convenience method:
        1. Creates Gene flyweights from characteristic names
        2. Creates Phene flyweights from characteristic names (if provided)
        3. Merges with any custom Gene/Phene flyweights
        4. Passes everything to the constructor for validation and caching

        Example:
            genotype = Genotype.by_characteristic_names(
                gene_names=["Strength", "Dexterity", "Endurance"],
                phene_names=["Intelligence"],
                custom_genes=[special_gene_with_modifiers]
            )
        """
        # Build genes from names
        genes: list[Gene] = [Gene.by_characteristic_name(name) for name in gene_names]

        # Build phenes from names (if provided)
        phenes: list[Phene] = []
        if phene_names is not None:
            phenes = [Phene.by_characteristic_name(name) for name in phene_names]

        # Merge custom flyweights
        if custom_genes is not None:
            genes.extend(custom_genes)
        if custom_phenes is not None:
            phenes.extend(custom_phenes)

        # Let the constructor handle validation, sorting, and caching
        return cls(genes, phenes if phenes else None)


    def _package_key(self) -> tuple[int, ...]:
        """
        Generate a compact key based on upp_indices for downstream use.

        Returns a tuple of upp_index values from genes followed by phenes.
        Useful for quick identity checks without comparing full flyweights.
        """
        gene_key = tuple(gene.characteristic.code[0] for gene in self.genes)
        phene_key = (
            tuple(phene.characteristic.code[0] for phene in self.phenes)
            if self.phenes is not None
            else ()
        )
        return gene_key + phene_key

    def get_genes_without_phenes(self) -> dict[int, Gene]:
        """
        Get genes that have no corresponding phene at the same upp_index.

        Returns:
            dict mapping upp_index -> Gene for genes without matching phenes
        """
        phene_codes: set[int] = set()
        if self.phenes is not None:
            phene_codes = {phene.characteristic.code[0] for phene in self.phenes}

        return {
            gene.characteristic.code[0]: gene
            for gene in self.genes
            if gene.characteristic.code[0] not in phene_codes
        }

    def get_phenes_without_genes(self) -> dict[int, Phene]:
        """
        Get phenes that have no corresponding gene at the same upp_index.

        Returns:
            dict mapping upp_index -> Phene for phenes without matching genes
        """
        gene_codes: set[int] = {gene.characteristic.code[0] for gene in self.genes}

        if self.phenes is None:
            return {}

        return {
            phene.characteristic.code[0]: phene
            for phene in self.phenes
            if phene.characteristic.code[0] not in gene_codes
        }

    def compute_max_inheritance_contributors(self) -> int:
        """
        Compute the maximum inheritance_contributors value across all genes.

        This determines the number of parent genotypes needed for inheritance
        calculations (e.g., 2 for standard two-parent inheritance).

        Returns:
            Maximum inheritance_contributors value, or 0 if no genes (for future use with chimera/cloning/personality grafts)
        """
        if not self.genes:
            return 0
        return max(gene.inheritance_contributors for gene in self.genes)
