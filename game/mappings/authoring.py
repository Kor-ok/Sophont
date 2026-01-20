from __future__ import annotations

from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import Any

import pandas as pd

try:
    import numpy as np
except ModuleNotFoundError:  # pragma: no cover
    np = None  # type: ignore[assignment]

StringAliases = tuple[str, ...]
CodeInt = int


def _read_excel(
    excel_or_path: pd.ExcelFile | str,
    *,
    sheet_name: str,
    usecols: Iterable[str] | None = None,
    header: int | None = 0,
) -> pd.DataFrame:
    try:
        return pd.read_excel(excel_or_path, sheet_name=sheet_name, usecols=usecols, header=header)
    except ValueError:
        # Some workbooks/sheets may not have the expected columns; fall back to reading the sheet.
        return pd.read_excel(excel_or_path, sheet_name=sheet_name, header=header)


def _coerce_aliases_row(values: Iterable[Any]) -> StringAliases:
    aliases: list[str] = []
    for value in values:
        if value is None or pd.isna(value):
            continue
        s = str(value).strip()
        if s:
            aliases.append(s)
    return tuple(aliases)


def load_code_to_str_aliases_from_xlsx(
    path: str,
    table_name: str,
    language_code: str,
    *,
    excel: pd.ExcelFile | None = None,
) -> dict[CodeInt, StringAliases]:
    """Load code -> aliases table from an Excel file.

    If `excel` is provided, the already-open workbook is reused.
    """
    sheet_name = f"{table_name}.{language_code}"
    excel_or_path: pd.ExcelFile | str = excel if excel is not None else path

    alias_cols = [f"Alias{i}" for i in range(1, 6)]
    df = _read_excel(excel_or_path, sheet_name=sheet_name, usecols=["Code", *alias_cols])

    # Fast path: columns exist as expected.
    table: dict[CodeInt, StringAliases] = {}
    code_series = df.get("Code")
    if code_series is None:
        return table

    existing_alias_cols = [c for c in alias_cols if c in df.columns]
    for row in df[["Code", *existing_alias_cols]].itertuples(index=False, name=None):
        code = int(row[0])
        table[code] = _coerce_aliases_row(row[1:])
    return table


BaseSkillCodeInt = int
MasterCategoryInt = int
SubCategoryInt = int
CategoryCodesTuple = tuple[MasterCategoryInt, SubCategoryInt]


def load_skill_code_to_categories_from_xlsx(
    path: str,
    table_name: str,
    *,
    excel: pd.ExcelFile | None = None,
) -> dict[BaseSkillCodeInt, CategoryCodesTuple]:
    """Load skill base-code -> (master, sub) categories mapping from an Excel file."""
    sheet_name = f"{table_name}"
    excel_or_path: pd.ExcelFile | str = excel if excel is not None else path

    df = _read_excel(
        excel_or_path,
        sheet_name=sheet_name,
        usecols=["Base Code", "Master Code", "Sub Code"],
    )
    table: dict[BaseSkillCodeInt, CategoryCodesTuple] = {}
    for base_code, master_code, sub_code in df.itertuples(index=False, name=None):
        table[int(base_code)] = (int(master_code), int(sub_code))
    return table


BaseKnowledgeCodeInt = int
AssociatedSkillCodes = tuple[int, ...]


def load_knowledge_to_skills_associations_from_xlsx(
    path: str,
    table_name: str,
    *,
    excel: pd.ExcelFile | None = None,
) -> dict[BaseKnowledgeCodeInt, AssociatedSkillCodes]:
    """Load knowledge base-code -> associated skill codes from an Excel file."""
    sheet_name = f"{table_name}"
    excel_or_path: pd.ExcelFile | str = excel if excel is not None else path

    skill_cols = [f"Skill Code{i}" for i in range(1, 6)]
    df = _read_excel(excel_or_path, sheet_name=sheet_name, usecols=["Base Code", *skill_cols])
    existing_skill_cols = [c for c in skill_cols if c in df.columns]

    table: dict[BaseKnowledgeCodeInt, AssociatedSkillCodes] = {}
    for row in df[["Base Code", *existing_skill_cols]].itertuples(index=False, name=None):
        base_code = int(row[0])
        codes: list[int] = []
        for value in row[1:]:
            if value is None or pd.isna(value):
                continue
            codes.append(int(value))
        table[base_code] = tuple(codes)
    return table


UPPIndexInt = int
SubCodeInt = int
MasterCodeInt = int
FullCharacteristicCodeTuple = tuple[
    UPPIndexInt, SubCodeInt, MasterCodeInt
]  # FullCode = tuple[int, int, int]

