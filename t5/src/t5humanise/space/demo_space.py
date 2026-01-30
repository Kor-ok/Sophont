"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.space.space_coordinates import (  # noqa: E402
    Milieu,
    SpaceCoordinates,
    TagSource,
    TagStatus,
    pack_coordinate_package,
    unpack_coordinate_package,
)


def demo_low_level_packing() -> None:
    """Demonstrate the low-level pack/unpack functions."""
    print("Low-Level Packing Functions")
    print("-" * 40)

    print("\nBit layout (64 bits total, 45 used):")
    print("  Bits 48-63: x_coord (16 bits, signed)")
    print("  Bits 32-47: y_coord (16 bits, signed)")
    print("  Bits 28-31: tag_status (4 bits)")
    print("  Bits 24-27: tag_source (4 bits)")
    print("  Bits 19-23: milieu (5 bits)")
    print("  Bits 0-18:  reserved (19 bits)")

    print("\nPacking examples:")
    test_cases = [
        (100, 200, 1, 2, 2),
        (-50, -100, 3, 1, 1),
        (32767, -32768, 15, 15, 31),
    ]
    for x, y, status, source, milieu in test_cases:
        packed = pack_coordinate_package(x, y, status, source, milieu)
        print(f"  ({x:6d}, {y:6d}, s={status}, src={source}, m={milieu}) -> 0x{packed:016X}")

    print("\nRoundtrip verification:")
    for original in test_cases:
        packed = pack_coordinate_package(*original)
        unpacked = unpack_coordinate_package(packed)
        match = "✓" if unpacked == original else "✗"
        print(f"  {original} -> {unpacked} {match}")

    print()


def demo_enums() -> None:
    """Demonstrate the metadata enumerations."""
    print("Metadata Enumerations")
    print("-" * 40)

    print("\nTagStatus values (data validity):")
    for status in TagStatus:
        if status.value <= 8:  # Show defined values
            print(f"  {status.value:2d}: {status.name}")

    print("\nTagSource values (data origin):")
    for source in TagSource:
        if source.value <= 12:  # Show defined values
            print(f"  {source.value:2d}: {source.name}")

    print("\nMilieu values (timeline/era):")
    for m in Milieu:
        if m.value <= 12:  # Show defined values
            print(f"  {m.value:2d}: {m.name}")

    print()


def demo_factory_methods() -> None:
    """Demonstrate SpaceCoordinates creation methods."""
    print("Factory Methods")
    print("-" * 40)

    # Basic creation
    print("\n1. Basic creation with defaults:")
    coord1 = SpaceCoordinates(100, 200)
    print(f"   {coord1!r}")

    # With metadata
    print("\n2. With explicit metadata:")
    coord2 = SpaceCoordinates(
        x=100,
        y=200,
        tag_status=TagStatus.CANONICAL,
        tag_source=TagSource.T5_SECOND_SURVEY,
        milieu=Milieu.GOLDEN_AGE,
    )
    print(f"   {coord2!r}")

    # Canonical shortcut
    print("\n3. Using canonical() factory:")
    coord3 = SpaceCoordinates.canonical(100, 200)
    print(f"   {coord3!r}")

    # From hex label
    print("\n4. From hex label (sector-relative):")
    coord4 = SpaceCoordinates.from_hex_label("0505")  # Column 05, Row 05
    print(f"   Hex '0505' in sector (0,0): {coord4!r}")
    print(f"   Position: {coord4.to_coordinate_string()}")

    # From hex label with sector offset
    print("\n5. From hex label with sector offset:")
    coord5 = SpaceCoordinates.from_hex_label("0101", sector_x=1, sector_y=0)
    print(f"   Hex '0101' in sector (1,0): {coord5!r}")
    print(f"   Position: {coord5.to_coordinate_string()}")

    # From packed value
    print("\n6. From packed 64-bit integer:")
    packed = coord2.packed
    coord6 = SpaceCoordinates.from_packed(packed)
    print(f"   Packed: 0x{packed:016X}")
    print(f"   {coord6!r}")
    print(f"   Equal to original? {coord2 == coord6}")

    print()


def demo_property_extraction() -> None:
    """Demonstrate extracting properties from coordinates."""
    print("Property Extraction")
    print("-" * 40)

    coord = SpaceCoordinates(
        x=-150,
        y=300,
        tag_status=TagStatus.VERIFIED,
        tag_source=TagSource.TRAVELLERMAP,
        milieu=Milieu.REBELLION,
    )

    print(f"\nCoordinate: {coord!r}")

    print("\nExtracted properties:")
    print(f"  x:              {coord.x}")
    print(f"  y:              {coord.y}")
    print(f"  coordinates:    {coord.coordinates}")
    print(f"  tag_status:     {coord.tag_status} ({coord.tag_status_name})")
    print(f"  tag_source:     {coord.tag_source} ({coord.tag_source_name})")
    print(f"  milieu:         {coord.milieu} ({coord.milieu_name})")

    print("\nPacked value:")
    print(f"  0x{coord.packed:016X}")

    print()


