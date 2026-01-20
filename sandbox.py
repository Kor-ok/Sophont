from __future__ import annotations

from game.improvedmappings.set import ATTRIBUTES

print("\033c", end="")

result = ATTRIBUTES.characteristics.default_canonical_alias_strkey_to_code
for strkey, code in result.items():
    print(f"String Key: \"{strkey}\" -> Code: {code}")