from __future__ import annotations

import dataclasses
import struct
from functools import lru_cache
from typing import Any, ClassVar, Union, get_type_hints

from colorama import Fore, Style
from colorama import init as colorama_init

from utils.semantics import SemanticMap

colorama_init(autoreset=True)

@lru_cache(maxsize=300)
def _compute_component_signature(
    instance: Any,
) -> bytes:
    """Return a flattened signed-byte signature (immutable `bytes`) for *instance*.

    Each integer is stored as a single signed byte; negative values are encoded
    with two's-complement mapping (value & 0xFF). The result is immutable.
    """
    result: list[int] = []

    subclass_index = instance.subclass_dict.get(instance.__class__)
    if subclass_index is None:
        raise ValueError(f"Class {instance.__class__.__name__} not found in subclass_dict.")
    result.append(subclass_index)

    instance_fields = dataclasses.fields(instance)

    for f in instance_fields:
        value = getattr(instance, f.name)
        if isinstance(value, Primitive):
            nested = _compute_component_signature(value)
            # Convert nested bytes to a list of integers for concatenation
            nested_ints = struct.unpack(f"{len(nested)}b", nested)
            result.extend(nested_ints)
        else:
            result.append(value)

    return struct.pack(f"{len(result)}b", *result)


Map = tuple[Any, ...]
Members = dict[tuple[str, type], int]
def _recursive_semantic_map(cls: type, recursion: int = 0, _root: bool = True) -> tuple[Map, Members]:
    if recursion > 2:
        raise RecursionError(f"Recursion limit exceeded while generating semantic map for {cls.__name__}. This may indicate a circular reference in the class definitions.")
    """
    class TestComplexComponent:
        field1: int
        field2: semantics.data.CharacteristicCode
        field3: int
        field4: int
        field5: semantics.data.KnowledgeCode
        field6: int

    Example: for a ``TestComplexComponent`` with the above fields, the result is

    Semantic Map = (4, 1, (0, 3), 2, ((2, 2, (1, 3))), 1)
                    ↑  ↑   ↑      ↑    ↑      ↑        ↑
                    a  b   c      d    e      f        g
    where:
    a: the subclass index for TestComplexComponent in its subclass_dict
    b: the number of fields before the first field of type in domain_map (field1)
    c: the semantic map for the nested class CharacteristicCode (field2)
    d: the number of fields between the first field of type in domain_map and the
       second field of type in domain_map (field3 and field4)
    e: the semantic map for the nested class KnowledgeCode (field5)
    f: the deeper semantic map for SkillCode inside KnowledgeCode (field5)
    g: the number of fields after the last field of type in domain_map (field6) 
    """
    domain_map = cls.subclass_dict
    filtered_members = _filter_type_hints(cls)
    
    cumm_semantic_map: Map = (cls.subclass_dict[cls],)
    cumm_members_map: Members = {}

    for name, type in filtered_members.items():
        cumm_members_map[(f"{cls.__name__}.{name}", type)] = len(cumm_members_map)

    def _recursive_member_identity_search() -> tuple[int, Union[type, None], bool]:
        nonlocal member_position
        items = list(filtered_members.items())
        count = 0
        nested_with = None

        while member_position < number_of_members:
            name, t = items[member_position]
            member_position += 1
            if t in domain_map:
                nested_with = t
                return count, nested_with, member_position >= number_of_members
            count += 1

        return count, None, True
    
    member_position = 0
    number_of_members = len(filtered_members)
    # Count the number of fields in filtered_members in order before the first
    # field of type in domain_map
    while member_position < number_of_members:
        
        count, nested, finished = _recursive_member_identity_search()
        if not nested and finished:
            cumm_semantic_map += (count,)
            break
        elif nested: # nested and not finished: nested and finished:
            # pass _root=False for internal recursive calls
            nested_result, nested_members = _recursive_semantic_map(nested, recursion + 1, False)
            cumm_members_map.update(nested_members)
            cumm_semantic_map += (count, (nested_result),)
        else: # not nested and not finished
            cumm_semantic_map += (count,)
    
    return cumm_semantic_map, cumm_members_map

def _generate_semantic_map(cls: type) -> tuple[Map, Members]:
    """Generate a semantic map for *cls*.

    The semantic map is a nested tuple structure that encodes the positions of
    fields of types in the domain (i.e. Primitive subclasses) and their nested
    structures. It also returns a mapping of member names and types to their
    positions in the signature.

    The recursion limit is set to 2 to prevent infinite loops in case of circular references.
    """
    semantic_map, member_map = _recursive_semantic_map(cls, recursion=0, _root=True)

    # print(f"  {Fore.GREEN}Semantic map {cls.__name__}:{Style.RESET_ALL}")
    # print(f"    {Fore.BLUE}Semantic Map: {semantic_map}{Style.RESET_ALL}")
    # print(f"    {Fore.CYAN}Members:{Style.RESET_ALL}")
    # for (name, type) , index in member_map.items():
    #     print(f"      {Fore.CYAN}{index}: {name}{Style.RESET_ALL}")

    return semantic_map, member_map

def _filter_type_hints(cls: type) -> dict[str, type]:
    base_class = cls.mro()[-2]
    subclasses = base_class.subclass_dict
    type_hints = get_type_hints(cls)
    filtered_type_hints = {}
    for name, type in type_hints.items():
        if name not in ("subclass_dict", "component_signature", "semantic_signature", "semantic_map"):
            if type in (int, float, bool) or type in subclasses:
                filtered_type_hints[name] = type
    return filtered_type_hints

class Primitive:

    subclass_dict: ClassVar[dict[type, int]] = {}

    def __init_subclass__(cls) -> None:     
        if dataclasses.is_dataclass(cls):
            base_dict = Primitive.subclass_dict
            if cls not in base_dict:
                cls.semantic_map: SemanticMap
                cls.component_signature: bytes
                cls.semantic_signature: tuple[int, ...]
                base_dict[cls] = len(base_dict)
                # print(f"{Fore.YELLOW}Registered {cls.__name__}{Style.RESET_ALL}")
                map, members = _generate_semantic_map(cls)
                cls.semantic_map = SemanticMap.from_raw(map, members)

    @property
    def domain_identity(self) -> int:
        """Return the domain identity for this instance's class."""
        return Primitive.subclass_dict[self.__class__]

class Applied:
    """Base class for all components of a more complex signature
    that can hold references to Primitive components or other
    Applied components.
    """

    pass
