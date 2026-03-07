from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[2]


def _bootstrap_core() -> tuple[object, object, object]:
    src_dir = ROOT / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from clawimaging.artifacts import init_artifact_bundle, sha256_text
    from clawimaging.benchmarks import resolve_benchmark_manifest

    return init_artifact_bundle, resolve_benchmark_manifest, sha256_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="Benchmark spec YAML path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--demo", action="store_true", help="Resolve the default CT benchmark spec")
    return parser


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _report_sections(manifest: dict[str, object], environment_digest: str) -> list[tuple[str, str]]:
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
                    f"- Data kind: `{dataset_entry['data_kind']}`",
                    f"- Source: {dataset_entry['source']}",
                    f"- Redistribution policy: {dataset_entry['redistribution_policy']}",
                    f"- Card: `{dataset_entry['card']}`",
                ]
            ),
        ),
        (
            "Methods",
            _format_bullets(
                [
                    f"{method['name']} ({method['class']})"
                    for method in methods
                ]
            ),
        ),
        (
            "Metrics",
            "\n".join(
                [
                    _format_bullets([str(metric) for metric in manifest["metrics"]]),
                    "",
                    "Calibration assumptions:",
                    _format_bullets([str(item) for item in manifest["calibration_assumptions"]]),
                    "",
                    "Preprocessing:",
                    _format_bullets([str(item) for item in manifest["preprocessing"]]),
                ]
            ),
        ),
        (
            "Reproducibility Notes",
            "\n".join(
                [
                    f"- Dataset registry path: `{manifest['source_paths']['dataset_registry']}`",
                    f"- Environment digest: `{environment_digest}`",
                    f"- Hardware notes: {hardware}",
                    f"- Environment snapshot: {environment}",
                ]
            ),
        ),
    ]


def _resolve_spec_path(args: argparse.Namespace) -> Path:
    if args.demo:
        return ROOT / "benchmarks" / "specs" / "lodopab_ct_baselines.yaml"
    if args.input:
        return Path(args.input).resolve()
    raise SystemExit("Provide --demo or --input.")


def main() -> None:
    args = build_parser().parse_args()
    init_artifact_bundle, resolve_benchmark_manifest, sha256_text = _bootstrap_core()

    spec_path = _resolve_spec_path(args)
    manifest = resolve_benchmark_manifest(spec_path)
    environment_yaml = yaml.safe_dump(
        {
            "benchmark_environment": manifest["environment"],
            "benchmark_hardware": manifest["hardware"],
            "benchmark_identity": {
                "name": manifest["name"],
                "version": manifest["version"],
                "task": manifest["task"],
            },
        },
        sort_keys=False,
    )
    environment_digest = sha256_text(environment_yaml)
    manifest["environment_digest"] = environment_digest

    metrics = {
        "status": "validated",
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
                "data_kind": manifest["dataset"]["registry_entry"]["data_kind"],
            },
            "methods": [method["name"] for method in manifest["methods"]],
            "method_count": len(manifest["methods"]),
            "metrics": list(manifest["metrics"]),
            "metric_count": len(manifest["metrics"]),
        },
        "environment_digest": environment_digest,
    }
    summary = (
        "Resolved and validated a declared benchmark manifest against the dataset registry. "
        "This phase records protocol metadata, provenance, baseline coverage, and reproducibility "
        "artifacts without dispatching modality-specific methods yet."
    )
    commands = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"python3 skills/benchmark-run/benchmark_run.py --input {manifest['source_paths']['benchmark_spec']} "
        f"--output {Path(args.output).resolve()}\n"
    )
    analysis_log = "\n".join(
        [
            "# Analysis log",
            "",
            f"- Loaded benchmark spec `{manifest['source_paths']['benchmark_spec']}`.",
            f"- Loaded dataset registry `{manifest['source_paths']['dataset_registry']}`.",
            (
                f"- Validated dataset reference `{manifest['dataset']['name']}@"
                f"{manifest['dataset']['version']}` against registry metadata."
            ),
            "- Verified analytic, iterative, and learned baseline coverage.",
            f"- Computed environment digest `{environment_digest}` from `environment.yml`.",
            "",
        ]
    )

    init_artifact_bundle(
        args.output,
        title=f"Benchmark Manifest: {manifest['name']}",
        skill_name="benchmark-run",
        summary=summary,
        metrics=metrics,
        config_yaml=yaml.safe_dump(manifest, sort_keys=False),
        report_sections=_report_sections(manifest, environment_digest),
        commands=commands,
        analysis_log=analysis_log,
        environment_yaml=environment_yaml,
    )
    print(f"Wrote benchmark bundle to {args.output}")


if __name__ == "__main__":
    main()