def demo_sector_conversion() -> None:
    """Demonstrate sector/hex conversion."""
    print("Sector/Hex Conversion")
    print("-" * 40)

    print("\nSector dimensions: 32 hexes wide × 40 hexes tall")

    examples = [
        ("0101", 0, 0),  # Top-left of origin sector
        ("3240", 0, 0),  # Bottom-right of origin sector
        ("0101", 1, 0),  # Adjacent sector
        ("1620", 0, 0),  # Middle of origin sector
    ]

    print("\nHex label to absolute coordinates:")
    for hex_label, sec_x, sec_y in examples:
        coord = SpaceCoordinates.from_hex_label(hex_label, sec_x, sec_y)
        print(
            f"  Sector ({sec_x},{sec_y}) Hex {hex_label} -> "
            f"absolute {coord.to_coordinate_string()}"
        )

    print("\nAbsolute coordinates to sector/hex:")
    test_coords = [
        SpaceCoordinates(5, 36),
        SpaceCoordinates(32, 1),
        SpaceCoordinates(33, 40),
        SpaceCoordinates(16, 21),
    ]
    for coord in test_coords:
        sec_x, sec_y, hex_label = coord.to_sector_hex()
        print(
            f"  {coord.to_coordinate_string():12s} -> " f"Sector ({sec_x},{sec_y}) Hex {hex_label}"
        )

    print()


def demo_distance_calculation() -> None:
    """Demonstrate distance calculations."""
    print("Distance Calculations")
    print("-" * 40)

    # Create some notable locations
    reference = SpaceCoordinates.canonical(0, 0)
    nearby = SpaceCoordinates.canonical(3, 4)
    distant = SpaceCoordinates.canonical(100, -50)
    negative = SpaceCoordinates.canonical(-20, -30)

    print("\nHex distances from Reference (0, 0):")
    for name, coord in [("Nearby", nearby), ("Distant", distant), ("Negative", negative)]:
        dist = reference.distance_to(coord)
        print(f"  To {name} {coord.to_coordinate_string():15s}: " f"{dist} parsecs")

    print("\nDistance between other points:")
    print(f"  Nearby to Distant:  {nearby.distance_to(distant)} parsecs")
    print(f"  Nearby to Negative: {nearby.distance_to(negative)} parsecs")

    print()


def demo_immutable_editing() -> None:
    """Demonstrate immutable 'with_*' methods."""
    print("Immutable Editing")
    print("-" * 40)

    original = SpaceCoordinates.canonical(100, 200)
    print(f"\nOriginal: {original!r}")

    # Coordinate changes
    print("\nEditing operations (each returns a new instance):")

    moved = original.with_coordinates(150, 250)
    print("  with_coordinates(150, 250):")
    print(f"    {moved!r}")

    offset_coord = original.offset(10, -20)
    print("  offset(10, -20):")
    print(f"    {offset_coord!r}")

    # Metadata changes
    new_status = original.with_tag_status(TagStatus.HISTORICAL)
    print("  with_tag_status(HISTORICAL):")
    print(f"    {new_status!r}")

    new_source = original.with_tag_source(TagSource.CUSTOM)
    print("  with_tag_source(CUSTOM):")
    print(f"    {new_source!r}")

    new_milieu = original.with_milieu(Milieu.REBELLION)
    print("  with_milieu(REBELLION):")
    print(f"    {new_milieu!r}")

    print(f"\nOriginal unchanged: {original!r}")

    # Chained edits
    print("\nChained edits:")
    chained = (
        original.offset(50, 50).with_tag_status(TagStatus.PROVISIONAL).with_milieu(Milieu.NEW_ERA)
    )
    print(f"  {chained!r}")

    print()


def demo_output_formats() -> None:
    """Demonstrate string output methods."""
    print("Output Formats")
    print("-" * 40)

    coord = SpaceCoordinates(
        x=-150,
        y=300,
        tag_status=TagStatus.CANONICAL,
        tag_source=TagSource.T5_SECOND_SURVEY,
        milieu=Milieu.GOLDEN_AGE,
    )

    print("\nrepr():")
    print(f"  {coord!r}")

    print("\nto_coordinate_string():")
    print(f"  {coord.to_coordinate_string()}")

    print("\nto_hex_string():")
    print(f"  {coord.to_hex_string()}")

    print("\nto_components_string():")
    for line in coord.to_components_string().split("\n"):
        print(f"  {line}")

    print()


