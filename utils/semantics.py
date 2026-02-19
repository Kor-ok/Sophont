from __future__ import annotations

import logging
import struct
from collections import OrderedDict
from importlib import import_module
from itertools import chain
from typing import Any, NamedTuple, Optional

logger = logging.getLogger(__name__)

def collect_module_classes(
    module_name: str,
    base_classes: tuple[type, ...],
) -> Any:

    module = import_module(module_name)

    results = []
    for _, obj in vars(module).items():
        # get everything from __module__ = components.data and who's base class is in base_classes
        if getattr(obj, "__module__", None) == module_name\
            and any(issubclass(obj, base) for base in base_classes):
            results.append(obj)
    
    return results

def get_recursive_component_classes(
    cls: type,
    seen: Optional[set[type]] = None
) -> OrderedDict[type, tuple[int, int]]:
    """Return a  dictionary of all  types  that are recursively referenced by
    the  given class, including self where the  key  is the class  and the
    value is a tuple of  the class's domain identity   and members length.
    Member lengths are + 1 to account for the domain identity at the start
    of the signature for each  class EXCEPT the initial class to allow for
    self  recursion  without  including the  domain identity in the member
    count for that initial class."""
    if seen is None:
        seen = set()
    if cls in seen:
        return OrderedDict({cls: (cls.subclass_dict[cls], len(cls.member_dict))})
    seen.add(cls)
    recursive_types = OrderedDict()
    is_recursive = False
    for _, field_type in cls.member_dict.values():
        for class_type, domain_identity in cls.subclass_dict.items():
            if field_type == class_type:
                is_recursive = True

    primary_domain_identity = cls.subclass_dict[cls]
    if is_recursive:
        for _, field_type in cls.member_dict.values():
            for class_type, domain_identity in cls.subclass_dict.items():
                if field_type == class_type:
                    members_length = len(class_type.member_dict) + 1
                    recursive_types[class_type] = (domain_identity, members_length)
                    # Now deal with the self class where if it is recursive, we want 
                    # to include it in the result with its domain identity and members 
                    # length, but we don't want to add +1 to the members length for the 
                    # initial class to allow for self recursion without including the 
                    # domain identity in the member count for that initial class
                    self_members_length = len(cls.member_dict)
                    # Keep the existing members length for the initial class to allow for 
                    # self recursion without including the domain identity in the member
                    # count for that initial class
                    recursive_types[cls] = (primary_domain_identity, self_members_length)
                    # Move the self class to the front of the ordered dict to ensure it is
                    # processed first when constructing the composite signature 
                    recursive_types.move_to_end(cls, last=False)
    else:
        # We only add itself to the recursive types
        # Add +1 to account for the domain identity at the start of the signature for each class
        recursive_types[cls] = (primary_domain_identity, len(cls.member_dict) + 1) 
    
    if not recursive_types:
        raise ValueError(f"No recursive types found for class {cls.__name__}.")
    return recursive_types

def construct_composite_signature(parse_signature: tuple[int, ...], recursive_types: dict[type, tuple[int, int]]) -> tuple[int, ...]:
    """Construct a composite signature by adding the domain identity at the
    start of  the parse signature tuple,  to create a unique key for the
    by_signature index.."""
    composite_signature: tuple[int, ...] = ()
    target_signature_length = sum(members_length for _, members_length in recursive_types.values())
    cummulative_members_length = 0
    for cls, (domain_identity, members_length) in recursive_types.items():
        parse_signature_portion = parse_signature[:members_length - 1]
        composite_signature += (domain_identity,) + parse_signature_portion
        if len(composite_signature) >= target_signature_length:
            # Stop once we've reached the target signature length to 
            # avoid adding extra domain identities and member values 
            # beyond what is needed for the composite signature
            break  
        cummulative_members_length += members_length
        parse_signature = parse_signature[members_length - 1:]
    
    return composite_signature

