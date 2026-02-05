from __future__ import annotations


class ChartedSpace:
    """Bit packed value representing the Traveller 5 system location.

    Layout (39 bits):
        source:  2 bits  [bits 37-38]
        milieu:  5 bits  [bits 32-36]
        x_coord: 16 bits [bits 16-31] (signed, stored as unsigned)
        y_coord: 16 bits [bits 0-15]  (signed, stored as unsigned)
    """

    @staticmethod
    def pack(source: int, milieu: int, x_coord: int, y_coord: int) -> int:
        """Pack the components into a single integer value."""
        return (
            ((source & 0b11) << 37)
            | ((milieu & 0b11111) << 32)
            | ((x_coord & 0xFFFF) << 16)
            | (y_coord & 0xFFFF)
        )

    @staticmethod
    def unpack(packed: int) -> tuple[int, int, int, int]:
        """Unpack into (source, milieu, x_coord, y_coord)."""

        def to_signed_16(val: int) -> int:
            return val - 0x10000 if val & 0x8000 else val

        source = (packed >> 37) & 0b11
        milieu = (packed >> 32) & 0b11111
        x_coord = to_signed_16((packed >> 16) & 0xFFFF)
        y_coord = to_signed_16(packed & 0xFFFF)
        return (source, milieu, x_coord, y_coord)


class SystemSpace:
    """Bit packed value representing the astral body within a star system.

    Layout (11 bits):
        orbit_num:           5 bits [bits 6-10]
        has_nested:          1 bit  [bit 5]
        satellite_orbit_num: 5 bits [bits 0-4]
    """

    @staticmethod
    def pack(orbit_num: int, has_nested: int, satellite_orbit_num: int = 0) -> int:
        """Pack the components into a single integer value."""
        return (
            ((orbit_num & 0b11111) << 6)
            | ((has_nested & 0b1) << 5)
            | (satellite_orbit_num & 0b11111)
        )

    @staticmethod
    def unpack(packed: int) -> tuple[int, int, int]:
        """Unpack into (orbit_num, has_nested, satellite_orbit_num)."""
        orbit_num = (packed >> 6) & 0b11111
        has_nested = (packed >> 5) & 0b1
        satellite_orbit_num = packed & 0b11111
        return (orbit_num, has_nested, satellite_orbit_num)


class WorldSpace:
    """Bit packed value for planetary surface coordinates.

    Layout (37 bits):
        tri_in_ico:       5 bits  [bits 32-36]
        hex_in_tri:       16 bits [bits 16-31]
        hex_in_hex_terrain: 8 bits [bits 8-15]
        hex_in_hex_local:   8 bits [bits 0-7]
    """

    @staticmethod
    def pack(
        tri_in_ico: int, hex_in_tri: int, hex_in_hex_terrain: int, hex_in_hex_local: int
    ) -> int:
        """Pack the components into a single integer value."""
        return (
            ((tri_in_ico & 0b11111) << 32)
            | ((hex_in_tri & 0xFFFF) << 16)
            | ((hex_in_hex_terrain & 0xFF) << 8)
            | (hex_in_hex_local & 0xFF)
        )

    @staticmethod
    def unpack(packed: int) -> tuple[int, int, int, int]:
        """Unpack into (tri_in_ico, hex_in_tri, terrain, local)."""
        tri_in_ico = (packed >> 32) & 0b11111
        hex_in_tri = (packed >> 16) & 0xFFFF
        terrain = (packed >> 8) & 0xFF
        local = packed & 0xFF
        return (tri_in_ico, hex_in_tri, terrain, local)


