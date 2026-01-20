from __future__ import annotations

import os
from typing import Final

import pandas as pd

from game.mappings.authoring import (
    load_characteristics_matrix_from_xlsx,
    load_code_to_str_aliases_from_xlsx,
    load_full_characteristic_code_to_str_aliases_from_xlsx,
    load_knowledge_to_skills_associations_from_xlsx,
    load_skill_code_to_categories_from_xlsx,
)

current_dir = os.path.dirname(os.path.abspath(__file__))

XLSX_FILENAME = "T5Mappings.xlsx"
XLSX_PATH = os.path.join(current_dir, XLSX_FILENAME)
LANG_CODE = "en"

sheet_skills_base = "skills.base"
sheet_skills_master = "skills.master"
sheet_skills_sub = "skills.sub"

StringAliases = tuple[str, ...]

sheet_skills_fullcode_data = "skills.fullcode.data"
sheet_knowledges_base = "knowledges.base"
sheet_knowledges_with_skill_associations_data = "knowledges.skills.data"
sheet_characteristics_master = "characteristics.master"
sheet_characteristics_base = "characteristics.base"
sheet_characteristics_matrix_data = "characteristics.matrix.data"

BaseSkillCode = int
MasterCategoryInt = int
SubCategoryInt = int
CategoryCodesTuple = tuple[MasterCategoryInt, SubCategoryInt]

BaseKnowledgeCodeInt = int
AssociatedSkillCodes = tuple[int, ...]

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCharacteristicCodeTuple = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
StrCodeStr = str


with pd.ExcelFile(XLSX_PATH) as excel:
    SKILLS_MASTER_CATEGORY_CODES: Final[dict[int, StringAliases]] = (
        load_code_to_str_aliases_from_xlsx(
            path=XLSX_PATH,
            table_name=sheet_skills_master,
            language_code=LANG_CODE,
            excel=excel,
        )
    )

    SKILLS_SUB_CATEGORY_CODES: Final[dict[int, StringAliases]] = load_code_to_str_aliases_from_xlsx(
        path=XLSX_PATH,
        table_name=sheet_skills_sub,
        language_code=LANG_CODE,
        excel=excel,
    )

    SKILLS_BASE_SKILL_CODES: Final[dict[int, StringAliases]] = load_code_to_str_aliases_from_xlsx(
        path=XLSX_PATH,
        table_name=sheet_skills_base,
        language_code=LANG_CODE,
        excel=excel,
    )

    SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES: Final[dict[BaseSkillCode, CategoryCodesTuple]] = (
        load_skill_code_to_categories_from_xlsx(
            path=XLSX_PATH,
            table_name=sheet_skills_fullcode_data,
            excel=excel,
        )
    )

    KNOWLEDGES_BASE_KNOWLEDGE_CODES: Final[dict[int, StringAliases]] = (
        load_code_to_str_aliases_from_xlsx(
            path=XLSX_PATH,
            table_name=sheet_knowledges_base,
            language_code=LANG_CODE,
            excel=excel,
        )
    )

    KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS: Final[
        dict[BaseKnowledgeCodeInt, AssociatedSkillCodes]
    ] = load_knowledge_to_skills_associations_from_xlsx(
        path=XLSX_PATH,
        table_name=sheet_knowledges_with_skill_associations_data,
        excel=excel,
    )

    CHARACTERISTICS_MASTER_CATEGORY_CODES: Final[dict[int, StringAliases]] = (
        load_code_to_str_aliases_from_xlsx(
            path=XLSX_PATH,
            table_name=sheet_characteristics_master,
            language_code=LANG_CODE,
            excel=excel,
        )
    )

    CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES: Final[
        dict[tuple[FullCharacteristicCodeTuple, StrCodeStr], StringAliases]
    ] = load_full_characteristic_code_to_str_aliases_from_xlsx(
        path=XLSX_PATH,
        table_name=sheet_characteristics_base,
        language_code=LANG_CODE,
        excel=excel,
    )

    CHARACTERISTICS_MATRIX: Final[
        dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float]
    ] = load_characteristics_matrix_from_xlsx(
        path=XLSX_PATH,
        table_name=sheet_characteristics_matrix_data,
        excel=excel,
    )
