from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import find_repo_root


def load_catalog(catalog_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(catalog_path) if catalog_path else find_repo_root() / "skills" / "catalog.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_skills(catalog_path: str | Path | None = None) -> list[dict[str, Any]]:
    return list(load_catalog(catalog_path).get("skills", []))


def get_skill(name_or_alias: str, catalog_path: str | Path | None = None) -> dict[str, Any] | None:
    name_or_alias = name_or_alias.strip().lower()
    for skill in list_skills(catalog_path):
        if skill.get("name", "").lower() == name_or_alias:
            return skill
        if (skill.get("cli_alias") or "").lower() == name_or_alias:
            return skill
    return None
