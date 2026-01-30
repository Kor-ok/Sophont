"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.space.system_coordinates import (  # noqa: E402
    SystemCoordinates,
    letter_to_satellite,
    satellite_to_letter,
)


def demo_satellite_letters() -> None:
    """Demonstrate satellite letter conversion utilities."""
    print("Satellite Letter Utilities")
    print("-" * 40)

    print("\nNumber to letter conversion:")
    for num in [1, 4, 13, 26]:
        letter = satellite_to_letter(num)
        print(f"  {num:2d} -> '{letter}'")

    print("\nLetter to number conversion:")
    for letter in ["A", "D", "M", "Z"]:
        num = letter_to_satellite(letter)
        print(f"  '{letter}' -> {num}")

    print("\nSpecial case (0 = no satellite):")
    print(f"  satellite_to_letter(0) -> '{satellite_to_letter(0)}' (empty)")
    print(f"  letter_to_satellite('') -> {letter_to_satellite('')}")

    print()


def demo_factory_methods() -> None:
    """Demonstrate the various factory methods for creating coordinates."""
    print("Factory Methods")
    print("-" * 40)

    # Simple planet
    print("\n1. Planet at orbit 3 (around primary star):")
    planet = SystemCoordinates.planet(3)
    print(f"   {planet!r}")
    print(f"   Designation: {planet.to_designation()}")

    # Moon with numeric designation
    print("\n2. Moon 4 (D) of planet at orbit 5:")
    moon_num = SystemCoordinates.moon(5, 4)
    print(f"   {moon_num!r}")
    print(f"   Designation: {moon_num.to_designation()}")

    # Moon with letter designation
    print("\n3. Moon 'A' of planet at orbit 7 (using letter):")
    moon_letter = SystemCoordinates.moon(7, "A")
    print(f"   {moon_letter!r}")
    print(f"   Designation: {moon_letter.to_designation()}")

    # Planet orbiting companion star
    print("\n4. Planet at orbit 2 of companion star at orbit 8:")
    comp_planet = SystemCoordinates.companion_planet(8, 2)
    print(f"   {comp_planet!r}")
    print(f"   Designation: {comp_planet.to_designation()}")

    # Moon orbiting planet around companion star
    print("\n5. Moon 'C' of planet at orbit 3 of companion at orbit 5:")
    comp_moon = SystemCoordinates.companion_moon(5, 3, "C")
    print(f"   {comp_moon!r}")
    print(f"   Designation: {comp_moon.to_designation()}")

    # Direct tuple construction for deeper nesting
    print("\n6. Deep nesting (4 levels) - via direct construction:")
    deep = SystemCoordinates(levels=((10, 0), (5, 0), (2, 0), (1, 3)))
    print(f"   {deep!r}")
    print(f"   Designation: {deep.to_designation()}")

    print()


def demo_property_extraction() -> None:
    """Demonstrate extracting properties from coordinates."""
    print("Property Extraction")
    print("-" * 40)

    # Create a complex coordinate
    coord = SystemCoordinates.companion_moon(8, 3, "D")

    print(f"\nCoordinate: {coord!r}")
    print(f"Designation: {coord.to_designation()}")

    print("\nExtracted properties:")
    print(f"  depth:          {coord.depth}")
    print(f"  levels:         {coord.levels}")
    print(f"  primary_orbit:  {coord.primary_orbit}")
    print(f"  final_orbit:    {coord.final_orbit}")
    print(f"  final_satellite: {coord.final_satellite}")
    print(f"  is_moon:        {coord.is_moon}")
    print(f"  is_nested:      {coord.is_nested}")

    print("\nComparison with simple planet:")
    planet = SystemCoordinates.planet(5)
    print(f"  Coordinate: {planet.to_designation()}")
    print(f"  is_moon:   {planet.is_moon}")
    print(f"  is_nested: {planet.is_nested}")

    print()


def demo_immutable_editing() -> None:
    """Demonstrate immutable 'with_*' methods and parent navigation."""
    print("Immutable Editing")
    print("-" * 40)

    # Start with a planet
    planet = SystemCoordinates.planet(5)
    print(f"\nOriginal planet: {planet.to_designation()}")

    # Add a moon designation
    moon = planet.with_satellite("B")
    print(f"With satellite 'B': {moon.to_designation()}")
    print(f"Original unchanged: {planet.to_designation()}")

    # Start fresh and add nesting
    print("\nBuilding nested coordinates:")
    step1 = SystemCoordinates.planet(8)
    print(f"  Step 1 (companion location): {step1.to_designation()}")

    step2 = step1.with_nested(3)
    print(f"  Step 2 (add planet orbit): {step2.to_designation()}")

    step3 = step2.with_satellite("A")
    print(f"  Step 3 (add moon): {step3.to_designation()}")

    # Navigate back up
    print("\nParent navigation:")
    print(f"  Current: {step3.to_designation()}")
    parent = step3.parent()
    if parent:
        print(f"  Parent:  {parent.to_designation()}")
        grandparent = parent.parent()
        if grandparent:
            print(f"  Grandparent: {grandparent.to_designation()}")

    print()


