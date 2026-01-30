"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.space.world_coordinates import (  # noqa: E402
    HexInHex,
    HexInTri,
    TriInIco,
    WorldCoordinates,
)


def demo_low_level_packing() -> None:
    """Demonstrate the low-level packing functions."""
    print("Low-Level Packing Functions")
    print("-" * 40)

    # TriInIco: Pack icosahedral face coordinates
    print("\nTriInIco (World Triangle - 5 bits):")
    print("  Packs row (0-3) and column (0-4) into 5 bits")
    for y, x in [(0, 0), (2, 3), (3, 4)]:
        packed = TriInIco(y, x)
        print(f"  ({y}, {x}) -> 0b{packed:05b} (0x{packed:02X})")

    # HexInTri: Pack hex-in-triangle coordinates
    print("\nHexInTri (World Hex - 16 bits):")
    print("  Packs vertex (0-2), dex (0-70), lev (0-70)")
    for vertex, dex, lev in [(0, 0, 0), (1, 15, 20), (2, 70, 70)]:
        packed = HexInTri(vertex, dex, lev)
        print(f"  (v={vertex}, d={dex}, l={lev}) -> 0x{packed:04X}")

    # HexInHex: Pack hex-in-hex coordinates
    print("\nHexInHex (Terrain/Local Hex - 16 bits):")
    print("  Packs two axes, each with (y, x) in range -5 to +5")
    for ax1, ax2 in [((0, 0), (0, 0)), ((2, -3), (0, 1)), ((-5, 5), (-5, 5))]:
        packed = HexInHex(ax1, ax2)
        print(f"  axis1={ax1}, axis2={ax2} -> 0x{packed:04X}")

    print()


def demo_coordinate_creation() -> None:
    """Demonstrate TravellerMappingSystem creation methods."""
    print("TravellerMappingSystem Creation")
    print("-" * 40)

    # Method 1: From pre-packed component values
    print("\n1. From pre-packed components:")
    coord1 = WorldCoordinates(
        tri_in_ico=TriInIco(2, 3),
        hex_in_tri=HexInTri(1, 15, 20),
        terrain_hex=HexInHex((2, -3), (0, 1)),
        local_hex=HexInHex((-1, 4), (5, -5)),
    )
    print(f"   {coord1!r}")

    # Method 2: From individual coordinate values
    print("\n2. From individual coordinates (keyword-only):")
    coord2 = WorldCoordinates.from_coordinates(
        ico_y=2,
        ico_x=3,
        vertex=1,
        dex=15,
        lev=20,
        terrain_axis_1=(2, -3),
        terrain_axis_2=(0, 1),
        local_axis_1=(-1, 4),
        local_axis_2=(5, -5),
    )
    print(f"   {coord2!r}")
    print(f"   Equal to coord1? {coord1 == coord2}")

    # Method 3: From a packed integer
    print("\n3. From packed 64-bit integer:")
    packed_value = coord1.packed
    coord3 = WorldCoordinates.from_packed(packed_value)
    print(f"   Packed value: 0x{packed_value:014X}")
    print(f"   {coord3!r}")
    print(f"   Equal to coord1? {coord1 == coord3}")

    print()


def demo_component_extraction() -> None:
    """Demonstrate extracting components from a TravellerMappingSystem."""
    print("Component Extraction")
    print("-" * 40)

    coord = WorldCoordinates.from_coordinates(
        ico_y=2,
        ico_x=3,
        vertex=1,
        dex=15,
        lev=20,
        terrain_axis_1=(2, -3),
        terrain_axis_2=(0, 1),
        local_axis_1=(-1, 4),
        local_axis_2=(5, -5),
    )

    print("\nPacked component values:")
    print(f"  tri_in_ico:   0x{coord.tri_in_ico:02X}")
    print(f"  hex_in_tri:   0x{coord.hex_in_tri:04X}")
    print(f"  terrain_hex:  0x{coord.terrain_hex:04X}")
    print(f"  local_hex:    0x{coord.local_hex:04X}")

    print("\nUnpacked individual values:")
    print(f"  TriInIco:  ico_y={coord.ico_y}, ico_x={coord.ico_x}")
    print(f"  HexInTri:  vertex={coord.vertex}, dex={coord.dex}, lev={coord.lev}")
    print(f"  Terrain:   axes={coord.terrain_axes}")
    print(f"  Local:     axes={coord.local_axes}")

    print()


