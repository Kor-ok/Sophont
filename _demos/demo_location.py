"""Demonstration of the Location immutable flyweight class."""

from __future__ import annotations

from components.location import ChartedSpace, Location, SystemSpace, WorldSpace


def demo_low_level_packing() -> None:
    """Demonstrate the low-level packing functions."""
    print("Low-Level Packing Functions")
    print("-" * 40)

    # ChartedSpace: Pack source, milieu, and world-space coordinates
    print("\nChartedSpace (39 bits):")
    print("  Packs source (2 bits), milieu (5 bits), x/y coords (16 bits each)")
    examples = [
        (0, 0, 0, 0),  # Origin
        (1, 15, 100, -50),  # TravellerMap, some milieu, positive/negative coords
        (2, 31, -1000, 2000),  # Max milieu example
    ]
    for source, milieu, x, y in examples:
        packed = ChartedSpace.pack(source, milieu, x, y)
        print(f"  (src={source}, mil={milieu}, x={x}, y={y}) -> 0x{packed:010X}")

    # SystemSpace: Pack orbit hierarchy
    print("\nSystemSpace (11 bits):")
    print("  Packs orbit_num (5 bits), has_nested (1 bit), satellite_orbit (5 bits)")
    examples = [
        (3, 0, 0),  # Earth (no moon focus)
        (3, 1, 13),  # Earth's Moon
        (2, 1, 5),  # ExoMoon of gas giant around secondary star
        (4, 0, 0),  # Mars
    ]
    for orbit, nested, sat in examples:
        packed = SystemSpace.pack(orbit, nested, sat)
        print(f"  (orbit={orbit}, nested={nested}, sat={sat}) -> 0x{packed:03X}")

    # WorldSpace: Pack planetary surface coordinates
    print("\nWorldSpace (37 bits):")
    print("  Packs tri_in_ico (5), hex_in_tri (16), terrain (8), local (8)")
    examples = [
        (0, 0, 0, 0),  # Origin
        (0x13, 0x4A0F, 0x2D, 0xF4),  # Example from world_coordinates demo
    ]
    for tri, hex_tri, terrain, local in examples:
        packed = WorldSpace.pack(tri, hex_tri, terrain, local)
        print(f"  (tri=0x{tri:02X}, hex=0x{hex_tri:04X}, ter=0x{terrain:02X}, loc=0x{local:02X}) -> 0x{packed:010X}")

    print()


def demo_location_creation() -> None:
    """Demonstrate Location creation methods."""
    print("Location Creation")
    print("-" * 40)

    # Method 1: From pre-packed component values
    print("\n1. From pre-packed components:")
    charted = ChartedSpace.pack(1, 15, 100, -50)
    system = SystemSpace.pack(3, 1, 13)
    world = WorldSpace.pack(0x13, 0x4A0F, 0x2D, 0xF4)
    loc1 = Location(charted, system, world)
    print(f"   {loc1!r}")

    # Method 2: From individual components
    print("\n2. From individual components:")
    loc2 = Location.from_components(
        source=1,
        milieu=15,
        x_coord=100,
        y_coord=-50,
        orbit_num=3,
        has_nested=1,
        satellite_orbit_num=13,
        tri_in_ico=0x13,
        hex_in_tri=0x4A0F,
        hex_in_hex_terrain=0x2D,
        hex_in_hex_local=0xF4,
    )
    print(f"   {loc2!r}")
    print(f"   Equal to loc1? {loc1 == loc2}")

    # Method 3: From a single packed integer
    print("\n3. From packed integer:")
    packed_value = loc1.packed
    loc3 = Location.from_packed(packed_value)
    print(f"   Packed value: 0x{packed_value:022X}")
    print(f"   {loc3!r}")
    print(f"   Equal to loc1? {loc1 == loc3}")

    print()


