from __future__ import annotations

import sys

from game.mappings.data import (
    AliasMap,
    CanonicalCodeInt,
)

milieu_aliases: dict[CanonicalCodeInt, AliasMap] = {
    0: {"undefined": ("unknown", "none", "null")},
    1: {"grandfather's children": ("grandfathers children", "grandfather")},
    2: {"the false dawn": ("false dawn",)},
    3: {"early ziru sirka": ("ziru sirka",)},
    4: {"consolidation wars": ("consolidation",)},
    5: {"rigid vilani culture": ("rigid vilani culture",)},
    6: {"iw": ("interstellar wars", "the interstellar wars")},
    7: {"the rule of man": ("rule of man",)},
    8: {"the long night": ("long night",)},
    9: {"m0": ("milieu 0", "early imperium")},
    10: {"aslan border wars": ("aslan wars",)},
    11: {"m600": ("civil war",)},
    12: {"psionic suppressions": ("psionic",)},
    13: {"m990": ("solomani rim war", "solomani rim")},
    14: {"m1105": ("the golden age", "golden age")},
    15: {"the rebellion": ("rebellion",)},
    16: {"m1120": ("the collapse", "collapse")},
    17: {"the virus era": ("virus era", "virus")},
    18: {"m1201": ("the dark ages", "dark ages", "the new era", "new era")},
    19: {"m1248": ("the long night", "long night", "the new new era", "new new era")},
    20: {"m1900": ("the new imperium", "new imperium", "the far far future", "far far future")},
}

milieu_year_map: dict[CanonicalCodeInt, int] = {
    0: -sys.maxsize,
    1: -300000,
    2: -200000,
    3: -9200,
    4: -5400,
    5: -4400,
    6: 2100,
    7: 2300,
    8: 2750,
    9: 4518,
    10: 4518+300,
    11: 4518+600,
    12: 4518+880,
    13: 4518+990,
    14: 4518+1000,
    15: 4518+1116,
    16: 4518+1130,
    17: 4518+1200,
    18: 4518+1201,
    19: 4518+1248,
    20: 4518+1902,
}