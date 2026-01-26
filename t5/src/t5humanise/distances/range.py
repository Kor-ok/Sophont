from __future__ import annotations

from enum import Enum

from typing_extensions import TypeAlias

RangeIndex: TypeAlias = int
"""An index representing a specific range band."""
RangeSubBand: TypeAlias = float
"""A sub-division within a range band."""
Range: TypeAlias = tuple[RangeIndex, RangeSubBand]
"""Any Range Band can be divided into several decimal 
Sub-Bands when the distinction is important. Most often, 
some altitudes need further differentiation. """

SizeIndex: TypeAlias = int
"""An index representing a specific size band."""
WorldSurfaceIndex: TypeAlias = int
"""Useful with individuals, with small arms, and with events on or near worlds. """
DistanceMeters: TypeAlias = float
"""A distance in meters."""
RangeDescriptor: TypeAlias = str
"""A textual descriptor for a range band."""
Benchmark: TypeAlias = str
"""An illustrative example for a range band."""

class WorldRange(Enum):
    CONTACT = 0
    READING = "R"
    TALKING = "T"
    VSHORT = 1
    SHORT = 2
    MEDIUM = 3
    LONG = 4
    VLONG = 5
    DISTANT = 6
    VDISTANT = 7
    ORBIT = 8
    FARORBIT = 9 

class SpaceRange:
    @staticmethod
    def to_world_range(v: int | str) -> int:
        if v == "B" or v == "BOARDING":
            return WorldRange.VLONG.value
        elif isinstance(v, int):
            return v + WorldRange.VLONG.value
        else:
            raise ValueError(f"Cannot convert {v} to WorldRange index.")
        
    @staticmethod
    def from_world_range(v: WorldRange) -> int | str | None:
        if v == WorldRange.VLONG:
            return "BOARDING"
        elif v == WorldRange.READING or v == WorldRange.TALKING:
            v = WorldRange.CONTACT
        elif v.value > WorldRange.VLONG.value:
            return v.value - WorldRange.VLONG.value
        else:
            raise ValueError(f"Cannot convert {v} from WorldRange index.")
    

world_surface_range_distances: dict[WorldRange, DistanceMeters] = {
    WorldRange.CONTACT: 0.0,
    WorldRange.READING: 0.5,
    WorldRange.TALKING: 1.5,
    WorldRange.VSHORT: 5.0,
    WorldRange.SHORT: 50.0,
    WorldRange.MEDIUM: 150.0,
    WorldRange.LONG: 500.0,
    WorldRange.VLONG: 1000.0,
    WorldRange.DISTANT: 5000.0,
    WorldRange.VDISTANT: 50000.0, # 50 km
    WorldRange.ORBIT: 500000.0, # 500 km
    WorldRange.FARORBIT: 5000000.0, # 5000 km
}

range_benchmarks: dict[WorldRange, Benchmark] = {
    WorldRange.CONTACT: "Touching",
    WorldRange.READING: "Normal Reading",
    WorldRange.TALKING: "Conversations",
    WorldRange.VSHORT: "Lectures",
    WorldRange.SHORT: "Shouting Distance. Pistol Shot.",
    WorldRange.MEDIUM: "City Block. Rifle Shot.",
    WorldRange.DISTANT: "Near The Horizon",
    WorldRange.VDISTANT: "Beyond The Horizon",
}

size_benchmarks: dict[SizeIndex, Benchmark] = {
    WorldRange.VSHORT.value: "Coin",
    WorldRange.SHORT.value: "Eye",
    WorldRange.MEDIUM.value: "Head",
    WorldRange.LONG.value: "Rifle",
    WorldRange.VLONG.value: "Person",
    WorldRange.DISTANT.value: "Vehicle",
    WorldRange.VDISTANT.value: "ACS",
    WorldRange.ORBIT.value: "BCS",
    WorldRange.FARORBIT.value: "Moonlet",
}

range_band_width_meters: dict[WorldRange, tuple[DistanceMeters, DistanceMeters]] = {
    WorldRange.CONTACT: (0.0, 3.0),
    WorldRange.READING: (0.25, 1.0),
    WorldRange.TALKING: (1.0, 3.0),
    WorldRange.VSHORT: (3.0, 25.0),
    WorldRange.SHORT: (25.0, 100.0),
    WorldRange.MEDIUM: (100.0, 300.0),
    WorldRange.LONG: (300.0, 750.0),
    WorldRange.VLONG: (750.0, 3000.0),
    WorldRange.DISTANT: (3000.0, 25000.0),
    WorldRange.VDISTANT: (25000.0, 250000.0),
    WorldRange.ORBIT: (250000.0, 2500000.0),
    WorldRange.FARORBIT: (2500000.0, 25000000.0),
}

world_surface_ranges: dict[Range, WorldRange | None] = {
    (13, 0.0): None,
    (12, 0.0): None,
    (11, 0.0): None,
    (10, 0.0): None,
    (9, 0.0): WorldRange.FARORBIT,
    (8, 0.0): WorldRange.ORBIT,
    (7, 0.8): None,
    (7, 0.6): None,
    (7, 0.4): None,
    (7, 0.2): None,
    (7, 0.0): WorldRange.VDISTANT,
    (6, 0.8): None,
    (6, 0.6): None,
    (6, 0.4): None,
    (6, 0.2): None,
    (6, 0.0): WorldRange.DISTANT,
    (5, 0.0): WorldRange.VLONG,
    (4, 0.0): WorldRange.LONG,
    (3, 0.0): WorldRange.MEDIUM,
    (2, 0.0): WorldRange.SHORT,
    (1, 0.0): WorldRange.VSHORT,
    (0, 0.3): WorldRange.TALKING,
    (0, 0.1): WorldRange.READING,
    (0, 0.0): WorldRange.CONTACT,
    (0, -0.1): WorldRange.READING,
    (0, -0.3): WorldRange.TALKING,
    (-1, 0.0): None,
    (-2, 0.0): None,
    (-3, 0.0): None,
    (-4, 0.0): None,
    (-5, 0.0): None,
    (-6, 0.0): None,
    (-7, 0.0): None,
    (-8, 0.0): None,
    (-9, 0.0): None,
}

standard_range_bands: tuple[Range, ...] = (
    (18, 0.0),
    (17, 0.0),
    (16, 0.0),
    (15, 0.0),
    (14, 0.0),
    (13, 0.0),
    (12, 0.0),
    (11, 0.0),
    (10, 0.0),
    (9, 0.0),
    (8, 0.0),
    (7, 0.8),
    (7, 0.6),
    (7, 0.4),
    (7, 0.2),
    (7, 0.0),
    (6, 0.8),
    (6, 0.6),
    (6, 0.4),
    (6, 0.2),
    (6, 0.0),
    (5, 0.0),
    (4, 0.0),
    (3, 0.0),
    (2, 0.0),
    (1, 0.0),
    (0, 0.3),
    (0, 0.1),
    (0, 0.0),
    (0, -0.1),
    (0, -0.3),
    (-1, 0.0),
    (-2, 0.0),
    (-3, 0.0),
    (-4, 0.0),
    (-5, 0.0),
    (-6, 0.0),
    (-7, 0.0),
    (-8, 0.0),
    (-9, 0.0),
)

STANDARD_RANGE_BANDS_DICT: dict[int, Range] = {
    i: band for i, band in enumerate(standard_range_bands)
}

class Band:

    pass # Placeholder for actual implementation