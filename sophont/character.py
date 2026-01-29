from __future__ import annotations

from textwrap import indent

from game.location import Location
from game.species import Species
from game.uid.guid import GUID, NameSpaces
from sophont.aptitudes import Aptitudes
from sophont.epigenetics import Epigenetics
from sophont.personals import Personals


class Sophont:
    __slots__ = (
        "uuid",
        "name",
        "age_seconds",
        "location",
        "aptitudes",
        "epigenetics",
        "personals"
    )

    def __init__(self, species: Species, name: str = "Unnamed", age_seconds: int = -1):
        self.uuid: int = GUID.generate(NameSpaces.Entity.CHARACTERS, NameSpaces.Owner.PLAYER)
        self.name: str = name
        self.age_seconds: int = age_seconds
        self.location: Location = Location()
        self.aptitudes: Aptitudes = Aptitudes()
        self.epigenetics: Epigenetics = Epigenetics(species=species)
        self.personals: Personals = Personals(self.epigenetics.species.genotype.genes[2].characteristic)

        # Initialize parent UUIDs list with self UUID for cloning scenarios.
        self.epigenetics.parent_uuids.append(self.uuid)

        # Populate parent UUIDs up to max contributors.
        max_contributors = (self.epigenetics.species.genotype
                            .compute_max_inheritance_contributors())
        while len(self.epigenetics.parent_uuids) <= max_contributors:
            self.epigenetics.parent_uuids.append(GUID.generate(NameSpaces.Entity.CHARACTERS, NameSpaces.Owner.PLAYER))

        # Set Epigentic Profile Gender tuple to (selected_gender, max_contributors)
        self.epigenetics.gender = (-1, max_contributors)
        
    def __repr__(self) -> str:
        indentation = "  "
        display = []
        display.append(f"uuid={self.uuid!r}")
        display.append(f"name={self.name!r}")
        display.append(f"age_seconds={self.age_seconds!r}")
        display.append(f"location={self.location!r}")
        display.append(f"aptitudes={self.aptitudes!r}")
        display.append(f"epigenetics={self.epigenetics!r}")
        display.append(f"personals={self.personals!r}")
        # Join with Newlines for readability
        return "Sophont(\n" + indent(",\n".join(display), indentation) + "\n)"