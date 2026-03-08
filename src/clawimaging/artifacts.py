from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path
from typing import Any

from .release_manifest import default_release_manifest_path, load_release_manifest, render_release_metadata


MINIMUM_BUNDLE_FILES = [
    "report.md",
    "metrics.json",
    "resolved_config.yaml",
    "reproducibility/commands.sh",
    "reproducibility/analysis_log.md",
    "reproducibility/environment.yml",
    "reproducibility/checksums.sha256",
    "CITATION.cff",
    "codemeta.json",
    "ro-crate-metadata.json",
]
REQUIRED_BUNDLE_DIRECTORIES = [
    "figures",
    "tables",
    "reproducibility",
]
CHECKSUM_MANIFEST = "reproducibility/checksums.sha256"

ReportSection = tuple[str, str]


def sha256_text(text: str) -> str:
    digest = hashlib.sha256()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _relative_path(path: Path, *, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _iter_bundle_files(root: Path) -> list[Path]:
    bundle_files = [
        path
        for path in root.rglob("*")
        if path.is_file() and _relative_path(path, root=root) != CHECKSUM_MANIFEST
    ]
    return sorted(bundle_files, key=lambda path: _relative_path(path, root=root))


def _ensure_executable(path: Path) -> None:
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _read_checksum_manifest(checksum_path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line_number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line:
            continue
        if "  " not in line:
            raise ValueError(
                "Artifact bundle checksum manifest contains an invalid entry at "
                f"line {line_number}: {line}"
            )
        digest, relative_path = line.split("  ", 1)
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(
                "Artifact bundle checksum manifest contains an invalid digest for "
                f"{relative_path}"
            )
        if relative_path in entries:
            raise ValueError(
                "Artifact bundle checksum manifest contains a duplicate entry for "
                f"{relative_path}"
            )
        entries[relative_path] = digest
    return entries


def _render_report(
    *,
    title: str,
    skill_name: str,
    summary: str,
    report_sections: list[ReportSection] | None,
) -> str:
    lines = [
        f"# {title}",
        "",
        f"**Skill:** {skill_name}",
        "",
        "## Summary",
        "",
        summary,
    ]
    for section_title, section_body in report_sections or []:
        lines.extend(["", f"## {section_title}", "", section_body])
    return "\n".join(lines) + "\n"


def init_artifact_bundle(
    output_dir: str | Path,
    *,
    title: str,
    skill_name: str,
    summary: str,
    metrics: dict[str, Any] | None = None,
    config_yaml: str | None = None,
    report_sections: list[ReportSection] | None = None,
    commands: str | None = None,
    analysis_log: str | None = None,
    environment_yaml: str | None = None,
) -> Path:
    root = Path(output_dir)
    (root / "figures").mkdir(parents=True, exist_ok=True)
    (root / "tables").mkdir(parents=True, exist_ok=True)
    (root / "reproducibility").mkdir(parents=True, exist_ok=True)

    rendered_metadata: dict[str, Any] | None = None
    try:
        release_manifest = load_release_manifest(default_release_manifest_path())
    except (FileNotFoundError, ValueError):
        release_manifest = None
    if release_manifest is not None:
        rendered_metadata = render_release_metadata(
            release_manifest,
            title=title,
            description=summary,
        )

    (root / "report.md").write_text(
        _render_report(
            title=title,
            skill_name=skill_name,
            summary=summary,
            report_sections=report_sections,
        ),
        encoding="utf-8",
    )
    (root / "metrics.json").write_text(
        json.dumps(metrics or {"status": "scaffold", "skill": skill_name}, indent=2) + "\n",
        encoding="utf-8",
    )
    (root / "resolved_config.yaml").write_text(
        config_yaml or "status: scaffold\nmethod: placeholder\n",
        encoding="utf-8",
    )
    (root / "reproducibility" / "commands.sh").write_text(
        commands or "#!/usr/bin/env bash\nset -euo pipefail\n# Replace with real reproduction commands.\n",
        encoding="utf-8",
    )
    _ensure_executable(root / "reproducibility" / "commands.sh")
    (root / "reproducibility" / "analysis_log.md").write_text(
        analysis_log or f"# Analysis log\n\nGenerated scaffold bundle for `{skill_name}`.\n",
        encoding="utf-8",
    )
    (root / "reproducibility" / "environment.yml").write_text(
        environment_yaml
        or "name: clawimaging\nchannels:\n  - conda-forge\ndependencies:\n  - python>=3.10\n",
        encoding="utf-8",
    )
    (root / "CITATION.cff").write_text(
        (
            str(rendered_metadata["CITATION.cff"])
            if rendered_metadata is not None
            else "cff-version: 1.2.0\n"
            f"title: {title}\n"
            'message: "Replace stub metadata before public release."\n'
            "type: software\n"
        ),
        encoding="utf-8",
    )
    (root / "codemeta.json").write_text(
        (
            str(rendered_metadata["codemeta.json"])
            if rendered_metadata is not None
            else json.dumps(
                {
                    "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
                    "@type": "SoftwareSourceCode",
                    "name": title,
                    "description": summary,
                },
                indent=2,
            )
            + "\n"
        ),
        encoding="utf-8",
    )
    (root / "ro-crate-metadata.json").write_text(
        json.dumps(
            {
                "@context": ["https://w3id.org/ro/crate/1.1/context"],
                "@graph": [
                    {"@id": "ro-crate-metadata.json", "@type": "CreativeWork", "about": {"@id": "./"}},
                    {"@id": "./", "@type": "Dataset", "name": title},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    refresh_checksums(root)
    validate_artifact_bundle(root)
    return root


def refresh_checksums(bundle_root: str | Path) -> None:
    root = Path(bundle_root)
    checksum_path = root / CHECKSUM_MANIFEST
    lines = []
    for path in _iter_bundle_files(root):
        relative_path = _relative_path(path, root=root)
        lines.append(f"{_sha256(path)}  {relative_path}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_artifact_bundle(bundle_root: str | Path) -> None:
    root = Path(bundle_root)
    if not root.exists():
        raise ValueError(f"Artifact bundle root does not exist: {root}")

    missing_directories = [directory for directory in REQUIRED_BUNDLE_DIRECTORIES if not (root / directory).is_dir()]
    missing_files = [relative_path for relative_path in MINIMUM_BUNDLE_FILES if not (root / relative_path).is_file()]
    if missing_directories or missing_files:
        messages: list[str] = []
        if missing_directories:
            messages.append(f"missing directories: {', '.join(missing_directories)}")
        if missing_files:
            messages.append(f"missing files: {', '.join(missing_files)}")
        raise ValueError(f"Artifact bundle is incomplete ({'; '.join(messages)})")

    commands_path = root / "reproducibility" / "commands.sh"
    if not commands_path.stat().st_mode & stat.S_IXUSR:
        raise ValueError("Artifact bundle commands.sh must be executable")

    checksum_entries = _read_checksum_manifest(root / CHECKSUM_MANIFEST)
    expected_files = { _relative_path(path, root=root): path for path in _iter_bundle_files(root) }
    missing_entries = sorted(set(expected_files) - set(checksum_entries))
    unexpected_entries = sorted(set(checksum_entries) - set(expected_files))
    if missing_entries or unexpected_entries:
        details: list[str] = []
        if missing_entries:
            details.append(f"missing checksum entries: {', '.join(missing_entries)}")
        if unexpected_entries:
            details.append(f"unexpected checksum entries: {', '.join(unexpected_entries)}")
        raise ValueError(f"Artifact bundle checksum manifest is out of sync ({'; '.join(details)})")

    for relative_path, path in expected_files.items():
        if checksum_entries[relative_path] != _sha256(path):
            raise ValueError(f"Artifact bundle checksum mismatch for {relative_path}")
