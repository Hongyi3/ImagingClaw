from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import init_artifact_bundle


def run_scaffold_skill(
    *,
    skill_name: str,
    title: str,
    output_dir: str | Path,
    summary: str,
    input_path: str | None = None,
    extra_metrics: dict[str, Any] | None = None,
) -> Path:
    if input_path:
        summary = summary + f"\n\nInput: `{input_path}`"
    return init_artifact_bundle(
        output_dir,
        title=title,
        skill_name=skill_name,
        summary=summary,
        metrics=extra_metrics or {"status": "scaffold", "skill": skill_name},
    )
