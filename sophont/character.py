from __future__ import annotations

from game.location import Location
from game.uid.guid import GUID, NameSpaces
from sophont.aptitudes import Aptitudes
from sophont.attributes.species import Species
from sophont.epigenetics import Epigenetics
from sophont.personals import Personals


class Sophont:
    __slots__ = (
        "guid",
        "name",
        "age_seconds",
        "location",
        "aptitudes",
        "epigenetics",
        "personals"
    )

    def __init__(self, species: Species, name: str = "Unnamed", age_seconds: int = -1):
        self.guid: int = GUID.generate(NameSpaces.Entity.CHARACTERS, NameSpaces.Owner.PLAYER)
        self.name: str = name
        self.age_seconds: int = age_seconds
        self.location: Location = Location()
        self.aptitudes: Aptitudes = Aptitudes()
        self.epigenetics: Epigenetics = Epigenetics(species=species)
        self.personals: Personals = Personals(self.epigenetics.species.genotype.genes[2].characteristic)

        # Initialize parent GUIDs list with self GUID for cloning scenarios.
        self.epigenetics.parent_guids.append(self.guid)

        # Populate parent GUIDs up to max contributors.
        max_contributors = (self.epigenetics.species.genotype
                            .compute_max_inheritance_contributors())
        while len(self.epigenetics.parent_guids) <= max_contributors:
            self.epigenetics.parent_guids.append(GUID.generate(NameSpaces.Entity.CHARACTERS, NameSpaces.Owner.PLAYER))
        # Set Epigentic Profile Gender tuple to (selected_gender, max_contributors)
        self.epigenetics.gender = (-1, max_contributors)
        
