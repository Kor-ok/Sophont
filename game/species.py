from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from game.genotype import Genotype
from game.mappings.world_id import WorldID


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