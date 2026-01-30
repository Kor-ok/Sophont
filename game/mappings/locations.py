from __future__ import annotations

from game.mappings.data import (
    AliasMap,
    CanonicalCodeInt,
)

tag_status: dict[CanonicalCodeInt, AliasMap] = {
    -99: {"undefined": ("unknown", "none", "null")},
    -1: {"custom": ("user defined", "user-defined", "user")},
    0: {"official": ("canonical", "canon")},
    1: {"inreview": ("in review", "in-review")},
    2: {"unreviewed": ("un reviewed", "un-reviewed")},
    3: {"apocryphal": ("apocrypha",)},
    4: {"preserve": ("preserved", "legacy")},
}

tag_source: dict[CanonicalCodeInt, AliasMap] = {
    -99: {"undefined": ("unknown", "none", "null")},
    -1: {"custom": ("user defined", "user-defined", "user")},
    0: {"otu": ("original",)},
    1: {"zcr": ("zcr",)},
    2: {"orionob1": ("orion",)},
    3: {"distantfringe": ("distant fringe", "fringe")},
    4: {"faraway": ("farway",)},
}

