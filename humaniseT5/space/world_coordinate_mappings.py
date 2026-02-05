from __future__ import annotations

from enum import Enum, IntEnum

from typing_extensions import TypeAlias

DieType: TypeAlias = int
Die_1: TypeAlias = int
Die_2: TypeAlias = int
Hex_x: TypeAlias = int
Hex_y: TypeAlias = int

DiceValue: TypeAlias = tuple[DieType, Die_1, Die_2]
HexCoordinate: TypeAlias = tuple[Hex_x, Hex_y]

worldhex_mappings: dict[DiceValue, HexCoordinate] = {
    (0, 1, 1): (-5, -1), 
    (0, 1, 2): (-5, -2), 
    (0, 1, 3): (-5, -4), 
    (0, 1, 4): (-5, -5), 
    (0, 1, 5): (-4, -5), 
    (0, 1, 6): (-3, -5), 
    (0, 2, 1): (-1, -5), 
    (0, 2, 2): (0, -5), 
    (0, 2, 3): (1, -4), 
    (0, 2, 4): (3, -2), 
    (0, 2, 5): (4, -1), 
    (0, 2, 6): (4, 0), 
    (0, 3, 1): (4, 1), 
    (0, 3, 2): (4, 3), 
    (0, 3, 3): (4, 4), 
    (0, 3, 4): (2, 4), 
    (0, 3, 5): (1, 4), 
    (0, 3, 6): (0, 4), 
    (0, 4, 1): (-1, 3), 
    (0, 4, 2): (-2, 2), 
    (0, 4, 3): (-4, 0), 
    (0, 4, 4): (-4, -1), 
    (0, 4, 5): (-4, -3), 
    (0, 4, 6): (-4, -4), 
    (0, 5, 1): (-3, -4), 
    (0, 5, 2): (-1, -4), 
    (0, 5, 3): (0, -4), 
    (0, 5, 4): (1, -3), 
    (0, 5, 5): (3, -1), 
    (0, 5, 6): (3, 0), 
    (0, 6, 1): (3, 3), 
    (0, 6, 2): (1, 3), 
    (0, 6, 3): (0, 3), 
    (0, 6, 4): (0, 2), 
    (0, 6, 5): (-1, 1), 
    (0, 6, 6): (-2, 0), 
    (1, 1, 1): (0, 0), 
    (1, 1, 2): (-1, -1), 
    (1, 1, 3): (0, -1), 
    (1, 1, 4): (1, 0), 
    (1, 1, 5): (1, 1), 
    (1, 1, 6): (0, 1), 
    (1, 2, 1): (-1, 0), 
    (1, 2, 2): (-2, -1), 
    (1, 2, 3): (-3, -1), 
    (1, 2, 4): (-3, 0), 
    (1, 2, 5): (-2, 1), 
    (1, 2, 6): (-1, 2), 
    (1, 3, 1): (-3, 1), 
    (1, 3, 2): (-4, -2), 
    (1, 3, 3): (-3, -2), 
    (1, 3, 4): (-3, -3), 
    (1, 3, 5): (-2, -2), 
    (1, 3, 6): (-2, -3), 
    (1, 4, 1): (-2, -4), 
    (1, 4, 2): (-1, -3), 
    (1, 4, 3): (-1, -2), 
    (1, 4, 4): (0, -2), 
    (1, 4, 5): (0, -3), 
    (1, 4, 6): (1, -2), 
    (1, 5, 1): (2, -2), 
    (1, 5, 2): (2, -1), 
    (1, 5, 3): (1, -1), 
    (1, 5, 4): (2, 0), 
    (1, 5, 5): (3, 1), 
    (1, 5, 6): (4, 2), 
    (1, 6, 1): (3, 2), 
    (1, 6, 2): (2, 1), 
    (1, 6, 3): (2, 2), 
    (1, 6, 4): (1, 2), 
    (1, 6, 5): (2, 3), 
    (1, 6, 6): (3, 4), 
}

