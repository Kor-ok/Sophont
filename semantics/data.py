from __future__ import annotations

from collections.abc import Iterable

from semantics import component
from semantics.base import Applied, Primitive
from systems.uid.guid import GUID

"""
The intention here is to use the custom @component decorator as the transition point between OOP and DOTS,
i.e. the decorated class is still a normal Python class with all the usual features, but it also becomes 
a component definition that can be looked up by the various helper functions on the semantics layer.
"""

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
    """lookup code for the name of the specialisation i.e. 'anglic' as part of a language knowledge """
    associated_skill: SkillCode


@component
class GenderCode(Primitive):
    key: int
    """-1 unspecified, 0 solo, 1 female, 2 male, 3 neuter ... etc."""

class SomeTestClass:
    field1: int

@component
class TestComplexComponent(Primitive):
    field1: int
    field2: CharacteristicCode
    field3: int
    field4: int
    field5: KnowledgeCode
    field6: int
    field7: SomeTestClass

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
