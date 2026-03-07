from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ..artifacts import init_artifact_bundle, validate_artifact_bundle
from ..release_audit import audit_release_metadata
from .common import finalize_bundle, render_analysis_log, render_commands, stringify_paths, write_tsv


def _bundle_inventory(source_root: Path) -> list[dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_root).as_posix()
        inventory.append(
            {
                "path": relative_path,
                "size_bytes": path.stat().st_size,
            }
        )
    return inventory


def run_repro_export(
    output_dir: str | Path,
    *,
    source_bundle: str | Path,
    repo_root: str | Path,
    reproduction_command: str,
) -> Path:
    source_root = Path(source_bundle).resolve()
    validate_artifact_bundle(source_root)

    inventory = _bundle_inventory(source_root)
    metadata_audit = audit_release_metadata(repo_root)
    summary = (
        "Validated a completed artifact bundle, inventoried its contents, and audited the "
        "repository release metadata for parseability, placeholders, and cross-file mismatches."
    )
    bundle_root = Path(output_dir).resolve()
    init_artifact_bundle(
        bundle_root,
        title=f"Repro Export Audit for {source_root.name}",
        skill_name="repro-export",
        summary=summary,
        metrics={
            "status": "completed",
            "skill": "repro-export",
            "source_bundle": str(source_root),
            "source_file_count": len(inventory),
            "metadata_audit_status": metadata_audit["status"],
            "metadata_warning_count": len(metadata_audit["warnings"]),
            "metadata_error_count": len(metadata_audit["errors"]),
        },
        config_yaml=yaml.safe_dump(
            stringify_paths(
                {
                    "source_bundle": str(source_root),
                    "inventory": inventory,
                    "metadata_audit": metadata_audit,
                }
            ),
            sort_keys=False,
        ),
        report_sections=[
            (
                "Source Bundle",
                "\n".join(
                    [
                        f"- Source bundle: `{source_root}`",
                        f"- Validated file count: {len(inventory)}",
                        "- Source bundle files were not modified during export.",
                    ]
                ),
            ),
            (
                "Inventory Summary",
                "\n".join(
                    [
                        f"- Figures: {sum(1 for item in inventory if item['path'].startswith('figures/'))}",
                        f"- Tables: {sum(1 for item in inventory if item['path'].startswith('tables/'))}",
                        f"- Reproducibility files: {sum(1 for item in inventory if item['path'].startswith('reproducibility/'))}",
                    ]
                ),
            ),
            (
                "Metadata Audit",
                "\n".join(
                    [
                        f"- Audit status: `{metadata_audit['status']}`",
                        f"- Warnings: {len(metadata_audit['warnings'])}",
                        f"- Errors: {len(metadata_audit['errors'])}",
                        "- Missing scientific release metadata is reported, not fabricated.",
                    ]
                ),
            ),
            (
                "Reproducibility Notes",
                "\n".join(
                    [
                        "- Root metadata files audited: `CITATION.cff`, `codemeta.json`, `.zenodo.json`",
                        "- Export output is a separate audit bundle rather than an in-place mutation.",
                    ]
                ),
            ),
        ],
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Validated source bundle `{source_root}`.",
                f"Inventoried {len(inventory)} files from the source bundle.",
                f"Release metadata audit status: {metadata_audit['status']}.",
                "Emitted a separate audit bundle without modifying the source bundle.",
            ]
        ),
        environment_yaml=yaml.safe_dump(
            {
                "source_bundle": str(source_root),
                "metadata_audit_status": metadata_audit["status"],
                "inventory_file_count": len(inventory),
            },
            sort_keys=False,
        ),
    )

    write_tsv(
        bundle_root / "tables" / "source_inventory.tsv",
        headers=["path", "size_bytes"],
        rows=[[item["path"], item["size_bytes"]] for item in inventory],
    )
    write_tsv(
        bundle_root / "tables" / "metadata_audit.tsv",
        headers=["kind", "detail"],
        rows=[
            ["status", metadata_audit["status"]],
            *[["warning", warning] for warning in metadata_audit["warnings"]],
            *[["error", error] for error in metadata_audit["errors"]],
        ]
        or [["status", metadata_audit["status"]]],
    )
    (bundle_root / "reproducibility" / "metadata_audit.json").write_text(
        json.dumps(metadata_audit, indent=2) + "\n",
        encoding="utf-8",
    )
    finalize_bundle(bundle_root)
    return bundle_root
