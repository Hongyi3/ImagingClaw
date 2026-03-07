from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .datasets import get_dataset_entry
from .paths import find_repo_root
from .specs import BenchmarkSpec


def _resolve_spec_path(path: str | Path) -> Path:
    return Path(path).resolve()


def _resolve_spec_dir(spec_dir: str | Path | None = None) -> Path:
    if spec_dir is not None:
        return Path(spec_dir).resolve()
    return (find_repo_root() / "benchmarks" / "specs").resolve()


def _display_path(path: Path) -> str:
    try:
        repo_root = find_repo_root(path)
    except FileNotFoundError:
        return str(path)
    try:
        return str(path.resolve().relative_to(repo_root))
    except ValueError:
        return str(path)


def load_benchmark_spec(path: str | Path) -> BenchmarkSpec:
    spec_path = _resolve_spec_path(path)
    with spec_path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise ValueError("Benchmark spec must be a mapping")
    try:
        return BenchmarkSpec.from_dict(payload)
    except ValueError as exc:
        raise ValueError(f"Benchmark spec {spec_path.name}: {exc}") from exc


def load_benchmark_specs(spec_dir: str | Path | None = None) -> list[BenchmarkSpec]:
    root = _resolve_spec_dir(spec_dir)
    paths = sorted(path for path in root.iterdir() if path.suffix in {".yaml", ".yml"})
    return [load_benchmark_spec(path) for path in paths]


def resolve_benchmark_manifest(
    spec_path: str | Path,
    registry_path: str | Path | None = None,
) -> dict[str, Any]:
    resolved_spec_path = _resolve_spec_path(spec_path)
    benchmark = load_benchmark_spec(resolved_spec_path)
    dataset_entry = get_dataset_entry(
        benchmark.dataset.name,
        benchmark.dataset.version,
        path=registry_path,
    )
    benchmark.validate_against_dataset(dataset_entry)

    resolved_registry_path = (
        Path(registry_path).resolve()
        if registry_path is not None
        else (find_repo_root(resolved_spec_path) / "datasets" / "registry.yaml").resolve()
    )
    manifest = benchmark.to_dict()
    dataset_manifest = dict(manifest["dataset"])
    dataset_manifest["registry_entry"] = dataset_entry.to_dict()
    manifest["dataset"] = dataset_manifest
    manifest["source_paths"] = {
        "benchmark_spec": _display_path(resolved_spec_path),
        "dataset_registry": _display_path(resolved_registry_path),
    }
    return manifest
