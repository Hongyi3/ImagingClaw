from pathlib import Path

import pytest
import yaml

from clawimaging.release_audit import audit_release_metadata
from clawimaging.release_manifest import load_release_manifest, write_release_metadata


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_release_repo(tmp_path: Path) -> Path:
    _write_text(tmp_path / "skills" / "catalog.json", "{\n  \"skills\": []\n}\n")
    _write_text(tmp_path / "README.md", "# Demo\n")
    _write_text(tmp_path / "docs" / "architecture.md", "# Architecture\n")
    _write_text(tmp_path / "docs" / "benchmark-policy.md", "# Benchmark\n")
    _write_text(tmp_path / "docs" / "dataset-policy.md", "# Dataset\n")
    _write_text(tmp_path / "docs" / "reproducibility-contract.md", "# Repro\n")
    _write_text(tmp_path / "docs" / "release-checklist.md", "# Release\n")
    _write_text(tmp_path / "docs" / "publication-strategy.md", "# Publication\n")
    _write_text(tmp_path / "PROJECT-CHARTER.md", "# Charter\n")
    _write_text(tmp_path / "BLUEPRINT.md", "# Blueprint\n")
    _write_text(tmp_path / "benchmarks" / "specs" / "demo.yaml", "name: demo\n")
    _write_text(tmp_path / "release" / "v1.0.yaml", "")
    _write_text(tmp_path / "pyproject.toml", '[project]\nname = "clawimaging"\nversion = "1.0.0"\n')
    manifest = {
        "project": {
            "title": "ClawImaging",
            "package_name": "clawimaging",
            "version": "1.0.0",
            "description": "Reproducibility-first computational imaging skill library.",
            "repository_url": "https://github.com/Hongyi3/ImagingClaw",
            "license": "BSD-3-Clause",
            "keywords": ["computational imaging", "reproducibility"],
        },
        "maintainers": [
            {
                "display_name": "Hongyi3",
                "family_names": "Hongyi3",
                "given_names": "Hongyi",
                "affiliation": "ClawImaging",
                "email": "hongyi3@users.noreply.github.com",
                "github": "Hongyi3",
            }
        ],
        "archive": {
            "doi_status": "pending",
            "doi": None,
            "release_tag": "v1.0.0",
            "notes": ["DOI pending."],
        },
        "packages": {
            "software": {
                "title": "Software package",
                "summary": "Software package summary.",
                "include_paths": [
                    "README.md",
                    "PROJECT-CHARTER.md",
                    "BLUEPRINT.md",
                    "docs/architecture.md",
                    "docs/benchmark-policy.md",
                    "docs/dataset-policy.md",
                    "docs/reproducibility-contract.md",
                    "docs/release-checklist.md",
                    "docs/publication-strategy.md",
                    "skills/catalog.json",
                ],
            },
            "benchmark": {
                "title": "Benchmark package",
                "summary": "Benchmark package summary.",
                "default_benchmark_spec": "benchmarks/specs/demo.yaml",
            },
        },
    }
    (tmp_path / "release" / "v1.0.yaml").write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
    )
    return tmp_path


def test_load_release_manifest_rejects_missing_required_field(tmp_path: Path) -> None:
    repo_root = _write_release_repo(tmp_path)
    manifest_path = repo_root / "release" / "v1.0.yaml"
    broken = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    del broken["project"]["version"]
    manifest_path.write_text(yaml.safe_dump(broken, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="release.project missing required fields: version"):
        load_release_manifest(manifest_path)


def test_load_release_manifest_rejects_placeholders(tmp_path: Path) -> None:
    repo_root = _write_release_repo(tmp_path)
    manifest_path = repo_root / "release" / "v1.0.yaml"
    broken = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    broken["project"]["repository_url"] = "https://github.com/YOUR-ORG/ClawImaging"
    manifest_path.write_text(yaml.safe_dump(broken, sort_keys=False), encoding="utf-8")

    with pytest.raises(ValueError, match="placeholder"):
        load_release_manifest(manifest_path)


def test_audit_release_metadata_rejects_manifest_mismatch(tmp_path: Path) -> None:
    repo_root = _write_release_repo(tmp_path)
    manifest = load_release_manifest(repo_root / "release" / "v1.0.yaml")
    write_release_metadata(repo_root, manifest=manifest)
    citation_path = repo_root / "CITATION.cff"
    citation_path.write_text(
        citation_path.read_text(encoding="utf-8").replace("version: 1.0.0", "version: 0.9.0"),
        encoding="utf-8",
    )

    payload = audit_release_metadata(repo_root)
    assert payload["status"] == "failed"
    assert any("CITATION.cff field `version`" in error for error in payload["errors"])
