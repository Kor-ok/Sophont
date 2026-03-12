from __future__ import annotations

from rich import print
from rich.pretty import pprint

from components.factories.species import generate
from processors.inheritance import InheritanceProcessor
from utils.guid import GUID

test_human_json = "D:\\Projects\\Python\\Sophont\\data\\species\\Human.json"
test_alien_json = "D:\\Projects\\Python\\Sophont\\data\\species\\TestSpecies.json"

species, guid = generate(filepath=test_human_json)
# pprint(species, expand_all=True)
# pprint(guid, expand_all=True)

sophont_guid = GUID.generate(
    ns1=GUID.Entity.CHARACTERS,
    ns2=GUID.Owner.PLAYER,
    name="Player",
)
sophont_upps, progenitor_guids = InheritanceProcessor.species_to_upps(sophont_guid, species)

print("Constructed UPP List:")
for upp in sophont_upps:
    print(
        f"{upp.xene.__class__.__name__} - {upp.xene.characteristic.upp_position} - {repr(upp.xene.characteristic)}: {upp.rolls}"
    )

print("\nProgenitor GUIDs and Traits:")
pprint(progenitor_guids)
