from __future__ import annotations

from collections.abc import Iterable

from systems.attributes.genotype import Genotype
from systems.uid.guid import GUID


class Species:
    __slots__ = (
        "guid",
        "genotype",
    )

    def __init__(self, genotype: Genotype, guid: None | GUID = None):
        self.genotype: Genotype = genotype
        if guid is None:
            guid = GUID.generate(GUID.NameSpaces.Entity.SPECIES, GUID.NameSpaces.Owner.ENV)
        self.guid: GUID = guid
    
class Genus:
    __slots__ = (
        "tree_of_life_node_guid",
        "species_collection",
    )

    def __init__(self, species_collection: Iterable[Species], tree_of_life_node_guid: None | GUID = None):
        self.species_collection: tuple[Species, ...] = tuple(species_collection)
        if tree_of_life_node_guid is None:
            tree_of_life_node_guid = GUID.generate(GUID.NameSpaces.Entity.SPECIES, GUID.NameSpaces.Owner.ENV)
        self.tree_of_life_node_guid: GUID = tree_of_life_node_guid
    
class TreeOfLifeNode:
    __slots__ = (
        "guid",
        "children",
    )
    def __init__(self, children: Iterable[TreeOfLifeNode], guid: None | GUID = None):
        self.children: tuple[TreeOfLifeNode, ...] = tuple(children)
        if guid is None:
            guid = GUID.generate(GUID.NameSpaces.Entity.SPECIES, GUID.NameSpaces.Owner.ENV)
        self.guid: GUID = guid
    def add_child(self, path) -> None:
        node = self
        for guid in path:
            matching_child = next((child for child in node.children if child.guid == guid), None)
            if matching_child is None:
                new_child = TreeOfLifeNode(children=(), guid=guid)
                node.children += (new_child,)
                node = new_child
            else:
                node = matching_child

# class TreeOfLifeOrigin:
#     __slots__ = (
#         "root",
#         "world_id",
#     )
#     def __init__(self, world_id: WorldID):
#         self.root: TreeOfLifeNode = TreeOfLifeNode(children=())
#         self.world_id: WorldID = world_id

#     def add_node(self, path: Iterable[bytes]) -> None:
#         self.root.add_child(path)
    
#     def display(self) -> None:
#         def _display_node(node: TreeOfLifeNode, depth: int) -> None:
#             indent = "  " * depth
#             print(f"{indent}- Node UUID: {node.uuid!r}")
#             for child in node.children:
#                 _display_node(child, depth + 1)
        
#         print(f"Tree of Life Origin for World ID: {self.world_id}")
#         _display_node(self.root, 0)