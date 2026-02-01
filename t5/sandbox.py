"""Sandbox for testing and demonstrating the t5humanise package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add the src directory to sys.path for local development
_src_path = Path(__file__).parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

# Now we can import with full IDE support
from t5humanise.space.world_coordinate_mappings import WorldMapper  # noqa: E402


def demo_world_coordinate_mappings() -> None:
    """Demonstrate the world coordinate mappings."""
    print("World Coordinate Mappings")
    print("-" * 40)

    test_rolls = [
        (WorldMapper.DieTypeEnum.BLACK, 1, 1),
        (WorldMapper.DieTypeEnum.BLACK, 3, 4),
        (WorldMapper.DieTypeEnum.WHITE, 2, 5),
        (WorldMapper.DieTypeEnum.WHITE, 6, 6),
        (WorldMapper.DieTypeEnum.BLACK, 0, 7),  # Out of bounds test
    ]

    for die_type, roll_1, roll_2 in test_rolls:
        hex_coord = WorldMapper.get_hex_coordinate(map_type=WorldMapper.MapType.WORLD, die_type=die_type, roll_1=roll_1, roll_2=roll_2)
        print(f"Die Type: {die_type.name}, Rolls: ({roll_1}, {roll_2}) -> Hex Coordinate(x,y): {hex_coord}")
    
    test_coords = [
        (0, -1),
        (-3, 2),
        (1, 4),
        (3, 4),
        (6, -6),  # Out of bounds test
    ]
    for hex_x, hex_y in test_coords:
        dice_value = WorldMapper.get_dice_value_from_coordinate(map_type=WorldMapper.MapType.WORLD, hex_x=hex_x, hex_y=hex_y)
        print(f"Hex Coordinate(x,y): ({hex_x}, {hex_y}) -> Dice Value: {dice_value}")

def demo_terrain_coordinate_mappings() -> None:
    """Demonstrate the terrain coordinate mappings."""
    print("Terrain Coordinate Mappings")
    print("-" * 40)

    test_rolls = [
        (WorldMapper.DieTypeEnum.BLACK, 1, 1),
        (WorldMapper.DieTypeEnum.BLACK, 3, 4),
        (WorldMapper.DieTypeEnum.WHITE, 2, 5),
        (WorldMapper.DieTypeEnum.WHITE, 6, 6),
        (WorldMapper.DieTypeEnum.BLACK, 0, 7),  # Out of bounds test
    ]

    for die_type, roll_1, roll_2 in test_rolls:
        hex_coord = WorldMapper.get_hex_coordinate(map_type=WorldMapper.MapType.TERRAIN, die_type=die_type, roll_1=roll_1, roll_2=roll_2)
        print(f"Die Type: {die_type.name}, Rolls: ({roll_1}, {roll_2}) -> Terrain Hex Coordinate(x,y): {hex_coord}")
    
    test_coords = [
        (0, -1),
        (-3, 2),
        (1, 4),
        (3, 4),
        (6, -6),  # Out of bounds test
    ]
    for hex_x, hex_y in test_coords:
        dice_value = WorldMapper.get_dice_value_from_coordinate(map_type=WorldMapper.MapType.TERRAIN, hex_x=hex_x, hex_y=hex_y)
        print(f"Terrain Hex Coordinate(x,y): ({hex_x}, {hex_y}) -> Dice Value: {dice_value}")

def main() -> None:
    """Run all demonstrations."""
    print("\033c", end="")
    print("Demo")
    print("=" * 60)
    print()

    demo_world_coordinate_mappings()
    demo_terrain_coordinate_mappings()
    
    print("=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    main()
