from clawimaging.specs import BenchmarkSpec, DatasetEntry


def test_dataset_entry_roundtrip() -> None:
    payload = {
        "name": "lodopab-ct",
        "version": "1.0",
        "modality": "ct",
        "measurement_domain": "sinogram",
        "data_kind": "raw-measurements",
        "access": "open",
        "source": "LoDoPaB-CT",
        "redistribution_policy": "metadata only",
        "license_or_terms": "upstream terms",
        "labels": [],
        "known_preprocessing_assumptions": ["published split"],
        "card": "datasets/cards/lodopab-ct.md",
        "notes": ["flagship"],
    }
    spec = DatasetEntry.from_dict(payload)
    assert spec.to_dict()["data_kind"] == "raw-measurements"


def test_benchmark_spec_roundtrip() -> None:
    payload = {
        "name": "demo",
        "version": "0.1.0",
        "modality": "ct",
        "task": "reconstruction",
        "dataset": {
            "name": "lodopab-ct",
            "version": "1.0",
            "split": "standard",
            "access": "open",
        },
        "forward_model": {
            "operator": "x-ray-transform",
            "geometry": "parallel-beam",
            "noise_model": "poisson",
        },
        "preprocessing": ["published split"],
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
    }
    spec = BenchmarkSpec.from_dict(payload)
    assert spec.to_dict()["name"] == "demo"
