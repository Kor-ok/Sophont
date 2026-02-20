from __future__ import annotations

import dataclasses
import struct
from functools import lru_cache
from typing import Any, ClassVar, Union, get_type_hints

from utils.semantics import SemanticMap


@lru_cache(maxsize=300)
def _compute_component_signature(
    instance: Any,
) -> bytes:
    """Return a flattened signed-byte signature (immutable `bytes`) for *instance*.

    Each integer is stored as a single signed byte; negative values are encoded
    with two's-complement mapping (value & 0xFF). The result is immutable.
    """
    builder = bytearray()

    subclass_index = Primitive.subclass_dict.get(instance.__class__)
    if subclass_index is None:
        raise KeyError(f"Class {instance.__class__.__name__} not registered in Primitive.subclass_dict")
    if not (-128 <= int(subclass_index) <= 127):
        raise ValueError("subclass_index out of signed-byte range")
    builder.append(int(subclass_index) & 0xFF)

    for f in dataclasses.fields(instance):
        value = getattr(instance, f.name)
        if isinstance(value, Primitive):
            # nested returns bytes, which can be extended directly
            nested = _compute_component_signature(value)
            builder.extend(nested)
        else:
            iv = int(value)
            if not (-128 <= iv <= 127):
                raise ValueError(f"field {f.name!r} value {iv} out of signed-byte range")
            builder.append(iv & 0xFF)

    return struct.pack(f"{len(builder)}b", *builder)

def _generate_semantic_map(cls: type, recursion: int = 0) -> tuple[Any, ...]:
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
    semantic_map = (cls.subclass_dict[cls],)

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
            semantic_map += (count,)
            break
        elif nested: # nested and not finished: nested and finished:
            nested_result = _generate_semantic_map(nested, recursion + 1)
            semantic_map += (count, (nested_result),)
        else: # not nested and not finished
            semantic_map += (count,)
        
    return semantic_map


def _filter_type_hints(cls: type) -> Any:
    base_class = cls.mro()[-2]
    subclasses = base_class.subclass_dict
    type_hints = get_type_hints(cls)
    filtered_type_hints = {}
    for name, type in type_hints.items():
        if name not in ("subclass_dict", "member_dict", "component_signature", "semantic_signature", "semantic_map"):
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
                cls.semantic_map = SemanticMap.from_raw(_generate_semantic_map(cls))

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