def demo_hashing_and_equality() -> None:
    """Demonstrate that coordinates are hashable and comparable."""
    print("Hashing and Equality")
    print("-" * 40)

    coord1 = SpaceCoordinates.canonical(100, 200)
    coord2 = SpaceCoordinates.canonical(100, 200)
    coord3 = SpaceCoordinates.canonical(100, 201)
    coord4 = SpaceCoordinates(100, 200)  # Different metadata

    print(f"\ncoord1: {coord1.to_coordinate_string()} {coord1.tag_status_name}")
    print(f"coord2: {coord2.to_coordinate_string()} {coord2.tag_status_name}")
    print(f"coord3: {coord3.to_coordinate_string()} {coord3.tag_status_name}")
    print(f"coord4: {coord4.to_coordinate_string()} {coord4.tag_status_name}")

    print(f"\ncoord1 == coord2: {coord1 == coord2} (same position and metadata)")
    print(f"coord1 == coord3: {coord1 == coord3} (different y)")
    print(f"coord1 == coord4: {coord1 == coord4} (same position, different metadata)")
    print(f"coord1 is coord2: {coord1 is coord2}")

    print("\nUsable as dict keys:")
    locations = {
        SpaceCoordinates.canonical(0, 0): "Capital/Reference",
        SpaceCoordinates.canonical(10, -5): "Rhylanor",
        SpaceCoordinates.canonical(-15, 20): "Regina",
    }
    for coord, name in locations.items():
        print(f"  {coord.to_coordinate_string():12s} -> {name}")

    print("\nUsable in sets:")
    coord_set = {coord1, coord2, coord3}
    print(f"  Set of 3 coords (2 equal): {len(coord_set)} unique")

    print()


def demo_real_world_scenario() -> None:
    """Demonstrate a real-world usage scenario."""
    print("Real-World Scenario: Subsector Survey")
    print("-" * 40)

    print(
        """
Scenario: Creating a survey record of systems in a subsector,
tracking data provenance across different sources and eras.
"""
    )

    # Create survey data
    survey = [
        ("Capital", 0, 0, TagStatus.CANONICAL, TagSource.T5_SECOND_SURVEY, Milieu.GOLDEN_AGE),
        ("Frontier Post", 5, 8, TagStatus.VERIFIED, TagSource.TRAVELLERMAP, Milieu.GOLDEN_AGE),
        ("Lost Colony", -10, 15, TagStatus.HISTORICAL, TagSource.THIRD_IMPERIUM, Milieu.LONG_NIGHT),
        ("Disputed Zone", 12, -3, TagStatus.DISPUTED, TagSource.ZHODANI, Milieu.REBELLION),
        ("New Discovery", 20, 25, TagStatus.PROVISIONAL, TagSource.CUSTOM, Milieu.NEW_ERA),
    ]

    print("Survey Records:")
    print(f"{'Name':<15} {'Position':>12} {'Status':<12} {'Source':<16} {'Era'}")
    print("-" * 70)

    coords = []
    for name, x, y, status, source, milieu in survey:
        coord = SpaceCoordinates(x, y, status, source, milieu)
        coords.append((name, coord))
        print(
            f"{name:<15} {coord.to_coordinate_string():>12} "
            f"{coord.tag_status_name:<12} {coord.tag_source_name:<16} {coord.milieu_name}"
        )

    # Distance matrix
    print("\nDistance Matrix (parsecs):")
    names = [name for name, _ in coords]
    print(f"{'':15}", end="")
    for name in names:
        print(f"{name[:8]:>9}", end="")
    print()

    for name1, coord1 in coords:
        print(f"{name1:<15}", end="")
        for _, coord2 in coords:
            dist = coord1.distance_to(coord2)
            print(f"{dist:>9}", end="")
        print()

    print()


def main() -> None:
    """Run all demonstrations."""
    print("T5 SpaceCoordinates Demo")
    print("=" * 60)
    print()
    print("A coordinate system for Charted Space locations:")
    print("  - Signed 16-bit x/y coordinates (-32,768 to 32,767)")
    print("  - Data provenance metadata (status, source, milieu)")
    print("  - Sector/hex label conversion")
    print("  - Distance calculations")
    print()

    demo_low_level_packing()
    demo_enums()
    demo_factory_methods()
    demo_property_extraction()
    demo_sector_conversion()
    demo_distance_calculation()
    demo_immutable_editing()
    demo_output_formats()
    demo_hashing_and_equality()
    demo_real_world_scenario()

    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
