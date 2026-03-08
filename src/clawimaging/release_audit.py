from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Callable

import yaml

from .benchmarks import load_benchmark_specs
from .datasets import load_dataset_registry
from .paths import find_repo_root
from .release_manifest import (
    contains_placeholder,
    default_release_manifest_path,
    load_release_manifest,
    render_release_metadata,
)


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


def _compare_expected_fields(
    actual: dict[str, Any],
    expected: dict[str, Any],
    *,
    label: str,
    fields: tuple[str, ...],
) -> list[str]:
    errors: list[str] = []
    for field_name in fields:
        if actual.get(field_name) != expected.get(field_name):
            errors.append(
                f"{label} field `{field_name}` does not match release manifest rendering"
            )
    return errors


def _audit_release_manifest(root: Path) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    manifest_path = default_release_manifest_path(root)
    try:
        manifest = load_release_manifest(manifest_path)
    except (FileNotFoundError, ValueError, yaml.YAMLError) as exc:
        return None, {
            "path": str(manifest_path.relative_to(root)),
            "status": "error",
            "detail": str(exc),
        }
    return manifest, {
        "path": str(manifest_path.relative_to(root)),
        "status": "ok",
        "detail": "valid",
    }


def audit_release_metadata(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    pyproject_path = root / "pyproject.toml"
    citation_path = root / "CITATION.cff"
    codemeta_path = root / "codemeta.json"
    zenodo_path = root / ".zenodo.json"

    checks: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    release_manifest, manifest_check = _audit_release_manifest(root)
    checks.append(
        {
            "file": manifest_check["path"],
            "status": manifest_check["status"],
            "detail": manifest_check["detail"],
        }
    )
    if manifest_check["status"] != "ok":
        errors.append(f"release manifest invalid: {manifest_check['detail']}")

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
        if contains_placeholder(payload):
            errors.append(f"{path.name} contains placeholder metadata")
            checks.append(
                {
                    "file": path.name,
                    "status": "error",
                    "detail": "contains placeholder metadata",
                }
            )
            continue
        checks.append({"file": path.name, "status": "ok", "detail": "parseable"})

    project_payload = _load_pyproject_project(pyproject_path)
    project_name = str(project_payload.get("name", "")).strip()
    project_version = str(project_payload.get("version", "")).strip()

    if release_manifest is not None:
        manifest_project = dict(release_manifest["project"])
        if project_name and project_name != manifest_project["package_name"]:
            errors.append(
                "pyproject project.name does not match release manifest package_name"
            )
        if project_version and project_version != manifest_project["version"]:
            errors.append(
                "pyproject version does not match release manifest version"
            )

        expected_text = render_release_metadata(release_manifest)
        expected_citation = yaml.safe_load(expected_text["CITATION.cff"]) or {}
        expected_codemeta = json.loads(str(expected_text["codemeta.json"]))
        expected_zenodo = json.loads(str(expected_text[".zenodo.json"]))

        citation = files_payload.get("CITATION.cff", {})
        codemeta = files_payload.get("codemeta.json", {})
        zenodo = files_payload.get(".zenodo.json", {})
        errors.extend(
            _compare_expected_fields(
                citation,
                dict(expected_citation),
                label="CITATION.cff",
                fields=(
                    "title",
                    "version",
                    "license",
                    "repository-code",
                    "url",
                    "authors",
                ),
            )
        )
        errors.extend(
            _compare_expected_fields(
                codemeta,
                dict(expected_codemeta),
                label="codemeta.json",
                fields=(
                    "name",
                    "version",
                    "description",
                    "codeRepository",
                    "license",
                    "author",
                ),
            )
        )
        errors.extend(
            _compare_expected_fields(
                zenodo,
                dict(expected_zenodo),
                label=".zenodo.json",
                fields=(
                    "title",
                    "version",
                    "description",
                    "license",
                    "creators",
                ),
            )
        )
        if release_manifest["archive"]["doi_status"] == "published":
            if not citation.get("doi"):
                errors.append("CITATION.cff must include a DOI when the release manifest marks it published")
            if not codemeta.get("identifier"):
                errors.append("codemeta.json must include an identifier when the release manifest marks it published")
            if not zenodo.get("doi"):
                errors.append(".zenodo.json must include a DOI when the release manifest marks it published")

    return {
        "status": "failed" if errors else ("warning" if warnings else "passed"),
        "files": checks,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "project_name": project_name,
            "project_version": project_version,
            "release_manifest": manifest_check["path"],
            "release_manifest_status": manifest_check["status"],
        },
    }


def _run_validation_check(
    name: str,
    action: Callable[[], Any],
    *,
    detail: Callable[[Any], str],
) -> dict[str, Any]:
    try:
        payload = action()
    except (FileNotFoundError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        return {
            "name": name,
            "status": "failed",
            "detail": str(exc),
        }
    return {
        "name": name,
        "status": "passed",
        "detail": detail(payload),
    }


def evaluate_release_readiness(repo_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    metadata_audit = audit_release_metadata(root)
    manifest_check = _run_validation_check(
        "release_manifest_valid",
        lambda: load_release_manifest(root / "release" / "v1.0.yaml"),
        detail=lambda payload: f"{payload['source_path']} validated",
    )
    dataset_check = _run_validation_check(
        "dataset_registry_valid",
        lambda: load_dataset_registry(root / "datasets" / "registry.yaml"),
        detail=lambda payload: f"{len(payload)} dataset entries validated",
    )
    benchmark_check = _run_validation_check(
        "benchmark_specs_valid",
        lambda: load_benchmark_specs(root / "benchmarks" / "specs"),
        detail=lambda payload: f"{len(payload)} benchmark specs validated",
    )
    checks = [
        dataset_check,
        benchmark_check,
        manifest_check,
        {
            "name": "release_metadata_audit",
            "status": metadata_audit["status"],
            "detail": (
                f"{len(metadata_audit['errors'])} errors, "
                f"{len(metadata_audit['warnings'])} warnings"
            ),
        },
    ]
    overall_status = "passed"
    if any(check["status"] == "failed" for check in checks):
        overall_status = "failed"
    elif any(check["status"] == "warning" for check in checks):
        overall_status = "warning"

    return {
        "status": overall_status,
        "checks": checks,
        "metadata_audit": metadata_audit,
    }
