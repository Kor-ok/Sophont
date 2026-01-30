from __future__ import annotations

from enum import IntEnum


class TagStatus(IntEnum):
    """Status of location data validity/currency."""

    UNKNOWN = 0
    CANONICAL = 1  # Official T5 data
    VERIFIED = 2  # Cross-referenced and confirmed
    PROVISIONAL = 3  # Pending verification
    HISTORICAL = 4  # Data from previous milieu
    DISPUTED = 5  # Conflicting sources
    THEORETICAL = 6  # Predicted but unconfirmed
    RESTRICTED = 7  # Classified/limited access
    DEPRECATED = 8  # Superseded data
    # 9-15 reserved for future use


class TagSource(IntEnum):
    """Source of the coordinate data."""

    UNKNOWN = 0
    T5_SECOND_SURVEY = 1  # Official Second Survey
    TRAVELLERMAP = 2  # TravellerMap.com
    THIRD_IMPERIUM = 3  # Third Imperium sources
    ZHODANI = 4  # Zhodani Consulate sources
    ASLAN = 5  # Aslan Hierate sources
    VARGR = 6  # Vargr Extents sources
    SOLOMANI = 7  # Solomani Confederation sources
    HIVER = 8  # Hive Federation sources
    KKREE = 9  # K'kree sources
    DROYNE = 10  # Droyne sources
    CUSTOM = 11  # User-defined
    GENERATED = 12  # Procedurally generated
    # 13-15 reserved for future use


class Milieu(IntEnum):
    """Game timeline/era identifier."""

    UNKNOWN = 0
    MILIEU_0 = 1  # Year 0 (founding of Third Imperium)
    GOLDEN_AGE = 2  # circa 1000
    REBELLION = 3  # 1116+
    HARD_TIMES = 4  # 1120s
    VIRUS = 5  # 1130s
    NEW_ERA = 6  # 1200+
    MILIEU_1248 = 7  # TNE: 1248
    MILIEU_1900 = 8  # Far future
    LONG_NIGHT = 9  # -1776 to 0
    RULE_OF_MAN = 10  # -2204 to -1776
    FIRST_IMPERIUM = 11  # Ziru Sirka era
    INTERSTELLAR_WARS = 12  # -2408 to -2219
    # 13-31 reserved for future use/custom milieus


def pack_coordinate_package(
    x_coord: int, y_coord: int, tag_status: int, tag_source: int, milieu: int
) -> int:
    """Pack the Charted Space coordinate data into a single integer.

    Args:
        x_coord (int): -32,768 to 32,767 = 16 bits
        y_coord (int): -32,768 to 32,767 = 16 bits
        tag_status (int): 0 to 15 = 4 bits
        tag_source (int): 0 to 15 = 4 bits
        milieu (int): 0 to 31 = 5 bits
    """
    if not (-32768 <= x_coord <= 32767):
        raise ValueError("x_coord must be between -32,768 and 32,767")
    if not (-32768 <= y_coord <= 32767):
        raise ValueError("y_coord must be between -32,768 and 32,767")
    if not (0 <= tag_status <= 15):
        raise ValueError("tag_status must be between 0 and 15")
    if not (0 <= tag_source <= 15):
        raise ValueError("tag_source must be between 0 and 15")
    if not (0 <= milieu <= 31):
        raise ValueError("milieu must be between 0 and 31")

    packed = (
        ((x_coord & 0xFFFF) << 48)
        | ((y_coord & 0xFFFF) << 32)
        | ((tag_status & 0x0F) << 28)
        | ((tag_source & 0x0F) << 24)
        | ((milieu & 0x1F) << 19)
    )
    return packed


def unpack_coordinate_package(packed: int) -> tuple[int, int, int, int, int]:
    """Unpack the Charted Space coordinate data from a single integer.

    Args:
        packed (int): The packed coordinate integer.
    """
    x_coord = (packed >> 48) & 0xFFFF
    if x_coord >= 0x8000:
        x_coord -= 0x10000  # Convert to signed

    y_coord = (packed >> 32) & 0xFFFF
    if y_coord >= 0x8000:
        y_coord -= 0x10000  # Convert to signed

    tag_status = (packed >> 28) & 0x0F
    tag_source = (packed >> 24) & 0x0F
    milieu = (packed >> 19) & 0x1F

    return x_coord, y_coord, tag_status, tag_source, milieu


