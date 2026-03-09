from __future__ import annotations

from typing import Optional

from components import component
from components.base import Applied
from components.primitives import CharacteristicCode, GenderCode
from utils.guid import GUID
from utils.inspection import ModuleGraph

"""Nested ECS Component System:
Applied gather data via the internal, runtime semantics system.
vs. Primitives which gather data via the T5 API.
"""


@component
class GeneCode(Applied):
    characteristic: CharacteristicCode
    precedence: int
    die_mult: int
    gender_link: Optional[GenderCode]
    characteristic_link: Optional[CharacteristicCode]
    contributor_pool_size: int
    contributor_guid: GUID


@component
class PheneCode(Applied):
    characteristic: CharacteristicCode
    is_grafted: bool
    precedence: int
    die_mult: int
    contributor_guid: GUID


@component
class GenotypeCode(Applied):
    genes: tuple[GeneCode, ...]
    phenes: tuple[PheneCode, ...]


@component
class SpeciesCode(Applied):
    genotype: GenotypeCode
    identifying_guid: GUID


@component
class UPP(Applied):
    position: int
    value: int


MODULE_GRAPH = ModuleGraph()