class Location:
    """Immutable flyweight location packed into a single 87-bit integer.

    Bit Layout (87 bits total):
        ChartedSpace: 39 bits [bits 48-86]
        SystemSpace:  11 bits [bits 37-47]
        WorldSpace:   37 bits [bits 0-36]
    """

    __slots__ = ("_packed",)

    # Bit positions
    WORLD_SPACE_BITS = 37
    SYSTEM_SPACE_BITS = 11
    CHARTED_SPACE_BITS = 39

    SYSTEM_SPACE_SHIFT = WORLD_SPACE_BITS  # 37
    CHARTED_SPACE_SHIFT = WORLD_SPACE_BITS + SYSTEM_SPACE_BITS  # 48

    # Masks
    WORLD_SPACE_MASK = (1 << WORLD_SPACE_BITS) - 1  # 37 bits
    SYSTEM_SPACE_MASK = (1 << SYSTEM_SPACE_BITS) - 1  # 11 bits
    CHARTED_SPACE_MASK = (1 << CHARTED_SPACE_BITS) - 1  # 39 bits

    def __new__(
        cls,
        charted_space: int = 0,
        system_space: int = 0,
        world_space: int = 0,
    ) -> Location:
        """Create a new Location instance from component integers."""
        instance = object.__new__(cls)
        packed = (
            ((charted_space & cls.CHARTED_SPACE_MASK) << cls.CHARTED_SPACE_SHIFT)
            | ((system_space & cls.SYSTEM_SPACE_MASK) << cls.SYSTEM_SPACE_SHIFT)
            | (world_space & cls.WORLD_SPACE_MASK)
        )
        object.__setattr__(instance, "_packed", packed)
        return instance

    def __init__(
        self,
        charted_space: int = 0,
        system_space: int = 0,
        world_space: int = 0,
    ) -> None:
        pass  # Immutable; initialization in __new__

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError(f"{self.__class__.__name__} is immutable")

    def __hash__(self) -> int:
        return hash(self._packed)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Location):
            return self._packed == other._packed
        return NotImplemented

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(0x{self._packed:022X})"

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_packed(cls, packed: int) -> Location:
        """Create a Location instance from a single packed integer."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "_packed", packed)
        return instance

    @classmethod
    def from_components(
        cls,
        *,
        source: int = 0,
        milieu: int = 0,
        x_coord: int = 0,
        y_coord: int = 0,
        orbit_num: int = 0,
        has_nested: int = 0,
        satellite_orbit_num: int = 0,
        tri_in_ico: int = 0,
        hex_in_tri: int = 0,
        hex_in_hex_terrain: int = 0,
        hex_in_hex_local: int = 0,
    ) -> Location:
        """Create a Location instance from individual components."""
        charted_space = ChartedSpace.pack(source, milieu, x_coord, y_coord)
        system_space = SystemSpace.pack(orbit_num, has_nested, satellite_orbit_num)
        world_space = WorldSpace.pack(
            tri_in_ico, hex_in_tri, hex_in_hex_terrain, hex_in_hex_local
        )
        return cls(charted_space, system_space, world_space)

    # -------------------------------------------------------------------------
    # Properties for packed component extraction
    # -------------------------------------------------------------------------

    @property
    def packed(self) -> int:
        """Return the full packed 87-bit coordinate."""
        return self._packed

    @property
    def charted_space(self) -> int:
        """Extract the packed ChartedSpace integer (39 bits)."""
        return (self._packed >> self.CHARTED_SPACE_SHIFT) & self.CHARTED_SPACE_MASK

    @property
    def system_space(self) -> int:
        """Extract the packed SystemSpace integer (11 bits)."""
        return (self._packed >> self.SYSTEM_SPACE_SHIFT) & self.SYSTEM_SPACE_MASK

    @property
    def world_space(self) -> int:
        """Extract the packed WorldSpace integer (37 bits)."""
        return self._packed & self.WORLD_SPACE_MASK

    # -------------------------------------------------------------------------
    # Unpacked component access
    # -------------------------------------------------------------------------

    @property
    def source(self) -> int:
        """Extract source from ChartedSpace."""
        return (self.charted_space >> 37) & 0b11

    @property
    def milieu(self) -> int:
        """Extract milieu from ChartedSpace."""
        return (self.charted_space >> 32) & 0b11111

    @property
    def x_coord(self) -> int:
        """Extract x coordinate from ChartedSpace (signed)."""
        val = (self.charted_space >> 16) & 0xFFFF
        return val - 0x10000 if val & 0x8000 else val

    @property
    def y_coord(self) -> int:
        """Extract y coordinate from ChartedSpace (signed)."""
        val = self.charted_space & 0xFFFF
        return val - 0x10000 if val & 0x8000 else val

    @property
    def orbit_num(self) -> int:
        """Extract orbit number from SystemSpace."""
        return (self.system_space >> 6) & 0b11111

    @property
    def has_nested(self) -> bool:
        """Extract has_nested flag from SystemSpace."""
        return bool((self.system_space >> 5) & 0b1)

    @property
    def satellite_orbit_num(self) -> int:
        """Extract satellite orbit number from SystemSpace."""
        return self.system_space & 0b11111

    @property
    def tri_in_ico(self) -> int:
        """Extract tri_in_ico from WorldSpace."""
        return (self.world_space >> 32) & 0b11111

    @property
    def hex_in_tri(self) -> int:
        """Extract hex_in_tri from WorldSpace."""
        return (self.world_space >> 16) & 0xFFFF

    @property
    def hex_in_hex_terrain(self) -> int:
        """Extract terrain hex from WorldSpace."""
        return (self.world_space >> 8) & 0xFF

    @property
    def hex_in_hex_local(self) -> int:
        """Extract local hex from WorldSpace."""
        return self.world_space & 0xFF

    # -------------------------------------------------------------------------
    # Immutable "edit" methods
    # -------------------------------------------------------------------------

    def with_charted_space(
        self, source: int, milieu: int, x_coord: int, y_coord: int
    ) -> Location:
        """Return a new Location with updated ChartedSpace."""
        new_charted = ChartedSpace.pack(source, milieu, x_coord, y_coord)
        return Location(new_charted, self.system_space, self.world_space)

    def with_system_space(
        self, orbit_num: int, has_nested: int, satellite_orbit_num: int = 0
    ) -> Location:
        """Return a new Location with updated SystemSpace."""
        new_system = SystemSpace.pack(orbit_num, has_nested, satellite_orbit_num)
        return Location(self.charted_space, new_system, self.world_space)

    def with_world_space(
        self,
        tri_in_ico: int,
        hex_in_tri: int,
        hex_in_hex_terrain: int,
        hex_in_hex_local: int,
    ) -> Location:
        """Return a new Location with updated WorldSpace."""
        new_world = WorldSpace.pack(
            tri_in_ico, hex_in_tri, hex_in_hex_terrain, hex_in_hex_local
        )
        return Location(self.charted_space, self.system_space, new_world)

    # -------------------------------------------------------------------------
    # String output methods
    # -------------------------------------------------------------------------

    def to_hex_string(self) -> str:
        """Return the packed integer as a 22-character hex string."""
        return f"0x{self._packed:022X}"

    def to_components_string(self) -> str:
        """Return a human-readable breakdown of all components."""
        return (
            f"ChartedSpace: source={self.source}, milieu={self.milieu}, "
            f"x={self.x_coord}, y={self.y_coord}\n"
            f"SystemSpace: orbit={self.orbit_num}, nested={self.has_nested}, "
            f"sat_orbit={self.satellite_orbit_num}\n"
            f"WorldSpace: tri=0x{self.tri_in_ico:02X}, hex=0x{self.hex_in_tri:04X}, "
            f"terrain=0x{self.hex_in_hex_terrain:02X}, local=0x{self.hex_in_hex_local:02X}"
        )