CanonicalStrKey = str
AliasMap = Mapping[CanonicalStrKey, StringAliases]
AliasMappedFullCode = tuple[AliasMap, FullCharacteristicCodeTuple]


def load_full_characteristic_code_to_str_aliases_from_xlsx(
    path: str,
    table_name: str,
    language_code: str,
    *,
    excel: pd.ExcelFile | None = None,
) -> tuple[AliasMappedFullCode, ...]:
    """Load ((upp, sub, master), str_code) -> aliases mapping from an Excel file."""
    sheet_name = f"{table_name}.{language_code}"
    excel_or_path: pd.ExcelFile | str = excel if excel is not None else path

    alias_cols = [f"Alias{i}" for i in range(1, 6)]
    df = _read_excel(
        excel_or_path,
        sheet_name=sheet_name,
        usecols=["UPP Index", "Sub Code", "Master Code", "Str Code", *alias_cols],
    )
    existing_alias_cols = [c for c in alias_cols if c in df.columns]

    entries: list[AliasMappedFullCode] = []
    needed = ["UPP Index", "Sub Code", "Master Code", "Str Code", *existing_alias_cols]
    for row in df[needed].itertuples(index=False, name=None):
        upp_index = int(row[0])
        sub_code = int(row[1])
        master_code = int(row[2])
        str_code = str(row[3]).strip()
        aliases = _coerce_aliases_row(row[4:])
        entries.append((MappingProxyType({str_code: aliases}), (upp_index, sub_code, master_code)))
    return tuple(entries)


# Now for the more complex characteristics.matrix.data
# X and Y axes are both FullCharacteristicCodeTuple
# Rows 3,2,1 are UPPIndexInt, SubCodeInt, MasterCodeInt respectively
# Columns C, B, A are UPPIndexInt, SubCodeInt, MasterCodeInt respectively
# The matrix data is held from F6 (top left) to the end of the data block
# Row 4, 5 and Column D, E are ignored (headers or notes)


def load_characteristics_matrix_from_xlsx(
    path: str,
    table_name: str,
    *,
    excel: pd.ExcelFile | None = None,
) -> dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float]:
    """Load characteristics matrix from an Excel file."""
    sheet_name = f"{table_name}"
    excel_or_path: pd.ExcelFile | str = excel if excel is not None else path
    df = _read_excel(excel_or_path, sheet_name=sheet_name, header=None)

    start_col = 5  # Column F (0-indexed)
    start_row = 5  # Row 6 (0-indexed)

    # Use NumPy when available to minimize DataFrame indexing overhead.
    if np is not None:
        arr = df.to_numpy(copy=False)

        x_meta = arr[0:3, start_col:]
        x_axis_codes = [
            (int(upp), int(sub), int(master))
            for master, sub, upp in zip(x_meta[0], x_meta[1], x_meta[2])
        ]

        y_meta = arr[start_row:, 0:3]
        y_axis_codes = [
            (int(upp), int(sub), int(master))
            for master, sub, upp in zip(y_meta[:, 0], y_meta[:, 1], y_meta[:, 2])
        ]

        values = arr[start_row:, start_col:]
        # Default value is 1.0 where missing.
        values_f = np.where(pd.isna(values), 1.0, values).astype(float, copy=False)

        matrix: dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float] = {}
        for row_idx, y_code in enumerate(y_axis_codes):
            row_vals = values_f[row_idx]
            for col_idx, x_code in enumerate(x_axis_codes):
                matrix[(y_code, x_code)] = float(row_vals[col_idx])
        return matrix

    # Fallback path (no NumPy) - still correct, just slower.
    x_axis_codes: list[FullCharacteristicCodeTuple] = []
    for col in range(start_col, df.shape[1]):
        upp_index = int(df.iat[2, col])
        sub_code = int(df.iat[1, col])
        master_code = int(df.iat[0, col])
        x_axis_codes.append((upp_index, sub_code, master_code))

    y_axis_codes: list[FullCharacteristicCodeTuple] = []
    for row in range(start_row, df.shape[0]):
        upp_index = int(df.iat[row, 2])
        sub_code = int(df.iat[row, 1])
        master_code = int(df.iat[row, 0])
        y_axis_codes.append((upp_index, sub_code, master_code))

    matrix: dict[tuple[FullCharacteristicCodeTuple, FullCharacteristicCodeTuple], float] = {}
    for row_idx, y_code in enumerate(y_axis_codes):
        for col_idx, x_code in enumerate(x_axis_codes):
            value = df.iat[start_row + row_idx, start_col + col_idx]
            matrix[(y_code, x_code)] = float(value) if pd.notna(value) else 1.0
    return matrix
