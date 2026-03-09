from __future__ import annotations

import dataclasses
from typing import Any, ClassVar, get_type_hints

from utils.semantics import SemanticMap, SemanticsDescriptor

_SKIP_FIELDS = frozenset(
    ("subclass_dict", "component_signature", "semantic_signature", "semantic_map")
)


def _filter_type_hints(cls: type) -> dict[str, type]:
    """Return the subset of *cls*'s type-hints that are domain-relevant
    (primitive scalars or registered ``Primitive`` subclasses)."""
    base_class = cls.mro()[-2]
    subclasses = base_class.subclass_dict
    return {
        name: tp
        for name, tp in get_type_hints(cls).items()
        if name not in _SKIP_FIELDS and (tp in (int, float, bool) or tp in subclasses)
    }


def _recursive_semantic_map(
    cls: type, recursion: int = 0
) -> tuple[tuple[Any, ...], dict[tuple[str, type], int]]:
    """Build a nested semantic-map tuple and a member-position dict for *cls*.

    See _prototypes.component_bases.py
    """
    if recursion > 2:
        raise RecursionError(
            f"Recursion limit exceeded while generating semantic map for "
            f"{cls.__name__}. This may indicate a circular reference."
        )

    domain_map = cls.subclass_dict
    filtered_members = _filter_type_hints(cls)
    items = list(filtered_members.items())
    number_of_members = len(items)

    cumm_semantic_map: tuple[Any, ...] = (domain_map[cls],)
    cumm_members_map: dict[tuple[str, type], int] = {
        (f"{cls.__name__}.{name}", tp): idx for idx, (name, tp) in enumerate(items)
    }

    member_position = 0

    def _next_segment() -> tuple[int, type | None, bool]:
        """Advance through *items*, returning (scalar_count, nested_type | None, finished)."""
        nonlocal member_position
        count = 0
        while member_position < number_of_members:
            _, tp = items[member_position]
            member_position += 1
            if tp in domain_map:
                return count, tp, member_position >= number_of_members
            count += 1
        return count, None, True

    while member_position < number_of_members:
        count, nested, finished = _next_segment()
        if nested:
            nested_result, nested_members = _recursive_semantic_map(nested, recursion + 1)
            cumm_members_map.update(nested_members)
            cumm_semantic_map += (count, (nested_result))
        else:
            cumm_semantic_map += (count,)
        if not nested and finished:
            break

    return cumm_semantic_map, cumm_members_map


class Primitive:
    subclass_dict: ClassVar[dict[type, int]] = {}

    def __init_subclass__(cls) -> None:
        if dataclasses.is_dataclass(cls):
            base_dict = Primitive.subclass_dict
            if cls not in base_dict:
                cls.semantic_map: SemanticMap
                cls.component_signature: bytes
                cls.semantic_signature: tuple[int, ...]
                cls.semantics: SemanticsDescriptor

                base_dict[cls] = len(base_dict)
                raw_map, members = _recursive_semantic_map(cls)
                cls.semantic_map = SemanticMap.from_raw(raw_map, members)

    @property
    def domain_identity(self) -> int:
        """Return the domain identity for this instance's class."""
        return Primitive.subclass_dict[self.__class__]


class Applied:
    subclass_dict: ClassVar[dict[type, int]] = {}

    def __init_subclass__(cls) -> None:
        if dataclasses.is_dataclass(cls):
            base_dict = Applied.subclass_dict
            if cls not in base_dict:
                cls.semantic_map: SemanticMap
                cls.component_signature: bytes
                cls.semantic_signature: tuple[int, ...]
                cls.semantics: SemanticsDescriptor

                base_dict[cls] = len(base_dict)
                raw_map, members = _recursive_semantic_map(cls)
                cls.semantic_map = SemanticMap.from_raw(raw_map, members)

    @property
    def domain_identity(self) -> int:
        """Return the domain identity for this instance's class."""
        return Applied.subclass_dict[self.__class__]
