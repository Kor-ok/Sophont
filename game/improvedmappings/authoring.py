from __future__ import annotations

import pandas as pd

StringAliases = tuple[str, ...]
CodeInt = int
def load_code_to_str_aliases_from_xlsx(path: str, table_name: str, language_code: str) -> dict[CodeInt, StringAliases]:
    """Load a table from an Excel file."""
    sheet_name = f"{table_name}.{language_code}"
    df = pd.read_excel(path, sheet_name=sheet_name)
    table: dict[CodeInt, StringAliases] = {}
    for _, row in df.iterrows():
        code = int(row["Code"])
        aliases = tuple(
            str(row[f"Alias{i}"]).strip()
            for i in range(1, 6)
            if pd.notna(row.get(f"Alias{i}")) and str(row[f"Alias{i}"]).strip() != ""
        )
        table[code] = aliases
    return table

BaseSkillCodeInt = int
MasterCategoryInt = int
SubCategoryInt = int
CategoryCodesTuple = tuple[MasterCategoryInt, SubCategoryInt]
def load_skill_code_to_categories_from_xlsx(path: str, table_name: str) -> dict[BaseSkillCodeInt, CategoryCodesTuple]:
    """Load skill code to categories mapping from an Excel file."""
    sheet_name = f"{table_name}"
    df = pd.read_excel(path, sheet_name=sheet_name)
    table: dict[BaseSkillCodeInt, CategoryCodesTuple] = {}
    for _, row in df.iterrows():
        base_skill_code = int(row["Base Code"])
        master_category = int(row["Master Code"])
        sub_category = int(row["Sub Code"])
        table[base_skill_code] = (master_category, sub_category)
    return table

BaseKnowledgeCodeInt = int
AssociatedSkillCodes = tuple[int, ...]
def load_knowledge_to_skills_associations_from_xlsx(path: str, table_name: str) -> dict[BaseKnowledgeCodeInt, AssociatedSkillCodes]:
    """Load knowledge to skills associations from an Excel file."""
    sheet_name = f"{table_name}"
    df = pd.read_excel(path, sheet_name=sheet_name)
    table: dict[BaseKnowledgeCodeInt, AssociatedSkillCodes] = {}
    for _, row in df.iterrows():
        knowledge_code = int(row["Base Code"])
        skill_codes = tuple(
            int(row[f"Skill Code{i}"])
            for i in range(1, 6)
            if pd.notna(row.get(f"Skill Code{i}"))
        )
        table[knowledge_code] = skill_codes
    return table

UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCharacteristicCodeTuple = tuple[UPPIndexInt, SubCodeInt, MasterCodeInt]
StrCodeStr = str
def load_full_characteristic_code_to_str_aliases_from_xlsx(path: str, table_name: str, language_code: str) -> dict[tuple[FullCharacteristicCodeTuple, StrCodeStr], StringAliases]:
    """Load full characteristic code to string alias mapping from an Excel file."""
    sheet_name = f"{table_name}.{language_code}"
    df = pd.read_excel(path, sheet_name=sheet_name)
    table: dict[tuple[FullCharacteristicCodeTuple, StrCodeStr], StringAliases] = {}
    for _, row in df.iterrows():
        upp_index = int(row["UPP Index"])
        sub_code = int(row["Sub Code"])
        master_code = int(row["Master Code"])
        str_code = str(row["Str Code"]).strip()
        aliases = tuple(
            str(row[f"Alias{i}"]).strip()
            for i in range(1, 6)
            if pd.notna(row.get(f"Alias{i}")) and str(row[f"Alias{i}"]).strip() != ""
        )
        table[((upp_index, sub_code, master_code), str_code)] = aliases
    return table

# Now for the more complex characteristics.matrix.data
# X and Y axes are both FullCharacteristicCodeTuple
# Rows 3,2,1 are UPPIndexInt, SubCodeInt, MasterCodeInt respectively
# Columns C, B, A are UPPIndexInt, SubCodeInt, MasterCodeInt respectively
# The matrix data is held from F6 (top left) to the end of the data block
# Row 4, 5 and Column D, E are ignored (headers or notes)
def load_characteristics_matrix_from_xlsx(path: str, table_name: str) -> dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float]:
    """Load characteristics matrix from an Excel file."""
    sheet_name = f"{table_name}"
    df = pd.read_excel(path, sheet_name=sheet_name, header=None)
        
    # Extract X axis codes
    x_axis_codes: list[FullCharacteristicCodeTuple] = []
    start_col = 5  # Column F (0-indexed)
    for col in range(start_col, df.shape[1]):
        upp_index = int(df.iat[2, col])
        sub_code = int(df.iat[1, col])
        master_code = int(df.iat[0, col])
        x_axis_codes.append((upp_index, sub_code, master_code))
    # Extract Y axis codes
    y_axis_codes: list[FullCharacteristicCodeTuple] = []
    start_row = 5  # Row 6 (0-indexed)
    for row in range(start_row, df.shape[0]):
        upp_index = int(df.iat[row, 2])
        sub_code = int(df.iat[row, 1])
        master_code = int(df.iat[row, 0])
        y_axis_codes.append((upp_index, sub_code, master_code))
    # Build the matrix
    matrix: dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float] = {}
    for row_idx, y_code in enumerate(y_axis_codes):
        for col_idx, x_code in enumerate(x_axis_codes):
            value = df.iat[start_row + row_idx, start_col + col_idx]
            if pd.notna(value):
                matrix[(y_code, x_code)] = float(value)
            else:
                matrix[(y_code, x_code)] = 0.0  # Default value if missing
    
    return matrix