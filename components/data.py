from __future__ import annotations

from abc import ABC
from collections.abc import Iterable

from components import component
from systems.uid.guid import GUID


@component
class Primitive(ABC):
    """ Base class for all primitives where their signature can 
    return their defined name from semantic layer utilities.

    i.e. a CharacteristicCode with upp_position 1, subtype 0, and 
    category 1 would have a signature that can fetch "strength" as
    mapped by the semantic layer. 
    """
    pass

@component
class Applied(ABC):
    """ Base class for all components of a more complex signature
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