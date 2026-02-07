from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from typing_extensions import TypeAlias

from humaniseT5.authoring.excel import (
    extract_licensed_material,
    open_encrypted_licensed_material,
    read_excel,
)

CanonicalStrKey: TypeAlias = str
CanonicalCodeInt: TypeAlias = int
StringAliases: TypeAlias = list[str]
AliasMap: TypeAlias = Mapping[CanonicalStrKey, StringAliases]

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

Domain: TypeAlias = str
DomainField: TypeAlias = str


def fetch_definitions(define: dict[Domain, list[DomainField]], language: str = "en") -> Any:
    definitions = {}
    for domain in define.keys():
        target_sheet = f"{domain}.Aliases"
        try:
            df = read_excel(DEFINITIONS_XLSX_PATH, sheet_name=target_sheet)
            # Column with header "code" has tuple[int, ...]
            # If column with header "lang" = language, then
            # column with header "canonical" is CanonicalStrKey and
            # column with header "alias" StringAliases

            for _, row in df.iterrows():
                code = row.get("code")
                lang = row.get("lang")
                canonical = row.get("canonical")
                alias = row.get("alias")

                # For the definitions[domain] we create a list of dict code: AliasMap
                if lang == language:
                    if domain not in definitions:
                        definitions[domain] = []
                    definitions[domain].append(
                        {
                            "code": code,
                            "canonical": canonical,
                            "alias": alias.split(",") if isinstance(alias, str) else [],
                        }
                    )

        except Exception as e:
            print(f"Error reading sheet '{domain}': {e}")

        for field in define[domain]:
            target_sheet = f"{domain}.{field}"
            try:
                df = read_excel(DEFINITIONS_XLSX_PATH, sheet_name=target_sheet)
                # Column with header "{field}" has integer value
                # If column with header "lang" = language, then
                # column with header "canonical" is CanonicalStrKey and
                # column with header "alias" StringAliases
                for _, row in df.iterrows():
                    value = row.get(field)
                    lang = row.get("lang")
                    canonical = row.get("canonical")
                    alias = row.get("alias")

                    if lang == language:
                        if domain not in definitions:
                            definitions[domain] = []
                        definitions[domain].append(
                            {
                                field: value,
                                "canonical": canonical,
                                "alias": alias.split(",") if isinstance(alias, str) else [],
                            }
                        )
            except Exception as e:
                print(f"Error reading sheet '{domain}.{field}': {e}")

    return definitions


def save_encrypted_licensed_material() -> None:
    # Save the encrypted licensed material to a binary file in current_directory
    data = extract_licensed_material(LICENSED_XLSX_PATH)
    encrypted_path = ENCRYPTED_LICENSED_MATERIAL_PATH
    with open(encrypted_path, "wb") as file:
        file.write(data)


def fetch_licensed_material(define: dict[Domain, list[DomainField]], language: str = "en") -> Any:
    licensed_material: list[dict[str, Any]] = []

    with open(ENCRYPTED_LICENSED_MATERIAL_PATH, "rb") as f:
        encrypted_data = f.read()

    with open_encrypted_licensed_material(encrypted_data) as xls:
        for domain in define.keys():
            target_sheet = f"{domain}.Aliases"
            try:
                df = read_excel(xls, sheet_name=target_sheet)
                # Column with header "code" has tuple[int, ...]
                # If column with header "lang" = language, then
                # column with header "text" is the licensed material

                for _, row in df.iterrows():
                    code = row.get("code")
                    lang = row.get("lang")
                    text = row.get("text")

                    if lang == language:
                        licensed_material.append(
                            {
                                "code": code,
                                "text": text,
                            }
                        )

            except Exception as e:
                print(f"Error reading sheet '{target_sheet}': {e}")

            for field in define[domain]:
                target_sheet = f"{domain}.{field}"
                try:
                    df = read_excel(xls, sheet_name=target_sheet)
                    # Column with header "{field}" has integer value
                    # If column with header "lang" = language, then
                    # column with header "text" is the licensed material
                    for _, row in df.iterrows():
                        value = row.get(field)
                        lang = row.get("lang")
                        text = row.get("text")

                        if lang == language:
                            licensed_material.append(
                                {
                                    field: value,
                                    "text": text,
                                }
                            )
                except Exception as e:
                    print(f"Error reading sheet '{target_sheet}': {e}")

    return licensed_material
