from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the repository root from a file or directory within the tree."""

    current = (start or Path(__file__).resolve()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in [current, *current.parents]:
        if (candidate / "skills" / "catalog.json").exists():
            return candidate
    raise FileNotFoundError("Could not locate repository root containing skills/catalog.json")
