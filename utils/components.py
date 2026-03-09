from __future__ import annotations

import dataclasses
import struct
from functools import lru_cache
from typing import Any

from utils.guid import GUID


@lru_cache(maxsize=300)
def _compute_component_signature_parts(
    instance: Any,
    base_classes: tuple[type, ...],
) -> tuple[int, ...]:
    """Return a flattened signed-byte signature as integers for *instance*.

    This keeps nested traversal in integer space so callers only pack to bytes
    once at the top level.
    """
    signed_char_results: list[int] = []

    subclass_index = instance.subclass_dict.get(instance.__class__)
    if subclass_index is None:
        raise ValueError(f"Class {instance.__class__.__name__} not found in subclass_dict.")
    signed_char_results.append(subclass_index)

    instance_field_names = getattr(instance.__class__, "__component_field_names__", None)
    if instance_field_names is None:
        instance_field_names = tuple(field.name for field in dataclasses.fields(instance))

    for field_name in instance_field_names:
        value = getattr(instance, field_name)
        if isinstance(value, GUID):
            # For GUIDs, we can store the integer value directly
            # value = getattr(instance, f.name)
            # Skipping GUIDs for now, as they are not currently used in signatures
            pass
        elif value is None:
            pass  # Skip None values for optional fields
        elif isinstance(value, tuple):
            # For tuples, we can store the length followed by the elements
            signed_char_results.append(len(value))
            for item in value:
                if isinstance(item, base_classes):
                    signed_char_results.extend(
                        _compute_component_signature_parts(item, base_classes)
                    )
                else:
                    signed_char_results.append(item)
        elif isinstance(value, base_classes):
            signed_char_results.extend(_compute_component_signature_parts(value, base_classes))
        else:
            signed_char_results.append(value)

    return tuple(signed_char_results)


def compute_component_signature(
    instance: Any,
    base_classes: tuple[type, ...],
) -> bytes:
    """Return a flattened signed-byte signature (immutable `bytes`) for *instance*.

    Each integer is stored as a single signed byte; negative values are encoded
    with two's-complement mapping (value & 0xFF). The result is immutable.
    For GUIDs, 32-bit unsigned integers are stored separately to avoid overflow issues with signed bytes.
    """
    signed_char_results = _compute_component_signature_parts(instance, base_classes)
    return struct.pack(f"{len(signed_char_results)}b", *signed_char_results)


compute_component_signature.cache_info = _compute_component_signature_parts.cache_info  # type: ignore[attr-defined]
compute_component_signature.cache_clear = _compute_component_signature_parts.cache_clear  # type: ignore[attr-defined]
