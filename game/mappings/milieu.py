from __future__ import annotations

from game.mappings.data import (
    AliasMap,
    CanonicalCodeInt,
)

milieu_aliases: dict[CanonicalCodeInt, AliasMap] = {
    -99: {"undefined": ("unknown", "none", "null")},
    -5: {"grandfather's children": ("grandfathers children", "grandfather")},
    -4: {"the false dawn": ("false dawn",)},
    -3: {"early ziru sirka": ("ziru sirka",)},
    -2: {"consolidation wars": ("consolidation",)},
    -1: {"rigid vilani culture": ("rigid vilani culture",)},
    0: {"iw": ("interstellar wars", "the interstellar wars")},
    1: {"the rule of man": ("rule of man",)},
    2: {"the long night": ("long night",)},
    3: {"m0": ("milieu 0", "early imperium")},
    4: {"aslan border wars": ("aslan wars",)},
    5: {"m600": ("civil war",)},
    6: {"psionic suppressions": ("psionic",)},
    7: {"m990": ("solomani rim war", "solomani rim")},
    8: {"m1105": ("the golden age", "golden age")},
    9: {"the rebellion": ("rebellion",)},
    10: {"m1120": ("the collapse", "collapse")},
    11: {"the virus era": ("virus era", "virus")},
    12: {"m1201": ("the dark ages", "dark ages", "the new era", "new era")},
    13: {"m1248": ("the long night", "long night", "the new new era", "new new era")},
    14: {"m1900": ("the new imperium", "new imperium", "the far far future", "far far future")},
}

milieu_year_map: dict[CanonicalCodeInt, int] = {
    -5: -300000,
    -4: -200000,
    -3: -9200,
    -2: -5400,
    -1: -4400,
    0: 2100,
    1: 2300,
    2: 2750,
    3: 4518,
    4: 4518+300,
    5: 4518+600,
    6: 4518+880,
    7: 4518+990,
    8: 4518+1000,
    9: 4518+1116,
    10: 4518+1130,
    11: 4518+1200,
    12: 4518+1248,
    13: 4518+1902,
}