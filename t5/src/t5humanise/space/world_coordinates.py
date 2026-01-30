from __future__ import annotations


def TriInIco(y: int, x: int) -> int:
    """
    Pack icosahedral face coordinates into a single int (5 bits used).

    Args:
        y: Row index (0-3)
        x: Column index (0-4)

    Returns:
        Packed int with y in bits 4-3, x in bits 2-0.
    """
    if not (0 <= y <= 3):
        raise ValueError("y must be in range 0-3")
    if not (0 <= x <= 4):
        raise ValueError("x must be in range 0-4")
    return (y << 3) | x


def TriInIco_y(packed: int) -> int:
    """Extract y coordinate from packed Ico."""
    return packed >> 3


def TriInIco_x(packed: int) -> int:
    """Extract x coordinate from packed Ico."""
    return packed & 0b111


def HexInTri(vertex: int, dex: int, lev: int) -> int:
    """
    For an arbitrary number of hexagons between 1 and 210 fit within an icosahedral face,
    the coordinate system picks a vertex (0-2) and dex (clockwise edge axis, x),
    lev (anticlockwise edge axis, y) offsets from that vertex
    by the number of hexagons along each axis where 0, 0 is the partial pentagon at
    that vertex.

    We will use clockwise winding for the vertices
    """

    if not (0 <= vertex <= 2):
        raise ValueError("vertex must be in range 0-2")
    if not (0 <= dex <= 70):
        raise ValueError("dex must be in range 0-70")
    if not (0 <= lev <= 70):
        raise ValueError("lev must be in range 0-70")
    return (vertex << 14) | (lev << 7) | dex


def HexInHex(axis_1: tuple[int, int], axis_2: tuple[int, int]) -> int:
    """
    There are 91 component hexagons fit within a master hexagon.
    The identification of a component hexagon is by one of two axes,
    each with a y (-5 to +5) and x (-5 to +5) coordinate.
    The two axes are at 60 degrees to each other.
    Each axis coordinate is stored as a 4-bit signed integer (two's complement)

    Args:
        axis_1: Tuple of (y, x) for axis 1
        axis_2: Tuple of (y, x) for axis 2

    Returns:
        Packed int
    """
    # TODO: Validate so that either axis_1 or axis_2 is used,
    # or the second value of axis_1 with the first value of axis_2
    # This will cover the whole face.
    y1, x1 = axis_1
    y2, x2 = axis_2

    for coord, name in [(y1, "axis_1 y"), (x1, "axis_1 x"), (y2, "axis_2 y"), (x2, "axis_2 x")]:
        if not (-5 <= coord <= 5):
            raise ValueError(f"{name} must be in range -5 to +5")

    def to_signed_4bit(value: int) -> int:
        """Convert an integer to a 4-bit signed representation."""
        if value < 0:
            value = (1 << 4) + value  # Two's complement for negative values
        return value & 0b1111  # Ensure it's 4 bits

    packed = (
        (to_signed_4bit(y1) << 12)
        | (to_signed_4bit(x1) << 8)
        | (to_signed_4bit(y2) << 4)
        | to_signed_4bit(x2)
    )
    return packed


