from __future__ import annotations
from uuid import uuid4

from sophont.aptitudes import Aptitudes
from sophont.epigenetics import EpigeneticProfile
from game.genotype import SpeciesGenotype

class Sophont:
    __slots__ = (
        "uuid",
        "name",
        "age_seconds",
        "aptitudes",
        "epigenetic_profile",
        "age_years",
    )

    def __init__(self, name: str = "Unnamed", age_seconds: int = -1):
        self.uuid: bytes = uuid4().bytes
        self.name: str = name
        self.age_seconds: int = age_seconds
        self.aptitudes: Aptitudes = Aptitudes()
        self.epigenetic_profile: EpigeneticProfile = NotImplemented  # Placeholder for SpeciesGenotype
        self.age_years: int = (
            age_seconds // 31557600 if age_seconds >= 0 else -1
        )
        
    def __repr__(self) -> str:
        return f"Sophont(uuid={self.uuid!r}, name={self.name!r}, age_seconds={self.age_seconds!r}, age_years={self.age_years!r}, aptitudes={self.aptitudes!r})"