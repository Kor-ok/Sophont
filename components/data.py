from __future__ import annotations

import dataclasses
from abc import ABC
from collections.abc import Iterable
from typing import ClassVar, get_type_hints

from components import component
from systems.uid.guid import GUID


def _get_signature_type(
    cls: type,
    primitive_types: tuple[type, ...] = (int, float, bool),
) -> tuple[type, ...]:
    """Return a flattened tuple of primitive field types for *cls*,
    preserving declaration order.

    Non-primitive fields whose type carries its own annotations
    (e.g. another component class) are expanded recursively.
    """
    result: list[type] = []
    hints = get_type_hints(cls)

    # Prefer dataclass fields (excludes ClassVar, ordered correctly).
    # Fall back to the class's own __annotations__ for classes that
    # have not yet been processed by @dataclass / @component.
    try:
        own_field_names = [f.name for f in dataclasses.fields(cls)]
    except TypeError:
        own_field_names = list(cls.__dict__.get("__annotations__", {}))

    for name in own_field_names:
        field_type = hints.get(name)
        if field_type is None:
            continue
        if field_type in primitive_types:
            result.append(field_type)
        elif hasattr(field_type, "__annotations__"):
            result.extend(_get_signature_type(field_type, primitive_types))

    return tuple(result)


@component
class Primitive(ABC):
    """Base class for all primitives where their signature can
    return their defined name from semantic layer utilities.

    i.e. a CharacteristicCode with upp_position 1, subtype 0, and
    category 1 would have a signature that can fetch "strength" as
    mapped by the semantic layer.

    ``Signature`` is a class-level attribute computed automatically for
    each concrete subclass — a flattened tuple of primitive field types
    preserving declaration order.
    """

    Signature: ClassVar[tuple[type, ...]] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        cls.Signature = _get_signature_type(cls)


@component
class Applied(ABC):
    """Base class for all components of a more complex signature
    that can hold references to Primitive components or other
    Applied components.
    """

    pass


@component
class CharacteristicCode(Primitive):
    upp_position: int
    subtype: int
    """0 is default, i.e. upp_position 1 of subtype 0 is strength"""
    category: int
    """1 physical, 2 mental, 3 social, 4 obscure"""


@component
class SkillCode(Primitive):
    key: int
    """code for the skill, i.e. 21 language"""
    set: int
    """1 general, 2 default, 3 talents, 4 personals, 5 intuitions"""
    group: int
    """1 base, 2 starship skills, 3 trades, 4 arts, 5 soldier skills"""


@component
class KnowledgeCode(Primitive):
    key: int
    """code for the knowledge, i.e. 57 sophontology"""
    focus: int
    """lookup code for the name of the specialisation i.e. 'anglic' """
    associated_skill: SkillCode


@component
class GenderCode(Primitive):
    key: int
    """-1 unspecified, 0 solo, 1 female, 2 male, 3 neuter ... etc."""


@component
class GeneCode(Applied):
    characteristic: CharacteristicCode
    precedence: int
    die_mult: int
    gender_link: GenderCode
    characteristic_link: CharacteristicCode
    contributor_pool_size: int


@component
class PheneCode(Applied):
    characteristic: CharacteristicCode
    is_grafted: bool
    precedence: int
    contributor_guid: GUID


@component
class GenotypeCode(Applied):
    genes: Iterable[GeneCode]
    phenes: Iterable[PheneCode]


@component
class SpeciesCode(Applied):
    genotype: GenotypeCode
    identifying_guid: GUID
