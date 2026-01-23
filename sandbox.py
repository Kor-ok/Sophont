from __future__ import annotations

import os
import sys
from collections import defaultdict
from collections.abc import Mapping
from random import choice, randint

from game.characteristic import Characteristic
from game.gene import Gene
from game.genotype import Genotype
from game.mappings.set import ATTRIBUTES
from game.phene import Phene

if sys.stdout.isatty() and "CLEAR_SCREEN" in os.environ:
    print("\033c", end="")

CanonicalStrKey = str
StringAliases = tuple[str, ...]
AliasMap = Mapping[CanonicalStrKey, StringAliases]

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCode = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]

AliasMappedFullCode = tuple[AliasMap, FullCode]

CharacteristicName = str
CharacteristicCodeCollection = list[FullCode]


if __name__ == "__main__":

    print("\033c", end="")
    result = ATTRIBUTES.knowledges.get_all()
    print(result)
