from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

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
VALID_DOI_STATUSES = {"pending", "published"}


def _as_mapping(data: Any, *, context: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError(f"{context} must be a mapping")
    return dict(data)


def _as_non_empty_string(value: Any, *, context: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{context} must not be blank")
    return text


def _as_string_list(values: Any, *, context: str) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{context} must be a list")
    result: list[str] = []
    for index, value in enumerate(values):
        result.append(_as_non_empty_string(value, context=f"{context}[{index}]"))
    if not result:
        raise ValueError(f"{context} must not be empty")
    return result


def contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return any(marker in value for marker in PLACEHOLDER_MARKERS)
    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_placeholder(item) for item in value)
    return False


def default_release_manifest_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    return root / "release" / "v1.0.yaml"


def _validate_project(project_raw: Any) -> dict[str, Any]:
    project = _as_mapping(project_raw, context="release.project")
    required_fields = (
        "title",
        "package_name",
        "version",
        "description",
        "repository_url",
        "license",
        "keywords",
    )
    missing = [field_name for field_name in required_fields if field_name not in project]
    if missing:
        raise ValueError(f"release.project missing required fields: {', '.join(missing)}")
    return {
        "title": _as_non_empty_string(project["title"], context="release.project.title"),
        "package_name": _as_non_empty_string(
            project["package_name"],
            context="release.project.package_name",
        ),
        "version": _as_non_empty_string(project["version"], context="release.project.version"),
        "description": _as_non_empty_string(
            project["description"],
            context="release.project.description",
        ),
        "repository_url": _as_non_empty_string(
            project["repository_url"],
            context="release.project.repository_url",
        ),
        "license": _as_non_empty_string(project["license"], context="release.project.license"),
        "keywords": _as_string_list(project["keywords"], context="release.project.keywords"),
    }


def _validate_maintainers(maintainers_raw: Any) -> list[dict[str, Any]]:
    if not isinstance(maintainers_raw, list):
        raise ValueError("release.maintainers must be a list")
    if not maintainers_raw:
        raise ValueError("release.maintainers must not be empty")

    maintainers: list[dict[str, Any]] = []
    for index, maintainer_raw in enumerate(maintainers_raw):
        payload = _as_mapping(maintainer_raw, context=f"release.maintainers[{index}]")
        required_fields = ("display_name", "family_names", "affiliation", "email", "github")
        missing = [field_name for field_name in required_fields if field_name not in payload]
        if missing:
            raise ValueError(
                f"release.maintainers[{index}] missing required fields: {', '.join(missing)}"
            )
        maintainers.append(
            {
                "display_name": _as_non_empty_string(
                    payload["display_name"],
                    context=f"release.maintainers[{index}].display_name",
                ),
                "family_names": _as_non_empty_string(
                    payload["family_names"],
                    context=f"release.maintainers[{index}].family_names",
                ),
                "given_names": str(payload.get("given_names", "")).strip(),
                "affiliation": _as_non_empty_string(
                    payload["affiliation"],
                    context=f"release.maintainers[{index}].affiliation",
                ),
                "email": _as_non_empty_string(
                    payload["email"],
                    context=f"release.maintainers[{index}].email",
                ),
                "github": _as_non_empty_string(
                    payload["github"],
                    context=f"release.maintainers[{index}].github",
                ),
            }
        )
    return maintainers


def _validate_archive(archive_raw: Any) -> dict[str, Any]:
    archive = _as_mapping(archive_raw, context="release.archive")
    required_fields = ("doi_status", "release_tag", "notes")
    missing = [field_name for field_name in required_fields if field_name not in archive]
    if missing:
        raise ValueError(f"release.archive missing required fields: {', '.join(missing)}")

    doi_status = _as_non_empty_string(archive["doi_status"], context="release.archive.doi_status")
    if doi_status not in VALID_DOI_STATUSES:
        allowed = ", ".join(sorted(VALID_DOI_STATUSES))
        raise ValueError(f"release.archive.doi_status must be one of: {allowed}")

    doi_raw = archive.get("doi")
    doi = None if doi_raw in (None, "") else _as_non_empty_string(doi_raw, context="release.archive.doi")
    if doi_status == "published" and doi is None:
        raise ValueError("release.archive.doi must be set when doi_status is `published`")

    return {
        "doi_status": doi_status,
        "doi": doi,
        "release_tag": _as_non_empty_string(
            archive["release_tag"],
            context="release.archive.release_tag",
        ),
        "notes": _as_string_list(archive["notes"], context="release.archive.notes"),
    }


def _resolve_required_path(repo_root: Path, relative_path: str, *, context: str) -> str:
    path = (repo_root / relative_path).resolve()
    if not path.exists():
        raise ValueError(f"{context} references missing path: {relative_path}")
    return relative_path


def _validate_packages(packages_raw: Any, *, repo_root: Path) -> dict[str, dict[str, Any]]:
    packages = _as_mapping(packages_raw, context="release.packages")
    required_sections = ("software", "benchmark")
    missing = [section_name for section_name in required_sections if section_name not in packages]
    if missing:
        raise ValueError(f"release.packages missing required sections: {', '.join(missing)}")

    software = _as_mapping(packages["software"], context="release.packages.software")
    software_required_fields = ("title", "summary", "include_paths")
    software_missing = [
        field_name for field_name in software_required_fields if field_name not in software
    ]
    if software_missing:
        raise ValueError(
            "release.packages.software missing required fields: "
            + ", ".join(software_missing)
        )
    software_include_paths = _as_string_list(
        software["include_paths"],
        context="release.packages.software.include_paths",
    )

    benchmark = _as_mapping(packages["benchmark"], context="release.packages.benchmark")
    benchmark_required_fields = ("title", "summary", "default_benchmark_spec")
    benchmark_missing = [
        field_name for field_name in benchmark_required_fields if field_name not in benchmark
    ]
    if benchmark_missing:
        raise ValueError(
            "release.packages.benchmark missing required fields: "
            + ", ".join(benchmark_missing)
        )

    return {
        "software": {
            "title": _as_non_empty_string(
                software["title"],
                context="release.packages.software.title",
            ),
            "summary": _as_non_empty_string(
                software["summary"],
                context="release.packages.software.summary",
            ),
            "include_paths": [
                _resolve_required_path(
                    repo_root,
                    relative_path,
                    context="release.packages.software.include_paths",
                )
                for relative_path in software_include_paths
            ],
        },
        "benchmark": {
            "title": _as_non_empty_string(
                benchmark["title"],
                context="release.packages.benchmark.title",
            ),
            "summary": _as_non_empty_string(
                benchmark["summary"],
                context="release.packages.benchmark.summary",
            ),
            "default_benchmark_spec": _resolve_required_path(
                repo_root,
                _as_non_empty_string(
                    benchmark["default_benchmark_spec"],
                    context="release.packages.benchmark.default_benchmark_spec",
                ),
                context="release.packages.benchmark.default_benchmark_spec",
            ),
        },
    }


def load_release_manifest(path: str | Path | None = None) -> dict[str, Any]:
    manifest_path = Path(path).resolve() if path is not None else default_release_manifest_path()
    repo_root = find_repo_root(manifest_path)
    with manifest_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    manifest = _as_mapping(payload, context="release manifest")

    required_sections = ("project", "maintainers", "archive", "packages")
    missing = [section_name for section_name in required_sections if section_name not in manifest]
    if missing:
        raise ValueError(f"release manifest missing required sections: {', '.join(missing)}")

    normalized = {
        "project": _validate_project(manifest["project"]),
        "maintainers": _validate_maintainers(manifest["maintainers"]),
        "archive": _validate_archive(manifest["archive"]),
        "packages": _validate_packages(manifest["packages"], repo_root=repo_root),
        "source_path": str(manifest_path.relative_to(repo_root)),
    }
    if contains_placeholder(normalized):
        raise ValueError("release manifest contains placeholder values")
    return normalized


def _render_citation_author(maintainer: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "family-names": maintainer["family_names"],
        "alias": maintainer["github"],
        "email": maintainer["email"],
        "affiliation": maintainer["affiliation"],
    }
    if maintainer["given_names"]:
        payload["given-names"] = maintainer["given_names"]
    return payload


def _render_codemeta_author(maintainer: dict[str, Any]) -> dict[str, Any]:
    return {
        "@type": "Person",
        "name": maintainer["display_name"],
        "email": maintainer["email"],
        "affiliation": {
            "@type": "Organization",
            "name": maintainer["affiliation"],
        },
        "identifier": f"https://github.com/{maintainer['github']}",
    }


def _render_zenodo_creator(maintainer: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": maintainer["display_name"],
        "affiliation": maintainer["affiliation"],
    }


def render_release_metadata(
    manifest: dict[str, Any],
    *,
    title: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    project = dict(manifest["project"])
    archive = dict(manifest["archive"])
    maintainers = [dict(item) for item in manifest["maintainers"]]

    rendered_title = title or str(project["title"])
    rendered_description = description or str(project["description"])
    repository_url = str(project["repository_url"])
    version = str(project["version"])

    citation_payload: dict[str, Any] = {
        "cff-version": "1.2.0",
        "message": f"If you use {rendered_title}, please cite this software release.",
        "title": rendered_title,
        "type": "software",
        "version": version,
        "license": project["license"],
        "abstract": rendered_description,
        "authors": [_render_citation_author(maintainer) for maintainer in maintainers],
        "repository-code": repository_url,
        "url": repository_url,
        "keywords": list(project["keywords"]),
    }
    if archive["doi"]:
        citation_payload["doi"] = archive["doi"]

    codemeta_payload: dict[str, Any] = {
        "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
        "@type": "SoftwareSourceCode",
        "name": rendered_title,
        "version": version,
        "description": rendered_description,
        "codeRepository": repository_url,
        "license": f"https://spdx.org/licenses/{project['license']}.html",
        "programmingLanguage": ["Python"],
        "keywords": list(project["keywords"]),
        "developmentStatus": "active",
        "author": [_render_codemeta_author(maintainer) for maintainer in maintainers],
    }
    if archive["doi"]:
        codemeta_payload["identifier"] = archive["doi"]

    zenodo_payload: dict[str, Any] = {
        "title": rendered_title,
        "version": version,
        "description": rendered_description,
        "license": project["license"],
        "upload_type": "software",
        "creators": [_render_zenodo_creator(maintainer) for maintainer in maintainers],
        "keywords": list(project["keywords"]),
        "notes": "Release archive DOI pending public deposit."
        if archive["doi_status"] == "pending"
        else f"Archived release DOI: {archive['doi']}",
    }
    if archive["doi"]:
        zenodo_payload["doi"] = archive["doi"]

    return {
        "CITATION.cff": yaml.safe_dump(citation_payload, sort_keys=False),
        "codemeta.json": json.dumps(codemeta_payload, indent=2) + "\n",
        ".zenodo.json": json.dumps(zenodo_payload, indent=2) + "\n",
    }


def write_release_metadata(
    repo_root: str | Path | None = None,
    *,
    manifest: dict[str, Any] | None = None,
) -> dict[str, str]:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    resolved_manifest = manifest or load_release_manifest(default_release_manifest_path(root))
    rendered = render_release_metadata(resolved_manifest)

    written_paths: dict[str, str] = {}
    for relative_path, text in rendered.items():
        path = root / relative_path
        path.write_text(str(text), encoding="utf-8")
        written_paths[relative_path] = str(path)
    return written_paths
