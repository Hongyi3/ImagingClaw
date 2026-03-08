from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ..artifacts import init_artifact_bundle, sha256_text
from ..benchmarks import resolve_benchmark_manifest
from ..paths import find_repo_root
from .common import (
    finalize_bundle,
    format_bullets,
    render_analysis_log,
    render_commands,
    stringify_paths,
    write_tsv,
)
from .ct import run_ct_reconstruction
from .mri import run_mri_reconstruction
from .phase import run_phase_retrieval


DEFAULT_BENCHMARK_SPEC = "benchmarks/specs/lodopab_ct_baselines.yaml"


@dataclass(frozen=True)
class BenchmarkRunResult:
    bundle_path: Path
    child_bundle_path: Path
    selected_method: str
    selected_skill: str
    manifest: dict[str, Any]
    metrics: dict[str, Any]
    resolved_config: dict[str, Any]


def default_benchmark_spec_path(repo_root: str | Path | None = None) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    return (root / DEFAULT_BENCHMARK_SPEC).resolve()


WORKFLOW_MAP: dict[str, Callable[..., Any]] = {
    "ct": run_ct_reconstruction,
    "mri": run_mri_reconstruction,
    "coherent-imaging": run_phase_retrieval,
}
SUPPORTED_METHODS: dict[str, dict[str, Any]] = {
    "ct": {
        "method": "fbp",
        "skill": "ct-recon",
        "proxy_for_benchmark": True,
        "executed_data_kind": "synthetic-measurements",
    },
    "mri": {
        "method": "rss-zero-fill",
        "skill": "mri-recon",
        "proxy_for_benchmark": True,
        "executed_data_kind": "synthetic-measurements",
    },
    "coherent-imaging": {
        "method": "gerchberg-saxton",
        "skill": "phase-retrieve",
        "proxy_for_benchmark": False,
        "executed_data_kind": "synthetic-measurements",
    },
}


def _report_sections(
    manifest: dict[str, Any],
    *,
    environment_digest: str,
    child_bundle_path: str,
    child_skill: str,
    child_method: str,
    child_metrics: dict[str, float],
    executed_data_kind: str,
    proxy_for_benchmark: bool,
) -> list[tuple[str, str]]:
    dataset = dict(manifest["dataset"])
    dataset_entry = dict(dataset["registry_entry"])
    methods = [dict(method) for method in manifest["methods"]]
    hardware = dict(manifest["hardware"])
    environment = dict(manifest["environment"])
    return [
        (
            "Benchmark Metadata",
            "\n".join(
                [
                    f"- Name: `{manifest['name']}`",
                    f"- Version: `{manifest['version']}`",
                    f"- Modality: `{manifest['modality']}`",
                    f"- Task: `{manifest['task']}`",
                    f"- Spec path: `{manifest['source_paths']['benchmark_spec']}`",
                ]
            ),
        ),
        (
            "Dataset Provenance",
            "\n".join(
                [
                    f"- Dataset: `{dataset['name']}` `{dataset['version']}`",
                    f"- Split: `{dataset['split']}`",
                    f"- Access: `{dataset['access']}`",
                    f"- Measurement domain: `{dataset_entry['measurement_domain']}`",
                    f"- Protocol data kind: `{dataset_entry['data_kind']}`",
                    f"- Executed data kind: `{executed_data_kind}`",
                    f"- Proxy for benchmark protocol: `{str(proxy_for_benchmark).lower()}`",
                    f"- Source: {dataset_entry['source']}",
                    f"- Redistribution policy: {dataset_entry['redistribution_policy']}",
                    f"- Card: `{dataset_entry['card']}`",
                ]
            ),
        ),
        (
            "Methods",
            format_bullets([f"{method['name']} ({method['class']})" for method in methods]),
        ),
        (
            "Executed Reconstruction",
            "\n".join(
                [
                    f"- Child bundle: `{child_bundle_path}`",
                    f"- Child skill: `{child_skill}`",
                    f"- Selected method: `{child_method}`",
                ]
            ),
        ),
        (
            "Metrics",
            "\n".join(
                [
                    "Benchmark protocol metrics:",
                    format_bullets([str(metric) for metric in manifest["metrics"]]),
                    "",
                    "Calibration assumptions:",
                    format_bullets([str(item) for item in manifest["calibration_assumptions"]]),
                    "",
                    "Preprocessing:",
                    format_bullets([str(item) for item in manifest["preprocessing"]]),
                    "",
                    "Executed child metrics:",
                    format_bullets([f"{name}: {value:.6f}" for name, value in child_metrics.items()]),
                ]
            ),
        ),
        (
            "Reproducibility Notes",
            "\n".join(
                [
                    f"- Dataset registry path: `{manifest['source_paths']['dataset_registry']}`",
                    f"- Environment digest: `{environment_digest}`",
                    (
                        "- Upstream benchmark measurements were not executed directly in this "
                        "smoke run."
                        if proxy_for_benchmark
                        else "- The benchmark executed directly against repository-local synthetic measurements."
                    ),
                    f"- Hardware notes: {hardware}",
                    f"- Environment snapshot: {environment}",
                ]
            ),
        ),
    ]


