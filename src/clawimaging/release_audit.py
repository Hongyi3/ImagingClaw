from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import yaml

from .benchmarks import load_benchmark_specs
from .datasets import load_dataset_registry
from .paths import find_repo_root


PLACEHOLDER_MARKERS = (
    "YOUR-ORG",
    "Replace",
    "replace",
    "Please update",
    "update authors",
    "your lab or org",
    "Your Institution",
)


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDER_MARKERS)
    if isinstance(value, dict):
        return any(_contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_placeholder(item) for item in value)
    return False


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be a mapping")
    return dict(payload)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must be a mapping")
    return dict(payload)


def _load_pyproject_project(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^\[project\]\n(.*?)(?:^\[|\Z)", text)
    if match is None:
        return {}
    section = match.group(1)
    payload: dict[str, str] = {}
    for field_name in ("name", "version"):
        field_match = re.search(
            rf'(?m)^{re.escape(field_name)}\s*=\s*"([^"]+)"',
            section,
        )
        if field_match is not None:
            payload[field_name] = field_match.group(1).strip()
    return payload


def audit_release_metadata(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    pyproject_path = root / "pyproject.toml"
    citation_path = root / "CITATION.cff"
    codemeta_path = root / "codemeta.json"
    zenodo_path = root / ".zenodo.json"

    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    files_payload: dict[str, dict[str, Any]] = {}
    for path, loader in (
        (citation_path, _load_yaml),
        (codemeta_path, _load_json),
        (zenodo_path, _load_json),
    ):
        try:
            payload = loader(path)
        except FileNotFoundError:
            errors.append(f"Missing required release metadata file: {path.name}")
            checks.append({"file": path.name, "status": "error", "detail": "missing"})
            continue
        except (json.JSONDecodeError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{path.name} is not parseable: {exc}")
            checks.append({"file": path.name, "status": "error", "detail": str(exc)})
            continue

        files_payload[path.name] = payload
        status = "warning" if _contains_placeholder(payload) else "ok"
        checks.append(
            {
                "file": path.name,
                "status": status,
                "detail": "contains placeholder metadata" if status == "warning" else "parseable",
            }
        )
        if status == "warning":
            warnings.append(f"{path.name} contains placeholder metadata")

    project_payload = _load_pyproject_project(pyproject_path)
    project_version = str(project_payload.get("version", "")).strip()
    project_name = str(project_payload.get("name", "")).strip()

    citation = files_payload.get("CITATION.cff", {})
    codemeta = files_payload.get("codemeta.json", {})
    zenodo = files_payload.get(".zenodo.json", {})

    title_values = {
        "CITATION.cff": str(citation.get("title", "")).strip(),
        "codemeta.json": str(codemeta.get("name", "")).strip(),
        ".zenodo.json": str(zenodo.get("title", "")).strip(),
    }
    non_empty_titles = {name: value for name, value in title_values.items() if value}
    if len(set(non_empty_titles.values())) > 1:
        warnings.append("Release metadata titles do not match across CITATION.cff, codemeta.json, and .zenodo.json")

    citation_version = str(citation.get("version", "")).strip()
    if citation_version and project_version and citation_version != project_version:
        warnings.append(
            f"CITATION.cff version `{citation_version}` does not match pyproject version `{project_version}`"
        )

    repository_values = {
        "CITATION.cff repository-code": str(citation.get("repository-code", "")).strip(),
        "CITATION.cff url": str(citation.get("url", "")).strip(),
        "codemeta.json codeRepository": str(codemeta.get("codeRepository", "")).strip(),
    }
    non_empty_repositories = {
        name: value for name, value in repository_values.items() if value
    }
    if len(set(non_empty_repositories.values())) > 1:
        warnings.append("Repository URLs do not match across release metadata files")

    if project_name:
        title_mismatch_sources = [
            name
            for name, value in non_empty_titles.items()
            if value and value.lower() != project_name.lower()
        ]
        if title_mismatch_sources:
            warnings.append(
                f"Release metadata names do not match pyproject project.name `{project_name}`"
            )

    return {
        "status": "failed" if errors else ("warning" if warnings else "passed"),
        "files": checks,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "project_name": project_name,
            "project_version": project_version,
            "title_values": non_empty_titles,
            "repository_values": non_empty_repositories,
        },
    }


def evaluate_release_readiness(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    metadata_audit = audit_release_metadata(root)

    checks = [
        {
            "name": "dataset_registry_valid",
            "status": "passed",
            "detail": f"{len(load_dataset_registry(root / 'datasets' / 'registry.yaml'))} dataset entries validated",
        },
        {
            "name": "benchmark_specs_valid",
            "status": "passed",
            "detail": f"{len(load_benchmark_specs(root / 'benchmarks' / 'specs'))} benchmark specs validated",
        },
        {
            "name": "release_metadata_audit",
            "status": metadata_audit["status"],
            "detail": (
                f"{len(metadata_audit['errors'])} errors, {len(metadata_audit['warnings'])} warnings"
            ),
        },
    ]

    overall_status = "failed" if metadata_audit["errors"] else (
        "warning" if metadata_audit["warnings"] else "passed"
    )

    return {
        "status": overall_status,
        "checks": checks,
        "metadata_audit": metadata_audit,
    }
