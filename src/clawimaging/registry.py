from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .paths import find_repo_root


SkillRecord = dict[str, Any]


def _as_mapping(data: object, *, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a mapping")
    return dict(data)


def _as_skill_list(data: object, *, context: str) -> list[SkillRecord]:
    if data is None:
        return []
    if not isinstance(data, list):
        raise ValueError(f"{context} must be a list")
    skills: list[SkillRecord] = []
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"{context}[{index}] must be a mapping")
        skills.append(dict(item))
    return skills


def load_catalog(catalog_path: str | Path | None = None) -> dict[str, Any]:
    path = Path(catalog_path) if catalog_path else find_repo_root() / "skills" / "catalog.json"
    with path.open("r", encoding="utf-8") as handle:
        payload = _as_mapping(json.load(handle), context="skills catalog")
    payload["skills"] = _as_skill_list(payload.get("skills", []), context="skills catalog.skills")
    return payload


def list_skills(catalog_path: str | Path | None = None) -> list[SkillRecord]:
    return list(load_catalog(catalog_path).get("skills", []))


def get_skill(name_or_alias: str, catalog_path: str | Path | None = None) -> SkillRecord | None:
    name_or_alias = name_or_alias.strip().lower()
    for skill in list_skills(catalog_path):
        if skill.get("name", "").lower() == name_or_alias:
            return skill
        if (skill.get("cli_alias") or "").lower() == name_or_alias:
            return skill
    return None
