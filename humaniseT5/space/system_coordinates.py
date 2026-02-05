from __future__ import annotations


def pack_orbital_coordinate(primary_orbit_number: int, satellite_orbit: int) -> int:
    """Pack an orbit number (0-20) and satellite orbit (1-26)"""
    if not (0 <= primary_orbit_number <= 20):
        raise ValueError("Primary orbit number must be in range 0-20")
    if not (1 <= satellite_orbit <= 26):
        raise ValueError("Satellite orbit must be in range 1-26")
    return (primary_orbit_number << 5) | (satellite_orbit & 0x1F)


def unpack_orbital_coordinate(packed_orbit: int) -> tuple[int, int]:
    """Unpack an orbit number into (primary_orbit_number, satellite_orbit)"""
    primary_orbit_number = (packed_orbit >> 5) & 0x1F
    satellite_orbit = packed_orbit & 0x1F
    return primary_orbit_number, satellite_orbit


def pack_nested_orbital_coordinate(
    primary_orbit_number: int, nested_orbital_coordinate: int
) -> int:
    """Within a primary orbit number (0-20), pack a nested orbital coordinate (0-255)"""
    if not (0 <= primary_orbit_number <= 20):
        raise ValueError("Primary orbit number must be in range 0-20")
    if not (0 <= nested_orbital_coordinate <= 255):
        raise ValueError("Nested orbital coordinate must be in range 0-255")
    return (primary_orbit_number << 8) | (nested_orbital_coordinate & 0xFF)


def unpack_nested_orbital_coordinate(packed_orbit: int) -> tuple[int, int]:
    """Unpack a nested orbital coordinate into (primary_orbit_number, nested_orbital_coordinate)"""
    primary_orbit_number = (packed_orbit >> 8) & 0x1F
    nested_orbital_coordinate = packed_orbit & 0xFF
    return primary_orbit_number, nested_orbital_coordinate


# Satellite orbit letter mapping (1-26 -> A-Z)
SATELLITE_LETTERS = " ABCDEFGHIJKLMNOPQRSTUVWXYZ"  # Index 0 = no satellite, 1-26 = A-Z


def satellite_to_letter(satellite_orbit: int) -> str:
    """Convert satellite orbit number (1-26) to letter (A-Z). 0 returns empty string."""
    if satellite_orbit == 0:
        return ""
    if not (1 <= satellite_orbit <= 26):
        raise ValueError("Satellite orbit must be in range 1-26")
    return SATELLITE_LETTERS[satellite_orbit]


def letter_to_satellite(letter: str) -> int:
    """Convert letter (A-Z) to satellite orbit number (1-26). Empty string returns 0."""
    if not letter:
        return 0
    letter = letter.upper()
    if len(letter) != 1 or letter not in SATELLITE_LETTERS:
        raise ValueError("Letter must be A-Z")
    return SATELLITE_LETTERS.index(letter)


