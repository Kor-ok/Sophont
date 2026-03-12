from __future__ import annotations

from typing import Optional, Union

from components import component
from components.base import Applied
from components.primitives import CharacteristicCode, GenderCode, VisionCode
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


@component
class PheneCode(Applied):
    characteristic: CharacteristicCode
    is_grafted: bool
    precedence: int
    die_mult: int


@component(flyweight=False)
class GenotypeCode(Applied):
    genes: tuple[GeneCode, ...]
    phenes: Optional[tuple[PheneCode, ...]]


@component
class SpeciesCode(Applied):
    genotype: GenotypeCode
    genders: tuple[GenderCode, ...]


@component(flyweight=False)
class UPP(Applied):
    xene: Union[GeneCode, PheneCode]
    rolls: tuple[int, ...]


@component
class Sensation(Applied):
    sense: Union[tuple[VisionCode, ...], None]
    constant: tuple[int, ...]


MODULE_GRAPH = ModuleGraph()
