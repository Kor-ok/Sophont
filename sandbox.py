from __future__ import annotations

from pprint import pprint

from systems.uid.guid import GUID

example_guid: GUID = GUID.generate(GUID.NameSpaces.Entity.CHARACTERS, GUID.NameSpaces.Owner.PLAYER, name="ExampleCharacter")
pprint(f"Generated GUID: {example_guid} ({example_guid.uid_to_string})")
