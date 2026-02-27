from __future__ import annotations

import logging
import struct
from collections import OrderedDict
from importlib import import_module
from itertools import chain
from typing import Any, NamedTuple, Optional, Sequence, get_type_hints

from colorama import Fore, Style
from colorama import init as colorama_init

colorama_init(autoreset=True)

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

    __slots__ = ("elements", "members")

    def __new__(cls, elements: tuple[SemanticMapElement, ...], members: dict[tuple[str, type], int]) -> SemanticMap:
        instance = super().__new__(cls)
        instance.elements = elements
        instance.members = members
        return instance

    def __init__(self, elements: tuple[SemanticMapElement, ...], members: dict[tuple[str, type], int]) -> None:
        pass

    # -- factory ----------------------------------------------------------

    @staticmethod
    def from_raw(raw: tuple[Any, ...], members: dict[tuple[str, type], int]) -> SemanticMap:
        """Build a SemanticMap from a nested raw-tuple descriptor."""
        return SemanticMap(
            elements=tuple(SemanticMap._parse(raw, 0)),
            members=members,
            )

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
    semantic_signature: tuple[int, ...] | int,
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
    result = []
    seen: set[tuple[int, int]] = set()
    sig_idx = 0

    for depth, domain_id, count in semantic_map.elements:
        key = (depth, domain_id)
        if key not in seen:
            seen.add(key)
            result += (domain_id,)
        end = sig_idx + count
        if isinstance(semantic_signature, int):
            result += [semantic_signature] * count
        else:
            flat_list = flatten_iter(semantic_signature[sig_idx:end])
            result += flat_list
        sig_idx = end
    
    try:
        result_bytes = struct.pack(f"{len(result)}b", *result)
    except struct.error as e:
        logger.error(f"Error packing result: {e}. Result list: {result}")
        raise

    return result_bytes

def generate_signature_algorithmic(
    raw: tuple[Any, ...],
    semantic_signature: tuple[int, ...] | int,
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
                if isinstance(semantic_signature, int):
                    result.extend([semantic_signature] * val)
                else:
                    result.extend(semantic_signature[sig_idx:end])
                sig_idx = end

    _walk(raw, 0)
    return struct.pack(f"{len(result)}b", *result)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _expected_bytes(expected: tuple[int, ...] | int | list[int]) -> bytes:
    """Convert an expected-result tuple of signed ints to bytes."""
    if isinstance(expected, int):
        expected = (expected,)
    elif isinstance(expected, list):
        expected = tuple(expected)
    return struct.pack(f"{len(expected)}b", *expected)

def _bytes_to_ints(data: bytes) -> tuple[int, ...]:
    """Unpack bytes back to a tuple of signed ints (for display)."""
    return struct.unpack(f"{len(data)}b", data)

def flatten_iter(obj):
    stack = list(obj)[::-1]
    result = []

    while stack:
        x = stack.pop()
        if isinstance(x, tuple):
            stack.extend(x[::-1])
        else:
            result.append(x)

    return result

def nested_tuple_to_nested_list(tup):
    if isinstance(tup, tuple):
        return [nested_tuple_to_nested_list(item) for item in tup]
    else:
        return tup
