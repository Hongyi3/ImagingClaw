from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from ..artifacts import init_artifact_bundle, sha256_text, validate_artifact_bundle
from .common import finalize_bundle, render_analysis_log, render_commands, stringify_paths, write_tsv


PREVIEW_CANDIDATES = [
    "figures/reconstruction_phase.npy",
    "figures/reconstruction.npy",
    "figures/reference_phase.npy",
    "figures/reference.npy",
    "figures/measurement_magnitude.npy",
    "figures/measurement.npy",
]


def _load_preview_source(source_bundle: Path) -> tuple[str, np.ndarray]:
    for relative_path in PREVIEW_CANDIDATES:
        candidate = source_bundle / relative_path
        if not candidate.exists():
            continue
        array = np.load(candidate, allow_pickle=False)
        preview_array = np.asarray(array)
        while preview_array.ndim > 2:
            preview_array = preview_array[0]
        if preview_array.ndim != 2:
            raise ValueError(
                f"Preview candidate {relative_path} is not 2D after squeezing leading axes"
            )
        if np.iscomplexobj(preview_array):
            preview_array = np.abs(preview_array)
        return relative_path, preview_array.astype(float)
    raise ValueError("No reconstruction-like .npy array found in the source bundle")


def _numeric_metric_map(payload: dict[str, Any]) -> dict[str, float]:
    candidates = [
        payload.get("metrics"),
        dict(payload.get("child_run", {})).get("metrics"),
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        numeric_items: dict[str, float] = {}
        for key, value in candidate.items():
            if isinstance(value, (int, float)):
                numeric_items[str(key)] = float(value)
        if numeric_items:
            return numeric_items
    raise ValueError("No structured numeric metrics found in source bundle metrics.json")


def _write_pgm(path: Path, array: np.ndarray) -> None:
    image = np.asarray(array, dtype=float)
    min_value = float(np.min(image))
    max_value = float(np.max(image))
    if max_value > min_value:
        normalized = (image - min_value) / (max_value - min_value)
    else:
        normalized = np.zeros_like(image)
    pixels = np.round(np.clip(normalized, 0.0, 1.0) * 255.0).astype(np.uint8)
    header = f"P5\n{pixels.shape[1]} {pixels.shape[0]}\n255\n".encode("ascii")
    path.write_bytes(header + pixels.tobytes())


def run_paper_figure(
    output_dir: str | Path,
    *,
    source_bundle: str | Path,
    reproduction_command: str,
) -> Path:
    source_root = Path(source_bundle).resolve()
    validate_artifact_bundle(source_root)

    preview_source, preview_array = _load_preview_source(source_root)
    metrics_payload = json.loads((source_root / "metrics.json").read_text(encoding="utf-8"))
    metric_values = _numeric_metric_map(metrics_payload)
    environment_yaml = yaml.safe_dump(
        {
            "source_bundle": str(source_root),
            "preview_source": preview_source,
            "metric_count": len(metric_values),
        },
        sort_keys=False,
    )
    environment_digest = sha256_text(environment_yaml)
    summary = (
        "Regenerated a manuscript preview asset and a manuscript-ready metrics table directly "
        "from a validated ClawImaging artifact bundle."
    )

    bundle_root = Path(output_dir).resolve()
    provenance_manifest = {
        "figure_asset": "figures/manuscript_preview.pgm",
        "metrics_table": "tables/manuscript_metrics.tsv",
        "source_bundle": str(source_root),
        "source_metrics_file": str(source_root / "metrics.json"),
        "source_array": preview_source,
    }
    init_artifact_bundle(
        bundle_root,
        title=f"Paper Assets from {source_root.name}",
        skill_name="paper-figure",
        summary=summary,
        metrics={
            "status": "completed",
            "skill": "paper-figure",
            "metric_count": len(metric_values),
            "preview_source": preview_source,
            "environment_digest": environment_digest,
        },
        config_yaml=yaml.safe_dump(
            stringify_paths(
                {
                    "source_bundle": str(source_root),
                    "preview_source": preview_source,
                    "metric_values": metric_values,
                    "provenance_manifest": provenance_manifest,
                    "environment_digest": environment_digest,
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
                        f"- Preview source array: `{preview_source}`",
                        f"- Source metrics file: `{source_root / 'metrics.json'}`",
                    ]
                ),
            ),
            (
                "Generated Assets",
                "\n".join(
                    [
                        "- Preview image: `figures/manuscript_preview.pgm`",
                        "- Metrics table: `tables/manuscript_metrics.tsv`",
                        "- Provenance manifest: `reproducibility/figure_provenance.json`",
                    ]
                ),
            ),
            (
                "Metrics Table",
                "\n".join([f"- {name}: {value:.6f}" for name, value in metric_values.items()]),
            ),
            (
                "Provenance",
                "\n".join(
                    [
                        f"- Environment digest: `{environment_digest}`",
                        "- Outputs are generated from bundle files, not manual figure edits.",
                    ]
                ),
            ),
        ],
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Validated source bundle `{source_root}`.",
                f"Selected preview source `{preview_source}`.",
                "Regenerated manuscript preview and metrics table from structured bundle outputs.",
                f"Computed environment digest `{environment_digest}`.",
            ]
        ),
        environment_yaml=environment_yaml,
    )

    _write_pgm(bundle_root / "figures" / "manuscript_preview.pgm", preview_array)
    write_tsv(
        bundle_root / "tables" / "manuscript_metrics.tsv",
        headers=["metric", "value"],
        rows=[[name, f"{value:.6f}"] for name, value in metric_values.items()],
    )
    (bundle_root / "reproducibility" / "figure_provenance.json").write_text(
        json.dumps(provenance_manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    finalize_bundle(bundle_root)
    return bundle_root