class SpaceCoordinates:
    """
    Represents a location in Charted Space using hex coordinates.

    The coordinate system uses (x, y) positions where:
        - x increases to spinward-trailing (right on standard maps)
        - y increases to coreward (up on standard maps)
        - (0, 0) is typically Reference/Capital or a sector origin

    Additional metadata tracks the data provenance:
        - tag_status: validity/currency of the data
        - tag_source: origin of the coordinate data
        - milieu: game timeline/era

    Bit layout (64 bits total, 45 used):
        Bits 48-63: x_coord (16 bits, signed)
        Bits 32-47: y_coord (16 bits, signed)
        Bits 28-31: tag_status (4 bits)
        Bits 24-27: tag_source (4 bits)
        Bits 19-23: milieu (5 bits)
        Bits 0-18:  reserved (19 bits)
    """

    __slots__ = ("_packed",)

    # Bit positions and masks
    _X_SHIFT = 48
    _Y_SHIFT = 32
    _STATUS_SHIFT = 28
    _SOURCE_SHIFT = 24
    _MILIEU_SHIFT = 19

    _COORD_MASK = 0xFFFF  # 16 bits
    _STATUS_MASK = 0x0F  # 4 bits
    _SOURCE_MASK = 0x0F  # 4 bits
    _MILIEU_MASK = 0x1F  # 5 bits

    def __new__(
        cls,
        x: int = 0,
        y: int = 0,
        tag_status: int | TagStatus = TagStatus.UNKNOWN,
        tag_source: int | TagSource = TagSource.UNKNOWN,
        milieu: int | Milieu = Milieu.UNKNOWN,
    ) -> SpaceCoordinates:
        """Create a new SpaceCoordinates instance."""
        instance = object.__new__(cls)
        packed = pack_coordinate_package(x, y, int(tag_status), int(tag_source), int(milieu))
        object.__setattr__(instance, "_packed", packed)
        return instance

    def __init__(
        self,
        x: int = 0,
        y: int = 0,
        tag_status: int | TagStatus = TagStatus.UNKNOWN,
        tag_source: int | TagSource = TagSource.UNKNOWN,
        milieu: int | Milieu = Milieu.UNKNOWN,
    ) -> None:
        pass  # Immutable; all initialization in __new__

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("SpaceCoordinates is immutable")

    def __hash__(self) -> int:
        return hash(self._packed)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SpaceCoordinates):
            return self._packed == other._packed
        return NotImplemented

    def __repr__(self) -> str:
        return (
            f"SpaceCoordinates(x={self.x}, y={self.y}, "
            f"tag_status={self.tag_status_name}, "
            f"tag_source={self.tag_source_name}, "
            f"milieu={self.milieu_name})"
        )

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_packed(cls, packed: int) -> SpaceCoordinates:
        """Create a SpaceCoordinates from a pre-packed 64-bit integer."""
        instance = object.__new__(cls)
        object.__setattr__(instance, "_packed", packed)
        return instance

    @classmethod
    def from_hex_label(
        cls, hex_label: str, sector_x: int = 0, sector_y: int = 0
    ) -> SpaceCoordinates:
        """
        Create coordinates from a 4-digit hex label within a sector.

        Args:
            hex_label: 4-digit hex label like "0101" (column 01, row 01)
            sector_x: Sector x offset (each sector is 32 hexes wide)
            sector_y: Sector y offset (each sector is 40 hexes tall)

        Returns:
            SpaceCoordinates for the absolute position
        """
        if len(hex_label) != 4 or not hex_label.isdigit():
            raise ValueError("hex_label must be a 4-digit string like '0101'")

        col = int(hex_label[:2])  # 01-32
        row = int(hex_label[2:])  # 01-40

        if not (1 <= col <= 32):
            raise ValueError("Column must be 01-32")
        if not (1 <= row <= 40):
            raise ValueError("Row must be 01-40")

        # Convert to absolute coordinates
        # Column 01 of sector 0 = x position 1, etc.
        x = sector_x * 32 + col
        # Row 01 is at the top (higher y), row 40 at bottom
        y = sector_y * 40 + (41 - row)

        return cls(x, y)

    @classmethod
    def canonical(
        cls, x: int, y: int, milieu: int | Milieu = Milieu.GOLDEN_AGE
    ) -> SpaceCoordinates:
        """Create coordinates marked as canonical T5 data."""
        return cls(
            x,
            y,
            tag_status=TagStatus.CANONICAL,
            tag_source=TagSource.T5_SECOND_SURVEY,
            milieu=milieu,
        )

    # -------------------------------------------------------------------------
    # Properties for extraction
    # -------------------------------------------------------------------------

    @property
    def packed(self) -> int:
        """Return the full packed 64-bit coordinate."""
        return self._packed

    @property
    def x(self) -> int:
        """Return the x coordinate (spinward-trailing axis)."""
        raw = (self._packed >> self._X_SHIFT) & self._COORD_MASK
        if raw >= 0x8000:
            raw -= 0x10000
        return raw

    @property
    def y(self) -> int:
        """Return the y coordinate (rimward-coreward axis)."""
        raw = (self._packed >> self._Y_SHIFT) & self._COORD_MASK
        if raw >= 0x8000:
            raw -= 0x10000
        return raw

    @property
    def tag_status(self) -> int:
        """Return the tag status value."""
        return (self._packed >> self._STATUS_SHIFT) & self._STATUS_MASK

    @property
    def tag_status_name(self) -> str:
        """Return the tag status as a name string."""
        try:
            return TagStatus(self.tag_status).name
        except ValueError:
            return f"UNKNOWN({self.tag_status})"

    @property
    def tag_source(self) -> int:
        """Return the tag source value."""
        return (self._packed >> self._SOURCE_SHIFT) & self._SOURCE_MASK

    @property
    def tag_source_name(self) -> str:
        """Return the tag source as a name string."""
        try:
            return TagSource(self.tag_source).name
        except ValueError:
            return f"UNKNOWN({self.tag_source})"

    @property
    def milieu(self) -> int:
        """Return the milieu value."""
        return (self._packed >> self._MILIEU_SHIFT) & self._MILIEU_MASK

    @property
    def milieu_name(self) -> str:
        """Return the milieu as a name string."""
        try:
            return Milieu(self.milieu).name
        except ValueError:
            return f"UNKNOWN({self.milieu})"

    @property
    def coordinates(self) -> tuple[int, int]:
        """Return (x, y) coordinate tuple."""
        return (self.x, self.y)

    # -------------------------------------------------------------------------
    # Sector/hex conversion
    # -------------------------------------------------------------------------

    def to_sector_hex(
        self, sector_origin_x: int = 0, sector_origin_y: int = 0
    ) -> tuple[int, int, str]:
        """
        Convert absolute coordinates to sector-relative hex label.

        Args:
            sector_origin_x: X offset of sector origin (in sector units)
            sector_origin_y: Y offset of sector origin (in sector units)

        Returns:
            Tuple of (sector_x, sector_y, hex_label)
        """
        # Determine which sector this hex is in
        # Each sector is 32 hexes wide, 40 hexes tall
        adjusted_x = self.x - sector_origin_x * 32
        adjusted_y = self.y - sector_origin_y * 40

        sector_x = (adjusted_x - 1) // 32
        sector_y = (adjusted_y - 1) // 40

        # Get position within sector
        col = ((adjusted_x - 1) % 32) + 1
        row = 41 - (((adjusted_y - 1) % 40) + 1)

        hex_label = f"{col:02d}{row:02d}"
        return sector_x, sector_y, hex_label

    # -------------------------------------------------------------------------
    # Distance calculations
    # -------------------------------------------------------------------------

    def distance_to(self, other: SpaceCoordinates) -> int:
        """
        Calculate hex distance to another coordinate.

        Uses standard hex grid distance calculation for offset coordinates.
        """
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        # For hex grids, this approximation works for offset coordinates
        return max(dx, dy, (dx + dy + 1) // 2)

    def parsecs_to(self, other: SpaceCoordinates) -> int:
        """
        Alias for distance_to; in Traveller, 1 hex = 1 parsec.
        """
        return self.distance_to(other)

    # -------------------------------------------------------------------------
    # Immutable "edit" methods (return new instances)
    # -------------------------------------------------------------------------

    def with_coordinates(self, x: int, y: int) -> SpaceCoordinates:
        """Return a new instance with updated coordinates."""
        return SpaceCoordinates(x, y, self.tag_status, self.tag_source, self.milieu)

    def with_tag_status(self, tag_status: int | TagStatus) -> SpaceCoordinates:
        """Return a new instance with updated tag status."""
        return SpaceCoordinates(self.x, self.y, int(tag_status), self.tag_source, self.milieu)

    def with_tag_source(self, tag_source: int | TagSource) -> SpaceCoordinates:
        """Return a new instance with updated tag source."""
        return SpaceCoordinates(self.x, self.y, self.tag_status, int(tag_source), self.milieu)

    def with_milieu(self, milieu: int | Milieu) -> SpaceCoordinates:
        """Return a new instance with updated milieu."""
        return SpaceCoordinates(self.x, self.y, self.tag_status, self.tag_source, int(milieu))

    def offset(self, dx: int, dy: int) -> SpaceCoordinates:
        """Return a new instance offset by (dx, dy)."""
        return self.with_coordinates(self.x + dx, self.y + dy)

    # -------------------------------------------------------------------------
    # String output methods
    # -------------------------------------------------------------------------

    def to_hex_string(self) -> str:
        """Return the packed coordinate as a zero-padded hex string."""
        return f"{self._packed:016X}"

    def to_coordinate_string(self) -> str:
        """Return coordinates as a simple (x, y) string."""
        return f"({self.x}, {self.y})"

    def to_components_string(self) -> str:
        """Return a detailed breakdown of all components."""
        return (
            f"Position: ({self.x}, {self.y})\n"
            f"Tag Status: {self.tag_status_name} ({self.tag_status})\n"
            f"Tag Source: {self.tag_source_name} ({self.tag_source})\n"
            f"Milieu: {self.milieu_name} ({self.milieu})"
        )