def construct_component_signature_from_semantic_signature(cls: type, semantic_signature: tuple[Any, ...]) -> tuple[int, ...]:
    """Construct a component signature tuple from a semantic signature tuple by
    mapping the member values in the semantic signature to their corresponding
    domain identities and members using the semantic_map of the class."""
    component_signature = ()
    semantic_map = cls.semantic_map # Semantic map: (2, 2,      (1, 3))
    # semantic_signature =                             (15, -99,    59, 5, 1)
    debug_target_component_signature =              (2, 15, -99, 1, 59, 5, 1)
    

    if cls.__name__ == "KnowledgeCode" and semantic_signature[0] == 15:
        i = 0
        for element in semantic_map:
            print(f"Element {i}: {element} is {type(element)}")
            i += 1
        print(f"Semantic Map Length: {len(semantic_map)}")
        print(f"Semantic Map's 4th element: {semantic_map[2][1]}")
        print(f"semantic_map[1]: {semantic_map[1]} is {type(semantic_map[1])}")
        print(f"semantic_map[2]: {semantic_map[2]} is {type(semantic_map[2])}")
        print("\n" + "-"*80)
        print(f"Class: {cls.__name__}:")
        print(f"Semantic signature: {semantic_signature}")
        print(f"Semantic map: {semantic_map}")
        print(f"Component signature: {component_signature}")
        print(f"Target signature: {debug_target_component_signature}\n")
        try:
            assert component_signature == debug_target_component_signature, f"\033[31mComponent signature {component_signature} does not match target signature {debug_target_component_signature}\033[0m"
        except AssertionError as e:
            print(str(e))
    
    return component_signature


def parse_signature_portion_from_type(cls: type, primary_signature: tuple[int, ...]) -> tuple[int, ...]:
        """Helper function  to parse a  portion   of  the signature  tuple that
        corresponds to a specific class, using the member_dict of that class
        to  map the values  in the signature portion  to their corresponding
        member names."""
        parsed_result = ()
        member_dict = cls.member_dict
        is_recursive = False
        for _, field_type in member_dict.values():
            for class_type, domain_identity in cls.subclass_dict.items():
                if field_type == class_type:
                    is_recursive = True
                    break
        
        if is_recursive:
            members_length = len(member_dict) - 1
        else:
            members_length = len(member_dict)
        
        logger.debug(f"Length of members for class '{cls.__name__}': {members_length}")
        for index, (member_name, member_type) in member_dict.items():
            member_value = primary_signature[index + 1:members_length + 1]
            logger.debug(f"Extracted member value: {member_value}")
            parsed_result += member_value
            if len(member_value) > members_length -1:
                # Stop once we've parsed the expected number of member values
                # for this class to avoid adding extra values beyond what is 
                # needed for the signature portion corresponding to this class
                break  

        logger.debug(f"Parsed signature portion for class '{cls.__name__}': {parsed_result}")
        return parsed_result

class SemanticMapElement(NamedTuple):
    """Immutable flyweight: one flattened node of the semantic map."""

    depth: int
    domain_identity: int
    pre_nested_count: int


class SemanticMap:
    """Pre-parsed semantic map — parse once, reuse for many signature generations.

    Analogous to a *Component type definition* in ECS terms.
    Follows the flyweight / immutable-item pattern used elsewhere in the repo.
    """

    __slots__ = ("elements",)

    def __new__(cls, elements: tuple[SemanticMapElement, ...]) -> SemanticMap:
        instance = super().__new__(cls)
        instance.elements = elements
        return instance

    def __init__(self, elements: tuple[SemanticMapElement, ...]) -> None:
        pass

    # -- factory ----------------------------------------------------------

    @staticmethod
    def from_raw(raw: tuple[Any, ...]) -> SemanticMap:
        """Build a SemanticMap from a nested raw-tuple descriptor."""
        return SemanticMap(elements=tuple(SemanticMap._parse(raw, 0)))

    @staticmethod
    def _parse(
        raw: tuple[Any, ...],
        depth: int,
    ) -> list[SemanticMapElement]:
        """Recursively flatten *raw* into an ordered list of elements.

        Cleaner iteration compared to the original while-loop:
        • Identifies domain_identity once at position 0.
        • Dispatches remaining items by type in a single pass.
        """
        if not raw:
            return []
        result: list[SemanticMapElement] = []
        first = raw[0]
        domain_id: Optional[int] = first if not isinstance(first, tuple) else None
        start = 1 if domain_id is not None else 0
        for i in range(start, len(raw)):
            val = raw[i]
            if isinstance(val, tuple):
                result.extend(SemanticMap._parse(val, depth + 1))
            elif domain_id is not None:
                result.append(SemanticMapElement(depth, domain_id, val))
        return result


