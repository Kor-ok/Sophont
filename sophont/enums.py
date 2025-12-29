from enum import Enum

class CharValueType(Enum):
    GENETIC = 1
    LIFE = 2
    MODIFIER = 3
    TOTAL = 4

CHAR_VALUE_MAP = {
    CharValueType.GENETIC: lambda char: char.genetic_value,
    CharValueType.LIFE: lambda char: char.life_value,
    CharValueType.MODIFIER: lambda char: char.mod_value,
    CharValueType.TOTAL: lambda char: char.total_value
}