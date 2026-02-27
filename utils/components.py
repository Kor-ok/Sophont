from __future__ import annotations

import dataclasses
import struct
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=300)
def compute_component_signature(
    instance: Any,
    base_classes: tuple[type, ...],
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
        if isinstance(value, base_classes):
            nested = compute_component_signature(value, base_classes)
            # Convert nested bytes to a list of integers for concatenation
            nested_ints = struct.unpack(f"{len(nested)}b", nested)
            result.extend(nested_ints)
        else:
            result.append(value)

    return struct.pack(f"{len(result)}b", *result)