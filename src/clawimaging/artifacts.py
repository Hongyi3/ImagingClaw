from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


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

ReportSection = tuple[str, str]


def sha256_text(text: str) -> str:
    digest = hashlib.sha256()
    digest.update(text.encode("utf-8"))
    return digest.hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


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
        "cff-version: 1.2.0\n"
        f"title: {title}\n"
        'message: "Replace stub metadata before public release."\n'
        "type: software\n",
        encoding="utf-8",
    )
    (root / "codemeta.json").write_text(
        json.dumps(
            {
                "@context": "https://doi.org/10.5063/schema/codemeta-2.0",
                "@type": "SoftwareSourceCode",
                "name": title,
                "description": summary,
            },
            indent=2,
        )
        + "\n",
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
    return root


def refresh_checksums(bundle_root: str | Path) -> None:
    root = Path(bundle_root)
    checksum_path = root / "reproducibility" / "checksums.sha256"
    lines = []
    for rel in MINIMUM_BUNDLE_FILES:
        path = root / rel
        if path.exists():
            lines.append(f"{_sha256(path)}  {rel}")
    checksum_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