def demo_immutable_editing() -> None:
    """Demonstrate immutable 'with_*' methods for editing."""
    print("Immutable Editing (with_* methods)")
    print("-" * 40)

    original = WorldCoordinates.from_coordinates(ico_y=1, ico_x=2, vertex=0, dex=10, lev=10)
    print(f"\nOriginal: {original!r}")

    # Each with_* method returns a NEW instance
    print("\nEditing operations (each returns a new instance):")

    new1 = original.with_tri_in_ico(3, 4)
    print(f"  with_tri_in_ico(3, 4):  ico_y={new1.ico_y}, ico_x={new1.ico_x}")
    print(f"    Original unchanged?   ico_y={original.ico_y}, ico_x={original.ico_x}")

    new2 = original.with_hex_in_tri(2, 50, 60)
    print(f"  with_hex_in_tri(2, 50, 60): vertex={new2.vertex}, dex={new2.dex}, lev={new2.lev}")

    new3 = original.with_terrain_hex((1, 2), (3, 4))
    print(f"  with_terrain_hex((1,2), (3,4)): {new3.terrain_axes}")

    new4 = original.with_local_hex((-2, -3), (4, 5))
    print(f"  with_local_hex((-2,-3), (4,5)): {new4.local_axes}")

    # Chaining edits
    print("\nChained edits:")
    chained = (
        original.with_tri_in_ico(3, 4)
        .with_hex_in_tri(2, 30, 40)
        .with_terrain_hex((1, 1), (2, 2))
        .with_local_hex((3, 3), (4, 4))
    )
    print(f"  {chained!r}")

    print()


def demo_output_formats() -> None:
    """Demonstrate string output methods."""
    print("Output Formats")
    print("-" * 40)

    coord = WorldCoordinates.from_coordinates(
        ico_y=2,
        ico_x=3,
        vertex=1,
        dex=15,
        lev=20,
        terrain_axis_1=(2, -3),
        terrain_axis_2=(0, 1),
        local_axis_1=(-1, 4),
        local_axis_2=(5, -5),
    )

    print("\nrepr():")
    print(f"  {coord!r}")

    print("\nto_hex_string() (14 hex digits):")
    print(f"  {coord.to_hex_string()}")

    print("\nto_components_string():")
    for line in coord.to_components_string().split("\n"):
        print(f"  {line}")

    print()


def demo_hashing_and_equality() -> None:
    """Demonstrate that coordinates are hashable and comparable."""
    print("Hashing and Equality")
    print("-" * 40)

    coord1 = WorldCoordinates.from_coordinates(ico_y=1, ico_x=2)
    coord2 = WorldCoordinates.from_coordinates(ico_y=1, ico_x=2)
    coord3 = WorldCoordinates.from_coordinates(ico_y=1, ico_x=3)

    print(f"\ncoord1 == coord2: {coord1 == coord2}")
    print(f"coord1 == coord3: {coord1 == coord3}")
    print(f"coord1 is coord2: {coord1 is coord2}")

    print("\nUsable as dict keys:")
    coord_dict = {coord1: "Location A", coord3: "Location B"}
    print(f"  coord_dict[coord1] = {coord_dict[coord1]!r}")
    print(f"  coord_dict[coord2] = {coord_dict[coord2]!r}  (same as coord1)")

    print("\nUsable in sets:")
    coord_set = {coord1, coord2, coord3}
    print(f"  Set of 3 coords (2 equal): {len(coord_set)} unique")

    print()


def demo_immutability() -> None:
    """Demonstrate that TravellerMappingSystem is immutable."""
    print("Immutability")
    print("-" * 40)

    coord = WorldCoordinates.from_coordinates(ico_y=1, ico_x=2)

    print("\nAttempting to modify _packed attribute:")
    try:
        coord._packed = 0  # type: ignore[misc]
    except AttributeError as e:
        print(f"  Caught: {e}")

    print()


def main() -> None:
    """Run all demonstrations."""
    print("T5 TravellerMappingSystem Demo")
    print("=" * 60)
    print()
    print("A hierarchical coordinate system for planetary locations:")
    print("  TriInIco    -> World Triangle (icosahedral face)")
    print("  HexInTri    -> World Hex (within triangle)")
    print("  HexInHex    -> Terrain Hex (within world hex)")
    print("  HexInHex    -> Local Hex (within terrain hex)")
    print()

    demo_low_level_packing()
    demo_coordinate_creation()
    demo_component_extraction()
    demo_immutable_editing()
    demo_output_formats()
    demo_hashing_and_equality()
    demo_immutability()

    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
