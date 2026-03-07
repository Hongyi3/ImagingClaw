import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import yaml

from clawimaging.artifacts import validate_artifact_bundle
from clawimaging.skill_workflows.ct import run_ct_reconstruction
from clawimaging.skill_workflows.mri import run_mri_reconstruction


def _run_skill(script_path: Path, args: list[str], output_dir: Path) -> None:
    subprocess.run(
        [sys.executable, str(script_path), *args, "--output", str(output_dir)],
        check=True,
    )


def _assert_structured_bundle(
    output_dir: Path,
    *,
    expected_skill: str,
    required_metrics: list[str],
) -> None:
    validate_artifact_bundle(output_dir)
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (output_dir / "report.md").read_text(encoding="utf-8")

    assert metrics["status"] == "completed"
    assert metrics["skill"] == expected_skill
    for metric_name in required_metrics:
        assert metric_name in metrics["metrics"]
    assert "## Data Provenance" in report
    assert "## Acquisition" in report
    assert "## Metrics" in report
    assert (output_dir / "tables" / "metrics.tsv").exists()


def test_ct_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "ct-demo"
    _run_skill(repo_root / "skills" / "ct-recon" / "ct_recon.py", ["--demo"], output_dir)
    _assert_structured_bundle(output_dir, expected_skill="ct-recon", required_metrics=["psnr", "ssim", "nrmse"])


def test_mri_demo_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "mri-demo"
    _run_skill(repo_root / "skills" / "mri-recon" / "mri_recon.py", ["--demo"], output_dir)
    _assert_structured_bundle(output_dir, expected_skill="mri-recon", required_metrics=["nmse", "psnr", "ssim"])


def test_ct_declared_config_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "ct-config"
    _run_skill(
        repo_root / "skills" / "ct-recon" / "ct_recon.py",
        ["--config", str(repo_root / "experiments" / "specs" / "ct_fbp_example.yaml")],
        output_dir,
    )
    _assert_structured_bundle(output_dir, expected_skill="ct-recon", required_metrics=["psnr", "ssim", "nrmse"])


def test_mri_declared_config_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "mri-config"
    _run_skill(
        repo_root / "skills" / "mri-recon" / "mri_recon.py",
        ["--config", str(repo_root / "experiments" / "specs" / "mri_zero_fill_example.yaml")],
        output_dir,
    )
    _assert_structured_bundle(output_dir, expected_skill="mri-recon", required_metrics=["nmse", "psnr", "ssim"])


def test_ct_plain_npy_requires_declared_metadata(tmp_path: Path) -> None:
    measurement_path = tmp_path / "measurement.npy"
    np.save(measurement_path, np.zeros((8, 8), dtype=float))

    with pytest.raises(ValueError, match="require --config"):
        run_ct_reconstruction(
            tmp_path / "bundle",
            input_path=measurement_path,
            reproduction_command="python3 skills/ct-recon/ct_recon.py --input measurement.npy",
        )


def test_mri_config_requires_sampling_mask(tmp_path: Path) -> None:
    measurement_path = tmp_path / "measurement.npy"
    reference_path = tmp_path / "reference.npy"
    config_path = tmp_path / "mri.yaml"
    np.save(measurement_path, np.zeros((4, 8, 8), dtype=np.complex128))
    np.save(reference_path, np.zeros((8, 8), dtype=float))
    config_path.write_text(
        yaml.safe_dump(
            {
                "experiment": {
                    "experiment_id": "broken-mri",
                    "title": "Broken MRI config",
                    "modality": "mri",
                    "task": "synthetic",
                    "dataset": {
                        "name": "mri-demo-kspace",
                        "version": "0.1",
                        "split": "synthetic-example",
                        "access": "open",
                    },
                    "forward_model": {
                        "operator": "fourier-encoding",
                        "geometry": "cartesian",
                        "noise_model": "acquisition-native",
                    },
                    "method": "rss-zero-fill",
                    "metrics": ["nmse"],
                    "seed": 7,
                },
                "input": {
                    "measurement_path": str(measurement_path),
                    "reference_path": str(reference_path),
                    "provenance": {
                        "data_kind": "synthetic-measurements",
                        "measurement_domain": "k-space",
                        "source": "unit test",
                    },
                },
                "acquisition": {"coil_count": 4},
                "method_config": {"coil_combination": "rss"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="sampling_mask_path or sampling_mask"):
        run_mri_reconstruction(
            tmp_path / "bundle",
            config_path=config_path,
            reproduction_command="python3 skills/mri-recon/mri_recon.py --config mri.yaml",
        )
