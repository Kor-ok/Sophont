from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto

from game.primitives.data import FullCode
from game.primitives.senses import Sensor
from sophont.attributes.characteristic import Characteristic
from sophont.attributes.package import AttributePackage
from sophont.attributes.skill import Skill

PartID = tuple[FullCode, Sensor]

class Symmetry(Enum):
    BILATERAL = auto()
    TRILATERAL = auto()
    RADIAL = auto()
    ASYMMETRICAL = auto()

class BodySegments(Enum):
    HEAD = PartID
    TORSO = PartID
    FRONT_LIMBS = PartID
    REAR_LIMBS = PartID
    TAIL_OR_SNOUT = PartID

@dataclass(frozen=True)
class Brain:
    type: int
    intelligence: AttributePackage[Characteristic] | None
    units: int
    skills: Iterable[AttributePackage[Skill]] | None