def run_benchmark(
    output_dir: str | Path,
    *,
    spec_path: str | Path,
    reproduction_command: str,
) -> BenchmarkRunResult:
    resolved_spec_path = Path(spec_path).resolve()
    manifest = resolve_benchmark_manifest(resolved_spec_path)
    modality = str(manifest["modality"])
    if modality not in WORKFLOW_MAP:
        raise ValueError(f"Benchmark dispatch does not support modality: {modality}")

    execution_config = SUPPORTED_METHODS[modality]
    expected_method_name = str(execution_config["method"])
    child_skill_name = str(execution_config["skill"])
    selected_method = next(
        (
            method
            for method in manifest["methods"]
            if str(method["name"]).lower() == expected_method_name
        ),
        None,
    )
    if selected_method is None:
        raise ValueError(
            f"Benchmark spec {manifest['name']} does not include the required supported method: "
            f"{expected_method_name}"
        )

    bundle_root = Path(output_dir).resolve()
    child_bundle_path = bundle_root / "runs" / f"{child_skill_name}-{expected_method_name}"
    child_result = WORKFLOW_MAP[modality](
        child_bundle_path,
        benchmark_manifest=manifest,
        reproduction_command=reproduction_command,
    )

    environment_yaml = yaml.safe_dump(
        {
            "benchmark_environment": manifest["environment"],
            "benchmark_hardware": manifest["hardware"],
            "benchmark_identity": {
                "name": manifest["name"],
                "version": manifest["version"],
                "task": manifest["task"],
            },
            "selected_method": expected_method_name,
            "executed_data_kind": execution_config["executed_data_kind"],
            "proxy_for_benchmark": execution_config["proxy_for_benchmark"],
        },
        sort_keys=False,
    )
    environment_digest = sha256_text(environment_yaml)
    manifest["environment_digest"] = environment_digest

    metrics = {
        "status": "completed",
        "skill": "benchmark-run",
        "benchmark": {
            "name": manifest["name"],
            "version": manifest["version"],
            "task": manifest["task"],
            "dataset": {
                "name": manifest["dataset"]["name"],
                "version": manifest["dataset"]["version"],
                "split": manifest["dataset"]["split"],
                "access": manifest["dataset"]["access"],
                "protocol_data_kind": manifest["dataset"]["registry_entry"]["data_kind"],
                "executed_data_kind": execution_config["executed_data_kind"],
            },
            "methods": [method["name"] for method in manifest["methods"]],
            "method_count": len(manifest["methods"]),
            "metrics": list(manifest["metrics"]),
            "metric_count": len(manifest["metrics"]),
            "selected_method": expected_method_name,
            "child_bundle": str(child_bundle_path.relative_to(bundle_root)),
            "proxy_for_benchmark": execution_config["proxy_for_benchmark"],
        },
        "child_run": child_result.metrics,
        "environment_digest": environment_digest,
    }
    summary = (
        "Resolved and validated a declared benchmark manifest against the dataset registry, then "
        "dispatched the supported baseline into a nested child bundle with explicit data-kind "
        "and proxy reporting."
    )
    analysis_log = render_analysis_log(
        [
            f"Loaded benchmark spec `{manifest['source_paths']['benchmark_spec']}`.",
            f"Loaded dataset registry `{manifest['source_paths']['dataset_registry']}`.",
            (
                f"Validated dataset reference `{manifest['dataset']['name']}@"
                f"{manifest['dataset']['version']}` against registry metadata."
            ),
            f"Selected supported method `{expected_method_name}` for modality `{modality}`.",
            f"Created child bundle at `runs/{child_skill_name}-{expected_method_name}`.",
            f"Computed environment digest `{environment_digest}` from `environment.yml`.",
        ]
    )
    resolved_config = {
        "manifest": manifest,
        "execution": {
            "selected_method": expected_method_name,
            "selected_skill": child_skill_name,
            "child_bundle": str(child_bundle_path.relative_to(bundle_root)),
            "proxy_for_benchmark": execution_config["proxy_for_benchmark"],
            "executed_data_kind": execution_config["executed_data_kind"],
        },
        "child_run": child_result.resolved_config,
    }

    init_artifact_bundle(
        bundle_root,
        title=f"Benchmark Manifest: {manifest['name']}",
        skill_name="benchmark-run",
        summary=summary,
        metrics=metrics,
        config_yaml=yaml.safe_dump(stringify_paths(resolved_config), sort_keys=False),
        report_sections=_report_sections(
            manifest,
            environment_digest=environment_digest,
            child_bundle_path=str(child_bundle_path.relative_to(bundle_root)),
            child_skill=child_skill_name,
            child_method=expected_method_name,
            child_metrics=child_result.metrics["metrics"],
            executed_data_kind=str(execution_config["executed_data_kind"]),
            proxy_for_benchmark=bool(execution_config["proxy_for_benchmark"]),
        ),
        commands=render_commands(reproduction_command),
        analysis_log=analysis_log,
        environment_yaml=environment_yaml,
    )
    write_tsv(
        bundle_root / "tables" / "benchmark_summary.tsv",
        headers=["field", "value"],
        rows=[
            ["benchmark", manifest["name"]],
            ["modality", modality],
            ["selected_method", expected_method_name],
            ["child_bundle", str(child_bundle_path.relative_to(bundle_root))],
            ["executed_data_kind", str(execution_config["executed_data_kind"])],
            ["proxy_for_benchmark", str(execution_config["proxy_for_benchmark"]).lower()],
        ],
    )
    finalize_bundle(bundle_root)
    return BenchmarkRunResult(
        bundle_path=bundle_root,
        child_bundle_path=child_bundle_path,
        selected_method=expected_method_name,
        selected_skill=child_skill_name,
        manifest=manifest,
        metrics=metrics,
        resolved_config=resolved_config,
    )
