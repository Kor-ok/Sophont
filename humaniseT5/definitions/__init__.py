from __future__ import annotations

import os
import sys
from collections.abc import Iterable
from os import PathLike
from typing import Any, Union

from humaniseT5.authoring.excel import (
    extract_licensed_material,
    open_encrypted_licensed_material,
    read_excel,
)

current_dir = os.path.dirname(os.path.abspath(__file__))

DEFINITIONS_XLSX_FILENAME = "Definitions.xlsx"
LICENSED_XLSX_FILENAME = "T5LicensedMaterial.xlsx"
ENCRYPTED_LICENSED_MATERIAL_FILENAME = "T5LicensedMaterial.bin"

FILE_PATHS = [
    DEFINITIONS_XLSX_PATH := os.path.join(current_dir, DEFINITIONS_XLSX_FILENAME),
    LICENSED_XLSX_PATH := os.path.join(current_dir, LICENSED_XLSX_FILENAME),
    ENCRYPTED_LICENSED_MATERIAL_PATH := os.path.join(current_dir, ENCRYPTED_LICENSED_MATERIAL_FILENAME),
    ]

PathOrStr = Union[str, PathLike]

def files_status_check(paths: Union[PathOrStr, Iterable[PathOrStr]]) -> None:
    if isinstance(paths, (str, PathLike)):
        paths = [paths]

    for path in paths:
        p = os.fspath(path)
        if not os.path.isfile(p):
            print(f"File at path {p} does not exist.")
            continue

        error_message = f"File at path {p} is locked by another process."
        try:
            if sys.platform.startswith("win"):
                import msvcrt

                with open(p, "r+b") as f:
                    try:
                        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                    except OSError:
                        print(error_message)
                    else:
                        try:
                            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
                        except OSError:
                            pass
            else:
                import fcntl

                with open(p, "rb") as f:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)  # type: ignore
                    except BlockingIOError:
                        print(error_message)
                    else:
                        try:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # type: ignore
                        except OSError:
                            pass
        except Exception as exc:
            print(f"Error checking file {p}: {exc}")
            # Ask user if they want to continue or exit
            while True:
                user_input = input("Do you want to continue? (y/n): ").strip().lower()
                if user_input == "y":
                    break
                elif user_input == "n":
                    print("Exiting.")
                    sys.exit(1)
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")
            

files_status_check(FILE_PATHS)

def save_encrypted_licensed_material() -> None:
    # Save the encrypted licensed material to a binary file in current_directory
    data = extract_licensed_material(LICENSED_XLSX_PATH)
    encrypted_path = ENCRYPTED_LICENSED_MATERIAL_PATH
    with open(encrypted_path, "wb") as file:
        file.write(data)


def fetch_licensed_material(
    define: dict[type, Any],
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