class SystemCoordinates:
    """
    Represents a location within a stellar system.

    Supports nested coordinate systems for multi-star systems where companion
    stars orbit the primary at specific orbit numbers, and bodies can orbit
    those companions.

    Structure (up to 4 nesting levels, 64 bits total):
        Level 0 (bits 48-59): Primary system - orbit (5 bits) + satellite (5 bits) + has_nested (1 bit)
        Level 1 (bits 32-47): Secondary system - orbit (5 bits) + satellite (5 bits) + has_nested (1 bit)
        Level 2 (bits 16-31): Tertiary system - orbit (5 bits) + satellite (5 bits) + has_nested (1 bit)
        Level 3 (bits 0-15):  Quaternary system - orbit (5 bits) + satellite (5 bits)
        Bits 60-63: Depth indicator (0-4)

    Examples:
        - Planet at orbit 3: depth=1, level0=(3, 0)
        - Moon 'D' of planet at orbit 5: depth=1, level0=(5, 4)
        - Planet at orbit 2 of companion star at orbit 8: depth=2, level0=(8, 0, nested), level1=(2, 0)
        - Moon 'A' of planet at orbit 1 of companion at orbit 5: depth=2, level0=(5, 0, nested), level1=(1, 1)
    """

    __slots__ = ("_packed",)

    # Each level: 5 bits orbit + 5 bits satellite + 1 bit has_nested = 11 bits
    # But we'll use 12 bits per level for alignment (padding 1 bit)
    _BITS_PER_LEVEL = 12
    _ORBIT_BITS = 5
    _SATELLITE_BITS = 5
    _NESTED_BIT = 1

    _ORBIT_MASK = 0x1F  # 5 bits
    _SATELLITE_MASK = 0x1F  # 5 bits
    _LEVEL_MASK = 0xFFF  # 12 bits

    _DEPTH_SHIFT = 60
    _DEPTH_MASK = 0xF  # 4 bits

    _MAX_ORBIT = 20
    _MAX_SATELLITE = 26
    _MAX_DEPTH = 4

    def __new__(
        cls,
        levels: tuple[tuple[int, int], ...] | None = None,
    ) -> SystemCoordinates:
        """
        Create a new SystemCoordinates from a tuple of (orbit, satellite) pairs.

        Args:
            levels: Tuple of (orbit_number, satellite_orbit) pairs, from outermost to innermost.
                   satellite_orbit of 0 means the primary body at that orbit, 1-26 for moons.
        """
        instance = object.__new__(cls)

        if levels is None:
            levels = ()

        depth = len(levels)
        if depth > cls._MAX_DEPTH:
            raise ValueError(f"Maximum nesting depth is {cls._MAX_DEPTH}")

        packed = depth << cls._DEPTH_SHIFT

        for i, (orbit, satellite) in enumerate(levels):
            if not (0 <= orbit <= cls._MAX_ORBIT):
                raise ValueError(f"Orbit at level {i} must be in range 0-{cls._MAX_ORBIT}")
            if not (0 <= satellite <= cls._MAX_SATELLITE):
                raise ValueError(f"Satellite at level {i} must be in range 0-{cls._MAX_SATELLITE}")

            # Determine if this level has a nested level below it
            has_nested = 1 if i < depth - 1 else 0

            level_value = (orbit << 6) | (satellite << 1) | has_nested
            shift = (3 - i) * cls._BITS_PER_LEVEL
            packed |= level_value << shift

        object.__setattr__(instance, "_packed", packed)
        return instance

    def __init__(
        self,
        levels: tuple[tuple[int, int], ...] | None = None,
    ) -> None:
        pass  # Immutable; all initialization in __new__

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("SystemCoordinates is immutable")

    def __hash__(self) -> int:
        return hash(self._packed)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SystemCoordinates):
            return self._packed == other._packed
        return NotImplemented

    def __repr__(self) -> str:
        levels_str = ", ".join(f"({orbit}, {sat})" for orbit, sat in self.levels)
        return f"SystemCoordinates(levels=({levels_str}))"

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_packed(cls, packed: int) -> SystemCoordinates:
        """Create a SystemCoordinates from a pre-packed 64-bit integer."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "_packed", packed)
        return instance

    @classmethod
    def planet(cls, orbit: int) -> SystemCoordinates:
        """Create coordinates for a planet at the given orbit around the primary star."""
        return cls(levels=((orbit, 0),))

    @classmethod
    def moon(cls, orbit: int, satellite: int | str) -> SystemCoordinates:
        """
        Create coordinates for a moon orbiting a planet.

        Args:
            orbit: The planet's orbit number (0-20)
            satellite: Moon designation as number (1-26) or letter ('A'-'Z')
        """
        if isinstance(satellite, str):
            satellite = letter_to_satellite(satellite)
        return cls(levels=((orbit, satellite),))

    @classmethod
    def companion_planet(cls, companion_orbit: int, planet_orbit: int) -> SystemCoordinates:
        """
        Create coordinates for a planet orbiting a companion star.

        Args:
            companion_orbit: The orbit where the companion star resides
            planet_orbit: The planet's orbit around the companion
        """
        return cls(levels=((companion_orbit, 0), (planet_orbit, 0)))

    @classmethod
    def companion_moon(
        cls, companion_orbit: int, planet_orbit: int, satellite: int | str
    ) -> SystemCoordinates:
        """
        Create coordinates for a moon orbiting a planet around a companion star.

        Args:
            companion_orbit: The orbit where the companion star resides
            planet_orbit: The planet's orbit around the companion
            satellite: Moon designation as number (1-26) or letter ('A'-'Z')
        """
        if isinstance(satellite, str):
            satellite = letter_to_satellite(satellite)
        return cls(levels=((companion_orbit, 0), (planet_orbit, satellite)))

    # -------------------------------------------------------------------------
    # Properties for extraction
    # -------------------------------------------------------------------------

    @property
    def packed(self) -> int:
        """Return the full packed 64-bit coordinate."""
        return self._packed

    @property
    def depth(self) -> int:
        """Return the nesting depth (number of levels)."""
        return (self._packed >> self._DEPTH_SHIFT) & self._DEPTH_MASK

    def _extract_level(self, level_index: int) -> tuple[int, int, bool]:
        """Extract (orbit, satellite, has_nested) from a specific level."""
        shift = (3 - level_index) * self._BITS_PER_LEVEL
        level_value = (self._packed >> shift) & self._LEVEL_MASK
        orbit = (level_value >> 6) & self._ORBIT_MASK
        satellite = (level_value >> 1) & self._SATELLITE_MASK
        has_nested = bool(level_value & 1)
        return orbit, satellite, has_nested

    @property
    def levels(self) -> tuple[tuple[int, int], ...]:
        """Return all levels as a tuple of (orbit, satellite) pairs."""
        result = []
        for i in range(self.depth):
            orbit, satellite, _ = self._extract_level(i)
            result.append((orbit, satellite))
        return tuple(result)

    @property
    def primary_orbit(self) -> int | None:
        """Return the outermost orbit number, or None if empty."""
        if self.depth == 0:
            return None
        orbit, _, _ = self._extract_level(0)
        return orbit

    @property
    def final_orbit(self) -> int | None:
        """Return the innermost orbit number, or None if empty."""
        if self.depth == 0:
            return None
        orbit, _, _ = self._extract_level(self.depth - 1)
        return orbit

    @property
    def final_satellite(self) -> int | None:
        """Return the innermost satellite designation, or None if empty."""
        if self.depth == 0:
            return None
        _, satellite, _ = self._extract_level(self.depth - 1)
        return satellite

    @property
    def is_moon(self) -> bool:
        """Return True if this coordinate refers to a moon (satellite > 0)."""
        sat = self.final_satellite
        return sat is not None and sat > 0

    @property
    def is_nested(self) -> bool:
        """Return True if this coordinate is in a nested subsystem (depth > 1)."""
        return self.depth > 1

    # -------------------------------------------------------------------------
    # Immutable "edit" methods (return new instances)
    # -------------------------------------------------------------------------

    def with_satellite(self, satellite: int | str) -> SystemCoordinates:
        """Return a new instance with the innermost satellite changed."""
        if self.depth == 0:
            raise ValueError("Cannot set satellite on empty coordinates")
        if isinstance(satellite, str):
            satellite = letter_to_satellite(satellite)

        levels = list(self.levels)
        orbit, _ = levels[-1]
        levels[-1] = (orbit, satellite)
        return SystemCoordinates(levels=tuple(levels))

    def with_nested(self, orbit: int, satellite: int = 0) -> SystemCoordinates:
        """Return a new instance with an additional nesting level."""
        if self.depth >= self._MAX_DEPTH:
            raise ValueError(f"Maximum nesting depth is {self._MAX_DEPTH}")

        # The current innermost level should have satellite=0 to add nesting
        levels = list(self.levels)
        if levels and levels[-1][1] != 0:
            raise ValueError(
                "Cannot add nesting below a satellite; " "set the parent's satellite to 0 first"
            )

        levels.append((orbit, satellite))
        return SystemCoordinates(levels=tuple(levels))

    def parent(self) -> SystemCoordinates | None:
        """Return the parent coordinate (one level up), or None if at top level."""
        if self.depth <= 1:
            return None
        return SystemCoordinates(levels=self.levels[:-1])

    # -------------------------------------------------------------------------
    # String output methods
    # -------------------------------------------------------------------------

    def to_hex_string(self) -> str:
        """Return the packed coordinate as a zero-padded hex string."""
        return f"{self._packed:016X}"

    def to_designation(self) -> str:
        """
        Return a human-readable designation string.

        Format examples:
            - "III" for orbit 3 (Roman numerals)
            - "V-c" for orbit 5, moon C
            - "[VIII] II" for orbit 2 of companion at orbit 8
            - "[V] III-a" for moon A of orbit 3 of companion at orbit 5
        """
        if self.depth == 0:
            return "(empty)"

        roman_numerals = [
            "",
            "I",
            "II",
            "III",
            "IV",
            "V",
            "VI",
            "VII",
            "VIII",
            "IX",
            "X",
            "XI",
            "XII",
            "XIII",
            "XIV",
            "XV",
            "XVI",
            "XVII",
            "XVIII",
            "XIX",
            "XX",
        ]

        parts = []
        levels = self.levels

        for i, (orbit, satellite) in enumerate(levels):
            orbit_str = roman_numerals[orbit] if orbit <= 20 else str(orbit)

            if i < len(levels) - 1:
                # This is a parent level (companion star subsystem)
                parts.append(f"[{orbit_str}]")
            else:
                # This is the final level
                if satellite > 0:
                    sat_letter = satellite_to_letter(satellite).lower()
                    parts.append(f"{orbit_str}-{sat_letter}")
                else:
                    parts.append(orbit_str)

        return " ".join(parts)

    def to_components_string(self) -> str:
        """Return a detailed breakdown of all components."""
        if self.depth == 0:
            return "Empty coordinates (no location specified)"

        lines = [f"Depth: {self.depth} level(s)"]
        for i, (orbit, satellite) in enumerate(self.levels):
            sat_str = (
                f", satellite {satellite} ({satellite_to_letter(satellite)})"
                if satellite > 0
                else ""
            )
            if i < self.depth - 1:
                lines.append(f"  Level {i}: Companion subsystem at orbit {orbit}")
            else:
                lines.append(f"  Level {i}: Orbit {orbit}{sat_str}")

        lines.append(f"Designation: {self.to_designation()}")
        return "\n".join(lines)