class WorldCoordinates:
    """A full coordinate is comprised of:

    TriInIco (World Triangle)       - 5 bits  (bits 48-52)
        HexInTri (World Hex)        - 16 bits (bits 32-47)
            HexInHex (Terrain Hex)  - 16 bits (bits 16-31)
                HexInHex (Local Hex)- 16 bits (bits 0-15)

    Total: 53 bits packed into a 64-bit integer.
    """

    __slots__ = ("_packed",)

    # Bit positions and masks
    _TRI_IN_ICO_SHIFT = 48
    _TRI_IN_ICO_MASK = 0b11111  # 5 bits

    _HEX_IN_TRI_SHIFT = 32
    _HEX_IN_TRI_MASK = 0xFFFF  # 16 bits

    _TERRAIN_HEX_SHIFT = 16
    _TERRAIN_HEX_MASK = 0xFFFF  # 16 bits

    _LOCAL_HEX_SHIFT = 0
    _LOCAL_HEX_MASK = 0xFFFF  # 16 bits

    def __new__(
        cls,
        tri_in_ico: int = 0,
        hex_in_tri: int = 0,
        terrain_hex: int = 0,
        local_hex: int = 0,
    ) -> WorldCoordinates:
        """Create a new TravellerMappingSystem from component parts."""
        instance = object.__new__(cls)
        packed = (
            ((tri_in_ico & cls._TRI_IN_ICO_MASK) << cls._TRI_IN_ICO_SHIFT)
            | ((hex_in_tri & cls._HEX_IN_TRI_MASK) << cls._HEX_IN_TRI_SHIFT)
            | ((terrain_hex & cls._TERRAIN_HEX_MASK) << cls._TERRAIN_HEX_SHIFT)
            | ((local_hex & cls._LOCAL_HEX_MASK) << cls._LOCAL_HEX_SHIFT)
        )
        object.__setattr__(instance, "_packed", packed)
        return instance

    def __init__(
        self,
        tri_in_ico: int = 0,
        hex_in_tri: int = 0,
        terrain_hex: int = 0,
        local_hex: int = 0,
    ) -> None:
        pass  # Immutable; all initialization in __new__

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("TravellerMappingSystem is immutable")

    def __hash__(self) -> int:
        return hash(self._packed)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, WorldCoordinates):
            return self._packed == other._packed
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"WorldCoordinates("
            f"tri_in_ico=0x{self.tri_in_ico:02X}, "
            f"hex_in_tri=0x{self.hex_in_tri:04X}, "
            f"terrain_hex=0x{self.terrain_hex:04X}, "
            f"local_hex=0x{self.local_hex:04X})"
        )

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_packed(cls, packed: int) -> WorldCoordinates:
        """Create a TravellerMappingSystem from a pre-packed 64-bit integer."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "_packed", packed)
        return instance

    @classmethod
    def from_coordinates(
        cls,
        *,
        # TriInIco components
        ico_y: int = 0,
        ico_x: int = 0,
        # HexInTri components
        vertex: int = 0,
        dex: int = 0,
        lev: int = 0,
        # Terrain HexInHex components
        terrain_axis_1: tuple[int, int] = (0, 0),
        terrain_axis_2: tuple[int, int] = (0, 0),
        # Local HexInHex components
        local_axis_1: tuple[int, int] = (0, 0),
        local_axis_2: tuple[int, int] = (0, 0),
    ) -> WorldCoordinates:
        """Create a TravellerMappingSystem from individual coordinate components."""
        tri_in_ico = TriInIco(ico_y, ico_x)
        hex_in_tri = HexInTri(vertex, dex, lev)
        terrain_hex = HexInHex(terrain_axis_1, terrain_axis_2)
        local_hex = HexInHex(local_axis_1, local_axis_2)
        return cls(tri_in_ico, hex_in_tri, terrain_hex, local_hex)

    # -------------------------------------------------------------------------
    # Properties for packed component extraction
    # -------------------------------------------------------------------------

    @property
    def packed(self) -> int:
        """Return the full packed 64-bit coordinate."""
        return self._packed

    @property
    def tri_in_ico(self) -> int:
        """Return the packed TriInIco (World Triangle) component."""
        return (self._packed >> self._TRI_IN_ICO_SHIFT) & self._TRI_IN_ICO_MASK

    @property
    def hex_in_tri(self) -> int:
        """Return the packed HexInTri (World Hex) component."""
        return (self._packed >> self._HEX_IN_TRI_SHIFT) & self._HEX_IN_TRI_MASK

    @property
    def terrain_hex(self) -> int:
        """Return the packed HexInHex (Terrain Hex) component."""
        return (self._packed >> self._TERRAIN_HEX_SHIFT) & self._TERRAIN_HEX_MASK

    @property
    def local_hex(self) -> int:
        """Return the packed HexInHex (Local Hex) component."""
        return (self._packed >> self._LOCAL_HEX_SHIFT) & self._LOCAL_HEX_MASK

    # -------------------------------------------------------------------------
    # Unpacked coordinate extraction
    # -------------------------------------------------------------------------

    @property
    def ico_y(self) -> int:
        """Extract y coordinate from TriInIco component."""
        return TriInIco_y(self.tri_in_ico)

    @property
    def ico_x(self) -> int:
        """Extract x coordinate from TriInIco component."""
        return TriInIco_x(self.tri_in_ico)

    @property
    def vertex(self) -> int:
        """Extract vertex from HexInTri component."""
        return (self.hex_in_tri >> 14) & 0b11

    @property
    def dex(self) -> int:
        """Extract dex (clockwise edge offset) from HexInTri component."""
        return self.hex_in_tri & 0x7F

    @property
    def lev(self) -> int:
        """Extract lev (anticlockwise edge offset) from HexInTri component."""
        return (self.hex_in_tri >> 7) & 0x7F

    def _unpack_hex_in_hex(self, packed: int) -> tuple[tuple[int, int], tuple[int, int]]:
        """Unpack a HexInHex value into two axis tuples."""

        def from_signed_4bit(value: int) -> int:
            """Convert 4-bit two's complement to signed int."""
            if value & 0b1000:  # Negative (bit 3 set)
                return value - 16
            return value

        y1 = from_signed_4bit((packed >> 12) & 0xF)
        x1 = from_signed_4bit((packed >> 8) & 0xF)
        y2 = from_signed_4bit((packed >> 4) & 0xF)
        x2 = from_signed_4bit(packed & 0xF)
        return ((y1, x1), (y2, x2))

    @property
    def terrain_axes(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Extract terrain hex axes as ((y1, x1), (y2, x2))."""
        return self._unpack_hex_in_hex(self.terrain_hex)

    @property
    def local_axes(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Extract local hex axes as ((y1, x1), (y2, x2))."""
        return self._unpack_hex_in_hex(self.local_hex)

    # -------------------------------------------------------------------------
    # Immutable "edit" methods (return new instances)
    # -------------------------------------------------------------------------

    def with_tri_in_ico(self, ico_y: int, ico_x: int) -> WorldCoordinates:
        """Return a new instance with updated TriInIco component."""
        new_tri = TriInIco(ico_y, ico_x)
        return WorldCoordinates(new_tri, self.hex_in_tri, self.terrain_hex, self.local_hex)

    def with_hex_in_tri(self, vertex: int, dex: int, lev: int) -> WorldCoordinates:
        """Return a new instance with updated HexInTri component."""
        new_hex = HexInTri(vertex, dex, lev)
        return WorldCoordinates(self.tri_in_ico, new_hex, self.terrain_hex, self.local_hex)

    def with_terrain_hex(
        self, axis_1: tuple[int, int], axis_2: tuple[int, int]
    ) -> WorldCoordinates:
        """Return a new instance with updated terrain HexInHex component."""
        new_terrain = HexInHex(axis_1, axis_2)
        return WorldCoordinates(self.tri_in_ico, self.hex_in_tri, new_terrain, self.local_hex)

    def with_local_hex(
        self, axis_1: tuple[int, int], axis_2: tuple[int, int]
    ) -> WorldCoordinates:
        """Return a new instance with updated local HexInHex component."""
        new_local = HexInHex(axis_1, axis_2)
        return WorldCoordinates(self.tri_in_ico, self.hex_in_tri, self.terrain_hex, new_local)

    # -------------------------------------------------------------------------
    # String output methods
    # -------------------------------------------------------------------------

    def to_hex_string(self) -> str:
        """Return the packed coordinate as a zero-padded hex string (14 hex digits)."""
        return f"{self._packed:014X}"

    def to_components_string(self) -> str:
        """Return a human-readable breakdown of all components."""
        t_ax1, t_ax2 = self.terrain_axes
        l_ax1, l_ax2 = self.local_axes
        return (
            f"TriInIco: (y={self.ico_y}, x={self.ico_x})\n"
            f"HexInTri: (vertex={self.vertex}, dex={self.dex}, lev={self.lev})\n"
            f"TerrainHex: axis1={t_ax1}, axis2={t_ax2}\n"
            f"LocalHex: axis1={l_ax1}, axis2={l_ax2}"
        )
