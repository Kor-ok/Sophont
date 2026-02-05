from __future__ import annotations

from abc import ABC
from collections.abc import Iterable

from components import component


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
    """-99 undefined, 1	physical, 2	mental, 3 social, 4	obscure""" 

@component
class SkillCode(Primitive):
    key: int
    set: int
    group: int

@component
class KnowledgeCode(Primitive):
    key: int
    focus: int
    associated_skill: SkillCode

@component
class GenderCode(Primitive):
    code: int


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
    contributor_guid: int

@component
class GenotypeCode(Applied):
    genes: Iterable[GeneCode]
    phenes: Iterable[PheneCode]

@component
class SpeciesCode(Applied):
    genotype: GenotypeCode
    origin_guid: int