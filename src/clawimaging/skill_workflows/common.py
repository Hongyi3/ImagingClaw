from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
from typing import Any

import numpy as np
import yaml

from ..artifacts import refresh_checksums, validate_artifact_bundle


@dataclass(frozen=True)
class WorkflowResult:
    bundle_path: Path
    skill_name: str
    method_name: str
    title: str
    summary: str
    metrics: dict[str, Any]
    resolved_config: dict[str, Any]
    proxy_for_benchmark: bool


def format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def stringify_paths(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): stringify_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [stringify_paths(item) for item in value]
    return value


def write_tsv(path: Path, *, headers: list[str], rows: list[list[Any]]) -> None:
    lines = ["\t".join(headers)]
    for row in rows:
        lines.append("\t".join(str(item) for item in row))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def environment_snapshot(
    *,
    skill_name: str,
    run_mode: str,
    extra: dict[str, Any] | None = None,
) -> str:
    payload: dict[str, Any] = {
        "skill": skill_name,
        "run_mode": run_mode,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "numpy_version": np.__version__,
    }
    if extra:
        payload.update(extra)
    snapshot = yaml.safe_dump(payload, sort_keys=False)
    return str(snapshot)


def render_commands(command: str) -> str:
    return "#!/usr/bin/env bash\nset -euo pipefail\n" + command.rstrip() + "\n"


def render_analysis_log(lines: list[str]) -> str:
    return "# Analysis log\n\n" + "\n".join(f"- {line}" for line in lines) + "\n"


def finalize_bundle(bundle_root: Path) -> None:
    refresh_checksums(bundle_root)
    validate_artifact_bundle(bundle_root)
