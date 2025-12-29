from __future__ import annotations
from uuid import uuid4

from sophont.aptitudes import Aptitudes
from sophont.epigenetics import EpigeneticProfile
from game.genotype import Genotype

class Sophont:
    __slots__ = (
        "uuid",
        "name",
        "age_seconds",
        "aptitudes",
        "epigenetic_profile",
    )

    def __init__(self, species_genotype: Genotype, name: str = "Unnamed", age_seconds: int = -1):
        self.uuid: bytes = uuid4().bytes
        self.name: str = name
        self.age_seconds: int = age_seconds
        self.aptitudes: Aptitudes = Aptitudes()
        self.epigenetic_profile: EpigeneticProfile = EpigeneticProfile(genotype=species_genotype)
        
    def __repr__(self) -> str:
        return f"Sophont(uuid={self.uuid!r}, name={self.name!r}, age_seconds={self.age_seconds!r}, aptitudes={self.aptitudes!r})"