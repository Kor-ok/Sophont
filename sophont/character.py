from __future__ import annotations

from textwrap import indent
from uuid import uuid4

from game.species import Species
from sophont.aptitudes import Aptitudes
from sophont.epigenetics import EpigeneticProfile


class Sophont:
    __slots__ = (
        "uuid",
        "name",
        "age_seconds",
        "aptitudes",
        "epigenetic_profile",
    )

    def __init__(self, species_genotype: Species, name: str = "Unnamed", age_seconds: int = -1):
        self.uuid: bytes = uuid4().bytes
        self.name: str = name
        self.age_seconds: int = age_seconds
        self.aptitudes: Aptitudes = Aptitudes()
        self.epigenetic_profile: EpigeneticProfile = EpigeneticProfile(species_genotype=species_genotype)
        
    def __repr__(self) -> str:
        indentation = "  "
        display = []
        display.append(f"uuid={self.uuid!r}")
        display.append(f"name={self.name!r}")
        display.append(f"age_seconds={self.age_seconds!r}")
        display.append(f"aptitudes={self.aptitudes!r}")
        display.append(f"epigenetic_profile={self.epigenetic_profile!r}")
        # Join with Newlines for readability
        return "Sophont(\n" + indent(",\n".join(display), indentation) + "\n)"