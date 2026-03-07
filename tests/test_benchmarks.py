from pathlib import Path

import pytest
import yaml

from clawimaging.benchmarks import (
    load_benchmark_spec,
    load_benchmark_specs,
    resolve_benchmark_manifest,
)


def _dataset_entry(name: str = "demo-dataset", version: str = "1.0", **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": name,
        "version": version,
        "modality": "ct",
        "measurement_domain": "sinogram",
        "data_kind": "raw-measurements",
        "access": "open",
        "source": "Demo source",
        "redistribution_policy": "metadata only",
        "license_or_terms": "demo terms",
        "labels": [],
        "known_preprocessing_assumptions": ["none"],
        "card": "cards/demo.md",
        "notes": ["demo"],
    }
    payload.update(overrides)
    return payload


def _benchmark_spec(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "demo-benchmark",
        "version": "0.1.0",
        "modality": "ct",
        "task": "reconstruction",
        "dataset": {
            "name": "demo-dataset",
            "version": "1.0",
            "split": "standard",
            "access": "open",
        },
        "forward_model": {
            "operator": "x-ray-transform",
            "geometry": "parallel-beam",
            "noise_model": "poisson",
        },
        "preprocessing": ["none"],
        "calibration_assumptions": ["none"],
        "methods": [
            {"name": "fbp", "class": "analytic"},
            {"name": "tv", "class": "iterative"},
            {"name": "unrolled", "class": "learned"},
        ],
        "metrics": ["psnr"],
        "seeds": {"eval": 23},
        "hardware": {"reference_device": "cpu"},
        "environment": {"python": ">=3.10"},
        "notes": {"smoke_subset": 1},
    }
    payload.update(overrides)
    return payload


def _write_dataset_registry(tmp_path: Path, datasets: list[dict[str, object]]) -> Path:
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir(exist_ok=True)
    (cards_dir / "demo.md").write_text("# Demo\n", encoding="utf-8")
    path = tmp_path / "registry.yaml"
    path.write_text(yaml.safe_dump({"datasets": datasets}, sort_keys=False), encoding="utf-8")
    return path


def _write_benchmark_spec(tmp_path: Path, payload: dict[str, object]) -> Path:
    path = tmp_path / "benchmark.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


def test_load_benchmark_spec_repo_fixture() -> None:
    spec = load_benchmark_spec("benchmarks/specs/lodopab_ct_baselines.yaml")
    assert spec.name == "lodopab-ct-baselines"


def test_load_benchmark_spec_missing_metadata_field(tmp_path: Path) -> None:
    payload = _benchmark_spec()
    payload.pop("preprocessing")
    spec_path = _write_benchmark_spec(tmp_path, payload)
    with pytest.raises(ValueError, match="missing required fields: preprocessing"):
        load_benchmark_spec(spec_path)


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("metrics", []),
        ("preprocessing", []),
        ("calibration_assumptions", []),
        ("seeds", {}),
    ],
)
def test_load_benchmark_spec_rejects_empty_required_fields(
    tmp_path: Path,
    field_name: str,
    value: object,
) -> None:
    payload = _benchmark_spec(**{field_name: value})
    spec_path = _write_benchmark_spec(tmp_path, payload)
    with pytest.raises(ValueError, match=field_name):
        load_benchmark_spec(spec_path)


def test_load_benchmark_spec_requires_baseline_classes(tmp_path: Path) -> None:
    payload = _benchmark_spec(
        methods=[
            {"name": "fbp", "class": "analytic"},
            {"name": "tv", "class": "iterative"},
        ]
    )
    spec_path = _write_benchmark_spec(tmp_path, payload)
    with pytest.raises(ValueError, match="missing required baseline classes: learned"):
        load_benchmark_spec(spec_path)


def test_resolve_benchmark_manifest_unknown_dataset(tmp_path: Path) -> None:
    spec_path = _write_benchmark_spec(tmp_path, _benchmark_spec())
    registry_path = _write_dataset_registry(tmp_path, [_dataset_entry(name="other-dataset")])
    with pytest.raises(ValueError, match="not found"):
        resolve_benchmark_manifest(spec_path, registry_path=registry_path)


def test_resolve_benchmark_manifest_modality_mismatch(tmp_path: Path) -> None:
    spec_path = _write_benchmark_spec(tmp_path, _benchmark_spec())
    registry_path = _write_dataset_registry(
        tmp_path,
        [_dataset_entry(modality="mri")],
    )
    with pytest.raises(ValueError, match="modality does not match"):
        resolve_benchmark_manifest(spec_path, registry_path=registry_path)


def test_resolve_benchmark_manifest_access_mismatch(tmp_path: Path) -> None:
    spec_path = _write_benchmark_spec(tmp_path, _benchmark_spec())
    registry_path = _write_dataset_registry(
        tmp_path,
        [_dataset_entry(access="restricted")],
    )
    with pytest.raises(ValueError, match="access does not match"):
        resolve_benchmark_manifest(spec_path, registry_path=registry_path)


def test_load_benchmark_specs_repo_validate_against_registry() -> None:
    specs = load_benchmark_specs()
    assert {spec.name for spec in specs} == {
        "fastmri-knee-baselines",
        "lodopab-ct-baselines",
        "phase-retrieval-synthetic",
    }
    for spec_name in [
        "benchmarks/specs/lodopab_ct_baselines.yaml",
        "benchmarks/specs/fastmri_knee_baselines.yaml",
        "benchmarks/specs/phase_retrieval_synthetic.yaml",
    ]:
        manifest = resolve_benchmark_manifest(spec_name)
        assert "registry_entry" in manifest["dataset"]
