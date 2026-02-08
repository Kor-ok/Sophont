from __future__ import annotations

import os
import re
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import pandas as pd
from typing_extensions import TypeAlias

from humaniseT5.authoring.excel import (
    extract_licensed_material,
    open_encrypted_licensed_material,
    read_excel,
)

current_dir = os.path.dirname(os.path.abspath(__file__))

DEFINITIONS_XLSX_FILENAME = "Definitions.xlsx"
DEFINITIONS_XLSX_PATH = os.path.join(current_dir, DEFINITIONS_XLSX_FILENAME)

LICENSED_XLSX_FILENAME = "T5LicensedMaterial.xlsx"
LICENSED_XLSX_PATH = os.path.join(current_dir, LICENSED_XLSX_FILENAME)

ENCRYPTED_LICENSED_MATERIAL_FILENAME = "T5LicensedMaterial.bin"
ENCRYPTED_LICENSED_MATERIAL_PATH = os.path.join(current_dir, ENCRYPTED_LICENSED_MATERIAL_FILENAME)

definitions_file_exists = os.path.isfile(DEFINITIONS_XLSX_PATH)
if not definitions_file_exists:
    raise FileNotFoundError(
        f"Could not find expected mappings file at path: {DEFINITIONS_XLSX_PATH}"
    )

licensed_file_exists = os.path.isfile(LICENSED_XLSX_PATH)
if not licensed_file_exists:
    raise FileNotFoundError(
        f"Could not find expected licensed material file at path: {LICENSED_XLSX_PATH}"
    )

encrypted_file_exists = os.path.isfile(ENCRYPTED_LICENSED_MATERIAL_PATH)
if not encrypted_file_exists:
    print(
        f"Encrypted licensed material not found at path: {ENCRYPTED_LICENSED_MATERIAL_PATH}. You can generate it by running this script directly."
    )

def save_encrypted_licensed_material() -> None:
    # Save the encrypted licensed material to a binary file in current_directory
    data = extract_licensed_material(LICENSED_XLSX_PATH)
    encrypted_path = ENCRYPTED_LICENSED_MATERIAL_PATH
    with open(encrypted_path, "wb") as file:
        file.write(data)

def _convert_type_to_str_name(t: type) -> str:
    """Convert a type object to a string representation, e.g. int -> 'int'."""
    if hasattr(t, "__name__"):
        return t.__name__
    else:
        return str(t)

def _convert_comma_delimited_str_to_tuple(s: Any, type: type | None = None) -> tuple[Any, ...]:
    """Convert a comma-delimited string like "1, 0, 1" into a tuple of a sensible type.

    Rules:
    - If `s` is already a tuple/list, return a tuple(s).
    - If `s` is not a string, return a single-element tuple `(s,)`.
    - Ignore empty items produced by consecutive commas or surrounding whitespace.
    - If `type` is provided, coerce every item to that type.
    - If `type` is not provided, infer the most specific common type across all items
      using these checks (in order): all-int -> int, all-float-or-int -> float,
      all-bool -> bool, otherwise str.
    """
    # If Pandas is providing a nan, convert to empty tuple
    if isinstance(s, float) and pd.isna(s):
        return tuple()
    if isinstance(s, (tuple, list)):
        return tuple(s)
    if not isinstance(s, str):
        return (s,)

    parts = [p.strip() for p in s.split(",")]
    parts = [p for p in parts if p != ""]
    if not parts:
        return tuple()

    int_re = re.compile(r"^[+-]?\d+$")
    float_re = re.compile(r"^[+-]?(?:\d+\.\d*|\.\d+|\d+[eE][+-]?\d+)$")
    bool_vals = {"true", "false", "yes", "no", "1", "0"}

    def is_int(x: str) -> bool:
        return bool(int_re.match(x))

    def is_float(x: str) -> bool:
        return bool(float_re.match(x)) or is_int(x)

    def is_bool(x: str) -> bool:
        return x.lower() in bool_vals

    # If caller provided a type, use it
    if type is not None:
        if type is int:
            return tuple(int(p) for p in parts)
        if type is float:
            return tuple(float(p) for p in parts)
        if type is bool:
            return tuple(p.lower() in ("true", "1", "yes") for p in parts)
        return tuple(p for p in parts)

    # Infer a common type across all parts
    if all(is_int(p) for p in parts):
        return tuple(int(p) for p in parts)
    if all(is_float(p) for p in parts):
        return tuple(float(p) for p in parts)
    if all(is_bool(p) for p in parts):
        return tuple(p.lower() in ("true", "1", "yes") for p in parts)

    return tuple(p for p in parts)


