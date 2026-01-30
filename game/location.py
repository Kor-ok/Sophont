from __future__ import annotations

from typing import ClassVar

from typing_extensions import TypeAlias

SpaceCoordinate: TypeAlias = float
"""A custom coordinate based on Traveller Map's Map-Space Coordinates with
in system orbit number, decimal orbit number, and satellite number encoded in
the fractional part.
"""
TagStatus: TypeAlias = int
"""['Official', 'InReview', 'Unreviewed', 'Apocryphal', 'Preserve']"""
TagSource: TypeAlias = int
"""['OTU', 'ZCR', 'OrionOB1', 'DistantFringe', 'Faraway']"""

class Location:
    
    __slots__ = (
        "space_x",
        "space_y",
        "space_z",
        "tag_status",
        "tag_source",
        "year",
    )
    Key = tuple[SpaceCoordinate, SpaceCoordinate, SpaceCoordinate, TagStatus, TagSource, int]
    _cache: ClassVar[dict[Key, Location]] = {}

    def __new__(
        cls,
        space_x: SpaceCoordinate = 0.0,
        space_y: SpaceCoordinate = 0.0,
        space_z: SpaceCoordinate = 0.0,
        tag_status: TagStatus = 0,
        tag_source: TagSource = 0,
        year: int = 0,
    ) -> Location:
        space_x_float = float(space_x)
        space_y_float = float(space_y)
        space_z_float = float(space_z)
        tag_status_int = int(tag_status)
        tag_source_int = int(tag_source)
        year_int = int(year)
        key = (space_x_float, space_y_float, space_z_float, tag_status_int, tag_source_int, year_int)
        cached = cls._cache.get(key)
        if cached is not None:
            return cached
        
        self = super().__new__(cls)

        object.__setattr__(self, "space_x", space_x_float)
        object.__setattr__(self, "space_y", space_y_float)
        object.__setattr__(self, "space_z", space_z_float)
        object.__setattr__(self, "tag_status", tag_status_int)
        object.__setattr__(self, "tag_source", tag_source_int)
        object.__setattr__(self, "year", year_int)

        cls._cache[key] = self
        return self