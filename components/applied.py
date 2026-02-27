from __future__ import annotations

from collections.abc import Iterable

from components import component
from components.base import Applied
from components.primitives import CharacteristicCode, GenderCode
from utils.guid import GUID
from utils.inspection import ModuleGraph


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


MODULE_GRAPH = ModuleGraph()