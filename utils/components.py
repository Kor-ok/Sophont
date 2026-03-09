from __future__ import annotations

import dataclasses
import struct
from functools import lru_cache
from typing import Any

from utils.guid import GUID


@lru_cache(maxsize=300)
def compute_component_signature(
    instance: Any,
    base_classes: tuple[type, ...],
) -> bytes:
    """Return a flattened signed-byte signature (immutable `bytes`) for *instance*.

    Each integer is stored as a single signed byte; negative values are encoded
    with two's-complement mapping (value & 0xFF). The result is immutable.
    For GUIDs, 32-bit unsigned integers are stored separately to avoid overflow issues with signed bytes.
    """
    signed_char_results: list[int] = []
    unsigned_long_results: list[int] = []  # GUID # Skipping for now

    subclass_index = instance.subclass_dict.get(instance.__class__)
    if subclass_index is None:
        raise ValueError(f"Class {instance.__class__.__name__} not found in subclass_dict.")
    signed_char_results.append(subclass_index)

    instance_fields = dataclasses.fields(instance)

    for f in instance_fields:
        value = getattr(instance, f.name)
        if isinstance(value, GUID):
            # For GUIDs, we can store the integer value directly
            # value = getattr(instance, f.name)
            # unsigned_long_results.append(value)
            # Skipping GUIDs for now, as they are not currently used in signatures
            pass
        elif value is None:
            pass  # Skip None values for optional fields
        elif isinstance(value, tuple):
            # For tuples, we can store the length followed by the elements
            signed_char_results.append(len(value))
            for item in value:
                if isinstance(item, base_classes):
                    nested = compute_component_signature(item, base_classes)
                    nested_ints = struct.unpack(f"{len(nested)}b", nested)
                    signed_char_results.extend(nested_ints)
                else:
                    signed_char_results.append(item)
        elif isinstance(value, base_classes):
            nested = compute_component_signature(value, base_classes)
            # Convert nested bytes to a list of integers for concatenation
            nested_ints = struct.unpack(f"{len(nested)}b", nested)
            signed_char_results.extend(nested_ints)
        else:
            signed_char_results.append(value)

    result = struct.pack(f"{len(signed_char_results)}b", *signed_char_results)
    result += struct.pack(f"{len(unsigned_long_results)}L", *unsigned_long_results)
    return result
