from __future__ import annotations

from game.improvedmappings.init_mappings import (
    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES,
    CHARACTERISTICS_MASTER_CATEGORY_CODES,
    CHARACTERISTICS_MATRIX,
    KNOWLEDGES_BASE_KNOWLEDGE_CODES,
    KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS,
    SKILLS_BASE_SKILL_CODES,
    SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES,
    SKILLS_MASTER_CATEGORY_CODES,
    SKILLS_SUB_CATEGORY_CODES,
)

print("\033c", end="")

def TestSkillsMapping():
    print("Base Skill Codes to Categories Mapping:")
    for base_skill_code, (master_cat, sub_cat) in SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES.items():
        base_skill_aliases = SKILLS_BASE_SKILL_CODES.get(base_skill_code, ("<unknown>",))
        master_cat_aliases = SKILLS_MASTER_CATEGORY_CODES.get(master_cat, ("<unknown>",))
        sub_cat_aliases = SKILLS_SUB_CATEGORY_CODES.get(sub_cat, ("<unknown>",))
        print(
            f"Base Skill Code: {base_skill_code} ({', '.join(base_skill_aliases)}) -> "
            f"Master Category: {master_cat} ({', '.join(master_cat_aliases)}), "
            f"Sub Category: {sub_cat} ({', '.join(sub_cat_aliases)})"
        )

def TestKnowledgesMapping():
    print("\nKnowledge to Associated Skills Mapping:")
    for knowledge_code, skill_codes in KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS.items():
        knowledge_aliases = KNOWLEDGES_BASE_KNOWLEDGE_CODES.get(knowledge_code, ("<unknown>",))
        skill_aliases_list = [
            SKILLS_BASE_SKILL_CODES.get(skill_code, ("<unknown>",))
            for skill_code in skill_codes
        ]
        skill_aliases_str = "; ".join(
            f"{skill_code} ({', '.join(aliases)})"
            for skill_code, aliases in zip(skill_codes, skill_aliases_list)
        )
        print(
            f"Knowledge Code: {knowledge_code} ({', '.join(knowledge_aliases)}) -> "
            f"Associated Skills: {skill_aliases_str}"
        )

def TestCharacteristicsMapping():
    print("\nCharacteristic Master Category Codes:")
    for category_code, aliases in CHARACTERISTICS_MASTER_CATEGORY_CODES.items():
        print(f"Category Code: {category_code} -> Aliases: {', '.join(aliases)}")

    print("\nCharacteristic Full Code to String Aliases Mapping:")
    for (full_code_tuple, str_code), aliases in CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES.items():
        upp_index, sub_code, master_code = full_code_tuple
        print(
            f"Full Code: (UPP Index: {upp_index}, Sub Code: {sub_code}, Master Code: {master_code}), "
            f"String Code: {str_code} -> Aliases: {', '.join(aliases)}"
        )

    print("\nCharacteristics Matrix:")
    for characteristic in CHARACTERISTICS_MATRIX:
        print(f"Characteristic: {characteristic}")
        for (y_code, x_code), value in CHARACTERISTICS_MATRIX.items():
            print(
                f"  Y Code: {y_code}, X Code: {x_code} -> Value: {value}"
            )

    # Count the number of entries in the characteristics matrix
    matrix_size = len(CHARACTERISTICS_MATRIX)
    print(f"\nTotal entries in Characteristics Matrix: {matrix_size}")