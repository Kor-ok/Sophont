from __future__ import annotations
from typing import Any, ClassVar, Dict, Iterable, Tuple, Optional
from uuid import uuid4

from game.gene import Gene
from game.mappings.world_id import WorldID


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

class Genotype:
    """
    gene.characteristic.upp_index must be unique within a Genotype.
    the of classmethod must provide validation for this constraint.
    The list must be ordered by upp_index.
    """
    __slots__ = (
        "genes",
    )
    _cache: ClassVar[Dict[Tuple[Gene, ...], "Genotype"]] = {}
    def __new__(
        cls,
        genes: Iterable[Gene],
    ) -> "Genotype":
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
    def of(cls, genes: Iterable[Gene]) -> "Genotype":
        # `__new__` performs validation, normalization, and caching.
        return cls(genes)
    
    @classmethod
    def by_gene_characteristic_names(cls, names: Iterable[str]) -> "Genotype":
        genes = []
        for name in names:
            gene = Gene.by_characteristic_name(name)
            genes.append(gene)
        return cls.of(genes)
    
    def get_all_genes(self) -> Dict[int, Gene]:
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

    def __init__(self, genotype: Genotype, uuid: Optional[bytes] = None):
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

    def __init__(self, species_collection: Iterable[Species], tree_of_life_node_uuid: bytes = bytes(16)):
        self.species_collection: Tuple[Species, ...] = tuple(species_collection)
        if tree_of_life_node_uuid is bytes(16):
            tree_of_life_node_uuid = uuid4().bytes
        self.tree_of_life_node_uuid: bytes = tree_of_life_node_uuid

    def __repr__(self) -> str:
        return f"Genus(uuid={self.tree_of_life_node_uuid!r}, species_collection={self.species_collection!r})"
    
class TreeOfLifeNode:
    __slots__ = (
        "uuid",
        "children",
    )
    def __init__(self, children: Iterable[TreeOfLifeNode], uuid: Optional[bytes] = None):
        self.children: Tuple[TreeOfLifeNode, ...] = tuple(children)
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