CanonicalStrKey: TypeAlias = str
StringAliases: TypeAlias = tuple[str, ...]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]
Signature: TypeAlias = tuple[int, ...]
SheetName: TypeAlias = str
def fetch_definitions(
        classes: dict[type, Any], 
        language: str = "en"
        ) -> Any: # dict[type, list[dict[SheetName, AliasMap]]]
    
    df_sheet_names = read_excel(DEFINITIONS_XLSX_PATH) # DataFrame
    # Build a one-pass mapping from the sheet base (before first '.') -> list of sheet names.
    # This avoids scanning the entire DataFrame for every domain (avoids O(D*N)).
    sheet_names = (
        df_sheet_names["sheet_name"].dropna().astype(str).str.strip().unique().tolist()
    )
    base_map: dict[str, list[str]] = {}
    for s in sheet_names:
        base = s.split(".", 1)[0]
        base_map.setdefault(base, []).append(s)

    definitions = {}
    for domain in classes.keys():
        matches = base_map.get(_convert_type_to_str_name(domain))
        # Master sheets are those that match the domain name exactly (e.g. "CharacteristicCode" for the CharacteristicCode class).
        # Signature sheets are those that end with ".signature" (e.g. "CharacteristicCode.signature").
        # Field sheets are those that match the pattern "{Domain}.{FieldName}" (e.g. "CharacteristicCode.upp_position").
        if not matches:
            print(f"Warning: No sheets found for domain '{domain}' (searched for base '{_convert_type_to_str_name(domain)}').")
            continue
        master_sheets = next((s for s in matches if s == _convert_type_to_str_name(domain)), None)
        signature_sheets = next((s for s in matches if s.endswith(".signature")), None)
        field_sheets = [s for s in matches if s not in (master_sheets, signature_sheets)]
        # pprint(f"Domain '{domain}': master_sheet={master_sheet}, signature_sheet={signature_sheet}, field_sheets={field_sheets}")
        # For signature and field sheets, we expect columns: 'lang', 'canonical', 'aliases'
        for signature_sheet in [signature_sheets]:
            if not signature_sheet:
                continue
            df = read_excel(DEFINITIONS_XLSX_PATH, sheet_name=signature_sheet)
            for _, row in df.iterrows():
                signature = row.get("signature")
                lang = row.get("lang")
                canonical = row.get("canonical")
                aliases = row.get("aliases")
                if lang == language:
                    definitions.setdefault(domain, []).append(
                        {
                            signature_sheet.split(".", 1)[1]: OrderedDict({
                                "signature": _convert_comma_delimited_str_to_tuple(signature, type=int),
                                "canonical": canonical,
                                "aliases": _convert_comma_delimited_str_to_tuple(aliases, type=str),
                            })
                        }
                    )
        for field_sheet in field_sheets:
            if not field_sheet:
                continue
            df = read_excel(DEFINITIONS_XLSX_PATH, sheet_name=field_sheet)
            for _, row in df.iterrows():
                lang = row.get("lang")
                canonical = row.get("canonical")
                aliases = row.get("aliases")
                if lang == language and canonical is not None:
                    definitions.setdefault(domain, []).append(
                        {
                            field_sheet.split(".", 1)[1]: OrderedDict({
                                "canonical": canonical,
                                "aliases": _convert_comma_delimited_str_to_tuple(aliases, type=str),
                            })
                        }
                    )            
    return definitions

def fetch_licensed_material(
    define: dict[str, Any],
    language: str = "en",
) -> Any:
    """Load licensed descriptive text from the encrypted workbook.

    *define* maps class names to ``ComponentClassInfo`` named-tuples (or any
    object exposing a ``.fields`` dict of ``{field_name: type}``).
    """
    licensed_material: list[dict[str, Any]] = []

    with open(ENCRYPTED_LICENSED_MATERIAL_PATH, "rb") as f:
        encrypted_data = f.read()

    with open_encrypted_licensed_material(encrypted_data) as xls:
        for domain, info in define.items():
            # ---- 1. Per-class sheet ({Domain}.Aliases) ----
            target_sheet = f"{domain}.Aliases"
            try:
                df = read_excel(xls, sheet_name=target_sheet)
                for _, row in df.iterrows():
                    code = row.get("code")
                    lang = row.get("lang")
                    text = row.get("text")

                    if lang == language:
                        licensed_material.append({"code": code, "text": text})
            except Exception as e:
                print(f"Error reading sheet '{target_sheet}': {e}")

            # ---- 2. Per-field sheets ({Domain}.{TypeName}) ----
            for field_name, field_type in info.fields.items():
                type_name = getattr(field_type, "__name__", str(field_type))
                target_sheet = f"{domain}.{type_name}"
                try:
                    df = read_excel(xls, sheet_name=target_sheet)
                    for _, row in df.iterrows():
                        value = row.get(type_name)
                        lang = row.get("lang")
                        text = row.get("text")

                        if lang == language:
                            licensed_material.append({field_name: value, "text": text})
                except Exception as e:
                    print(f"Error reading sheet '{target_sheet}': {e}")

    return licensed_material
