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


# Tile-Space Coordinates system is only used by the Tile API. The coordinates are specified as x and y parameters.
# Example: Regina would be centered in a 512x384, 48px/pc tile at (x=-9.4919375, y=-9.3125)
# sqrt(12) radius = 3.46410162

# Map-Space Coordinates This is the only coordinate system with an inverted Y-axis. 
# function isEven(n) { return (n % 2) === 0; }
# var PARSEC_SCALE_X = Math.cos(Math.PI / 6); // cosine 30°
# var PARSEC_SCALE_Y = 1;

# function worldXYToMapXY(world_x, world_y) {
#   var ix = world_x - 0.5
#   var iy = isEven(world_x) ? world_y - 0.5 : world_y
#   var x = ix * PARSEC_SCALE_X;
#   var y = iy * -PARSEC_SCALE_Y;
#   return { x, y };
# }
# Example: Regina is (x=-95.914, y=70.5)

# World-Space Coordinates
# var SECTOR_WIDTH = 32;
# var SECTOR_HEIGHT = 40;

# // Core sector is (0, 0)
# var REFERENCE_SECTOR_X = 0;
# var REFERENCE_SECTOR_Y = 0;

# // Reference is Core 0140
# var REFERENCE_HEX_X = 1;
# var REFERENCE_HEX_Y = 40;

# function sectorHexToWorldXY(sx, sy, hx, hy) {
#   var x = (sx - REFERENCE_SECTOR_X) * SECTOR_WIDTH
#         + (hx - REFERENCE_HEX_X);
#   var y = (sy - REFERENCE_SECTOR_Y) * SECTOR_HEIGHT
#         + (hy - REFERENCE_HEX_Y);
#   return { x, y };
# }
# Example: Regina is (x=-110, y=-70)