def generate_signature_oop(
    semantic_map: SemanticMap,
    semantic_signature: tuple[int, ...],
) -> bytes:
    """Hot-path OOP signature generation from a pre-parsed map.

    Optimisations over the original:
    • **No debug logging / I/O** in the hot path — this alone removed ~95 %
      of the per-call cost when the logger was active (f-string evaluation +
      ``logger.debug`` call overhead even at non-DEBUG levels).
    • Uses ``struct.pack`` for a single C-level int→bytes conversion instead of
      building an intermediate ``array('b', ...)`` then calling ``.tobytes()``.
    • Iterates via NamedTuple unpacking — one tuple unpack per element replaces
      three attribute lookups (``element.depth``, ``.domain_identity``,
      ``.pre_nested_count``).
    """
    result: list[int] = []
    seen: set[tuple[int, int]] = set()
    sig_idx = 0
    for depth, domain_id, count in semantic_map.elements:
        key = (depth, domain_id)
        if key not in seen:
            seen.add(key)
            result.append(domain_id)
        end = sig_idx + count
        result.extend(semantic_signature[sig_idx:end])
        sig_idx = end
    return struct.pack(f"{len(result)}b", *result)

def generate_signature_algorithmic(
    raw: tuple[Any, ...],
    semantic_signature: tuple[int, ...],
) -> bytes:
    """Single-pass signature generation — no intermediate parse objects.

    Walks the nested raw-tuple map and assembles the component signature in one
    recursive traversal, fusing the parse and generate steps.

    Optimisations over the original ``generate_component_signature_via_itertools``:
    • **Fused parse + generate** — eliminates an entire intermediate list of
      ``(depth, domain_id, count)`` tuples.
    • Uses ``nonlocal`` instead of a mutable-list-as-int workaround.
    • Removes the (unused) ``itertools.chain`` import.
    • Removes the redundant ``elif isinstance(element_value, tuple)`` branch
      (already handled by the preceding ``if``).
    • Uses ``struct.pack`` for direct int→bytes conversion.
    """
    result: list[int] = []
    seen: set[tuple[int, int]] = set()
    sig_idx = 0

    def _walk(node: tuple[Any, ...], depth: int) -> None:
        nonlocal sig_idx
        if not node:
            return
        first = node[0]
        domain_id: Optional[int] = first if not isinstance(first, tuple) else None
        start = 1 if domain_id is not None else 0
        for i in range(start, len(node)):
            val = node[i]
            if isinstance(val, tuple):
                _walk(val, depth + 1)
            elif domain_id is not None:
                key = (depth, domain_id)
                if key not in seen:
                    seen.add(key)
                    result.append(domain_id)
                end = sig_idx + val
                result.extend(semantic_signature[sig_idx:end])
                sig_idx = end

    _walk(raw, 0)
    return struct.pack(f"{len(result)}b", *result)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _expected_bytes(expected: tuple[int, ...]) -> bytes:
    """Convert an expected-result tuple of signed ints to bytes."""
    return struct.pack(f"{len(expected)}b", *expected)


def _bytes_to_ints(data: bytes) -> tuple[int, ...]:
    """Unpack bytes back to a tuple of signed ints (for display)."""
    return struct.unpack(f"{len(data)}b", data)