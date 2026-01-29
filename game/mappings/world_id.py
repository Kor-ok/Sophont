from __future__ import annotations

from dataclasses import dataclass


#region To Deprecate
@dataclass(frozen=True)
class OrbitID:
    Primary: int
    Secondary: int
    Tertiary: int
    Quarternary: int

@dataclass(frozen=True)
class WorldID:
    x: float
    y: float
    orbit_id: OrbitID


# p=14.289!-107!7 where p=x!y!s
# compact coordinates; x and y are Map-space coordinates; s is 1 + log2 scale.

# Earth:
EARTH_WORLD_ID = WorldID(
    x=14.289,
    y=-107.0,
    orbit_id=OrbitID(
        Primary=3,
        Secondary=0,
        Tertiary=0,
        Quarternary=0
    )
)

# p=-14.289!63.5!7
VLAND_WORLD_ID = WorldID(
    x=-14.289,
    y=63.5,
    orbit_id=OrbitID(
        Primary=4,
        Secondary=0,
        Tertiary=0,
        Quarternary=0
    )
)

# Kargol p=92.232!-45!7
KARGOL_WORLD_ID = WorldID(
    x=92.232,
    y=-45.0,
    orbit_id=OrbitID(
        Primary=1,
        Secondary=0,
        Tertiary=0,
        Quarternary=0
    )
)
#endregion
@dataclass(frozen=True)
class SystemID:
    sector_x: int
    sector_y: int
    hex_x: int
    hex_y: int
    tag: str # TODO: Find a way to map this to integer IDs.
    # tag_apocrypha: int # ['Official', 'InReview', 'Unreviewed', 'Apocryphal', 'Preserve']
    # tag_milieu: int # ['OTU', 'ZCR', 'OrionOB1', 'DistantFringe', 'Faraway']
    # year: int
    # world_space_x: int
    # world_space_y: int
    # map_space_x: float
    # map_space_y: float