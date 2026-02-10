from __future__ import annotations

from collections.abc import Iterable

from numpy import bool as np_bool
from numpy import int8

from components import component
from components.base import Applied, Primitive
from systems.uid.guid import GUID


@component
class CharacteristicCode(Primitive):
    upp_position: int8
    subtype: int8
    """0 is default, i.e. upp_position 1 of subtype 0 is strength"""
    category: int8
    """1 physical, 2 mental, 3 social, 4 obscure"""


@component
class SkillCode(Primitive):
    key: int8
    """code for the skill, i.e. 21 language"""
    set: int8
    """1 general, 2 default, 3 talents, 4 personals, 5 intuitions"""
    group: int8
    """1 base, 2 starship skills, 3 trades, 4 arts, 5 soldier skills"""


@component
class KnowledgeCode(Primitive):
    key: int8
    """code for the knowledge, i.e. 57 sophontology"""
    focus: int8
    """lookup code for the name of the specialisation i.e. 'anglic' """
    associated_skill: SkillCode


@component
class GenderCode(Primitive):
    key: int8
    """-1 unspecified, 0 solo, 1 female, 2 male, 3 neuter ... etc."""


@component
class GeneCode(Applied):
    characteristic: CharacteristicCode
    precedence: int8
    die_mult: int8
    gender_link: GenderCode
    characteristic_link: CharacteristicCode
    contributor_pool_size: int8


@component
class PheneCode(Applied):
    characteristic: CharacteristicCode
    is_grafted: np_bool
    precedence: int8
    contributor_guid: GUID


@component
class GenotypeCode(Applied):
    genes: Iterable[GeneCode]
    phenes: Iterable[PheneCode]


@component
class SpeciesCode(Applied):
    genotype: GenotypeCode
    identifying_guid: GUID
