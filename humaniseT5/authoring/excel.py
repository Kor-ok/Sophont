from __future__ import annotations

import io
from os import getenv
from pathlib import Path

import pandas as pd
from cryptography.fernet import Fernet
from dotenv import load_dotenv

root_dir = Path(__file__).parent.parent.parent
dotenv_path = root_dir / ".env"

TOKEN_KEY = "LICENSE_TOKEN"


def _load_fernet() -> Fernet:
    """Load the cryptographic key from .env and return a Fernet instance."""
    load_dotenv(dotenv_path)
    key = getenv(TOKEN_KEY)
    if key is None:
        raise ValueError(
            f"Environment variable {TOKEN_KEY} not found. " "Please set it in your .env file."
        )
    return Fernet(key)


def read_excel(excel_or_path: pd.ExcelFile | str, *, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(excel_or_path, sheet_name=sheet_name)


def extract_licensed_material(excel_path: str | Path) -> bytes:
    """Encrypt the raw bytes of an Excel file, preserving all sheet structure."""
    fernet = _load_fernet()
    raw = Path(excel_path).read_bytes()
    return fernet.encrypt(raw)


def read_encrypted_licensed_material(encrypted_data: bytes, *, sheet_name: str) -> pd.DataFrame:
    """Decrypt an encrypted Excel blob and return a single sheet as a DataFrame."""
    fernet = _load_fernet()
    decrypted = fernet.decrypt(encrypted_data)
    return pd.read_excel(io.BytesIO(decrypted), sheet_name=sheet_name)


def open_encrypted_licensed_material(encrypted_data: bytes) -> pd.ExcelFile:
    """Decrypt an encrypted Excel blob and return an open ExcelFile for
    sheet-by-sheet access (caller should use ``with`` or close explicitly).
    """
    fernet = _load_fernet()
    decrypted = fernet.decrypt(encrypted_data)
    return pd.ExcelFile(io.BytesIO(decrypted))
