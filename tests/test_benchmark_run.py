import json
from pathlib import Path
import subprocess
import sys

import yaml

from clawimaging.artifacts import validate_artifact_bundle


def _run_benchmark(spec_path: Path, output_dir: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "skills" / "benchmark-run" / "benchmark_run.py"
    subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(spec_path),
            "--output",
            str(output_dir),
        ],
        check=True,
    )


def test_benchmark_run_dispatches_ct_child_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "bundle"
    _run_benchmark(repo_root / "benchmarks" / "specs" / "lodopab_ct_baselines.yaml", output_dir)

    validate_artifact_bundle(output_dir)
    validate_artifact_bundle(output_dir / "runs" / "ct-recon-fbp")

    manifest = yaml.safe_load((output_dir / "resolved_config.yaml").read_text(encoding="utf-8"))
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (output_dir / "report.md").read_text(encoding="utf-8")

    assert manifest["execution"]["selected_phase2_method"] == "fbp"
    assert manifest["execution"]["child_bundle"] == "runs/ct-recon-fbp"
    assert metrics["status"] == "completed"
    assert metrics["benchmark"]["selected_phase2_method"] == "fbp"
    assert metrics["benchmark"]["dataset"]["executed_data_kind"] == "synthetic-measurements"
    assert "psnr" in metrics["child_run"]["metrics"]
    assert "## Executed Reconstruction" in report
    assert "Proxy for benchmark protocol: `true`" in report
    assert (output_dir / "tables" / "benchmark_summary.tsv").exists()


def test_benchmark_run_dispatches_mri_child_bundle(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_dir = tmp_path / "bundle"
    _run_benchmark(repo_root / "benchmarks" / "specs" / "fastmri_knee_baselines.yaml", output_dir)

    validate_artifact_bundle(output_dir)
    validate_artifact_bundle(output_dir / "runs" / "mri-recon-rss-zero-fill")

    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (output_dir / "report.md").read_text(encoding="utf-8")

    assert metrics["benchmark"]["selected_phase2_method"] == "rss-zero-fill"
    assert metrics["benchmark"]["child_bundle"] == "runs/mri-recon-rss-zero-fill"
    assert metrics["child_run"]["proxy_for_benchmark"] is True
    assert "nmse" in metrics["child_run"]["metrics"]
    assert "Upstream benchmark measurements were not executed directly" in report


def test_benchmark_run_rejects_missing_supported_method(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "skills" / "benchmark-run" / "benchmark_run.py"
    spec_path = tmp_path / "benchmark.yaml"
    spec_path.write_text(
        yaml.safe_dump(
            {
                "name": "broken-ct-benchmark",
                "version": "0.1.0",
                "modality": "ct",
                "task": "synthetic-ct",
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
                "preprocessing": ["none"],
                "calibration_assumptions": ["none"],
                "methods": [
                    {"name": "analytic-surrogate", "class": "analytic"},
                    {"name": "tv", "class": "iterative"},
                    {"name": "unrolled", "class": "learned"},
                ],
                "metrics": ["psnr"],
                "seeds": {"eval": 13},
                "hardware": {"reference_device": "cpu"},
                "environment": {"python": ">=3.10"},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--input",
            str(spec_path),
            "--output",
            str(tmp_path / "bundle"),
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "does not include the required Phase 2 method" in result.stderr
