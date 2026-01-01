from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Union
from uuid import uuid4

from game.gene import Gene
from game.mappings.world_id import WorldID
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
    
    def get_all_genes(self) -> dict[int, Gene]:
        return {gene.characteristic.upp_index: gene for gene in self.genes}
    
    def __repr__(self) -> str:
        return (
            f"Number of Genes={len(self.genes)}\n"
            f"{repr(self.genes)}"
            )
    
class Species:
    __slots__ = (
        "uuid",
        "genotype",
    )

    def __init__(self, genotype: Genotype, uuid: None | bytes = None):
        self.genotype: Genotype = genotype
        if uuid is None:
            uuid = uuid4().bytes
        self.uuid: bytes = uuid

    def __repr__(self) -> str:
        return f"Species(uuid={self.uuid!r}, genotype={self.genotype!r})"
    
class Genus:
    __slots__ = (
        "tree_of_life_node_uuid",
        "species_collection",
    )

    def __init__(self, species_collection: Iterable[Species], tree_of_life_node_uuid: None | bytes = None):
        self.species_collection: tuple[Species, ...] = tuple(species_collection)
        if tree_of_life_node_uuid is None:
            tree_of_life_node_uuid = uuid4().bytes
        self.tree_of_life_node_uuid: bytes = tree_of_life_node_uuid

    def __repr__(self) -> str:
        return f"Genus(uuid={self.tree_of_life_node_uuid!r}, species_collection={self.species_collection!r})"
    
class TreeOfLifeNode:
    __slots__ = (
        "uuid",
        "children",
    )
    def __init__(self, children: Iterable[TreeOfLifeNode], uuid: None | bytes = None):
        self.children: tuple[TreeOfLifeNode, ...] = tuple(children)
        if uuid is None:
            uuid = uuid4().bytes
        self.uuid: bytes = uuid

    def add_child(self, path) -> None:
        node = self
        for uuid in path:
            matching_child = next((child for child in node.children if child.uuid == uuid), None)
            if matching_child is None:
                new_child = TreeOfLifeNode(children=(), uuid=uuid)
                node.children += (new_child,)
                node = new_child
            else:
                node = matching_child

class TreeOfLifeOrigin:
    __slots__ = (
        "root",
        "world_id",
    )
    def __init__(self, world_id: WorldID):
        self.root: TreeOfLifeNode = TreeOfLifeNode(children=())
        self.world_id: WorldID = world_id

    def add_node(self, path: Iterable[bytes]) -> None:
        self.root.add_child(path)
    
    def display(self) -> None:
        def _display_node(node: TreeOfLifeNode, depth: int) -> None:
            indent = "  " * depth
            print(f"{indent}- Node UUID: {node.uuid!r}")
            for child in node.children:
                _display_node(child, depth + 1)
        
        print(f"Tree of Life Origin for World ID: {self.world_id}")
        _display_node(self.root, 0)