terrainhex_mappings: dict[DiceValue, HexCoordinate] = {
    (0, 1, 1): (-5, -1), 
    (0, 1, 2): (-5, -2), 
    (0, 1, 3): (-5, -3), 
    (0, 1, 4): (-5, -5), 
    (0, 1, 5): (-4, -5), 
    (0, 1, 6): (-3, -5), 
    (0, 2, 1): (-1, -5), 
    (0, 2, 2): (0, -5), 
    (0, 2, 3): (1, -4), 
    (0, 2, 4): (2, -3), 
    (0, 2, 5): (4, -1), 
    (0, 2, 6): (4, 0), 
    (0, 3, 1): (4, 1), 
    (0, 3, 2): (4, 3), 
    (0, 3, 3): (4, 4), 
    (0, 3, 4): (2, 4), 
    (0, 3, 5): (1, 4), 
    (0, 3, 6): (0, 4), 
    (0, 4, 1): (-1, 3), 
    (0, 4, 2): (-2, 2), 
    (0, 4, 3): (-4, 0), 
    (0, 4, 4): (-4, -1), 
    (0, 4, 5): (-4, -2), 
    (0, 4, 6): (-4, -4), 
    (0, 5, 1): (-3, -4), 
    (0, 5, 2): (-1, -4), 
    (0, 5, 3): (0, -4), 
    (0, 5, 4): (2, -2), 
    (0, 5, 5): (3, -1), 
    (0, 5, 6): (3, 0), 
    (0, 6, 1): (3, 3), 
    (0, 6, 2): (1, 3), 
    (0, 6, 3): (0, 3), 
    (0, 6, 4): (0, 2), 
    (0, 6, 5): (0, 1), 
    (0, 6, 6): (1, 1), 
    (1, 1, 1): (0, 0), 
    (1, 1, 2): (-1, 0), 
    (1, 1, 3): (-1, 1), 
    (1, 1, 4): (-1, 2), 
    (1, 1, 5): (-2, 1), 
    (1, 1, 6): (-3, 1), 
    (1, 2, 1): (-3, 0), 
    (1, 2, 2): (-2, 0), 
    (1, 2, 3): (-2, -1), 
    (1, 2, 4): (-3, -1), 
    (1, 2, 5): (-3, -2), 
    (1, 2, 6): (-4, -3), 
    (1, 3, 1): (-3, -3), 
    (1, 3, 2): (-2, -2), 
    (1, 3, 3): (-2, -3), 
    (1, 3, 4): (-2, -4), 
    (1, 3, 5): (-1, -3), 
    (1, 3, 6): (0, -3), 
    (1, 4, 1): (1, -3), 
    (1, 4, 2): (1, -2), 
    (1, 4, 3): (0, -2), 
    (1, 4, 4): (-1, -2), 
    (1, 4, 5): (-1, -1), 
    (1, 4, 6): (0, -1), 
    (1, 5, 1): (1, -1), 
    (1, 5, 2): (2, -1), 
    (1, 5, 3): (2, 0), 
    (1, 5, 4): (1, 0), 
    (1, 5, 5): (2, 1), 
    (1, 5, 6): (3, 1), 
    (1, 6, 1): (4, 2), 
    (1, 6, 2): (3, 2), 
    (1, 6, 3): (2, 2), 
    (1, 6, 4): (1, 2), 
    (1, 6, 5): (2, 3), 
    (1, 6, 6): (3, 4), 
}

class WorldMapper:
    class DieTypeEnum(IntEnum):
        BLACK = 0
        WHITE = 1

    class MapType(Enum):
        WORLD = "WorldHex"
        TERRAIN = "TerrainHex"
        LOCAL = "LocalHex"

    @staticmethod
    def get_hex_coordinate(map_type: MapType,die_type: DieTypeEnum, roll_1: int, roll_2: int) -> HexCoordinate | None:
        """Get the hex coordinate for a given dice value.

        Args:
            die_type (DieTypeEnum): The type of die (BLACK or WHITE).
            roll_1 (int): The result of the first die roll.
            roll_2 (int): The result of the second die roll.

        Returns:
            HexCoordinate | None: The corresponding hex coordinate (Hex_x, Hex_y) or None if not found.
        """
        roll_1 = max(1, min(6, roll_1))
        roll_2 = max(1, min(6, roll_2))
        dice_value: DiceValue = (die_type.value, roll_1, roll_2)
        if map_type in (WorldMapper.MapType.WORLD, WorldMapper.MapType.LOCAL):
            return worldhex_mappings.get(dice_value)
        elif map_type == WorldMapper.MapType.TERRAIN:
            return terrainhex_mappings.get(dice_value)
    
    @staticmethod
    def get_dice_value_from_coordinate(map_type: MapType, hex_x: int, hex_y: int) -> DiceValue | None:
        """Get the dice value for a given hex coordinate.

        Args:
            hex_x (int): The x coordinate of the hex.
            hex_y (int): The y coordinate of the hex.

        Returns:
            DiceValue | None: The corresponding dice value (DieType, Die_1, Die_2) or None if not found.
        """
        if map_type in (WorldMapper.MapType.WORLD, WorldMapper.MapType.LOCAL):
            mapping = worldhex_mappings
        elif map_type == WorldMapper.MapType.TERRAIN:
            mapping = terrainhex_mappings
        else:
            return None
        for dice_value, coordinate in mapping.items():
            if coordinate == (hex_x, hex_y):
                return dice_value
        return None