def demo_component_extraction() -> None:
    """Demonstrate extracting components from a Location."""
    print("Component Extraction")
    print("-" * 40)

    loc = Location.from_components(
        source=2,
        milieu=10,
        x_coord=-500,
        y_coord=750,
        orbit_num=4,
        has_nested=1,
        satellite_orbit_num=7,
        tri_in_ico=0x0A,
        hex_in_tri=0x1234,
        hex_in_hex_terrain=0x55,
        hex_in_hex_local=0xAA,
    )

    print("\nFull packed value:")
    print(f"  packed: {loc.to_hex_string()}")

    print("\nPacked component values:")
    print(f"  charted_space:  0x{loc.charted_space:010X}")
    print(f"  system_space:   0x{loc.system_space:03X}")
    print(f"  world_space:    0x{loc.world_space:010X}")

    print("\nUnpacked individual values:")
    print(f"  ChartedSpace: source={loc.source}, milieu={loc.milieu}, x={loc.x_coord}, y={loc.y_coord}")
    print(f"  SystemSpace:  orbit={loc.orbit_num}, nested={loc.has_nested}, sat_orbit={loc.satellite_orbit_num}")
    print(f"  WorldSpace:   tri=0x{loc.tri_in_ico:02X}, hex=0x{loc.hex_in_tri:04X}, terrain=0x{loc.hex_in_hex_terrain:02X}, local=0x{loc.hex_in_hex_local:02X}")

    print("\nHuman-readable breakdown:")
    for line in loc.to_components_string().split("\n"):
        print(f"  {line}")

    print()


def demo_real_world_examples() -> None:
    """Demonstrate real-world-ish location examples."""
    print("Real-World Examples")
    print("-" * 40)

    # Earth's Moon in the Solomani Rim
    print("\n1. Earth's Moon (Sol System, Solomani Rim):")
    earth_moon = Location.from_components(
        source=0,  # TravellerMap
        milieu=4,  # Milieu 0 (arbitrary)
        x_coord=1827,  # Sol sector coordinates (example)
        y_coord=549,
        orbit_num=3,  # Earth's orbit
        has_nested=1,  # Yes, we're on a satellite
        satellite_orbit_num=1,  # Moon's orbit index
        tri_in_ico=0,  # Surface location (default)
        hex_in_tri=0,
        hex_in_hex_terrain=0,
        hex_in_hex_local=0,
    )
    print(f"   {earth_moon!r}")

    # Mars surface location
    print("\n2. Mars Surface (Olympus Mons region):")
    mars = Location.from_components(
        source=0,
        milieu=4,
        x_coord=1827,
        y_coord=549,
        orbit_num=4,  # Mars orbit
        has_nested=0,  # No satellite
        satellite_orbit_num=0,
        tri_in_ico=0x05,  # Some icosahedral face
        hex_in_tri=0x1000,  # Some world hex
        hex_in_hex_terrain=0x12,  # Terrain hex
        hex_in_hex_local=0x34,  # Local hex
    )
    print(f"   {mars!r}")

    # ExoMoon of a gas giant in a binary system
    print("\n3. ExoMoon of Gas Giant (Binary Star System):")
    exomoon = Location.from_components(
        source=1,  # Different source
        milieu=8,  # Different era
        x_coord=-200,
        y_coord=300,
        orbit_num=2,  # Secondary star's orbit around primary
        has_nested=1,  # Nested (gas giant -> moon)
        satellite_orbit_num=5,  # Moon's orbit around gas giant
        tri_in_ico=0x0F,
        hex_in_tri=0x2468,
        hex_in_hex_terrain=0xAB,
        hex_in_hex_local=0xCD,
    )
    print(f"   {exomoon!r}")

    print()


def demo_immutable_editing() -> None:
    """Demonstrate immutable 'with_*' methods for editing."""
    print("Immutable Editing (with_* methods)")
    print("-" * 40)

    original = Location.from_components(
        source=0, milieu=4, x_coord=100, y_coord=200,
        orbit_num=3, has_nested=0, satellite_orbit_num=0,
        tri_in_ico=0x05, hex_in_tri=0x1000, hex_in_hex_terrain=0x12, hex_in_hex_local=0x34,
    )
    print(f"\nOriginal: {original!r}")

    # Each with_* method returns a NEW instance
    print("\nEditing operations (each returns a new instance):")

    new1 = original.with_charted_space(1, 8, -500, 750)
    print(f"  with_charted_space(1, 8, -500, 750):")
    print(f"    source={new1.source}, milieu={new1.milieu}, x={new1.x_coord}, y={new1.y_coord}")
    print(f"    Original unchanged? source={original.source}, milieu={original.milieu}")

    new2 = original.with_system_space(5, 1, 10)
    print(f"  with_system_space(5, 1, 10):")
    print(f"    orbit={new2.orbit_num}, nested={new2.has_nested}, sat={new2.satellite_orbit_num}")

    new3 = original.with_world_space(0x0A, 0x2000, 0x55, 0xAA)
    print(f"  with_world_space(0x0A, 0x2000, 0x55, 0xAA):")
    print(f"    tri=0x{new3.tri_in_ico:02X}, hex=0x{new3.hex_in_tri:04X}, terrain=0x{new3.hex_in_hex_terrain:02X}, local=0x{new3.hex_in_hex_local:02X}")

    # Chaining edits
    print("\nChained edits:")
    chained = (
        original
        .with_charted_space(2, 10, 1000, -1000)
        .with_system_space(4, 1, 7)
        .with_world_space(0x0F, 0x5000, 0xCC, 0xDD)
    )
    print(f"  {chained!r}")

    print()