def demo_output_formats() -> None:
    """Demonstrate string output methods."""
    print("Output Formats")
    print("-" * 40)

    # Various coordinates to demonstrate
    examples = [
        ("Simple planet", SystemCoordinates.planet(3)),
        ("Planet with moon", SystemCoordinates.moon(5, "D")),
        ("Companion planet", SystemCoordinates.companion_planet(8, 2)),
        ("Companion moon", SystemCoordinates.companion_moon(5, 3, "C")),
        (
            "Deep nesting",
            SystemCoordinates(levels=((10, 0), (5, 0), (2, 3))),
        ),
    ]

    for name, coord in examples:
        print(f"\n{name}:")
        print(f"  repr():          {coord!r}")
        print(f"  to_designation(): {coord.to_designation()}")
        print(f"  to_hex_string():  {coord.to_hex_string()}")

    print("\nDetailed component breakdown:")
    deep = SystemCoordinates(levels=((10, 0), (5, 0), (2, 3)))
    print(deep.to_components_string())

    print()


def demo_hashing_and_equality() -> None:
    """Demonstrate that coordinates are hashable and comparable."""
    print("Hashing and Equality")
    print("-" * 40)

    coord1 = SystemCoordinates.moon(5, "C")
    coord2 = SystemCoordinates.moon(5, 3)  # Same as "C"
    coord3 = SystemCoordinates.moon(5, "D")

    print(f"\ncoord1: {coord1.to_designation()}")
    print(f"coord2: {coord2.to_designation()} (same moon, different constructor)")
    print(f"coord3: {coord3.to_designation()}")

    print(f"\ncoord1 == coord2: {coord1 == coord2}")
    print(f"coord1 == coord3: {coord1 == coord3}")
    print(f"coord1 is coord2: {coord1 is coord2}")

    print("\nUsable as dict keys:")
    locations = {
        SystemCoordinates.planet(3): "Earth-like world",
        SystemCoordinates.moon(5, "A"): "Mining colony",
        SystemCoordinates.companion_planet(8, 2): "Gas giant",
    }
    for coord, name in locations.items():
        print(f"  {coord.to_designation():15s} -> {name}")

    print()


def demo_packed_roundtrip() -> None:
    """Demonstrate packing and unpacking coordinates."""
    print("Packed Value Roundtrip")
    print("-" * 40)

    original = SystemCoordinates.companion_moon(8, 3, "D")
    print(f"\nOriginal:   {original!r}")
    print(f"Designation: {original.to_designation()}")

    packed = original.packed
    print(f"\nPacked value: 0x{packed:016X}")

    restored = SystemCoordinates.from_packed(packed)
    print(f"Restored:    {restored!r}")
    print(f"Designation: {restored.to_designation()}")

    print(f"\nOriginal == Restored: {original == restored}")

    print()


def demo_real_world_scenario() -> None:
    """Demonstrate a real-world multi-star system scenario."""
    print("Real-World Scenario: Binary Star System")
    print("-" * 40)

    print(
        """
Scenario: A binary star system where:
  - Primary star (A) has planets at orbits III, V, and VII
  - Companion star (B) orbits at position VIII
  - Companion has its own planet at orbit II with moons
"""
    )

    # Define locations
    locations = {
        "Primary III": SystemCoordinates.planet(3),
        "Primary V": SystemCoordinates.planet(5),
        "Primary VII (with moon a)": SystemCoordinates.moon(7, "A"),
        "Companion B location": SystemCoordinates.planet(8),
        "Companion II": SystemCoordinates.companion_planet(8, 2),
        "Companion II moon c": SystemCoordinates.companion_moon(8, 2, "C"),
    }

    print("System map:")
    for name, coord in locations.items():
        print(f"  {coord.to_designation():20s} <- {name}")

    # Show navigation
    print("\nNavigating from Companion II moon c back to primary:")
    current = locations["Companion II moon c"]
    path = [current]
    while current.parent():
        current = current.parent()  # type: ignore[assignment]
        path.append(current)

    for i, loc in enumerate(path):
        indent = "  " * i
        print(f"  {indent}{loc.to_designation()}")

    print()


def main() -> None:
    """Run all demonstrations."""
    print("T5 SystemCoordinates Demo")
    print("=" * 60)
    print()
    print("A hierarchical coordinate system for stellar system locations:")
    print("  - Supports orbits 0-20 around any star")
    print("  - Supports satellite designations A-Z (1-26)")
    print("  - Supports nested subsystems for companion stars")
    print("  - Up to 4 levels of nesting")
    print()

    demo_satellite_letters()
    demo_factory_methods()
    demo_property_extraction()
    demo_immutable_editing()
    demo_output_formats()
    demo_hashing_and_equality()
    demo_packed_roundtrip()
    demo_real_world_scenario()

    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
