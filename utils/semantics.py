from __future__ import annotations

import struct
from typing import Any, NamedTuple, Optional


class SemanticMapElement(NamedTuple):
    """Immutable flyweight: one flattened node of the semantic map."""

    depth: int
    domain_identity: int
    pre_nested_count: int


class SemanticMap:
    """Pre-parsed semantic map
    See prototype: _prototypes.semantic_mapping.py
    """

    __slots__ = ("elements", "members")

    def __new__(cls, elements: tuple[SemanticMapElement, ...], members: dict[tuple[str, type], int]) -> SemanticMap:
        instance = super().__new__(cls)
        instance.elements = elements
        instance.members = members
        return instance

    def __init__(self, elements: tuple[SemanticMapElement, ...], members: dict[tuple[str, type], int]) -> None:
        pass


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
        """Recursively flatten *raw* into an ordered list of elements."""
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
    """OOP based signature generation from a pre-parsed map."""
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
        raise ValueError(f"Error packing result: {e}. Result list: {result}") from e

    return result_bytes

def generate_signature_algorithmic(
    raw: tuple[Any, ...],
    semantic_signature: tuple[int, ...] | int,
) -> bytes:
    """Single-pass signature generation — no intermediate parse objects.

    Walks the nested raw-tuple map and assembles the component signature in one
    recursive traversal, fusing the parse and generate steps.
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

def signature_transformer(semantic_signature: list, semantic_mapping: list) -> list:
    """Produce a hierarchical listing with embedded IDs from the pattern.
    See prototype: _prototypes.semantic_mapping.py
    """
    def atoms_with_depth(arr: list, depth: int = 0):
        """Yield (depth, value) for each non-list element."""
        for item in arr:
            if isinstance(item, list):
                yield from atoms_with_depth(item, depth + 1)
            else:
                yield (depth, item)

    tagged = list(atoms_with_depth(semantic_signature))
    
    def hierarchy(
        tagged_atoms: list[tuple[int, int]],
        pattern: list[list[int]],
    ) -> list[list[int]]:
        
        if not tagged_atoms:
            return []

        max_depth = max(d for d, _ in tagged_atoms)

        depth_pools: dict[int, list[int | None]] = {}
        for target_depth in range(max_depth + 1):
            pool: list[int | None] = []
            in_subtree = False
            for depth, value in tagged_atoms:
                if depth < target_depth:
                    if in_subtree:
                        pool.append(None)  # sentinel: subtree boundary
                        in_subtree = False
                elif depth == target_depth:
                    in_subtree = True
                    pool.append(value)
                else:
                    in_subtree = True
            depth_pools[target_depth] = pool

        depth_cursors: dict[int, int] = {d: 0 for d in depth_pools}
        depth_subtree_idx: dict[int, int] = {d: 0 for d in depth_pools}

        rows: dict[tuple[int, int], list[int]] = {}

        def _ensure_row(d: int, si: int) -> list[int]:
            if (d, si) not in rows:
                rows[(d, si)] = []
            return rows[(d, si)]

        def _consume(target_depth: int, count: int) -> list[int]:
            pool = depth_pools[target_depth]
            cursor = depth_cursors[target_depth]
            values: list[int] = []
            while len(values) < count and cursor < len(pool):
                item = pool[cursor]
                cursor += 1
                if item is None:
                    depth_subtree_idx[target_depth] += 1
                else:
                    values.append(item)
            depth_cursors[target_depth] = cursor
            return values

        prev_depth = -1
        for step_depth, step_id, step_count in pattern:
            entering_deeper = step_depth > prev_depth

            consumed = _consume(step_depth, step_count)

            for d in range(step_depth + 1):
                si = depth_subtree_idx[d]
                row = _ensure_row(d, si)
                if entering_deeper:
                    row.append(step_id)
                row.extend(consumed)

            prev_depth = step_depth

        result: list[list[int]] = []
        for d in range(max_depth + 1):
            si = 0
            while (d, si) in rows:
                result.append(rows[(d, si)])
                si += 1

        return result
    
    result = hierarchy(tagged, semantic_mapping)
    return result
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

def split_flattened_aliases(flattened_aliases: str | None) -> tuple[str, ...]:
    if flattened_aliases is None:
        return ("UNDEFINED",)
    return tuple(alias.strip().capitalize() for alias in flattened_aliases.split(",") if alias.strip())