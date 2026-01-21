from __future__ import annotations

import importlib
import os
from types import MappingProxyType

current_dir = os.path.dirname(os.path.abspath(__file__))

XLSX_FILENAME = "T5Mappings.xlsx"
XLSX_PATH = os.path.join(current_dir, XLSX_FILENAME)

does_excel_file_exist = os.path.isfile(XLSX_PATH)
if not does_excel_file_exist:
    raise FileNotFoundError(f"Could not find expected mappings file at path: {XLSX_PATH}")

_excel = importlib.import_module("game.mappings.init_mappings")


SKILLS_MASTER_CATEGORY_CODES = MappingProxyType(dict(_excel.SKILLS_MASTER_CATEGORY_CODES))
SKILLS_SUB_CATEGORY_CODES = MappingProxyType(dict(_excel.SKILLS_SUB_CATEGORY_CODES))
SKILLS_BASE_SKILL_CODES = MappingProxyType(dict(_excel.SKILLS_BASE_SKILL_CODES))
SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES = (_excel.SKILLS_MAPPING_BASE_SKILL_CODE_TO_CATEGORIES) # Keep the shape of the data tuple[AliasMappedFullCode, ...]

KNOWLEDGES_BASE_KNOWLEDGE_CODES = MappingProxyType(dict(_excel.KNOWLEDGES_BASE_KNOWLEDGE_CODES))
KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS = MappingProxyType(dict(_excel.KNOWLEDGES_DEFAULT_KNOWLEDGE_TO_SKILLS_ASSOCIATIONS))
KNOWLEDGES_FULL_CODE_TO_STR_ALIASES = (_excel.KNOWLEDGES_FULL_CODE_TO_STR_ALIASES) # Keep the shape of the data tuple[AliasMappedFullCode, ...]

CHARACTERISTICS_MASTER_CATEGORY_CODES = MappingProxyType(dict(_excel.CHARACTERISTICS_MASTER_CATEGORY_CODES))
CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES = (_excel.CHARACTERISTICS_BASE_FULL_CODE_TO_STR_ALIASES) # Keep the shape of the data tuple[AliasMappedFullCode, ...]
CHARACTERISTICS_MATRIX = MappingProxyType(dict(_excel.CHARACTERISTICS_MATRIX))