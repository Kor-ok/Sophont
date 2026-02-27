from __future__ import annotations

from pathlib import Path

_root_dir = None

SEARCH_FOR = ".venv"

def find_root(match: str =SEARCH_FOR) -> Path:
    directories = Path(__file__).resolve().parents

    for directory in directories:
        if (directory / match).exists():
            global _root_dir
            _root_dir = directory
            break
    
    if _root_dir is None:
        raise FileNotFoundError(f"Could not find a directory containing '{match}' in the parent directories of {__file__}")

    return _root_dir

def get_all_folders_from(dir: Path | None = None) -> list[Path]:
    global _root_dir
    if _root_dir is None:
        raise ValueError("Root directory has not been found. Call find_root() first.")
    
    if dir is None:
        dir = _root_dir
        
    result: list[Path] = []
    result.append(dir)
    # Get only the folder names down the root directory excluding folders that start with a dot (like .venv) or underscore (like __pycache__)
    
    for item in dir.iterdir():
        if item.is_dir() and not item.name.startswith((".", "_")):
            result.append(item)
            for subitem in item.rglob("*"):
                if subitem.is_dir() and not subitem.name.startswith((".", "_")):
                    result.append(subitem)

    return result

REPO_ROOT = find_root()
REPO_DIRS = get_all_folders_from()