def demo_hashing_and_equality() -> None:
    """Demonstrate that Location instances are hashable and comparable."""
    print("Hashing and Equality")
    print("-" * 40)

    loc1 = Location.from_components(
        source=1, milieu=5, x_coord=100, y_coord=200,
        orbit_num=3, has_nested=0, satellite_orbit_num=0,
        tri_in_ico=0, hex_in_tri=0, hex_in_hex_terrain=0, hex_in_hex_local=0,
    )
    loc2 = Location.from_components(
        source=1, milieu=5, x_coord=100, y_coord=200,
        orbit_num=3, has_nested=0, satellite_orbit_num=0,
        tri_in_ico=0, hex_in_tri=0, hex_in_hex_terrain=0, hex_in_hex_local=0,
    )
    loc3 = Location.from_components(
        source=1, milieu=5, x_coord=100, y_coord=201,  # Different y
        orbit_num=3, has_nested=0, satellite_orbit_num=0,
        tri_in_ico=0, hex_in_tri=0, hex_in_hex_terrain=0, hex_in_hex_local=0,
    )

    print(f"\nloc1 == loc2: {loc1 == loc2}")
    print(f"loc1 == loc3: {loc1 == loc3}")
    print(f"loc1 is loc2: {loc1 is loc2}")

    print("\nUsable as dict keys:")
    loc_dict = {loc1: "Home Base", loc3: "Nearby System"}
    print(f"  loc_dict[loc1] = {loc_dict[loc1]!r}")
    print(f"  loc_dict[loc2] = {loc_dict[loc2]!r}  (same as loc1)")

    print("\nUsable in sets:")
    loc_set = {loc1, loc2, loc3}
    print(f"  Set of 3 locations (2 equal): {len(loc_set)} unique")

    print()


def demo_immutability() -> None:
    """Demonstrate that Location is immutable."""
    print("Immutability")
    print("-" * 40)

    loc = Location.from_components(
        source=0, milieu=0, x_coord=0, y_coord=0,
        orbit_num=0, has_nested=0, satellite_orbit_num=0,
        tri_in_ico=0, hex_in_tri=0, hex_in_hex_terrain=0, hex_in_hex_local=0,
    )

    print("\nAttempting to modify _packed attribute:")
    try:
        loc._packed = 0  # type: ignore[misc]
    except AttributeError as e:
        print(f"  Caught: {e}")

    print()


def demo_bit_efficiency() -> None:
    """Demonstrate the bit-packing efficiency."""
    print("Bit-Packing Efficiency")
    print("-" * 40)

    print("\nLocation packs everything into a single 87-bit integer:")
    print("  - ChartedSpace (39 bits): source, milieu, x/y coordinates")
    print("  - SystemSpace (11 bits): orbit hierarchy")
    print("  - WorldSpace (37 bits): planetary surface location")
    print("\nBit layout: [ChartedSpace:39][SystemSpace:11][WorldSpace:37]")

    loc = Location.from_components(
        source=3, milieu=31, x_coord=32767, y_coord=-32768,
        orbit_num=31, has_nested=1, satellite_orbit_num=31,
        tri_in_ico=0x1F, hex_in_tri=0xFFFF, hex_in_hex_terrain=0xFF, hex_in_hex_local=0xFF,
    )
    print(f"\nMax values example:")
    print(f"  {loc!r}")
    print(f"  {loc.to_hex_string()}")

    print()


def main() -> None:
    """Run all demonstrations."""
    print("Location Immutable Flyweight Demo")
    print("=" * 60)
    print()
    print("A hierarchical location system combining:")
    print("  ChartedSpace  -> Sector/subsector coordinates")
    print("  SystemSpace   -> Orbital hierarchy within a system")
    print("  WorldSpace    -> Planetary surface coordinates")
    print()

    demo_low_level_packing()
    demo_location_creation()
    demo_component_extraction()
    demo_real_world_examples()
    demo_immutable_editing()
    demo_hashing_and_equality()
    demo_immutability()
    demo_bit_efficiency()

    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()