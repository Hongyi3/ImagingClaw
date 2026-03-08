from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import yaml

from .artifacts import init_artifact_bundle, validate_artifact_bundle
from .paths import find_repo_root
from .release_audit import evaluate_release_readiness
from .release_manifest import load_release_manifest
from .skill_workflows.benchmark import run_benchmark
from .skill_workflows.common import (
    finalize_bundle,
    render_analysis_log,
    render_commands,
    stringify_paths,
    write_tsv,
)
from .skill_workflows.paper import run_paper_figure
from .skill_workflows.repro import run_repro_export


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _copy_file(source: Path, destination: Path) -> dict[str, str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return {
        "source": str(source),
        "destination": str(destination),
        "sha256": _sha256_file(destination),
    }


def _copy_repo_relative_paths(
    repo_root: Path,
    *,
    relative_paths: list[str],
    output_root: Path,
    destination_prefix: str,
) -> list[dict[str, str]]:
    copied: list[dict[str, str]] = []
    for relative_path in relative_paths:
        source = (repo_root / relative_path).resolve()
        copied.append(
            _copy_file(
                source,
                output_root / destination_prefix / relative_path,
            )
        )
    return copied


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return dict(payload)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a mapping")
    return dict(payload)


def _resolve_benchmark_inputs(source_bundle: Path) -> tuple[Path, Path]:
    validate_artifact_bundle(source_bundle)
    metrics = _load_json(source_bundle / "metrics.json")
    skill_name = str(metrics.get("skill", ""))
    if skill_name == "benchmark-run":
        child_relative_path = str(metrics["benchmark"]["child_bundle"])
        child_bundle = (source_bundle / child_relative_path).resolve()
        validate_artifact_bundle(child_bundle)
        return source_bundle, child_bundle

    candidate_parent = source_bundle.parent.parent
    candidate_metrics_path = candidate_parent / "metrics.json"
    if candidate_metrics_path.exists():
        candidate_metrics = _load_json(candidate_metrics_path)
        if str(candidate_metrics.get("skill", "")) == "benchmark-run":
            validate_artifact_bundle(candidate_parent)
            return candidate_parent, source_bundle

    raise ValueError(
        "Benchmark package source must be a benchmark-run bundle or one of its child run bundles"
    )


def _benchmark_manifest_from_bundle(benchmark_bundle: Path) -> dict[str, Any]:
    resolved_config = _load_yaml(benchmark_bundle / "resolved_config.yaml")
    manifest_raw = resolved_config.get("manifest")
    if not isinstance(manifest_raw, dict):
        raise ValueError("Benchmark bundle resolved_config.yaml is missing `manifest`")
    return dict(manifest_raw)


def build_software_package(
    output_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    reproduction_command: str,
) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    release_manifest = load_release_manifest(root / "release" / "v1.0.yaml")
    package_config = dict(release_manifest["packages"]["software"])
    readiness = evaluate_release_readiness(root)
    copied_documents = _copy_repo_relative_paths(
        root,
        relative_paths=list(package_config["include_paths"]),
        output_root=Path(output_dir).resolve(),
        destination_prefix="documents",
    )
    copied_metadata = _copy_repo_relative_paths(
        root,
        relative_paths=["CITATION.cff", "codemeta.json", ".zenodo.json"],
        output_root=Path(output_dir).resolve(),
        destination_prefix="metadata",
    )
    copied_files = copied_documents + copied_metadata

    bundle_root = Path(output_dir).resolve()
    summary = str(package_config["summary"])
    init_artifact_bundle(
        bundle_root,
        title=str(package_config["title"]),
        skill_name="publication-package",
        summary=summary,
        metrics={
            "status": "completed",
            "package_type": "software",
            "included_file_count": len(copied_files),
            "release_readiness_status": readiness["status"],
        },
        config_yaml=yaml.safe_dump(
            stringify_paths(
                {
                    "package_type": "software",
                    "release_manifest": release_manifest["source_path"],
                    "included_files": copied_files,
                    "release_readiness": readiness,
                }
            ),
            sort_keys=False,
        ),
        report_sections=[
            (
                "Release Source Of Truth",
                "\n".join(
                    [
                        f"- Release manifest: `{release_manifest['source_path']}`",
                        f"- Repository URL: `{release_manifest['project']['repository_url']}`",
                        f"- Version: `{release_manifest['project']['version']}`",
                    ]
                ),
            ),
            (
                "Included Documents",
                "\n".join(
                    [
                        f"- Included repository documents: {len(copied_documents)}",
                        "- Root release metadata copied into `metadata/`.",
                    ]
                ),
            ),
            (
                "Release Readiness",
                "\n".join(
                    [
                        f"- Overall status: `{readiness['status']}`",
                        *[
                            f"- {check['name']}: `{check['status']}` ({check['detail']})"
                            for check in readiness["checks"]
                        ],
                    ]
                ),
            ),
            (
                "Reproducibility Notes",
                "\n".join(
                    [
                        "- Package contents are copied from repo-tracked source files.",
                        "- The bundle inventory records the exact copied paths and checksums.",
                    ]
                ),
            ),
        ],
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Loaded release manifest `{release_manifest['source_path']}`.",
                f"Copied {len(copied_documents)} software-paper support documents.",
                "Copied root release metadata into the package bundle.",
                f"Release readiness status at package build time: {readiness['status']}.",
            ]
        ),
        environment_yaml=yaml.safe_dump(
            {
                "package_type": "software",
                "release_version": release_manifest["project"]["version"],
                "included_file_count": len(copied_files),
                "release_readiness_status": readiness["status"],
            },
            sort_keys=False,
        ),
    )
    write_tsv(
        bundle_root / "tables" / "software_package_inventory.tsv",
        headers=["source", "destination", "sha256"],
        rows=[[item["source"], item["destination"], item["sha256"]] for item in copied_files],
    )
    write_tsv(
        bundle_root / "tables" / "release_readiness.tsv",
        headers=["check", "status", "detail"],
        rows=[
            [check["name"], check["status"], check["detail"]]
            for check in readiness["checks"]
        ],
    )
    (bundle_root / "reproducibility" / "package_manifest.json").write_text(
        json.dumps(
            {
                "package_type": "software",
                "release_manifest": release_manifest["source_path"],
                "included_files": copied_files,
                "release_readiness": readiness,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    finalize_bundle(bundle_root)
    return bundle_root


def build_benchmark_package(
    output_dir: str | Path,
    *,
    repo_root: str | Path | None = None,
    source_bundle: str | Path | None = None,
    demo: bool = False,
    reproduction_command: str,
) -> Path:
    root = Path(repo_root).resolve() if repo_root is not None else find_repo_root()
    release_manifest = load_release_manifest(root / "release" / "v1.0.yaml")
    package_config = dict(release_manifest["packages"]["benchmark"])
    bundle_root = Path(output_dir).resolve()

    if demo:
        benchmark_bundle = bundle_root / "runs" / "source-benchmark"
        benchmark_result = run_benchmark(
            benchmark_bundle,
            spec_path=root / package_config["default_benchmark_spec"],
            reproduction_command=(
                "python3 skills/benchmark-run/benchmark_run.py"
                f" --input {root / package_config['default_benchmark_spec']}"
                f" --output {benchmark_bundle}"
            ),
        )
        benchmark_bundle_root = benchmark_result.bundle_path
        paper_source_bundle = benchmark_result.child_bundle_path
    else:
        if source_bundle is None:
            raise ValueError("Provide --demo or --source-bundle for the benchmark package")
        benchmark_bundle_root, paper_source_bundle = _resolve_benchmark_inputs(
            Path(source_bundle).resolve()
        )

    paper_bundle_root = run_paper_figure(
        bundle_root / "runs" / "paper-assets",
        source_bundle=paper_source_bundle,
        reproduction_command=(
            "python3 skills/paper-figure/paper_figure.py"
            f" --input {paper_source_bundle}"
            f" --output {bundle_root / 'runs' / 'paper-assets'}"
        ),
    )
    repro_bundle_root = run_repro_export(
        bundle_root / "runs" / "repro-export",
        source_bundle=paper_source_bundle,
        repo_root=root,
        reproduction_command=(
            "python3 skills/repro-export/repro_export.py"
            f" --input {paper_source_bundle}"
            f" --output {bundle_root / 'runs' / 'repro-export'}"
        ),
    )

    benchmark_manifest = _benchmark_manifest_from_bundle(benchmark_bundle_root)
    benchmark_metrics = _load_json(benchmark_bundle_root / "metrics.json")
    copied_documents = _copy_repo_relative_paths(
        root,
        relative_paths=[
            str(benchmark_manifest["source_paths"]["benchmark_spec"]),
            str(benchmark_manifest["source_paths"]["dataset_registry"]),
            str(benchmark_manifest["dataset"]["registry_entry"]["card"]),
            release_manifest["source_path"],
        ],
        output_root=bundle_root,
        destination_prefix="documents",
    )
    copied_assets = [
        _copy_file(
            paper_bundle_root / "figures" / "manuscript_preview.pgm",
            bundle_root / "figures" / "manuscript_preview.pgm",
        ),
        _copy_file(
            paper_bundle_root / "tables" / "manuscript_metrics.tsv",
            bundle_root / "tables" / "manuscript_metrics.tsv",
        ),
        _copy_file(
            benchmark_bundle_root / "tables" / "benchmark_summary.tsv",
            bundle_root / "tables" / "benchmark_summary.tsv",
        ),
        _copy_file(
            repro_bundle_root / "tables" / "metadata_audit.tsv",
            bundle_root / "tables" / "release_metadata_audit.tsv",
        ),
    ]
    copied_files = copied_documents + copied_assets

    init_artifact_bundle(
        bundle_root,
        title=str(package_config["title"]),
        skill_name="publication-package",
        summary=str(package_config["summary"]),
        metrics={
            "status": "completed",
            "package_type": "benchmark",
            "benchmark_name": benchmark_manifest["name"],
            "selected_method": benchmark_metrics["benchmark"]["selected_method"],
            "paper_source_bundle": str(paper_source_bundle),
            "included_file_count": len(copied_files),
        },
        config_yaml=yaml.safe_dump(
            stringify_paths(
                {
                    "package_type": "benchmark",
                    "release_manifest": release_manifest["source_path"],
                    "benchmark_bundle": benchmark_bundle_root,
                    "paper_source_bundle": paper_source_bundle,
                    "paper_bundle": paper_bundle_root,
                    "repro_bundle": repro_bundle_root,
                    "included_files": copied_files,
                }
            ),
            sort_keys=False,
        ),
        report_sections=[
            (
                "Benchmark Provenance",
                "\n".join(
                    [
                        f"- Benchmark: `{benchmark_manifest['name']}` `{benchmark_manifest['version']}`",
                        f"- Spec path: `{benchmark_manifest['source_paths']['benchmark_spec']}`",
                        f"- Dataset registry: `{benchmark_manifest['source_paths']['dataset_registry']}`",
                        f"- Dataset card: `{benchmark_manifest['dataset']['registry_entry']['card']}`",
                    ]
                ),
            ),
            (
                "Source Bundles",
                "\n".join(
                    [
                        f"- Benchmark bundle: `{benchmark_bundle_root}`",
                        f"- Paper source bundle: `{paper_source_bundle}`",
                        "- Nested paper-assets bundle: `runs/paper-assets`",
                        "- Nested repro-export bundle: `runs/repro-export`",
                    ]
                ),
            ),
            (
                "Generated Assets",
                "\n".join(
                    [
                        "- Top-level preview copied to `figures/manuscript_preview.pgm`.",
                        "- Top-level manuscript metrics copied to `tables/manuscript_metrics.tsv`.",
                        "- Top-level benchmark summary copied to `tables/benchmark_summary.tsv`.",
                        "- Top-level metadata audit copied to `tables/release_metadata_audit.tsv`.",
                    ]
                ),
            ),
            (
                "Reproducibility Notes",
                "\n".join(
                    [
                        "- Benchmark package assembly reuses the benchmark, paper, and repro-export workflows.",
                        "- Nested bundles remain intact under `runs/` for direct inspection.",
                    ]
                ),
            ),
        ],
        commands=render_commands(reproduction_command),
        analysis_log=render_analysis_log(
            [
                f"Loaded release manifest `{release_manifest['source_path']}`.",
                f"Resolved benchmark provenance from `{benchmark_bundle_root}`.",
                f"Used `{paper_source_bundle}` as the manuscript-asset source bundle.",
                "Ran nested paper-assets and repro-export workflows for package support material.",
                f"Copied {len(copied_files)} benchmark-paper support files into the top-level package.",
            ]
        ),
        environment_yaml=yaml.safe_dump(
            {
                "package_type": "benchmark",
                "release_version": release_manifest["project"]["version"],
                "benchmark_name": benchmark_manifest["name"],
                "benchmark_version": benchmark_manifest["version"],
                "paper_source_bundle": str(paper_source_bundle),
            },
            sort_keys=False,
        ),
    )
    write_tsv(
        bundle_root / "tables" / "benchmark_package_inventory.tsv",
        headers=["source", "destination", "sha256"],
        rows=[[item["source"], item["destination"], item["sha256"]] for item in copied_files],
    )
    (bundle_root / "reproducibility" / "package_manifest.json").write_text(
        json.dumps(
            {
                "package_type": "benchmark",
                "release_manifest": release_manifest["source_path"],
                "benchmark_bundle": str(benchmark_bundle_root),
                "paper_source_bundle": str(paper_source_bundle),
                "paper_bundle": str(paper_bundle_root),
                "repro_bundle": str(repro_bundle_root),
                "included_files": copied_files,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    finalize_bundle(bundle_root)
    return bundle_root
